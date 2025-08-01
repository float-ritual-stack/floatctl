# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Workflow & Issue Tracking

### Before Starting Work
1. **Check existing issues**: `gh issue list --repo evanschultz/floatctl`
2. **Create/reference issue**: Every change should have an issue number
3. **Create feature branch**: 
   ```bash
   # Format: type/issue-description
   git checkout -b fix/42-toolbar-custom-domains
   git checkout -b feature/43-forest-diagnostics
   git checkout -b chore/44-consolidate-plugins
   ```

### Commit Message Format
```
type(scope): description (#issue)

[optional body]

# Examples:
fix(forest): toolbar display on custom domains (#42)
feat(forest): add diagnostics command (#43)
docs(plugins): clarify which note plugin to use
chore(plugins): archive old note implementations (#44)
```

### Types
- **fix**: Bug fixes
- **feat**: New features
- **docs**: Documentation only changes
- **chore**: Maintenance, refactoring, cleanup
- **test**: Adding missing tests
- **perf**: Performance improvements

### Issue Management
- **One issue per bug/feature** - Keep them focused
- **Link PRs to issues**: Use "Fixes #42" in PR description
- **Update issue status**: Comment progress on the issue
- **Small PRs**: One issue = one PR when possible

### Development Flow
1. Create/claim issue
2. Create feature branch from main
3. Make focused changes
4. Test locally: `uv run floatctl [command]`
5. Commit with proper message
6. Push and create PR
7. Reference issue in PR

## Session Summary - 2025-07-13

### Completed Features
- ✅ Pattern extraction in markdown exports (:: markers, float.* calls, tool usage)
- ✅ YAML frontmatter with conversation metadata
- ✅ Start time metadata for each message
- ✅ Clean filename generation (YYYY-MM-DD - Title format)
- ✅ Timezone-aware datetime filtering
- ✅ Global floatctl access via shell function
- ✅ Updated README and created CHANGELOG

### Global Access Setup
```bash
# Add to ~/.zshrc for development access
floatctl() {
    (cd /path/to/floatctl-py && uv run floatctl "$@")
}
```
This approach auto-reflects code changes without reinstallation.

### Shell Completions - TODO
Attempted Click-based shell completions but hit logging interference issues. The completion script generates correctly but needs clean separation of logging from completion output. Future approach: suppress all logging when `_FLOATCTL_COMPLETE` environment variable is set.

## Development Commands

### Setup and Installation
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install in development mode with all extras
uv pip install -e ".[dev]"
```

### Running the Tool
```bash
# Run via main.py
python main.py

# Run via entry point
floatctl --help

# Test conversation splitting (example)
python test_cli.py
```

### Testing and Quality
```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=floatctl

# Type checking
uv run mypy src/

# Linting and formatting
uv run ruff check src/
uv run ruff format src/
```

### Common Development Tasks
```bash
# Split conversation exports
floatctl conversations split <input-file.json> --output-dir ./output

# Extract artifacts from conversations
floatctl artifacts extract --input-dir ./conversations

# Smart export with auto-detection
floatctl export smart ./data --output ./processed
```

## Architecture Overview

### Plugin-Based Architecture
FloatCtl uses a plugin architecture that allows for extensible functionality. The system consists of:

1. **CLI Factory Pattern** (`cli.py`):
   - `create_cli_app()` function loads plugins before CLI execution
   - Ensures plugins are registered before command parsing
   - Uses Rich-Click for beautiful terminal output

2. **Plugin System** (`plugin_manager.py`):
   - `PluginBase`: Abstract base class all plugins inherit from
   - `PluginManager`: Discovers and loads plugins via setuptools entry points
   - Plugins register their commands with the main CLI group

3. **Core Components** (`core/`):
   - `config.py`: Pydantic-based configuration management
   - `database.py`: SQLite tracking of file operations using SQLAlchemy
   - `logging.py`: Structured JSON logging with structlog

### Plugin-Specific Documentation

Each plugin has its own CLAUDE.md file with detailed guidance:

- **Chroma Plugin**: `src/floatctl/plugins/chroma/CLAUDE.md`
  - FloatQL query patterns and syntax
  - Collection routing strategies
  - Query optimization tips
  
- **Conversations Plugin**: `src/floatctl/plugins/conversations/CLAUDE.md`
  - Pattern extraction details
  - File naming conventions
  - Tool call handling
  
- **Forest Plugin**: `src/floatctl/plugins/forest/CLAUDE.md`
  - V0 project management
  - Toolbar injection workflow
  - Deployment strategies

### Plugin Development
To create a new plugin:

1. Inherit from `PluginBase` in `plugin_manager.py`
2. Implement the `register_commands()` method
3. Create a plugin-specific `CLAUDE.md` in your plugin directory
4. Add plugin entry point in `pyproject.toml`:
   ```toml
   [project.entry-points."floatctl.plugins"]
   your_plugin = "floatctl.plugins.your_plugin:YourPlugin"
   ```

### Data Flow
1. **Input**: JSON exports from Claude/AI conversations
2. **Processing**: Plugins parse and transform data
3. **Storage**: SQLite tracks operations, files written to disk
4. **Logging**: All operations logged to JSONL format

### Key Design Decisions
- **UV for package management**: Ultra-fast dependency resolution
- **Rich for CLI**: Beautiful terminal output with progress bars
- **Pydantic for config**: Type-safe configuration handling
- **SQLAlchemy for database**: Robust ORM for operation tracking
- **Structlog for logging**: Structured JSON logs for analytics

### Database Schema
The system tracks all file operations in SQLite:
- File paths, sizes, and hashes
- Processing status and timestamps
- Conversation metadata and titles
- Plugin-specific tracking data

### Configuration
Configuration is loaded from (in order):
1. Environment variable: `FLOATCTL_CONFIG`
2. User config: `~/.config/floatctl/config.json`
3. Project config: `./floatctl.config.json`
4. Command-line overrides

## Important Context

This tool is part of the FLOAT ecosystem for processing AI conversation exports. It's designed to handle large conversation files efficiently and extract valuable artifacts and insights from them. The plugin architecture allows for easy extension with new processing capabilities.