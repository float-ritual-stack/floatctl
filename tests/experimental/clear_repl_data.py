#!/usr/bin/env python3
"""Clear REPL data for a fresh start."""

import shutil
from pathlib import Path

data_dir = Path.home() / '.floatctl' / 'repl_notes'

if data_dir.exists():
    shutil.rmtree(data_dir)
    print(f"Cleared {data_dir}")
else:
    print(f"{data_dir} doesn't exist")

# Recreate empty directory
data_dir.mkdir(parents=True, exist_ok=True)
print(f"Created fresh {data_dir}")
print("\nYou can now run: uv run floatctl repl")
print("It will start with no entries, and you can test:")
print("- Type entries and press Enter")
print("- Use Alt+↑/↓ to navigate")
print("- Tab/Shift+Tab to indent")
print("- Ctrl+R to toggle REPL mode")