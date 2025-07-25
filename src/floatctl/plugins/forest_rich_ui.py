"""Rich-based interactive UI for forest management."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import rich_click as click
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box
from rich.columns import Columns
from rich.console import Group
from rich.syntax import Syntax

console = Console()


class ForestDashboard:
    """Interactive dashboard for forest management using Rich layouts."""
    
    def __init__(self, forest_path: Path):
        self.forest_path = forest_path
        self.sites = []
        self.selected_index = 0
        self.filter_text = ""
        self.load_sites()
        
    def load_sites(self):
        """Load site data from deployment status."""
        status_file = self.forest_path / "deployment-status.csv"
        if status_file.exists():
            import csv
            with open(status_file, 'r') as f:
                reader = csv.DictReader(f)
                self.sites = list(reader)
    
    def get_filtered_sites(self) -> List[Dict]:
        """Get filtered list of sites."""
        if not self.filter_text:
            return self.sites
        
        return [
            site for site in self.sites
            if self.filter_text.lower() in site['Project'].lower() or
               self.filter_text.lower() in site.get('CustomDomain', '').lower()
        ]
    
    def create_header(self) -> Panel:
        """Create header panel."""
        header_text = Text()
        header_text.append("🌲 FLOAT Forest Navigator\n", style="bold green")
        header_text.append(f"Managing {len(self.sites)} sites", style="dim")
        
        return Panel(
            Align.center(header_text),
            box=box.DOUBLE,
            style="green"
        )
    
    def create_site_list(self) -> Panel:
        """Create scrollable site list."""
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            expand=True
        )
        
        table.add_column("", width=2)  # Selection indicator
        table.add_column("Status", width=6)
        table.add_column("Project", width=40)
        table.add_column("Domain", width=40)
        table.add_column("Last Check", width=20)
        
        filtered_sites = self.get_filtered_sites()
        
        # Window for scrolling
        start_idx = max(0, self.selected_index - 10)
        end_idx = min(len(filtered_sites), start_idx + 20)
        
        for i in range(start_idx, end_idx):
            site = filtered_sites[i]
            
            # Selection indicator
            selected = "→" if i == self.selected_index else " "
            
            # Status icon
            status = site.get('Status', 'UNKNOWN')
            if status == 'OK':
                status_icon = "[green]✓[/green]"
            elif status == 'NO_DOMAIN':
                status_icon = "[yellow]-[/yellow]"
            else:
                status_icon = "[red]✗[/red]"
            
            # Format last check time
            last_check = site.get('LastChecked', '')
            if last_check:
                try:
                    dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                    last_check = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            style = "bold white on blue" if i == self.selected_index else ""
            
            table.add_row(
                selected,
                status_icon,
                site['Project'],
                site.get('CustomDomain', '-'),
                last_check,
                style=style
            )
        
        footer = f"\n[dim]Showing {start_idx+1}-{end_idx} of {len(filtered_sites)} sites[/dim]"
        if self.filter_text:
            footer += f"\n[yellow]Filter: {self.filter_text}[/yellow]"
        
        return Panel(
            Group(table, Text(footer)),
            title="[bold]Sites[/bold]",
            box=box.ROUNDED,
            expand=True
        )
    
    def create_details_panel(self) -> Panel:
        """Create details panel for selected site."""
        filtered_sites = self.get_filtered_sites()
        
        if not filtered_sites or self.selected_index >= len(filtered_sites):
            return Panel("No site selected", title="Details", box=box.ROUNDED)
        
        site = filtered_sites[self.selected_index]
        
        details = Table(show_header=False, box=None, padding=(0, 1))
        details.add_column("Key", style="cyan")
        details.add_column("Value")
        
        details.add_row("Project", site['Project'])
        details.add_row("Domain", site.get('CustomDomain', 'None'))
        details.add_row("Status", site.get('Status', 'Unknown'))
        details.add_row("Last Checked", site.get('LastChecked', 'Never'))
        
        if site.get('Issues'):
            details.add_row("Issues", site['Issues'])
        
        # Add action hints
        actions = "\n[dim]Actions:[/dim]\n"
        actions += "  [cyan]Enter[/cyan] - Open in browser\n"
        actions += "  [cyan]d[/cyan] - Deploy\n"
        actions += "  [cyan]c[/cyan] - Check status\n"
        actions += "  [cyan]l[/cyan] - View logs"
        
        return Panel(
            Group(details, Text(actions)),
            title=f"[bold]{site['Project']}[/bold]",
            box=box.ROUNDED
        )
    
    def create_help_panel(self) -> Panel:
        """Create help panel."""
        help_text = """
[bold cyan]Keyboard Shortcuts:[/bold cyan]

