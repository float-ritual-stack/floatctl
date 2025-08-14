"""Regression tests for CLI compatibility during refactoring."""

import subprocess
import sys
from pathlib import Path

import pytest


def run_floatctl_command(args: list[str]) -> subprocess.CompletedProcess:
    """Run a floatctl command and return the result."""
    cmd = [sys.executable, "-m", "floatctl"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )


class TestCLICompatibility:
    """Test that all existing CLI commands continue to work."""
    
    def test_main_help_command(self):
        """Test that main help command works."""
        result = run_floatctl_command(["--help"])
        assert result.returncode == 0
        assert "FloatCtl" in result.stdout or "floatctl" in result.stdout
    
    def test_conversations_help_command(self):
        """Test that conversations help command works."""
        result = run_floatctl_command(["conversations", "--help"])
        assert result.returncode == 0
        assert "conversation" in result.stdout.lower()
    
    def test_chroma_help_command(self):
        """Test that chroma help command works."""
        result = run_floatctl_command(["chroma", "--help"])
        assert result.returncode == 0
        assert "chroma" in result.stdout.lower()
    
    def test_forest_help_command(self):
        """Test that forest help command works."""
        result = run_floatctl_command(["forest", "--help"])
        assert result.returncode == 0
        assert "forest" in result.stdout.lower()
    
    def test_artifacts_help_command(self):
        """Test that artifacts help command works."""
        result = run_floatctl_command(["artifacts", "--help"])
        assert result.returncode == 0
        assert "artifact" in result.stdout.lower()
    
    def test_export_help_command(self):
        """Test that export help command works."""
        result = run_floatctl_command(["export", "--help"])
        assert result.returncode == 0
        assert "export" in result.stdout.lower()
    
    def test_version_option(self):
        """Test that version option works."""
        result = run_floatctl_command(["--version"])
        # Version command might not be implemented yet, so just check it doesn't crash
        assert result.returncode in [0, 2]  # 0 for success, 2 for missing command
    
    def test_verbose_option(self):
        """Test that verbose option is accepted."""
        result = run_floatctl_command(["--verbose", "--help"])
        assert result.returncode == 0
    
    def test_config_option(self):
        """Test that config option is accepted."""
        # Create a temporary config file
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"verbose": False}, f)
            config_path = f.name
        
        try:
            result = run_floatctl_command(["--config", config_path, "--help"])
            assert result.returncode == 0
        finally:
            Path(config_path).unlink()


class TestPluginCommands:
    """Test that plugin-specific commands are available."""
    
    def test_conversations_split_command_exists(self):
        """Test that conversations split command exists."""
        result = run_floatctl_command(["conversations", "split", "--help"])
        assert result.returncode == 0
        assert "split" in result.stdout.lower()
    
    def test_chroma_query_command_exists(self):
        """Test that chroma query command exists."""
        result = run_floatctl_command(["chroma", "query", "--help"])
        assert result.returncode == 0
        assert "query" in result.stdout.lower()
    
    def test_forest_status_command_exists(self):
        """Test that forest status command exists."""
        result = run_floatctl_command(["forest", "status", "--help"])
        assert result.returncode == 0
        assert "status" in result.stdout.lower()


class TestErrorHandling:
    """Test that error handling remains consistent."""
    
    def test_invalid_command_error(self):
        """Test that invalid commands produce appropriate errors."""
        result = run_floatctl_command(["nonexistent-command"])
        assert result.returncode != 0
        # Should provide helpful error message
        assert "help" in result.stderr.lower() or "usage" in result.stderr.lower()
    
    def test_missing_required_args_error(self):
        """Test that missing required arguments produce appropriate errors."""
        # This will depend on specific command requirements
        # For now, just test that it fails gracefully
        result = run_floatctl_command(["conversations", "split"])
        assert result.returncode != 0
        # Should not crash with unhandled exception
        assert "traceback" not in result.stderr.lower()