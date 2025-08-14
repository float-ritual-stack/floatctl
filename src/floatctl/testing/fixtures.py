"""Common test fixtures for FloatCtl testing."""

import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock
import pytest

from floatctl.testing.plugin_test_utils import MockConfig, MockDatabaseManager


@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".floatctl"
        config_dir.mkdir(parents=True)
        yield config_dir


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.bind = MagicMock(return_value=logger)
    return logger


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "name": "Test Conversation",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T01:00:00Z",
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "human",
                "text": "Hello, how are you?",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "uuid": "msg-2", 
                "sender": "assistant",
                "text": "I'm doing well, thank you! How can I help you today?",
                "created_at": "2024-01-01T00:01:00Z"
            },
            {
                "uuid": "msg-3",
                "sender": "human", 
                "text": "Can you help me with a Python question?",
                "created_at": "2024-01-01T00:02:00Z"
            },
            {
                "uuid": "msg-4",
                "sender": "assistant",
                "text": "Of course! I'd be happy to help with Python. What's your question?",
                "created_at": "2024-01-01T00:03:00Z"
            }
        ]
    }


@pytest.fixture
def sample_file_data():
    """Sample file data for testing."""
    return {
        "conversations": [
            {
                "id": "conv-1",
                "title": "Python Help",
                "messages": [
                    {"role": "user", "content": "How do I use list comprehensions?"},
                    {"role": "assistant", "content": "List comprehensions are a concise way to create lists..."}
                ]
            },
            {
                "id": "conv-2", 
                "title": "Data Analysis",
                "messages": [
                    {"role": "user", "content": "How do I analyze CSV data with pandas?"},
                    {"role": "assistant", "content": "You can use pandas.read_csv() to load CSV files..."}
                ]
            }
        ]
    }


@pytest.fixture
def sample_artifacts():
    """Sample artifacts for testing."""
    return [
        {
            "type": "code",
            "language": "python",
            "content": "def hello_world():\n    print('Hello, World!')",
            "filename": "hello.py"
        },
        {
            "type": "markdown",
            "content": "# Test Document\n\nThis is a test document.",
            "filename": "test.md"
        },
        {
            "type": "json",
            "content": '{"key": "value", "number": 42}',
            "filename": "data.json"
        }
    ]


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client for testing."""
    client = MagicMock()
    
    # Mock collection
    collection = MagicMock()
    collection.query.return_value = {
        "documents": [["Sample document 1", "Sample document 2"]],
        "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
        "distances": [[0.1, 0.2]]
    }
    collection.add.return_value = None
    collection.count.return_value = 2
    
    client.get_collection.return_value = collection
    client.create_collection.return_value = collection
    client.list_collections.return_value = [
        MagicMock(name="test_collection"),
        MagicMock(name="another_collection")
    ]
    
    return client


@pytest.fixture
def mock_file_system(tmp_path):
    """Create a mock file system structure for testing."""
    # Create test directories
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    config_dir = tmp_path / ".floatctl"
    
    input_dir.mkdir()
    output_dir.mkdir()
    config_dir.mkdir()
    
    # Create test files
    test_json = input_dir / "test.json"
    test_json.write_text('{"test": "data"}')
    
    test_md = input_dir / "test.md"
    test_md.write_text("# Test\n\nThis is a test file.")
    
    config_file = config_dir / "config.yaml"
    config_file.write_text("verbose: true\noutput_dir: ./output")
    
    return {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "config_dir": config_dir,
        "test_json": test_json,
        "test_md": test_md,
        "config_file": config_file
    }


@pytest.fixture
def plugin_config():
    """Sample plugin configuration for testing."""
    return {
        "enabled": True,
        "settings": {
            "batch_size": 10,
            "timeout": 30,
            "retry_count": 3
        },
        "features": {
            "auto_save": True,
            "notifications": False,
            "debug_mode": True
        }
    }


@pytest.fixture
def middleware_test_data():
    """Test data for middleware testing."""
    return {
        "simple_data": {"key": "value", "number": 42},
        "list_data": [1, 2, 3, 4, 5],
        "complex_data": {
            "users": [
                {"name": "Alice", "age": 30, "active": True},
                {"name": "Bob", "age": 25, "active": False},
                {"name": "Charlie", "age": 35, "active": True}
            ],
            "metadata": {
                "total": 3,
                "created": "2024-01-01T00:00:00Z"
            }
        }
    }


@pytest.fixture
def event_test_data():
    """Test data for event system testing."""
    return {
        "file_processed": {
            "file_path": "/test/file.txt",
            "plugin": "test_plugin",
            "status": "completed",
            "size": 1024
        },
        "plugin_loaded": {
            "plugin_name": "test_plugin",
            "version": "1.0.0",
            "load_time": 0.5
        },
        "error_occurred": {
            "error_type": "ValidationError",
            "message": "Invalid input data",
            "plugin": "test_plugin"
        }
    }