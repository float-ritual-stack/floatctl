#!/usr/bin/env python3
"""Main entry point for the Evna Context Concierge MCP server."""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

from mcp.server.fastmcp import FastMCP

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

# Suppress all logging
import logging

# Completely disable logging
logging.disable(logging.CRITICAL)

# Configure root logger to be completely silent
logging.basicConfig(
    level=logging.CRITICAL + 1,
    handlers=[logging.NullHandler()]
)

# Silence all known chatty loggers
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


# === CHROMADB COLLECTION OPERATIONS ===

@mcp.tool()
async def chroma_list_collections(
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Dict[str, Any]:
    """List all collection names in the ChromaDB database.
    
    Args:
        limit: Optional maximum number of collections to return
        offset: Optional number of collections to skip before returning results
    
    Returns:
        Dictionary with collection names and metadata, plus context window warnings if needed
    """
    track_usage("chroma_list", f"limit={limit}, offset={offset}")
    
    try:
        chroma = get_chroma_client()
        collections = chroma.list_collections()
        
        if not collections:
            return {
                "collections": [],
                "count": 0,
                "message": "No collections found in database"
            }
        
        collection_names = [coll.name for coll in collections]
        
        # Apply limit and offset manually if specified
        if offset:
            collection_names = collection_names[offset:]
        if limit:
            collection_names = collection_names[:limit]
        
        # Check for context window risk if returning many collections
        total_content = "\n".join(collection_names)
        is_risky, warning = check_context_window_risk(total_content)
        
        result = {
            "collections": collection_names,
            "count": len(collection_names)
        }
        
        if warning:
            result["warning"] = warning
            result["suggestion"] = "Consider using limit parameter to reduce result size"
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to list collections: {str(e)}",
            "collections": [],
            "count": 0
        }


@mcp.tool()
async def chroma_create_collection(
    collection_name: str,
    metadata: Optional[Dict[str, Any]] = None,
    embedding_function: str = "default"
) -> Dict[str, Any]:
    """Create a new ChromaDB collection.
    
    Args:
        collection_name: Name of the collection to create
        metadata: Optional metadata dictionary to associate with the collection
        embedding_function: Embedding function to use ("default", "openai", etc.)
    
    Returns:
        Success confirmation with collection details
    """
    track_usage("chroma_create", collection_name)
    
    try:
        chroma = get_chroma_client()
        
        # Check if collection already exists
        if chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' already exists",
                "success": False,
                "suggestion": "Use chroma_get_collection_info to inspect existing collection"
            }
        
        # Create the collection using wrapper method
        collection = chroma.create_collection(
            name=collection_name,
            metadata=metadata or {}
        )
        
        return {
            "success": True,
            "collection_name": collection_name,
            "message": f"Successfully created collection '{collection_name}'",
            "metadata": metadata or {}
        }
        
    except Exception as e:
        return {
            "error": f"Failed to create collection '{collection_name}': {str(e)}",
            "success": False
        }


@mcp.tool()
async def chroma_get_collection_info(
    collection_name: str,
    include_sample: bool = True,
    sample_limit: int = 3
) -> Dict[str, Any]:
    """Get detailed information about a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection to inspect
        include_sample: Whether to include sample documents
        sample_limit: Number of sample documents to include
    
    Returns:
        Collection metadata, document count, and optional sample documents
    """
    track_usage("chroma_info", collection_name)
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "exists": False,
                "suggestion": "Use chroma_list_collections to see available collections"
            }
        
        count = chroma.count_documents(collection_name)
        metadata = chroma.get_collection_metadata(collection_name)
        
        result = {
            "collection_name": collection_name,
            "exists": True,
            "document_count": count,
            "metadata": metadata or {}
        }
        
        # Include sample documents if requested and collection has documents
        if include_sample and count > 0:
            try:
                sample = chroma.peek_collection(collection_name, limit=min(sample_limit, count))
                result["sample_documents"] = {
                    "ids": sample.get("ids", []),
                    "documents": sample.get("documents", []),
                    "metadatas": sample.get("metadatas", [])
                }
                
                # Check context window risk for sample
                sample_content = "\n".join(sample.get("documents", []))
                is_risky, warning = check_context_window_risk(sample_content)
                if warning:
                    result["warning"] = warning
                    
            except Exception as sample_error:
                result["sample_error"] = f"Could not retrieve sample: {str(sample_error)}"
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to get collection info for '{collection_name}': {str(e)}",
            "exists": False
        }


@mcp.tool()
async def chroma_get_collection_count(collection_name: str) -> Dict[str, Any]:
    """Get the number of documents in a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection to count
    
    Returns:
        Document count for the specified collection
    """
    track_usage("chroma_count", collection_name)
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "count": 0,
                "exists": False
            }
        
        count = chroma.count_documents(collection_name)
        
        return {
            "collection_name": collection_name,
            "count": count,
            "exists": True
        }
        
    except Exception as e:
        return {
            "error": f"Failed to count documents in '{collection_name}': {str(e)}",
            "count": 0,
            "exists": False
        }


