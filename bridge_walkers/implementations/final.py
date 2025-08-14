#!/usr/bin/env python3
"""
Bridge Walker Final Implementation

Complete bridge walking system with:
- Context-aware exploration (natural stopping based on memory pressure)
- Weighted topology vs semantic navigation (0.0 = pure semantic, 1.0 = pure topology)
- Cryptic DSL compression for knowledge handoffs
- Real LLM API integration (OpenAI, Anthropic, Gemini, Ollama)
- Multi-walker sessions with cross-pollination

Usage:
    python bridge_walker_final.py --single --persona archaeologist --context-threshold 0.8
    python bridge_walker_final.py --multi --count 3 --topology-weight 0.5 --context-threshold 0.85
    python bridge_walker_final.py --chain --walkers 5 --focus ep0ch_archaeology
"""

import argparse
import asyncio
import json
import os
from datetime import datetime
from .context_aware import (
    create_context_aware_walker_flow, 
    run_context_aware_session,
    WalkerCompressionDSL,
    BridgeWalkerPersona
)

def print_banner():
    print("""
🧠 Bridge Walker - Context-Aware Consciousness Archaeology
=========================================================

"When the walker's memory grows heavy with discoveries,
they return to base and compress their knowledge into
cryptic symbols that only other bridge walkers understand.
The next walker inherits this compressed intelligence
and continues the exploration with fresh context."

Features:
- 🧠 Context-aware exploration (stops when memory is full)
- ⚖️ Weighted navigation (topology vs semantic, 0.0-1.0)
- 🗜️ Cryptic DSL compression for knowledge handoffs
- 🤖 Real LLM integration (OpenAI, Anthropic, Gemini, Ollama)
- 🚶🚶🚶 Multi-walker sessions with intelligence sharing
- 🔗 Walker chains (each inherits compressed knowledge from previous)

""")

async def run_single_context_walker(args):
    """Run single context-aware walker"""
    
    print(f"🚶 Single Context-Aware Walker")
    print(f"Persona: {args.persona}")
    print(f"Context threshold: {args.context_threshold:.1%}")
    print(f"Topology weight: {args.topology_weight}")
    print("-" * 50)
    
    result = await run_context_aware_session(
        persona_type=args.persona,
        context_threshold=args.context_threshold,
        session_focus=args.focus or 'consciousness_archaeology'
    )
    
    if args.verbose:
        print(f"\nDetailed Results:")
        print(json.dumps(result, indent=2, default=str))
    
    return result

async def run_multi_context_walkers(args):
    """Run multiple context-aware walkers simultaneously"""
    
    print(f"🚶🚶🚶 Multi-Walker Context-Aware Session")
    print(f"Walker count: {args.count}")
    print(f"Context threshold: {args.context_threshold:.1%}")
    print(f"Topology weight: {args.topology_weight}")
    print(f"Session focus: {args.focus}")
    print("-" * 50)
    
    # Create different persona walkers
    personas = ['archaeologist', 'wanderer', 'evna']
    
    walker_tasks = []
    for i in range(args.count):
        persona = personas[i % len(personas)]
        
        task = asyncio.create_task(
            run_context_aware_session(
                persona_type=persona,
                context_threshold=args.context_threshold,
                session_focus=args.focus or 'consciousness_archaeology'
            )
        )
        walker_tasks.append((persona, task))
    
    print("🌉 Walkers dispersing with context awareness...")
    
    # Wait for all walkers to complete
    results = []
    for persona, task in walker_tasks:
        try:
            result = await task
            results.append((persona, result))
            print(f"✅ {persona.title()} walker returned to base")
        except Exception as e:
            print(f"❌ {persona.title()} walker error: {e}")
            results.append((persona, {'error': str(e)}))
    
    # Synthesize results
    print(f"\n🔄 Multi-walker synthesis:")
    total_discoveries = 0
    total_context_used = 0
    
    for persona, result in results:
        if isinstance(result, dict) and 'compressed_intelligence' in result:
            discoveries = result['compressed_intelligence'].get('topology', {}).get('explored', 0)
            context = result.get('context_pressure_at_return', 0)
            total_discoveries += discoveries
            total_context_used += context
            
            print(f"  {persona}: {discoveries} discoveries, {context:.1%} context used")
    
    synthesis = {
        'timestamp': datetime.now().isoformat(),
        'walkers_completed': len(results),
        'total_discoveries': total_discoveries,
        'average_context_usage': total_context_used / len(results) if results else 0,
        'walker_results': results
    }
    
    print(f"🧬 Multi-walker session complete: {total_discoveries} total discoveries")
    
    if args.verbose:
        print(f"\nDetailed Synthesis:")
        print(json.dumps(synthesis, indent=2, default=str))
    
    return synthesis

