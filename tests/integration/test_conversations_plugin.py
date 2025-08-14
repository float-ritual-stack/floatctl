"""Integration tests for the conversations plugin."""

import pytest
import tempfile
import json
from pathlib import Path

from click.testing import CliRunner

from floatctl.cli import create_cli_app


class TestConversationsPluginIntegration:
    """End-to-end integration tests for the conversations plugin."""
    
    def test_conversations_command_is_available(self):
        """Test that the conversations command is available in the CLI."""
        cli_app = create_cli_app()
        
        # The conversations command should be available
        assert 'conversations' in cli_app.commands, f"Available commands: {list(cli_app.commands.keys())}"
    
    def test_conversations_split_command_exists(self):
        """Test that the conversations split subcommand exists."""
        cli_app = create_cli_app()
        
        # Get the conversations group
        conversations_group = cli_app.commands.get('conversations')
        assert conversations_group is not None, "conversations command should exist"
        
        # The split command should be available
        assert 'split' in conversations_group.commands, f"Available subcommands: {list(conversations_group.commands.keys())}"
    
    def test_conversations_split_with_real_file(self):
        """Test the conversations split command with a real test file."""
        cli_app = create_cli_app()
        
        # Create a test conversations file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {
                "conversations": [
                    {
                        "title": "Test Conversation",
                        "create_time": "2024-01-01T12:00:00Z",
                        "messages": [
                            {
                                "role": "user", 
                                "content": "Hello, this is a test message.",
                                "create_time": "2024-01-01T12:00:00Z"
                            },
                            {
                                "role": "assistant",
                                "content": "Hi! This is a test response.",
                                "create_time": "2024-01-01T12:00:01Z"
                            }
                        ]
                    }
                ]
            }
            json.dump(test_data, f)
            test_file = f.name
        
        try:
            # Test the actual command execution
            runner = CliRunner()
            result = runner.invoke(cli_app, [
                'conversations', 'split', test_file, '--format', 'markdown', '--dry-run'
            ])
            
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            if result.exception:
                print(f"Exception: {result.exception}")
                import traceback
                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
            
            # The main test - should not fail with the specific attribute error
            error_message = "'ConversationsPlugin' object has no attribute 'obj'"
            
            # Check both output and exception
            assert error_message not in str(result.output), f"Found attribute error in output: {result.output}"
            
            if result.exception:
                assert error_message not in str(result.exception), f"Found attribute error in exception: {result.exception}"
            
            # Should exit successfully (or at least not with the attribute error)
            if result.exit_code != 0:
                # If it failed, it should be for a different reason than the attribute error
                assert error_message not in str(result.output)
                assert not result.exception or error_message not in str(result.exception)
            
        finally:
            Path(test_file).unlink(missing_ok=True)
    
    def test_conversations_split_help_works(self):
        """Test that the conversations split --help command works."""
        cli_app = create_cli_app()
        
        runner = CliRunner()
        result = runner.invoke(cli_app, ['conversations', 'split', '--help'])
        
        print(f"Help exit code: {result.exit_code}")
        print(f"Help output: {result.output}")
        
        # Help should work without the attribute error
        error_message = "'ConversationsPlugin' object has no attribute 'obj'"
        assert error_message not in str(result.output)
        assert not result.exception or error_message not in str(result.exception)
        
        # Help should show the command description
        assert "Split a conversations export file" in result.output or "conversation" in result.output.lower()
    
    def test_full_cli_integration_with_plugin_loading(self):
        """Test the full CLI integration including plugin loading."""
        # This tests the actual plugin loading mechanism
        from floatctl.cli import load_and_register_plugins
        
        # Create a CLI app
        cli_app = create_cli_app()
        
        # Load plugins (this is what main() does)
        plugin_manager = load_and_register_plugins(cli_app)
        
        # Should have loaded the conversations plugin
        assert "conversations" in plugin_manager.plugins
        plugin_info = plugin_manager.plugins["conversations"]
        
        # Plugin should be in active state
        assert plugin_info.state.value == "active", f"Plugin state: {plugin_info.state.value}, error: {plugin_info.error}"
        
        # Should have an instance
        assert plugin_info.instance is not None
        
        # CLI should have the conversations command
        assert 'conversations' in cli_app.commands
        
        # Test that we can invoke a command
        runner = CliRunner()
        result = runner.invoke(cli_app, ['conversations', '--help'])
        
        # Should not have the attribute error
        error_message = "'ConversationsPlugin' object has no attribute 'obj'"
        assert error_message not in str(result.output)
        assert not result.exception or error_message not in str(result.exception)