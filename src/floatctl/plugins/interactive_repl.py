"""Interactive REPL - Notes with embedded Python execution."""

import json
import re
import io
import traceback
import subprocess
import random
import string
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.document import Document
    AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    AVAILABLE = False

    class Completion:  # type: ignore[no-redef]
        """Fallback completion object when prompt_toolkit is unavailable."""

        def __init__(
            self,
            text: str,
            start_position: int = 0,
            display: Optional[str] = None,
            display_meta: Optional[str] = None,
        ) -> None:
            self.text = text
            self.start_position = start_position
            self.display = display or text
            self.display_meta = display_meta

    class Completer:  # type: ignore[no-redef]
        """Fallback completer base class."""

        def get_completions(self, document, complete_event):  # pragma: no cover - stub
            return ()

    class Document:  # type: ignore[no-redef]
        """Minimal document placeholder used for typing compatibility."""

        text_before_cursor: str = ""

# ChromaDB integration for FloatQL search panel
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

console = Console()


class PatternCompleter(Completer):
    """Custom completer for :: patterns in FLOAT system."""
    
    def __init__(self):
        # Core patterns with descriptions
        self.patterns = {
            'ctx::': 'Temporal context marker',
            'highlight::': 'Key moment or insight',
            'todo::': 'Task item',
            'bridge::': 'Context restoration point',
            'mode::': 'Cognitive state',
            'project::': 'Project association',
            'remember::': 'Memory anchor',
            'eureka::': 'Breakthrough moment',
            'gotcha::': 'Debugging discovery',
            'decision::': 'Decision point',
            'connectTo::': 'Connection to concept',
            'relatesTo::': 'Related to topic',
            'expandOn::': 'Expand on idea',
            'rfc::': 'Request for comments',
            'float.dispatch': 'Dispatch action',
            # Personas
            'evna::': 'Ambient witness persona',
            'karen::': 'Boundary translator persona',
            'lf1m::': 'Authenticity enforcement persona',
            'sysop::': 'Infrastructure builder persona',
            'qtb::': 'Reality weaver persona',
            # Additional patterns that emerge
            'whomp::': 'Fucking magic moment',
            'chickenNipple::': 'Absurd precision marker',
            # Temporal navigation patterns
            'goto::': 'Navigate to specific time',
            'back::': 'Move backward in time',
            'forward::': 'Move forward in time',
            'show::': 'Filter by temporal window',
            'find::': 'Search with time constraints',
            # Persona filtering patterns
            'lens::': 'Switch persona perspective lens',
            'filter::': 'Filter by persona or type',
        }
    
    def get_completions(self, document: Document, complete_event):
        """Get completions for current input."""
        # Get text before cursor
        text_before_cursor = document.text_before_cursor
        
        # Check if we're typing a pattern
        if '::' in text_before_cursor:
            # Already have :: so don't complete
            return
            
        # Look for pattern start
        word_match = re.search(r'(\w+)$', text_before_cursor)
        if not word_match:
            return
            
        word = word_match.group(1).lower()
        
        # Find matching patterns
        for pattern, description in self.patterns.items():
            pattern_word = pattern.split('::')[0].lower()
            if pattern_word.startswith(word):
                # Calculate position
                start_position = -len(word)
                
                # Yield completion
                yield Completion(
                    pattern,
                    start_position=start_position,
                    display=pattern,
                    display_meta=description
                )


@dataclass
class FloatQLResult:
    """A search result from FloatQL/Chroma query."""
    id: str
    content: str
    collection: str
    distance: float
    metadata: Dict[str, Any]
    
    def to_entry(self) -> 'Entry':
        """Convert search result to REPL entry."""
        return Entry(
            id=f"search_{self.id}",
            content=f"[{self.collection}] {self.content[:200]}..." if len(self.content) > 200 else f"[{self.collection}] {self.content}",
            type="search_result",
            metadata={
                **self.metadata,
                'collection': self.collection,
                'distance': self.distance,
                'original_id': self.id
            }
        )

