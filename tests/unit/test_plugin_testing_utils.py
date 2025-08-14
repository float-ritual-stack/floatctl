"""Tests for plugin testing utilities."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

import rich_click as click

from floatctl.testing import (
    PluginTestCase,
    MockConfig,
    MockDatabaseManager,
    create_test_plugin,
    assert_command_registered,
    assert_plugin_valid
)
from floatctl.plugin_manager import PluginBase
from floatctl.core.database import ProcessingStatus


class TestMockConfig:
    """Test the MockConfig utility."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MockConfig()
        
        assert config.data_dir.name == "floatctl_test"
        assert config.db_path.name == "test.db"
        assert config.output_dir.name == "output"
        assert config.verbose is False
        assert config.plugin_config == {}
    
    def test_custom_config(self):
        """Test configuration with custom values."""
        config = MockConfig(
            verbose=True,
            plugin_config={"test": {"key": "value"}}
        )
        
        assert config.verbose is True
        assert config.plugin_config == {"test": {"key": "value"}}
    
    def test_get_plugin_config(self):
        """Test getting plugin-specific configuration."""
        config = MockConfig(plugin_config={"test_plugin": {"setting": "value"}})
        
        plugin_config = config.get_plugin_config("test_plugin")
        assert plugin_config == {"setting": "value"}
        
        empty_config = config.get_plugin_config("nonexistent")
        assert empty_config == {}


class TestMockDatabaseManager:
    """Test the MockDatabaseManager utility."""
    
    def test_record_file_run(self):
        """Test recording file runs."""
        db = MockDatabaseManager()
        
        run = db.record_file_run(
            file_path=Path("/test/file.txt"),
            plugin="test_plugin",
            command="test_command"
        )
        
        assert run.id == 1
        assert run.file_path == "/test/file.txt"
        assert run.plugin == "test_plugin"
        assert run.command == "test_command"
        assert run.status == ProcessingStatus.PROCESSING
        assert len(db.file_runs) == 1
    
    def test_complete_file_run(self):
        """Test completing file runs."""
        db = MockDatabaseManager()
        
        run = db.record_file_run(
            file_path=Path("/test/file.txt"),
            plugin="test_plugin", 
            command="test_command"
        )
        
        success = db.complete_file_run(run.id, ProcessingStatus.COMPLETED)
        assert success is True
        assert run.status == ProcessingStatus.COMPLETED
        
        # Test non-existent run
        success = db.complete_file_run(999, ProcessingStatus.COMPLETED)
        assert success is False
    
    def test_get_file_history(self):
        """Test getting file history."""
        db = MockDatabaseManager()
        
        # Record multiple runs for the same file
        file_path = Path("/test/file.txt")
        run1 = db.record_file_run(file_path, "plugin1", "command1")
        run2 = db.record_file_run(file_path, "plugin2", "command2")
        
        # Record run for different file
        db.record_file_run(Path("/test/other.txt"), "plugin1", "command1")
        
        history = db.get_file_history(file_path)
        assert len(history) == 2
        assert run1 in history
        assert run2 in history
    
    def test_queue_file(self):
        """Test queuing files."""
        db = MockDatabaseManager()
        
        db.queue_file(Path("/test/file.txt"), "test_plugin")
        
        assert len(db.queue_items) == 1
        assert db.queue_items[0].file_path == "/test/file.txt"
        assert db.queue_items[0].plugin == "test_plugin"


