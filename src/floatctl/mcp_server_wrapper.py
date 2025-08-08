#!/usr/bin/env python3
"""Clean wrapper for MCP server that suppresses all telemetry before any imports."""

import os
import sys
from pathlib import Path

# AGGRESSIVE telemetry suppression BEFORE any imports
os.environ.update({
    'MCP_SERVER_MODE': '1',
    'ANONYMIZED_TELEMETRY': 'False',
    'ALLOW_RESET': 'False',
    'CHROMA_SERVER_NOFILE': '1',
    'POSTHOG_DISABLED': '1',
    'POSTHOG_API_KEY': '',
    'POSTHOG_HOST': '',
    'REQUESTS_CA_BUNDLE': '',
    'CURL_CA_BUNDLE': '',
    'PYTHONWARNINGS': 'ignore',
    'PYTHONIOENCODING': 'utf-8'
})

# Disable all logging before any imports
import logging
logging.disable(logging.CRITICAL)

# Monkey patch print to suppress any print statements
original_print = print
def silent_print(*args, **kwargs):
    pass

# Only restore print for MCP protocol messages
def mcp_print(*args, **kwargs):
    text = ' '.join(str(arg) for arg in args)
    if text.startswith('{"jsonrpc"') or text.startswith('Content-Length:'):
        original_print(*args, **kwargs)

# Replace print globally
import builtins
builtins.print = silent_print

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# Now import and run the actual server
if __name__ == "__main__":
    try:
        # Import the actual MCP server
        from floatctl.mcp_server import mcp
        
        # Restore print for MCP protocol only
        builtins.print = mcp_print
        
        # Run the server
        mcp.run(transport='stdio')
        
    except Exception as e:
        # Silent exit on any error
        sys.exit(1)