"""FLOAT Notes - A Textual-based interactive notes system."""

import json
import re
import sys
import io
import subprocess
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Iterable
from code import InteractiveInterpreter

import rich_click as click
from rich.console import Console, RenderableType
from rich.syntax import Syntax
from rich.text import Text

from floatctl.plugin_manager import PluginBase

try:
    from textual import on, work
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.command import Provider, Hits, Hit, DiscoveryHit
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, VerticalScroll
    from textual.widgets import (
        Header, Footer, Input, 
        Label, Button, Static, Markdown
    )
    from textual.widget import Widget
    from textual.reactive import reactive
    from textual.screen import ModalScreen
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
    parent_id: Optional[str] = None
    children: List['Entry'] = field(default_factory=list)
    collapsed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_code(self) -> bool:
        return self.type in ('code', 'python', 'shell')
    
    @property
    def is_output(self) -> bool:
        return self.type in ('output', 'error')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'parent_id': self.parent_id,
            'children': [c.to_dict() for c in self.children],
            'collapsed': self.collapsed,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entry':
        entry = cls(
            id=data['id'],
            content=data['content'],
            type=data.get('type', 'log'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            parent_id=data.get('parent_id'),
            collapsed=data.get('collapsed', False),
            metadata=data.get('metadata', {}),
        )
        entry.children = [cls.from_dict(c) for c in data.get('children', [])]
        return entry


class EntryWidget(Static):
    """Widget for displaying an entry."""
    
    def __init__(self, entry: Entry, depth: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.entry = entry
        self.depth = depth
        self.selected = False
        
    def render(self) -> RenderableType:
        """Render the entry."""
        indent = "  " * self.depth
        time_str = self.entry.timestamp.strftime("%H:%M")
        
        # Type-specific styling
        if self.entry.is_code:
            type_marker = "[cyan][code][/cyan]"
            content = Syntax(self.entry.content, "python", theme="monokai", line_numbers=False)
        elif self.entry.type == 'output':
            type_marker = "[green][out][/green]"
            content = Text(self.entry.content, style="green")
        elif self.entry.type == 'error':
            type_marker = "[red][err][/red]"
            content = Text(self.entry.content, style="red")
        elif self.entry.type != 'log':
            type_marker = f"[bold yellow]{self.entry.type}::[/bold yellow]"
            content = self.entry.content
        else:
            type_marker = ""
            content = self.entry.content
        
        # Selection indicator
        prefix = "▶ " if self.selected else "  "
        
        # Collapse indicator
        if self.entry.children:
            collapse = "[dim]▼[/dim] " if not self.entry.collapsed else "[dim]▶[/dim] "
        else:
            collapse = "  "
        
        # Build the display
        line = f"{prefix}{time_str} {indent}{collapse}{type_marker}{content}"
        return Text(line)


class FloatCtlProvider(Provider):
    """Command provider for floatctl commands."""
    
    async def discover(self) -> Hits:
        """Discover commands for the command palette."""
        yield DiscoveryHit(
            "chroma", 
            "list", 
            "List all Chroma collections",
            action=lambda: self.app.run_floatctl("chroma list")
        )
        yield DiscoveryHit(
            "chroma", 
            "floatql",
            "Query with FloatQL", 
            action=lambda: self.app.prompt_floatql()
        )
        yield DiscoveryHit(
            "forest",
            "status",
            "Check forest status",
            action=lambda: self.app.run_floatctl("forest status")
        )
        yield DiscoveryHit(
            "repl",
            "toggle",
            "Toggle REPL mode",
            action=lambda: self.app.action_toggle_repl()
        )
    
    async def search(self, query: str) -> Hits:
        """Search for commands."""
        # Use the built-in discovery search
        async for hit in super().search(query):
            yield hit


class InputModal(ModalScreen):
    """Modal dialog for input."""
    
    def __init__(self, prompt: str, callback):
        super().__init__()
        self.prompt = prompt
        self.callback = callback
        
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.prompt)
            yield Input(id="modal-input")
            with Horizontal():
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", id="cancel")
    
    @on(Button.Pressed, "#ok")
    def handle_ok(self):
        value = self.query_one("#modal-input", Input).value
        self.dismiss(value)
        if value and self.callback:
            self.callback(value)
    
    @on(Button.Pressed, "#cancel")
    def handle_cancel(self):
        self.dismiss(None)


class FloatNotes(App):
    """FLOAT Notes application."""
    
    CSS = """
    Screen {
        layers: base overlay notes;
        overflow: hidden;
    }
    
    #tree-view {
        dock: left;
        width: 40%;
        height: 100%;
        border-right: solid $primary;
        background: $surface;
        layer: notes;
    }
    
    #detail-view {
        width: 60%;
        padding: 1;
        layer: notes;
    }
    
    #input-container {
        dock: bottom;
        height: auto;
        min-height: 3;
        max-height: 10;
        border-top: solid $primary;
        background: $surface;
        padding: 0 1;
    }
    
    EntryWidget {
        width: 100%;
        height: auto;
    }
    
    EntryWidget:hover {
        background: $boost;
    }
    
    EntryWidget.selected {
        background: $accent;
    }
    
    .entry-tree {
        padding: 1;
        width: 100%;
        height: 100%;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text-muted;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+r", "toggle_repl", "REPL"),
        Binding("alt+up", "move_up", "Up", show=False),
        Binding("alt+down", "move_down", "Down", show=False),
        Binding("ctrl+right", "indent", "Indent", show=False),
        Binding("ctrl+left", "unindent", "Unindent", show=False),
        Binding("ctrl+d", "delete", "Delete"),
        Binding("ctrl+q", "quit", "Quit"),
    ]
    
    COMMANDS = {FloatCtlProvider}
    
    # Reactive properties
    repl_mode = reactive(False)
    selected_entry: reactive[Optional[Entry]] = reactive(None)
    
    def __init__(self):
        super().__init__()
        self.entries: List[Entry] = []
        self.entry_widgets: Dict[str, EntryWidget] = {}
        self.selected_index: int = -1
        
        # Python interpreter
        self.interpreter = InteractiveInterpreter()
        self.repl_locals = {}
        self.repl_locals['floatctl'] = self.run_floatctl
        
        # Storage
        self.data_file = Path.home() / '.floatctl' / 'float_notes' / 'entries.json'
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
            except Exception as e:
                self.notify(f"Error loading: {e}", severity="error")
    
    def _save_entries(self):
        """Save entries to file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
            pass  # Silent save - no notification
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Main content area
        with VerticalScroll(id="entry-list"):
            yield Container(id="entry-tree")
        
        # Input at bottom
        with Container(id="input-line"):
            yield Input(
                placeholder="/ type here... Alt+↑/↓ navigate, Ctrl+←/→ indent, Ctrl+R REPL",
                id="main-input"
            )
    
    def on_mount(self):
        """Initialize on mount."""
        self.title = "FLOAT Notes"
        self.sub_title = "REPL OFF"
        self.refresh_entries()
        
        # Focus input
        self.set_focus(self.query_one("#main-input", Input))
    
    def watch_repl_mode(self, old_value: bool, new_value: bool):
        """React to REPL mode changes."""
        self.sub_title = "REPL ON" if new_value else "REPL OFF"
    
    def refresh_entries(self):
        """Refresh the entry tree."""
        tree_container = self.query_one("#entry-tree")
        tree_container.remove_children()
        self.entry_widgets.clear()
        
        # Build tree recursively
        def add_entries(entries: List[Entry], parent: Widget, depth: int = 0):
            for entry in entries:
                widget = EntryWidget(entry, depth)
                widget.selected = (entry == self.selected_entry)
                self.entry_widgets[entry.id] = widget
                parent.mount(widget)
                
                # Add children if not collapsed
                if entry.children and not entry.collapsed:
                    add_entries(entry.children, parent, depth + 1)
        
        add_entries(self.entries, tree_container)
    
    def action_toggle_repl(self):
        """Toggle REPL mode."""
        self.repl_mode = not self.repl_mode
    
    def action_new_entry(self):
        """Focus input for new entry."""
        self.set_focus(self.query_one("#main-input", Input))
    
    def action_move_up(self):
        """Move selection up."""
        flat_entries = self._flatten_entries()
        if flat_entries and self.selected_index > 0:
            self.selected_index -= 1
            self.selected_entry = flat_entries[self.selected_index]
            self.refresh_entries()
    
    def action_move_down(self):
        """Move selection down."""
        flat_entries = self._flatten_entries()
        if flat_entries and self.selected_index < len(flat_entries) - 1:
            self.selected_index += 1
            self.selected_entry = flat_entries[self.selected_index]
            self.refresh_entries()
    
    def action_indent(self):
        """Indent selected entry (make it a child of previous)."""
        if not self.selected_entry:
            return
            
        flat_entries = self._flatten_entries()
        if self.selected_index > 0:
            # Make it a child of the previous entry
            parent = flat_entries[self.selected_index - 1]
            
            # Remove from current parent
            if self.selected_entry.parent_id:
                old_parent = self._find_entry(self.selected_entry.parent_id)
                if old_parent:
                    old_parent.children.remove(self.selected_entry)
            else:
                self.entries.remove(self.selected_entry)
            
            # Add to new parent
            self.selected_entry.parent_id = parent.id
            parent.children.append(self.selected_entry)
            
            self._save_entries()
            self.refresh_entries()
    
    def action_unindent(self):
        """Unindent selected entry (move to parent's level)."""
        if not self.selected_entry or not self.selected_entry.parent_id:
            return
            
        parent = self._find_entry(self.selected_entry.parent_id)
        if not parent:
            return
            
        # Remove from parent
        parent.children.remove(self.selected_entry)
        
        # Add after parent at root level or grandparent level
        if parent.parent_id:
            grandparent = self._find_entry(parent.parent_id)
            if grandparent:
                idx = grandparent.children.index(parent)
                grandparent.children.insert(idx + 1, self.selected_entry)
                self.selected_entry.parent_id = grandparent.id
        else:
            idx = self.entries.index(parent)
            self.entries.insert(idx + 1, self.selected_entry)
            self.selected_entry.parent_id = None
        
        self._save_entries()
        self.refresh_entries()
    
    def action_collapse(self):
        """Collapse selected entry."""
        if self.selected_entry and self.selected_entry.children:
            self.selected_entry.collapsed = True
            self.refresh_entries()
    
    def action_expand(self):
        """Expand selected entry."""
        if self.selected_entry and self.selected_entry.children:
            self.selected_entry.collapsed = False
            self.refresh_entries()
    
    def action_delete(self):
        """Delete selected entry."""
        if not self.selected_entry:
            return
            
        # Remove from parent or root
        if self.selected_entry.parent_id:
            parent = self._find_entry(self.selected_entry.parent_id)
            if parent:
                parent.children.remove(self.selected_entry)
        else:
            self.entries.remove(self.selected_entry)
        
        self.selected_entry = None
        self._save_entries()
        self.refresh_entries()
    
    def action_save(self):
        """Save entries."""
        self._save_entries()
    
    def action_multiline(self):
        """Enter multiline mode."""
        # TODO: Implement multiline input
        self.notify("Multiline mode not yet implemented")
    
    @on(Input.Submitted, "#main-input")
    def handle_input(self, event: Input.Submitted):
        """Handle input submission."""
        text = event.value
        if not text:
            return
        
        # Clear input
        event.input.value = ""
        
        # Add entry
        self.add_entry(text)
    
    # TODO: Add click handling for entry selection
    
    def add_entry(self, text: str, parent: Optional[Entry] = None):
        """Add a new entry."""
        # Parse type
        entry_type = 'log'
        content = text
        
        # Check for code blocks
        if text.startswith('```'):
            entry_type = 'code'
            lines = text.split('\n')
            if len(lines) > 2 and lines[-1].strip() == '```':
                content = '\n'.join(lines[1:-1])
            else:
                content = '\n'.join(lines[1:]) if len(lines) > 1 else ''
        else:
            # Check for type markers
            match = re.match(r'^(\w+)::\s*(.*)$', text)
            if match:
                entry_type = match.group(1).lower()
                content = match.group(2)
        
        # Create entry
        entry = Entry(
            id=str(int(datetime.now().timestamp() * 1000000)),  # microsecond precision
            content=content,
            type=entry_type,
            parent_id=parent.id if parent else None
        )
        
        # Add to tree
        if parent:
            parent.children.append(entry)
        else:
            # Add after selected entry at same level
            if self.selected_entry:
                if self.selected_entry.parent_id:
                    parent_entry = self._find_entry(self.selected_entry.parent_id)
                    if parent_entry:
                        idx = parent_entry.children.index(self.selected_entry)
                        parent_entry.children.insert(idx + 1, entry)
                        entry.parent_id = parent_entry.id
                else:
                    idx = self.entries.index(self.selected_entry)
                    self.entries.insert(idx + 1, entry)
            else:
                self.entries.append(entry)
        
        # Select new entry
        self.selected_entry = entry
        self.selected_index = len(self._flatten_entries()) - 1
        
        self._save_entries()
        self.refresh_entries()
        
        # Execute if REPL mode and code
        if self.repl_mode and entry.is_code:
            self.execute_code(entry)
    
    # Removed update_detail_view - we're keeping it simple
    
    @work(thread=True)
    def execute_code(self, entry: Entry):
        """Execute code in background."""
        try:
            # Capture output
            stdout = io.StringIO()
            stderr = io.StringIO()
            
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = stdout
            sys.stderr = stderr
            
            try:
                # Try eval first
                try:
                    result = eval(entry.content, self.repl_locals)
                    if result is not None:
                        print(result)
                except:
                    # Fall back to exec
                    exec(entry.content, self.repl_locals)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
            # Get output
            out = stdout.getvalue()
            err = stderr.getvalue()
            
            # Add output entries
            if out:
                output_entry = Entry(
                    id=str(int(datetime.now().timestamp() * 1000000)),
                    content=out.rstrip(),
                    type='output',
                    parent_id=entry.id
                )
                entry.children.append(output_entry)
                self.call_from_thread(self.refresh_entries)
            if err:
                error_entry = Entry(
                    id=str(int(datetime.now().timestamp() * 1000000)),
                    content=err.rstrip(),
                    type='error',
                    parent_id=entry.id
                )
                entry.children.append(error_entry)
                self.call_from_thread(self.refresh_entries)
                
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            error_entry = Entry(
                id=str(int(datetime.now().timestamp() * 1000000)),
                content=error_msg,
                type='error',
                parent_id=entry.id
            )
            entry.children.append(error_entry)
            self.call_from_thread(self.refresh_entries)
    
    def run_floatctl(self, command: str):
        """Run a floatctl command."""
        self.add_entry(f"!floatctl {command}")
        # TODO: Actually execute the command
        self.notify(f"Executed: floatctl {command}")
    
    def prompt_floatql(self):
        """Prompt for FloatQL query."""
        def handle_query(query: str):
            if query:
                self.run_floatctl(f"chroma floatql '{query}'")
        
        self.push_screen(InputModal("Enter FloatQL query:", handle_query))
    
    def _flatten_entries(self) -> List[Entry]:
        """Flatten the entry tree for navigation."""
        flat = []
        
        def flatten(entries: List[Entry]):
            for entry in entries:
                flat.append(entry)
                if not entry.collapsed:
                    flatten(entry.children)
        
        flatten(self.entries)
        return flat
    
    def _find_entry(self, entry_id: str) -> Optional[Entry]:
        """Find an entry by ID."""
        def search(entries: List[Entry]) -> Optional[Entry]:
            for entry in entries:
                if entry.id == entry_id:
                    return entry
                found = search(entry.children)
                if found:
                    return found
            return None
        
        return search(self.entries)
    
    def _find_entry_by_id(self, entry_id: str) -> Optional[Entry]:
        """Find entry by ID (alias for consistency)."""
        return self._find_entry(entry_id)


class TextualFloatPlugin(PluginBase):
    """Textual-based FLOAT Notes."""
    
    name = "float"
    description = "FLOAT Notes - Beautiful interactive notes with Textual"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        
        @cli_group.command(name="float")
        def cmd():
            """Launch FLOAT Notes with Textual UI.
            
            Features:
            - Tree-based hierarchical notes
            - REPL mode with Python execution
            - Command palette (Ctrl+P)
            - Mouse support
            - Collapsible entries
            - Beautiful UI with themes
            
            Keyboard shortcuts:
            - Ctrl+N: New entry
            - Ctrl+R: Toggle REPL
            - Ctrl+P: Command palette
            - Arrow keys: Navigate
            - Tab/Shift+Tab: Indent/unindent
            - Ctrl+S: Save
            - Ctrl+Q: Quit
            """
            if not TEXTUAL_AVAILABLE:
                console.print("[red]Textual not installed![/red]")
                console.print("Install with: pip install 'floatctl[textual]'")
                return
                
            app = FloatNotes()
            app.run()