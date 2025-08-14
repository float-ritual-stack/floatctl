# Getting Started with FloatCtl

Welcome to FloatCtl! This guide will get you up and running in 10 minutes with practical examples that demonstrate the power of consciousness technology for AI workflow management.

## 🎯 What You'll Accomplish

By the end of this 10-minute guide, you'll have:
- ✅ A working FloatCtl installation with global access
- ✅ Successfully processed your first conversation export
- ✅ Performed semantic searches on your data using Chroma
- ✅ Created and tested a custom plugin
- ✅ Set up MCP integration with Claude Desktop (optional)

**Time Investment:** 10 minutes for core setup, +5 minutes for MCP integration

## 🚀 Why FloatCtl?

FloatCtl transforms your AI conversations from static exports into a queryable, searchable knowledge base. It's designed around the **"shacks not cathedrals"** philosophy - practical tools that solve real problems without unnecessary complexity.

## 📋 Prerequisites

- Python 3.10 or higher
- Basic familiarity with command-line tools
- (Optional) Claude Desktop for MCP integration

## 🚀 Quick Installation

### Step 1: Install UV Package Manager
```bash
# Install UV (ultra-fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your terminal or source your shell config
source ~/.zshrc  # or ~/.bashrc
```

### Step 2: Clone and Setup FloatCtl
```bash
# Clone the repository
git clone https://github.com/float-ritual-stack/floatctl.git
cd floatctl-py

# Install dependencies (this is fast with UV!)
uv sync

# Verify installation
uv run floatctl --help
```

**✅ Success Check**: You should see the FloatCtl help menu with available commands including `conversations`, `chroma`, and `forest` plugins.

**Expected Output:**
```
Usage: floatctl [OPTIONS] COMMAND [ARGS]...

  FloatCtl - Consciousness Technology Command Line Interface

Commands:
  chroma         Chroma vector database operations
  conversations  Process AI conversation exports
  forest         V0 project management
  ...
```

### Step 3: Global Access Setup (Recommended)
Add this function to your `~/.zshrc` or `~/.bashrc` for global access:

```bash
# FloatCtl global access function
floatctl() {
    (cd /path/to/floatctl-py && uv run floatctl "$@")
}
```

Replace `/path/to/floatctl-py` with your actual path. Reload your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
floatctl --help  # Should work from anywhere now
```

## 🎮 Your First FloatCtl Experience

### Example 1: Process a Conversation Export

Let's start with the most common use case - processing Claude conversation exports.

**Step 1: Get Sample Data**
```bash
# Create a test directory
mkdir ~/floatctl-test && cd ~/floatctl-test

# FloatCtl includes sample data for testing
# Replace /path/to/floatctl-py with your actual path
cp /path/to/floatctl-py/test_data/conversation_with_attachments.json ./sample.json

# Verify the file exists and has content
ls -la sample.json
# Should show a file with size > 0 bytes
```

**Step 2: Split Conversations**
```bash
# Basic split - creates individual files
floatctl conversations split sample.json

# Check the output
ls -la output/conversations/
```

**Step 3: Advanced Processing**
```bash
# Export as markdown with pattern extraction
floatctl conversations split sample.json --format markdown

