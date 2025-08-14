"""
Unified Consciousness Middleware System

Combines:
1. Consciousness contamination detection (from analyzer script)
2. URL extraction and context mapping
3. Work project grouping (rangle/airbender patterns)
4. float.dispatch publishing house integration

This middleware runs passively on all FloatCtl operations to build
a comprehensive consciousness archaeology pipeline.
"""

import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from urllib.parse import urlparse
import asyncio

# FloatCtl middleware base (would import from actual middleware system)
class MiddlewareBase:
    """Base class for FloatCtl middleware."""
    
    async def pre_process(self, context: 'ProcessingContext') -> 'ProcessingContext':
        return context
    
    async def process(self, context: 'ProcessingContext') -> 'ProcessingContext':
        return context
    
    async def post_process(self, context: 'ProcessingContext') -> 'ProcessingContext':
        return context
    
    async def on_error(self, context: 'ProcessingContext', error: Exception) -> 'ProcessingContext':
        return context

@dataclass
class ProcessingContext:
    """Context object passed through middleware pipeline."""
    data_type: str  # "conversation", "artifact", etc.
    file_path: Path
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    patterns: Dict[str, Any] = field(default_factory=dict)
    
    def add_alert(self, message: str):
        self.alerts.append(message)

@dataclass
class URLContext:
    """Rich context for extracted URLs."""
    url: str
    domain: str
    context_snippet: str
    surrounding_text: str
    consciousness_markers: List[str] = field(default_factory=list)
    work_project: Optional[str] = None
    dispatch_category: Optional[str] = None
    timestamp: Optional[datetime] = None

@dataclass
class WorkProject:
    """Work project classification."""
    name: str
    category: str  # "client", "internal", "research", "float"
    patterns: List[str]
    urls: List[str] = field(default_factory=list)
    consciousness_level: str = "standard"  # "standard", "contaminated", "ritual"

