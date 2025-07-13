#!/usr/bin/env python3
"""Test the floatctl CLI."""

import os
import sys
from pathlib import Path

# Set up the environment
os.environ["FLOATCTL_CONFIG"] = ""  # Use default config

# Import and run
from floatctl.cli import main

if __name__ == "__main__":
    # Test splitting recent conversations
    test_file = Path.cwd().parent / "floatctl" / "recent-conversations.json"
    if test_file.exists():
        print(f"Testing with: {test_file}")
        sys.argv = ["floatctl", "conversations", "split", str(test_file), "--dry-run"]
        main()
    else:
        print("No test file found, showing help")
        sys.argv = ["floatctl", "--help"]
        main()