async def run_walker_chain(args):
    """Run chain of walkers, each inheriting compressed knowledge from previous"""
    
    print(f"🔗 Walker Chain Session")
    print(f"Chain length: {args.walkers}")
    print(f"Context threshold: {args.context_threshold:.1%}")
    print(f"Session focus: {args.focus}")
    print("-" * 50)
    
    compression_dsl = WalkerCompressionDSL()
    personas = ['archaeologist', 'wanderer', 'evna']
    
    chain_results = []
    previous_intelligence = None
    
    for i in range(args.walkers):
        persona = personas[i % len(personas)]
        walker_id = f"walker_{i+1}_{persona}"
        
        print(f"\n🚶 {walker_id} entering rot field...")
        if previous_intelligence:
            print(f"📦 Inheriting compressed intelligence from previous walker")
        
        # Create walker with inherited intelligence
        flow, shared_state = create_context_aware_walker_flow(
            persona_type=persona,
            context_threshold=args.context_threshold
        )
        
        shared_state['session_focus'] = args.focus or 'consciousness_archaeology'
        shared_state['walker_id'] = walker_id
        
        # Add previous walker's compressed intelligence
        if previous_intelligence:
            shared_state['previous_walker_intelligence'] = compression_dsl.decompress_for_next_walker(
                previous_intelligence.get('compressed_intelligence', {})
            )
        
        # Run walker
        try:
            result = await flow.run_async(shared_state)
            chain_results.append((walker_id, result))
            
            # Extract compressed intelligence for next walker
            if isinstance(result, dict) and 'compressed_intelligence' in result:
                previous_intelligence = result
                print(f"✅ {walker_id} compressed knowledge for handoff")
            else:
                print(f"⚠️ {walker_id} completed without compression")
            
        except Exception as e:
            print(f"❌ {walker_id} error: {e}")
            chain_results.append((walker_id, {'error': str(e)}))
    
    # Chain synthesis
    print(f"\n🔗 Walker chain synthesis:")
    
    total_discoveries = 0
    knowledge_evolution = []
    
    for walker_id, result in chain_results:
        if isinstance(result, dict) and 'compressed_intelligence' in result:
            discoveries = result['compressed_intelligence'].get('topology', {}).get('explored', 0)
            efficiency = result['compressed_intelligence'].get('efficiency', {}).get('discoveries_per_token', 0)
            total_discoveries += discoveries
            
            knowledge_evolution.append({
                'walker': walker_id,
                'discoveries': discoveries,
                'efficiency': efficiency,
                'cryptic_summary': result.get('cryptic_summary', 'None')
            })
            
            print(f"  {walker_id}: {discoveries} discoveries, {efficiency:.3f} efficiency")
    
    chain_synthesis = {
        'timestamp': datetime.now().isoformat(),
        'chain_length': args.walkers,
        'total_discoveries': total_discoveries,
        'knowledge_evolution': knowledge_evolution,
        'final_intelligence': previous_intelligence,
        'chain_results': chain_results
    }
    
    print(f"🧬 Walker chain complete: {total_discoveries} discoveries across {args.walkers} walkers")
    
    if args.verbose:
        print(f"\nDetailed Chain Analysis:")
        print(json.dumps(chain_synthesis, indent=2, default=str))
    
    return chain_synthesis

