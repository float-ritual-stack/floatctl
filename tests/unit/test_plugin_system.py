"""Unit tests for the plugin system - focusing on decorator-based plugins."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

import click
from click.testing import CliRunner

from floatctl.plugin_manager import PluginManager, PluginBase, group, command, option, argument
from floatctl.plugins.conversations import ConversationsPlugin


class TestNestedScopePluginSystem:
    """Test the nested scope plugin system."""
    
    def test_plugin_discovery_finds_nested_scope_plugins(self):
        """Test that nested scope plugins are discovered correctly."""
        plugin_manager = PluginManager()
        plugin_manager._discover_entry_point_plugins()
        
        # Should find the conversations plugin
        assert "conversations" in plugin_manager.plugins
        plugin_info = plugin_manager.plugins["conversations"]
        assert plugin_info.state.value == "discovered"
        assert plugin_info.entry_point is not None
    
    def test_nested_scope_plugin_registration(self):
        """Test that nested scope plugins register commands correctly."""
        plugin = ConversationsPlugin()
        
        # Plugin should have required attributes
        assert hasattr(plugin, 'name')
        assert hasattr(plugin, 'description')
        assert hasattr(plugin, 'version')
        assert hasattr(plugin, 'register_commands')
        
        # Plugin should be callable for registration
        assert callable(plugin.register_commands)
        
        # Plugin should have correct metadata
        assert plugin.name == "conversations"
        assert isinstance(plugin.description, str)
        assert isinstance(plugin.version, str)
    
    def test_nested_scope_plugin_command_registration(self):
        """Test that nested scope plugins register commands with Click."""
        plugin = ConversationsPlugin()
        
        # Create a test CLI group
        @click.group()
        def test_cli():
            pass
        
        # Register the plugin commands
        plugin.register_commands(test_cli)
        
        # Should have registered the 'conversations' group
        assert 'conversations' in test_cli.commands
        conversations_group = test_cli.commands['conversations']
        
        # Should have registered the 'split' command under conversations
        assert 'split' in conversations_group.commands
    
    def test_nested_scope_plugin_with_context_access(self):
        """Test that @click.pass_context works with nested scope plugins."""
        plugin = ConversationsPlugin()
        
        # Create a test CLI group with context setup
        @click.group()
        @click.pass_context
        def test_cli(ctx):
            ctx.ensure_object(dict)
            # Mock the config that the conversations plugin expects
            from floatctl.core.config import Config
            ctx.obj["config"] = Config()
        
        # Register the plugin commands
        plugin.register_commands(test_cli)
        
        # Create a test conversations file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {
                "conversations": [
                    {
                        "title": "Test Conversation",
                        "messages": [
                            {"role": "user", "content": "Hello"},
                            {"role": "assistant", "content": "Hi there!"}
                        ]
                    }
                ]
            }
            json.dump(test_data, f)
            test_file = f.name
        
        try:
            # Test that we can invoke the split command without the 'obj' error
            runner = CliRunner()
            result = runner.invoke(test_cli, [
                'conversations', 'split', test_file, '--format', 'markdown', '--dry-run'
            ])
            
            # This should NOT fail with "'ConversationsPlugin' object has no attribute 'obj'"
            assert "'ConversationsPlugin' object has no attribute 'obj'" not in result.output
            assert result.exit_code == 0 or "does not exist" not in result.output
            
        finally:
            Path(test_file).unlink(missing_ok=True)


class TestConversationsPluginIntegration:
    """Integration tests for the conversations plugin specifically."""
    
    def test_conversations_plugin_split_command_execution(self):
        """Test that the conversations split command can be executed."""
        # Create a minimal CLI app like the real one
        @click.group()
        @click.pass_context
        def cli(ctx):
            ctx.ensure_object(dict)
            # Set up the config that conversations plugin expects
            from floatctl.core.config import Config
            ctx.obj["config"] = Config()
        
        # Load and register the conversations plugin
        plugin = ConversationsPlugin()
        plugin.register_commands(cli)
        
        # Create a test conversations file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {
                "conversations": [
                    {
                        "title": "Test Conversation", 
                        "messages": [
                            {"role": "user", "content": "Hello"},
                            {"role": "assistant", "content": "Hi!"}
                        ]
                    }
                ]
            }
            json.dump(test_data, f)
            test_file = f.name
        
        try:
            # Test the actual command execution
            runner = CliRunner()
            result = runner.invoke(cli, [
                'conversations', 'split', test_file, '--format', 'markdown', '--dry-run'
            ])
            
            # Should not fail with the attribute error
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            if result.exception:
                print(f"Exception: {result.exception}")
                import traceback
                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
            
            # The main assertion - should not have the 'obj' attribute error
            assert "'ConversationsPlugin' object has no attribute 'obj'" not in str(result.output)
            assert "'ConversationsPlugin' object has no attribute 'obj'" not in str(result.exception) if result.exception else True
            
        finally:
            Path(test_file).unlink(missing_ok=True)
    
    def test_plugin_register_commands_integration(self):
        """Test that plugin register_commands method works with Click integration."""
        plugin = ConversationsPlugin()
        
        # Create a test CLI group
        @click.group()
        def test_cli():
            pass
        
        # Register the plugin commands - this should not raise any errors
        plugin.register_commands(test_cli)
        
        # Should have registered the 'conversations' group
        assert 'conversations' in test_cli.commands
        conversations_group = test_cli.commands['conversations']
        
        # Should be a Click Group
        assert isinstance(conversations_group, click.Group)
        
        # Should have registered commands under the conversations group
        assert len(conversations_group.commands) > 0
        
        # Should have the 'split' command
        assert 'split' in conversations_group.commands
        
        # Should have the 'history' command  
        assert 'history' in conversations_group.commands