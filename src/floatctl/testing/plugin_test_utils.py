"""Testing utilities for FloatCtl plugins."""

import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import MagicMock, patch
import pytest

import rich_click as click
from click.testing import CliRunner

from floatctl.plugin_manager import PluginBase
from floatctl.core.database import ProcessingStatus


class MockConfig:
    """Mock configuration for testing."""
    
    def __init__(self, **kwargs):
        self.data_dir = Path(tempfile.gettempdir()) / "floatctl_test"
        self.db_path = self.data_dir / "test.db"
        self.output_dir = self.data_dir / "output"
        self.verbose = False
        self.plugin_config = {}
        
        # Override with provided values
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get plugin-specific configuration."""
        return self.plugin_config.get(plugin_name, {})


class MockDatabaseManager:
    """Mock database manager for testing."""
    
    def __init__(self):
        self.file_runs = []
        self.artifacts = []
        self.queue_items = []
    
    def record_file_run(self, file_path: Path, plugin: str, command: str, **kwargs):
        """Mock file run recording."""
        run = MagicMock()
        run.id = len(self.file_runs) + 1
        run.file_path = str(file_path)
        run.plugin = plugin
        run.command = command
        run.status = ProcessingStatus.PROCESSING
        self.file_runs.append(run)
        return run
    
    def complete_file_run(self, run_id: int, status: ProcessingStatus, **kwargs):
        """Mock file run completion."""
        for run in self.file_runs:
            if run.id == run_id:
                run.status = status
                return True
        return False
    
    def get_file_history(self, file_path: Path, limit: int = 10):
        """Mock file history retrieval."""
        return [run for run in self.file_runs if run.file_path == str(file_path)][:limit]
    
    def queue_file(self, file_path: Path, plugin: str, **kwargs):
        """Mock file queuing."""
        item = MagicMock()
        item.file_path = str(file_path)
        item.plugin = plugin
        self.queue_items.append(item)


class MockEventBus:
    """Mock event bus for testing."""
    
    def __init__(self):
        self.events = []
        self.subscribers = {}
    
    def subscribe(self, event_type: str, callback):
        """Mock event subscription."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    async def emit(self, event_type: str, data: Any = None, **kwargs):
        """Mock event emission."""
        event = {
            "type": event_type,
            "data": data,
            "kwargs": kwargs
        }
        self.events.append(event)
        
        # Call subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                if hasattr(callback, '__call__'):
                    callback(data, **kwargs)


class MockServiceRegistry:
    """Mock service registry for testing."""
    
    def __init__(self):
        self.services = {}
    
    def register(self, name: str, service: Any):
        """Mock service registration."""
        self.services[name] = service
    
    def get(self, name: str) -> Optional[Any]:
        """Mock service retrieval."""
        return self.services.get(name)
    
    def list_services(self) -> List[str]:
        """Mock service listing."""
        return list(self.services.keys())


class PluginTestCase:
    """Base test case for plugin testing."""
    
    def __init__(self):
        self.config = MockConfig()
        self.db_manager = MockDatabaseManager()
        self.event_bus = MockEventBus()
        self.service_registry = MockServiceRegistry()
        self.cli_runner = CliRunner()
    
    def create_plugin(self, plugin_class, config_overrides: Dict[str, Any] = None) -> PluginBase:
        """Create a plugin instance for testing."""
        config = config_overrides or {}
        plugin = plugin_class(config)
        return plugin
    
    def register_plugin_commands(self, plugin: PluginBase) -> click.Group:
        """Register plugin commands and return CLI group."""
        cli_group = click.Group()
        plugin.register_commands(cli_group)
        return cli_group
    
    def run_command(self, cli_group: click.Group, command_args: List[str]):
        """Run a CLI command and return result."""
        return self.cli_runner.invoke(cli_group, command_args)
    
    def assert_command_exists(self, cli_group: click.Group, command_name: str):
        """Assert that a command exists in the CLI group."""
        if not _command_in_group(cli_group, command_name):
            raise AssertionError(f"Command '{command_name}' not found in CLI group")
    
    def assert_command_successful(self, result):
        """Assert that a command ran successfully."""
        assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}: {result.output}"
    
    def assert_plugin_valid(self, plugin: PluginBase):
        """Assert that a plugin is valid."""
        assert hasattr(plugin, 'name'), "Plugin must have a name attribute"
        assert hasattr(plugin, 'description'), "Plugin must have a description attribute"
        assert hasattr(plugin, 'version'), "Plugin must have a version attribute"
        assert hasattr(plugin, 'register_commands'), "Plugin must have register_commands method"
        assert callable(plugin.register_commands), "register_commands must be callable"
        assert plugin.validate_config() is True, "Plugin configuration validation failed"


