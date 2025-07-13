"""Plugin management system for FloatCtl."""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from importlib import import_module
from importlib.metadata import entry_points

import rich_click as click
from rich.console import Console

from floatctl.core.logging import get_logger, log_plugin_event

console = Console()


class PluginBase:
    """Base class for FloatCtl plugins."""
    
    name: str = "unnamed"
    description: str = "No description provided"
    version: str = "0.1.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin with configuration."""
        self.config = config or {}
        if not os.environ.get('_FLOATCTL_COMPLETE'):
            self.logger = log_plugin_event(self.name, "initialized")
        else:
            self.logger = None
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register plugin commands with the CLI."""
        raise NotImplementedError("Plugins must implement register_commands")
    
    def validate_config(self) -> bool:
        """Validate plugin configuration."""
        return True
    
    def cleanup(self) -> None:
        """Cleanup resources when plugin is unloaded."""
        pass


class PluginManager:
    """Manage plugin discovery, loading, and lifecycle."""
    
    def __init__(self):
        """Initialize plugin manager."""
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self._logger = None
    
    @property
    def logger(self):
        """Get logger lazily."""
        if self._logger is None:
            self._logger = get_logger(__name__)
        return self._logger
    
    def load_plugins(self) -> None:
        """Load all available plugins."""
        # Load entry point plugins first
        self._load_entry_point_plugins()
        
        # Then load directory-based plugins (if needed)
        # self._load_directory_plugins()
        
        if not os.environ.get('_FLOATCTL_COMPLETE'):
            self.logger.info(
                "plugins_loaded",
                count=len(self.plugins),
                plugins=list(self.plugins.keys()),
            )
    
    def _load_entry_point_plugins(self) -> None:
        """Load plugins via setuptools entry points."""
        # For Python 3.9 compatibility
        if sys.version_info >= (3, 10):
            discovered = entry_points(group="floatctl.plugins")
        else:
            discovered = entry_points().get("floatctl.plugins", [])
        
        for entry_point in discovered:
            try:
                # Load the plugin class
                plugin_class = entry_point.load()
                
                # Instantiate the plugin
                plugin_instance = plugin_class()
                
                # Validate it's a proper plugin
                if not isinstance(plugin_instance, PluginBase):
                    if not os.environ.get('_FLOATCTL_COMPLETE'):
                        get_logger(__name__).warning(
                            "invalid_plugin",
                            name=entry_point.name,
                            reason="Not a PluginBase subclass",
                        )
                    continue
                
                # Store plugin info
                self.plugins[entry_point.name] = {
                    "instance": plugin_instance,
                    "entry_point": entry_point.value,
                    "loaded_from": "entry_point",
                }
                
                if not os.environ.get('_FLOATCTL_COMPLETE'):
                    log_plugin_event(
                        entry_point.name,
                        "loaded",
                        version=plugin_instance.version,
                    ).info("plugin_loaded_successfully")
                
            except Exception as e:
                log_plugin_event(
                    entry_point.name,
                    "load_error",
                    error=str(e),
                ).error("failed_to_load_plugin", exc_info=True)
    
    def register_cli_commands(self, cli_group: click.Group) -> None:
        """Register all plugin commands with the CLI."""
        for name, plugin_info in self.plugins.items():
            try:
                plugin_instance = plugin_info["instance"]
                plugin_instance.register_commands(cli_group)
                
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
        return plugin_info["instance"] if plugin_info else None
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins with their information."""
        return [
            {
                "name": name,
                "description": info["instance"].description,
                "version": info["instance"].version,
                "loaded_from": info["loaded_from"],
            }
            for name, info in self.plugins.items()
        ]
    
    def unload_plugin(self, name: str) -> bool:
        """Unload a specific plugin."""
        if name not in self.plugins:
            return False
        
        try:
            plugin_instance = self.plugins[name]["instance"]
            plugin_instance.cleanup()
            
            del self.plugins[name]
            
            log_plugin_event(
                name,
                "unloaded",
            ).info("plugin_unloaded")
            
            return True
            
        except Exception as e:
            log_plugin_event(
                name,
                "unload_error",
                error=str(e),
            ).error("failed_to_unload_plugin", exc_info=True)
            return False
    
    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin."""
        # Get the current plugin info
        if name not in self.plugins:
            return False
        
        plugin_info = self.plugins[name]
        
        # Unload it first
        if not self.unload_plugin(name):
            return False
        
        # Try to reload based on how it was loaded
        if plugin_info["loaded_from"] == "entry_point":
            self._load_entry_point_plugins()
            return name in self.plugins
        
        return False