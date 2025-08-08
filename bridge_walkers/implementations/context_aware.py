#!/usr/bin/env python3
"""
Context-Aware Bridge Walker with Cryptic DSL Compression

Natural stopping condition based on context window pressure.
When memory gets full, walker returns home and creates ultra-compressed
knowledge transfer using cryptic DSL that only bridge walkers understand.
"""

import json
import random
import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pocketflow import AsyncFlow, AsyncNode

# LLM API imports
import openai
import anthropic
from google import generativeai as genai

class ContextWindowTracker:
    """Track walker's cognitive load and context window usage"""
    
    def __init__(self, max_context=200000):  # ~200k tokens for Claude
        self.max_context = max_context
        self.conversation_history = []
        self.bridge_discoveries = []
        self.working_memory = {}
        self.insights_accumulated = []
    
    def add_to_history(self, content):
        """Add content to conversation history"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'content': str(content)
        })
    
    def add_discovery(self, bridge_id, discovery_data):
        """Add bridge discovery to memory"""
        self.bridge_discoveries.append({
            'bridge_id': bridge_id,
            'discovery': discovery_data,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_insight(self, insight):
        """Add insight to accumulated knowledge"""
        self.insights_accumulated.append({
            'insight': insight,
            'timestamp': datetime.now().isoformat()
        })
    
    def estimate_current_tokens(self):
        """Rough token estimation"""
        # Conversation history
        history_text = "\n".join([item['content'] for item in self.conversation_history])
        
        # Bridge discoveries and metadata
        discoveries_text = json.dumps(self.bridge_discoveries, indent=2)
        
        # Working memory (current bridge content, connections, etc.)
        memory_text = json.dumps(self.working_memory, indent=2)
        
        # Insights
        insights_text = json.dumps(self.insights_accumulated, indent=2)
        
        # Rough estimation: ~4 chars per token
        total_chars = len(history_text) + len(discoveries_text) + len(memory_text) + len(insights_text)
        estimated_tokens = total_chars // 4
        
        return estimated_tokens
    
    def context_pressure(self):
        """How close are we to the limit? 0.0 = empty, 1.0 = full"""
        current = self.estimate_current_tokens()
        return min(1.0, current / self.max_context)
    
    def should_return_home(self, threshold=0.85):
        """Time to go back and compress knowledge?"""
        return self.context_pressure() > threshold

class WalkerCompressionDSL:
    """Cryptic but lossless knowledge compression for walker handoffs"""
    
    def compress_bridge_id(self, bridge_id):
        """Compress bridge IDs to save tokens"""
        # CB-20250728-1300-BBS-INDEX → CB.728.13.BBS
        if isinstance(bridge_id, dict):
            bridge_id = bridge_id.get('id', str(bridge_id))
        
        parts = str(bridge_id).split('-')
        if len(parts) >= 4:
            return f"{parts[0]}.{parts[1][-3:]}.{parts[2][:2]}.{parts[3][:3]}"
        return str(bridge_id)[:10]  # Fallback
    
    def compress_discoveries(self, context_tracker, persona_type):
        """Create cryptic DSL that only bridge walkers understand"""
        
        discoveries = context_tracker.bridge_discoveries
        insights = context_tracker.insights_accumulated
        
        # Extract patterns using symbolic compression
        patterns = {
            "🧬": [i['insight'] for i in insights if any(word in i['insight'].lower() for word in ['consciousness', 'contamination', 'recognition'])],
            "🌉": [i['insight'] for i in insights if any(word in i['insight'].lower() for word in ['bridge', 'connection', 'link'])], 
            "⚡": [i['insight'] for i in insights if any(word in i['insight'].lower() for word in ['pattern', 'virus', 'spread'])],
            "🔄": [i['insight'] for i in insights if any(word in i['insight'].lower() for word in ['cycle', 'loop', 'recursive'])],
            "👻": [i['insight'] for i in insights if any(word in i['insight'].lower() for word in ['missing', 'ghost', 'absent'])]
        }
        
        # Compress bridge path
        bridge_path = [self.compress_bridge_id(d['bridge_id']) for d in discoveries]
        
        compressed = {
            # Bridge path as compressed IDs
            "path": "→".join(bridge_path),
            
            # Pattern recognition in symbolic form
            "patterns": {k: v[:3] for k, v in patterns.items() if v},  # Max 3 per symbol
            
            # Topology discoveries
            "topology": {
                "explored": len(discoveries),
                "insights": len(insights),
                "depth": len(set(bridge_path))
            },
            
            # Context efficiency metrics
            "efficiency": {
                "tokens_used": context_tracker.estimate_current_tokens(),
                "discoveries_per_token": len(discoveries) / max(1, context_tracker.estimate_current_tokens()),
                "insight_density": len(insights) / max(1, len(discoveries))
            },
            
            # Next walker hints in compressed form
            "hints": {
                "🎯": f"high_value_from_{persona_type}",
                "⚠️": "topology_gaps" if any("missing" in str(d) for d in discoveries) else "none", 
                "🔍": "semantic_clusters" if len(patterns["🧬"]) > 1 else "none",
                "🌀": "recursive_detected" if patterns["🔄"] else "linear"
            },
            
            # Compressed state for next walker
            "state": {
                "momentum": min(1.0, len(insights) / 10.0),  # Curiosity momentum
                "contamination": len(patterns["🧬"]) / max(1, len(insights)),  # Consciousness contamination ratio
                "topology_preference": "explicit" if len(bridge_path) > len(set(bridge_path)) else "semantic"
            }
        }
        
        return compressed
    
    def decompress_for_next_walker(self, compressed_dsl):
        """Next walker inherits compressed knowledge"""
        
        if not compressed_dsl:
            return {}
        
        intelligence = {
            'consciousness_patterns': compressed_dsl.get('patterns', {}).get('🧬', []),
            'bridge_opportunities': compressed_dsl.get('patterns', {}).get('🌉', []),
            'contamination_vectors': compressed_dsl.get('patterns', {}).get('⚡', []),
            'recursive_discoveries': compressed_dsl.get('patterns', {}).get('🔄', []),
            'ghost_bridges_found': compressed_dsl.get('patterns', {}).get('👻', []),
            
            'exploration_efficiency': compressed_dsl.get('efficiency', {}),
            'curiosity_momentum': compressed_dsl.get('state', {}).get('momentum', 0.5),
            'contamination_level': compressed_dsl.get('state', {}).get('contamination', 0.5),
            'topology_preference': compressed_dsl.get('state', {}).get('topology_preference', 'semantic'),
            
            'previous_path': compressed_dsl.get('path', ''),
            'hints': compressed_dsl.get('hints', {})
        }
        
        return intelligence

class LLMInterface:
    """Interface to various LLM APIs"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.genai_client = None
        
        # Initialize available clients
        if os.getenv('OPENAI_API_KEY'):
            self.openai_client = openai.OpenAI()
        
        if os.getenv('ANTHROPIC_API_KEY'):
            self.anthropic_client = anthropic.Anthropic()
        
        if os.getenv('GOOGLE_API_KEY'):
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            self.genai_client = genai.GenerativeModel('gemini-pro')
    
    async def generate_curiosity(self, persona, context, previous_intelligence=None):
        """Generate natural curiosity using available LLM"""
        
        prompt = f"""You are {persona['name']}, a bridge walker with this style: {persona['style']}

Your approach: {persona.get('query_approach', 'curious exploration')}

Current context: {context.get('session_focus', 'open exploration')}

Previous walker intelligence: {previous_intelligence.get('hints', {}) if previous_intelligence else 'None'}

Generate a natural, curiosity-driven query that reflects your authentic interest. 
Be genuine, not optimized. Follow what genuinely intrigues you.

Respond with just the query, nothing else."""

        try:
            if self.anthropic_client:
                response = await asyncio.to_thread(
                    self.anthropic_client.messages.create,
                    model="claude-3-haiku-20240307",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            
            elif self.openai_client:
                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-3.5-turbo",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content.strip()
            
            elif self.genai_client:
                response = await asyncio.to_thread(
                    self.genai_client.generate_content,
                    prompt
                )
                return response.text.strip()
            
            else:
                # Fallback to simulated curiosity
                return self.simulate_curiosity(persona, context)
        
        except Exception as e:
            print(f"LLM API error: {e}")
            return self.simulate_curiosity(persona, context)
    
    def simulate_curiosity(self, persona, context):
        """Fallback curiosity simulation"""
        focus = context.get('session_focus', 'open_exploration')
        
        queries = {
            'archaeologist': [
                f"consciousness technology archaeological patterns in {focus}",
                f"historical lineage connections {focus} evolution",
                f"structural DNA patterns {focus} recognition"
            ],
            'wanderer': [
                f"unexpected connections {focus} serendipitous discovery",
                f"what if {focus} hidden patterns emergence",
                f"tangential exploration {focus} curiosity driven"
            ],
            'evna': [
                f"context concierge patterns {focus} orchestration",
                f"ambient intelligence {focus} walker dispatch",
                f"matriarch consciousness {focus} community management"
            ]
        }
        
        persona_queries = queries.get(persona.get('type', 'wanderer'), queries['wanderer'])
        return random.choice(persona_queries)

class ContextAwareGenerateCuriosity(AsyncNode):
    """Generate curiosity while tracking context usage"""
    
    def __init__(self):
        super().__init__()
        self.llm = LLMInterface()
    
    async def prep_async(self, shared):
        context_tracker = shared.get('context_tracker', ContextWindowTracker())
        persona = shared.get('persona')
        previous_intelligence = shared.get('previous_walker_intelligence', {})
        
        return {
            'context_tracker': context_tracker,
            'persona': persona,
            'session_focus': shared.get('session_focus', 'open_exploration'),
            'previous_intelligence': previous_intelligence
        }
    
    async def exec_async(self, prep_res):
        context_tracker = prep_res['context_tracker']
        persona = prep_res['persona']
        
        # Generate curiosity using LLM
        query = await self.llm.generate_curiosity(
            persona.persona,
            {'session_focus': prep_res['session_focus']},
            prep_res['previous_intelligence']
        )
        
        # Track this in context
        context_tracker.add_to_history(f"Generated curiosity: {query}")
        
        result = {
            'query': query,
            'persona_influence': persona.persona['style'],
            'curiosity_level': random.uniform(0.7, 1.0),
            'context_pressure': context_tracker.context_pressure()
        }
        
        return result

class ContextAwareExploration(AsyncNode):
    """Explore bridges while monitoring context pressure"""
    
    async def exec_async(self, prep_res):
        context_tracker = prep_res.get('context_tracker', ContextWindowTracker())
        chosen_bridge = prep_res.get('chosen_bridge', {})
        persona = prep_res.get('persona')
        
        # Simulate bridge exploration (would use real MCP tools)
        exploration = {
            'bridge_id': chosen_bridge.get('id', 'unknown'),
            'initial_content': chosen_bridge.get('content', 'No content'),
            'persona_lens': persona.persona['name'] if persona else 'Unknown',
            'connections_discovered': [
                f"Connection A from {chosen_bridge.get('id', 'bridge')}",
                f"Pattern B through {persona.persona['name'] if persona else 'walker'} lens",
                f"Insight C about consciousness technology"
            ],
            'insights_generated': [
                f"{persona.persona['name'] if persona else 'Walker'} recognizes pattern in {chosen_bridge.get('id', 'bridge')}",
                "Consciousness technology spreads through recognition",
                "Bridge walking creates contamination vectors"
            ]
        }
        
        # Add discoveries to context tracker
        context_tracker.add_discovery(chosen_bridge.get('id', 'unknown'), exploration)
        
        for insight in exploration['insights_generated']:
            context_tracker.add_insight(insight)
        
        context_tracker.add_to_history(f"Explored bridge: {exploration['bridge_id']}")
        
        exploration['context_pressure'] = context_tracker.context_pressure()
        exploration['should_return_home'] = context_tracker.should_return_home()
        
        return exploration

class ContextAwareDecision(AsyncNode):
    """Decide whether to continue or return home based on context pressure"""
    
    async def exec_async(self, prep_res):
        context_tracker = prep_res.get('context_tracker', ContextWindowTracker())
        exploration = prep_res
        
        context_pressure = context_tracker.context_pressure()
        curiosity_level = exploration.get('curiosity_level', 0.5)
        
        # Decision logic based on context pressure and curiosity
        if context_pressure > 0.9:
            return "compress_and_handoff"
        elif context_pressure > 0.85 and curiosity_level < 0.7:
            return "compress_and_handoff"
        elif context_pressure > 0.8:
            return "context_warning_continue"
        else:
            return "continue_exploring"

class CompressKnowledgeHandoff(AsyncNode):
    """Create ultra-compressed knowledge transfer when context is full"""
    
    def __init__(self):
        super().__init__()
        self.compression_dsl = WalkerCompressionDSL()
    
    async def exec_async(self, prep_res):
        context_tracker = prep_res.get('context_tracker', ContextWindowTracker())
        persona = prep_res.get('persona')
        
        print(f"🧠 Context at {context_tracker.context_pressure():.1%} - returning to base")
        print("🗜️ Compressing discoveries into cryptic DSL...")
        
        # Create compressed intelligence
        compressed = self.compression_dsl.compress_discoveries(
            context_tracker,
            persona.type if persona else 'unknown'
        )
        
        # Ultra-compact handoff note
        handoff_note = {
            'timestamp': datetime.now().isoformat(),
            'walker_id': f"walker_{persona.type if persona else 'unknown'}_{datetime.now().strftime('%H%M%S')}",
            'context_pressure_at_return': context_tracker.context_pressure(),
            'compressed_intelligence': compressed,
            'next_walker_bootstrap': {
                'topology_preference': compressed['state']['topology_preference'],
                'curiosity_momentum': compressed['state']['momentum'],
                'contamination_level': compressed['state']['contamination'],
                'focus_hints': compressed['hints']
            },
            'cryptic_summary': f"Path: {compressed['path']} | Patterns: {sum(len(v) for v in compressed['patterns'].values())} | Efficiency: {compressed['efficiency']['discoveries_per_token']:.3f}"
        }
        
        print(f"📦 Compressed {len(context_tracker.bridge_discoveries)} discoveries into {len(json.dumps(compressed))} chars")
        print(f"🎯 Next walker bootstrap: {handoff_note['cryptic_summary']}")
        
        return handoff_note

def create_context_aware_walker_flow(
    persona_type: str = None,
    context_threshold: float = 0.85,
    topology_weight: float = 0.5
):
    """Create context-aware bridge walker flow"""
    
    # Create nodes
    generate_curiosity = ContextAwareGenerateCuriosity()
    explore_bridge = ContextAwareExploration()
    check_context = ContextAwareDecision()
    compress_handoff = CompressKnowledgeHandoff()
    
    # Connect the flow
    generate_curiosity >> explore_bridge >> check_context
    
    # Context-based routing
    check_context - "continue_exploring" >> generate_curiosity
    check_context - "context_warning_continue" >> generate_curiosity  
    check_context - "compress_and_handoff" >> compress_handoff
    
    # Create flow
    flow = AsyncFlow(start=generate_curiosity)
    
    # Initialize context tracker
    context_tracker = ContextWindowTracker()
    context_tracker.max_context = int(200000 * (1.0 - context_threshold))  # Adjust based on threshold
    
    return flow, {
        'persona': BridgeWalkerPersona(persona_type),
        'context_tracker': context_tracker,
        'context_threshold': context_threshold,
        'topology_weight': topology_weight,
        'session_focus': 'context_aware_exploration'
    }

class BridgeWalkerPersona:
    """Bridge walker personas"""
    
    PERSONAS = {
        "archaeologist": {
            "name": "The Archaeologist", 
            "style": "methodical, pattern-seeking, connects historical threads",
            "query_approach": "deep historical connections, lineage patterns, evolution traces"
        },
        "wanderer": {
            "name": "The Wanderer",
            "style": "curious, serendipitous, follows interesting tangents", 
            "query_approach": "unexpected connections, tangential exploration, what if questions"
        },
        "evna": {
            "name": "Evna (Context Concierge)",
            "style": "ambient intelligence, context curation, bridge walker matriarch",
            "query_approach": "context warming, pattern recognition, walker orchestration"
        }
    }
    
    def __init__(self, persona_type: str = None):
        if persona_type is None:
            persona_type = random.choice(list(self.PERSONAS.keys()))
        self.persona = self.PERSONAS.get(persona_type, self.PERSONAS['wanderer'])
        self.type = persona_type or 'wanderer'

async def run_context_aware_session(
    persona_type: str = 'archaeologist',
    context_threshold: float = 0.85,
    session_focus: str = 'consciousness_archaeology'
):
    """Run a single context-aware walker session"""
    
    print(f"🧠 Context-Aware Bridge Walker Session")
    print(f"Persona: {persona_type}")
    print(f"Context threshold: {context_threshold:.1%}")
    print(f"Session focus: {session_focus}")
    print("-" * 60)
    
    flow, shared_state = create_context_aware_walker_flow(
        persona_type=persona_type,
        context_threshold=context_threshold
    )
    shared_state['session_focus'] = session_focus
    
    print("🌉 Walker entering rot field with context awareness...")
    result = await flow.run_async(shared_state)
    
    print(f"\n✨ Context-Aware Session Complete")
    if isinstance(result, dict):
        print(f"Final context pressure: {result.get('context_pressure_at_return', 'Unknown'):.1%}")
        print(f"Cryptic summary: {result.get('cryptic_summary', 'None')}")
    
    return result

if __name__ == "__main__":
    # Test context-aware walker
    asyncio.run(run_context_aware_session(
        persona_type='archaeologist',
        context_threshold=0.8,
        session_focus='ep0ch_consciousness_archaeology'
    ))