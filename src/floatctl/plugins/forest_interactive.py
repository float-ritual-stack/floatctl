"""Interactive forest management features for FloatCtl."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich import box

# For interactive selection
try:
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import Window, HSplit, VSplit
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.widgets import TextArea
    INTERACTIVE_AVAILABLE = True
except ImportError:
    INTERACTIVE_AVAILABLE = False

console = Console()


class InteractiveSelector:
    """Interactive site selector with arrow key navigation."""
    
    def __init__(self, items: List[Dict], title: str = "Select an item"):
        self.items = items
        self.title = title
        self.selected_index = 0
        self.filter_text = ""
        self.filtered_items = items.copy()
        
    def get_display_text(self) -> str:
        """Build the display text for the current state."""
        lines = [f"<b>{self.title}</b>", ""]
        
        if self.filter_text:
            lines.append(f"Filter: {self.filter_text}")
            lines.append("")
        
        lines.append("Use ↑/↓ arrows to navigate, Enter to select, / to filter, Esc to cancel")
        lines.append("")
        
        # Show items with selection indicator
        start_idx = max(0, self.selected_index - 10)
        end_idx = min(len(self.filtered_items), start_idx + 20)
        
        for i in range(start_idx, end_idx):
            item = self.filtered_items[i]
            prefix = "→ " if i == self.selected_index else "  "
            status_icon = "✓" if item.get('status') == 'OK' else "✗"
            
            line = f"{prefix}{status_icon} {item['name']}"
            if item.get('domain'):
                line += f" - {item['domain']}"
            
            if i == self.selected_index:
                line = f"<reverse>{line}</reverse>"
                
            lines.append(line)
        
        if len(self.filtered_items) > 20:
            lines.append(f"\n... and {len(self.filtered_items) - 20} more items")
            
        return "\n".join(lines)
    
    def filter_items(self):
        """Filter items based on filter text."""
        if not self.filter_text:
            self.filtered_items = self.items.copy()
        else:
            self.filtered_items = [
                item for item in self.items
                if self.filter_text.lower() in item['name'].lower() or
                   self.filter_text.lower() in item.get('domain', '').lower()
            ]
        self.selected_index = 0
    
    def run(self) -> Optional[Dict]:
        """Run the interactive selector and return selected item."""
        if not INTERACTIVE_AVAILABLE:
            console.print("[yellow]Interactive mode not available. Install prompt-toolkit:[/yellow]")
            console.print("  pip install prompt-toolkit")
            return None
            
        selected_item = None
        
        # Key bindings
        kb = KeyBindings()
        
        @kb.add('c-c')
        @kb.add('escape')
        def _(event):
            event.app.exit()
        
        @kb.add('enter')
        def _(event):
            nonlocal selected_item
            if self.filtered_items:
                selected_item = self.filtered_items[self.selected_index]
            event.app.exit()
        
        @kb.add('up')
        def _(event):
            if self.selected_index > 0:
                self.selected_index -= 1
                event.app.invalidate()
        
        @kb.add('down')
        def _(event):
            if self.selected_index < len(self.filtered_items) - 1:
                self.selected_index += 1
                event.app.invalidate()
        
        @kb.add('/')
        def _(event):
            # Start filtering
            self.filter_text = ""
            event.app.layout.focus(filter_input)
        
        # Filter input handling
        filter_input = TextArea(
            height=1,
            prompt='Filter: ',
            multiline=False
        )
        
        def on_text_changed(_):
            self.filter_text = filter_input.text
            self.filter_items()
            app.invalidate()
        
        filter_input.buffer.on_text_changed += on_text_changed
        
        # Layout
        content = FormattedTextControl(
            lambda: HTML(self.get_display_text()),
            focusable=True
        )
        
        layout = Layout(
            HSplit([
                Window(content),
                filter_input
            ])
        )
        
        # Application
        app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True
        )
        
        app.run()
        
        return selected_item


def add_interactive_commands(forest_group):
    """Add interactive commands to the forest group."""
    
    @forest_group.command(name="select")
    @click.option('--filter', '-f', help='Initial filter text')
    def select_site(filter):
        """Interactively select a site from the catalog."""
        # Load site data
        forest_path = Path.home() / "projects" / "float-workspace" / "artifacts" / "float-forest-navigator"
        
        try:
            # Load deployment status
            status_file = forest_path / "deployment-status.csv"
            sites = []
            
            if status_file.exists():
                import csv
                with open(status_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        sites.append({
                            'name': row['Project'],
                            'domain': row['CustomDomain'],
                            'status': row['Status'],
                            'last_checked': row['LastChecked']
                        })
            
            if not sites:
                console.print("[red]No sites found in deployment-status.csv[/red]")
                return
            
            # Create selector
            selector = InteractiveSelector(sites, "Select a FLOAT Forest Site")
            if filter:
                selector.filter_text = filter
                selector.filter_items()
            
            selected = selector.run()
            
            if selected:
                console.print(f"\n[green]Selected:[/green] {selected['name']}")
                if selected['domain']:
                    console.print(f"[blue]Domain:[/blue] {selected['domain']}")
                    console.print(f"[blue]Status:[/blue] {selected['status']}")
                    
                    # Offer actions
                    if Prompt.ask("\nOpen in browser?", choices=["y", "n"], default="y") == "y":
                        import webbrowser
                        webbrowser.open(f"https://{selected['domain']}")
            else:
                console.print("\n[yellow]No selection made[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    @forest_group.command(name="manage")
    def manage_sites():
        """Interactive site management interface."""
        if not INTERACTIVE_AVAILABLE:
            console.print("[yellow]Interactive mode requires prompt-toolkit:[/yellow]")
            console.print("  pip install prompt-toolkit")
            return
            
        console.print("[cyan]Interactive Forest Management[/cyan]")
        console.print("This feature is under development...")
        
        # TODO: Add full interactive management interface with:
        # - Site list with status indicators
        # - Actions menu (deploy, check status, view logs, etc.)
        # - Multi-select for batch operations
        # - Real-time status updates