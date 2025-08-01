#!/usr/bin/env python3
"""Main entry point for the Evna Context Concierge MCP server."""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

from mcp.server.fastmcp import FastMCP

# Suppress all logging before imports
import os
os.environ['MCP_SERVER_MODE'] = '1'

# Disable all telemetry - must use string 'False' not 'false'
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['ALLOW_RESET'] = 'False'

# Suppress all logging
import logging

# Configure logging to be silent
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)

# Specifically silence known chatty loggers
for logger_name in ['chromadb', 'chromadb.telemetry', 'posthog', 'backoff', 'urllib3', 'httpcore', 'httpx']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Import the shared Chroma utilities
from floatctl.core.chroma import ChromaClient

# Try to import ollama, but don't fail if not available
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Create the MCP server instance
mcp = FastMCP("evna-context-concierge")

# Initialize Chroma client (lazy loaded)
_chroma_client = None

def get_chroma_client() -> ChromaClient:
    """Get or create the Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
    return _chroma_client

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


def parse_ctx_marker(text: str) -> Dict[str, Any]:
    """Extract ctx:: marker and metadata from text.
    
    Handles various formats:
    - ctx::2025-07-21 - 2:15 PM [mode:: pre-work ritual] - [project:: rangle/airbender]
    - ctx:: 2025-07-21 -9:49 PM - [project:: rangle/airbender] - [task: 477]
    - ctx::2025-07-28 @ 08:05:00 PM - URL collection data dump
    """
    metadata = {}
    
    # Find ctx:: line
    ctx_match = re.search(r'ctx::\s*([^\n]+)', text, re.IGNORECASE)
    if not ctx_match:
        return metadata
    
    ctx_line = ctx_match.group(1)
    
    # Extract timestamp (flexible format)
    timestamp_patterns = [
        r'(\d{4}-\d{2}-\d{2})\s*[@\-]?\s*(\d{1,2}:\d{2}:\d{2})\s*(AM|PM)?',  # @ or - with seconds
        r'(\d{4}-\d{2}-\d{2})\s*[@\-]?\s*(\d{1,2}:\d{2})\s*(AM|PM)?',        # @ or - without seconds
        r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2}:\d{2})',                       # space separator
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
                # Try with seconds first, then without
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M:%S %p")
                except ValueError:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
            else:
                dt_str = f"{date_str} {time_str}"
                # Try with seconds first, then without
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
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


def parse_boundary_duration(boundary_text: str) -> int:
    """Parse boundary text to get duration in seconds.
    
    Examples:
    - "break for an hour" -> 3600
    - "15 minute break" -> 900
    - "break" -> 900 (default 15 min)
    """
    # Common patterns
    if "hour" in boundary_text:
        return 3600
    elif "30 min" in boundary_text or "thirty min" in boundary_text:
        return 1800
    elif "15 min" in boundary_text or "fifteen min" in boundary_text:
        return 900
    elif "5 min" in boundary_text or "five min" in boundary_text:
        return 300
    else:
        # Default to 15 minutes if no duration specified
        return 900


async def detect_boundary_need(message: str) -> Tuple[bool, str]:
    """Use Ollama to detect if message indicates need for boundary.
    
    Returns:
        Tuple of (needs_boundary, reason)
    """
    if not OLLAMA_AVAILABLE:
        return False, "Ollama not available"
    
    try:
        response = ollama.chat(
            model='llama3.2:3b',  # Small, fast model
            messages=[{
                'role': 'system',
                'content': '''Detect if the user needs a break or boundary. Look for:
- Fatigue indicators (tired, exhausted, burning eyes, sore, hunched)
- Time markers (hours, too long, still working, been at this)
- Physical needs (hungry, need food, shower, movement, haven't eaten)
- Frustration about continuing (still fucking with, can't stop, rabbit hole)
- Explicit break mentions (need break, gotta stop, boundary)

Reply ONLY with: YES or NO'''
            }, {
                'role': 'user',
                'content': message
            }],
            options={
                'temperature': 0.1,  # Low temperature for consistent detection
                'num_predict': 10,   # Only need YES/NO
            }
        )
        
        response_text = response['message']['content'].strip().upper()
        needs_boundary = 'YES' in response_text
        
        if needs_boundary:
            # Try to extract what type of need
            if any(word in message.lower() for word in ['hungry', 'food', 'eat']):
                reason = "Food needed"
            elif any(word in message.lower() for word in ['shower', 'wash']):
                reason = "Hygiene break needed"
            elif any(word in message.lower() for word in ['eyes', 'sore', 'hurt', 'burning']):
                reason = "Physical discomfort"
            elif any(word in message.lower() for word in ['hours', 'long', 'rabbit hole']):
                reason = "Extended work session"
            else:
                reason = "Break needed"
        else:
            reason = ""
            
        return needs_boundary, reason
        
    except Exception as e:
        # Fallback to simple pattern matching
        patterns = [
            'still working', 'still fucking', 'rabbit hole', 'need break',
            'gotta stop', 'eyes hurt', 'hungry', 'need food', 'shower',
            'been at this', 'hours', 'too long'
        ]
        
        message_lower = message.lower()
        if any(pattern in message_lower for pattern in patterns):
            return True, "Pattern match: break indicators"
        
        return False, ""


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
    elif 'boundary-set' in metadata:
        suffix = "boundary"
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
    
    # Check if we actually found a ctx:: marker
    ctx_found = bool(re.search(r'ctx::', message, re.IGNORECASE))
    
    if not ctx_found:
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
    
    # Check for explicit boundary-set or use AI detection
    if 'boundary-set' in metadata:
        # Parse duration from boundary text
        duration = parse_boundary_duration(metadata['boundary-set'])
        metadata['boundary-duration'] = duration
        metadata['boundary-expires'] = (
            datetime.fromisoformat(metadata['timestamp']) + timedelta(seconds=duration)
        ).isoformat()
    else:
        # Use Ollama to detect implicit boundary needs
        needs_boundary, reason = await detect_boundary_need(message)
        if needs_boundary:
            metadata['boundary-detected'] = True
            metadata['boundary-reason'] = reason
            metadata['boundary-duration'] = 900  # Default 15 min
            metadata['boundary-expires'] = (
                datetime.fromisoformat(metadata.get('timestamp', datetime.now(timezone.utc).isoformat())) 
                + timedelta(seconds=900)
            ).isoformat()
    
    # Generate document ID
    doc_id = generate_context_id(metadata)
    
    captured = None
    related = []
    
    try:
        chroma = get_chroma_client()
        
        if auto_capture:
            # Add to active_context_stream
            try:
                doc_id = chroma.add_context_marker(
                    collection_name="active_context_stream",
                    document=message,
                    metadata=metadata,
                    doc_id=doc_id
                )
                captured = {
                    "id": doc_id,
                    "document": message,
                    "metadata": metadata
                }
            except Exception as e:
                return {
                    "error": f"Failed to capture context: {str(e)}",
                    "captured": False
                }
        
        # Find related recent context
        # Query for entries with similar metadata in last 36 hours
        results = chroma.query_recent_context(
            collection_name="active_context_stream",
            hours=36,
            project=metadata.get('project'),
            mode=metadata.get('mode'),
            limit=5
        )
        
        # Format related results
        for doc, meta, doc_id in zip(
            results.get("documents", []),
            results.get("metadatas", []),
            results.get("ids", [])
        ):
            # Skip the one we just added
            if doc_id == captured.get("id"):
                continue
            
            related.append({
                "id": doc_id,
                "preview": doc[:200] + "..." if len(doc) > 200 else doc,
                "metadata": meta
            })
    
    except Exception as e:
        return {
            "error": f"Chroma operation failed: {str(e)}",
            "captured": False
        }
    
    return {
        "captured": captured,
        "related_context": related,
        "extracted_metadata": metadata
    }


@mcp.tool()
async def get_morning_context(
    lookback_hours: int = 36
) -> List[Dict[str, Any]]:
    """Get recent context for morning brain boot.
    
    Retrieves recent context entries, prioritizing:
    - Unfinished work from yesterday
    - Recent project activity
    - Mode transitions
    """
    try:
        chroma = get_chroma_client()
        return chroma.get_morning_context(
            collection_name="active_context_stream",
            lookback_hours=lookback_hours
        )
    except Exception as e:
        return [{
            "error": f"Failed to get morning context: {str(e)}",
            "summary": "Error loading context",
            "recent_projects": [],
            "open_tasks": [],
            "last_mode": None
        }]


@mcp.tool()
async def query_recent_context(
    project: Optional[str] = None,
    mode: Optional[str] = None,
    hours: int = 24
) -> List[Dict[str, Any]]:
    """Query recent context with filters.
    
    Returns context entries matching the specified criteria.
    """
    try:
        chroma = get_chroma_client()
        results = chroma.query_recent_context(
            collection_name="active_context_stream",
            hours=hours,
            project=project,
            mode=mode,
            limit=10
        )
        
        # Format results
        output = []
        for doc, meta, doc_id in zip(
            results.get("documents", []),
            results.get("metadatas", []),
            results.get("ids", [])
        ):
            output.append({
                "id": doc_id,
                "content": doc,
                "metadata": meta
            })
        
        return output
    except Exception as e:
        return [{
            "error": f"Failed to query context: {str(e)}"
        }]


@mcp.tool()
async def search_context(
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Semantic search in active_context_stream.
    
    Uses Chroma's semantic search to find relevant context.
    """
    try:
        chroma = get_chroma_client()
        return chroma.search_context(
            collection_name="active_context_stream",
            query=query,
            limit=limit
        )
    except Exception as e:
        return [{
            "error": f"Failed to search context: {str(e)}"
        }]