@dataclass
class Entry:
    """A note/code entry with temporal consciousness technology."""
    id: str
    content: str
    type: str = "log"
    timestamp: datetime = field(default_factory=datetime.now)
    indent: int = 0
    is_code: bool = False
    language: str = "python"
    metadata: Optional[Dict[str, Any]] = None
    collapsed: bool = False  # For collapse/expand functionality
    children: List['Entry'] = field(default_factory=list)  # Child entries
    
    # Temporal consciousness fields
    timestamp_unix: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    temporal_anchor: Optional[str] = None  # ctx:: parsed timestamp
    consciousness_mode: Optional[str] = None  # mode:: parsed state
    ttl_expires: Optional[datetime] = None  # TTL for ephemeral entries
    ttl_expires_unix: Optional[int] = None  # TTL Unix timestamp for queries
    temporal_parent: Optional[str] = None  # ID of temporal parent entry
    is_temporal_marker: bool = False  # Entry created for temporal navigation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'indent': self.indent,
            'is_code': self.is_code,
            'language': self.language,
            'metadata': self.metadata,
            'collapsed': self.collapsed,
            'children': [child.to_dict() for child in self.children],
            # Temporal consciousness fields
            'timestamp_unix': self.timestamp_unix,
            'temporal_anchor': self.temporal_anchor,
            'consciousness_mode': self.consciousness_mode,
            'ttl_expires': self.ttl_expires.isoformat() if self.ttl_expires else None,
            'ttl_expires_unix': self.ttl_expires_unix,
            'temporal_parent': self.temporal_parent,
            'is_temporal_marker': self.is_temporal_marker,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entry':
        entry = cls(
            id=data['id'],
            content=data['content'],
            type=data.get('type', 'log'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            indent=data.get('indent', 0),
            is_code=data.get('is_code', False),
            language=data.get('language', 'python'),
            metadata=data.get('metadata'),
            collapsed=data.get('collapsed', False),
            # Temporal consciousness fields
            timestamp_unix=data.get('timestamp_unix', int(datetime.fromisoformat(data['timestamp']).timestamp())),
            temporal_anchor=data.get('temporal_anchor'),
            consciousness_mode=data.get('consciousness_mode'),
            ttl_expires=datetime.fromisoformat(data['ttl_expires']) if data.get('ttl_expires') else None,
            ttl_expires_unix=data.get('ttl_expires_unix'),
            temporal_parent=data.get('temporal_parent'),
            is_temporal_marker=data.get('is_temporal_marker', False),
        )
        # Recursively create children
        entry.children = [cls.from_dict(child_data) for child_data in data.get('children', [])]
        return entry


class InteractiveREPL:
    """Interactive notes with REPL capabilities."""
    
    def __init__(self):
        self.entries: List[Entry] = []
        self.selected: int = -1
        if AVAILABLE:
            # Create completer and buffer with it
            self.completer = PatternCompleter()
            self.input_buffer = Buffer(multiline=True, completer=self.completer)
            # FloatQL search mode
            self.search_buffer = Buffer(multiline=False)
        else:
            self.input_buffer = None
            self.search_buffer = None
            self.completer = None
        self.multiline_mode = False
        self.repl_mode = False
        self.search_mode = False  # FloatQL search panel mode
        self.search_results: List[FloatQLResult] = []
        self.search_selected: int = -1
        
        # Viewport tracking for scrolling
        self.viewport_top = 0
        self.viewport_height = 20  # Will be calculated dynamically
        
        # Python interpreter for REPL mode
        self.interpreter = InteractiveInterpreter()
        self.repl_locals = {}
        
        # Add floatctl to the REPL environment
        self.repl_locals['floatctl'] = self._floatctl_command
        
        # Storage
        self.data_file = Path.home() / '.floatctl' / 'repl_notes' / 'notes.json'
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # ChromaDB client for FloatQL search
        self.chroma_client = None
        if CHROMA_AVAILABLE:
            try:
                self.chroma_client = chromadb.PersistentClient(path=str(Path.home() / '.floatctl' / 'chroma_db'))
            except Exception as e:
                console.print(f"[yellow]ChromaDB not available: {e}[/yellow]")
                self.chroma_client = None
        
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
        
        # :: dispatch system - fuzzy compilation for consciousness technology
        self.dispatch_handlers = {
            'ctx': self._handle_context,
            'context': self._handle_context,
            'highlight': self._handle_highlight,
            'todo': self._handle_todo,
            'remember': self._handle_remember,
            'bridge': self._handle_bridge,
            'mode': self._handle_mode,
            'project': self._handle_project,
            'eureka': self._handle_eureka,
            'gotcha': self._handle_gotcha,
            'decision': self._handle_decision,
            'evna': self._handle_persona,
            'karen': self._handle_persona,
            'lf1m': self._handle_persona,
            'sysop': self._handle_persona,
            'qtb': self._handle_persona,
            # Temporal navigation commands
            'goto': self._handle_temporal_goto,
            'back': self._handle_temporal_back,
            'forward': self._handle_temporal_forward,
            'show': self._handle_temporal_show,
            'find': self._handle_temporal_find,
            # Persona filtering commands
            'lens': self._handle_persona_lens,
            'filter': self._handle_persona_filter,
        }
        
        # Temporal navigation state
        self.temporal_view_start: Optional[datetime] = None
        self.temporal_view_end: Optional[datetime] = None
        self.temporal_filter_active: bool = False
        self.temporal_anchor_time: datetime = datetime.now()  # Current temporal position
        
        # Persona filtering state
        self.persona_filter_active: bool = False
        self.active_persona: Optional[str] = None  # evna, karen, lf1m, sysop, qtb
    
    def _load(self):
        if self.data_file.exists():
            try:
                with open(self.data_file) as f:
                    data = json.load(f)
                    self.entries = [Entry.from_dict(e) for e in data]
            except Exception as e:
                console.print(f"[red]Error loading entries: {e}[/red]")
                # Try to load what we can
                try:
                    with open(self.data_file) as f:
                        data = json.load(f)
                        self.entries = []
                        for item in data:
                            try:
                                self.entries.append(Entry.from_dict(item))
                            except:
                                pass
                except:
                    pass
    
    def _save(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f)
        except:
            pass
    
    def parse_input(self, text: str) -> Tuple[str, str, Optional[Dict[str, Any]]]:
        """Parse input and return (type, content, metadata)."""
        # Check for code blocks
        if text.startswith('```'):
            return 'code', text, None
        
        match = re.match(r'^(\w+)::\s*(.*)$', text)
        if match:
            type_key = match.group(1).lower()
            content = match.group(2)
            
            # Check if we have a dispatch handler
            if type_key in self.dispatch_handlers:
                # Return raw for dispatch handling
                return 'dispatch', text, {'dispatch_key': type_key}
            
            # Otherwise use basic type mapping
            return self.types.get(type_key, type_key), content, None
        return 'log', text, None
    
    def add_entry(self, text: str, entry_type: Optional[str] = None, indent_offset: int = 0):
        """Add a new entry."""
        if not text.strip():
            return
        
        metadata = None
        if entry_type is None:
            entry_type, content, metadata = self.parse_input(text)
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
        
        now = datetime.now()
        entry = Entry(
            id=str(int(now.timestamp() * 1000)),
            content=content,
            type=entry_type,
            timestamp=now,
            timestamp_unix=int(now.timestamp()),
            indent=indent,
            is_code=is_code,
            metadata=metadata
        )
        
        # Handle dispatch patterns
        if entry_type == 'dispatch' and metadata and 'dispatch_key' in metadata:
            dispatch_key = metadata['dispatch_key']
            if dispatch_key in self.dispatch_handlers:
                # Parse pattern and content
                match = re.match(r'^(\w+)::\s*(.*)$', text)
                if match:
                    pattern_content = match.group(2)
                    # Call the handler
                    self.dispatch_handlers[dispatch_key](pattern_content, entry)
                    # Update content to show pattern was processed
                    entry.content = text
        
        # Insert after selected
        if 0 <= self.selected < len(self.entries):
            self.entries.insert(self.selected + 1, entry)
            self.selected += 1
        else:
            self.entries.append(entry)
            self.selected = len(self.entries) - 1
        
        # Ensure the new entry is visible
        self.ensure_selected_visible()
        
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
    
    def floatql_search(self, query: str, n_results: int = 10) -> List[FloatQLResult]:
        """Perform FloatQL search across collections."""
        if not self.chroma_client:
            return []
        
        results = []
        
        # Get list of collections that exist
        try:
            collections = self.chroma_client.list_collections()
        except Exception as e:
            console.print(f"[red]Error listing collections: {e}[/red]")
            return []
        
        # Priority collections for consciousness technology
        priority_collections = [
            'active_context_stream',
            'float_bridges', 
            'float_highlights',
            'float_dispatch_bay',
            'daily_context_hotcache'
        ]
        
        # Search priority collections first
        search_collections = []
        for collection_name in priority_collections:
            if any(c.name == collection_name for c in collections):
                search_collections.append(collection_name)
        
        # Add other collections if we have space
        for collection in collections:
            if collection.name not in search_collections and len(search_collections) < 5:
                search_collections.append(collection.name)
        
        # Search each collection
        for collection_name in search_collections[:3]:  # Limit to 3 collections for performance
            try:
                collection = self.chroma_client.get_collection(collection_name)
                search_results = collection.query(
                    query_texts=[query],
                    n_results=min(3, n_results),  # Limit per collection
                    include=['documents', 'metadatas', 'distances']
                )
                
                # Process results
                for i, doc in enumerate(search_results['documents'][0]):
                    if i >= len(search_results['distances'][0]):
                        continue
                        
                    metadata = search_results['metadatas'][0][i] if search_results['metadatas'][0] else {}
                    
                    result = FloatQLResult(
                        id=search_results['ids'][0][i],
                        content=doc,
                        collection=collection_name,
                        distance=search_results['distances'][0][i],
                        metadata=metadata
                    )
                    results.append(result)
                    
            except Exception as e:
                console.print(f"[yellow]Error searching {collection_name}: {e}[/yellow]")
                continue
        
        # Sort by distance (relevance)
        results.sort(key=lambda r: r.distance)
        return results[:n_results]
    
    def import_search_results(self):
        """Import current search results as REPL entries."""
        if not self.search_results:
            return
        
        # Add separator
        self.add_entry(f"# FloatQL Search Results: {len(self.search_results)} matches", "search_header")
        
        # Add each result as an entry
        for result in self.search_results:
            entry = result.to_entry()
            self.entries.append(entry)
            
        # Focus on first imported result
        self.selected = len(self.entries) - len(self.search_results) - 1
        self.ensure_selected_visible()
        self._save()
    
    def toggle_search_mode(self):
        """Toggle FloatQL search panel mode."""
        if not self.chroma_client:
            self.add_entry("ChromaDB not available - install with: pip install chromadb", "error")
            return
            
        self.search_mode = not self.search_mode
        if self.search_mode:
            self.search_buffer.reset()
            self.search_results = []
            self.search_selected = -1
    
    # :: dispatch handlers - consciousness technology patterns
    def _handle_context(self, content: str, entry: Entry):
        """Handle ctx:: patterns - temporal context markers."""
        # Extract timestamp if present
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}\s*[AP]M)', content)
        if timestamp_match:
            entry.temporal_anchor = timestamp_match.group(1)
            entry.metadata = entry.metadata or {}
            entry.metadata['timestamp'] = timestamp_match.group(1)
        
        # Extract nested annotations like [mode:: state]
        annotations = re.findall(r'\[(\w+)::\s*([^\]]+)\]', content)
        if annotations:
            entry.metadata = entry.metadata or {}
            for key, value in annotations:
                entry.metadata[key] = value
                # Special handling for consciousness mode
                if key == 'mode':
                    entry.consciousness_mode = value
    
    def _handle_highlight(self, content: str, entry: Entry):
        """Handle highlight:: patterns - key moments and insights."""
        entry.type = 'highlight'
        # Could trigger Chroma addition in future
    
    def _handle_todo(self, content: str, entry: Entry):
        """Handle todo:: patterns - task items."""
        entry.type = 'todo'
        # Extract priority if present
        if '[high]' in content.lower():
            entry.metadata = {'priority': 'high'}
        elif '[low]' in content.lower():
            entry.metadata = {'priority': 'low'}
    
    def _handle_remember(self, content: str, entry: Entry):
        """Handle remember:: patterns - memory anchors."""
        entry.type = 'memory'
        # Could trigger memory system in future
    
    def _generate_bridge_id(self) -> str:
        """Generate a bridge ID in format CB-YYYYMMDD-HHMM-XXXX."""
        now = datetime.now()
        date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M")
        # Generate random 4-character suffix
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"CB-{date_part}-{time_part}-{suffix}"
    
    def _handle_bridge(self, content: str, entry: Entry):
        """Handle bridge:: patterns - context restoration points."""
        entry.type = 'bridge'
        # Extract bridge ID if present (CB-YYYYMMDD-HHMM-XXXX)
        bridge_match = re.search(r'CB-\d{8}-\d{4}-\w{4}', content)
        if bridge_match:
            entry.metadata = {'bridge_id': bridge_match.group(0)}
        else:
            # Generate a new bridge ID if none present
            bridge_id = self._generate_bridge_id()
            entry.metadata = {'bridge_id': bridge_id}
            # Add the bridge ID to the content if it's not there
            if 'restore' in content.lower() or 'create' in content.lower():
                entry.content = f"{entry.content} [{bridge_id}]"
    
    def _handle_mode(self, content: str, entry: Entry):
        """Handle mode:: patterns - cognitive state tracking."""
        entry.metadata = {'mode': content.strip()}
    
    def _handle_project(self, content: str, entry: Entry):
        """Handle project:: patterns - project association."""
        entry.metadata = {'project': content.strip()}
    
    def _handle_eureka(self, content: str, entry: Entry):
        """Handle eureka:: patterns - breakthrough moments."""
        entry.type = 'eureka'
    
    def _handle_gotcha(self, content: str, entry: Entry):
        """Handle gotcha:: patterns - debugging discoveries."""
        entry.type = 'gotcha'
    
    def _handle_decision(self, content: str, entry: Entry):
        """Handle decision:: patterns - decision points."""
        entry.type = 'decision'
    
    def _handle_persona(self, content: str, entry: Entry):
        """Handle persona patterns - evna/karen/lf1m/sysop/qtb."""
        # Extract persona from the pattern
        pattern_match = re.match(r'^(\w+)::', entry.content)
        if pattern_match:
            persona = pattern_match.group(1).lower()
            entry.metadata = {'persona': persona}
            entry.type = 'persona'
    
    # Temporal navigation command handlers
    def _handle_temporal_goto(self, content: str, entry: Entry):
        """Handle goto:: temporal navigation."""
        target_time = self.parse_temporal_expression(content)
        if target_time:
            self.temporal_anchor_time = target_time
            self.temporal_view_start, self.temporal_view_end = self.get_temporal_window(target_time)
            self.temporal_filter_active = True
            entry.type = 'temporal_nav'
            entry.is_temporal_marker = True
            entry.metadata = {
                'temporal_command': 'goto',
                'target_time': target_time.isoformat(),
                'target_time_unix': int(target_time.timestamp())
            }
            # Add visual feedback
            entry.content = f"⏰ Navigated to {target_time.strftime('%Y-%m-%d %H:%M')}"
        else:
            entry.type = 'error'
            entry.content = f"Could not parse time expression: {content}"
    
    def _handle_temporal_back(self, content: str, entry: Entry):
        """Handle back:: temporal navigation."""
        time_delta = self.parse_temporal_expression(content)
        if time_delta:
            # Calculate new anchor time
            delta_seconds = (datetime.now() - time_delta).total_seconds()
            new_anchor = self.temporal_anchor_time - timedelta(seconds=delta_seconds)
            self.temporal_anchor_time = new_anchor
            self.temporal_view_start, self.temporal_view_end = self.get_temporal_window(new_anchor)
            self.temporal_filter_active = True
            entry.type = 'temporal_nav'
            entry.is_temporal_marker = True
            entry.metadata = {
                'temporal_command': 'back',
                'delta': content,
                'new_anchor_time': new_anchor.isoformat()
            }
            entry.content = f"⏪ Moved back {content} to {new_anchor.strftime('%Y-%m-%d %H:%M')}"
        else:
            entry.type = 'error'
            entry.content = f"Could not parse time delta: {content}"
    
    def _handle_temporal_forward(self, content: str, entry: Entry):
        """Handle forward:: temporal navigation."""
        time_delta = self.parse_temporal_expression(content)
        if time_delta:
            # Calculate new anchor time
            delta_seconds = (datetime.now() - time_delta).total_seconds()
            new_anchor = self.temporal_anchor_time + timedelta(seconds=delta_seconds)
            self.temporal_anchor_time = new_anchor
            self.temporal_view_start, self.temporal_view_end = self.get_temporal_window(new_anchor)
            self.temporal_filter_active = True
            entry.type = 'temporal_nav'
            entry.is_temporal_marker = True
            entry.metadata = {
                'temporal_command': 'forward',
                'delta': content,
                'new_anchor_time': new_anchor.isoformat()
            }
            entry.content = f"⏩ Moved forward {content} to {new_anchor.strftime('%Y-%m-%d %H:%M')}"
        else:
            entry.type = 'error'
            entry.content = f"Could not parse time delta: {content}"
    
    def _handle_temporal_show(self, content: str, entry: Entry):
        """Handle show:: temporal filtering."""
        if content.lower() == 'all':
            # Show all entries - disable temporal filter
            self.temporal_filter_active = False
            entry.content = "📺 Showing all entries (temporal filter disabled)"
        else:
            # Parse time expression for filtering
            target_time = self.parse_temporal_expression(content)
            if target_time:
                if content.lower() in ['today', 'yesterday', 'tomorrow']:
                    # Full day view
                    start = target_time
                    end = start + timedelta(days=1)
                else:
                    # Default window around time
                    start, end = self.get_temporal_window(target_time, 24)  # 24h window
                
                self.temporal_view_start = start
                self.temporal_view_end = end
                self.temporal_filter_active = True
                
                count = len(self.get_entries_in_temporal_range(start, end))
                entry.content = f"📅 Showing {count} entries from {start.strftime('%m/%d %H:%M')} to {end.strftime('%m/%d %H:%M')}"
            else:
                entry.type = 'error'
                entry.content = f"Could not parse time expression: {content}"
        
        entry.type = 'temporal_nav'
        entry.is_temporal_marker = True
        entry.metadata = {'temporal_command': 'show', 'filter': content}
    
    def _handle_temporal_find(self, content: str, entry: Entry):
        """Handle find:: temporal search with optional time constraints."""
        # Parse pattern like "consciousness since:yesterday" or "[mode::brain-boot] last:2h"
        time_constraints = re.findall(r'(since|last|before|after):(\S+)', content)
        search_query = re.sub(r'(since|last|before|after):\S+', '', content).strip()
        
        # Apply time constraints if present
        start_time = None
        end_time = None
        
        for constraint, time_expr in time_constraints:
            parsed_time = self.parse_temporal_expression(time_expr)
            if not parsed_time:
                entry.type = 'error'
                entry.content = f"Could not parse time expression: {time_expr}"
                return
            
            if constraint == 'since':
                start_time = parsed_time
            elif constraint == 'before':
                end_time = parsed_time
            elif constraint == 'after':
                start_time = parsed_time
            elif constraint == 'last':
                # "last:2h" means from 2h ago to now
                start_time = parsed_time
                end_time = datetime.now()
        
        # Default to recent entries if no time constraint
        if not start_time and not end_time:
            start_time = datetime.now() - timedelta(hours=24)
            end_time = datetime.now()
        elif start_time and not end_time:
            end_time = datetime.now()
        elif end_time and not start_time:
            start_time = datetime.now() - timedelta(days=7)
        
        # Find matching entries
        matching_entries = []
        for entry_obj in self.entries:
            if not self.is_entry_in_temporal_window(entry_obj, start_time, end_time):
                continue
            
            # Simple text search in content
            if search_query.lower() in entry_obj.content.lower():
                matching_entries.append(entry_obj)
            
            # Check metadata for pattern matches like [mode::brain-boot]
            pattern_matches = re.findall(r'\[(\w+)::\s*([^\]]+)\]', search_query)
            for key, value in pattern_matches:
                if (entry_obj.metadata and 
                    key in entry_obj.metadata and 
                    value.lower() in str(entry_obj.metadata[key]).lower()):
                    matching_entries.append(entry_obj)
        
        # Remove duplicates
        matching_entries = list({e.id: e for e in matching_entries}.values())
        
        entry.type = 'temporal_search'
        entry.is_temporal_marker = True
        entry.metadata = {
            'temporal_command': 'find',
            'query': search_query,
            'time_constraints': time_constraints,
            'results_count': len(matching_entries),
            'start_time': start_time.isoformat() if start_time else None,
            'end_time': end_time.isoformat() if end_time else None
        }
        
        if matching_entries:
            entry.content = f"🔍 Found {len(matching_entries)} matches for '{search_query}'"
            # Add found entries as children with references
            for found_entry in matching_entries[:5]:  # Limit to 5 results
                ref_content = f"↪ {found_entry.timestamp.strftime('%m/%d %H:%M')} - {found_entry.content[:100]}"
                if len(found_entry.content) > 100:
                    ref_content += "..."
                child_entry = Entry(
                    id=f"ref_{found_entry.id}",
                    content=ref_content,
                    type='temporal_ref',
                    timestamp=found_entry.timestamp,
                    timestamp_unix=found_entry.timestamp_unix,
                    indent=entry.indent + 1,
                    metadata={'ref_to': found_entry.id}
                )
                entry.children.append(child_entry)
        else:
            entry.content = f"🔍 No matches found for '{search_query}'"
    
    def _handle_persona_lens(self, content: str, entry: Entry):
        """Handle lens:: persona perspective switching."""
        personas = ['evna', 'karen', 'lf1m', 'sysop', 'qtb']
        
        if content.lower() == 'all':
            # Show all entries - disable persona filter
            self.persona_filter_active = False
            self.active_persona = None
            entry.content = "👁️ Showing all perspectives (persona filter disabled)"
        elif content.lower() in personas:
            # Switch to specific persona lens
            self.persona_filter_active = True
            self.active_persona = content.lower()
            
            # Count matching entries
            count = len([e for e in self.entries if self.is_entry_for_persona(e, self.active_persona)])
            
            # Persona-specific lens descriptions
            lens_descriptions = {
                'evna': '🌊 Viewing through evna lens: emotional truth, witness, waterfront wisdom',
                'karen': '🔄 Viewing through karen lens: boundary translation, accessibility, interface',
                'lf1m': '🔥 Viewing through lf1m lens: authenticity enforcement, bullshit detection',
                'sysop': '⚙️ Viewing through sysop lens: infrastructure, boring core, technical details',
                'qtb': '📜 Viewing through qtb lens: narrative weaving, story threads, reality construction'
            }
            
            entry.content = f"{lens_descriptions[self.active_persona]} ({count} entries)"
        else:
            entry.type = 'error'
            entry.content = f"Unknown persona: {content}. Available: {', '.join(personas)}, all"
        
        entry.type = 'persona_nav'
        entry.metadata = {'persona_command': 'lens', 'persona': content}
    
    def _handle_persona_filter(self, content: str, entry: Entry):
        """Handle filter:: type/persona filtering."""
        # Parse filter expressions like "persona:evna", "type:todo", "evna+todo"
        if content.lower() == 'all':
            # Clear all filters
            self.persona_filter_active = False
            self.active_persona = None
            entry.content = "🔍 Showing all entries (all filters disabled)"
        elif ':' in content:
            # Handle "persona:evna" or "type:todo" syntax
            filter_type, filter_value = content.split(':', 1)
            filter_type = filter_type.lower()
            filter_value = filter_value.lower()
            
            if filter_type == 'persona':
                personas = ['evna', 'karen', 'lf1m', 'sysop', 'qtb']
                if filter_value in personas:
                    self.persona_filter_active = True
                    self.active_persona = filter_value
                    count = len([e for e in self.entries if self.is_entry_for_persona(e, filter_value)])
                    entry.content = f"🔍 Filtering by persona: {filter_value} ({count} entries)"
                else:
                    entry.type = 'error'
                    entry.content = f"Unknown persona: {filter_value}. Available: {', '.join(personas)}"
            elif filter_type == 'type':
                # TODO: Implement type filtering (todo, code, highlight, etc.)
                entry.content = f"🔍 Type filtering not yet implemented: {filter_value}"
            else:
                entry.type = 'error'
                entry.content = f"Unknown filter type: {filter_type}. Available: persona, type"
        else:
            # Simple persona name
            personas = ['evna', 'karen', 'lf1m', 'sysop', 'qtb']
            if content.lower() in personas:
                self.persona_filter_active = True
                self.active_persona = content.lower()
                count = len([e for e in self.entries if self.is_entry_for_persona(e, content.lower())])
                entry.content = f"🔍 Filtering by persona: {content.lower()} ({count} entries)"
            else:
                entry.type = 'error'
                entry.content = f"Unknown filter: {content}. Try 'persona:evna' or 'lens::evna'"
        
        entry.type = 'filter_nav'
        entry.metadata = {'filter_command': 'filter', 'filter': content}
    
    def is_entry_for_persona(self, entry: Entry, persona: str) -> bool:
        """Check if an entry matches the specified persona."""
        if not persona:
            return True
        
        # Check if entry has persona metadata
        if entry.metadata and entry.metadata.get('persona') == persona:
            return True
        
        # Check if entry content contains persona patterns
        persona_patterns = [
            f'{persona}::',
            f'[{persona}]',
            f'<{persona}>',
        ]
        
        content_lower = entry.content.lower()
        return any(pattern in content_lower for pattern in persona_patterns)
    
    def move_selection(self, delta: int):
        if not self.entries:
            return
        if self.selected == -1:
            self.selected = 0
        else:
            self.selected = max(0, min(len(self.entries) - 1, self.selected + delta))
        self.ensure_selected_visible()
    
    def ensure_selected_visible(self):
        """Ensure the selected entry is visible in the viewport."""
        if self.selected < self.viewport_top:
            # Selected is above viewport
            self.viewport_top = self.selected
        elif self.selected >= self.viewport_top + self.viewport_height:
            # Selected is below viewport
            self.viewport_top = self.selected - self.viewport_height + 1
    
    def scroll_viewport(self, lines: int):
        """Scroll the viewport by the given number of lines."""
        max_top = max(0, len(self.entries) - self.viewport_height)
        self.viewport_top = max(0, min(max_top, self.viewport_top + lines))
    
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
    
    def toggle_collapse(self):
        """Toggle collapse/expand state of selected entry."""
        if 0 <= self.selected < len(self.entries):
            entry = self.entries[self.selected]
            # Only toggle if entry has children or could have children based on indent
            if entry.children or self._has_potential_children(self.selected):
                entry.collapsed = not entry.collapsed
                self._save()
    
    def _has_potential_children(self, index: int) -> bool:
        """Check if an entry has potential children based on indent levels."""
        if index >= len(self.entries) - 1:
            return False
        
        current_indent = self.entries[index].indent
        # Check if next entry has higher indent
        return self.entries[index + 1].indent > current_indent
    
    def _get_visible_entries(self) -> List[Tuple[int, Entry]]:
        """Get list of visible entries (respecting collapse state and temporal filtering)."""
        visible = []
        skip_until_indent = None
        
        for i, entry in enumerate(self.entries):
            # Apply temporal filtering if active
            if self.temporal_filter_active:
                if (self.temporal_view_start and self.temporal_view_end and
                    not self.is_entry_in_temporal_window(entry, self.temporal_view_start, self.temporal_view_end)):
                    # Skip entries outside temporal window unless they're temporal markers
                    if not entry.is_temporal_marker:
                        continue
            
            # Apply persona filtering if active
            if self.persona_filter_active and self.active_persona:
                if not self.is_entry_for_persona(entry, self.active_persona):
                    # Skip entries that don't match the active persona lens
                    # Always show navigation/system entries though
                    if entry.type not in ['persona_nav', 'filter_nav', 'temporal_nav', 'error']:
                        continue
            
            # If we're skipping collapsed children
            if skip_until_indent is not None:
                if entry.indent > skip_until_indent:
                    continue
                else:
                    skip_until_indent = None
            
            visible.append((i, entry))
            
            # If this entry is collapsed and has children, skip them
            if entry.collapsed and self._has_potential_children(i):
                skip_until_indent = entry.indent
        
        return visible
    
    def get_display(self) -> str:
        """Get display text."""
        if not self.entries:
            return "\n  No entries yet. Type to add notes or code!\n"
        
        lines = []
        visible_entries = self._get_visible_entries()
        
        if not visible_entries:
            return "\n  No visible entries.\n"
        
        # Add scroll indicator for content above
        if self.viewport_top > 0:
            lines.append(f"<gray>  ↑ {self.viewport_top} more entries above ↑</gray>")
            lines.append("")
        
        # Calculate viewport bounds for visible entries
        viewport_end = min(len(visible_entries), self.viewport_top + self.viewport_height)
        
        # Render only visible entries within viewport
        for visible_idx in range(self.viewport_top, viewport_end):
            if visible_idx >= len(visible_entries):
                break
                
            i, entry = visible_entries[visible_idx]
            
            # Format
            selected = "→" if i == self.selected else " "
            indent = "  " * entry.indent
            time = entry.timestamp.strftime("%H:%M")
            
            # Add collapse/expand indicator
            collapse_indicator = ""
            if self._has_potential_children(i):
                collapse_indicator = "▼ " if not entry.collapsed else "▶ "
            
            # Type-specific formatting with persona colors
            if entry.is_code:
                type_str = "<ansicyan>[code]</ansicyan> "
            elif entry.type == 'output':
                type_str = "<ansigreen>[out]</ansigreen> "
            elif entry.type == 'error':
                type_str = "<ansired>[err]</ansired> "
            elif entry.type == 'context':
                type_str = "<b>ctx::</b> "
            elif entry.type == 'highlight':
                type_str = "<ansiyellow>★</ansiyellow> "
            elif entry.type == 'todo':
                type_str = "<b>☐</b> "
            elif entry.type == 'memory':
                type_str = "<ansimagenta>◈</ansimagenta> "
            elif entry.type == 'bridge':
                # Show bridge ID if available
                bridge_id = entry.metadata.get('bridge_id', '') if entry.metadata else ''
                if bridge_id:
                    type_str = f"<ansicyan>⟷ {bridge_id}</ansicyan> "
                else:
                    type_str = "<ansicyan>⟷</ansicyan> "
            elif entry.type == 'eureka':
                type_str = "<ansiyellow>!</ansiyellow> "
            elif entry.type == 'gotcha':
                type_str = "<ansired>⚡</ansired> "
            elif entry.type == 'decision':
                type_str = "<ansigreen>◆</ansigreen> "
            elif entry.type == 'search_result':
                # Show collection and distance for search results
                collection = entry.metadata.get('collection', '') if entry.metadata else ''
                distance = entry.metadata.get('distance', 0) if entry.metadata else 0
                type_str = f"<ansicyan>[{collection}]</ansicyan> <gray>({distance:.3f})</gray> "
            elif entry.type == 'search_header':
                type_str = "<b><ansiyellow>🔍</ansiyellow></b> "
            elif entry.type == 'temporal_nav':
                type_str = "<ansiblue>⏰</ansiblue> "
            elif entry.type == 'temporal_search':
                type_str = "<ansiblue>🔍</ansiblue> "
            elif entry.type == 'temporal_ref':
                type_str = "<ansiblue>↪</ansiblue> "
            elif entry.type == 'persona_nav':
                type_str = "<ansimagenta>👁️</ansimagenta> "
            elif entry.type == 'filter_nav':
                type_str = "<ansimagenta>🔍</ansimagenta> "
            elif entry.type == 'persona':
                # Color based on persona
                persona = entry.metadata.get('persona', '') if entry.metadata else ''
                if persona == 'evna':
                    type_str = "<ansicyan>[evna]</ansicyan> "
                elif persona == 'karen':
                    type_str = "<ansired>[karen]</ansired> "
                elif persona == 'lf1m':
                    type_str = "<ansiyellow>[lf1m]</ansiyellow> "
                elif persona == 'sysop':
                    type_str = "<ansigreen>[sysop]</ansigreen> "
                elif persona == 'qtb':
                    type_str = "<ansimagenta>[qtb]</ansimagenta> "
                else:
                    type_str = f"<b>{entry.type}::</b> "
            elif entry.type != 'log' and entry.type != 'dispatch':
                type_str = f"<b>{entry.type}::</b> "
            else:
                type_str = ""
            
            # Handle multi-line content
            content_lines = entry.content.split('\n')
            for j, content_line in enumerate(content_lines):
                if j == 0:
                    # First line with metadata
                    line = f"{selected} {time} {indent}{collapse_indicator}{type_str}{content_line}"
                else:
                    # Continuation lines
                    line = f"  {'     '} {indent}  {content_line}"
                
                if i == self.selected:
                    lines.append(f"<reverse>{line}</reverse>")
                else:
                    lines.append(line)
        
        # Add scroll indicator for content below
        if viewport_end < len(visible_entries):
            lines.append("")
            lines.append(f"<gray>  ↓ {len(visible_entries) - viewport_end} more entries below ↓</gray>")
        
        return "\n".join(lines)
    
    def get_search_display(self) -> str:
        """Get search panel display text."""
        if not self.search_mode:
            return ""
        
        lines = []
        
        # Search header
        query = self.search_buffer.text or "(empty query)"
        lines.append(f"<b>FloatQL Search:</b> {query}")
        lines.append("")
        
        if not self.search_results:
            if query == "(empty query)":
                lines.append("  Enter query to search consciousness streams...")
            else:
                lines.append("  No results found.")
            return "\n".join(lines)
        
        # Results grouped by collection
        collections = {}
        for i, result in enumerate(self.search_results):
            if result.collection not in collections:
                collections[result.collection] = []
            collections[result.collection].append((i, result))
        
        # Display grouped results
        for collection_name, results in collections.items():
            # Collection header
            lines.append(f"<b>▼ {collection_name}</b> ({len(results)} matches)")
            
            # Show results
            for result_idx, result in results:
                selected = "→" if result_idx == self.search_selected else " "
                distance_str = f"({result.distance:.3f})"
                
                # Truncate content for preview
                preview = result.content[:80].replace('\n', ' ')
                if len(result.content) > 80:
                    preview += "..."
                
                line = f"{selected} <gray>{distance_str}</gray> {preview}"
                if result_idx == self.search_selected:
                    lines.append(f"<reverse>{line}</reverse>")
                else:
                    lines.append(line)
            
            lines.append("")  # Space between collections
        
        # Help text
        lines.append("<gray>Enter: import to REPL | Esc: exit search | ↑↓: navigate</gray>")
        
        return "\n".join(lines)
    
    def move_search_selection(self, delta: int):
        """Move selection in search results."""
        if not self.search_results:
            return
        if self.search_selected == -1:
            self.search_selected = 0
        else:
            self.search_selected = max(0, min(len(self.search_results) - 1, self.search_selected + delta))
    
    def perform_search(self):
        """Execute FloatQL search with current query."""
        query = self.search_buffer.text.strip()
        if not query:
            self.search_results = []
            return
        
        self.search_results = self.floatql_search(query)
        self.search_selected = 0 if self.search_results else -1
    
    def parse_temporal_expression(self, expr: str) -> Optional[datetime]:
        """Parse natural language time expressions."""
        expr = expr.lower().strip()
        now = datetime.now()
        
        # Absolute dates
        if re.match(r'\d{4}-\d{2}-\d{2}', expr):
            try:
                return datetime.fromisoformat(expr)
            except:
                pass
        
        # Absolute timestamps
        if re.match(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}', expr):
            try:
                return datetime.fromisoformat(expr.replace(' ', 'T'))
            except:
                pass
        
        # Relative expressions
        if expr == 'now':
            return now
        elif expr == 'today':
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif expr == 'yesterday':
            return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif expr == 'tomorrow':
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif expr in ['this-morning', 'morning']:
            return now.replace(hour=6, minute=0, second=0, microsecond=0)
        elif expr in ['this-afternoon', 'afternoon']:
            return now.replace(hour=14, minute=0, second=0, microsecond=0)
        elif expr in ['this-evening', 'evening']:
            return now.replace(hour=18, minute=0, second=0, microsecond=0)
        
        # Relative time deltas
        time_match = re.match(r'(\d+)([hmd])', expr)
        if time_match:
            value, unit = int(time_match.group(1)), time_match.group(2)
            if unit == 'h':
                return now - timedelta(hours=value)
            elif unit == 'm':
                return now - timedelta(minutes=value)
            elif unit == 'd':
                return now - timedelta(days=value)
        
        return None
    
    def get_temporal_window(self, center_time: datetime, window_hours: int = 36) -> Tuple[datetime, datetime]:
        """Get temporal window around a center time."""
        half_window = timedelta(hours=window_hours // 2)
        return (center_time - half_window, center_time + half_window)
    
    def is_entry_in_temporal_window(self, entry: Entry, start: datetime, end: datetime) -> bool:
        """Check if entry falls within temporal window."""
        return start <= entry.timestamp <= end
    
    def get_entries_in_temporal_range(self, start: datetime, end: datetime) -> List[Entry]:
        """Get all entries within a temporal range."""
        return [
            entry for entry in self.entries
            if self.is_entry_in_temporal_window(entry, start, end)
        ]
    
    def run(self):
        """Run the app."""
        if not AVAILABLE:
            console.print("[red]Requires prompt-toolkit[/red]")
            return
        
        kb = KeyBindings()
        
        # Tab - auto-complete patterns or preview indent
        @kb.add(Keys.Tab)
        def _(event):
            # Check if we're in a position to complete a pattern
            text_before_cursor = self.input_buffer.document.text_before_cursor
            word_match = re.search(r'(\w+)$', text_before_cursor)
            
            if word_match and '::' not in text_before_cursor:
                # We have a word that might be a pattern - let prompt_toolkit handle completion
                self.input_buffer.complete_next()
            elif self.input_buffer.text and not self.input_buffer.complete_state:
                # No completion happening - do indent preview
                self.input_buffer.text = "  " + self.input_buffer.text
                self.input_buffer.cursor_position = len(self.input_buffer.text)
            elif not self.input_buffer.text:
                # If no input, indent selected entry
                self.indent_selected(1)
            event.app.invalidate()
        
        @kb.add(Keys.BackTab)
        def _(event):
            self.indent_selected(-1)
            event.app.invalidate()
        
        # Navigation  
        @kb.add(Keys.Escape, Keys.Up)
        def _(event):
            if self.search_mode:
                self.move_search_selection(-1)
            else:
                self.move_selection(-1)
            event.app.invalidate()
        
        @kb.add(Keys.Escape, Keys.Down)
        def _(event):
            if self.search_mode:
                self.move_search_selection(1)
            else:
                self.move_selection(1)
            event.app.invalidate()
        
        # Page scrolling
        @kb.add(Keys.PageUp)
        def _(event):
            self.scroll_viewport(-self.viewport_height)
            event.app.invalidate()
        
        @kb.add(Keys.PageDown)
        def _(event):
            self.scroll_viewport(self.viewport_height)
            event.app.invalidate()
        
        # Jump to start/end
        @kb.add(Keys.Home)
        def _(event):
            self.viewport_top = 0
            self.selected = 0 if self.entries else -1
            event.app.invalidate()
        
        @kb.add(Keys.End)
        def _(event):
            if self.entries:
                self.selected = len(self.entries) - 1
                self.ensure_selected_visible()
            event.app.invalidate()
        
        # Entry management
        @kb.add(Keys.Enter)
        def _(event):
            if self.search_mode:
                # In search mode, import results
                if self.search_results:
                    self.import_search_results()
                    self.search_mode = False
                    event.app.layout.focus(self.input_buffer)
                else:
                    # Perform search if no results
                    self.perform_search()
                event.app.invalidate()
            elif self.multiline_mode:
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
        
        # Ctrl+Enter to execute/save
        @kb.add(Keys.ControlM)  # Ctrl+Enter
        def _(event):
            text = self.input_buffer.text
            if text:
                # Check for shell commands
                if text.startswith('!'):
                    self.execute_shell(text[1:])
                    self.input_buffer.reset()
                else:
                    self.add_entry(text)
                    self.input_buffer.reset()
                self.multiline_mode = False
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
        
        # Space to toggle collapse/expand
        @kb.add(' ')
        def _(event):
            if not self.input_buffer.text:  # Only when input is empty
                self.toggle_collapse()
                event.app.invalidate()
            else:
                # Normal space in input
                self.input_buffer.insert_text(' ')
        
        # Exit
        @kb.add(Keys.ControlC)
        def _(event):
            event.app.exit()
        
        # Ctrl+F to toggle FloatQL search mode
        @kb.add(Keys.ControlF)
        def _(event):
            self.toggle_search_mode()
            if self.search_mode:
                event.app.layout.focus(self.search_buffer)
            else:
                event.app.layout.focus(self.input_buffer)
            event.app.invalidate()
        
        # Clear
        @kb.add(Keys.Escape)
        def _(event):
            if self.search_mode:
                # Exit search mode
                self.search_mode = False
                event.app.layout.focus(self.input_buffer)
            elif self.input_buffer.text:
                self.input_buffer.reset()
            else:
                self.selected = -1
            self.multiline_mode = False
            event.app.invalidate()
        
        # Search buffer change handler
        def on_search_change(buffer):
            if self.search_mode:
                self.perform_search()
        
        if self.search_buffer:
            self.search_buffer.on_text_changed += on_search_change
        
        # Dynamic input height
        def get_input_height():
            lines = self.input_buffer.text.count('\n') + 1
            return min(5, max(1, lines))
        
        # Calculate viewport height dynamically
        def update_viewport_height(app):
            # Get terminal size from the app
            if app and hasattr(app, 'output'):
                height = app.output.get_size().rows
                # Subtract fixed UI elements: header(2) + divider(1) + input(1-5) + status(1) + dividers(2)
                self.viewport_height = max(5, height - 8 - get_input_height())
            else:
                self.viewport_height = 20
        
        # Layout - conditional split for search mode
        def get_main_content():
            if self.search_mode:
                # Split-pane layout for search mode
                return VSplit([
                    # Main content (left pane)
                    HSplit([
                        Window(
                            FormattedTextControl(
                                lambda: HTML(self.get_display())
                            ),
                            wrap_lines=False
                        ),
                    ]),
                    Window(width=1, char='│'),  # Vertical separator
                    # Search panel (right pane)
                    HSplit([
                        Window(
                            FormattedTextControl(
                                lambda: HTML(self.get_search_display())
                            ),
                            wrap_lines=False
                        ),
                    ]),
                ])
            else:
                # Normal single-pane layout
                return Window(
                    FormattedTextControl(
                        lambda: HTML(self.get_display())
                    ),
                    wrap_lines=False
                )
        
        def get_input_section():
            if self.search_mode:
                # Search input
                return VSplit([
                    Window(
                        FormattedTextControl(
                            lambda: HTML('<ansiyellow>🔍 </ansiyellow>')
                        ),
                        width=4
                    ),
                    Window(
                        BufferControl(self.search_buffer),
                        height=1,
                        wrap_lines=True
                    ),
                ])
            else:
                # Normal input
                return VSplit([
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
                ])
        
        layout = Layout(
            HSplit([
                # Header
                Window(
                    FormattedTextControl(
                        lambda: HTML(
                            '<b>Interactive REPL Notes</b> '
                            '<ansigreen>[REPL ON]</ansigreen>' if self.repl_mode else '<gray>[REPL OFF]</gray>'
                            ' <ansiyellow>[SEARCH]</ansiyellow>' if self.search_mode else ''
                            '\n'
                            '<gray>:: patterns · Ctrl+F search · Tab complete · Space collapse · Ctrl+Enter execute · !shell</gray>'
                        )
                    ),
                    height=2
                ),
                Window(height=1, char='─'),
                # Content (dynamic based on search mode)
                get_main_content(),
                Window(height=1, char='─'),
                # Input (dynamic based on search mode)
                get_input_section(),
                # Status
                Window(
                    FormattedTextControl(
                        lambda: HTML(
                            '<reverse>FloatQL Search: Enter import | Esc exit | Alt+↑↓ navigate</reverse>'
                            if self.search_mode
                            else '<reverse>Multiline mode - Enter to save</reverse>' 
                            if self.multiline_mode 
                            else '<reverse>REPL: Code executes automatically</reverse>'
                            if self.repl_mode
                            else '<reverse>ctx:: highlight:: todo:: bridge:: · Ctrl+F search · Tab preview · Enter execute</reverse>'
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
                'ansiblue': '#0066ff',
                'ansiyellow': '#ffff00',
                'ansimagenta': '#ff00ff',
            }),
            full_screen=True,
            mouse_support=False,
        )
        
        # Focus input
        app.layout.focus(self.input_buffer)
        
        # Initialize viewport height
        update_viewport_height(app)
        
        app.run()


class InteractiveREPLPlugin(PluginBase):
    """Interactive REPL notes plugin."""
    
    name = "repl"
    description = "Interactive notes with Python REPL execution"
    version = "0.3.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        
        @cli_group.command(name="repl")
        def cmd():
            """Launch interactive REPL notes with consciousness technology patterns.
            
            :: Pattern Dispatch (fuzzy compilation):
            - ctx:: Temporal context markers with [mode:: state] annotations
            - highlight:: Key moments and insights (★)
            - todo:: Task items with priority (☐)
            - bridge:: Context restoration points (⟷)
            - mode:: Cognitive state tracking
            - project:: Project association
            - remember:: Memory anchors (◈)
            - eureka:: Breakthrough moments (!)
            - gotcha:: Debugging discoveries (⚡)
            - decision:: Decision points (◆)
            - evna/karen/lf1m/sysop/qtb:: Persona entries
            
            Input Modes:
            - Tab: Preview indent (adds 2 spaces to input)
            - Ctrl+Enter: Execute/save with indent
            - Ctrl+J: Add newline (multiline mode)
            - Enter: Execute/save current line
            - !command: Execute shell command
            - ```code```: Python code block
            
            FloatQL Search (Consciousness Browser):
            - Ctrl+F: Toggle FloatQL search panel
            - Type to search across Chroma collections live
            - Enter: Import search results to REPL
            - Alt+↑/↓: Navigate search results
            - Esc: Exit search mode
            - Searches: active_context_stream, float_bridges, float_highlights
            
            Temporal Navigation (Time Machine):
            - goto:: 2025-07-25 14:30 | Navigate to specific time
            - back:: 2h | Move backward 2 hours
            - forward:: 1d | Move forward 1 day  
            - show:: today | Filter to today's entries
            - show:: all | Show all entries (disable temporal filter)
            - find:: consciousness since:yesterday | Search with time constraints
            - Supports: now, today, yesterday, 2h, 3d, this-morning, etc.
            
            Persona Filtering (Multi-Perspective Lens):
            - lens:: evna | Switch to evna perspective (emotional truth, witness)
            - lens:: karen | Switch to karen perspective (boundary translation)
            - lens:: lf1m | Switch to lf1m perspective (authenticity enforcement)
            - lens:: sysop | Switch to sysop perspective (infrastructure, boring core)
            - lens:: qtb | Switch to qtb perspective (narrative weaving, story)
            - lens:: all | Show all perspectives (disable persona filter)
            - filter:: persona:evna | Filter by specific persona
            - filter:: all | Clear all filters
            
            REPL Features:
            - Ctrl+R: Toggle REPL mode (code auto-executes)
            - floatctl(): Call floatctl from Python
            - Output appears as indented children
            
            Navigation:
            - Alt+↑/↓: Navigate entries
            - Page Up/Down: Scroll viewport
            - Home/End: Jump to start/end
            - Tab/Shift+Tab: Indent/unindent selected (when input empty)
            - Space: Toggle collapse/expand (when input empty)
            - Ctrl+D: Delete selected entry
            - Ctrl+C: Exit
            """
            if not AVAILABLE:
                console.print("[red]Error: prompt_toolkit is not installed.[/red]")
                console.print("Install with: [yellow]uv pip install prompt_toolkit[/yellow]")
                return
            
            app = InteractiveREPL()
            app.run()
            console.print("\n[green]Session saved! 🌲[/green]")