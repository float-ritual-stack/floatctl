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
from pathlib import Path
from typing import Optional

import rich_click as click
import structlog
from rich.console import Console
from rich.panel import Panel

from floatctl import __version__
from floatctl.core.config import Config, load_config
from floatctl.core.logging import setup_logging
from floatctl.plugin_manager import PluginManager

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
            plugin_instance = plugin_info["instance"]
            console.print(f"[blue]•[/blue] [bold]{plugin_name}[/bold]")
            if hasattr(plugin_instance, "description"):
                console.print(f"  [dim]{plugin_instance.description}[/dim]")
            if hasattr(plugin_instance, "version"):
                console.print(f"  [dim]Version: {plugin_instance.version}[/dim]")
            console.print(f"  [dim]Entry point: {plugin_info['entry_point']}[/dim]")
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
        instance = plugin_info["instance"]
        
        console.print(
            Panel(
                f"[bold]Name:[/bold] {plugin_name}\n"
                f"[bold]Entry Point:[/bold] {plugin_info['entry_point']}\n"
                f"[bold]Class:[/bold] {instance.__class__.__name__}\n"
                f"[bold]Module:[/bold] {instance.__class__.__module__}\n"
                + (f"[bold]Description:[/bold] {instance.description}\n" if hasattr(instance, "description") else "")
                + (f"[bold]Version:[/bold] {instance.version}\n" if hasattr(instance, "version") else ""),
                title=f"Plugin: {plugin_name}",
                border_style="blue",
            )
        )
    
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
    
    return cli


def load_and_register_plugins(cli_app: click.Group) -> PluginManager:
    """Load plugins and register their commands with the CLI."""
    
    # Initialize plugin manager
    plugin_manager = PluginManager()
    
    try:
        # Load all plugins
        plugin_manager.load_plugins()
        
        # Register plugin commands with CLI
        plugin_manager.register_cli_commands(cli_app)
        
        if not os.environ.get('_FLOATCTL_COMPLETE'):
            structlog.get_logger().info(
                "plugins_loaded_successfully",
                count=len(plugin_manager.plugins)
            )
        
    except Exception as e:
        structlog.get_logger().error("plugin_loading_failed", error=str(e))
        console.print(f"[red]Failed to load plugins: {e}[/red]")
        # Don't exit - let CLI work without plugins
    
    return plugin_manager


def main():
    """Main entry point that sets up everything."""
    try:
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