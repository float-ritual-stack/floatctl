"""Hybrid Notes REPL - A structured logging interface inspired by FLOAT methodology."""

import os
import json
import shlex
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import re

import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import box
from rich.syntax import Syntax
from rich.text import Text
from rich.live import Live
from rich.layout import Layout

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.formatted_text import HTML, ANSI
    from prompt_toolkit.styles import Style
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.application import get_app
    REPL_AVAILABLE = True
except ImportError:
    REPL_AVAILABLE = False

console = Console()


class Mode(Enum):
    """REPL interaction modes."""
    CHAT = "chat"
    EDIT = "edit"
    COMMAND = "command"


@dataclass
class Entry:
    """A single entry in the hybrid notes system."""
    id: str
    content: str
    type: str = "log"
    timestamp: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    indent: int = 0
    parent_id: Optional[str] = None
    children: List['Entry'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'indent': self.indent,
            'parent_id': self.parent_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entry':
        """Create entry from dictionary."""
        entry = cls(
            id=data['id'],
            content=data['content'],
            type=data.get('type', 'log'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            indent=data.get('indent', 0),
            parent_id=data.get('parent_id'),
            metadata=data.get('metadata', {})
        )
        if data.get('updated_at'):
            entry.updated_at = datetime.fromisoformat(data['updated_at'])
        return entry


class HybridREPL:
    """Enhanced REPL with hybrid notes functionality."""
    
    def __init__(self, name: str = "floatctl"):
        self.name = name
        self.entries: List[Entry] = []
        self.mode = Mode.CHAT
        self.selected_index: Optional[int] = None
        self.show_details = False
        self.show_help = False
        
        # File paths
        self.data_dir = Path.home() / '.floatctl' / 'hybrid'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.entries_file = self.data_dir / 'entries.json'
        self.history_file = self.data_dir / 'history'
        
        # Load existing entries
        self._load_entries()
        
        # Type patterns for entry parsing
        self.type_patterns = {
            'ctx': 'context',
            'highlight': 'highlight',
            'mode': 'mode',
            'project': 'project',
            'todo': 'todo',
            'note': 'note',
            'idea': 'idea',
            'bridge': 'bridge',
            'dispatch': 'dispatch'
        }
        
    def _load_entries(self):
        """Load entries from file."""
        if self.entries_file.exists():
            try:
                with open(self.entries_file, 'r') as f:
                    data = json.load(f)
                    self.entries = [Entry.from_dict(e) for e in data]
            except Exception as e:
                console.print(f"[red]Error loading entries: {e}[/red]")
    
    def _save_entries(self):
        """Save entries to file."""
        try:
            with open(self.entries_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving entries: {e}[/red]")
    
    def parse_entry_input(self, input_text: str) -> Tuple[str, str]:
        """Parse input to extract type and content."""
        # Check for type:: pattern
        match = re.match(r'^(\w+)::\s*(.*)$', input_text)
        if match:
            type_key = match.group(1).lower()
            content = match.group(2)
            # Map to known types or use as-is
            entry_type = self.type_patterns.get(type_key, type_key)
            return entry_type, content
        
        # Check for special commands
        if input_text.startswith('/'):
            return 'command', input_text[1:]
        
        return 'log', input_text
    
    def add_entry(self, input_text: str):
        """Add a new entry."""
        if not input_text.strip():
            return
        
        entry_type, content = self.parse_entry_input(input_text)
        
        # Create new entry
        new_entry = Entry(
            id=str(int(datetime.now().timestamp() * 1000)),
            content=content,
            type=entry_type,
            indent=self.entries[self.selected_index].indent if self.selected_index is not None else 0
        )
        
        # Insert after selected entry or at end
        if self.selected_index is not None:
            self.entries.insert(self.selected_index + 1, new_entry)
            self.selected_index += 1
        else:
            self.entries.append(new_entry)
            self.selected_index = len(self.entries) - 1
        
        self._save_entries()
    
    def update_entry(self, index: int, content: str):
        """Update an existing entry."""
        if 0 <= index < len(self.entries):
            entry_type, parsed_content = self.parse_entry_input(content)
            self.entries[index].content = parsed_content
            self.entries[index].type = entry_type
            self.entries[index].updated_at = datetime.now()
            self._save_entries()
    
    def indent_entry(self, index: int, increase: bool):
        """Change entry indentation."""
        if 0 <= index < len(self.entries):
            entry = self.entries[index]
            if increase:
                entry.indent = min(6, entry.indent + 1)
            else:
                entry.indent = max(0, entry.indent - 1)
            self._save_entries()
    
    def move_selection(self, direction: int):
        """Move selection up or down."""
        if not self.entries:
            return
        
        if self.selected_index is None:
            self.selected_index = 0 if direction > 0 else len(self.entries) - 1
        else:
            self.selected_index = max(0, min(len(self.entries) - 1, self.selected_index + direction))
    
    def format_entry(self, entry: Entry, is_selected: bool = False) -> Text:
        """Format an entry for display."""
        text = Text()
        
        # Add selection indicator
        if is_selected:
            text.append("→ ", style="bold green")
        else:
            text.append("  ")
        
        # Add indentation
        text.append("  " * entry.indent)
        
        # Add type marker if not 'log'
        if entry.type != 'log':
            text.append(f"{entry.type}::", style="green")
            text.append(" ")
        
        # Add content
        text.append(entry.content)
        
        # Add details if enabled
        if self.show_details:
            text.append("\n")
            text.append("  " * (entry.indent + 1))
            text.append(
                f"{entry.timestamp.strftime('%H:%M:%S')} · ID: {entry.id[:6]}",
                style="dim"
            )
        
        return text
    
    def render_entries_panel(self) -> Panel:
        """Render the entries panel."""
        if not self.entries:
            content = Text("No entries yet. Start typing to add your first entry.", style="dim")
        else:
            content = Text()
            for i, entry in enumerate(self.entries):
                if i > 0:
                    content.append("\n")
                content.append(self.format_entry(entry, i == self.selected_index))
        
        return Panel(
            content,
            title="[bold cyan]Structured View[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
    
    def render_status_bar(self) -> Text:
        """Render the status bar."""
        parts = []
        
        # Mode indicator
        mode_style = {
            Mode.CHAT: "green",
            Mode.EDIT: "yellow",
            Mode.COMMAND: "blue"
        }[self.mode]
        parts.append(f"[{mode_style}]{self.mode.value.upper()}[/{mode_style}]")
        
        # Selection info
        if self.selected_index is not None:
            parts.append(f"Entry #{self.selected_index + 1}/{len(self.entries)}")
        
        # Shortcuts
        parts.append("Alt+↑/↓: Navigate · Tab: Indent · Ctrl+E: Mode · Ctrl+H: Help")
        
        return Text(" · ".join(parts), style="dim")
    
    def render_help_panel(self) -> Panel:
        """Render the help panel."""
        help_text = """
[bold cyan]Keyboard Shortcuts[/bold cyan]

[yellow]Navigation:[/yellow]
  Alt + ↑/↓     Select previous/next entry
  Home/End      Jump to first/last entry

[yellow]Editing:[/yellow]
  Tab           Indent selected entry
  Shift + Tab   Unindent selected entry
  Enter         Add new entry (in chat mode)
  Ctrl + D      Delete selected entry

[yellow]Modes:[/yellow]
  Ctrl + E      Toggle between chat/edit mode
  Ctrl + C      Command mode
  Esc           Return to chat mode

[yellow]Display:[/yellow]
  Ctrl + H      Show/hide this help
  Ctrl + I      Toggle details view
  Ctrl + S      Save session

[yellow]Entry Types:[/yellow]
  type::        Set entry type (ctx::, highlight::, todo::, etc.)
  /command      Execute command (in chat mode)
"""
        return Panel(
            help_text.strip(),
            title="[bold green]Help[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
    
    def render_ui(self) -> Layout:
        """Render the full UI."""
        layout = Layout()
        
        # Main layout structure
        layout.split_column(
            Layout(name="header", size=7),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=1)
        )
        
        # Header
        header_text = """[bold green]Hybrid Notes[/bold green]
[dim]Chat mode for quick logging · Edit mode for full control[/dim]"""
        layout["header"].update(Panel(header_text, box=box.SIMPLE))
        
        # Main content
        if self.show_help:
            layout["main"].update(self.render_help_panel())
        else:
            layout["main"].update(self.render_entries_panel())
        
        # Footer
        layout["footer"].update(self.render_status_bar())
        
        return layout
    
    def setup_key_bindings(self, session: PromptSession) -> KeyBindings:
        """Setup key bindings for the prompt session."""
        kb = KeyBindings()
        
        @kb.add(Keys.ControlE)
        def toggle_mode(event):
            """Toggle between chat and edit mode."""
            self.mode = Mode.EDIT if self.mode == Mode.CHAT else Mode.CHAT
            self.refresh_display()
        
        @kb.add(Keys.ControlH)
        def toggle_help(event):
            """Toggle help display."""
            self.show_help = not self.show_help
            self.refresh_display()
        
        @kb.add(Keys.ControlI)
        def toggle_details(event):
            """Toggle details view."""
            self.show_details = not self.show_details
            self.refresh_display()
        
        @kb.add(Keys.Escape, 'Up')  # Alt+Up
        def move_up(event):
            """Move selection up."""
            self.move_selection(-1)
            self.refresh_display()
        
        @kb.add(Keys.Escape, 'Down')  # Alt+Down
        def move_down(event):
            """Move selection down."""
            self.move_selection(1)
            self.refresh_display()
        
        @kb.add(Keys.Tab)
        def indent(event):
            """Indent selected entry."""
            if self.selected_index is not None:
                self.indent_entry(self.selected_index, True)
                self.refresh_display()
        
        @kb.add(Keys.BackTab)  # Shift+Tab
        def unindent(event):
            """Unindent selected entry."""
            if self.selected_index is not None:
                self.indent_entry(self.selected_index, False)
                self.refresh_display()
        
        return kb
    
    def refresh_display(self):
        """Refresh the display (placeholder for Live update)."""
        # This would be called to update the Live display
        pass
    
    def run(self):
        """Run the hybrid REPL."""
        if not REPL_AVAILABLE:
            console.print("[red]Hybrid REPL requires prompt-toolkit:[/red]")
            console.print("  pip install prompt-toolkit")
            return
        
        # Initial display
        console.clear()
        
        with Live(self.render_ui(), refresh_per_second=4, screen=True) as live:
            # Create prompt session
            session = PromptSession(
                history=FileHistory(str(self.history_file)),
                auto_suggest=AutoSuggestFromHistory(),
                key_bindings=self.setup_key_bindings(session)
            )
            
            # Store live context for refresh
            self._live = live
            
            def refresh_display():
                live.update(self.render_ui())
            
            self.refresh_display = refresh_display
            
            # Main loop
            while True:
                try:
                    # Update display
                    refresh_display()
                    
                    # Get input based on mode
                    if self.mode == Mode.CHAT:
                        prompt_text = "/ "
                        input_text = session.prompt(prompt_text)
                        
                        if input_text.strip():
                            self.add_entry(input_text)
                    
                    elif self.mode == Mode.EDIT and self.selected_index is not None:
                        # In edit mode, allow editing selected entry
                        entry = self.entries[self.selected_index]
                        prompt_text = f"Edit [{entry.type}]> "
                        
                        # Pre-fill with current content
                        input_text = session.prompt(
                            prompt_text,
                            default=f"{entry.type}:: {entry.content}" if entry.type != 'log' else entry.content
                        )
                        
                        if input_text.strip():
                            self.update_entry(self.selected_index, input_text)
                    
                except KeyboardInterrupt:
                    continue
                except EOFError:
                    break
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
        
        console.print("\n[green]Session saved. Goodbye! 🌲[/green]")


# Plugin integration
class HybridREPLPlugin:
    """Plugin wrapper for hybrid REPL."""
    
    def __init__(self):
        self.name = "hybrid"
        self.description = "Hybrid notes interface with structured logging"
        self.version = "0.1.0"
    
    def register_commands(self, cli_group: click.Group):
        """Register the hybrid command."""
        
        @cli_group.command(name="hybrid")
        @click.option('--import', 'import_file', type=click.Path(exists=True),
                      help='Import entries from JSON file')
        @click.option('--export', 'export_file', type=click.Path(),
                      help='Export entries to JSON file')
        def hybrid_cmd(import_file, export_file):
            """Launch the hybrid notes interface.
            
            A structured logging system with:
            - Multiple entry types (ctx::, highlight::, todo::, etc.)
            - Hierarchical indentation
            - Keyboard navigation
            - Chat and edit modes
            - Persistent storage
            """
            repl = HybridREPL()
            
            if import_file:
                # Import functionality
                console.print(f"[yellow]Importing from {import_file}...[/yellow]")
                # Implementation here
                
            elif export_file:
                # Export functionality
                console.print(f"[yellow]Exporting to {export_file}...[/yellow]")
                # Implementation here
                
            else:
                # Run the REPL
                repl.run()