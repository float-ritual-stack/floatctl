#!/usr/bin/env python3
"""Debug the REPL to see what's happening."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from floatctl.plugins.interactive_repl import InteractiveREPL

# Create instance
repl = InteractiveREPL()

print(f"Loaded {len(repl.entries)} entries")
print(f"Viewport: top={repl.viewport_top}, height={repl.viewport_height}")
print(f"Selected: {repl.selected}")

# Test viewport calculations
if repl.entries:
    print(f"\nFirst 3 entries:")
    for i, entry in enumerate(repl.entries[:3]):
        print(f"  {i}: {entry.type} - {entry.content[:50]}...")

# Test scrolling
print(f"\nTesting scroll_viewport(5)...")
repl.scroll_viewport(5)
print(f"After scroll: viewport_top={repl.viewport_top}")

# Test selection movement
print(f"\nTesting move_selection(1)...")
repl.move_selection(1)
print(f"After move: selected={repl.selected}, viewport_top={repl.viewport_top}")