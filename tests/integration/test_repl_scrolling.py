#!/usr/bin/env python3
"""Test script to verify REPL scrolling functionality."""

import json
from pathlib import Path
from datetime import datetime

# Create test data with many entries to test scrolling
test_entries = []

# Add 50 test entries to force scrolling
for i in range(50):
    entry = {
        'id': f'test-{i}',
        'content': f'Test entry {i} - This is a test entry to verify scrolling works',
        'type': 'log' if i % 3 == 0 else 'code' if i % 3 == 1 else 'output',
        'timestamp': datetime.now().isoformat(),
        'indent': i % 3,  # Vary indentation
        'is_code': i % 3 == 1,
        'language': 'python'
    }
    test_entries.append(entry)

# Save to REPL data file
data_dir = Path.home() / '.floatctl' / 'repl_notes'
data_dir.mkdir(parents=True, exist_ok=True)
data_file = data_dir / 'notes.json'

# Write test data
with open(data_file, 'w') as f:
    json.dump(test_entries, f, indent=2)

print(f"Created {len(test_entries)} test entries in {data_file}")
print("\nTo test scrolling:")
print("1. Run: uv run floatctl repl")
print("2. Use Alt+↑/↓ to navigate entries")
print("3. Use Page Up/Page Down to scroll viewport")
print("4. Use Home/End to jump to start/end")
print("5. Notice scroll indicators showing entries above/below")
print("\nThe selected entry should always remain visible!")