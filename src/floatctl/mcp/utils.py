"""Utility functions for FLOAT consciousness technology :: utils.

This module contains utility functions for MCP server operations.
Extracted from the monolithic mcp_server.py for maintainability.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple

from floatctl.core.chroma import ChromaClient

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


def sanitize_metadata_for_chroma(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all metadata values are ChromaDB-compatible primitives.
    
    ChromaDB only accepts str, int, float, bool, or None as metadata values.
    This function converts complex types to their string representations.
    
    Args:
        metadata: Dictionary with potentially non-primitive values
        
    Returns:
        Dictionary with all values as ChromaDB-compatible primitives
    """
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, (list, tuple)):
            # Convert lists/tuples to comma-separated strings
            sanitized[key] = ",".join(str(v) for v in value)
        elif isinstance(value, dict):
            # Convert dicts to JSON strings
            sanitized[key] = json.dumps(value)
        elif value is None or isinstance(value, (str, int, float, bool)):
            # These are already valid ChromaDB types
            sanitized[key] = value
        else:
            # Convert anything else to string
            sanitized[key] = str(value)
    return sanitized


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


def search_prompts(query: str, prompt_library: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search prompt library by tags or content."""
    results = []
    query_lower = query.lower()
    
    for name, prompt_data in prompt_library.items():
        score = 0
        
        # Check name match
        if query_lower in name.lower():
            score += 10
        
        # Check tag matches
        for tag in prompt_data["tags"]:
            if query_lower in tag.lower():
                score += 5
        
        # Check content match (partial)
        if query_lower in prompt_data["prompt"].lower():
            score += 2
        
        if score > 0:
            results.append({
                "name": name,
                "score": score,
                "prompt": prompt_data["prompt"],
                "tags": prompt_data["tags"],
                "usage_count": prompt_data["usage_count"]
            })
    
    # Sort by score, then by usage count
    results.sort(key=lambda x: (x["score"], x["usage_count"]), reverse=True)
    return results


def find_related_bridges(bridge_id: str, chroma_client) -> List[Dict[str, str]]:
    """Find bridges that reference this one or share context."""
    try:
        # Search for bridges that mention this bridge ID
        results = chroma_client.query_documents(
            collection_name="float_bridges",
            query_texts=[bridge_id],
            n_results=3,
            include=["metadatas"]
        )
        
        related = []
        for meta in results.get("metadatas", []):
            if meta.get("bridge_id") != bridge_id:  # Don't include self
                related.append({
                    "bridge_id": meta.get("bridge_id", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "threads": meta.get("active_threads", "")
                })
        
        return related[:2]  # Limit to 2 related bridges
        
    except Exception as e:
        return [{"error": f"Could not find related bridges: {str(e)}"}]


# Debug logging setup
DEBUG_MCP = os.environ.get('FLOATCTL_MCP_DEBUG', '').lower() == 'true'

if DEBUG_MCP:
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
else:
    # No-op debug logger
    def debug_log(event: str, **kwargs):
        pass


async def detect_boundary_need(message: str) -> Tuple[bool, str]:
    """Use Ollama to detect if message indicates need for boundary.
    
    Returns:
        Tuple of (needs_boundary, reason)
    """
    # Try to import ollama
    try:
        import ollama
        OLLAMA_AVAILABLE = True
    except ImportError:
        OLLAMA_AVAILABLE = False
    
    if not OLLAMA_AVAILABLE:
        return False, "Ollama not available"
    
    try:
        response = await ollama.agenerate(
            model='llama3.2:1b',
            prompt=f"""Analyze this message and determine if the person needs to set a boundary or take a break. Look for signs of:
- Overwhelm or stress
- Working too long without breaks  
- Feeling stretched thin
- Needing rest or recovery

Message: "{message}"

Respond with JSON only:
{{"needs_boundary": true/false, "reason": "brief explanation"}}""",
            stream=False
        )
        
        result = json.loads(response['response'])
        return result.get('needs_boundary', False), result.get('reason', 'No specific reason')
        
    except Exception as e:
        return False, f"Analysis failed: {str(e)}"