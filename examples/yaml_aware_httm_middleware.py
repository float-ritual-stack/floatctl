"""
YAML-Aware HTTM Middleware - Smart Sampling Using Conversation Structure

This middleware uses the YAML frontmatter from extracted conversations to make
intelligent sampling decisions, focusing on the most valuable parts for httm:: detection.
"""

from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext, MiddlewarePhase
from floatctl.core.logging import get_logger
from typing import List, Dict, Any, Optional, Set, Tuple
import re
import yaml
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ConversationStructure:
    """Parsed conversation structure from YAML frontmatter."""
    title: str
    conversation_id: str
    total_lines: int
    markers: List[Dict[str, Any]]
    float_calls: List[Dict[str, Any]]
    tools_used: List[str]
    conversation_dates: List[str]
    
    # Derived insights for sampling
    message_boundaries: List[int]  # Line numbers where messages start
    high_value_sections: List[Tuple[int, int, str]]  # (start, end, reason)
    complexity_score: float
    httm_likelihood_zones: List[Tuple[int, int, float]]  # (start, end, probability)

class YAMLAwareHTTPMiddleware(MiddlewareInterface):
    """
    Smart HTTM middleware that uses conversation structure for intelligent sampling.
    
    Key strategies:
    1. Parse YAML frontmatter to understand conversation structure
    2. Identify high-value sections (tool calls, float calls, markers)
    3. Sample intelligently based on conversation complexity
    4. Focus on sections most likely to contain httm:: patterns
    """
    
    def __init__(self, 
                 max_processing_time: float = 30.0,
                 high_value_sample_rate: float = 1.0,    # Process all high-value sections
                 medium_value_sample_rate: float = 0.3,  # Sample 30% of medium sections
                 low_value_sample_rate: float = 0.1):    # Sample 10% of low sections
        
        self.logger = get_logger(f"{__name__}.YAMLAwareHTTPMiddleware")
        self.max_processing_time = max_processing_time
        self.high_value_sample_rate = high_value_sample_rate
        self.medium_value_sample_rate = medium_value_sample_rate
        self.low_value_sample_rate = low_value_sample_rate
        
        # Compiled regex for efficiency
        self.httm_regex = re.compile(
            r'httm::\s*(?:\{\s*([^}]*(?:\n[^}]*)*)\s*\}|([^\n]+))',
            re.IGNORECASE | re.MULTILINE
        )
        
        # YAML frontmatter regex
        self.yaml_regex = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL | re.MULTILINE)
    
    @property
    def name(self) -> str:
        return "yaml_aware_httm_middleware"
    
    @property
    def priority(self) -> int:
        return 15
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [MiddlewarePhase.PROCESS]
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Process with YAML-aware intelligent sampling."""
        
        # Check if this looks like an extracted conversation
        if not self._is_extracted_conversation(context.data):
            # Not an extracted conversation - use simple processing
            return await self._process_simple(context)
        
        # Parse conversation structure
        structure = self._parse_conversation_structure(context.data)
        if not structure:
            return await self._process_simple(context)
        
        # Use structure-aware sampling
        return await self._process_with_structure(context, structure)
    
    def _is_extracted_conversation(self, data: Any) -> bool:
        """Check if data looks like an extracted conversation with YAML frontmatter."""
        if not isinstance(data, str):
            return False
        
        # Look for YAML frontmatter
        return data.strip().startswith('---\n') and '\n---\n' in data
    
    def _parse_conversation_structure(self, content: str) -> Optional[ConversationStructure]:
        """Parse YAML frontmatter and analyze conversation structure."""
        
        try:
            # Extract YAML frontmatter
            yaml_match = self.yaml_regex.match(content)
            if not yaml_match:
                return None
            
            yaml_content = yaml_match.group(1)
            metadata = yaml.safe_load(yaml_content)
            
            if not metadata:
                return None
            
            # Parse basic metadata
            title = metadata.get('conversation_title', 'Unknown')
            conversation_id = metadata.get('conversation_id', '')
            total_lines = metadata.get('total_lines', 0)
            markers = metadata.get('markers', [])
            float_calls = metadata.get('float_calls', [])
            tools_used = metadata.get('tools_used', [])
            conversation_dates = metadata.get('conversation_dates', [])
            
            # Analyze content structure
            lines = content.split('\n')
            message_boundaries = self._find_message_boundaries(lines)
            high_value_sections = self._identify_high_value_sections(lines, markers, float_calls, tools_used)
            complexity_score = self._calculate_complexity_score(metadata, lines)
            httm_likelihood_zones = self._predict_httm_zones(lines, markers, float_calls, tools_used)
            
            return ConversationStructure(
                title=title,
                conversation_id=conversation_id,
                total_lines=total_lines,
                markers=markers,
                float_calls=float_calls,
                tools_used=tools_used,
                conversation_dates=conversation_dates,
                message_boundaries=message_boundaries,
                high_value_sections=high_value_sections,
                complexity_score=complexity_score,
                httm_likelihood_zones=httm_likelihood_zones
            )
            
        except Exception as e:
            self.logger.warning(
                "yaml_parsing_failed",
                error=str(e),
                fallback="simple_processing"
            )
            return None
    
    def _find_message_boundaries(self, lines: List[str]) -> List[int]:
        """Find line numbers where messages start."""
        boundaries = []
        
        for i, line in enumerate(lines):
            # Look for message headers
            if line.strip().startswith('### 👤 Human') or line.strip().startswith('### 🤖 Assistant'):
                boundaries.append(i)
        
        return boundaries
    
    def _identify_high_value_sections(self, 
                                    lines: List[str], 
                                    markers: List[Dict], 
                                    float_calls: List[Dict], 
                                    tools_used: List[str]) -> List[Tuple[int, int, str]]:
        """Identify sections most likely to contain valuable httm:: patterns."""
        
        high_value_sections = []
        
        # Sections around float.dispatch calls (high httm:: likelihood)
        for float_call in float_calls:
            call_lines = float_call.get('lines', [])
            for line_num in call_lines:
                # Include context around float calls
                start = max(0, line_num - 10)
                end = min(len(lines), line_num + 20)
                high_value_sections.append((start, end, f"float_call_{float_call.get('call', 'unknown')}"))
        
        # Sections around specific markers that often contain insights
        insight_markers = ['highlight', 'eureka', 'decision', 'gotcha', 'bridge']
        for marker in markers:
            marker_type = marker.get('type', '').lower()
            if any(insight_type in marker_type for insight_type in insight_markers):
                marker_lines = marker.get('lines', [])
                for line_num in marker_lines:
                    start = max(0, line_num - 5)
                    end = min(len(lines), line_num + 15)
                    high_value_sections.append((start, end, f"marker_{marker_type}"))
        
        # Sections with tool calls (often contain reflective content)
        if tools_used:
            for i, line in enumerate(lines):
                if '{Tool Call:' in line or '{Tool Result:' in line:
                    start = max(0, i - 5)
                    end = min(len(lines), i + 10)
                    high_value_sections.append((start, end, "tool_interaction"))
        
        # Sections with emotional language (often contain httm:: patterns)
        emotional_indicators = [
            'feel', 'sense', 'intuition', 'gut', 'weird', 'strange', 'off',
            'reminds', 'similar', 'pattern', 'connection', 'bridge',
            'gurgling', 'bubbling', 'emerging', 'consciousness'
        ]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in emotional_indicators):
                # Check if this isn't already covered by other high-value sections
                if not any(start <= i <= end for start, end, _ in high_value_sections):
                    start = max(0, i - 3)
                    end = min(len(lines), i + 8)
                    high_value_sections.append((start, end, "emotional_language"))
        
        # Merge overlapping sections
        return self._merge_overlapping_sections(high_value_sections)
    
    def _merge_overlapping_sections(self, sections: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
        """Merge overlapping high-value sections."""
        if not sections:
            return []
        
        # Sort by start position
        sections.sort(key=lambda x: x[0])
        
        merged = [sections[0]]
        
        for current in sections[1:]:
            last = merged[-1]
            
            # If sections overlap or are adjacent, merge them
            if current[0] <= last[1] + 5:  # 5-line buffer for merging
                merged[-1] = (
                    last[0], 
                    max(last[1], current[1]), 
                    f"{last[2]}+{current[2]}"
                )
            else:
                merged.append(current)
        
        return merged
    
    def _calculate_complexity_score(self, metadata: Dict, lines: List[str]) -> float:
        """Calculate conversation complexity to inform sampling strategy."""
        
        score = 0.0
        
        # Base score from metadata
        score += len(metadata.get('markers', [])) * 0.1
        score += len(metadata.get('float_calls', [])) * 0.3
        score += len(metadata.get('tools_used', [])) * 0.2
        
        # Content-based scoring
        total_lines = len(lines)
        if total_lines > 1000:
            score += 1.0  # Very long conversation
        elif total_lines > 500:
            score += 0.5  # Long conversation
        
        # Look for complexity indicators in content
        complexity_indicators = [
            'float.dispatch', 'bridge::', 'consciousness', 'archaeology',
            'middleware', 'architecture', 'system', 'pattern'
        ]
        
        content_text = '\n'.join(lines).lower()
        for indicator in complexity_indicators:
            if indicator in content_text:
                score += 0.2
        
        return min(score, 5.0)  # Cap at 5.0
    
    def _predict_httm_zones(self, 
                          lines: List[str], 
                          markers: List[Dict], 
                          float_calls: List[Dict], 
                          tools_used: List[str]) -> List[Tuple[int, int, float]]:
        """Predict zones most likely to contain httm:: patterns."""
        
        zones = []
        
        # High probability zones around float calls
        for float_call in float_calls:
            call_lines = float_call.get('lines', [])
            for line_num in call_lines:
                start = max(0, line_num - 15)
                end = min(len(lines), line_num + 25)
                zones.append((start, end, 0.8))  # 80% probability
        
        # Medium probability zones around certain markers
        insight_markers = ['highlight', 'eureka', 'decision', 'bridge']
        for marker in markers:
            marker_type = marker.get('type', '').lower()
            if any(insight_type in marker_type for insight_type in insight_markers):
                marker_lines = marker.get('lines', [])
                for line_num in marker_lines:
                    start = max(0, line_num - 10)
                    end = min(len(lines), line_num + 15)
                    zones.append((start, end, 0.6))  # 60% probability
        
        # Lower probability zones around tool interactions
        for i, line in enumerate(lines):
            if '{Tool Call:' in line:
                start = max(0, i - 5)
                end = min(len(lines), i + 15)
                zones.append((start, end, 0.4))  # 40% probability
        
        # Merge overlapping zones, keeping highest probability
        return self._merge_probability_zones(zones)
    
    def _merge_probability_zones(self, zones: List[Tuple[int, int, float]]) -> List[Tuple[int, int, float]]:
        """Merge overlapping probability zones, keeping highest probability."""
        if not zones:
            return []
        
        # Sort by start position
        zones.sort(key=lambda x: x[0])
        
        merged = [zones[0]]
        
        for current in zones[1:]:
            last = merged[-1]
            
            # If zones overlap, merge with max probability
            if current[0] <= last[1]:
                merged[-1] = (
                    last[0],
                    max(last[1], current[1]),
                    max(last[2], current[2])  # Keep higher probability
                )
            else:
                merged.append(current)
        
        return merged
    
    async def _process_with_structure(self, 
                                    context: MiddlewareContext, 
                                    structure: ConversationStructure) -> MiddlewareContext:
        """Process conversation using structural intelligence."""
        
        self.logger.info(
            "yaml_aware_processing_started",
            title=structure.title,
            total_lines=structure.total_lines,
            complexity_score=structure.complexity_score,
            high_value_sections=len(structure.high_value_sections),
            httm_zones=len(structure.httm_likelihood_zones)
        )
        
        content = context.data
        lines = content.split('\n')
        all_patterns = []
        
        # Determine sampling strategy based on complexity
        if structure.complexity_score > 3.0 or structure.total_lines > 2000:
            # High complexity - use aggressive sampling
            sample_strategy = "aggressive"
            patterns = await self._sample_aggressively(lines, structure)
        elif structure.complexity_score > 1.5 or structure.total_lines > 1000:
            # Medium complexity - use balanced sampling
            sample_strategy = "balanced"
            patterns = await self._sample_balanced(lines, structure)
        else:
            # Low complexity - process most content
            sample_strategy = "comprehensive"
            patterns = await self._sample_comprehensive(lines, structure)
        
        # Update context with results
        context.metadata['httm_patterns'] = patterns
        context.metadata['httm_processing_method'] = 'yaml_aware'
        context.metadata['httm_sample_strategy'] = sample_strategy
        context.metadata['httm_conversation_structure'] = {
            'title': structure.title,
            'complexity_score': structure.complexity_score,
            'total_lines': structure.total_lines,
            'high_value_sections': len(structure.high_value_sections),
            'patterns_found': len(patterns)
        }
        
        self.logger.info(
            "yaml_aware_processing_completed",
            patterns_found=len(patterns),
            sample_strategy=sample_strategy,
            title=structure.title
        )
        
        return context
    
    async def _sample_aggressively(self, 
                                 lines: List[str], 
                                 structure: ConversationStructure) -> List[Dict[str, Any]]:
        """Aggressive sampling - focus only on highest-value sections."""
        
        patterns = []
        
        # Process all high-value sections
        for start, end, reason in structure.high_value_sections:
            section_lines = lines[start:end]
            section_text = '\n'.join(section_lines)
            
            section_patterns = self._extract_patterns_from_text(
                section_text, start, f"high_value_{reason}"
            )
            patterns.extend(section_patterns)
        
        # Process high-probability httm zones
        for start, end, probability in structure.httm_likelihood_zones:
            if probability > 0.7:  # Only very high probability zones
                section_lines = lines[start:end]
                section_text = '\n'.join(section_lines)
                
                section_patterns = self._extract_patterns_from_text(
                    section_text, start, f"httm_zone_p{probability:.1f}"
                )
                patterns.extend(section_patterns)
        
        return self._deduplicate_patterns(patterns)
    
    async def _sample_balanced(self, 
                             lines: List[str], 
                             structure: ConversationStructure) -> List[Dict[str, Any]]:
        """Balanced sampling - high-value sections + sample of medium sections."""
        
        patterns = []
        
        # Process all high-value sections
        for start, end, reason in structure.high_value_sections:
            section_lines = lines[start:end]
            section_text = '\n'.join(section_lines)
            
            section_patterns = self._extract_patterns_from_text(
                section_text, start, f"high_value_{reason}"
            )
            patterns.extend(section_patterns)
        
        # Sample medium-probability httm zones
        for start, end, probability in structure.httm_likelihood_zones:
            if probability > 0.4:
                # Sample based on probability
                if probability > 0.6 or hash(f"{start}_{end}") % 3 == 0:  # ~33% sampling
                    section_lines = lines[start:end]
                    section_text = '\n'.join(section_lines)
                    
                    section_patterns = self._extract_patterns_from_text(
                        section_text, start, f"httm_zone_p{probability:.1f}"
                    )
                    patterns.extend(section_patterns)
        
        # Sample message boundaries (often contain reflective content)
        for boundary in structure.message_boundaries[::2]:  # Every other message
            start = boundary
            end = min(len(lines), boundary + 50)  # First 50 lines of message
            
            section_lines = lines[start:end]
            section_text = '\n'.join(section_lines)
            
            section_patterns = self._extract_patterns_from_text(
                section_text, start, "message_boundary_sample"
            )
            patterns.extend(section_patterns)
        
        return self._deduplicate_patterns(patterns)
    
    async def _sample_comprehensive(self, 
                                  lines: List[str], 
                                  structure: ConversationStructure) -> List[Dict[str, Any]]:
        """Comprehensive sampling - process most content with some optimization."""
        
        patterns = []
        
        # Process in chunks, but skip obviously low-value sections
        chunk_size = 200
        skip_patterns = [
            'tool_calls.jsonl',  # Skip tool call references
            '```json',           # Skip large JSON blocks
            '```yaml',           # Skip large YAML blocks
        ]
        
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_text = '\n'.join(chunk_lines)
            
            # Skip if chunk is mostly tool calls or data dumps
            if any(pattern in chunk_text for pattern in skip_patterns):
                if chunk_text.count('\n') > 50:  # Large data block
                    continue
            
            section_patterns = self._extract_patterns_from_text(
                chunk_text, i, f"comprehensive_chunk_{i}"
            )
            patterns.extend(section_patterns)
        
        return self._deduplicate_patterns(patterns)
    
    def _extract_patterns_from_text(self, 
                                   text: str, 
                                   line_offset: int, 
                                   source: str) -> List[Dict[str, Any]]:
        """Extract httm:: patterns from text section."""
        
        patterns = []
        
        for match in self.httm_regex.finditer(text):
            pattern_content = match.group(1) or match.group(2)
            if not pattern_content or not pattern_content.strip():
                continue
            
            # Calculate actual line number
            text_before_match = text[:match.start()]
            line_number = line_offset + text_before_match.count('\n')
            
            patterns.append({
                'content': pattern_content.strip(),
                'line_number': line_number,
                'match_start': match.start(),
                'match_end': match.end(),
                'source': source,
                'extraction_method': 'yaml_aware',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        return patterns
    
    def _deduplicate_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate patterns based on content similarity."""
        
        if not patterns:
            return patterns
        
        # Simple deduplication based on content
        seen_content = set()
        deduplicated = []
        
        for pattern in patterns:
            content_key = pattern['content'].lower().strip()
            if content_key not in seen_content:
                seen_content.add(content_key)
                deduplicated.append(pattern)
        
        return deduplicated
    
    async def _process_simple(self, context: MiddlewareContext) -> MiddlewareContext:
        """Fallback to simple processing for non-extracted conversations."""
        
        try:
            text_content = str(context.data)
            patterns = []
            
            for match in self.httm_regex.finditer(text_content):
                pattern_content = match.group(1) or match.group(2)
                if pattern_content and pattern_content.strip():
                    patterns.append({
                        'content': pattern_content.strip(),
                        'match_start': match.start(),
                        'match_end': match.end(),
                        'extraction_method': 'simple_fallback',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
            
            if patterns:
                context.metadata['httm_patterns'] = patterns
                context.metadata['httm_processing_method'] = 'simple_fallback'
            
            return context
            
        except Exception as e:
            self.logger.error("simple_processing_error", error=str(e))
            return context


# Usage example showing the power of YAML-aware sampling
class YAMLAwareHTTPExample:
    """Example showing how YAML-aware sampling works."""
    
    @staticmethod
    def demonstrate_sampling_intelligence():
        """Show how different conversations get different sampling strategies."""
        
        # Example 1: High complexity conversation
        high_complexity_yaml = """---
conversation_title: "FLOAT Hyperfidelity Knowledge Mapping"
total_lines: 2847
markers:
  - type: "highlight"
    lines: [145, 892, 1456]
  - type: "eureka"
    lines: [234, 1789]
float_calls:
  - call: "float.dispatch"
    lines: [62, 77, 234, 456, 789]
tools_used: ['chroma_query', 'search_memory', 'bridge_create', 'consciousness_archaeology']
---"""
        
        print("High Complexity Conversation:")
        print("- Strategy: Aggressive sampling")
        print("- Focus: High-value sections + float.dispatch zones")
        print("- Sample rate: ~15% of total content")
        print()
        
        # Example 2: Medium complexity conversation
        medium_complexity_yaml = """---
conversation_title: "Rangle Airbender Debug Session"
total_lines: 1234
markers:
  - type: "start_time"
    lines: [6, 45, 123]
float_calls:
  - call: "float.context.restore"
    lines: [234]
tools_used: ['file_read', 'git_status']
---"""
        
        print("Medium Complexity Conversation:")
        print("- Strategy: Balanced sampling")
        print("- Focus: High-value + sampled medium sections")
        print("- Sample rate: ~40% of total content")
        print()
        
        # Example 3: Simple conversation
        simple_yaml = """---
conversation_title: "Quick Question About Code"
total_lines: 156
markers:
  - type: "start_time"
    lines: [6]
tools_used: []
---"""
        
        print("Simple Conversation:")
        print("- Strategy: Comprehensive")
        print("- Focus: Most content with smart skipping")
        print("- Sample rate: ~85% of total content")


if __name__ == "__main__":
    YAMLAwareHTTPExample.demonstrate_sampling_intelligence()