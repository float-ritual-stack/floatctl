"""FloatQL Translator - Converts parsed FloatQL to destination query formats."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class FloatQLTranslator:
    """Translator for FloatQL parsed queries to various backends.
    
    Currently supports:
    - Chroma vector database queries
    - Future: Obsidian search, Roam queries, etc.
    """
    
    def __init__(self):
        pass
    
    def translate_to_chroma_query(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Translate parsed FloatQL to Chroma query parameters.
        
        Returns:
            Dictionary with:
            - query_texts: List of text queries for semantic search
            - where: Metadata filter conditions
            - where_document: Document content filters
        """
        # Build query text from terms and patterns
        query_parts = []
        
        # Add text terms
        if parsed['text_terms']:
            query_parts.extend(parsed['text_terms'])
        
        # Add pattern-based terms for semantic search
        for pattern in parsed['float_patterns']:
            query_parts.append(f"{pattern}::")
        
        for persona in parsed['persona_patterns']:
            query_parts.append(f"[{persona}::]")
        
        # Add bridge IDs
        query_parts.extend(parsed['bridge_ids'])
        
        # Build metadata filters
        where_conditions = self._build_where_clause(parsed)
        
        # Build document content filters if needed
        where_document = self._build_document_filters(parsed)
        
        return {
            'query_texts': [' '.join(query_parts)] if query_parts else [''],
            'where': where_conditions,
            'where_document': where_document
        }
    
    def _build_where_clause(self, parsed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build Chroma where clause from parsed components."""
        conditions = []
        
        # Type filters - simplified to avoid unsupported operators
        if parsed['type_filters']:
            for type_filter in parsed['type_filters']:
                # Use simple equality checks that Chroma supports
                if type_filter == 'conversation':
                    conditions.append({'type': {'$eq': 'conversation'}})
                elif type_filter == 'log':
                    conditions.append({'type': {'$eq': 'log'}})
                elif type_filter == 'bridge':
                    conditions.append({'type': {'$eq': 'bridge'}})
        
        # Temporal filters
        if parsed['temporal_filters']:
            if 'since' in parsed['temporal_filters']:
                since_dt = parsed['temporal_filters']['since']
                if not isinstance(since_dt, str):
                    # Ensure timezone aware
                    if hasattr(since_dt, 'tzinfo') and since_dt.tzinfo is None:
                        since_dt = since_dt.replace(tzinfo=timezone.utc)
                    since_str = since_dt.isoformat()
                else:
                    since_str = since_dt
                
                # Check multiple possible timestamp fields
                temporal_condition = {
                    '$or': [
                        {'timestamp': {'$gte': since_str}},
                        {'created_at': {'$gte': since_str}},
                        {'updated_at': {'$gte': since_str}}
                    ]
                }
                conditions.append(temporal_condition)
            
            elif 'date' in parsed['temporal_filters']:
                date_val = parsed['temporal_filters']['date']
                if not isinstance(date_val, str):
                    date_str = date_val.isoformat()
                else:
                    date_str = date_val
                
                # Match documents from that specific date
                conditions.append({
                    '$or': [
                        {'conversation_date': {'$eq': date_str}},
                        {'date': {'$eq': date_str}}
                    ]
                })
        
        # Bridge ID filters
        if parsed['bridge_ids']:
            bridge_conditions = []
            for bridge_id in parsed['bridge_ids']:
                bridge_conditions.append({'bridge_id': {'$eq': bridge_id}})
            
            if len(bridge_conditions) == 1:
                conditions.append(bridge_conditions[0])
            else:
                conditions.append({'$or': bridge_conditions})
        
        # Specific FLOAT pattern filters
        # Note: Chroma doesn't support $exists, so we skip metadata filters for patterns
        # The semantic search will find documents with these patterns
        
        # Combine all conditions
        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {'$and': conditions}
    
    def _build_document_filters(self, parsed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build document content filters.
        
        Currently not used much, but could filter document text directly.
        """
        # For now, we rely on semantic search for document content
        # Future: could add regex filters for specific patterns
        return None
    
    def explain_translation(self, parsed: Dict[str, Any]) -> str:
        """Generate human-readable explanation of the translation."""
        explanation = []
        
        if parsed['text_terms']:
            explanation.append(f"Searching for text: {' '.join(parsed['text_terms'])}")
        
        if parsed['float_patterns']:
            explanation.append(f"Looking for FLOAT patterns: {', '.join(parsed['float_patterns'])}")
        
        if parsed['persona_patterns']:
            explanation.append(f"Looking for personas: {', '.join(parsed['persona_patterns'])}")
        
        if parsed['bridge_ids']:
            explanation.append(f"Looking for bridges: {', '.join(parsed['bridge_ids'])}")
        
        if parsed['temporal_filters']:
            if 'since' in parsed['temporal_filters']:
                explanation.append(f"Since: {parsed['temporal_filters']['since']}")
            if 'date' in parsed['temporal_filters']:
                explanation.append(f"On date: {parsed['temporal_filters']['date']}")
        
        if parsed['type_filters']:
            explanation.append(f"Types: {', '.join(parsed['type_filters'])}")
        
        return ' | '.join(explanation) if explanation else "General search"