# Organize by date
floatctl conversations split sample.json --by-date --format both
```

**✅ Success Check**: You should see organized output files:
```bash
ls -la output/conversations/
# Expected files:
# 2025-08-04 - Test Conversation with Attachments.md
# 2025-08-04 - Test Conversation with Attachments.json
# 2025-08-04 - Test Conversation with Attachments.tool_calls.jsonl
```

**Validation Steps:**
```bash
# Check markdown file has YAML frontmatter
head -20 output/conversations/*.md
# Should show YAML header with conversation metadata

# Verify tool calls were extracted
wc -l output/conversations/*.tool_calls.jsonl
# Should show number of tool calls extracted
```

### Example 2: Semantic Search with Chroma

FloatCtl includes powerful vector database integration for semantic search.

**Step 1: List Available Collections**
```bash
# See what Chroma collections are available
floatctl chroma list

# Expected output (your collections may vary):
# active_context_stream (1,234 documents)
# float_bridges (56 documents)  
# float_highlights (789 documents)
# conversation_highlights (234 documents)
```

**✅ Success Check**: You should see a list of collections with document counts. If you see "No collections found", that's normal for a fresh installation.

**Step 2: Natural Language Queries**
```bash
# Search for context markers
floatctl chroma floatql "ctx:: meeting with nick"

# Find highlights from yesterday
floatctl chroma floatql "highlights from yesterday"

# Search for specific bridge IDs
floatctl chroma floatql "bridge::CB-20250713"
```

**Step 3: Collection Exploration**
```bash
# Peek at collection contents
floatctl chroma peek active_context_stream --limit 5

# Get detailed collection info
floatctl chroma info float_bridges

# Recent documents
floatctl chroma recent float_highlights --limit 10
```

### Example 3: Interactive Note-Taking

FloatCtl provides multiple interfaces for capturing thoughts and context.

**Step 1: Try the REPL Mode**
```bash
# Launch the fast, low-friction REPL
floatctl repl
```

In the REPL, try:
```
/ ctx:: learning floatctl basics
/ todo:: explore chroma integration
/ highlight:: this tool is powerful for consciousness archaeology
```

Press `Ctrl+C` to exit.

**Step 2: Try the Visual Interface**
```bash
# Launch the rich Textual interface
floatctl float-simple
```

Use `Tab`/`Shift+Tab` to indent, `Enter` to add entries.

## 🔌 Plugin Development Quick Start

Let's create your first plugin in 5 minutes.

**Step 1: Generate Plugin Scaffold**
```bash
# Generate a working plugin automatically
floatctl dev scaffold hello_world --output-dir ./my-plugins

# Check what was created
ls -la my-plugins/hello_world/
```

**Step 2: Install Your Plugin**
```bash
# The scaffold tool shows you exactly what to add to pyproject.toml
# Add this to the [project.entry-points."floatctl.plugins"] section:
# hello_world = "my_plugins.hello_world.plugin:HelloWorldPlugin"

# After adding the entry point, test your plugin
floatctl hello-world --help
floatctl hello-world greet --name "Developer"
```

**✅ Success Check**: You should see:
```
Usage: floatctl hello-world [OPTIONS] COMMAND [ARGS]...

Commands:
  greet  Greet someone
```

And running the greet command should output: `Hello, Developer!`

**Step 3: Customize Your Plugin**
Edit the generated plugin file and add your own commands. The scaffold includes:
- ✅ Proper `register_commands()` structure
- ✅ Rich CLI output examples
- ✅ Database integration patterns
- ✅ Error handling
- ✅ Tests and documentation

## 🤖 MCP Server Integration

Connect FloatCtl to Claude Desktop for seamless context management.

**Step 1: Install MCP Server**
```bash
# Install to Claude Desktop
floatctl mcp install --claude-desktop

# Restart Claude Desktop
```

**Step 2: Test Integration**
In Claude Desktop, try typing:
```
ctx::2025-08-06 - Learning FloatCtl - [project:: consciousness-tech]
```

**✅ Success Check**: Claude should respond acknowledging the context capture, something like:
> "I've captured that context marker to your active context stream. You're working on consciousness-tech project and learning FloatCtl."

**Step 3: Query Your Context**
```bash
# See recent context
floatctl chroma recent active_context_stream --limit 5
```

**✅ Success Check**: You should see your context marker in the results:
```
Recent documents from active_context_stream:
1. ctx::2025-08-06 - Learning FloatCtl - [project:: consciousness-tech]
   Timestamp: 2025-08-06T10:30:00Z
   TTL: 36 hours
```

## 🎯 Next Steps

Now that you have FloatCtl running, explore these areas:

### Immediate Next Actions
1. **Process Your Own Data**: Export conversations from Claude and process them
2. **Explore Collections**: Use `floatctl chroma list` to see available data
3. **Try Different Plugins**: Each plugin has its own `CLAUDE.md` with specific guidance

### Learning Path
1. **[User Guide](README.md)** - Complete feature documentation
2. **[Plugin Development](development/PLUGIN_DEVELOPMENT_GUIDE.md)** - Build custom plugins
3. **[Middleware Tutorial](guides/MIDDLEWARE_TUTORIAL.md)** - Advanced data processing
4. **[Troubleshooting](development/PLUGIN_TROUBLESHOOTING.md)** - Common issues and solutions

### Advanced Features to Explore
- **Bridge Walking**: Consciousness archaeology with `bridge_walkers/`
- **Forest Plugin**: V0 project management
- **Workflow Intelligence**: Memory prosthetic for daily questions
- **Consciousness Middleware**: Pattern recognition and contamination analysis

## 🆘 Getting Help

### Quick Diagnostics
```bash
# Check plugin registration
floatctl --help | grep your-plugin

# Test completion
_FLOATCTL_COMPLETE=zsh_source floatctl

# Validate plugin structure
floatctl dev validate /path/to/your/plugin
```

### Common Issues
- **Commands not showing**: Check that all commands are inside `register_commands()` method
- **Plugin not loading**: Verify entry point in `pyproject.toml`
- **Import errors**: Check file paths and dependencies

### Resources
- **[Troubleshooting Guide](development/PLUGIN_TROUBLESHOOTING.md)**
- **[Development Guide](development/AGENTS.md)**
- **[GitHub Issues](https://github.com/float-ritual-stack/floatctl/issues)**

---

**🎉 Congratulations!** You now have a working FloatCtl installation and understand the core concepts. The tool is designed around the "shacks not cathedrals" philosophy - each plugin is a focused tool that does one thing well.

Ready to dive deeper? Check out the [Complete User Guide](README.md) for comprehensive documentation of all features.