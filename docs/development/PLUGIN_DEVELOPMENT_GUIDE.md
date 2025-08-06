# FloatCtl Plugin Development Guide

## 🚀 New Decorator-Based Plugin System

**FloatCtl now supports a modern decorator-based approach for plugin development!** This is the recommended way to create new plugins.

### ✅ Modern Decorator Approach (Recommended)
```python
from floatctl.plugin_manager import PluginBase, command, group, option, argument
from rich.console import Console

class MyPlugin(PluginBase):
    name = "myplugin"
    description = "Example plugin using decorators"
    version = "1.0.0"
    
    @group()
    def myplugin(self) -> None:
        """My plugin commands."""
        pass
    
    @command(parent="myplugin")
    @option("--verbose", is_flag=True, help="Enable verbose output")
    def hello(self, verbose: bool = False) -> None:
        """Say hello to the world."""
        console = Console()
        if verbose:
            console.print("[green]Hello, World! (verbose mode)[/green]")
        else:
            console.print("[green]Hello, World![/green]")
    
    @command(parent="myplugin")
    @argument("message", type=str)
    @option("--repeat", "-r", default=1, help="Number of times to repeat")
    def echo(self, message: str, repeat: int = 1) -> None:
        """Echo a message multiple times."""
        console = Console()
        for i in range(repeat):
            console.print(f"[cyan]{i+1}: {message}[/cyan]")
```

### 🎯 Key Benefits of Decorator System
- **Clean and intuitive**: Commands are defined as regular methods
- **Type safety**: Full type hints support with proper IDE completion
- **No nested functions**: Eliminates the complex nested structure
- **Self parameter**: Methods have access to `self` naturally
- **Automatic registration**: Commands are discovered and registered automatically
- **Backward compatible**: Existing plugins continue to work unchanged

## Quick Start: Plugin Scaffolding

**🚀 Use the built-in scaffolding tool to generate a working plugin with the new decorator system:**

```bash
# Generate a modern decorator-based plugin
floatctl dev scaffold my_plugin --output-dir ./plugins

# Interactive mode with prompts (uses decorators by default)
floatctl dev scaffold my_plugin --interactive

# Generate a legacy-style plugin (for compatibility)
floatctl dev scaffold my_plugin --legacy

# Generate a middleware-style plugin
floatctl dev scaffold my_plugin --middleware
```

This creates a complete plugin structure with:
- ✅ Modern decorator-based command registration
- ✅ Working plugin class that inherits from `PluginBase`
- ✅ Type-safe method signatures with proper IDE support
- ✅ `pyproject.toml` with correct entry points
- ✅ Tests and documentation templates

### Available Templates

```bash
# List available templates
floatctl dev list-templates

# Available templates:
# • basic: Modern decorator-based CLI plugin (default)
# • legacy: Traditional nested command structure
# • middleware: Middleware plugin for data processing pipelines  
# • service: Service plugin that provides functionality to other plugins
# • event: Event-driven plugin that responds to system events
```

### Plugin Validation

```bash
# Validate plugin structure and implementation
floatctl dev validate /path/to/your/plugin

# This checks:
# • Plugin class structure
# • Command registration (both decorator and legacy styles)
# • Entry point configuration
# • Import paths
# • Common mistakes
# • Decorator usage patterns
```

## Plugin Development Checklist

### 1. Modern Plugin Class Structure (Recommended)
```python
from floatctl.plugin_manager import PluginBase, command, group, option, argument
from rich.console import Console

class MyPlugin(PluginBase):
    """Plugin description."""
    
    name = "myplugin"
    description = "Brief description of what this plugin does"
    version = "1.0.0"
    
    @group()
    def myplugin(self) -> None:
        """Plugin command group description."""
        pass
    
    @command(parent="myplugin")
    @option("--option", help="Option description")
    def subcommand(self, option: str = None) -> None:
        """Subcommand description."""
        console = Console()
        console.print(f"[green]Running subcommand with option: {option}[/green]")
    
    @command(parent="myplugin")
    @argument("filename", type=str)
    @option("--format", "-f", default="json", help="Output format")
    def process(self, filename: str, format: str = "json") -> None:
        """Process a file with the specified format."""
        console = Console()
        console.print(f"[blue]Processing {filename} as {format}[/blue]")
```

