# FloatCtl Middleware Tutorial

A comprehensive guide to writing middleware for the FloatCtl plugin system.

## Table of Contents

1. [What is Middleware?](#what-is-middleware)
2. [Basic Middleware Structure](#basic-middleware-structure)
3. [Middleware Phases](#middleware-phases)
4. [Simple Example: Logging Middleware](#simple-example-logging-middleware)
5. [Advanced Example: Data Transformation](#advanced-example-data-transformation)
6. [Event System](#event-system)
7. [Service Registry](#service-registry)
8. [Error Handling](#error-handling)
9. [Testing Middleware](#testing-middleware)
10. [Best Practices](#best-practices)

## What is Middleware?

Middleware in FloatCtl allows plugins to:
- **Intercept and transform data** in processing pipelines
- **Listen to and emit events** across the system
- **Provide services** to other plugins
- **Form processing chains** for complex operations

Think of middleware as a series of filters that data passes through, where each filter can:
- Examine the data
- Transform it
- Add metadata
- Trigger side effects
- Pass it to the next filter

## Basic Middleware Structure

Every middleware must implement the `MiddlewareInterface`:

```python
from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext, MiddlewarePhase
from typing import List

class MyMiddleware(MiddlewareInterface):
    @property
    def name(self) -> str:
        """Unique name for this middleware."""
        return "my_middleware"
    
    @property
    def priority(self) -> int:
        """Execution priority (lower numbers run first)."""
        return 100  # Default priority
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        """Which phases this middleware participates in."""
        return [MiddlewarePhase.PROCESS]
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Main processing logic."""
        # Your middleware logic here
        return context
```

## Middleware Phases

FloatCtl middleware operates in five phases:

1. **PRE_PROCESS** - Setup, validation, preparation
2. **PROCESS** - Main data transformation
3. **POST_PROCESS** - Cleanup, finalization, side effects
4. **ERROR** - Error handling and recovery
5. **CLEANUP** - Resource cleanup (always runs)

```python
class MultiPhaseMiddleware(MiddlewareInterface):
    @property
    def name(self) -> str:
        return "multi_phase_middleware"
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [
            MiddlewarePhase.PRE_PROCESS,
            MiddlewarePhase.PROCESS,
            MiddlewarePhase.POST_PROCESS,
            MiddlewarePhase.ERROR,
            MiddlewarePhase.CLEANUP
        ]
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Setup phase - validate inputs, prepare resources."""
        print(f"Pre-processing: {context.operation}")
        return context
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Main processing phase."""
        print(f"Processing: {context.data}")
        return context
    
    async def post_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Finalization phase."""
        print(f"Post-processing complete")
        return context
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> MiddlewareContext:
        """Handle errors."""
        print(f"Error occurred: {error}")
        return context
    
    async def cleanup(self, context: MiddlewareContext) -> None:
        """Cleanup resources."""
        print("Cleaning up resources")
```

## Simple Example: Logging Middleware

Let's create a middleware that logs all operations:

```python
from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext, MiddlewarePhase
from floatctl.core.logging import get_logger
from typing import List
import time

class LoggingMiddleware(MiddlewareInterface):
    def __init__(self):
        self.logger = get_logger(f"{__name__}.LoggingMiddleware")
        self._start_times = {}
    
    @property
    def name(self) -> str:
        return "logging_middleware"
    
    @property
    def priority(self) -> int:
        return 10  # Run early to capture everything
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [
            MiddlewarePhase.PRE_PROCESS,
            MiddlewarePhase.POST_PROCESS,
            MiddlewarePhase.ERROR,
            MiddlewarePhase.CLEANUP
        ]
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Log operation start."""
        operation_id = id(context)
        self._start_times[operation_id] = time.time()
        
        self.logger.info(
            "operation_started",
            operation=context.operation,
            plugin=context.plugin_name,
            data_type=type(context.data).__name__
        )
        
        return context
    
    async def post_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Log successful completion."""
        operation_id = id(context)
        duration = time.time() - self._start_times.get(operation_id, 0)
        
        self.logger.info(
            "operation_completed",
            operation=context.operation,
            duration_ms=round(duration * 1000, 2),
            success=True
        )
        
        return context
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> MiddlewareContext:
        """Log errors."""
        operation_id = id(context)
        duration = time.time() - self._start_times.get(operation_id, 0)
        
        self.logger.error(
            "operation_failed",
            operation=context.operation,
            duration_ms=round(duration * 1000, 2),
            error=str(error),
            error_type=type(error).__name__
        )
        
        return context
    
    async def cleanup(self, context: MiddlewareContext) -> None:
        """Clean up timing data."""
        operation_id = id(context)
        self._start_times.pop(operation_id, None)
```

## Advanced Example: Data Transformation

Here's a more complex middleware that transforms conversation data:

```python
from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext, MiddlewarePhase
from typing import List, Dict, Any
import re
from datetime import datetime

class ConversationEnhancerMiddleware(MiddlewareInterface):
    """Enhances conversation data with extracted patterns and metadata."""
    
    @property
    def name(self) -> str:
        return "conversation_enhancer"
    
    @property
    def priority(self) -> int:
        return 50  # Run in the middle of the pipeline
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [MiddlewarePhase.PROCESS]
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Enhance conversation data with patterns and metadata."""
        
        # Only process conversation data
        if context.operation != "process_conversation":
            return context
        
        data = context.data
        if not isinstance(data, dict) or 'messages' not in data:
            return context
        
        # Extract patterns from all messages
        patterns = self._extract_patterns(data['messages'])
        
        # Add enhancement metadata
        enhanced_data = data.copy()
        enhanced_data['extracted_patterns'] = patterns
        enhanced_data['enhancement_timestamp'] = datetime.utcnow().isoformat()
        enhanced_data['enhanced_by'] = self.name
        
        # Update context metadata
        context.metadata['patterns_found'] = len(patterns)
        context.metadata['enhanced'] = True
        
        return context.clone(data=enhanced_data)
    
    def _extract_patterns(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract :: patterns from messages."""
        patterns = []
        
        for msg_idx, message in enumerate(messages):
            content = message.get('content', '')
            if isinstance(content, list):
                # Handle structured content
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        content = item.get('text', '')
                        break
                else:
                    continue
            
            # Find all :: patterns
            pattern_matches = re.findall(r'([a-zA-Z_-]+)::\s*([^\n]*)', content, re.IGNORECASE)
            
            for pattern_type, pattern_content in pattern_matches:
                patterns.append({
                    'type': pattern_type.lower(),
                    'content': pattern_content.strip(),
                    'message_index': msg_idx,
                    'sender': message.get('sender', 'unknown')
                })
        
        return patterns
```

## Event System

Middleware can emit and listen to events for loose coupling:

```python
class EventAwareMiddleware(MiddlewareInterface):
    def __init__(self):
        self.processed_count = 0
    
    @property
    def name(self) -> str:
        return "event_aware_middleware"
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Process data and emit events."""
        
        # Emit event before processing
        await self.emit_event("before_processing", {
            "operation": context.operation,
            "data_size": len(str(context.data))
        })
        
        # Do some processing
        self.processed_count += 1
        
        # Emit event after processing
        await self.emit_event("after_processing", {
            "operation": context.operation,
            "processed_count": self.processed_count
        })
        
        return context
    
    # Event handling methods (available through PluginBase)
    async def emit_event(self, event_type: str, data: Any = None, **kwargs) -> None:
        """Emit an event (inherited from PluginBase)."""
        # This method is available when your plugin inherits from PluginBase
        pass
```

To listen to events in your plugin:

```python
class EventListenerPlugin(PluginBase, MiddlewareInterface):
    def __init__(self, config=None):
        super().__init__(config)
        # Subscribe to events
        self.subscribe_to_event("before_processing", self._on_before_processing)
        self.subscribe_to_event("after_processing", self._on_after_processing)
    
    async def _on_before_processing(self, data, **kwargs):
        """Handle before_processing event."""
        print(f"About to process: {data}")
    
    async def _on_after_processing(self, data, **kwargs):
        """Handle after_processing event."""
        print(f"Finished processing: {data}")
```

## Service Registry

Middleware can provide services to other plugins:

```python
class CacheService:
    """Simple in-memory cache service."""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Any:
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
    
    def clear(self) -> None:
        self._cache.clear()

class CacheMiddleware(MiddlewareInterface):
    def __init__(self):
        self.cache_service = CacheService()
    
    @property
    def name(self) -> str:
        return "cache_middleware"
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [MiddlewarePhase.PRE_PROCESS, MiddlewarePhase.POST_PROCESS]
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Register cache service and check for cached results."""
        
        # Register the cache service for other plugins to use
        self.register_service("cache", self.cache_service)
        
        # Check cache for this operation
        cache_key = f"{context.operation}:{hash(str(context.data))}"
        cached_result = self.cache_service.get(cache_key)
        
        if cached_result:
            context.metadata['cache_hit'] = True
            context.metadata['cached_result'] = cached_result
        
        return context
    
    async def post_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Cache the result."""
        
        if not context.metadata.get('cache_hit'):
            cache_key = f"{context.operation}:{hash(str(context.data))}"
            self.cache_service.set(cache_key, context.data)
            context.metadata['cached'] = True
        
        return context
```

Using services in other plugins:

```python
class ServiceUserPlugin(PluginBase):
    async def some_method(self):
        # Get the cache service
        cache = self.get_service("cache")
        if cache:
            result = cache.get("my_key")
            if result:
                return result
        
        # Compute result and cache it
        result = self._expensive_computation()
        if cache:
            cache.set("my_key", result)
        
        return result
```

## Error Handling

Middleware can handle and recover from errors:

```python
class ErrorRecoveryMiddleware(MiddlewareInterface):
    @property
    def name(self) -> str:
        return "error_recovery"
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [MiddlewarePhase.ERROR]
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> MiddlewareContext:
        """Attempt to recover from errors."""
        
        if isinstance(error, FileNotFoundError):
            # Try to create missing directories
            if context.file_path:
                context.file_path.parent.mkdir(parents=True, exist_ok=True)
                context.metadata['recovery_attempted'] = True
                context.metadata['recovery_type'] = 'create_directories'
        
        elif isinstance(error, ValueError) and "invalid data" in str(error):
            # Try to clean the data
            if isinstance(context.data, str):
                cleaned_data = self._clean_data(context.data)
                context = context.clone(data=cleaned_data)
                context.metadata['recovery_attempted'] = True
                context.metadata['recovery_type'] = 'data_cleaning'
        
        return context
    
    def _clean_data(self, data: str) -> str:
        """Clean invalid characters from data."""
        # Remove null bytes and other problematic characters
        return data.replace('\x00', '').strip()
```

## Testing Middleware

FloatCtl provides utilities for testing middleware:

```python
import pytest
from floatctl.testing.middleware_test_utils import (
    MockMiddlewareManager,
    run_middleware_pipeline,
    assert_middleware_phases
)
from floatctl.core.middleware import MiddlewareContext, MiddlewarePhase

class TestMyMiddleware:
    @pytest.fixture
    def middleware(self):
        return MyMiddleware()
    
    @pytest.fixture
    def manager(self):
        return MockMiddlewareManager()
    
    def test_middleware_phases(self, middleware):
        """Test that middleware declares correct phases."""
        assert_middleware_phases(middleware, [MiddlewarePhase.PROCESS])
    
    @pytest.mark.asyncio
    async def test_middleware_processing(self, middleware):
        """Test middleware processing logic."""
        
        # Create test data
        test_data = {"test": "data"}
        
        # Run through pipeline
        result_context = await run_middleware_pipeline(
            [middleware], 
            test_data, 
            operation="test_operation"
        )
        
        # Assert results
        assert result_context.data == test_data
        assert result_context.operation == "test_operation"
    
    @pytest.mark.asyncio
    async def test_middleware_with_manager(self, middleware, manager):
        """Test middleware with full manager."""
        
        # Register middleware
        manager.add_middleware(middleware)
        
        # Process data
        result = await manager.process("test_operation", {"input": "data"})
        
        # Verify result
        assert result is not None
```

## Best Practices

### 1. **Single Responsibility**
Each middleware should have one clear purpose:

```python
# Good: Focused on one task
class TimestampMiddleware(MiddlewareInterface):
    """Adds timestamps to data."""
    pass

# Bad: Doing too many things
class EverythingMiddleware(MiddlewareInterface):
    """Adds timestamps, validates data, sends emails, makes coffee..."""
    pass
```

### 2. **Proper Priority Management**
Use priority to control execution order:

```python
class ValidationMiddleware(MiddlewareInterface):
    @property
    def priority(self) -> int:
        return 10  # Run early to validate inputs

class LoggingMiddleware(MiddlewareInterface):
    @property
    def priority(self) -> int:
        return 5   # Run first to log everything

class CleanupMiddleware(MiddlewareInterface):
    @property
    def priority(self) -> int:
        return 200  # Run last to clean up
```

### 3. **Immutable Context Updates**
Always use `context.clone()` to update context:

```python
# Good: Immutable update
async def process(self, context: MiddlewareContext) -> MiddlewareContext:
    new_data = self._transform_data(context.data)
    return context.clone(data=new_data, metadata={'transformed': True})

# Bad: Mutating context
async def process(self, context: MiddlewareContext) -> MiddlewareContext:
    context.data = self._transform_data(context.data)  # Don't do this!
    return context
```

### 4. **Error Handling**
Be defensive and handle errors gracefully:

```python
async def process(self, context: MiddlewareContext) -> MiddlewareContext:
    try:
        # Your processing logic
        result = self._risky_operation(context.data)
        return context.clone(data=result)
    except Exception as e:
        # Log the error but don't break the pipeline
        self.logger.error("processing_failed", error=str(e))
        # Return original context unchanged
        return context
```

### 5. **Resource Management**
Always clean up resources:

```python
class ResourceMiddleware(MiddlewareInterface):
    def __init__(self):
        self._connections = []
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        connection = self._create_connection()
        self._connections.append(connection)
        # ... use connection
        return context
    
    async def cleanup(self, context: MiddlewareContext) -> None:
        """Always clean up resources."""
        for connection in self._connections:
            try:
                connection.close()
            except Exception:
                pass  # Don't let cleanup errors break things
        self._connections.clear()
```

### 6. **Configuration**
Make middleware configurable:

```python
from pydantic import BaseModel, Field

class MyMiddlewareConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable this middleware")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: float = Field(default=30.0, description="Operation timeout")

class ConfigurableMiddleware(MiddlewareInterface):
    def __init__(self, config: MyMiddlewareConfig):
        self.config = config
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        if not self.config.enabled:
            return context
        
        # Use configuration
        for attempt in range(self.config.max_retries):
            try:
                # Process with timeout
                result = await asyncio.wait_for(
                    self._do_processing(context.data),
                    timeout=self.config.timeout_seconds
                )
                return context.clone(data=result)
            except asyncio.TimeoutError:
                if attempt == self.config.max_retries - 1:
                    raise
                continue
```

## Integration with Plugins

To use middleware in your plugin, implement both `PluginBase` and `MiddlewareInterface`:

```python
from floatctl.plugin_manager import PluginBase
from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext

class MyPlugin(PluginBase, MiddlewareInterface):
    name = "my_plugin"
    description = "A plugin with middleware capabilities"
    
    # PluginBase methods
    def register_commands(self, cli_group):
        # Register CLI commands
        pass
    
    # MiddlewareInterface methods
    @property
    def name(self) -> str:
        return "my_plugin_middleware"
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        # Middleware processing logic
        return context
```

The plugin manager will automatically register your middleware when the plugin loads.

---

This tutorial covers the essential concepts for writing middleware in FloatCtl. Start with simple middleware and gradually add complexity as needed. The middleware system is designed to be flexible and composable, allowing you to build sophisticated processing pipelines.