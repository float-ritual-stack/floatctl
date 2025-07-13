"""Plugin for processing conversation exports."""

import json
import hashlib
from pathlib import Path
from datetime import datetime
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
        filtered = []
        for conv in conversations:
            created_at = self._parse_datetime(conv.get("created_at"))
            if created_at and created_at >= after_date:
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
    
    def _safe_filename(self, text: str, max_length: int = 50) -> str:
        """Convert text to safe filename."""
        if not text:
            return "untitled"
        # Remove special characters and limit length
        clean = re.sub(r'[^a-zA-Z0-9 \\-_]', '_', text)
        return clean[:max_length].strip()
    
    def _format_conversation_markdown(self, conversation: Dict[str, Any]) -> str:
        """Format conversation as markdown."""
        lines = []
        
        # Header
        title = conversation.get('name', 'Untitled Conversation')
        lines.append(f"# {title}")
        lines.append("")
        
        # Metadata
        lines.append("## Metadata")
        lines.append(f"- **ID**: `{conversation.get('uuid', 'unknown')}`")
        lines.append(f"- **Created**: {conversation.get('created_at', 'unknown')}")
        lines.append(f"- **Updated**: {conversation.get('updated_at', 'unknown')}")
        lines.append("")
        
        # Messages
        lines.append("## Conversation")
        lines.append("")
        
        messages = conversation.get('chat_messages', [])
        for msg in messages:
            sender = msg.get('sender', 'unknown')
            if sender == 'human':
                lines.append("### 👤 Human")
            elif sender == 'assistant':
                lines.append("### 🤖 Assistant")
            else:
                lines.append(f"### ❓ {sender}")
            
            lines.append("")
            content = msg.get('text', '')
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\\n".join(lines)
    
    def _process_conversation(
        self,
        conversation: Dict[str, Any],
        output_dir: Path,
        format: str,
        by_date: bool,
    ) -> Path:
        """Process a single conversation and return the output path."""
        # Generate timestamp
        created_at = self._parse_datetime(conversation.get('created_at'))
        if created_at:
            timestamp = created_at.strftime("%Y%m%d_%H%M%S")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate safe filename
        title = self._safe_filename(conversation.get('name', 'untitled'))
        uuid = conversation.get('uuid', 'unknown')[:8]
        filename = f"{timestamp}_{title}_{uuid}"
        
        # Determine output path
        if by_date and created_at:
            date_str = created_at.strftime("%Y-%m-%d")
            date_dir = output_dir / date_str
            date_dir.mkdir(exist_ok=True)
            base_path = date_dir / filename
        else:
            base_path = output_dir / filename
        
        # Save in requested format
        if format in ["json", "both"]:
            json_path = base_path.with_suffix('.json')
            with open(json_path, 'w') as f:
                json.dump(conversation, f, indent=2)
        
        if format in ["markdown", "both"]:
            md_path = base_path.with_suffix('.md')
            markdown = self._format_conversation_markdown(conversation)
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
        console.print("\\n[yellow]DRY RUN - No files will be created[/yellow]\\n")
        
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
            console.print(f"\\nConversations by date:")
            for date, count in sorted(by_date_count.items()):
                console.print(f"  {date}: {count} conversations")
        
        # Show sample filenames
        console.print(f"\\nSample output filenames:")
        for conv in conversations[:5]:
            created_at = self._parse_datetime(conv.get('created_at'))
            if created_at:
                timestamp = created_at.strftime("%Y%m%d_%H%M%S")
            else:
                timestamp = "YYYYMMDD_HHMMSS"
            
            title = self._safe_filename(conv.get('name', 'untitled'))
            uuid = conversation.get('uuid', 'unknown')[:8]
            filename = f"{timestamp}_{title}_{uuid}"
            
            if format == "json":
                console.print(f"  {filename}.json")
            elif format == "markdown":
                console.print(f"  {filename}.md")
            else:
                console.print(f"  {filename}.json")
                console.print(f"  {filename}.md")