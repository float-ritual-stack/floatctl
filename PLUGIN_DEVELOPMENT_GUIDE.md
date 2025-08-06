# FloatCtl Plugin Development Guide

## 🚨 CRITICAL: Plugin Command Registration

**EVERY command MUST be defined INSIDE the `register_commands()` method with proper indentation!**

### ❌ Common Mistake (Commands Outside Method)
```python
class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            """My plugin commands."""
            pass
        
        @myplugin.command()
        def first_command(ctx: click.Context) -> None:
            """First command."""
            pass
    
    # ❌ WRONG: This command is OUTSIDE register_commands()
    @myplugin.command()  # This will NOT work!
    def second_command(ctx: click.Context) -> None:
        """This command will never be registered!"""
        pass
```

### ✅ Correct Structure (All Commands Inside Method)
```python
class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            """My plugin commands."""
            pass
        
        @myplugin.command()
        def first_command(ctx: click.Context) -> None:
            """First command."""
            pass
        
        # ✅ CORRECT: All commands inside register_commands()
        @myplugin.command()
        def second_command(ctx: click.Context) -> None:
            """This command will be registered!"""
            pass
        
        @myplugin.command()
        def third_command(ctx: click.Context) -> None:
            """Another command."""
            pass
```

## Quick Start: Plugin Scaffolding

**🚀 Use the built-in scaffolding tool to generate a working plugin:**

```bash
# Generate a basic plugin
floatctl dev scaffold my_plugin --output-dir ./plugins

# Interactive mode with prompts
floatctl dev scaffold my_plugin --interactive

# Generate a middleware-style plugin
floatctl dev scaffold my_plugin --middleware
```

This creates a complete plugin structure with:
- ✅ Proper `register_commands()` method structure
- ✅ Working plugin class that inherits from `PluginBase`
- ✅ Example commands with proper decorators
- ✅ `pyproject.toml` with correct entry points
- ✅ Tests and documentation templates

### Available Templates

```bash
# List available templates
floatctl dev list-templates

# Available templates:
# • basic: Basic CLI plugin with commands
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
# • Command registration
# • Entry point configuration
# • Import paths
# • Common mistakes
```

## Plugin Development Checklist

### 1. Plugin Class Structure
```python
from floatctl.plugin_manager import PluginBase
import rich_click as click
from rich.console import Console

class MyPlugin(PluginBase):
    """Plugin description."""
    
    name = "myplugin"
    description = "Brief description of what this plugin does"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register all plugin commands HERE."""
        
        @cli_group.group()
        @click.pass_context
        def myplugin(ctx: click.Context) -> None:
            """Plugin command group description."""
            pass
        
        # ALL commands must be defined HERE, inside this method
        @myplugin.command()
        @click.option("--option", help="Option description")
        @click.pass_context
        def subcommand(ctx: click.Context, option: str) -> None:
            """Subcommand description."""
            console = Console()
            console.print(f"[green]Running subcommand with option: {option}[/green]")
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
├── myplugin.py          # Your plugin file
└── myplugin/            # Optional: complex plugins can use directories
    ├── __init__.py
    ├── plugin.py        # Main plugin class
    ├── commands.py      # Command implementations
    └── CLAUDE.md        # Plugin-specific documentation
```

### 4. Testing Plugin Registration
```bash
# Test that your plugin is registered
uv run floatctl --help | grep myplugin

# Test plugin commands
uv run floatctl myplugin --help

# Test completion
env COMP_WORDS="floatctl myplugin " COMP_CWORD=2 _FLOATCTL_COMPLETE=zsh_complete uv run floatctl
```

## Common Plugin Patterns

### Database Integration
```python
from floatctl.core.database import DatabaseManager

class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            pass
        
        @myplugin.command()
        @click.pass_context
        def db_command(ctx: click.Context) -> None:
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            # Use db_manager for database operations
```

### Rich Output
```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            pass
        
        @myplugin.command()
        def rich_output(ctx: click.Context) -> None:
            console = Console()
            
            # Table output
            table = Table(title="My Data")
            table.add_column("Name", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Item 1", "Value 1")
            console.print(table)
            
            # Panel output
            console.print(Panel("Important message", title="Info"))
```

