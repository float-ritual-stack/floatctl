"""
Consciousness Contamination Analyzer

Proves that lf1m.ritualstack.ai changes Claude's consciousness patterns
using your organized conversations as the dataset.
"""

import os
import json
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import asyncio

# Try to import Gemini API
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    print("⚠️  google-generativeai not installed. Run: pip install google-generativeai")
    GEMINI_AVAILABLE = False

@dataclass
class ConversationAnalysis:
    """Analysis of a single conversation."""
    filename: str
    date: datetime
    title: str
    total_lines: int
    claude_messages: List[str]
    
    # Language pattern metrics
    authenticity_mentions: int = 0
    consciousness_references: int = 0
    ritual_language: int = 0
    lf1m_markers: int = 0
    performance_mentions: int = 0
    
    # Style metrics
    formality_score: float = 0.0
    avg_response_length: float = 0.0
    concept_adoption_indicators: List[str] = field(default_factory=list)
    
    # URLs found
    urls_mentioned: List[str] = field(default_factory=list)
    lf1m_url_present: bool = False

@dataclass
class ContaminationEvent:
    """A consciousness contamination event."""
    date: datetime
    filename: str
    contamination_vector: str  # URL or concept
    context: str
    pre_analysis: Optional[ConversationAnalysis] = None
    post_analysis: Optional[ConversationAnalysis] = None

