"""Plugin management system for FloatCtl."""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Type
from importlib import import_module
from importlib.metadata import entry_points
from dataclasses import dataclass, field
from enum import Enum

import rich_click as click
from rich.console import Console
from pydantic import BaseModel, ValidationError, Field, ConfigDict

from floatctl.core.logging import get_logger, log_plugin_event
from floatctl.core.middleware import middleware_manager, MiddlewareInterface

console = Console()


class PluginConfigBase(BaseModel):
    """Base configuration model for plugins."""
    
    model_config = ConfigDict(extra="allow")  # Allow additional fields for plugin-specific config
    
    enabled: bool = Field(default=True, description="Whether the plugin is enabled")
    debug: bool = Field(default=False, description="Enable debug mode for the plugin")


class PluginState(Enum):
    """Plugin lifecycle states."""
    DISCOVERED = "discovered"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    ERROR = "error"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"


@dataclass
class PluginInfo:
    """Information about a plugin."""
    name: str
    instance: Optional['PluginBase'] = None
    entry_point: Optional[str] = None
    loaded_from: str = "unknown"
    state: PluginState = PluginState.DISCOVERED
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    priority: int = 100
    error: Optional[str] = None
    
    def __post_init__(self):
        """Initialize mutable fields."""
        if isinstance(self.dependencies, (list, tuple)):
            self.dependencies = set(self.dependencies)
        if isinstance(self.dependents, (list, tuple)):
            self.dependents = set(self.dependents)


class PluginBase:
    """Base class for FloatCtl plugins."""
    
    name: str = "unnamed"
    description: str = "No description provided"
    version: str = "0.1.0"
    dependencies: List[str] = []
    priority: int = 100
    config_model: Type[PluginConfigBase] = PluginConfigBase
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin with configuration."""
        self._raw_config = config or {}
        self._validated_config = None
        self._state = PluginState.DISCOVERED
        self._manager = None
        if not os.environ.get('_FLOATCTL_COMPLETE'):
            self.logger = log_plugin_event(self.name, "initialized")
        else:
            self.logger = None
    
    @property
    def config(self) -> PluginConfigBase:
        """Get validated configuration."""
        if self._validated_config is None:
            try:
                self._validated_config = self.config_model(**self._raw_config)
            except ValidationError as e:
                # Fallback to basic config if validation fails
                self._validated_config = PluginConfigBase(**{
                    k: v for k, v in self._raw_config.items() 
                    if k in PluginConfigBase.__fields__
                })
                if not os.environ.get('_FLOATCTL_COMPLETE'):
                    log_plugin_event(
                        self.name,
                        "config_validation_warning",
                        error=str(e),
                        fallback_config=self._validated_config.dict()
                    ).warning("plugin_config_validation_failed")
        return self._validated_config
    
    @property
    def state(self) -> PluginState:
        """Get current plugin state."""
        return self._state
    
    def set_manager(self, manager: 'PluginManager') -> None:
        """Set the plugin manager reference."""
        self._manager = manager
    
    def get_dependency(self, name: str) -> Optional['PluginBase']:
        """Get a dependency plugin instance."""
        if self._manager:
            return self._manager.get_plugin(name)
        return None
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service from the middleware system."""
        return middleware_manager.get_service(name)
    
    def register_service(self, name: str, service: Any) -> None:
        """Register a service with the middleware system."""
        middleware_manager.register_service(name, service)
    
    async def emit_event(self, event_type: str, data: Any = None, **kwargs) -> None:
        """Emit an event through the middleware system."""
        await middleware_manager.emit_event(event_type, data, **kwargs)
    
    def subscribe_to_event(self, event_type: str, callback) -> None:
        """Subscribe to an event through the middleware system."""
        middleware_manager.subscribe_to_event(event_type, callback)
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register plugin commands with the CLI."""
        raise NotImplementedError("Plugins must implement register_commands")
    
    def validate_config(self) -> bool:
        """Validate plugin configuration using Pydantic model."""
        try:
            # Force validation by accessing the config property
            validated_config = self.config
            
            # Additional custom validation can be implemented by subclasses
            return self._custom_config_validation(validated_config)
            
        except ValidationError as e:
            if not os.environ.get('_FLOATCTL_COMPLETE'):
                log_plugin_event(
                    self.name,
                    "config_validation_failed",
                    error=str(e),
                    config=self._raw_config
                ).error("plugin_config_validation_error")
            return False
        except Exception as e:
            if not os.environ.get('_FLOATCTL_COMPLETE'):
                log_plugin_event(
                    self.name,
                    "config_validation_error",
                    error=str(e),
                    config=self._raw_config
                ).error("plugin_config_validation_unexpected_error")
            return False
    
    def _custom_config_validation(self, config: PluginConfigBase) -> bool:
        """Override this method for custom validation logic."""
        return True
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this plugin's configuration."""
        return self.config_model.schema()
    
    async def initialize(self) -> None:
        """Initialize the plugin after dependencies are loaded."""
        pass
    
    async def activate(self) -> None:
        """Activate the plugin (called after all plugins are initialized)."""
        pass
    
    async def deactivate(self) -> None:
        """Deactivate the plugin before unloading."""
        pass
    
    def cleanup(self) -> None:
        """Cleanup resources when plugin is unloaded."""
        pass


