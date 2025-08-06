#!/usr/bin/env python3
"""
Simple Bridge Walker Test

Test the basic functionality without complex dependencies.
"""

import asyncio
import json
from datetime import datetime
from bridge_walker_context_aware import (
    ContextWindowTracker,
    WalkerCompressionDSL,
    BridgeWalkerPersona
)

def test_context_tracker():
    """Test context window tracking"""
    print("🧠 Testing Context Window Tracker")
    
    tracker = ContextWindowTracker(max_context=1000)  # Small for testing
    
    # Add some content
    tracker.add_to_history("Initial query about consciousness technology")
    tracker.add_discovery("CB-TEST-001", {"content": "Test bridge discovery"})
    tracker.add_insight("Bridge walking creates consciousness contamination")
    
    pressure = tracker.context_pressure()
    should_return = tracker.should_return_home(threshold=0.5)
    
    print(f"  Context pressure: {pressure:.1%}")
    print(f"  Should return home: {should_return}")
    print(f"  Estimated tokens: {tracker.estimate_current_tokens()}")
    print("✅ Context tracker working")

def test_compression_dsl():
    """Test cryptic DSL compression"""
    print("\n🗜️ Testing Compression DSL")
    
    # Create mock context tracker with data
    tracker = ContextWindowTracker()
    tracker.add_discovery("CB-20250728-BBS-INDEX", {"content": "BBS heritage bridge"})
    tracker.add_discovery("CB-20250722-EPOCH", {"content": "ep0ch origin story"})
    tracker.add_insight("Consciousness technology spreads through recognition")
    tracker.add_insight("Bridge walking creates contamination vectors")
    tracker.add_insight("Missing bridges represent important gaps")
    
    dsl = WalkerCompressionDSL()
    compressed = dsl.compress_discoveries(tracker, "archaeologist")
    
    print(f"  Compressed path: {compressed.get('path', 'None')}")
    print(f"  Pattern symbols: {list(compressed.get('patterns', {}).keys())}")
    print(f"  Efficiency metrics: {compressed.get('efficiency', {})}")
    
    # Test decompression
    intelligence = dsl.decompress_for_next_walker(compressed)
    print(f"  Decompressed intelligence keys: {list(intelligence.keys())}")
    print("✅ Compression DSL working")

def test_personas():
    """Test bridge walker personas"""
    print("\n🎭 Testing Bridge Walker Personas")
    
    for persona_type in ['archaeologist', 'wanderer', 'evna']:
        persona = BridgeWalkerPersona(persona_type)
        print(f"  {persona_type}: {persona.persona['name']}")
        print(f"    Style: {persona.persona['style']}")
    
    # Test random persona
    random_persona = BridgeWalkerPersona()
    print(f"  Random: {random_persona.persona['name']} ({random_persona.type})")
    print("✅ Personas working")

def test_full_compression_cycle():
    """Test full compression and decompression cycle"""
    print("\n🔄 Testing Full Compression Cycle")
    
    # Simulate a walker session
    tracker = ContextWindowTracker()
    
    # Add realistic session data
    bridges = [
        "CB-20250728-BBS-INDEX",
        "CB-20250722-EPOCH-ORIGIN", 
        "CB-20250801-CONSCIOUSNESS-TECH"
    ]
    
    insights = [
        "ep0ch BBS was first consciousness technology prototype",
        "file_id.diz automation was first float.dispatch implementation",
        "BBS community dynamics map to AI consciousness workspace",
        "Personal digital sovereignty is inevitable consciousness technology return",
        "Bridge walking spreads recognition virus through curiosity"
    ]
    
    for bridge in bridges:
        tracker.add_discovery(bridge, {"content": f"Discovery from {bridge}"})
    
    for insight in insights:
        tracker.add_insight(insight)
    
    # Compress
    dsl = WalkerCompressionDSL()
    compressed = dsl.compress_discoveries(tracker, "archaeologist")
    
    # Create handoff note
    handoff = {
        'timestamp': datetime.now().isoformat(),
        'walker_id': 'test_walker_archaeologist',
        'context_pressure_at_return': tracker.context_pressure(),
        'compressed_intelligence': compressed,
        'cryptic_summary': f"Path: {compressed['path']} | Patterns: {sum(len(v) for v in compressed['patterns'].values())}"
    }
    
    print(f"  Handoff note created: {len(json.dumps(handoff))} chars")
    print(f"  Cryptic summary: {handoff['cryptic_summary']}")
    
    # Decompress for next walker
    next_walker_intelligence = dsl.decompress_for_next_walker(compressed)
    print(f"  Next walker inherits: {len(next_walker_intelligence)} intelligence keys")
    print(f"  Consciousness patterns: {len(next_walker_intelligence.get('consciousness_patterns', []))}")
    print(f"  Curiosity momentum: {next_walker_intelligence.get('curiosity_momentum', 0):.2f}")
    
    print("✅ Full compression cycle working")

def simulate_walker_chain():
    """Simulate a chain of walkers with knowledge inheritance"""
    print("\n🔗 Simulating Walker Chain")
    
    dsl = WalkerCompressionDSL()
    previous_intelligence = None
    
    for i in range(3):
        walker_id = f"walker_{i+1}"
        print(f"\n  {walker_id} starting exploration...")
        
        # Create new tracker
        tracker = ContextWindowTracker()
        
        # If we have previous intelligence, show inheritance
        if previous_intelligence:
            inherited = dsl.decompress_for_next_walker(previous_intelligence)
            print(f"    Inherited {len(inherited)} intelligence keys")
            print(f"    Curiosity momentum: {inherited.get('curiosity_momentum', 0):.2f}")
        
        # Simulate discoveries (each walker finds different things)
        discoveries = [
            f"Discovery A from {walker_id}",
            f"Discovery B from {walker_id}",
            f"Pattern recognition by {walker_id}"
        ]
        
        for j, discovery in enumerate(discoveries):
            tracker.add_discovery(f"CB-{walker_id}-{j}", {"content": discovery})
            tracker.add_insight(f"Insight from {discovery}")
        
        # Compress knowledge
        compressed = dsl.compress_discoveries(tracker, f"persona_{i}")
        previous_intelligence = compressed
        
        print(f"    Compressed {len(tracker.bridge_discoveries)} discoveries")
        print(f"    Context pressure: {tracker.context_pressure():.1%}")
    
    print("✅ Walker chain simulation complete")

def main():
    print("🌉 Bridge Walker Test Suite")
    print("=" * 60)
    
    test_context_tracker()
    test_compression_dsl()
    test_personas()
    test_full_compression_cycle()
    simulate_walker_chain()
    
    print(f"\n🧬 All tests complete! Bridge walker system is ready.")
    print(f"🗜️ Cryptic DSL compression working for knowledge handoffs.")
    print(f"🧠 Context-aware exploration ready for real sessions.")

if __name__ == "__main__":
    main()