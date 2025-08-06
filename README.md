# FloatCtl - Consciousness Technology Command Line Interface

> **"Shacks not cathedrals"** - Practical consciousness archaeology tools for the FLOAT ecosystem

FloatCtl is a plugin-based CLI tool for processing AI conversation exports, consciousness archaeology, and bridge walking through semantic memory networks.

## Quick Start

```bash
# Install dependencies
uv sync

# Run floatctl
uv run floatctl --help

# Process conversations
floatctl conversations split input.json --output-dir ./processed

# Bridge walking
cd bridge_walkers && python run_bridge_walkers.py --single --persona archaeologist
```

## Documentation

- **[Complete Documentation](docs/README.md)** - Full user guide and API reference
- **[Development Guide](docs/development/AGENTS.md)** - Build commands, coding standards, plugin development
- **[Plugin Development](docs/development/PLUGIN_DEVELOPMENT_GUIDE.md)** - Create new plugins
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