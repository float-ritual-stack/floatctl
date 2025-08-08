"""Testing utilities for middleware plugins."""

import asyncio
from typing import Any, Dict, List
from unittest.mock import MagicMock
from pathlib import Path

from floatctl.core.middleware import (
    MiddlewareInterface, 
    MiddlewareContext, 
    MiddlewarePhase,
    MiddlewarePipeline,
    EventBus,
    ServiceRegistry
)


class MockMiddlewareContext:
    """Mock middleware context for testing."""
    
    def __init__(self, data: Any = None, **kwargs):
        self.data = data or {}
        self.metadata = kwargs.get('metadata', {})
        self.phase = kwargs.get('phase', MiddlewarePhase.PROCESS)
        self.plugin_name = kwargs.get('plugin_name')
        self.operation = kwargs.get('operation')
        self.file_path = kwargs.get('file_path')
    
    def clone(self, **updates):
        """Create a copy with updates."""
        new_context = MockMiddlewareContext(
            data=self.data,
            metadata=self.metadata.copy(),
            phase=self.phase,
            plugin_name=self.plugin_name,
            operation=self.operation,
            file_path=self.file_path
        )
        
        for key, value in updates.items():
            setattr(new_context, key, value)
        
        return new_context


class TestMiddleware(MiddlewareInterface):
    """Test middleware implementation."""
    
    def __init__(self, name: str, priority: int = 100, phases: List[MiddlewarePhase] = None):
        self._name = name
        self._priority = priority
        self._phases = phases or [MiddlewarePhase.PROCESS]
        self.call_log = []
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def priority(self) -> int:
        return self._priority
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return self._phases
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        self.call_log.append(('pre_process', context.data))
        context.metadata[f'{self.name}_pre_processed'] = True
        return context
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        self.call_log.append(('process', context.data))
        context.metadata[f'{self.name}_processed'] = True
        return context
    
    async def post_process(self, context: MiddlewareContext) -> MiddlewareContext:
        self.call_log.append(('post_process', context.data))
        context.metadata[f'{self.name}_post_processed'] = True
        return context
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> MiddlewareContext:
        self.call_log.append(('on_error', str(error)))
        context.metadata[f'{self.name}_error_handled'] = True
        return context
    
    async def cleanup(self, context: MiddlewareContext) -> None:
        self.call_log.append(('cleanup', context.data))


class MiddlewareTestCase:
    """Base test case for middleware testing."""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.service_registry = ServiceRegistry()
        self.pipeline = MiddlewarePipeline(self.event_bus, self.service_registry)
    
    def create_test_middleware(self, name: str, **kwargs) -> TestMiddleware:
        """Create a test middleware instance."""
        return TestMiddleware(name, **kwargs)
    
    def add_middleware(self, middleware: MiddlewareInterface):
        """Add middleware to the test pipeline."""
        self.pipeline.add_middleware(middleware)
    
    async def run_pipeline(self, data: Any, operation: str = "test") -> MiddlewareContext:
        """Run the middleware pipeline with test data."""
        context = MiddlewareContext(data=data, operation=operation)
        return await self.pipeline.execute(context)
    
    def assert_middleware_called(self, middleware: TestMiddleware, phase: str):
        """Assert that middleware was called for a specific phase."""
        calls = [call[0] for call in middleware.call_log]
        assert phase in calls, f"Middleware {middleware.name} was not called for phase {phase}"
    
    def assert_middleware_order(self, middlewares: List[TestMiddleware], phase: str):
        """Assert that middlewares were called in the correct order for a phase."""
        for i, middleware in enumerate(middlewares):
            phase_calls = [call for call in middleware.call_log if call[0] == phase]
            assert len(phase_calls) > 0, f"Middleware {middleware.name} was not called for phase {phase}"


def create_test_middleware(name: str, **kwargs) -> TestMiddleware:
    """Create a test middleware instance."""
    return TestMiddleware(name, **kwargs)


def assert_middleware_phases(middleware: MiddlewareInterface, expected_phases: List[MiddlewarePhase]):
    """Assert that middleware participates in expected phases."""
    assert set(middleware.phases) == set(expected_phases), \
        f"Middleware phases {middleware.phases} don't match expected {expected_phases}"


async def run_middleware_pipeline(middlewares: List[MiddlewareInterface], data: Any, operation: str = "test") -> MiddlewareContext:
    """Run a middleware pipeline with given middlewares and data."""
    event_bus = EventBus()
    service_registry = ServiceRegistry()
    pipeline = MiddlewarePipeline(event_bus, service_registry)
    
    for middleware in middlewares:
        pipeline.add_middleware(middleware)
    
    context = MiddlewareContext(data=data, operation=operation)
    return await pipeline.execute(context)


class MockAsyncMiddleware(MiddlewareInterface):
    """Mock middleware for testing async behavior."""
    
    def __init__(self, name: str, delay: float = 0.1):
        self._name = name
        self.delay = delay
        self.calls = []
    
    @property
    def name(self) -> str:
        return self._name
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        await asyncio.sleep(self.delay)
        self.calls.append('process')
        context.metadata[f'{self.name}_processed'] = True
        return context


class ErrorMiddleware(MiddlewareInterface):
    """Middleware that raises errors for testing error handling."""
    
    def __init__(self, name: str, error_phase: MiddlewarePhase = MiddlewarePhase.PROCESS):
        self._name = name
        self.error_phase = error_phase
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [self.error_phase, MiddlewarePhase.ERROR]
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        if self.error_phase == MiddlewarePhase.PRE_PROCESS:
            raise ValueError(f"Error in {self.name} pre_process")
        return context
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        if self.error_phase == MiddlewarePhase.PROCESS:
            raise ValueError(f"Error in {self.name} process")
        return context
    
    async def post_process(self, context: MiddlewareContext) -> MiddlewareContext:
        if self.error_phase == MiddlewarePhase.POST_PROCESS:
            raise ValueError(f"Error in {self.name} post_process")
        return context
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> MiddlewareContext:
        context.metadata[f'{self.name}_handled_error'] = str(error)
        return context


# Test utilities for specific middleware patterns
class DataTransformMiddleware(MiddlewareInterface):
    """Middleware that transforms data for testing."""
    
    def __init__(self, name: str, transform_func):
        self._name = name
        self.transform_func = transform_func
    
    @property
    def name(self) -> str:
        return self._name
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        context.data = self.transform_func(context.data)
        return context


class FilterMiddleware(MiddlewareInterface):
    """Middleware that filters data for testing."""
    
    def __init__(self, name: str, filter_func):
        self._name = name
        self.filter_func = filter_func
    
    @property
    def name(self) -> str:
        return self._name
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        if isinstance(context.data, list):
            context.data = [item for item in context.data if self.filter_func(item)]
        return context


class ValidationMiddleware(MiddlewareInterface):
    """Middleware that validates data for testing."""
    
    def __init__(self, name: str, validation_func):
        self._name = name
        self.validation_func = validation_func
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [MiddlewarePhase.PRE_PROCESS]
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        if not self.validation_func(context.data):
            raise ValueError(f"Validation failed in {self.name}")
        return context