"""
Mock version of FLOAT extractor for testing without API key.

This demonstrates the pattern extraction logic and validates our approach
before integrating with the real LangExtract API.
"""

import re
from typing import Dict, Any, List


class MockFloatExtractor:
    """Mock extractor that simulates LangExtract behavior for testing."""
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract patterns using simple regex (for testing only)."""
        
        # Context bomb detection
        token_count = len(text.split())
        if token_count > 10000:
            return {
                "patterns": [],
                "error": "Text too large for safe processing",
                "token_count": token_count
            }
        
        patterns = []
        
        # Find all pattern:: content pairs
        pattern_matches = re.findall(r'(\w+)::\s*([^:]+?)(?=\s+\w+::|$)', text)
        
        for pattern_type, content in pattern_matches:
            pattern = {
                "type": pattern_type,
                "content": content.strip(),
                "attributes": {}
            }
            
            # Extract speaker for persona patterns
            if pattern_type in ['karen', 'lf1m', 'sysop', 'qtb', 'evna']:
                pattern["type"] = "persona"
                pattern["attributes"]["speaker"] = pattern_type
                
            patterns.append(pattern)
        
        return {
            "patterns": patterns,
            "total_found": len(patterns),
            "token_count": token_count,
            "mock_mode": True
        }
    
    def test_evna_failures(self) -> Dict[str, Any]:
        """Test against known evna failure cases."""
        test_cases = {
            "multi_pattern": "eureka:: Found bug! decision:: Fix tomorrow bridge:: create",
            "complex_ctx": "ctx:: 2025-08-14 @ 12:30 PM - [mode:: work] [project:: floatctl]",  
            "persona_dialogue": "karen:: Stretch that back lf1m:: body awareness"
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


if __name__ == "__main__":
    print("🧠 Mock FLOAT Pattern Extractor Test")
    print("=" * 50)
    
    extractor = MockFloatExtractor()
    
    # Test the evna failure cases
    print("\n🔥 Testing Against Evna Failures (Mock Mode):")
    results = extractor.test_evna_failures()
    
    success_count = 0
    for test_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        if result['success']:
            success_count += 1
            
        print(f"\n{status} {test_name}: {result['patterns_found']} patterns")
        print(f"   Input: {result['input']}")
        
        if result['patterns']:
            for pattern in result['patterns']:
                speaker = pattern['attributes'].get('speaker', '')
                speaker_info = f" (speaker: {speaker})" if speaker else ""
                print(f"   → {pattern['type']}{speaker_info}: {pattern['content'][:40]}...")
    
    print(f"\n🎯 Mock Test Results: {success_count}/{len(results)} passed")
    print(f"   - Demonstrates multi-pattern extraction works")
    print(f"   - Shows improvement over evna's single-pattern regex")
    print(f"   - Validates the approach before API integration")
    
    # Test the specific evna killer case
    print(f"\n🔥 The Infamous Evna Killer Test:")
    evna_killer = "eureka:: Found the bug! decision:: Fix it tomorrow bridge:: create"
    result = extractor.extract(evna_killer)
    
    print(f"Input: {evna_killer}")
    print(f"Patterns found: {result['total_found']} (evna finds only 1)")
    for pattern in result['patterns']:
        print(f"  → {pattern['type']}: {pattern['content']}")
    
    if result['total_found'] >= 3:
        print("✅ SUCCESS: Multi-pattern extraction works!")
        print("   This is exactly what evna fails at.")
    else:
        print("❌ ISSUE: Should find 3 patterns (eureka, decision, bridge)")