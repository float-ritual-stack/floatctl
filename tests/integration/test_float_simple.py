#!/usr/bin/env python3
"""Test the float-simple interface by simulating keyboard input."""

import subprocess
import time
import sys

# Create a test script that will:
# 1. Start float-simple
# 2. Send some keystrokes
# 3. Exit after a few seconds

test_input = """test entry
\x1b[A
\x1b[B
\x03
"""

# Run floatctl float-simple with input
proc = subprocess.Popen(
    ["uv", "run", "floatctl", "float-simple"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send input and get output
stdout, stderr = proc.communicate(input=test_input, timeout=5)

print("STDOUT:")
print(stdout)
print("\nSTDERR:")
print(stderr)
print(f"\nExit code: {proc.returncode}")