[yellow]Navigation:[/yellow]
  ↑/k     - Move up
  ↓/j     - Move down
  PgUp/u  - Page up
  PgDn/d  - Page down
  Home/g  - Go to top
  End/G   - Go to bottom

[yellow]Actions:[/yellow]
  Enter   - Open site in browser
  d       - Deploy selected site
  D       - Deploy all sites
  c       - Check site status
  r       - Refresh data
  /       - Filter sites
  ?       - Toggle help

[yellow]Other:[/yellow]
  q/Esc   - Quit
        """
        
        return Panel(
            help_text.strip(),
            title="[bold]Help[/bold]",
            box=box.ROUNDED
        )
    
    def create_layout(self, show_help: bool = False) -> Layout:
        """Create the full layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(self.create_header(), size=3),
            Layout(name="main")
        )
        
        if show_help:
            layout["main"].split_row(
                Layout(self.create_site_list(), name="list"),
                Layout(self.create_help_panel(), name="help")
            )
        else:
            layout["main"].split_row(
                Layout(self.create_site_list(), name="list", ratio=2),
                Layout(self.create_details_panel(), name="details", ratio=1)
            )
        
        return layout
    
    def handle_action(self, key: str) -> Optional[str]:
        """Handle a key press and return action if any."""
        filtered_sites = self.get_filtered_sites()
        
        if key in ['up', 'k']:
            if self.selected_index > 0:
                self.selected_index -= 1
        elif key in ['down', 'j']:
            if self.selected_index < len(filtered_sites) - 1:
                self.selected_index += 1
        elif key in ['pageup', 'u']:
            self.selected_index = max(0, self.selected_index - 10)
        elif key in ['pagedown', 'd']:
            self.selected_index = min(len(filtered_sites) - 1, self.selected_index + 10)
        elif key in ['home', 'g']:
            self.selected_index = 0
        elif key in ['end', 'G']:
            self.selected_index = len(filtered_sites) - 1
        elif key == 'enter':
            if filtered_sites:
                site = filtered_sites[self.selected_index]
                if site.get('CustomDomain'):
                    return f"open:https://{site['CustomDomain']}"
        elif key == 'c':
            if filtered_sites:
                site = filtered_sites[self.selected_index]
                return f"check:{site['Project']}"
        elif key == 'r':
            self.load_sites()
            return "refresh"
        
        return None


def add_rich_commands(forest_group):
    """Add Rich-based interactive commands."""
    
    @forest_group.command(name="dashboard")
    @click.option('--auto-refresh', '-a', is_flag=True, help='Auto-refresh every 30 seconds')
    def dashboard(auto_refresh):
        """Interactive dashboard for forest management."""
        forest_path = Path.home() / "projects" / "float-workspace" / "artifacts" / "float-forest-navigator"
        dashboard = ForestDashboard(forest_path)
        
        # For demo, just show the layout
        # In a real implementation, you'd use prompt-toolkit or similar for key handling
        layout = dashboard.create_layout()
        
        if auto_refresh:
            with Live(layout, refresh_per_second=4, screen=True) as live:
                try:
                    while True:
                        time.sleep(30)
                        dashboard.load_sites()
                        live.update(dashboard.create_layout())
                except KeyboardInterrupt:
                    pass
        else:
            console.print(layout)
            console.print("\n[dim]Note: This is a static view. Use --auto-refresh for live updates.[/dim]")
            console.print("[dim]Full interactive mode requires additional setup with prompt-toolkit.[/dim]")
    
    @forest_group.command(name="monitor")
    @click.option('--interval', '-i', default=5, help='Check interval in seconds')
    def monitor(interval):
        """Monitor site status with live updates."""
        forest_path = Path.home() / "projects" / "float-workspace" / "artifacts" / "float-forest-navigator"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} sites"),
            console=console,
            transient=True
        ) as progress:
            
            task = progress.add_task("Checking sites...", total=100)
            
            # Simulate checking sites
            for i in range(100):
                progress.update(task, advance=1)
                time.sleep(interval / 100)
            
            console.print("[green]✓[/green] All sites checked!")
    
    @forest_group.command(name="tui")
    def tui():
        """Launch full terminal UI (requires prompt-toolkit)."""
        try:
            from .forest_interactive import InteractiveSelector, INTERACTIVE_AVAILABLE
            
            if not INTERACTIVE_AVAILABLE:
                console.print("[yellow]Full TUI requires prompt-toolkit:[/yellow]")
                console.print("  pip install prompt-toolkit")
                console.print("\nShowing static dashboard instead...")
                dashboard(auto_refresh=False)
            else:
                console.print("[cyan]Launching interactive TUI...[/cyan]")
                # Launch the interactive selector or a more complex TUI
        except ImportError:
            console.print("[red]Interactive features not available[/red]")