#!/usr/bin/env python3
"""
Test script to verify the evna MCP server integration with hybrid extractor.
This tests that parse_any_pattern now captures ALL patterns, not just first.
"""

import sys
from pathlib import Path

# Add src to path so we can import
sys.path.insert(0, str(Path(__file__).parent / "src"))

from floatctl.mcp_server import parse_any_pattern

def test_evna_killer():
    """Test the multi-pattern extraction that evna failed at."""
    print("🔥 THE EVNA KILLER TEST")
    print("=" * 50)
    
    test_input = "eureka:: Found the bug! decision:: Fix it tomorrow bridge:: create restoration point"
    print(f"Input: {test_input}")
    print()
    
    result = parse_any_pattern(test_input)
    
    print("Parse Results:")
    print(f"  Patterns found: {result.get('patterns_found', [])}")
    print(f"  Primary pattern: {result.get('primary_pattern', 'none')}")
    print(f"  Extraction method: {result.get('extraction_method', 'unknown')}")
    print()
    
    print("Pattern Contents:")
    for pattern in result.get('patterns_found', []):
        content_key = f"{pattern}_content"
        if content_key in result:
            print(f"  {pattern}: {result[content_key]}")
    
    # Verify all 3 patterns were found
    patterns = result.get('patterns_found', [])
    if len(patterns) >= 3:
        print(f"\n✅ SUCCESS: Found {len(patterns)} patterns (evna would only find 1)")
        return True
    else:
        print(f"\n❌ FAILURE: Only found {len(patterns)} patterns")
        return False

def test_complex_metadata():
    """Test extraction of nested metadata."""
    print("\n📊 COMPLEX METADATA TEST")
    print("=" * 50)
    
    test_input = "ctx::2025-08-14 @ 12:30 PM - [mode:: work] [project:: floatctl]"
    print(f"Input: {test_input}")
    print()
    
    result = parse_any_pattern(test_input)
    
    print("Metadata Extracted:")
    for key, value in result.items():
        if key not in ['patterns_found']:  # Skip the list for cleaner output
            print(f"  {key}: {value}")
    
    # Check if mode and project were extracted
    if result.get('mode') == 'work' and result.get('project') == 'floatctl':
        print("\n✅ SUCCESS: Nested metadata extracted correctly")
        return True
    else:
        print("\n❌ FAILURE: Missing nested metadata")
        return False

def test_persona_patterns():
    """Test persona dialogue extraction."""
    print("\n🎭 PERSONA PATTERNS TEST")
    print("=" * 50)
    
    test_input = 'karen:: "Honey, stretch that back" lf1m:: *body awareness*'
    print(f"Input: {test_input}")
    print()
    
    result = parse_any_pattern(test_input)
    
    print("Personas Found:")
    personas = result.get('persona_speakers', '').split(',') if result.get('persona_speakers') else []
    for persona in personas:
        content_key = f"{persona}_content"
        if content_key in result:
            print(f"  {persona}: {result[content_key]}")
    
    if len(personas) >= 2:
        print(f"\n✅ SUCCESS: Found {len(personas)} personas")
        return True
    else:
        print(f"\n❌ FAILURE: Only found {len(personas)} personas")
        return False

def test_mixed_patterns():
    """Test mixed pattern types in one line."""
    print("\n🌈 MIXED PATTERNS TEST")
    print("=" * 50)
    
    test_input = "ctx::morning [mode::focus] eureka::solved it! karen::good job"
    print(f"Input: {test_input}")
    print()
    
    result = parse_any_pattern(test_input)
    
    print("All Patterns Found:")
    for pattern in result.get('patterns_found', []):
        content_key = f"{pattern}_content"
        if content_key in result:
            print(f"  {pattern}: {result[content_key]}")
    
    patterns = result.get('patterns_found', [])
    if len(patterns) >= 3:
        print(f"\n✅ SUCCESS: Found {len(patterns)} different pattern types")
        return True
    else:
        print(f"\n❌ FAILURE: Only found {len(patterns)} patterns")
        return False

def main():
    """Run all tests and report results."""
    print("🧠 EVNA MCP SERVER INTEGRATION TEST")
    print("Testing parse_any_pattern with hybrid extractor")
    print("=" * 50)
    
    tests = [
        test_evna_killer,
        test_complex_metadata,
        test_persona_patterns,
        test_mixed_patterns
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("📈 TEST SUMMARY")
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! The evna fix is working!")
        print("Multi-pattern extraction is now operational.")
    else:
        print(f"\n⚠️  {failed} tests failed. Check the implementation.")

if __name__ == "__main__":
    main()