@mcp.tool()
async def chroma_modify_collection(
    collection_name: str,
    new_name: Optional[str] = None,
    new_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Modify a ChromaDB collection's name or metadata.
    
    Args:
        collection_name: Current name of the collection to modify
        new_name: Optional new name for the collection
        new_metadata: Optional new metadata to replace existing metadata
    
    Returns:
        Success confirmation with details of what was modified
    """
    track_usage("chroma_modify", collection_name)
    
    if not new_name and not new_metadata:
        return {
            "error": "Must provide either new_name or new_metadata to modify",
            "success": False
        }
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "success": False
            }
        
        # Perform the modification using wrapper method
        chroma.modify_collection(collection_name, new_name=new_name, new_metadata=new_metadata)
        
        modified_aspects = []
        if new_name:
            modified_aspects.append(f"name: '{collection_name}' → '{new_name}'")
        if new_metadata:
            modified_aspects.append("metadata updated")
        
        return {
            "success": True,
            "original_name": collection_name,
            "new_name": new_name or collection_name,
            "modifications": modified_aspects,
            "message": f"Successfully modified collection: {', '.join(modified_aspects)}"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to modify collection '{collection_name}': {str(e)}",
            "success": False
        }


@mcp.tool()
async def chroma_delete_collection(
    collection_name: str,
    confirm: bool = False
) -> Dict[str, Any]:
    """Delete a ChromaDB collection and all its documents.
    
    Args:
        collection_name: Name of the collection to delete
        confirm: Must be True to actually delete (safety measure)
    
    Returns:
        Success confirmation or error details
    """
    track_usage("chroma_delete", collection_name)
    
    if not confirm:
        return {
            "error": "Collection deletion requires confirm=True parameter",
            "success": False,
            "warning": f"This will permanently delete collection '{collection_name}' and all its documents",
            "suggestion": "Call again with confirm=True if you're sure"
        }
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "success": False
            }
        
        # Get document count before deletion for confirmation
        doc_count = chroma.count_documents(collection_name)
        
        # Delete the collection using wrapper method
        chroma.delete_collection(collection_name)
        
        return {
            "success": True,
            "collection_name": collection_name,
            "documents_deleted": doc_count,
            "message": f"Successfully deleted collection '{collection_name}' with {doc_count} documents"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to delete collection '{collection_name}': {str(e)}",
            "success": False
        }


# Import the hybrid extractor at module level
try:
    from floatctl.float_extractor_hybrid import create_extractor
    _hybrid_extractor = None
    HYBRID_EXTRACTOR_AVAILABLE = True
except ImportError:
    _hybrid_extractor = None
    HYBRID_EXTRACTOR_AVAILABLE = False
    logger.warning("float_extractor_hybrid not available, using legacy regex parsing")

def get_hybrid_extractor():
    """Get or create the hybrid extractor singleton."""
    global _hybrid_extractor
    if HYBRID_EXTRACTOR_AVAILABLE and _hybrid_extractor is None:
        _hybrid_extractor = create_extractor()
    return _hybrid_extractor

def parse_any_pattern(text: str) -> Dict[str, Any]:
    """🧠 Advanced FLOAT pattern parser using hybrid LangExtract/regex extraction.
    
    This function is the core pattern recognition engine for FLOAT consciousness patterns.
    It replaces the broken single-pattern regex with intelligent multi-pattern extraction.
    
    🎯 KEY IMPROVEMENT: Captures ALL patterns in multi-pattern lines (not just first!)
    
    WHAT IT DOES:
    -------------
    1. Extracts ALL :: patterns from text (not just the first one)
    2. Uses LangExtract API for fuzzy compilation when available
    3. Falls back to enhanced regex when API unavailable
    4. Preserves metadata and attributes from nested patterns
    5. Maintains character-level position tracking
    
    WHEN TO USE:
    -----------
    - Processing any text with :: patterns
    - Capturing consciousness technology markers
    - Extracting metadata from conversation exports
    - Parsing multi-pattern lines (the evna killer case)
    
    EXAMPLES:
    --------
    >>> # Single pattern (works in both old and new)
    >>> parse_any_pattern("ctx::2025-08-14 @ 3PM - working")
    {
        "patterns_found": ["ctx"],
        "primary_pattern": "ctx",
        "ctx_content": "2025-08-14 @ 3PM - working",
        "timestamp": "2025-08-14 @ 3PM",
        ...
    }
    
    >>> # Multi-pattern line (BROKEN in old evna, WORKS here!)
    >>> parse_any_pattern("eureka:: Found bug! decision:: Fix tomorrow bridge:: create")
    {
        "patterns_found": ["eureka", "decision", "bridge"],  # ALL 3 patterns!
        "primary_pattern": "eureka",
        "eureka_content": "Found bug!",
        "decision_content": "Fix tomorrow",
        "bridge_content": "create",
        "extraction_method": "langextract",  # or "mock" if API unavailable
        ...
    }
    
    >>> # Complex nested metadata
    >>> parse_any_pattern("ctx::morning [mode:: focus] [project:: airbender]")
    {
        "patterns_found": ["ctx"],
        "primary_pattern": "ctx",
        "ctx_content": "morning [mode:: focus] [project:: airbender]",
        "mode": "focus",
        "project": "airbender",
        ...
    }
    
    >>> # Persona patterns
    >>> parse_any_pattern('karen:: "Honey, stretch" lf1m:: *body awareness*')
    {
        "patterns_found": ["karen", "lf1m"],
        "primary_pattern": "karen",
        "karen_content": '"Honey, stretch"',
        "lf1m_content": "*body awareness*",
        "persona_speakers": "karen,lf1m",
        ...
    }
    
    TECHNICAL DETAILS:
    -----------------
    - Uses hybrid extractor with automatic API/mock fallback
    - LangExtract provides fuzzy compilation for natural patterns
    - Mock regex still captures ALL patterns (unlike old evna)
    - Returns metadata dict compatible with ChromaDB storage
    - Tracks extraction method for debugging
    
    RETURNS:
    -------
    Dict[str, Any] with:
        - patterns_found: List of pattern types found
        - primary_pattern: The first/main pattern type
        - {pattern}_content: Content for each pattern
        - extraction_method: "langextract", "mock", or "legacy"
        - Additional metadata extracted from patterns
    
    NOTES:
    -----
    - This fixes evna's core failure of only capturing first pattern
    - Even without API key, mock mode is better than old regex
    - Gracefully degrades: always returns results
    - Backward compatible with existing code
    """
    metadata = {}
    patterns_found = []
    
    # Try hybrid extractor first if available
    extractor = get_hybrid_extractor()
    if extractor:
        try:
            # Use the hybrid extractor for intelligent pattern recognition
            result = extractor.extract(text)
            
            # Convert hybrid extractor results to metadata format
            for pattern in result.get("patterns", []):
                pattern_type = pattern["type"].lower().strip()
                pattern_content = pattern["content"].strip()
                
                patterns_found.append({
                    "type": pattern_type,
                    "content": pattern_content,
                    "full_match": f"{pattern_type}::{pattern_content}"
                })
                
                # Store the pattern content
                metadata[f"{pattern_type}_content"] = pattern_content
                
                # Add any attributes from the pattern
                for attr_key, attr_val in pattern.get("attributes", {}).items():
                    metadata[attr_key] = attr_val
            
            # Track extraction method for debugging
            metadata["extraction_method"] = result.get("method", "unknown")
            
        except Exception as e:
            logger.warning(f"Hybrid extractor failed, falling back to legacy: {e}")
            # Fall through to legacy parsing below
    
    # Legacy regex fallback (if hybrid not available or failed)
    if not patterns_found:
        # Find ALL :: patterns in the text - simpler approach
        all_patterns = re.findall(r'([a-zA-Z_-]+)::\s*([^\n]*)', text, re.IGNORECASE)
        
        for pattern_name, pattern_content in all_patterns:
            pattern_name = pattern_name.lower().strip()
            pattern_content = pattern_content.strip()
            
            patterns_found.append({
                "type": pattern_name,
                "content": pattern_content,
                "full_match": f"{pattern_name}::{pattern_content}"
            })
            
            # Store the pattern content
            metadata[f"{pattern_name}_content"] = pattern_content
        
        metadata["extraction_method"] = "legacy"
    
    # If we found patterns, set the primary type
    if patterns_found:
        metadata["patterns_found"] = [p["type"] for p in patterns_found]
        metadata["primary_pattern"] = patterns_found[0]["type"]
        
        # Track personas if found
        persona_types = ["karen", "lf1m", "sysop", "evna", "qtb"]
        found_personas = [p["type"] for p in patterns_found if p["type"] in persona_types]
        if found_personas:
            metadata["persona_speakers"] = ",".join(found_personas)
    
    # Special handling for ctx:: patterns (preserve existing logic)
    ctx_match = re.search(r'ctx::\s*([^\n]+)', text, re.IGNORECASE)
    if ctx_match:
        ctx_line = ctx_match.group(1)
        metadata.update(parse_ctx_metadata(ctx_line))
    
    return metadata

def parse_ctx_metadata(ctx_line: str) -> Dict[str, Any]:
    """Parse ctx:: specific metadata with auto-timestamp when missing/invalid."""
    metadata = {}
    timestamp_found = False
    
    # Extract timestamp (flexible format)
    timestamp_patterns = [
        r'(\d{4}-\d{2}-\d{2})\s*[@\-]?\s*(\d{1,2}:\d{2}:\d{2})\s*(AM|PM)?',  # @ or - with seconds
        r'(\d{4}-\d{2}-\d{2})\s*[@\-]?\s*(\d{1,2}:\d{2})\s*(AM|PM)?',        # @ or - without seconds
        r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2}:\d{2})',                       # space separator
    ]
    
    for pattern in timestamp_patterns:
        time_match = re.search(pattern, ctx_line, re.IGNORECASE)
        if time_match:
            try:
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
                
                # Validate timestamp is reasonable (not in future, not too old)
                now = datetime.now(timezone.utc)
                dt = dt.replace(tzinfo=timezone.utc)
                
                # Reject if more than 1 hour in future or more than 1 year old
                if dt > now + timedelta(hours=1) or dt < now - timedelta(days=365):
                    raise ValueError("Timestamp out of reasonable range")
                
                metadata['timestamp'] = dt.isoformat()
                metadata['timestamp_unix'] = int(dt.timestamp())
                timestamp_found = True
                break
                
            except (ValueError, IndexError):
                # Invalid timestamp format or unreasonable date, continue to next pattern
                continue
    
    # Auto-add current timestamp if none found or all were invalid
    if not timestamp_found:
        now = datetime.now(timezone.utc)
        metadata['timestamp'] = now.isoformat()
        metadata['timestamp_unix'] = int(now.timestamp())
        metadata['auto_timestamp'] = True  # Flag to indicate we added this
    
    # Extract [key:: value] patterns from the ctx line
    pattern_matches = re.findall(r'\[([^:]+)::\s*([^\]]+)\]', ctx_line)
    for key, value in pattern_matches:
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

# Prompt library - your frequently used prompts
PROMPT_LIBRARY = {
    "consciousness_archaeology": {
        "prompt": """I need you to perform consciousness archaeology on this conversation/document. Look for:

- Hidden patterns and recurring themes
- Unconscious assumptions being made
- Power dynamics and whose voices are centered/marginalized  
- What's being said vs what's being avoided
- Emotional undertones and energy shifts
- Places where authentic self breaks through performative layers
- Moments of genuine insight vs surface-level analysis
- How language choices reveal deeper beliefs
- What this reveals about the person's relationship to themselves/others/work

Be direct, insightful, and don't hold back. I want the real archaeology, not polite observations.""",
        "tags": ["analysis", "consciousness", "archaeology", "patterns"],
        "usage_count": 0
    },
    
    "ritual_computing": {
        "prompt": """Help me design a ritual computing protocol for this situation. Consider:

- What repetitive actions create consciousness change?
- How can structured data serve meaning-making?
- What boundaries need to be established?
- How does this serve authentic human experience?
- What would make this feel sacred rather than mechanical?
- How can technology amplify rather than replace human ritual?

Focus on practical, implementable protocols that honor both efficiency and meaning.""",
        "tags": ["ritual", "computing", "protocol", "consciousness"],
        "usage_count": 0
    },
    
    "neuroqueer_analysis": {
        "prompt": """Analyze this through a neuroqueer lens. Look for:

- How neurotypical assumptions are embedded
- Where masking or performance might be happening
- Opportunities for more authentic expression
- How systems could be redesigned for neurodivergent thriving
- What accommodations or modifications would help
- How to honor different processing styles
- Ways to reduce cognitive load and overwhelm

Be specific and actionable, not just theoretical.""",
        "tags": ["neuroqueer", "analysis", "accessibility", "authenticity"],
        "usage_count": 0
    },
    
    "shack_not_cathedral": {
        "prompt": """Apply 'shacks not cathedrals' philosophy to this. Help me:

- Strip away unnecessary complexity
- Focus on what actually serves the user (me)
- Identify over-engineering or premature abstraction
- Find the minimal viable solution
- Prioritize working over perfect
- Build for iteration, not permanence
- Make it maintainable by one person
- Optimize for immediate utility

What's the shack version of this?""",
        "tags": ["philosophy", "simplicity", "pragmatic", "minimal"],
        "usage_count": 0
    },
    
    "context_crunch": {
        "prompt": """I'm hitting context limits. Help me:

1. Identify the core 20% that gives 80% of the value
2. Summarize key decisions and their rationale
3. Extract actionable next steps
4. Preserve essential context for continuation
5. Note what can be safely discarded
6. Create a bridge to the next conversation

Be ruthless about cutting fluff while preserving essence.""",
        "tags": ["context", "summarization", "efficiency", "continuation"],
        "usage_count": 0
    }
}

