# FloatCtl Plugin Troubleshooting

## 🚨 Most Common Issues

### 1. Commands Not Showing in Help

**Symptom**: `uv run floatctl myplugin --help` shows no subcommands

**Cause**: Commands defined outside `register_commands()` method

**Fix**: Move ALL commands inside the method:

```python
class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            pass
        
        # ✅ ALL commands must be HERE, inside register_commands()
        @myplugin.command()
        def my_command(ctx: click.Context) -> None:
            pass
```

### 2. Plugin Not Showing in Main Help

**Symptom**: `uv run floatctl --help` doesn't show your plugin

**Causes & Fixes**:

1. **Missing entry point** - Add to `pyproject.toml`:
   ```toml
   [project.entry-points."floatctl.plugins"]
   myplugin = "floatctl.plugins.myplugin:MyPlugin"
   ```

2. **Wrong class name** - Check import path matches actual class name

3. **Syntax error** - Check plugin file for Python syntax errors

4. **Missing PluginBase inheritance**:
   ```python
   from floatctl.plugin_manager import PluginBase
   
   class MyPlugin(PluginBase):  # Must inherit from PluginBase
   ```

### 3. Completion Not Working

**Symptom**: Tab completion doesn't show plugin commands

**Fixes**:

1. **Check plugin registration**: `uv run floatctl --help | grep myplugin`
2. **Test completion generation**: `_FLOATCTL_COMPLETE=zsh_source uv run floatctl`
3. **Reload completion**: `source ~/.config/floatctl/floatctl-complete.sh`

### 4. Import Errors

**Symptom**: `ModuleNotFoundError` when loading plugin

**Fixes**:

1. **Check file location**: Plugin file must be in `src/floatctl/plugins/`
2. **Check import path**: Entry point path must match file structure
3. **Missing dependencies**: Install required packages with `uv add package_name`

## Quick Diagnostic Commands

```bash
# 1. Check if plugin is registered
uv run floatctl --help | grep myplugin

# 2. Check plugin commands
uv run floatctl myplugin --help

# 3. Test completion
env COMP_WORDS="floatctl myplugin " COMP_CWORD=2 _FLOATCTL_COMPLETE=zsh_complete uv run floatctl

# 4. Check entry points
python -c "import pkg_resources; print([ep.name for ep in pkg_resources.iter_entry_points('floatctl.plugins')])"

# 5. Test plugin import
python -c "from floatctl.plugins.myplugin import MyPlugin; print('Import successful')"
```

## Plugin Development Workflow

1. **Create plugin file**: `src/floatctl/plugins/myplugin.py`
2. **Add entry point**: Edit `pyproject.toml`
3. **Test registration**: `uv run floatctl --help`
4. **Test commands**: `uv run floatctl myplugin --help`
5. **Test completion**: Tab completion test
6. **Debug issues**: Use diagnostic commands above

## Common Patterns That Work

### Simple Command Plugin
```python
from floatctl.plugin_manager import PluginBase
import rich_click as click
from rich.console import Console

class SimplePlugin(PluginBase):
    name = "simple"
    description = "Simple plugin"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        @click.pass_context
        def simple(ctx: click.Context) -> None:
            """Simple commands."""
            pass
        
        @simple.command()
        @click.pass_context
        def hello(ctx: click.Context) -> None:
            """Say hello."""
            Console().print("[green]Hello![/green]")
```

### Database Integration Plugin
```python
from floatctl.plugin_manager import PluginBase
from floatctl.core.database import DatabaseManager
import rich_click as click

class DatabasePlugin(PluginBase):
    name = "dbplugin"
    description = "Database plugin"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        @click.pass_context
        def dbplugin(ctx: click.Context) -> None:
            """Database commands."""
            pass
        
        @dbplugin.command()
        @click.pass_context
        def status(ctx: click.Context) -> None:
            """Show database status."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            # Use db_manager here
```

## When All Else Fails

1. **Check existing plugins** - Look at `src/floatctl/plugins/conversations.py` for working examples
2. **Start simple** - Create minimal plugin first, then add complexity
3. **Check indentation** - Python is whitespace-sensitive
4. **Restart terminal** - Sometimes needed for completion updates
5. **Check logs** - Look for error messages in terminal output

## Success Indicators

✅ **Plugin registered**: Shows in `floatctl --help`  
✅ **Commands work**: `floatctl myplugin --help` shows subcommands  
✅ **Completion works**: Tab completion shows plugin and subcommands  
✅ **No import errors**: Plugin loads without Python errors