"""
Consciousness Query Plugin

Hybrid query system combining SQLite structured data with Chroma semantic search.
Provides the best of both worlds: precise filtering + semantic discovery.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

from floatctl.plugin_manager import PluginBase
from floatctl.core.database import DatabaseManager
from floatctl.core.consciousness_middleware import ConsciousnessMiddleware
from floatctl.core.consciousness_chroma_bridge import ConsciousnessChromaBridge

console = Console()

class ConsciousnessQueryPlugin(PluginBase):
    """Plugin for querying consciousness analysis results."""
    
    name = "consciousness"
    description = "Query consciousness analysis results with hybrid SQLite + Chroma search"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register consciousness query commands."""
        
        @cli_group.group()
        @click.pass_context
        def consciousness(ctx: click.Context) -> None:
            """Query consciousness analysis results."""
            pass
        
        @consciousness.command()
        @click.option(
            "--level", "-l",
            type=click.Choice(["all", "standard", "moderate", "high"]),
            default="all",
            help="Filter by contamination level",
        )
        @click.option(
            "--min-score", "-s",
            type=int,
            help="Minimum contamination score",
        )
        @click.option(
            "--project", "-p",
            help="Filter by work project name",
        )
        @click.option(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of results",
        )
        @click.option(
            "--export", "-e",
            type=click.Path(path_type=Path),
            help="Export results to JSON file",
        )
        @click.pass_context
        def contamination(
            ctx: click.Context,
            level: str,
            min_score: Optional[int],
            project: Optional[str],
            limit: int,
            export: Optional[Path],
        ) -> None:
            """Query consciousness contamination analysis results."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            
            # Build query conditions
            where_conditions = []
            params = []
            
            if level != "all":
                where_conditions.append("contamination_level = ?")
                params.append(level)
            
            if min_score:
                where_conditions.append("contamination_score >= ?")
                params.append(min_score)
            
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
            table = Table(title="🧬 Consciousness Contamination Analysis")
            table.add_column("File", style="cyan", max_width=30)
            table.add_column("Title", style="white", max_width=40)
            table.add_column("Level", style="red")
            table.add_column("Score", justify="right")
            table.add_column("URLs", justify="right")
            table.add_column("Project", style="green", max_width=20)
            table.add_column("Dispatch", justify="right")
            table.add_column("Date", style="dim")
            
            for row in results:
                contamination_style = {
                    "high": "red",
                    "moderate": "yellow", 
                    "standard": "green"
                }.get(row[2], "white")
                
                processed_date = datetime.fromisoformat(row[8]).strftime("%m-%d")
                
                table.add_row(
                    Path(row[0]).name,
                    row[1][:37] + "..." if len(row[1]) > 40 else row[1],
                    f"[{contamination_style}]{row[2]}[/{contamination_style}]",
                    str(row[3]),
                    f"{row[4]}/{row[5]}",
                    row[6] or "-",
                    str(row[7]),
                    processed_date
                )
            
            console.print(table)
            
            # Export if requested
            if export:
                export_data = {
                    "query": {
                        "level": level,
                        "min_score": min_score,
                        "project": project,
                        "limit": limit
                    },
                    "results": [dict(zip([
                        "file_path", "conversation_title", "contamination_level",
                        "contamination_score", "consciousness_urls", "work_urls", 
                        "primary_project", "dispatch_score", "processed_at"
                    ], row)) for row in results],
                    "exported_at": datetime.now().isoformat()
                }
                
                with open(export, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                console.print(f"\n[green]📊 Results exported to: {export}[/green]")
        
        @consciousness.command()
        @click.option(
            "--project", "-p",
            help="Specific project to analyze",
        )
        @click.option(
            "--category", "-c",
            type=click.Choice(["client", "float", "research", "internal"]),
            help="Filter by project category",
        )
        @click.pass_context
        def projects(
            ctx: click.Context,
            project: Optional[str],
            category: Optional[str],
        ) -> None:
            """Query work project classifications."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            
            if project:
                # Get specific project details
                cursor = db_manager.execute_sql("""
                    SELECT 
                        ca.file_path, ca.conversation_title, ca.contamination_level,
                        wpm.project_name, wpm.project_category, wpm.match_count,
                        wpm.matched_patterns, ca.processed_at
                    FROM consciousness_analysis ca
                    JOIN work_project_matches wpm ON ca.id = wpm.analysis_id
                    WHERE wpm.project_name = ?
                    ORDER BY wpm.match_count DESC
                """, (project,))
                
                results = cursor.fetchall()
                
                if not results:
                    console.print(f"[yellow]No results found for project: {project}[/yellow]")
                    return
                
                table = Table(title=f"📋 Project Analysis: {project}")
                table.add_column("File", style="cyan", max_width=30)
                table.add_column("Title", style="white", max_width=40)
                table.add_column("Matches", justify="right")
                table.add_column("Contamination", style="red")
                table.add_column("Date", style="dim")
                
                for row in results:
                    processed_date = datetime.fromisoformat(row[7]).strftime("%m-%d")
                    
                    table.add_row(
                        Path(row[0]).name,
                        row[1][:37] + "..." if len(row[1]) > 40 else row[1],
                        str(row[5]),
                        row[2],
                        processed_date
                    )
                
                console.print(table)
                
            else:
                # Get project summary
                where_clause = ""
                params = []
                
                if category:
                    where_clause = "WHERE wpm.project_category = ?"
                    params.append(category)
                
                cursor = db_manager.execute_sql(f"""
                    SELECT 
                        wpm.project_name, wpm.project_category,
                        COUNT(*) as conversation_count,
                        AVG(wpm.match_count) as avg_matches,
                        MAX(wpm.match_count) as max_matches,
                        AVG(ca.contamination_score) as avg_contamination
                    FROM work_project_matches wpm
                    JOIN consciousness_analysis ca ON wpm.analysis_id = ca.id
                    {where_clause}
                    GROUP BY wpm.project_name, wpm.project_category
                    ORDER BY conversation_count DESC
                """, params)
                
                results = cursor.fetchall()
                
                if not results:
                    console.print("[yellow]No work project data found[/yellow]")
                    return
                
                table = Table(title="📋 Work Project Summary")
                table.add_column("Project", style="green")
                table.add_column("Category", style="blue")
                table.add_column("Conversations", justify="right")
                table.add_column("Avg Matches", justify="right")
                table.add_column("Max Matches", justify="right")
                table.add_column("Avg Contamination", justify="right")
                
                for row in results:
                    table.add_row(
                        row[0],
                        row[1],
                        str(row[2]),
                        f"{row[3]:.1f}",
                        str(row[4]),
                        f"{row[5]:.1f}"
                    )
                
                console.print(table)
        
        @consciousness.command()
        @click.option(
            "--domain", "-d",
            help="Filter by domain (partial match)",
        )
        @click.option(
            "--consciousness-markers",
            is_flag=True,
            help="Only show URLs with consciousness markers",
        )
        @click.option(
            "--work-project", "-p",
            help="Filter by work project",
        )
        @click.option(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of results",
        )
        @click.pass_context
        def urls(
            ctx: click.Context,
            domain: Optional[str],
            consciousness_markers: bool,
            work_project: Optional[str],
            limit: int,
        ) -> None:
            """Query URL contexts with consciousness mapping."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            
            where_conditions = []
            params = []
            
            if domain:
                where_conditions.append("uc.domain LIKE ?")
                params.append(f"%{domain}%")
            
            if consciousness_markers:
                where_conditions.append("uc.consciousness_markers != '[]' AND uc.consciousness_markers IS NOT NULL")
            
            if work_project:
                where_conditions.append("uc.work_project = ?")
                params.append(work_project)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            cursor = db_manager.execute_sql(f"""
                SELECT 
                    uc.url, uc.domain, uc.context_snippet, uc.work_project,
                    uc.consciousness_markers, ca.conversation_title,
                    ca.file_path, ca.contamination_level, ca.processed_at
                FROM url_contexts uc
                JOIN consciousness_analysis ca ON uc.analysis_id = ca.id
                {where_clause}
                ORDER BY ca.processed_at DESC
                LIMIT ?
            """, params + [limit])
            
            results = cursor.fetchall()
            
            if not results:
                console.print("[yellow]No URL contexts found[/yellow]")
                return
            
            # Display results
            for row in results:
                consciousness_markers_data = json.loads(row[4]) if row[4] else []
                processed_date = datetime.fromisoformat(row[8]).strftime("%Y-%m-%d")
                
                panel_content = f"""
