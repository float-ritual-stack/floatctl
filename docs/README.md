# FloatCtl - FLOAT Conversation Processing Tool

A command-line tool for processing and analyzing AI conversation exports, built on a plugin-based architecture for extensibility.

## Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install in development mode
uv pip install -e ".[dev]"

# Optional: Install REPL support
uv pip install -e ".[repl]"
```

### Global Access

To make `floatctl` available globally, add this function to your `~/.zshrc` or `~/.bashrc`:

```bash
# FloatCtl function for development - reflects changes immediately
floatctl() {
    (cd /path/to/floatctl-py && uv run floatctl "$@")
}
```

### Shell Completions

FloatCtl supports tab completion for commands and options. To enable:

**For zsh:**
```bash
# Add to ~/.zshrc
if [ ! -f "$HOME/.config/floatctl/completion.zsh" ]; then
    mkdir -p "$HOME/.config/floatctl"
    _FLOATCTL_COMPLETE=zsh_source floatctl > "$HOME/.config/floatctl/completion.zsh" 2>/dev/null
fi
[ -f "$HOME/.config/floatctl/completion.zsh" ] && source "$HOME/.config/floatctl/completion.zsh"
```

**For bash:**
```bash
# Add to ~/.bashrc
if [ ! -f "$HOME/.config/floatctl/completion.bash" ]; then
    mkdir -p "$HOME/.config/floatctl"
    _FLOATCTL_COMPLETE=bash_source floatctl > "$HOME/.config/floatctl/completion.bash" 2>/dev/null
fi
[ -f "$HOME/.config/floatctl/completion.bash" ] && source "$HOME/.config/floatctl/completion.bash"
```

After adding, reload your shell configuration:
```bash
source ~/.zshrc  # or ~/.bashrc
```

## Usage

### Basic Conversation Splitting

```bash
# Split a conversation export into individual files (outputs to ./output/conversations)
floatctl conversations split conversations.json

# Works with relative paths from any directory
cd /path/to/data/directory
floatctl conversations split ./conversations.json

# Specify custom output directory
floatctl conversations split conversations.json --output-dir ./output

# Export as markdown instead of JSON
floatctl conversations split conversations.json --format markdown

# Export both JSON and markdown (creates .md and .tool_calls.jsonl files)
floatctl conversations split conversations.json --format both

# Organize by date
floatctl conversations split conversations.json --by-date

# Filter conversations after a specific date
floatctl conversations split conversations.json --filter-after 2025-07-01
```

### Pattern Extraction Feature

When exporting conversations to markdown format, FloatCtl automatically extracts and indexes inline patterns from your conversations. This feature is particularly useful for tracking personal annotation systems, commands, and tool usage.

#### Extracted Patterns

1. **Markers** - Inline annotations using `::` syntax (e.g., `ctx::`, `highlight::`, `mode::`)
2. **Float Calls** - FLOAT system commands (e.g., `float.dispatch()`, `float.context.restore()`)
3. **Tool Usage** - AI assistant tool calls tracked throughout the conversation

#### Example Output

When you export a conversation to markdown, the YAML frontmatter includes extracted patterns:

```yaml
---
conversation_title: "2025-07-12 - Consciousness Bootstrap Protocol"
conversation_id: 39a4426e-9076-456b-a22a-9a7bf52e581e
conversation_src: https://claude.ai/chat/39a4426e-9076-456b-a22a-9a7bf52e581e
conversation_created: 2025-07-13T00:17:06.800914Z
conversation_updated: 2025-07-13T06:48:47.435126Z
conversation_dates:
  - 2025-07-13
markers:
  - type: "ctx"
    content: "2025-07-12"
    lines: [9]
  - type: "start_time"
    content: "2025-07-13T00:17:07.780677Z"
    lines: [6]
  - type: "highlight"
    content: "consciousness technology breakthrough"
    lines: [42, 43]
float_calls:
  - call: "float.context.restore.surgical"
    content: ""
    lines: [531]
  - call: "float.dispatch"
    content: "{type: 'consciousness_boot'}"
    lines: [645]
