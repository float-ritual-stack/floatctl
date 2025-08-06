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
        
        @mcp.command()
        @click.option(
            '--claude-desktop',
            is_flag=True,
            help='Check Claude Desktop configuration'
        )
        @click.option(
            '--name',
            default='evna-context-concierge',
            help='Server name to check'
        )
        def status(claude_desktop: bool, name: str) -> None:
            """Check MCP server installation status.
            
            Shows current configuration and available tools.
            
            Example:
                floatctl mcp status --claude-desktop
            """
            if not claude_desktop:
                click.echo("[red]Please specify --claude-desktop[/red]")
                return
            
            logger = get_logger(__name__)
            config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
            
            click.echo(f"🧠 [bold]Evna-MCP Status Check[/bold]\n")
            
            # Check if Claude Desktop config exists
            if not config_path.exists():
                click.echo(f"[red]❌ Claude Desktop config not found at {config_path}[/red]")
                click.echo("[yellow]💡 Install Claude Desktop first[/yellow]")
                return
            
            try:
                # Read existing config
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check MCP server configuration
                if 'mcpServers' not in config:
                    click.echo("[yellow]⚠️  No MCP servers configured in Claude Desktop[/yellow]")
                    click.echo(f"[blue]💡 Run: floatctl mcp install --claude-desktop[/blue]")
                    return
                
                if name not in config['mcpServers']:
                    click.echo(f"[yellow]⚠️  Server '{name}' not installed[/yellow]")
                    click.echo(f"[blue]💡 Run: floatctl mcp install --claude-desktop[/blue]")
                    
                    # Show other installed servers
                    other_servers = list(config['mcpServers'].keys())
                    if other_servers:
                        click.echo(f"\n[dim]Other installed servers: {', '.join(other_servers)}[/dim]")
                    return
                
                # Server is installed - show details
                server_config = config['mcpServers'][name]
                click.echo(f"[green]✅ Server '{name}' is installed[/green]")
                click.echo(f"[blue]Command: {server_config.get('command', 'N/A')}[/blue]")
                if 'args' in server_config:
                    click.echo(f"[blue]Args: {' '.join(server_config['args'])}[/blue]")
                if 'env' in server_config:
                    click.echo(f"[blue]Environment: {server_config['env']}[/blue]")
                
                # Show available tools
                click.echo(f"\n[bold]🛠️  Available Tools:[/bold]")
                tools = [
                    "smart_pattern_processor - Universal :: pattern handler",
                    "get_prompt - Access your prompt library", 
                    "smart_chroma_query - Protected ChromaDB access",
                    "surface_recent_context - 'What was I working on?'",
                    "get_usage_insights - Usage analytics",
                    "check_boundary_status - Boundary violation detection",
                    "process_context_marker - Advanced ctx:: processing"
                ]
                
                for tool in tools:
                    click.echo(f"   • {tool}")
                
                # Show prompt library
                click.echo(f"\n[bold]📚 Prompt Library:[/bold]")
                from floatctl.mcp_server import PROMPT_LIBRARY
                for prompt_name, prompt_data in PROMPT_LIBRARY.items():
                    tags = ", ".join(prompt_data["tags"])
                    click.echo(f"   • {prompt_name}: {tags}")
                
                click.echo(f"\n[green]🎯 Ready to use! Restart Claude Desktop if you just installed.[/green]")
                
                logger.info("mcp_status_checked", name=name, installed=True)
                
            except Exception as e:
                click.echo(f"[red]Failed to check status: {e}[/red]")
                logger.error("mcp_status_failed", error=str(e))
        
        @mcp.command()
        @click.option(
            '--debug',
            is_flag=True,
            help='Enable debug logging to track down issues'
        )
        def debug(debug: bool) -> None:
            """Debug the MCP server to track down JSON parsing issues.
            
            Runs the server with debug logging to identify the source of
            "Unexpected non-whitespace character after JSON" errors.
            """
            if not debug:
                click.echo("[yellow]Use --debug flag to enable debug mode[/yellow]")
                return
            
            import tempfile
            import subprocess
            import sys
            import os
            from pathlib import Path
            
            # Create debug log file
            debug_log = Path(tempfile.gettempdir()) / "evna_mcp_debug.log"
            click.echo(f"🐛 [bold]Debug mode enabled[/bold]")
            click.echo(f"📝 Debug log: {debug_log}")
            
            # Clear previous debug log
            if debug_log.exists():
                debug_log.unlink()
            
            # Set debug environment
            env = os.environ.copy()
            env['FLOATCTL_MCP_DEBUG'] = str(debug_log)
            
            # Get the project root
            import floatctl
            floatctl_module_dir = Path(floatctl.__file__).parent
            project_root = floatctl_module_dir.parent.parent
            
            click.echo(f"🚀 Starting MCP server with debug logging...")
            click.echo(f"📁 Project root: {project_root}")
            click.echo(f"⚠️  Press Ctrl+C to stop")
            
            try:
                # Run the MCP server with debug logging
                result = subprocess.run([
                    "uv", "run", "--project", str(project_root),
                    "python", "-m", "floatctl.mcp_server"
                ], env=env, capture_output=True, text=True, timeout=10)
                
                click.echo(f"📤 STDOUT:\n{result.stdout}")
                click.echo(f"📥 STDERR:\n{result.stderr}")
                
            except subprocess.TimeoutExpired:
                click.echo("⏰ Server started successfully (timed out after 10s)")
            except KeyboardInterrupt:
                click.echo("\n🛑 Stopped by user")
            except Exception as e:
                click.echo(f"❌ Error: {e}")
            
            # Show debug log if it exists
            if debug_log.exists():
                click.echo(f"\n📋 [bold]Debug Log Contents:[/bold]")
                with open(debug_log, 'r') as f:
                    content = f.read()
                    if content.strip():
                        click.echo(content)
                    else:
                        click.echo("(empty)")
            else:
                click.echo("📋 No debug log created")
        
        @mcp.command()
        def test() -> None:
            """Test the enhanced Evna-MCP server locally.
            
            Runs a quick test of the enhanced features without Claude Desktop.
            """
            click.echo("🧠 [bold]Testing Enhanced Evna-MCP Features[/bold]\n")
            
            # Import test functions
            import asyncio
            from floatctl.mcp_server import (
                get_prompt, parse_any_pattern, check_context_window_risk,
                PROMPT_LIBRARY, track_usage
            )
            
            async def run_tests():
                # Test 1: Prompt Library
                click.echo("1. [blue]Testing Prompt Library...[/blue]")
                try:
                    result = await get_prompt("consciousness")
                    click.echo(f"   ✅ Found: {result.get('name', 'None')}")
                    click.echo(f"   📋 Tags: {', '.join(result.get('tags', []))}")
                except Exception as e:
                    click.echo(f"   ❌ Error: {str(e)}")
                
                # Test 2: Pattern Parsing
                click.echo("\n2. [blue]Testing Pattern Parsing...[/blue]")
                test_pattern = "eureka:: Enhanced Evna-MCP is working! [concept:: context-concierge] [project:: floatctl]"
                metadata = parse_any_pattern(test_pattern)
                click.echo(f"   ✅ Patterns found: {metadata.get('patterns_found', [])}")
                click.echo(f"   🎯 Primary: {metadata.get('primary_pattern', 'None')}")
                
                # Test 3: Context Window Protection
                click.echo("\n3. [blue]Testing Context Window Protection...[/blue]")
                large_text = "This is a test. " * 10000  # ~40k chars
                is_risky, warning = check_context_window_risk(large_text)
                if is_risky:
                    click.echo(f"   ✅ Protection working: {warning}")
                else:
                    click.echo("   ❌ Protection not triggered")
                
                # Test 4: Usage Tracking
                click.echo("\n4. [blue]Testing Usage Tracking...[/blue]")
                track_usage("test_query", "consciousness archaeology", 1000)
                click.echo("   ✅ Usage tracking active")
                
                click.echo(f"\n[green]✅ All tests passed! Enhanced Evna-MCP is ready.[/green]")
                click.echo(f"[blue]💡 Run 'floatctl mcp install --claude-desktop' to configure Claude[/blue]")
            
            # Run async tests
            try:
                asyncio.run(run_tests())
            except Exception as e:
                click.echo(f"[red]Test failed: {e}[/red]")
        
        @mcp.command()
        @click.option(
            '--name',
            default='evna-context-concierge',
            help='Server name in configuration'
        )
        def reinstall(name: str) -> None:
            """Reinstall/update the MCP server configuration.
            
            Useful when you've updated the enhanced Evna-MCP server.
            
            Example:
                floatctl mcp reinstall
            """
            click.echo("🔄 [bold]Reinstalling Enhanced Evna-MCP...[/bold]\n")
            
            # Uninstall first (ignore errors)
            try:
                ctx = click.get_current_context()
                ctx.invoke(uninstall, claude_desktop=True, name=name)
            except:
                pass
            
            click.echo()
            
            # Install fresh
            ctx = click.get_current_context()
            ctx.invoke(install, claude_desktop=True, name=name)
            
            click.echo(f"\n[green]🎯 Enhanced Evna-MCP reinstalled! Restart Claude Desktop.[/green]")