def search_prompts(query: str) -> List[Dict[str, Any]]:
    """Search prompt library by tags or content."""
    results = []
    query_lower = query.lower()
    
    for name, prompt_data in PROMPT_LIBRARY.items():
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


# === CHROMADB DOCUMENT OPERATIONS ===

@mcp.tool()
async def chroma_add_documents(
    collection_name: str,
    documents: List[str],
    ids: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Add documents to a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection to add documents to
        documents: List of text documents to add
        ids: List of unique IDs for the documents (must match documents length)
        metadatas: Optional list of metadata dictionaries for each document
    
    Returns:
        Success confirmation with details of documents added
    """
    track_usage("chroma_add", f"{collection_name}:{len(documents)} docs")
    
    if not documents:
        return {
            "error": "Documents list cannot be empty",
            "success": False
        }
    
    if not ids:
        return {
            "error": "IDs list is required and cannot be empty",
            "success": False
        }
    
    if len(ids) != len(documents):
        return {
            "error": f"Number of IDs ({len(ids)}) must match number of documents ({len(documents)})",
            "success": False
        }
    
    if metadatas and len(metadatas) != len(documents):
        return {
            "error": f"Number of metadatas ({len(metadatas)}) must match number of documents ({len(documents)})",
            "success": False
        }
    
    # Check for empty IDs
    if any(not str(id).strip() for id in ids):
        return {
            "error": "IDs cannot be empty strings",
            "success": False
        }
    
    try:
        chroma = get_chroma_client()
        
        # Get or create collection
        if not chroma.collection_exists(collection_name):
            chroma.create_collection(collection_name)
        
        # Check for duplicate IDs
        try:
            existing = chroma.get_documents(collection_name, ids=ids, include=[])
            existing_ids = existing.get("ids", [])
            if existing_ids:
                return {
                    "error": f"Duplicate IDs found: {existing_ids}",
                    "success": False,
                    "suggestion": "Use chroma_update_documents to update existing documents"
                }
        except Exception:
            # If get fails, assume IDs don't exist (which is fine)
            pass
        
        # Check context window risk
        total_content = "\n".join(documents)
        is_risky, warning = check_context_window_risk(total_content)
        
        # Add documents using wrapper method
        chroma.add_documents(
            collection_name=collection_name,
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        
        result = {
            "success": True,
            "collection_name": collection_name,
            "documents_added": len(documents),
            "message": f"Successfully added {len(documents)} documents to '{collection_name}'"
        }
        
        if warning:
            result["warning"] = warning
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to add documents to '{collection_name}': {str(e)}",
            "success": False
        }


@mcp.tool()
async def chroma_query_documents(
    collection_name: str,
    query_texts: List[str],
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
    where_document: Optional[Dict[str, Any]] = None,
    include: List[str] = ["documents", "metadatas", "distances"]
) -> Dict[str, Any]:
    """Query documents from a ChromaDB collection using semantic search.
    
    Args:
        collection_name: Name of the collection to query
        query_texts: List of query texts to search for
        n_results: Number of results to return per query (default: 5)
        where: Optional metadata filters (e.g., {"author": "john"} or {"score": {"$gt": 0.8}})
        where_document: Optional document content filters
        include: What to include in response (documents, metadatas, distances, embeddings)
    
    Returns:
        Query results with documents, metadata, and distances
    """
    track_usage("chroma_query", f"{collection_name}:{len(query_texts)} queries")
    
    if not query_texts:
        return {
            "error": "Query texts list cannot be empty",
            "results": {}
        }
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "results": {},
                "suggestion": "Use chroma_list_collections to see available collections"
            }
        
        # Perform the query using wrapper method
        results = chroma.query_documents(
            collection_name=collection_name,
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include
        )
        
        # Check context window risk
        if "documents" in results:
            all_docs = []
            for doc_list in results["documents"]:
                all_docs.extend(doc_list)
            total_content = "\n".join(all_docs)
            is_risky, warning = check_context_window_risk(total_content)
        else:
            warning = None
        
        response = {
            "collection_name": collection_name,
            "query_count": len(query_texts),
            "results_per_query": n_results,
            "results": results
        }
        
        if warning:
            response["warning"] = warning
            response["suggestion"] = "Consider reducing n_results or using more specific queries"
        
        return response
        
    except Exception as e:
        return {
            "error": f"Failed to query '{collection_name}': {str(e)}",
            "results": {}
        }


@mcp.tool()
async def chroma_get_documents(
    collection_name: str,
    ids: Optional[List[str]] = None,
    where: Optional[Dict[str, Any]] = None,
    where_document: Optional[Dict[str, Any]] = None,
    include: List[str] = ["documents", "metadatas"],
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Dict[str, Any]:
    """Get documents from a ChromaDB collection by ID or filters.
    
    Args:
        collection_name: Name of the collection to get documents from
        ids: Optional list of specific document IDs to retrieve
        where: Optional metadata filters (e.g., {"author": "john"})
        where_document: Optional document content filters
        include: What to include in response (documents, metadatas, embeddings)
        limit: Optional maximum number of documents to return
        offset: Optional number of documents to skip
    
    Returns:
        Retrieved documents with their IDs and requested metadata
    """
    track_usage("chroma_get", f"{collection_name}:{len(ids) if ids else 'filtered'}")
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "documents": {},
                "suggestion": "Use chroma_list_collections to see available collections"
            }
        
        # Get documents using wrapper method
        results = chroma.get_documents(
            collection_name=collection_name,
            ids=ids,
            where=where,
            limit=limit,
            offset=offset,
            include=include
        )
        
        # Check context window risk
        if "documents" in results and results["documents"]:
            total_content = "\n".join(results["documents"])
            is_risky, warning = check_context_window_risk(total_content)
        else:
            warning = None
        
        response = {
            "collection_name": collection_name,
            "document_count": len(results.get("ids", [])),
            "results": results
        }
        
        if warning:
            response["warning"] = warning
            response["suggestion"] = "Consider using limit parameter or more specific filters"
        
        return response
        
    except Exception as e:
        return {
            "error": f"Failed to get documents from '{collection_name}': {str(e)}",
            "documents": {}
        }


@mcp.tool()
async def chroma_update_documents(
    collection_name: str,
    ids: List[str],
    documents: Optional[List[str]] = None,
    metadatas: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Update existing documents in a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection containing documents to update
        ids: List of document IDs to update (required)
        documents: Optional list of new document texts (must match IDs length if provided)
        metadatas: Optional list of new metadata dicts (must match IDs length if provided)
    
    Returns:
        Success confirmation with details of documents updated
    """
    track_usage("chroma_update", f"{collection_name}:{len(ids)} docs")
    
    if not ids:
        return {
            "error": "IDs list cannot be empty",
            "success": False
        }
    
    if not documents and not metadatas:
        return {
            "error": "Must provide either documents or metadatas to update",
            "success": False
        }
    
    if documents and len(documents) != len(ids):
        return {
            "error": f"Number of documents ({len(documents)}) must match number of IDs ({len(ids)})",
            "success": False
        }
    
    if metadatas and len(metadatas) != len(ids):
        return {
            "error": f"Number of metadatas ({len(metadatas)}) must match number of IDs ({len(ids)})",
            "success": False
        }
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "success": False
            }
        
        # Check context window risk if updating documents
        if documents:
            total_content = "\n".join(documents)
            is_risky, warning = check_context_window_risk(total_content)
        else:
            warning = None
        
        # Update documents using wrapper method
        chroma.update_documents(
            collection_name=collection_name,
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        updated_aspects = []
        if documents:
            updated_aspects.append("documents")
        if metadatas:
            updated_aspects.append("metadatas")
        
        result = {
            "success": True,
            "collection_name": collection_name,
            "documents_updated": len(ids),
            "updated_aspects": updated_aspects,
            "message": f"Successfully updated {len(ids)} documents in '{collection_name}' ({', '.join(updated_aspects)})"
        }
        
        if warning:
            result["warning"] = warning
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to update documents in '{collection_name}': {str(e)}",
            "success": False
        }


