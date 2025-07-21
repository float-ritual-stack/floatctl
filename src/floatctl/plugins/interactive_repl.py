"""Interactive REPL - Notes with embedded Python execution."""

import json
import re
import sys
import io
import traceback
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


class InteractiveREPL:
    """Interactive notes with REPL capabilities."""
    
    def __init__(self):
        self.entries: List[Entry] = []
        self.selected: int = -1
        self.input_buffer = Buffer(multiline=True)
        self.multiline_mode = False
        self.repl_mode = False
        
        # Python interpreter for REPL mode
        self.interpreter = InteractiveInterpreter()
        self.repl_locals = {}
        
        # Add floatctl to the REPL environment
        self.repl_locals['floatctl'] = self._floatctl_command
        
        # Storage
        self.data_file = Path.home() / '.floatctl' / 'repl_notes' / 'entries.json'
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load
        self._load()
        
        # Type patterns
        self.types = {
            'ctx': 'context',
            'highlight': 'highlight',
            'todo': 'todo',
            'code': 'code',
            'output': 'output',
            'error': 'error',
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
        # Check for code blocks
        if text.startswith('```'):
            return 'code', text
        
        match = re.match(r'^(\w+)::\s*(.*)$', text)
        if match:
            type_key = match.group(1).lower()
            content = match.group(2)
            return self.types.get(type_key, type_key), content
        return 'log', text
    
    def add_entry(self, text: str, entry_type: Optional[str] = None, indent_offset: int = 0):
        """Add a new entry."""
        if not text.strip():
            return
        
        if entry_type is None:
            entry_type, content = self.parse_input(text)
        else:
            content = text
        
        # Determine indent
        indent = 0
        if 0 <= self.selected < len(self.entries):
            indent = self.entries[self.selected].indent + indent_offset
        
        # Check if it's code
        is_code = entry_type == 'code' or text.startswith('```')
        if is_code and text.startswith('```'):
            # Extract code from markdown code block
            lines = text.split('\n')
            if len(lines) > 2 and lines[-1].strip() == '```':
                content = '\n'.join(lines[1:-1])
            else:
                content = '\n'.join(lines[1:]) if len(lines) > 1 else ''
        
        entry = Entry(
            id=str(int(datetime.now().timestamp() * 1000)),
            content=content,
            type=entry_type,
            indent=indent,
            is_code=is_code
        )
        
        # Insert after selected
        if 0 <= self.selected < len(self.entries):
            self.entries.insert(self.selected + 1, entry)
            self.selected += 1
        else:
            self.entries.append(entry)
            self.selected = len(self.entries) - 1
        
        self._save()
        
        # If in REPL mode and it's code, execute it
        if self.repl_mode and is_code:
            self.execute_code(entry)
    
    def execute_code(self, code_entry: Entry):
        """Execute code and add output as child entries."""
        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Save current position
        original_selected = self.selected
        
        try:
            # Execute the code
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Try to compile and exec
                try:
                    compiled = compile(code_entry.content, '<repl>', 'eval')
                    result = eval(compiled, self.repl_locals)
                    if result is not None:
                        stdout_capture.write(str(result))
                except:
                    # If eval fails, try exec
                    exec(code_entry.content, self.repl_locals)
            
            # Get output
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            # Add output as child entries
            if stdout_output:
                self.add_entry(stdout_output, 'output', indent_offset=1)
            
            if stderr_output:
                self.add_entry(stderr_output, 'error', indent_offset=1)
                
        except Exception as e:
            # Add error as child entry
            error_msg = traceback.format_exc()
            self.add_entry(error_msg, 'error', indent_offset=1)
    
    def execute_shell(self, command: str):
        """Execute shell command and capture output."""
        original_selected = self.selected
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                self.add_entry(result.stdout.rstrip(), 'output', indent_offset=1)
            
            if result.stderr:
                self.add_entry(result.stderr.rstrip(), 'error', indent_offset=1)
                
            if result.returncode != 0 and not result.stderr:
                self.add_entry(f"Exit code: {result.returncode}", 'error', indent_offset=1)
                
        except subprocess.TimeoutExpired:
            self.add_entry("Command timed out after 30 seconds", 'error', indent_offset=1)
        except Exception as e:
            self.add_entry(f"Shell error: {str(e)}", 'error', indent_offset=1)
    
    def _floatctl_command(self, *args):
        """Execute floatctl command from within REPL."""
        command = ['floatctl'] + list(args)
        self.execute_shell(' '.join(command))
        return f"Executed: {' '.join(command)}"
    
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
            return "\n  No entries yet. Type to add notes or code!\n"
        
        lines = []
        for i, entry in enumerate(self.entries):
            # Format
            selected = "→" if i == self.selected else " "
            indent = "  " * entry.indent
            time = entry.timestamp.strftime("%H:%M")
            
            # Type-specific formatting
            if entry.is_code:
                type_str = "<ansicyan>[code]</ansicyan> "
            elif entry.type == 'output':
                type_str = "<ansigreen>[out]</ansigreen> "
            elif entry.type == 'error':
                type_str = "<ansired>[err]</ansired> "
            elif entry.type != 'log':
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
        
        # Tab/Shift+Tab for indentation
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
                # In multiline, Enter saves
                text = self.input_buffer.text
                if text:
                    self.add_entry(text)
                    self.input_buffer.reset()
                    self.multiline_mode = False
                    event.app.invalidate()
            else:
                text = self.input_buffer.text
                if text:
                    # Check for shell commands
                    if text.startswith('!'):
                        self.execute_shell(text[1:])
                        self.input_buffer.reset()
                    else:
                        self.add_entry(text)
                        self.input_buffer.reset()
                    event.app.invalidate()
        
        # Ctrl+J for newline
        @kb.add(Keys.ControlJ)
        def _(event):
            self.multiline_mode = True
            self.input_buffer.insert_text('\n')
            event.app.invalidate()
        
        # Ctrl+R to toggle REPL mode
        @kb.add(Keys.ControlR)
        def _(event):
            self.repl_mode = not self.repl_mode
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
            self.multiline_mode = False
            event.app.invalidate()
        
        # Dynamic input height
        def get_input_height():
            lines = self.input_buffer.text.count('\n') + 1
            return min(5, max(1, lines))
        
        # Layout
        layout = Layout(
            HSplit([
                # Header
                Window(
                    FormattedTextControl(
                        lambda: HTML(
                            '<b>Interactive REPL Notes</b> '
                            '<ansigreen>[REPL ON]</ansigreen>' if self.repl_mode else '<gray>[REPL OFF]</gray>'
                            '\n'
                            '<gray>Ctrl+R REPL · !cmd Shell · ```code``` Python · floatctl() in REPL · Ctrl+J Newline</gray>'
                        )
                    ),
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
                            lambda: HTML(
                                '<ansigreen>>>> </ansigreen>' if self.repl_mode 
                                else '<b>/ </b>' if not self.multiline_mode 
                                else '<b>» </b>'
                            )
                        ),
                        width=4
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
                            else '<reverse>REPL: Code executes automatically</reverse>'
                            if self.repl_mode
                            else '<reverse>Tab indents · Alt+↑/↓ navigates</reverse>'
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
                'ansicyan': '#00ffff',
                'ansigreen': '#00ff00',
                'ansired': '#ff0000',
            }),
            full_screen=True,
            mouse_support=False,
        )
        
        # Focus input
        app.layout.focus(self.input_buffer)
        
        app.run()


class InteractiveREPLPlugin(PluginBase):
    """Interactive REPL notes plugin."""
    
    name = "repl"
    description = "Interactive notes with Python REPL execution"
    version = "0.3.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        
        @cli_group.command(name="repl")
        def cmd():
            """Launch interactive REPL notes.
            
            Features:
            - Ctrl+R: Toggle REPL mode (code auto-executes)
            - ```code```: Python code blocks
            - !command: Shell commands
            - floatctl(): Call floatctl commands from Python
            - Output appears as indented children
            
            Examples in REPL mode:
            >>> floatctl('chroma', 'list')
            >>> floatctl('notes', 'add', 'ctx:: testing')
            >>> !ls -la
            
            Keyboard shortcuts:
            - Tab/Shift+Tab: Indent/unindent
            - Alt+↑/↓: Navigate entries
            - Ctrl+J: Newline in input
            - Enter: Execute/save entry
            - Ctrl+C: Exit
            
            Entry types:
            - code:: Python code
            - ctx:: Context marker
            - todo:: Task item
            - [code], [out], [err] auto-generated
            """
            app = InteractiveREPL()
            app.run()
            console.print("\n[green]Session saved! 🌲[/green]")