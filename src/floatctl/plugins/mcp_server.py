"""MCP Server plugin - CLI commands for managing the Evna Context Concierge installation."""

import json
import sys
from pathlib import Path
import shutil

import click

from floatctl.plugin_manager import PluginBase
from floatctl.core.logging import get_logger


class MCPServerPlugin(PluginBase):
    """MCP Server plugin for FloatCtl."""
    
    name = "mcp"
    description = "MCP server installation and management commands"
    version = "0.1.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register MCP server commands."""
        
        @cli_group.group()
        @click.pass_context
        def mcp(ctx: click.Context) -> None:
            """MCP server for context concierge functionality."""
            pass
        
        @mcp.command()
        @click.option(
            '--transport',
            type=click.Choice(['stdio', 'sse', 'streamable-http']),
            default='stdio',
            help='Transport mode for MCP server'
        )
        @click.option(
            '--port',
            type=int,
            default=3000,
            help='Port for HTTP transport'
        )
        def serve(transport: str, port: int) -> None:
            """Run the Evna Context Concierge MCP server.
            
            This server provides context management tools for active_context_stream,
            enabling natural context capture and retrieval.
            
            Examples:
                floatctl mcp serve              # Run with stdio transport
                floatctl mcp serve --transport sse --port 8080
            """
            logger = get_logger(__name__)
            
            # Import and run the actual MCP server
            from floatctl.mcp_server import mcp
            
            if transport == 'stdio':
                click.echo("Starting Evna Context Concierge MCP server (stdio)...")
                logger.info("mcp_server_start", transport="stdio")
                
                # Run the MCP server
                mcp.run(transport='stdio')
                
            elif transport in ['sse', 'streamable-http']:
                click.echo(f"Starting Evna Context Concierge MCP server ({transport}) on port {port}...")
                logger.info("mcp_server_start", transport=transport, port=port)
                
                # Note: SSE/HTTP transports would require additional setup with uvicorn
                # For now, we'll just use stdio
                click.echo(f"[yellow]Note: {transport} transport requires additional setup. Using stdio for now.[/yellow]")
                mcp.run(transport='stdio')
        
        @mcp.command()
        @click.option(
            '--claude-desktop',
            is_flag=True,
            help='Install for Claude Desktop'
        )
        @click.option(
            '--name',
            default='evna-context-concierge',
            help='Server name in configuration'
        )
        def install(claude_desktop: bool, name: str) -> None:
            """Install the MCP server configuration.
            
            Adds the floatctl MCP server to Claude Desktop configuration.
            
            Example:
                floatctl mcp install --claude-desktop
            """
            if not claude_desktop:
                click.echo("[red]Please specify --claude-desktop[/red]")
                return
            
            logger = get_logger(__name__)
            config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
            
            if not config_path.exists():
                click.echo(f"[red]Claude Desktop config not found at {config_path}[/red]")
                return
            
            try:
                # Read existing config
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check if already installed
                if 'mcpServers' not in config:
                    config['mcpServers'] = {}
                
                if name in config['mcpServers']:
                    click.echo(f"[yellow]Server '{name}' already installed in Claude Desktop[/yellow]")
                    return
                
                # Get the project root directory
                import floatctl
                floatctl_module_dir = Path(floatctl.__file__).parent
                project_root = floatctl_module_dir.parent.parent  # Go up from src/floatctl to project root
                
                # Find uv executable
                uv_path = shutil.which("uv")
                if not uv_path:
                    # Try common locations
                    for path in ["/Users/evan/.local/bin/uv", "/usr/local/bin/uv", "/opt/homebrew/bin/uv"]:
                        if Path(path).exists():
                            uv_path = path
                            break
                
                if uv_path:
                    # Use uv run to execute in the project environment
                    config['mcpServers'][name] = {
                        "command": uv_path,
                        "args": [
                            "run",
                            "--project", str(project_root),
                            "python", "-m", "floatctl.mcp_server"
                        ]
                    }
                else:
                    # Fallback to direct Python execution
                    config['mcpServers'][name] = {
                        "command": sys.executable,
                        "args": ["-m", "floatctl.mcp_server"],
                        "env": {
                            "PYTHONPATH": str(project_root / "src")
                        }
                    }
                
                # Write updated config
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                
                click.echo(f"[green]✓ Installed '{name}' MCP server to Claude Desktop[/green]")
                if uv_path:
                    click.echo(f"[blue]Command: {uv_path} run --project {project_root} python -m floatctl.mcp_server[/blue]")
                else:
                    click.echo(f"[blue]Command: {sys.executable} -m floatctl.mcp_server[/blue]")
                    click.echo(f"[blue]PYTHONPATH: {project_root / 'src'}[/blue]")
                click.echo("[yellow]Restart Claude Desktop to activate the server[/yellow]")
                
                logger.info("mcp_server_installed", name=name, config_path=str(config_path))
                
            except Exception as e:
                click.echo(f"[red]Failed to install: {e}[/red]")
                logger.error("mcp_install_failed", error=str(e))
        
        @mcp.command()
        @click.option(
            '--claude-desktop',
            is_flag=True,
            help='Uninstall from Claude Desktop'
        )
        @click.option(
            '--name',
            default='evna-context-concierge',
            help='Server name in configuration'
        )
        def uninstall(claude_desktop: bool, name: str) -> None:
            """Uninstall the MCP server configuration.
            
            Removes the floatctl MCP server from Claude Desktop configuration.
            
            Example:
                floatctl mcp uninstall --claude-desktop
            """
            if not claude_desktop:
                click.echo("[red]Please specify --claude-desktop[/red]")
                return
            
            logger = get_logger(__name__)
            config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
            
            if not config_path.exists():
                click.echo(f"[red]Claude Desktop config not found at {config_path}[/red]")
                return
            
            try:
                # Read existing config
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check if installed
                if 'mcpServers' not in config or name not in config['mcpServers']:
                    click.echo(f"[yellow]Server '{name}' not found in Claude Desktop configuration[/yellow]")
                    return
                
                # Remove server configuration
                del config['mcpServers'][name]
                
                # Write updated config
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                
                click.echo(f"[green]✓ Uninstalled '{name}' MCP server from Claude Desktop[/green]")
                click.echo("[yellow]Restart Claude Desktop to apply changes[/yellow]")
                
                logger.info("mcp_server_uninstalled", name=name, config_path=str(config_path))
                
            except Exception as e:
                click.echo(f"[red]Failed to uninstall: {e}[/red]")
                logger.error("mcp_uninstall_failed", error=str(e))