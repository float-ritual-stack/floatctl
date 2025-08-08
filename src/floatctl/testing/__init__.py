"""Testing utilities for FloatCtl plugins."""

from .plugin_test_utils import (
    PluginTestCase,
    MockConfig,
    MockDatabaseManager,
    MockEventBus,
    MockServiceRegistry,
    create_test_plugin,
    assert_command_registered,
    assert_plugin_valid
)

from .middleware_test_utils import (
    MiddlewareTestCase,
    MockMiddlewareContext,
    create_test_middleware,
    assert_middleware_phases,
    run_middleware_pipeline
)

from .fixtures import (
    temp_config_dir,
    mock_logger,
    sample_conversation_data,
    sample_file_data
)

__all__ = [
    # Plugin testing
    "PluginTestCase",
    "MockConfig", 
    "MockDatabaseManager",
    "MockEventBus",
    "MockServiceRegistry",
    "create_test_plugin",
    "assert_command_registered",
    "assert_plugin_valid",
    
    # Middleware testing
    "MiddlewareTestCase",
    "MockMiddlewareContext",
    "create_test_middleware", 
    "assert_middleware_phases",
    "run_middleware_pipeline",
    
    # Fixtures
    "temp_config_dir",
    "mock_logger",
    "sample_conversation_data",
    "sample_file_data"
]