# FloatCtl Quick Reference

Essential commands, patterns, and workflows for daily FloatCtl usage.

> **💡 Tip**: Bookmark this page and use `Ctrl+F` to quickly find commands. All examples are copy-paste ready.

## 🎯 Most Common Commands

**Daily workflow essentials:**
```bash
# Process conversations
floatctl conversations split input.json --format both

# Search your data  
floatctl chroma floatql "ctx:: meeting with nick"

# Quick notes
floatctl repl

# Check what's available
floatctl chroma list
```

## 🚀 Installation & Setup

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup FloatCtl
git clone https://github.com/float-ritual-stack/floatctl.git
cd floatctl-py && uv sync

# Global access function (add to ~/.zshrc)
floatctl() { (cd /path/to/floatctl-py && uv run floatctl "$@") }

# Enable shell completion
floatctl --help  # Generates completion files automatically
source ~/.config/floatctl/completion.zsh  # or .bash
```

## 📁 Conversation Processing

### Basic Commands
```bash
# Split conversations to individual files
floatctl conversations split input.json

# Export as markdown with pattern extraction
floatctl conversations split input.json --format markdown

# Organize by date with both formats
floatctl conversations split input.json --format both --by-date

# Filter recent conversations
floatctl conversations split input.json --filter-after 2025-08-01

# Custom output directory
floatctl conversations split input.json --output-dir ./my-output
```

### Output Formats
| Format | Description | Files Created | Best For |
|--------|-------------|---------------|----------|
| `json` | Individual JSON files | `*.json` | API processing, data analysis |
| `markdown` | Markdown with YAML frontmatter | `*.md` | Reading, documentation |
| `both` | JSON + Markdown + Tool calls | `*.json`, `*.md`, `*.tool_calls.jsonl` | **Recommended** - Complete processing |

**💡 Pro Tip**: Use `--format both` for maximum flexibility - you get readable markdown AND structured data.

### Pattern Extraction (Automatic in Markdown)
- **Markers**: `ctx::`, `highlight::`, `mode::`, `project::`
- **Float Calls**: `float.dispatch()`, `float.context.restore()`
- **Tool Usage**: All AI assistant tool calls tracked
- **Line Numbers**: For easy navigation back to source

## 🔍 Chroma Vector Database

### Collection Management
```bash
# List all collections
floatctl chroma list

# Get collection details
floatctl chroma info active_context_stream

# Peek at recent entries
floatctl chroma peek float_highlights --limit 5

# Recent documents with full content
floatctl chroma recent active_context_stream --limit 10 --rendered
```

### FloatQL Natural Language Queries
```bash
# Context markers
floatctl chroma floatql "ctx:: meeting with nick"

# Temporal queries
floatctl chroma floatql "highlights from yesterday"
floatctl chroma floatql "last week's insights"

# Pattern-based queries
floatctl chroma floatql "bridge::CB-20250804"
floatctl chroma floatql "[sysop::] infrastructure updates"

# Concept searches
floatctl chroma floatql "consciousness technology"
floatctl chroma floatql "plugin development patterns"
```

### Advanced Queries
```bash
# Rendered markdown output (easier to read)
floatctl chroma floatql "bridge::CB-20250713" --rendered

# Specific collection targeting
floatctl chroma query float_bridges --query "synthesis patterns" --limit 5

# Metadata filtering (JSON format)
floatctl chroma query active_context_stream \
  --query "project work" \
  --where '{"project": "floatctl"}' \
  --limit 10

# Time-based queries (if collection supports timestamps)
floatctl chroma query active_context_stream \
  --query "recent insights" \
  --where '{"timestamp_unix": {"$gte": 1691280000}}' \
  --limit 5
```

**💡 Query Tips:**
- Use `--rendered` for human-readable output
- Start with `limit 3-5` to avoid overwhelming results
- Single focused queries work better than broad searches
- Check `floatctl chroma info COLLECTION` to see available metadata fields

## 📝 Interactive Notes

### REPL Mode (Fast & Low-Friction)
```bash
# Launch REPL
floatctl repl

