"""Context management tools for FLOAT consciousness technology :: context_tools.

This module contains all context-related MCP tools and utilities.
Extracted from the monolithic mcp_server.py for maintainability.
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from floatctl.core.chroma import ChromaClient

# Import pattern processing utilities
from floatctl.mcp.patterns import (
    parse_any_pattern,
    parse_ctx_metadata,
    get_pattern_collection,
    PATTERN_ROUTING
)

# Set up logging
logger = logging.getLogger(__name__)

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

def debug_log(event: str, **kwargs):
    """Simple debug logging for context operations."""
    logger.debug(f"[CONTEXT] {event}: {kwargs}")

def parse_boundary_duration(boundary_text: str) -> int:
    """Parse duration from boundary text into seconds."""
    # Simple parsing - extract numbers and assume minutes
    import re
    numbers = re.findall(r'\d+', boundary_text.lower())
    if numbers:
        duration = int(numbers[0])
        if 'hour' in boundary_text.lower():
            return duration * 3600
        elif 'sec' in boundary_text.lower():
            return duration
        else:
            return duration * 60  # Default to minutes
    return 900  # Default 15 minutes

async def detect_boundary_need(message: str) -> Tuple[bool, str]:
    """Simple boundary detection without Ollama dependency."""
    # Simple keyword-based detection
    fatigue_indicators = ['tired', 'exhausted', 'burning eyes', 'sore', 'hunched', 
                         'haven\'t eaten', 'need food', 'hungry', 'break']
    
    message_lower = message.lower()
    for indicator in fatigue_indicators:
        if indicator in message_lower:
            return True, f"Detected fatigue indicator: {indicator}"
    
    return False, "No boundary needs detected"

# Global Chroma client instance
_chroma_client: Optional[ChromaClient] = None

def get_chroma_client() -> ChromaClient:
    """Get or create the Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
    return _chroma_client