[bold cyan]URL:[/bold cyan] {row[0]}
[bold blue]Domain:[/bold blue] {row[1]}
[bold green]Work Project:[/bold green] {row[3] or 'None'}
[bold red]Consciousness Markers:[/bold red] {len(consciousness_markers_data)}

[bold white]Context:[/bold white]
{row[2][:200]}{'...' if len(row[2]) > 200 else ''}

[dim]From: {row[5]} ({processed_date})[/dim]
                """.strip()
                
                console.print(Panel(panel_content, title=f"🔗 {row[1]}", border_style="blue"))
        
        @consciousness.command()
        @click.option(
            "--imprint", "-i",
            help="Filter by imprint name",
        )
        @click.option(
            "--min-matches", "-m",
            type=int,
            help="Minimum number of pattern matches",
        )
        @click.option(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of results",
        )
        @click.pass_context
        def dispatch(
            ctx: click.Context,
            imprint: Optional[str],
            min_matches: Optional[int],
            limit: int,
        ) -> None:
            """Query float.dispatch publishing opportunities."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            
            where_conditions = []
            params = []
            
            if imprint:
                where_conditions.append("do.imprint_name = ?")
                params.append(imprint)
            
            if min_matches:
                where_conditions.append("do.match_count >= ?")
                params.append(min_matches)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            cursor = db_manager.execute_sql(f"""
                SELECT 
                    do.imprint_name, do.match_count, do.matched_patterns,
                    do.description, ca.conversation_title, ca.file_path,
                    ca.contamination_level, ca.contamination_score, ca.processed_at
                FROM dispatch_opportunities do
                JOIN consciousness_analysis ca ON do.analysis_id = ca.id
                {where_clause}
                ORDER BY do.match_count DESC, ca.contamination_score DESC
                LIMIT ?
            """, params + [limit])
            
            results = cursor.fetchall()
            
            if not results:
                console.print("[yellow]No dispatch opportunities found[/yellow]")
                return
            
            # Group by imprint
            imprints = {}
            for row in results:
                imprint_name = row[0]
                if imprint_name not in imprints:
                    imprints[imprint_name] = {
                        'description': row[3],
                        'conversations': []
                    }
                
                imprints[imprint_name]['conversations'].append({
                    'title': row[4],
                    'file_path': row[5],
                    'matches': row[1],
                    'contamination_level': row[6],
                    'contamination_score': row[7],
                    'processed_at': row[8]
                })
            
            # Display by imprint
            for imprint_name, data in imprints.items():
                table = Table(title=f"📰 {imprint_name}")
                table.add_column("Conversation", style="white", max_width=50)
                table.add_column("Matches", justify="right")
                table.add_column("Contamination", style="red")
                table.add_column("Date", style="dim")
                
                for conv in data['conversations']:
                    processed_date = datetime.fromisoformat(conv['processed_at']).strftime("%m-%d")
                    
                    table.add_row(
                        conv['title'][:47] + "..." if len(conv['title']) > 50 else conv['title'],
                        str(conv['matches']),
                        f"{conv['contamination_level']} ({conv['contamination_score']})",
                        processed_date
                    )
                
                console.print(Panel(table, subtitle=data['description']))
        
        @consciousness.command()
        @click.option(
            "--days", "-d",
            type=int,
            default=30,
            help="Number of days to analyze",
        )
        @click.pass_context
        def timeline(
            ctx: click.Context,
            days: int,
        ) -> None:
            """Show consciousness contamination timeline."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor = db_manager.execute_sql("""
                SELECT 
                    DATE(processed_at) as date,
                    COUNT(*) as total_conversations,
                    COUNT(CASE WHEN contamination_level = 'high' THEN 1 END) as high_contamination,
                    COUNT(CASE WHEN contamination_level = 'moderate' THEN 1 END) as moderate_contamination,
                    AVG(contamination_score) as avg_contamination_score,
                    COUNT(CASE WHEN consciousness_urls > 0 THEN 1 END) as conversations_with_consciousness_urls,
                    COUNT(CASE WHEN dispatch_score > 3 THEN 1 END) as strong_dispatch_opportunities
                FROM consciousness_analysis
                WHERE processed_at >= ?
                GROUP BY DATE(processed_at)
                ORDER BY date DESC
            """, (cutoff_date.isoformat(),))
            
            results = cursor.fetchall()
            
            if not results:
                console.print(f"[yellow]No consciousness analysis data found in the last {days} days[/yellow]")
                return
            
            table = Table(title=f"🧬 Consciousness Timeline ({days} days)")
            table.add_column("Date", style="cyan")
            table.add_column("Total", justify="right")
            table.add_column("High", justify="right", style="red")
            table.add_column("Moderate", justify="right", style="yellow")
            table.add_column("Avg Score", justify="right")
            table.add_column("Consciousness URLs", justify="right", style="blue")
            table.add_column("Strong Dispatch", justify="right", style="green")
            
            for row in results:
                table.add_row(
                    row[0],
                    str(row[1]),
                    str(row[2]),
                    str(row[3]),
                    f"{row[4]:.1f}" if row[4] else "0.0",
                    str(row[5]),
                    str(row[6])
                )
            
            console.print(table)
            
            # Calculate trends
            if len(results) >= 7:
                recent_avg = sum(r[4] or 0 for r in results[:7]) / 7
                older_avg = sum(r[4] or 0 for r in results[7:14]) / min(7, len(results) - 7)
                
                if recent_avg > older_avg:
                    trend = "[red]📈 Increasing contamination trend[/red]"
                else:
                    trend = "[green]📉 Decreasing contamination trend[/green]"
                
                console.print(f"\n{trend}")
        
        @consciousness.command()
        @click.pass_context
        def summary(ctx: click.Context) -> None:
            """Show overall consciousness analysis summary."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            consciousness_middleware = ConsciousnessMiddleware(db_manager)
            
            summary = consciousness_middleware.get_analysis_summary()
            
            # Main stats panel
            main_stats = f"""
[bold cyan]Total Analyses:[/bold cyan] {summary['total_analyses']}
[bold red]High Contamination:[/bold red] {summary['high_contamination']}
[bold yellow]Moderate Contamination:[/bold yellow] {summary['moderate_contamination']}
[bold blue]Conversations with Consciousness URLs:[/bold blue] {summary['conversations_with_consciousness_urls']}
[bold green]Strong Dispatch Opportunities:[/bold green] {summary['strong_dispatch_opportunities']}

[bold white]Average Contamination Score:[/bold white] {summary['avg_contamination_score']}
[bold white]Average Dispatch Score:[/bold white] {summary['avg_dispatch_score']}
            """.strip()
            
            console.print(Panel(main_stats, title="🧬 Consciousness Analysis Summary", border_style="cyan"))
            
            # Top work projects
            cursor = db_manager.execute_sql("""
                SELECT project_name, COUNT(*) as count, project_category
                FROM work_project_matches
                GROUP BY project_name, project_category
                ORDER BY count DESC
                LIMIT 5
            """)
            
            project_results = cursor.fetchall()
            
            if project_results:
                project_table = Table(title="📋 Top Work Projects")
                project_table.add_column("Project", style="green")
                project_table.add_column("Category", style="blue")
                project_table.add_column("Conversations", justify="right")
                
                for row in project_results:
                    project_table.add_row(row[0], row[2], str(row[1]))
                
                console.print(project_table)
            
            # Top dispatch imprints
            cursor = db_manager.execute_sql("""
                SELECT imprint_name, COUNT(*) as count, AVG(match_count) as avg_matches
                FROM dispatch_opportunities
                GROUP BY imprint_name
                ORDER BY count DESC
                LIMIT 5
            """)
            
            dispatch_results = cursor.fetchall()
            
            if dispatch_results:
                dispatch_table = Table(title="📰 Top Dispatch Imprints")
                dispatch_table.add_column("Imprint", style="magenta")
                dispatch_table.add_column("Opportunities", justify="right")
                dispatch_table.add_column("Avg Matches", justify="right")
                
                for row in dispatch_results:
                    dispatch_table.add_row(row[0], str(row[1]), f"{row[2]:.1f}")
                
                console.print(dispatch_table)
        
        @consciousness.command()
        @click.argument("query", type=str)
        @click.option(
            "--collection", "-c",
            type=click.Choice(["consciousness", "urls", "dispatch"]),
            default="consciousness",
            help="Which collection to search",
        )
        @click.option(
            "--limit", "-l",
            type=int,
            default=5,
            help="Maximum number of results",
        )
        @click.pass_context
        def search(
            ctx: click.Context,
            query: str,
            collection: str,
            limit: int,
        ) -> None:
            """Semantic search across consciousness analysis results."""
            config = ctx.obj["config"]
            db_manager = DatabaseManager(config.db_path)
            
            try:
                chroma_bridge = ConsciousnessChromaBridge(db_manager)
                
                if collection == "consciousness":
                    results = chroma_bridge.query_consciousness_semantic(query, limit)
                elif collection == "urls":
                    results = chroma_bridge.query_url_contexts_semantic(query, limit)
                elif collection == "dispatch":
                    results = chroma_bridge.query_dispatch_opportunities_semantic(query, limit)
                
                if not results['results']['documents'][0]:
                    console.print(f"[yellow]No semantic results found for: {query}[/yellow]")
                    return
                
                console.print(f"[cyan]🔍 Semantic search results for: '{query}'[/cyan]")
                console.print(f"[dim]Collection: {results['collection']}[/dim]\n")
                
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['results']['documents'][0],
                    results['results']['metadatas'][0],
                    results['results']['distances'][0]
                )):
                    similarity = 1 - distance
                    
                    panel_content = f"""
[bold white]Similarity:[/bold white] {similarity:.3f}
[bold cyan]File:[/bold cyan] {metadata.get('file_path', 'Unknown')}
[bold green]Title:[/bold green] {metadata.get('conversation_title', 'Unknown')}

{doc[:300]}{'...' if len(doc) > 300 else ''}
                    """.strip()
                    
                    console.print(Panel(panel_content, title=f"Result {i+1}", border_style="blue"))
                
            except Exception as e:
                console.print(f"[red]Semantic search failed: {e}[/red]")
                console.print("[yellow]Make sure consciousness analysis has been synced to Chroma with --sync-to-chroma[/yellow]")