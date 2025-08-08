"""
HTTM Pattern Detection Middleware Example

This middleware demonstrates how to capture and process `httm::` patterns
(representing "gurgling" or intuitive insights) across all FloatCtl operations.
"""

from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext, MiddlewarePhase
from floatctl.core.logging import get_logger
from typing import List, Dict, Any, Optional
import re
from datetime import datetime, timezone
from pathlib import Path
import json

class HTTPMiddleware(MiddlewareInterface):
    """
    Middleware that detects and processes `httm::` patterns across all operations.
    
    HTTM (Heuristic Thought-Thread Mapping) patterns represent those moments of
    intuitive insight, "gurgling" thoughts, or emergent understanding that bubble
    up during processing.
    
    Examples it would catch:
    - httm:: something feels off about this data structure
    - httm:: { the user is asking for X but really needs Y }
    - httm:: this reminds me of the bridge pattern from last week
    - httm:: { gurgling about consciousness archaeology }
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.logger = get_logger(f"{__name__}.HTTPMiddleware")
        self.output_dir = output_dir or Path.home() / ".floatctl" / "httm_captures"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory store for this session
        self.httm_patterns = []
        
        # Pattern matching for various httm:: formats
        self.httm_patterns_regex = [
            # Basic: httm:: content
            r'httm::\s*([^\n]+)',
            # Bracketed: httm:: { content }
            r'httm::\s*\{\s*([^}]+)\s*\}',
            # Multi-line with context
            r'httm::\s*\{([^}]*(?:\n[^}]*)*)\}',
        ]
    
    @property
    def name(self) -> str:
        return "httm_pattern_detector"
    
    @property
    def priority(self) -> int:
        return 20  # Run early to catch patterns before other transformations
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [
            MiddlewarePhase.PRE_PROCESS,  # Scan incoming data
            MiddlewarePhase.PROCESS,      # Scan during processing
            MiddlewarePhase.POST_PROCESS, # Final scan and storage
            MiddlewarePhase.CLEANUP       # Session cleanup
        ]
    
    async def pre_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Scan incoming data for httm:: patterns."""
        patterns = self._extract_httm_patterns(context.data, "input", context)
        
        if patterns:
            self.logger.info(
                "httm_patterns_detected_input",
                operation=context.operation,
                pattern_count=len(patterns),
                patterns=[p['content'][:50] + "..." if len(p['content']) > 50 else p['content'] for p in patterns]
            )
            
            # Add to context metadata for other middleware to use
            context.metadata['httm_input_patterns'] = patterns
        
        return context
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Monitor for httm:: patterns that emerge during processing."""
        
        # Check if data was transformed and scan for new patterns
        if hasattr(context, '_original_data'):
            patterns = self._extract_httm_patterns(context.data, "processing", context)
            if patterns:
                context.metadata['httm_processing_patterns'] = patterns
        
        return context
    
    async def post_process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Final scan and storage of httm:: patterns."""
        
        # Collect all patterns found during this operation
        all_patterns = []
        
        # Input patterns
        all_patterns.extend(context.metadata.get('httm_input_patterns', []))
        
        # Processing patterns  
        all_patterns.extend(context.metadata.get('httm_processing_patterns', []))
        
        # Final output scan
        output_patterns = self._extract_httm_patterns(context.data, "output", context)
        all_patterns.extend(output_patterns)
        
        if all_patterns:
            # Store patterns for this session
            self.httm_patterns.extend(all_patterns)
            
            # Emit event for other plugins to react
            await self.emit_event("httm_patterns_detected", {
                "operation": context.operation,
                "patterns": all_patterns,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Save to persistent storage
            await self._save_httm_patterns(all_patterns, context)
            
            # Add summary to context
            context.metadata['httm_total_patterns'] = len(all_patterns)
            context.metadata['httm_summary'] = [
                {
                    'content_preview': p['content'][:100],
                    'source': p['source'],
                    'confidence': p.get('confidence', 1.0)
                }
                for p in all_patterns
            ]
        
        return context
    
    async def cleanup(self, context: MiddlewareContext) -> None:
        """Session cleanup and pattern analysis."""
        
        # If we have patterns from this session, do some analysis
        if self.httm_patterns:
            session_summary = self._analyze_session_patterns()
            
            # Save session summary
            session_file = self.output_dir / f"httm_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(session_file, 'w') as f:
                json.dump(session_summary, f, indent=2)
            
            self.logger.info(
                "httm_session_complete",
                total_patterns=len(self.httm_patterns),
                unique_operations=len(set(p.get('operation') for p in self.httm_patterns)),
                session_file=str(session_file)
            )
    
    def _extract_httm_patterns(self, data: Any, source: str, context: MiddlewareContext) -> List[Dict[str, Any]]:
        """Extract httm:: patterns from data."""
        patterns = []
        
        # Convert data to searchable text
        text_content = self._extract_text_content(data)
        if not text_content:
            return patterns
        
        # Apply each regex pattern
        for regex_pattern in self.httm_patterns_regex:
            matches = re.finditer(regex_pattern, text_content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                content = match.group(1).strip()
                
                # Skip empty matches
                if not content:
                    continue
                
                # Analyze the pattern
                analysis = self._analyze_httm_content(content)
                
                pattern_info = {
                    'content': content,
                    'source': source,
                    'operation': context.operation,
                    'plugin': context.plugin_name,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'match_start': match.start(),
                    'match_end': match.end(),
                    'regex_used': regex_pattern,
                    'analysis': analysis,
                    'confidence': analysis.get('confidence', 1.0),
                    'context_metadata': {
                        'file_path': str(context.file_path) if context.file_path else None,
                        'phase': context.phase.value if context.phase else None
                    }
                }
                
                patterns.append(pattern_info)
        
        return patterns
    
    def _extract_text_content(self, data: Any) -> str:
        """Extract searchable text from various data types."""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            # Handle conversation data
            if 'messages' in data:
                text_parts = []
                for message in data['messages']:
                    content = message.get('content', '')
                    if isinstance(content, list):
                        # Handle structured content
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                text_parts.append(item.get('text', ''))
                    else:
                        text_parts.append(str(content))
                return '\n'.join(text_parts)
            else:
                # Generic dict - extract all string values
                return ' '.join(str(v) for v in data.values() if isinstance(v, (str, int, float)))
        elif isinstance(data, list):
            return ' '.join(str(item) for item in data)
        else:
            return str(data)
    
    def _analyze_httm_content(self, content: str) -> Dict[str, Any]:
        """Analyze httm:: content for patterns and insights."""
        analysis = {
            'length': len(content),
            'word_count': len(content.split()),
            'confidence': 1.0,
            'categories': [],
            'emotional_indicators': [],
            'cognitive_markers': []
        }
        
        content_lower = content.lower()
        
        # Categorize the httm pattern
        if any(word in content_lower for word in ['feel', 'sense', 'intuition', 'gut']):
            analysis['categories'].append('intuitive')
            analysis['emotional_indicators'].append('intuitive_sensing')
        
        if any(word in content_lower for word in ['gurgling', 'bubbling', 'emerging']):
            analysis['categories'].append('emergent')
            analysis['cognitive_markers'].append('emergence_language')
        
        if any(word in content_lower for word in ['reminds', 'similar', 'like', 'pattern']):
            analysis['categories'].append('pattern_recognition')
            analysis['cognitive_markers'].append('pattern_matching')
        
        if any(word in content_lower for word in ['wrong', 'off', 'weird', 'strange']):
            analysis['categories'].append('anomaly_detection')
            analysis['emotional_indicators'].append('dissonance')
        
        if any(word in content_lower for word in ['bridge', 'connection', 'link']):
            analysis['categories'].append('connection_making')
            analysis['cognitive_markers'].append('synthesis')
        
        # Confidence scoring based on content richness
        if len(analysis['categories']) > 1:
            analysis['confidence'] = min(1.0, analysis['confidence'] + 0.2)
        
        if analysis['word_count'] > 10:
            analysis['confidence'] = min(1.0, analysis['confidence'] + 0.1)
        
        # Check for bracketed content (often more intentional)
        if content.strip().startswith('{') and content.strip().endswith('}'):
            analysis['confidence'] = min(1.0, analysis['confidence'] + 0.3)
            analysis['categories'].append('intentional_capture')
        
        return analysis
    
    async def _save_httm_patterns(self, patterns: List[Dict[str, Any]], context: MiddlewareContext) -> None:
        """Save httm patterns to persistent storage."""
        
        # Create operation-specific file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        operation_safe = re.sub(r'[^\w\-_]', '_', context.operation or 'unknown')
        filename = f"httm_{operation_safe}_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        save_data = {
            'operation': context.operation,
            'plugin': context.plugin_name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'patterns': patterns,
            'context': {
                'file_path': str(context.file_path) if context.file_path else None,
                'metadata': context.metadata
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        self.logger.debug("httm_patterns_saved", filepath=str(filepath), pattern_count=len(patterns))
    
    def _analyze_session_patterns(self) -> Dict[str, Any]:
        """Analyze all patterns from this session."""
        if not self.httm_patterns:
            return {}
        
        # Group by categories
        category_counts = {}
        for pattern in self.httm_patterns:
            for category in pattern.get('analysis', {}).get('categories', []):
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Find most common operations
        operation_counts = {}
        for pattern in self.httm_patterns:
            op = pattern.get('operation', 'unknown')
            operation_counts[op] = operation_counts.get(op, 0) + 1
        
        # Calculate average confidence
        confidences = [p.get('confidence', 1.0) for p in self.httm_patterns]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'session_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_patterns': len(self.httm_patterns),
            'category_distribution': category_counts,
            'operation_distribution': operation_counts,
            'average_confidence': avg_confidence,
            'high_confidence_patterns': [
                p for p in self.httm_patterns 
                if p.get('confidence', 0) > 0.8
            ],
            'patterns': self.httm_patterns
        }
    
    # Event emission method (would be available through PluginBase)
    async def emit_event(self, event_type: str, data: Any = None, **kwargs) -> None:
        """Emit event - this would be inherited from PluginBase in real implementation."""
        # In a real plugin, this would use the middleware manager's event system
        self.logger.info("httm_event_emitted", event_type=event_type, data=data)


# Example of how another plugin could listen for httm:: patterns
class HTTPReactionPlugin:
    """Example plugin that reacts to httm:: pattern detection."""
    
    def __init__(self):
        # Subscribe to httm events
        self.subscribe_to_event("httm_patterns_detected", self._on_httm_detected)
    
    async def _on_httm_detected(self, data, **kwargs):
        """React to httm:: pattern detection."""
        patterns = data.get('patterns', [])
        operation = data.get('operation')
        
        print(f"🧠 HTTM patterns detected in {operation}:")
        
        for pattern in patterns:
            content = pattern['content']
            categories = pattern.get('analysis', {}).get('categories', [])
            confidence = pattern.get('confidence', 1.0)
            
            print(f"  • {content[:80]}{'...' if len(content) > 80 else ''}")
            print(f"    Categories: {', '.join(categories)}")
            print(f"    Confidence: {confidence:.2f}")
            print()
        
        # Could trigger additional processing:
        # - Save to special httm:: collection in ChromaDB
        # - Send to consciousness archaeology pipeline
        # - Trigger bridge creation if patterns connect to existing knowledge
        # - Alert user if high-confidence anomaly detection


# Example usage in a plugin
class MyPluginWithHTTM(PluginBase, MiddlewareInterface):
    """Example of a plugin that both uses and generates httm:: patterns."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.httm_middleware = HTTPMiddleware()
    
    def register_commands(self, cli_group):
        @cli_group.command()
        def analyze_httm():
            """Analyze captured httm:: patterns."""
            httm_dir = Path.home() / ".floatctl" / "httm_captures"
            
            if not httm_dir.exists():
                click.echo("No httm:: patterns captured yet")
                return
            
            # Load and analyze all httm files
            all_patterns = []
            for httm_file in httm_dir.glob("httm_*.json"):
                with open(httm_file) as f:
                    data = json.load(f)
                    all_patterns.extend(data.get('patterns', []))
            
            if not all_patterns:
                click.echo("No httm:: patterns found")
                return
            
            # Show analysis
            click.echo(f"Found {len(all_patterns)} httm:: patterns")
            
            # Group by category
            categories = {}
            for pattern in all_patterns:
                for cat in pattern.get('analysis', {}).get('categories', ['uncategorized']):
                    categories[cat] = categories.get(cat, 0) + 1
            
            click.echo("\nCategory distribution:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                click.echo(f"  {cat}: {count}")
            
            # Show high-confidence patterns
            high_conf = [p for p in all_patterns if p.get('confidence', 0) > 0.8]
            if high_conf:
                click.echo(f"\nHigh-confidence patterns ({len(high_conf)}):")
                for pattern in high_conf[:5]:  # Show top 5
                    content = pattern['content'][:100]
                    conf = pattern.get('confidence', 0)
                    click.echo(f"  • [{conf:.2f}] {content}")
    
    # This plugin could also generate httm:: patterns
    async def some_processing_method(self, data):
        """Example method that might generate httm:: patterns."""
        
        # Normal processing
        result = self._process_data(data)
        
        # But also capture intuitive insights
        if self._something_feels_off(result):
            # Generate an httm:: pattern that the middleware will catch
            insight = "httm:: { something feels off about this result - the pattern doesn't match what I'd expect from this type of data }"
            
            # Add it to the result where middleware can find it
            if isinstance(result, dict):
                result['_httm_insights'] = [insight]
            else:
                # Or emit as an event
                await self.emit_event("httm_insight_generated", {
                    "insight": insight,
                    "context": "data_processing",
                    "data_preview": str(data)[:100]
                })
        
        return result