def create_test_plugin(name: str, description: str = None, version: str = "1.0.0") -> type:
    """Create a test plugin class."""
    
    class TestPlugin(PluginBase):
        def __init__(self, config: Dict[str, Any] = None):
            super().__init__(config)
        
        @property
        def name(self) -> str:
            return name
        
        @property 
        def description(self) -> str:
            return description or f"Test plugin: {name}"
        
        @property
        def version(self) -> str:
            return version
        
        def register_commands(self, cli_group: click.Group) -> None:
            @cli_group.command(name="test-command")
            def test_command():
                """Test command."""
                click.echo(f"Hello from {self.name}")
        
        def validate_config(self) -> bool:
            return True
        
        def cleanup(self) -> None:
            pass
    
    return TestPlugin


def assert_command_registered(cli_group: click.Group, command_name: str):
    """Assert that a command is registered in the CLI group."""
    if not _command_in_group(cli_group, command_name):
        raise AssertionError(f"Command '{command_name}' not registered")


def assert_plugin_valid(plugin: PluginBase):
    """Assert that a plugin meets the basic requirements."""
    assert hasattr(plugin, 'name'), "Plugin must have a name"
    assert hasattr(plugin, 'description'), "Plugin must have a description"
    assert hasattr(plugin, 'version'), "Plugin must have a version"
    assert hasattr(plugin, 'register_commands'), "Plugin must have register_commands method"
    assert callable(plugin.register_commands), "register_commands must be callable"
    assert plugin.validate_config() is True, "Plugin configuration validation failed"


def _command_in_group(cli_group: click.Group, command_name: str) -> bool:
    """Return True if any normalized form of the command exists in the group."""

    candidates = {command_name}

    if "-" in command_name:
        parts = [part for part in command_name.split("-") if part]
        if parts:
            candidates.add(parts[0])
        candidates.add(command_name.replace("-", "_"))
        candidates.add(command_name.replace("-", ""))

    if "_" in command_name:
        parts = [part for part in command_name.split("_") if part]
        if parts:
            candidates.add(parts[0])
        candidates.add(command_name.replace("_", "-"))
        candidates.add(command_name.replace("_", ""))

    return any(candidate in cli_group.commands for candidate in candidates)


# Pytest fixtures for common testing scenarios
@pytest.fixture
def plugin_test_case():
    """Create a PluginTestCase instance."""
    return PluginTestCase()


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return MockConfig()


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    return MockDatabaseManager()


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    return MockEventBus()


@pytest.fixture
def mock_service_registry():
    """Create a mock service registry."""
    return MockServiceRegistry()


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


# Context managers for patching
class MockPluginEnvironment:
    """Context manager for mocking plugin environment."""
    
    def __init__(self, config: MockConfig = None, db_manager: MockDatabaseManager = None):
        self.config = config or MockConfig()
        self.db_manager = db_manager or MockDatabaseManager()
        self.patches = []
    
    def __enter__(self):
        # Patch logging to avoid issues in tests
        self.patches.append(patch('floatctl.core.logging.get_logger'))
        self.patches.append(patch('floatctl.core.logging.log_command'))
        self.patches.append(patch('floatctl.core.logging.log_file_operation'))
        
        for p in self.patches:
            p.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for p in self.patches:
            p.stop()


def with_mock_plugin_environment(config: MockConfig = None, db_manager: MockDatabaseManager = None):
    """Decorator for mocking plugin environment."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with MockPluginEnvironment(config, db_manager):
                return func(*args, **kwargs)
        return wrapper
    return decorator