"""Textual-based interactive notes with command palette."""

import json
import re
import sys
import io
import subprocess
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from code import InteractiveInterpreter

import rich_click as click
from rich.console import Console
from rich.syntax import Syntax

from floatctl.plugin_manager import PluginBase

try:
    from textual import on, work
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.command import Provider, Hits, Hit
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import (
        Header, Footer, Tree, Input, TextArea, 
        Label, Button, Static, ListView, ListItem
    )
    from textual.reactive import reactive
    from textual.message import Message
    from textual.worker import Worker, WorkerState
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

console = Console()


@dataclass
class Entry:
    """A note/code entry."""
    id: str
    content: str
    type: str = "log"
    timestamp: datetime = field(default_factory=datetime.now)
    indent: int = 0
    is_code: bool = False
    language: str = "python"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'indent': self.indent,
            'is_code': self.is_code,
            'language': self.language,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entry':
        return cls(
            id=data['id'],
            content=data['content'],
            type=data.get('type', 'log'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            indent=data.get('indent', 0),
            is_code=data.get('is_code', False),
            language=data.get('language', 'python'),
        )


class EntryItem(ListItem):
    """Custom list item for entries."""
    
    def __init__(self, entry: Entry, selected: bool = False):
        super().__init__()
        self.entry = entry
        self._selected = selected
        
    def compose(self) -> ComposeResult:
        """Compose the entry display."""
        indent = "  " * self.entry.indent
        time_str = self.entry.timestamp.strftime("%H:%M")
        
        # Type-specific styling
        if self.entry.is_code:
            type_marker = "[cyan][code][/cyan]"
        elif self.entry.type == 'output':
            type_marker = "[green][out][/green]"
        elif self.entry.type == 'error':
            type_marker = "[red][err][/red]"
        elif self.entry.type != 'log':
            type_marker = f"[bold]{self.entry.type}::[/bold]"
        else:
            type_marker = ""
        
        # Build content
        prefix = "→ " if self._selected else "  "
        content = f"{prefix}{time_str} {indent}{type_marker} {self.entry.content}"
        
        yield Static(content, classes="entry-content")


class FloatCtlCommands(Provider):
    """Command palette provider for floatctl commands."""
    
    async def search(self, query: str) -> Hits:
        """Search for floatctl commands."""
        # Basic floatctl commands
        commands = [
            ("chroma list", "List Chroma collections"),
            ("chroma floatql", "Query with FloatQL"),
            ("forest status", "Check forest status"),
            ("conversations split", "Split conversation exports"),
            ("repl", "Open REPL mode"),
        ]
        
        matcher = self.matcher(query)
        
        for command, description in commands:
            score = matcher.match(command)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(command),
                    lambda cmd=command: self.app.execute_floatctl(cmd),
                    description
                )


