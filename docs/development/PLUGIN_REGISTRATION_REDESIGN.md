# Plugin Registration System Redesign

## Problem Statement

The current plugin registration system has a critical architectural flaw that significantly impacts developer experience:

**Current Pattern (Problematic):**
```python
class MyPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def myplugin(ctx: click.Context) -> None:
            pass
        
        # ALL commands must be nested here - creates maintenance nightmare
        @myplugin.command()
        def command1(ctx: click.Context) -> None:
            # 50+ lines of logic here
            pass
        
        @myplugin.command()
        def command2(ctx: click.Context) -> None:
            # Another 50+ lines here
            pass
```

**Issues with Current Approach:**
1. **Deep nesting** - Commands are buried inside methods, making code hard to read
2. **Testing difficulty** - Individual commands can't be easily unit tested
3. **Code organization** - Large plugins become unwieldy with all logic in one method
4. **IDE support** - Poor code completion and navigation
5. **Maintenance burden** - Adding commands requires modifying the registration method

## Proposed Solution: Decorator-Based Registration

### New Architecture

```python
from floatctl.plugin_manager import PluginBase, command, group

class MyPlugin(PluginBase):
    name = "myplugin"
    description = "My plugin description"
    
    @group()
    def myplugin(self, ctx: click.Context) -> None:
        """My plugin commands."""
        pass
    
    @command(parent="myplugin")
    def command1(self, ctx: click.Context) -> None:
        """First command - now easily testable!"""
        pass
    
    @command(parent="myplugin")
    def command2(self, ctx: click.Context) -> None:
        """Second command - clean and maintainable!"""
        pass
```

### Implementation Design

#### 1. Enhanced PluginBase Class

```python
from typing import Dict, List, Tuple, Callable, Any
import functools
import inspect

class PluginBase:
    """Enhanced base class with decorator-based command registration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._command_registry = []
        self._group_registry = []
        self._discover_decorated_commands()
    
    def _discover_decorated_commands(self):
        """Discover all decorated commands and groups in the plugin."""
        for name in dir(self):
            method = getattr(self, name)
            if hasattr(method, '_floatctl_command_info'):
                self._command_registry.append((name, method, method._floatctl_command_info))
            elif hasattr(method, '_floatctl_group_info'):
                self._group_registry.append((name, method, method._floatctl_group_info))
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Auto-register all decorated commands and groups."""
        # Create groups first
        created_groups = {}
        for name, method, group_info in self._group_registry:
            group_name = group_info.get('name', name)
            click_group = cli_group.group(
                name=group_name,
                help=group_info.get('help', method.__doc__),
                **group_info.get('kwargs', {})
            )(self._wrap_method(method))
            created_groups[group_name] = click_group
        
        # Register commands
        for name, method, command_info in self._command_registry:
            parent = command_info.get('parent')
            if parent and parent in created_groups:
                target_group = created_groups[parent]
            else:
                target_group = cli_group
            
            command_name = command_info.get('name', name)
            target_group.command(
                name=command_name,
                help=command_info.get('help', method.__doc__),
                **command_info.get('kwargs', {})
            )(self._wrap_method(method))
    
    def _wrap_method(self, method):
        """Wrap plugin method to handle self parameter."""
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            # Insert self as first parameter
            return method(self, *args, **kwargs)
        return wrapper
```

#### 2. Decorator Functions

```python
def command(name: Optional[str] = None, 
           parent: Optional[str] = None,
           help: Optional[str] = None,
           **kwargs):
    """Decorator to register a plugin command."""
    def decorator(func):
        func._floatctl_command_info = {
            'name': name or func.__name__,
            'parent': parent,
            'help': help or func.__doc__,
            'kwargs': kwargs
        }
        return func
    return decorator

def group(name: Optional[str] = None,
          help: Optional[str] = None,
          **kwargs):
    """Decorator to register a plugin command group."""
    def decorator(func):
        func._floatctl_group_info = {
            'name': name or func.__name__,
            'help': help or func.__doc__,
            'kwargs': kwargs
        }
        return func
    return decorator

# Convenience decorators for common Click options
def option(*args, **kwargs):
    """Decorator to add Click options to commands."""
    def decorator(func):
        return click.option(*args, **kwargs)(func)
    return decorator

def argument(*args, **kwargs):
    """Decorator to add Click arguments to commands."""
    def decorator(func):
        return click.argument(*args, **kwargs)(func)
    return decorator
```

#### 3. Advanced Features

```python
# Support for command dependencies
def requires(*dependencies):
    """Decorator to specify command dependencies."""
    def decorator(func):
        if not hasattr(func, '_floatctl_command_info'):
            func._floatctl_command_info = {}
        func._floatctl_command_info['requires'] = dependencies
        return func
    return decorator

# Support for command categories
def category(name: str):
    """Decorator to categorize commands."""
    def decorator(func):
        if not hasattr(func, '_floatctl_command_info'):
            func._floatctl_command_info = {}
        func._floatctl_command_info['category'] = name
        return func
    return decorator

# Support for async commands
def async_command(*args, **kwargs):
    """Decorator for async commands."""
    def decorator(func):
        func = command(*args, **kwargs)(func)
        func._floatctl_async = True
        return func
    return decorator
```

