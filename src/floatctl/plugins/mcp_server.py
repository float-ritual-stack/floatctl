"""MCP (Model Context Protocol) server installation and management commands."""

import json
import shutil
import sys
from pathlib import Path

import click
from floatctl.plugin_manager import PluginBase, command, group, option
from floatctl.core.logging import get_logger


class MCPServerPlugin(PluginBase):
    """MCP server installation and management commands."""
    
    name = "mcp"
    description = "MCP server installation and management commands"
    version = "0.1.0"
    
    @group()
    @click.pass_context
    def mcp(self, ctx: click.Context) -> None:
        """MCP server for context concierge functionality."""
        pass
    
    @command(parent="mcp")
    @option(
        '--transport',
        type=click.Choice(['stdio', 'sse', 'streamable-http']),
        default='stdio',
        help='Transport mode for MCP server'
    )
    @option(
        '--port',
        type=int,
        default=8000,
        help='Port for HTTP transport'
    )
    @option(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host for HTTP transport (use 0.0.0.0 for remote access)'
    )
    def serve(self, transport: str, port: int, host: str) -> None:
        """Run the Evna Context Concierge MCP server.
        
        This server provides context management tools for active_context_stream,
        enabling natural context capture and retrieval.
        
        Examples:
            floatctl mcp serve              # Run with stdio transport
            floatctl mcp serve --transport sse --port 8000 --host 0.0.0.0
        """
        logger = get_logger(__name__)
        
        # Set environment variables for the MCP server configuration
        import os
        os.environ['FASTMCP_HOST'] = host
        os.environ['FASTMCP_PORT'] = str(port)
        
        # Import and run the actual MCP server
        from floatctl.mcp_server import mcp
        
        if transport == 'stdio':
            click.echo("Starting Evna Context Concierge MCP server (stdio)...")
            logger.info("mcp_server_start", transport="stdio")
            
            # Run the MCP server
            mcp.run(transport='stdio')
            
        elif transport == 'sse':
            click.echo(f"Starting Evna Context Concierge MCP server (SSE) on {host}:{port}...")
            click.echo(f"[cyan]Server will be available at: http://{host}:{port}/sse[/cyan]")
            logger.info("mcp_server_start", transport=transport, host=host, port=port)
            
            # Run the MCP server with SSE transport
            mcp.run(transport='sse')
            
        elif transport == 'streamable-http':
            click.echo(f"Starting Evna Context Concierge MCP server (HTTP) on {host}:{port}...")
            click.echo(f"[cyan]Server will be available at: http://{host}:{port}/mcp[/cyan]")
            logger.info("mcp_server_start", transport=transport, host=host, port=port)
            
            # Run the MCP server with streamable-http transport
            mcp.run(transport='streamable-http')
        
    @command(parent="mcp")
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
    def install(self, claude_desktop: bool, name: str) -> None:
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
                # Use uv run to execute the wrapper (cleaner startup)
                config['mcpServers'][name] = {
                    "command": uv_path,
                    "args": [
                        "run",
                        "--project", str(project_root),
                        "python", "-m", "floatctl.mcp_server_wrapper"
                    ]
                }
            else:
                # Fallback to direct Python execution with wrapper
                config['mcpServers'][name] = {
                    "command": sys.executable,
                    "args": ["-m", "floatctl.mcp_server_wrapper"],
                    "env": {
                        "PYTHONPATH": str(project_root / "src")
                    }
                }
            
            # Write updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            click.echo(f"[green]✓ Installed '{name}' MCP server to Claude Desktop[/green]")
            if uv_path:
                click.echo(f"[blue]Command: {uv_path} run --project {project_root} python -m floatctl.mcp_server_wrapper[/blue]")
            else:
                click.echo(f"[blue]Command: {sys.executable} -m floatctl.mcp_server_wrapper[/blue]")
                click.echo(f"[blue]PYTHONPATH: {project_root / 'src'}[/blue]")
            click.echo("[yellow]Restart Claude Desktop to activate the server[/yellow]")
            
            logger.info("mcp_server_installed", name=name, config_path=str(config_path))
            
        except Exception as e:
            click.echo(f"[red]Failed to install: {e}[/red]")
            logger.error("mcp_install_failed", error=str(e))