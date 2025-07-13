"""Configuration management using Pydantic."""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, field_validator
import yaml
import json

from floatctl.core.logging import get_logger

logger = get_logger(__name__)


class Config(BaseModel):
    """Main configuration model for FloatCtl."""
    
    # Core settings
    verbose: bool = Field(default=False, description="Enable verbose output")
    output_dir: Path = Field(default=Path("./output"), description="Default output directory")
    data_dir: Path = Field(
        default=Path.home() / ".floatctl",
        description="Directory for FloatCtl data (database, logs, etc.)"
    )
    
    # Database settings
    db_path: Path = Field(
        default_factory=lambda: Path.home() / ".floatctl" / "floatctl.db",
        description="SQLite database path"
    )
    
    # Plugin settings
    plugin_dirs: List[Path] = Field(
        default_factory=lambda: [Path.home() / ".floatctl" / "plugins"],
        description="Directories to search for plugins"
    )
    disabled_plugins: List[str] = Field(
        default_factory=list,
        description="List of plugins to disable"
    )
    
    # Processing settings
    batch_size: int = Field(default=100, description="Default batch size for processing")
    max_workers: int = Field(default=4, description="Maximum parallel workers")
    
    # File handling
    ignore_patterns: List[str] = Field(
        default_factory=lambda: [".*", "__pycache__", "*.pyc"],
        description="File patterns to ignore"
    )
    
    # Plugin-specific settings
    plugin_config: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Plugin-specific configuration"
    )
    
    @field_validator("output_dir", "data_dir", mode="after")
    def expand_paths(cls, v: Path) -> Path:
        """Expand user paths and make absolute."""
        return v.expanduser().resolve()
    
    
    @field_validator("plugin_dirs", mode="after")
    def expand_plugin_dirs(cls, v: List[Path]) -> List[Path]:
        """Expand and resolve plugin directories."""
        return [p.expanduser().resolve() for p in v]
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin."""
        return self.plugin_config.get(plugin_name, {})
    
    def to_yaml(self) -> str:
        """Export configuration to YAML."""
        # Convert paths to strings for serialization
        data = self.model_dump()
        for key in ["output_dir", "data_dir", "db_path"]:
            if data.get(key):
                data[key] = str(data[key])
        if "plugin_dirs" in data:
            data["plugin_dirs"] = [str(p) for p in data["plugin_dirs"]]
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    def to_json(self) -> str:
        """Export configuration to JSON."""
        return self.model_dump_json(indent=2)
    
    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """Load configuration from file."""
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        content = path.read_text()
        
        if path.suffix.lower() in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        elif path.suffix.lower() == ".json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported configuration file format: {path.suffix}")
        
        return cls(**data)
    
    def save(self, path: Path) -> None:
        """Save configuration to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.suffix.lower() in [".yaml", ".yml"]:
            content = self.to_yaml()
        elif path.suffix.lower() == ".json":
            content = self.to_json()
        else:
            raise ValueError(f"Unsupported configuration file format: {path.suffix}")
        
        path.write_text(content)
        logger.info("config_saved", path=str(path))


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from various sources with precedence:
    1. Command-line specified config file
    2. Environment variable FLOATCTL_CONFIG
    3. Project config (.floatctl.yaml in current directory)
    4. User config (~/.floatctl/config.yaml)
    5. Default configuration
    """
    # Try command-line specified config first
    if config_path:
        logger.info("loading_config", source="cli", path=str(config_path))
        return Config.from_file(config_path)
    
    # Try environment variable
    env_config = os.environ.get("FLOATCTL_CONFIG")
    if env_config:
        env_path = Path(env_config)
        if env_path.exists():
            logger.info("loading_config", source="env", path=str(env_path))
            return Config.from_file(env_path)
    
    # Try project config
    project_configs = [".floatctl.yaml", ".floatctl.yml", ".floatctl.json"]
    for config_name in project_configs:
        project_path = Path.cwd() / config_name
        if project_path.exists():
            logger.info("loading_config", source="project", path=str(project_path))
            return Config.from_file(project_path)
    
    # Try user config
    user_configs = [
        Path.home() / ".floatctl" / "config.yaml",
        Path.home() / ".floatctl" / "config.yml",
        Path.home() / ".floatctl" / "config.json",
    ]
    for user_path in user_configs:
        if user_path.exists():
            logger.info("loading_config", source="user", path=str(user_path))
            return Config.from_file(user_path)
    
    # Return default configuration
    logger.info("loading_config", source="default")
    config = Config()
    
    # Create default directories
    config.data_dir.mkdir(parents=True, exist_ok=True)
    for plugin_dir in config.plugin_dirs:
        plugin_dir.mkdir(parents=True, exist_ok=True)
    
    return config


def merge_configs(base: Config, override: Dict[str, Any]) -> Config:
    """Merge configuration with overrides."""
    data = base.model_dump()
    
    # Deep merge for nested dictionaries
    for key, value in override.items():
        if key in data and isinstance(data[key], dict) and isinstance(value, dict):
            data[key] = {**data[key], **value}
        else:
            data[key] = value
    
    return Config(**data)