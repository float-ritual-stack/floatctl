# FloatCtl Tests

This directory contains the test suite for FloatCtl.

## Test Organization

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for CLI and UI components
├── fixtures/       # Test data and shared fixtures
└── experimental/   # Debug scripts and experimental tests
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run only unit tests
uv run pytest tests/unit/

# Run only integration tests  
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=floatctl

# Run specific test file
uv run pytest tests/unit/test_structlog.py

# Run tests with specific marker
uv run pytest -m "not slow"
```

## Test Guidelines

1. **Unit Tests** (`tests/unit/`)
   - Test individual functions and classes in isolation
   - Mock external dependencies
   - Should be fast and deterministic

2. **Integration Tests** (`tests/integration/`)
   - Test CLI commands end-to-end
   - Test UI components with simulated input
   - May create temporary files/directories

3. **Fixtures** (`tests/fixtures/`)
   - Sample conversation JSON files
   - Test configuration files
   - Mock data for testing

4. **Experimental** (`tests/experimental/`)
   - Debug scripts not part of main test suite
   - Manual testing utilities
   - Work-in-progress tests

## Writing Tests

Tests should follow pytest conventions:
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

Use fixtures from `conftest.py` for common test needs like temporary directories and mock configurations.