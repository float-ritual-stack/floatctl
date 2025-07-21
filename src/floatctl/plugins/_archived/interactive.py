"""Interactive plugin - True interactive notes with keyboard navigation."""

import os
import sys
import json
import re
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable

import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.table import Table

from floatctl.plugin_manager import PluginBase

try:
    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import (
        Window, HSplit, VSplit, ConditionalContainer
    )
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.layout.dimension import Dimension
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.formatted_text import HTML, ANSI, to_formatted_text
    from prompt_toolkit.filters import Condition, has_focus, is_done
    from prompt_toolkit.styles import Style
    from prompt_toolkit.application import get_app
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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'indent': self.indent,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entry':
        return cls(
            id=data['id'],
            content=data['content'],
            type=data.get('type', 'log'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            indent=data.get('indent', 0),
        )


class InteractiveApp:
    """The interactive application."""
    
    def __init__(self):
        self.entries: List[Entry] = []
        self.selected_index: Optional[int] = None
        self.mode = 'chat'
        
        # Storage
        self.data_dir = Path.home() / '.floatctl' / 'interactive'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.entries_file = self.data_dir / 'entries.json'
        
        # Load existing
        self._load_entries()
        
        # UI components
        self.input_buffer = Buffer(multiline=False)
        self.app: Optional[Application] = None
        
        # Type patterns
        self.type_patterns = {
            'ctx': 'context',
            'highlight': 'highlight',
            'mode': 'mode',
            'todo': 'todo',
            'bridge': 'bridge',
            'dispatch': 'dispatch',
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
            except:
                pass
    
    def _save_entries(self):
        """Save entries to file."""
        try:
            with open(self.entries_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
        except:
            pass
    
    def parse_input(self, text: str) -> Tuple[str, str]:
        """Parse input for type."""
        match = re.match(r'^(\w+)::\s*(.*)$', text)
        if match:
            type_key = match.group(1).lower()
            content = match.group(2)
            return self.type_patterns.get(type_key, type_key), content
        return 'log', text
    
    def add_entry(self, text: str):
        """Add a new entry."""
        if not text.strip():
            return
        
        entry_type, content = self.parse_input(text)
        
        # Get indent from selected entry
        indent = 0
        if self.selected_index is not None and 0 <= self.selected_index < len(self.entries):
            indent = self.entries[self.selected_index].indent
        
        new_entry = Entry(
            id=str(int(datetime.now().timestamp() * 1000)),
            content=content,
            type=entry_type,
            indent=indent
        )
        
        # Insert after selected
        if self.selected_index is not None:
            self.entries.insert(self.selected_index + 1, new_entry)
            self.selected_index += 1
        else:
            self.entries.append(new_entry)
            self.selected_index = len(self.entries) - 1
        
        self._save_entries()
        self.app.invalidate()  # Force redraw
    
    def move_selection(self, direction: int):
        """Move selection up/down."""
        if not self.entries:
            return
        
        if self.selected_index is None:
            self.selected_index = 0 if direction > 0 else len(self.entries) - 1
        else:
            self.selected_index = max(0, min(len(self.entries) - 1, self.selected_index + direction))
        
        self.app.invalidate()
    
    def adjust_indent(self, increase: bool):
        """Adjust indentation."""
        if self.selected_index is not None and 0 <= self.selected_index < len(self.entries):
            entry = self.entries[self.selected_index]
            if increase:
                entry.indent = min(6, entry.indent + 1)
            else:
                entry.indent = max(0, entry.indent - 1)
            self._save_entries()
            self.app.invalidate()
    
    def get_entries_display(self) -> List:
        """Get formatted display of entries."""
        result = []
        
        if not self.entries:
            result.append(('', '\n  No entries yet. Start typing to add your first entry.\n\n'))
            return result
        
        for i, entry in enumerate(self.entries):
            # Selection and indent
            is_selected = i == self.selected_index
            prefix = "→ " if is_selected else "  "
            indent = "  " * entry.indent
            
            # Time
            time_str = entry.timestamp.strftime("%H:%M")
            
            # Type styling
            if entry.type != 'log':
                type_part = ('ansigreen bold', f"{entry.type}::")
                content_part = ('', f" {entry.content}")
            else:
                type_part = ('', '')
                content_part = ('', entry.content)
            
            # Build line
            if is_selected:
                # Highlight entire line
                result.append(('reverse', f"{prefix}{time_str} {indent}"))
                if type_part[1]:
                    result.append(('reverse ansigreen bold', type_part[1]))
                    result.append(('reverse', content_part[1]))
                else:
                    result.append(('reverse', content_part[1]))
                result.append(('', '\n'))
            else:
                result.append(('', f"{prefix}{time_str} {indent}"))
                if type_part[1]:
                    result.append(type_part)
                    result.append(content_part)
                else:
                    result.append(content_part)
                result.append(('', '\n'))
        
        return result
    
    def create_application(self) -> Application:
        """Create the prompt_toolkit application."""
        kb = KeyBindings()
        
        # Focus on input by default
        def focus_input():
            if self.app:
                self.app.layout.focus(self.input_buffer)
        
        # Navigation
        @kb.add(Keys.Escape, Keys.Up)  # Alt+Up
        def _(event):
            self.move_selection(-1)
        
        @kb.add(Keys.Escape, Keys.Down)  # Alt+Down
        def _(event):
            self.move_selection(1)
        
        # Indentation
        @kb.add(Keys.Tab)
        def _(event):
            # If we're in the input buffer and it's empty, treat as indent
            if has_focus(self.input_buffer)() and not self.input_buffer.text.strip():
                self.adjust_indent(True)
            elif not has_focus(self.input_buffer)():
                self.adjust_indent(True)
            else:
                # Let tab work normally in input
                event.app.current_buffer.insert_text('    ')
        
        @kb.add(Keys.BackTab)
        def _(event):
            self.adjust_indent(False)
        
        # Add entry
        @kb.add(Keys.Enter, filter=has_focus(self.input_buffer))
        def _(event):
            text = self.input_buffer.text.strip()
            if text:
                self.add_entry(text)
                self.input_buffer.reset()
        
        # Exit
        @kb.add(Keys.ControlC)
        @kb.add(Keys.ControlQ)
        def _(event):
            event.app.exit()
        
        # Clear input
        @kb.add(Keys.Escape, filter=has_focus(self.input_buffer))
        def _(event):
            self.input_buffer.reset()
            self.selected_index = None
            event.app.invalidate()
        
        # Delete selected
        @kb.add(Keys.ControlD, filter=~has_focus(self.input_buffer))
        def _(event):
            if self.selected_index is not None and self.entries:
                self.entries.pop(self.selected_index)
                if self.entries:
                    self.selected_index = min(self.selected_index, len(self.entries) - 1)
                else:
                    self.selected_index = None
                self._save_entries()
                event.app.invalidate()
        
        # Create layout
        def get_entries():
            return self.get_entries_display()
        
        def get_status():
            if self.selected_index is not None:
                selection = f"Entry {self.selected_index + 1}/{len(self.entries)}"
            else:
                selection = "No selection"
            return [
                ('ansigreen bold', '[CHAT] '),
                ('', f'{selection} · '),
                ('ansiyellow', 'Alt+↑/↓'),
                ('', ' Navigate · '),
                ('ansiyellow', 'Tab'),
                ('', ' Indent · '),
                ('ansiyellow', 'Ctrl+C'),
                ('', ' Exit')
            ]
        
        # Layout
        layout = Layout(
            HSplit([
                # Header
                Window(
                    FormattedTextControl([
                        ('ansigreen bold', 'Interactive Notes\n'),
                        ('ansigray', 'Type to add entries · Use :: for entry types (ctx::, todo::, highlight::)')
                    ]),
                    height=2
                ),
                Window(height=1, char='─'),
                # Entries
                Window(
                    FormattedTextControl(get_entries),
                    wrap_lines=False
                ),
                Window(height=1, char='─'),
                # Input
                VSplit([
                    Window(FormattedTextControl([('ansigreen bold', '/ ')]), width=2),
                    Window(BufferControl(self.input_buffer))
                ], height=1),
                # Status
                Window(FormattedTextControl(get_status), height=1, style='reverse')
            ])
        )
        
        # Create app
        self.app = Application(
            layout=layout,
            key_bindings=kb,
            style=Style.from_dict({
                'ansigreen': '#00ff00',
                'ansiyellow': '#ffff00', 
                'ansigray': '#888888',
            }),
            full_screen=True,
            mouse_support=False
        )
        
        return self.app
    
    def run(self):
        """Run the interactive app."""
        if not PROMPT_TOOLKIT_AVAILABLE:
            console.print("[red]Interactive mode requires prompt-toolkit[/red]")
            console.print("Install with: pip install prompt-toolkit")
            return
        
        app = self.create_application()
        app.run()


class InteractivePlugin(PluginBase):
    """Interactive notes plugin with true keyboard navigation."""
    
    name = "interactive"
    description = "Interactive notes with keyboard navigation"
    version = "0.1.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register interactive command."""
        
        @cli_group.command(name="interactive")
        def interactive_cmd():
            """Launch interactive notes interface.
            
            A truly interactive note-taking interface with:
            
            \b
            Navigation:
              Alt+↑/↓     Navigate entries
              
            Editing:
              Tab         Indent selected entry  
              Shift+Tab   Unindent selected entry
              Ctrl+D      Delete selected entry
              
            Entry Types:
              ctx::       Context marker
              highlight:: Important note
              todo::      Task item
              bridge::    Bridge reference
              
            Other:
              Enter       Add new entry
              Escape      Clear input/selection
              Ctrl+C      Exit
            """
            app = InteractiveApp()
            app.run()
            console.print("\n[green]Session saved! 🌲[/green]")