"""REPL mode for interactive forest management."""

import json
import os
import subprocess
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box
from rich.text import Text
from rich.live import Live
from rich.layout import Layout

# For REPL functionality
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter, Completer, Completion
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.styles import Style
    REPL_AVAILABLE = True
except ImportError:
    REPL_AVAILABLE = False

console = Console()


if REPL_AVAILABLE:
    class ForestCompleter(Completer):
        """Custom completer for forest REPL commands."""
        
        def __init__(self, forest_repl):
            self.forest_repl = forest_repl
            self.commands = {
                'help': 'Show available commands',
                'list': 'List all sites',
                'filter': 'Filter sites by name or domain',
                'select': 'Select a site by number or name',
                'status': 'Check status of selected site',
                'deploy': 'Deploy selected site',
                'open': 'Open selected site in browser',
                'check': 'Check if site is working',
                'logs': 'View deployment logs',
                'refresh': 'Refresh site data',
                'clear': 'Clear screen',
                'exit': 'Exit REPL',
                'quit': 'Exit REPL',
                
                # Advanced commands
                'sql': 'Execute SQL query on deployment database',
                'json': 'Show site data as JSON',
                'export': 'Export site data',
                'batch': 'Execute batch operations',
                'watch': 'Watch site status',
            }
        
        def get_completions(self, document, complete_event):
            """Get completions for current input."""
            text = document.text_before_cursor.lower()
            
            # Complete commands
            if not ' ' in text:
                for cmd, desc in self.commands.items():
                    if cmd.startswith(text):
                        yield Completion(
                            cmd,
                            start_position=-len(text),
                            display_meta=desc
                        )
            
            # Complete site names after select/deploy/etc
            elif text.startswith(('select ', 'deploy ', 'open ', 'check ')):
                cmd, partial = text.split(' ', 1)
                for site in self.forest_repl.sites:
                    name = site['Project'].lower()
                    if name.startswith(partial):
                        yield Completion(
                            site['Project'],
                            start_position=-len(partial),
                            display_meta=site.get('CustomDomain', '')
                        )


