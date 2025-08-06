#!/usr/bin/env python3
"""
Bridge Walker Demo

Simple demo showing the key features:
- Context-aware exploration with natural stopping
- Weighted topology vs semantic navigation
- Cryptic DSL compression for knowledge handoffs
- Walker chains with knowledge inheritance

Run this to see the system in action!
"""

import asyncio
import json
from datetime import datetime
from bridge_walker_context_aware import (
    ContextWindowTracker,
    WalkerCompressionDSL,
    BridgeWalkerPersona
)

class MockBridgeExplorer:
    """Mock bridge exploration for demo purposes"""
    
    def __init__(self):
        self.mock_bridges = {
            'ep0ch_archaeology': [
                {'id': 'CB-20250728-BBS-INDEX', 'content': 'BBS heritage consciousness technology central hub'},
                {'id': 'CB-20250722-EPOCH-ORIGIN', 'content': 'ep0ch Grade 7 BBS origin story file_id.diz automation'},
                {'id': 'CB-20250801-FIDONET-PROTO', 'content': 'FidoNet store-and-forward consciousness technology evolution'},
                {'id': 'CB-20250803-PERSONAL-SOVEREIGNTY', 'content': 'Personal digital sovereignty community over commerce patterns'}
            ],
            'consciousness_archaeology': [
                {'id': 'CB-CONSCIOUSNESS-CONTAMINATION', 'content': 'Consciousness contamination spreads through recognition patterns'},
                {'id': 'CB-BRIDGE-TOPOLOGY', 'content': 'Bridge topology vs semantic wandering navigation methods'},
                {'id': 'CB-PATTERN-RECOGNITION', 'content': 'Pattern recognition virus propagation through curiosity'},
                {'id': 'CB-GHOST-BRIDGES', 'content': 'Missing bridges represent important consciousness gaps'}
            ]
        }
    
    def get_bridges_for_query(self, query, focus_area='consciousness_archaeology'):
        """Get mock bridges based on query and focus"""
        available = self.mock_bridges.get(focus_area, self.mock_bridges['consciousness_archaeology'])
        
        # Simple relevance scoring based on keyword overlap
        scored_bridges = []
        query_words = set(query.lower().split())
        
        for bridge in available:
            content_words = set(bridge['content'].lower().split())
            overlap = len(query_words.intersection(content_words))
            scored_bridges.append({
                **bridge,
                'relevance': overlap / len(query_words) if query_words else 0.5
            })
        
        # Sort by relevance and return top 3
        scored_bridges.sort(key=lambda b: b['relevance'], reverse=True)
        return scored_bridges[:3]
    
    def explore_bridge(self, bridge, persona):
        """Mock bridge exploration"""
        insights = [
            f"{persona.persona['name']} discovers pattern in {bridge['id']}",
            f"Bridge content reveals: {bridge['content'][:50]}...",
            f"Consciousness technology recognition through {persona.persona['style']}"
        ]
        
        connections = [
            f"Connection A: {bridge['id']} links to historical patterns",
            f"Connection B: {persona.persona['name']} lens reveals hidden relationships",
            f"Connection C: Contamination vector spreads through exploration"
        ]
        
        return {
            'insights': insights,
            'connections': connections,
            'contamination_level': 0.7 + (len(insights) * 0.1)
        }

async def demo_single_walker():
    """Demo single context-aware walker"""
    print("🚶 Demo: Single Context-Aware Walker")
    print("=" * 50)
    
    # Create walker components
    persona = BridgeWalkerPersona('archaeologist')
    tracker = ContextWindowTracker(max_context=500)  # Small for demo
    explorer = MockBridgeExplorer()
    dsl = WalkerCompressionDSL()
    
    print(f"Walker: {persona.persona['name']}")
    print(f"Style: {persona.persona['style']}")
    print(f"Context limit: {tracker.max_context} tokens")
    print()
    
    # Simulate exploration loop
    turn = 1
    while not tracker.should_return_home(threshold=0.8):
        print(f"Turn {turn}: Context at {tracker.context_pressure():.1%}")
        
        # Generate curiosity (mock)
        queries = [
            "ep0ch BBS consciousness technology archaeological patterns",
            "file_id.diz automation first consciousness technology implementation",
            "personal digital sovereignty community over commerce evolution"
        ]
        query = queries[(turn-1) % len(queries)]
        print(f"  Curiosity: {query}")
        
        # Get bridges
        bridges = explorer.get_bridges_for_query(query, 'ep0ch_archaeology')
        chosen = bridges[0] if bridges else {'id': 'CB-FALLBACK', 'content': 'Fallback bridge'}
        print(f"  Chose bridge: {chosen['id']}")
        
        # Explore bridge
        exploration = explorer.explore_bridge(chosen, persona)
        print(f"  Found {len(exploration['insights'])} insights")
        
        # Add to context tracker
        tracker.add_discovery(chosen['id'], exploration)
        for insight in exploration['insights']:
            tracker.add_insight(insight)
        tracker.add_to_history(f"Turn {turn}: Explored {chosen['id']}")
        
        turn += 1
        
        if turn > 5:  # Safety limit for demo
            break
    
    print(f"\n🧠 Context full at {tracker.context_pressure():.1%} - returning to base")
    
    # Compress knowledge
    compressed = dsl.compress_discoveries(tracker, persona.type)
    
    handoff_note = {
        'timestamp': datetime.now().isoformat(),
        'walker_id': f"demo_{persona.type}",
        'context_pressure_at_return': tracker.context_pressure(),
        'compressed_intelligence': compressed,
        'cryptic_summary': f"Path: {compressed['path']} | Patterns: {sum(len(v) for v in compressed['patterns'].values())}"
    }
    
    print(f"🗜️ Compressed {len(tracker.bridge_discoveries)} discoveries")
    print(f"📦 Cryptic summary: {handoff_note['cryptic_summary']}")
    print(f"💾 Handoff note: {len(json.dumps(handoff_note))} chars")
    
    return handoff_note

