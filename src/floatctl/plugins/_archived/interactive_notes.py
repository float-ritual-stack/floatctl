"""Interactive Notes REPL with proper keyboard navigation."""

import os
import sys
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich import box
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.align import Align

try:
    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import (
        Window, HSplit, VSplit, FloatContainer, Float, 
        ConditionalContainer, Container
    )
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout.layout import Layout as PTLayout
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.formatted_text import HTML, ANSI
    from prompt_toolkit.widgets import Label, Frame, TextArea
    from prompt_toolkit.application import get_app
    from prompt_toolkit.filters import Condition, has_focus
    from prompt_toolkit.styles import Style
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

console = Console()


@dataclass
class Entry:
    """A single entry in the notes system."""
    id: str
    content: str
    type: str = "log"
    timestamp: datetime = field(default_factory=datetime.now)
    indent: int = 0
    parent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'indent': self.indent,
            'parent_id': self.parent_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entry':
        return cls(
            id=data['id'],
            content=data['content'],
            type=data.get('type', 'log'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            indent=data.get('indent', 0),
            parent_id=data.get('parent_id')
        )


class InteractiveNotes:
    """Interactive notes interface with keyboard navigation."""
    
    def __init__(self):
        self.entries: List[Entry] = []
        self.selected_index: Optional[int] = None
        self.mode = 'chat'  # 'chat' or 'edit'
        self.show_details = False
        
        # Storage
        self.data_dir = Path.home() / '.floatctl' / 'interactive_notes'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.entries_file = self.data_dir / 'entries.json'
        
        # Load existing entries
        self._load_entries()
        
        # UI state
        self.input_buffer = Buffer()
        self.status_text = "Ready"
        
        # Type patterns
        self.type_patterns = {
            'ctx': 'context',
            'highlight': 'highlight',
            'mode': 'mode',
            'project': 'project',
            'todo': 'todo',
            'idea': 'idea',
            'bridge': 'bridge',
            'dispatch': 'dispatch',
            'sysop': 'sysop',
            'karen': 'karen',
            'evna': 'evna',
            'lf1m': 'lf1m'
        }
    
    def _load_entries(self):
        """Load entries from file."""
        if self.entries_file.exists():
            try:
                with open(self.entries_file, 'r') as f:
                    data = json.load(f)
                    self.entries = [Entry.from_dict(e) for e in data]
                    if self.entries:
                        self.selected_index = len(self.entries) - 1
            except Exception as e:
                self.status_text = f"Error loading: {e}"
    
    def _save_entries(self):
        """Save entries to file."""
        try:
            with open(self.entries_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
        except Exception as e:
            self.status_text = f"Error saving: {e}"
    
    def parse_entry_input(self, text: str) -> Tuple[str, str]:
        """Parse input to extract type and content."""
        match = re.match(r'^(\w+)::\s*(.*)$', text)
        if match:
            type_key = match.group(1).lower()
            content = match.group(2)
            entry_type = self.type_patterns.get(type_key, type_key)
            return entry_type, content
        return 'log', text
    
    def add_entry(self, text: str):
        """Add a new entry."""
        if not text.strip():
            return
        
        entry_type, content = self.parse_entry_input(text)
        
        # Determine indent
        indent = 0
        if self.selected_index is not None and self.selected_index < len(self.entries):
            indent = self.entries[self.selected_index].indent
        
        # Create entry
        new_entry = Entry(
            id=str(int(datetime.now().timestamp() * 1000)),
            content=content,
            type=entry_type,
            indent=indent
        )
        
        # Insert after selected or at end
        if self.selected_index is not None:
            self.entries.insert(self.selected_index + 1, new_entry)
            self.selected_index += 1
        else:
            self.entries.append(new_entry)
            self.selected_index = len(self.entries) - 1
        
        self._save_entries()
        self.status_text = f"Added {entry_type}"
    
    def move_selection(self, direction: int):
        """Move selection up or down."""
        if not self.entries:
            return
        
        if self.selected_index is None:
            self.selected_index = 0 if direction > 0 else len(self.entries) - 1
        else:
            self.selected_index = max(0, min(len(self.entries) - 1, self.selected_index + direction))
    
    def adjust_indent(self, increase: bool):
        """Adjust indentation of selected entry."""
        if self.selected_index is not None and self.selected_index < len(self.entries):
            entry = self.entries[self.selected_index]
            if increase:
                entry.indent = min(6, entry.indent + 1)
            else:
                entry.indent = max(0, entry.indent - 1)
            self._save_entries()
            self.status_text = f"Indent: {entry.indent}"
    
    def delete_selected(self):
        """Delete the selected entry."""
        if self.selected_index is not None and self.selected_index < len(self.entries):
            self.entries.pop(self.selected_index)
            if self.entries:
                self.selected_index = min(self.selected_index, len(self.entries) - 1)
            else:
                self.selected_index = None
            self._save_entries()
            self.status_text = "Deleted entry"
    
    def get_entries_display(self) -> str:
        """Get formatted display of entries."""
        if not self.entries:
            return "\n  No entries yet. Start typing to add your first entry.\n"
        
        lines = []
        for i, entry in enumerate(self.entries):
            # Selection indicator
            selected = "→" if i == self.selected_index else " "
            
            # Indentation
            indent = "  " * entry.indent
            
            # Type marker
            if entry.type != 'log':
                type_str = f"[{entry.type}::] "
            else:
                type_str = ""
            
            # Time
            time_str = entry.timestamp.strftime("%H:%M")
            
            # Format line
            if i == self.selected_index:
                # Highlight selected line
                line = f"{selected} {time_str} {indent}{type_str}{entry.content}"
                lines.append(f"\x1b[7m{line}\x1b[0m")  # Reverse video
            else:
                line = f"{selected} {time_str} {indent}{type_str}{entry.content}"
                lines.append(line)
        
        return "\n".join(lines)
    
    def create_keybindings(self) -> KeyBindings:
        """Create key bindings."""
        kb = KeyBindings()
        
        # Navigation
        @kb.add(Keys.Escape, Keys.Up)  # Alt+Up
        def move_up(event):
            self.move_selection(-1)
        
        @kb.add(Keys.Escape, Keys.Down)  # Alt+Down  
        def move_down(event):
            self.move_selection(1)
        
        # Indentation
        @kb.add(Keys.Tab, filter=~has_focus(self.input_buffer))
        def indent(event):
            self.adjust_indent(True)
        
        @kb.add(Keys.BackTab, filter=~has_focus(self.input_buffer))
        def unindent(event):
            self.adjust_indent(False)
        
        # Entry management
        @kb.add(Keys.ControlD)
        def delete_entry(event):
            self.delete_selected()
        
        # Mode switching
        @kb.add(Keys.ControlE)
        def toggle_mode(event):
            self.mode = 'edit' if self.mode == 'chat' else 'chat'
            self.status_text = f"Mode: {self.mode}"
        
        # Add entry on Enter
        @kb.add(Keys.Enter, filter=has_focus(self.input_buffer))
        def add_entry(event):
            text = self.input_buffer.text
            if text.strip():
                self.add_entry(text)
                self.input_buffer.reset()
        
        # Exit
        @kb.add(Keys.ControlC)
        def exit_app(event):
            event.app.exit()
        
        return kb
    
    def create_layout(self):
        """Create the application layout."""
        # Header
        header = Window(
            FormattedTextControl(
                HTML('<ansigreen><b>Interactive Notes</b></ansigreen>\n'
                     '<ansigray>Alt+↑/↓: Navigate · Tab: Indent · Enter: Add · Ctrl+C: Exit</ansigray>')
            ),
            height=2
        )
        
        # Main content area showing entries
        def get_entries_text():
            return ANSI(self.get_entries_display())
        
        entries_window = Window(
            FormattedTextControl(get_entries_text),
            wrap_lines=False
        )
        
        # Status line
        def get_status_text():
            mode_indicator = f"[{self.mode.upper()}]"
            selection_info = f"Entry {self.selected_index + 1}/{len(self.entries)}" if self.selected_index is not None else "No selection"
            return HTML(f'<ansiyellow>{mode_indicator}</ansiyellow> {selection_info} · {self.status_text}')
        
        status_window = Window(
            FormattedTextControl(get_status_text),
            height=1
        )
        
        # Input area
        input_prompt = Window(
            FormattedTextControl(HTML('<ansigreen>/</ansigreen> ')),
            width=2
        )
        
        input_field = Window(
            BufferControl(buffer=self.input_buffer),
            height=1
        )
        
        input_container = VSplit([
            input_prompt,
            input_field
        ])
        
        # Main layout
        return HSplit([
            header,
            Window(height=1, char='─'),
            entries_window,
            Window(height=1, char='─'),
            input_container,
            status_window
        ])
    
    def run(self):
        """Run the interactive application."""
        if not PROMPT_TOOLKIT_AVAILABLE:
            console.print("[red]Interactive mode requires prompt-toolkit[/red]")
            return
        
        # Create application
        app = Application(
            layout=PTLayout(self.create_layout()),
            key_bindings=self.create_keybindings(),
            style=Style.from_dict({
                'ansigreen': '#00ff00',
                'ansiyellow': '#ffff00',
                'ansigray': '#888888',
            }),
            full_screen=True,
            mouse_support=True
        )
        
        # Run it
        app.run()
        
        console.print("\n[green]Session saved. Goodbye! 🌲[/green]")


def create_plugin():
    """Create the interactive notes plugin."""
    
    class InteractiveNotesPlugin:
        """Plugin wrapper for interactive notes."""
        
        name = "interactive"
        description = "Interactive notes with keyboard navigation"
        version = "0.1.0"
        
        def register_commands(self, cli_group: click.Group):
            """Register the interactive command."""
            
            @cli_group.command(name="interactive")
            def interactive_cmd():
                """Launch interactive notes interface.
                
                Keyboard shortcuts:
                - Alt+↑/↓: Navigate entries
                - Tab/Shift+Tab: Indent/unindent
                - Enter: Add new entry
                - Ctrl+D: Delete entry
                - Ctrl+E: Toggle mode
                - Ctrl+C: Exit
                """
                app = InteractiveNotes()
                app.run()
    
    return InteractiveNotesPlugin()


# For testing directly
if __name__ == "__main__":
    app = InteractiveNotes()
    app.run()