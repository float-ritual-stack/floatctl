"""Plugin for processing conversation exports."""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import re

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from floatctl.plugin_manager import PluginBase, group, command, option, argument
from floatctl.core.database import DatabaseManager, ProcessingStatus
from floatctl.core.logging import log_command, log_file_operation
from floatctl.core.consciousness_middleware import ConsciousnessMiddleware
from floatctl.core.consciousness_chroma_bridge import ConsciousnessChromaBridge
from floatctl.core.workflow_intelligence import WorkflowIntelligence

console = Console()


class ConversationsPlugin(PluginBase):
    """Plugin for splitting and processing conversation exports."""
    
    name = "conversations"
    description = "Split and process conversation exports from various AI systems"
    version = "1.0.0"
    
    @group()
    @click.pass_context
    def conversations(self, ctx: click.Context) -> None:
        """Manage conversation exports."""
        pass
    
    @command(parent="conversations")
    @argument("input_file", type=click.Path(exists=True, path_type=Path))
    @option(
        "--output-dir", "-o",
        type=click.Path(path_type=Path),
        help="Output directory for split conversations",
    )
    @option(
        "--format", "-f",
        type=click.Choice(["json", "markdown", "both"]),
        default="json",
        help="Output format",
    )
    @option(
        "--by-date",
        is_flag=True,
        help="Organize output files by date",
    )
    @option(
        "--filter-after",
        type=click.DateTime(),
        help="Only process conversations created after this date",
    )
    @option(
        "--dry-run",
        is_flag=True,
        help="Show what would be processed without actually doing it",
    )
    @option(
        "--consciousness-analysis",
        is_flag=True,
        default=True,
        help="Enable consciousness contamination analysis (default: enabled)",
    )
    @option(
        "--export-consciousness",
        type=click.Path(path_type=Path),
        help="Export consciousness analysis results to JSON file",
    )
    @option(
        "--sync-to-chroma",
        is_flag=True,
        help="Sync consciousness analysis results to Chroma for semantic search",
    )
    @click.pass_context
    def split(
        self,
        ctx: click.Context,
        input_file: Path,
        output_dir: Optional[Path],
        format: str,
        by_date: bool,
        filter_after: Optional[datetime],
        dry_run: bool,
        consciousness_analysis: bool,
        export_consciousness: Optional[Path],
        sync_to_chroma: bool,
    ) -> None:
        """Split a conversations export file into individual conversation files."""
        config = ctx.obj["config"]
        db_manager = DatabaseManager(config.db_path)
        
        # Set up output directory
        if output_dir is None:
            output_dir = Path.cwd() / "output" / "conversations"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Record the file run
        file_run = db_manager.record_file_run(
            file_path=input_file,
            plugin=self.name,
            command="split",
            metadata={
                "format": format,
                "by_date": by_date,
                "filter_after": filter_after.isoformat() if filter_after else None,
                "dry_run": dry_run,
                "consciousness_analysis": consciousness_analysis,
            }
        )
        
        try:
            result = self._split_conversations(
                input_file=input_file,
                output_dir=output_dir,
                format=format,
                by_date=by_date,
                filter_after=filter_after,
                dry_run=dry_run,
                consciousness_analysis=consciousness_analysis,
                export_consciousness=export_consciousness,
                sync_to_chroma=sync_to_chroma,
                config=config,
                db_manager=db_manager,
            )
            
            # Complete the file run
            db_manager.complete_file_run(
                file_run.id,
                output_path=output_dir,
                items_processed=result.get("conversations_processed", 0),
                metadata=result
            )
            
            console.print(f"[green]✓[/green] Processing completed successfully")
            if not dry_run:
                console.print(f"[blue]Output directory:[/blue] {output_dir}")
                
        except Exception as e:
            # Mark the file run as failed
            db_manager.fail_file_run(file_run.id, str(e))
            console.print(f"[red]✗ Error processing conversations: {e}[/red]")
            raise click.ClickException(str(e))
    
    @command(parent="conversations")
    @argument("input_file", type=click.Path(exists=True, path_type=Path))
    @click.pass_context
    def history(self, ctx: click.Context, input_file: Path) -> None:
        """Show processing history for a file."""
        config = ctx.obj["config"]
        db_manager = DatabaseManager(config.db_path)
        
        file_hash = hashlib.md5(input_file.read_bytes()).hexdigest()
        runs = db_manager.get_file_history(input_file)
        
        if not runs:
            console.print(f"[yellow]No processing history found for {input_file}[/yellow]")
            return
        
        table = Table(title=f"Processing History: {input_file.name}")
        table.add_column("Run ID", style="cyan")
        table.add_column("Plugin", style="green")
        table.add_column("Command", style="blue")
        table.add_column("Status", style="magenta")
        table.add_column("Started", style="yellow")
        table.add_column("Duration", style="white")
        
        for run in runs:
            duration = "N/A"
            if run.completed_at:
                duration = str(run.completed_at - run.started_at)
            elif run.failed_at:
                duration = str(run.failed_at - run.started_at)
            
            table.add_row(
                str(run.id),
                run.plugin,
                run.command,
                run.status.value,
                run.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                duration
            )
        
        console.print(table)
        
        @conversations.command()
        @click.argument("conversations_dir", type=click.Path(exists=True, path_type=Path))
        @click.option(
            "--output", "-o",
            type=click.Path(path_type=Path),
            help="Output file for analysis summary (default: ~/conversation-history/YYYYMMDD-analysis.md)",
        )
        @click.option(
            "--format",
            type=click.Choice(["markdown", "json"]),
            default="markdown",
            help="Output format for analysis",
        )
        @click.pass_context
        def analyze(
            ctx: click.Context,
            conversations_dir: Path,
            output: Optional[Path],
            format: str,
        ) -> None:
            """Analyze conversations and export summary to markdown."""
            config = ctx.obj["config"]
            
            # Set default output path
            if output is None:
                home = Path.home()
                history_dir = home / "conversation-history"
                history_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d-%H%M")
                output = history_dir / f"{timestamp}-analysis.md"
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
            
            # Find all conversation files
            md_files = list(conversations_dir.glob("*.md"))
            jsonl_files = list(conversations_dir.glob("*.tool_calls.jsonl"))
            
            if not md_files:
                console.print(f"[yellow]No conversation markdown files found in {conversations_dir}[/yellow]")
                return
            
            console.print(f"[cyan]Analyzing {len(md_files)} conversation files...[/cyan]")
            
            # Generate analysis
            analysis = self._analyze_conversations(md_files, jsonl_files, conversations_dir)
            
            # Export analysis
            if format == "markdown":
                self._export_markdown_analysis(analysis, output, conversations_dir)
            else:
                self._export_json_analysis(analysis, output)
            
            console.print(f"[green]Analysis exported to {output}[/green]")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _filter_conversations(
        self, conversations: List[Dict[str, Any]], after_date: datetime
    ) -> List[Dict[str, Any]]:
        """Filter conversations by creation date."""
        # Make after_date timezone-aware if it isn't already
        if after_date.tzinfo is None:
            # Assume UTC for naive datetimes
            after_date = after_date.replace(tzinfo=timezone.utc)
        
        filtered = []
        for conv in conversations:
            created_at = self._parse_datetime(conv.get("created_at"))
            if created_at:
                # Ensure both datetimes are timezone-aware for comparison
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if created_at >= after_date:
                    filtered.append(conv)
        return filtered
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from various formats."""
        if not date_str:
            return None
        
        try:
            # Try ISO format with Z suffix
            if date_str.endswith('Z'):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Try standard ISO format
            return datetime.fromisoformat(date_str)
        except:
            return None
    
    def _safe_filename(self, text: str, max_length: int = 100) -> str:
        """Convert text to safe filename, preserving more characters for readability."""
        if not text:
            return "untitled"
        
        # First, check if the text already has a date prefix and remove it
        # Pattern matches YYYY-MM-DD or YYYY_MM_DD at the start
        date_prefix_pattern = r'^(\d{4}[-_]\d{2}[-_]\d{2})\s*[-_]\s*'
        text = re.sub(date_prefix_pattern, '', text)
        
        # Preserve more characters but still ensure filename safety
        # Allow letters, numbers, spaces, hyphens, underscores, and parentheses
        clean = re.sub(r'[^a-zA-Z0-9 \-_()]', '', text)
        # Replace multiple spaces/underscores with single space
        clean = re.sub(r'[\s_]+', ' ', clean)
        # Trim and limit length
        clean = clean.strip()[:max_length].strip()
        
        return clean if clean else "untitled"
    
    def _extract_conversation_dates(self, conversation: Dict[str, Any]) -> List[str]:
        """Extract unique dates when the conversation was active."""
        dates = set()
        
        # Add conversation creation date
        created_at = self._parse_datetime(conversation.get('created_at'))
        if created_at:
            dates.add(created_at.strftime("%Y-%m-%d"))
        
        # Add dates from messages
        messages = conversation.get('chat_messages', [])
        for msg in messages:
            # Try to get date from content items first
            content_items = msg.get('content', [])
            if content_items and isinstance(content_items, list):
                for content in content_items:
                    timestamp = content.get('start_timestamp')
                    if timestamp:
                        parsed = self._parse_datetime(timestamp)
                        if parsed:
                            dates.add(parsed.strftime("%Y-%m-%d"))
            
            # Fall back to message created_at
            msg_created = msg.get('created_at')
            if msg_created:
                parsed = self._parse_datetime(msg_created)
                if parsed:
                    dates.add(parsed.strftime("%Y-%m-%d"))
        
        return sorted(list(dates))
    
    def _extract_patterns(self, text: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patterns from conversation text with line numbers."""
        lines = text.split('\n')
        patterns = {
            'markers': [],
            'float_calls': [],
            'tools_used': set(),
            'total_lines': len(lines)
        }
        
        # Extract markers with line numbers
        marker_pattern = re.compile(r'(\w+)::\s*(.+?)(?=\n|$)', re.MULTILINE | re.DOTALL)
        for i, line in enumerate(lines, 1):
            # Check for markers in this line
            matches = marker_pattern.finditer(line)
            for match in matches:
                marker_type = match.group(1)
                content = match.group(2).strip()
                
                # Check if this marker continues on next lines
                # Look for continuation (lines that don't start with a new marker)
                line_nums = [i]
                if i < len(lines):
                    j = i
                    while j < len(lines):
                        next_line = lines[j]
                        # If next line is indented or doesn't contain a new marker, it's a continuation
                        if next_line and not re.match(r'^\s*\w+::', next_line) and (next_line.startswith(' ') or next_line.startswith('\t')):
                            line_nums.append(j + 1)
                            content += ' ' + next_line.strip()
                            j += 1
                        else:
                            break
                
                patterns['markers'].append({
                    'type': marker_type,
                    'content': content,
                    'lines': line_nums
                })
        
        # Extract float calls with line numbers
        float_pattern = re.compile(r'(float\.[\w.]+)\((.*?)\)')
        for i, line in enumerate(lines, 1):
            matches = float_pattern.finditer(line)
            for match in matches:
                call = match.group(1)
                args = match.group(2).strip()
                patterns['float_calls'].append({
                    'call': call,
                    'content': args,
                    'lines': [i]
                })
        
        # Extract tool usage from conversation content
        messages = conversation.get('chat_messages', [])
        for msg in messages:
            content_items = msg.get('content', [])
            if isinstance(content_items, list):
                for item in content_items:
                    if item.get('type') == 'tool_use':
                        tool_name = item.get('name', 'unknown')
                        patterns['tools_used'].add(tool_name)
        
        # Convert tools_used set to sorted list
        patterns['tools_used'] = sorted(list(patterns['tools_used']))
        
        return patterns
    
    def _extract_and_save_tool_calls(self, conversation: Dict[str, Any], base_path: Path) -> Optional[Path]:
        """Extract tool calls from conversation and save to JSONL file."""
        tool_calls = []
        
        messages = conversation.get('chat_messages', [])
        for msg_idx, msg in enumerate(messages):
            content_items = msg.get('content', [])
            if isinstance(content_items, list):
                for item_idx, item in enumerate(content_items):
                    if item.get('type') == 'tool_use':
                        tool_call = {
                            'id': item.get('id'),
                            'type': item.get('type'),
                            'name': item.get('name'),
                            'input': item.get('input', {}),
                            'message_index': msg_idx,
                            'content_index': item_idx,
                            'sender': msg.get('sender'),
                            'created_at': msg.get('created_at')
                        }
                        tool_calls.append(tool_call)
                    elif item.get('type') == 'tool_result':
                        # Also capture tool results
                        tool_result = {
                            'id': item.get('tool_use_id'),
                            'type': item.get('type'),
                            'output': item.get('output'),
                            'is_error': item.get('is_error', False),
                            'message_index': msg_idx,
                            'content_index': item_idx,
                            'sender': msg.get('sender'),
                            'created_at': msg.get('created_at')
                        }
                        tool_calls.append(tool_result)
        
        if not tool_calls:
            return None
        
        # Save tool calls to JSONL file
        jsonl_path = base_path.with_suffix('.tool_calls.jsonl')
        with open(jsonl_path, 'w') as f:
            for idx, tool_call in enumerate(tool_calls):
                tool_call['line_number'] = idx + 1  # 1-based line numbers
                f.write(json.dumps(tool_call) + '\n')
        
        return jsonl_path
    
    def _extract_and_save_attachments(self, conversation: Dict[str, Any], base_path: Path) -> Dict[str, Any]:
        """Extract and save attachments from conversation. Stub implementation."""
        # TODO: Implement attachment extraction
        return {
            'attachments': [],
            'attachment_count': 0,
            'total_size': 0
        }
    
    def _format_conversation_markdown(self, conversation: Dict[str, Any], tool_calls_file: Optional[Path] = None, attachment_info: Optional[Dict[str, Any]] = None) -> str:
        """Format conversation as markdown with tool call references."""
        # First, generate the main content to extract patterns from it
        content_lines = []
        tool_call_counter = 1  # Track which tool call we're on
        
        # Header
        title = conversation.get('name', 'Untitled Conversation')
        content_lines.append(f"# {title}")
        content_lines.append("")
        
        # Messages
        content_lines.append("## Conversation")
        content_lines.append("")
        
        messages = conversation.get('chat_messages', [])
        for msg in messages:
            sender = msg.get('sender', 'unknown')
            if sender == 'human':
                content_lines.append("### 👤 Human")
            elif sender == 'assistant':
                content_lines.append("### 🤖 Assistant")
            else:
                content_lines.append(f"### ❓ {sender}")
            
            # Add start_time metadata from the first content item if available
            content_items = msg.get('content', [])
            if content_items and isinstance(content_items, list) and len(content_items) > 0:
                first_content = content_items[0]
                start_timestamp = first_content.get('start_timestamp')
                if start_timestamp:
                    content_lines.append(f"- start_time:: {start_timestamp}")
            
            content_lines.append("")
            
            # Process content items
            if content_items and isinstance(content_items, list):
                for item in content_items:
                    if item.get('type') == 'text':
                        content = item.get('text', '')
                        content_lines.append(content)
                    elif item.get('type') == 'tool_use' and tool_calls_file:
                        # Add tool call reference using safe format
                        tool_id = item.get('id', f'tool_call_{tool_call_counter}')
                        content_lines.append(f"{{Tool Call: {tool_id} → {tool_calls_file.name}:{tool_call_counter}}}")
                        tool_call_counter += 1
                    elif item.get('type') == 'tool_result' and tool_calls_file:
                        # Add tool result reference
                        tool_id = item.get('tool_use_id', f'tool_result_{tool_call_counter}')
                        content_lines.append(f"{{Tool Result: {tool_id} → {tool_calls_file.name}:{tool_call_counter}}}")
                        tool_call_counter += 1
            else:
                # Fallback to old text field
                content = msg.get('text', '')
                content_lines.append(content)
            
            content_lines.append("")
            content_lines.append("---")
            content_lines.append("")
        
        # Join content to extract patterns
        content_text = "\n".join(content_lines)
        
        # Extract patterns from the content
        patterns = self._extract_patterns(content_text, conversation)
        
        # Now build the full document with YAML frontmatter
        lines = []
        
        # YAML frontmatter
        lines.append("---")
        lines.append(f"conversation_title: \"{conversation.get('name', 'Untitled Conversation')}\"")
        lines.append(f"conversation_id: {conversation.get('uuid', 'unknown')}")
        lines.append(f"conversation_src: https://claude.ai/chat/{conversation.get('uuid', 'unknown')}")
        lines.append(f"conversation_created: {conversation.get('created_at', 'unknown')}")
        lines.append(f"conversation_updated: {conversation.get('updated_at', 'unknown')}")
        
        # Extract unique dates from messages
        conversation_dates = self._extract_conversation_dates(conversation)
        if conversation_dates:
            lines.append("conversation_dates:")
            for date in conversation_dates:
                lines.append(f"  - {date}")
        
        # Add pattern extraction results
        if patterns['markers']:
            lines.append("markers:")
            for marker in patterns['markers']:
                lines.append(f"  - type: \"{marker['type']}\"")
                # Escape quotes in content for YAML
                content = marker['content'].replace('"', '\\"')
                lines.append(f"    content: \"{content}\"")
                lines.append(f"    lines: {marker['lines']}")
        
        if patterns['float_calls']:
            lines.append("float_calls:")
            for call in patterns['float_calls']:
                lines.append(f"  - call: \"{call['call']}\"")
                # Escape quotes in content for YAML
                content = call['content'].replace('"', '\\"')
                lines.append(f"    content: \"{content}\"")
                lines.append(f"    lines: {call['lines']}")
        
        if patterns['tools_used']:
            lines.append(f"tools_used: {patterns['tools_used']}")
        
        lines.append(f"total_lines: {patterns['total_lines']}")
        
        lines.append("---")
        lines.append("")
        
        # Add the content
        lines.extend(content_lines)
        
        return "\n".join(lines)
    
    def _process_conversation(
        self,
        conversation: Dict[str, Any],
        output_dir: Path,
        format: str,
        by_date: bool,
    ) -> Path:
        """Process a single conversation and return the output path."""
        # Get creation date
        created_at = self._parse_datetime(conversation.get('created_at'))
        if created_at:
            date_prefix = created_at.strftime("%Y-%m-%d")
        else:
            date_prefix = datetime.now().strftime("%Y-%m-%d")
        
        # Generate safe filename (which strips any existing date prefix)
        title = self._safe_filename(conversation.get('name', 'untitled'))
        
        # Create filename with date prefix
        filename = f"{date_prefix} - {title}"
        
        # Determine output path
        if by_date and created_at:
            date_str = created_at.strftime("%Y-%m-%d")
            date_dir = output_dir / date_str
            date_dir.mkdir(exist_ok=True)
            base_dir = date_dir
        else:
            base_dir = output_dir
        
        # Handle naming conflicts by appending a number
        base_path = base_dir / filename
        counter = 1
        while (base_path.with_suffix('.json').exists() or 
               base_path.with_suffix('.md').exists()):
            base_path = base_dir / f"{filename}-{counter}"
            counter += 1
        
        # Save in requested format
        if format in ["json", "both"]:
            json_path = base_path.with_suffix('.json')
            with open(json_path, 'w') as f:
                json.dump(conversation, f, indent=2)
        
        # Extract tool calls if we're generating markdown
        tool_calls_file = None
        if format in ["markdown", "both"]:
            tool_calls_file = self._extract_and_save_tool_calls(conversation, base_path)
        
        if format in ["markdown", "both"]:
            md_path = base_path.with_suffix('.md')
            markdown = self._format_conversation_markdown(conversation, tool_calls_file)
            md_path.write_text(markdown)
        
        return base_path
    
    def _show_dry_run_summary(
        self,
        conversations: List[Dict[str, Any]],
        output_dir: Path,
        format: str,
        by_date: bool,
    ) -> None:
        """Show what would be processed in a dry run."""
        console.print("\n[yellow]DRY RUN - No files will be created[/yellow]\n")
        
        # Summary statistics
        total = len(conversations)
        by_date_count = {}
        
        for conv in conversations:
            created_at = self._parse_datetime(conv.get('created_at'))
            if created_at:
                date_str = created_at.strftime("%Y-%m-%d")
                by_date_count[date_str] = by_date_count.get(date_str, 0) + 1
        
        console.print(f"Would process [cyan]{total}[/cyan] conversations")
        console.print(f"Output directory: [cyan]{output_dir}[/cyan]")
        console.print(f"Format: [cyan]{format}[/cyan]")
        
        if by_date:
            console.print(f"\nConversations by date:")
            for date, count in sorted(by_date_count.items()):
                console.print(f"  {date}: {count} conversations")
        
        # Show sample filenames
        console.print(f"\nSample output filenames:")
        for conv in conversations[:5]:
            created_at = self._parse_datetime(conv.get('created_at'))
            if created_at:
                date_prefix = created_at.strftime("%Y-%m-%d")
            else:
                date_prefix = "YYYY-MM-DD"
            
            title = self._safe_filename(conv.get('name', 'untitled'))
            filename = f"{date_prefix} - {title}"
            
            if format == "json":
                console.print(f"  {filename}.json")
            elif format == "markdown":
                console.print(f"  {filename}.md")
            else:
                console.print(f"  {filename}.json")
                console.print(f"  {filename}.md")

    def _analyze_conversations(self, md_files: List[Path], jsonl_files: List[Path], conversations_dir: Path) -> Dict[str, Any]:
        """Analyze conversation files and extract key insights."""
        analysis = {
            "summary": {
                "total_conversations": len(md_files),
                "total_tool_calls": 0,
                "date_range": {"start": None, "end": None},
                "conversations_by_date": {},
            },
            "patterns": {
                "personas": {},
                "tools": {},
                "bridges": [],
                "contexts": [],
            },
            "insights": [],
            "tool_analysis": {
                "most_used_tools": {},
                "chroma_operations": 0,
                "obsidian_operations": 0,
                "memory_operations": 0,
            }
        }
        
        # Analyze each conversation
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract YAML frontmatter
                if content.startswith('---'):
                    try:
                        import yaml
                        yaml_end = content.find('---', 3) + 3
                        yaml_content = content[3:yaml_end-3]
                        metadata = yaml.safe_load(yaml_content)
                        
                        # Extract date info
                        if 'conversation_created' in metadata:
                            created = datetime.fromisoformat(metadata['conversation_created'].replace('Z', '+00:00'))
                            date_str = created.strftime('%Y-%m-%d')
                            
                            if analysis["summary"]["date_range"]["start"] is None or created < analysis["summary"]["date_range"]["start"]:
                                analysis["summary"]["date_range"]["start"] = created
                            if analysis["summary"]["date_range"]["end"] is None or created > analysis["summary"]["date_range"]["end"]:
                                analysis["summary"]["date_range"]["end"] = created
                            
                            analysis["summary"]["conversations_by_date"][date_str] = analysis["summary"]["conversations_by_date"].get(date_str, 0) + 1
                        
                        # Extract patterns from markers
                        if 'markers' in metadata:
                            for marker in metadata['markers']:
                                marker_type = marker.get('type', '')
                                if marker_type in ['lf1m', 'evna', 'karen', 'sysop', 'qtb']:
                                    analysis["patterns"]["personas"][marker_type] = analysis["patterns"]["personas"].get(marker_type, 0) + 1
                                elif marker_type == 'bridge':
                                    analysis["patterns"]["bridges"].append(marker.get('content', ''))
                                elif marker_type == 'ctx':
                                    analysis["patterns"]["contexts"].append(marker.get('content', ''))
                    except Exception:
                        pass
                
                # Count tool call markers
                tool_call_count = content.count('{Tool Call:')
                analysis["summary"]["total_tool_calls"] += tool_call_count
                
            except Exception as e:
                console.print(f"[yellow]Warning: Could not analyze {md_file}: {e}[/yellow]")
        
        # Analyze tool call files
        for jsonl_file in jsonl_files:
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            tool_call = json.loads(line)
                            tool_name = tool_call.get('name', 'unknown')
                            analysis["tool_analysis"]["most_used_tools"][tool_name] = analysis["tool_analysis"]["most_used_tools"].get(tool_name, 0) + 1
                            
                            # Count specific operation types
                            if 'chroma' in tool_name:
                                analysis["tool_analysis"]["chroma_operations"] += 1
                            elif 'obsidian' in tool_name:
                                analysis["tool_analysis"]["obsidian_operations"] += 1
                            elif 'memory' in tool_name or 'localhost' in tool_name:
                                analysis["tool_analysis"]["memory_operations"] += 1
            except Exception as e:
                console.print(f"[yellow]Warning: Could not analyze {jsonl_file}: {e}[/yellow]")
        
        # Generate insights
        if analysis["summary"]["total_conversations"] > 10:
            analysis["insights"].append("High conversation volume indicates active consciousness technology deployment")
        
        if analysis["tool_analysis"]["chroma_operations"] > 50:
            analysis["insights"].append("Significant Chroma usage suggests systematic knowledge base building")
        
        if len(analysis["patterns"]["personas"]) >= 3:
            analysis["insights"].append("Multiple persona activations indicate distributed consciousness system operational")
        
        if analysis["patterns"]["bridges"]:
            analysis["insights"].append(f"Bridge creation activity: {len(analysis['patterns']['bridges'])} bridges referenced")
        
        return analysis

    def _export_markdown_analysis(self, analysis: Dict[str, Any], output_path: Path, conversations_dir: Path) -> None:
        """Export analysis as markdown file."""
        content = f"""# Conversation Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}

**Source**: `{conversations_dir}`
**Generated**: {datetime.now().isoformat()}

## Summary

- **Total Conversations**: {analysis['summary']['total_conversations']}
- **Total Tool Calls**: {analysis['summary']['total_tool_calls']}
- **Date Range**: {analysis['summary']['date_range']['start'].strftime('%Y-%m-%d') if analysis['summary']['date_range']['start'] else 'Unknown'} to {analysis['summary']['date_range']['end'].strftime('%Y-%m-%d') if analysis['summary']['date_range']['end'] else 'Unknown'}

### Conversations by Date
"""
        
        for date, count in sorted(analysis['summary']['conversations_by_date'].items()):
            content += f"- **{date}**: {count} conversations\n"
        
        content += f"""
## Pattern Analysis

### Persona Activity
"""
        for persona, count in sorted(analysis['patterns']['personas'].items(), key=lambda x: x[1], reverse=True):
            content += f"- **{persona}**: {count} activations\n"
        
        content += f"""
### Tool Usage Analysis

**Infrastructure Operations**:
- **Chroma Operations**: {analysis['tool_analysis']['chroma_operations']} (knowledge persistence)
- **Obsidian Operations**: {analysis['tool_analysis']['obsidian_operations']} (documentation/bridges)
- **Memory Operations**: {analysis['tool_analysis']['memory_operations']} (context management)

**Most Used Tools**:
"""
        
        sorted_tools = sorted(analysis['tool_analysis']['most_used_tools'].items(), key=lambda x: x[1], reverse=True)
        for tool, count in sorted_tools[:10]:
            content += f"- **{tool}**: {count} calls\n"
        
        if analysis['patterns']['bridges']:
            content += f"""
### Bridge References
"""
            for bridge in analysis['patterns']['bridges'][:10]:  # Show first 10
                content += f"- {bridge}\n"
        
        if analysis['insights']:
            content += f"""
## Key Insights

"""
            for insight in analysis['insights']:
                content += f"- {insight}\n"
        
        content += f"""
## Technical Infrastructure Evidence

The enhanced tool call extraction reveals **consciousness technology in operation**:

- **{analysis['tool_analysis']['chroma_operations']} Chroma operations** = Active knowledge persistence and retrieval
- **{analysis['tool_analysis']['obsidian_operations']} Obsidian operations** = Bridge creation and documentation workflows  
- **{analysis['tool_analysis']['memory_operations']} Memory operations** = Context management and state preservation

### Pattern Recognition

"""
        
        if len(analysis['patterns']['personas']) >= 3:
            content += "- **Multi-persona system operational**: Evidence of distributed consciousness architecture\n"
        
        if analysis['tool_analysis']['chroma_operations'] > analysis['summary']['total_conversations']:
            content += "- **Active learning system**: More Chroma operations than conversations indicates systematic knowledge building\n"
        
        if analysis['patterns']['bridges']:
            content += f"- **Bridge infrastructure active**: {len(analysis['patterns']['bridges'])} bridge references indicate context restoration protocols\n"
        
        content += f"""
---

*Analysis generated by floatctl conversations analyze*  
*Enhanced metadata and tool call extraction enables systematic consciousness technology archaeology*
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _export_json_analysis(self, analysis: Dict[str, Any], output_path: Path) -> None:
        """Export analysis as JSON file."""
        # Convert datetime objects to strings for JSON serialization
        if analysis["summary"]["date_range"]["start"]:
            analysis["summary"]["date_range"]["start"] = analysis["summary"]["date_range"]["start"].isoformat()
        if analysis["summary"]["date_range"]["end"]:
            analysis["summary"]["date_range"]["end"] = analysis["summary"]["date_range"]["end"].isoformat()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)
        
        # Add consciousness analysis command
        @conversations.command()
        @click.option(
            "--export", "-e",
            type=click.Path(path_type=Path),
            help="Export consciousness analysis results to JSON file",
        )
        @click.option(
            "--contamination-level",
            type=click.Choice(["all", "standard", "moderate", "high"]),
            default="all",
            help="Filter by contamination level",
        )
        @click.option(
            "--project",
            help="Filter by work project name",
        )
        @click.option(
            "--limit", "-l",
            type=int,
            default=20,
            help="Limit number of results",
        )
        @click.pass_context
        def consciousness(
            ctx: click.Context,
            export: Optional[Path],
            contamination_level: str,
            project: Optional[str],
            limit: int,
        ) -> None:
            """Query consciousness analysis results."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            consciousness_middleware = ConsciousnessMiddleware(db_manager)
            
            # Build query conditions
            where_conditions = []
            params = []
            
            if contamination_level != "all":
                where_conditions.append("contamination_level = ?")
                params.append(contamination_level)
            
            if project:
                where_conditions.append("primary_project = ?")
                params.append(project)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Query consciousness analyses
            cursor = db_manager.execute_sql(f"""
                SELECT 
                    file_path, conversation_title, contamination_level, 
                    contamination_score, consciousness_urls, work_urls,
                    primary_project, dispatch_score, processed_at
                FROM consciousness_analysis 
                {where_clause}
                ORDER BY contamination_score DESC, dispatch_score DESC
                LIMIT ?
            """, params + [limit])
            
            results = cursor.fetchall()
            
            if not results:
                console.print("[yellow]No consciousness analysis results found[/yellow]")
                return
            
            # Display results table
            table = Table(title="🧬 Consciousness Analysis Results")
            table.add_column("File", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Contamination", style="red")
            table.add_column("Score", justify="right")
            table.add_column("URLs", justify="right")
            table.add_column("Project", style="green")
            table.add_column("Dispatch", justify="right")
            
            for row in results:
                contamination_style = {
                    "high": "red",
                    "moderate": "yellow", 
                    "standard": "green"
                }.get(row[2], "white")
                
                table.add_row(
                    Path(row[0]).name,
                    row[1][:40] + "..." if len(row[1]) > 40 else row[1],
                    f"[{contamination_style}]{row[2]}[/{contamination_style}]",
                    str(row[3]),
                    f"{row[4]}/{row[5]}",
                    row[6] or "-",
                    str(row[7])
                )
            
            console.print(table)
            
            # Show summary
            summary = consciousness_middleware.get_analysis_summary()
            console.print(f"\n[cyan]📊 Overall Summary:[/cyan]")
            console.print(f"  • Total analyses: {summary['total_analyses']}")
            console.print(f"  • High contamination: {summary['high_contamination']}")
            console.print(f"  • Average contamination score: {summary['avg_contamination_score']}")
            console.print(f"  • Strong dispatch opportunities: {summary['strong_dispatch_opportunities']}")
            
            # Export if requested
            if export:
                consciousness_middleware.export_analysis_results(export)
                console.print(f"\n[green]📊 Full analysis exported to: {export}[/green]")
        
        @conversations.command()
        @click.option(
            "--days", "-d",
            type=int,
            default=7,
            help="Number of days to look back",
        )
        @click.pass_context
        def last_week(ctx: click.Context, days: int) -> None:
            """What did I do last week?"""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            workflow = WorkflowIntelligence(db_manager)
            
            results = workflow.what_did_i_do_last_week(days)
            
            if not results['activities']:
                console.print(f"[yellow]No completed activities found in the last {days} days[/yellow]")
                return
            
            console.print(f"[cyan]📅 What you did in the last {days} days:[/cyan]")
            console.print(f"[dim]Total activities: {results['total_activities']}[/dim]\n")
            
            # Group by project
            for project, activities in results['by_project'].items():
                table = Table(title=f"📋 {project.replace('_', ' ').title()}")
                table.add_column("Activity", style="white", max_width=60)
                table.add_column("Date", style="dim")
                table.add_column("From", style="cyan", max_width=30)
                
                for activity in activities:
                    date_str = datetime.fromisoformat(activity['date']).strftime("%m-%d")
                    table.add_row(
                        activity['activity'],
                        date_str,
                        activity['conversation'][:27] + "..." if len(activity['conversation']) > 30 else activity['conversation']
                    )
                
                console.print(table)
        
        @conversations.command()
        @click.option(
            "--days", "-d",
            type=int,
            default=30,
            help="Number of days to look back",
        )
        @click.pass_context
        def nick_actions(ctx: click.Context, days: int) -> None:
            """Action items from Nick."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            workflow = WorkflowIntelligence(db_manager)
            
            results = workflow.action_items_from_nick(days)
            
            if not results['action_items']:
                console.print(f"[green]No open action items from Nick in the last {days} days[/green]")
                return
            
            console.print(f"[cyan]📋 Action items from Nick (last {days} days):[/cyan]")
            console.print(f"[dim]Total: {results['total_items']} | High priority: {results['high_priority']}[/dim]\n")
            
            table = Table(title="🎯 Nick's Action Items")
            table.add_column("Action", style="white", max_width=50)
            table.add_column("Priority", style="red")
            table.add_column("Context", style="dim", max_width=30)
            table.add_column("From", style="cyan", max_width=25)
            table.add_column("Date", style="dim")
            
            for item in results['action_items']:
                priority_style = {
                    'high': 'red',
                    'medium': 'yellow',
                    'low': 'green'
                }.get(item['priority'], 'white')
                
                date_str = datetime.fromisoformat(item['date']).strftime("%m-%d")
                
                table.add_row(
                    item['content'],
                    f"[{priority_style}]{item['priority']}[/{priority_style}]",
                    item['context'][:27] + "..." if len(item['context']) > 30 else item['context'],
                    item['conversation'][:22] + "..." if len(item['conversation']) > 25 else item['conversation'],
                    date_str
                )
            
            console.print(table)
        
        @conversations.command()
        @click.option(
            "--days", "-d",
            type=int,
            default=14,
            help="Number of days to look back",
        )
        @click.pass_context
        def priorities(ctx: click.Context, days: int) -> None:
            """What are my current priorities?"""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            workflow = WorkflowIntelligence(db_manager)
            
            results = workflow.current_priorities(days)
            
            console.print(f"[cyan]🎯 Current priorities (last {days} days):[/cyan]\n")
            
            # Show explicit priorities
            if results['explicit_priorities']:
                table = Table(title="📌 Explicit Priorities")
                table.add_column("Priority", style="white", max_width=50)
                table.add_column("Level", style="red")
                table.add_column("Project", style="green")
                table.add_column("From", style="cyan", max_width=25)
                
                for priority in results['explicit_priorities']:
                    priority_style = {
                        'high': 'red',
                        'medium': 'yellow',
                        'low': 'green'
                    }.get(priority['priority_level'], 'white')
                    
                    table.add_row(
                        priority['priority_text'],
                        f"[{priority_style}]{priority['priority_level']}[/{priority_style}]",
                        priority['project'],
                        priority['conversation'][:22] + "..." if len(priority['conversation']) > 25 else priority['conversation']
                    )
                
                console.print(table)
            
            # Show open action items as priorities
            if results['open_action_items']:
                table = Table(title="📋 Open Action Items")
                table.add_column("Action", style="white", max_width=50)
                table.add_column("Priority", style="red")
                table.add_column("Source", style="blue")
                table.add_column("From", style="cyan", max_width=25)
                
                for item in results['open_action_items']:
                    priority_style = {
                        'high': 'red',
                        'medium': 'yellow',
                        'low': 'green'
                    }.get(item['priority'], 'white')
                    
                    table.add_row(
                        item['content'],
                        f"[{priority_style}]{item['priority']}[/{priority_style}]",
                        item['source'],
                        item['conversation'][:22] + "..." if len(item['conversation']) > 25 else item['conversation']
                    )
                
                console.print(table)
            
            if not results['explicit_priorities'] and not results['open_action_items']:
                console.print(f"[yellow]No explicit priorities or open action items found in the last {days} days[/yellow]")
        
        @conversations.command()
        @click.option(
            "--days", "-d",
            type=int,
            default=30,
            help="How far back to look for forgotten tasks",
        )
        @click.pass_context
        def forgotten(ctx: click.Context, days: int) -> None:
            """What tasks might I have forgotten?"""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            workflow = WorkflowIntelligence(db_manager)
            
            results = workflow.forgotten_tasks(days)
            
            if not results['forgotten_items']:
                console.print(f"[green]No potentially forgotten tasks found (older than {days} days)[/green]")
                return
            
            console.print(f"[yellow]⚠️  Potentially forgotten tasks (older than {days} days):[/yellow]")
            console.print(f"[dim]Total: {results['total_forgotten']} | High priority: {results['high_priority_forgotten']}[/dim]\n")
            
            table = Table(title="🤔 Potentially Forgotten Tasks")
            table.add_column("Task", style="white", max_width=50)
            table.add_column("Priority", style="red")
            table.add_column("Source", style="blue")
            table.add_column("Age", style="dim")
            table.add_column("From", style="cyan", max_width=25)
            
            for item in results['forgotten_items']:
                priority_style = {
                    'high': 'red',
                    'medium': 'yellow',
                    'low': 'green'
                }.get(item['priority'], 'white')
                
                # Calculate age
                item_date = datetime.fromisoformat(item['date'])
                age_days = (datetime.now() - item_date).days
                age_str = f"{age_days}d"
                
                table.add_row(
                    item['content'],
                    f"[{priority_style}]{item['priority']}[/{priority_style}]",
                    item['source'],
                    age_str,
                    item['conversation'][:22] + "..." if len(item['conversation']) > 25 else item['conversation']
                )
            
            console.print(table)
        
        @conversations.command()
        @click.option(
            "--days", "-d",
            type=int,
            default=14,
            help="Number of days to look back",
        )
        @click.pass_context
        def meetings(ctx: click.Context, days: int) -> None:
            """Meeting follow-ups and action items."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            workflow = WorkflowIntelligence(db_manager)
            
            results = workflow.meeting_follow_ups(days)
            
            if not results['meeting_items']:
                console.print(f"[green]No open meeting follow-ups in the last {days} days[/green]")
                return
            
            console.print(f"[cyan]🤝 Meeting follow-ups (last {days} days):[/cyan]")
            console.print(f"[dim]Total items: {results['total_items']}[/dim]\n")
            
            table = Table(title="📝 Meeting Action Items")
            table.add_column("Action", style="white", max_width=50)
            table.add_column("Priority", style="red")
            table.add_column("Context", style="dim", max_width=30)
            table.add_column("From", style="cyan", max_width=25)
            table.add_column("Date", style="dim")
            
            for item in results['meeting_items']:
                priority_style = {
                    'high': 'red',
                    'medium': 'yellow',
                    'low': 'green'
                }.get(item['priority'], 'white')
                
                date_str = datetime.fromisoformat(item['date']).strftime("%m-%d")
                
                table.add_row(
                    item['content'],
                    f"[{priority_style}]{item['priority']}[/{priority_style}]",
                    item['context'][:27] + "..." if len(item['context']) > 30 else item['context'],
                    item['conversation'][:22] + "..." if len(item['conversation']) > 25 else item['conversation'],
                    date_str
                )
            
            console.print(table)