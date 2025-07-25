#!/usr/bin/env python3
"""Minimal test to see what's happening with REPL."""

import sys
from pathlib import Path

# Add src to path  
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Just create the REPL and check what it loads
from floatctl.plugins.interactive_repl import InteractiveREPL

print("Creating InteractiveREPL instance...")
repl = InteractiveREPL()

print(f"Loaded {len(repl.entries)} entries")
if repl.entries:
    print("First 5 entries:")
    for i, entry in enumerate(repl.entries[:5]):
        print(f"  {i}: {entry.type} - {entry.content}")
    
    print("\nLast 5 entries:")
    for i, entry in enumerate(repl.entries[-5:], len(repl.entries)-5):
        print(f"  {i}: {entry.type} - {entry.content}")