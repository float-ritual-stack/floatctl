# Plugin Registration System - Architecture Decision

## Final Decision: Nested Scope Pattern

**As of August 2025, we use the NESTED SCOPE pattern for plugin registration.**

## Why We Reverted from Decorators

After implementing decorator-based registration (commit `4739aa0`), we discovered fundamental incompatibilities with Click's context injection system. 

**The decorator approach was reverted because:**
- ❌ Broke Click context passing (`'ConversationsPlugin' object has no attribute 'obj'`)
- ❌ Complex debugging and error handling
- ❌ Confusing for both humans and LLMs

## Current Working Pattern

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

## Regression Protection

This decision is protected by `tests/regression/test_plugin_system_stability.py`.

**Any change that breaks these tests must be reverted immediately.**

## References

- See AGENTS.md for current development guidelines
- Use `floatctl dev scaffold` to generate correct patterns
- Commit `3cc1ddd` contains the working implementation