### Migration Strategy

#### Phase 1: Backward Compatibility
- Keep existing `register_commands` method working
- Add decorator support alongside existing system
- Plugins can use either approach

#### Phase 2: Gradual Migration
- Update plugin scaffolding to use decorators
- Provide migration tools for existing plugins
- Update documentation and examples

#### Phase 3: Deprecation
- Mark old pattern as deprecated
- Provide clear migration path
- Eventually remove old system

### Example: Migrated Plugin

#### Before (Current System)
```python
class ConversationsPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        @click.pass_context
        def conversations(ctx: click.Context) -> None:
            """Manage conversation exports."""
            pass
        
        @conversations.command()
        @click.argument("input_file", type=click.Path(exists=True, path_type=Path))
        @click.option("--output-dir", "-o", type=click.Path(path_type=Path))
        @click.option("--format", "-f", type=click.Choice(["json", "markdown", "both"]))
        @click.pass_context
        def split(ctx, input_file, output_dir, format):
            # 200+ lines of logic here
            pass
```

#### After (Decorator System)
```python
from floatctl.plugin_manager import PluginBase, group, command, option, argument

class ConversationsPlugin(PluginBase):
    name = "conversations"
    description = "Split and process conversation exports"
    
    @group()
    def conversations(self, ctx: click.Context) -> None:
        """Manage conversation exports."""
        pass
    
    @command(parent="conversations")
    @argument("input_file", type=click.Path(exists=True, path_type=Path))
    @option("--output-dir", "-o", type=click.Path(path_type=Path))
    @option("--format", "-f", type=click.Choice(["json", "markdown", "both"]))
    @click.pass_context
    def split(self, ctx: click.Context, input_file: Path, output_dir: Optional[Path], format: str) -> None:
        """Split a conversations export file into individual conversation files."""
        # Same logic, but now easily testable and maintainable
        return self._split_conversations(ctx, input_file, output_dir, format)
    
    def _split_conversations(self, ctx, input_file, output_dir, format):
        """Extracted logic for easy testing."""
        # Implementation here
        pass
```

### Testing Benefits

#### Before (Difficult to Test)
```python
# Can't easily test individual commands
class TestConversationsPlugin(unittest.TestCase):
    def test_split_command(self):
        # Have to mock the entire CLI system
        # Very complex setup required
        pass
```

#### After (Easy to Test)
```python
class TestConversationsPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = ConversationsPlugin()
    
    def test_split_conversations(self):
        # Can test the logic directly
        result = self.plugin._split_conversations(
            mock_ctx, 
            Path("test.json"), 
            Path("output"), 
            "json"
        )
        self.assertIsNotNone(result)
    
    def test_split_command_integration(self):
        # Can test command registration
        from click.testing import CliRunner
        runner = CliRunner()
        
        # Test that command is properly registered
        result = runner.invoke(self.plugin.split, ["test.json"])
        self.assertEqual(result.exit_code, 0)
```

### Performance Impact

- **Minimal overhead** - Decorators are processed once at plugin load time
- **Better memory usage** - Commands aren't recreated on each registration
- **Faster plugin loading** - More efficient command discovery

### Developer Experience Improvements

1. **Better IDE Support**
   - Code completion works properly
   - Easy navigation between commands
   - Proper syntax highlighting

2. **Easier Debugging**
   - Can set breakpoints in individual commands
   - Stack traces are cleaner
   - Better error messages

3. **Improved Maintainability**
   - Commands are self-contained
   - Easy to add/remove commands
   - Clear separation of concerns

4. **Enhanced Testing**
   - Unit test individual commands
   - Mock dependencies easily
   - Integration tests are simpler

### Implementation Timeline

#### Week 1: Core Infrastructure
- Implement enhanced PluginBase class
- Create decorator functions
- Add backward compatibility layer

#### Week 2: Migration Tools
- Create automatic migration script
- Update plugin scaffolding
- Test with existing plugins

#### Week 3: Documentation & Examples
- Update all documentation
- Create migration guide
- Update examples to use new system

#### Week 4: Community Rollout
- Release with backward compatibility
- Gather feedback
- Refine based on usage

### Success Metrics

- **Developer Velocity**: 40% faster plugin development
- **Code Quality**: Reduced complexity, better test coverage
- **Maintainability**: Easier to add/modify commands
- **Community Adoption**: Positive feedback from plugin developers

## Conclusion

This redesign addresses the critical architectural flaw in the current plugin system while maintaining backward compatibility. The decorator-based approach aligns with Python best practices and significantly improves the developer experience.

The migration can be done gradually, allowing existing plugins to continue working while new plugins benefit from the improved architecture. This change will unlock the full potential of FloatCtl's plugin ecosystem and establish it as a best-in-class CLI framework.