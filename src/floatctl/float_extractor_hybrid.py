"""
Hybrid FLOAT pattern extractor with automatic fallback.

Uses LangExtract when API key is available, falls back to regex-based
mock extractor when not. This ensures the system always works while
providing the best extraction quality when possible.
"""

import os
import re
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

try:
    import langextract as lx
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False


class HybridFloatExtractor:
    """FLOAT pattern extractor with automatic API/mock fallback."""
    
    def __init__(self):
        """Initialize with API key check and fallback strategy."""
        # Try loading from ~/.env.local first
        env_local = Path.home() / '.env.local'
        if env_local.exists():
            load_dotenv(env_local)
            
        # Check for API key
        self.api_key = os.environ.get('LANGEXTRACT_API_KEY') or os.environ.get('GEMINI_API_KEY')
        
        # Validate API key (Gemini keys should be 39 chars)
        self.api_available = False
        if LANGEXTRACT_AVAILABLE and self.api_key and len(self.api_key) >= 39:
            # Test the API key with a simple request
            try:
                import langextract as lx
                # Quick validation test
                test_result = lx.extract(
                    text_or_documents="test",
                    prompt_description="test",
                    examples=[lx.data.ExampleData(
                        text="test",
                        extractions=[lx.data.Extraction(
                            extraction_class="test",
                            extraction_text="test"
                        )]
                    )],
                    model_id="gemini-2.5-flash",
                    api_key=self.api_key,
                )
                self.api_available = True
                print("✅ LangExtract API available and working")
            except Exception as e:
                print(f"⚠️  LangExtract API check failed: {str(e)[:50]}...")
                self.api_available = False
        else:
            if not LANGEXTRACT_AVAILABLE:
                print("⚠️  LangExtract not installed, using mock extractor")
            elif not self.api_key:
                print("⚠️  No API key found, using mock extractor")
            elif len(self.api_key) < 39:
                print(f"⚠️  API key appears invalid (length: {len(self.api_key)}), using mock extractor")
                
        # Set up LangExtract if available
        if self.api_available:
            self._setup_langextract()
        else:
            print("📝 Using regex-based mock extractor (still better than evna!)")
    
    def _setup_langextract(self):
        """Set up LangExtract prompt and examples."""
        import langextract as lx
        
        self.prompt = """
        Extract FLOAT consciousness patterns from the text.
        
        Key patterns to find:
        - ctx:: (context with timestamps and metadata)
        - decision:: (key decisions)
        - eureka:: (insights)
        - bridge:: (context restoration points)
        - highlight:: (important moments)
        - Persona dialogues (karen::, lf1m::, sysop::, evna::, qtb::)
        - Mode indicators ([mode:: state])
        - Project markers ([project:: name])
        
        Extract each pattern with its content and preserve the order they appear.
        Extract ALL patterns, not just the first one.
        """
        
        self.examples = [
            # Multi-pattern case (the evna killer)
            lx.data.ExampleData(
                text="eureka:: Found the bug! decision:: Fix it tomorrow bridge:: create",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="eureka",
                        extraction_text="Found the bug!"
                    ),
                    lx.data.Extraction(
                        extraction_class="decision", 
                        extraction_text="Fix it tomorrow"
                    ),
                    lx.data.Extraction(
                        extraction_class="bridge",
                        extraction_text="create"
                    )
                ]
            ),
            # Complex ctx pattern
            lx.data.ExampleData(
                text="ctx::2025-08-14 @ 12:30 PM - [mode:: work] [project:: floatctl]",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="ctx",
                        extraction_text="2025-08-14 @ 12:30 PM - [mode:: work] [project:: floatctl]",
                        attributes={
                            "timestamp": "2025-08-14 @ 12:30 PM",
                            "mode": "work",
                            "project": "floatctl"
                        }
                    )
                ]
            ),
            # Persona dialogue
            lx.data.ExampleData(
                text='karen:: "Honey, stretch that back"',
                extractions=[
                    lx.data.Extraction(
                        extraction_class="persona",
                        extraction_text="Honey, stretch that back",
                        attributes={"speaker": "karen"}
                    )
                ]
            ),
            # Nested metadata
            lx.data.ExampleData(
                text="highlight:: Key insight [status:: active]",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="highlight",
                        extraction_text="Key insight [status:: active]",
                        attributes={"status": "active"}
                    )
                ]
            )
        ]
    
    def _extract_with_langextract(self, text: str) -> Dict[str, Any]:
        """Extract using LangExtract API."""
        import langextract as lx
        
        try:
            result = lx.extract(
                text_or_documents=text,
                prompt_description=self.prompt,
                examples=self.examples,
                model_id="gemini-2.5-flash",
                api_key=self.api_key,
            )
            
            # Convert to standard format
            patterns = []
            for extraction in result.extractions:
                pattern = {
                    "type": extraction.extraction_class,
                    "content": extraction.extraction_text,
                    "attributes": extraction.attributes or {}
                }
                if extraction.char_interval:
                    pattern["position"] = {
                        "start": extraction.char_interval.start_pos,
                        "end": extraction.char_interval.end_pos
                    }
                patterns.append(pattern)
            
            return {
                "patterns": patterns,
                "total_found": len(patterns),
                "method": "langextract",
                "token_count": len(text.split())
            }
            
        except Exception as e:
            # Fall back to mock on API errors
            print(f"⚠️  LangExtract failed, using mock: {str(e)[:50]}...")
            return self._extract_with_mock(text)
    
    def _extract_with_mock(self, text: str) -> Dict[str, Any]:
        """Extract using regex-based mock (better than evna!)."""
        
        patterns = []
        
        # Pattern 1: Standard :: patterns with content
        # This regex captures multiple patterns per line (evna's weakness)
        standard_matches = re.finditer(
            r'(\w+)::\s*([^:\n]+?)(?=\s+\w+::|$|\n)',
            text,
            re.MULTILINE
        )
        
        for match in standard_matches:
            pattern_type = match.group(1)
            content = match.group(2).strip()
            
            pattern = {
                "type": pattern_type,
                "content": content,
                "attributes": {},
                "position": {
                    "start": match.start(),
                    "end": match.end()
                }
            }
            
            # Check if it's a persona
            if pattern_type.lower() in ['karen', 'lf1m', 'sysop', 'qtb', 'evna']:
                pattern["type"] = "persona"
                pattern["attributes"]["speaker"] = pattern_type.lower()
            
            # Extract nested metadata like [mode:: work]
            metadata_matches = re.findall(r'\[(\w+)::\s*([^\]]+)\]', content)
            for meta_key, meta_val in metadata_matches:
                pattern["attributes"][meta_key] = meta_val
            
            patterns.append(pattern)
        
        # Pattern 2: Inline metadata [key:: value]
        inline_matches = re.finditer(
            r'\[(\w+)::\s*([^\]]+)\]',
            text
        )
        
        for match in inline_matches:
            # Check if this isn't already captured as part of another pattern
            already_captured = any(
                match.start() >= p["position"]["start"] and 
                match.end() <= p["position"]["end"]
                for p in patterns
            )
            
            if not already_captured:
                patterns.append({
                    "type": "metadata",
                    "content": f"{match.group(1)}:: {match.group(2)}",
                    "attributes": {
                        match.group(1): match.group(2)
                    },
                    "position": {
                        "start": match.start(),
                        "end": match.end()
                    }
                })
        
        # Sort by position to maintain order
        patterns.sort(key=lambda p: p["position"]["start"])
        
        return {
            "patterns": patterns,
            "total_found": len(patterns),
            "method": "mock",
            "token_count": len(text.split())
        }
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract FLOAT patterns from text.
        
        Uses LangExtract if available, falls back to mock otherwise.
        Always returns results, never fails completely.
        """
        # Context bomb detection
        token_count = len(text.split())
        if token_count > 10000:
            return {
                "patterns": [],
                "error": "Text too large for safe processing",
                "token_count": token_count,
                "method": "none"
            }
        
        # Use appropriate extraction method
        if self.api_available:
            return self._extract_with_langextract(text)
        else:
            return self._extract_with_mock(text)
    
    def test_evna_failures(self) -> Dict[str, Any]:
        """Test against known evna failure cases."""
        test_cases = {
            "multi_pattern": "eureka:: Found bug! decision:: Fix tomorrow bridge::create",
            "complex_ctx": "ctx::2025-08-14 @ 12:30 PM - [mode:: work] [project:: floatctl]",
            "persona_nested": 'karen:: "Stretch that back"\n    lf1m:: *body awareness*',
            "inline_metadata": "Working on [project:: airbender] with [status:: active]",
            "mixed_patterns": "ctx::morning [mode::focus] eureka::solved it! karen::good job"
        }
        
        results = {}
        for name, test_input in test_cases.items():
            result = self.extract(test_input)
            
            # Count expected patterns for validation
            expected = len(re.findall(r'\w+::', test_input))
            
            results[name] = {
                "input": test_input,
                "patterns_found": result.get("total_found", 0),
                "expected": expected,
                "success": result.get("total_found", 0) >= expected,
                "method": result.get("method", "unknown"),
                "patterns": result.get("patterns", [])
            }
        
        return results


def create_extractor() -> HybridFloatExtractor:
    """Create a hybrid FLOAT extractor instance."""
    return HybridFloatExtractor()


if __name__ == "__main__":
    print("🧠 Hybrid FLOAT Pattern Extractor")
    print("==" * 25)
    
    extractor = create_extractor()
    
    print(f"\n📊 Extractor Status:")
    print(f"   LangExtract available: {LANGEXTRACT_AVAILABLE}")
    print(f"   API configured: {extractor.api_available}")
    print(f"   Using method: {'LangExtract' if extractor.api_available else 'Mock (Regex)'}")
    
    # Test the evna failure cases
    print("\n🔥 Testing Against Evna Failures:")
    print("=" * 50)
    results = extractor.test_evna_failures()
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r['success'])
    
    for test_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"\n{status} {test_name}: {result['patterns_found']}/{result['expected']} patterns (via {result['method']})")
        print(f"   Input: {result['input'][:60]}...")
        
        if result['patterns']:
            for pattern in result['patterns'][:3]:  # Show first 3
                attrs = f" {pattern['attributes']}" if pattern['attributes'] else ""
                print(f"   → {pattern['type']}: {pattern['content'][:30]}...{attrs}")
    
    # Summary
    print(f"\n📈 Test Summary:")
    print(f"   Tests passed: {passed_tests}/{total_tests}")
    print(f"   Extraction method: {results[list(results.keys())[0]]['method']}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Ready to replace evna's broken regex.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Check the patterns.")
    
    # The evna killer test
    print("\n" + "=" * 50)
    print("🔥 THE EVNA KILLER TEST (multi-pattern extraction):")
    evna_killer = "eureka:: Found the bug! decision:: Fix it tomorrow bridge:: create restoration point"
    result = extractor.extract(evna_killer)
    
    print(f"Input: {evna_killer}")
    print(f"Patterns found: {result['total_found']} (evna finds only 1)")
    print(f"Method used: {result['method']}")
    
    for pattern in result['patterns']:
        print(f"  → {pattern['type']}: {pattern['content']}")
    
    if result['total_found'] >= 3:
        print("\n✅ SUCCESS: Multi-pattern extraction works!")
        print("   This hybrid extractor solves evna's core failure.")
    
    print("\n" + "==" * 25)
    print("📝 Hybrid Extractor Features:")
    print("   • Automatic API/mock fallback")
    print("   • Always returns results (never fails)")
    print("   • Mock is still better than evna's regex")
    print("   • Ready for immediate integration")
    print("   • Handles invalid/missing API keys gracefully")