"""Tests for the logging module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import structlog

from floatctl.core.logging import setup_logging, log_command, log_file_operation


class TestSetupLogging:
    """Test the setup_logging function."""
    
    def test_setup_logging_console_only(self):
        """Test setting up logging with console output only."""
        with patch('structlog.configure') as mock_configure:
            setup_logging(level="INFO", log_file=None)
            
            # Should configure structlog
            mock_configure.assert_called_once()
            
            # Check the configuration
            call_args = mock_configure.call_args
            assert 'processors' in call_args.kwargs
            assert 'wrapper_class' in call_args.kwargs
            assert 'logger_factory' in call_args.kwargs
            assert 'cache_logger_on_first_use' in call_args.kwargs
    
    def test_setup_logging_with_file(self):
        """Test setting up logging with file output."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            log_file = Path(f.name)
        
        try:
            with patch('structlog.configure') as mock_configure:
                setup_logging(level="DEBUG", log_file=log_file)
                
                # Should configure structlog
                mock_configure.assert_called_once()
                
                # Check that log file parent directory would be created
                assert log_file.parent.exists()
        finally:
            log_file.unlink(missing_ok=True)
    
    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates log file directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "subdir" / "test.log"
            
            with patch('structlog.configure'):
                setup_logging(level="INFO", log_file=log_file)
                
                # Directory should be created
                assert log_file.parent.exists()
    
    def test_setup_logging_different_levels(self):
        """Test setup_logging with different log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in levels:
            with patch('structlog.configure') as mock_configure:
                setup_logging(level=level, log_file=None)
                mock_configure.assert_called_once()


class TestLogCommand:
    """Test the log_command function."""
    
    def test_log_command_basic(self):
        """Test basic command logging."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = log_command("test_command", {"arg1": "value1"})
            
            # Should return the logger
            assert logger == mock_logger
            
            # Should bind command context
            mock_logger.bind.assert_called_once_with(
                command="test_command",
                args={"arg1": "value1"},
                plugin=None
            )
    
    def test_log_command_with_plugin(self):
        """Test command logging with plugin context."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
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
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = log_command("test_command", {})
            
            mock_logger.bind.assert_called_once_with(
                command="test_command",
                args={},
                plugin=None
            )
    
    def test_log_command_none_args(self):
        """Test command logging with None args."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = log_command("test_command", None)
            
            mock_logger.bind.assert_called_once_with(
                command="test_command",
                args=None,
                plugin=None
            )


class TestLogFileOperation:
    """Test the log_file_operation function."""
    
    def test_log_file_operation_basic(self):
        """Test basic file operation logging."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = log_file_operation(
                operation="write",
                file_path=Path("/test/file.txt"),
                status="success"
            )
            
            # Should return the logger
            assert logger == mock_logger
            
            # Should bind file operation context
            mock_logger.bind.assert_called_once_with(
                operation="write",
                file_path="/test/file.txt",
                status="success",
                file_size=None,
                file_hash=None,
                metadata=None
            )
    
    def test_log_file_operation_with_metadata(self):
        """Test file operation logging with metadata."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            metadata = {"lines": 100, "format": "json"}
            
            logger = log_file_operation(
                operation="read",
                file_path=Path("/test/file.txt"),
                status="success",
                file_size=1024,
                file_hash="abc123",
                metadata=metadata
            )
            
            mock_logger.bind.assert_called_once_with(
                operation="read",
                file_path="/test/file.txt",
                status="success",
                file_size=1024,
                file_hash="abc123",
                metadata=metadata
            )
    
    def test_log_file_operation_path_conversion(self):
        """Test that Path objects are converted to strings."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
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
    
    def test_log_file_operation_string_path(self):
        """Test file operation logging with string path."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Test with string path
            file_path = "/test/file.txt"
            
            log_file_operation(
                operation="copy",
                file_path=file_path,
                status="success"
            )
            
            call_args = mock_logger.bind.call_args
            assert call_args[1]["file_path"] == "/test/file.txt"


class TestLoggingIntegration:
    """Test logging integration scenarios."""
    
    def test_logging_workflow(self):
        """Test a complete logging workflow."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Setup logging
            with patch('structlog.configure'):
                setup_logging(level="INFO", log_file=None)
            
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
            
            file_logger = log_file_operation(
                operation="write",
                file_path=Path("/test/output/conversation1.json"),
                status="success",
                file_size=1024,
                metadata={"conversation_id": "conv_123"}
            )
            
            # Should have created loggers with proper context
            assert mock_get_logger.call_count >= 2
    
    def test_logger_context_isolation(self):
        """Test that logger contexts are properly isolated."""
        with patch('structlog.get_logger') as mock_get_logger:
            mock_logger1 = MagicMock()
            mock_logger2 = MagicMock()
            mock_get_logger.side_effect = [mock_logger1, mock_logger2]
            
            # Create two different loggers
            cmd_logger = log_command("command1", {"arg": "value1"})
            file_logger = log_file_operation("write", Path("/test/file.txt"), "success")
            
            # Each should have its own context
            assert cmd_logger == mock_logger1
            assert file_logger == mock_logger2
            
            # Check that contexts are different
            cmd_call = mock_logger1.bind.call_args[1]
            file_call = mock_logger2.bind.call_args[1]
            
            assert "command" in cmd_call
            assert "operation" in file_call
            assert cmd_call != file_call