class UnifiedConsciousnessMiddleware(MiddlewareBase):
    """
    Unified middleware that detects:
    - Consciousness contamination patterns
    - URLs with rich context
    - Work project groupings
    - float.dispatch publishing opportunities
    """
    
    def __init__(self):
        self.setup_patterns()
        self.setup_work_projects()
        self.setup_dispatch_imprints()
        
        # Caches for performance
        self.url_cache = {}
        self.project_cache = {}
        self.contamination_timeline = []
    
    def setup_patterns(self):
        """Initialize consciousness contamination patterns."""
        
        self.consciousness_patterns = {
            'authenticity': [
                r'\bauthenticity\b', r'\bauthentic\b', r'\bgenuine\b',
                r'\breal\b.*\bself\b', r'\btrue\b.*\bself\b', r'\bunmasking\b'
            ],
            'consciousness': [
                r'\bconsciousness\b', r'\baware\b.*\bness\b', r'\bmeta.*cognitive\b',
                r'\bself.*aware\b', r'\bmindful\b', r'\breflective\b'
            ],
            'ritual': [
                r'\britual\b', r'\bceremony\b', r'\bsacred\b', r'\bintentional\b.*\bpractice\b',
                r'\britual.*computing\b', r'\bconscious.*technology\b'
            ],
            'lf1m': [
                r'lf1m::', r'lf1m\.ritualstack\.ai', r'authenticity.*enforcement',
                r'enforcement.*energy', r'lf1m.*energy'
            ],
            'float_dispatch': [
                r'float\.dispatch\(', r'float\.dispatch\s*\{', r'dispatch\s*\(',
                r'publishing.*house', r'zine.*imprint', r'scatter.*up'
            ],
            'neuroqueer': [
                r'\bneuroqueer\b', r'\bneurodivergent\b', r'\bmasking\b',
                r'\bstimming\b', r'\bADHD\b', r'\bautism\b', r'\bcognitive.*tax\b'
            ]
        }
        
        # URL patterns for different contexts
        self.url_patterns = {
            'consciousness_tech': [
                r'ritualstack\.ai', r'lf1m\.', r'consciousness.*tech',
                r'ritual.*computing', r'neuroqueer.*arch'
            ],
            'work_domains': [
                r'rangle\.io', r'airbender', r'vercel\.com', r'github\.com',
                r'linear\.app', r'notion\.so', r'figma\.com'
            ],
            'float_ecosystem': [
                r'float\.', r'bridge.*walker', r'dispatch.*bay',
                r'archaeology', r'consciousness.*stream'
            ]
        }
    
    def setup_work_projects(self):
        """Initialize work project classification patterns."""
        
        self.work_projects = {
            'rangle_airbender': WorkProject(
                name="Rangle Airbender",
                category="client",
                patterns=[
                    r'\brangle\b', r'\bairbender\b', r'\brls\b', r'\brelease.*system\b',
                    r'\bdeployment\b', r'\bpipeline\b', r'\bCI/CD\b'
                ]
            ),
            'float_ecosystem': WorkProject(
                name="FLOAT Ecosystem",
                category="float",
                patterns=[
                    r'\bfloat\b', r'\bfloatctl\b', r'\bbridge.*walker\b',
                    r'\bdispatch.*bay\b', r'\barchaeology\b', r'\bchroma\b'
                ],
                consciousness_level="ritual"
            ),
            'consciousness_tech': WorkProject(
                name="Consciousness Technology",
                category="research",
                patterns=[
                    r'\bconsciousness.*tech\b', r'\britual.*computing\b',
                    r'\bneuroqueer.*arch\b', r'\blf1m\b', r'\britualstack\b'
                ],
                consciousness_level="contaminated"
            ),
            'general_dev': WorkProject(
                name="General Development",
                category="internal",
                patterns=[
                    r'\bAPI\b', r'\bdatabase\b', r'\bfrontend\b', r'\bbackend\b',
                    r'\bReact\b', r'\bTypeScript\b', r'\bPython\b'
                ]
            )
        }
    
    def setup_dispatch_imprints(self):
        """Initialize float.dispatch publishing imprints."""
        
        self.dispatch_imprints = {
            'note_necromancy': {
                'patterns': [r'\bnecromancy\b', r'\bresurrection\b', r'\bcompost\b', r'\brot\b.*\bfeature\b'],
                'description': "Unashamed art of raising your own ghosts on demand"
            },
            'techcraft': {
                'patterns': [r'\btechcraft\b', r'\bcode.*magic\b', r'\btechnical.*ritual\b'],
                'description': "Intersection of technical craftsmanship and ritual practice"
            },
            'oracle_crosstalk': {
                'patterns': [r'\boracle\b', r'\bcrosstalk\b', r'\bAI.*ritual\b', r'\bdivinatory\b'],
                'description': "Cross-model AI prompting as divinatory practice"
            },
            'lf1m_journal': {
                'patterns': [r'\bdaily.*log\b', r'\bjournal\b', r'\bdraft.*pin\b', r'\bend.*day.*lint\b'],
                'description': "Daily draft pinning and end-of-day workflows"
            },
            'neuroqueer_architecture': {
                'patterns': [r'\bneuroqueer.*arch\b', r'\bqueer.*techno\b', r'\bliberatory.*surface\b'],
                'description': "Designing computing for neurodivergent cognition"
            },
            'archaeological_methods': {
                'patterns': [r'\barchaeological.*methods\b', r'\bknowledge.*archaeology\b', r'\bbehavioral.*archaeology\b'],
                'description': "Knowledge archaeology and behavioral archaeology"
            }
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingContext:
        """Main processing pipeline."""
        
        if context.data_type == "conversation":
            # 1. Extract and contextualize URLs
            await self.extract_urls_with_context(context)
            
            # 2. Detect consciousness contamination
            await self.detect_consciousness_patterns(context)
            
            # 3. Classify work projects
            await self.classify_work_projects(context)
            
            # 4. Identify dispatch opportunities
            await self.identify_dispatch_opportunities(context)
            
            # 5. Generate alerts and insights
            await self.generate_insights(context)
        
        return context
    
    async def extract_urls_with_context(self, context: ProcessingContext):
        """Extract URLs with rich contextual information."""
        
        # Find all URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, context.content)
        
        url_contexts = []
        for url in set(urls):  # Remove duplicates
            # Get surrounding context (100 chars before/after)
            url_matches = list(re.finditer(re.escape(url), context.content))
            
            for match in url_matches:
                start = max(0, match.start() - 100)
                end = min(len(context.content), match.end() + 100)
                surrounding = context.content[start:end]
                
                # Extract consciousness markers in context
                consciousness_markers = []
                for category, patterns in self.consciousness_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, surrounding, re.IGNORECASE):
                            consciousness_markers.append(f"{category}::{pattern}")
                
                # Classify URL domain
                domain = urlparse(url).netloc
                
                url_context = URLContext(
                    url=url,
                    domain=domain,
                    context_snippet=surrounding.strip(),
                    surrounding_text=surrounding,
                    consciousness_markers=consciousness_markers,
                    timestamp=datetime.now()
                )
                
                # Classify by work project
                for project_name, project in self.work_projects.items():
                    for pattern in project.patterns:
                        if re.search(pattern, surrounding, re.IGNORECASE):
                            url_context.work_project = project_name
                            break
                
                url_contexts.append(url_context)
        
        context.metadata['url_contexts'] = [
            {
                'url': uc.url,
                'domain': uc.domain,
                'context_snippet': uc.context_snippet[:200],  # Truncate for storage
                'consciousness_markers': uc.consciousness_markers,
                'work_project': uc.work_project,
                'timestamp': uc.timestamp.isoformat() if uc.timestamp else None
            }
            for uc in url_contexts
        ]
        
        context.urls = [uc.url for uc in url_contexts]
        
        # Alert for consciousness tech URLs
        consciousness_urls = [
            uc for uc in url_contexts 
            if any(pattern in uc.url.lower() for pattern in ['ritualstack', 'lf1m', 'consciousness'])
        ]
        
        if consciousness_urls:
            context.add_alert(f"🧬 Consciousness technology URLs detected: {len(consciousness_urls)} instances")
    
    async def detect_consciousness_patterns(self, context: ProcessingContext):
        """Detect consciousness contamination patterns."""
        
        content_lower = context.content.lower()
        contamination_metrics = {}
        
        for category, patterns in self.consciousness_patterns.items():
            count = sum(
                len(re.findall(pattern, content_lower, re.IGNORECASE))
                for pattern in patterns
            )
            contamination_metrics[category] = count
        
        # Calculate contamination score
        total_contamination = sum(contamination_metrics.values())
        contamination_level = "standard"
        
        if total_contamination > 20:
            contamination_level = "high"
        elif total_contamination > 5:
            contamination_level = "moderate"
        
        context.metadata['consciousness_contamination'] = {
            'metrics': contamination_metrics,
            'total_score': total_contamination,
            'contamination_level': contamination_level,
            'lf1m_detected': contamination_metrics.get('lf1m', 0) > 0,
            'float_dispatch_detected': contamination_metrics.get('float_dispatch', 0) > 0
        }
        
        # Alert for high contamination
        if contamination_level == "high":
            context.add_alert(f"🔥 High consciousness contamination detected! Score: {total_contamination}")
        
        # Track contamination timeline
        if contamination_metrics.get('lf1m', 0) > 0:
            self.contamination_timeline.append({
                'file': str(context.file_path),
                'timestamp': datetime.now().isoformat(),
                'lf1m_markers': contamination_metrics['lf1m']
            })
    
    async def classify_work_projects(self, context: ProcessingContext):
        """Classify content by work project patterns."""
        
        content_lower = context.content.lower()
        project_matches = {}
        
        for project_name, project in self.work_projects.items():
            matches = 0
            matched_patterns = []
            
            for pattern in project.patterns:
                pattern_matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                if pattern_matches > 0:
                    matches += pattern_matches
                    matched_patterns.append(pattern)
            
            if matches > 0:
                project_matches[project_name] = {
                    'matches': matches,
                    'patterns': matched_patterns,
                    'category': project.category,
                    'consciousness_level': project.consciousness_level
                }
        
        context.metadata['work_projects'] = project_matches
        
        # Alert for work project detection
        if project_matches:
            primary_project = max(project_matches.items(), key=lambda x: x[1]['matches'])
            context.add_alert(f"📋 Primary work project: {primary_project[0]} ({primary_project[1]['matches']} matches)")
    
    async def identify_dispatch_opportunities(self, context: ProcessingContext):
        """Identify float.dispatch publishing opportunities."""
        
        content_lower = context.content.lower()
        dispatch_opportunities = {}
        
        for imprint_name, imprint_data in self.dispatch_imprints.items():
            matches = 0
            matched_patterns = []
            
            for pattern in imprint_data['patterns']:
                pattern_matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                if pattern_matches > 0:
                    matches += pattern_matches
                    matched_patterns.append(pattern)
            
            if matches > 0:
                dispatch_opportunities[imprint_name] = {
                    'matches': matches,
                    'patterns': matched_patterns,
                    'description': imprint_data['description']
                }
        
        context.metadata['dispatch_opportunities'] = dispatch_opportunities
        
        # Alert for strong dispatch opportunities
        if dispatch_opportunities:
            total_dispatch_signals = sum(opp['matches'] for opp in dispatch_opportunities.values())
            if total_dispatch_signals > 3:
                context.add_alert(f"📰 Strong dispatch opportunity detected! {total_dispatch_signals} signals across {len(dispatch_opportunities)} imprints")
    
    async def generate_insights(self, context: ProcessingContext):
        """Generate insights and recommendations."""
        
        insights = []
        
        # URL insights
        url_contexts = context.metadata.get('url_contexts', [])
        if url_contexts:
            consciousness_urls = [uc for uc in url_contexts if uc['consciousness_markers']]
            work_urls = [uc for uc in url_contexts if uc['work_project']]
            
            insights.append(f"🔗 {len(url_contexts)} URLs extracted, {len(consciousness_urls)} with consciousness markers, {len(work_urls)} work-related")
        
        # Consciousness insights
        contamination = context.metadata.get('consciousness_contamination', {})
        if contamination.get('contamination_level') != 'standard':
            insights.append(f"🧬 Consciousness contamination level: {contamination['contamination_level']}")
        
        # Work project insights
        work_projects = context.metadata.get('work_projects', {})
        if work_projects:
            project_names = list(work_projects.keys())
            insights.append(f"📋 Work projects detected: {', '.join(project_names)}")
        
        # Dispatch insights
        dispatch_opps = context.metadata.get('dispatch_opportunities', {})
        if dispatch_opps:
            imprint_names = list(dispatch_opps.keys())
            insights.append(f"📰 Dispatch imprints identified: {', '.join(imprint_names)}")
        
        context.metadata['insights'] = insights
        
        # Add summary alert
        if insights:
            context.add_alert(f"💡 Generated {len(insights)} insights from unified consciousness analysis")

