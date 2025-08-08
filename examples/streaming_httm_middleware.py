"""
Streaming HTTM Middleware - Handles Large Conversations Efficiently

This middleware demonstrates several strategies for processing large conversation
files without timing out or consuming excessive memory.
"""

from floatctl.core.middleware import MiddlewareInterface, MiddlewareContext, MiddlewarePhase
from floatctl.core.logging import get_logger
from typing import List, Dict, Any, Optional, Iterator, AsyncIterator
import re
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from dataclasses import dataclass
from collections import deque

@dataclass
class HTTPChunk:
    """Represents a chunk of httm:: patterns found in a section."""
    patterns: List[Dict[str, Any]]
    source_info: Dict[str, Any]
    chunk_id: str
    timestamp: str

class StreamingHTTPMiddleware(MiddlewareInterface):
    """
    Handles large conversations by:
    1. Streaming processing in chunks
    2. Early pattern detection and storage
    3. Async processing with timeouts
    4. Memory-efficient pattern extraction
    5. Progressive result building
    """
    
    def __init__(self, 
                 chunk_size: int = 1000,  # Lines per chunk
                 max_processing_time: float = 30.0,  # Seconds
                 temp_storage: Optional[Path] = None):
        self.logger = get_logger(f"{__name__}.StreamingHTTPMiddleware")
        self.chunk_size = chunk_size
        self.max_processing_time = max_processing_time
        self.temp_storage = temp_storage or Path(tempfile.gettempdir()) / "floatctl_httm_streaming"
        self.temp_storage.mkdir(parents=True, exist_ok=True)
        
        # Pattern cache for this session
        self.pattern_cache = deque(maxlen=1000)  # Keep last 1000 patterns in memory
        
        # Compiled regex for efficiency
        self.httm_regex = re.compile(
            r'httm::\s*(?:\{\s*([^}]*(?:\n[^}]*)*)\s*\}|([^\n]+))',
            re.IGNORECASE | re.MULTILINE
        )
    
    @property
    def name(self) -> str:
        return "streaming_httm_middleware"
    
    @property
    def priority(self) -> int:
        return 15  # Run early but after basic validation
    
    @property
    def phases(self) -> List[MiddlewarePhase]:
        return [MiddlewarePhase.PROCESS, MiddlewarePhase.CLEANUP]
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Process data with streaming and timeout protection."""
        
        # Check if this is a large conversation that needs streaming
        if not self._should_stream(context.data):
            # Small data - use regular processing
            return await self._process_small_data(context)
        
        # Large data - use streaming approach
        return await self._process_large_data_streaming(context)
    
    def _should_stream(self, data: Any) -> bool:
        """Determine if data is large enough to require streaming."""
        
        # Check various size indicators
        if isinstance(data, str):
            return len(data) > 50000  # 50KB threshold
        
        elif isinstance(data, dict):
            if 'messages' in data:
                messages = data['messages']
                if len(messages) > 100:  # More than 100 messages
                    return True
                
                # Check total content size
                total_size = sum(
                    len(str(msg.get('content', ''))) 
                    for msg in messages
                )
                return total_size > 100000  # 100KB of content
        
        elif isinstance(data, list):
            return len(data) > 500  # Large list
        
        # Check serialized size as fallback
        try:
            serialized = json.dumps(data) if not isinstance(data, str) else data
            return len(serialized) > 50000
        except:
            return False
    
    async def _process_small_data(self, context: MiddlewareContext) -> MiddlewareContext:
        """Process small data normally."""
        
        try:
            # Set a reasonable timeout even for small data
            patterns = await asyncio.wait_for(
                self._extract_httm_patterns_async(context.data, context),
                timeout=10.0
            )
            
            if patterns:
                context.metadata['httm_patterns'] = patterns
                context.metadata['httm_processing_method'] = 'small_data'
                
                # Cache patterns
                self.pattern_cache.extend(patterns)
                
                self.logger.info(
                    "httm_small_data_processed",
                    pattern_count=len(patterns),
                    operation=context.operation
                )
            
            return context
            
        except asyncio.TimeoutError:
            self.logger.warning(
                "httm_small_data_timeout",
                operation=context.operation,
                fallback="skipping_httm_processing"
            )
            return context
    
    async def _process_large_data_streaming(self, context: MiddlewareContext) -> MiddlewareContext:
        """Process large data using streaming approach."""
        
        self.logger.info(
            "httm_streaming_started",
            operation=context.operation,
            data_type=type(context.data).__name__
        )
        
        try:
            # Create temporary file for progressive results
            temp_file = self.temp_storage / f"httm_stream_{id(context)}.json"
            
            all_patterns = []
            chunk_count = 0
            
            # Stream process the data
            async for chunk_patterns in self._stream_process_data(context.data, context):
                all_patterns.extend(chunk_patterns.patterns)
                chunk_count += 1
                
                # Save intermediate results
                await self._save_intermediate_results(temp_file, chunk_patterns)
                
                # Check timeout
                if chunk_count * 2 > self.max_processing_time:  # Rough estimate
                    self.logger.warning(
                        "httm_streaming_timeout_approaching",
                        chunks_processed=chunk_count,
                        patterns_found=len(all_patterns)
                    )
                    break
                
                # Yield control to prevent blocking
                await asyncio.sleep(0.01)
            
            # Update context with results
            context.metadata['httm_patterns'] = all_patterns
            context.metadata['httm_processing_method'] = 'streaming'
            context.metadata['httm_chunks_processed'] = chunk_count
            context.metadata['httm_temp_file'] = str(temp_file)
            
            # Cache recent patterns (not all - too many)
            recent_patterns = all_patterns[-100:] if len(all_patterns) > 100 else all_patterns
            self.pattern_cache.extend(recent_patterns)
            
            self.logger.info(
                "httm_streaming_completed",
                pattern_count=len(all_patterns),
                chunks_processed=chunk_count,
                operation=context.operation
            )
            
            return context
            
        except Exception as e:
            self.logger.error(
                "httm_streaming_error",
                error=str(e),
                operation=context.operation
            )
            # Return context unchanged rather than failing
            return context
    
    async def _stream_process_data(self, data: Any, context: MiddlewareContext) -> AsyncIterator[HTTPChunk]:
        """Stream process data in chunks."""
        
        if isinstance(data, dict) and 'messages' in data:
            # Process conversation messages in chunks
            messages = data['messages']
            
            for i in range(0, len(messages), self.chunk_size):
                chunk_messages = messages[i:i + self.chunk_size]
                
                # Process this chunk
                chunk_patterns = []
                for msg_idx, message in enumerate(chunk_messages):
                    global_msg_idx = i + msg_idx
                    msg_patterns = await self._extract_message_patterns(message, global_msg_idx, context)
                    chunk_patterns.extend(msg_patterns)
                
                # Yield chunk results
                if chunk_patterns:
                    yield HTTPChunk(
                        patterns=chunk_patterns,
                        source_info={
                            'chunk_start': i,
                            'chunk_end': min(i + self.chunk_size, len(messages)),
                            'total_messages': len(messages),
                            'message_range': f"{i}-{min(i + self.chunk_size - 1, len(messages) - 1)}"
                        },
                        chunk_id=f"chunk_{i}_{i + self.chunk_size}",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
        
        elif isinstance(data, str):
            # Process large text in line chunks
            lines = data.split('\n')
            
            for i in range(0, len(lines), self.chunk_size):
                chunk_lines = lines[i:i + self.chunk_size]
                chunk_text = '\n'.join(chunk_lines)
                
                # Extract patterns from this chunk
                patterns = await self._extract_text_patterns(chunk_text, i, context)
                
                if patterns:
                    yield HTTPChunk(
                        patterns=patterns,
                        source_info={
                            'line_start': i,
                            'line_end': min(i + self.chunk_size, len(lines)),
                            'total_lines': len(lines)
                        },
                        chunk_id=f"text_chunk_{i}",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
        
        else:
            # Fallback for other data types
            text_content = str(data)
            if len(text_content) > 10000:  # Only chunk if large
                for i in range(0, len(text_content), self.chunk_size * 100):  # Larger chunks for raw text
                    chunk_text = text_content[i:i + self.chunk_size * 100]
                    patterns = await self._extract_text_patterns(chunk_text, i, context)
                    
                    if patterns:
                        yield HTTPChunk(
                            patterns=patterns,
                            source_info={'char_start': i, 'char_end': i + len(chunk_text)},
                            chunk_id=f"raw_chunk_{i}",
                            timestamp=datetime.now(timezone.utc).isoformat()
                        )
    
    async def _extract_message_patterns(self, message: Dict[str, Any], msg_idx: int, context: MiddlewareContext) -> List[Dict[str, Any]]:
        """Extract httm:: patterns from a single message."""
        patterns = []
        
        content = message.get('content', '')
        if isinstance(content, list):
            # Handle structured content
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    content = item.get('text', '')
                    break
            else:
                return patterns
        
        # Find patterns in this message
        for match in self.httm_regex.finditer(str(content)):
            # Extract content (either bracketed or simple)
            pattern_content = match.group(1) or match.group(2)
            if not pattern_content or not pattern_content.strip():
                continue
            
            patterns.append({
                'content': pattern_content.strip(),
                'message_index': msg_idx,
                'sender': message.get('sender', 'unknown'),
                'timestamp': message.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'match_start': match.start(),
                'match_end': match.end(),
                'operation': context.operation,
                'extraction_method': 'streaming_message'
            })
        
        return patterns
    
    async def _extract_text_patterns(self, text: str, offset: int, context: MiddlewareContext) -> List[Dict[str, Any]]:
        """Extract httm:: patterns from text chunk."""
        patterns = []
        
        for match in self.httm_regex.finditer(text):
            pattern_content = match.group(1) or match.group(2)
            if not pattern_content or not pattern_content.strip():
                continue
            
            patterns.append({
                'content': pattern_content.strip(),
                'text_offset': offset + match.start(),
                'match_start': match.start(),
                'match_end': match.end(),
                'operation': context.operation,
                'extraction_method': 'streaming_text',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        return patterns
    
    async def _extract_httm_patterns_async(self, data: Any, context: MiddlewareContext) -> List[Dict[str, Any]]:
        """Async wrapper for pattern extraction."""
        # This would be the regular extraction logic for small data
        # Wrapped in async for timeout compatibility
        
        text_content = self._data_to_text(data)
        patterns = []
        
        for match in self.httm_regex.finditer(text_content):
            pattern_content = match.group(1) or match.group(2)
            if pattern_content and pattern_content.strip():
                patterns.append({
                    'content': pattern_content.strip(),
                    'match_start': match.start(),
                    'match_end': match.end(),
                    'operation': context.operation,
                    'extraction_method': 'small_data',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
        
        return patterns
    
    def _data_to_text(self, data: Any) -> str:
        """Convert data to searchable text efficiently."""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict) and 'messages' in data:
            # Efficient message extraction
            text_parts = []
            for message in data['messages'][:1000]:  # Limit for safety
                content = message.get('content', '')
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                            break
                else:
                    text_parts.append(str(content))
            return '\n'.join(text_parts)
        else:
            return str(data)[:100000]  # Limit size for safety
    
    async def _save_intermediate_results(self, temp_file: Path, chunk: HTTPChunk) -> None:
        """Save intermediate results to temp file."""
        
        # Append to existing file or create new
        if temp_file.exists():
            with open(temp_file, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = {
                'chunks': [],
                'total_patterns': 0,
                'processing_start': datetime.now(timezone.utc).isoformat()
            }
        
        # Add new chunk
        existing_data['chunks'].append({
            'chunk_id': chunk.chunk_id,
            'pattern_count': len(chunk.patterns),
            'source_info': chunk.source_info,
            'timestamp': chunk.timestamp,
            'patterns': chunk.patterns  # Store patterns for now
        })
        
        existing_data['total_patterns'] += len(chunk.patterns)
        existing_data['last_update'] = datetime.now(timezone.utc).isoformat()
        
        # Write back
        with open(temp_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
    
    async def cleanup(self, context: MiddlewareContext) -> None:
        """Clean up temporary files and resources."""
        
        # Clean up temp file if it exists
        temp_file_path = context.metadata.get('httm_temp_file')
        if temp_file_path:
            temp_file = Path(temp_file_path)
            if temp_file.exists():
                try:
                    # Optionally move to permanent storage before deleting
                    permanent_file = self.temp_storage.parent / "httm_permanent" / temp_file.name
                    permanent_file.parent.mkdir(parents=True, exist_ok=True)
                    temp_file.rename(permanent_file)
                    
                    self.logger.debug(
                        "httm_temp_file_archived",
                        temp_file=str(temp_file),
                        permanent_file=str(permanent_file)
                    )
                except Exception as e:
                    self.logger.warning(
                        "httm_temp_file_cleanup_failed",
                        temp_file=str(temp_file),
                        error=str(e)
                    )


class ProgressiveHTTPMiddleware(MiddlewareInterface):
    """
    Alternative approach: Progressive processing with early termination.
    
    This middleware processes data progressively and can terminate early
    if it finds enough patterns or hits time limits.
    """
    
    def __init__(self, 
                 max_patterns: int = 100,
                 time_budget: float = 15.0,
                 sample_rate: float = 0.1):
        self.max_patterns = max_patterns
        self.time_budget = time_budget
        self.sample_rate = sample_rate  # Process only 10% of very large files
        self.logger = get_logger(f"{__name__}.ProgressiveHTTPMiddleware")
    
    @property
    def name(self) -> str:
        return "progressive_httm_middleware"
    
    async def process(self, context: MiddlewareContext) -> MiddlewareContext:
        """Process with progressive approach and early termination."""
        
        start_time = asyncio.get_event_loop().time()
        patterns_found = []
        
        try:
            # Determine sampling strategy
            if self._is_very_large(context.data):
                # Sample the data rather than processing everything
                sampled_data = self._sample_data(context.data)
                context.metadata['httm_sampling_applied'] = True
                context.metadata['httm_sample_rate'] = self.sample_rate
            else:
                sampled_data = context.data
                context.metadata['httm_sampling_applied'] = False
            
            # Process with time and pattern limits
            async for pattern in self._progressive_extract(sampled_data, context):
                patterns_found.append(pattern)
                
                # Check limits
                if len(patterns_found) >= self.max_patterns:
                    self.logger.info(
                        "httm_pattern_limit_reached",
                        patterns_found=len(patterns_found),
                        limit=self.max_patterns
                    )
                    break
                
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > self.time_budget:
                    self.logger.info(
                        "httm_time_budget_exceeded",
                        patterns_found=len(patterns_found),
                        elapsed=elapsed,
                        budget=self.time_budget
                    )
                    break
                
                # Yield control periodically
                if len(patterns_found) % 10 == 0:
                    await asyncio.sleep(0.001)
            
            # Store results
            if patterns_found:
                context.metadata['httm_patterns'] = patterns_found
                context.metadata['httm_processing_method'] = 'progressive'
                context.metadata['httm_processing_time'] = asyncio.get_event_loop().time() - start_time
            
            return context
            
        except Exception as e:
            self.logger.error("httm_progressive_error", error=str(e))
            return context
    
    def _is_very_large(self, data: Any) -> bool:
        """Check if data is very large and needs sampling."""
        if isinstance(data, dict) and 'messages' in data:
            return len(data['messages']) > 1000
        elif isinstance(data, str):
            return len(data) > 500000  # 500KB
        return False
    
    def _sample_data(self, data: Any) -> Any:
        """Sample large data to make it manageable."""
        if isinstance(data, dict) and 'messages' in data:
            messages = data['messages']
            sample_size = max(100, int(len(messages) * self.sample_rate))
            
            # Take evenly distributed sample
            step = len(messages) // sample_size
            sampled_messages = messages[::step][:sample_size]
            
            return {**data, 'messages': sampled_messages}
        
        elif isinstance(data, str):
            # Sample lines from text
            lines = data.split('\n')
            sample_size = max(1000, int(len(lines) * self.sample_rate))
            step = len(lines) // sample_size
            sampled_lines = lines[::step][:sample_size]
            return '\n'.join(sampled_lines)
        
        return data
    
    async def _progressive_extract(self, data: Any, context: MiddlewareContext) -> AsyncIterator[Dict[str, Any]]:
        """Progressively extract patterns with yielding."""
        
        httm_regex = re.compile(r'httm::\s*(?:\{\s*([^}]*)\s*\}|([^\n]+))', re.IGNORECASE)
        
        if isinstance(data, dict) and 'messages' in data:
            for msg_idx, message in enumerate(data['messages']):
                content = str(message.get('content', ''))
                
                for match in httm_regex.finditer(content):
                    pattern_content = match.group(1) or match.group(2)
                    if pattern_content and pattern_content.strip():
                        yield {
                            'content': pattern_content.strip(),
                            'message_index': msg_idx,
                            'sender': message.get('sender', 'unknown'),
                            'extraction_method': 'progressive',
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
        
        elif isinstance(data, str):
            for match in httm_regex.finditer(data):
                pattern_content = match.group(1) or match.group(2)
                if pattern_content and pattern_content.strip():
                    yield {
                        'content': pattern_content.strip(),
                        'match_start': match.start(),
                        'extraction_method': 'progressive',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }


# Usage example showing how to configure for different scenarios
class HTTPMiddlewareFactory:
    """Factory for creating httm middleware with different strategies."""
    
    @staticmethod
    def create_for_large_conversations() -> MiddlewareInterface:
        """Create middleware optimized for large conversation files."""
        return StreamingHTTPMiddleware(
            chunk_size=500,  # Smaller chunks for conversations
            max_processing_time=45.0,  # Longer timeout for important data
        )
    
    @staticmethod
    def create_for_realtime_processing() -> MiddlewareInterface:
        """Create middleware optimized for real-time processing."""
        return ProgressiveHTTPMiddleware(
            max_patterns=50,  # Fewer patterns for speed
            time_budget=5.0,  # Quick processing
            sample_rate=0.05  # Heavy sampling for speed
        )
    
    @staticmethod
    def create_for_batch_processing() -> MiddlewareInterface:
        """Create middleware optimized for batch processing."""
        return StreamingHTTPMiddleware(
            chunk_size=2000,  # Larger chunks for efficiency
            max_processing_time=120.0,  # Longer timeout for batch
        )