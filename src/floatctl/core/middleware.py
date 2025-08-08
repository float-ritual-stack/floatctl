"""Middleware-style plugin framework for FloatCtl.

This module provides a middleware pattern for plugins, allowing them to:
- Intercept and transform data in processing pipelines
- Listen to and emit events across the system
- Provide services to other plugins
- Form processing chains for complex operations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from pathlib import Path

from floatctl.core.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic middleware
T = TypeVar('T')
R = TypeVar('R')


class MiddlewarePhase(Enum):
    """Phases in the middleware pipeline."""
    PRE_PROCESS = "pre_process"
    PROCESS = "process"
    POST_PROCESS = "post_process"
    ERROR = "error"
    CLEANUP = "cleanup"


@dataclass
class MiddlewareContext:
    """Context passed through middleware pipeline."""
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    phase: MiddlewarePhase = MiddlewarePhase.PRE_PROCESS
    plugin_name: Optional[str] = None
    operation: Optional[str] = None
    file_path: Optional[Path] = None
    
    def clone(self, **updates) -> 'MiddlewareContext':
        """Create a copy of context with updates."""
        new_data = {
            'data': self.data,
            'metadata': self.metadata.copy(),
            'phase': self.phase,
            'plugin_name': self.plugin_name,
            'operation': self.operation,
            'file_path': self.file_path,
        }
        new_data.update(updates)
        return MiddlewareContext(**new_data)


class MiddlewareInterface(ABC):
    """Interface for middleware plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    def priority(self) -> int:
        """Execution priority (lower numbers run first)."""
        return 100
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        """Which phases this middleware participates in."""
        return [MiddlewarePhase.PROCESS]
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called before main processing."""
        return context
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Main processing logic."""
        return context
    
    async def post_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Called after main processing."""
        return context
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> MiddlewareContext:
        """Called when an error occurs."""
        return context
    
    async def cleanup(self, context: MiddlewareContext) -> None:
        """Called for cleanup regardless of success/failure."""
        pass


class EventBus:
    """Simple event bus for plugin communication."""
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._logger = get_logger(f"{__name__}.EventBus")
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        self._logger.debug("event_subscription", event_type=event_type, callback=callback.__name__)
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
                self._logger.debug("event_unsubscription", event_type=event_type, callback=callback.__name__)
            except ValueError:
                pass
    
    async def emit(self, event_type: str, data: Any = None, **kwargs) -> None:
        """Emit an event to all subscribers."""
        if event_type not in self._listeners:
            return
        
        self._logger.debug("event_emission", event_type=event_type, listener_count=len(self._listeners[event_type]))
        
        for callback in self._listeners[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data, **kwargs)
                else:
                    callback(data, **kwargs)
            except Exception as e:
                self._logger.error("event_callback_error", 
                                 event_type=event_type, 
                                 callback=callback.__name__, 
                                 error=str(e))


class ServiceRegistry:
    """Registry for plugin services."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._logger = get_logger(f"{__name__}.ServiceRegistry")
    
    def register(self, name: str, service: Any) -> None:
        """Register a service."""
        self._services[name] = service
        self._logger.debug("service_registered", name=name, service_type=type(service).__name__)
    
    def unregister(self, name: str) -> None:
        """Unregister a service."""
        if name in self._services:
            del self._services[name]
            self._logger.debug("service_unregistered", name=name)
    
    def get(self, name: str) -> Optional[Any]:
        """Get a service by name."""
        return self._services.get(name)
    
    def list_services(self) -> List[str]:
        """List all registered service names."""
        return list(self._services.keys())


