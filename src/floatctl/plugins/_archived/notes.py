"""Notes plugin - Hybrid structured logging interface."""

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
from rich.table import Table

from floatctl.plugin_manager import PluginBase
from floatctl.repl import REPLPlugin, REPLContext

console = Console()


@dataclass
class Note:
    """A single note entry."""
    id: str
    content: str
    type: str = "log"
    timestamp: datetime = field(default_factory=datetime.now)
    indent: int = 0
    parent_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'indent': self.indent,
            'parent_id': self.parent_id,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            content=data['content'],
            type=data.get('type', 'log'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            indent=data.get('indent', 0),
            parent_id=data.get('parent_id'),
            tags=data.get('tags', [])
        )


class NotesPlugin(PluginBase, REPLPlugin):
    """Plugin for structured note-taking with FLOAT patterns."""
    
    name = "notes"
    description = "Hybrid structured logging with FLOAT patterns"
    version = "0.1.0"
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize notes plugin."""
        super().__init__(config)
        
        # Storage
        self.data_dir = Path.home() / '.floatctl' / 'notes'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notes_file = self.data_dir / 'notes.json'
        
        # State
        self.notes: List[Note] = []
        self.selected_index: Optional[int] = None
        self.show_details = False
        
        # Load existing notes
        self._load_notes()
        
        # FLOAT type patterns
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
    
    def _load_notes(self):
        """Load notes from file."""
        if self.notes_file.exists():
            try:
                with open(self.notes_file, 'r') as f:
                    data = json.load(f)
                    self.notes = [Note.from_dict(n) for n in data]
            except Exception as e:
                console.print(f"[red]Error loading notes: {e}[/red]")
    
    def _save_notes(self):
        """Save notes to file."""
        try:
            with open(self.notes_file, 'w') as f:
                json.dump([n.to_dict() for n in self.notes], f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving notes: {e}[/red]")
    
    def parse_input(self, text: str) -> Tuple[str, str, List[str]]:
        """Parse input for type and tags."""
        # Extract type
        type_match = re.match(r'^(\w+)::\s*(.*)$', text)
        if type_match:
            type_key = type_match.group(1).lower()
            content = type_match.group(2)
            note_type = self.type_patterns.get(type_key, type_key)
        else:
            note_type = 'log'
            content = text
        
        # Extract tags
        tags = re.findall(r'#(\w+)', content)
        
        return note_type, content, tags
    
    def add_note(self, text: str, indent: Optional[int] = None):
        """Add a new note."""
        if not text.strip():
            return
        
        note_type, content, tags = self.parse_input(text)
        
        # Determine indent level
        if indent is None:
            indent = self.notes[self.selected_index].indent if self.selected_index is not None else 0
        
        # Create note
        note = Note(
            id=str(int(datetime.now().timestamp() * 1000)),
            content=content,
            type=note_type,
            indent=indent,
            tags=tags
        )
        
        # Insert after selected or at end
        if self.selected_index is not None:
            self.notes.insert(self.selected_index + 1, note)
            self.selected_index += 1
        else:
            self.notes.append(note)
            self.selected_index = len(self.notes) - 1
        
        self._save_notes()
        console.print(f"[green]✓[/green] Added {note_type} note")
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register notes commands."""
        
        @cli_group.group(name="notes", help=self.description)
        def notes_group():
            """Notes management commands."""
            pass
        
        @notes_group.command(name="add")
        @click.argument('text', nargs=-1, required=True)
        @click.option('--type', '-t', help='Note type (ctx, highlight, todo, etc.)')
        @click.option('--indent', '-i', type=int, help='Indentation level')
        def add_cmd(text, type, indent):
            """Add a new note."""
            full_text = ' '.join(text)
            if type:
                full_text = f"{type}:: {full_text}"
            self.add_note(full_text, indent)
        
        @notes_group.command(name="list")
        @click.option('--type', '-t', help='Filter by type')
        @click.option('--tag', help='Filter by tag')
        @click.option('--today', is_flag=True, help='Show only today\'s notes')
        @click.option('--tree', is_flag=True, help='Show as tree')
        def list_cmd(type, tag, today, tree):
            """List notes."""
            filtered = self.notes
            
            # Apply filters
            if type:
                filtered = [n for n in filtered if n.type == type]
            if tag:
                filtered = [n for n in filtered if tag in n.tags]
            if today:
                today_date = datetime.now().date()
                filtered = [n for n in filtered if n.timestamp.date() == today_date]
            
            if not filtered:
                console.print("[yellow]No notes match the criteria[/yellow]")
                return
            
            if tree:
                self._show_tree(filtered)
            else:
                self._show_list(filtered)
        
        @notes_group.command(name="search")
        @click.argument('query')
        def search_cmd(query):
            """Search notes by content."""
            query_lower = query.lower()
            matches = [n for n in self.notes if query_lower in n.content.lower()]
            
            if not matches:
                console.print(f"[yellow]No notes found matching '{query}'[/yellow]")
                return
            
            console.print(f"\n[bold]Found {len(matches)} matches:[/bold]\n")
            self._show_list(matches)
        
        @notes_group.command(name="export")
        @click.argument('output', type=click.Path())
        @click.option('--format', type=click.Choice(['json', 'markdown']), default='markdown')
        def export_cmd(output, format):
            """Export notes to file."""
            output_path = Path(output)
            
            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump([n.to_dict() for n in self.notes], f, indent=2)
            else:
                self._export_markdown(output_path)
            
            console.print(f"[green]✓[/green] Exported {len(self.notes)} notes to {output}")
    
    def _show_list(self, notes: List[Note]):
        """Show notes as a list."""
        table = Table(box=box.SIMPLE)
        table.add_column("Time", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Content")
        table.add_column("Tags", style="dim")
        
        for note in notes:
            indent = "  " * note.indent
            type_display = f"[{note.type}]" if note.type != 'log' else ""
            tags_display = " ".join(f"#{t}" for t in note.tags) if note.tags else ""
            
            table.add_row(
                note.timestamp.strftime("%H:%M"),
                type_display,
                indent + note.content,
                tags_display
            )
        
        console.print(table)
    
    def _show_tree(self, notes: List[Note]):
        """Show notes as a tree."""
        tree = Tree("[bold]Notes[/bold]")
        
        # Build tree structure based on indentation
        stack = [(tree, -1)]  # (node, indent_level)
        
        for note in notes:
            # Find parent at the right level
            while stack and stack[-1][1] >= note.indent:
                stack.pop()
            
            parent_node = stack[-1][0] if stack else tree
            
            # Format note
            note_text = Text()
            if note.type != 'log':
                note_text.append(f"{note.type}:: ", style="green")
            note_text.append(note.content)
            
            # Add to tree
            node = parent_node.add(note_text)
            stack.append((node, note.indent))
        
        console.print(tree)
    
    def _export_markdown(self, output_path: Path):
        """Export notes as markdown."""
        with open(output_path, 'w') as f:
            f.write("# FLOAT Notes Export\n\n")
            f.write(f"Exported: {datetime.now().isoformat()}\n\n")
            
            current_date = None
            for note in self.notes:
                # Date headers
                note_date = note.timestamp.date()
                if note_date != current_date:
                    current_date = note_date
                    f.write(f"\n## {note_date}\n\n")
                
                # Note content
                indent = "  " * note.indent
                time_str = note.timestamp.strftime("%H:%M")
                
                if note.type != 'log':
                    f.write(f"{indent}- `{time_str}` **{note.type}::** {note.content}\n")
                else:
                    f.write(f"{indent}- `{time_str}` {note.content}\n")
    
    # REPL Plugin Methods
    def register_repl_commands(self, repl):
        """Register notes-specific REPL commands."""
        repl.register_command('add', 'Add a note', self._repl_add)
        repl.register_command('list', 'List recent notes', self._repl_list)
        repl.register_command('select', 'Select a note', self._repl_select)
        repl.register_command('indent', 'Change indentation', self._repl_indent)
        repl.register_command('delete', 'Delete selected note', self._repl_delete)
        repl.register_command('export', 'Export notes', self._repl_export)
        repl.register_command('tree', 'Show notes as tree', self._repl_tree)
    
    def handle_repl_command(self, ctx: REPLContext, cmd: str, args: List[str]) -> bool:
        """Handle direct input as note addition."""
        # Any non-command input becomes a note
        if not cmd.startswith('/'):
            full_text = cmd + (' ' + ' '.join(args) if args else '')
            self.add_note(full_text)
            return True
        return False
    
    def get_repl_help(self) -> str:
        """Return help text for notes REPL."""
        return """Notes Commands:
  <text>         Add note (type:: prefix for types)
  list [n]       Show last n notes (default: 10)
  select <n>     Select note by number
  indent +/-     Increase/decrease indent
  delete         Delete selected note
  tree           Show notes as tree
  export <file>  Export to markdown
  
Note Types:
  ctx::          Context marker
  highlight::    Important content
  todo::         Task item
  bridge::       Bridge reference
  mode::         Cognitive state"""
    
    def _repl_add(self, ctx: REPLContext, args: List[str]):
        """Add note from REPL."""
        if args:
            self.add_note(' '.join(args))
        else:
            console.print("[yellow]Usage: add <text>[/yellow]")
    
    def _repl_list(self, ctx: REPLContext, args: List[str]):
        """List recent notes."""
        limit = int(args[0]) if args and args[0].isdigit() else 10
        recent = self.notes[-limit:] if len(self.notes) > limit else self.notes
        
        if not recent:
            console.print("[yellow]No notes yet[/yellow]")
            return
        
        # Show with selection indicators
        for i, note in enumerate(recent):
            idx = len(self.notes) - len(recent) + i
            selected = "→" if idx == self.selected_index else " "
            
            time_str = note.timestamp.strftime("%H:%M")
            indent = "  " * note.indent
            
            if note.type != 'log':
                console.print(f"{selected} [{idx + 1}] {time_str} {indent}[green]{note.type}::[/green] {note.content}")
            else:
                console.print(f"{selected} [{idx + 1}] {time_str} {indent}{note.content}")
    
    def _repl_select(self, ctx: REPLContext, args: List[str]):
        """Select a note."""
        if not args or not args[0].isdigit():
            console.print("[yellow]Usage: select <number>[/yellow]")
            return
        
        idx = int(args[0]) - 1
        if 0 <= idx < len(self.notes):
            self.selected_index = idx
            note = self.notes[idx]
            console.print(f"[green]Selected:[/green] {note.content}")
        else:
            console.print("[red]Invalid note number[/red]")
    
    def _repl_indent(self, ctx: REPLContext, args: List[str]):
        """Change indentation of selected note."""
        if self.selected_index is None:
            console.print("[yellow]No note selected[/yellow]")
            return
        
        if not args or args[0] not in ['+', '-']:
            console.print("[yellow]Usage: indent +/- [/yellow]")
            return
        
        note = self.notes[self.selected_index]
        if args[0] == '+':
            note.indent = min(6, note.indent + 1)
        else:
            note.indent = max(0, note.indent - 1)
        
        self._save_notes()
        console.print(f"[green]Indent:[/green] {note.indent}")
    
    def _repl_delete(self, ctx: REPLContext, args: List[str]):
        """Delete selected note."""
        if self.selected_index is None:
            console.print("[yellow]No note selected[/yellow]")
            return
        
        note = self.notes.pop(self.selected_index)
        self._save_notes()
        console.print(f"[red]Deleted:[/red] {note.content}")
        
        # Adjust selection
        if self.notes:
            self.selected_index = min(self.selected_index, len(self.notes) - 1)
        else:
            self.selected_index = None
    
    def _repl_export(self, ctx: REPLContext, args: List[str]):
        """Export notes from REPL."""
        if not args:
            console.print("[yellow]Usage: export <filename>[/yellow]")
            return
        
        output_path = Path(args[0])
        self._export_markdown(output_path)
        console.print(f"[green]✓[/green] Exported to {output_path}")
    
    def _repl_tree(self, ctx: REPLContext, args: List[str]):
        """Show notes as tree."""
        if not self.notes:
            console.print("[yellow]No notes yet[/yellow]")
            return
        
        self._show_tree(self.notes)