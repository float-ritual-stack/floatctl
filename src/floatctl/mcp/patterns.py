"""Pattern processing for FLOAT consciousness technology :: patterns.

This module contains the core pattern recognition engine for FLOAT consciousness patterns.
Extracted from the monolithic mcp_server.py for maintainability.
"""

import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Pattern routing configuration for consciousness technology
PATTERN_ROUTING = {
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
        # Find ALL :: patterns in the text - now supports dots in pattern names
        all_patterns = re.findall(r'([a-zA-Z0-9._-]+)::\s*([^\n]*)', text, re.IGNORECASE)
        
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
            
            # Also extract nested patterns from within brackets (with dots support)
            nested_patterns = re.findall(r'\[([a-zA-Z0-9._-]+)::\s*([^\]]+)\]', pattern_content)
            for nested_name, nested_content in nested_patterns:
                nested_name = nested_name.lower().strip()
                nested_content = nested_content.strip()
                
                patterns_found.append({
                    "type": nested_name,
                    "content": nested_content,
                    "full_match": f"[{nested_name}::{nested_content}]"
                })
                
                # Store the nested pattern content
                metadata[f"{nested_name}_content"] = nested_content
        
        # Also look for function-style patterns like float.dispatch({ or float.ritual({
        function_patterns = re.findall(r'(float\.[a-zA-Z_]+|float)\s*\(\s*\{([^}]*)\}?', text, re.IGNORECASE)
        for func_name, func_content in function_patterns:
            func_name = func_name.lower().strip()
            func_content = func_content.strip()
            
            patterns_found.append({
                "type": func_name,
                "content": func_content,
                "full_match": f"{func_name}({{{func_content}"
            })
            
            # Store the function pattern content
            metadata[f"{func_name.replace('.', '_')}_content"] = func_content
            metadata["has_function_patterns"] = True
        
        metadata["extraction_method"] = "legacy"
    
    # If we found patterns, set the primary type
    if patterns_found:
        # Convert list to comma-separated string for ChromaDB compatibility
        metadata["patterns_found"] = ",".join([p["type"] for p in patterns_found])
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


def get_pattern_collection(primary_pattern: str) -> str:
    """Get the target collection for a pattern type using the routing table."""
    return PATTERN_ROUTING.get(primary_pattern, "active_context_stream")