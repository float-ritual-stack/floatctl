"""Regression tests for plugin compatibility during refactoring."""

import pytest
from unittest.mock import patch, MagicMock

from floatctl.plugin_manager import PluginManager, PluginBase


class TestPluginLoading:
    """Test that all existing plugins load correctly."""
    
    def test_plugin_manager_initialization(self):
        """Test that PluginManager initializes without errors."""
        manager = PluginManager()
        assert manager is not None
        assert hasattr(manager, 'plugins')
        assert isinstance(manager.plugins, dict)
    
    def test_all_expected_plugins_discoverable(self):
        """Test that all expected plugins can be discovered."""
        manager = PluginManager()
        
        # Mock the entry points to avoid dependency on actual installation
        with patch('floatctl.plugin_manager.entry_points') as mock_entry_points:
            # Create mock entry points for expected plugins
            expected_plugins = [
                'conversations', 'chroma', 'forest', 'artifacts', 
                'export', 'repl', 'textual', 'mcp'
            ]
            
            mock_entries = []
            for plugin_name in expected_plugins:
                mock_entry = MagicMock()
                mock_entry.name = plugin_name
                mock_entry.load.return_value = type(f'{plugin_name.title()}Plugin', (PluginBase,), {
                    'name': plugin_name,
                    'description': f'Test {plugin_name} plugin',
                    'version': '1.0.0',
                    'register_commands': lambda self, cli_group: None
                })
                mock_entries.append(mock_entry)
            
            mock_entry_points.return_value = mock_entries
            
            # Load plugins
            manager.load_plugins()
            
            # Verify all expected plugins were loaded
            loaded_plugins = list(manager.plugins.keys())
            for plugin_name in expected_plugins:
                assert plugin_name in loaded_plugins, f"Plugin {plugin_name} not loaded"
    
    def test_plugin_base_class_interface(self):
        """Test that PluginBase interface remains stable."""
        # Test that PluginBase has expected attributes and methods
        assert hasattr(PluginBase, 'name')
        assert hasattr(PluginBase, 'description')
        assert hasattr(PluginBase, 'version')
        assert hasattr(PluginBase, 'register_commands')
        assert hasattr(PluginBase, 'validate_config')
        assert hasattr(PluginBase, 'cleanup')
        
        # Test that we can instantiate PluginBase
        plugin = PluginBase()
        assert plugin.name == "unnamed"
        assert plugin.description == "No description provided"
        assert plugin.version == "0.1.0"
        
        # Test that required methods exist
        assert callable(plugin.register_commands)
        assert callable(plugin.validate_config)
        assert callable(plugin.cleanup)
    
    def test_plugin_registration_interface(self):
        """Test that plugin registration interface is stable."""
        import rich_click as click
        
        class TestPlugin(PluginBase):
            name = "test"
            description = "Test plugin"
            version = "1.0.0"
            
            def register_commands(self, cli_group: click.Group) -> None:
                @cli_group.command()
                def test_command():
                    """Test command."""
                    pass
        
        # Test that plugin can be instantiated and registered
        plugin = TestPlugin()
        cli_group = click.Group()
        
        # This should not raise any exceptions
        plugin.register_commands(cli_group)
        
        # Verify command was registered
        assert 'test-command' in cli_group.commands or 'test_command' in cli_group.commands


class TestPluginManager:
    """Test PluginManager functionality."""
    
    def test_get_plugin_method(self):
        """Test that get_plugin method works correctly."""
        manager = PluginManager()
        
        # Test getting non-existent plugin
        result = manager.get_plugin("nonexistent")
        assert result is None
        
        # Test with mock plugin
        mock_plugin = MagicMock(spec=PluginBase)
        manager.plugins["test"] = {"instance": mock_plugin}
        
        result = manager.get_plugin("test")
        assert result is mock_plugin
    
    def test_list_plugins_method(self):
        """Test that list_plugins method works correctly."""
        manager = PluginManager()
        
        # Test with empty plugins
        result = manager.list_plugins()
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Test with mock plugin
        mock_plugin = MagicMock(spec=PluginBase)
        mock_plugin.name = "test"
        mock_plugin.description = "Test plugin"
        mock_plugin.version = "1.0.0"
        
        manager.plugins["test"] = {
            "instance": mock_plugin,
            "loaded_from": "entry_point"
        }
        
        result = manager.list_plugins()
        assert len(result) == 1
        assert result[0]["name"] == "test"
        assert result[0]["description"] == "Test plugin"
        assert result[0]["version"] == "1.0.0"
        assert result[0]["loaded_from"] == "entry_point"
    
    def test_register_cli_commands_method(self):
        """Test that register_cli_commands method works correctly."""
        import rich_click as click
        
        manager = PluginManager()
        cli_group = click.Group()
        
        # Test with mock plugin
        mock_plugin = MagicMock(spec=PluginBase)
        manager.plugins["test"] = {"instance": mock_plugin}
        
        # This should not raise any exceptions
        manager.register_cli_commands(cli_group)
        
        # Verify register_commands was called
        mock_plugin.register_commands.assert_called_once_with(cli_group)


class TestBackwardsCompatibility:
    """Test backwards compatibility of plugin system."""
    
    def test_old_plugin_still_works(self):
        """Test that plugins written for old interface still work."""
        import rich_click as click
        
        # Simulate an old plugin that only implements the minimum interface
        class OldStylePlugin(PluginBase):
            name = "old_style"
            description = "Old style plugin"
            version = "1.0.0"
            
            def register_commands(self, cli_group: click.Group) -> None:
                @cli_group.command()
                def old_command():
                    """Old style command."""
                    pass
        
        # Test that old plugin can be loaded and used
        plugin = OldStylePlugin()
        cli_group = click.Group()
        
        # Should work without any issues
        plugin.register_commands(cli_group)
        assert plugin.validate_config() is True  # Default implementation
        plugin.cleanup()  # Should not raise
    
    def test_plugin_config_compatibility(self):
        """Test that plugin configuration remains compatible."""
        # Test that plugins can be initialized with or without config
        plugin1 = PluginBase()
        assert plugin1.config == {}
        
        plugin2 = PluginBase({"test": "value"})
        assert plugin2.config == {"test": "value"}
        
        plugin3 = PluginBase(None)
        assert plugin3.config == {}