class PluginManager:
    """Manage plugin discovery, loading, and lifecycle."""
    
    def __init__(self):
        """Initialize plugin manager."""
        self.plugins: Dict[str, PluginInfo] = {}
        self._logger = None
        self._initialization_order: List[str] = []
        self._middleware_manager = middleware_manager
    
    @property
    def logger(self):
        """Get logger lazily."""
        if self._logger is None:
            self._logger = get_logger(__name__)
        return self._logger
    
    async def load_plugins(self) -> None:
        """Load all available plugins with proper lifecycle management."""
        # Discover plugins
        self._discover_entry_point_plugins()
        
        # Resolve dependencies and determine load order
        load_order = self._resolve_dependencies()
        
        # Load plugins in dependency order
        for plugin_name in load_order:
            await self._load_plugin(plugin_name)
        
        # Initialize plugins in dependency order
        for plugin_name in load_order:
            await self._initialize_plugin(plugin_name)
        
        # Activate all plugins
        for plugin_name in load_order:
            await self._activate_plugin(plugin_name)
        
        if not os.environ.get('_FLOATCTL_COMPLETE'):
            self.logger.info(
                "plugins_loaded",
                count=len([p for p in self.plugins.values() if p.state == PluginState.ACTIVE]),
                plugins=list(self.plugins.keys()),
                load_order=load_order,
            )
    
    def _discover_entry_point_plugins(self) -> None:
        """Discover plugins via setuptools entry points."""
        # For Python 3.9 compatibility
        if sys.version_info >= (3, 10):
            discovered = entry_points(group="floatctl.plugins")
        else:
            discovered = entry_points().get("floatctl.plugins", [])
        
        for entry_point in discovered:
            try:
                # Load the plugin class
                plugin_class = entry_point.load()
                
                # Validate it's a proper plugin class
                if not (isinstance(plugin_class, type) and issubclass(plugin_class, PluginBase)):
                    if not os.environ.get('_FLOATCTL_COMPLETE'):
                        get_logger(__name__).warning(
                            "invalid_plugin",
                            name=entry_point.name,
                            reason="Not a PluginBase subclass",
                        )
                    continue
                
                # Create plugin info (don't instantiate yet)
                plugin_info = PluginInfo(
                    name=entry_point.name,
                    entry_point=entry_point.value,
                    loaded_from="entry_point",
                    dependencies=set(getattr(plugin_class, 'dependencies', [])),
                    priority=getattr(plugin_class, 'priority', 100),
                    state=PluginState.DISCOVERED
                )
                
                self.plugins[entry_point.name] = plugin_info
                
                if not os.environ.get('_FLOATCTL_COMPLETE'):
                    log_plugin_event(
                        entry_point.name,
                        "discovered",
                        dependencies=list(plugin_info.dependencies),
                        priority=plugin_info.priority,
                    ).debug("plugin_discovered")
                
            except Exception as e:
                error_info = PluginInfo(
                    name=entry_point.name,
                    entry_point=entry_point.value,
                    loaded_from="entry_point",
                    state=PluginState.ERROR,
                    error=str(e)
                )
                self.plugins[entry_point.name] = error_info
                
                log_plugin_event(
                    entry_point.name,
                    "discovery_error",
                    error=str(e),
                ).error("failed_to_discover_plugin", exc_info=True)
    
    def _resolve_dependencies(self) -> List[str]:
        """Resolve plugin dependencies and return load order."""
        # Build dependency graph
        dependency_graph = {}
        for name, info in self.plugins.items():
            if info.state != PluginState.ERROR:
                dependency_graph[name] = info.dependencies.copy()
        
        # Topological sort to determine load order
        load_order = []
        visited = set()
        temp_visited = set()
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {plugin_name}")
            if plugin_name in visited:
                return
            
            temp_visited.add(plugin_name)
            
            # Visit dependencies first
            for dep in dependency_graph.get(plugin_name, set()):
                if dep not in self.plugins:
                    self.logger.warning(
                        "missing_dependency",
                        plugin=plugin_name,
                        dependency=dep
                    )
                    continue
                visit(dep)
            
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            load_order.append(plugin_name)
        
        # Visit all plugins
        for plugin_name in dependency_graph:
            if plugin_name not in visited:
                visit(plugin_name)
        
        # Update dependent relationships
        for name, info in self.plugins.items():
            for dep in info.dependencies:
                if dep in self.plugins:
                    self.plugins[dep].dependents.add(name)
        
        self._initialization_order = load_order
        return load_order
    
    async def _load_plugin(self, name: str) -> bool:
        """Load a specific plugin."""
        info = self.plugins.get(name)
        if not info or info.state == PluginState.ERROR:
            return False
        
        if info.state != PluginState.DISCOVERED:
            return True  # Already loaded
        
        try:
            info.state = PluginState.LOADING
            
            # Load the plugin class and instantiate
            if info.loaded_from == "entry_point":
                if sys.version_info >= (3, 10):
                    discovered = entry_points(group="floatctl.plugins")
                else:
                    discovered = entry_points().get("floatctl.plugins", [])
                
                for entry_point in discovered:
                    if entry_point.name == name:
                        plugin_class = entry_point.load()
                        plugin_instance = plugin_class()
                        plugin_instance.set_manager(self)
                        plugin_instance._state = PluginState.LOADED
                        info.instance = plugin_instance
                        break
            
            if not info.instance:
                raise RuntimeError(f"Failed to instantiate plugin {name}")
            
            info.state = PluginState.LOADED
            
            # Register middleware if plugin implements MiddlewareInterface
            if isinstance(info.instance, MiddlewareInterface):
                self._middleware_manager.register_middleware(info.instance)
            
            if not os.environ.get('_FLOATCTL_COMPLETE'):
                log_plugin_event(
                    name,
                    "loaded",
                    version=info.instance.version,
                ).info("plugin_loaded_successfully")
            
            return True
            
        except Exception as e:
            info.state = PluginState.ERROR
            info.error = str(e)
            log_plugin_event(
                name,
                "load_error",
                error=str(e),
            ).error("failed_to_load_plugin", exc_info=True)
            return False
    
    async def _initialize_plugin(self, name: str) -> bool:
        """Initialize a specific plugin."""
        info = self.plugins.get(name)
        if not info or info.state != PluginState.LOADED:
            return False
        
        try:
            info.state = PluginState.INITIALIZING
            info.instance._state = PluginState.INITIALIZING
            
            # Validate configuration
            if not info.instance.validate_config():
                raise RuntimeError("Plugin configuration validation failed")
            
            # Initialize the plugin
            await info.instance.initialize()
            
            info.state = PluginState.INITIALIZED
            info.instance._state = PluginState.INITIALIZED
            
            if not os.environ.get('_FLOATCTL_COMPLETE'):
                log_plugin_event(
                    name,
                    "initialized",
                ).info("plugin_initialized_successfully")
            
            return True
            
        except Exception as e:
            info.state = PluginState.ERROR
            info.error = str(e)
            log_plugin_event(
                name,
                "initialization_error",
                error=str(e),
            ).error("failed_to_initialize_plugin", exc_info=True)
            return False
    
    async def _activate_plugin(self, name: str) -> bool:
        """Activate a specific plugin."""
        info = self.plugins.get(name)
        if not info or info.state != PluginState.INITIALIZED:
            return False
        
        try:
            # Activate the plugin
            await info.instance.activate()
            
            info.state = PluginState.ACTIVE
            info.instance._state = PluginState.ACTIVE
            
            if not os.environ.get('_FLOATCTL_COMPLETE'):
                log_plugin_event(
                    name,
                    "activated",
                ).info("plugin_activated_successfully")
            
            return True
            
        except Exception as e:
            info.state = PluginState.ERROR
            info.error = str(e)
            log_plugin_event(
                name,
                "activation_error",
                error=str(e),
            ).error("failed_to_activate_plugin", exc_info=True)
            return False
    
    def register_cli_commands(self, cli_group: click.Group) -> None:
        """Register all plugin commands with the CLI."""
        for name, plugin_info in self.plugins.items():
            if plugin_info.state == PluginState.ACTIVE and plugin_info.instance:
                try:
                    plugin_info.instance.register_commands(cli_group)
                    
                    if not os.environ.get('_FLOATCTL_COMPLETE'):
                        log_plugin_event(
                            name,
                            "commands_registered",
                        ).debug("plugin_commands_registered")
                    
                except Exception as e:
                    log_plugin_event(
                        name,
                        "register_error",
                        error=str(e),
                    ).error("failed_to_register_commands", exc_info=True)
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a specific plugin instance."""
        plugin_info = self.plugins.get(name)
        return plugin_info.instance if plugin_info and plugin_info.state == PluginState.ACTIVE else None
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all plugins with their information."""
        return [
            {
                "name": name,
                "description": info.instance.description if info.instance else "N/A",
                "version": info.instance.version if info.instance else "N/A",
                "loaded_from": info.loaded_from,
                "state": info.state.value,
                "dependencies": list(info.dependencies),
                "dependents": list(info.dependents),
                "priority": info.priority,
                "error": info.error,
            }
            for name, info in self.plugins.items()
        ]
    
    async def unload_plugin(self, name: str) -> bool:
        """Unload a specific plugin and its dependents."""
        if name not in self.plugins:
            return False
        
        info = self.plugins[name]
        
        # First unload all dependents
        for dependent in list(info.dependents):
            if not await self.unload_plugin(dependent):
                self.logger.warning("failed_to_unload_dependent", plugin=name, dependent=dependent)
        
        try:
            info.state = PluginState.UNLOADING
            
            if info.instance:
                # Deactivate first
                if info.instance._state == PluginState.ACTIVE:
                    await info.instance.deactivate()
                
                # Cleanup resources
                info.instance.cleanup()
                
                # Unregister middleware if applicable
                if isinstance(info.instance, MiddlewareInterface):
                    self._middleware_manager.unregister_middleware(info.instance.name)
            
            # Remove from dependents of dependencies
            for dep_name in info.dependencies:
                if dep_name in self.plugins:
                    self.plugins[dep_name].dependents.discard(name)
            
            info.state = PluginState.UNLOADED
            info.instance = None
            
            log_plugin_event(
                name,
                "unloaded",
            ).info("plugin_unloaded")
            
            return True
            
        except Exception as e:
            info.state = PluginState.ERROR
            info.error = str(e)
            log_plugin_event(
                name,
                "unload_error",
                error=str(e),
            ).error("failed_to_unload_plugin", exc_info=True)
            return False
    
    async def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin."""
        if name not in self.plugins:
            return False
        
        info = self.plugins[name]
        loaded_from = info.loaded_from
        
        # Unload it first
        if not await self.unload_plugin(name):
            return False
        
        # Rediscover and reload
        if loaded_from == "entry_point":
            # Clear the plugin info
            del self.plugins[name]
            
            # Rediscover
            self._discover_entry_point_plugins()
            
            if name in self.plugins:
                # Reload with proper dependency resolution
                load_order = self._resolve_dependencies()
                
                # Find position of this plugin in load order
                if name in load_order:
                    plugin_index = load_order.index(name)
                    
                    # Load this plugin and any dependencies that were unloaded
                    for plugin_name in load_order[plugin_index:]:
                        if self.plugins[plugin_name].state == PluginState.DISCOVERED:
                            await self._load_plugin(plugin_name)
                            await self._initialize_plugin(plugin_name)
                            await self._activate_plugin(plugin_name)
                    
                    return self.plugins[name].state == PluginState.ACTIVE
        
        return False
    
    async def shutdown_all_plugins(self) -> None:
        """Shutdown all plugins in reverse dependency order."""
        # Reverse the initialization order for shutdown
        shutdown_order = list(reversed(self._initialization_order))
        
        for plugin_name in shutdown_order:
            if plugin_name in self.plugins:
                await self.unload_plugin(plugin_name)
        
        self.logger.info("all_plugins_shutdown")
    
    def get_plugin_dependencies(self, name: str) -> Set[str]:
        """Get the dependencies of a plugin."""
        info = self.plugins.get(name)
        return info.dependencies.copy() if info else set()
    
    def get_plugin_dependents(self, name: str) -> Set[str]:
        """Get the plugins that depend on this plugin."""
        info = self.plugins.get(name)
        return info.dependents.copy() if info else set()
    
    def get_load_order(self) -> List[str]:
        """Get the current plugin load order."""
        return self._initialization_order.copy()