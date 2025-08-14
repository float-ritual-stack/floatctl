# ADR-001: Plugin Command Registration Architecture

**Status:** Accepted  
**Date:** 2025-08-08  
**Deciders:** Evan Schultz, Claude (AI Assistant)  

## Context

FloatCtl uses a plugin system to organize CLI commands. The original implementation required all commands to be defined within the `register_commands()` method, creating a "scope trap" where command logic became deeply nested and hard to maintain.

### Problems with Original Nested Approach
- **Deep Nesting**: Commands had to be defined inside `register_commands()` method
- **Poor Testability**: Hard to test individual commands in isolation  
- **IDE Support**: Poor autocomplete and navigation
- **Maintenance**: Adding new commands required modifying the registration method
- **Code Organization**: All command logic crammed into one method

### Attempted Solution: Decorator-Based System
We attempted to implement a decorator-based plugin registration system using `@group()` and `@command()` decorators to mark methods for automatic registration.

**Example of attempted approach:**
```python
class ConversationsPlugin(PluginBase):
    @group()
    @click.pass_context
    def conversations(self, ctx: click.Context) -> None:
        """Manage conversation exports."""
        pass
    
    @command(parent="conversations")
    @click.pass_context
    def split(self, ctx: click.Context, input_file: Path, ...) -> None:
        """Split conversations."""
        config = ctx.obj["config"]  # This failed!
```

### Critical Issues with Decorator Approach
1. **Method Binding vs Click Decorators**: Click's `@click.pass_context` expects unbound functions, but plugin methods are bound to `self`
2. **Parameter Injection Conflicts**: Click calls `method(context, **kwargs)` but bound methods expect `method(self, context, **kwargs)`
3. **Complex Wrapper Logic**: Attempts to create wrappers that handle both `self` and Click's parameter injection led to increasingly complex and fragile code
4. **Context Passing Failures**: The error `'ConversationsPlugin' object has no attribute 'obj'` indicated that the plugin instance was being passed as context instead of the actual Click context

## Decision

**We will revert to and standardize on the nested scope approach** for plugin command registration.

### Rationale
1. **It Works**: The nested approach has proven reliable and stable
2. **Click Compatibility**: Aligns with Click's design patterns and expectations
3. **Simplicity**: Avoids complex wrapper logic and parameter injection issues
4. **Maintainability**: While nested, it's predictable and debuggable
5. **Framework Alignment**: Follows established Click plugin patterns

### Standard Implementation Pattern
```python
class ConversationsPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        """Register conversation commands."""
        
        @cli_group.group()
        @click.pass_context
        def conversations(ctx: click.Context) -> None:
            """Manage conversation exports."""
            pass
        
        @conversations.command()
        @click.argument("input_file", type=click.Path(exists=True, path_type=Path))
        @click.option("--format", "-f", type=click.Choice(["json", "markdown", "both"]))
        @click.pass_context
        def split(ctx: click.Context, input_file: Path, format: str) -> None:
            """Split a conversations export file."""
            config = ctx.obj["config"]  # This works!
            # Implementation can call instance methods
            return self._split_conversations(input_file, format, config)
    
    def _split_conversations(self, input_file: Path, format: str, config) -> None:
        """Actual implementation - easily testable."""
        pass
```

## Consequences

### Positive
- ✅ **Reliable Context Passing**: Click's `@click.pass_context` works correctly
- ✅ **Framework Compatibility**: Aligns with Click's design patterns
- ✅ **Predictable Behavior**: No complex wrapper logic to debug
- ✅ **Testable**: Implementation methods can be tested independently
- ✅ **IDE Support**: Better navigation and autocomplete within nested functions

### Negative
- ❌ **Nested Scope**: Commands are nested inside `register_commands()` method
- ❌ **Code Organization**: Command definitions are not at class level
- ❌ **Repetitive**: Each plugin must implement similar registration patterns

### Mitigation Strategies
1. **Separate Implementation**: Keep command logic in separate methods (e.g., `_split_conversations()`)
2. **Clear Patterns**: Establish consistent patterns for command registration
3. **Documentation**: Provide clear examples and templates
4. **Testing**: Test implementation methods independently of Click integration

## Implementation Notes

### Plugin Manager Changes
The `_wrap_method()` function should not attempt to handle Click decorators:
```python
def _wrap_method(self, method):
    """Wrap plugin method to handle self parameter and Click decorators properly."""
    # For methods with Click decorators, don't wrap them at all
    if hasattr(method, '__click_params__'):
        return method
    
    # For methods without Click decorators, wrap normally
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        return method(*args, **kwargs)
    return wrapper
```

### Entry Points
Plugin entry points should continue to work as before:
```toml
[project.entry-points."floatctl.plugins"]
conversations = "floatctl.plugins.conversations:ConversationsPlugin"
```

## Alternatives Considered

### 1. Entry Point Pattern (click-contrib/click-plugins style)
**Rejected**: Would lose plugin class benefits and make state sharing harder

### 2. Hybrid Approach
**Rejected**: Would create inconsistency and confusion about which pattern to use

### 3. Fix Decorator System
**Rejected**: After extensive debugging, the complexity of making decorators work with Click's parameter injection outweighs the benefits

## Review

**Review Date:** August 2026 (1 year)  
**Review Criteria:** 
- Has the nested approach proven maintainable?
- Have Click framework patterns evolved?
- Are there new solutions to the decorator/binding problem?

## References

- [Click Documentation - Complex Applications](https://click.palletsprojects.com/en/8.1.x/complex/)
- [click-contrib/click-plugins](https://github.com/click-contrib/click-plugins) - Standard plugin patterns
- Original issue: `'ConversationsPlugin' object has no attribute 'obj'`
- Failed decorator implementation commits: `4739aa0` and later
- Working nested implementation: commit `3cc1ddd`

---

**Key Takeaway**: Sometimes the "less elegant" solution that works reliably is better than the "elegant" solution that fights the framework. The nested scope approach aligns with Click's design and avoids complex parameter injection issues.