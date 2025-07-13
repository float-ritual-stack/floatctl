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
# Split a conversation export into individual files
floatctl conversations split conversations.json --output-dir ./output

# Export as markdown instead of JSON
floatctl conversations split conversations.json --format markdown

# Export both JSON and markdown
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

### Filename Generation

FloatCtl generates clean, readable filenames:
- Format: `YYYY-MM-DD - Title`
- Example: `2025-07-13 - Consciousness Bootstrap Protocol.md`
- Handles naming conflicts by appending numbers
- Strips redundant date prefixes from titles

### Other Commands

```bash
# Show processing history for a file
floatctl conversations history conversations.json

# Dry run to preview what would be processed
floatctl conversations split conversations.json --dry-run

# Get help
floatctl --help
floatctl conversations --help
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

To create a new plugin:

1. Inherit from `PluginBase` in `plugin_manager.py`
2. Implement the `register_commands()` method
3. Add entry point in `pyproject.toml`:
   ```toml
   [project.entry-points."floatctl.plugins"]
   your_plugin = "floatctl.plugins.your_plugin:YourPlugin"
   ```

## License

[Add your license here]