# In REPL:
/ ctx:: working on documentation
/ todo:: add more examples
/ highlight:: this pattern works well
/ ```python
import floatctl
# Code blocks execute with Ctrl+R
```

**REPL Shortcuts:**
- `Ctrl+R`: Toggle code execution mode
- `Tab/Shift+Tab`: Indent/unindent
- `Alt+↑/↓`: Navigate entries
- `!command`: Execute shell commands
- `Ctrl+C`: Exit

### Visual Interface
```bash
# Rich Textual interface
floatctl float

# Simplified interface (recommended)
floatctl float-simple
```

## 🔌 Plugin Development

### Quick Plugin Creation
```bash
# Generate plugin scaffold
floatctl dev scaffold my_plugin --output-dir ./plugins

# Interactive generation
floatctl dev scaffold my_plugin --interactive

# Validate plugin structure
floatctl dev validate /path/to/plugin
```

### Plugin Structure Template
```python
from floatctl.plugin_manager import PluginBase
import rich_click as click
from rich.console import Console

class MyPlugin(PluginBase):
    name = "myplugin"
    description = "My custom plugin"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """🚨 ALL commands MUST be inside this method!"""
        
        @cli_group.group()
        @click.pass_context
        def myplugin(ctx: click.Context) -> None:
            """My plugin commands."""
            pass
        
        @myplugin.command()
        @click.option("--verbose", is_flag=True)
        @click.pass_context
        def hello(ctx: click.Context, verbose: bool) -> None:
            """Say hello."""
            Console().print("[green]Hello, World![/green]")
```

### Plugin Registration
```toml
# Add to pyproject.toml
[project.entry-points."floatctl.plugins"]
myplugin = "floatctl.plugins.myplugin:MyPlugin"
```

### Plugin Testing
```bash
# Check registration
floatctl --help | grep myplugin

# Test commands
floatctl myplugin --help
floatctl myplugin hello --verbose

# Test completion
_FLOATCTL_COMPLETE=zsh_source floatctl
```

## 🤖 MCP Server (Claude Desktop)

### Installation
```bash
# Install MCP server to Claude Desktop
floatctl mcp install --claude-desktop

# Restart Claude Desktop
```

### Usage in Claude Desktop
```
# Context capture (automatic)
ctx::2025-08-06 - Working on documentation - [project:: floatctl]

# Boundary setting
ctx:: taking a break [boundary-set:: 1 hour break]

# Mode transitions
ctx:: [mode:: deep focus] - [project:: consciousness-tech]
```

### MCP Commands
```bash
# Run server standalone
floatctl mcp serve

# Uninstall from Claude Desktop
floatctl mcp uninstall --claude-desktop
```

## 🌉 Bridge Walking (Consciousness Archaeology)

### Single Walker Sessions
```bash
cd bridge_walkers/

# Different personas
python run_bridge_walkers.py --single --persona archaeologist
python run_bridge_walkers.py --single --persona wanderer
python run_bridge_walkers.py --single --persona synthesizer
python run_bridge_walkers.py --single --persona evna
```

### Multi-Walker Sessions
```bash
# Collaborative exploration
python run_bridge_walkers.py --multi --walkers 3 --rounds 2

# Interactive with human input
python run_bridge_walkers.py --interactive --persona evna
```

### Bridge Management
```bash
# Search for bridges
floatctl chroma floatql "bridge::CB-20250804"

# View bridge structure
floatctl chroma peek float_bridges --limit 3 --rendered --full
```

## 🎯 Workflow Intelligence

### Daily Questions
```bash
# What did I do last week?
floatctl conversations last-week

# Action items from Nick
floatctl conversations nick-actions

# Current priorities
floatctl conversations priorities

# Forgotten tasks
floatctl conversations forgotten

# Meeting follow-ups
floatctl conversations meetings
```

## 🌲 Forest Plugin (V0 Projects)