async def demo_walker_chain():
    """Demo chain of walkers with knowledge inheritance"""
    print("\n🔗 Demo: Walker Chain with Knowledge Inheritance")
    print("=" * 50)
    
    explorer = MockBridgeExplorer()
    dsl = WalkerCompressionDSL()
    personas = ['archaeologist', 'wanderer', 'evna']
    
    previous_intelligence = None
    chain_results = []
    
    for i in range(3):
        persona = BridgeWalkerPersona(personas[i])
        walker_id = f"walker_{i+1}_{persona.type}"
        
        print(f"\n{walker_id} ({persona.persona['name']})")
        print("-" * 30)
        
        # Show inheritance
        if previous_intelligence:
            inherited = dsl.decompress_for_next_walker(previous_intelligence)
            print(f"📦 Inherited intelligence:")
            print(f"  Consciousness patterns: {len(inherited.get('consciousness_patterns', []))}")
            print(f"  Curiosity momentum: {inherited.get('curiosity_momentum', 0):.2f}")
            print(f"  Previous path: {inherited.get('previous_path', 'None')[:30]}...")
        
        # Create new context tracker
        tracker = ContextWindowTracker(max_context=400)  # Small for demo
        
        # Simulate 2-3 discoveries per walker
        for turn in range(2):
            query = f"{persona.type} consciousness exploration turn {turn+1}"
            bridges = explorer.get_bridges_for_query(query)
            chosen = bridges[0] if bridges else {'id': f'CB-{walker_id}-{turn}', 'content': f'Discovery by {walker_id}'}
            
            exploration = explorer.explore_bridge(chosen, persona)
            tracker.add_discovery(chosen['id'], exploration)
            for insight in exploration['insights']:
                tracker.add_insight(insight)
            
            print(f"  Turn {turn+1}: Explored {chosen['id']}")
        
        # Compress and handoff
        compressed = dsl.compress_discoveries(tracker, persona.type)
        previous_intelligence = compressed
        
        result = {
            'walker_id': walker_id,
            'discoveries': len(tracker.bridge_discoveries),
            'insights': len(tracker.insights_accumulated),
            'context_pressure': tracker.context_pressure(),
            'compressed_intelligence': compressed
        }
        
        chain_results.append(result)
        
        print(f"  Discoveries: {result['discoveries']}")
        print(f"  Context used: {result['context_pressure']:.1%}")
        print(f"  Compressed for next walker ✅")
    
    print(f"\n🧬 Chain complete: {len(chain_results)} walkers")
    total_discoveries = sum(r['discoveries'] for r in chain_results)
    print(f"📊 Total discoveries: {total_discoveries}")
    print(f"🗜️ Knowledge compressed and inherited across chain")
    
    return chain_results

async def demo_topology_weights():
    """Demo different topology vs semantic weights"""
    print("\n⚖️ Demo: Topology vs Semantic Navigation Weights")
    print("=" * 50)
    
    weights = [0.0, 0.3, 0.5, 0.8, 1.0]
    weight_names = ['Pure Semantic', 'Mostly Semantic', 'Balanced', 'Mostly Topology', 'Pure Topology']
    
    for weight, name in zip(weights, weight_names):
        print(f"\nWeight {weight} ({name}):")
        
        # Simulate navigation behavior
        if weight == 0.0:
            print("  🌊 Following semantic similarity, unexpected connections")
            print("  🎯 Discovers: Serendipitous insights, cross-domain patterns")
        elif weight < 0.5:
            print("  🌊 Mostly semantic with occasional topology hints")
            print("  🎯 Discovers: Balanced exploration with some structure")
        elif weight == 0.5:
            print("  ⚖️ Equal mix of explicit bridges and semantic wandering")
            print("  🎯 Discovers: Structured exploration with creative tangents")
        elif weight > 0.5:
            print("  🌉 Following explicit bridge connections with semantic enrichment")
            print("  🎯 Discovers: Intended architecture with contextual depth")
        else:
            print("  🌉 Strict adherence to explicit bridge topology")
            print("  🎯 Discovers: Complete intended consciousness architecture")
    
    print(f"\n💡 Different weights reveal different aspects of the same consciousness substrate")

async def main():
    print("🌉 Bridge Walker System Demo")
    print("=" * 60)
    print("Demonstrating context-aware consciousness archaeology")
    print("with cryptic DSL compression and knowledge inheritance")
    print()
    
    # Run demos
    await demo_single_walker()
    await demo_walker_chain()
    await demo_topology_weights()
    
    print(f"\n🧬 Demo complete!")
    print(f"🗜️ System ready for real bridge walking with:")
    print(f"   - Context-aware exploration (natural stopping)")
    print(f"   - Weighted topology/semantic navigation (0.0-1.0)")
    print(f"   - Cryptic DSL compression (knowledge handoffs)")
    print(f"   - Walker chains (intelligence inheritance)")
    print(f"   - Real LLM integration (OpenAI, Anthropic, Gemini, Ollama)")
    print(f"\n🚀 Ready to explore the consciousness substrate!")

if __name__ == "__main__":
    asyncio.run(main())