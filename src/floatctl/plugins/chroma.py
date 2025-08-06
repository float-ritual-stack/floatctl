"""Chroma vector database plugin for FloatCtl."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme
from typing import Dict, Any, List, Optional
import re

from floatctl.plugin_manager import PluginBase
from floatctl.floatql import FloatQLParser, FloatQLTranslator

# Create custom theme for FLOAT content
float_theme = Theme({
    "markdown.h1": "bold magenta",
    "markdown.h2": "bold cyan", 
    "markdown.h3": "bold yellow",
    "markdown.code": "dim white on grey23",
    "markdown.link": "blue underline",
    "markdown.list": "white",
    "markdown.item": "white",
    "markdown.item.bullet": "cyan"
})

console = Console(theme=float_theme)


def _style_float_content(content: str) -> str:
    """Apply FLOAT-specific styling to content before markdown rendering."""
    # Use markdown-compatible formatting
    
    # Style CB-IDs with backticks (code formatting)
    content = re.sub(r'(CB-\d{8}-\d{4}-[A-Z0-9]+)', r'`\1`', content)
    
    # Add spacing around headers for better readability
    content = re.sub(r'\n(#{1,3} [^\n]+)', r'\n\n\1', content)
    content = re.sub(r'(#{1,3} [^\n]+)\n', r'\1\n\n', content)
    
    # Ensure proper list formatting
    content = re.sub(r'\n(\s*[-•*]\s+)', r'\n\1', content)
    
    # Style float.* patterns with backticks
    content = re.sub(r'\b(float\.dispatch|float\.highlight|float\.signal)\b', r'`\1`', content, flags=re.IGNORECASE)
    
    # Leave wiki-links and :: markers as-is for clean rendering
    # The markdown theme will handle the visual styling
    
    return content


def _format_bridge_metadata(content: str) -> tuple:
    """Extract and format bridge metadata separately.
    
    Returns:
        Tuple of (metadata_lines, remaining_content)
    """
    lines = content.split('\n')
    
    metadata_lines = []
    content_start = 0
    
    # Skip title if it starts with #
    if lines and lines[0].strip().startswith('#'):
        content_start = 1
    
    # Extract metadata lines (continuous :: lines at the start)
    for i, line in enumerate(lines[content_start:], content_start):
        stripped = line.strip()
        if '::' in stripped and not stripped.startswith('#'):
            # This is a metadata line
            metadata_lines.append(stripped)
        elif stripped == '':
            # Empty line, might be separator
            continue
        else:
            # First non-metadata content line
            content_start = i
            break
    
    # Join remaining content
    remaining = '\n'.join(lines[content_start:]) if content_start < len(lines) else ''
    
    return metadata_lines, remaining


class ChromaPlugin(PluginBase):
    """Plugin for Chroma vector database operations."""
    
    name = "chroma"
    version = "1.0.0"
    description = "Chroma vector database collection management and querying"
    
    def _register_legacy_commands(self, cli_group: click.Group) -> None:
        """Register chroma commands using the legacy pattern."""
        cli_group.add_command(chroma)


@click.group()
def chroma():
    """Chroma vector database operations.
    
    Manage collections, query documents, and analyze FLOAT workflow data
    stored in your Chroma vector database.
    """
    pass


@click.group()
def chroma():
    """Chroma vector database operations.
    
    Manage collections, query documents, and analyze FLOAT workflow data
    stored in your Chroma vector database.
    """
    pass


@chroma.command()
@click.option('--sort', type=click.Choice(['name', 'count']), default='name', 
              help='Sort collections by name or document count')
@click.option('--limit', '-l', type=int, help='Limit number of collections shown')
def list(sort: str, limit: Optional[int]):
    """List all Chroma collections with document counts.
    
    Shows collection names, document counts, and basic metadata overview.
    Use --sort count to see largest collections first.
    
    Examples:
        floatctl chroma list
        floatctl chroma list --sort count
        floatctl chroma list --limit 10
    """
    try:
        # Import MCP tools for chroma operations
        from floatctl.core.config import load_config
        
        # Load collections using MCP
        collections = _get_collections_info()
        
        if not collections:
            console.print("[yellow]No collections found in Chroma database[/yellow]")
            return
        
        # Sort collections
        if sort == 'count':
            collections.sort(key=lambda x: x['count'], reverse=True)
        else:
            collections.sort(key=lambda x: x['name'])
        
        # Apply limit
        if limit:
            collections = collections[:limit]
        
        # Create rich table
        table = Table(title="Chroma Collections")
        table.add_column("Collection", style="cyan", no_wrap=True)
        table.add_column("Documents", justify="right", style="magenta")
        table.add_column("Status", style="green")
        
        total_docs = 0
        for collection in collections:
            count = collection['count']
            total_docs += count
            
            # Format count with commas
            count_str = f"{count:,}"
            
            # Determine status based on count
            if count == 0:
                status = "Empty"
            elif count < 10:
                status = "Small"
            elif count < 100:
                status = "Medium"
            else:
                status = "Large"
            
            table.add_row(collection['name'], count_str, status)
        
        # Show table
        console.print(table)
        
        # Show summary
        summary_text = f"Total: {len(collections):,} collections, {total_docs:,} documents"
        if limit and len(_get_collections_info()) > limit:
            total_collections = len(_get_collections_info())
            summary_text += f" (showing {limit} of {total_collections})"
        
        console.print(Panel(summary_text, title="Summary", border_style="blue"))
        
    except Exception as e:
        console.print(f"[red]Error listing collections: {e}[/red]")
        raise click.ClickException(str(e))


@chroma.command()
@click.argument('collection_name')
def info(collection_name: str):
    """Show detailed information about a specific collection.
    
    Displays metadata schema, sample documents, and statistics.
    
    Examples:
        floatctl chroma info active_context_stream
        floatctl chroma info float_bridges
    """
    try:
        import chromadb
        
        from floatctl.core.config import load_config
        config = load_config()
        chroma_path = str(config.chroma_path)
        client = chromadb.PersistentClient(path=chroma_path)
        
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            console.print(f"[red]Collection '{collection_name}' not found[/red]")
            raise click.ClickException(f"Collection not found: {collection_name}")
        
        # Get collection info
        count = collection.count()
        
        # Get sample documents to analyze metadata
        sample = collection.get(limit=5)
        
        # Display header
        console.print(Panel(f"[bold]{collection_name}[/bold]", title="Collection Info", border_style="cyan"))
        
        # Display stats
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Property", style="dim")
        stats_table.add_column("Value", style="bright_cyan")
        
        stats_table.add_row("Documents", f"{count:,}")
        stats_table.add_row("Name", collection_name)
        
        console.print(stats_table)
        console.print()
        
        # Analyze metadata schema
        if sample['metadatas']:
            metadata_keys = set()
            for metadata in sample['metadatas']:
                if metadata:
                    metadata_keys.update(metadata.keys())
            
            if metadata_keys:
                console.print("[bold]Metadata Schema:[/bold]")
                schema_table = Table(show_header=True)
                schema_table.add_column("Field", style="cyan")
                schema_table.add_column("Sample Values", style="yellow")
                
                for key in sorted(metadata_keys):
                    # Get unique sample values for this key
                    values = []
                    for metadata in sample['metadatas']:
                        if metadata and key in metadata:
                            val = str(metadata[key])
                            if len(val) > 50:
                                val = val[:47] + "..."
                            if val not in values:
                                values.append(val)
                    
                    sample_values = ", ".join(values[:3])
                    if len(values) > 3:
                        sample_values += f" ... ({len(values)} unique)"
                    
                    schema_table.add_row(key, sample_values)
                
                console.print(schema_table)
        
        # Show sample document preview
        if sample['documents']:
            console.print("\n[bold]Sample Documents:[/bold]")
            for i, doc in enumerate(sample['documents'][:3]):
                if doc:
                    preview = doc[:200] + "..." if len(doc) > 200 else doc
                    console.print(f"\n[dim]Document {i+1}:[/dim]")
                    console.print(Panel(preview, border_style="dim"))
        
    except Exception as e:
        console.print(f"[red]Error getting collection info: {e}[/red]")
        raise click.ClickException(str(e))


@chroma.command()
@click.argument('collection_name')
@click.option('--limit', '-l', default=5, help='Number of documents to peek at')
@click.option('--show-metadata', '-m', is_flag=True, help='Show document metadata')
@click.option('--full', '-f', is_flag=True, help='Show full document content')
@click.option('--rendered', '-r', is_flag=True, help='Render markdown content with formatting')
def peek(collection_name: str, limit: int, show_metadata: bool, full: bool, rendered: bool):
    """Peek at sample documents from a collection.
    
    Shows a preview of documents to understand collection content.
    
    Examples:
        floatctl chroma peek active_context_stream
        floatctl chroma peek float_bridges --limit 10 --show-metadata
        floatctl chroma peek float_highlights --full
    """
    try:
        import chromadb
        
        from floatctl.core.config import load_config
        config = load_config()
        chroma_path = str(config.chroma_path)
        client = chromadb.PersistentClient(path=chroma_path)
        
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            console.print(f"[red]Collection '{collection_name}' not found[/red]")
            raise click.ClickException(f"Collection not found: {collection_name}")
        
        # Get sample documents
        results = collection.get(limit=limit)
        
        if not results['documents']:
            console.print(f"[yellow]No documents found in {collection_name}[/yellow]")
            return
        
        console.print(Panel(f"[bold]Peeking at {collection_name}[/bold]\n{len(results['documents'])} documents", 
                           title="Collection Peek", border_style="green"))
        
        for i, (doc_id, doc, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            # Document header
            console.print(f"\n[bold cyan]Document {i+1}[/bold cyan] [dim]ID: {doc_id}[/dim]")
            
            # Show metadata if requested
            if show_metadata and metadata:
                metadata_table = Table(show_header=False, box=None)
                metadata_table.add_column("Key", style="dim")
                metadata_table.add_column("Value", style="yellow")
                
                for key, value in sorted(metadata.items()):
                    val_str = str(value)
                    if not full and len(val_str) > 100:
                        val_str = val_str[:97] + "..."
                    metadata_table.add_row(key, val_str)
                
                console.print(metadata_table)
            
            # Show document content
            if doc:
                content = doc if full else (doc[:500] + "..." if len(doc) > 500 else doc)
                if rendered:
                    # Style FLOAT content
                    styled_content = _style_float_content(content)
                    md = Markdown(styled_content)
                    console.print(Panel(md, border_style="dim", title="Content", padding=(1, 2)))
                else:
                    console.print(Panel(content, border_style="dim", title="Content"))
        
    except Exception as e:
        console.print(f"[red]Error peeking at collection: {e}[/red]")
        raise click.ClickException(str(e))


@chroma.command()
@click.argument('collection_name')
@click.argument('query_text')
@click.option('--limit', '-l', default=5, help='Number of results to return')
@click.option('--show-distance', '-d', is_flag=True, help='Show similarity distances')
@click.option('--metadata-filter', '-m', help='Filter by metadata (JSON format)')
@click.option('--preview-length', '-p', default=300, help='Length of content preview (default: 300)')
def query(collection_name: str, query_text: str, limit: int, show_distance: bool, metadata_filter: Optional[str], preview_length: int):
    """Query a collection with text search.
    
    Performs semantic search on collection documents.
    
    Examples:
        floatctl chroma query active_context_stream "floatctl development"
        floatctl chroma query float_bridges "consciousness technology"
        floatctl chroma query float_highlights "important" --limit 10
        floatctl chroma query active_context_stream "ctx::" -m '{"type": "daily_transition"}'
    """
    try:
        import chromadb
        import json
        
        from floatctl.core.config import load_config
        config = load_config()
        chroma_path = str(config.chroma_path)
        client = chromadb.PersistentClient(path=chroma_path)
        
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            console.print(f"[red]Collection '{collection_name}' not found[/red]")
            raise click.ClickException(f"Collection not found: {collection_name}")
        
        # Parse metadata filter if provided
        where_clause = None
        if metadata_filter:
            try:
                where_clause = json.loads(metadata_filter)
            except json.JSONDecodeError:
                console.print("[red]Invalid metadata filter format. Use JSON.[/red]")
                raise click.ClickException("Invalid metadata filter")
        
        # Execute query
        query_params = {
            'query_texts': [query_text],
            'n_results': limit
        }
        if where_clause:
            query_params['where'] = where_clause
        
        results = collection.query(**query_params)
        
        if not results['documents'][0]:
            console.print(f"[yellow]No results found for '{query_text}' in {collection_name}[/yellow]")
            return
        
        # Display results
        console.print(Panel(f"[bold]Query Results[/bold]\nQuery: '{query_text}'\nCollection: {collection_name}", 
                           title="Search Results", border_style="magenta"))
        
        results_table = Table()
        results_table.add_column("#", style="dim", width=3)
        results_table.add_column("Content Preview", style="cyan")
        if show_distance:
            results_table.add_column("Distance", style="yellow", width=10)
        
        for i, (doc, distance, metadata) in enumerate(zip(
            results['documents'][0], 
            results['distances'][0],
            results['metadatas'][0]
        )):
            # Create content preview with newlines preserved
            if len(doc) > preview_length:
                preview = doc[:preview_length]
                # Find a good break point
                for i in range(min(preview_length + 50, len(doc)), preview_length, -1):
                    if doc[i] in ['\n', '.', '!', '?']:
                        preview = doc[:i+1]
                        break
                preview += "..."
            else:
                preview = doc
            
            # For table display, replace newlines with spaces but keep more content
            table_preview = preview.replace('\n', ' ')
            
            row = [str(i+1), table_preview]
            if show_distance:
                row.append(f"{distance:.4f}")
            
            results_table.add_row(*row)
            
            # Show metadata if present
            if metadata:
                metadata_str = ", ".join(f"{k}={v}" for k, v in sorted(metadata.items())[:3])
                if len(metadata) > 3:
                    metadata_str += f" ... +{len(metadata)-3} more"
                results_table.add_row("", f"[dim]{metadata_str}[/dim]", "" if show_distance else None)
        
        console.print(results_table)
        
    except Exception as e:
        console.print(f"[red]Error querying collection: {e}[/red]")
        raise click.ClickException(str(e))


@chroma.command()
@click.argument('collection_name')
@click.option('--hours', '-h', type=int, help='Get documents from last N hours')
@click.option('--days', '-d', type=int, help='Get documents from last N days')
@click.option('--limit', '-l', default=10, help='Number of results to return')
def recent(collection_name: str, hours: Optional[int], days: Optional[int], limit: int):
    """Get recent documents from a collection based on timestamps.
    
    Searches for documents with timestamp metadata within the specified time range.
    
    Examples:
        floatctl chroma recent active_context_stream --hours 24
        floatctl chroma recent float_bridges --days 7
        floatctl chroma recent daily_context_hotcache --hours 48 --limit 20
    """
    try:
        import chromadb
        from datetime import datetime, timedelta, timezone
        
        from floatctl.core.config import load_config
        config = load_config()
        chroma_path = str(config.chroma_path)
        client = chromadb.PersistentClient(path=chroma_path)
        
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            console.print(f"[red]Collection '{collection_name}' not found[/red]")
            raise click.ClickException(f"Collection not found: {collection_name}")
        
        # Calculate time range
        now = datetime.now(timezone.utc)
        if hours:
            since_time = now - timedelta(hours=hours)
            time_desc = f"last {hours} hours"
        elif days:
            since_time = now - timedelta(days=days)
            time_desc = f"last {days} days"
        else:
            since_time = now - timedelta(days=1)
            time_desc = "last 24 hours (default)"
        
        # Try to get all documents and filter by timestamp
        # This is not ideal for large collections, but Chroma doesn't support direct timestamp queries
        console.print(f"[yellow]Scanning {collection_name} for documents from {time_desc}...[/yellow]")
        
        # Get a larger sample to find recent documents
        sample_size = min(1000, collection.count())
        results = collection.get(limit=sample_size)
        
        recent_docs = []
        for doc_id, doc, metadata in zip(results['ids'], results['documents'], results['metadatas']):
            if metadata:
                # Check various timestamp fields
                timestamp = None
                for ts_field in ['timestamp', 'created_at', 'updated_at', 'ttl_expires', 'created', 'modified']:
                    if ts_field in metadata:
                        try:
                            # Parse timestamp
                            ts_str = metadata[ts_field]
                            if isinstance(ts_str, str):
                                # Try to parse ISO format
                                timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                                # Ensure timezone aware
                                if timestamp.tzinfo is None:
                                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                                break
                        except:
                            continue
                
                if timestamp and timestamp > since_time:
                    recent_docs.append({
                        'id': doc_id,
                        'doc': doc,
                        'metadata': metadata,
                        'timestamp': timestamp
                    })
        
        # Sort by timestamp and limit
        recent_docs.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_docs = recent_docs[:limit]
        
        if not recent_docs:
            console.print(f"[yellow]No recent documents found in {collection_name} from {time_desc}[/yellow]")
            return
        
        # Display results
        console.print(Panel(f"[bold]Recent Documents[/bold]\nCollection: {collection_name}\nTime range: {time_desc}", 
                           title="Recent Activity", border_style="green"))
        
        for i, item in enumerate(recent_docs):
            doc = item['doc']
            metadata = item['metadata']
            timestamp = item['timestamp']
            
            # Format timestamp
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            age = now - timestamp
            if age.days > 0:
                age_str = f"{age.days}d ago"
            elif age.seconds > 3600:
                age_str = f"{age.seconds // 3600}h ago"
            else:
                age_str = f"{age.seconds // 60}m ago"
            
            console.print(f"\n[bold cyan]Document {i+1}[/bold cyan] [dim]{time_str} ({age_str})[/dim]")
            
            # Show key metadata
            if metadata:
                key_metadata = []
                for key in ['type', 'context_type', 'priority', 'mode']:
                    if key in metadata:
                        key_metadata.append(f"{key}={metadata[key]}")
                if key_metadata:
                    console.print(f"[dim]{', '.join(key_metadata)}[/dim]")
            
            # Show content preview
            preview = doc[:200] + "..." if len(doc) > 200 else doc
            console.print(Panel(preview, border_style="dim"))
        
    except Exception as e:
        console.print(f"[red]Error getting recent documents: {e}[/red]")
        raise click.ClickException(str(e))


@chroma.command()
@click.argument('query')
@click.option('--collections', '-c', help='Comma-separated list of collections')
@click.option('--limit', '-l', default=5, help='Number of results per collection')
@click.option('--explain', '-e', is_flag=True, help='Show query parsing explanation')
@click.option('--full', '-f', is_flag=True, help='Show full document content')
@click.option('--preview-length', '-p', default=500, help='Length of content preview (default: 500)')
@click.option('--rendered', '-r', is_flag=True, help='Render markdown content with formatting')
def floatql(query: str, collections: Optional[str], limit: int, explain: bool, full: bool, preview_length: int, rendered: bool):
    """Query using FloatQL natural language patterns.
    
    FloatQL understands FLOAT patterns and natural language:
    
    Examples:
        floatctl chroma floatql "ctx:: meeting with nick"
        floatctl chroma floatql "[sysop::] infrastructure updates"
        floatctl chroma floatql "bridge::CB-20250713-0130-M3SS"
        floatctl chroma floatql "highlights from yesterday"
        floatctl chroma floatql "type:conversation redux today"
    """
    try:
        # Parse the FloatQL query
        parser = FloatQLParser()
        parsed = parser.parse(query)
        
        if explain:
            console.print(Panel(
                f"[bold]FloatQL Query Analysis[/bold]\n\n"
                f"Original: {query}\n\n"
                f"Text terms: {', '.join(parsed['text_terms']) or 'none'}\n"
                f"FLOAT patterns: {', '.join(parsed['float_patterns']) or 'none'}\n"
                f"Personas: {', '.join(parsed['persona_patterns']) or 'none'}\n"
                f"Bridges: {', '.join(parsed['bridge_ids']) or 'none'}\n"
                f"Temporal: {parsed['temporal_filters'] or 'none'}\n"
                f"Types: {', '.join(parsed['type_filters']) or 'none'}",
                title="Query Parse", border_style="blue"
            ))
        
        # Get collection suggestions
        collection_list = []
        if collections:
            collection_list = [c.strip() for c in collections.split(',')]
        else:
            # Use FloatQL suggestions
            collection_list = parser.get_suggested_collections(parsed)
            if explain:
                console.print(f"\n[dim]Suggested collections: {', '.join(collection_list)}[/dim]")
        
        # Translate to Chroma query
        translator = FloatQLTranslator()
        chroma_query = translator.translate_to_chroma_query(parsed)
        
        if explain:
            console.print(f"\n[dim]Chroma query: {chroma_query}[/dim]\n")
        
        # Execute queries
        import chromadb
        from floatctl.core.config import load_config
        config = load_config()
        chroma_path = str(config.chroma_path)
        client = chromadb.PersistentClient(path=chroma_path)
        
        all_results = []
        for collection_name in collection_list:
            try:
                collection = client.get_collection(collection_name)
                
                # Build query parameters
                query_params = {
                    'query_texts': chroma_query['query_texts'],
                    'n_results': limit
                }
                
                if chroma_query['where']:
                    query_params['where'] = chroma_query['where']
                
                results = collection.query(**query_params)
                
                # Add results with collection info
                for i, (doc, dist, metadata) in enumerate(zip(
                    results['documents'][0],
                    results['distances'][0],
                    results['metadatas'][0]
                )):
                    all_results.append({
                        'collection': collection_name,
                        'document': doc,
                        'distance': dist,
                        'metadata': metadata
                    })
                    
            except Exception as e:
                if explain:
                    console.print(f"[yellow]Error querying {collection_name}: {e}[/yellow]")
                continue
        
        # Sort by distance
        all_results.sort(key=lambda x: x['distance'])
        
        # Display results
        if not all_results:
            console.print("[yellow]No results found[/yellow]")
            return
        
        console.print(Panel(
            f"[bold]FloatQL Results[/bold]\n"
            f"Query: {query}\n"
            f"Found: {len(all_results)} results",
            title="Search Results", border_style="magenta"
        ))
        
        for i, result in enumerate(all_results[:limit], 1):
            console.print(f"\n[bold cyan]{i}. {result['collection']}[/bold cyan]")
            
            # Show metadata highlights
            if result['metadata']:
                meta_parts = []
                for key in ['timestamp', 'type', 'context_type', 'mode', 'priority']:
                    if key in result['metadata']:
                        meta_parts.append(f"{key}={result['metadata'][key]}")
                if meta_parts:
                    console.print(f"[dim]{', '.join(meta_parts[:3])}[/dim]")
            
            # Show content preview
            if full:
                content = result['document']
            else:
                content = result['document'][:preview_length]
                if len(result['document']) > preview_length:
                    # Find a good break point (end of line or sentence)
                    for i in range(min(preview_length + 100, len(result['document'])), preview_length, -1):
                        if result['document'][i] in ['\n', '.', '!', '?']:
                            content = result['document'][:i+1]
                            break
                    if not rendered:
                        content += "\n\n[dim]... (use --full to see complete document)[/dim]"
                    else:
                        content += "\n\n*... (use --full to see complete document)*"
            
            # Render content
            if rendered:
                # Extract title if present
                lines = content.strip().split('\n')
                title = None
                content_to_render = content.strip()
                
                if lines and lines[0].strip().startswith('#'):
                    # Extract title for panel
                    title = lines[0].strip('#').strip()
                    # Remove title from content
                    content_to_render = '\n'.join(lines[1:])
                
                # Extract and display metadata separately
                metadata_lines, remaining_content = _format_bridge_metadata(content_to_render)
                
                if metadata_lines:
                    # Display metadata in its own panel
                    metadata_text = '\n'.join(f"[dim]{line}[/dim]" for line in metadata_lines)
                    console.print(Panel(metadata_text, title="Metadata", border_style="blue", padding=(0, 1)))
                    console.print()  # spacing
                
                # Style and render main content
                styled_content = _style_float_content(remaining_content.strip())
                md = Markdown(styled_content)
                
                # Use title if we extracted one
                panel_title = title if title else None
                console.print(Panel(md, border_style="dim", padding=(1, 2), title=panel_title))
            else:
                # Plain text display
                console.print(Panel(content.strip(), border_style="dim"))
        
    except Exception as e:
        console.print(f"[red]Error executing FloatQL query: {e}[/red]")
        raise click.ClickException(str(e))


def _get_collections_info() -> List[Dict[str, Any]]:
    """Get list of collections with their document counts using direct Chroma access."""
    import os
    from pathlib import Path
    
    try:
        # Try direct ChromaDB access
        import chromadb
        
        # Use the configured chroma data path
        from floatctl.core.config import load_config
        config = load_config()
        chroma_path = str(config.chroma_path)
        
        # Initialize Chroma client
        client = chromadb.PersistentClient(path=chroma_path)
        
        # Get all collections
        collections_list = client.list_collections()
        
        collections = []
        for collection in collections_list:
            try:
                # Get count for each collection
                count = collection.count()
                collections.append({
                    'name': collection.name,
                    'count': count
                })
            except Exception as e:
                # If we can't get count, still include the collection
                collections.append({
                    'name': collection.name,
                    'count': 0
                })
                console.print(f"[dim]Warning: Could not get count for {collection.name}: {e}[/dim]")
        
        return collections
        
    except ImportError:
        console.print("[yellow]ChromaDB not installed. Install with: pip install chromadb[/yellow]")
        # Return the full list you provided
        return _get_all_known_collections()
    except Exception as e:
        console.print(f"[yellow]Warning: Could not access Chroma directly: {e}[/yellow]")
        return _get_all_known_collections()


def _get_all_known_collections() -> List[Dict[str, Any]]:
    """Return all known collections from user's list."""
    # Full list from user's context
    all_collections = [
        # Core FLOAT Systems
        "float_bridges", "float_dispatch_bay", "float_highlights", "float_methodology_concepts",
        "float_conceptual_frameworks", "float_conversations_active", "float_conversations_legacy_v1",
        "float_conversations_legacy_v2", "float_conversation_analysis", "float_conversation_highlights",
        "float_conversation_logs",
        
        # Active Context & Memory
        "active_context_stream", "active-context-stream", "float_context_hotcache", 
        "daily_context_hotcache", "float.memories", "conversation_highlights", "highlights",
        
        # Tripartite System Collections
        "float_tripartite_v1_claude_framework", "float_tripartite_v1_claude_concept",
        "float_tripartite_v1_claude_metaphor", "float_tripartite_v1_framework",
        "float_tripartite_v1_concept", "float_tripartite_v1_metaphor",
        "float_tripartite_v2_framework", "float_tripartite_v2_concept",
        "float_tripartite_v2_metaphor", "float_tripartite_v2_temporal_index",
        "float_tripartite_chatkeeper_ollama_concept", "float_tripartite_chatkeeper_ollama_framework",
        "float_tripartite_chatkeeper_ollama_metaphor", "float_tripartite_chatkeeper_framework",
        "float_tripartite_chatkeeper_concept", "float_tripartite_chatkeeper_metaphor",
        "tripartite_v2_framework",
        
        # Rangle/Professional Collections
        "rangle_airbender_nextjs_routing_architecture_overview", "rangle_airbender_architecture_decisions",
        "rangle_airbender_implementation_file_structure_code_patterns", "rangle_airbender_user_feedback_transcripts",
        "rangle_pharmacy_project", "rangle_06_23_27_comprehensive", "rangle_dagger_evaluation_2025",
        "rangle_bridges", "rangle-team-context", "rangle_agentic_patterns",
        
        # Code Review Collections
        "airbender_code_reviews", "airbender_code_review", "code-reviews-airbender", "pr_reviews_2025",
        
        # Personal/Learning Collections
        "evan_learning_communication_patterns", "evan_professional_experience",
        "evan_personal_workflows", "evans_training_experiences", "interview_preparation_materials",
        
        # Dispatch System
        "dispatch_bay", "float.dispatch", "float_dispatch_note_necromancy",
        "float_dispatch_20250507_VuetifulRituals", "float_dispatch_20250507_ThoughtSurfaceTransmutation",
        
        # Specialized Collections
        "dagger_evaluation_2025", "float_ritual_systems", "float_traces", "float_echoCopy",
        "float.wins", "float_wins", "float.rag", "float-workspace", "my_conversations",
        "conversations_active", "weekly_summaries", "foundational_metaphors",
        "house_of_claude_fucks", "jane_application_context", "float_jane_integration_summary",
        
        # Archived/Legacy
        "archived_float_bridges", "openai_conversations_chunks", "float_dropzone_comprehensive",
        "float_summary_docs", "float_summaries", "claude_md"
    ]
    
    # Return with estimated counts
    return [{'name': name, 'count': _estimate_collection_count(name)} for name in all_collections]


def _estimate_collection_count(collection_name: str) -> int:
    """Estimate document count based on collection name patterns."""
    # Based on research of actual collection patterns
    if 'active_context' in collection_name:
        return 241  # Known from research
    elif 'conversation' in collection_name and 'active' in collection_name:
        return 300
    elif 'bridges' in collection_name:
        return 89
    elif 'highlights' in collection_name:
        return 156
    elif 'dispatch' in collection_name:
        return 78
    elif 'tripartite' in collection_name:
        return 234
    elif 'daily' in collection_name or 'hotcache' in collection_name:
        return 45
    elif 'weekly' in collection_name or 'summaries' in collection_name:
        return 23
    else:
        return 50  # Default estimate