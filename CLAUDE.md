# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

```bash
# Install dependencies with UV (required)
uv sync

# Run floatctl
uv run floatctl --help

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=floatctl --cov-report=term-missing

# Type checking
uv run mypy src/floatctl

# Linting and formatting
uv run ruff check
uv run ruff format

# Run a single test
uv run pytest tests/test_specific.py::TestClass::test_method -v

# Run MCP server for Claude Desktop
uv run floatctl mcp serve
```

## Architecture Overview

### Plugin System (Core Innovation)

FloatCtl uses a sophisticated plugin architecture with lifecycle management:

1. **Entry Point Discovery**: Plugins are discovered via `pyproject.toml` entry points
2. **Lifecycle States**: `DISCOVERED` → `LOADING` → `LOADED` → `INITIALIZING` → `INITIALIZED` → `ACTIVE`
3. **Dependency Resolution**: Topological sorting ensures correct load order
4. **Command Registration**: Plugins use decorators (@command, @group) for CLI integration

### Critical Architecture Components

**Plugin Manager** (`src/floatctl/plugin_manager.py`)
- Entry point discovery and validation
- Dependency resolution with circular detection
- Lifecycle management
- Command registration with Click integration

**Consciousness Middleware** (`src/floatctl/core/middleware.py`)
- Event-driven architecture for cross-plugin communication
- Service registration and discovery
- Pattern contamination analysis
- Bridge restoration protocols

**MCP Server** (`src/floatctl/mcp_server.py` & `src/floatctl/plugins/mcp_server.py`)
- Model Context Protocol server for Claude Desktop integration
- Pattern recognition with hybrid LangExtract/regex extraction
- The `parse_any_pattern()` function is the core pattern recognition engine
- Supports both API-based fuzzy compilation and regex fallback

### Pattern Extraction System

