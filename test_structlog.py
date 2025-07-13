#!/usr/bin/env python3
"""Test to isolate structlog logging issue."""

import os

# Set completion environment early
os.environ['_FLOATCTL_COMPLETE'] = 'zsh_complete'

import structlog

# Monkey-patch before any other imports
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

# Replace structlog completely
structlog.get_logger = lambda *args, **kwargs: NullLogger()
structlog.configure(
    processors=[],
    logger_factory=lambda: NullLogger(),
    cache_logger_on_first_use=False,
)

# Now import floatctl components
from floatctl.plugin_manager import PluginManager

print("Testing plugin loading with null logger...")

pm = PluginManager()
pm.load_plugins()

print("Done - no logging should have appeared above this line.")