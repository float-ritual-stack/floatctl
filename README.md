# FloatCtl - Consciousness Technology Command Line Interface

> **"Shacks not cathedrals"** - Practical consciousness archaeology tools for the FLOAT ecosystem

FloatCtl is a plugin-based CLI tool for processing AI conversation exports, consciousness archaeology, and bridge walking through semantic memory networks.

## 🎉 New in v0.6.0: Multi-Pattern Extraction Fixed!

**Major Bug Fix**: FloatCtl now captures **ALL patterns** in multi-pattern lines, not just the first one! This fixes a critical consciousness technology failure that was breaking pattern extraction.

- **Before**: `"eureka:: Found! decision:: Fix tomorrow"` → Only captured 'eureka' ❌
- **After**: `"eureka:: Found! decision:: Fix tomorrow"` → Captures both patterns ✅
- **Performance**: **3x improvement** in pattern capture rate
- **Technology**: Hybrid LangExtract/regex with automatic fallback

[See CHANGELOG](CHANGELOG.md) for full details.

## 🚀 Quick Start

**New to FloatCtl?** Get up and running in 10 minutes:

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/evanschultz/floatctl-py.git
cd floatctl-py && uv sync

# Your first command
uv run floatctl --help
```

**👉 [Complete Getting Started Guide](docs/GETTING_STARTED.md)** - Step-by-step tutorial with examples and success validation

## 🎯 What FloatCtl Does

FloatCtl transforms your AI conversations from static exports into a **queryable, searchable knowledge base**:

- **📁 Process Conversations**: Split Claude exports into organized, searchable files
- **🔍 Semantic Search**: Find insights using natural language queries  
- **🧠 Context Management**: Automatic capture and restoration of conversation context
- **🔌 Extensible**: Plugin architecture for custom workflows
- **🤖 MCP Integration**: Seamless Claude Desktop integration

## 📚 Documentation

### 🌱 New User Path
1. **[Getting Started Guide](docs/GETTING_STARTED.md)** - 10-minute setup with validation steps
2. **[Quick Reference](docs/QUICK_REFERENCE.md)** - Essential commands cheat sheet  
3. **[Complete User Guide](docs/README.md)** - Full feature documentation

### 🔧 Developer Path  
1. **[Plugin Development Guide](docs/development/PLUGIN_DEVELOPMENT_GUIDE.md)** - Create custom plugins
2. **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation with examples
3. **[Development Guide](docs/development/AGENTS.md)** - Build commands, coding standards

### 🆘 Support & Reference
- **[Troubleshooting Guide](docs/TROUBLESHOOTING_GUIDE.md)** - Common issues with step-by-step solutions
- **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Complete documentation map
- **[Workflow Tutorials](docs/tutorials/WORKFLOW_TUTORIALS.md)** - Advanced workflow guides
- **[Changelog](docs/CHANGELOG.md)** - Version history and recent changes

## Key Features

- **🔌 Plugin Architecture** - Extensible command system
- **🧠 Consciousness Middleware** - Pattern recognition and contamination analysis  
- **🌉 Bridge Walking** - Organic exploration of semantic networks
- **📊 Workflow Intelligence** - Memory prosthetic for daily questions
- **🎯 FloatQL** - Query language for consciousness collections
- **🔍 Smart Export** - Conversation processing with pattern extraction

## Project Structure

```
floatctl-py/
├── docs/                    # All documentation
├── bridge_walkers/          # Bridge walking consciousness archaeology
├── scripts/                 # Utility scripts
├── examples/                # Example files and integrations
├── src/floatctl/           # Core source code
│   ├── core/               # Core functionality
│   ├── plugins/            # Plugin implementations
│   └── testing/            # Test utilities
└── tests/                  # Test suite
```

## Philosophy

FloatCtl embodies the **"shacks not cathedrals"** philosophy - building practical, focused tools that solve real problems rather than grand architectures. Each plugin is a small, purpose-built shack that does one thing well.

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*Part of the FLOAT ecosystem for consciousness technology and digital sovereignty.*