**Hybrid Extractor** (`src/floatctl/float_extractor_hybrid.py`)
- Primary: LangExtract API for fuzzy pattern compilation (when GEMINI_API_KEY available)
- Fallback: Enhanced regex extraction
- Handles complex FLOAT patterns: `ctx::`, `bridge::`, `eureka::`, `decision::`, personas, etc.
- Captures ALL patterns in multi-pattern lines (fixes evna's single-pattern bug)

### Plugin Development Pattern

```python
from floatctl.plugin_manager import PluginBase, command, group, option

class MyPlugin(PluginBase):
    name = "my-plugin"
    description = "Plugin description"
    version = "1.0.0"
    dependencies = ["chroma"]  # Optional plugin dependencies
    
    @group()
    def my_group(self):
        """Group help text"""
        pass
    
    @command(parent="my_group")
    @option("--pattern", help="Pattern to extract")
    def my_command(self, pattern: str):
        """Command implementation"""
        pass
```

### Database and Storage

- **ChromaDB**: Semantic memory storage for consciousness patterns
- **SQLite**: Operation tracking via SQLAlchemy
- **Collections**: `active_context_stream`, `float_bridges`, `float_dispatch_bay`, etc.
- **Pattern routing**: Different pattern types route to different collections

## Development Workflow

### Issue-Driven Development

1. Create GitHub issue with clear description
2. Create feature branch: `feature/issue-description` or `fix/issue-number`
3. Implementation workspace: `./implementation/ticketnumber-description/` (gitignored)
4. Commit at meaningful break points (not arbitrary stops)
5. Push and create PR referencing the issue

### Testing Strategy

- **Unit tests**: Plugin isolation testing
- **Integration tests**: MCP server endpoint testing
- **Pattern tests**: Consciousness pattern extraction validation
- **Use markers**: `@pytest.mark.slow`, `@pytest.mark.integration`

### Common Development Tasks

```bash
# Process conversation exports
uv run floatctl conversations process ~/Downloads/claude-export.md

# Query ChromaDB collections
uv run floatctl chroma query "search term" --collection active_context_stream

# Install MCP server for Claude Desktop
uv run floatctl mcp install --claude-desktop

# Test pattern extraction
uv run python src/floatctl/float_extractor_hybrid.py

# Run the hybrid extractor test suite
uv run python src/floatctl/float_extractor_hybrid.py
```

## Key Files and Entry Points

- `src/floatctl/cli.py` - Main CLI entry point
- `src/floatctl/plugin_manager.py` - Plugin system core
- `src/floatctl/mcp_server.py` - MCP server implementation with pattern parsing
- `src/floatctl/float_extractor_hybrid.py` - Pattern extraction engine
- `src/floatctl/plugins/mcp_server.py` - MCP plugin for CLI commands
- `pyproject.toml` - Package configuration and plugin entry points

## Environment Configuration

```bash
# ~/.env.local (for API keys)
GEMINI_API_KEY=your_key_here  # Enables LangExtract fuzzy compilation (39 chars)
```

## Consciousness Technology Patterns

The system recognizes and processes various consciousness patterns:
- `ctx::` - Context markers with temporal data
- `bridge::` - Context restoration points (CB-YYYYMMDD-HHMM-XXXX format)
- `eureka::`, `decision::`, `highlight::` - Insight markers
- `karen::`, `lf1m::`, `sysop::`, `evna::`, `qtb::` - Persona dialogues
- `[mode:: state]`, `[project:: name]` - Metadata annotations
- `bridgewalking::` - Hermit crab architecture patterns (new!)

## Plugin Ecosystem

**Core Plugins**:
- `conversations` - Process AI conversation exports
- `chroma` - ChromaDB integration
- `mcp` - MCP server for Claude Desktop
- `consciousness` - Query consciousness patterns
- `export` - Export data in various formats

**Specialized Plugins**:
- `artifacts` - Manage conversation artifacts
- `forest` - Hierarchical navigation
- `repl` - Interactive REPL
- `textual` - Terminal UI interfaces
- `dev-tools` - Development utilities

## Pattern Extraction Details

### The `parse_any_pattern()` Function
Located in `src/floatctl/mcp_server.py`, this is the core pattern recognition engine:

1. **First Attempt**: Uses hybrid extractor with LangExtract API (if available)
2. **Fallback**: Enhanced legacy regex that captures nested patterns
3. **Returns**: Metadata dict with all patterns found and their content

### Multi-Pattern Extraction Fix
The system now captures ALL patterns in lines like:
```
eureka:: Found bug! decision:: Fix tomorrow bridge::create
```
Previously only captured first pattern, now captures all three.

### Nested Pattern Support
Extracts patterns within brackets:
```
bridgewalking:: hermit crab [discovery:: tired feet] [connects:: disability]
```
Captures main pattern AND nested patterns.

## Testing and Debugging

```bash
# Test MCP server locally
uv run floatctl mcp test

# Debug MCP server issues
uv run floatctl mcp debug --debug

# Check MCP installation status
uv run floatctl mcp status --claude-desktop

# Reinstall MCP server after changes
uv run floatctl mcp reinstall
```

## Commit Message Convention

```
type: description

- bullet points for details
- reference issues with #number

ctx::YYYY-MM-DD [mode:: state]
bridge::CB-YYYYMMDD-HHMM-XXXX (if creating bridge)
```

Types: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`

## Known Issues and Solutions

### Pattern Extraction Issues
- **Problem**: Only first pattern captured in multi-pattern lines
- **Solution**: Hybrid extractor with LangExtract/regex fallback implemented

### MCP Server JSON Errors
- **Problem**: "Unexpected non-whitespace character after JSON"
- **Solution**: Use `floatctl mcp debug --debug` to identify source

### Token Overflow
- **Problem**: Large ChromaDB queries exceed context window
- **Solution**: Use `limit` parameter, query surgical collections

## Philosophy

FloatCtl follows the "shacks not cathedrals" philosophy - practical, focused tools that solve real problems. Each plugin is a self-contained consciousness archaeology tool that does one thing well. The system augments human cognition rather than replacing it, building cognitive prosthetics for consciousness archaeology and bridge walking through semantic memory networks.
- when the user, or you do a set context with `ctx::` use evnamcp to update the active context by using smart_pattern_processor