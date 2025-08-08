"""Shared Chroma database utilities for FloatCtl."""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union

import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection

from floatctl.core.logging import get_logger

# Only enable logging if not running as MCP server
import os
if os.environ.get('MCP_SERVER_MODE'):
    # Create a dummy logger that does nothing
    class DummyLogger:
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass
    logger = DummyLogger()
else:
    logger = get_logger(__name__)


class ChromaClient:
    """Wrapper for ChromaDB client with FloatCtl-specific utilities."""
    
    def __init__(self, path: Optional[str] = None):
        """Initialize Chroma client.
        
        Args:
            path: Path to Chroma database. If not provided, uses environment
                  variable FLOATCTL_CHROMA_PATH or config setting.
        """
        if path is None:
            # Check environment variable first
            path = os.environ.get('FLOATCTL_CHROMA_PATH')
            
            if path is None:
                # Try to load from config
                try:
                    from floatctl.core.config import load_config
                    config = load_config()
                    path = str(config.chroma_path)
                except:
                    # Fallback to default
                    path = '/Users/evan/github/chroma-data'
        
        self.path = path
        logger.info("chroma_client_init", path=path)
        
        try:
            # Create settings with telemetry disabled
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
            self.client = chromadb.PersistentClient(path=path, settings=settings)
        except Exception as e:
            logger.error("chroma_client_init_failed", error=str(e), path=path)
            raise
    
    def get_collection(self, name: str) -> Optional[Collection]:
        """Get a collection by name.
        
        Args:
            name: Collection name
            
        Returns:
            Collection object or None if not found
        """
        try:
            return self.client.get_collection(name)
        except Exception as e:
            logger.warning("collection_not_found", name=name, error=str(e))
            return None
    
    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists.
        
        Args:
            name: Collection name
            
        Returns:
            True if collection exists
        """
        try:
            self.client.get_collection(name)
            return True
        except:
            return False
    
    def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Collection:
        """Create a new collection.
        
        Args:
            name: Collection name
            metadata: Optional metadata for the collection
            
        Returns:
            Created collection object
        """
        try:
            collection = self.client.create_collection(name=name, metadata=metadata or {})
            logger.info("collection_created", name=name)
            return collection
        except Exception as e:
            logger.error("collection_create_failed", name=name, error=str(e))
            raise
    
    def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: Collection name to delete
        """
        try:
            self.client.delete_collection(name)
            logger.info("collection_deleted", name=name)
        except Exception as e:
            logger.error("collection_delete_failed", name=name, error=str(e))
            raise
    
    def list_collections(self) -> List[Collection]:
        """List all collections.
        
        Returns:
            List of collection objects
        """
        try:
            collections = self.client.list_collections()
            logger.debug("collections_listed", count=len(collections))
            return collections
        except Exception as e:
            logger.error("collections_list_failed", error=str(e))
            raise
    
    def add_context_marker(
        self,
        collection_name: str,
        document: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None
    ) -> str:
        """Add a context marker document to a collection.
        
        Args:
            collection_name: Name of the collection
            document: Document content
            metadata: Document metadata
            doc_id: Optional document ID (generated if not provided)
            
        Returns:
            Document ID that was added
        """
        collection = self.get_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")
        
        # Generate ID if not provided
        if not doc_id:
            timestamp = metadata.get('timestamp', datetime.now(timezone.utc).isoformat())
            dt = datetime.fromisoformat(timestamp)
            base = f"ctx_{dt.strftime('%Y%m%d_%H%M%S')}"
            
            # Add suffix from metadata
            if 'mode' in metadata:
                suffix = metadata['mode'].replace(' ', '_')[:20]
            elif 'project' in metadata:
                suffix = metadata['project'].split('/')[-1][:20]
            else:
                suffix = "marker"
            
            doc_id = f"{base}_{suffix}"
        
        # Ensure we have unix timestamps
        if 'timestamp' in metadata and 'timestamp_unix' not in metadata:
            dt = datetime.fromisoformat(metadata['timestamp'])
            metadata['timestamp_unix'] = int(dt.timestamp())
        
        if 'ttl_expires' in metadata and 'ttl_expires_unix' not in metadata:
            dt = datetime.fromisoformat(metadata['ttl_expires'])
            metadata['ttl_expires_unix'] = int(dt.timestamp())
        
        # Add document
        collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        logger.info(
            "context_marker_added",
            collection=collection_name,
            doc_id=doc_id,
            metadata_keys=list(metadata.keys())
        )
        
        return doc_id
    
    def query_recent_context(
        self,
        collection_name: str,
        hours: int = 24,
        project: Optional[str] = None,
        mode: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Query recent context with filters.
        
        Args:
            collection_name: Name of the collection
            hours: Number of hours to look back
            project: Optional project filter
            mode: Optional mode filter
            limit: Maximum results
            
        Returns:
            Query results with documents and metadata
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return {"documents": [], "metadatas": [], "ids": []}
        
        # Build query
        query_parts = []
        if project:
            query_parts.append(f"project {project}")
        if mode:
            query_parts.append(f"mode {mode}")
        
        query_text = " ".join(query_parts) if query_parts else "context"
        
        # Calculate timestamp for filtering
        now_unix = int(datetime.now(timezone.utc).timestamp())
        since_unix = now_unix - (hours * 3600)
        
        # Build where clause
        where = {"timestamp_unix": {"$gte": since_unix}}
        
        # Query with semantic search and timestamp filter
        results = collection.query(
            query_texts=[query_text],
            where=where,
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        # Flatten results (query returns nested arrays)
        return {
            "documents": results.get("documents", [[]])[0],
            "metadatas": results.get("metadatas", [[]])[0],
            "ids": results.get("ids", [[]])[0],
            "distances": results.get("distances", [[]])[0]
        }
    
    def get_morning_context(
        self,
        collection_name: str,
        lookback_hours: int = 36
    ) -> List[Dict[str, Any]]:
        """Get context for morning brain boot.
        
        Retrieves recent context entries, prioritizing:
        - Recent project activity
        - Open tasks
        - Mode transitions
        
        Args:
            collection_name: Name of the collection
            lookback_hours: Hours to look back
            
        Returns:
            List of context summaries
        """
        # Get recent context
        results = self.query_recent_context(
            collection_name=collection_name,
            hours=lookback_hours,
            limit=20
        )
        
        # Analyze results
        projects = set()
        modes = []
        tasks = []
        
        for metadata in results.get("metadatas", []):
            if "project" in metadata:
                projects.add(metadata["project"])
            if "mode" in metadata:
                modes.append({
                    "mode": metadata["mode"],
                    "timestamp": metadata.get("timestamp", "")
                })
            if "task" in metadata:
                tasks.append(metadata["task"])
        
        # Get last mode if any
        last_mode = None
        if modes:
            # Sort by timestamp and get the most recent
            modes.sort(key=lambda x: x["timestamp"], reverse=True)
            last_mode = modes[0]["mode"]
        
        return [{
            "summary": "Morning context loaded",
            "recent_projects": list(projects),
            "open_tasks": tasks,
            "last_mode": last_mode,
            "context_count": len(results.get("documents", []))
        }]
    
    def search_context(
        self,
        collection_name: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Semantic search in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Search query
            limit: Maximum results
            
        Returns:
            List of search results with content and metadata
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return []
        
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        for doc, meta, doc_id, distance in zip(docs, metas, ids, distances):
            output.append({
                "id": doc_id,
                "content": doc,
                "metadata": meta,
                "distance": distance
            })
        
        return output
    
    # Additional ChromaDB operations for MCP server compatibility
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs
        """
        collection = self.get_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")
        
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(
            "documents_added",
            collection=collection_name,
            count=len(documents)
        )
    
    def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Update documents in a collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to update
            documents: Optional new document texts
            metadatas: Optional new metadata dicts
        """
        collection = self.get_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")
        
        collection.update(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(
            "documents_updated",
            collection=collection_name,
            count=len(ids)
        )
    
    def delete_documents(
        self,
        collection_name: str,
        ids: List[str]
    ) -> None:
        """Delete documents from a collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
        """
        collection = self.get_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")
        
        collection.delete(ids=ids)
        
        logger.info(
            "documents_deleted",
            collection=collection_name,
            count=len(ids)
        )
    
    def get_documents(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get documents from a collection.
        
        Args:
            collection_name: Name of the collection
            ids: Optional list of specific document IDs
            where: Optional where clause for filtering
            limit: Optional limit on results
            offset: Optional offset for pagination
            include: Optional list of fields to include
            
        Returns:
            Dictionary with documents, metadatas, ids, etc.
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return {"documents": [], "metadatas": [], "ids": []}
        
        # Set default include if not provided
        if include is None:
            include = ["documents", "metadatas"]
        
        results = collection.get(
            ids=ids,
            where=where,
            limit=limit,
            offset=offset,
            include=include
        )
        
        return results
    
    def query_documents(
        self,
        collection_name: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Query documents in a collection.
        
        Args:
            collection_name: Name of the collection
            query_texts: Optional list of query texts
            query_embeddings: Optional list of query embeddings
            n_results: Number of results to return
            where: Optional where clause for metadata filtering
            where_document: Optional where clause for document filtering
            include: Optional list of fields to include
            
        Returns:
            Dictionary with query results
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
        
        # Set default include if not provided
        if include is None:
            include = ["documents", "metadatas", "distances"]
        
        results = collection.query(
            query_texts=query_texts,
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include
        )
        
        return results
    
    def count_documents(self, collection_name: str) -> int:
        """Count documents in a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of documents in the collection
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return 0
        
        return collection.count()
    
    def get_collection_metadata(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection metadata or None if not found
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return None
        
        return collection.metadata
    
    def modify_collection(
        self,
        collection_name: str,
        new_name: Optional[str] = None,
        new_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Modify a collection's name or metadata.
        
        Args:
            collection_name: Current name of the collection
            new_name: Optional new name for the collection
            new_metadata: Optional new metadata for the collection
        """
        collection = self.get_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")
        
        collection.modify(name=new_name, metadata=new_metadata)
        
        logger.info(
            "collection_modified",
            old_name=collection_name,
            new_name=new_name,
            metadata_updated=new_metadata is not None
        )
    
    def upsert_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """Upsert documents to a collection (add or update).
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs
        """
        collection = self.get_collection(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")
        
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(
            "documents_upserted",
            collection=collection_name,
            count=len(documents)
        )
    
    def peek_collection(self, collection_name: str, limit: int = 10) -> Dict[str, Any]:
        """Peek at documents in a collection.
        
        Args:
            collection_name: Name of the collection
            limit: Number of documents to peek at
            
        Returns:
            Dictionary with sample documents and metadata
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return {"documents": [], "metadatas": [], "ids": []}
        
        results = collection.peek(limit=limit)
        return results