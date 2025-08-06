"""
Workflow Intelligence for FloatCtl

Practical daily workflow queries that actually help with human memory:
- What did I do last week?
- Action items from Nick
- Current priorities
- Meeting follow-ups
- Forgotten tasks

This bridges consciousness archaeology with actual productivity needs.
"""

import re
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from floatctl.core.database import DatabaseManager
from floatctl.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ActionItem:
    """An action item extracted from conversations."""
    content: str
    source: str  # "nick", "meeting", "self", etc.
    priority: str  # "high", "medium", "low"
    status: str  # "open", "completed", "blocked"
    due_date: Optional[datetime] = None
    context: str = ""
    conversation_id: str = ""
    conversation_title: str = ""
    extracted_at: datetime = field(default_factory=datetime.now)

@dataclass
class WorkActivity:
    """Work activity extracted from conversations."""
    activity: str
    project: str
    date: datetime
    duration_estimate: Optional[str] = None
    outcome: Optional[str] = None
    conversation_id: str = ""
    conversation_title: str = ""

class WorkflowIntelligence:
    """Extract practical workflow intelligence from consciousness analysis."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.setup_patterns()
        self.setup_database()
    
    def setup_patterns(self):
        """Initialize workflow extraction patterns."""
        
        # Action item patterns
        self.action_patterns = {
            'explicit_todos': [
                r'TODO:?\s*(.+)',
                r'Action item:?\s*(.+)',
                r'Need to:?\s*(.+)',
                r'Should:?\s*(.+)',
                r'Must:?\s*(.+)',
                r'Remember to:?\s*(.+)',
                r'Follow up:?\s*(.+)',
            ],
            'nick_requests': [
                r'Nick.*(?:said|asked|wants|needs|requested):?\s*(.+)',
                r'From Nick:?\s*(.+)',
                r'Nick.*action:?\s*(.+)',
                r'Nick.*follow.?up:?\s*(.+)',
            ],
            'meeting_actions': [
                r'Meeting.*action:?\s*(.+)',
                r'Decided:?\s*(.+)',
                r'Agreed:?\s*(.+)',
                r'Next steps?:?\s*(.+)',
            ],
            'priority_indicators': [
                r'Priority:?\s*(.+)',
                r'Important:?\s*(.+)',
                r'Urgent:?\s*(.+)',
                r'Critical:?\s*(.+)',
                r'ASAP:?\s*(.+)',
            ]
        }
        
        # Work activity patterns
        self.activity_patterns = {
            'completed_work': [
                r'Completed:?\s*(.+)',
                r'Finished:?\s*(.+)',
                r'Done:?\s*(.+)',
                r'Shipped:?\s*(.+)',
                r'Deployed:?\s*(.+)',
                r'Fixed:?\s*(.+)',
                r'Implemented:?\s*(.+)',
            ],
            'in_progress': [
                r'Working on:?\s*(.+)',
                r'Currently:?\s*(.+)',
                r'In progress:?\s*(.+)',
                r'Building:?\s*(.+)',
                r'Developing:?\s*(.+)',
            ],
            'blocked_work': [
                r'Blocked by:?\s*(.+)',
                r'Waiting for:?\s*(.+)',
                r'Stuck on:?\s*(.+)',
                r'Can\'t proceed:?\s*(.+)',
            ]
        }
        
        # Priority extraction patterns
        self.priority_patterns = {
            'high': [
                r'\b(?:urgent|critical|asap|high.?priority|important)\b',
                r'\b(?:deadline|due|emergency)\b',
            ],
            'medium': [
                r'\b(?:medium.?priority|should|need to)\b',
                r'\b(?:follow.?up|next week)\b',
            ],
            'low': [
                r'\b(?:low.?priority|eventually|someday|nice.?to.?have)\b',
                r'\b(?:when time|if possible)\b',
            ]
        }
        
        # People patterns for attribution
        self.people_patterns = {
            'nick': [r'\bnick\b', r'\bnicholas\b'],
            'evan': [r'\bevan\b', r'\bme\b', r'\bi\b'],
            'ditmar': [r'\bditmar\b'],
            'tom': [r'\btom\b'],
            'team': [r'\bteam\b', r'\bwe\b', r'\bus\b'],
        }
    
    def setup_database(self):
        """Setup database tables for workflow intelligence."""
        
        # Use raw SQL execution through the engine
        with self.db_manager.get_session() as session:
            # Action items table
            session.execute("""
                CREATE TABLE IF NOT EXISTS workflow_action_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    source TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'open',
                    due_date TIMESTAMP,
                    context TEXT,
                    conversation_id TEXT,
                    conversation_title TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Work activities table
            session.execute("""
                CREATE TABLE IF NOT EXISTS workflow_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity TEXT NOT NULL,
                    project TEXT,
                    activity_date TIMESTAMP,
                    duration_estimate TEXT,
                    outcome TEXT,
                    conversation_id TEXT,
                    conversation_title TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Current priorities table
            session.execute("""
                CREATE TABLE IF NOT EXISTS workflow_priorities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    priority_text TEXT NOT NULL,
                    priority_level TEXT,
                    project TEXT,
                    status TEXT DEFAULT 'active',
                    conversation_id TEXT,
                    conversation_title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            session.commit()
    
    def extract_workflow_intelligence(self, conversation_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Extract workflow intelligence from a conversation."""
        
        conversation_id = conversation_data.get("uuid", "unknown")
        conversation_title = conversation_data.get("name", "Unknown")
        conversation_date = self._parse_conversation_date(conversation_data)
        
        # Extract action items
        action_items = self._extract_action_items(content, conversation_id, conversation_title)
        
        # Extract work activities
        activities = self._extract_work_activities(content, conversation_id, conversation_title, conversation_date)
        
        # Extract priorities
        priorities = self._extract_priorities(content, conversation_id, conversation_title)
        
        # Save to database
        self._save_action_items(action_items)
        self._save_activities(activities)
        self._save_priorities(priorities)
        
        return {
            'action_items': len(action_items),
            'activities': len(activities),
            'priorities': len(priorities),
            'conversation_id': conversation_id,
            'conversation_title': conversation_title
        }
    
    def _extract_action_items(self, content: str, conversation_id: str, conversation_title: str) -> List[ActionItem]:
        """Extract action items from conversation content."""
        
        action_items = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Check each action pattern category
            for category, patterns in self.action_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, line_clean, re.IGNORECASE)
                    
                    for match in matches:
                        action_content = match.group(1).strip()
                        if len(action_content) < 5:  # Skip very short matches
                            continue
                        
                        # Determine source
                        source = self._determine_source(line_clean, category)
                        
                        # Determine priority
                        priority = self._determine_priority(line_clean)
                        
                        # Get context (surrounding lines)
                        context_lines = []
                        for i in range(max(0, line_num-2), min(len(lines), line_num+3)):
                            if i != line_num:
                                context_lines.append(lines[i].strip())
                        context = ' '.join(context_lines)[:200]
                        
                        action_item = ActionItem(
                            content=action_content,
                            source=source,
                            priority=priority,
                            status='open',
                            context=context,
                            conversation_id=conversation_id,
                            conversation_title=conversation_title
                        )
                        
                        action_items.append(action_item)
        
        return action_items
    
    def _extract_work_activities(self, content: str, conversation_id: str, conversation_title: str, conversation_date: datetime) -> List[WorkActivity]:
        """Extract work activities from conversation content."""
        
        activities = []
        
        for category, patterns in self.activity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    activity_text = match.group(1).strip()
                    if len(activity_text) < 5:
                        continue
                    
                    # Determine project from context
                    project = self._determine_project_from_context(match.string, match.start())
                    
                    # Determine outcome based on category
                    outcome = {
                        'completed_work': 'completed',
                        'in_progress': 'in_progress',
                        'blocked_work': 'blocked'
                    }.get(category, 'unknown')
                    
                    activity = WorkActivity(
                        activity=activity_text,
                        project=project,
                        date=conversation_date,
                        outcome=outcome,
                        conversation_id=conversation_id,
                        conversation_title=conversation_title
                    )
                    
                    activities.append(activity)
        
        return activities
    
    def _extract_priorities(self, content: str, conversation_id: str, conversation_title: str) -> List[Dict[str, Any]]:
        """Extract current priorities from conversation content."""
        
        priorities = []
        
        # Look for explicit priority statements
        priority_indicators = [
            r'Current priorities?:?\s*(.+)',
            r'Focus on:?\s*(.+)',
            r'Main goals?:?\s*(.+)',
            r'This week:?\s*(.+)',
            r'Next:?\s*(.+)',
        ]
        
        for pattern in priority_indicators:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                priority_text = match.group(1).strip()
                if len(priority_text) < 5:
                    continue
                
                # Determine priority level
                priority_level = self._determine_priority(priority_text)
                
                # Determine project
                project = self._determine_project_from_context(content, match.start())
                
                priorities.append({
                    'priority_text': priority_text,
                    'priority_level': priority_level,
                    'project': project,
                    'conversation_id': conversation_id,
                    'conversation_title': conversation_title
                })
        
        return priorities
    
    def _determine_source(self, line: str, category: str) -> str:
        """Determine the source of an action item."""
        
        line_lower = line.lower()
        
        # Check for specific people
        for person, patterns in self.people_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line_lower):
                    return person
        
        # Check category-based sources
        if category == 'nick_requests':
            return 'nick'
        elif category == 'meeting_actions':
            return 'meeting'
        else:
            return 'self'
    
    def _determine_priority(self, text: str) -> str:
        """Determine priority level from text."""
        
        text_lower = text.lower()
        
        for priority_level, patterns in self.priority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return priority_level
        
        return 'medium'  # Default priority
    
    def _determine_project_from_context(self, content: str, position: int) -> str:
        """Determine project from surrounding context."""
        
        # Get context around the position
        start = max(0, position - 200)
        end = min(len(content), position + 200)
        context = content[start:end].lower()
        
        # Project keywords
        project_keywords = {
            'rangle_airbender': ['rangle', 'airbender', 'rls', 'deployment'],
            'float_ecosystem': ['float', 'floatctl', 'bridge', 'dispatch', 'chroma'],
            'consciousness_tech': ['consciousness', 'ritual', 'lf1m', 'neuroqueer'],
            'general_dev': ['api', 'database', 'frontend', 'backend']
        }
        
        for project, keywords in project_keywords.items():
            if any(keyword in context for keyword in keywords):
                return project
        
        return 'general'
    
    def _parse_conversation_date(self, conversation_data: Dict[str, Any]) -> datetime:
        """Parse conversation date from metadata."""
        
        created_at = conversation_data.get('created_at')
        if created_at:
            try:
                return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                pass
        
        return datetime.now()
    
    def _save_action_items(self, action_items: List[ActionItem]) -> None:
        """Save action items to database."""
        
        with self.db_manager.get_session() as session:
            for item in action_items:
                session.execute("""
                    INSERT INTO workflow_action_items 
                    (content, source, priority, status, context, conversation_id, conversation_title)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.content, item.source, item.priority, item.status,
                    item.context, item.conversation_id, item.conversation_title
                ))
            session.commit()
    
    def _save_activities(self, activities: List[WorkActivity]) -> None:
        """Save work activities to database."""
        
        with self.db_manager.get_session() as session:
            for activity in activities:
                session.execute("""
                    INSERT INTO workflow_activities 
                    (activity, project, activity_date, outcome, conversation_id, conversation_title)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    activity.activity, activity.project, activity.date.isoformat(),
                    activity.outcome, activity.conversation_id, activity.conversation_title
                ))
            session.commit()
    
    def _save_priorities(self, priorities: List[Dict[str, Any]]) -> None:
        """Save priorities to database."""
        
        with self.db_manager.get_session() as session:
            for priority in priorities:
                session.execute("""
                    INSERT INTO workflow_priorities 
                    (priority_text, priority_level, project, conversation_id, conversation_title)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    priority['priority_text'], priority['priority_level'], priority['project'],
                    priority['conversation_id'], priority['conversation_title']
                ))
            session.commit()
    
    # Query methods for practical workflow questions
    
    def what_did_i_do_last_week(self, days_back: int = 7) -> Dict[str, Any]:
        """Answer: What did I do last week?"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.db_manager.get_session() as session:
            result = session.execute("""
                SELECT activity, project, activity_date, outcome, conversation_title
                FROM workflow_activities
                WHERE activity_date >= ? AND outcome = 'completed'
                ORDER BY activity_date DESC
            """, (cutoff_date.isoformat(),))
            
            activities = [dict(zip(['activity', 'project', 'date', 'outcome', 'conversation'], row)) 
                         for row in result.fetchall()]
        
        # Group by project
        by_project = defaultdict(list)
        for activity in activities:
            by_project[activity['project']].append(activity)
        
        return {
            'query': f'What did I do in the last {days_back} days?',
            'total_activities': len(activities),
            'by_project': dict(by_project),
            'activities': activities
        }
    
    def action_items_from_nick(self, days_back: int = 30) -> Dict[str, Any]:
        """Answer: What action items do I have from Nick?"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.db_manager.get_session() as session:
            result = session.execute("""
                SELECT content, priority, status, context, conversation_title, extracted_at
                FROM workflow_action_items
                WHERE source = 'nick' AND extracted_at >= ? AND status = 'open'
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END,
                    extracted_at DESC
            """, (cutoff_date.isoformat(),))
            
            action_items = [dict(zip(['content', 'priority', 'status', 'context', 'conversation', 'date'], row)) 
                           for row in result.fetchall()]
        
        return {
            'query': f'Action items from Nick (last {days_back} days)',
            'total_items': len(action_items),
            'high_priority': len([item for item in action_items if item['priority'] == 'high']),
            'action_items': action_items
        }
    
    def current_priorities(self, days_back: int = 14) -> Dict[str, Any]:
        """Answer: What are my current priorities?"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get recent priorities
        cursor = self.db_manager.execute_sql("""
            SELECT priority_text, priority_level, project, conversation_title, created_at
            FROM workflow_priorities
            WHERE created_at >= ? AND status = 'active'
            ORDER BY 
                CASE priority_level 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END,
                created_at DESC
        """, (cutoff_date.isoformat(),))
        
        priorities = [dict(zip(['priority_text', 'priority_level', 'project', 'conversation', 'date'], row)) 
                     for row in cursor.fetchall()]
        
        # Get open action items as additional priorities
        cursor = self.db_manager.execute_sql("""
            SELECT content, priority, source, conversation_title
            FROM workflow_action_items
            WHERE status = 'open' AND extracted_at >= ?
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END
            LIMIT 10
        """, (cutoff_date.isoformat(),))
        
        action_items = [dict(zip(['content', 'priority', 'source', 'conversation'], row)) 
                       for row in cursor.fetchall()]
        
        return {
            'query': f'Current priorities (last {days_back} days)',
            'explicit_priorities': priorities,
            'open_action_items': action_items,
            'total_priorities': len(priorities),
            'total_action_items': len(action_items)
        }
    
    def forgotten_tasks(self, days_back: int = 30) -> Dict[str, Any]:
        """Answer: What tasks might I have forgotten?"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get old open action items that haven't been mentioned recently
        cursor = self.db_manager.execute_sql("""
            SELECT content, priority, source, context, conversation_title, extracted_at
            FROM workflow_action_items
            WHERE status = 'open' 
                AND extracted_at <= ?
                AND priority IN ('high', 'medium')
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                END,
                extracted_at ASC
        """, (cutoff_date.isoformat(),))
        
        forgotten_items = [dict(zip(['content', 'priority', 'source', 'context', 'conversation', 'date'], row)) 
                          for row in cursor.fetchall()]
        
        return {
            'query': f'Potentially forgotten tasks (older than {days_back} days)',
            'forgotten_items': forgotten_items,
            'total_forgotten': len(forgotten_items),
            'high_priority_forgotten': len([item for item in forgotten_items if item['priority'] == 'high'])
        }
    
    def meeting_follow_ups(self, days_back: int = 14) -> Dict[str, Any]:
        """Answer: What meeting follow-ups do I have?"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        cursor = self.db_manager.execute_sql("""
            SELECT content, priority, context, conversation_title, extracted_at
            FROM workflow_action_items
            WHERE source = 'meeting' AND extracted_at >= ? AND status = 'open'
            ORDER BY extracted_at DESC
        """, (cutoff_date.isoformat(),))
        
        meeting_items = [dict(zip(['content', 'priority', 'context', 'conversation', 'date'], row)) 
                        for row in cursor.fetchall()]
        
        return {
            'query': f'Meeting follow-ups (last {days_back} days)',
            'meeting_items': meeting_items,
            'total_items': len(meeting_items)
        }