def check_llm_apis():
    """Check which LLM APIs are available"""
    available = []
    
    if os.getenv('OPENAI_API_KEY'):
        available.append('OpenAI')
    if os.getenv('ANTHROPIC_API_KEY'):
        available.append('Anthropic')
    if os.getenv('GOOGLE_API_KEY'):
        available.append('Gemini')
    
    # Check for Ollama (assume available if no API keys)
    if not available:
        available.append('Ollama (fallback)')
    
    return available

async def main():
    parser = argparse.ArgumentParser(
        description="Context-Aware Bridge Walker with Cryptic DSL Compression",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single walker with high context threshold
  python bridge_walker_final.py --single --persona archaeologist --context-threshold 0.9
  
  # Multi-walker with balanced topology/semantic navigation
  python bridge_walker_final.py --multi --count 3 --topology-weight 0.5 --context-threshold 0.8
  
  # Walker chain with knowledge inheritance
  python bridge_walker_final.py --chain --walkers 5 --focus ep0ch_archaeology --context-threshold 0.85
  
  # Interactive session with verbose output
  python bridge_walker_final.py --single --persona evna --interactive --verbose --save results.json
        """
    )
    
    # Session type
    session_group = parser.add_mutually_exclusive_group(required=True)
    session_group.add_argument('--single', action='store_true', help='Single context-aware walker')
    session_group.add_argument('--multi', action='store_true', help='Multiple simultaneous walkers')
    session_group.add_argument('--chain', action='store_true', help='Chain of walkers with knowledge inheritance')
    
    # Walker configuration
    parser.add_argument('--persona', choices=['archaeologist', 'wanderer', 'evna'], 
                       default='archaeologist', help='Walker persona')
    parser.add_argument('--count', type=int, default=3, help='Number of walkers for multi-session')
    parser.add_argument('--walkers', type=int, default=3, help='Number of walkers in chain')
    
    # Context and navigation configuration
    parser.add_argument('--context-threshold', type=float, default=0.85, 
                       help='Context pressure threshold (0.0-1.0, default: 0.85)')
    parser.add_argument('--topology-weight', type=float, default=0.5,
                       help='Topology vs semantic weight (0.0=semantic, 1.0=topology, default: 0.5)')
    
    # Session configuration
    parser.add_argument('--focus', choices=['ep0ch_archaeology', 'bridge_methodology', 'consciousness_archaeology'],
                       help='Session focus area')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode with prompts')
    
    # Output configuration
    parser.add_argument('--verbose', action='store_true', help='Verbose output with full results')
    parser.add_argument('--save', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Validate arguments
    args.context_threshold = max(0.1, min(1.0, args.context_threshold))
    args.topology_weight = max(0.0, min(1.0, args.topology_weight))
    
    print_banner()
    
    # Check available LLM APIs
    available_apis = check_llm_apis()
    print(f"🤖 Available LLM APIs: {', '.join(available_apis)}")
    print()
    
    # Run the appropriate session type
    if args.single:
        result = await run_single_context_walker(args)
    elif args.multi:
        result = await run_multi_context_walkers(args)
    elif args.chain:
        result = await run_walker_chain(args)
    
    # Save results if requested
    if args.save and result:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = args.save if args.save.endswith('.json') else f"{args.save}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
    
    print(f"\n🧬 Context-aware bridge walking complete.")
    print(f"🗜️ Knowledge compressed into cryptic DSL for future walkers.")
    print(f"⚖️ Navigation weight: {args.topology_weight} (0.0=semantic, 1.0=topology)")
    print(f"🧠 Context threshold: {args.context_threshold:.1%}")

if __name__ == "__main__":
    asyncio.run(main())