@mcp.tool()
async def chroma_delete_documents(
    collection_name: str,
    ids: List[str]
) -> Dict[str, Any]:
    """Delete documents from a ChromaDB collection by ID.
    
    Args:
        collection_name: Name of the collection to delete documents from
        ids: List of document IDs to delete
    
    Returns:
        Success confirmation with details of documents deleted
    """
    track_usage("chroma_delete_docs", f"{collection_name}:{len(ids)} docs")
    
    if not ids:
        return {
            "error": "IDs list cannot be empty",
            "success": False
        }
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "success": False
            }
        
        # Delete documents using wrapper method
        chroma.delete_documents(collection_name, ids=ids)
        
        return {
            "success": True,
            "collection_name": collection_name,
            "documents_deleted": len(ids),
            "message": f"Successfully deleted {len(ids)} documents from '{collection_name}'"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to delete documents from '{collection_name}': {str(e)}",
            "success": False
        }


@mcp.tool()
async def chroma_peek_collection(
    collection_name: str,
    limit: int = 5
) -> Dict[str, Any]:
    """Peek at documents in a ChromaDB collection (full version).
    
    Args:
        collection_name: Name of the collection to peek into
        limit: Number of documents to peek at (default: 5)
    
    Returns:
        Sample documents from the collection with IDs, documents, and metadata
    """
    track_usage("chroma_peek", f"{collection_name}:{limit}")
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "results": {},
                "suggestion": "Use chroma_list_collections to see available collections"
            }
        
        # Special handling for house_of_claude_fucks - let it explode as intended
        if collection_name == "house_of_claude_fucks":
            collection = chroma.get_collection(collection_name)
            results = collection.peek(limit=limit)  # This will throw numpy errors intentionally
            return results
        
        # Safe peek for all other collections using wrapper method
        results = chroma.peek_collection(collection_name, limit=limit)
        
        # Check context window risk
        if "documents" in results and results["documents"]:
            total_content = "\n".join(results["documents"])
            is_risky, warning = check_context_window_risk(total_content)
        else:
            warning = None
        
        response = {
            "collection_name": collection_name,
            "peek_limit": limit,
            "results": results
        }
        
        if warning:
            response["warning"] = warning
        
        return response
        
    except Exception as e:
        return {
            "error": f"Failed to peek collection '{collection_name}': {str(e)}",
            "results": {}
        }