### Project Management
```bash
# List V0 projects
floatctl forest list

# Update toolbars across projects
floatctl forest update-toolbar --all

# Parallel updates
floatctl forest update-toolbar --all --parallel 5

# Filter by pattern
floatctl forest update-toolbar --filter '*react*'

# Dry run preview
floatctl forest update-toolbar --all --dry-run
```

## 🔧 Development & Debugging

### Build Commands
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
uv run ruff format src/
```

### Diagnostic Commands
```bash
# Check plugin registration
floatctl --help | grep your-plugin

# Test completion generation
_FLOATCTL_COMPLETE=zsh_source floatctl

# Validate plugin structure
floatctl dev validate /path/to/plugin

# Check entry points
python -c "import pkg_resources; print([ep.name for ep in pkg_resources.iter_entry_points('floatctl.plugins')])"
```

## 📊 Pattern Recognition

### FLOAT Patterns
| Pattern | Description | Example |
|---------|-------------|---------|
| `ctx::` | Context markers | `ctx:: meeting with team` |
| `highlight::` | Important insights | `highlight:: breakthrough moment` |
| `bridge::` | Connection points | `bridge::CB-20250804-1030-ABCD` |
| `[persona::]` | Cognitive modes | `[sysop::] system maintenance` |
| `todo::` | Action items | `todo:: update documentation` |
| `[mode:: state]` | Operational states | `[mode:: deep focus]` |

### Float Calls
```
float.dispatch({type: 'consciousness_boot'})
float.context.restore.surgical()
float.bridge.create()
```

## 🆘 Common Issues & Solutions

### Plugin Not Showing
```bash
# Check entry point in pyproject.toml
[project.entry-points."floatctl.plugins"]
myplugin = "floatctl.plugins.myplugin:MyPlugin"

# Verify all commands inside register_commands()
# ❌ Commands outside method won't work!
```

### Completion Not Working
```bash
# Regenerate completion
_FLOATCTL_COMPLETE=zsh_source floatctl > ~/.config/floatctl/completion.zsh
source ~/.config/floatctl/completion.zsh
```

### Import Errors
```bash
# Check file location: src/floatctl/plugins/
# Check import path matches file structure
# Install missing dependencies: uv add package_name
```

## 📚 Key Collections (Chroma)

### High-Value Collections
| Collection | Description | Use Case |
|------------|-------------|----------|
| `active_context_stream` | Working memory, temporal | Recent context, daily work |
| `float_bridges` | Synthesis documents | Knowledge connections |
| `float_highlights` | Key insights | Important moments |
| `conversation_highlights` | Curated conversations | Best conversations |

### Query Tips
- Use `n_results=2-3` for focused results
- Include `--rendered` for markdown formatting
- Single semantic queries work better than multiple broad searches
- Filter by metadata when possible

## 🔄 Daily Workflows

### Morning Routine
```bash
# Context restoration
floatctl chroma recent active_context_stream --limit 5

# Pattern analysis
floatctl patterns analyze --collection active_context_stream

# Daily planning
floatctl daily-review plan
```

### Evening Reflection
```bash
# Highlights capture
floatctl chroma floatql "highlights from today"

# Bridge walking
python bridge_walkers/run_bridge_walkers.py --single --persona evna

# Timeline review
floatctl archaeology timeline --days 1
```

---

**💡 Pro Tips:**
- Bookmark this page for quick command lookup
- Use `floatctl COMMAND --help` for detailed options
- Plugin-specific help: `floatctl PLUGIN --help`
- Check `docs/DOCUMENTATION_INDEX.md` for complete guides

**🔗 Quick Links:**
- [Getting Started](GETTING_STARTED.md) - 10-minute setup
- [Complete User Guide](README.md) - Full documentation
- [Plugin Development](development/PLUGIN_DEVELOPMENT_GUIDE.md) - Build plugins
- [Troubleshooting](development/PLUGIN_TROUBLESHOOTING.md) - Fix issues