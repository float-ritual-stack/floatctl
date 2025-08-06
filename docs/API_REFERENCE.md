# FloatCtl API Reference

Complete reference for FloatCtl's core classes, interfaces, and plugin development APIs.

> **💡 Quick Start**: New to plugin development? Check the [Plugin Development Guide](development/PLUGIN_DEVELOPMENT_GUIDE.md) for step-by-step tutorials, then return here for detailed API documentation.

## 🎯 Common Use Cases

| I want to... | Start with... | Key APIs |
|--------------|---------------|----------|
| **Create a simple plugin** | [PluginBase](#pluginbase) | `register_commands()`, `click.Group` |
| **Process data with middleware** | [MiddlewareInterface](#middlewareinterface) | `process()`, `MiddlewareContext` |
| **Track file operations** | [DatabaseManager](#databasemanager) | `record_file_run()`, `complete_file_run()` |
| **Add configuration** | [Plugin Configuration](#plugin-configuration) | `PluginConfigBase`, `Field()` |
| **Handle errors gracefully** | [Error Handling](#error-handling) | `PluginError`, structured logging |

## Table of Contents

1. [Core Classes](#core-classes)
2. [Plugin System](#plugin-system)
3. [Middleware Interface](#middleware-interface)
4. [Database Models](#database-models)
5. [Configuration System](#configuration-system)
6. [Logging and Events](#logging-and-events)
7. [Utility Functions](#utility-functions)

---

## Core Classes

### `floatctl.core.config.Config`

Main configuration class using Pydantic for validation.

```python
from floatctl.core.config import Config, load_config

# Load configuration from multiple sources
config = load_config(config_path="/path/to/config.json")
```

#### Properties

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| `db_path` | `Path` | SQLite database file path | `~/.floatctl/floatctl.db` |
| `output_dir` | `Path` | Default output directory | `./output` |
| `log_level` | `str` | Logging level | `"INFO"` |
| `log_file` | `Optional[Path]` | Log file path | `None` |
| `plugins` | `Dict[str, Any]` | Plugin-specific configuration | `{}` |

#### Methods

##### `load_config(config_path: Optional[Path] = None) -> Config`

Loads configuration from multiple sources in priority order:
1. Environment variable: `FLOATCTL_CONFIG`
2. User config: `~/.config/floatctl/config.json`
3. Project config: `./floatctl.config.json`
4. Command-line overrides

**Parameters:**
- `config_path`: Optional path to specific config file

**Returns:** Validated `Config` instance

**Example:**
```python
# Load with defaults
config = load_config()

# Load specific file
config = load_config(Path("./my-config.json"))

# Access configuration
print(config.db_path)
print(config.plugins.get("chroma", {}))

# Use in plugin
class MyPlugin(PluginBase):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Access global config
        global_config = load_config()
        self.output_dir = global_config.output_dir
```

---

### `floatctl.core.database.DatabaseManager`

SQLite database manager for tracking file operations and metadata.

```python
from floatctl.core.database import DatabaseManager

db_manager = DatabaseManager(config.db_path)
```

#### Methods

##### `record_file_run(file_path: Path, plugin: str, command: str, metadata: Optional[Dict] = None) -> FileRun`

Records the start of a file processing operation.

**Parameters:**
- `file_path`: Path to the file being processed
- `plugin`: Name of the plugin performing the operation
- `command`: Command being executed
- `metadata`: Optional metadata dictionary

**Returns:** `FileRun` instance with unique ID

**Example:**
```python
# In your plugin command
@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.pass_context
def process_file(ctx: click.Context, input_file: str) -> None:
    """Process a file with tracking."""
    from floatctl.core.database import DatabaseManager
    from floatctl.core.config import load_config
    
    config = load_config()
    db_manager = DatabaseManager(config.db_path)
    
    # Start tracking
    file_run = db_manager.record_file_run(
        Path(input_file),
        plugin="myplugin",
        command="process_file",
        metadata={"format": "markdown", "user": "developer"}
    )
    
    try:
        # Your processing logic here
        items_processed = process_data(input_file)
        
        # Mark as completed
        db_manager.complete_file_run(
            file_run.id,
            output_path=Path("./output"),
            items_processed=items_processed
        )
        
    except Exception as e:
        # Mark as failed
        db_manager.fail_file_run(file_run.id, str(e))
        raise
```

##### `complete_file_run(run_id: int, output_path: Optional[Path] = None, items_processed: int = 0) -> None`

Marks a file run as completed.

**Parameters:**
- `run_id`: ID from `record_file_run()`
- `output_path`: Optional path to output file/directory
- `items_processed`: Number of items processed

**Example:**
```python
db_manager.complete_file_run(
    file_run.id,
    output_path=Path("./output/conversations"),
    items_processed=5
)
```

##### `get_file_history(file_path: Path) -> List[FileRun]`

Gets processing history for a specific file.

**Parameters:**
- `file_path`: Path to the file

**Returns:** List of `FileRun` instances ordered by timestamp

---

## Plugin System

### `floatctl.plugin_manager.PluginBase`

Abstract base class that all plugins must inherit from.

```python
from floatctl.plugin_manager import PluginBase
import rich_click as click
from rich.console import Console

class MyPlugin(PluginBase):
    name = "myplugin"
    description = "My custom plugin"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        # ALL commands must be defined here
        pass
```

#### Class Attributes

| Attribute | Type | Description | Required |
|-----------|------|-------------|----------|
| `name` | `str` | Unique plugin identifier | ✅ |
| `description` | `str` | Brief plugin description | ✅ |
| `version` | `str` | Plugin version (semver) | ✅ |
| `dependencies` | `List[str]` | List of required plugin names | ❌ |
| `priority` | `int` | Load priority (lower = earlier) | ❌ |
| `config_model` | `Type[PluginConfigBase]` | Pydantic config model | ❌ |

#### Methods

##### `register_commands(self, cli_group: click.Group) -> None`

**🚨 CRITICAL**: All plugin commands MUST be defined inside this method.

**Parameters:**
- `cli_group`: Click group to register commands with

**Complete Plugin Example:**
```python
from floatctl.plugin_manager import PluginBase
import rich_click as click
from rich.console import Console
from rich.table import Table
from pathlib import Path

class MyPlugin(PluginBase):
    name = "myplugin"
    description = "Example plugin with multiple commands"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """🚨 ALL commands MUST be inside this method!"""
        
        @cli_group.group()
        @click.pass_context
        def myplugin(ctx: click.Context) -> None:
            """My plugin commands."""
            pass
        
        # ✅ Basic command with options
        @myplugin.command()
        @click.option("--verbose", is_flag=True, help="Verbose output")
        @click.option("--name", default="World", help="Name to greet")
        @click.pass_context
        def hello(ctx: click.Context, verbose: bool, name: str) -> None:
            """Say hello with optional verbosity."""
            console = Console()
            message = f"Hello, {name}!"
            if verbose:
                message += " (verbose mode enabled)"
            console.print(f"[green]{message}[/green]")
        
        # ✅ Command with file processing
        @myplugin.command()
        @click.argument("input_file", type=click.Path(exists=True))
        @click.option("--output-dir", type=click.Path(), default="./output")
        @click.pass_context
        def process(ctx: click.Context, input_file: str, output_dir: str) -> None:
            """Process a file."""
            console = Console()
            
            # Use database tracking
            from floatctl.core.database import DatabaseManager
            from floatctl.core.config import load_config
            
            config = load_config()
            db_manager = DatabaseManager(config.db_path)
            
            file_run = db_manager.record_file_run(
                Path(input_file),
                plugin=self.name,
                command="process"
            )
            
            try:
                # Your processing logic
                console.print(f"Processing {input_file}...")
                # ... processing code ...
                
                db_manager.complete_file_run(file_run.id, items_processed=1)
                console.print("[green]✅ Processing complete![/green]")
                
            except Exception as e:
                self.logger.error("Processing failed", error=str(e))
                console.print(f"[red]❌ Error: {e}[/red]")
                raise click.ClickException(str(e))
        
        # ✅ Command with rich output
        @myplugin.command()
        @click.pass_context
        def status(ctx: click.Context) -> None:
            """Show plugin status."""
            console = Console()
            
            table = Table(title="Plugin Status")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Name", self.name)
            table.add_row("Version", self.version)
            table.add_row("Description", self.description)
            
            console.print(table)
```

##### `__init__(self, config: Optional[Dict[str, Any]] = None)`

Plugin constructor with configuration.

**Parameters:**
- `config`: Plugin-specific configuration dictionary

**Properties Available:**
- `self.config`: Validated configuration object
- `self.logger`: Structured logger instance (if not in completion mode)

---

### `floatctl.plugin_manager.PluginManager`

Manages plugin discovery, loading, and lifecycle.

```python
from floatctl.plugin_manager import PluginManager

manager = PluginManager()
plugins = manager.discover_plugins()
manager.load_plugins(cli_group)
```

#### Methods

##### `discover_plugins() -> Dict[str, PluginInfo]`

Discovers all available plugins via entry points.

**Returns:** Dictionary mapping plugin names to `PluginInfo` objects

##### `load_plugins(cli_group: click.Group, config: Optional[Config] = None) -> None`

Loads and registers all discovered plugins.

**Parameters:**
- `cli_group`: Click group to register plugin commands with
- `config`: Optional configuration object

---

## Middleware Interface

### `floatctl.core.middleware.MiddlewareInterface`

Abstract interface for middleware components.

```python
from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext, MiddlewarePhase

class MyMiddleware(MiddlewareInterface):
    @property
    def name(self) -> str:
        return "my_middleware"
    
    @property
    def priority(self) -> int:
        return 100
    
    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        # Transform data here
        return context
```

#### Abstract Properties

##### `name: str`
Unique identifier for the middleware.

##### `priority: int`
Execution priority (lower numbers execute first).

#### Abstract Methods

##### `process(self, context: MiddlewareContext) -> MiddlewareContext`

Main processing method called by the middleware pipeline.

**Parameters:**
- `context`: Current middleware context with data and metadata

**Returns:** Modified context to pass to next middleware

**Complete Middleware Example:**
```python
from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext
from datetime import datetime
from typing import Any, Dict
import re

class PatternExtractionMiddleware(MiddlewareInterface):
    """Extract patterns from conversation data."""
    
    @property
    def name(self) -> str:
        return "pattern_extraction"
    
    @property
    def priority(self) -> int:
        return 100  # Run early in pipeline
    
    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Extract patterns from conversation content."""
        
        # Add processing timestamp
        context.add_metadata("processed_at", datetime.utcnow().isoformat())
        context.add_metadata("processed_by", self.name)
        
        # Extract patterns if data contains text
        if isinstance(context.data, dict) and "content" in context.data:
            patterns = self._extract_patterns(context.data["content"])
            context.add_metadata("extracted_patterns", patterns)
            
            # Modify data to include pattern markers
            context.data["pattern_count"] = len(patterns)
            context.data["has_ctx_markers"] = any(p["type"] == "ctx" for p in patterns)
        
        return context
    
    def _extract_patterns(self, content: str) -> list[Dict[str, Any]]:
        """Extract :: patterns from content."""
        patterns = []
        
        # Find ctx:: markers
        ctx_pattern = r'ctx::([^\\n]+)'
        for match in re.finditer(ctx_pattern, content):
            patterns.append({
                "type": "ctx",
                "content": match.group(1).strip(),
                "position": match.start()
            })
        
        # Find highlight:: markers  
        highlight_pattern = r'highlight::([^\\n]+)'
        for match in re.finditer(highlight_pattern, content):
            patterns.append({
                "type": "highlight", 
                "content": match.group(1).strip(),
                "position": match.start()
            })
        
        return patterns

# Usage in plugin
class ConversationPlugin(PluginBase):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Register middleware
        self.middleware = [PatternExtractionMiddleware()]
    
    def process_with_middleware(self, data: Any) -> Any:
        """Process data through middleware pipeline."""
        context = MiddlewareContext(
            data=data,
            metadata={},
            phase="processing",
            plugin_name=self.name,
            command_name="process"
        )
        
        # Run through middleware
        for middleware in self.middleware:
            context = middleware.process(context)
        
        return context.data, context.metadata
```

---

### `floatctl.core.middleware.MiddlewareContext`

Context object passed through middleware pipeline.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `Any` | Primary data being processed |
| `metadata` | `Dict[str, Any]` | Processing metadata |
| `phase` | `MiddlewarePhase` | Current processing phase |
| `plugin_name` | `str` | Name of originating plugin |
| `command_name` | `str` | Name of command being executed |

#### Methods

##### `add_metadata(self, key: str, value: Any) -> None`

Adds metadata to the context.

##### `get_metadata(self, key: str, default: Any = None) -> Any`

Retrieves metadata value with optional default.

---

## Database Models

### `floatctl.core.database.FileRun`

SQLAlchemy model for tracking file processing operations.

#### Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | `Integer` | Primary key |
| `file_path` | `String` | Path to processed file |
| `file_size` | `Integer` | File size in bytes |
| `file_hash` | `String` | SHA-256 hash of file |
| `plugin` | `String` | Plugin that processed the file |
| `command` | `String` | Command that was executed |
| `started_at` | `DateTime` | Processing start time |
| `completed_at` | `DateTime` | Processing completion time |
| `status` | `String` | Processing status |
| `output_path` | `String` | Path to output file/directory |
| `items_processed` | `Integer` | Number of items processed |
| `metadata` | `JSON` | Additional metadata |

---

## Configuration System

### Plugin Configuration

Plugins can define custom configuration models by extending `PluginConfigBase`:

```python
from floatctl.plugin_manager import PluginConfigBase
from pydantic import Field

class MyPluginConfig(PluginConfigBase):
    api_key: str = Field(..., description="API key for external service")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Batch processing size")

class MyPlugin(PluginBase):
    config_model = MyPluginConfig
    
    def some_method(self):
        # Access validated configuration
        api_key = self.config.api_key
        timeout = self.config.timeout
```

### Configuration File Format

```json
{
  "db_path": "~/.floatctl/floatctl.db",
  "output_dir": "./output",
  "log_level": "INFO",
  "plugins": {
    "myplugin": {
      "api_key": "your-api-key",
      "timeout": 60,
      "batch_size": 50
    },
    "chroma": {
      "host": "localhost",
      "port": 8000
    }
  }
}
```

---

## Logging and Events

### `floatctl.core.logging.get_logger(name: str) -> structlog.BoundLogger`

Gets a structured logger instance.

**Parameters:**
- `name`: Logger name (usually plugin name)

**Returns:** Configured structlog logger

**Example:**
```python
from floatctl.core.logging import get_logger

logger = get_logger("myplugin")
logger.info("Processing started", file_count=5, format="markdown")
logger.error("Processing failed", error=str(e), file_path=str(path))
```

### `floatctl.core.logging.log_plugin_event(plugin_name: str, event: str) -> structlog.BoundLogger`

Creates a plugin-specific event logger.

**Parameters:**
- `plugin_name`: Name of the plugin
- `event`: Event type/name

**Returns:** Bound logger with plugin context

**Example:**
```python
from floatctl.core.logging import log_plugin_event

logger = log_plugin_event("myplugin", "file_processed")
logger.info("File processed successfully", 
           file_path=str(path), 
           items_extracted=10)
```

---

## Utility Functions

### `floatctl.core.utils.ensure_directory(path: Path) -> Path`

Ensures a directory exists, creating it if necessary.

**Parameters:**
- `path`: Directory path to ensure

**Returns:** The path (for chaining)

### `floatctl.core.utils.safe_filename(name: str) -> str`

Converts a string to a safe filename by removing/replacing invalid characters.

**Parameters:**
- `name`: Original filename

**Returns:** Safe filename string

### `floatctl.core.utils.calculate_file_hash(path: Path) -> str`

Calculates SHA-256 hash of a file.

**Parameters:**
- `path`: Path to file

**Returns:** Hexadecimal hash string

---

## Error Handling

### Common Exceptions

#### `PluginError`
Base exception for plugin-related errors. Use for expected error conditions that users can understand and potentially fix.

#### `ConfigurationError`
Raised when configuration validation fails. Includes details about what configuration is invalid.

#### `DatabaseError`
Raised for database operation failures. Includes context about the failed operation.

### Production-Ready Error Handling Patterns

#### Comprehensive File Processing Example

```python
from floatctl.core.exceptions import PluginError, ConfigurationError, DatabaseError
from floatctl.core.logging import log_plugin_event
from pathlib import Path
from rich.console import Console
import json
import click

def process_conversation_file(self, file_path: Path) -> Optional[ConversationAnalysis]:
    """Process conversation file with comprehensive error handling."""
    logger = log_plugin_event(self.name, "process_conversation")
    console = Console()
    
    try:
        # Input validation
        if not file_path.exists():
            raise FileNotFoundError(f"Conversation file not found: {file_path}")
        
        if not file_path.is_file():
            raise PluginError(f"Path is not a file: {file_path}")
        
        # Size validation
        file_size = file_path.stat().st_size
        if file_size > self.config.max_file_size:
            raise PluginError(
                f"File too large: {file_size:,} bytes "
                f"(max: {self.config.max_file_size:,} bytes)"
            )
        
        if file_size == 0:
            logger.warning("empty_file", file_path=str(file_path))
            return None
        
        # Database operation with retry
        file_run = None
        try:
            file_run = self.db_manager.record_file_run(
                file_path=file_path,
                plugin=self.name,
                command="process",
                metadata={"file_size": file_size}
            )
        except DatabaseError as e:
            logger.error("database_record_failed", error=str(e))
            raise PluginError(f"Failed to record operation in database: {e}")
        
        # File reading with encoding handling
        try:
            with file_path.open('r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            logger.error("encoding_error", file_path=str(file_path), error=str(e))
            # Try alternative encodings
            for encoding in ['latin1', 'cp1252']:
                try:
                    with file_path.open('r', encoding=encoding) as f:
                        content = f.read()
                    logger.info("encoding_fallback", encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise PluginError(f"Cannot decode file {file_path}: {e}")
        
        # JSON parsing with detailed error info
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("json_parse_error", 
                        file_path=str(file_path), 
                        line=e.lineno, 
                        column=e.colno)
            raise PluginError(
                f"Invalid JSON in {file_path} at line {e.lineno}, column {e.colno}: {e.msg}"
            )
        
        # Memory management for large files
        try:
            analysis = self._analyze_conversation_data(data)
        except MemoryError:
            logger.error("memory_exhausted", file_path=str(file_path))
            raise PluginError(
                f"File {file_path} too large to process in available memory. "
                f"Try processing smaller files or increase system memory."
            )
        
        # Success logging
        logger.info("processing_completed", 
                   file_size=file_size,
                   patterns_found=len(analysis.markers) if analysis else 0)
        
        # Complete database operation
        if file_run:
            try:
                self.db_manager.complete_file_run(
                    file_run.id,
                    output_path=self.output_dir,
                    items_processed=1 if analysis else 0
                )
            except DatabaseError as e:
                logger.error("database_complete_failed", error=str(e))
                # Don't fail the operation for database issues
        
        return analysis
        
    except FileNotFoundError as e:
        logger.error("file_not_found", file_path=str(file_path))
        console.print(f"[red]File not found: {file_path}[/red]")
        raise click.ClickException(f"File not found: {file_path}")
        
    except PermissionError as e:
        logger.error("permission_denied", file_path=str(file_path))
        console.print(f"[red]Permission denied: {file_path}[/red]")
        raise click.ClickException(f"Permission denied: {file_path}")
        
    except PluginError as e:
        # PluginError already has user-friendly messages
        logger.error("plugin_error", error=str(e))
        console.print(f"[red]{e}[/red]")
        raise click.ClickException(str(e))
        
    except Exception as e:
        # Unexpected errors - log with full context
        logger.error("unexpected_error", 
                    file_path=str(file_path), 
                    error=str(e), 
                    error_type=type(e).__name__)
        
        # Always complete database operation on failure
        if file_run:
            try:
                self.db_manager.fail_file_run(file_run.id, str(e))
            except DatabaseError:
                pass  # Don't fail on database cleanup errors
        
        console.print(f"[red]Unexpected error processing {file_path}: {e}[/red]")
        raise click.ClickException(f"Unexpected error: {e}")
```

#### Database Operation Error Handling

```python
from floatctl.core.database import DatabaseManager
from floatctl.core.exceptions import DatabaseError

def safe_database_operation(self, operation_name: str, **kwargs):
    """Perform database operation with retry and graceful degradation."""
    logger = log_plugin_event(self.name, f"db_{operation_name}")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if operation_name == "record_file_run":
                return self.db_manager.record_file_run(**kwargs)
            elif operation_name == "complete_file_run":
                return self.db_manager.complete_file_run(**kwargs)
            # Add other operations as needed
            
        except DatabaseError as e:
            logger.warning("database_retry", 
                          attempt=attempt + 1, 
                          max_retries=max_retries,
                          error=str(e))
            
            if attempt == max_retries - 1:
                # Final attempt failed
                logger.error("database_operation_failed", 
                           operation=operation_name,
                           error=str(e))
                
                # Decide whether to fail or continue
                if operation_name in ["record_file_run"]:
                    # Critical operations should fail
                    raise PluginError(f"Database operation failed: {e}")
                else:
                    # Non-critical operations can be skipped
                    logger.warning("database_operation_skipped", operation=operation_name)
                    return None
            
            # Wait before retry (exponential backoff)
            import time
            time.sleep(0.1 * (2 ** attempt))
```

#### Configuration Validation with User-Friendly Messages

```python
from floatctl.core.exceptions import ConfigurationError
from pydantic import Field, validator

class MyPluginConfig(PluginConfigBase):
    api_key: str = Field(..., description="API key for external service")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_file_size: int = Field(default=100_000_000, description="Maximum file size in bytes")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("Timeout must be positive")
        if v > 300:
            raise ValueError("Timeout cannot exceed 5 minutes (300 seconds)")
        return v
    
    @validator('max_file_size')
    def validate_file_size(cls, v):
        if v <= 0:
            raise ValueError("Max file size must be positive")
        if v > 1_000_000_000:  # 1GB
            raise ValueError("Max file size cannot exceed 1GB")
        return v

def load_plugin_config(self, config_dict: Dict[str, Any]) -> MyPluginConfig:
    """Load and validate plugin configuration with helpful error messages."""
    try:
        return MyPluginConfig(**config_dict)
    except ValidationError as e:
        # Convert Pydantic errors to user-friendly messages
        error_messages = []
        for error in e.errors():
            field = error['loc'][0] if error['loc'] else 'unknown'
            message = error['msg']
            error_messages.append(f"  • {field}: {message}")
        
        friendly_message = (
            f"Configuration validation failed for {self.name} plugin:\n" +
            "\n".join(error_messages) +
            f"\n\nExample configuration:\n{self._get_example_config()}"
        )
        
        raise ConfigurationError(friendly_message)

def _get_example_config(self) -> str:
    """Return example configuration for user reference."""
    return '''
{
  "plugins": {
    "my_plugin": {
      "api_key": "your-api-key-here",
      "timeout": 30,
      "max_file_size": 100000000
    }
  }
}'''
```

### Performance Considerations

#### Memory Management
```python
def process_large_file(self, file_path: Path) -> Iterator[ProcessedItem]:
    """Process large files with memory-efficient streaming."""
    try:
        # Check available memory
        import psutil
        available_memory = psutil.virtual_memory().available
        file_size = file_path.stat().st_size
        
        if file_size > available_memory * 0.5:  # Use max 50% of available memory
            logger.warning("large_file_processing", 
                          file_size=file_size,
                          available_memory=available_memory)
            
            # Use streaming approach
            yield from self._process_file_streaming(file_path)
        else:
            # Use in-memory approach for better performance
            yield from self._process_file_memory(file_path)
            
    except Exception as e:
        logger.error("memory_management_error", error=str(e))
        # Fallback to streaming approach
        yield from self._process_file_streaming(file_path)
```

#### Timeout Handling
```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout_context(seconds: int):
    """Context manager for operation timeouts."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def process_with_timeout(self, data: Any) -> ProcessedData:
    """Process data with timeout protection."""
    try:
        with timeout_context(self.config.timeout):
            return self._process_data(data)
    except TimeoutError as e:
        logger.error("processing_timeout", timeout=self.config.timeout)
        raise PluginError(f"Processing timed out after {self.config.timeout} seconds")
```

### Error Recovery Patterns

#### Graceful Degradation
```python
def process_with_fallback(self, input_data: Any) -> ProcessedData:
    """Process data with multiple fallback strategies."""
    strategies = [
        ("primary", self._process_primary),
        ("secondary", self._process_secondary),
        ("minimal", self._process_minimal)
    ]
    
    last_error = None
    for strategy_name, strategy_func in strategies:
        try:
            logger.info("trying_strategy", strategy=strategy_name)
            result = strategy_func(input_data)
            logger.info("strategy_succeeded", strategy=strategy_name)
            return result
        except Exception as e:
            logger.warning("strategy_failed", 
                          strategy=strategy_name, 
                          error=str(e))
            last_error = e
            continue
    
    # All strategies failed
    logger.error("all_strategies_failed", error=str(last_error))
    raise PluginError(f"All processing strategies failed. Last error: {last_error}")
```

---

## Testing Utilities

### `floatctl.testing.plugin_test_utils.PluginTestCase`

Base test case for plugin testing.

```python
from floatctl.testing.plugin_test_utils import PluginTestCase
from my_plugin import MyPlugin

class TestMyPlugin(PluginTestCase):
    def setUp(self):
        self.plugin = MyPlugin()
    
    def test_plugin_registration(self):
        # Test plugin can be registered
        self.assert_plugin_registers(self.plugin)
    
    def test_command_execution(self):
        # Test command execution
        result = self.run_plugin_command(self.plugin, "hello", ["--name", "Test"])
        self.assertIn("Hello, Test!", result.output)
```

---

This API reference provides the foundation for building robust FloatCtl plugins and understanding the core system architecture. For practical examples and tutorials, see the [Plugin Development Guide](development/PLUGIN_DEVELOPMENT_GUIDE.md) and [Getting Started Guide](GETTING_STARTED.md).