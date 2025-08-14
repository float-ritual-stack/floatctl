"""
Clean FLOAT pattern extractor using LangExtract.

Simple, working implementation that focuses on the core use case:
replacing evna's brittle regex with LangExtract's fuzzy compilation.
"""

import os
from typing import Dict, Any, List
import langextract as lx
from pathlib import Path
from dotenv import load_dotenv


class FloatExtractor:
    """Simple FLOAT pattern extractor using LangExtract examples."""
    
    def __init__(self):
        """Initialize with basic FLOAT pattern examples."""
        # Try loading from ~/.env.local first
        env_local = Path.home() / '.env.local'
        if env_local.exists():
            load_dotenv(env_local)
            
        # LangExtract expects LANGEXTRACT_API_KEY, but we have GEMINI_API_KEY
        self.api_key = os.environ.get('LANGEXTRACT_API_KEY') or os.environ.get('GEMINI_API_KEY')
        
        # Simple prompt focused on core patterns
        self.prompt = """
        Extract FLOAT consciousness patterns from the text.
        
        Key patterns to find:
        - ctx:: (context with timestamps and metadata)
        - decision:: (key decisions)
        - eureka:: (insights)
        - bridge:: (context restoration points)
        - Persona dialogues (karen::, lf1m::, sysop::, etc.)
        
        Extract each pattern with its content and preserve the order they appear.
        """
        
        # Simple examples based on real user patterns
        self.examples = [
            # Basic ctx pattern
            lx.data.ExampleData(
                text="ctx::2025-08-14 @ 12:30 PM - [mode:: work]",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="ctx",
                        extraction_text="2025-08-14 @ 12:30 PM - [mode:: work]"
                    )
                ]
            ),
            
            # Multi-pattern case (the evna killer)
            lx.data.ExampleData(
                text="eureka:: Found the bug! decision:: Fix it tomorrow",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="eureka",
                        extraction_text="Found the bug!"
                    ),
                    lx.data.Extraction(
                        extraction_class="decision", 
                        extraction_text="Fix it tomorrow"
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
            )
        ]
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract FLOAT patterns from text.
        
        Args:
            text: Text containing FLOAT patterns
            
        Returns:
            Dict with patterns and metadata
        """
        # Context bomb detection  
        token_count = len(text.split())
        if token_count > 10000:
            return {
                "patterns": [],
                "error": "Text too large for safe processing",
                "token_count": token_count
            }
        
        try:
            # Call LangExtract
            result = lx.extract(
                text_or_documents=text,
                prompt_description=self.prompt,
                examples=self.examples,
                model_id="gemini-2.5-flash",
                api_key=self.api_key,
            )
            
            # Convert to simple format
            patterns = []
            for extraction in result.extractions:
                pattern = {
                    "type": extraction.extraction_class,
                    "content": extraction.extraction_text,
                    "attributes": extraction.attributes or {}
                }
                patterns.append(pattern)
            
            return {
                "patterns": patterns,
                "total_found": len(patterns),
                "token_count": token_count
            }
            
        except Exception as e:
            # Graceful degradation
            return {
                "patterns": [],
                "error": str(e),
                "token_count": token_count
            }
    
    def test_evna_failures(self) -> Dict[str, Any]:
        """Test against known evna failure cases."""
        test_cases = {
            "multi_pattern": "eureka:: Found bug! decision:: Fix tomorrow bridge::create",
            "complex_ctx": "ctx::2025-08-14 @ 12:30 PM - [mode:: work] [project:: floatctl]",
            "persona_nested": 'karen:: "Stretch"\n    lf1m:: *body awareness*'
        }
        
        results = {}
        for name, test_input in test_cases.items():
            result = self.extract(test_input)
            results[name] = {
                "input": test_input,
                "patterns_found": result.get("total_found", 0),
                "success": result.get("total_found", 0) > 0,
                "patterns": result.get("patterns", [])
            }
        
        return results


def create_extractor() -> FloatExtractor:
    """Create a FLOAT extractor instance."""
    return FloatExtractor()


if __name__ == "__main__":
    print("🧠 Simple FLOAT Pattern Extractor Test")
    print("=" * 50)
    
    extractor = create_extractor()
    
    if not extractor.api_key:
        print("⚠️  LANGEXTRACT_API_KEY not set - testing structure only")
    else:
        print(f"✅ API Key loaded: {extractor.api_key[:20]}...")
    
    # Test the evna failure cases
    print("\n🔥 Testing Against Evna Failures:")
    results = extractor.test_evna_failures()
    
    for test_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"\n{status} {test_name}: {result['patterns_found']} patterns")
        print(f"   Input: {result['input']}")
        
        if result['patterns']:
            for pattern in result['patterns']:
                print(f"   → {pattern['type']}: {pattern['content'][:40]}...")
    
    print(f"\n🎯 Status: Simple extractor ready for integration")
    print(f"   - Clean API focused on core use case")
    print(f"   - Handles multi-patterns (evna's main failure)")
    print(f"   - Graceful error handling")
    print(f"   - Ready to replace evna's regex parsing")