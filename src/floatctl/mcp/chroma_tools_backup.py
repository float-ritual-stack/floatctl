"""ChromaDB operations for FLOAT consciousness technology :: chroma_tools.

This module contains all ChromaDB-related MCP tools and utilities.
Extracted from the monolithic mcp_server.py for maintainability.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from chromadb.api import ChromaClient

# Set up logging
logger = logging.getLogger(__name__)

# Global Chroma client instance
_chroma_client: Optional[ChromaClient] = None

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

# Note: These functions will be imported and registered by the main server module
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


# NOTE: Pattern processing functions moved to floatctl.mcp.patterns module

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
        
        # Sanitize metadatas if provided
        sanitized_metadatas = None
        if metadatas:
            sanitized_metadatas = [sanitize_metadata_for_chroma(m) for m in metadatas]
        
        # Special handling for float_bridges collection to ensure consistent metadata
        if collection_name == "float_bridges":
            # Use centralized bridge creation for each document
            created_ids = []
            for i, (doc, doc_id) in enumerate(zip(documents, ids)):
                # Get metadata for this document
                doc_metadata = sanitized_metadatas[i] if sanitized_metadatas else {}
                
                # Extract bridge_type from metadata or infer from content
                bridge_type = doc_metadata.get("bridge_type", "modular")
                if "complete" in doc.lower():
                    bridge_type = "complete"
                elif "index" in doc.lower():
                    bridge_type = "index"
                
                # Create bridge using centralized function
                created_id = chroma.create_bridge_document(
                    content=doc,
                    metadata=doc_metadata,
                    bridge_id=doc_id,  # Use provided ID if given
                    bridge_type=bridge_type
                )
                created_ids.append(created_id)
            
            # Update result to show actual IDs created
            result = {
                "success": True,
                "collection_name": collection_name,
                "documents_added": len(documents),
                "bridge_ids_created": created_ids,
                "message": f"Successfully added {len(documents)} bridge documents to '{collection_name}' with standardized metadata"
            }
        else:
            # Add documents using wrapper method for non-bridge collections
            chroma.add_documents(
                collection_name=collection_name,
                documents=documents,
                ids=ids,
                metadatas=sanitized_metadatas
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
        
        # Sanitize metadatas if provided
        sanitized_metadatas = None
        if metadatas:
            sanitized_metadatas = [sanitize_metadata_for_chroma(m) for m in metadatas]
        
        # Update documents using wrapper method
        chroma.update_documents(
            collection_name=collection_name,
            ids=ids,
            documents=documents,
            metadatas=sanitized_metadatas
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
