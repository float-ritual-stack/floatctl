"""
Consciousness-Chroma Bridge

Pushes consciousness analysis results to Chroma for semantic search
while maintaining structured SQLite queries for precise filtering.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings

from floatctl.core.consciousness_middleware import ConsciousnessMiddleware, ConsciousnessAnalysis
from floatctl.core.database import DatabaseManager
from floatctl.core.logging import get_logger

logger = get_logger(__name__)

class ConsciousnessChromaBridge:
    """Bridge between consciousness analysis SQLite data and Chroma semantic search."""
    
    def __init__(self, db_manager: DatabaseManager, chroma_path: Optional[Path] = None):
        self.db_manager = db_manager
        self.consciousness_middleware = ConsciousnessMiddleware(db_manager)
        
        # Initialize Chroma client
        if chroma_path is None:
            chroma_path = Path.home() / ".floatctl" / "chroma"
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create consciousness collections
        self.consciousness_collection = self.chroma_client.get_or_create_collection(
            name="consciousness_analysis",
            metadata={"description": "Consciousness contamination analysis results"}
        )
        
        self.url_contexts_collection = self.chroma_client.get_or_create_collection(
            name="consciousness_url_contexts", 
            metadata={"description": "URLs with consciousness context mapping"}
        )
        
        self.dispatch_opportunities_collection = self.chroma_client.get_or_create_collection(
            name="consciousness_dispatch_opportunities",
            metadata={"description": "Float.dispatch publishing opportunities"}
        )
    
    def sync_analysis_to_chroma(self, analysis: ConsciousnessAnalysis) -> None:
        """Sync a consciousness analysis to Chroma collections."""
        
        # 1. Main consciousness analysis document
        self._add_consciousness_analysis(analysis)
        
        # 2. URL contexts as separate documents
        self._add_url_contexts(analysis)
        
        # 3. Dispatch opportunities as separate documents  
        self._add_dispatch_opportunities(analysis)
    
    def _add_consciousness_analysis(self, analysis: ConsciousnessAnalysis) -> None:
        """Add main consciousness analysis to Chroma."""
        
        # Create searchable document text
        doc_text = f"""
        Consciousness Analysis: {analysis.conversation_title}
        
        File: {analysis.file_path}
        Contamination Level: {analysis.contamination_level}
        Contamination Score: {analysis.contamination_score}
        Primary Project: {analysis.primary_project or 'None'}
        
        Consciousness Metrics:
        {json.dumps(analysis.consciousness_metrics, indent=2)}
        
        Work Projects Detected:
        {', '.join(analysis.work_projects.keys()) if analysis.work_projects else 'None'}
        
        Dispatch Opportunities:
        {', '.join(analysis.dispatch_opportunities.keys()) if analysis.dispatch_opportunities else 'None'}
        
        Alerts:
        {chr(10).join(analysis.alerts)}
        
        Insights:
        {chr(10).join(analysis.insights)}
        """
        
        # Create metadata for filtering
        metadata = {
            "file_path": analysis.file_path,
            "conversation_id": analysis.conversation_id,
            "conversation_title": analysis.conversation_title,
            "contamination_level": analysis.contamination_level,
            "contamination_score": analysis.contamination_score,
            "consciousness_urls": analysis.consciousness_urls,
            "work_urls": analysis.work_urls,
            "primary_project": analysis.primary_project or "",
            "dispatch_score": analysis.dispatch_score,
            "processed_at": analysis.processed_at.isoformat(),
            "timestamp_unix": int(analysis.processed_at.timestamp()),
            "has_lf1m": analysis.consciousness_metrics.get('lf1m', 0) > 0,
            "has_float_dispatch": analysis.consciousness_metrics.get('float_dispatch', 0) > 0,
            "has_neuroqueer": analysis.consciousness_metrics.get('neuroqueer', 0) > 0,
            "work_project_count": len(analysis.work_projects),
            "dispatch_opportunity_count": len(analysis.dispatch_opportunities)
        }
        
        # Add to Chroma
        doc_id = f"consciousness_{analysis.conversation_id}_{int(analysis.processed_at.timestamp())}"
        
        self.consciousness_collection.upsert(
            ids=[doc_id],
            documents=[doc_text.strip()],
            metadatas=[metadata]
        )
        
        logger.info(f"Added consciousness analysis to Chroma: {doc_id}")
    
    def _add_url_contexts(self, analysis: ConsciousnessAnalysis) -> None:
        """Add URL contexts to Chroma for semantic search."""
        
        if not analysis.urls:
            return
        
        ids = []
        documents = []
        metadatas = []
        
        for i, url_data in enumerate(analysis.urls):
            # Create searchable document
            doc_text = f"""
            URL Context Analysis
            
            URL: {url_data['url']}
            Domain: {url_data['domain']}
            Work Project: {url_data.get('work_project', 'None')}
            
            Context:
            {url_data['context_snippet']}
            
            Consciousness Markers:
            {', '.join(url_data['consciousness_markers']) if url_data['consciousness_markers'] else 'None'}
            
            From Conversation: {analysis.conversation_title}
            """
            
            metadata = {
                "url": url_data['url'],
                "domain": url_data['domain'],
                "work_project": url_data.get('work_project', ''),
                "consciousness_marker_count": len(url_data['consciousness_markers']),
                "has_consciousness_markers": len(url_data['consciousness_markers']) > 0,
                "conversation_id": analysis.conversation_id,
                "conversation_title": analysis.conversation_title,
                "file_path": analysis.file_path,
                "processed_at": analysis.processed_at.isoformat(),
                "timestamp_unix": int(analysis.processed_at.timestamp())
            }
            
            doc_id = f"url_context_{analysis.conversation_id}_{i}_{int(analysis.processed_at.timestamp())}"
            
            ids.append(doc_id)
            documents.append(doc_text.strip())
            metadatas.append(metadata)
        
        self.url_contexts_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(ids)} URL contexts to Chroma")
    
    def _add_dispatch_opportunities(self, analysis: ConsciousnessAnalysis) -> None:
        """Add dispatch opportunities to Chroma."""
        
        if not analysis.dispatch_opportunities:
            return
        
        ids = []
        documents = []
        metadatas = []
        
        for imprint_name, imprint_data in analysis.dispatch_opportunities.items():
            # Create searchable document
            doc_text = f"""
            Float.Dispatch Opportunity: {imprint_name}
            
            Description: {imprint_data['description']}
            Match Count: {imprint_data['matches']}
            Matched Patterns: {', '.join(imprint_data['patterns'])}
            
            From Conversation: {analysis.conversation_title}
            File: {analysis.file_path}
            
            This conversation shows strong potential for the {imprint_name} imprint.
            """
            
            metadata = {
                "imprint_name": imprint_name,
                "imprint_description": imprint_data['description'],
                "match_count": imprint_data['matches'],
                "conversation_id": analysis.conversation_id,
                "conversation_title": analysis.conversation_title,
                "file_path": analysis.file_path,
                "contamination_level": analysis.contamination_level,
                "contamination_score": analysis.contamination_score,
                "processed_at": analysis.processed_at.isoformat(),
                "timestamp_unix": int(analysis.processed_at.timestamp())
            }
            
            doc_id = f"dispatch_{imprint_name}_{analysis.conversation_id}_{int(analysis.processed_at.timestamp())}"
            
            ids.append(doc_id)
            documents.append(doc_text.strip())
            metadatas.append(metadata)
        
        self.dispatch_opportunities_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(ids)} dispatch opportunities to Chroma")
    
    def sync_all_analyses_to_chroma(self) -> Dict[str, int]:
        """Sync all consciousness analyses from SQLite to Chroma."""
        
        # Get all analyses from SQLite
        cursor = self.db_manager.execute_sql("""
            SELECT 
                ca.file_path, ca.conversation_id, ca.conversation_title,
                ca.contamination_level, ca.contamination_score,
                ca.consciousness_urls, ca.work_urls, ca.primary_project,
                ca.dispatch_score, ca.processed_at
            FROM consciousness_analysis ca
            ORDER BY ca.processed_at DESC
        """)
        
        analyses = cursor.fetchall()
        synced_count = 0
        
        for row in analyses:
            try:
                # Reconstruct analysis object (simplified)
                analysis = ConsciousnessAnalysis(
                    file_path=row[0],
                    conversation_id=row[1],
                    conversation_title=row[2],
                    contamination_level=row[3],
                    contamination_score=row[4],
                    consciousness_urls=row[5],
                    work_urls=row[6],
                    primary_project=row[7],
                    dispatch_score=row[8],
                    processed_at=datetime.fromisoformat(row[9])
                )
                
                # Get detailed data for this analysis
                self._populate_analysis_details(analysis)
                
                # Sync to Chroma
                self.sync_analysis_to_chroma(analysis)
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Failed to sync analysis {row[1]}: {e}")
        
        return {
            "total_analyses": len(analyses),
            "synced_successfully": synced_count,
            "consciousness_docs": self.consciousness_collection.count(),
            "url_context_docs": self.url_contexts_collection.count(),
            "dispatch_opportunity_docs": self.dispatch_opportunities_collection.count()
        }
    
    def _populate_analysis_details(self, analysis: ConsciousnessAnalysis) -> None:
        """Populate detailed data for an analysis from SQLite."""
        
        # Get consciousness metrics
        cursor = self.db_manager.execute_sql("""
            SELECT metric_type, metric_value 
            FROM consciousness_metrics 
            WHERE analysis_id = (
                SELECT id FROM consciousness_analysis 
                WHERE conversation_id = ? AND file_path = ?
            )
        """, (analysis.conversation_id, analysis.file_path))
        
        analysis.consciousness_metrics = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get URL contexts
        cursor = self.db_manager.execute_sql("""
            SELECT url, domain, context_snippet, work_project, consciousness_markers
            FROM url_contexts 
            WHERE analysis_id = (
                SELECT id FROM consciousness_analysis 
                WHERE conversation_id = ? AND file_path = ?
            )
        """, (analysis.conversation_id, analysis.file_path))
        
        analysis.urls = []
        for row in cursor.fetchall():
            analysis.urls.append({
                'url': row[0],
                'domain': row[1],
                'context_snippet': row[2],
                'work_project': row[3],
                'consciousness_markers': json.loads(row[4]) if row[4] else []
            })
        
        # Get work projects
        cursor = self.db_manager.execute_sql("""
            SELECT project_name, project_category, match_count, matched_patterns
            FROM work_project_matches 
            WHERE analysis_id = (
                SELECT id FROM consciousness_analysis 
                WHERE conversation_id = ? AND file_path = ?
            )
        """, (analysis.conversation_id, analysis.file_path))
        
        analysis.work_projects = {}
        for row in cursor.fetchall():
            analysis.work_projects[row[0]] = {
                'category': row[1],
                'matches': row[2],
                'patterns': json.loads(row[3]) if row[3] else []
            }
        
        # Get dispatch opportunities
        cursor = self.db_manager.execute_sql("""
            SELECT imprint_name, match_count, matched_patterns, description
            FROM dispatch_opportunities 
            WHERE analysis_id = (
                SELECT id FROM consciousness_analysis 
                WHERE conversation_id = ? AND file_path = ?
            )
        """, (analysis.conversation_id, analysis.file_path))
        
        analysis.dispatch_opportunities = {}
        for row in cursor.fetchall():
            analysis.dispatch_opportunities[row[0]] = {
                'matches': row[1],
                'patterns': json.loads(row[2]) if row[2] else [],
                'description': row[3]
            }
        
        # Get alerts
        cursor = self.db_manager.execute_sql("""
            SELECT alert_message
            FROM consciousness_alerts 
            WHERE analysis_id = (
                SELECT id FROM consciousness_analysis 
                WHERE conversation_id = ? AND file_path = ?
            )
        """, (analysis.conversation_id, analysis.file_path))
        
        analysis.alerts = [row[0] for row in cursor.fetchall()]
    
    def query_consciousness_semantic(self, query: str, n_results: int = 5, 
                                   contamination_level: Optional[str] = None,
                                   project: Optional[str] = None) -> Dict[str, Any]:
        """Semantic search across consciousness analyses."""
        
        where_filter = {}
        if contamination_level:
            where_filter["contamination_level"] = contamination_level
        if project:
            where_filter["primary_project"] = project
        
        results = self.consciousness_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )
        
        return {
            "query": query,
            "results": results,
            "collection": "consciousness_analysis"
        }
    
    def query_url_contexts_semantic(self, query: str, n_results: int = 5,
                                   domain: Optional[str] = None) -> Dict[str, Any]:
        """Semantic search across URL contexts."""
        
        where_filter = {}
        if domain:
            where_filter["domain"] = domain
        
        results = self.url_contexts_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )
        
        return {
            "query": query,
            "results": results,
            "collection": "consciousness_url_contexts"
        }
    
    def query_dispatch_opportunities_semantic(self, query: str, n_results: int = 5,
                                            imprint: Optional[str] = None) -> Dict[str, Any]:
        """Semantic search across dispatch opportunities."""
        
        where_filter = {}
        if imprint:
            where_filter["imprint_name"] = imprint
        
        results = self.dispatch_opportunities_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )
        
        return {
            "query": query,
            "results": results,
            "collection": "consciousness_dispatch_opportunities"
        }