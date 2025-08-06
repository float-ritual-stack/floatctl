# AGENTS.md - FloatCtl Development Guide

## Build & Test Commands
```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/unit/test_structlog.py

# Run specific test
uv run pytest tests/integration/test_cli.py::test_specific_function -v

# Type checking
uv run mypy src/

# Linting & formatting
uv run ruff check src/
uv run ruff format src/

# Coverage
uv run pytest --cov=floatctl --cov-report=html
```

## Code Style Guidelines
- **Imports**: Standard library first, third-party, then local imports with blank lines between groups
- **Types**: Use type hints everywhere, import from `typing` for Python <3.9 compatibility
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Docstrings**: Use triple quotes with brief description, Args/Returns sections for complex functions
- **Error handling**: Use specific exceptions, log errors with structlog, include context
- **Plugin architecture**: Inherit from `PluginBase`, implement `register_commands()` method
- **Rich output**: Use rich-click for CLI, Rich Console for formatted output, avoid plain print()
- **Database**: Use SQLAlchemy models, track operations in DatabaseManager
- **Config**: Use Pydantic models with Field() descriptions and validators

## 🚨 CRITICAL: Plugin Development Rules

### Plugin Command Registration
**EVERY command MUST be defined INSIDE the `register_commands()` method!**

❌ **WRONG** (Commands outside method):
```python
class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            pass
        
        @myplugin.command()
        def first_command(ctx: click.Context) -> None:
            pass
    
    # ❌ This command is OUTSIDE register_commands() - will NOT work!
    @myplugin.command()
    def broken_command(ctx: click.Context) -> None:
        pass
```

✅ **CORRECT** (All commands inside method):
```python
class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            pass
        
        @myplugin.command()
        def first_command(ctx: click.Context) -> None:
            pass
        
        # ✅ All commands inside register_commands()
        @myplugin.command()
        def second_command(ctx: click.Context) -> None:
            pass
```

### Plugin Registration Checklist
1. **Class inherits from `PluginBase`**
2. **All commands inside `register_commands()` method**
3. **Entry point added to `pyproject.toml`**:
   ```toml
   [project.entry-points."floatctl.plugins"]
   myplugin = "floatctl.plugins.myplugin:MyPlugin"
   ```
4. **Test registration**: `uv run floatctl --help | grep myplugin`
5. **Test commands**: `uv run floatctl myplugin --help`

### Quick Plugin Template
```python
from floatctl.plugin_manager import PluginBase
import rich_click as click
from rich.console import Console

class MyPlugin(PluginBase):
    name = "myplugin"
    description = "Plugin description"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        @click.pass_context
        def myplugin(ctx: click.Context) -> None:
            """Plugin commands."""
            pass
        
        # ALL commands must be defined HERE
        @myplugin.command()
        @click.pass_context
        def subcommand(ctx: click.Context) -> None:
            """Subcommand description."""
            Console().print("[green]Command executed![/green]")
```

**📖 Plugin Development Documentation:**
- `PLUGIN_DEVELOPMENT_GUIDE.md` - Complete plugin development guide with templates
- `PLUGIN_TROUBLESHOOTING.md` - Common issues and quick fixes
- **Most common issue**: Commands defined outside `register_commands()` method won't work!

### 🚀 Quick Start: Use Plugin Scaffolding
```bash
# Generate a working plugin automatically
floatctl dev scaffold my_plugin --output-dir ./plugins

# Interactive mode with prompts  
floatctl dev scaffold my_plugin --interactive
```
**This creates a complete plugin with proper structure and avoids common mistakes!**