class MiddlewarePipeline:
    """Manages middleware execution pipeline."""
    
    def __init__(self, event_bus: EventBus, service_registry: ServiceRegistry):
        self.event_bus = event_bus
        self.service_registry = service_registry
        self._middleware: List[MiddlewareInterface] = []
        self._logger = get_logger(f"{__name__}.MiddlewarePipeline")
    
    def add_middleware(self, middleware: MiddlewareInterface) -> None:
        """Add middleware to the pipeline."""
        self._middleware.append(middleware)
        # Sort by priority (lower numbers first)
        self._middleware.sort(key=lambda m: m.priority)
        self._logger.debug("middleware_added", name=middleware.name, priority=middleware.priority)
    
    def remove_middleware(self, name: str) -> bool:
        """Remove middleware by name."""
        for i, middleware in enumerate(self._middleware):
            if middleware.name == name:
                del self._middleware[i]
                self._logger.debug("middleware_removed", name=name)
                return True
        return False
    
    async def execute(self, context: MiddlewareContext) -> MiddlewareContext:
        """Execute the middleware pipeline."""
        self._logger.debug("pipeline_start", operation=context.operation, plugin_count=len(self._middleware))
        
        try:
            # Pre-process phase
            context = context.clone(phase=MiddlewarePhase.PRE_PROCESS)
            for middleware in self._middleware:
                if MiddlewarePhase.PRE_PROCESS in middleware.phases:
                    context = await middleware.pre_process(context)
            
            # Process phase
            context = context.clone(phase=MiddlewarePhase.PROCESS)
            for middleware in self._middleware:
                if MiddlewarePhase.PROCESS in middleware.phases:
                    context = await middleware.process(context)
            
            # Post-process phase
            context = context.clone(phase=MiddlewarePhase.POST_PROCESS)
            for middleware in self._middleware:
                if MiddlewarePhase.POST_PROCESS in middleware.phases:
                    context = await middleware.post_process(context)
            
            self._logger.debug("pipeline_success", operation=context.operation)
            return context
            
        except Exception as e:
            self._logger.error("pipeline_error", operation=context.operation, error=str(e))
            
            # Error phase
            context = context.clone(phase=MiddlewarePhase.ERROR)
            for middleware in self._middleware:
                if MiddlewarePhase.ERROR in middleware.phases:
                    try:
                        context = await middleware.on_error(context, e)
                    except Exception as cleanup_error:
                        self._logger.error("middleware_error_handler_failed", 
                                         middleware=middleware.name, 
                                         error=str(cleanup_error))
            raise
        
        finally:
            # Cleanup phase
            context = context.clone(phase=MiddlewarePhase.CLEANUP)
            for middleware in self._middleware:
                if MiddlewarePhase.CLEANUP in middleware.phases:
                    try:
                        await middleware.cleanup(context)
                    except Exception as cleanup_error:
                        self._logger.error("middleware_cleanup_failed", 
                                         middleware=middleware.name, 
                                         error=str(cleanup_error))


class MiddlewareManager:
    """Central manager for the middleware system."""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.service_registry = ServiceRegistry()
        self.pipeline = MiddlewarePipeline(self.event_bus, self.service_registry)
        self._logger = get_logger(f"{__name__}.MiddlewareManager")
    
    def register_middleware(self, middleware: MiddlewareInterface) -> None:
        """Register a middleware plugin."""
        self.pipeline.add_middleware(middleware)
        self._logger.info("middleware_registered", name=middleware.name)
    
    def unregister_middleware(self, name: str) -> bool:
        """Unregister a middleware plugin."""
        success = self.pipeline.remove_middleware(name)
        if success:
            self._logger.info("middleware_unregistered", name=name)
        return success
    
    async def process(self, operation: str, data: Any, **metadata) -> Any:
        """Process data through the middleware pipeline."""
        context = MiddlewareContext(
            data=data,
            metadata=metadata,
            operation=operation
        )
        
        result_context = await self.pipeline.execute(context)
        return result_context.data
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a registered service."""
        return self.service_registry.get(name)
    
    def register_service(self, name: str, service: Any) -> None:
        """Register a service."""
        self.service_registry.register(name, service)
    
    async def emit_event(self, event_type: str, data: Any = None, **kwargs) -> None:
        """Emit an event."""
        await self.event_bus.emit(event_type, data, **kwargs)
    
    def subscribe_to_event(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event."""
        self.event_bus.subscribe(event_type, callback)


# Global middleware manager instance
middleware_manager = MiddlewareManager()