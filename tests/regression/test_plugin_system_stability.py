"""
Regression tests to prevent plugin system breakage.

These tests ensure the core plugin functionality remains stable
and prevent regressions that break basic conversation processing.
"""

import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner

from floatctl.core.config import Config
from floatctl.core.database import DatabaseManager
from floatctl.plugins.conversations import ConversationsPlugin


class TestPluginSystemStability:
    """Critical regression tests for plugin system stability."""
    
    def test_conversations_plugin_registration(self):
        """Test that conversations plugin registers commands correctly."""
        plugin = ConversationsPlugin()
        
        # Verify plugin has required attributes
        assert hasattr(plugin, 'name')
        assert hasattr(plugin, 'description') 
        assert hasattr(plugin, 'version')
        assert hasattr(plugin, 'register_commands')
        
        # Verify plugin can be instantiated
        assert plugin.name == "conversations"
        assert isinstance(plugin.description, str)
        assert isinstance(plugin.version, str)
    
    def test_database_manager_has_execute_sql(self):
        """Test that DatabaseManager has execute_sql method (critical for consciousness middleware)."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db_manager = DatabaseManager(db_path)
            
            # Verify execute_sql method exists
            assert hasattr(db_manager, 'execute_sql')
            assert callable(db_manager.execute_sql)
            
            # Test basic SQL execution
            result = db_manager.execute_sql("SELECT 1 as test")
            assert result is not None
            
        finally:
            db_path.unlink(missing_ok=True)
    
    def test_plugin_command_discovery(self):
        """Test that plugin commands are discoverable via CLI."""
        from floatctl.cli import create_cli_app
        
        runner = CliRunner()
        cli_app = create_cli_app()
        
        # Test main help shows conversations plugin
        result = runner.invoke(cli_app, ['--help'])
        assert result.exit_code == 0
        assert 'conversations' in result.output
        
        # Test conversations plugin help works
        result = runner.invoke(cli_app, ['conversations', '--help'])
        assert result.exit_code == 0
        assert 'split' in result.output
        assert 'history' in result.output
    
    def test_basic_conversation_splitting_works(self):
        """Test that basic conversation splitting functionality works."""
        from floatctl.cli import create_cli_app
        
        # Create minimal test conversation data
        test_data = {
            "conversations": [
                {
                    "id": "test-123",
                    "title": "Test Conversation",
                    "create_time": "2025-08-08T12:00:00Z",
                    "mapping": {
                        "msg1": {
                            "id": "msg1",
                            "message": {
                                "id": "msg1",
                                "content": {
                                    "content_type": "text",
                                    "parts": ["Hello world"]
                                },
                                "role": "user",
                                "create_time": "2025-08-08T12:00:00Z"
                            }
                        }
                    }
                }
            ]
        }
        
        runner = CliRunner()
        cli_app = create_cli_app()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(test_data, f)
            test_file = Path(f.name)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Test conversation splitting (without consciousness analysis)
                result = runner.invoke(cli_app, [
                    'conversations', 'split', 
                    str(test_file),
                    '--output-dir', temp_dir
                ])
                
                # Should succeed without errors
                assert result.exit_code == 0, f"Command failed with output: {result.output}"
                assert "Successfully processed" in result.output
                
                # Should create output file
                output_files = list(Path(temp_dir).glob("*.json"))
                assert len(output_files) > 0, "No output files created"
                
            finally:
                test_file.unlink(missing_ok=True)
    
    def test_plugin_scaffolding_generates_correct_pattern(self):
        """Test that plugin scaffolding generates the correct nested scope pattern."""
        from floatctl.plugins.dev_tools import DevToolsPlugin
        
        plugin = DevToolsPlugin()
        
        # Generate a test plugin template
        template = plugin._generate_cli_plugin("test_plugin", {
            "description": "Test plugin",
            "version": "1.0.0",
            "has_config": False,
            "has_database": False,
            "has_async": False,
            "type": "cli"
        })
        
        # Verify the template uses nested scope pattern
        assert "def register_commands(self, cli_group: click.Group)" in template
        assert "@test_plugin.command()" in template
        assert "def hello(ctx: click.Context)" in template
        assert "def echo(ctx: click.Context, message: str)" in template
        
        # Verify it does NOT use the broken manual add_command pattern
        assert "add_command(hello)" not in template


class TestCriticalFunctionality:
    """Tests for functionality that must never break."""
    
    def test_floatctl_help_works(self):
        """Test that basic floatctl --help works."""
        from floatctl.cli import create_cli_app
        
        runner = CliRunner()
        cli_app = create_cli_app()
        result = runner.invoke(cli_app, ['--help'])
        
        assert result.exit_code == 0
        assert 'FloatCtl' in result.output or 'floatctl' in result.output
    
    def test_conversations_commands_exist(self):
        """Test that core conversation commands exist and are accessible."""
        from floatctl.cli import create_cli_app
        
        runner = CliRunner()
        cli_app = create_cli_app()
        
        # Test conversations help
        result = runner.invoke(cli_app, ['conversations', '--help'])
        assert result.exit_code == 0
        
        # Test split command help
        result = runner.invoke(cli_app, ['conversations', 'split', '--help'])
        assert result.exit_code == 0
        
        # Test history command help  
        result = runner.invoke(cli_app, ['conversations', 'history', '--help'])
        assert result.exit_code == 0
    
    def test_database_operations_work(self):
        """Test that basic database operations work."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db_manager = DatabaseManager(db_path)
            
            # Test basic database operations
            test_file = Path("/tmp/test.txt")
            
            # Record a file run
            file_run = db_manager.record_file_run(
                test_file, 
                "test_plugin", 
                "test_command"
            )
            assert file_run.id is not None
            
            # Complete the file run
            from floatctl.core.database import ProcessingStatus
            db_manager.complete_file_run(
                file_run.id,
                ProcessingStatus.COMPLETED,
                items_processed=1
            )
            
            # Get file history
            history = db_manager.get_file_history(test_file)
            assert len(history) == 1
            assert history[0].status.value == "completed"
            
        finally:
            db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])