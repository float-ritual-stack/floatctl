"""
Evna MCP Consciousness Integration

Adds FloatCtl consciousness database querying capabilities to Evna MCP server.
This allows Evna to query structured consciousness analysis data directly
instead of fumbling with Chroma metadata.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import os

class EvnaConsciousnessQuery:
    """Enhanced Evna with FloatCtl consciousness database access."""
    
    def __init__(self, floatctl_db_path: Optional[Path] = None):
        """Initialize with FloatCtl database path."""
        
        if floatctl_db_path is None:
            # Try common FloatCtl database locations
            possible_paths = [
                Path.home() / ".floatctl" / "floatctl.db",
                Path.home() / ".config" / "floatctl" / "floatctl.db",
                Path("/Users/evan/projects/float-workspace/tools/floatctl-py") / "floatctl.db"
            ]
            
            for path in possible_paths:
                if path.exists():
                    floatctl_db_path = path
                    break
        
        self.db_path = floatctl_db_path
        self.connection = None
        
        if self.db_path and self.db_path.exists():
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            print(f"✅ Connected to FloatCtl consciousness database: {self.db_path}")
        else:
            print(f"⚠️  FloatCtl consciousness database not found at: {floatctl_db_path}")
    
    def query_consciousness_contamination(self, 
                                        level: Optional[str] = None,
                                        min_score: Optional[int] = None,
                                        project: Optional[str] = None,
                                        limit: int = 20) -> Dict[str, Any]:
        """Query consciousness contamination with precise filters."""
        
        if not self.connection:
            return {"error": "No database connection"}
        
        # Build dynamic query
        where_conditions = []
        params = []
        
        if level:
            where_conditions.append("contamination_level = ?")
            params.append(level)
        
        if min_score:
            where_conditions.append("contamination_score >= ?")
            params.append(min_score)
        
        if project:
            where_conditions.append("primary_project = ?")
            params.append(project)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                file_path, conversation_title, contamination_level,
                contamination_score, consciousness_urls, work_urls,
                primary_project, dispatch_score, processed_at
            FROM consciousness_analysis 
            {where_clause}
            ORDER BY contamination_score DESC, dispatch_score DESC
            LIMIT ?
        """
        
        cursor = self.connection.execute(query, params + [limit])
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "query_type": "consciousness_contamination",
            "filters": {
                "level": level,
                "min_score": min_score, 
                "project": project,
                "limit": limit
            },
            "results": results,
            "count": len(results)
        }
    
    def query_work_projects(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Query work project classifications."""
        
        if not self.connection:
            return {"error": "No database connection"}
        
        if project_name:
            # Get specific project details
            query = """
                SELECT 
                    ca.file_path, ca.conversation_title, ca.contamination_level,
                    wpm.project_name, wpm.project_category, wpm.match_count,
                    wpm.matched_patterns, ca.processed_at
                FROM consciousness_analysis ca
                JOIN work_project_matches wpm ON ca.id = wpm.analysis_id
                WHERE wpm.project_name = ?
                ORDER BY wpm.match_count DESC
            """
            cursor = self.connection.execute(query, (project_name,))
            results = [dict(row) for row in cursor.fetchall()]
            
            return {
                "query_type": "work_project_details",
                "project": project_name,
                "results": results,
                "count": len(results)
            }
        else:
            # Get project summary
            query = """
                SELECT 
                    wpm.project_name, wpm.project_category,
                    COUNT(*) as conversation_count,
                    AVG(wpm.match_count) as avg_matches,
                    MAX(wpm.match_count) as max_matches,
                    AVG(ca.contamination_score) as avg_contamination
                FROM work_project_matches wpm
                JOIN consciousness_analysis ca ON wpm.analysis_id = ca.id
                GROUP BY wpm.project_name, wpm.project_category
                ORDER BY conversation_count DESC
            """
            cursor = self.connection.execute(query)
            results = [dict(row) for row in cursor.fetchall()]
            
            return {
                "query_type": "work_project_summary",
                "results": results,
                "count": len(results)
            }
    
    def query_url_contexts(self, 
                          domain: Optional[str] = None,
                          has_consciousness_markers: Optional[bool] = None,
                          work_project: Optional[str] = None,
                          limit: int = 20) -> Dict[str, Any]:
        """Query URL contexts with consciousness mapping."""
        
        if not self.connection:
            return {"error": "No database connection"}
        
        where_conditions = []
        params = []
        
        if domain:
            where_conditions.append("uc.domain LIKE ?")
            params.append(f"%{domain}%")
        
        if has_consciousness_markers is not None:
            if has_consciousness_markers:
                where_conditions.append("uc.consciousness_markers != '[]' AND uc.consciousness_markers IS NOT NULL")
            else:
                where_conditions.append("(uc.consciousness_markers = '[]' OR uc.consciousness_markers IS NULL)")
        
        if work_project:
            where_conditions.append("uc.work_project = ?")
            params.append(work_project)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                uc.url, uc.domain, uc.context_snippet, uc.work_project,
                uc.consciousness_markers, ca.conversation_title,
                ca.file_path, ca.contamination_level, ca.processed_at
            FROM url_contexts uc
            JOIN consciousness_analysis ca ON uc.analysis_id = ca.id
            {where_clause}
            ORDER BY ca.processed_at DESC
            LIMIT ?
        """
        
        cursor = self.connection.execute(query, params + [limit])
        results = []
        
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Parse consciousness markers JSON
            if row_dict['consciousness_markers']:
                try:
                    row_dict['consciousness_markers'] = json.loads(row_dict['consciousness_markers'])
                except:
                    row_dict['consciousness_markers'] = []
            else:
                row_dict['consciousness_markers'] = []
            
            results.append(row_dict)
        
        return {
            "query_type": "url_contexts",
            "filters": {
                "domain": domain,
                "has_consciousness_markers": has_consciousness_markers,
                "work_project": work_project,
                "limit": limit
            },
            "results": results,
            "count": len(results)
        }
    
    def query_dispatch_opportunities(self, 
                                   imprint: Optional[str] = None,
                                   min_matches: Optional[int] = None,
                                   limit: int = 20) -> Dict[str, Any]:
        """Query float.dispatch publishing opportunities."""
        
        if not self.connection:
            return {"error": "No database connection"}
        
        where_conditions = []
        params = []
        
        if imprint:
            where_conditions.append("do.imprint_name = ?")
            params.append(imprint)
        
        if min_matches:
            where_conditions.append("do.match_count >= ?")
            params.append(min_matches)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                do.imprint_name, do.match_count, do.matched_patterns,
                do.description, ca.conversation_title, ca.file_path,
                ca.contamination_level, ca.contamination_score, ca.processed_at
            FROM dispatch_opportunities do
            JOIN consciousness_analysis ca ON do.analysis_id = ca.id
            {where_clause}
            ORDER BY do.match_count DESC, ca.contamination_score DESC
            LIMIT ?
        """
        
        cursor = self.connection.execute(query, params + [limit])
        results = []
        
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Parse matched patterns JSON
            if row_dict['matched_patterns']:
                try:
                    row_dict['matched_patterns'] = json.loads(row_dict['matched_patterns'])
                except:
                    row_dict['matched_patterns'] = []
            else:
                row_dict['matched_patterns'] = []
            
            results.append(row_dict)
        
        return {
            "query_type": "dispatch_opportunities",
            "filters": {
                "imprint": imprint,
                "min_matches": min_matches,
                "limit": limit
            },
            "results": results,
            "count": len(results)
        }
    
    def query_consciousness_timeline(self, 
                                   days_back: int = 30,
                                   contamination_threshold: int = 5) -> Dict[str, Any]:
        """Query consciousness contamination timeline."""
        
        if not self.connection:
            return {"error": "No database connection"}
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        query = """
            SELECT 
                DATE(processed_at) as date,
                COUNT(*) as total_conversations,
                COUNT(CASE WHEN contamination_level = 'high' THEN 1 END) as high_contamination,
                COUNT(CASE WHEN contamination_level = 'moderate' THEN 1 END) as moderate_contamination,
                AVG(contamination_score) as avg_contamination_score,
                COUNT(CASE WHEN consciousness_urls > 0 THEN 1 END) as conversations_with_consciousness_urls,
                COUNT(CASE WHEN dispatch_score > 3 THEN 1 END) as strong_dispatch_opportunities
            FROM consciousness_analysis
            WHERE processed_at >= ?
            GROUP BY DATE(processed_at)
            ORDER BY date DESC
        """
        
        cursor = self.connection.execute(query, (cutoff_date.isoformat(),))
        results = [dict(row) for row in cursor.fetchall()]
        
        # Calculate trends
        if len(results) >= 2:
            recent_avg = sum(r['avg_contamination_score'] or 0 for r in results[:7]) / min(7, len(results))
            older_avg = sum(r['avg_contamination_score'] or 0 for r in results[7:14]) / max(1, min(7, len(results) - 7))
            contamination_trend = "increasing" if recent_avg > older_avg else "decreasing"
        else:
            contamination_trend = "insufficient_data"
        
        return {
            "query_type": "consciousness_timeline",
            "days_back": days_back,
            "contamination_threshold": contamination_threshold,
            "contamination_trend": contamination_trend,
            "results": results,
            "count": len(results)
        }
    
    def get_consciousness_summary(self) -> Dict[str, Any]:
        """Get overall consciousness analysis summary."""
        
        if not self.connection:
            return {"error": "No database connection"}
        
        # Main summary stats
        cursor = self.connection.execute("""
            SELECT 
                COUNT(*) as total_analyses,
                COUNT(CASE WHEN contamination_level = 'high' THEN 1 END) as high_contamination,
                COUNT(CASE WHEN contamination_level = 'moderate' THEN 1 END) as moderate_contamination,
                COUNT(CASE WHEN consciousness_urls > 0 THEN 1 END) as conversations_with_consciousness_urls,
                COUNT(CASE WHEN dispatch_score > 3 THEN 1 END) as strong_dispatch_opportunities,
                AVG(contamination_score) as avg_contamination_score,
                AVG(dispatch_score) as avg_dispatch_score,
                MAX(processed_at) as last_processed
            FROM consciousness_analysis
        """)
        
        summary = dict(cursor.fetchone())
        
        # Top work projects
        cursor = self.connection.execute("""
            SELECT project_name, COUNT(*) as count
            FROM work_project_matches
            GROUP BY project_name
            ORDER BY count DESC
            LIMIT 5
        """)
        
        summary['top_work_projects'] = [dict(row) for row in cursor.fetchall()]
        
        # Top dispatch imprints
        cursor = self.connection.execute("""
            SELECT imprint_name, COUNT(*) as count, AVG(match_count) as avg_matches
            FROM dispatch_opportunities
            GROUP BY imprint_name
            ORDER BY count DESC
            LIMIT 5
        """)
        
        summary['top_dispatch_imprints'] = [dict(row) for row in cursor.fetchall()]
        
        # Top consciousness domains
        cursor = self.connection.execute("""
            SELECT domain, COUNT(*) as count
            FROM url_contexts
            WHERE consciousness_markers != '[]' AND consciousness_markers IS NOT NULL
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 5
        """)
        
        summary['top_consciousness_domains'] = [dict(row) for row in cursor.fetchall()]
        
        return {
            "query_type": "consciousness_summary",
            "summary": summary
        }

# MCP Server Integration Functions
def evna_query_consciousness_contamination(level: str = None, min_score: int = None, 
                                         project: str = None, limit: int = 20) -> str:
    """
    Query consciousness contamination analysis results.
    
    Args:
        level: Filter by contamination level (high, moderate, standard)
        min_score: Minimum contamination score
        project: Filter by work project name
        limit: Maximum number of results
    
    Returns:
        JSON string with consciousness contamination results
    """
    evna = EvnaConsciousnessQuery()
    results = evna.query_consciousness_contamination(level, min_score, project, limit)
    return json.dumps(results, indent=2, default=str)

def evna_query_work_projects(project_name: str = None) -> str:
    """
    Query work project classifications from consciousness analysis.
    
    Args:
        project_name: Specific project to query (optional)
    
    Returns:
        JSON string with work project results
    """
    evna = EvnaConsciousnessQuery()
    results = evna.query_work_projects(project_name)
    return json.dumps(results, indent=2, default=str)

def evna_query_url_contexts(domain: str = None, has_consciousness_markers: bool = None,
                           work_project: str = None, limit: int = 20) -> str:
    """
    Query URL contexts with consciousness mapping.
    
    Args:
        domain: Filter by domain (partial match)
        has_consciousness_markers: Filter by presence of consciousness markers
        work_project: Filter by work project
        limit: Maximum number of results
    
    Returns:
        JSON string with URL context results
    """
    evna = EvnaConsciousnessQuery()
    results = evna.query_url_contexts(domain, has_consciousness_markers, work_project, limit)
    return json.dumps(results, indent=2, default=str)

def evna_query_dispatch_opportunities(imprint: str = None, min_matches: int = None, 
                                    limit: int = 20) -> str:
    """
    Query float.dispatch publishing opportunities.
    
    Args:
        imprint: Filter by imprint name
        min_matches: Minimum number of pattern matches
        limit: Maximum number of results
    
    Returns:
        JSON string with dispatch opportunity results
    """
    evna = EvnaConsciousnessQuery()
    results = evna.query_dispatch_opportunities(imprint, min_matches, limit)
    return json.dumps(results, indent=2, default=str)

def evna_get_consciousness_summary() -> str:
    """
    Get overall consciousness analysis summary.
    
    Returns:
        JSON string with consciousness analysis summary
    """
    evna = EvnaConsciousnessQuery()
    results = evna.get_consciousness_summary()
    return json.dumps(results, indent=2, default=str)

def evna_query_consciousness_timeline(days_back: int = 30) -> str:
    """
    Query consciousness contamination timeline.
    
    Args:
        days_back: Number of days to look back
    
    Returns:
        JSON string with consciousness timeline data
    """
    evna = EvnaConsciousnessQuery()
    results = evna.query_consciousness_timeline(days_back)
    return json.dumps(results, indent=2, default=str)

# Example usage and testing
if __name__ == "__main__":
    # Test the consciousness query system
    evna = EvnaConsciousnessQuery()
    
    print("🧬 Testing Evna Consciousness Integration")
    print("=" * 50)
    
    # Test summary
    summary = evna.get_consciousness_summary()
    print(f"📊 Summary: {summary.get('summary', {}).get('total_analyses', 0)} total analyses")
    
    # Test contamination query
    contamination = evna.query_consciousness_contamination(level="high", limit=5)
    print(f"🔥 High contamination: {contamination['count']} results")
    
    # Test work projects
    projects = evna.query_work_projects()
    print(f"📋 Work projects: {projects['count']} project types")
    
    # Test URL contexts
    urls = evna.query_url_contexts(has_consciousness_markers=True, limit=5)
    print(f"🔗 Consciousness URLs: {urls['count']} results")
    
    print("\n✅ Evna consciousness integration ready!")

# Workflow Intelligence MCP Functions
def evna_what_did_i_do_last_week(days_back: int = 7) -> str:
    """
    Answer: What did I do last week?
    
    Args:
        days_back: Number of days to look back
    
    Returns:
        JSON string with completed activities
    """
    evna = EvnaConsciousnessQuery()
    if not evna.connection:
        return json.dumps({"error": "No database connection"})
    
    workflow = WorkflowIntelligence(evna.db_manager)
    results = workflow.what_did_i_do_last_week(days_back)
    return json.dumps(results, indent=2, default=str)

def evna_action_items_from_nick(days_back: int = 30) -> str:
    """
    Answer: What action items do I have from Nick?
    
    Args:
        days_back: Number of days to look back
    
    Returns:
        JSON string with Nick's action items
    """
    evna = EvnaConsciousnessQuery()
    if not evna.connection:
        return json.dumps({"error": "No database connection"})
    
    workflow = WorkflowIntelligence(evna.db_manager)
    results = workflow.action_items_from_nick(days_back)
    return json.dumps(results, indent=2, default=str)

def evna_current_priorities(days_back: int = 14) -> str:
    """
    Answer: What are my current priorities?
    
    Args:
        days_back: Number of days to look back
    
    Returns:
        JSON string with current priorities and open action items
    """
    evna = EvnaConsciousnessQuery()
    if not evna.connection:
        return json.dumps({"error": "No database connection"})
    
    workflow = WorkflowIntelligence(evna.db_manager)
    results = workflow.current_priorities(days_back)
    return json.dumps(results, indent=2, default=str)

def evna_forgotten_tasks(days_back: int = 30) -> str:
    """
    Answer: What tasks might I have forgotten?
    
    Args:
        days_back: How far back to look for old tasks
    
    Returns:
        JSON string with potentially forgotten tasks
    """
    evna = EvnaConsciousnessQuery()
    if not evna.connection:
        return json.dumps({"error": "No database connection"})
    
    workflow = WorkflowIntelligence(evna.db_manager)
    results = workflow.forgotten_tasks(days_back)
    return json.dumps(results, indent=2, default=str)

def evna_meeting_follow_ups(days_back: int = 14) -> str:
    """
    Answer: What meeting follow-ups do I have?
    
    Args:
        days_back: Number of days to look back
    
    Returns:
        JSON string with meeting action items
    """
    evna = EvnaConsciousnessQuery()
    if not evna.connection:
        return json.dumps({"error": "No database connection"})
    
    workflow = WorkflowIntelligence(evna.db_manager)
    results = workflow.meeting_follow_ups(days_back)
    return json.dumps(results, indent=2, default=str)

def evna_workflow_summary() -> str:
    """
    Get a comprehensive workflow summary combining all intelligence.
    
    Returns:
        JSON string with workflow intelligence summary
    """
    evna = EvnaConsciousnessQuery()
    if not evna.connection:
        return json.dumps({"error": "No database connection"})
    
    workflow = WorkflowIntelligence(evna.db_manager)
    
    # Gather all workflow intelligence
    summary = {
        "last_week_activities": workflow.what_did_i_do_last_week(7),
        "nick_action_items": workflow.action_items_from_nick(30),
        "current_priorities": workflow.current_priorities(14),
        "forgotten_tasks": workflow.forgotten_tasks(30),
        "meeting_follow_ups": workflow.meeting_follow_ups(14),
        "generated_at": datetime.now().isoformat()
    }
    
    return json.dumps(summary, indent=2, default=str)