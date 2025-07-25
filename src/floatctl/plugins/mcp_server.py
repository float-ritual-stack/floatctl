"""MCP Server plugin - Evna Context Concierge for active_context_stream management."""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import json

import click
from mcp.server.fastmcp import FastMCP
import chromadb
from chromadb.config import Settings

from floatctl.plugin_manager import PluginBase
from floatctl.core.logging import get_logger

# Create the MCP server instance
mcp = FastMCP("evna-context-concierge")


def parse_ctx_marker(text: str) -> Dict[str, Any]:
    """Extract ctx:: marker and metadata from text.
    
    Handles various formats:
    - ctx::2025-07-21 - 2:15 PM [mode:: pre-work ritual] - [project:: rangle/airbender]
    - ctx:: 2025-07-21 -9:49 PM - [project:: rangle/airbender] - [task: 477]
    """
    metadata = {}
    
    # Find ctx:: line
    ctx_match = re.search(r'ctx::\s*([^\n]+)', text, re.IGNORECASE)
    if not ctx_match:
        return metadata
    
    ctx_line = ctx_match.group(1)
    
    # Extract timestamp (flexible format)
    timestamp_patterns = [
        r'(\d{4}-\d{2}-\d{2})\s*-?\s*(\d{1,2}:\d{2})\s*(AM|PM)?',
        r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2}:\d{2})',
    ]
    
    for pattern in timestamp_patterns:
        time_match = re.search(pattern, ctx_line, re.IGNORECASE)
        if time_match:
            date_str = time_match.group(1)
            time_str = time_match.group(2)
            am_pm = time_match.group(3) if len(time_match.groups()) >= 3 else None
            
            # Parse timestamp
            if am_pm:
                dt_str = f"{date_str} {time_str} {am_pm}"
                dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
            else:
                dt_str = f"{date_str} {time_str}"
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            
            # Assume UTC if no timezone specified
            dt = dt.replace(tzinfo=timezone.utc)
            metadata['timestamp'] = dt.isoformat()
            metadata['timestamp_unix'] = int(dt.timestamp())
            break
    
    # Extract [key:: value] patterns
    pattern_matches = re.findall(r'\[([^:]+)::\s*([^\]]+)\]', ctx_line)
    for key, value in pattern_matches:
        metadata[key.strip()] = value.strip()
    
    # Also check the full message for additional patterns
    full_patterns = re.findall(r'\[([^:]+)::\s*([^\]]+)\]', text)
    for key, value in full_patterns:
        if key.strip() not in metadata:
            metadata[key.strip()] = value.strip()
    
    return metadata


def generate_context_id(metadata: Dict[str, Any]) -> str:
    """Generate a document ID for the context entry."""
    if 'timestamp' in metadata:
        dt = datetime.fromisoformat(metadata['timestamp'])
        base = f"ctx_{dt.strftime('%Y%m%d_%H%M')}"
    else:
        base = f"ctx_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
    
    # Add descriptive suffix if available
    if 'mode' in metadata:
        suffix = metadata['mode'].replace(' ', '_')[:20]
    elif 'project' in metadata:
        suffix = metadata['project'].split('/')[-1][:20]
    else:
        suffix = "context"
    
    return f"{base}_{suffix}"


