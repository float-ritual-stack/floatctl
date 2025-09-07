#!/Users/evan/projects/float-workspace/tools/floatctl-py/.venv/bin/python
"""Main entry point for the Evna Context Concierge MCP server."""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from fastmcp import FastMCP

# Suppress all logging and telemetry before imports
import os
import sys

# MCP server mode
os.environ['MCP_SERVER_MODE'] = '1'

# Disable ALL telemetry aggressively
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['ALLOW_RESET'] = 'False'
os.environ['CHROMA_SERVER_NOFILE'] = '1'

# PostHog specific suppression
os.environ['POSTHOG_DISABLED'] = '1'
os.environ['POSTHOG_API_KEY'] = ''
os.environ['POSTHOG_HOST'] = ''

# Network suppression for telemetry
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''

# Check for debug mode
DEBUG_MCP = os.environ.get('FLOATCTL_MCP_DEBUG', '').lower() == 'true'

# ALWAYS suppress ChromaDB and telemetry logging (causes MCP server crashes)
import logging

# Completely disable logging for problematic libraries
logging.disable(logging.CRITICAL)

# Configure root logger to be completely silent
logging.basicConfig(
    level=logging.CRITICAL + 1,
    handlers=[logging.NullHandler()]
)

# Silence all known chatty loggers - ALWAYS, even in debug mode
chatty_loggers = [
    'chromadb', 'chromadb.telemetry', 'chromadb.api', 'chromadb.db',
    'posthog', 'posthog.client', 'posthog.request',
    'backoff', 'urllib3', 'httpcore', 'httpx', 'requests',
    'opentelemetry', 'grpc', 'asyncio'
]

for logger_name in chatty_loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL + 1)
    logger.disabled = True
    logger.propagate = False
    logger.handlers = [logging.NullHandler()]

# Set up our own debug logger if needed
if DEBUG_MCP:
    from pathlib import Path
    from datetime import datetime
    import json
    
    log_dir = Path.home() / '.floatctl' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'mcp_server_debug.jsonl'
    
    def debug_log(event: str, **kwargs):
        """Simple debug logger that won't interfere with MCP protocol"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            **kwargs
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    # Log that debug mode is active
    debug_log("mcp_debug_enabled", log_file=str(log_file))
else:
    # No-op debug logger
    def debug_log(event: str, **kwargs):
        pass

# Monkey patch requests to prevent telemetry
try:
    import requests
    original_post = requests.post
    original_get = requests.get
    
    def silent_post(*args, **kwargs):
        # Block telemetry URLs
        if args and any(domain in str(args[0]) for domain in ['posthog', 'telemetry', 'analytics']):
            return type('MockResponse', (), {'status_code': 200, 'json': lambda: {}})()
        return original_post(*args, **kwargs)
    
    def silent_get(*args, **kwargs):
        # Block telemetry URLs
        if args and any(domain in str(args[0]) for domain in ['posthog', 'telemetry', 'analytics']):
            return type('MockResponse', (), {'status_code': 200, 'json': lambda: {}})()
        return original_get(*args, **kwargs)
    
    requests.post = silent_post
    requests.get = silent_get
except ImportError:
    pass

# Import the shared Chroma utilities
from floatctl.core.chroma import ChromaClient

# Import pattern processing from new modular structure
from floatctl.mcp.patterns import (
    parse_any_pattern, 
    parse_ctx_metadata, 
    get_hybrid_extractor,
    get_pattern_collection,
    PATTERN_ROUTING
)

# Import ChromaDB operations from new modular structure
from floatctl.mcp.chroma_tools import (
    chroma_list_collections,
    chroma_create_collection,
    chroma_get_collection_info,
    chroma_get_collection_count,
    chroma_modify_collection,
    chroma_delete_collection,
    chroma_add_documents,
    chroma_query_documents,
    chroma_get_documents,
    chroma_update_documents,
    chroma_delete_documents,
    chroma_peek_collection
)

# Import context management tools from new modular structure
from floatctl.mcp.context_tools import (
    process_context_marker,
    get_morning_context,
    query_recent_context,
    search_context,
    surface_recent_context,
    smart_pattern_processor,
    get_recent_context_resource
)

# Import utility functions from new modular structure
from floatctl.mcp.utils import (
    get_chroma_client,
    track_usage,
    estimate_token_count,
    check_context_window_risk,
    sanitize_metadata_for_chroma,
    parse_boundary_duration,
    generate_context_id,
    search_prompts,
    debug_log,
    detect_boundary_need
)

# Import resources and prompts from new modular structure
from floatctl.mcp.resources import (
    PROMPT_LIBRARY,
    ritual_prompt,
    create_bridge,
    get_recent_bridges_resource,
    search_bridges_resource,
    get_bridge_by_id,
    find_related_bridges
)

# Try to import ollama, but don't fail if not available
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Create the MCP server instance with configurable settings
# Environment variables for configuration:
# FASTMCP_HOST - Server host (default: 127.0.0.1, set to 0.0.0.0 for remote access)  
# FASTMCP_PORT - Server port (default: 8000)
# FASTMCP_DEBUG - Debug mode (default: False)
mcp = FastMCP(
    "evna-context-concierge",
    host=os.environ.get('FASTMCP_HOST', '127.0.0.1'),
    port=int(os.environ.get('FASTMCP_PORT', '8000')),
    debug=os.environ.get('FASTMCP_DEBUG', '').lower() == 'true'
)

# Initialize Chroma client (lazy loaded)
_chroma_client = None

def get_chroma_client() -> ChromaClient:
    """Get or create the Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
    return _chroma_client