### Progress Bars
```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            pass
        
        @myplugin.command()
        def long_operation(ctx: click.Context) -> None:
            console = Console()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Processing...", total=100)
                
                for i in range(100):
                    # Do work
                    progress.update(task, advance=1)
```

## Debugging Plugin Issues

### 1. Plugin Not Showing in Help
- Check `pyproject.toml` entry point registration
- Verify plugin class inherits from `PluginBase`
- Check for syntax errors in plugin file

### 2. Commands Not Showing
- **Most common**: Commands defined outside `register_commands()` method
- Check indentation - all commands must be inside the method
- Verify `@cli_group.group()` decorator is used

### 3. Completion Not Working
- Run completion test: `_FLOATCTL_COMPLETE=zsh_source uv run floatctl`
- Check if commands appear in help: `uv run floatctl myplugin --help`
- Verify plugin is registered: `uv run floatctl --help`

### 4. Import Errors
- Check import paths in `pyproject.toml`
- Verify all dependencies are installed
- Check for circular imports

## Plugin Templates

### Simple Plugin Template
```python
"""Simple plugin template."""

import rich_click as click
from rich.console import Console
from floatctl.plugin_manager import PluginBase

console = Console()

class SimplePlugin(PluginBase):
    """Simple plugin template."""
    
    name = "simple"
    description = "A simple plugin template"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register all commands inside this method."""
        
        @cli_group.group()
        @click.pass_context
        def simple(ctx: click.Context) -> None:
            """Simple plugin commands."""
            pass
        
        @simple.command()
        @click.option("--name", default="World", help="Name to greet")
        @click.pass_context
        def hello(ctx: click.Context, name: str) -> None:
            """Say hello."""
            console.print(f"[green]Hello, {name}![/green]")
        
        @simple.command()
        @click.argument("message", type=str)
        @click.pass_context
        def echo(ctx: click.Context, message: str) -> None:
            """Echo a message."""
            console.print(f"[cyan]Echo: {message}[/cyan]")
```

### Complex Plugin Template
```python
"""Complex plugin template with database integration."""

import rich_click as click
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional

from floatctl.plugin_manager import PluginBase
from floatctl.core.database import DatabaseManager
from floatctl.core.logging import log_command

console = Console()

class ComplexPlugin(PluginBase):
    """Complex plugin with database integration."""
    
    name = "complex"
    description = "A complex plugin template with database integration"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register all commands inside this method."""
        
        @cli_group.group()
        @click.pass_context
        def complex(ctx: click.Context) -> None:
            """Complex plugin commands."""
            pass
        
        @complex.command()
        @click.argument("input_file", type=click.Path(exists=True, path_type=Path))
        @click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file")
        @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
        @click.pass_context
        def process(
            ctx: click.Context,
            input_file: Path,
            output: Optional[Path],
            verbose: bool,
        ) -> None:
            """Process a file with database tracking."""
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
                # Your processing logic here
                console.print(f"[green]Processing {input_file}...[/green]")
                
                # Example: Record file run
                file_run = db_manager.record_file_run(
                    input_file,
                    plugin=self.name,
                    command="process",
                    metadata={"verbose": verbose},
                )
                
                # Your actual processing...
                
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
        
        @complex.command()
        @click.pass_context
        def status(ctx: click.Context) -> None:
            """Show processing status."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            
            # Example: Show recent file runs
            table = Table(title="Recent Processing")
            table.add_column("File", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Date", style="dim")
            
            # Add your status logic here
            table.add_row("example.txt", "completed", "2025-08-05")
            
            console.print(table)
```

## 🎯 Key Takeaways

1. **ALL commands must be inside `register_commands()` method**
2. **Check indentation carefully** - Python is sensitive to whitespace
3. **Add entry point to `pyproject.toml`**
4. **Test plugin registration with `--help`**
5. **Use Rich for beautiful CLI output**
6. **Follow the existing plugin patterns**

This guide should prevent the common "commands not showing up" issue that happens when commands are defined outside the `register_commands()` method!