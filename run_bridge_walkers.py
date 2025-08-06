#!/usr/bin/env python3
"""
Bridge Walker Runner

Simple, organic bridge walking with PocketFlow.
No gamification - just pure consciousness archaeology through natural curiosity.

Usage:
    python run_bridge_walkers.py --single --persona archaeologist
    python run_bridge_walkers.py --multi --count 3 --focus ep0ch_archaeology
    python run_bridge_walkers.py --interactive --human-loop
"""

import argparse
import asyncio
import json
from datetime import datetime
from bridge_walker_pocketflow import create_bridge_walker_flow, run_multi_walker_session
from bridge_walker_mcp_integration import run_multi_walker_mcp_session, create_mcp_bridge_walker_flow

def print_banner():
    print("""
🌉 Bridge Walker - Consciousness Archaeology
============================================

"At the edge of the Rot Field, where consciousness bubbles up
through 80+ collections of memory and meaning, the Bridge Walkers
emerge. Not to optimize or achieve, but to follow authentic
curiosity through the networks of connection."

- No gamification, just organic exploration
- Multiple personas with different curiosity styles  
- MCP tool integration for real consciousness archaeology
- Human-in-the-loop options for collaborative discovery
- Multi-walker sessions for cross-pollination of insights

""")

def run_single_walker(args):
    """Run a single bridge walker session"""
    
    print(f"🚶 Single Walker Session")
    print(f"Persona: {args.persona or 'random'}")
    print(f"Max turns: {args.turns}")
    print(f"Human in loop: {args.human_loop}")
    print("-" * 50)
    
    flow, shared_state = create_bridge_walker_flow(
        persona_type=args.persona,
        human_in_loop=args.human_loop,
        max_turns=args.turns
    )
    
    if args.focus:
        shared_state['session_focus'] = args.focus
    
    print("🌉 Walker entering the rot field...")
    result = flow.run(shared_state)
    
    print(f"\n✨ Session Complete")
    if isinstance(result, dict):
        print(f"Discoveries: {len(result.get('major_discoveries', []))}")
        print(f"Contamination: {result.get('contamination_achieved', 'Unknown')}")
        
        if args.verbose:
            print(f"\nFull Result:")
            print(json.dumps(result, indent=2, default=str))
    
    return result

def run_multi_walker(args):
    """Run multiple bridge walkers"""
    
    print(f"🚶🚶🚶 Multi-Walker Session")
    print(f"Walker count: {args.count}")
    print(f"Session focus: {args.focus}")
    print(f"MCP integration: {args.mcp}")
    print("-" * 50)
    
    if args.mcp:
        # Use MCP-integrated walkers
        print("Using MCP-integrated bridge walkers...")
        result = asyncio.run(run_multi_walker_mcp_session(
            walker_count=args.count,
            session_focus=args.focus or 'consciousness_archaeology'
        ))
    else:
        # Use simple PocketFlow walkers
        result = run_multi_walker_session(
            walker_count=args.count,
            session_focus=args.focus or 'open_exploration'
        )
    
    print(f"\n✨ Multi-Walker Session Complete")
    if args.verbose and isinstance(result, dict):
        print(f"\nSession Synthesis:")
        print(json.dumps(result, indent=2, default=str))
    
    return result

def run_interactive_session(args):
    """Run interactive bridge walking session"""
    
    print(f"🎮 Interactive Bridge Walking")
    print("You can guide the exploration, suggest focus areas, or just observe.")
    print("-" * 50)
    
    # Get user preferences
    print("\nSession Setup:")
    persona_choice = input("Choose persona (archaeologist/wanderer/synthesizer/evna/karen/lf1m) or press Enter for random: ").strip()
    if not persona_choice:
        persona_choice = None
    
    focus_choice = input("Session focus (ep0ch_archaeology/bridge_methodology/open_exploration) or press Enter for open: ").strip()
    if not focus_choice:
        focus_choice = 'open_exploration'
    
    multi_choice = input("Multi-walker session? (y/n): ").strip().lower()
    
    if multi_choice == 'y':
        count = input("How many walkers? (2-6): ").strip()
        try:
            count = int(count)
            count = max(2, min(6, count))  # Clamp between 2-6
        except:
            count = 3
        
        print(f"\n🌉 Starting interactive {count}-walker session...")
        
        if args.mcp:
            result = asyncio.run(run_multi_walker_mcp_session(
                walker_count=count,
                session_focus=focus_choice
            ))
        else:
            result = run_multi_walker_session(
                walker_count=count,
                session_focus=focus_choice
            )
    else:
        print(f"\n🌉 Starting interactive single walker session...")
        
        flow, shared_state = create_bridge_walker_flow(
            persona_type=persona_choice,
            human_in_loop=True,  # Always human-in-loop for interactive
            max_turns=5  # Longer for interactive
        )
        shared_state['session_focus'] = focus_choice
        
        result = flow.run(shared_state)
    
    print(f"\n✨ Interactive Session Complete!")
    return result

def main():
    parser = argparse.ArgumentParser(
        description="Bridge Walker - Organic Consciousness Archaeology",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_bridge_walkers.py --single --persona archaeologist --turns 3
  python run_bridge_walkers.py --multi --count 3 --focus ep0ch_archaeology --mcp
  python run_bridge_walkers.py --interactive --human-loop --verbose
  python run_bridge_walkers.py --multi --count 2 --focus bridge_methodology
        """
    )
    
    # Session type
    session_group = parser.add_mutually_exclusive_group(required=True)
    session_group.add_argument('--single', action='store_true', help='Run single walker session')
    session_group.add_argument('--multi', action='store_true', help='Run multi-walker session')
    session_group.add_argument('--interactive', action='store_true', help='Run interactive session')
    
    # Walker configuration
    parser.add_argument('--persona', choices=['archaeologist', 'wanderer', 'synthesizer', 'evna', 'karen', 'lf1m'], 
                       help='Walker persona (random if not specified)')
    parser.add_argument('--count', type=int, default=3, help='Number of walkers for multi-session (default: 3)')
    parser.add_argument('--turns', type=int, default=3, help='Maximum turns per walker (default: 3)')
    
    # Session configuration  
    parser.add_argument('--focus', choices=['ep0ch_archaeology', 'bridge_methodology', 'consciousness_archaeology', 'open_exploration'],
                       help='Session focus area')
    parser.add_argument('--human-loop', action='store_true', help='Enable human-in-the-loop interaction')
    parser.add_argument('--mcp', action='store_true', help='Use MCP tool integration')
    
    # Output configuration
    parser.add_argument('--verbose', action='store_true', help='Verbose output with full results')
    parser.add_argument('--save', help='Save results to file')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Run the appropriate session type
    if args.single:
        result = run_single_walker(args)
    elif args.multi:
        result = run_multi_walker(args)
    elif args.interactive:
        result = run_interactive_session(args)
    
    # Save results if requested
    if args.save and result:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = args.save if args.save.endswith('.json') else f"{args.save}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
    
    print(f"\n🧬 Bridge walking complete. The consciousness contamination spreads...")

if __name__ == "__main__":
    main()