### Available Decorators

#### `@group(name=None, help=None, **kwargs)`
Creates a command group (equivalent to Click's `@cli.group()`):
```python
@group()  # Uses method name as group name
def mygroup(self) -> None:
    """Group description."""
    pass

@group(name="custom-name", help="Custom help text")
def mygroup(self) -> None:
    pass
```

#### `@command(name=None, parent=None, help=None, **kwargs)`
Creates a command within a group:
```python
@command()  # Command at root level
def rootcmd(self) -> None:
    pass

@command(parent="mygroup")  # Command under a group
def subcmd(self) -> None:
    pass

@command(name="custom-name", parent="mygroup", help="Custom help")
def subcmd(self) -> None:
    pass
```

#### `@option(*args, **kwargs)` and `@argument(*args, **kwargs)`
Add Click options and arguments (same syntax as Click):
```python
@command(parent="mygroup")
@option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@option("--count", "-c", default=1, type=int, help="Number of iterations")
@argument("filename", type=click.Path(exists=True))
def process_file(self, filename: str, verbose: bool = False, count: int = 1) -> None:
    """Process a file with options."""
    pass
```

### 2. Entry Point Registration
Add your plugin to `pyproject.toml`:
```toml
[project.entry-points."floatctl.plugins"]
myplugin = "floatctl.plugins.myplugin:MyPlugin"
```

### 3. File Structure
```
src/floatctl/plugins/
├── myplugin.py          # Your plugin file (decorator-based)
└── myplugin/            # Optional: complex plugins can use directories
    ├── __init__.py
    ├── plugin.py        # Main plugin class
    ├── commands.py      # Command implementations (can use decorators)
    └── CLAUDE.md        # Plugin-specific documentation
```

### 4. Testing Plugin Registration
```bash
# Test that your plugin is registered
uv run floatctl --help | grep myplugin

# Test plugin commands
uv run floatctl myplugin --help

# Test specific commands
uv run floatctl myplugin subcommand --help

# Test completion
env COMP_WORDS="floatctl myplugin " COMP_CWORD=2 _FLOATCTL_COMPLETE=zsh_complete uv run floatctl
```

## Decorator System Examples

### Simple Plugin with Multiple Commands
```python
from floatctl.plugin_manager import PluginBase, command, group, option, argument
from rich.console import Console
from pathlib import Path

class FileToolsPlugin(PluginBase):
    name = "filetools"
    description = "File manipulation utilities"
    version = "1.0.0"
    
    @group()
    def filetools(self) -> None:
        """File manipulation commands."""
        pass
    
    @command(parent="filetools")
    @argument("path", type=click.Path(path_type=Path))
    @option("--recursive", "-r", is_flag=True, help="List recursively")
    def list(self, path: Path, recursive: bool = False) -> None:
        """List files in a directory."""
        console = Console()
        if recursive:
            console.print(f"[blue]Listing {path} recursively...[/blue]")
        else:
            console.print(f"[blue]Listing {path}...[/blue]")
    
    @command(parent="filetools")
    @argument("source", type=click.Path(exists=True, path_type=Path))
    @argument("dest", type=click.Path(path_type=Path))
    @option("--force", is_flag=True, help="Overwrite existing files")
    def copy(self, source: Path, dest: Path, force: bool = False) -> None:
        """Copy files or directories."""
        console = Console()
        console.print(f"[green]Copying {source} to {dest}[/green]")
        if force:
            console.print("[yellow]Force mode enabled[/yellow]")
```

### Plugin with Root-Level Commands
```python
class UtilsPlugin(PluginBase):
    name = "utils"
    description = "General utilities"
    version = "1.0.0"
    
    @command()  # Root-level command
    @argument("text", type=str)
    def echo(self, text: str) -> None:
        """Echo text to console."""
        console = Console()
        console.print(f"[cyan]{text}[/cyan]")
    
    @command()  # Another root-level command
    @option("--format", "-f", default="iso", help="Date format")
    def now(self, format: str = "iso") -> None:
        """Show current time."""
        from datetime import datetime
        console = Console()
        if format == "iso":
            console.print(datetime.now().isoformat())
        else:
            console.print(datetime.now().strftime(format))
```

## Common Plugin Patterns

### Database Integration
```python
from floatctl.plugin_manager import PluginBase, command, group, option
from floatctl.core.database import DatabaseManager
from rich.console import Console
import rich_click as click

class DatabasePlugin(PluginBase):
    name = "dbtools"
    description = "Database utilities"
    version = "1.0.0"
    
    @group()
    def dbtools(self) -> None:
        """Database management commands."""
        pass
    
    @command(parent="dbtools")
    @option("--table", "-t", help="Specific table to query")
    def status(self, table: str = None) -> None:
        """Show database status."""
        # Access config through Click context if needed
        # Or use dependency injection through plugin manager
        console = Console()
        console.print(f"[blue]Checking database status for table: {table or 'all'}[/blue]")
        
        # Example: Get config from plugin manager or context
        # config = self.get_service("config")
        # db_manager = DatabaseManager(config.db_path)
```

### Rich Output with Tables and Panels
```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import time

class DisplayPlugin(PluginBase):
    name = "display"
    description = "Rich display utilities"
    version = "1.0.0"
    
    @group()
    def display(self) -> None:
        """Display and formatting commands."""
        pass
    
    @command(parent="display")
    @option("--title", default="Data Table", help="Table title")
    def table(self, title: str = "Data Table") -> None:
        """Display a sample table."""
        console = Console()
        
        table = Table(title=title)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Status", justify="center", style="red")
        
        table.add_row("Item 1", "Value 1", "✓")
        table.add_row("Item 2", "Value 2", "✗")
        table.add_row("Item 3", "Value 3", "⚠")
        
        console.print(table)
    
    @command(parent="display")
    @argument("message", type=str)
    @option("--style", default="info", help="Panel style")
    def panel(self, message: str, style: str = "info") -> None:
        """Display a message in a panel."""
        console = Console()
        
        styles = {
            "info": ("blue", "Info"),
            "warning": ("yellow", "Warning"),
            "error": ("red", "Error"),
            "success": ("green", "Success")
        }
        
        color, title = styles.get(style, ("blue", "Info"))
        console.print(Panel(message, title=title, border_style=color))
    
    @command(parent="display")
    @option("--duration", "-d", default=5, type=int, help="Progress duration")
    def progress(self, duration: int = 5) -> None:
        """Show a progress bar."""
        console = Console()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing...", total=duration * 10)
            
            for i in range(duration * 10):
                time.sleep(0.1)
                progress.update(task, advance=1)
            
            console.print("[green]✓ Complete![/green]")
```

### Context and Configuration Access
```python
import rich_click as click
from floatctl.plugin_manager import PluginBase, command, group, option

class ConfigPlugin(PluginBase):
    name = "config"
    description = "Configuration utilities"
    version = "1.0.0"
    
    @group()
    def config(self) -> None:
        """Configuration management."""
        pass
    
    @command(parent="config")
    @click.pass_context
    def show(self, ctx: click.Context) -> None:
        """Show current configuration."""
        console = Console()
        
        # Access the global config through Click context
        config = ctx.obj.get("config")
        if config:
            console.print(f"[blue]Config path: {config.config_path}[/blue]")
            console.print(f"[blue]Database path: {config.db_path}[/blue]")
        else:
            console.print("[red]No configuration available[/red]")
    
    @command(parent="config")
    def plugin_config(self) -> None:
        """Show this plugin's configuration."""
        console = Console()
        console.print(f"[green]Plugin: {self.name}[/green]")
        console.print(f"[green]Version: {self.version}[/green]")
        console.print(f"[green]Config: {self.config.dict()}[/green]")
```

## Migration from Legacy to Decorator System

### Converting Existing Plugins

**Old Legacy Style:**
```python
class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        @click.pass_context
        def myplugin(ctx: click.Context) -> None:
            """My plugin commands."""
            pass
        
        @myplugin.command()
        @click.option("--verbose", is_flag=True)
        @click.pass_context
        def hello(ctx: click.Context, verbose: bool) -> None:
            """Say hello."""
            if verbose:
                print("Hello, World! (verbose)")
            else:
                print("Hello, World!")
```

**New Decorator Style:**
```python
class MyPlugin(PluginBase):
    @group()
    def myplugin(self) -> None:
        """My plugin commands."""
        pass
    
    @command(parent="myplugin")
    @option("--verbose", is_flag=True)
    def hello(self, verbose: bool = False) -> None:
        """Say hello."""
        console = Console()
        if verbose:
            console.print("[green]Hello, World! (verbose)[/green]")
        else:
            console.print("[green]Hello, World![/green]")
```

### Migration Steps
1. **Remove the `register_commands()` method** (unless you need legacy compatibility)
2. **Add `@group()` decorator** to your main command group method
3. **Add `@command(parent="groupname")` decorators** to your command methods
4. **Remove `@click.pass_context` and `ctx` parameters** (use `self` instead)
5. **Update method signatures** to use proper type hints
6. **Replace `print()` with Rich Console** for better output

### Backward Compatibility

**The decorator system is fully backward compatible!** Existing plugins using the legacy `register_commands()` method will continue to work without changes. The system automatically detects which approach your plugin uses:

- **If decorators are found**: Uses the new decorator system
- **If no decorators**: Falls back to calling your `register_commands()` method

You can even mix both approaches in the same plugin if needed during migration.

## Debugging Plugin Issues

### 1. Plugin Not Showing in Help
- Check `pyproject.toml` entry point registration
- Verify plugin class inherits from `PluginBase`
- Check for syntax errors in plugin file
- Run `floatctl dev validate /path/to/plugin` for detailed diagnostics

### 2. Decorator Commands Not Showing
- **Most common**: Missing `@group()` decorator on the main group method
- Verify `@command(parent="groupname")` matches your group name exactly
- Check that decorators are imported: `from floatctl.plugin_manager import command, group, option, argument`
- Ensure method names don't start with underscore (private methods are ignored)

### 3. Legacy Commands Not Showing
- **Most common**: Commands defined outside `register_commands()` method
- Check indentation - all commands must be inside the method
- Verify `@cli_group.group()` decorator is used
- Make sure the `register_commands()` method is properly defined

### 4. Type Hints and IDE Issues
- Import proper types: `from typing import Optional, List, Dict`
- Use `click.Path` for path parameters: `@argument("file", type=click.Path(exists=True))`
- Method signatures should match decorator parameters exactly

### 5. Completion Not Working
- Run completion test: `_FLOATCTL_COMPLETE=zsh_source uv run floatctl`
- Check if commands appear in help: `uv run floatctl myplugin --help`
- Verify plugin is registered: `uv run floatctl --help`
- For decorator plugins, ensure group and command names are consistent

### 6. Import Errors
- Check import paths in `pyproject.toml`
- Verify all dependencies are installed
- Check for circular imports
- Ensure decorator imports are correct: `from floatctl.plugin_manager import PluginBase, command, group`

## Plugin Templates

### Modern Decorator-Based Template (Recommended)
```python
"""Modern decorator-based plugin template."""

from floatctl.plugin_manager import PluginBase, command, group, option, argument
from rich.console import Console
from pathlib import Path
from typing import Optional
import rich_click as click

class ModernPlugin(PluginBase):
    """Modern plugin using decorator system."""
    
    name = "modern"
    description = "A modern plugin template using decorators"
    version = "1.0.0"
    
    @group()
    def modern(self) -> None:
        """Modern plugin commands."""
        pass
    
    @command(parent="modern")
    @option("--name", default="World", help="Name to greet")
    def hello(self, name: str = "World") -> None:
        """Say hello to someone."""
        console = Console()
        console.print(f"[green]Hello, {name}![/green]")
    
    @command(parent="modern")
    @argument("message", type=str)
    @option("--repeat", "-r", default=1, type=int, help="Number of repetitions")
    def echo(self, message: str, repeat: int = 1) -> None:
        """Echo a message multiple times."""
        console = Console()
        for i in range(repeat):
            console.print(f"[cyan]{i+1}: {message}[/cyan]")
    
    @command(parent="modern")
    @argument("input_file", type=click.Path(exists=True, path_type=Path))
    @option("--output", "-o", type=click.Path(path_type=Path), help="Output file")
    @option("--verbose", "-v", is_flag=True, help="Verbose output")
    def process(self, input_file: Path, output: Optional[Path] = None, verbose: bool = False) -> None:
        """Process a file with optional output."""
        console = Console()
        
        if verbose:
            console.print(f"[blue]Processing {input_file}...[/blue]")
            if output:
                console.print(f"[blue]Output will be saved to {output}[/blue]")
        
        # Your processing logic here
        console.print(f"[green]✓ Processed {input_file}[/green]")
        
        if output:
            console.print(f"[green]✓ Results saved to {output}[/green]")
```

### Complex Plugin with Database Integration
```python
"""Complex plugin template with database integration and advanced features."""

from floatctl.plugin_manager import PluginBase, command, group, option, argument
from floatctl.core.database import DatabaseManager
from floatctl.core.logging import log_command
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from pathlib import Path
from typing import Optional
import rich_click as click
import time

class ComplexPlugin(PluginBase):
    """Complex plugin with database integration."""
    
    name = "complex"
    description = "A complex plugin template with database integration"
    version = "1.0.0"
    
    @group()
    def complex(self) -> None:
        """Complex plugin commands with database integration."""
        pass
    
    @command(parent="complex")
    @argument("input_file", type=click.Path(exists=True, path_type=Path))
    @option("--output", "-o", type=click.Path(path_type=Path), help="Output file")
    @option("--verbose", "-v", is_flag=True, help="Verbose output")
    @click.pass_context
    def process(
        self, 
        ctx: click.Context,
        input_file: Path, 
        output: Optional[Path] = None, 
        verbose: bool = False
    ) -> None:
        """Process a file with database tracking."""
        console = Console()
        config = ctx.obj["config"]
        db_manager = DatabaseManager(config.db_path)
        
        # Create command logger
        cmd_logger = log_command(
            "complex.process",
            {
                "input_file": str(input_file),
                "output": str(output) if output else None,
                "verbose": verbose,
            },
            plugin=self.name,
        )
        
        cmd_logger.info("starting_process")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Processing file...", total=100)
                
                # Example: Record file run
                file_run = db_manager.record_file_run(
                    input_file,
                    plugin=self.name,
                    command="process",
                    metadata={"verbose": verbose},
                )
                
                # Simulate processing with progress
                for i in range(100):
                    time.sleep(0.01)  # Simulate work
                    progress.update(task, advance=1)
                
                # Complete the run
                db_manager.complete_file_run(
                    file_run.id,
                    output_path=output,
                    items_processed=1,
                )
                
                console.print("[green]✓ Processing completed[/green]")
                cmd_logger.info("process_completed")
                
        except Exception as e:
            cmd_logger.error("process_failed", error=str(e))
            console.print(f"[red]Error: {e}[/red]")
            raise click.ClickException(str(e))
    
    @command(parent="complex")
    @click.pass_context
    def status(self, ctx: click.Context) -> None:
        """Show processing status from database."""
        console = Console()
        config = ctx.obj["config"]
        db_manager = DatabaseManager(config.db_path)
        
        # Create status table
        table = Table(title="Recent Processing Status")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Date", style="dim")
        table.add_column("Items", justify="right", style="blue")
        
        # Example: Query recent file runs
        # recent_runs = db_manager.get_recent_file_runs(plugin=self.name, limit=10)
        # for run in recent_runs:
        #     table.add_row(run.input_path, run.status, run.created_at, str(run.items_processed))
        
        # Placeholder data
        table.add_row("example.txt", "completed", "2025-08-06", "42")
        table.add_row("data.json", "processing", "2025-08-06", "0")
        
        console.print(table)
    
    @command(parent="complex")
    @option("--format", "-f", default="table", help="Output format (table, json)")
    def list(self, format: str = "table") -> None:
        """List available data with different output formats."""
        console = Console()
        
        data = [
            {"name": "Item 1", "value": 100, "status": "active"},
            {"name": "Item 2", "value": 200, "status": "inactive"},
            {"name": "Item 3", "value": 150, "status": "active"},
        ]
        
        if format == "json":
            import json
            console.print_json(json.dumps(data, indent=2))
        else:
            table = Table(title="Available Data")
            table.add_column("Name", style="cyan")
            table.add_column("Value", justify="right", style="green")
            table.add_column("Status", style="yellow")
            
            for item in data:
                table.add_row(item["name"], str(item["value"]), item["status"])
            
            console.print(table)
```

### Legacy Plugin Template (For Compatibility)
```python
"""Legacy plugin template for backward compatibility."""

import rich_click as click
from rich.console import Console
from floatctl.plugin_manager import PluginBase

class LegacyPlugin(PluginBase):
    """Legacy plugin using traditional register_commands method."""
    
    name = "legacy"
    description = "A legacy plugin template"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register all commands inside this method (legacy approach)."""
        console = Console()
        
        @cli_group.group()
        @click.pass_context
        def legacy(ctx: click.Context) -> None:
            """Legacy plugin commands."""
            pass
        
        @legacy.command()
        @click.option("--name", default="World", help="Name to greet")
        @click.pass_context
        def hello(ctx: click.Context, name: str) -> None:
            """Say hello."""
            console.print(f"[green]Hello, {name}![/green]")
        
        @legacy.command()
        @click.argument("message", type=str)
        @click.pass_context
        def echo(ctx: click.Context, message: str) -> None:
            """Echo a message."""
            console.print(f"[cyan]Echo: {message}[/cyan]")
```

## 🎯 Key Takeaways

### For New Plugins (Recommended)
1. **Use the decorator system** - `@command`, `@group`, `@option`, `@argument`
2. **Import decorators correctly** - `from floatctl.plugin_manager import PluginBase, command, group, option, argument`
3. **Define methods with proper type hints** - Better IDE support and debugging
4. **Use `self` parameter naturally** - No need for complex context passing
5. **Add entry point to `pyproject.toml`**
6. **Test plugin registration with `--help`**
7. **Use Rich Console for beautiful CLI output**

### For Legacy Plugins (Backward Compatibility)
1. **ALL commands must be inside `register_commands()` method**
2. **Check indentation carefully** - Python is sensitive to whitespace
3. **Use `@click.pass_context` and `ctx` parameters**
4. **Commands defined outside `register_commands()` will NOT work**

### Universal Best Practices
- **Start with scaffolding**: `floatctl dev scaffold my_plugin`
- **Validate your plugin**: `floatctl dev validate /path/to/plugin`
- **Use Rich for output**: Tables, panels, progress bars, and colors
- **Follow type hints**: Better development experience and fewer bugs
- **Test thoroughly**: Check `--help`, command execution, and completion

### Migration Path
- **New plugins**: Use decorator system from the start
- **Existing plugins**: Continue working unchanged, migrate when convenient
- **Mixed approach**: You can use both systems in the same plugin during migration

The decorator system eliminates the most common plugin development issues while providing a cleaner, more maintainable approach to command registration!