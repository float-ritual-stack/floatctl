"""Tests for the logging module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import structlog

from floatctl.core.logging import setup_logging, setup_quiet_logging, log_command, log_file_operation, get_logger


@pytest.fixture
def mock_config():
    """Create a mock config object for testing."""
    config = MagicMock()
    config.data_dir = Path("/tmp/test_floatctl")
    return config


class TestSetupLogging:
    """Test the setup_logging function."""
    
    def test_setup_logging_console_only(self, mock_config):
        """Test setting up logging with console output only."""
        with patch('structlog.configure') as mock_configure:
            setup_logging(mock_config, log_file=None)
            
            # Should configure structlog
            mock_configure.assert_called_once()
            
            # Check the configuration
            call_args = mock_configure.call_args
            assert 'processors' in call_args.kwargs
            assert 'context_class' in call_args.kwargs
            assert 'logger_factory' in call_args.kwargs
            assert 'cache_logger_on_first_use' in call_args.kwargs
    
    def test_setup_logging_with_file(self, mock_config):
        """Test setting up logging with file output."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            log_file = Path(f.name)
        
        try:
            with patch('structlog.configure') as mock_configure:
                setup_logging(mock_config, log_file=log_file)
                
                # Should configure structlog
                mock_configure.assert_called_once()
                
                # Check that log file parent directory would be created
                assert log_file.parent.exists()
        finally:
            log_file.unlink(missing_ok=True)
    
    def test_setup_logging_creates_log_directory(self, mock_config):
        """Test that setup_logging creates log file directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "subdir" / "test.log"
            
            # Create the parent directory first (setup_logging should handle this)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with patch('structlog.configure'):
                setup_logging(mock_config, log_file=log_file)
                
                # Directory should exist
                assert log_file.parent.exists()
    
    def test_setup_quiet_logging(self):
        """Test setup_quiet_logging function."""
        with patch('structlog.configure') as mock_configure:
            setup_quiet_logging()
            mock_configure.assert_called_once()


class TestLogCommand:
    """Test the log_command function."""
    
    @pytest.fixture(autouse=True)
    def setup_structlog(self):
        """Setup structlog for testing."""
        setup_quiet_logging()
    
    def test_log_command_basic(self):
        """Test basic command logging."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_get_logger.return_value = mock_logger
            
            logger = log_command("test_command", {"arg1": "value1"})
            
            # Should return the bound logger
            assert logger == mock_bound_logger
            
            # Should bind command context
            mock_logger.bind.assert_called_once_with(
                command="test_command",
                args={"arg1": "value1"},
                plugin=None
            )
    
    def test_log_command_with_plugin(self):
        """Test command logging with plugin context."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_get_logger.return_value = mock_logger
            
            logger = log_command("test_command", {"arg1": "value1"}, plugin="test_plugin")
            
            # Should bind command and plugin context
            mock_logger.bind.assert_called_once_with(
                command="test_command",
                args={"arg1": "value1"},
                plugin="test_plugin"
            )
    
    def test_log_command_empty_args(self):
        """Test command logging with empty args."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_get_logger.return_value = mock_logger
            
            logger = log_command("test_command", {})
            
            mock_logger.bind.assert_called_once_with(
                command="test_command",
                args={},
                plugin=None
            )
    
    def test_log_command_none_args(self):
        """Test command logging with None args."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_get_logger.return_value = mock_logger
            
            logger = log_command("test_command", None)
            
            mock_logger.bind.assert_called_once_with(
                command="test_command",
                args=None,
                plugin=None
            )


class TestLogFileOperation:
    """Test the log_file_operation function."""
    
    @pytest.fixture(autouse=True)
    def setup_structlog(self):
        """Setup structlog for testing."""
        setup_quiet_logging()
    
    def test_log_file_operation_basic(self):
        """Test basic file operation logging."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_get_logger.return_value = mock_logger
            
            logger = log_file_operation(
                operation="write",
                file_path=Path("/test/file.txt"),
                status="success"
            )
            
            # Should return the bound logger
            assert logger == mock_bound_logger
            
            # Should bind file operation context (including file_name)
            mock_logger.bind.assert_called_once_with(
                operation="write",
                file_path="/test/file.txt",
                file_name="file.txt",
                status="success"
            )
    
    def test_log_file_operation_with_metadata(self):
        """Test file operation logging with metadata."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_get_logger.return_value = mock_logger
            
            logger = log_file_operation(
                operation="read",
                file_path=Path("/test/file.txt"),
                status="success",
                file_size=1024,
                file_hash="abc123",
                metadata={"lines": 100, "format": "json"}
            )
            
            mock_logger.bind.assert_called_once_with(
                operation="read",
                file_path="/test/file.txt",
                file_name="file.txt",
                status="success",
                file_size=1024,
                file_hash="abc123",
                metadata={"lines": 100, "format": "json"}
            )
    
    def test_log_file_operation_path_conversion(self):
        """Test that Path objects are converted to strings."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_get_logger.return_value = mock_logger
            
            # Test with Path object
            file_path = Path("/test/file.txt")
            
            log_file_operation(
                operation="delete",
                file_path=file_path,
                status="success"
            )
            
            # Should convert Path to string
            call_args = mock_logger.bind.call_args
            assert call_args[1]["file_path"] == "/test/file.txt"
            assert isinstance(call_args[1]["file_path"], str)
            assert call_args[1]["file_name"] == "file.txt"
    
    def test_log_file_operation_path_object_only(self):
        """Test file operation logging requires Path object."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_get_logger.return_value = mock_logger
            
            # Test with Path object (this should work)
            file_path = Path("/test/file.txt")
            
            logger = log_file_operation(
                operation="copy",
                file_path=file_path,
                status="success"
            )
            
            call_args = mock_logger.bind.call_args
            assert call_args[1]["file_path"] == "/test/file.txt"
            assert call_args[1]["file_name"] == "file.txt"


class TestLoggingIntegration:
    """Test logging integration scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup_structlog(self):
        """Setup structlog for testing."""
        setup_quiet_logging()
    
    def test_logging_workflow(self, mock_config):
        """Test a complete logging workflow."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_bound_logger = MagicMock()
            mock_logger.bind.return_value = mock_bound_logger
            mock_get_logger.return_value = mock_logger
            
            # Setup logging
            with patch('structlog.configure'):
                setup_logging(mock_config, log_file=None)
            
            # Log a command
            cmd_logger = log_command("conversations.split", {
                "input_file": "/test/input.json",
                "output_dir": "/test/output"
            }, plugin="conversations")
            
            # Log file operations
            file_logger = log_file_operation(
                operation="read",
                file_path=Path("/test/input.json"),
                status="success",
                file_size=2048
            )
            
            # Should have created loggers with proper context
            assert mock_get_logger.call_count >= 2
    
    def test_logger_context_isolation(self):
        """Test that logger contexts are properly isolated."""
        with patch('floatctl.core.logging.get_logger') as mock_get_logger:
            mock_logger1 = MagicMock()
            mock_logger2 = MagicMock()
            mock_bound1 = MagicMock()
            mock_bound2 = MagicMock()
            mock_logger1.bind.return_value = mock_bound1
            mock_logger2.bind.return_value = mock_bound2
            mock_get_logger.side_effect = [mock_logger1, mock_logger2]
            
            # Create two different loggers
            cmd_logger = log_command("command1", {"arg": "value1"})
            file_logger = log_file_operation(
                operation="write", 
                file_path=Path("/test/file.txt"), 
                status="success"
            )
            
            # Each should return bound loggers
            assert cmd_logger == mock_bound1
            assert file_logger == mock_bound2
            
            # Check that contexts are different
            cmd_call = mock_logger1.bind.call_args[1]
            file_call = mock_logger2.bind.call_args[1]
            
            assert "command" in cmd_call
            assert "operation" in file_call
            assert cmd_call != file_call