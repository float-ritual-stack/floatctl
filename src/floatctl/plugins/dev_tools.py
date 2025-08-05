"""Development tools plugin for FloatCtl plugin development."""

import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm

from floatctl.plugin_manager import PluginBase
from floatctl.core.logging import log_command

console = Console()


class DevToolsPlugin(PluginBase):
    """Plugin providing development tools for FloatCtl plugin development."""
    
    name = "dev-tools"
    description = "Development tools for creating and testing FloatCtl plugins"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register development tool commands."""
        
        @cli_group.group()
        @click.pass_context
        def dev(ctx: click.Context) -> None:
            """Development tools for plugin creation and testing."""
            pass
        
        @dev.command()
        @click.argument("plugin_name")
        @click.option(
            "--output-dir", "-o",
            type=click.Path(path_type=Path),
            default=Path.cwd(),
            help="Output directory for plugin files"
        )
        @click.option(
            "--middleware", "-m",
            is_flag=True,
            help="Create a middleware-style plugin"
        )
        @click.option(
            "--interactive", "-i",
            is_flag=True,
            help="Interactive plugin creation with prompts"
        )
        @click.pass_context
        def scaffold(
            ctx: click.Context,
            plugin_name: str,
            output_dir: Path,
            middleware: bool,
            interactive: bool
        ) -> None:
            """Scaffold a new FloatCtl plugin."""
            logger = log_command("dev.scaffold", {
                "plugin_name": plugin_name,
                "output_dir": str(output_dir),
                "middleware": middleware,
                "interactive": interactive
            })
            
            logger.info("starting_plugin_scaffold")
            
            # Validate plugin name
            if not self._is_valid_plugin_name(plugin_name):
                console.print("[red]Error: Plugin name must be a valid Python identifier[/red]")
                raise click.Abort()
            
            # Interactive mode
            plugin_info = {}
            if interactive:
                plugin_info = self._interactive_plugin_setup(plugin_name)
            else:
                plugin_info = self._default_plugin_info(plugin_name)
            
            # Create plugin files
            plugin_dir = output_dir / f"floatctl_plugin_{plugin_name}"
            self._create_plugin_structure(plugin_dir, plugin_name, plugin_info, middleware)
            
            console.print(Panel(
                f"✅ Plugin '{plugin_name}' scaffolded successfully!\n\n"
                f"📁 Location: {plugin_dir}\n"
                f"📝 Next steps:\n"
                f"   1. cd {plugin_dir}\n"
                f"   2. pip install -e .\n"
                f"   3. Edit {plugin_name}_plugin.py\n"
                f"   4. Run tests: pytest\n"
                f"   5. Test with floatctl: floatctl {plugin_name.replace('_', '-')} --help",
                title="🚀 Plugin Created",
                border_style="green"
            ))
        
        @dev.command()
        @click.argument("plugin_path", type=click.Path(exists=True, path_type=Path))
        @click.pass_context
        def validate(ctx: click.Context, plugin_path: Path) -> None:
            """Validate a plugin's structure and implementation."""
            logger = log_command("dev.validate", {"plugin_path": str(plugin_path)})
            
            logger.info("starting_plugin_validation")
            
            issues = self._validate_plugin(plugin_path)
            
            if not issues:
                console.print("✅ Plugin validation passed!")
            else:
                console.print("❌ Plugin validation failed:")
                for issue in issues:
                    console.print(f"  • {issue}")
        
        @dev.command()
        @click.pass_context
        def list_templates(ctx: click.Context) -> None:
            """List available plugin templates."""
            templates = {
                "basic": "Basic CLI plugin with commands",
                "middleware": "Middleware plugin for data processing pipelines",
                "service": "Service plugin that provides functionality to other plugins",
                "event": "Event-driven plugin that responds to system events"
            }
            
            console.print("📋 Available Plugin Templates:")
            for name, description in templates.items():
                console.print(f"  • [bold]{name}[/bold]: {description}")
    
    def _is_valid_plugin_name(self, name: str) -> bool:
        """Check if plugin name is a valid Python identifier."""
        return name.isidentifier() and not name.startswith('_')
    
    def _interactive_plugin_setup(self, plugin_name: str) -> Dict[str, Any]:
        """Interactive setup for plugin creation."""
        console.print(f"🔧 Setting up plugin: [bold]{plugin_name}[/bold]")
        
        description = Prompt.ask("Plugin description", default=f"A FloatCtl plugin for {plugin_name}")
        author = Prompt.ask("Author name", default="FloatCtl Developer")
        email = Prompt.ask("Author email", default="developer@example.com")
        version = Prompt.ask("Initial version", default="0.1.0")
        
        # Plugin type selection
        console.print("\n📦 Plugin Types:")
        console.print("  1. CLI Plugin - Adds new commands to floatctl")
        console.print("  2. Middleware Plugin - Processes data in pipelines")
        console.print("  3. Service Plugin - Provides services to other plugins")
        console.print("  4. Event Plugin - Responds to system events")
        
        plugin_type = Prompt.ask("Select plugin type", choices=["1", "2", "3", "4"], default="1")
        type_map = {"1": "cli", "2": "middleware", "3": "service", "4": "event"}
        
        has_config = Confirm.ask("Does your plugin need configuration?", default=True)
        has_database = Confirm.ask("Does your plugin need database access?", default=False)
        has_async = Confirm.ask("Does your plugin use async operations?", default=False)
        
        return {
            "description": description,
            "author": author,
            "email": email,
            "version": version,
            "type": type_map[plugin_type],
            "has_config": has_config,
            "has_database": has_database,
            "has_async": has_async
        }
    
    def _default_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """Default plugin information."""
        return {
            "description": f"A FloatCtl plugin for {plugin_name}",
            "author": "FloatCtl Developer",
            "email": "developer@example.com",
            "version": "0.1.0",
            "type": "cli",
            "has_config": True,
            "has_database": False,
            "has_async": False
        }
    
    def _create_plugin_structure(self, plugin_dir: Path, plugin_name: str, info: Dict[str, Any], middleware: bool) -> None:
        """Create the plugin directory structure and files."""
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create package structure
        src_dir = plugin_dir / "src" / f"floatctl_plugin_{plugin_name}"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        tests_dir = plugin_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Create __init__.py files
        (src_dir / "__init__.py").write_text(self._generate_init_file(plugin_name, info))
        (tests_dir / "__init__.py").write_text("")
        
        # Create main plugin file
        plugin_file = src_dir / f"{plugin_name}_plugin.py"
        if middleware or info["type"] == "middleware":
            plugin_file.write_text(self._generate_middleware_plugin(plugin_name, info))
        else:
            plugin_file.write_text(self._generate_cli_plugin(plugin_name, info))
        
        # Create test file
        test_file = tests_dir / f"test_{plugin_name}_plugin.py"
        test_file.write_text(self._generate_test_file(plugin_name, info))
        
        # Create configuration files
        (plugin_dir / "pyproject.toml").write_text(self._generate_pyproject_toml(plugin_name, info))
        (plugin_dir / "README.md").write_text(self._generate_readme(plugin_name, info))
        (plugin_dir / ".gitignore").write_text(self._generate_gitignore())
        
        # Create example config if needed
        if info["has_config"]:
            (plugin_dir / f"{plugin_name}_config.example.yaml").write_text(self._generate_example_config(plugin_name, info))
    
    def _generate_init_file(self, plugin_name: str, info: Dict[str, Any]) -> str:
        """Generate __init__.py file."""
        class_name = self._to_class_name(plugin_name)
        return f'''"""FloatCtl {plugin_name} plugin."""

from .{plugin_name}_plugin import {class_name}Plugin

__version__ = "{info["version"]}"
__all__ = ["{class_name}Plugin"]
'''
    
    def _generate_cli_plugin(self, plugin_name: str, info: Dict[str, Any]) -> str:
        """Generate CLI plugin template."""
        class_name = self._to_class_name(plugin_name)
        
        imports = [
            "import rich_click as click",
            "from rich.console import Console",
            "from floatctl.plugin_manager import PluginBase",
            "from floatctl.core.logging import log_command"
        ]
        
        if info["has_config"]:
            imports.append("from floatctl.core.config import Config")
        
        if info["has_database"]:
            imports.append("from floatctl.core.database import DatabaseManager")
        
        if info["has_async"]:
            imports.append("import asyncio")
        
        async_decorator = "@click.command()\n        @click.pass_context\n        " if not info["has_async"] else "@click.command()\n        @click.pass_context\n        "
        
        return f'''"""{info["description"]}"""

{chr(10).join(imports)}

console = Console()


class {class_name}Plugin(PluginBase):
    """{info["description"]}"""
    
    name = "{plugin_name.replace('_', '-')}"
    description = "{info["description"]}"
    version = "{info["version"]}"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register {plugin_name} commands."""
        
        @cli_group.group()
        @click.pass_context
        def {plugin_name.replace('-', '_')}(ctx: click.Context) -> None:
            """{info["description"]}"""
            pass
        
        {async_decorator}
        {"async " if info["has_async"] else ""}def hello(ctx: click.Context) -> None:
            """Say hello from the {plugin_name} plugin."""
            logger = log_command("{plugin_name}.hello", {{}})
            logger.info("hello_command_executed")
            
            console.print(f"👋 Hello from {{self.name}} plugin!")
            console.print(f"📝 Description: {{self.description}}")
            console.print(f"🔢 Version: {{self.version}}")
        
        @{plugin_name.replace('-', '_')}.command()
        @click.argument("message")
        @click.pass_context
        {"async " if info["has_async"] else ""}def echo(ctx: click.Context, message: str) -> None:
            """Echo a message."""
            logger = log_command("{plugin_name}.echo", {{"message": message}})
            logger.info("echo_command_executed")
            
            console.print(f"🔊 Echo: {{message}}")
        
        # Add the hello command to the group
        {plugin_name.replace('-', '_')}.add_command(hello)
    
    def validate_config(self) -> bool:
        """Validate plugin configuration."""
        # Add your configuration validation logic here
        return True
    
    def cleanup(self) -> None:
        """Cleanup resources when plugin is unloaded."""
        # Add cleanup logic here
        pass
'''
    
    def _generate_middleware_plugin(self, plugin_name: str, info: Dict[str, Any]) -> str:
        """Generate middleware plugin template."""
        class_name = self._to_class_name(plugin_name)
        
        return f'''"""{info["description"]}"""

import rich_click as click
from rich.console import Console
from typing import Dict, Any

from floatctl.plugin_manager import PluginBase
from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext, MiddlewarePhase
from floatctl.core.logging import log_command

console = Console()


class {class_name}Middleware(MiddlewareInterface):
    """Middleware for {plugin_name} processing."""
    
    @property
    def name(self) -> str:
        return "{plugin_name}"
    
    @property
    def priority(self) -> int:
        return 100  # Adjust priority as needed
    
    @property
    def phases(self) -> list:
        return [MiddlewarePhase.PRE_PROCESS, MiddlewarePhase.PROCESS, MiddlewarePhase.POST_PROCESS]
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Pre-processing logic."""
        # Add your pre-processing logic here
        context.metadata["{plugin_name}_processed"] = True
        return context
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Main processing logic."""
        # Add your main processing logic here
        # Example: transform context.data
        return context
    
    async def post_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Post-processing logic."""
        # Add your post-processing logic here
        return context


class {class_name}Plugin(PluginBase):
    """{info["description"]}"""
    
    name = "{plugin_name.replace('_', '-')}"
    description = "{info["description"]}"
    version = "{info["version"]}"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.middleware = {class_name}Middleware()
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register {plugin_name} commands."""
        
        @cli_group.group()
        @click.pass_context
        def {plugin_name.replace('-', '_')}(ctx: click.Context) -> None:
            """{info["description"]}"""
            pass
        
        @{plugin_name.replace('-', '_')}.command()
        @click.pass_context
        def status(ctx: click.Context) -> None:
            """Show {plugin_name} middleware status."""
            logger = log_command("{plugin_name}.status", {{}})
            logger.info("status_command_executed")
            
            console.print(f"🔧 Middleware: {{self.middleware.name}}")
            console.print(f"⚡ Priority: {{self.middleware.priority}}")
            console.print(f"📋 Phases: {{[p.value for p in self.middleware.phases]}}")
    
    def validate_config(self) -> bool:
        """Validate plugin configuration."""
        return True
    
    def cleanup(self) -> None:
        """Cleanup resources when plugin is unloaded."""
        pass
'''
    
    def _generate_test_file(self, plugin_name: str, info: Dict[str, Any]) -> str:
        """Generate test file template."""
        class_name = self._to_class_name(plugin_name)
        
        return f'''"""Tests for {plugin_name} plugin."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from floatctl_plugin_{plugin_name} import {class_name}Plugin


class Test{class_name}Plugin:
    """Test the {class_name}Plugin class."""
    
    @pytest.fixture
    def plugin(self):
        """Create plugin instance for testing."""
        return {class_name}Plugin()
    
    def test_plugin_attributes(self, plugin):
        """Test plugin has correct attributes."""
        assert plugin.name == "{plugin_name.replace('_', '-')}"
        assert plugin.description == "{info["description"]}"
        assert plugin.version == "{info["version"]}"
    
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
        assert "{plugin_name.replace('-', '_')}" in cli_group.commands


class Test{class_name}Commands:
    """Test the plugin commands."""
    
    @pytest.fixture
    def plugin(self):
        """Create plugin instance for testing."""
        return {class_name}Plugin()
    
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
        result = cli_runner.invoke(cli_group, ["{plugin_name.replace('-', '_')}", "hello"])
        assert result.exit_code == 0
    
    def test_echo_command(self, plugin, cli_runner):
        """Test the echo command."""
        import rich_click as click
        
        cli_group = click.Group()
        plugin.register_commands(cli_group)
        
        # Test the command with an argument
        result = cli_runner.invoke(cli_group, ["{plugin_name.replace('-', '_')}", "echo", "test message"])
        assert result.exit_code == 0
'''
    
    def _generate_pyproject_toml(self, plugin_name: str, info: Dict[str, Any]) -> str:
        """Generate pyproject.toml file."""
        return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "floatctl-plugin-{plugin_name}"
