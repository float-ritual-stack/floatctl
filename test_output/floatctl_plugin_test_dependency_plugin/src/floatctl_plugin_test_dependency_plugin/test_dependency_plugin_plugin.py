"""A FloatCtl plugin for test_dependency_plugin"""

import os
import rich_click as click
from rich.console import Console
from typing import Dict, Any
from pydantic import Field, validator

from floatctl.plugin_manager import PluginBase, PluginConfigBase
from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext, MiddlewarePhase
from floatctl.core.logging import log_command

console = Console()


class TestDependencyPluginConfig(PluginConfigBase):
    """Configuration model for test dependency plugin."""
    
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum number of retries")
    timeout: float = Field(default=30.0, gt=0, description="Timeout in seconds")
    service_url: str = Field(default="http://localhost:8000", description="Service URL")
    
    @validator('service_url')
    def validate_service_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('service_url must start with http:// or https://')
        return v


class TestDependencyPluginMiddleware(MiddlewareInterface):
    """Middleware for test_dependency_plugin processing."""
    
    @property
    def name(self) -> str:
        return "test_dependency_plugin"
    
    @property
    def priority(self) -> int:
        return 100  # Adjust priority as needed
    
    @property
    def phases(self) -> list:
        return [MiddlewarePhase.PRE_PROCESS, MiddlewarePhase.PROCESS, MiddlewarePhase.POST_PROCESS]
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Pre-processing logic."""
        # Add your pre-processing logic here
        context.metadata["test_dependency_plugin_processed"] = True
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


class TestDependencyPluginPlugin(PluginBase):
    """A FloatCtl plugin for test_dependency_plugin"""
    
    name = "test-dependency-plugin"
    description = "A test plugin that depends on dev-tools and chroma plugins"
    version = "0.1.0"
    dependencies = ["dev-tools", "chroma"]  # Depends on these plugins
    priority = 200  # Load after dependencies
    config_model = TestDependencyPluginConfig
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.middleware = TestDependencyPluginMiddleware()
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register test_dependency_plugin commands."""
        
        @cli_group.group()
        @click.pass_context
        def test_dependency_plugin(ctx: click.Context) -> None:
            """A FloatCtl plugin for test_dependency_plugin"""
            pass
        
        @test_dependency_plugin.command()
        @click.pass_context
        def status(ctx: click.Context) -> None:
            """Show test_dependency_plugin middleware status."""
            logger = log_command("test_dependency_plugin.status", {})
            logger.info("status_command_executed")
            
            console.print(f"🔧 Middleware: {self.middleware.name}")
            console.print(f"⚡ Priority: {self.middleware.priority}")
            console.print(f"📋 Phases: {[p.value for p in self.middleware.phases]}")
            
            # Test dependency access
            dev_tools = self.get_dependency("dev-tools")
            chroma = self.get_dependency("chroma")
            
            console.print(f"🔗 Dev-tools dependency: {'✅ Available' if dev_tools else '❌ Missing'}")
            console.print(f"🔗 Chroma dependency: {'✅ Available' if chroma else '❌ Missing'}")
            
            # Test service access
            test_service = self.get_service("test_service")
            console.print(f"🔧 Test service: {'✅ Available' if test_service else '❌ Not registered'}")
            
            # Show configuration
            console.print(f"⚙️  Max retries: {self.config.max_retries}")
            console.print(f"⏱️  Timeout: {self.config.timeout}s")
            console.print(f"🌐 Service URL: {self.config.service_url}")
            console.print(f"🐛 Debug mode: {'✅ Enabled' if self.config.debug else '❌ Disabled'}")
        
        @test_dependency_plugin.command()
        @click.pass_context
        def register_service(ctx: click.Context) -> None:
            """Register a test service."""
            logger = log_command("test_dependency_plugin.register_service", {})
            logger.info("register_service_command_executed")
            
            # Register a test service
            test_service = {"name": "test_dependency_plugin_service", "version": "1.0.0"}
            self.register_service("test_service", test_service)
            
            console.print("✅ Test service registered successfully!")
            console.print(f"📋 Service details: {test_service}")
    
    def _custom_config_validation(self, config: TestDependencyPluginConfig) -> bool:
        """Custom validation logic for test dependency plugin."""
        # Example: ensure timeout is reasonable for max_retries
        if config.timeout < config.max_retries * 2:
            if not os.environ.get('_FLOATCTL_COMPLETE'):
                log_command("test_dependency_plugin.config_validation", {
                    "warning": "timeout might be too low for max_retries"
                }).warning("config_validation_warning")
        
        return True
    
    def cleanup(self) -> None:
        """Cleanup resources when plugin is unloaded."""
        pass
