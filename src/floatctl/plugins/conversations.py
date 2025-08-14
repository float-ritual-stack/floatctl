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

from floatctl.plugin_manager import PluginBase
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
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register conversation commands."""
        
        @cli_group.group()
        @click.pass_context
        def conversations(ctx: click.Context) -> None:
            """Manage conversation exports."""
            pass
        
        @conversations.command()
        @click.argument("input_file", type=click.Path(exists=True, path_type=Path))
        @click.option(
            "--output-dir", "-o",
            type=click.Path(path_type=Path),
            help="Output directory for split conversations",
        )
        @click.option(
            "--format", "-f",
            type=click.Choice(["json", "markdown", "both"]),
            default="json",
            help="Output format",
        )
        @click.option(
            "--by-date",
            is_flag=True,
            help="Organize output files by date",
        )
        @click.option(
            "--filter-after",
            type=click.DateTime(),
            help="Only process conversations created after this date",
        )
        @click.option(
            "--dry-run",
            is_flag=True,
            help="Show what would be processed without actually doing it",
        )
        @click.option(
            "--consciousness-analysis",
            is_flag=True,
            default=False,
            help="Enable consciousness contamination analysis (default: disabled)",
        )
        @click.option(
            "--export-consciousness",
            type=click.Path(path_type=Path),
            help="Export consciousness analysis results to JSON file",
        )
        @click.option(
            "--sync-to-chroma",
            is_flag=True,
            help="Sync consciousness analysis results to Chroma for semantic search",
        )
        @click.pass_context
        def split(
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
            
            # Initialize consciousness middleware if enabled
            consciousness_middleware = None
            chroma_bridge = None
            workflow_intelligence = None
            if consciousness_analysis:
                consciousness_middleware = ConsciousnessMiddleware(db_manager)
                workflow_intelligence = WorkflowIntelligence(db_manager)
                console.print("[cyan]🧬 Consciousness analysis enabled[/cyan]")
                console.print("[cyan]📋 Workflow intelligence enabled[/cyan]")
                
                if sync_to_chroma:
                    chroma_bridge = ConsciousnessChromaBridge(db_manager)
                    console.print("[cyan]🔗 Chroma sync enabled[/cyan]")
            
            # Set default output directory
            if output_dir is None:
                output_dir = config.output_dir / "conversations"
            
            # Create logger for this command
            cmd_logger = log_command(
                "conversations.split",
                {
                    "input_file": str(input_file),
                    "output_dir": str(output_dir),
                    "format": format,
                    "by_date": by_date,
                    "filter_after": filter_after.isoformat() if filter_after else None,
                    "dry_run": dry_run,
                },
                plugin=self.name,
            )
            
            cmd_logger.info("starting_conversation_split")
            
            # Calculate file hash for change detection
            file_hash = self._calculate_file_hash(input_file)
            
            # Record the run (unless dry run)
            file_run = None
            if not dry_run:
                file_run = db_manager.record_file_run(
                    input_file,
                    plugin=self.name,
                    command="split",
                    file_hash=file_hash,
                    metadata={
                        "format": format,
                        "by_date": by_date,
                        "filter_after": filter_after.isoformat() if filter_after else None,
                    },
                )
            
            try:
                # Load conversations
                file_logger = log_file_operation("read", input_file)
                file_logger.info("loading_conversations")
                
                with open(input_file, 'r') as f:
                    conversations = json.load(f)
                
                if not isinstance(conversations, list):
                    raise ValueError("Expected array of conversations")
                
                console.print(f"[green]Found {len(conversations)} conversations[/green]")
                
                # Filter conversations if needed
                if filter_after:
                    original_count = len(conversations)
                    conversations = self._filter_conversations(conversations, filter_after)
                    filtered_count = original_count - len(conversations)
                    if filtered_count > 0:
                        console.print(f"[yellow]Filtered out {filtered_count} conversations before {filter_after}[/yellow]")
                
                if dry_run:
                    # Show what would be processed
                    self._show_dry_run_summary(conversations, output_dir, format, by_date)
                    return
                
                # Create output directory
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Process conversations with progress bar
                processed = 0
                errors = 0
                consciousness_analyses = []
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task("Processing conversations...", total=len(conversations))
                    
                    for conv in conversations:
                        try:
                            artifact_path = self._process_conversation(
                                conv, output_dir, format, by_date
                            )
                            
                            # Run consciousness analysis if enabled
                            if consciousness_middleware and artifact_path:
                                try:
                                    # Read the generated file content for analysis
                                    if artifact_path.suffix == '.md':
                                        with open(artifact_path, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                        
                                        # Analyze consciousness patterns
                                        analysis = consciousness_middleware.analyze_conversation(
                                            artifact_path, conv, content
                                        )
                                        
                                        # Save analysis to database
                                        consciousness_middleware.save_analysis(analysis)
                                        consciousness_analyses.append(analysis)
                                        
                                        # Extract workflow intelligence
                                        if workflow_intelligence:
                                            workflow_intelligence.extract_workflow_intelligence(conv, content)
                                        
                                        # Sync to Chroma if enabled
                                        if chroma_bridge:
                                            chroma_bridge.sync_analysis_to_chroma(analysis)
                                        
                                        # Show alerts in console (optional - can be disabled)
                                        for alert in analysis.alerts[:2]:  # Show max 2 alerts per conversation
                                            console.print(f"  [yellow]{alert}[/yellow]")
                                        
                                except Exception as e:
                                    console.print(f"  [red]Consciousness analysis failed: {e}[/red]")
                            
                            # Record artifact in database
                            if file_run:
                                db_manager.add_artifact(
                                    file_run.id,
                                    artifact_type="conversation",
                                    artifact_path=artifact_path,
                                    artifact_id=conv.get("uuid"),
                                    artifact_name=conv.get("name"),
                                    created_at=self._parse_datetime(conv.get("created_at")),
                                    metadata={
                                        "format": format,
                                        "message_count": len(conv.get("chat_messages", [])),
                                    },
                                )
                            
                            processed += 1
                            
                        except Exception as e:
                            errors += 1
                            console.print(f"[red]Error processing conversation: {e}[/red]")
                            cmd_logger.error(
                                "conversation_processing_error",
                                error=str(e),
                                conversation_id=conv.get("uuid", "unknown"),
                            )
                        
                        progress.update(task, advance=1)
                
                # Complete the run
                if file_run:
                    db_manager.complete_file_run(
                        file_run.id,
                        status=ProcessingStatus.COMPLETED if errors == 0 else ProcessingStatus.COMPLETED,
                        output_path=output_dir,
                        items_processed=processed,
                        metadata={
                            "errors": errors,
                            "total_conversations": len(conversations),
                        },
                    )
                
                # Show summary
                console.print(f"\n[green]✓ Successfully processed {processed} conversations[/green]")
                if errors > 0:
                    console.print(f"[yellow]⚠ {errors} conversations had errors[/yellow]")
                
                # Show consciousness analysis summary
                if consciousness_middleware and consciousness_analyses:
                    summary = consciousness_middleware.get_analysis_summary()
                    console.print(f"\n[cyan]🧬 Consciousness Analysis Summary:[/cyan]")
                    console.print(f"  • Total analyses: {summary['total_analyses']}")
                    console.print(f"  • High contamination: {summary['high_contamination']}")
                    console.print(f"  • Moderate contamination: {summary['moderate_contamination']}")
                    console.print(f"  • Conversations with consciousness URLs: {summary['conversations_with_consciousness_urls']}")
                    console.print(f"  • Strong dispatch opportunities: {summary['strong_dispatch_opportunities']}")
                    console.print(f"  • Average contamination score: {summary['avg_contamination_score']}")
                    console.print(f"  • Average dispatch score: {summary['avg_dispatch_score']}")
                
                # Export consciousness analysis if requested
                if export_consciousness and consciousness_middleware:
                    consciousness_middleware.export_analysis_results(export_consciousness)
                    console.print(f"\n[green]📊 Consciousness analysis exported to: {export_consciousness}[/green]")
                
                cmd_logger.info(
                    "conversation_split_completed",
                    processed=processed,
                    errors=errors,
                    total=len(conversations),
                )
                
            except Exception as e:
                cmd_logger.error("conversation_split_failed", error=str(e), exc_info=True)
                
                if file_run:
                    db_manager.complete_file_run(
                        file_run.id,
                        status=ProcessingStatus.FAILED,
                        error_message=str(e),
                    )
                
                console.print(f"[red]Error: {e}[/red]")
                raise click.ClickException(str(e))
        
        @conversations.command()
        @click.argument("file_path", type=click.Path(exists=True, path_type=Path))
        @click.pass_context
        def history(ctx: click.Context, file_path: Path) -> None:
            """Show processing history for a conversations file."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            
            history = db_manager.get_file_history(file_path)
            
            if not history:
                console.print(f"[yellow]No processing history found for {file_path}[/yellow]")
                return
            
            # Create table
            table = Table(title=f"Processing History: {file_path.name}")
            table.add_column("Date", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Items", justify="right")
            table.add_column("Duration", justify="right")
            table.add_column("Output")
            
            for run in history:
                status_style = {
                    ProcessingStatus.COMPLETED: "green",
                    ProcessingStatus.FAILED: "red",
                    ProcessingStatus.PROCESSING: "yellow",
                    ProcessingStatus.NEEDS_REPROCESS: "magenta",
                }.get(run.status, "white")
                
                table.add_row(
                    run.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                    f"[{status_style}]{run.status.value}[/{status_style}]",
                    str(run.items_processed or "-"),
                    f"{run.duration_seconds}s" if run.duration_seconds else "-",
                    str(Path(run.output_path).name) if run.output_path else "-",
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