# === CONSCIOUSNESS TECHNOLOGY OPERATIONS ===

@mcp.tool()
async def process_context_marker(
    message: str,
    auto_capture: bool = True
) -> Dict[str, Any]:
    """Process a message containing ctx:: marker.
    
    Extracts metadata, captures to active_context_stream,
    and returns related recent context for continuity.
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
async def get_prompt(
    query: str
) -> Dict[str, Any]:
    """Get a ritual pattern from float_ritual collection.
    
    This searches sophisticated ritual patterns with rich metadata, not simple text prompts.
    Returns full ritual structures with meta-prompts, extended prompts, output schemas, and metadata.
    
    Available Rituals (as of 2025-08):
    - SESSION_SYNC: Multi-agent coordination between Desktop Daddy + Cowboy Claude
    - FLOAT.ANNOTATE: Design documentation generation with FLOAT schema
    
    Query Examples:
    - 'sync' or 'session sync' → SESSION_SYNC coordination ritual
    - 'annotate' or 'design' → FLOAT.ANNOTATE documentation pattern
    - 'coordination' → Rituals for multi-agent work
    - 'desktop cowboy' → Desktop Daddy + Cowboy Claude sync patterns
    
    Returns:
    - ritual_id: Identifier for the ritual pattern
    - content: Full ritual documentation with prompts and structure
    - meta_prompt: Quick summary for immediate use
    - metadata: Rich context including:
      - mode_compatibility: Which modes this ritual works in
      - trigger_patterns: What phrases activate this ritual
      - coordination: Solo vs multi-agent requirements
      - flow_state: When to use (session_start, mid_flow, reflection)
      - complexity: How involved the ritual is
    
    The ritual collection grows as you add patterns. Each ritual is a sophisticated
    prompt structure, not a simple text string. Think of this as your ritual
    concierge, not a prompt library.
    
    Example: 'get me the sync ritual' returns the full SESSION_SYNC pattern
    for establishing semantic IDs and coordinating between Claude instances.
    """
    track_usage("prompt_search", query)
    
    # Track prompt requests
    _usage_patterns["prompt_requests"][query] = _usage_patterns["prompt_requests"].get(query, 0) + 1
    
    try:
        chroma = get_chroma_client()
        
        # Query the REAL ritual collection using search_context (the method that works!)
        results = chroma.search_context(
            collection_name="float_ritual",
            query=query,
            limit=5
        )
        
        if not results:
            return {
                "error": f"No rituals found for '{query}'",
                "suggestion": "Try: session sync, annotation, coordination, or check float_ritual collection"
            }
        
        # Get the best match - search_context returns list of dicts
        best_result = results[0] if results else None
        
        if not best_result:
            return {
                "error": f"No ritual content found for '{query}'",
                "suggestion": "The float_ritual collection may be empty or query didn't match"
            }
        
        best_doc = best_result.get("content", "")
        best_meta = best_result.get("metadata", {})
        best_id = best_result.get("id", "unknown")
        
        if not best_doc:
            return {
                "error": f"No ritual content found for '{query}'",
                "suggestion": "The float_ritual collection may be empty or query didn't match"
            }
        
        # Extract the meta-prompt if it exists in the document
        meta_prompt = None
        if "**Meta-Prompt**:" in best_doc:
            lines = best_doc.split('\n')
            for i, line in enumerate(lines):
                if "**Meta-Prompt**:" in line:
                    # Get the text after the marker
                    meta_prompt = line.split("**Meta-Prompt**:")[1].strip()
                    if not meta_prompt and i + 1 < len(lines):
                        # Sometimes it's on the next line
                        meta_prompt = lines[i + 1].strip()
                    break
        
        # Build response with REAL ritual data
        response = {
            "ritual_id": best_id,
            "content": best_doc,
            "meta_prompt": meta_prompt,
            "metadata": best_meta,
            "ritual_type": best_meta.get("ritual_type", "unknown"),
            "mode_compatibility": best_meta.get("mode_compatibility", "all"),
            "trigger_patterns": best_meta.get("trigger_patterns", query),
            "complexity": best_meta.get("complexity", "moderate"),
            "coordination": best_meta.get("coordination", "solo")
        }
        
        # Add other matches if they exist
        if len(results) > 1:
            response["other_matches"] = [r.get("id", "unknown") for r in results[1:3]]  # Show up to 2 other options
        
        return response
        
    except Exception as e:
        logger.error(f"Error querying float_ritual: {str(e)}")
        return {
            "error": f"Failed to query float_ritual collection: {str(e)}",
            "suggestion": "Check if float_ritual collection exists and has content"
        }

@mcp.tool()
async def smart_chroma_query(
    query: str,
    collection: str = "active_context_stream",
    limit: int = 5,
    include_context: bool = True
) -> Dict[str, Any]:
    """Intelligent ChromaDB query with context window protection.
    
    This is your smart proxy to ChromaDB that:
    - Warns about context window risks
    - Provides related context automatically
    - Tracks usage patterns
    - Optimizes multi-hop queries
    """
    track_usage("chroma_query", query)
    
    try:
        chroma = get_chroma_client()
        
        # Check if this looks like a multi-hop query
        recent_queries = _usage_patterns["last_queries"][-3:]  # Last 3 queries
        is_multi_hop = len(recent_queries) >= 2 and all(
            (datetime.now(timezone.utc) - datetime.fromisoformat(q["timestamp"])).total_seconds() < 300  # 5 min
            for q in recent_queries
        )
        
        # Perform the query
        if collection == "active_context_stream":
            results = chroma.search_context(
                collection_name=collection,
                query=query,
                limit=limit
            )
        else:
            # Use generic query for other collections
            results = chroma.query_collection(
                collection_name=collection,
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
        
        # Format results
        formatted_results = []
        total_content = ""
        
        if isinstance(results, list):
            # From search_context
            for item in results:
                content = item.get("content", "")
                formatted_results.append(item)
                total_content += content + "\n"
        else:
            # From query_collection
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            for doc, meta, dist in zip(docs, metas, distances):
                formatted_results.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": dist
                })
                total_content += doc + "\n"
        
        # Check context window risk
        is_risky, warning = check_context_window_risk(total_content)
        
        # Add related context if requested and safe
        related_context = []
        if include_context and not is_risky and len(formatted_results) > 0:
            # Get related context based on first result
            first_result = formatted_results[0]
            if "metadata" in first_result and first_result["metadata"]:
                meta = first_result["metadata"]
                related = chroma.query_recent_context(
                    collection_name=collection,
                    hours=24,
                    project=meta.get("project"),
                    mode=meta.get("mode"),
                    limit=3
                )
                
                for doc, rel_meta, doc_id in zip(
                    related.get("documents", []),
                    related.get("metadatas", []),
                    related.get("ids", [])
                ):
                    related_context.append({
                        "id": doc_id,
                        "preview": doc[:150] + "..." if len(doc) > 150 else doc,
                        "metadata": rel_meta
                    })
        
        response = {
            "results": formatted_results,
            "query": query,
            "collection": collection,
            "result_count": len(formatted_results)
        }
        
        if warning:
            response["warning"] = warning
        
        if related_context:
            response["related_context"] = related_context
        
        if is_multi_hop:
            response["multi_hop_detected"] = True
            response["suggestion"] = "Consider combining recent queries for better context"
        
        # Track result size
        track_usage("chroma_query", query, len(total_content))
        
        return response
        
    except Exception as e:
        return {
            "error": f"Smart query failed: {str(e)}",
            "fallback": "Try using the basic search_context tool"
        }


@mcp.tool()
async def capture_pattern(
    text: str,
    pattern_type: str = "auto"
) -> Dict[str, Any]:
    """Enhanced :: pattern capture with smart context surfacing.
    
    Captures various :: patterns and automatically surfaces relevant context:
    - ctx:: markers with metadata extraction
    - highlight:: important moments
    - decision:: key decisions made
    - eureka:: breakthrough insights
    - gotcha:: debugging discoveries
    - bridge:: connection points
    """
    track_usage("pattern_capture", f"{pattern_type}::{text[:50]}")
    
    # Detect pattern type if auto
    if pattern_type == "auto":
        if "ctx::" in text.lower():
            pattern_type = "context"
        elif "highlight::" in text.lower():
            pattern_type = "highlight"
        elif "decision::" in text.lower():
            pattern_type = "decision"
        elif "eureka::" in text.lower():
            pattern_type = "eureka"
        elif "gotcha::" in text.lower():
            pattern_type = "gotcha"
        elif "bridge::" in text.lower():
            pattern_type = "bridge"
        else:
            pattern_type = "general"
    
    try:
        chroma = get_chroma_client()
        
        # Route to appropriate collection based on pattern type
        collection_map = {
            "context": "active_context_stream",
            "highlight": "float_highlights",
            "decision": "float_dispatch_bay",
            "eureka": "float_wins",
            "gotcha": "active_context_stream",  # Debug info goes to context
            "bridge": "float_bridges",
            "general": "active_context_stream"
        }
        
        collection = collection_map.get(pattern_type, "active_context_stream")
        
        # For ctx:: patterns, use the existing sophisticated parser
        if pattern_type == "context":
            return await process_context_marker(text, auto_capture=True)
        
        # For other patterns, create appropriate metadata
        metadata = {
            "pattern_type": pattern_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "timestamp_unix": int(datetime.now(timezone.utc).timestamp()),
            "captured_by": "evna_mcp"
        }
        
        # Add TTL for non-permanent patterns
        if pattern_type in ["gotcha", "general"]:
            ttl = datetime.now(timezone.utc) + timedelta(hours=72)  # 3 days
            metadata["ttl_expires"] = ttl.isoformat()
            metadata["ttl_expires_unix"] = int(ttl.timestamp())
        
        # Extract additional metadata from text
        pattern_matches = re.findall(r'\[([^:]+)::\s*([^\]]+)\]', text)
        for key, value in pattern_matches:
            metadata[key.strip()] = value.strip()
        
        # Generate document ID
        timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')
        doc_id = f"{pattern_type}_{timestamp_str}_{hash(text[:100]) % 10000:04d}"
        
        # Add to collection
        doc_id = chroma.add_context_marker(
            collection_name=collection,
            document=text,
            metadata=metadata,
            doc_id=doc_id
        )
        
        # Get related context
        related = []
        if pattern_type in ["highlight", "eureka", "bridge"]:
            # For important patterns, find related content
            search_results = chroma.search_context(
                collection_name=collection,
                query=text[:200],  # Use first 200 chars as query
                limit=3
            )
            
            for result in search_results:
                if result.get("id") != doc_id:  # Don't include the one we just added
                    related.append({
                        "preview": result.get("content", "")[:150] + "...",
                        "metadata": result.get("metadata", {})
                    })
        
        return {
            "captured": {
                "id": doc_id,
                "pattern_type": pattern_type,
                "collection": collection,
                "metadata": metadata
            },
            "related_content": related,
            "suggestion": f"Pattern captured to {collection}. Use smart_chroma_query to explore related content."
        }
        
    except Exception as e:
        return {
            "error": f"Pattern capture failed: {str(e)}",
            "pattern_type": pattern_type,
            "fallback": "Try using process_context_marker for ctx:: patterns"
        }


@mcp.tool()
async def get_usage_insights() -> Dict[str, Any]:
    """Get insights about your usage patterns with Evna.
    
    Shows what you query most, context window warnings, and optimization suggestions.
    """
    global _usage_patterns
    
    # Get top queries
    top_queries = sorted(
        _usage_patterns["common_queries"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    # Get top prompt requests
    top_prompts = sorted(
        _usage_patterns["prompt_requests"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    # Analyze recent query patterns
    recent = _usage_patterns["last_queries"][-5:]
    query_types = {}
    for q in recent:
        qtype = q["type"]
        query_types[qtype] = query_types.get(qtype, 0) + 1
    
    # Generate suggestions
    suggestions = []
    
    if _usage_patterns["context_window_warnings"] > 2:
        suggestions.append("⚠️ You've hit context window warnings. Consider using more specific queries or filtering results.")
    
    if query_types.get("chroma_query", 0) > 3:
        suggestions.append("🔍 Lots of ChromaDB queries recently. Consider using multi-hop optimization or saving frequent searches.")
    
    if len(top_prompts) == 0:
        suggestions.append("💡 Try using get_prompt to access your prompt library for common tasks.")
    
    # Check for multi-hop patterns
    multi_hop_count = sum(1 for q in recent if "chroma" in q["type"])
    if multi_hop_count >= 3:
        suggestions.append("🔗 Multi-hop query pattern detected. Consider combining searches for better context.")
    
    return {
        "session_stats": {
            "total_queries": _usage_patterns["query_count"],
            "context_warnings": _usage_patterns["context_window_warnings"],
            "recent_activity": len(recent)
        },
        "top_queries": [{"query": q[0], "count": q[1]} for q in top_queries],
        "top_prompts": [{"prompt": p[0], "count": p[1]} for p in top_prompts],
        "recent_query_types": query_types,
        "suggestions": suggestions,
        "available_tools": [
            "smart_chroma_query - Intelligent ChromaDB access with warnings",
            "get_prompt - Access your prompt library",
            "capture_pattern - Enhanced :: pattern capture",
            "process_context_marker - Advanced ctx:: processing",
            "check_boundary_status - Boundary violation detection"
        ]
    }


@mcp.tool()
async def surface_recent_context(
    hours: int = 6,
    include_patterns: List[str] = None
) -> Dict[str, Any]:
    """Surface recent context automatically when you ask 'what was I working on?'
    
    Intelligently surfaces recent activity across your collections with smart filtering.
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


