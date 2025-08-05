"""A FloatCtl plugin for test_example"""

import rich_click as click
from rich.console import Console
from floatctl.plugin_manager import PluginBase
from floatctl.core.logging import log_command
from floatctl.core.config import Config

console = Console()


class TestExamplePlugin(PluginBase):
    """A FloatCtl plugin for test_example"""
    
    name = "test-example"
    description = "A FloatCtl plugin for test_example"
    version = "0.1.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register test_example commands."""
        
        @cli_group.group()
        @click.pass_context
        def test_example(ctx: click.Context) -> None:
            """A FloatCtl plugin for test_example"""
            pass
        
        @click.command()
        @click.pass_context
        
        def hello(ctx: click.Context) -> None:
            """Say hello from the test_example plugin."""
            logger = log_command("test_example.hello", {})
            logger.info("hello_command_executed")
            
            console.print(f"👋 Hello from {self.name} plugin!")
            console.print(f"📝 Description: {self.description}")
            console.print(f"🔢 Version: {self.version}")
        
        @test_example.command()
        @click.argument("message")
        @click.pass_context
        def echo(ctx: click.Context, message: str) -> None:
            """Echo a message."""
            logger = log_command("test_example.echo", {"message": message})
            logger.info("echo_command_executed")
            
            console.print(f"🔊 Echo: {message}")
        
        # Add the hello command to the group
        test_example.add_command(hello)
    
    def validate_config(self) -> bool:
        """Validate plugin configuration."""
        # Add your configuration validation logic here
        return True
    
    def cleanup(self) -> None:
        """Cleanup resources when plugin is unloaded."""
        # Add cleanup logic here
        pass
