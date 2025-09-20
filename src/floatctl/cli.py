"""Main CLI entry point for FloatCtl."""

import os
import sys

# CRITICAL: Monkey-patch structlog BEFORE any other imports if generating completions
if os.environ.get('_FLOATCTL_COMPLETE'):
    import logging
    logging.disable(logging.CRITICAL)
    
    import structlog
    
    # Monkey-patch structlog completely before any floatctl imports
    class NullLogger:
        def debug(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def critical(self, *args, **kwargs): pass
        def bind(self, *args, **kwargs): return self
        def unbind(self, *args, **kwargs): return self
        def new(self, *args, **kwargs): return self
        def __call__(self, *args, **kwargs): return self
    
    # Replace structlog functions entirely
    structlog.get_logger = lambda *args, **kwargs: NullLogger()
    structlog.configure(
        processors=[],
        logger_factory=lambda: NullLogger(),
        cache_logger_on_first_use=False,
    )

# Now safe to import everything else
import json
from pathlib import Path
from typing import Optional

import rich_click as click
import structlog
from rich.console import Console
from rich.panel import Panel

from floatctl import __version__
from floatctl.core.config import Config, load_config
from floatctl.core.logging import setup_logging, setup_quiet_logging
from floatctl.plugin_manager import PluginManager, PluginState

# Configure rich-click for beautiful output
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
click.rich_click.ERRORS_EPILOGUE = "To find out more, visit https://github.com/evanschultz/floatctl"

console = Console()


def show_welcome() -> None:
    """Display welcome message with plugin info."""
    console.print(
        Panel.fit(
            "[bold blue]FloatCtl[/bold blue] - Modern AI Workflow Management\n"
            f"[dim]Version {__version__}[/dim]\n\n"
            "[green]✓[/green] Plugin architecture for extensibility\n"
            "[green]✓[/green] Beautiful terminal output with Rich\n"
            "[green]✓[/green] Fast operations with modern Python tools\n"
            "[green]✓[/green] FLOAT ecosystem integration",
            title="Welcome to FloatCtl",
            border_style="blue",
        )
    )


def create_cli_app() -> click.Group:
    """Factory function to create CLI app with plugins loaded."""
    
    # Create base CLI group
    @click.group(
        name="floatctl",
        context_settings={"help_option_names": ["-h", "--help"]},
        invoke_without_command=True,
    )
    @click.option(
        "--config",
        "-c",
        type=click.Path(exists=True, path_type=Path),
        help="Path to configuration file",
    )
    @click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Enable verbose logging",
    )
    @click.option(
        "--output-dir",
        "-o",
        type=click.Path(path_type=Path),
        help="Default output directory for operations",
    )
    @click.version_option(
        version=__version__,
        prog_name="floatctl",
        message="%(prog)s %(version)s - A modern plugin-based CLI tool for FLOAT workflows",
    )
    @click.pass_context
    def cli(
        ctx: click.Context,
        config: Optional[Path] = None,
        verbose: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        **FloatCtl** - A modern plugin-based CLI tool for managing FLOAT conversation exports and AI workflows.
        
        FloatCtl provides a unified interface for processing Claude conversation exports, extracting artifacts,
        and managing AI workflow data through a powerful plugin architecture.
        
        ## Quick Start
        
        ```bash
        # Split conversations from an export file
        floatctl conversations split conversations.json
        
        # Extract artifacts from conversations
        floatctl artifacts extract --input-dir ./conversations
        
        # Smart export with auto-detection
        floatctl export smart ./data --output ./processed
        ```
        
        ## Configuration
        
        FloatCtl can be configured via:
        - Configuration files (YAML/JSON)
        - Environment variables
        - Command-line options
        
        Run `floatctl config --help` for configuration management commands.
        """
        # Ensure context object exists
        ctx.ensure_object(dict)
        
        # Load configuration
        try:
            ctx.obj["config"] = load_config(config)
        except Exception as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
            sys.exit(1)
        
        # Override config with CLI options
        if verbose:
            ctx.obj["config"].verbose = True
        if output_dir:
            ctx.obj["config"].output_dir = output_dir
        
        # Setup logging (skip if generating completions)
        if not os.environ.get('_FLOATCTL_COMPLETE'):
            setup_logging(ctx.obj["config"])
        
        # Store plugin manager in context (it's already loaded)
        ctx.obj["plugin_manager"] = cli.plugin_manager
        
        # If no command provided, show help (unless generating completions)
        if ctx.invoked_subcommand is None and not os.environ.get('_FLOATCTL_COMPLETE'):
            show_welcome()
            click.echo(ctx.get_help())
    
    # Core command groups
    @cli.group()
    @click.pass_context
    def config(ctx: click.Context) -> None:
        """Configuration management commands."""
        pass
    
    @config.command("show")
    @click.pass_context
    def config_show(ctx: click.Context) -> None:
        """Show current configuration."""
        config_obj: Config = ctx.obj["config"]
        console.print(
            Panel(
                config_obj.model_dump_json(indent=2),
                title="Current Configuration",
                border_style="green",
            )
        )
    
    @config.command("validate")
    @click.pass_context
    def config_validate(ctx: click.Context) -> None:
        """Validate configuration file."""
        config_obj: Config = ctx.obj["config"]
        try:
            Config.model_validate(config_obj.model_dump())
            console.print("[green]✓[/green] Configuration is valid")
        except Exception as e:
            console.print(f"[red]✗[/red] Configuration validation failed: {e}")
            sys.exit(1)
    
    @cli.group()
    @click.pass_context
    def plugin(ctx: click.Context) -> None:
        """Plugin management commands."""
        pass
    
    @plugin.command("list")
    @click.pass_context
    def plugin_list(ctx: click.Context) -> None:
        """List available plugins."""
        pm = ctx.obj.get("plugin_manager")
        if not pm:
            console.print("[red]Plugin manager not initialized[/red]")
            return
            
        console.print("\n[bold]Available Plugins:[/bold]\n")
        
        for plugin_name, plugin_info in pm.plugins.items():
            # Color code by state
            state_colors = {
                "active": "green",
                "loaded": "yellow", 
                "initialized": "blue",
                "error": "red",
                "discovered": "dim",
            }
            state_color = state_colors.get(plugin_info.state.value, "white")
            
            console.print(f"[blue]•[/blue] [bold]{plugin_name}[/bold] [{state_color}]({plugin_info.state.value})[/{state_color}]")
            
            if plugin_info.instance:
                if hasattr(plugin_info.instance, "description"):
                    console.print(f"  [dim]{plugin_info.instance.description}[/dim]")
                if hasattr(plugin_info.instance, "version"):
                    console.print(f"  [dim]Version: {plugin_info.instance.version}[/dim]")
            
            console.print(f"  [dim]Entry point: {plugin_info.entry_point}[/dim]")
            
            if plugin_info.dependencies:
                console.print(f"  [dim]Dependencies: {', '.join(plugin_info.dependencies)}[/dim]")
            
            if plugin_info.error:
                console.print(f"  [red]Error: {plugin_info.error}[/red]")
            
            console.print()
    
    @plugin.command("info")
    @click.argument("plugin_name")
    @click.pass_context
    def plugin_info(ctx: click.Context, plugin_name: str) -> None:
        """Show detailed information about a plugin."""
        pm = ctx.obj.get("plugin_manager")
        if not pm:
            console.print("[red]Plugin manager not initialized[/red]")
            return
        
        if plugin_name not in pm.plugins:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            sys.exit(1)
        
        plugin_info = pm.plugins[plugin_name]
        instance = plugin_info.instance
        
        info_text = (
            f"[bold]Name:[/bold] {plugin_name}\n"
            f"[bold]State:[/bold] {plugin_info.state.value}\n"
            f"[bold]Entry Point:[/bold] {plugin_info.entry_point}\n"
            f"[bold]Priority:[/bold] {plugin_info.priority}\n"
        )
        
        if plugin_info.dependencies:
            info_text += f"[bold]Dependencies:[/bold] {', '.join(plugin_info.dependencies)}\n"
        
        if plugin_info.dependents:
            info_text += f"[bold]Dependents:[/bold] {', '.join(plugin_info.dependents)}\n"
        
        if instance:
            info_text += (
                f"[bold]Class:[/bold] {instance.__class__.__name__}\n"
                f"[bold]Module:[/bold] {instance.__class__.__module__}\n"
            )
            if hasattr(instance, "description"):
                info_text += f"[bold]Description:[/bold] {instance.description}\n"
            if hasattr(instance, "version"):
                info_text += f"[bold]Version:[/bold] {instance.version}\n"
        
        if plugin_info.error:
            info_text += f"[bold red]Error:[/bold red] {plugin_info.error}\n"
        
        console.print(
            Panel(
                info_text.rstrip(),
                title=f"Plugin: {plugin_name}",
                border_style="blue",
            )
        )
    
    @plugin.command("reload")
    @click.argument("plugin_name")
    @click.pass_context
    def plugin_reload(ctx: click.Context, plugin_name: str) -> None:
        """Reload a specific plugin."""
        pm = ctx.obj.get("plugin_manager")
        if not pm:
            console.print("[red]Plugin manager not initialized[/red]")
            return
        
        if plugin_name not in pm.plugins:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            sys.exit(1)
        
        console.print(f"🔄 Reloading plugin '{plugin_name}'...")
        
        import asyncio
        try:
            success = asyncio.run(pm.reload_plugin(plugin_name))
            if success:
                console.print(f"[green]✅ Plugin '{plugin_name}' reloaded successfully[/green]")
            else:
                console.print(f"[red]❌ Failed to reload plugin '{plugin_name}'[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error reloading plugin '{plugin_name}': {e}[/red]")
    
    @plugin.command("unload")
    @click.argument("plugin_name")
    @click.pass_context
    def plugin_unload(ctx: click.Context, plugin_name: str) -> None:
        """Unload a specific plugin."""
        pm = ctx.obj.get("plugin_manager")
        if not pm:
            console.print("[red]Plugin manager not initialized[/red]")
            return
        
        if plugin_name not in pm.plugins:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            sys.exit(1)
        
        console.print(f"🔄 Unloading plugin '{plugin_name}'...")
        
        import asyncio
        try:
            success = asyncio.run(pm.unload_plugin(plugin_name))
            if success:
                console.print(f"[green]✅ Plugin '{plugin_name}' unloaded successfully[/green]")
            else:
                console.print(f"[red]❌ Failed to unload plugin '{plugin_name}'[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error unloading plugin '{plugin_name}': {e}[/red]")
    
    @plugin.command("dependencies")
    @click.argument("plugin_name")
    @click.pass_context
    def plugin_dependencies(ctx: click.Context, plugin_name: str) -> None:
        """Show plugin dependency tree."""
        pm = ctx.obj.get("plugin_manager")
        if not pm:
            console.print("[red]Plugin manager not initialized[/red]")
            return
        
        if plugin_name not in pm.plugins:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            sys.exit(1)
        
        plugin_info = pm.plugins[plugin_name]
        
        console.print(f"\n[bold]Dependency Tree for '{plugin_name}':[/bold]\n")
        
        # Show dependencies
        if plugin_info.dependencies:
            console.print("[blue]📦 Dependencies:[/blue]")
            for dep in plugin_info.dependencies:
                dep_info = pm.plugins.get(dep)
                if dep_info:
                    state_color = "green" if dep_info.state.value == "active" else "red"
                    console.print(f"  └─ {dep} [{state_color}]({dep_info.state.value})[/{state_color}]")
                else:
                    console.print(f"  └─ {dep} [red](missing)[/red]")
        else:
            console.print("[dim]📦 No dependencies[/dim]")
        
        # Show dependents
        if plugin_info.dependents:
            console.print("\n[blue]🔗 Dependents:[/blue]")
            for dep in plugin_info.dependents:
                dep_info = pm.plugins.get(dep)
                if dep_info:
                    state_color = "green" if dep_info.state.value == "active" else "red"
                    console.print(f"  └─ {dep} [{state_color}]({dep_info.state.value})[/{state_color}]")
                else:
                    console.print(f"  └─ {dep} [red](missing)[/red]")
        else:
            console.print("\n[dim]🔗 No dependents[/dim]")
        
        # Show load order
        load_order = pm.get_load_order()
        if plugin_name in load_order:
            position = load_order.index(plugin_name) + 1
            console.print(f"\n[blue]📋 Load Order:[/blue] {position}/{len(load_order)}")
            console.print(f"[dim]Full order: {' → '.join(load_order)}[/dim]")
    
    @plugin.command("config")
    @click.argument("plugin_name")
    @click.option("--schema", is_flag=True, help="Show configuration schema")
    @click.pass_context
    def plugin_config(ctx: click.Context, plugin_name: str, schema: bool) -> None:
        """Show plugin configuration."""
        pm = ctx.obj.get("plugin_manager")
        if not pm:
            console.print("[red]Plugin manager not initialized[/red]")
            return
        
        if plugin_name not in pm.plugins:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            sys.exit(1)
        
        plugin_info = pm.plugins[plugin_name]
        if not plugin_info.instance:
            console.print(f"[red]Plugin '{plugin_name}' is not loaded[/red]")
            return
        
        if schema:
            # Show configuration schema
            try:
                schema_data = plugin_info.instance.get_config_schema()
                console.print(
                    Panel(
                        f"```json\n{json.dumps(schema_data, indent=2)}\n```",
                        title=f"Configuration Schema: {plugin_name}",
                        border_style="blue",
                    )
                )
            except Exception as e:
                console.print(f"[red]Error getting schema: {e}[/red]")
        else:
            # Show current configuration
            try:
                config_data = plugin_info.instance.config.dict()
                console.print(
                    Panel(
                        f"```json\n{json.dumps(config_data, indent=2)}\n```",
                        title=f"Current Configuration: {plugin_name}",
                        border_style="green",
                    )
                )
            except Exception as e:
                console.print(f"[red]Error getting configuration: {e}[/red]")
    
    @plugin.command("validate")
    @click.argument("plugin_name", required=False)
    @click.pass_context
    def plugin_validate(ctx: click.Context, plugin_name: Optional[str]) -> None:
        """Validate plugin configurations."""
        pm = ctx.obj.get("plugin_manager")
        if not pm:
            console.print("[red]Plugin manager not initialized[/red]")
            return
        
        plugins_to_validate = [plugin_name] if plugin_name else list(pm.plugins.keys())
        
        console.print(f"\n[bold]Validating {len(plugins_to_validate)} plugin(s)...[/bold]\n")
        
        validation_results = []
        for name in plugins_to_validate:
            if name not in pm.plugins:
                console.print(f"[red]❌ Plugin '{name}' not found[/red]")
                continue
            
            plugin_info = pm.plugins[name]
            if not plugin_info.instance:
                console.print(f"[yellow]⚠️  Plugin '{name}' is not loaded[/yellow]")
                validation_results.append((name, "not_loaded"))
                continue
            
            try:
                is_valid = plugin_info.instance.validate_config()
                if is_valid:
                    console.print(f"[green]✅ Plugin '{name}' configuration is valid[/green]")
                    validation_results.append((name, "valid"))
                else:
                    console.print(f"[red]❌ Plugin '{name}' configuration is invalid[/red]")
                    validation_results.append((name, "invalid"))
            except Exception as e:
                console.print(f"[red]❌ Plugin '{name}' validation error: {e}[/red]")
                validation_results.append((name, "error"))
        
        # Summary
        valid_count = sum(1 for _, status in validation_results if status == "valid")
        total_count = len(validation_results)
        
        console.print(f"\n[bold]Summary:[/bold] {valid_count}/{total_count} plugins have valid configurations")
    
    # Add completion command
    @cli.command()
    @click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']))
    def completion(shell: str) -> None:
        """Generate shell completion script.
        
        Examples:
            # For zsh (add to ~/.zshrc):
            eval "$(floatctl completion zsh)"
            
            # Or save to a file:
            floatctl completion zsh > ~/.config/floatctl/completion.zsh
            source ~/.config/floatctl/completion.zsh
        """
        import subprocess
        import os
        
        # Get the shell completion script
        env = os.environ.copy()
        env['_FLOATCTL_COMPLETE'] = f'{shell}_source'
        
        # Run floatctl with the completion environment variable
        result = subprocess.run(
            [sys.executable, '-m', 'floatctl'],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            click.echo(result.stdout)
        else:
            click.echo(f"Error generating {shell} completion: {result.stderr}", err=True)
    
    @cli.command()
    @click.pass_context
    def repl(ctx: click.Context) -> None:
        """Launch interactive REPL mode for FloatCtl.
        
        The REPL provides an interactive shell experience with:
        - Command completion with Tab
        - Command history with arrow keys
        - Plugin-specific contexts
        - Rich formatted output
        
        Example:
            $ floatctl repl
            floatctl> help
            floatctl> plugin use forest
            floatctl[forest]> list
        """
        from floatctl.repl import FloatREPL, REPL_AVAILABLE
        
        if not REPL_AVAILABLE:
            console.print("[red]REPL mode requires prompt-toolkit:[/red]")
            console.print("  pip install prompt-toolkit")
            return
            
        # Create REPL instance
        repl = FloatREPL("floatctl")
        
        # Register all loaded plugins with REPL
        pm = ctx.obj.get("plugin_manager")
        if pm and hasattr(pm, 'plugins'):
            for name, plugin_info in pm.plugins.items():
                plugin_instance = plugin_info.get('instance')
                if plugin_instance:
                    repl.register_plugin(name, plugin_instance)
        
        # Run the REPL
        try:
            repl.run()
        except Exception as e:
            console.print(f"[red]REPL error: {e}[/red]")
            if ctx.obj.get("config", {}).get("verbose", False):
                console.print_exception()
    
    return cli


async def load_and_register_plugins_async(cli_app: click.Group) -> PluginManager:
    """Load plugins and register their commands with the CLI."""
    
    # Initialize plugin manager
    plugin_manager = PluginManager()
    
    try:
        # Load all plugins with async lifecycle management
        await plugin_manager.load_plugins()
        
        # Register plugin commands with CLI
        plugin_manager.register_cli_commands(cli_app)
        
        if not os.environ.get('_FLOATCTL_COMPLETE'):
            structlog.get_logger().info(
                "plugins_loaded_successfully",
                count=len([p for p in plugin_manager.plugins.values() if p.state.value == "active"])
            )
        
    except Exception as e:
        structlog.get_logger().error("plugin_loading_failed", error=str(e))
        console.print(f"[red]Failed to load plugins: {e}[/red]")
        # Don't exit - let CLI work without plugins
    
    return plugin_manager


def load_and_register_plugins(cli_app: click.Group) -> PluginManager:
    """Synchronous wrapper for async plugin loading."""
    import asyncio
    
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we need to handle this differently
            # For now, fall back to synchronous loading
            plugin_manager = PluginManager()
            plugin_manager._discover_entry_point_plugins()
            
            # Load plugins synchronously (basic loading without full lifecycle)
            for name, info in plugin_manager.plugins.items():
                if info.state.value == "discovered":
                    try:
                        # Basic synchronous loading
                        if info.loaded_from == "entry_point":
                            plugin_class = plugin_manager.get_plugin_class(name)
                            if plugin_class is None:
                                raise RuntimeError(f"Failed to find plugin class for {name}")

                            plugin_instance = plugin_class()
                            plugin_instance.set_manager(plugin_manager)
                            plugin_instance._state = PluginState.ACTIVE  # Skip full lifecycle for now
                            info.instance = plugin_instance
                            info.state = PluginState.ACTIVE
                    except Exception as e:
                        info.state = PluginState.ERROR
                        info.error = str(e)
            
            plugin_manager.register_cli_commands(cli_app)
            return plugin_manager
        else:
            # Run async loading in new event loop
            return asyncio.run(load_and_register_plugins_async(cli_app))
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(load_and_register_plugins_async(cli_app))


def main():
    """Main entry point that sets up everything."""
    try:
        # Set up quiet logging initially to prevent verbose plugin loading output
        if not os.environ.get('_FLOATCTL_COMPLETE'):
            setup_quiet_logging()
        
        # Create CLI app
        cli_app = create_cli_app()
        
        # Load and register plugins
        plugin_manager = load_and_register_plugins(cli_app)
        
        # Store plugin manager on the CLI for access in commands
        cli_app.plugin_manager = plugin_manager
        
        # Run CLI
        cli_app()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()