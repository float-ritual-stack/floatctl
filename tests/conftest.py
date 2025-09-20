"""Pytest configuration and fixtures for FloatCtl tests."""

import json
from datetime import datetime
import tempfile
from pathlib import Path

import pytest

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


@pytest.fixture(scope="session", autouse=True)
def ensure_repl_fixture_data() -> None:
    """Ensure REPL integration tests have a minimal notes.json to read."""

    notes_dir = Path.home() / ".floatctl" / "repl_notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    notes_file = notes_dir / "notes.json"

    if notes_file.exists():
        return

    timestamp = datetime.utcnow()
    entry = {
        "id": "test-entry",
        "content": "Welcome to the FloatCtl REPL test fixture.",
        "type": "log",
        "timestamp": timestamp.isoformat(),
        "indent": 0,
        "is_code": False,
        "language": "text",
        "metadata": None,
        "collapsed": False,
        "children": [],
        "timestamp_unix": int(timestamp.timestamp()),
        "temporal_anchor": None,
        "consciousness_mode": None,
        "ttl_expires": None,
        "ttl_expires_unix": None,
        "temporal_parent": None,
        "is_temporal_marker": False,
    }

    notes_file.write_text(json.dumps([entry]))