tools_used: ['chroma:chroma_query_documents', 'localhost:search_memory', 'web_fetch']
total_lines: 747
---
```

#### Benefits of Pattern Extraction

- **Search by Pattern Type**: Quickly find all conversations containing specific markers or commands
- **Track Tool Usage**: See which AI tools were used in each conversation
- **Personal Annotation System**: Your `::` markers are preserved with line numbers for easy reference
- **Context Restoration**: Float calls are indexed to help restore context in future conversations
- **Conversation Analytics**: Line numbers help you navigate to specific parts of long conversations

#### Using Pattern Data

The extracted patterns make it easy to:

```bash
# Find all conversations with specific markers
grep -l "type: \"ctx\"" output/*.md

# Find conversations using specific tools
grep -l "chroma_query_documents" output/*.md

# Find all float.dispatch calls
grep -A2 "float_calls:" output/*.md | grep "call:"

# Get conversations from a specific date
grep -l "2025-07-12" output/*.md
```

### Tool Call Extraction

When exporting to markdown format with `--format markdown` or `--format both`, FloatCtl automatically extracts tool calls to separate JSONL files:

- Tool calls and results are saved to `.tool_calls.jsonl` files
- Each entry includes the tool name, input, output, and line reference
- In the markdown, tool calls are replaced with references: `{Tool Call: id → filename:line}`
- This keeps markdown files readable while preserving all tool interaction data

Example tool calls file:
```json
{"id": "toolu_01ABC", "type": "tool_use", "name": "Read", "input": {"file_path": "/path/to/file"}, "message_index": 1, "content_index": 1, "sender": "assistant", "created_at": "2025-07-13T10:00:05Z", "line_number": 1}
{"id": "toolu_01ABC", "type": "tool_result", "output": "File contents here...", "is_error": false, "message_index": 1, "content_index": 2, "sender": "assistant", "created_at": "2025-07-13T10:00:06Z", "line_number": 2}
```

### Thinking Blocks and Attachments

FloatCtl handles advanced conversation features:

- **Thinking Blocks**: Preserves Claude's `<thinking>` blocks in markdown exports
- **Attachments**: Automatically creates attachment directories for conversations with file references
- **PDF Support**: Handles PDF attachments and maintains file metadata
- **Structure Preservation**: Maintains original conversation structure including thinking content

### Filename Generation

FloatCtl generates clean, readable filenames:
- Format: `YYYY-MM-DD - Title`
- Example: `2025-07-13 - Consciousness Bootstrap Protocol.md`
- Handles naming conflicts by appending numbers
- Strips redundant date prefixes from titles

### Chroma Vector Database Integration

FloatCtl includes a powerful Chroma plugin for working with vector databases:

```bash
# List all collections
floatctl chroma list

# Get detailed collection info
floatctl chroma info float_bridges

# Peek at collection contents
floatctl chroma peek active_context_stream --limit 5

# Query recent documents
floatctl chroma recent float_highlights --limit 10

# Natural language queries with FloatQL
floatctl chroma floatql "ctx:: meeting with nick"
floatctl chroma floatql "[sysop::] infrastructure updates"
floatctl chroma floatql "bridge::CB-20250713-0130-M3SS"
floatctl chroma floatql "highlights from yesterday"

# Rendered markdown output for better readability
floatctl chroma floatql "bridge::CB-20250713" --rendered
floatctl chroma peek float_bridges --rendered --full
```

#### FloatQL Query Language

FloatQL supports natural language queries with FLOAT-specific patterns:

- **Markers**: `ctx::`, `highlight::`, `mode::` - Find documents with these annotations
- **Personas**: `[sysop::]`, `[karen::]`, `[evna::]` - Filter by persona
- **Bridge IDs**: `bridge::CB-YYYYMMDD-HHMM-XXXX` - Find specific bridges
- **Temporal**: "yesterday", "last week", "July 13" - Time-based filtering
- **Collections**: Automatically detects and routes to appropriate collections

### Interactive Notes & REPL

FloatCtl offers two interactive note-taking interfaces:

#### REPL Mode (Low Friction)

```bash
floatctl repl
```

The original fast-flow interface with:
- **Minimal UI**: Full-screen, no popups, just you and your thoughts
- **Smart parsing**: ctx::, todo::, highlight:: markers
- **REPL mode**: Ctrl+R toggles auto-execution of code blocks
- **Natural indentation**: Tab/Shift+Tab to organize hierarchically
- **Alt+↑/↓ navigation**: Move through entries quickly
- **Shell commands**: !command executes in shell
- **FloatCtl integration**: floatctl() available in Python environment
- **Persistent storage**: ~/.floatctl/repl_notes/

Example workflow:
```
/ ctx:: working on parser optimization
/ todo:: benchmark current implementation
/ ```code
import time
start = time.time()
# ... code here
print(f"Elapsed: {time.time() - start}s")
```

Press Ctrl+R to enable REPL mode - code blocks execute automatically!

#### Textual Mode (Feature Rich)

```bash
floatctl float
```

A more visual interface built with Textual:
- **Tree view**: Hierarchical display of entries
- **Command palette**: Ctrl+P for floatctl commands  
- **Visual styling**: Syntax highlighting, type indicators
- **Mouse support**: Click to select entries
- **Alt+↑/↓ navigation**: Move through tree
- **Ctrl+←/→ indentation**: Organize your thoughts

#### Simplified Mode (Low Friction)

```bash
floatctl float-simple
```

The distilled essence of FLOAT Notes based on maw-held-stories insights:
- **Same-level insertion**: New entries go at the same indent level as selected
- **Tab/Shift+Tab**: Indent/unindent selected entries naturally
- **No popups**: Silent saves, no interruptions
- **Visual indicator**: Shows exactly where next entry will appear
- **Minimal UI**: Just your thoughts and an input field
- **Fast flow**: Type → Enter → Keep going

### Forest Plugin - V0 Project Management

The forest plugin manages V0 projects with enhanced toolbar injection:

```bash
# Update toolbars across all projects
floatctl forest update-toolbar --all

# Update specific number of projects
floatctl forest update-toolbar -n 20

# Parallel updates for speed
floatctl forest update-toolbar --all --parallel 5

# Filter projects by pattern
floatctl forest update-toolbar --filter '*react*'

# Preview changes without applying
floatctl forest update-toolbar --all --dry-run

# Force re-injection of toolbar
floatctl forest update-toolbar --all --force

# Standard forest commands
floatctl forest list            # List all V0 projects
floatctl forest status          # Check project statuses
floatctl forest sync            # Sync projects
```

### MCP Server - Evna Context Concierge

FloatCtl includes an MCP (Model Context Protocol) server that provides natural context management tools for Claude Desktop.

#### Features

- **Natural Context Capture**: Automatically captures `ctx::` markers with flexible timestamp formats
- **Boundary Detection**: Uses local Ollama to detect when you need a break
- **Morning Context**: Retrieve recent context for "brain boot" sessions
- **Semantic Search**: Query your active_context_stream with natural language
- **Boundary Monitoring**: Checks if you're respecting your declared boundaries

#### Installation

```bash
# Install the MCP server in Claude Desktop
floatctl mcp install --claude-desktop

# Restart Claude Desktop to activate
```

#### Usage in Claude Desktop

Once installed, Claude can naturally process your context markers:

```
ctx::2025-07-28 @ 08:05:00 PM - Working on MCP improvements
ctx::2025-07-28 - 9:30 PM - [mode:: debugging] - [project:: floatctl]
ctx:: taking a break for an hour [boundary-set:: 1 hour break]
```

The MCP server automatically:
- Parses timestamps (supports `@`, `-`, various formats)
- Extracts metadata from `[key:: value]` patterns
- Adds to active_context_stream with 36-hour TTL
- Detects implicit break needs using Ollama
- Monitors boundary violations

#### MCP Commands

```bash
# Run the server standalone (for testing)
floatctl mcp serve

# Install to Claude Desktop
floatctl mcp install --claude-desktop

# Uninstall from Claude Desktop
floatctl mcp uninstall --claude-desktop
```

### Other Commands

```bash
# Show processing history for a file
floatctl conversations history conversations.json

# Dry run to preview what would be processed
floatctl conversations split conversations.json --dry-run

# Get help
floatctl --help
floatctl conversations --help
floatctl chroma --help
floatctl forest --help
```

## Architecture

FloatCtl uses a plugin-based architecture that allows for easy extension:

- **Plugin System**: Discover and load plugins via setuptools entry points
- **Database Tracking**: SQLite database tracks all file operations
- **Structured Logging**: JSON logs for analysis and debugging
- **Progress Tracking**: Rich terminal UI with progress bars

## Development

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
uv run ruff format src/
```

## Configuration

Configuration is loaded from (in order):
1. Environment variable: `FLOATCTL_CONFIG`
2. User config: `~/.config/floatctl/config.json`
3. Project config: `./floatctl.config.json`
4. Command-line overrides

## Creating Plugins

### 🚀 Quick Start: Use Plugin Scaffolding

**Generate a working plugin automatically:**

```bash
# Generate a basic plugin
floatctl dev scaffold my_plugin --output-dir ./plugins

# Interactive mode with prompts
floatctl dev scaffold my_plugin --interactive

# Generate a middleware-style plugin  
floatctl dev scaffold my_plugin --middleware
```

This creates a complete plugin structure with proper `register_commands()` method and avoids common mistakes!

### 🚨 CRITICAL: Plugin Command Registration

**ALL commands MUST be defined INSIDE the `register_commands()` method!**

To create a plugin manually:

1. **Inherit from `PluginBase`** and implement `register_commands()` method
2. **Define ALL commands inside the method** (common mistake: commands outside method won't work)
3. **Add entry point** in `pyproject.toml`:
   ```toml
   [project.entry-points."floatctl.plugins"]
   your_plugin = "floatctl.plugins.your_plugin:YourPlugin"
   ```

### Quick Plugin Template

```python
from floatctl.plugin_manager import PluginBase
import rich_click as click
from rich.console import Console

class YourPlugin(PluginBase):
    name = "yourplugin"
    description = "Your plugin description"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register ALL commands inside this method."""
        
        @cli_group.group()
        @click.pass_context
        def yourplugin(ctx: click.Context) -> None:
            """Your plugin commands."""
            pass
        
        # ✅ ALL commands must be defined HERE
        @yourplugin.command()
        @click.pass_context
        def hello(ctx: click.Context) -> None:
            """Say hello."""
            Console().print("[green]Hello from your plugin![/green]")
```

### Plugin Development Checklist

1. **✅ Class inherits from `PluginBase`**
2. **✅ All commands inside `register_commands()` method**
3. **✅ Entry point added to `pyproject.toml`**
4. **✅ Test registration**: `uv run floatctl --help | grep yourplugin`
5. **✅ Test commands**: `uv run floatctl yourplugin --help`

**📖 See `PLUGIN_DEVELOPMENT_GUIDE.md` for complete documentation and common pitfalls.**

## License

[Add your license here]