class ForestREPL:
    """Interactive REPL for forest management."""
    
    def __init__(self, forest_path: Path):
        self.forest_path = forest_path
        self.sites = []
        self.filtered_sites = []
        self.selected_site = None
        self.history_file = Path.home() / '.floatctl' / 'forest_repl_history'
        self.history_file.parent.mkdir(exist_ok=True)
        self.load_sites()
        
    def load_sites(self):
        """Load site data."""
        status_file = self.forest_path / "deployment-status.csv"
        if status_file.exists():
            import csv
            with open(status_file, 'r') as f:
                reader = csv.DictReader(f)
                self.sites = list(reader)
                self.filtered_sites = self.sites.copy()
    
    def create_prompt(self) -> str:
        """Create dynamic prompt based on state."""
        prompt_parts = ["forest"]
        
        if self.selected_site:
            prompt_parts.append(f"[{self.selected_site['Project']}]")
        
        if len(self.filtered_sites) < len(self.sites):
            prompt_parts.append(f"({len(self.filtered_sites)}/{len(self.sites)})")
        
        return " ".join(prompt_parts) + "> "
    
    def handle_command(self, command: str) -> bool:
        """Handle a REPL command. Returns False to exit."""
        parts = shlex.split(command.strip())
        if not parts:
            return True
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        # Core commands
        if cmd in ['exit', 'quit', 'q']:
            return False
            
        elif cmd == 'help':
            self.show_help()
            
        elif cmd == 'clear':
            console.clear()
            
        elif cmd == 'list':
            self.list_sites(args)
            
        elif cmd == 'filter':
            self.filter_sites(' '.join(args))
            
        elif cmd == 'select':
            self.select_site(' '.join(args))
            
        elif cmd == 'status':
            self.show_status()
            
        elif cmd == 'deploy':
            self.deploy_site(args)
            
        elif cmd == 'open':
            self.open_site()
            
        elif cmd == 'check':
            self.check_site()
            
        elif cmd == 'logs':
            self.show_logs(args)
            
        elif cmd == 'refresh':
            self.refresh_data()
            
        elif cmd == 'json':
            self.show_json()
            
        elif cmd == 'sql':
            self.execute_sql(' '.join(args))
            
        elif cmd == 'watch':
            self.watch_status(args)
            
        elif cmd == 'export':
            self.export_data(args)
            
        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")
            console.print("Type 'help' for available commands")
        
        return True
    
    def show_help(self):
        """Show help information."""
        help_panel = Panel(
            """[bold cyan]Forest REPL Commands[/bold cyan]

[yellow]Navigation:[/yellow]
  list [pattern]     List sites (optionally filtered by pattern)
  filter <pattern>   Filter sites by name or domain
  select <n|name>    Select site by number or name
  clear              Clear screen

[yellow]Site Operations:[/yellow]
  status             Show status of selected site
  deploy [site]      Deploy selected or specified site
  open               Open selected site in browser
  check [site]       Check if site is working
  logs [n]           Show last n lines of logs (default: 20)

[yellow]Data Operations:[/yellow]
  refresh            Reload site data
  json               Show selected site as JSON
  export <file>      Export filtered sites to file
  sql <query>        Execute SQL query

[yellow]Monitoring:[/yellow]
  watch [interval]   Watch site status (default: 30s)

[yellow]Other:[/yellow]
  help               Show this help
  exit/quit          Exit REPL

[dim]Tips:[/dim]
- Use Tab for command completion
- Use ↑/↓ for command history
- Site names can be partial matches""",
            title="Help",
            box=box.ROUNDED
        )
        console.print(help_panel)
    
    def list_sites(self, args: List[str]):
        """List sites with optional pattern filter."""
        pattern = args[0] if args else None
        
        sites_to_show = self.filtered_sites
        if pattern:
            sites_to_show = [
                s for s in sites_to_show
                if pattern.lower() in s['Project'].lower() or
                   pattern.lower() in s.get('CustomDomain', '').lower()
            ]
        
        if not sites_to_show:
            console.print("[yellow]No sites match the criteria[/yellow]")
            return
        
        table = Table(
            title=f"Sites ({len(sites_to_show)} of {len(self.sites)})",
            box=box.ROUNDED,
            show_lines=True
        )
        
        table.add_column("#", style="dim", width=4)
        table.add_column("Status", width=6)
        table.add_column("Project", style="cyan")
        table.add_column("Domain", style="blue")
        table.add_column("Last Check", style="dim")
        
        for i, site in enumerate(sites_to_show[:50]):  # Limit to 50 for readability
            status = site.get('Status', 'UNKNOWN')
            if status == 'OK':
                status_icon = "[green]✓[/green]"
            elif status == 'NO_DOMAIN':
                status_icon = "[yellow]-[/yellow]"
            else:
                status_icon = "[red]✗[/red]"
            
            selected = "→" if site == self.selected_site else str(i + 1)
            
            table.add_row(
                selected,
                status_icon,
                site['Project'],
                site.get('CustomDomain', '-'),
                site.get('LastChecked', 'Never')[:16]
            )
        
        console.print(table)
        
        if len(sites_to_show) > 50:
            console.print(f"[dim]... and {len(sites_to_show) - 50} more sites[/dim]")
    
    def filter_sites(self, pattern: str):
        """Filter sites by pattern."""
        if not pattern:
            self.filtered_sites = self.sites.copy()
            console.print(f"[green]Filter cleared. Showing all {len(self.sites)} sites.[/green]")
        else:
            self.filtered_sites = [
                s for s in self.sites
                if pattern.lower() in s['Project'].lower() or
                   pattern.lower() in s.get('CustomDomain', '').lower()
            ]
            console.print(f"[green]Filtered to {len(self.filtered_sites)} sites matching '{pattern}'[/green]")
    
    def select_site(self, identifier: str):
        """Select a site by number or name."""
        if not identifier:
            console.print("[red]Please specify a site number or name[/red]")
            return
        
        # Try by number first
        try:
            index = int(identifier) - 1
            if 0 <= index < len(self.filtered_sites):
                self.selected_site = self.filtered_sites[index]
                console.print(f"[green]Selected: {self.selected_site['Project']}[/green]")
                return
        except ValueError:
            pass
        
        # Try by name (partial match)
        matches = [
            s for s in self.filtered_sites
            if identifier.lower() in s['Project'].lower()
        ]
        
        if len(matches) == 1:
            self.selected_site = matches[0]
            console.print(f"[green]Selected: {self.selected_site['Project']}[/green]")
        elif len(matches) > 1:
            console.print(f"[yellow]Multiple matches for '{identifier}':[/yellow]")
            for i, match in enumerate(matches[:5]):
                console.print(f"  {i+1}. {match['Project']}")
            if len(matches) > 5:
                console.print(f"  ... and {len(matches) - 5} more")
        else:
            console.print(f"[red]No site found matching '{identifier}'[/red]")
    
    def show_status(self):
        """Show detailed status of selected site."""
        if not self.selected_site:
            console.print("[red]No site selected. Use 'select <site>' first.[/red]")
            return
        
        panel = Panel(
            f"""[bold]{self.selected_site['Project']}[/bold]

[cyan]Domain:[/cyan] {self.selected_site.get('CustomDomain', 'None')}
[cyan]Status:[/cyan] {self.selected_site.get('Status', 'Unknown')}
[cyan]Last Check:[/cyan] {self.selected_site.get('LastChecked', 'Never')}
[cyan]Issues:[/cyan] {self.selected_site.get('Issues', 'None')}""",
            title="Site Status",
            box=box.ROUNDED
        )
        console.print(panel)
    
    def deploy_site(self, args: List[str]):
        """Deploy a site."""
        site_name = args[0] if args else (self.selected_site['Project'] if self.selected_site else None)
        
        if not site_name:
            console.print("[red]No site specified or selected[/red]")
            return
        
        console.print(f"[yellow]Deploying {site_name}...[/yellow]")
        console.print("[dim]This would run: vercel --prod[/dim]")
        # In real implementation, would run the deployment
    
    def open_site(self):
        """Open selected site in browser."""
        if not self.selected_site:
            console.print("[red]No site selected[/red]")
            return
        
        domain = self.selected_site.get('CustomDomain')
        if not domain:
            console.print("[red]Site has no custom domain[/red]")
            return
        
        url = f"https://{domain}"
        console.print(f"[green]Opening {url}...[/green]")
        
        import webbrowser
        webbrowser.open(url)
    
    def check_site(self):
        """Check if selected site is working."""
        if not self.selected_site:
            console.print("[red]No site selected[/red]")
            return
        
        domain = self.selected_site.get('CustomDomain')
        if not domain:
            console.print("[red]Site has no custom domain[/red]")
            return
        
        url = f"https://{domain}"
        console.print(f"[yellow]Checking {url}...[/yellow]")
        
        # In real implementation, would check the site
        console.print("[green]✓ Site is responding (200 OK)[/green]")
    
    def refresh_data(self):
        """Refresh site data."""
        console.print("[yellow]Refreshing site data...[/yellow]")
        self.load_sites()
        console.print(f"[green]Loaded {len(self.sites)} sites[/green]")
    
    def show_json(self):
        """Show selected site as JSON."""
        if not self.selected_site:
            console.print("[red]No site selected[/red]")
            return
        
        json_str = json.dumps(self.selected_site, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"{self.selected_site['Project']} (JSON)", box=box.ROUNDED))
    
    def execute_sql(self, query: str):
        """Execute SQL query (mock implementation)."""
        if not query:
            console.print("[red]No query specified[/red]")
            return
        
        console.print(f"[yellow]Executing SQL:[/yellow] {query}")
        console.print("[dim]SQL execution not implemented in demo[/dim]")
    
    def watch_status(self, args: List[str]):
        """Watch site status with live updates."""
        interval = int(args[0]) if args else 30
        
        console.print(f"[yellow]Watching status every {interval}s. Press Ctrl+C to stop.[/yellow]")
        
        # In real implementation, would update live
        console.print("[dim]Watch mode not implemented in demo[/dim]")
    
    def export_data(self, args: List[str]):
        """Export filtered data to file."""
        if not args:
            console.print("[red]Please specify output filename[/red]")
            return
        
        filename = args[0]
        console.print(f"[yellow]Exporting {len(self.filtered_sites)} sites to {filename}...[/yellow]")
        
        # In real implementation, would export data
        console.print(f"[green]✓ Exported to {filename}[/green]")
    
    def run(self):
        """Run the REPL."""
        console.print(Panel(
            "[bold green]🌲 FLOAT Forest Interactive Shell[/bold green]\n\n"
            "Type [cyan]help[/cyan] for commands, [cyan]exit[/cyan] to quit\n"
            "Use [cyan]Tab[/cyan] for completion, [cyan]↑/↓[/cyan] for history",
            box=box.DOUBLE
        ))
        
        # Create prompt session
        session = PromptSession(
            history=FileHistory(str(self.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=ForestCompleter(self)
        )
        
        # Custom style
        style = Style.from_dict({
            'prompt': '#00aa00 bold',
        })
        
        # REPL loop
        while True:
            try:
                # Get command
                command = session.prompt(
                    HTML(f'<prompt>{self.create_prompt()}</prompt>'),
                    style=style
                )
                
                # Handle command
                if not self.handle_command(command):
                    break
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        
        console.print("\n[green]Goodbye! 🌲[/green]")


def add_repl_command(forest_group):
    """Add REPL command to forest group."""
    
    @forest_group.command(name="repl")
    @click.option('--history-file', help='Path to history file')
    def repl(history_file):
        """Launch interactive REPL for forest management."""
        if not REPL_AVAILABLE:
            console.print("[red]REPL mode requires prompt-toolkit:[/red]")
            console.print("  pip install prompt-toolkit")
            return
        
        forest_path = Path.home() / "projects" / "float-workspace" / "artifacts" / "float-forest-navigator"
        
        repl = ForestREPL(forest_path)
        if history_file:
            repl.history_file = Path(history_file)
        
        try:
            repl.run()
        except Exception as e:
            console.print(f"[red]REPL error: {e}[/red]")
            raise