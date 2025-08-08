# Plugin Development Guide

TODO: Update this guide to reflect the nested scope architecture.

For now, see AGENTS.md for the correct plugin development patterns.

## Quick Reference

The working plugin pattern is:

```python
class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            pass
        
        @myplugin.command()
        def mycommand(ctx: click.Context) -> None:
            pass
```

**All commands must be defined INSIDE the `register_commands()` method.**

See `tests/regression/test_plugin_system_stability.py` for examples that must continue to work.