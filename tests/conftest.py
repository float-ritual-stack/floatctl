"""Pytest configuration and fixtures for FloatCtl tests."""

import pytest
from pathlib import Path
import tempfile
import shutil

from floatctl.core.logging import setup_quiet_logging


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Setup quiet logging for all tests to avoid structlog configuration issues."""
    setup_quiet_logging()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config_dir(monkeypatch, temp_dir):
    """Mock the config directory to avoid affecting real config."""
    config_dir = temp_dir / ".config" / "floatctl"
    config_dir.mkdir(parents=True)
    monkeypatch.setenv("FLOATCTL_CONFIG", str(config_dir / "config.json"))
    return config_dir


@pytest.fixture
def sample_conversation_json():
    """Return a sample conversation JSON structure for testing."""
    return {
        "name": "Test Conversation",
        "created_at": "2024-01-01T00:00:00Z",
        "messages": [
            {
                "role": "user",
                "content": "Hello, world!",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "role": "assistant",
                "content": "Hello! How can I help you?",
                "created_at": "2024-01-01T00:01:00Z"
            }
        ]
    }