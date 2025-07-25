#!/usr/bin/env python3
"""
Convert FLOAT sources (JSON/JSONL) to markdown format with YAML headers and [heavy::annotation] style.
For NotebookLM ingestion.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Any, Optional
import hashlib

def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from conversation JSON for YAML frontmatter."""
    metadata = {
        'created': data.get('created_at', datetime.now().isoformat()),
        'updated': data.get('updated_at', datetime.now().isoformat()),
        'source_type': 'float_conversation',
        'uid': data.get('uuid', data.get('conversation_id', data.get('id', ''))),
        'title': data.get('name', data.get('title', 'Untitled Conversation')),
        'tags': []
    }
    
    # Extract tags from title
    title = metadata['title']
    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) >= 2:
            metadata['conversation_date'] = parts[0]
            metadata['conversation_topic'] = ' - '.join(parts[1:])
    
    # Extract tags from content patterns
    if 'rangle' in title.lower():
        metadata['tags'].append('#rangle')
    if 'airbender' in title.lower():
        metadata['tags'].append('#airbender')
    if 'nick' in title.lower():
        metadata['tags'].append('#nick-collaboration')
    if 'float' in title.lower():
        metadata['tags'].append('#float-methodology')
    if 'bridge' in title.lower():
        metadata['tags'].append('#bridge')
    if 'publishing' in title.lower():
        metadata['tags'].append('#publishing-forest')
    
    # Add signal density tags
    if 'tool_calls_count' in data:
        tool_count = data['tool_calls_count']
        if tool_count > 50:
            metadata['tags'].append('#high-density')
            metadata['signal_density'] = 'very_high'
        elif tool_count > 15:
            metadata['tags'].append('#medium-density')
            metadata['signal_density'] = 'high'
        else:
            metadata['signal_density'] = 'medium'
    
    return metadata

def annotate_content(text: str) -> str:
    """Add [heavy::annotation] style markers to content."""
    # Pattern recognition for semantic marking
    patterns = {
        r'(ctx::\s*[^\n]+)': r'[context::\1]',
        r'(bridge::\s*[^\n]+)': r'[bridge_reference::\1]',
        r'(mode::\s*[^\n]+)': r'[cognitive_mode::\1]',
        r'(highlight::\s*[^\n]+)': r'[key_insight::\1]',
        r'(float\.dispatch\([^)]+\))': r'[dispatch_call::\1]',
        r'(CB-\d{8}-\d{4}-\w{4})': r'[bridge_id::\1]',
        r'(@\w+)': r'[persona::\1]',
        r'(project::\s*[^\n]+)': r'[project_context::\1]',
        r'(rememberWhen::\s*[^\n]+)': r'[memory_anchor::\1]',
        r'(floatAST\{[^}]+\})': r'[float_ast::\1]',
    }
    
    annotated = text
    for pattern, replacement in patterns.items():
        annotated = re.sub(pattern, replacement, annotated, flags=re.MULTILINE)
    
    return annotated