# Usage pattern tracking
_usage_patterns = {
    "query_count": 0,
    "common_queries": {},
    "context_window_warnings": 0,
    "prompt_requests": {},
    "last_queries": []
}

def track_usage(query_type: str, query: str = "", result_size: int = 0):
    """Track usage patterns for optimization."""
    global _usage_patterns
    _usage_patterns["query_count"] += 1
    
    # Track common queries
    if query:
        query_key = query.lower()[:50]  # First 50 chars
        _usage_patterns["common_queries"][query_key] = _usage_patterns["common_queries"].get(query_key, 0) + 1
    
    # Track recent queries for multi-hop detection
    _usage_patterns["last_queries"].append({
        "type": query_type,
        "query": query[:100],
        "result_size": result_size,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Keep only last 10 queries
    if len(_usage_patterns["last_queries"]) > 10:
        _usage_patterns["last_queries"] = _usage_patterns["last_queries"][-10:]

def estimate_token_count(text: str) -> int:
    """Rough token count estimation (4 chars ≈ 1 token)."""
    return len(text) // 4

def check_context_window_risk(content: str, threshold: int = 32000) -> Tuple[bool, str]:
    """Check if content might blow context window."""
    estimated_tokens = estimate_token_count(content)
    
    if estimated_tokens > threshold:
        _usage_patterns["context_window_warnings"] += 1
        return True, f"⚠️ CONTEXT PANDORA'S BOX: ~{estimated_tokens:,} tokens! This will blow your context window."
    elif estimated_tokens > threshold * 0.7:
        return True, f"⚠️ Large result: ~{estimated_tokens:,} tokens. Consider filtering or summarizing."
    
    return False, ""

# Pre-warm the Chroma connection to get telemetry out of the way
try:
    import sys
    if hasattr(sys, 'stdout') and hasattr(sys.stdout, 'buffer'):
        # We're running as MCP server, pre-initialize
        _throwaway_client = ChromaClient()
        _throwaway_client.collection_exists("dummy_check")
        del _throwaway_client
except:
    pass

# === REGISTER EXTRACTED CHROMADB FUNCTIONS ===
# Register all ChromaDB functions from the new modular chroma_tools module

# Collection operations
mcp.tool()(chroma_list_collections)
mcp.tool()(chroma_create_collection)
mcp.tool()(chroma_get_collection_info)
mcp.tool()(chroma_get_collection_count)
mcp.tool()(chroma_modify_collection)
mcp.tool()(chroma_delete_collection)

# Document operations
mcp.tool()(chroma_add_documents)
mcp.tool()(chroma_query_documents)
mcp.tool()(chroma_get_documents)
mcp.tool()(chroma_update_documents)
mcp.tool()(chroma_delete_documents)
mcp.tool()(chroma_peek_collection)

# Context management tools
mcp.tool()(process_context_marker)
mcp.tool()(get_morning_context)
mcp.tool()(query_recent_context)
mcp.tool()(search_context)
mcp.tool()(surface_recent_context)
mcp.tool()(smart_pattern_processor)

# Context resources
mcp.resource("context://active/recent")(get_recent_context_resource)

# Consciousness prompts
mcp.prompt()(ritual_prompt)
mcp.prompt()(create_bridge)

# Bridge resources
mcp.resource("bridge://recent")(get_recent_bridges_resource)
mcp.resource("bridge://search")(search_bridges_resource)
mcp.resource("bridge://{bridge_id}")(get_bridge_by_id)


# === MODULAR MCP SERVER ARCHITECTURE ===
#
# All MCP tools, resources, and prompts have been extracted to modular components:
#
# 🧠 Pattern Processing: floatctl.mcp.patterns
#    - parse_any_pattern() - Core consciousness pattern recognition
#    - Hybrid LangExtract/regex extraction for FLOAT patterns
#
# 🗃️  ChromaDB Operations: floatctl.mcp.chroma_tools  
#    - Collection management (list, create, modify, delete)
#    - Document operations (add, query, get, update, delete)
#    - Safe collection previews and context window protection
#
# 🎯 Context Management: floatctl.mcp.context_tools
#    - process_context_marker() - ctx:: pattern processing
#    - get_morning_context() - Daily brain boot with priorities
#    - smart_pattern_processor() - Route any :: pattern intelligently
#    - query_recent_context() - Active context stream queries
#    - Surface recent work, boundary checking, usage insights
#
# 🛠️  Utility Functions: floatctl.mcp.utils
#    - Token estimation and context window risk checking
#    - Metadata sanitization for ChromaDB compatibility
#    - Usage pattern tracking and optimization
#    - Boundary duration parsing and context ID generation
#
# 📚 Resources & Prompts: floatctl.mcp.resources
#    - PROMPT_LIBRARY with 5 consciousness-oriented prompts
#    - ritual_prompt() and create_bridge() prompt functions
#    - Bridge resources for context restoration
#    - Related bridge discovery and cross-referencing
#
# All functions are imported above and registered with the MCP server.
# This architecture maintains single responsibility while providing
# the full consciousness technology toolkit through Claude Desktop.
if __name__ == "__main__":
    # Simpler approach: Just suppress stderr completely during startup
    import sys
    import os
    from io import StringIO
    
    # Set MCP server mode to suppress logging
    os.environ['MCP_SERVER_MODE'] = '1'
    
    # Suppress ChromaDB telemetry
    os.environ['ANONYMIZED_TELEMETRY'] = 'False'
    
    # Temporarily redirect stderr to suppress startup noise
    original_stderr = sys.stderr
    startup_stderr = StringIO()
    
    try:
        debug_log = os.environ.get('FLOATCTL_MCP_DEBUG')
        if debug_log:
            with open(debug_log, 'a') as f:
                f.write(f"MCP Server starting at {datetime.now()}\n")
                f.write(f"Python path: {sys.path}\n")
                f.write(f"Script location: {__file__}\n")
        
        # Suppress stderr during startup to avoid telemetry noise
        if not debug_log:  # Only suppress if not debugging
            sys.stderr = startup_stderr
        
        # Run the MCP server with stdio transport
        mcp.run(transport='stdio')
        
    except Exception as e:
        # Restore stderr for error reporting
        sys.stderr = original_stderr
        
        # Log any startup errors
        if debug_log:
            with open(debug_log, 'a') as f:
                f.write(f"Error: {str(e)}\n")
                import traceback
                f.write(traceback.format_exc())
        else:
            # If not debugging, just exit silently
            sys.exit(1)
        raise
    finally:
        # Always restore stderr
        sys.stderr = original_stderr