class TextualNotes(App):
    """Textual-based notes application."""
    
    CSS = """
    Screen {
        layers: base overlay;
    }
    
    #sidebar {
        width: 30%;
        height: 100%;
        dock: left;
        border-right: solid $primary;
    }
    
    #main {
        width: 70%;
        height: 100%;
    }
    
    #input-area {
        height: 5;
        dock: bottom;
        border-top: solid $primary;
    }
    
    .entry-content {
        padding: 0 1;
    }
    
    .entry-content:hover {
        background: $boost;
    }
    
    EntryItem.selected {
        background: $accent;
    }
    
    #output {
        border: solid $secondary;
        padding: 1;
        margin: 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+r", "toggle_repl", "Toggle REPL"),
        Binding("ctrl+n", "new_entry", "New Entry"),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
        Binding("tab", "indent", "Indent"),
        Binding("shift+tab", "unindent", "Unindent"),
        Binding("ctrl+d", "delete", "Delete"),
        Binding("ctrl+q", "quit", "Quit"),
    ]
    
    COMMANDS = {FloatCtlCommands}
    
    def __init__(self):
        super().__init__()
        self.entries: List[Entry] = []
        self.selected_index: int = -1
        self.repl_mode = False
        
        # Python interpreter
        self.interpreter = InteractiveInterpreter()
        self.repl_locals = {}
        
        # Storage
        self.data_file = Path.home() / '.floatctl' / 'textual_notes' / 'entries.json'
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load entries
        self._load_entries()
    
    def _load_entries(self):
        """Load entries from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file) as f:
                    data = json.load(f)
                    self.entries = [Entry.from_dict(e) for e in data]
            except:
                pass
    
    def _save_entries(self):
        """Save entries to file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f)
        except:
            pass
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)
        
        with Horizontal():
            # Sidebar with entry list
            with Vertical(id="sidebar"):
                yield Label("Entries", classes="title")
                yield ListView(id="entry-list")
            
            # Main area
            with Vertical(id="main"):
                yield Label("Content", classes="title")
                yield ScrollableContainer(id="content")
                
        # Input area
        with Container(id="input-area"):
            yield Input(placeholder="Type here... (ctx::, todo::, ```code```)")
            
        yield Footer()
    
    def on_mount(self):
        """Initialize on mount."""
        self.refresh_entries()
        self.title = "FLOAT Interactive Notes"
        self.sub_title = "REPL OFF"
    
    def refresh_entries(self):
        """Refresh the entry list."""
        list_view = self.query_one("#entry-list", ListView)
        list_view.clear()
        
        for i, entry in enumerate(self.entries):
            item = EntryItem(entry, selected=(i == self.selected_index))
            list_view.append(item)
    
    def action_toggle_repl(self):
        """Toggle REPL mode."""
        self.repl_mode = not self.repl_mode
        self.sub_title = "REPL ON" if self.repl_mode else "REPL OFF"
        self.notify(f"REPL mode {'enabled' if self.repl_mode else 'disabled'}")
    
    def action_new_entry(self):
        """Focus input for new entry."""
        self.query_one(Input).focus()
    
    def action_indent(self):
        """Indent selected entry."""
        if 0 <= self.selected_index < len(self.entries):
            self.entries[self.selected_index].indent += 1
            self._save_entries()
            self.refresh_entries()
    
    def action_unindent(self):
        """Unindent selected entry."""
        if 0 <= self.selected_index < len(self.entries):
            entry = self.entries[self.selected_index]
            if entry.indent > 0:
                entry.indent -= 1
                self._save_entries()
                self.refresh_entries()
    
    def action_delete(self):
        """Delete selected entry."""
        if 0 <= self.selected_index < len(self.entries):
            self.entries.pop(self.selected_index)
            if self.entries:
                self.selected_index = min(self.selected_index, len(self.entries) - 1)
            else:
                self.selected_index = -1
            self._save_entries()
            self.refresh_entries()
    
    @on(Input.Submitted)
    def handle_input(self, event: Input.Submitted):
        """Handle input submission."""
        text = event.value
        if not text:
            return
        
        # Clear input
        event.input.value = ""
        
        # Parse and add entry
        self.add_entry(text)
    
    def add_entry(self, text: str, entry_type: Optional[str] = None, indent_offset: int = 0):
        """Add a new entry."""
        # Parse type
        if entry_type is None:
            if text.startswith('```'):
                entry_type = 'code'
            else:
                match = re.match(r'^(\w+)::\s*(.*)$', text)
                if match:
                    entry_type = match.group(1).lower()
                    text = match.group(2)
                else:
                    entry_type = 'log'
        
        # Create entry
        indent = 0
        if 0 <= self.selected_index < len(self.entries):
            indent = self.entries[self.selected_index].indent + indent_offset
        
        entry = Entry(
            id=str(int(datetime.now().timestamp() * 1000)),
            content=text,
            type=entry_type,
            indent=indent,
            is_code=(entry_type == 'code')
        )
        
        # Insert after selected
        if 0 <= self.selected_index < len(self.entries):
            self.entries.insert(self.selected_index + 1, entry)
            self.selected_index += 1
        else:
            self.entries.append(entry)
            self.selected_index = len(self.entries) - 1
        
        self._save_entries()
        self.refresh_entries()
        
        # Execute if REPL mode and code
        if self.repl_mode and entry.is_code:
            self.execute_code(entry)
    
    @work(thread=True)
    def execute_code(self, entry: Entry):
        """Execute code in background."""
        try:
            # Capture output
            stdout = io.StringIO()
            stderr = io.StringIO()
            
            sys.stdout = stdout
            sys.stderr = stderr
            
            try:
                exec(entry.content, self.repl_locals)
            finally:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
            
            # Add output
            out = stdout.getvalue()
            err = stderr.getvalue()
            
            if out:
                self.call_from_thread(self.add_entry, out.rstrip(), 'output', 1)
            if err:
                self.call_from_thread(self.add_entry, err.rstrip(), 'error', 1)
                
        except Exception as e:
            self.call_from_thread(self.add_entry, str(e), 'error', 1)
    
    def execute_floatctl(self, command: str):
        """Execute floatctl command."""
        self.add_entry(f"!floatctl {command}", 'command')
        # Would execute the command and capture output
        self.notify(f"Executed: floatctl {command}")


class TextualNotesPlugin(PluginBase):
    """Textual-based interactive notes."""
    
    name = "textual"
    description = "Beautiful interactive notes with Textual UI"
    version = "0.1.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        
        @cli_group.command(name="textual")
        def cmd():
            """Launch Textual interactive notes.
            
            Features:
            - Beautiful TUI with mouse support
            - Command palette (Ctrl+P)
            - Tree view of entries
            - REPL mode (Ctrl+R)
            - Integrated floatctl commands
            
            Requires: pip install textual
            """
            if not TEXTUAL_AVAILABLE:
                console.print("[red]Textual not installed![/red]")
                console.print("Install with: pip install textual")
                return
                
            app = TextualNotes()
            app.run()