#!/usr/bin/env python3
"""
Convert key FLOAT bridge documents to markdown with YAML headers for NotebookLM.
This script reads bridges directly using the MCP tools.
"""

import yaml
import re
from datetime import datetime
from pathlib import Path

# Key bridges to convert
KEY_BRIDGES = [
    "nick_meeting_complete_session_analysis_20250701.md",
    "publishing_house_ecosystem_complete_20250702.md",
    "airbender_meeting_20250708_index.md",
    "bridge_creation_guide_enhancement_20250619.md",
    "consciousness_bootstrap_protocol_discovery_20250712.md",
    "float_system_technical_excellence_20250614.md",
    "unified_ecosystem_moc_20250614.md",
    "cognitive_dsl_associative_reasoning_formalization_20250705.md",
    "nick_collaboration_convergence_20250611.md",
    "tool_extraction_suite_achievement_20250712.md",
    "floatctl_pipeline_validation_complete_20250713.md",
    "rangle_return_context_20250625.md",
]

def annotate_content(text: str) -> str:
    """Add [heavy::annotation] style markers to content."""
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
        r'(\*\*Key [^:]+:\*\*)': r'[section_header::\1]',
        r'(##\s+[^\n]+)': r'[heading::\1]',
    }
    
    annotated = text
    for pattern, replacement in patterns.items():
        annotated = re.sub(pattern, replacement, annotated, flags=re.MULTILINE)
    
    return annotated

def process_bridge(bridge_name: str, content: str, output_dir: Path) -> bool:
    """Process a single bridge document."""
    try:
        # Create metadata from bridge content
        metadata = {
            'created': datetime.now().isoformat(),
            'source_type': 'float_bridge',
            'title': bridge_name.replace('_', ' ').replace('.md', '').title(),
            'tags': ['#bridge', '#float-methodology'],
            'bridge_name': bridge_name
        }
        
        # Extract additional metadata from content
        if 'nick' in bridge_name.lower():
            metadata['tags'].append('#nick-collaboration')
        if 'airbender' in bridge_name.lower():
            metadata['tags'].append('#airbender')
        if 'publishing' in bridge_name.lower():
            metadata['tags'].append('#publishing-forest')
        if 'consciousness' in bridge_name.lower():
            metadata['tags'].append('#consciousness-tech')
        if 'tool' in bridge_name.lower():
            metadata['tags'].append('#tool-development')
        
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
        output_path = output_dir / bridge_name
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_output)
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing bridge {bridge_name}: {e}")
        return False

def main():
    """Main function to coordinate bridge conversion."""
    output_dir = Path("/Users/evan/projects/float-workspace/offical-exports/data-2025-06-28-07-14-08/floatctl-py/float-sources/bridges")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Bridge conversion script ready.")
    print(f"Output directory: {output_dir}")
    print(f"\nTo convert bridges, use the MCP tools to read each bridge file from the vault")
    print("and then call process_bridge() with the content.")
    
    # Print list of bridges to convert
    print("\nKey bridges to convert:")
    for i, bridge in enumerate(KEY_BRIDGES, 1):
        print(f"{i}. FLOAT.bridges/{bridge}")

if __name__ == "__main__":
    main()