@mcp.tool()
async def check_boundary_status() -> Dict[str, Any]:
    """Check if you're respecting your boundaries.
    
    Looks for recent boundary declarations and checks if you're
    still working when you should be on break.
    """
    try:
        chroma = get_chroma_client()
        
        # Find recent boundary declarations (last 4 hours)
        now = datetime.now(timezone.utc)
        four_hours_ago = now - timedelta(hours=4)
        
        # Query for boundary-related entries
        results = chroma.query_recent_context(
            collection_name="active_context_stream",
            hours=4,
            limit=20
        )
        
        # Find most recent boundary
        most_recent_boundary = None
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            if any(key in meta for key in ['boundary-set', 'boundary-detected']):
                if not most_recent_boundary or meta.get('timestamp', '') > most_recent_boundary['timestamp']:
                    most_recent_boundary = meta
        
        if not most_recent_boundary:
            return {
                "status": "no_boundaries",
                "message": "No recent boundaries set. Working sustainably?"
            }
        
        # Check if boundary is expired
        boundary_expires = most_recent_boundary.get('boundary-expires')
        if boundary_expires:
            expires_dt = datetime.fromisoformat(boundary_expires)
            if now > expires_dt:
                return {
                    "status": "boundary_expired",
                    "message": f"Boundary expired {int((now - expires_dt).total_seconds() / 60)} minutes ago",
                    "boundary": most_recent_boundary
                }
        
        # Check for activity after boundary was set
        boundary_time = datetime.fromisoformat(most_recent_boundary['timestamp'])
        
        # Simple check: look for Claude project activity
        import os
        import glob
        claude_projects = os.path.expanduser("~/.claude/projects")
        
        # Find files modified after boundary was set
        violations = []
        for project_dir in glob.glob(f"{claude_projects}/*"):
            for jsonl_file in glob.glob(f"{project_dir}/*.jsonl"):
                try:
                    mtime = os.path.getmtime(jsonl_file)
                    if mtime > boundary_time.timestamp():
                        violations.append({
                            "project": os.path.basename(project_dir),
                            "minutes_after_boundary": int((mtime - boundary_time.timestamp()) / 60)
                        })
                except:
                    continue
        
        if violations:
            # Get unique projects
            projects = list(set(v["project"] for v in violations))
            max_minutes = max(v["minutes_after_boundary"] for v in violations)
            
            boundary_type = most_recent_boundary.get('boundary-set', 
                           most_recent_boundary.get('boundary-reason', 'break'))
            
            return {
                "status": "boundary_violated",
                "message": f"⚠️ You said '{boundary_type}' {int((now - boundary_time).total_seconds() / 60)} min ago but still working!",
                "violations": {
                    "projects_active": projects[:3],  # Top 3 projects
                    "latest_activity": f"{max_minutes} min after boundary"
                },
                "boundary": most_recent_boundary
            }
        else:
            return {
                "status": "boundary_respected",
                "message": "✓ Good job respecting your boundary!",
                "boundary": most_recent_boundary
            }
            
    except Exception as e:
        return {
            "error": f"Failed to check boundary: {str(e)}",
            "status": "error"
        }


if __name__ == "__main__":
    # Suppress all output except JSON
    import sys
    import os
    
    # Set MCP server mode to suppress logging
    os.environ['MCP_SERVER_MODE'] = '1'
    
    # Suppress ChromaDB telemetry
    os.environ['ANONYMIZED_TELEMETRY'] = 'False'
    
    # Add error handling for debugging
    try:
        debug_log = os.environ.get('FLOATCTL_MCP_DEBUG')
        if debug_log:
            with open(debug_log, 'a') as f:
                f.write(f"MCP Server starting at {datetime.now()}\n")
                f.write(f"Python path: {sys.path}\n")
                f.write(f"Script location: {__file__}\n")
        
        # Run the MCP server with stdio transport
        mcp.run(transport='stdio')
    except Exception as e:
        # Log any startup errors
        if debug_log:
            with open(debug_log, 'a') as f:
                f.write(f"Error: {str(e)}\n")
                import traceback
                f.write(traceback.format_exc())
        raise