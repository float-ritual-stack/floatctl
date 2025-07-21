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
        @click.pass_context
        def split(
            ctx: click.Context,
            input_file: Path,
            output_dir: Optional[Path],
            format: str,
            by_date: bool,
            filter_after: Optional[datetime],
            dry_run: bool,
        ) -> None:
            """Split a conversations export file into individual conversation files."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            
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
    
    def _format_conversation_markdown(self, conversation: Dict[str, Any], tool_calls_file: Optional[Path]) -> str:
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