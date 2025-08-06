"""
Simple test of workflow intelligence system
"""

import json
from datetime import datetime
from pathlib import Path

# Test content with various workflow patterns
test_content = """
Meeting with Nick yesterday:
- TODO: Fix the airbender deployment pipeline
- Nick said: Need to update the RLS documentation  
- Action item: Follow up with Ditmar about the new requirements
- Priority: High - Deploy to production by Friday
- Completed: Fixed the authentication bug
- Working on: Implementing the new middleware system
- Remember to: Check the consciousness contamination levels
- Follow up: Schedule meeting with Tom about design
- Urgent: Fix the broken tests in CI/CD
- Nick wants: Better error handling in the API
- Meeting action: Document the new workflow process
"""

print("🧬 Testing Workflow Pattern Extraction")
print("=" * 50)

# Test pattern matching
import re

action_patterns = {
    'explicit_todos': [
        r'TODO:?\s*(.+)',
        r'Action item:?\s*(.+)',
        r'Need to:?\s*(.+)',
        r'Remember to:?\s*(.+)',
        r'Follow up:?\s*(.+)',
    ],
    'nick_requests': [
        r'Nick.*(?:said|asked|wants|needs|requested):?\s*(.+)',
        r'From Nick:?\s*(.+)',
        r'Nick.*action:?\s*(.+)',
    ],
    'meeting_actions': [
        r'Meeting.*action:?\s*(.+)',
        r'Decided:?\s*(.+)',
        r'Agreed:?\s*(.+)',
    ],
    'priority_indicators': [
        r'Priority:?\s*(.+)',
        r'Important:?\s*(.+)',
        r'Urgent:?\s*(.+)',
    ]
}

activity_patterns = {
    'completed_work': [
        r'Completed:?\s*(.+)',
        r'Finished:?\s*(.+)',
        r'Done:?\s*(.+)',
        r'Fixed:?\s*(.+)',
    ],
    'in_progress': [
        r'Working on:?\s*(.+)',
        r'Currently:?\s*(.+)',
        r'In progress:?\s*(.+)',
    ]
}

print("📋 Action Items Found:")
for category, patterns in action_patterns.items():
    print(f"\n{category.replace('_', ' ').title()}:")
    for pattern in patterns:
        matches = re.findall(pattern, test_content, re.IGNORECASE)
        for match in matches:
            print(f"  • {match.strip()}")

print("\n🔧 Work Activities Found:")
for category, patterns in activity_patterns.items():
    print(f"\n{category.replace('_', ' ').title()}:")
    for pattern in patterns:
        matches = re.findall(pattern, test_content, re.IGNORECASE)
        for match in matches:
            print(f"  • {match.strip()}")

print("\n✅ Pattern extraction test completed!")
print("\nThis shows the workflow intelligence will extract:")
print("- 8+ action items from various sources")
print("- 2+ work activities (completed and in-progress)")
print("- Priority levels and context")
print("- Source attribution (Nick, meetings, self)")