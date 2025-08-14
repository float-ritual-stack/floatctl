"""Tests for test_dependency_plugin plugin."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from floatctl_plugin_test_dependency_plugin import TestDependencyPluginPlugin


class TestTestDependencyPluginPlugin:
    """Test the TestDependencyPluginPlugin class."""
    
    @pytest.fixture
    def plugin(self):
        """Create plugin instance for testing."""
        return TestDependencyPluginPlugin()
    
    def test_plugin_attributes(self, plugin):
        """Test plugin has correct attributes."""
        assert plugin.name == "test-dependency-plugin"
        assert plugin.description == "A FloatCtl plugin for test_dependency_plugin"
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
        assert "test_dependency_plugin" in cli_group.commands


class TestTestDependencyPluginCommands:
    """Test the plugin commands."""
    
    @pytest.fixture
    def plugin(self):
        """Create plugin instance for testing."""
        return TestDependencyPluginPlugin()
    
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
        result = cli_runner.invoke(cli_group, ["test_dependency_plugin", "hello"])
        assert result.exit_code == 0
    
    def test_echo_command(self, plugin, cli_runner):
        """Test the echo command."""
        import rich_click as click
        
        cli_group = click.Group()
        plugin.register_commands(cli_group)
        
        # Test the command with an argument
        result = cli_runner.invoke(cli_group, ["test_dependency_plugin", "echo", "test message"])
        assert result.exit_code == 0
