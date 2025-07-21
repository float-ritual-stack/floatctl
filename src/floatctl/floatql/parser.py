"""FloatQL Parser - Extracts FLOAT patterns from natural language queries."""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class FloatQLParser:
    """Parser for FloatQL natural language queries.
    
    Recognizes FLOAT patterns:
    - :: notation (ctx::, highlight::, signal::, etc.)
    - [persona::] notation (sysop, karen, qtb, evna, lf1m)
    - Bridge IDs (CB-YYYYMMDD-HHMM-XXXX)
    - Temporal filters (today, yesterday, last week, etc.)
    - Type filters (log, conversation, bridge, etc.)
    """
    
    # Core FLOAT patterns
    FLOAT_PATTERNS = {
        'ctx', 'highlight', 'signal', 'mode', 'project', 'bridge',
        'dispatch', 'float', 'redux', 'uid', 'claude', 'status',
        'priority', 'type', 'content_type', 'context_type'
    }
    
    # Persona patterns
    PERSONA_PATTERNS = {
        'sysop', 'karen', 'qtb', 'evna', 'lf1m', 'littlefucker'
    }
    
    # Bridge ID pattern
    BRIDGE_PATTERN = re.compile(r'CB-\d{8}-\d{4}-[A-Z0-9]{4}')
    
    # Pattern extractors
    FLOAT_MARKER_PATTERN = re.compile(r'(\w+)::', re.IGNORECASE)
    PERSONA_MARKER_PATTERN = re.compile(r'\[(\w+)::\]', re.IGNORECASE)
    
    def __init__(self):
        self.parsed = {}
    
    def parse(self, query: str) -> Dict[str, Any]:
        """Parse a FloatQL query into structured components.
        
        Returns:
            Dictionary with:
            - text_terms: List of plain text search terms
            - float_patterns: List of detected :: patterns
            - persona_patterns: List of detected [persona::] patterns
            - bridge_ids: List of bridge IDs
            - temporal_filters: Dict of time-based filters
            - type_filters: List of type filters
            - raw_query: Original query string
        """
        self.parsed = {
            'text_terms': [],
            'float_patterns': [],
            'persona_patterns': [],
            'bridge_ids': [],
            'temporal_filters': {},
            'type_filters': [],
            'raw_query': query
        }
        
        # Working copy of query for progressive extraction
        remaining_query = query
        
        # Extract bridge IDs
        bridge_matches = self.BRIDGE_PATTERN.findall(remaining_query)
        for bridge_id in bridge_matches:
            self.parsed['bridge_ids'].append(bridge_id)
            remaining_query = remaining_query.replace(bridge_id, '')
        
        # Extract persona patterns [persona::]
        persona_matches = self.PERSONA_MARKER_PATTERN.findall(remaining_query)
        for persona in persona_matches:
            if persona.lower() in self.PERSONA_PATTERNS:
                self.parsed['persona_patterns'].append(persona.lower())
            remaining_query = self.PERSONA_MARKER_PATTERN.sub('', remaining_query, count=1)
        
        # Extract FLOAT :: patterns
        float_matches = self.FLOAT_MARKER_PATTERN.findall(remaining_query)
        for pattern in float_matches:
            if pattern.lower() in self.FLOAT_PATTERNS:
                self.parsed['float_patterns'].append(pattern.lower())
            else:
                # Custom pattern, still include it
                self.parsed['float_patterns'].append(pattern.lower())
            remaining_query = remaining_query.replace(f"{pattern}::", '', 1)
        
        # Extract temporal filters
        remaining_query = self._extract_temporal_filters(remaining_query)
        
        # Extract type filters
        remaining_query = self._extract_type_filters(remaining_query)
        
        # Remaining text becomes search terms
        # Clean up extra spaces and split
        text_terms = remaining_query.strip().split()
        self.parsed['text_terms'] = [term for term in text_terms if term]
        
        return self.parsed
    
    def _extract_temporal_filters(self, query: str) -> str:
        """Extract temporal filters from query."""
        # Common temporal patterns
        temporal_patterns = {
            r'\btoday\b': lambda: datetime.now().date(),
            r'\byesterday\b': lambda: (datetime.now() - timedelta(days=1)).date(),
            r'\blast\s+(\d+)\s+hours?\b': lambda m: datetime.now() - timedelta(hours=int(m.group(1))),
            r'\blast\s+(\d+)\s+days?\b': lambda m: datetime.now() - timedelta(days=int(m.group(1))),
            r'\blast\s+week\b': lambda: datetime.now() - timedelta(days=7),
            r'\bthis\s+week\b': lambda: datetime.now() - timedelta(days=datetime.now().weekday()),
            r'\b(\d{4}-\d{2}-\d{2})\b': lambda m: datetime.strptime(m.group(1), '%Y-%m-%d').date()
        }
        
        remaining = query
        for pattern, date_func in temporal_patterns.items():
            match = re.search(pattern, remaining, re.IGNORECASE)
            if match:
                # Extract the temporal filter
                if hasattr(date_func, '__call__'):
                    if match.groups():
                        date_value = date_func(match)
                    else:
                        date_value = date_func()
                    
                    # Store the filter
                    if isinstance(date_value, datetime):
                        self.parsed['temporal_filters']['since'] = date_value
                    else:
                        self.parsed['temporal_filters']['date'] = date_value
                
                # Remove from query
                remaining = remaining[:match.start()] + remaining[match.end():]
        
        return remaining
    
    def _extract_type_filters(self, query: str) -> str:
        """Extract type filters from query."""
        # Common type patterns
        type_patterns = {
            r'\btype:\s*(\w+)\b': 'explicit',
            r'\b(logs?|conversations?|bridges?|dispatches?|highlights?)\b': 'implicit'
        }
        
        remaining = query
        for pattern, style in type_patterns.items():
            matches = re.finditer(pattern, remaining, re.IGNORECASE)
            for match in matches:
                if style == 'explicit':
                    type_value = match.group(1).lower()
                else:
                    # Normalize plural to singular
                    type_value = match.group(1).lower().rstrip('s')
                
                if type_value not in self.parsed['type_filters']:
                    self.parsed['type_filters'].append(type_value)
        
        # Remove explicit type: filters
        remaining = re.sub(r'\btype:\s*\w+\b', '', remaining, flags=re.IGNORECASE)
        
        return remaining
    
    def is_floatql_query(self, query: str) -> bool:
        """Check if query contains FloatQL patterns."""
        # Check for :: patterns
        if '::' in query:
            return True
        
        # Check for bridge IDs
        if self.BRIDGE_PATTERN.search(query):
            return True
        
        # Check for temporal keywords
        temporal_keywords = ['today', 'yesterday', 'last', 'week', 'hours', 'days']
        if any(keyword in query.lower() for keyword in temporal_keywords):
            return True
        
        # Check for type filters
        if 'type:' in query.lower():
            return True
        
        return False
    
    def get_suggested_collections(self, parsed: Dict[str, Any]) -> List[str]:
        """Suggest collections based on parsed query components."""
        suggestions = []
        
        # Bridge queries -> bridge collections
        if parsed['bridge_ids']:
            suggestions.extend(['float_bridges', 'rangle_bridges', 'archived_float_bridges'])
        
        # Context patterns -> active streams
        if 'ctx' in parsed['float_patterns']:
            suggestions.extend(['active_context_stream', 'daily_context_hotcache'])
        
        # Highlight patterns -> highlight collections
        if 'highlight' in parsed['float_patterns']:
            suggestions.extend(['float_highlights', 'conversation_highlights'])
        
        # Dispatch patterns -> dispatch collections
        if 'dispatch' in parsed['float_patterns']:
            suggestions.extend(['float_dispatch_bay', 'dispatch_bay'])
        
        # Conversation type -> conversation collections
        if 'conversation' in parsed['type_filters']:
            suggestions.extend(['float_conversations_active', 'my_conversations'])
        
        # Bridge type -> bridge collections
        if 'bridge' in parsed['type_filters']:
            suggestions.extend(['float_bridges', 'rangle_bridges', 'archived_float_bridges'])
        
        # Recent temporal filters -> active collections
        if parsed['temporal_filters']:
            suggestions.extend(['active_context_stream', 'daily_context_hotcache'])
        
        # Default if no specific patterns
        if not suggestions:
            suggestions = ['active_context_stream', 'float_bridges', 'float_highlights']
        
        # Remove duplicates while preserving order
        seen = set()
        return [x for x in suggestions if not (x in seen or seen.add(x))]
    
    def extract_search_terms(self, parsed: Dict[str, Any]) -> str:
        """Extract a basic search query from parsed components."""
        terms = []
        
        # Include text terms
        terms.extend(parsed['text_terms'])
        
        # Include pattern values as search terms
        for pattern in parsed['float_patterns']:
            terms.append(f"{pattern}::")
        
        for persona in parsed['persona_patterns']:
            terms.append(f"[{persona}::]")
        
        # Include bridge IDs
        terms.extend(parsed['bridge_ids'])
        
        return ' '.join(terms)