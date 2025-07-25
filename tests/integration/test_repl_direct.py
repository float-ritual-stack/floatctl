#!/usr/bin/env python3
"""Test REPL directly to understand the issue."""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Check what's in the file
data_file = Path.home() / '.floatctl' / 'repl_notes' / 'notes.json'
print(f"Reading from: {data_file}")

with open(data_file) as f:
    data = json.load(f)
    print(f"File contains {len(data)} entries")
    if data:
        print(f"First entry: {data[0]}")
        print(f"Last entry: {data[-1]}")

# Now test loading in REPL
from floatctl.plugins.interactive_repl import Entry

# Test Entry.from_dict
try:
    entry = Entry.from_dict(data[0])
    print(f"\nSuccessfully created Entry: {entry.type} - {entry.content[:30]}...")
except Exception as e:
    print(f"\nError creating Entry: {e}")
    import traceback
    traceback.print_exc()