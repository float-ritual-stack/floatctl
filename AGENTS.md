# AGENTS.md - FloatCtl Development Guide

## Build & Test Commands
```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/unit/test_structlog.py

# Run specific test
uv run pytest tests/integration/test_cli.py::test_specific_function -v

# Type checking
uv run mypy src/

# Linting & formatting
uv run ruff check src/
uv run ruff format src/

# Coverage
uv run pytest --cov=floatctl --cov-report=html
```

## Code Style Guidelines
- **Imports**: Standard library first, third-party, then local imports with blank lines between groups
- **Types**: Use type hints everywhere, import from `typing` for Python <3.9 compatibility
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Docstrings**: Use triple quotes with brief description, Args/Returns sections for complex functions
- **Error handling**: Use specific exceptions, log errors with structlog, include context
- **Plugin architecture**: Inherit from `PluginBase`, implement `register_commands()` method
- **Rich output**: Use rich-click for CLI, Rich Console for formatted output, avoid plain print()
- **Database**: Use SQLAlchemy models, track operations in DatabaseManager
- **Config**: Use Pydantic models with Field() descriptions and validators