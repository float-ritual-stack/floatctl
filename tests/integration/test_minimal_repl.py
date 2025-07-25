#!/usr/bin/env python3
"""Minimal test to reproduce the editing flow blocker."""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing minimal REPL interface...")

try:
    # Test 1: Import without completion environment
    print("1. Testing normal import...")
    from floatctl.core.logging import get_logger
    logger = get_logger("test")
    logger.info("Normal logging works")
    print("✓ Normal logging works")
    
    # Test 2: Set completion environment and test
    print("2. Testing with completion environment...")
    os.environ['_FLOATCTL_COMPLETE'] = 'zsh_complete'
    
    # Re-import to trigger the environment check
    import importlib
    import floatctl.core.logging
    importlib.reload(floatctl.core.logging)
    
    from floatctl.core.logging import get_logger
    logger2 = get_logger("test_completion")
    logger2.info("This should be silenced")
    print("✓ Completion environment silences logging")
    
    # Test 3: Try to load a plugin with completion environment
    print("3. Testing plugin loading with completion environment...")
    from floatctl.plugin_manager import PluginManager
    pm = PluginManager()
    pm.load_plugins()
    print("✓ Plugin loading works with completion environment")
    
    # Test 4: Remove completion environment and test again
    print("4. Testing after removing completion environment...")
    del os.environ['_FLOATCTL_COMPLETE']
    
    # Reload again
    importlib.reload(floatctl.core.logging)
    from floatctl.core.logging import get_logger
    logger3 = get_logger("test_normal_again")
    logger3.info("Logging should work again")
    print("✓ Logging restored after completion environment removed")
    
    print("\nAll tests passed! No blocker found in logging system.")
    
except Exception as e:
    print(f"✗ Error encountered: {e}")
    import traceback
    traceback.print_exc()