# Context processing utilities
def sanitize_metadata_for_chroma(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize metadata for ChromaDB compatibility."""
    safe_meta = {}
    for k, v in metadata.items():
        # ChromaDB supports: str, int, float, bool
        if isinstance(v, (str, int, float, bool, type(None))):
            safe_meta[k] = v
        elif isinstance(v, (list, tuple)):
            # Convert to comma-separated string for ChromaDB
            safe_meta[k] = ",".join(str(x) for x in v)
        elif isinstance(v, Path):
            safe_meta[k] = str(v)
        else:
            # Convert everything else to string
            safe_meta[k] = str(v)
    return safe_meta

def generate_context_id(metadata: Dict[str, Any]) -> str:
    """Generate a context-aware ID for documents."""
    base = f"context-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    
    # Add project if available
    if "project" in metadata:
        project_clean = str(metadata["project"]).replace("/", "-").replace(" ", "-")
        base += f"-{project_clean}"
    
    # Add source or type suffix
    if "source_file" in metadata:
        suffix = Path(str(metadata["source_file"])).stem
    elif "bridge_id" in metadata:
        suffix = "bridge"
    elif "chunk_id" in metadata:
        suffix = "chunk"
    else:
        suffix = "context"
    
    return f"{base}_{suffix}"

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


# === CONTEXT MANAGEMENT TOOLS ===

# Note: These functions will be imported and registered by the main server module
async def process_context_marker(
    message: str,
    auto_capture: bool = True
) -> Dict[str, Any]:
    """Process a message containing ctx:: marker.
    
    WHEN TO CALL THIS PROACTIVELY:
    - ANY time user writes "ctx::" followed by anything
    - When conversation context shifts significantly
    - At start of new work session (capture opening context)
    - After long explanations or complex discussions (capture summary)
    - When user mentions specific time, date, or duration of work
    
    IMPLICIT TRIGGERS (create ctx:: for user):
    - "Just got back to this" → ctx:: resuming work
    - "Starting on [project]" → ctx:: starting [project]
    - "Been working on this since [time]" → ctx:: working since [time]
    - "Switching to [topic]" → ctx:: switching to [topic]
    
    The tool extracts metadata, captures to active_context_stream,
    and returns related recent context for continuity.
    
    ALWAYS capture ctx:: markers immediately without asking permission.
    """
    # Parse the ctx:: marker and metadata using enhanced parser
    metadata = parse_any_pattern(message)
    
    # Ensure we have ctx:: specific handling
    if "ctx_content" not in metadata:
        # Fallback to old parser for ctx:: patterns
        ctx_metadata = parse_ctx_metadata(message)
        metadata.update(ctx_metadata)
    
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
            # Sanitize metadata for ChromaDB compatibility
            sanitized_metadata = sanitize_metadata_for_chroma(metadata)
            
            # Add to active_context_stream
            try:
                doc_id = chroma.add_context_marker(
                    collection_name="active_context_stream",
                    document=message,
                    metadata=sanitized_metadata,
                    doc_id=doc_id
                )
                captured = {
                    "id": doc_id,
                    "document": message,
                    "metadata": metadata  # Return original metadata for display
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


async def get_morning_context(
    lookback_hours: int = 36
) -> List[Dict[str, Any]]:
    """Get recent context for morning brain boot.
    
    WHEN TO CALL THIS PROACTIVELY:
    - First interaction of a new day (check if >6 hours since last interaction)
    - User mentions "morning", "starting day", "what was I doing"
    - User asks about recent work or yesterday's progress
    - After long gaps in conversation (>4 hours)
    - When user seems to be resuming work
    
    IMPLICIT TRIGGERS:
    - "Good morning" → Call immediately to surface context
    - "Where did we leave off?" → Call to retrieve recent work
    - "What was I working on?" → Call with appropriate lookback
    - Time-based: If current time is 6am-10am and no recent activity
    
    Retrieves recent context entries, prioritizing:
    - Unfinished work from yesterday
    - Recent project activity
    - Mode transitions
    - Open bridges and decisions
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


async def query_recent_context(
    project: Optional[str] = None,
    mode: Optional[str] = None,
    hours: int = 24
) -> List[Dict[str, Any]]:
    """Query recent context with filters.
    
    Returns context entries matching the specified criteria.
    """
    try:
        debug_log("query_recent_context_called", 
                 project=project, mode=mode, hours=hours)
        
        chroma = get_chroma_client()
        results = chroma.query_recent_context(
            collection_name="active_context_stream",
            hours=hours,
            project=project,
            mode=mode,
            limit=10
        )
        
        debug_log("query_recent_context_results",
                 doc_count=len(results.get("documents", [])),
                 has_ids=bool(results.get("ids")),
                 has_metadatas=bool(results.get("metadatas")))
        
        # Format results - ensure JSON serializable types
        output = []
        for doc, meta, doc_id in zip(
            results.get("documents", []),
            results.get("metadatas", []),
            results.get("ids", [])
        ):
            # Ensure all values are JSON-serializable
            safe_meta = {}
            if meta:
                for k, v in meta.items():
                    # Convert any non-serializable types to strings
                    if isinstance(v, (str, int, float, bool, type(None))):
                        safe_meta[k] = v
                    elif isinstance(v, (list, tuple)):
                        safe_meta[k] = list(v)
                    elif isinstance(v, dict):
                        safe_meta[k] = v
                    else:
                        safe_meta[k] = str(v)
            
            output.append({
                "id": str(doc_id) if doc_id else "",
                "content": str(doc) if doc else "",
                "metadata": safe_meta,
                "timestamp": safe_meta.get("timestamp", "")
            })
        
        return output
    except Exception as e:
        return [{
            "error": f"Failed to query context: {str(e)}"
        }]


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


async def surface_recent_context(
    hours: int = 6,
    include_patterns: List[str] = None
) -> Dict[str, Any]:
    """Surface recent context automatically when you ask 'what was I working on?'
    
    WHEN TO CALL THIS PROACTIVELY:
    - User asks any variation of "what was I doing/working on?"
    - After breaks or interruptions
    - When user seems lost or needs orientation
    - Start of conversation after gap >2 hours
    - When user mentions forgetting something
    
    IMPLICIT TRIGGERS:
    - "Remind me what..." → Surface relevant context
    - "I forgot where..." → Surface recent locations/topics
    - "What was that..." → Surface recent discussions
    - "Lost my train of thought" → Surface last few contexts
    - Gap detection: >2 hours since last message → Call automatically
    
    Intelligently surfaces recent activity across your collections with smart filtering.
    Provides overview without overwhelming detail.
    """
    if include_patterns is None:
        include_patterns = ["ctx::", "highlight::", "decision::", "eureka::"]
    
    track_usage("context_surface", f"last_{hours}h")
    
    try:
        chroma = get_chroma_client()
        
        # Get recent context from multiple collections
        collections_to_check = [
            "active_context_stream",
            "float_highlights", 
            "float_wins",
            "float_dispatch_bay"
        ]
        
        all_recent = []
        
        for collection in collections_to_check:
            try:
                results = chroma.query_recent_context(
                    collection_name=collection,
                    hours=hours,
                    limit=10
                )
                
                for doc, meta, doc_id in zip(
                    results.get("documents", []),
                    results.get("metadatas", []),
                    results.get("ids", [])
                ):
                    # Check if document contains any of the desired patterns
                    if any(pattern in doc.lower() for pattern in include_patterns):
                        all_recent.append({
                            "id": doc_id,
                            "content": doc,
                            "metadata": meta,
                            "collection": collection,
                            "timestamp": meta.get("timestamp", ""),
                            "preview": doc[:200] + "..." if len(doc) > 200 else doc
                        })
            except Exception as e:
                # Skip collections that don't exist or have issues
                continue
        
        # Sort by timestamp (most recent first)
        all_recent.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Group by project/mode for better organization
        by_project = {}
        by_mode = {}
        highlights = []
        decisions = []
        
        for item in all_recent[:15]:  # Limit to 15 most recent
            # Group by project
            project = item["metadata"].get("project", "unknown")
            if project not in by_project:
                by_project[project] = []
            by_project[project].append(item)
            
            # Group by mode
            mode = item["metadata"].get("mode", "unknown")
            if mode not in by_mode:
                by_mode[mode] = []
            by_mode[mode].append(item)
            
            # Categorize special items
            content_lower = item["content"].lower()
            if "highlight::" in content_lower or "eureka::" in content_lower:
                highlights.append(item)
            elif "decision::" in content_lower:
                decisions.append(item)
        
        # Check context window risk
        total_content = "\n".join(item["content"] for item in all_recent[:10])
        is_risky, warning = check_context_window_risk(total_content)
        
        response = {
            "recent_activity": {
                "total_items": len(all_recent),
                "time_range": f"Last {hours} hours",
                "collections_searched": collections_to_check
            },
            "by_project": {k: len(v) for k, v in by_project.items()},
            "by_mode": {k: len(v) for k, v in by_mode.items()},
            "highlights": [h["preview"] for h in highlights[:3]],
            "recent_decisions": [d["preview"] for d in decisions[:3]],
            "latest_items": [item["preview"] for item in all_recent[:5]]
        }
        
        if warning:
            response["warning"] = warning
            response["suggestion"] = "Use smart_chroma_query with specific filters to avoid context overload"
        
        return response
        
    except Exception as e:
        return {
            "error": f"Failed to surface context: {str(e)}",
            "fallback": "Try using query_recent_context with specific parameters"
        }


async def smart_pattern_processor(
    text: str,
    auto_surface_context: bool = True
) -> Dict[str, Any]:
    """▒▒ Smart Pattern Processor Guide (Compact)

    **Rule: Saturate with `::` patterns, never summarize**

    ### ❌ **Don't:**
    ```
    "ctx::meeting notes"  // Too thin
    "work stuff today"    // No patterns
    ```

    ### ✅ **Do:**
    ```
    "ctx::2025-09-07 @ 10:36AM meeting::pharmacy_sync 
    project::rangle/pharmacy pattern::PR_size_creep 
    insight::82_percent_reduction problem::2000_line_PRs 
    solution::size_gates mode::work_archaeology"
    ```

    **Pattern types:** `ctx::` `project::` `mode::` `bridge::` `ritual::` `insight::` `problem::` `solution::` `pattern::` `workflow::`

    **Core principle:** Every `::` marker = future search vector. Density enables discovery.

    **Impact:**
    - Thin (3 patterns) → 0 related context found
    - Dense (10+ patterns) → Auto-surfaces connections + metadata

    >> Add MORE patterns, not fewer
    >> The magic is in the metadata mesh
    """
    track_usage("smart_pattern", text[:50])
    
    # Parse all patterns in the text
    metadata = parse_any_pattern(text)
    
    if not metadata.get("patterns_found"):
        return {
            "error": "No :: patterns found in text",
            "suggestion": "Try patterns like: ctx::, highlight::, decision::, eureka::, gotcha::, bridge::",
            "example": "highlight:: This is an important insight [project:: my-project]"
        }
    
    patterns_found = metadata["patterns_found"]
    primary_pattern = metadata["primary_pattern"]
    
    # Smart collection routing
    collection_routing = {
        "ctx": "active_context_stream",
        "highlight": "float_highlights", 
        "highligght": "float_highlights",  # Common typo tolerance
        "decision": "float_dispatch_bay",
        "eureka": "float_wins",
        "gotcha": "active_context_stream",  # Debug info
        "bridge": "float_bridges",
        "concept": "float_dispatch_bay",  # New concepts
        "aka": "float_bridges",  # Aliases/references
        "mode": "active_context_stream",  # Mode changes
        "project": "active_context_stream",  # Project context
        "task": "active_context_stream",  # Task tracking
        "boundary": "active_context_stream",  # Boundary setting
        # Function-style patterns
        "float.dispatch": "float_dispatch_bay",
        "float.ritual": "float_ritual_systems",
        "float": "float_dispatch_bay",  # Generic float patterns
        "dispatch": "float_dispatch_bay"  # Standalone dispatch
    }
    
    target_collection = collection_routing.get(primary_pattern, "active_context_stream")
    
    # Add minimal core metadata
    now = datetime.now(timezone.utc)
    metadata.update({
        "timestamp": now.isoformat(),
        "timestamp_unix": int(now.timestamp()),
        "primary_pattern": primary_pattern
    })
    
    # Only add extra metadata if there are multiple patterns or it's not ctx::
    if len(patterns_found) > 1:
        metadata["pattern_count"] = len(patterns_found)
        metadata["patterns_found_str"] = ",".join(patterns_found)
    
    # Remove the list version to avoid ChromaDB errors
    if "patterns_found" in metadata:
        patterns_list = metadata.pop("patterns_found")  # Remove list, keep for response
    
    # Add TTL based on pattern type
    ttl_hours = {
        "ctx": 36,      # Context expires in 36 hours
        "gotcha": 72,   # Debug info lasts 3 days
        "highlight": 0, # Highlights are permanent
        "eureka": 0,    # Breakthroughs are permanent
        "decision": 0,  # Decisions are permanent
        "bridge": 0,    # Bridges are permanent
        "concept": 168, # New concepts last a week
        "boundary": 24  # Boundaries last 24 hours
    }
    
    ttl = ttl_hours.get(primary_pattern, 72)  # Default 3 days
    if ttl > 0:
        expires = now + timedelta(hours=ttl)
        metadata["ttl_expires"] = expires.isoformat()
        metadata["ttl_expires_unix"] = int(expires.timestamp())
        metadata["ttl_hours"] = ttl  # Track the TTL duration for reference
    
    # Generate smart document ID
    timestamp_str = now.strftime('%Y%m%d_%H%M')
    content_hash = hash(text[:100]) % 10000
    doc_id = f"{primary_pattern}_{timestamp_str}_{content_hash:04d}"
    
    captured_info = {
        "id": doc_id,
        "patterns": patterns_found,
        "primary_pattern": primary_pattern,
        "collection": target_collection,
        "metadata": metadata
    }
    
    # Context surfacing based on pattern type
    related_context = []
    suggestions = []
    
    try:
        chroma = get_chroma_client()
        
        # Special handling for bridge patterns to ensure consistent metadata
        if primary_pattern == "bridge":
            # Extract bridge type from content if present
            bridge_type = "modular"  # Default
            if "bridge::create" in text.lower():
                bridge_type = "modular"
            elif "complete" in text.lower():
                bridge_type = "complete"
            elif "index" in text.lower():
                bridge_type = "index"
            
            # Use centralized bridge creation function
            doc_id = chroma.create_bridge_document(
                content=text,
                metadata=metadata,
                bridge_type=bridge_type
            )
        else:
            # Capture to appropriate collection using existing method
            doc_id = chroma.add_context_marker(
                collection_name=target_collection,
                document=text,
                metadata=metadata,
                doc_id=doc_id
            )
        
        captured_info["id"] = doc_id
        captured_info["captured"] = True
        
        if auto_surface_context:
            # Smart context surfacing based on pattern type
            if primary_pattern in ["highlight", "eureka", "decision"]:
                # For important patterns, find related content across collections
                search_query = text[:200]  # Use first 200 chars
                
                # Search in the same collection
                results = chroma.search_context(
                    collection_name=target_collection,
                    query=search_query,
                    limit=3
                )
                
                for result in results:
                    if result.get("id") != doc_id:
                        related_context.append({
                            "type": "related_content",
                            "collection": target_collection,
                            "preview": result.get("content", "")[:150] + "...",
                            "metadata": result.get("metadata", {})
                        })
                
                suggestions.append(f"🔍 Found {len(related_context)} related items in {target_collection}")
            
            elif primary_pattern == "ctx":
                # For context markers, surface recent project/mode activity
                project = metadata.get("project")
                mode = metadata.get("mode")
                
                if project or mode:
                    recent = chroma.query_recent_context(
                        collection_name="active_context_stream",
                        hours=24,
                        project=project,
                        mode=mode,
                        limit=3
                    )
                    
                    for doc, meta, doc_id_recent in zip(
                        recent.get("documents", []),
                        recent.get("metadatas", []),
                        recent.get("ids", [])
                    ):
                        if doc_id_recent != doc_id:
                            related_context.append({
                                "type": "recent_context",
                                "collection": "active_context_stream",
                                "preview": doc[:150] + "...",
                                "metadata": meta
                            })
                
                suggestions.append("📅 Use surface_recent_context for broader activity overview")
            
            elif primary_pattern == "bridge":
                # For bridges, look for related bridges and concepts
                bridge_results = chroma.search_context(
                    collection_name="float_bridges",
                    query=text[:200],
                    limit=3
                )
                
                for result in bridge_results:
                    if result.get("id") != doc_id:
                        related_context.append({
                            "type": "related_bridge",
                            "collection": "float_bridges",
                            "preview": result.get("content", "")[:150] + "...",
                            "metadata": result.get("metadata", {})
                        })
                
                suggestions.append("🌉 Consider using smart_chroma_query to explore bridge connections")
        
        # Check for context window risk
        total_content = text + "\n".join(r.get("preview", "") for r in related_context)
        is_risky, warning = check_context_window_risk(total_content)
        
        # Generate smart suggestions
        if primary_pattern == "gotcha":
            suggestions.append("🐛 Debug discovery captured! Consider creating a bridge:: if this connects to other insights")
        elif primary_pattern == "eureka":
            suggestions.append("💡 Breakthrough captured! Consider highlighting related concepts or creating bridges")
        elif primary_pattern == "decision":
            suggestions.append("⚖️ Decision logged! Use smart_chroma_query to review related decisions later")
        elif len(patterns_found) > 1:
            suggestions.append(f"🔗 Multi-pattern detected ({', '.join(patterns_found)}). Rich context captured!")
        
        response = {
            "captured": captured_info,
            "related_context": related_context,
            "suggestions": suggestions,
            "pattern_analysis": {
                "primary": primary_pattern,
                "all_patterns": patterns_found,
                "target_collection": target_collection,
                "ttl_hours": ttl if ttl > 0 else "permanent"
            }
        }
        
        if warning:
            response["warning"] = warning
        
        return response
        
    except Exception as e:
        return {
            "error": f"Smart pattern processing failed: {str(e)}",
            "captured": False,
            "fallback_info": captured_info,
            "suggestion": "Try using capture_pattern or process_context_marker for simpler processing"
        }

async def get_recent_context_resource() -> Dict[str, Any]:
    """Expose recent active context as a resource.
    
    This makes your active_context_stream directly accessible
    to MCP clients without needing to call tools.
    """
    try:
        chroma = get_chroma_client()
        
        # Get last 6 hours of context
        results = chroma.query_recent_context(
            collection_name="active_context_stream",
            hours=6,
            limit=10
        )
        
        # Format for resource consumption
        context_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context_window": "6_hours",
            "total_entries": len(results.get("documents", [])),
            "entries": []
        }
        
        for doc, meta, doc_id in zip(
            results.get("documents", []),
            results.get("metadatas", []), 
            results.get("ids", [])
        ):
            context_data["entries"].append({
                "id": doc_id,
                "content": doc,
                "timestamp": meta.get("timestamp", ""),
                "project": meta.get("project", ""),
                "mode": meta.get("mode", ""),
                "patterns": meta.get("patterns_found", ""),
                "preview": doc[:200] + "..." if len(doc) > 200 else doc
            })
        
        return {
            "uri": "context://active/recent",
            "mimeType": "application/json",
            "text": json.dumps(context_data, indent=2)
        }
        
    except Exception as e:
        # Return error as JSON resource
        error_data = {
            "error": f"Failed to load recent context: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fallback": "Use query_recent_context tool instead"
        }
        
        return {
            "uri": "context://active/recent",
            "mimeType": "application/json", 
            "text": json.dumps(error_data, indent=2)
        }

