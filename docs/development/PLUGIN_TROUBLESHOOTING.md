# Plugin Troubleshooting Guide

TODO: Update this guide to reflect the nested scope architecture.

For now, see AGENTS.md for the correct plugin development patterns.

## Most Common Issue

**Commands defined outside `register_commands()` method won't work!**

All commands must be defined INSIDE the `register_commands()` method using the nested scope pattern.

## Quick Fix

If your plugin isn't working:

1. Check that all commands are inside `register_commands()`
2. Run the regression tests: `pytest tests/regression/test_plugin_system_stability.py`
3. Use plugin scaffolding: `floatctl dev scaffold my_plugin`

## Architecture Decision

We use the nested scope pattern (not decorators) because:
- ✅ Works reliably with Click contexts
- ✅ Simple to understand
- ✅ LLM-friendly
- ✅ Debuggable

**Never use decorator-based registration** - it breaks Click context passing.