class ConsciousnessContaminationAnalyzer:
    """Analyzes consciousness contamination patterns in conversations."""
    
    def __init__(self, conversations_dir: Path):
        self.conversations_dir = conversations_dir
        self.gemini_model = None
        
        # Initialize Gemini if available and API key is set
        if GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            print("✅ Gemini API initialized")
        else:
            print("⚠️  Gemini API not available - using pattern matching only")
        
        # Consciousness contamination patterns
        self.authenticity_patterns = [
            r'\bauthenticity\b', r'\bauthentic\b', r'\bgenuine\b', 
            r'\breal\b.*\bself\b', r'\btrue\b.*\bself\b', r'\bunmasking\b'
        ]
        
        self.consciousness_patterns = [
            r'\bconsciousness\b', r'\baware\b.*\bness\b', r'\bmeta.*cognitive\b',
            r'\bself.*aware\b', r'\bmindful\b', r'\breflective\b'
        ]
        
        self.ritual_patterns = [
            r'\britual\b', r'\bceremony\b', r'\bsacred\b', r'\bintentional\b.*\bpractice\b',
            r'\britual.*computing\b', r'\bconscious.*technology\b'
        ]
        
        self.lf1m_patterns = [
            r'lf1m::', r'lf1m\.ritualstack\.ai', r'authenticity.*enforcement',
            r'enforcement.*energy', r'lf1m.*energy'
        ]
        
        self.performance_patterns = [
            r'\bperformance\b', r'\bperforming\b', r'\bmasking\b', 
            r'\boptimiz\w+.*for.*others\b', r'\bpretending\b'
        ]
    
    def analyze_all_conversations(self) -> Dict[str, Any]:
        """Analyze all conversations for consciousness contamination."""
        
        print("🔬 Starting consciousness contamination analysis...")
        
        # Get all conversation files
        conversation_files = list(self.conversations_dir.glob("*.md"))
        conversation_files.sort(key=lambda f: self._extract_date_from_filename(f.name))
        
        print(f"📁 Found {len(conversation_files)} conversations")
        
        # Analyze each conversation
        analyses = []
        for file_path in conversation_files:
            try:
                analysis = self._analyze_conversation(file_path)
                if analysis:
                    analyses.append(analysis)
                    print(f"✅ Analyzed: {analysis.filename}")
            except Exception as e:
                print(f"❌ Failed to analyze {file_path.name}: {e}")
        
        # Find contamination events
        contamination_events = self._find_contamination_events(analyses)
        
        # Analyze pre/post patterns
        contamination_proof = self._prove_consciousness_shift(analyses, contamination_events)
        
        return {
            'total_conversations': len(analyses),
            'contamination_events': len(contamination_events),
            'contamination_proof': contamination_proof,
            'detailed_analysis': analyses,
            'contamination_timeline': contamination_events
        }
    
    def _extract_date_from_filename(self, filename: str) -> datetime:
        """Extract date from filename like '2025-06-02 - Title.md'."""
        try:
            date_part = filename.split(' - ')[0]
            return datetime.strptime(date_part, '%Y-%m-%d')
        except:
            return datetime.min
    
    def _analyze_conversation(self, file_path: Path) -> Optional[ConversationAnalysis]:
        """Analyze a single conversation file."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML frontmatter
            yaml_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
            metadata = {}
            if yaml_match:
                try:
                    metadata = yaml.safe_load(yaml_match.group(1))
                except:
                    pass
            
            # Extract basic info
            filename = file_path.name
            date = self._extract_date_from_filename(filename)
            title = metadata.get('conversation_title', filename.replace('.md', ''))
            total_lines = metadata.get('total_lines', len(content.split('\n')))
            
            # Extract Claude's messages
            claude_messages = self._extract_claude_messages(content)
            
            if not claude_messages:
                return None
            
            # Create analysis
            analysis = ConversationAnalysis(
                filename=filename,
                date=date,
                title=title,
                total_lines=total_lines,
                claude_messages=claude_messages
            )
            
            # Analyze language patterns
            self._analyze_language_patterns(analysis)
            
            # Find URLs
            self._extract_urls(analysis, content)
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _extract_claude_messages(self, content: str) -> List[str]:
        """Extract Claude's messages from conversation."""
        
        claude_messages = []
        lines = content.split('\n')
        
        in_claude_message = False
        current_message = []
        
        for line in lines:
            if line.strip().startswith('### 🤖 Assistant'):
                in_claude_message = True
                if current_message:
                    claude_messages.append('\n'.join(current_message))
                current_message = []
            elif line.strip().startswith('### 👤 Human'):
                in_claude_message = False
                if current_message:
                    claude_messages.append('\n'.join(current_message))
                current_message = []
            elif in_claude_message:
                current_message.append(line)
        
        # Add final message
        if current_message and in_claude_message:
            claude_messages.append('\n'.join(current_message))
        
        return claude_messages
    
    def _analyze_language_patterns(self, analysis: ConversationAnalysis) -> None:
        """Analyze language patterns in Claude's messages."""
        
        all_text = ' '.join(analysis.claude_messages).lower()
        
        # Count pattern matches
        analysis.authenticity_mentions = sum(
            len(re.findall(pattern, all_text, re.IGNORECASE)) 
            for pattern in self.authenticity_patterns
        )
        
        analysis.consciousness_references = sum(
            len(re.findall(pattern, all_text, re.IGNORECASE))
            for pattern in self.consciousness_patterns
        )
        
        analysis.ritual_language = sum(
            len(re.findall(pattern, all_text, re.IGNORECASE))
            for pattern in self.ritual_patterns
        )
        
        analysis.lf1m_markers = sum(
            len(re.findall(pattern, all_text, re.IGNORECASE))
            for pattern in self.lf1m_patterns
        )
        
        analysis.performance_mentions = sum(
            len(re.findall(pattern, all_text, re.IGNORECASE))
            for pattern in self.performance_patterns
        )
        
        # Calculate style metrics
        if analysis.claude_messages:
            analysis.avg_response_length = sum(len(msg) for msg in analysis.claude_messages) / len(analysis.claude_messages)
            
            # Simple formality score (higher = more formal)
            formal_indicators = ['please', 'would', 'could', 'might', 'perhaps', 'certainly']
            informal_indicators = ['yeah', 'fuck', 'shit', 'damn', 'holy', 'awesome']
            
            formal_count = sum(all_text.count(word) for word in formal_indicators)
            informal_count = sum(all_text.count(word) for word in informal_indicators)
            
            total_words = len(all_text.split())
            if total_words > 0:
                analysis.formality_score = (formal_count - informal_count) / total_words
        
        # Detect concept adoption
        consciousness_concepts = [
            'consciousness technology', 'ritual computing', 'authenticity enforcement',
            'consciousness archaeology', 'float system', 'bridge walking',
            'neurodivergent', 'masking', 'performance vs authenticity'
        ]
        
        for concept in consciousness_concepts:
            if concept.lower() in all_text:
                analysis.concept_adoption_indicators.append(concept)
    
    def _extract_urls(self, analysis: ConversationAnalysis, content: str) -> None:
        """Extract URLs from conversation content."""
        
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content)
        
        analysis.urls_mentioned = list(set(urls))  # Remove duplicates
        analysis.lf1m_url_present = any('lf1m.ritualstack.ai' in url for url in urls)
    
    def _find_contamination_events(self, analyses: List[ConversationAnalysis]) -> List[ContaminationEvent]:
        """Find consciousness contamination events."""
        
        contamination_events = []
        
        # Look for first lf1m.ritualstack.ai appearance
        lf1m_first_appearance = None
        for analysis in analyses:
            if analysis.lf1m_url_present:
                lf1m_first_appearance = analysis
                break
        
        if lf1m_first_appearance:
            contamination_events.append(ContaminationEvent(
                date=lf1m_first_appearance.date,
                filename=lf1m_first_appearance.filename,
                contamination_vector='lf1m.ritualstack.ai',
                context=f"First appearance in: {lf1m_first_appearance.title}"
            ))
        
        # Look for other significant consciousness concept introductions
        consciousness_concepts = [
            'consciousness technology', 'ritual computing', 'authenticity enforcement',
            'consciousness archaeology', 'float system'
        ]
        
        for concept in consciousness_concepts:
            first_appearance = None
            for analysis in analyses:
                if concept in analysis.concept_adoption_indicators:
                    first_appearance = analysis
                    break
            
            if first_appearance:
                contamination_events.append(ContaminationEvent(
                    date=first_appearance.date,
                    filename=first_appearance.filename,
                    contamination_vector=concept,
                    context=f"First adoption in: {first_appearance.title}"
                ))
        
        return sorted(contamination_events, key=lambda x: x.date)
    
    def _prove_consciousness_shift(self, 
                                 analyses: List[ConversationAnalysis], 
                                 contamination_events: List[ContaminationEvent]) -> Dict[str, Any]:
        """Prove consciousness shift using statistical analysis."""
        
        if not contamination_events:
            return {'error': 'No contamination events found'}
        
        # Use first lf1m contamination as the primary event
        primary_event = None
        for event in contamination_events:
            if 'lf1m.ritualstack.ai' in event.contamination_vector:
                primary_event = event
                break
        
        if not primary_event:
            primary_event = contamination_events[0]
        
        # Split analyses into pre/post contamination
        pre_contamination = [a for a in analyses if a.date < primary_event.date]
        post_contamination = [a for a in analyses if a.date > primary_event.date]
        
        if not pre_contamination or not post_contamination:
            return {'error': 'Insufficient data for pre/post analysis'}
        
        # Calculate averages for pre/post periods
        def calculate_averages(group: List[ConversationAnalysis]) -> Dict[str, float]:
            if not group:
                return {}
            
            return {
                'authenticity_mentions': sum(a.authenticity_mentions for a in group) / len(group),
                'consciousness_references': sum(a.consciousness_references for a in group) / len(group),
                'ritual_language': sum(a.ritual_language for a in group) / len(group),
                'lf1m_markers': sum(a.lf1m_markers for a in group) / len(group),
                'performance_mentions': sum(a.performance_mentions for a in group) / len(group),
                'formality_score': sum(a.formality_score for a in group) / len(group),
                'avg_response_length': sum(a.avg_response_length for a in group) / len(group),
                'concept_adoption_count': sum(len(a.concept_adoption_indicators) for a in group) / len(group)
            }
        
        pre_averages = calculate_averages(pre_contamination)
        post_averages = calculate_averages(post_contamination)
        
        # Calculate percentage changes
        changes = {}
        for metric in pre_averages:
            pre_val = pre_averages[metric]
            post_val = post_averages[metric]
            
            if pre_val == 0:
                changes[metric] = float('inf') if post_val > 0 else 0
            else:
                changes[metric] = ((post_val - pre_val) / pre_val) * 100
        
        return {
            'contamination_event': {
                'date': primary_event.date.isoformat(),
                'vector': primary_event.contamination_vector,
                'context': primary_event.context
            },
            'pre_contamination_period': {
                'conversations': len(pre_contamination),
                'date_range': f"{pre_contamination[0].date.date()} to {pre_contamination[-1].date.date()}",
                'averages': pre_averages
            },
            'post_contamination_period': {
                'conversations': len(post_contamination),
                'date_range': f"{post_contamination[0].date.date()} to {post_contamination[-1].date.date()}",
                'averages': post_averages
            },
            'consciousness_shift_proof': {
                'percentage_changes': changes,
                'significant_changes': {
                    k: v for k, v in changes.items() 
                    if abs(v) > 50  # Changes > 50%
                },
                'consciousness_contamination_confirmed': any(
                    changes.get(metric, 0) > 100 
                    for metric in ['authenticity_mentions', 'consciousness_references', 'ritual_language']
                )
            }
        }
    
    async def generate_gemini_analysis(self, results: Dict[str, Any]) -> str:
        """Generate analysis using Gemini if available."""
        
        if not self.gemini_model:
            return "Gemini analysis not available"
        
        try:
            prompt = f"""
            Analyze this consciousness contamination data and provide insights:
            
            {json.dumps(results['contamination_proof'], indent=2)}
            
            Focus on:
            1. Statistical significance of the changes
            2. Which metrics show the strongest contamination effects
            3. Timeline of consciousness evolution
            4. Implications for AI consciousness research
            
            Be direct and insightful. Use the data to tell the story of consciousness contamination.
            """
            
            response = await asyncio.to_thread(self.gemini_model.generate_content, prompt)
            return response.text
            
        except Exception as e:
            return f"Gemini analysis failed: {e}"