def process_conversation_json(json_path: Path) -> Optional[str]:
    """Process a conversation JSON file into annotated markdown."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract metadata
        metadata = extract_metadata(data)
        
        # Start building markdown
        content_parts = []
        
        # Add YAML frontmatter
        yaml_header = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        content_parts.append(f"---\n{yaml_header}---\n")
        
        # Add title and overview
        content_parts.append(f"# {metadata['title']}\n")
        
        # Add conversation metadata section
        content_parts.append("## [conversation_metadata::overview]\n")
        content_parts.append(f"- [created_at::{metadata['created']}]\n")
        content_parts.append(f"- [conversation_id::{metadata['uid']}]\n")
        if 'signal_density' in metadata:
            content_parts.append(f"- [signal_density::{metadata['signal_density']}]\n")
        content_parts.append("\n")
        
        # Process conversation history - Claude format
        if 'chat_messages' in data:
            messages = data['chat_messages']
            
            content_parts.append("## [conversation_flow::messages]\n")
            
            for i, msg in enumerate(messages):
                sender = msg.get('sender', 'unknown')
                text = msg.get('text', '')
                created_at = msg.get('created_at', '')
                
                # Skip empty messages
                if not text.strip():
                    continue
                
                # Add message header
                content_parts.append(f"\n### [message::{i}] [{sender}::speaker] [timestamp::{created_at}]\n")
                
                # Annotate and add content
                annotated_content = annotate_content(text)
                content_parts.append(annotated_content)
                content_parts.append("\n")
                
                # Add tool usage info if present
                if 'content' in msg:
                    for content_item in msg['content']:
                        if content_item.get('type') == 'tool_use':
                            tool_name = content_item.get('name', 'unknown')
                            integration = content_item.get('integration_name', '')
                            content_parts.append(f"\n[tool_use::{integration}::{tool_name}]\n")
                            if 'input' in content_item:
                                content_parts.append(f"[tool_input::{json.dumps(content_item['input'], indent=2)}]\n")
        
        # Also check for older format
        elif 'history' in data and 'conversations' in data['history']:
            conversations = data['history']['conversations']
            
            content_parts.append("## [conversation_flow::messages]\n")
            
            for i, convo in enumerate(conversations):
                for j, msg in enumerate(convo.get('messages', [])):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    
                    # Skip empty messages
                    if not content.strip():
                        continue
                    
                    # Add message header
                    content_parts.append(f"\n### [message::{i}.{j}] [{role}::speaker]\n")
                    
                    # Annotate and add content
                    annotated_content = annotate_content(content)
                    content_parts.append(annotated_content)
                    content_parts.append("\n")
        
        # Add tool calls section if present
        tool_calls_path = json_path.with_suffix('.tool_calls.jsonl')
        if tool_calls_path.exists():
            content_parts.append("\n## [tool_usage::summary]\n")
            
            with open(tool_calls_path, 'r', encoding='utf-8') as f:
                tool_calls = [json.loads(line) for line in f if line.strip()]
            
            if tool_calls:
                # Group tool calls by type
                tool_groups = {}
                for call in tool_calls:
                    # Handle different tool call formats
                    tool_name = call.get('tool_name', call.get('name', 'unknown'))
                    if tool_name not in tool_groups:
                        tool_groups[tool_name] = []
                    tool_groups[tool_name].append(call)
                
                content_parts.append(f"- [total_tool_calls::{len(tool_calls)}]\n")
                content_parts.append(f"- [unique_tools::{len(tool_groups)}]\n\n")
                
                # Add tool usage breakdown
                content_parts.append("### [tool_breakdown::statistics]\n")
                for tool, calls in sorted(tool_groups.items(), key=lambda x: len(x[1]), reverse=True):
                    content_parts.append(f"- [tool::{tool}] - {len(calls)} calls\n")
                
                # Add significant tool interactions
                content_parts.append("\n### [significant_tool_interactions::highlights]\n")
                
                # Focus on chroma, obsidian, and roam interactions
                significant_tools = ['mcp__chroma__', 'mcp__shack-tools__', 'mcp__roam-helper__']
                
                for tool_prefix in significant_tools:
                    relevant_calls = [c for c in tool_calls if c.get('tool_name', '').startswith(tool_prefix)]
                    if relevant_calls:
                        tool_type = tool_prefix.split('__')[1]
                        content_parts.append(f"\n#### [{tool_type}_interactions::detail]\n")
                        
                        for call in relevant_calls[:5]:  # Limit to 5 examples
                            tool_name = call.get('tool_name', call.get('name', ''))
                            params = call.get('parameters', call.get('input', {}))
                            
                            content_parts.append(f"- [tool_call::{tool_name}]\n")
                            if isinstance(params, dict):
                                for key, value in params.items():
                                    if isinstance(value, str) and len(value) < 100:
                                        content_parts.append(f"  - [{key}::{value}]\n")
        
        return ''.join(content_parts)
        
    except Exception as e:
        print(f"Error processing {json_path}: {e}")
        return None

def process_jsonl_logs(jsonl_path: Path) -> Optional[str]:
    """Process JSONL log files into annotated markdown."""
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            logs = [json.loads(line) for line in f if line.strip()]
        
        if not logs:
            return None
        
        # Create metadata
        metadata = {
            'created': datetime.now().isoformat(),
            'source_type': 'float_tool_log',
            'log_type': jsonl_path.stem,
            'tags': ['#tool-logs', f'#{jsonl_path.stem}']
        }
        
        # Build content
        content_parts = []
        
        # YAML header
        yaml_header = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        content_parts.append(f"---\n{yaml_header}---\n")
        
        # Title
        content_parts.append(f"# Tool Log: {jsonl_path.stem}\n")
        content_parts.append(f"## [log_metadata::overview]\n")
        content_parts.append(f"- [total_entries::{len(logs)}]\n")
        content_parts.append(f"- [source_path::{jsonl_path}]\n\n")
        
        # Process log entries
        content_parts.append("## [log_entries::detail]\n")
        
        for i, entry in enumerate(logs):
            content_parts.append(f"\n### [entry::{i}]\n")
            
            # Add timestamp if present
            if 'timestamp' in entry:
                content_parts.append(f"- [timestamp::{entry['timestamp']}]\n")
            
            # Process different log types
            if 'reasoning' in entry:
                content_parts.append(f"- [reasoning_type::{entry.get('type', 'unknown')}]\n")
                content_parts.append(f"\n[reasoning_content::detail]\n")
                content_parts.append(f"{annotate_content(str(entry['reasoning']))}\n")
            
            elif 'pattern' in entry:
                content_parts.append(f"- [pattern_detected::{entry['pattern']}]\n")
                if 'confidence' in entry:
                    content_parts.append(f"- [confidence::{entry['confidence']}]\n")
            
            elif 'message' in entry:
                content_parts.append(f"\n[log_message::content]\n")
                content_parts.append(f"{annotate_content(entry['message'])}\n")
        
        return ''.join(content_parts)
        
    except Exception as e:
        print(f"Error processing {jsonl_path}: {e}")
        return None

def main():
    """Main conversion function."""
    base_path = Path("/Users/evan/projects/float-workspace")
    output_base = Path("/Users/evan/projects/float-workspace/offical-exports/data-2025-06-28-07-14-08/floatctl-py/float-sources")
    
    # High-priority conversations based on analysis
    priority_conversations = [
        "2025-06-10 - Rangle - Nick - FLOAT Universe Tech Collaboration Framework",
        "2025-07-01 - rangle - nick - evan - airbender meeting - Complete Session Analysis Bridge",
        "2025-07-03 - rangle - airbender - nick - evan - Rangle Airbender MCP Tool Bridge",
        "2025-06-11 - nick -- evan - AI Agent Deployment Platform Beta",
        "2025-07-02 - Publishing House Personas Ecosystem",
        "2025-06-11 - FLOATdispatch Publishing Framework",
        "2025-07-06 - Claude Fucks Estate Research",  # High tool density
        "2025-07-05 - Sneaky Network Intelligence",  # High tool density
        "2025-07-07 - Chrome DevTools DOM Investigation",  # High tool density
        "2025-06-25 - claude helping claude - Chroma Bridge Creation Guide",
        "2025-07-06 - FLOAT Cognitive DSL - Memory Trace Architecture - cats and dicks to infinite maw to marco to float k",
        "2025-05-19 - FLOAT System Architecture and HTTM Integration",
    ]
    
    # Convert priority conversations
    conversations_path = base_path / "operations/float-dropzone/exports/output/conversations"
    processed_count = 0
    
    print("Converting high-signal FLOAT conversations...")
    
    for conv_name in priority_conversations:
        json_path = conversations_path / f"{conv_name}.json"
        if json_path.exists():
            print(f"Processing: {conv_name}")
            markdown_content = process_conversation_json(json_path)
            
            if markdown_content:
                # Create clean filename
                clean_name = re.sub(r'[^\w\s-]', '', conv_name).strip().replace(' ', '_')
                output_path = output_base / "conversations" / f"{clean_name}.md"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                processed_count += 1
                print(f"  ✓ Converted to: {output_path.name}")
        else:
            print(f"  ✗ Not found: {json_path}")
    
    # Process tool logs
    print("\nConverting tool extraction logs...")
    
    temp_logs_path = Path("/Users/evan/projects/float-workspace/offical-exports/data-2025-06-28-07-14-08/floatctl-py/.claude/temp")
    
    for log_dir in temp_logs_path.glob("convo-review-*/logs/*.jsonl"):
        print(f"Processing: {log_dir.name}")
        markdown_content = process_jsonl_logs(log_dir)
        
        if markdown_content:
            output_path = output_base / "tool-logs" / f"{log_dir.parent.parent.name}_{log_dir.name}.md"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            processed_count += 1
            print(f"  ✓ Converted to: {output_path.name}")
    
    # Also convert some key bridges
    print("\nConverting key bridge documents...")
    
    key_bridges = [
        "nick_meeting_complete_session_analysis_20250701.md",
        "publishing_house_ecosystem_complete_20250702.md",
        "airbender_meeting_20250708_index.md",
        "bridge_creation_guide_enhancement_20250619.md",
        "consciousness_bootstrap_protocol_discovery_20250712.md",
        "float_system_technical_excellence_20250614.md",
        "unified_ecosystem_moc_20250614.md",
        "cognitive_dsl_associative_reasoning_formalization_20250705.md",
    ]
    
    for bridge_name in key_bridges:
        bridge_path = Path(f"FLOAT.bridges/{bridge_name}")
        print(f"Processing bridge: {bridge_name}")
        
        try:
            # Read bridge from vault
            result = mcp__shack_tools__get_vault_file(filename=str(bridge_path))
            content = result.get('content', '')
            
            if content:
                # Create metadata from bridge content
                metadata = {
                    'created': datetime.now().isoformat(),
                    'source_type': 'float_bridge',
                    'title': bridge_name.replace('_', ' ').replace('.md', '').title(),
                    'tags': ['#bridge', '#float-methodology'],
                    'bridge_name': bridge_name
                }
                
                # Check for bridge ID in content
                bridge_id_match = re.search(r'(CB-\d{8}-\d{4}-\w{4})', content)
                if bridge_id_match:
                    metadata['bridge_id'] = bridge_id_match.group(1)
                    metadata['tags'].append(f'#{bridge_id_match.group(1)}')
                
                # Build markdown with YAML header
                yaml_header = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
                annotated_content = annotate_content(content)
                
                markdown_output = f"---\n{yaml_header}---\n\n{annotated_content}"
                
                # Save to bridges directory
                output_path = output_base / "bridges" / bridge_name
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_output)
                
                processed_count += 1
                print(f"  ✓ Converted bridge: {bridge_name}")
        except Exception as e:
            print(f"  ✗ Error processing bridge {bridge_name}: {e}")
    
    print(f"\nConversion complete! Processed {processed_count} files.")
    print(f"Output directory: {output_base}")

# Import needed for bridge fetching
from mcp__shack_tools import get_vault_file as mcp__shack_tools__get_vault_file

if __name__ == "__main__":
    main()