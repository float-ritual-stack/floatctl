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