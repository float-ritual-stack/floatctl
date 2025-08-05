"""Tests for the config module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

from floatctl.core.config import Config, load_config


class TestConfig:
    """Test the Config class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.output_dir == Path("output")
        assert config.data_dir == Path.home() / ".floatctl"
        assert config.db_path == Path.home() / ".floatctl" / "floatctl.db"
        assert config.verbose is False
        assert config.batch_size == 100
        assert config.max_workers == 4
        assert config.chroma_path == Path("/Users/evan/github/chroma-data")
        assert config.plugin_dirs == [Path.home() / ".floatctl" / "plugins"]
        assert config.disabled_plugins == []
        assert config.ignore_patterns == [".*", "__pycache__", "*.pyc"]
        assert config.plugin_config == {}
    
    def test_config_with_custom_values(self):
        """Test configuration with custom values."""
        config = Config(
            output_dir=Path("/custom/output"),
            data_dir=Path("/custom/data"),
            db_path=Path("/custom/db.sqlite"),
            verbose=True,
            batch_size=50,
            max_workers=8,
            chroma_path=Path("/custom/chroma"),
            plugin_dirs=[Path("/custom/plugins")],
            disabled_plugins=["test_plugin"],
            ignore_patterns=["*.tmp"],
            plugin_config={"test": {"key": "value"}}
        )
        
        assert config.output_dir == Path("/custom/output")
        assert config.data_dir == Path("/custom/data")
        assert config.db_path == Path("/custom/db.sqlite")
        assert config.verbose is True
        assert config.batch_size == 50
        assert config.max_workers == 8
        assert config.chroma_path == Path("/custom/chroma")
        assert config.plugin_dirs == [Path("/custom/plugins")]
        assert config.disabled_plugins == ["test_plugin"]
        assert config.ignore_patterns == ["*.tmp"]
        assert config.plugin_config == {"test": {"key": "value"}}
    
    def test_get_plugin_config(self):
        """Test getting plugin-specific configuration."""
        config = Config(plugin_config={"test_plugin": {"key": "value"}})
        
        plugin_config = config.get_plugin_config("test_plugin")
        assert plugin_config == {"key": "value"}
        
        # Non-existent plugin should return empty dict
        empty_config = config.get_plugin_config("nonexistent")
        assert empty_config == {}
    
    def test_to_yaml(self):
        """Test exporting configuration to YAML."""
        config = Config(verbose=True, batch_size=50)
        yaml_str = config.to_yaml()
        
        assert isinstance(yaml_str, str)
        assert "verbose: true" in yaml_str
        assert "batch_size: 50" in yaml_str
    
    def test_to_json(self):
        """Test exporting configuration to JSON."""
        config = Config(verbose=True, batch_size=50)
        json_str = config.to_json()
        
        assert isinstance(json_str, str)
        assert '"verbose": true' in json_str
        assert '"batch_size": 50' in json_str


class TestLoadConfig:
    """Test the load_config function."""
    
    def test_load_config_no_files(self):
        """Test loading config when no config files exist."""
        with patch('floatctl.core.config.Path.exists', return_value=False):
            with patch('floatctl.core.config.Path.mkdir'):  # Mock directory creation
                config = load_config()
            
        # Should return default config
        assert isinstance(config, Config)
        assert config.output_dir == Path("output")
    
    def test_load_config_from_env_var(self):
        """Test loading config from environment variable."""
        config_data = {
            "output_dir": "/env/output",
            "verbose": True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            with patch.dict('os.environ', {'FLOATCTL_CONFIG': temp_path}):
                config = load_config()
            
            assert config.output_dir == Path("/env/output")
            assert config.verbose is True
        finally:
            Path(temp_path).unlink()
    
    def test_load_config_with_explicit_path(self):
        """Test loading config from explicit path."""
        config_data = {
            "batch_size": 200,
            "max_workers": 8
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)
        
        try:
            config = load_config(config_path=temp_path)
            
            assert config.batch_size == 200
            assert config.max_workers == 8
        finally:
            temp_path.unlink()
    
    def test_load_config_nonexistent_file(self):
        """Test handling of non-existent config file."""
        nonexistent_path = Path("/nonexistent/config.json")
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            load_config(config_path=nonexistent_path)


class TestMergeConfigs:
    """Test the merge_configs function."""
    
    def test_merge_configs_basic(self):
        """Test basic config merging."""
        from floatctl.core.config import merge_configs
        
        base = Config(verbose=False, batch_size=100)
        override = {"verbose": True, "max_workers": 8}
        
        merged = merge_configs(base, override)
        
        assert merged.verbose is True
        assert merged.batch_size == 100  # Unchanged
        assert merged.max_workers == 8  # Overridden
    
    def test_merge_configs_nested(self):
        """Test merging nested configuration."""
        from floatctl.core.config import merge_configs
        
        base = Config(plugin_config={"plugin1": {"key1": "value1"}})
        override = {"plugin_config": {"plugin2": {"key2": "value2"}}}
        
        merged = merge_configs(base, override)
        
        # Should merge at the top level
        expected = {"plugin1": {"key1": "value1"}, "plugin2": {"key2": "value2"}}
        assert merged.plugin_config == expected