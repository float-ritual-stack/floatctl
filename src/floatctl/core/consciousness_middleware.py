"""
Consciousness Middleware for FloatCtl

Integrates consciousness contamination detection, URL extraction,
work project classification, and float.dispatch opportunities
into the FloatCtl processing pipeline.
"""

import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from urllib.parse import urlparse

from floatctl.core.database import DatabaseManager
from floatctl.core.logging import log_file_operation

@dataclass
class ConsciousnessAnalysis:
    """Results of consciousness analysis for a single conversation."""
    file_path: str
    conversation_id: str
    conversation_title: str
    
    # Consciousness contamination metrics
    consciousness_metrics: Dict[str, int] = field(default_factory=dict)
    contamination_level: str = "standard"
    contamination_score: int = 0
    
    # URL analysis
    urls: List[Dict[str, Any]] = field(default_factory=list)
    consciousness_urls: int = 0
    work_urls: int = 0
    
    # Work project classification
    work_projects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    primary_project: Optional[str] = None
    
    # Dispatch opportunities
    dispatch_opportunities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    dispatch_score: int = 0
    
    # Alerts and insights
    alerts: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    
    # Metadata
    processed_at: datetime = field(default_factory=datetime.now)

class ConsciousnessMiddleware:
    """Middleware for consciousness analysis in FloatCtl pipeline."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.setup_patterns()
        self.setup_work_projects()
        self.setup_dispatch_imprints()
        self.setup_database()
        
        # Performance caches
        self.url_cache = {}
        self.project_cache = {}
    
    def setup_database(self):
        """Setup database tables for consciousness analysis results."""
        
        # Create consciousness analysis table
        self.db_manager.execute_sql("""
            CREATE TABLE IF NOT EXISTS consciousness_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                conversation_id TEXT,
                conversation_title TEXT,
                contamination_level TEXT,
                contamination_score INTEGER,
                consciousness_urls INTEGER DEFAULT 0,
                work_urls INTEGER DEFAULT 0,
                primary_project TEXT,
                dispatch_score INTEGER DEFAULT 0,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_path, conversation_id)
            )
        """)
        
        # Create consciousness metrics table
        self.db_manager.execute_sql("""
            CREATE TABLE IF NOT EXISTS consciousness_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                metric_type TEXT,
                metric_value INTEGER,
                FOREIGN KEY (analysis_id) REFERENCES consciousness_analysis (id)
            )
        """)
        
        # Create URL contexts table
        self.db_manager.execute_sql("""
            CREATE TABLE IF NOT EXISTS url_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                url TEXT,
                domain TEXT,
                context_snippet TEXT,
                work_project TEXT,
                consciousness_markers TEXT, -- JSON array
                FOREIGN KEY (analysis_id) REFERENCES consciousness_analysis (id)
            )
        """)
        
        # Create work projects table
        self.db_manager.execute_sql("""
            CREATE TABLE IF NOT EXISTS work_project_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                project_name TEXT,
                project_category TEXT,
                match_count INTEGER,
                matched_patterns TEXT, -- JSON array
                FOREIGN KEY (analysis_id) REFERENCES consciousness_analysis (id)
            )
        """)
        
        # Create dispatch opportunities table
        self.db_manager.execute_sql("""
            CREATE TABLE IF NOT EXISTS dispatch_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                imprint_name TEXT,
                match_count INTEGER,
                matched_patterns TEXT, -- JSON array
                description TEXT,
                FOREIGN KEY (analysis_id) REFERENCES consciousness_analysis (id)
            )
        """)
        
        # Create alerts table
        self.db_manager.execute_sql("""
            CREATE TABLE IF NOT EXISTS consciousness_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                alert_type TEXT,
                alert_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES consciousness_analysis (id)
            )
        """)
    
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
    
    def setup_work_projects(self):
        """Initialize work project classification patterns."""
        
        self.work_projects = {
            'rangle_airbender': {
                'name': "Rangle Airbender",
                'category': "client",
                'patterns': [
                    r'\brangle\b', r'\bairbender\b', r'\brls\b', r'\brelease.*system\b',
                    r'\bdeployment\b', r'\bpipeline\b', r'\bCI/CD\b'
                ],
                'consciousness_level': "standard"
            },
            'float_ecosystem': {
                'name': "FLOAT Ecosystem",
                'category': "float",
                'patterns': [
                    r'\bfloat\b', r'\bfloatctl\b', r'\bbridge.*walker\b',
                    r'\bdispatch.*bay\b', r'\barchaeology\b', r'\bchroma\b'
                ],
                'consciousness_level': "ritual"
            },
            'consciousness_tech': {
                'name': "Consciousness Technology",
                'category': "research",
                'patterns': [
                    r'\bconsciousness.*tech\b', r'\britual.*computing\b',
                    r'\bneuroqueer.*arch\b', r'\blf1m\b', r'\britualstack\b'
                ],
                'consciousness_level': "contaminated"
            },
            'general_dev': {
                'name': "General Development",
                'category': "internal",
                'patterns': [
                    r'\bAPI\b', r'\bdatabase\b', r'\bfrontend\b', r'\bbackend\b',
                    r'\bReact\b', r'\bTypeScript\b', r'\bPython\b'
                ],
                'consciousness_level': "standard"
            }
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
    
    def analyze_conversation(self, file_path: Path, conversation_data: Dict[str, Any], content: str) -> ConsciousnessAnalysis:
        """Analyze a single conversation for consciousness patterns."""
        
        analysis = ConsciousnessAnalysis(
            file_path=str(file_path),
            conversation_id=conversation_data.get("uuid", "unknown"),
            conversation_title=conversation_data.get("name", file_path.stem)
        )
        
        # Analyze consciousness patterns
        self._analyze_consciousness_patterns(content, analysis)
        
        # Extract and analyze URLs
        self._analyze_urls(content, analysis)
        
        # Classify work projects
        self._classify_work_projects(content, analysis)
        
        # Identify dispatch opportunities
        self._identify_dispatch_opportunities(content, analysis)
        
        # Generate insights and alerts
        self._generate_insights(analysis)
        
        return analysis
    
    def _analyze_consciousness_patterns(self, content: str, analysis: ConsciousnessAnalysis):
        """Analyze consciousness contamination patterns."""
        
        content_lower = content.lower()
        
        for category, patterns in self.consciousness_patterns.items():
            count = sum(
                len(re.findall(pattern, content_lower, re.IGNORECASE))
                for pattern in patterns
            )
            analysis.consciousness_metrics[category] = count
        
        # Calculate contamination score and level
        analysis.contamination_score = sum(analysis.consciousness_metrics.values())
        
        if analysis.contamination_score > 20:
            analysis.contamination_level = "high"
        elif analysis.contamination_score > 5:
            analysis.contamination_level = "moderate"
        else:
            analysis.contamination_level = "standard"
        
        # Generate contamination alerts
        if analysis.contamination_level == "high":
            analysis.alerts.append(f"🔥 High consciousness contamination detected! Score: {analysis.contamination_score}")
        
        if analysis.consciousness_metrics.get('lf1m', 0) > 0:
            analysis.alerts.append(f"🧬 LF1M contamination detected: {analysis.consciousness_metrics['lf1m']} markers")
    
    def _analyze_urls(self, content: str, analysis: ConsciousnessAnalysis):
        """Extract and analyze URLs with context."""
        
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content)
        
        for url in set(urls):  # Remove duplicates
            # Get surrounding context
            url_matches = list(re.finditer(re.escape(url), content))
            
            for match in url_matches:
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                surrounding = content[start:end]
                
                # Extract consciousness markers in context
                consciousness_markers = []
                for category, patterns in self.consciousness_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, surrounding, re.IGNORECASE):
                            consciousness_markers.append(f"{category}::{pattern}")
                
                # Classify by work project
                work_project = None
                for project_name, project_data in self.work_projects.items():
                    for pattern in project_data['patterns']:
                        if re.search(pattern, surrounding, re.IGNORECASE):
                            work_project = project_name
                            break
                
                domain = urlparse(url).netloc
                
                url_data = {
                    'url': url,
                    'domain': domain,
                    'context_snippet': surrounding.strip()[:200],  # Truncate for storage
                    'consciousness_markers': consciousness_markers,
                    'work_project': work_project
                }
                
                analysis.urls.append(url_data)
                
                # Count special URL types
                if consciousness_markers:
                    analysis.consciousness_urls += 1
                if work_project:
                    analysis.work_urls += 1
        
        # Generate URL alerts
        if analysis.consciousness_urls > 0:
            analysis.alerts.append(f"🔗 Consciousness technology URLs detected: {analysis.consciousness_urls} instances")
    
    def _classify_work_projects(self, content: str, analysis: ConsciousnessAnalysis):
        """Classify content by work project patterns."""
        
        content_lower = content.lower()
        
        for project_name, project_data in self.work_projects.items():
            matches = 0
            matched_patterns = []
            
            for pattern in project_data['patterns']:
                pattern_matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                if pattern_matches > 0:
                    matches += pattern_matches
                    matched_patterns.append(pattern)
            
            if matches > 0:
                analysis.work_projects[project_name] = {
                    'matches': matches,
                    'patterns': matched_patterns,
                    'category': project_data['category'],
                    'consciousness_level': project_data['consciousness_level']
                }
        
        # Determine primary project
        if analysis.work_projects:
            analysis.primary_project = max(
                analysis.work_projects.items(), 
                key=lambda x: x[1]['matches']
            )[0]
            
            analysis.alerts.append(f"📋 Primary work project: {analysis.primary_project} ({analysis.work_projects[analysis.primary_project]['matches']} matches)")
    
    def _identify_dispatch_opportunities(self, content: str, analysis: ConsciousnessAnalysis):
        """Identify float.dispatch publishing opportunities."""
        
        content_lower = content.lower()
        
        for imprint_name, imprint_data in self.dispatch_imprints.items():
            matches = 0
            matched_patterns = []
            
            for pattern in imprint_data['patterns']:
                pattern_matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                if pattern_matches > 0:
                    matches += pattern_matches
                    matched_patterns.append(pattern)
            
            if matches > 0:
                analysis.dispatch_opportunities[imprint_name] = {
                    'matches': matches,
                    'patterns': matched_patterns,
                    'description': imprint_data['description']
                }
        
        # Calculate dispatch score
        analysis.dispatch_score = sum(
            opp['matches'] for opp in analysis.dispatch_opportunities.values()
        )
        
        # Generate dispatch alerts
        if analysis.dispatch_score > 3:
            imprint_count = len(analysis.dispatch_opportunities)
            analysis.alerts.append(f"📰 Strong dispatch opportunity detected! {analysis.dispatch_score} signals across {imprint_count} imprints")
    
    def _generate_insights(self, analysis: ConsciousnessAnalysis):
        """Generate insights and recommendations."""
        
        # URL insights
        if analysis.urls:
            analysis.insights.append(f"🔗 {len(analysis.urls)} URLs extracted, {analysis.consciousness_urls} with consciousness markers, {analysis.work_urls} work-related")
        
        # Consciousness insights
        if analysis.contamination_level != 'standard':
            analysis.insights.append(f"🧬 Consciousness contamination level: {analysis.contamination_level}")
        
        # Work project insights
        if analysis.work_projects:
            project_names = list(analysis.work_projects.keys())
            analysis.insights.append(f"📋 Work projects detected: {', '.join(project_names)}")
        
        # Dispatch insights
        if analysis.dispatch_opportunities:
            imprint_names = list(analysis.dispatch_opportunities.keys())
            analysis.insights.append(f"📰 Dispatch imprints identified: {', '.join(imprint_names)}")
    
    def save_analysis(self, analysis: ConsciousnessAnalysis) -> int:
        """Save consciousness analysis to database."""
        
        # Insert main analysis record
        cursor = self.db_manager.execute_sql("""
            INSERT OR REPLACE INTO consciousness_analysis 
            (file_path, conversation_id, conversation_title, contamination_level, 
             contamination_score, consciousness_urls, work_urls, primary_project, 
             dispatch_score, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis.file_path,
            analysis.conversation_id,
            analysis.conversation_title,
            analysis.contamination_level,
            analysis.contamination_score,
            analysis.consciousness_urls,
            analysis.work_urls,
            analysis.primary_project,
            analysis.dispatch_score,
            analysis.processed_at
        ))
        
        analysis_id = cursor.lastrowid
        
        # Save consciousness metrics
        for metric_type, metric_value in analysis.consciousness_metrics.items():
            self.db_manager.execute_sql("""
                INSERT INTO consciousness_metrics (analysis_id, metric_type, metric_value)
                VALUES (?, ?, ?)
            """, (analysis_id, metric_type, metric_value))
        
        # Save URL contexts
        for url_data in analysis.urls:
            self.db_manager.execute_sql("""
                INSERT INTO url_contexts 
                (analysis_id, url, domain, context_snippet, work_project, consciousness_markers)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                analysis_id,
                url_data['url'],
                url_data['domain'],
                url_data['context_snippet'],
                url_data['work_project'],
                json.dumps(url_data['consciousness_markers'])
            ))
        
        # Save work project matches
        for project_name, project_data in analysis.work_projects.items():
            self.db_manager.execute_sql("""
                INSERT INTO work_project_matches 
                (analysis_id, project_name, project_category, match_count, matched_patterns)
                VALUES (?, ?, ?, ?, ?)
            """, (
                analysis_id,
                project_name,
                project_data['category'],
                project_data['matches'],
                json.dumps(project_data['patterns'])
            ))
        
        # Save dispatch opportunities
        for imprint_name, imprint_data in analysis.dispatch_opportunities.items():
            self.db_manager.execute_sql("""
                INSERT INTO dispatch_opportunities 
                (analysis_id, imprint_name, match_count, matched_patterns, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                analysis_id,
                imprint_name,
                imprint_data['matches'],
                json.dumps(imprint_data['patterns']),
                imprint_data['description']
            ))
        
        # Save alerts
        for alert in analysis.alerts:
            self.db_manager.execute_sql("""
                INSERT INTO consciousness_alerts (analysis_id, alert_type, alert_message)
                VALUES (?, ?, ?)
            """, (analysis_id, "middleware", alert))
        
        return analysis_id
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all consciousness analyses."""
        
        cursor = self.db_manager.execute_sql("""
            SELECT 
                COUNT(*) as total_analyses,
                COUNT(CASE WHEN contamination_level = 'high' THEN 1 END) as high_contamination,
                COUNT(CASE WHEN contamination_level = 'moderate' THEN 1 END) as moderate_contamination,
                COUNT(CASE WHEN consciousness_urls > 0 THEN 1 END) as conversations_with_consciousness_urls,
                COUNT(CASE WHEN dispatch_score > 3 THEN 1 END) as strong_dispatch_opportunities,
                AVG(contamination_score) as avg_contamination_score,
                AVG(dispatch_score) as avg_dispatch_score
            FROM consciousness_analysis
        """)
        
        result = cursor.fetchone()
        
        return {
            'total_analyses': result[0],
            'high_contamination': result[1],
            'moderate_contamination': result[2],
            'conversations_with_consciousness_urls': result[3],
            'strong_dispatch_opportunities': result[4],
            'avg_contamination_score': round(result[5] or 0, 2),
            'avg_dispatch_score': round(result[6] or 0, 2)
        }
    
    def export_analysis_results(self, output_path: Path) -> None:
        """Export all consciousness analysis results to JSON."""
        
        # Get all analyses with related data
        cursor = self.db_manager.execute_sql("""
            SELECT 
                ca.*,
                GROUP_CONCAT(cm.metric_type || ':' || cm.metric_value) as metrics,
                GROUP_CONCAT(DISTINCT uc.url) as urls,
                GROUP_CONCAT(DISTINCT wpm.project_name) as projects,
                GROUP_CONCAT(DISTINCT do.imprint_name) as imprints
            FROM consciousness_analysis ca
            LEFT JOIN consciousness_metrics cm ON ca.id = cm.analysis_id
            LEFT JOIN url_contexts uc ON ca.id = uc.analysis_id
            LEFT JOIN work_project_matches wpm ON ca.id = wpm.analysis_id
            LEFT JOIN dispatch_opportunities do ON ca.id = do.analysis_id
            GROUP BY ca.id
            ORDER BY ca.processed_at DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'file_path': row[1],
                'conversation_id': row[2],
                'conversation_title': row[3],
                'contamination_level': row[4],
                'contamination_score': row[5],
                'consciousness_urls': row[6],
                'work_urls': row[7],
                'primary_project': row[8],
                'dispatch_score': row[9],
                'processed_at': row[10],
                'metrics': row[11],
                'urls': row[12],
                'projects': row[13],
                'imprints': row[14]
            })
        
        with open(output_path, 'w') as f:
            json.dump({
                'summary': self.get_analysis_summary(),
                'analyses': results,
                'exported_at': datetime.now().isoformat()
            }, f, indent=2)