@mcp.tool()
async def process_context_marker(
    message: str,
    auto_capture: bool = True
) -> Dict[str, Any]:
    """Process a message containing ctx:: marker.
    
    Extracts metadata, captures to active_context_stream,
    and returns related recent context for continuity.
    """
    # Parse the ctx:: marker and metadata
    metadata = parse_ctx_marker(message)
    
    if not metadata:
        return {
            "error": "No ctx:: marker found in message",
            "captured": False
        }
    
    # Add TTL if not present (36-hour default)
    if 'timestamp' in metadata and 'ttl_expires' not in metadata:
        dt = datetime.fromisoformat(metadata['timestamp'])
        ttl = dt + timedelta(hours=36)
        metadata['ttl_expires'] = ttl.isoformat()
        metadata['ttl_expires_unix'] = int(ttl.timestamp())
    
    # Set default type if not specified
    if 'type' not in metadata:
        metadata['type'] = 'context_marker'
    
    # Generate document ID
    doc_id = generate_context_id(metadata)
    
    captured = None
    if auto_capture:
        # Note: In actual implementation, this would use the Chroma MCP tools
        # For now, we'll return a mock response
        captured = {
            "id": doc_id,
            "document": message,
            "metadata": metadata
        }
    
    # Find related recent context
    related = []
    
    # Query for related entries based on metadata
    # Priority: same project > same mode > recent temporal
    query_terms = []
    if 'project' in metadata:
        query_terms.append(metadata['project'])
    if 'mode' in metadata:
        query_terms.append(metadata['mode'])
    if 'task' in metadata:
        query_terms.append(f"task {metadata['task']}")
    
    # Note: In actual implementation, would query Chroma
    # For now, return empty related context
    
    return {
        "captured": captured,
        "related_context": related,
        "extracted_metadata": metadata
    }


@mcp.tool()
async def get_morning_context(
    lookback_hours: int = 4
) -> List[Dict[str, Any]]:
    """Get recent context for morning brain boot.
    
    Retrieves recent context entries, prioritizing:
    - Unfinished work from yesterday
    - Recent project activity
    - Mode transitions
    """
    # Calculate timestamp for lookback
    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    since_unix = int(since.timestamp())
    
    # Note: Would use Chroma query with timestamp filtering
    # For now, return structured example
    return [
        {
            "id": "ctx_20250725_0800_morning",
            "summary": "Morning context loaded",
            "recent_projects": [],
            "open_tasks": [],
            "last_mode": None
        }
    ]


@mcp.tool()
async def query_recent_context(
    project: Optional[str] = None,
    mode: Optional[str] = None,
    hours: int = 24
) -> List[Dict[str, Any]]:
    """Query recent context with filters.
    
    Returns context entries matching the specified criteria.
    """
    # Calculate timestamp for filtering
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_unix = int(since.timestamp())
    
    # Build query
    query_parts = []
    if project:
        query_parts.append(f"project {project}")
    if mode:
        query_parts.append(f"mode {mode}")
    
    query_text = " ".join(query_parts) if query_parts else "context"
    
    # Note: Would use Chroma query
    # For now, return empty results
    return []


@mcp.tool()
async def search_context(
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Semantic search in active_context_stream.
    
    Uses Chroma's semantic search to find relevant context.
    """
    # Note: Would use Chroma semantic search
    # For now, return empty results
    return []


class MCPServerPlugin(PluginBase):
    """MCP Server plugin for FloatCtl."""
    
    name = "mcp"
    description = "MCP server for context concierge functionality"
    version = "0.1.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register MCP server commands."""
        
        @cli_group.group()
        @click.pass_context
        def mcp(ctx: click.Context) -> None:
            """MCP server for context concierge functionality."""
            pass
        
        @mcp.command()
        @click.option(
            '--transport',
            type=click.Choice(['stdio', 'http']),
            default='stdio',
            help='Transport mode for MCP server'
        )
        @click.option(
            '--port',
            type=int,
            default=3000,
            help='Port for HTTP transport'
        )
        def serve(transport: str, port: int) -> None:
            """Run the Evna Context Concierge MCP server.
            
            This server provides context management tools for active_context_stream,
            enabling natural context capture and retrieval.
            
            Examples:
                floatctl mcp serve              # Run with stdio transport
                floatctl mcp serve --transport http --port 8080
            """
            logger = get_logger(__name__)
            
            if transport == 'stdio':
                click.echo("Starting Evna Context Concierge MCP server (stdio)...")
                logger.info("mcp_server_start", transport="stdio")
                
                # Run the MCP server
                mcp.run()
                
            else:  # http
                click.echo(f"Starting Evna Context Concierge MCP server (http) on port {port}...")
                logger.info("mcp_server_start", transport="http", port=port)
                
                # Run with HTTP transport
                mcp.run(transport='http', port=port)