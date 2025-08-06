# FloatCtl Troubleshooting Guide

Comprehensive solutions for common issues, error scenarios, and debugging techniques.

## Table of Contents

1. [Quick Diagnostic Commands](#quick-diagnostic-commands)
2. [Installation Issues](#installation-issues)
3. [Plugin Problems](#plugin-problems)
4. [Chroma Database Issues](#chroma-database-issues)
5. [Performance Problems](#performance-problems)
6. [MCP Server Issues](#mcp-server-issues)
7. [Configuration Problems](#configuration-problems)
8. [Error Reference](#error-reference)
9. [Advanced Debugging](#advanced-debugging)

---

## Quick Diagnostic Commands

**Run these first to identify the problem area:**

```bash
# 1. Check FloatCtl installation
floatctl --version
floatctl --help

# 2. Check plugin registration (should see 3+ plugins)
floatctl --help | grep -E "(conversations|chroma|forest)"

# 3. Test basic functionality
floatctl conversations --help
floatctl chroma list

# 4. Check completion system
_FLOATCTL_COMPLETE=zsh_source floatctl 2>&1 | head -10

# 5. Verify Python environment
python --version
which python
uv --version
```

**🚨 Red Flags to Look For:**
- `floatctl: command not found` → Installation issue
- No plugins listed in help → Plugin registration problem  
- `ImportError` or `ModuleNotFoundError` → Dependency issue
- Commands hang or timeout → Performance/connection issue

**System Health Check Script:**
```bash
#!/bin/bash
# save as ~/bin/floatctl-health-check.sh

echo "=== FloatCtl Health Check ==="

echo "1. FloatCtl Installation:"
if command -v floatctl &> /dev/null; then
    echo "✅ FloatCtl command available"
    floatctl --version
else
    echo "❌ FloatCtl command not found"
fi

echo -e "\n2. Plugin Registration:"
plugin_count=$(floatctl --help 2>/dev/null | grep -c "Commands:")
if [ "$plugin_count" -gt 0 ]; then
    echo "✅ Plugins registered: $plugin_count"
else
    echo "❌ No plugins found"
fi

echo -e "\n3. Core Plugins:"
for plugin in conversations chroma forest; do
    if floatctl --help 2>/dev/null | grep -q "$plugin"; then
        echo "✅ $plugin plugin available"
    else
        echo "❌ $plugin plugin missing"
    fi
done

echo -e "\n4. Python Environment:"
echo "Python: $(python --version 2>&1)"
echo "UV: $(uv --version 2>&1)"

echo -e "\n5. Configuration:"
if [ -f ~/.config/floatctl/config.json ]; then
    echo "✅ User config found"
else
    echo "ℹ️  No user config (using defaults)"
fi

echo -e "\n=== Health Check Complete ==="
```

---

## Installation Issues

### Issue: "floatctl: command not found"

**Symptoms:**
```bash
$ floatctl --help
bash: floatctl: command not found
```

**Solutions:**

**Option 1: Global Function (Recommended for Development)**
```bash
# Add to ~/.zshrc or ~/.bashrc
floatctl() {
    (cd /path/to/floatctl-py && uv run floatctl "$@")
}

# Reload shell
source ~/.zshrc  # or ~/.bashrc

# Test
floatctl --help
```

**Option 2: Install in Development Mode**
```bash
cd /path/to/floatctl-py
uv pip install -e .

# Test
floatctl --help
```

**Option 3: Use UV Run Directly**
```bash
cd /path/to/floatctl-py
uv run floatctl --help
```

### Issue: "UV not found" or Installation Fails

**Symptoms:**
```bash
$ uv sync
bash: uv: command not found
```

**Solutions:**

**Install UV:**
```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal or source shell config
source ~/.zshrc  # or ~/.bashrc

# Verify installation
uv --version
```

**Alternative Installation Methods:**
```bash
# Using pip
pip install uv

# Using homebrew (macOS)
brew install uv

# Using conda
conda install -c conda-forge uv
```

### Issue: Python Version Compatibility

**Symptoms:**
```
ERROR: Python 3.9 is not supported. Requires Python 3.10+
```

**Solutions:**

**Check Python Version:**
```bash
python --version
python3 --version
```

**Install Python 3.10+ (macOS with Homebrew):**
```bash
brew install python@3.11
# Update PATH in ~/.zshrc
export PATH="/opt/homebrew/bin:$PATH"
```

**Install Python 3.10+ (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

**Use pyenv for Version Management:**
```bash
# Install pyenv
curl https://pyenv.run | bash

# Install Python 3.11
pyenv install 3.11.0
pyenv global 3.11.0
```

---

## Plugin Problems

### Issue: Plugin Not Showing in Help

**Symptoms:**
```bash
$ floatctl --help
# Your plugin is missing from the list
# OR you see fewer plugins than expected
```

**Quick Fix Checklist:**
```bash
# 1. Check if entry point exists in pyproject.toml
grep -A 5 "floatctl.plugins" pyproject.toml

# 2. Verify plugin file exists and has correct class name
ls -la src/floatctl/plugins/your_plugin.py
grep "class.*Plugin" src/floatctl/plugins/your_plugin.py

# 3. Test plugin import directly
python -c "from floatctl.plugins.your_plugin import YourPlugin; print('✅ Import OK')"

# 4. Reinstall in development mode
uv pip install -e .
```

**Diagnostic Steps:**
```bash
# 1. Check entry point registration
grep -A 10 "floatctl.plugins" pyproject.toml

# 2. Verify plugin file exists
ls -la src/floatctl/plugins/your_plugin.py

# 3. Test plugin import
python -c "from floatctl.plugins.your_plugin import YourPlugin; print('Import successful')"

# 4. Check entry points are installed
python -c "import pkg_resources; print([ep.name for ep in pkg_resources.iter_entry_points('floatctl.plugins')])"
```

**Common Causes & Solutions:**

**1. Missing Entry Point in pyproject.toml**
```toml
# Add this section to pyproject.toml
[project.entry-points."floatctl.plugins"]
your_plugin = "floatctl.plugins.your_plugin:YourPlugin"
```

**2. Wrong Import Path**
```bash
# File location: src/floatctl/plugins/your_plugin.py
# Entry point should be: "floatctl.plugins.your_plugin:YourPlugin"
# Class name must match exactly
```

**3. Plugin Class Doesn't Inherit from PluginBase**
```python
# ❌ Wrong
class YourPlugin:
    pass

# ✅ Correct
from floatctl.plugin_manager import PluginBase

class YourPlugin(PluginBase):
    name = "your_plugin"
    description = "Your plugin description"
    version = "1.0.0"
```

**4. Syntax Errors in Plugin File**
```bash
# Check for syntax errors
python -m py_compile src/floatctl/plugins/your_plugin.py
```

### Issue: Plugin Commands Not Showing

**Symptoms:**
```bash
$ floatctl your-plugin --help
Usage: floatctl your-plugin [OPTIONS]
# No subcommands listed
```

**🚨 Most Common Cause: Commands Outside register_commands() Method**

**❌ Wrong Structure:**
```python
class YourPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def your_plugin(ctx: click.Context) -> None:
            pass
        
        @your_plugin.command()
        def first_command(ctx: click.Context) -> None:
            pass
    
    # ❌ This command is OUTSIDE register_commands() - won't work!
    @your_plugin.command()
    def broken_command(ctx: click.Context) -> None:
        pass
```

**✅ Correct Structure:**
```python
class YourPlugin(PluginBase):
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        def your_plugin(ctx: click.Context) -> None:
            pass
        
        @your_plugin.command()
        def first_command(ctx: click.Context) -> None:
            pass
        
        # ✅ ALL commands must be inside register_commands()
        @your_plugin.command()
        def second_command(ctx: click.Context) -> None:
            pass
```

**Other Causes:**

**1. Indentation Errors**
```python
# Check that all commands are properly indented inside register_commands()
def register_commands(self, cli_group: click.Group) -> None:
    @cli_group.group()
    def your_plugin(ctx: click.Context) -> None:
        pass
    
    # These must be indented at the same level as the @cli_group.group()
    @your_plugin.command()
    def command1(ctx: click.Context) -> None:
        pass
```

**2. Missing @click.pass_context Decorator**
```python
# ❌ Missing context
@your_plugin.command()
def command(verbose: bool) -> None:
    pass

# ✅ With context
@your_plugin.command()
@click.pass_context
def command(ctx: click.Context, verbose: bool) -> None:
    pass
```

### Issue: Plugin Import Errors

**Symptoms:**
```
ImportError: cannot import name 'YourPlugin' from 'floatctl.plugins.your_plugin'
ModuleNotFoundError: No module named 'floatctl.plugins.your_plugin'
```

**Solutions:**

**1. Check File Structure**
```bash
# Correct structure
src/floatctl/plugins/
├── __init__.py
├── your_plugin.py          # Your plugin file
└── your_plugin/            # Or directory structure
    ├── __init__.py
    └── plugin.py
```

**2. Verify Class Name Matches Entry Point**
```python
# In your_plugin.py
class YourPlugin(PluginBase):  # Class name must match entry point
    pass

# In pyproject.toml
your_plugin = "floatctl.plugins.your_plugin:YourPlugin"
#                                            ^^^^^^^^^^^
#                                            Must match class name
```

**3. Check __init__.py Files**
```python
# src/floatctl/plugins/__init__.py should exist (can be empty)
# If using directory structure, your_plugin/__init__.py should exist
```

---

## Chroma Database Issues

### Issue: "Collection not found" or Chroma Connection Errors

**Symptoms:**
```bash
$ floatctl chroma list
Error: Could not connect to Chroma database
```

**Diagnostic Steps:**
```bash
# 1. Check if Chroma is running
ps aux | grep chroma

# 2. Test Chroma connection
python -c "import chromadb; client = chromadb.Client(); print('Chroma OK')"

# 3. Check Chroma configuration
floatctl chroma info --help
```

**Solutions:**

**1. Start Chroma Server (if using server mode)**
```bash
# Install Chroma if not installed
pip install chromadb

# Start Chroma server
chroma run --host localhost --port 8000
```

**2. Use Persistent Client (recommended)**
```python
# FloatCtl uses persistent client by default
# Check configuration in ~/.config/floatctl/config.json
{
  "chroma": {
    "persist_directory": "~/.floatctl/chroma_db"
  }
}
```

**3. Reset Chroma Database**
```bash
# ⚠️ This will delete all data!
rm -rf ~/.floatctl/chroma_db
floatctl chroma list  # Will recreate database
```

### Issue: FloatQL Queries Not Working

**Symptoms:**
```bash
$ floatctl chroma floatql "ctx:: meeting"
No results found
```

**Solutions:**

**1. Check Collection Contents**
```bash
# List all collections
floatctl chroma list

# Check if collection has data
floatctl chroma info active_context_stream
floatctl chroma peek active_context_stream --limit 5
```

**2. Try Different Query Patterns**
```bash
# Simple text search
floatctl chroma query active_context_stream --query "meeting"

# Check for specific patterns
floatctl chroma query active_context_stream --query "ctx"
```

**3. Verify Collection Routing**
```bash
# FloatQL automatically routes to collections
# Try specifying collection explicitly
floatctl chroma query active_context_stream --query "ctx:: meeting"
```

---

## Performance Problems

### Issue: Slow Conversation Processing

**Symptoms:**
- Processing large conversation files takes very long
- Memory usage spikes during processing
- System becomes unresponsive

**Solutions:**

**1. Process in Batches**
```bash
# Filter by date to reduce size
floatctl conversations split large_file.json --filter-after 2025-08-01

# Process specific date ranges
floatctl conversations split large_file.json --filter-after 2025-07-01 --filter-before 2025-08-01
```

**2. Use Streaming Processing**
```bash
# Process without loading entire file into memory
floatctl conversations split large_file.json --stream
```

**3. Optimize Output Format**
```bash
# JSON is faster than markdown
floatctl conversations split large_file.json --format json

# Skip pattern extraction if not needed
floatctl conversations split large_file.json --no-patterns
```

**4. Monitor Resource Usage**
```bash
# Monitor memory usage
top -p $(pgrep -f floatctl)

# Check disk space
df -h
```

### Issue: Chroma Queries Are Slow

**Symptoms:**
- FloatQL queries take a long time
- Chroma operations timeout

**Solutions:**

**1. Limit Query Results**
```bash
# Use smaller result sets
floatctl chroma floatql "ctx:: meeting" --limit 5

# Instead of large queries
floatctl chroma query collection --query "broad search" --limit 100
```

**2. Optimize Collection Size**
```bash
# Check collection sizes
floatctl chroma list

# Consider archiving old data
floatctl chroma archive --collection old_collection --older-than 30d
```

**3. Use Specific Collections**
```bash
# Target specific collections instead of broad searches
floatctl chroma query active_context_stream --query "recent work"
# Instead of searching all collections
```

---

## MCP Server Issues

### Issue: MCP Server Not Working with Claude Desktop

**Symptoms:**
- Context markers not being captured
- Claude Desktop doesn't recognize MCP tools

**Diagnostic Steps:**
```bash
# 1. Check MCP server installation
floatctl mcp --help

# 2. Test server standalone
floatctl mcp serve

# 3. Check Claude Desktop configuration
cat ~/.claude_desktop_config.json
```

**Solutions:**

**1. Reinstall MCP Server**
```bash
# Uninstall and reinstall
floatctl mcp uninstall --claude-desktop
floatctl mcp install --claude-desktop

# Restart Claude Desktop completely
```

**2. Check Configuration File**
```json
// ~/.claude_desktop_config.json should contain:
{
  "mcpServers": {
    "evna-context-concierge": {
      "command": "floatctl",
      "args": ["mcp", "serve"]
    }
  }
}
```

**3. Test MCP Server Manually**
```bash
# Run server in debug mode
floatctl mcp serve --debug

# Check logs
tail -f ~/.floatctl/logs/mcp_server.log
```

### Issue: Context Markers Not Being Captured

**Symptoms:**
```
ctx::2025-08-06 - Working on docs
# Nothing happens in Claude Desktop
```

**Solutions:**

**1. Check Marker Format**
```bash
# Supported formats:
ctx::2025-08-06 - Working on docs
ctx:: 2025-08-06 @ 10:30 AM - Meeting notes
ctx::2025-08-06 - 10:30 - [project:: floatctl]
```

**2. Verify MCP Server is Running**
```bash
# Check if server is responding
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "ping"}'
```

**3. Check Chroma Connection**
```bash
# Verify context is being stored
floatctl chroma recent active_context_stream --limit 5
```

---

## Configuration Problems

### Issue: Configuration Not Loading

**Symptoms:**
- Custom settings not being applied
- Default values used instead of config

**Diagnostic Steps:**
```bash
# 1. Check config file locations
ls -la ~/.config/floatctl/config.json
ls -la ./floatctl.config.json

# 2. Validate JSON syntax
python -m json.tool ~/.config/floatctl/config.json

# 3. Check environment variable
echo $FLOATCTL_CONFIG
```

**Solutions:**

**1. Create Valid Configuration**
```json
// ~/.config/floatctl/config.json
{
  "db_path": "~/.floatctl/floatctl.db",
  "output_dir": "./output",
  "log_level": "INFO",
  "plugins": {
    "chroma": {
      "persist_directory": "~/.floatctl/chroma_db"
    },
    "conversations": {
      "default_format": "markdown"
    }
  }
}
```

**2. Fix JSON Syntax Errors**
```bash
# Validate JSON
python -c "import json; json.load(open('~/.config/floatctl/config.json'))"

# Common issues:
# - Trailing commas
# - Missing quotes around keys
# - Incorrect nesting
```

**3. Check File Permissions**
```bash
# Ensure config file is readable
chmod 644 ~/.config/floatctl/config.json
```

---

## Error Reference

### Common Error Messages and Solutions

#### `PluginError: Plugin 'your_plugin' failed to load`

**Cause:** Plugin has syntax errors or missing dependencies

**Solution:**
```bash
# Check plugin syntax
python -m py_compile src/floatctl/plugins/your_plugin.py

# Check imports
python -c "from floatctl.plugins.your_plugin import YourPlugin"

# Install missing dependencies
uv add missing_package
```

#### `ConfigurationError: Invalid configuration`

**Cause:** Configuration file has invalid values or structure

**Solution:**
```bash
# Validate configuration
python -c "from floatctl.core.config import load_config; load_config()"

# Check specific values
python -c "import json; print(json.load(open('~/.config/floatctl/config.json')))"
```

#### `DatabaseError: Cannot connect to database`

**Cause:** Database file is corrupted or permissions issue

**Solution:**
```bash
# Check database file
ls -la ~/.floatctl/floatctl.db

# Reset database (⚠️ loses data)
rm ~/.floatctl/floatctl.db
floatctl conversations --help  # Recreates database

# Check permissions
chmod 644 ~/.floatctl/floatctl.db
```

#### `ChromaError: Collection does not exist`

**Cause:** Trying to access non-existent Chroma collection

**Solution:**
```bash
# List available collections
floatctl chroma list

# Create collection if needed
floatctl chroma create-collection your_collection

# Use existing collection
floatctl chroma query active_context_stream --query "your search"
```

---

## Advanced Debugging

### Enable Debug Logging

**1. Environment Variable**
```bash
export FLOATCTL_LOG_LEVEL=DEBUG
floatctl your-command
```

**2. Configuration File**
```json
{
  "log_level": "DEBUG",
  "log_file": "~/.floatctl/debug.log"
}
```

**3. Command Line**
```bash
floatctl --verbose your-command
```

### Debug Plugin Loading

**1. Plugin Discovery**
```python
# Debug script: debug_plugins.py
from floatctl.plugin_manager import PluginManager

manager = PluginManager()
plugins = manager.discover_plugins()

print("Discovered plugins:")
for name, info in plugins.items():
    print(f"  {name}: {info.entry_point}")
    print(f"    State: {info.state}")
    if info.error:
        print(f"    Error: {info.error}")
```

**2. Command Registration**
```python
# Debug command registration
import rich_click as click
from floatctl.plugin_manager import PluginManager

@click.group()
def cli():
    pass

manager = PluginManager()
manager.load_plugins(cli)

# Print all registered commands
def print_commands(group, indent=0):
    for name, command in group.commands.items():
        print("  " * indent + f"- {name}")
        if isinstance(command, click.Group):
            print_commands(command, indent + 1)

print_commands(cli)
```

### Memory and Performance Profiling

**1. Memory Usage**
```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
mprof run floatctl conversations split large_file.json
mprof plot
```

**2. Performance Profiling**
```bash
# Install profiling tools
pip install py-spy

# Profile running process
py-spy top --pid $(pgrep -f floatctl)

# Generate flame graph
py-spy record -o profile.svg -- floatctl your-command
```

### Network and Database Debugging

**1. Chroma Connection**
```python
# Test Chroma connection
import chromadb
from chromadb.config import Settings

# Test different connection methods
try:
    client = chromadb.Client()
    print("In-memory client: OK")
except Exception as e:
    print(f"In-memory client failed: {e}")

try:
    client = chromadb.PersistentClient(path="~/.floatctl/chroma_db")
    print("Persistent client: OK")
except Exception as e:
    print(f"Persistent client failed: {e}")
```

**2. Database Inspection**
```bash
# Install SQLite tools
sudo apt install sqlite3  # Ubuntu/Debian
brew install sqlite3      # macOS

# Inspect database
sqlite3 ~/.floatctl/floatctl.db
.tables
.schema file_runs
SELECT * FROM file_runs LIMIT 5;
```

---

## Common Scenarios & Solutions

### "I just want to process my Claude conversations"

**Quick Solution:**
```bash
# 1. Export conversations from Claude (JSON format)
# 2. Process them:
floatctl conversations split my_conversations.json --format both

# 3. Check output:
ls -la output/conversations/
```

**If this fails:**
- Check file exists: `ls -la my_conversations.json`
- Verify JSON format: `head -20 my_conversations.json`
- Try with sample data first: `floatctl conversations split test_data/conversation_with_attachments.json`

### "My plugin commands aren't showing up"

**Most Common Cause:** Commands defined outside `register_commands()` method

**Quick Fix:**
```python
# ❌ Wrong - command outside method
class MyPlugin(PluginBase):
    def register_commands(self, cli_group):
        @cli_group.group()
        def myplugin(ctx): pass
    
    @myplugin.command()  # ❌ This won't work!
    def broken_cmd(ctx): pass

# ✅ Correct - all commands inside method  
class MyPlugin(PluginBase):
    def register_commands(self, cli_group):
        @cli_group.group()
        def myplugin(ctx): pass
        
        @myplugin.command()  # ✅ This works!
        def working_cmd(ctx): pass
```

### "Chroma queries return no results"

**Diagnostic Steps:**
```bash
# 1. Check if collections exist
floatctl chroma list

# 2. Check collection contents
floatctl chroma peek active_context_stream --limit 3

# 3. Try simple text search instead of FloatQL
floatctl chroma query active_context_stream --query "meeting"

# 4. Check for typos in collection names
floatctl chroma info active_context_stream  # not "active_context_streams"
```

### "Installation works but commands are slow"

**Performance Optimization:**
```bash
# 1. Use smaller result limits
floatctl chroma floatql "your query" --limit 3

# 2. Target specific collections
floatctl chroma query active_context_stream --query "text" --limit 5

# 3. Check collection sizes
floatctl chroma list  # Look for very large collections

# 4. Filter by date if possible
floatctl conversations split large_file.json --filter-after 2025-08-01
```

### "MCP integration not working with Claude Desktop"

**Step-by-Step Fix:**
```bash
# 1. Reinstall MCP server
floatctl mcp uninstall --claude-desktop
floatctl mcp install --claude-desktop

# 2. Restart Claude Desktop completely (quit and reopen)

# 3. Test with simple context marker in Claude:
# ctx::2025-08-06 - Testing MCP integration

# 4. Verify capture worked:
floatctl chroma recent active_context_stream --limit 3
```

---

## Getting Additional Help

### Community Resources
- **GitHub Issues**: [Report bugs and request features](https://github.com/float-ritual-stack/floatctl/issues)
- **Discussions**: [Community discussions and Q&A](https://github.com/float-ritual-stack/floatctl/discussions)

### Documentation
- **[Getting Started Guide](GETTING_STARTED.md)** - Basic setup and usage
- **[Plugin Development Guide](development/PLUGIN_DEVELOPMENT_GUIDE.md)** - Plugin creation
- **[API Reference](API_REFERENCE.md)** - Complete API documentation

### Creating Bug Reports

**Include this information:**
```bash
# System information
uv --version
python --version
floatctl --version

# Plugin status
floatctl --help | grep -E "(conversations|chroma|forest)"

# Error reproduction
floatctl your-failing-command --verbose

# Configuration (remove sensitive data)
cat ~/.config/floatctl/config.json
```

**Template:**
```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Run command: `floatctl ...`
2. Expected: ...
3. Actual: ...

## Environment
- OS: macOS/Linux/Windows
- Python: 3.x.x
- UV: x.x.x
- FloatCtl: x.x.x

## Error Output
```
Paste error output here
```

## Additional Context
Any other relevant information
```

---

This troubleshooting guide covers the most common issues and their solutions. For issues not covered here, please check the [GitHub Issues](https://github.com/float-ritual-stack/floatctl/issues) or create a new issue with detailed information about your problem.