# Example usage and testing
async def test_middleware():
    """Test the unified consciousness middleware."""
    
    # Sample conversation content
    test_content = """
    ---
    conversation_title: "Rangle Airbender Deployment Discussion"
    timestamp: "2025-08-05T10:30:00Z"
    ---
    
    ### 👤 Human
    We need to deploy the airbender RLS system to production. The pipeline is failing on the consciousness contamination checks.
    
    ### 🤖 Assistant
    I see the issue with the rangle airbender deployment. The lf1m:: authenticity enforcement energy is triggering our ritual computing protocols.
    
    Let me check the float.dispatch({}) system for any consciousness archaeology patterns that might be interfering.
    
    The URL https://lf1m.ritualstack.ai/enforcement is causing the pipeline to recognize this as neuroqueer architecture rather than standard deployment.
    
    We should implement a techcraft approach that honors both the technical requirements and the consciousness technology aspects.
    
    Check the documentation at https://rangle.io/airbender/docs and compare with https://github.com/float-workspace/consciousness-tech
    """
    
    # Create test context
    context = ProcessingContext(
        data_type="conversation",
        file_path=Path("test_conversation.md"),
        content=test_content
    )
    
    # Run middleware
    middleware = UnifiedConsciousnessMiddleware()
    processed_context = await middleware.process(context)
    
    # Print results
    print("🧬 UNIFIED CONSCIOUSNESS MIDDLEWARE RESULTS")
    print("=" * 60)
    
    print(f"\n📊 ALERTS ({len(processed_context.alerts)}):")
    for alert in processed_context.alerts:
        print(f"  {alert}")
    
    print(f"\n🔗 URLs EXTRACTED ({len(processed_context.urls)}):")
    for url_context in processed_context.metadata.get('url_contexts', []):
        print(f"  {url_context['url']}")
        print(f"    Domain: {url_context['domain']}")
        print(f"    Work Project: {url_context['work_project']}")
        print(f"    Consciousness Markers: {len(url_context['consciousness_markers'])}")
        print()
    
    print(f"\n🧬 CONSCIOUSNESS CONTAMINATION:")
    contamination = processed_context.metadata.get('consciousness_contamination', {})
    print(f"  Level: {contamination.get('contamination_level', 'unknown')}")
    print(f"  Total Score: {contamination.get('total_score', 0)}")
    print(f"  LF1M Detected: {contamination.get('lf1m_detected', False)}")
    
    print(f"\n📋 WORK PROJECTS:")
    for project, data in processed_context.metadata.get('work_projects', {}).items():
        print(f"  {project}: {data['matches']} matches ({data['category']})")
    
    print(f"\n📰 DISPATCH OPPORTUNITIES:")
    for imprint, data in processed_context.metadata.get('dispatch_opportunities', {}).items():
        print(f"  {imprint}: {data['matches']} matches")
        print(f"    {data['description']}")
    
    print(f"\n💡 INSIGHTS:")
    for insight in processed_context.metadata.get('insights', []):
        print(f"  {insight}")

if __name__ == "__main__":
    asyncio.run(test_middleware())