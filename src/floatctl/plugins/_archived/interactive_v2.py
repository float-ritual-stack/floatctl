"""Interactive V2 - Simplified but robust interactive notes."""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import rich_click as click
from rich.console import Console

from floatctl.plugin_manager import PluginBase

try:
    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import HSplit, VSplit, Window
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.styles import Style
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

console = Console()


@dataclass
class Entry:
    """A note entry."""
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


class InteractiveNotesV2:
    """Simplified interactive notes."""
    
    def __init__(self):
        self.entries: List[Entry] = []
        self.selected: int = -1
        self.input_buffer = Buffer(multiline=True)
        self.multiline_mode = False
        
        # Storage
        self.data_file = Path.home() / '.floatctl' / 'interactive' / 'notes.json'
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load
        self._load()
        
        # Type patterns
        self.types = {
            'ctx': 'context',
            'highlight': 'highlight',
            'todo': 'todo',
            'bridge': 'bridge',
        }
    
    def _load(self):
        if self.data_file.exists():
            try:
                with open(self.data_file) as f:
                    data = json.load(f)
                    self.entries = [Entry.from_dict(e) for e in data]
            except:
                pass
    
    def _save(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f)
        except:
            pass
    
    def parse_input(self, text: str) -> Tuple[str, str]:
        match = re.match(r'^(\w+)::\s*(.*)$', text)
        if match:
            type_key = match.group(1).lower()
            content = match.group(2)
            return self.types.get(type_key, type_key), content
        return 'log', text
    
    def add_entry(self, text: str):
        if not text.strip():
            return
        
        entry_type, content = self.parse_input(text)
        
        # Inherit indent from selected
        indent = 0
        if 0 <= self.selected < len(self.entries):
            indent = self.entries[self.selected].indent
        
        entry = Entry(
            id=str(int(datetime.now().timestamp() * 1000)),
            content=content,
            type=entry_type,
            indent=indent
        )
        
        # Insert after selected
        if 0 <= self.selected < len(self.entries):
            self.entries.insert(self.selected + 1, entry)
            self.selected += 1
        else:
            self.entries.append(entry)
            self.selected = len(self.entries) - 1
        
        self._save()
    
    def move_selection(self, delta: int):
        if not self.entries:
            return
        if self.selected == -1:
            self.selected = 0
        else:
            self.selected = max(0, min(len(self.entries) - 1, self.selected + delta))
    
    def indent_selected(self, delta: int):
        if 0 <= self.selected < len(self.entries):
            entry = self.entries[self.selected]
            entry.indent = max(0, min(6, entry.indent + delta))
            self._save()
    
    def delete_selected(self):
        if 0 <= self.selected < len(self.entries):
            self.entries.pop(self.selected)
            if self.entries:
                self.selected = min(self.selected, len(self.entries) - 1)
            else:
                self.selected = -1
            self._save()
    
    def get_display(self) -> str:
        """Get display text."""
        if not self.entries:
            return "\n  No entries yet. Type to add one!\n"
        
        lines = []
        for i, entry in enumerate(self.entries):
            # Format
            selected = "→" if i == self.selected else " "
            indent = "  " * entry.indent
            time = entry.timestamp.strftime("%H:%M")
            
            if entry.type != 'log':
                type_str = f"<b>{entry.type}::</b> "
            else:
                type_str = ""
            
            # Handle multi-line content
            content_lines = entry.content.split('\n')
            for j, content_line in enumerate(content_lines):
                if j == 0:
                    # First line with metadata
                    line = f"{selected} {time} {indent}{type_str}{content_line}"
                else:
                    # Continuation lines
                    line = f"  {'     '} {indent}  {content_line}"
                
                if i == self.selected:
                    lines.append(f"<reverse>{line}</reverse>")
                else:
                    lines.append(line)
        
        return "\n".join(lines)
    
    def run(self):
        """Run the app."""
        if not AVAILABLE:
            console.print("[red]Requires prompt-toolkit[/red]")
            return
        
        kb = KeyBindings()
        
        # Always capture Tab/Shift+Tab regardless of focus
        @kb.add(Keys.Tab)
        def _(event):
            self.indent_selected(1)
            event.app.invalidate()
        
        @kb.add(Keys.BackTab)
        def _(event):
            self.indent_selected(-1)
            event.app.invalidate()
        
        # Navigation  
        @kb.add(Keys.Escape, Keys.Up)
        def _(event):
            self.move_selection(-1)
            event.app.invalidate()
        
        @kb.add(Keys.Escape, Keys.Down)
        def _(event):
            self.move_selection(1)
            event.app.invalidate()
        
        # Entry management
        @kb.add(Keys.Enter)
        def _(event):
            if self.multiline_mode:
                # In multiline mode, Enter adds the entry
                text = self.input_buffer.text
                if text:
                    self.add_entry(text)
                    self.input_buffer.reset()
                    self.multiline_mode = False
                    event.app.invalidate()
            else:
                # Normal mode - check if text exists
                text = self.input_buffer.text
                if text:
                    self.add_entry(text)
                    self.input_buffer.reset()
                    event.app.invalidate()
        
        # Ctrl+J for newline (standard terminal binding)
        @kb.add(Keys.ControlJ)
        def _(event):
            self.multiline_mode = True
            self.input_buffer.insert_text('\n')
            event.app.invalidate()
        
        @kb.add(Keys.ControlD)
        def _(event):
            self.delete_selected()
            event.app.invalidate()
        
        # Exit
        @kb.add(Keys.ControlC)
        def _(event):
            event.app.exit()
        
        # Clear
        @kb.add(Keys.Escape)
        def _(event):
            if self.input_buffer.text:
                self.input_buffer.reset()
            else:
                self.selected = -1
            event.app.invalidate()
        
        # Dynamic input height based on content
        def get_input_height():
            lines = self.input_buffer.text.count('\n') + 1
            return min(5, max(1, lines))  # 1-5 lines
        
        # Layout
        layout = Layout(
            HSplit([
                # Header
                Window(
                    FormattedTextControl(HTML(
                        '<b>Interactive Notes</b>\n'
                        '<gray>Alt+↑/↓ Navigate · Tab Indent · Ctrl+J Newline · Enter Add · Ctrl+C Exit</gray>'
                    )),
                    height=2
                ),
                Window(height=1, char='─'),
                # Content
                Window(
                    FormattedTextControl(
                        lambda: HTML(self.get_display())
                    ),
                    wrap_lines=False
                ),
                Window(height=1, char='─'),
                # Input
                VSplit([
                    Window(
                        FormattedTextControl(
                            lambda: HTML('<b>/ </b>' if not self.multiline_mode else '<b>» </b>')
                        ),
                        width=2
                    ),
                    Window(
                        BufferControl(self.input_buffer),
                        height=get_input_height,
                        wrap_lines=True
                    ),
                ]),
                # Status
                Window(
                    FormattedTextControl(
                        lambda: HTML(
                            '<reverse>Multiline mode - Enter to save</reverse>' 
                            if self.multiline_mode 
                            else '<reverse>Ctrl+J for multiline · Tab works everywhere</reverse>'
                        )
                    ),
                    height=1
                ),
            ])
        )
        
        app = Application(
            layout=layout,
            key_bindings=kb,
            style=Style.from_dict({
                'gray': '#888888',
            }),
            full_screen=True,
            mouse_support=False,
        )
        
        # Focus input on start
        app.layout.focus(self.input_buffer)
        
        app.run()


class InteractiveV2Plugin(PluginBase):
    """Interactive notes V2."""
    
    name = "iv2"
    description = "Interactive notes v2 - simplified and robust"
    version = "0.2.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        
        @cli_group.command(name="iv2")
        def cmd():
            """Launch interactive notes v2.
            
            Keyboard shortcuts that work everywhere:
            - Tab/Shift+Tab: Indent/unindent selected
            - Alt+↑/↓: Navigate entries
            - Enter: Add entry (save multiline)
            - Ctrl+J: Insert newline (multiline mode)
            - Ctrl+D: Delete selected
            - Ctrl+C: Exit
            
            Entry types:
            - ctx:: context marker
            - highlight:: important note
            - todo:: task item
            - bridge:: connection
            """
            app = InteractiveNotesV2()
            app.run()
            console.print("\n[green]Saved! 🌲[/green]")