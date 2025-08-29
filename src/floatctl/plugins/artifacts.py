"""Plugin for extracting artifacts from conversations."""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import rich_click as click
from rich.console import Console
from rich.table import Table

from floatctl.plugin_manager import PluginBase

console = Console()


class ArtifactsPlugin(PluginBase):
    """Plugin for extracting Claude artifacts from conversations."""
    
    name = "artifacts"
    description = "Extract and manage Claude artifacts from conversation exports"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register artifact commands."""
        
        @cli_group.group()
        @click.pass_context
        def artifacts(ctx: click.Context) -> None:
            """Extract and manage artifacts from conversations."""
            pass
        
        @artifacts.command()
        @click.option(
            "--input", "-i",
            type=click.Path(exists=True),
            required=True,
            help="Path to conversations.json file or directory containing conversation files",
        )
        @click.option(
            "--output", "-o",
            type=click.Path(),
            help="Output directory for artifacts (default: ./output/artifacts)",
        )
        @click.option(
            "--format",
            type=click.Choice(["files", "index", "both"]),
            default="both",
            help="Output format: files only, index only, or both",
        )
        @click.pass_context
        def extract(ctx: click.Context, input: Path, output: Optional[Path], format: str) -> None:
            """Extract artifacts from conversations."""
            input_path = Path(input)
            output_path = Path(output) if output else Path("./output/artifacts")
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Determine input type
            if input_path.is_file() and input_path.suffix == '.json':
                artifacts = self._extract_from_json(input_path)
            else:
                artifacts = self._extract_from_directory(input_path)
            
            if not artifacts:
                console.print("[yellow]No artifacts found[/yellow]")
                return
            
            # Save artifacts
            saved_artifacts = []
            if format in ["files", "both"]:
                saved_artifacts = self._save_artifacts(artifacts, output_path)
            
            # Generate index
            if format in ["index", "both"]:
                self._generate_index(artifacts, saved_artifacts, output_path)
            
            # Display results
            self._display_results(artifacts, saved_artifacts, output_path)
    
    def _extract_from_json(self, json_path: Path) -> List[Dict[str, Any]]:
        """Extract artifacts from conversations.json file."""
        artifacts = []
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
            
            console.print(f"[cyan]Processing {len(conversations)} conversations...[/cyan]")
            
            for conv in conversations:
                conv_artifacts = self._extract_artifacts_from_conversation(conv)
                artifacts.extend(conv_artifacts)
            
        except Exception as e:
            console.print(f"[red]Error reading {json_path}: {e}[/red]")
        
        return artifacts
    
    def _extract_from_directory(self, dir_path: Path) -> List[Dict[str, Any]]:
        """Extract artifacts from directory of conversation files."""
        artifacts = []
        
        # Look for JSON files first (original format)
        json_files = list(dir_path.glob("*.json"))
        if json_files:
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        conv_data = json.load(f)
                    conv_artifacts = self._extract_artifacts_from_conversation(conv_data)
                    artifacts.extend(conv_artifacts)
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not process {json_file}: {e}[/yellow]")
        
        # TODO: Add support for processed markdown files if needed
        
        return artifacts
    
    def _extract_artifacts_from_conversation(self, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract artifacts from a single conversation."""
        artifacts = []
        
        conv_id = conversation.get('uuid', 'unknown')
        conv_name = conversation.get('name', 'Untitled')
        conv_created = conversation.get('created_at', '')
        
        for msg_idx, message in enumerate(conversation.get('chat_messages', [])):
            for content_idx, content in enumerate(message.get('content', [])):
                # Look for tool_use with name "artifacts"
                if (content.get('type') == 'tool_use' and 
                    content.get('name') == 'artifacts'):
                    
                    artifact = {
                        'conversation_id': conv_id,
                        'conversation_name': conv_name,
                        'conversation_created': conv_created,
                        'message_index': msg_idx,
                        'content_index': content_idx,
                        'tool_use_id': content.get('id', ''),
                        'created_at': message.get('created_at', ''),
                        'sender': message.get('sender', ''),
                    }
                    
                    # Extract artifact metadata from input
                    input_data = content.get('input', {})
                    artifact.update({
                        'type': input_data.get('type', 'unknown'),
                        'title': input_data.get('title', 'Untitled Artifact'),
                        'identifier': input_data.get('identifier', ''),
                        'content': input_data.get('content', ''),
                    })
                    
                    # Try to find corresponding tool_result for content
                    artifact['result_content'] = self._find_tool_result(
                        conversation, artifact['tool_use_id']
                    )
                    
                    artifacts.append(artifact)
        
        return artifacts
    
    def _find_tool_result(self, conversation: Dict[str, Any], tool_use_id: str) -> str:
        """Find the tool_result content for a given tool_use_id."""
        for message in conversation.get('chat_messages', []):
            for content in message.get('content', []):
                if (content.get('type') == 'tool_result' and 
                    content.get('tool_use_id') == tool_use_id):
                    return content.get('content', '')
        return ''
    
    def _save_artifacts(self, artifacts: List[Dict[str, Any]], output_path: Path) -> List[Dict[str, Any]]:
        """Save artifacts as individual files."""
        saved_artifacts = []
        
        for artifact in artifacts:
            # Create date-based subdirectory
            conv_date = artifact['conversation_created'][:10] if artifact['conversation_created'] else 'unknown-date'
            date_dir = output_path / conv_date
            date_dir.mkdir(exist_ok=True)
            
            # Generate filename
            title = self._safe_filename(artifact['title'])
            identifier = artifact['identifier'] or 'artifact'
            filename = f"{identifier}_{title}"
            
            # Determine file extension based on type
            if artifact['type'] == 'text/html':
                ext = '.html'
            elif artifact['type'] == 'text/markdown':
                ext = '.md'
            elif 'json' in artifact['type']:
                ext = '.json'
            else:
                ext = '.txt'
            
            file_path = date_dir / f"{filename}{ext}"
            
            # Handle naming conflicts
            counter = 1
            while file_path.exists():
                file_path = date_dir / f"{filename}_{counter}{ext}"
                counter += 1
            
            # Save artifact content
            content = artifact.get('result_content') or artifact.get('content', '')
            if content:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    saved_info = {
                        'artifact': artifact,
                        'file_path': file_path,
                        'file_size': len(content),
                        'hash': hashlib.md5(content.encode()).hexdigest()
                    }
                    saved_artifacts.append(saved_info)
                    
                except Exception as e:
                    console.print(f"[red]Error saving {file_path}: {e}[/red]")
        
        return saved_artifacts
    
    def _generate_index(self, artifacts: List[Dict[str, Any]], saved_artifacts: List[Dict[str, Any]], output_path: Path) -> None:
        """Generate artifact index file."""
        index = {
            'generated_at': datetime.now().isoformat(),
            'total_artifacts': len(artifacts),
            'artifacts': []
        }
        
        for saved in saved_artifacts:
            artifact = saved['artifact']
            index['artifacts'].append({
                'title': artifact['title'],
                'identifier': artifact['identifier'],
                'type': artifact['type'],
                'conversation_id': artifact['conversation_id'],
                'conversation_name': artifact['conversation_name'],
                'conversation_created': artifact['conversation_created'],
                'file_path': str(saved['file_path']),
                'file_size': saved['file_size'],
                'hash': saved['hash'],
                'created_at': artifact['created_at'],
            })
        
        index_path = output_path / 'artifact_index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def _display_results(self, artifacts: List[Dict[str, Any]], saved_artifacts: List[Dict[str, Any]], output_path: Path) -> None:
        """Display extraction results."""
        console.print(f"\n[green]✓ Found {len(artifacts)} artifacts[/green]")
        
        if saved_artifacts:
            console.print(f"[green]✓ Saved {len(saved_artifacts)} artifacts to {output_path}[/green]")
            
            # Create summary table
            table = Table(title="Extracted Artifacts")
            table.add_column("Title", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Size", style="yellow")
            table.add_column("Conversation", style="blue")
            
            for saved in saved_artifacts[:10]:  # Show first 10
                artifact = saved['artifact']
                table.add_row(
                    artifact['title'][:40] + "..." if len(artifact['title']) > 40 else artifact['title'],
                    artifact['type'],
                    f"{saved['file_size']} chars",
                    artifact['conversation_name'][:30] + "..." if len(artifact['conversation_name']) > 30 else artifact['conversation_name']
                )
            
            console.print(table)
            
            if len(saved_artifacts) > 10:
                console.print(f"... and {len(saved_artifacts) - 10} more artifacts")
    
    def _safe_filename(self, name: str) -> str:
        """Convert a string to a safe filename."""
        # Remove/replace problematic characters
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        # Replace spaces with underscores and limit length
        safe_name = safe_name.replace(' ', '_')[:50]
        return safe_name or 'untitled'