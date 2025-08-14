# FloatCtl Documentation Index

Your complete guide to FloatCtl - from first installation to advanced plugin development.

## 🚀 Getting Started

**New to FloatCtl?** Follow this proven path for success:

### Step-by-Step Onboarding
| Step | Document | Description | Time | Success Criteria |
|------|----------|-------------|------|------------------|
| **1** | **[Getting Started Guide](GETTING_STARTED.md)** | 10-minute setup with validation steps | 10 min | ✅ Process first conversation, run semantic search |
| **2** | **[Quick Reference](QUICK_REFERENCE.md)** | Essential commands cheat sheet | 5 min | ✅ Bookmark for daily use |
| **3** | **[Complete User Guide](README.md)** | Full feature exploration | 30 min | ✅ Understand all core features |

### Quick Access
| Document | Description | When to Use |
|----------|-------------|-------------|
| **[Installation Troubleshooting](GETTING_STARTED.md#getting-help)** | Setup issues and solutions | Installation problems |
| **[Command Examples](QUICK_REFERENCE.md)** | Copy-paste commands | Daily workflow |

## 📚 User Documentation

**Using FloatCtl effectively** for AI workflow management.

### Core Features
| Document | Description | Audience |
|----------|-------------|----------|
| **[Complete User Guide](README.md)** | Comprehensive feature documentation | Users |
| **[Conversation Processing](README.md#basic-conversation-splitting)** | Split and analyze AI conversations | Users |
| **[Chroma Integration](README.md#chroma-vector-database-integration)** | Vector database and semantic search | Users |
| **[Interactive Notes](README.md#interactive-notes--repl)** | REPL and visual note-taking interfaces | Users |
| **[MCP Server Setup](guides/EVNA_MCP_SETUP.md)** | Claude Desktop integration | Users |

### Advanced Features
| Document | Description | Audience |
|----------|-------------|----------|
| **[FloatQL Query Language](README.md#floatql-query-language)** | Natural language queries for consciousness data | Advanced Users |
| **[Bridge Walking](../bridge_walkers/README.md)** | Consciousness archaeology system | Advanced Users |
| **[Workflow Intelligence](README.md#workflow-intelligence-system)** | Memory prosthetic for daily questions | Advanced Users |
| **[Forest Plugin](README.md#forest-plugin---v0-project-management)** | V0 project management | Advanced Users |

## 🔧 Developer Documentation

**Building with and extending FloatCtl** through plugins and middleware.

### Plugin Development Path
| Step | Document | Description | Time | Success Criteria |
|------|----------|-------------|------|------------------|
| **1** | **[Plugin Development Guide](development/PLUGIN_DEVELOPMENT_GUIDE.md)** | Complete plugin creation tutorial | 30 min | ✅ Create and test working plugin |
| **2** | **[API Reference](API_REFERENCE.md)** | Complete API documentation with examples | Reference | ✅ Understand core APIs |
| **3** | **[Middleware Tutorial](guides/MIDDLEWARE_TUTORIAL.md)** | Advanced data processing pipelines | 45 min | ✅ Build custom middleware |

### Developer Support
| Document | Description | When to Use |
|----------|-------------|-------------|
| **[Plugin Troubleshooting](development/PLUGIN_TROUBLESHOOTING.md)** | Common issues with step-by-step solutions | Plugin not working |
| **[Development Guide](development/AGENTS.md)** | Build commands, coding standards | Contributing to core |
| **[Testing Guide](../tests/README.md)** | Test organization and best practices | Writing tests |

### Development Workflow
| Document | Description | Audience |
|----------|-------------|----------|
| **[Development Guide](development/AGENTS.md)** | Build commands, coding standards | Contributors |
| **[Architecture Overview](development/CLAUDE.md#architecture-overview)** | System design and patterns | Contributors |
| **[Testing Guide](../tests/README.md)** | Test organization and guidelines | Contributors |

## 🎯 Specialized Guides

**Domain-specific documentation** for particular use cases.

### Consciousness Technology
| Document | Description | Audience |
|----------|-------------|----------|
| **[Consciousness Middleware](guides/EVNA_MCP_ENHANCED.md)** | Pattern recognition and contamination analysis | Consciousness Tech Users |
| **[Bridge Walker System](../bridge_walkers/SUMMARY.md)** | Organic consciousness archaeology | Consciousness Tech Users |
| **[Ritual Stack Integration](guides/COMPATIBILITY_STRATEGY.md)** | FLOAT ecosystem compatibility | Consciousness Tech Users |

### Technical Integration
| Document | Description | Audience |
|----------|-------------|----------|
| **[MCP Server Development](development/EVNA_MCP_ENHANCED.md)** | Model Context Protocol integration | MCP Developers |
| **[Chroma Database Setup](README.md#chroma-vector-database-integration)** | Vector database configuration | System Administrators |
| **[Shell Completion Setup](README.md#shell-completions)** | Tab completion configuration | Power Users |

## 🔍 Reference Materials

**Quick lookup** for specific information.

### Command References
| Document | Description | Use Case |
|----------|-------------|----------|
| **[CLI Command Reference](README.md#usage)** | All available commands with examples | Quick lookup |
| **[Plugin-Specific Commands](src/floatctl/plugins/*/CLAUDE.md)** | Detailed plugin documentation | Plugin users |
| **[Configuration Reference](API_REFERENCE.md#configuration-system)** | All configuration options | System setup |

### Technical References
| Document | Description | Use Case |
|----------|-------------|----------|
| **[Database Schema](API_REFERENCE.md#database-models)** | SQLite table structures | Database queries |
| **[Error Codes](API_REFERENCE.md#error-handling)** | Common errors and solutions | Troubleshooting |
| **[Changelog](CHANGELOG.md)** | Version history and changes | Version management |

## 🆘 Troubleshooting & Support

**When things go wrong** - diagnostic and support resources.

### Common Issues
| Document | Description | When to Use |
|----------|-------------|-------------|
| **[Plugin Troubleshooting](development/PLUGIN_TROUBLESHOOTING.md)** | Plugin not loading/working | Plugin development issues |
| **[Installation Issues](GETTING_STARTED.md#getting-help)** | Setup and installation problems | Initial setup problems |
| **[Performance Issues](development/AGENTS.md#testing-and-quality)** | Slow performance or memory issues | Performance problems |

### Diagnostic Tools
| Command | Description | Use Case |
|---------|-------------|----------|
| `floatctl --help` | Check plugin registration | Plugin not showing |
| `floatctl dev validate /path/to/plugin` | Validate plugin structure | Plugin development |
| `_FLOATCTL_COMPLETE=zsh_source floatctl` | Test completion | Completion not working |

### Getting Help
- **[GitHub Issues](https://github.com/float-ritual-stack/floatctl/issues)** - Bug reports and feature requests
- **[Development Guide](development/AGENTS.md)** - Contributing guidelines
- **[Plugin Examples](../examples/)** - Working code examples

## 📖 Documentation by Experience Level

### 🌱 Beginner (New to FloatCtl)
1. [Getting Started Guide](GETTING_STARTED.md) - Essential first read
2. [User Guide](README.md) - Core features overview
3. [Quick Reference](QUICK_REFERENCE.md) - Common commands

### 🌿 Intermediate (Regular User)
1. [Advanced Features](README.md#advanced-features) - Power user capabilities
2. [FloatQL Queries](README.md#floatql-query-language) - Semantic search
3. [MCP Integration](guides/EVNA_MCP_SETUP.md) - Claude Desktop setup

### 🌳 Advanced (Plugin Developer)
1. [Plugin Development Guide](development/PLUGIN_DEVELOPMENT_GUIDE.md) - Build plugins
2. [API Reference](API_REFERENCE.md) - Complete API docs
3. [Middleware Tutorial](guides/MIDDLEWARE_TUTORIAL.md) - Advanced patterns

### 🏗️ Expert (Core Contributor)
1. [Architecture Overview](development/CLAUDE.md#architecture-overview) - System design
2. [Development Workflow](development/AGENTS.md) - Contributing guidelines
3. [Testing Strategy](../tests/README.md) - Test organization

## 🔄 Documentation Maintenance

This index is maintained to reflect the current state of FloatCtl documentation. 

**Last Updated:** August 6, 2025  
**Version:** 0.1.0  
**Maintainer:** Development Team

### Contributing to Documentation
- All documentation follows the [Developer Experience Guidelines](development/AGENTS.md#code-style-guidelines)
- New features require corresponding documentation updates
- Plugin developers should create `CLAUDE.md` files in their plugin directories
- Documentation changes should be tested with real users when possible

---

**💡 Tip:** Bookmark this page for quick access to all FloatCtl documentation. Use `Ctrl+F` to search for specific topics.