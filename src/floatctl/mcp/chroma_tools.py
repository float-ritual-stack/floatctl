"""ChromaDB operations for FLOAT consciousness technology :: chroma_tools.

This module contains all ChromaDB-related MCP tools and utilities.
Extracted from the monolithic mcp_server.py for maintainability.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from floatctl.core.chroma import ChromaClient

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
        collection_name: Name for the new collection
        metadata: Optional metadata for the collection
        embedding_function: Embedding function to use (currently not implemented)
    
    Returns:
        Success status and collection info
    """
    track_usage("chroma_create", collection_name)
    
    try:
        chroma = get_chroma_client()
        
        # Check if collection already exists
        if chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' already exists",
                "success": False,
                "exists": True
            }
        
        # Sanitize metadata for ChromaDB
        safe_metadata = {}
        if metadata:
            safe_metadata = sanitize_metadata_for_chroma(metadata)
        
        # Create the collection
        collection = chroma.create_collection(
            name=collection_name,
            metadata=safe_metadata
        )
        
        return {
            "success": True,
            "collection_name": collection_name,
            "count": collection.count(),
            "metadata": safe_metadata
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
                "exists": False
            }
        
        collection = chroma.get_collection(collection_name)
        count = collection.count()
        
        result = {
            "name": collection_name,
            "count": count,
            "metadata": collection.metadata or {},
            "exists": True
        }
        
        # Add sample documents if requested and collection has documents
        if include_sample and count > 0:
            try:
                sample = collection.peek(limit=min(sample_limit, count))
                result["sample"] = {
                    "documents": sample.get("documents", []),
                    "metadatas": sample.get("metadatas", []),
                    "ids": sample.get("ids", [])
                }
            except Exception as e:
                result["sample_error"] = f"Failed to get sample: {str(e)}"
        
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
        
        collection = chroma.get_collection(collection_name)
        count = collection.count()
        
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
        collection_name: Current name of the collection
        new_name: New name for the collection (if renaming)
        new_metadata: New metadata for the collection
    
    Returns:
        Success status and updated collection info
    """
    track_usage("chroma_modify", collection_name)
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "success": False
            }
        
        collection = chroma.get_collection(collection_name)
        
        # Modify metadata if provided
        if new_metadata:
            safe_metadata = sanitize_metadata_for_chroma(new_metadata)
            collection.modify(metadata=safe_metadata)
        
        # Modify name if provided
        if new_name and new_name != collection_name:
            collection.modify(name=new_name)
            collection_name = new_name  # Update for response
        
        return {
            "success": True,
            "collection_name": collection_name,
            "count": collection.count(),
            "metadata": collection.metadata or {}
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
        confirm: Safety confirmation that user really wants to delete
    
    Returns:
        Success status of the deletion operation
    """
    if not confirm:
        return {
            "error": "Deletion requires explicit confirmation. Set confirm=True to proceed.",
            "collection_name": collection_name,
            "success": False,
            "safety_check": "Confirmation required for destructive operation"
        }
    
    track_usage("chroma_delete", collection_name)
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "success": False
            }
        
        # Get collection info before deletion for logging
        collection = chroma.get_collection(collection_name)
        doc_count = collection.count()
        
        # Delete the collection
        chroma.delete_collection(collection_name)
        
        return {
            "success": True,
            "collection_name": collection_name,
            "documents_deleted": doc_count,
            "message": f"Collection '{collection_name}' and {doc_count} documents successfully deleted"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to delete collection '{collection_name}': {str(e)}",
            "success": False
        }


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
        documents: List of document texts to add
        ids: List of unique IDs for the documents
        metadatas: Optional list of metadata dictionaries for each document
    
    Returns:
        Success status and summary of added documents
    """
    track_usage("chroma_add", f"{collection_name} ({len(documents)} docs)")
    
    try:
        # Validate inputs
        if len(documents) != len(ids):
            return {
                "error": "Number of documents must match number of IDs",
                "success": False
            }
        
        if metadatas and len(metadatas) != len(documents):
            return {
                "error": "Number of metadata entries must match number of documents",
                "success": False
            }
        
        chroma = get_chroma_client()
        
        # Check if collection exists
        if not chroma.collection_exists(collection_name):
            # Auto-create collection if it doesn't exist
            collection = chroma.create_collection(collection_name)
        else:
            collection = chroma.get_collection(collection_name)
        
        # Sanitize metadatas if provided
        safe_metadatas = None
        if metadatas:
            safe_metadatas = [sanitize_metadata_for_chroma(meta) for meta in metadatas]
        
        # Count before adding
        initial_count = collection.count()
        
        # Add the documents
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=safe_metadatas
        )
        
        # Count after adding
        final_count = collection.count()
        added_count = final_count - initial_count
        
        # Check for context window risk with the documents
        total_content = "\n".join(documents)
        is_risky, warning = check_context_window_risk(total_content)
        
        result = {
            "success": True,
            "collection_name": collection_name,
            "documents_added": added_count,
            "total_documents": final_count,
            "new_ids": ids
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
        query_texts: List of query strings to search for
        n_results: Maximum number of results to return per query
        where: Optional metadata filter conditions
        where_document: Optional document content filter conditions
        include: List of fields to include in results
    
    Returns:
        Query results with documents, metadata, and similarity scores
    """
    query_summary = f"{collection_name}: {query_texts[0][:50]}..." if query_texts else collection_name
    track_usage("chroma_query", query_summary, n_results * len(query_texts))
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "results": {}
            }
        
        collection = chroma.get_collection(collection_name)
        
        # Perform the query
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include
        )
        
        # Calculate total content size for context warning
        total_content = ""
        if "documents" in include and results.get("documents"):
            for doc_list in results["documents"]:
                if doc_list:
                    total_content += "\n".join(doc_list)
        
        is_risky, warning = check_context_window_risk(total_content)
        
        response = {
            "collection_name": collection_name,
            "query_texts": query_texts,
            "n_results": n_results,
            "results": results
        }
        
        if warning:
            response["warning"] = warning
            response["suggestion"] = "Consider reducing n_results or using metadata-only queries"
        
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
    """Get documents from a ChromaDB collection by ID or filter conditions.
    
    Args:
        collection_name: Name of the collection to get documents from
        ids: Optional list of specific document IDs to retrieve
        where: Optional metadata filter conditions
        where_document: Optional document content filter conditions
        include: List of fields to include in results
        limit: Optional maximum number of documents to return
        offset: Optional number of documents to skip
    
    Returns:
        Retrieved documents with their metadata
    """
    filter_desc = f"ids={len(ids) if ids else 0}, where={bool(where)}, limit={limit}"
    track_usage("chroma_get", f"{collection_name}: {filter_desc}")
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "documents": {}
            }
        
        collection = chroma.get_collection(collection_name)
        
        # Get documents based on parameters
        results = collection.get(
            ids=ids,
            where=where,
            where_document=where_document,
            include=include,
            limit=limit,
            offset=offset
        )
        
        # Calculate content size for context warning
        total_content = ""
        if "documents" in include and results.get("documents"):
            total_content = "\n".join(results["documents"])
        
        is_risky, warning = check_context_window_risk(total_content)
        
        response = {
            "collection_name": collection_name,
            "count": len(results.get("ids", [])),
            "documents": results
        }
        
        if warning:
            response["warning"] = warning
            response["suggestion"] = "Consider using limit parameter or metadata-only queries"
        
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
        collection_name: Name of the collection containing the documents
        ids: List of document IDs to update
        documents: Optional new document texts (if updating content)
        metadatas: Optional new metadata for the documents
    
    Returns:
        Success status and summary of updated documents
    """
    track_usage("chroma_update", f"{collection_name} ({len(ids)} docs)")
    
    try:
        # Validate inputs
        if documents and len(documents) != len(ids):
            return {
                "error": "Number of documents must match number of IDs",
                "success": False
            }
        
        if metadatas and len(metadatas) != len(ids):
            return {
                "error": "Number of metadata entries must match number of IDs",
                "success": False
            }
        
        if not documents and not metadatas:
            return {
                "error": "Must provide either documents or metadatas to update",
                "success": False
            }
        
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "success": False
            }
        
        collection = chroma.get_collection(collection_name)
        
        # Sanitize metadatas if provided
        safe_metadatas = None
        if metadatas:
            safe_metadatas = [sanitize_metadata_for_chroma(meta) for meta in metadatas]
        
        # Update the documents
        collection.update(
            ids=ids,
            documents=documents,
            metadatas=safe_metadatas
        )
        
        return {
            "success": True,
            "collection_name": collection_name,
            "updated_ids": ids,
            "updated_count": len(ids)
        }
        
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
        Success status and summary of deleted documents
    """
    track_usage("chroma_delete_docs", f"{collection_name} ({len(ids)} docs)")
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "success": False
            }
        
        collection = chroma.get_collection(collection_name)
        
        # Count before deletion
        initial_count = collection.count()
        
        # Delete the documents
        collection.delete(ids=ids)
        
        # Count after deletion
        final_count = collection.count()
        deleted_count = initial_count - final_count
        
        return {
            "success": True,
            "collection_name": collection_name,
            "deleted_ids": ids,
            "deleted_count": deleted_count,
            "remaining_count": final_count
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
        limit: Maximum number of documents to return
    
    Returns:
        Sample documents from the collection with all available fields
    """
    track_usage("chroma_peek", collection_name, limit)
    
    try:
        chroma = get_chroma_client()
        
        if not chroma.collection_exists(collection_name):
            return {
                "error": f"Collection '{collection_name}' does not exist",
                "documents": {},
                "exists": False
            }
        
        collection = chroma.get_collection(collection_name)
        
        if collection.count() == 0:
            return {
                "collection_name": collection_name,
                "count": 0,
                "documents": {},
                "message": "Collection is empty"
            }
        
        # Peek at the collection
        result = collection.peek(limit=limit)
        
        # Calculate content size for context warning
        total_content = ""
        if result.get("documents"):
            total_content = "\n".join(result["documents"])
        
        is_risky, warning = check_context_window_risk(total_content)
        
        response = {
            "collection_name": collection_name,
            "count": collection.count(),
            "sample_size": len(result.get("ids", [])),
            "documents": result
        }
        
        if warning:
            response["warning"] = warning
            response["suggestion"] = "Consider reducing limit parameter"
        
        return response
        
    except Exception as e:
        return {
            "error": f"Failed to peek at '{collection_name}': {str(e)}",
            "documents": {},
            "exists": False
        }