class TestPluginTestCase:
    """Test the PluginTestCase utility."""
    
    def test_initialization(self):
        """Test PluginTestCase initialization."""
        test_case = PluginTestCase()
        
        assert test_case.config is not None
        assert test_case.db_manager is not None
        assert test_case.event_bus is not None
        assert test_case.service_registry is not None
        assert test_case.cli_runner is not None
    
    def test_create_plugin(self):
        """Test creating plugin instances."""
        test_case = PluginTestCase()
        
        # Create a test plugin class
        TestPlugin = create_test_plugin("test_plugin")
        
        plugin = test_case.create_plugin(TestPlugin)
        assert plugin.name == "test_plugin"
        assert plugin.description == "Test plugin: test_plugin"
        assert plugin.version == "1.0.0"
    
    def test_register_plugin_commands(self):
        """Test registering plugin commands."""
        test_case = PluginTestCase()
        
        TestPlugin = create_test_plugin("test_plugin")
        plugin = test_case.create_plugin(TestPlugin)
        
        cli_group = test_case.register_plugin_commands(plugin)
        assert "test-command" in cli_group.commands
    
    def test_run_command(self):
        """Test running CLI commands."""
        test_case = PluginTestCase()
        
        TestPlugin = create_test_plugin("test_plugin")
        plugin = test_case.create_plugin(TestPlugin)
        cli_group = test_case.register_plugin_commands(plugin)
        
        result = test_case.run_command(cli_group, ["test-command"])
        assert result.exit_code == 0
        assert "Hello from test_plugin" in result.output
    
    def test_assert_command_exists(self):
        """Test asserting command existence."""
        test_case = PluginTestCase()
        
        TestPlugin = create_test_plugin("test_plugin")
        plugin = test_case.create_plugin(TestPlugin)
        cli_group = test_case.register_plugin_commands(plugin)
        
        # Should not raise
        test_case.assert_command_exists(cli_group, "test-command")
        
        # Should raise
        with pytest.raises(AssertionError):
            test_case.assert_command_exists(cli_group, "nonexistent-command")
    
    def test_assert_command_successful(self):
        """Test asserting command success."""
        test_case = PluginTestCase()
        
        # Mock successful result
        result = MagicMock()
        result.exit_code = 0
        test_case.assert_command_successful(result)
        
        # Mock failed result
        result.exit_code = 1
        result.output = "Error message"
        with pytest.raises(AssertionError):
            test_case.assert_command_successful(result)
    
    def test_assert_plugin_valid(self):
        """Test asserting plugin validity."""
        test_case = PluginTestCase()
        
        TestPlugin = create_test_plugin("test_plugin")
        plugin = test_case.create_plugin(TestPlugin)
        
        # Should not raise
        test_case.assert_plugin_valid(plugin)
        
        # Test invalid plugin
        class InvalidPlugin:
            pass
        
        invalid_plugin = InvalidPlugin()
        with pytest.raises(AssertionError):
            test_case.assert_plugin_valid(invalid_plugin)


class TestCreateTestPlugin:
    """Test the create_test_plugin utility."""
    
    def test_basic_plugin_creation(self):
        """Test creating a basic test plugin."""
        TestPlugin = create_test_plugin("my_plugin")
        plugin = TestPlugin()
        
        assert plugin.name == "my_plugin"
        assert plugin.description == "Test plugin: my_plugin"
        assert plugin.version == "1.0.0"
        assert plugin.validate_config() is True
    
    def test_custom_plugin_creation(self):
        """Test creating a plugin with custom attributes."""
        TestPlugin = create_test_plugin(
            "custom_plugin",
            description="Custom test plugin",
            version="2.0.0"
        )
        plugin = TestPlugin()
        
        assert plugin.name == "custom_plugin"
        assert plugin.description == "Custom test plugin"
        assert plugin.version == "2.0.0"
    
    def test_plugin_commands(self):
        """Test that created plugin has working commands."""
        TestPlugin = create_test_plugin("test_plugin")
        plugin = TestPlugin()
        
        cli_group = click.Group()
        plugin.register_commands(cli_group)
        
        assert "test-command" in cli_group.commands
    
    def test_plugin_lifecycle(self):
        """Test plugin lifecycle methods."""
        TestPlugin = create_test_plugin("test_plugin")
        plugin = TestPlugin()
        
        # Should not raise
        plugin.cleanup()


class TestAssertFunctions:
    """Test the assert utility functions."""
    
    def test_assert_command_registered(self):
        """Test assert_command_registered function."""
        cli_group = click.Group()
        
        @cli_group.command()
        def test_command():
            pass
        
        # Should not raise
        assert_command_registered(cli_group, "test-command")
        
        # Should raise
        with pytest.raises(AssertionError):
            assert_command_registered(cli_group, "nonexistent")
    
    def test_assert_plugin_valid(self):
        """Test assert_plugin_valid function."""
        TestPlugin = create_test_plugin("test_plugin")
        plugin = TestPlugin()
        
        # Should not raise
        assert_plugin_valid(plugin)
        
        # Test with invalid plugin
        class InvalidPlugin:
            pass
        
        invalid_plugin = InvalidPlugin()
        with pytest.raises(AssertionError):
            assert_plugin_valid(invalid_plugin)