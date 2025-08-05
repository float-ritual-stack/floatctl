"""Tests for test_example plugin."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from floatctl_plugin_test_example import TestExamplePlugin


class TestTestExamplePlugin:
    """Test the TestExamplePlugin class."""
    
    @pytest.fixture
    def plugin(self):
        """Create plugin instance for testing."""
        return TestExamplePlugin()
    
    def test_plugin_attributes(self, plugin):
        """Test plugin has correct attributes."""
        assert plugin.name == "test-example"
        assert plugin.description == "A FloatCtl plugin for test_example"
        assert plugin.version == "0.1.0"
    
    def test_validate_config(self, plugin):
        """Test configuration validation."""
        assert plugin.validate_config() is True
    
    def test_cleanup(self, plugin):
        """Test cleanup method."""
        # Should not raise any exceptions
        plugin.cleanup()
    
    def test_register_commands(self, plugin):
        """Test command registration."""
        import rich_click as click
        
        cli_group = click.Group()
        plugin.register_commands(cli_group)
        
        # Check that commands were registered
        assert "test_example" in cli_group.commands


class TestTestExampleCommands:
    """Test the plugin commands."""
    
    @pytest.fixture
    def plugin(self):
        """Create plugin instance for testing."""
        return TestExamplePlugin()
    
    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner()
    
    def test_hello_command(self, plugin, cli_runner):
        """Test the hello command."""
        import rich_click as click
        
        cli_group = click.Group()
        plugin.register_commands(cli_group)
        
        # Test the command exists and can be called
        result = cli_runner.invoke(cli_group, ["test_example", "hello"])
        assert result.exit_code == 0
    
    def test_echo_command(self, plugin, cli_runner):
        """Test the echo command."""
        import rich_click as click
        
        cli_group = click.Group()
        plugin.register_commands(cli_group)
        
        # Test the command with an argument
        result = cli_runner.invoke(cli_group, ["test_example", "echo", "test message"])
        assert result.exit_code == 0