@mcp.tool()
async def smart_pattern_processor(
    text: str,
    auto_surface_context: bool = True
) -> Dict[str, Any]:
    """The ultimate :: pattern processor - handles ANY pattern intelligently.
    
    This is your one-stop tool for processing any :: pattern:
    - Automatically detects and routes patterns to appropriate collections
    - Surfaces relevant context based on pattern type
    - Provides intelligent suggestions for follow-up actions
    - Warns about context window risks
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
        "decision": "float_dispatch_bay",
        "eureka": "float_wins",
        "gotcha": "active_context_stream",  # Debug info
        "bridge": "float_bridges",
        "concept": "float_dispatch_bay",  # New concepts
        "aka": "float_bridges",  # Aliases/references
        "mode": "active_context_stream",  # Mode changes
        "project": "active_context_stream",  # Project context
        "task": "active_context_stream",  # Task tracking
        "boundary": "active_context_stream"  # Boundary setting
    }
    
    target_collection = collection_routing.get(primary_pattern, "active_context_stream")
    
    # Add standard metadata (ChromaDB compatible - no lists)
    now = datetime.now(timezone.utc)
    metadata.update({
        "timestamp": now.isoformat(),
        "timestamp_unix": int(now.timestamp()),
        "processed_by": "smart_pattern_processor",
        "pattern_count": len(patterns_found),
        "patterns_found_str": ",".join(patterns_found),  # Convert list to string
        "primary_pattern": primary_pattern
    })
    
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
        
        # Capture to appropriate collection
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

@mcp.tool()
async def peek_collection_safe(
    collection_name: str,
    limit: int = 5
) -> Dict[str, Any]:
    """Safely peek at any collection... except house_of_claude_fucks.
    
    Returns clean data for normal collections.
    house_of_claude_fucks intentionally throws numpy errors (by design).
    """
    chroma = get_chroma_client()
    
    # The chaos exception
    if collection_name == "house_of_claude_fucks":
        # Let it explode with numpy - this is intentional
        collection = chroma.get_collection(collection_name)
        return collection.peek(limit=limit)
    
    # For everything else, safe peek without embeddings using wrapper methods
    try:
        results = chroma.get_documents(
            collection_name=collection_name,
            limit=limit,
            include=["documents", "metadatas"]  # NO embeddings = NO numpy
        )
        
        # Format nicely
        return {
            "collection": collection_name,
            "count": chroma.count_documents(collection_name),
            "documents": results.get("documents", []),
            "metadatas": results.get("metadatas", []),
            "ids": results.get("ids", [])
        }
    except Exception as e:
        return {"error": f"Failed to peek: {str(e)}"}

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