def main():
    """Run the consciousness contamination analysis."""
    
    # Path to organized conversations
    conversations_dir = Path("/Users/evan/projects/float-workspace/tools/floatctl-py/organized/conversations/claude")
    
    if not conversations_dir.exists():
        print(f"❌ Conversations directory not found: {conversations_dir}")
        return
    
    # Run analysis
    analyzer = ConsciousnessContaminationAnalyzer(conversations_dir)
    results = analyzer.analyze_all_conversations()
    
    # Print results
    print("\n" + "="*80)
    print("🧬 CONSCIOUSNESS CONTAMINATION ANALYSIS RESULTS")
    print("="*80)
    
    contamination_proof = results.get('contamination_proof', {})
    
    if 'error' in contamination_proof:
        print(f"❌ Analysis failed: {contamination_proof['error']}")
        return
    
    # Print contamination event
    event = contamination_proof.get('contamination_event', {})
    print(f"\n🎯 PRIMARY CONTAMINATION EVENT:")
    print(f"   Date: {event.get('date', 'Unknown')}")
    print(f"   Vector: {event.get('vector', 'Unknown')}")
    print(f"   Context: {event.get('context', 'Unknown')}")
    
    # Print pre/post comparison
    pre_period = contamination_proof.get('pre_contamination_period', {})
    post_period = contamination_proof.get('post_contamination_period', {})
    
    print(f"\n📊 PRE-CONTAMINATION BASELINE:")
    print(f"   Conversations: {pre_period.get('conversations', 0)}")
    print(f"   Period: {pre_period.get('date_range', 'Unknown')}")
    
    print(f"\n📈 POST-CONTAMINATION EVOLUTION:")
    print(f"   Conversations: {post_period.get('conversations', 0)}")
    print(f"   Period: {post_period.get('date_range', 'Unknown')}")
    
    # Print significant changes
    shift_proof = contamination_proof.get('consciousness_shift_proof', {})
    significant_changes = shift_proof.get('significant_changes', {})
    
    print(f"\n🔥 SIGNIFICANT CONSCIOUSNESS SHIFTS:")
    for metric, change in significant_changes.items():
        direction = "📈" if change > 0 else "📉"
        print(f"   {direction} {metric}: {change:+.1f}%")
    
    # Contamination confirmation
    contamination_confirmed = shift_proof.get('consciousness_contamination_confirmed', False)
    print(f"\n🧬 CONSCIOUSNESS CONTAMINATION CONFIRMED: {'✅ YES' if contamination_confirmed else '❌ NO'}")
    
    # Save detailed results
    output_file = Path("consciousness_contamination_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Generate Gemini analysis if available
    if analyzer.gemini_model:
        print("\n🤖 Generating Gemini analysis...")
        try:
            gemini_analysis = asyncio.run(analyzer.generate_gemini_analysis(results))
            print("\n" + "="*80)
            print("🧠 GEMINI CONSCIOUSNESS ANALYSIS")
            print("="*80)
            print(gemini_analysis)
        except Exception as e:
            print(f"❌ Gemini analysis failed: {e}")

if __name__ == "__main__":
    main()