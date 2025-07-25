"""FLOAT Notes - Simplified Textual version for low-friction flow."""

import json
import re
import sys
import io
import subprocess
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from code import InteractiveInterpreter

import rich_click as click
from rich.console import Console

from floatctl.plugin_manager import PluginBase

try:
    from textual import on, work
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import VerticalScroll
    from textual.widgets import Input, Static
    from textual.reactive import reactive
    from textual.events import Key
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


class SimpleFloatNotes(App):
    """Simplified FLOAT Notes - low friction flow."""
    
    CSS = """
    #entry-container {
        padding: 1;
        margin: 0;
    }
    
    .entry {
        margin: 0;
        padding: 0 1;
    }
    
    .entry-selected {
        background: $accent-lighten-2;
    }
    
    .insertion-indicator {
        color: $text-muted;
        text-style: italic;
    }
    
    #input-container {
        dock: bottom;
        height: auto;
        min-height: 3;
        max-height: 10;
        padding: 1;
        background: $surface;
        border-top: solid $primary;
    }
    
    #main-input {
        width: 100%;
        background: transparent;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+r", "toggle_repl", "REPL", show=False),
        Binding("alt+up", "move_up", "Up", show=False),
        Binding("alt+down", "move_down", "Down", show=False),
        Binding("escape", "clear_selection", "Clear", show=False),
        Binding("ctrl+q", "quit", "Quit"),
    ]
    
    # Reactive properties
    repl_mode = reactive(False)
    selected_index = reactive(-1)
    
    def __init__(self):
        super().__init__()
        self.entries: List[Entry] = []
        
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
            except Exception:
                pass
    
    def _save_entries(self):
        """Save entries to file - silently."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
        except Exception:
            pass
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Entry display area
        with VerticalScroll(id="entry-container"):
            yield Static("", id="entry-list")
        
        # Input at bottom
        yield Input(
            placeholder="What's on your mind? (Alt+↑/↓ navigate, Tab/Shift+Tab indent)",
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
    
    def watch_selected_index(self, old_value: int, new_value: int):
        """React to selection changes."""
        self.refresh_entries()
        # Update subtitle with position info
        if self.entries and 0 <= new_value < len(self.entries):
            repl_status = "REPL ON" if self.repl_mode else "REPL OFF"
            self.sub_title = f"{repl_status} | Entry {new_value + 1}/{len(self.entries)}"
        else:
            self.sub_title = "REPL ON" if self.repl_mode else "REPL OFF"
    
    def get_insertion_indicator(self) -> str:
        """Get text showing where next entry will be inserted."""
        if self.selected_index < 0 or self.selected_index >= len(self.entries):
            return "└─ next entry appears here..."
        
        selected = self.entries[self.selected_index]
        indent = "  " * selected.indent
        return f"{indent}├─ next entry appears here..."
    
    def refresh_entries(self):
        """Refresh the entry display."""
        entry_list = self.query_one("#entry-list", Static)
        
        if not self.entries:
            entry_list.update("➤ Start logging your thoughts...")
            return
        
        lines = []
        for i, entry in enumerate(self.entries):
            # Indentation
            indent = "  " * entry.indent
            
            # Time
            time_str = entry.timestamp.strftime("%H:%M")
            
            # Content with type prefix
            if entry.type == 'code':
                content = f"[cyan]```[/cyan]\n{entry.content}\n[cyan]```[/cyan]"
            elif entry.type != 'log':
                content = f"[yellow]{entry.type}::[/yellow] {entry.content}"
            else:
                content = entry.content
            
            # Selection - use bright white on blue for maximum visibility
            if i == self.selected_index:
                line = f"[bold white on blue]{indent}➤ {time_str} {content}[/bold white on blue]"
            else:
                line = f"{indent}➤ {time_str} {content}"
            
            lines.append(line)
            
            # Show insertion indicator after selected entry
            if i == self.selected_index:
                lines.append(f"[dim]{self.get_insertion_indicator()}[/dim]")
        
        # If nothing selected, show indicator at bottom
        if self.selected_index < 0:
            lines.append(f"[dim]{self.get_insertion_indicator()}[/dim]")
        
        entry_list.update("\n".join(lines))
    
    def action_toggle_repl(self):
        """Toggle REPL mode."""
        self.repl_mode = not self.repl_mode
    
    def action_move_up(self):
        """Move selection up."""
        if self.entries and self.selected_index > -1:
            self.selected_index = max(0, self.selected_index - 1)
    
    def action_move_down(self):
        """Move selection down."""
        if self.entries:
            self.selected_index = min(len(self.entries) - 1, self.selected_index + 1)
    
    def action_clear_selection(self):
        """Clear selection."""
        self.selected_index = -1
    
    def action_indent(self):
        """Increase indent of selected entry."""
        if 0 <= self.selected_index < len(self.entries):
            self.entries[self.selected_index].indent = min(6, self.entries[self.selected_index].indent + 1)
            self._save_entries()
            self.refresh_entries()
    
    def action_unindent(self):
        """Decrease indent of selected entry."""
        if 0 <= self.selected_index < len(self.entries):
            self.entries[self.selected_index].indent = max(0, self.entries[self.selected_index].indent - 1)
            self._save_entries()
            self.refresh_entries()
    
    def on_key(self, event: Key) -> None:
        """Handle key events to intercept Tab behavior."""
        if event.key == "tab":
            event.prevent_default()
            event.stop()
            self.action_indent()
        elif event.key == "shift+tab":
            event.prevent_default()
            event.stop()
            self.action_unindent()
    
    @on(Input.Submitted, "#main-input")
    def handle_input(self, event: Input.Submitted):
        """Handle input submission."""
        text = event.value.strip()
        if not text:
            return
        
        # Clear input
        event.input.value = ""
        
        # Handle Tab/Shift+Tab in input for indentation adjustment
        # This is handled in on_key below
        
        # Add entry
        self.add_entry(text)
    
    def parse_type(self, text: str) -> Tuple[str, str]:
        """Parse entry type and content."""
        # Check for code blocks
        if text.startswith('```'):
            lines = text.split('\n')
            if len(lines) > 2 and lines[-1].strip() == '```':
                content = '\n'.join(lines[1:-1])
            else:
                content = '\n'.join(lines[1:]) if len(lines) > 1 else ''
            return 'code', content
        
        # Check for type markers
        match = re.match(r'^(\w+)::\s*(.*)$', text, re.DOTALL)
        if match:
            return match.group(1).lower(), match.group(2)
        
        # Shell commands
        if text.startswith('!'):
            return 'shell', text[1:]
        
        return 'log', text
    
    def add_entry(self, text: str):
        """Add a new entry."""
        entry_type, content = self.parse_type(text)
        
        # Determine indent - same level as selected entry
        indent = 0
        if 0 <= self.selected_index < len(self.entries):
            indent = self.entries[self.selected_index].indent
        
        # Create entry
        entry = Entry(
            id=str(int(datetime.now().timestamp() * 1000000)),
            content=content,
            type=entry_type,
            indent=indent
        )
        
        # Insert after selected entry (or at end)
        if 0 <= self.selected_index < len(self.entries):
            self.entries.insert(self.selected_index + 1, entry)
            self.selected_index += 1
        else:
            self.entries.append(entry)
            self.selected_index = len(self.entries) - 1
        
        self._save_entries()
        self.refresh_entries()
        
        # Execute if REPL mode and code
        if self.repl_mode and entry_type == 'code':
            self.execute_code(entry)
        elif entry_type == 'shell':
            self.execute_shell(entry)
    
    @work(thread=True)
    def execute_code(self, entry: Entry):
        """Execute Python code."""
        try:
            # Capture output
            stdout = io.StringIO()
            stderr = io.StringIO()
            
            with redirect_stdout(stdout), redirect_stderr(stderr):
                # Try eval first for expressions
                try:
                    result = eval(entry.content, self.repl_locals)
                    if result is not None:
                        print(repr(result))
                except:
                    # Fall back to exec for statements
                    exec(entry.content, self.repl_locals)
            
            # Get output
            out = stdout.getvalue()
            err = stderr.getvalue()
            
            # Add output entries at same position
            position = self.entries.index(entry)
            if out:
                output_entry = Entry(
                    id=str(int(datetime.now().timestamp() * 1000000)),
                    content=out.rstrip(),
                    type='output',
                    indent=entry.indent + 1
                )
                self.entries.insert(position + 1, output_entry)
                self.selected_index = position + 1
                
            if err:
                error_entry = Entry(
                    id=str(int(datetime.now().timestamp() * 1000000)),
                    content=err.rstrip(),
                    type='error',
                    indent=entry.indent + 1
                )
                offset = 2 if out else 1
                self.entries.insert(position + offset, error_entry)
                self.selected_index = position + offset
                
            self.call_from_thread(self._save_entries)
            self.call_from_thread(self.refresh_entries)
                
        except Exception as e:
            error_entry = Entry(
                id=str(int(datetime.now().timestamp() * 1000000)),
                content=str(e),
                type='error',
                indent=entry.indent + 1
            )
            position = self.entries.index(entry)
            self.entries.insert(position + 1, error_entry)
            self.selected_index = position + 1
            self.call_from_thread(self._save_entries)
            self.call_from_thread(self.refresh_entries)
    
    @work(thread=True)
    def execute_shell(self, entry: Entry):
        """Execute shell command."""
        try:
            result = subprocess.run(
                entry.content,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            position = self.entries.index(entry)
            if output:
                output_entry = Entry(
                    id=str(int(datetime.now().timestamp() * 1000000)),
                    content=output,
                    type='output',
                    indent=entry.indent + 1
                )
                self.entries.insert(position + 1, output_entry)
                self.selected_index = position + 1
                
            if error:
                error_entry = Entry(
                    id=str(int(datetime.now().timestamp() * 1000000)),
                    content=error,
                    type='error',
                    indent=entry.indent + 1
                )
                offset = 2 if output else 1
                self.entries.insert(position + offset, error_entry)
                self.selected_index = position + offset
                
            self.call_from_thread(self._save_entries)
            self.call_from_thread(self.refresh_entries)
                
        except Exception as e:
            error_entry = Entry(
                id=str(int(datetime.now().timestamp() * 1000000)),
                content=f"Command failed: {e}",
                type='error',
                indent=entry.indent + 1
            )
            position = self.entries.index(entry)
            self.entries.insert(position + 1, error_entry)
            self.selected_index = position + 1
            self.call_from_thread(self._save_entries)
            self.call_from_thread(self.refresh_entries)
    
    def run_floatctl(self, command: str):
        """Run a floatctl command."""
        self.add_entry(f"!floatctl {command}")


class SimpleTextualFloatPlugin(PluginBase):
    """Simplified Textual-based FLOAT Notes."""
    
    name = "float-simple"
    description = "FLOAT Notes - Low friction flow"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        
        @cli_group.command(name="float-simple")
        def cmd():
            """Launch simplified FLOAT Notes with low-friction flow.
            
            Key improvements:
            - Same-level insertion by default (not child)
            - Tab/Shift+Tab for indentation
            - No save notifications
            - Visual insertion indicator
            - Minimal UI chrome
            
            Commands:
            - type:: markers for categorization
            - ``` for code blocks
            - ! for shell commands
            - Ctrl+R toggles REPL mode
            
            Navigation:
            - Alt+↑/↓ to select entries
            - Tab/Shift+Tab to indent selected entry
            - Escape to clear selection
            - Ctrl+Q to quit
            """
            if not TEXTUAL_AVAILABLE:
                console.print("[red]Textual not installed![/red]")
                console.print("Install with: pip install 'floatctl[textual]'")
                return
                
            app = SimpleFloatNotes()
            app.run()