version = "{info["version"]}"
description = "{info["description"]}"
authors = [
    {{name = "{info["author"]}", email = "{info["email"]}"}},
]
readme = "README.md"
license = {{text = "MIT"}}
requires-python = ">=3.9"
dependencies = [
    "floatctl",
    "rich-click>=1.6.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]

[project.entry-points."floatctl.plugins"]
{plugin_name.replace('_', '-')} = "floatctl_plugin_{plugin_name}:{self._to_class_name(plugin_name)}Plugin"

[project.urls]
Homepage = "https://github.com/yourusername/floatctl-plugin-{plugin_name}"
Repository = "https://github.com/yourusername/floatctl-plugin-{plugin_name}"
Issues = "https://github.com/yourusername/floatctl-plugin-{plugin_name}/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/floatctl_plugin_{plugin_name}"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.mypy]
python_version = "3.9"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
target-version = "py39"
line-length = 100
select = ["E", "F", "W", "I", "N", "UP", "YTT", "S", "BLE", "FBT", "B", "A", "COM", "C4", "DTZ", "T10", "EM", "EXE", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SIM", "TID", "TCH", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]
ignore = ["S101", "S603", "S607"]

[tool.ruff.per-file-ignores]
"tests/*" = ["S101", "PLR2004", "PLR0913"]
'''
    
    def _generate_readme(self, plugin_name: str, info: Dict[str, Any]) -> str:
        """Generate README.md file."""
        return f'''# FloatCtl {plugin_name.title()} Plugin

{info["description"]}

## Installation

```bash
pip install floatctl-plugin-{plugin_name}
```

## Usage

After installation, the plugin will be automatically available in FloatCtl:

```bash
floatctl {plugin_name.replace('_', '-')} --help
```

### Commands

- `floatctl {plugin_name.replace('_', '-')} hello` - Say hello from the plugin
- `floatctl {plugin_name.replace('_', '-')} echo <message>` - Echo a message

## Configuration

{"Create a configuration file at `~/.floatctl/config.yaml`:" if info["has_config"] else "This plugin does not require configuration."}

{"```yaml" if info["has_config"] else ""}
{f"{plugin_name}:" if info["has_config"] else ""}
{"  # Add your configuration options here" if info["has_config"] else ""}
{"```" if info["has_config"] else ""}

## Development

### Setup

```bash
git clone <your-repo>
cd floatctl-plugin-{plugin_name}
pip install -e ".[dev]"
```

### Testing

```bash
pytest
```

### Code Quality

```bash
ruff check .
mypy .
```

## License

MIT License - see LICENSE file for details.
'''
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore file."""
        return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
'''
    
    def _generate_example_config(self, plugin_name: str, info: Dict[str, Any]) -> str:
        """Generate example configuration file."""
        return f'''# Example configuration for {plugin_name} plugin
{plugin_name}:
  # Enable/disable the plugin
  enabled: true
  
  # Plugin-specific settings
  setting1: "value1"
  setting2: 42
  setting3: true
  
  # Nested configuration
  advanced:
    option1: "advanced_value"
    option2: ["item1", "item2", "item3"]
'''
    
    def _to_class_name(self, plugin_name: str) -> str:
        """Convert plugin name to class name."""
        return ''.join(word.capitalize() for word in plugin_name.split('_'))
    
    def _validate_plugin(self, plugin_path: Path) -> list:
        """Validate plugin structure and implementation."""
        issues = []
        
        # Check if it's a directory
        if not plugin_path.is_dir():
            issues.append("Plugin path must be a directory")
            return issues
        
        # Check for pyproject.toml
        if not (plugin_path / "pyproject.toml").exists():
            issues.append("Missing pyproject.toml file")
        
        # Check for src directory
        src_dirs = list(plugin_path.glob("src/floatctl_plugin_*"))
        if not src_dirs:
            issues.append("Missing src/floatctl_plugin_* directory")
        else:
            src_dir = src_dirs[0]
            
            # Check for __init__.py
            if not (src_dir / "__init__.py").exists():
                issues.append("Missing __init__.py in plugin package")
            
            # Check for main plugin file
            plugin_files = list(src_dir.glob("*_plugin.py"))
            if not plugin_files:
                issues.append("Missing main plugin file (*_plugin.py)")
        
        # Check for tests directory
        if not (plugin_path / "tests").exists():
            issues.append("Missing tests directory")
        
        # Check for README
        if not (plugin_path / "README.md").exists():
            issues.append("Missing README.md file")
        
        return issues