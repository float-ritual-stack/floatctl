"""Structured logging configuration using structlog."""

import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from rich.console import Console

console = Console()


def setup_quiet_logging() -> None:
    """
    Set up minimal logging for initial plugin loading.
    This prevents verbose output during CLI initialization.
    """
    # Configure minimal structlog for quiet operation
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(file=open(os.devnull, "w")),
        cache_logger_on_first_use=True,
    )


def setup_logging(config: Any, log_file: Optional[Path] = None) -> None:
    """
    Configure structured logging with JSON output.
    
    Args:
        config: Configuration object with logging settings
        log_file: Optional path to log file (defaults to floatctl.jsonl in config.data_dir)
    """
    # Determine log file path
    if log_file is None:
        log_dir = Path(config.data_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "floatctl.jsonl"
    
    # Configure structlog processors
    processors = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]
    
    # Add pretty printing for console if in verbose mode
    if config.verbose:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=open(log_file, "a")),
        cache_logger_on_first_use=True,
    )
    
    # Also set up a console logger for important messages
    if config.verbose:
        # In verbose mode, structlog already prints to console
        pass


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog BoundLogger
    """
    import os
    if os.environ.get('_FLOATCTL_COMPLETE'):
        # Return a null logger during completion
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
            def critical(self, *args, **kwargs): pass
            def bind(self, *args, **kwargs): return self
            def unbind(self, *args, **kwargs): return self
            def new(self, *args, **kwargs): return self
            def __call__(self, *args, **kwargs): return self
        return NullLogger()
    return structlog.get_logger(name)


def log_command(
    command: str,
    args: Dict[str, Any],
    plugin: Optional[str] = None,
) -> structlog.BoundLogger:
    """
    Create a logger bound with command context.
    
    Args:
        command: Command being executed
        args: Command arguments
        plugin: Plugin name if applicable
        
    Returns:
        Logger with bound context
    """
    logger = get_logger("floatctl.command")
    return logger.bind(
        command=command,
        args=args,
        plugin=plugin,
    )


def log_file_operation(
    operation: str,
    file_path: Path,
    **kwargs: Any,
) -> structlog.BoundLogger:
    """
    Create a logger bound with file operation context.
    
    Args:
        operation: Type of operation (read, write, process, etc.)
        file_path: Path to file being operated on
        **kwargs: Additional context to bind
        
    Returns:
        Logger with bound context
    """
    logger = get_logger("floatctl.file_op")
    return logger.bind(
        operation=operation,
        file_path=str(file_path),
        file_name=file_path.name,
        **kwargs,
    )


def log_plugin_event(
    plugin: str,
    event: str,
    **kwargs: Any,
) -> structlog.BoundLogger:
    """
    Create a logger bound with plugin event context.
    
    Args:
        plugin: Plugin name
        event: Event type (loaded, error, executed, etc.)
        **kwargs: Additional context to bind
        
    Returns:
        Logger with bound context
    """
    import os
    if os.environ.get('_FLOATCTL_COMPLETE'):
        # Return a null logger during completion
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
            def critical(self, *args, **kwargs): pass
            def bind(self, *args, **kwargs): return self
            def unbind(self, *args, **kwargs): return self
            def new(self, *args, **kwargs): return self
            def __call__(self, *args, **kwargs): return self
        return NullLogger()
    
    logger = get_logger(f"floatctl.plugin.{plugin}")
    return logger.bind(
        plugin=plugin,
        event=event,
        **kwargs,
    )