"""Core REPL functionality for FloatCtl."""

import shlex
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod

import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich import box

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.styles import Style
    REPL_AVAILABLE = True
except ImportError:
    REPL_AVAILABLE = False

console = Console()


class REPLContext:
    """Context object passed to REPL commands."""
    
    def __init__(self, repl):
        self.repl = repl
        self.console = console
        self.state = {}  # Plugin-specific state
        
    def set_prompt(self, prompt: str):
        """Set the prompt for next input."""
        self.repl.custom_prompt = prompt
        
    def get_state(self, key: str, default=None):
        """Get state value."""
        return self.state.get(key, default)
    
    def set_state(self, key: str, value: Any):
        """Set state value."""
        self.state[key] = value


class REPLCommand:
    """Base class for REPL commands."""
    
    def __init__(self, name: str, description: str, handler: Callable):
        self.name = name
        self.description = description
        self.handler = handler
        self.aliases = []
        
    def add_alias(self, alias: str):
        """Add an alias for this command."""
        self.aliases.append(alias)
        return self
        
    def execute(self, ctx: REPLContext, args: List[str]):
        """Execute the command."""
        return self.handler(ctx, args)


class FloatREPL:
    """Core REPL implementation for FloatCtl."""
    
    def __init__(self, name: str = "floatctl"):
        self.name = name
        self.commands = {}
        self.plugins = {}
        self.history_file = Path.home() / '.floatctl' / 'repl_history'
        self.history_file.parent.mkdir(exist_ok=True)
        self.custom_prompt = None
        self.context = REPLContext(self)
        
        # Register core commands
        self._register_core_commands()
        
    def _register_core_commands(self):
        """Register built-in REPL commands."""
        self.register_command('help', 'Show available commands', self._cmd_help)
        self.register_command('exit', 'Exit REPL', self._cmd_exit).add_alias('quit').add_alias('q')
        self.register_command('clear', 'Clear screen', self._cmd_clear)
        self.register_command('plugin', 'Manage plugins', self._cmd_plugin)
        self.register_command('state', 'Show REPL state', self._cmd_state)
        
    def register_command(self, name: str, description: str, handler: Callable) -> REPLCommand:
        """Register a new command."""
        cmd = REPLCommand(name, description, handler)
        self.commands[name] = cmd
        return cmd
        
    def register_plugin(self, name: str, plugin):
        """Register a plugin that provides REPL commands."""
        self.plugins[name] = plugin
        
        # Let plugin register its commands
        if hasattr(plugin, 'register_repl_commands'):
            plugin.register_repl_commands(self)
            
    def get_prompt(self) -> str:
        """Get the current prompt."""
        if self.custom_prompt:
            prompt = self.custom_prompt
            self.custom_prompt = None
            return prompt
            
        # Build prompt from context
        parts = [self.name]
        
        # Add plugin context if any
        active_plugin = self.context.get_state('active_plugin')
        if active_plugin:
            parts.append(f"[{active_plugin}]")
            
        # Add any custom state
        custom_prompt_suffix = self.context.get_state('prompt_suffix')
        if custom_prompt_suffix:
            parts.append(custom_prompt_suffix)
            
        return " ".join(parts) + "> "
        
    def handle_command(self, command_line: str) -> bool:
        """Handle a command line. Returns False to exit."""
        if not command_line.strip():
            return True
            
        parts = shlex.split(command_line.strip())
        cmd_name = parts[0].lower()
        args = parts[1:]
        
        # Check for command or alias
        command = None
        for name, cmd in self.commands.items():
            if name == cmd_name or cmd_name in cmd.aliases:
                command = cmd
                break
                
        if command:
            try:
                result = command.execute(self.context, args)
                if result is False:  # Explicit False means exit
                    return False
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        else:
            # Try plugin-specific parsing
            active_plugin = self.context.get_state('active_plugin')
            if active_plugin and active_plugin in self.plugins:
                plugin = self.plugins[active_plugin]
                if hasattr(plugin, 'handle_repl_command'):
                    if not plugin.handle_repl_command(self.context, cmd_name, args):
                        console.print(f"[red]Unknown command: {cmd_name}[/red]")
            else:
                console.print(f"[red]Unknown command: {cmd_name}[/red]")
                console.print("Type 'help' for available commands")
                
        return True
        
    def _cmd_help(self, ctx: REPLContext, args: List[str]):
        """Show help."""
        console.print("\n[bold cyan]FloatCtl REPL Commands[/bold cyan]\n")
        
        # Core commands
        console.print("[yellow]Core Commands:[/yellow]")
        for name, cmd in sorted(self.commands.items()):
            aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            console.print(f"  {name:<15} {cmd.description}{aliases}")
            
        # Plugin commands
        active_plugin = ctx.get_state('active_plugin')
        if active_plugin and active_plugin in self.plugins:
            plugin = self.plugins[active_plugin]
            if hasattr(plugin, 'get_repl_help'):
                console.print(f"\n[yellow]{active_plugin.title()} Commands:[/yellow]")
                console.print(plugin.get_repl_help())
                
        console.print()
        
    def _cmd_exit(self, ctx: REPLContext, args: List[str]):
        """Exit REPL."""
        return False
        
    def _cmd_clear(self, ctx: REPLContext, args: List[str]):
        """Clear screen."""
        console.clear()
        
    def _cmd_plugin(self, ctx: REPLContext, args: List[str]):
        """Manage plugins."""
        if not args:
            console.print("[yellow]Available plugins:[/yellow]")
            for name in self.plugins:
                active = " (active)" if name == ctx.get_state('active_plugin') else ""
                console.print(f"  {name}{active}")
        elif args[0] == 'use':
            if len(args) > 1 and args[1] in self.plugins:
                ctx.set_state('active_plugin', args[1])
                console.print(f"[green]Switched to {args[1]} plugin[/green]")
            else:
                console.print("[red]Unknown plugin[/red]")
        else:
            console.print("Usage: plugin [use <name>]")
            
    def _cmd_state(self, ctx: REPLContext, args: List[str]):
        """Show REPL state."""
        console.print("\n[bold]REPL State:[/bold]")
        for key, value in ctx.state.items():
            console.print(f"  {key}: {value}")
        console.print()
        
    def run(self):
        """Run the REPL."""
        if not REPL_AVAILABLE:
            console.print("[red]REPL mode requires prompt-toolkit:[/red]")
            console.print("  pip install prompt-toolkit")
            return
            
        console.print(Panel(
            f"[bold green]🌲 {self.name.title()} Interactive Shell[/bold green]\n\n"
            "Type [cyan]help[/cyan] for commands, [cyan]exit[/cyan] to quit\n"
            "Use [cyan]Tab[/cyan] for completion, [cyan]↑/↓[/cyan] for history",
            box=box.DOUBLE
        ))
        
        # Create prompt session
        session = PromptSession(
            history=FileHistory(str(self.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            # TODO: Add completer based on available commands
        )
        
        style = Style.from_dict({
            'prompt': '#00aa00 bold',
        })
        
        # REPL loop
        while True:
            try:
                command = session.prompt(
                    HTML(f'<prompt>{self.get_prompt()}</prompt>'),
                    style=style
                )
                
                if not self.handle_command(command):
                    break
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                
        console.print("\n[green]Goodbye! 🌲[/green]")


class REPLPlugin(ABC):
    """Base class for plugins that provide REPL functionality."""
    
    @abstractmethod
    def register_repl_commands(self, repl: FloatREPL):
        """Register commands with the REPL."""
        pass
        
    def handle_repl_command(self, ctx: REPLContext, cmd: str, args: List[str]) -> bool:
        """Handle plugin-specific commands. Return True if handled."""
        return False
        
    def get_repl_help(self) -> str:
        """Return help text for plugin commands."""
        return ""