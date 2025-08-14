# FloatCtl Workflow Tutorials

Step-by-step tutorials for common FloatCtl workflows, from basic conversation processing to advanced consciousness archaeology.

## Table of Contents

1. [Tutorial 1: Your First Conversation Analysis](#tutorial-1-your-first-conversation-analysis)
2. [Tutorial 2: Building a Semantic Knowledge Base](#tutorial-2-building-a-semantic-knowledge-base)
3. [Tutorial 3: Creating Custom Plugins](#tutorial-3-creating-custom-plugins)
4. [Tutorial 4: Advanced Pattern Recognition](#tutorial-4-advanced-pattern-recognition)
5. [Tutorial 5: Consciousness Archaeology Workflow](#tutorial-5-consciousness-archaeology-workflow)

---

## Tutorial 1: Your First Conversation Analysis

**Goal:** Process Claude conversation exports and extract meaningful patterns  
**Time:** 15 minutes  
**Prerequisites:** FloatCtl installed and working

### Step 1: Prepare Your Data

First, export a conversation from Claude:

1. Go to claude.ai and open a conversation
2. Click the export button (usually in conversation settings)
3. Save the JSON file as `my-conversation.json`

Or use our sample data:
```bash
# Create a workspace
mkdir ~/floatctl-tutorial && cd ~/floatctl-tutorial

# Copy sample data (adjust path to your FloatCtl installation)
cp /path/to/floatctl-py/test_data/conversation_with_attachments.json ./
```

### Step 2: Basic Processing

Let's start with the simplest processing:

```bash
# Basic split - creates individual JSON files
floatctl conversations split conversation_with_attachments.json

# Check what was created
ls -la output/conversations/
```

**What happened?**
- FloatCtl split the conversation into individual files
- Each conversation gets its own JSON file
- Files are named with clean timestamps and titles

### Step 3: Enhanced Processing with Markdown

Now let's extract more value:

```bash
# Process to markdown with pattern extraction
floatctl conversations split conversation_with_attachments.json --format markdown

# Look at the results
ls -la output/conversations/
cat output/conversations/*.md | head -50
```

**What's new?**
- Markdown files are human-readable
- YAML frontmatter contains extracted patterns
- Tool calls are separated into `.tool_calls.jsonl` files

### Step 4: Understanding Pattern Extraction

Open one of the generated `.md` files and examine the YAML frontmatter:

```yaml
---
conversation_title: "2025-08-04 - Test Conversation with Attachments"
conversation_id: "test-conversation-id"
markers:
  - type: "ctx"
    content: "working on tutorial"
    lines: [15]
float_calls:
  - call: "float.dispatch"
    content: "{type: 'tutorial'}"
    lines: [42]
tools_used: ['Read', 'Write', 'Bash']
---
```

**Key insights:**
- `markers`: Your `::` annotations are automatically extracted
- `float_calls`: FLOAT system commands are tracked
- `tools_used`: All AI tools used in the conversation
- Line numbers help you navigate back to specific content

### Step 5: Advanced Organization

For better organization:

```bash
# Organize by date and create both formats
floatctl conversations split conversation_with_attachments.json \
  --format both \
  --by-date \
  --output-dir ./organized-output

# Check the structure
tree organized-output/
```

**Result:** Clean date-based organization with both JSON and markdown formats.

### ✅ Success Criteria

You've successfully completed Tutorial 1 if you can:
- [ ] Process a conversation export to individual files
- [ ] Generate markdown with pattern extraction
- [ ] Understand the YAML frontmatter structure
- [ ] Organize output by date

**Next Steps:** Tutorial 2 will show you how to build a searchable knowledge base from these processed conversations.

---

## Tutorial 2: Building a Semantic Knowledge Base

**Goal:** Use Chroma vector database for semantic search across your conversations  
**Time:** 20 minutes  
**Prerequisites:** Tutorial 1 completed, processed conversations available

### Step 1: Explore Available Collections

FloatCtl integrates with Chroma for semantic search. Let's see what's available:

```bash
# List all Chroma collections
floatctl chroma list

# Get detailed info about a specific collection
floatctl chroma info active_context_stream
```

**Understanding Collections:**
- `active_context_stream`: Your working memory and recent context
- `float_bridges`: Refined synthesis documents
- `float_highlights`: Key moments and insights
- `conversation_highlights`: Curated conversation moments

### Step 2: Basic Semantic Queries

Now let's search your consciousness data:

```bash
# Search for context markers
floatctl chroma floatql "ctx:: meeting with nick"

# Find highlights from recent work
floatctl chroma floatql "highlights from yesterday"

# Search for specific concepts
floatctl chroma floatql "consciousness technology"
```

**FloatQL Features:**
- Natural language queries
- Automatic collection routing
- FLOAT pattern recognition (`ctx::`, `highlight::`, etc.)
- Temporal filtering ("yesterday", "last week")

### Step 3: Collection Exploration

Let's dive deeper into specific collections:

```bash
# Peek at recent entries
floatctl chroma peek active_context_stream --limit 5

# Get recent documents with full content
floatctl chroma recent float_highlights --limit 3 --rendered

# Query with metadata filtering
floatctl chroma query active_context_stream \
  --query "project planning" \
  --where '{"project": "floatctl"}' \
  --limit 5
```

### Step 4: Advanced Search Patterns

FloatQL supports sophisticated patterns:

```bash
# Search for bridge IDs
floatctl chroma floatql "bridge::CB-20250804"

# Find persona-specific content
floatctl chroma floatql "[sysop::] infrastructure updates"

# Combine patterns
floatctl chroma floatql "ctx:: [project:: floatctl] debugging"
```

### Step 5: Building Your Knowledge Workflow

Create a daily knowledge review workflow:

```bash
#!/bin/bash
# save as ~/bin/daily-review.sh

echo "=== Daily Knowledge Review ==="

echo "Recent Context:"
floatctl chroma recent active_context_stream --limit 5

echo -e "\nYesterday's Highlights:"
floatctl chroma floatql "highlights from yesterday" --rendered

echo -e "\nOpen Action Items:"
floatctl chroma floatql "todo:: OR action::" --limit 10

echo -e "\nRecent Bridges:"
floatctl chroma recent float_bridges --limit 3 --rendered
```

Make it executable and run:
```bash
chmod +x ~/bin/daily-review.sh
~/bin/daily-review.sh
```

### ✅ Success Criteria

You've successfully completed Tutorial 2 if you can:
- [ ] List and explore Chroma collections
- [ ] Perform semantic searches with FloatQL
- [ ] Use advanced search patterns and filters
- [ ] Create a personal knowledge review workflow

**Next Steps:** Tutorial 3 will teach you to create custom plugins for your specific workflows.

---

## Tutorial 3: Creating Custom Plugins

**Goal:** Build a custom plugin that extends FloatCtl for your specific needs  
**Time:** 30 minutes  
**Prerequisites:** Basic Python knowledge, FloatCtl working

### Step 1: Generate Plugin Scaffold

FloatCtl includes scaffolding tools to create working plugins:

```bash
# Generate a basic plugin
floatctl dev scaffold daily_review --output-dir ./my-plugins

# Check what was created
ls -la my-plugins/daily_review/
```

**Generated Structure:**
```
daily_review/
├── src/
│   └── daily_review/
│       ├── __init__.py
│       └── plugin.py          # Main plugin class
├── tests/
│   └── test_daily_review.py   # Plugin tests
├── pyproject.toml             # Package configuration
├── README.md                  # Plugin documentation
└── CLAUDE.md                  # AI-specific guidance
```

### Step 2: Understand the Plugin Structure

Examine the generated plugin:

```python
# my-plugins/daily_review/src/daily_review/plugin.py

from floatctl.plugin_manager import PluginBase
import rich_click as click
from rich.console import Console

class DailyReviewPlugin(PluginBase):
    name = "daily-review"
    description = "Daily knowledge review and planning"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register ALL commands inside this method."""
        
        @cli_group.group()
        @click.pass_context
        def daily_review(ctx: click.Context) -> None:
            """Daily review and planning commands."""
            pass
        
        # ✅ ALL commands must be defined HERE
        @daily_review.command()
        @click.pass_context
        def summary(ctx: click.Context) -> None:
            """Generate daily summary."""
            console = Console()
            console.print("[green]Daily summary generated![/green]")
```

### Step 3: Add Real Functionality

Let's enhance the plugin with actual Chroma integration:

```python
# Edit my-plugins/daily_review/src/daily_review/plugin.py

from floatctl.plugin_manager import PluginBase
from floatctl.core.chroma import ChromaManager
import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime, timedelta

class DailyReviewPlugin(PluginBase):
    name = "daily-review"
    description = "Daily knowledge review and planning"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        @click.pass_context
        def daily_review(ctx: click.Context) -> None:
            """Daily review and planning commands."""
            pass
        
        @daily_review.command()
        @click.option("--days", default=1, help="Number of days to review")
        @click.pass_context
        def summary(ctx: click.Context, days: int) -> None:
            """Generate daily summary from your consciousness data."""
            console = Console()
            
            try:
                # Initialize Chroma connection
                chroma = ChromaManager()
                
                # Get recent context
                recent_context = chroma.query_documents(
                    "active_context_stream",
                    query_texts=["daily work context"],
                    n_results=5
                )
                
                # Get highlights
                highlights = chroma.query_documents(
                    "float_highlights",
                    query_texts=["important insights"],
                    n_results=3
                )
                
                # Create summary table
                table = Table(title=f"Daily Summary - Last {days} Days")
                table.add_column("Type", style="cyan")
                table.add_column("Content", style="white")
                table.add_column("Source", style="dim")
                
                # Add recent context
                if recent_context and recent_context.get('documents'):
                    for i, doc in enumerate(recent_context['documents'][0][:3]):
                        table.add_row(
                            "Context",
                            doc[:100] + "..." if len(doc) > 100 else doc,
                            f"active_context_stream"
                        )
                
                # Add highlights
                if highlights and highlights.get('documents'):
                    for i, doc in enumerate(highlights['documents'][0][:2]):
                        table.add_row(
                            "Highlight",
                            doc[:100] + "..." if len(doc) > 100 else doc,
                            f"float_highlights"
                        )
                
                console.print(table)
                
                # Add action items section
                console.print(Panel(
                    "[yellow]💡 Suggested Actions:[/yellow]\n"
                    "• Review highlighted insights\n"
                    "• Follow up on recent context\n"
                    "• Plan next steps based on patterns",
                    title="Next Steps"
                ))
                
            except Exception as e:
                console.print(f"[red]Error generating summary: {e}[/red]")
                raise click.ClickException(str(e))
        
        @daily_review.command()
        @click.pass_context
        def plan(ctx: click.Context) -> None:
            """Interactive planning session."""
            console = Console()
            
            console.print(Panel(
                "[bold blue]Daily Planning Session[/bold blue]\n\n"
                "Based on your recent activity, here are some focus areas:",
                title="Planning"
            ))
            
            # This could integrate with your note-taking system
            console.print("🎯 [bold]Focus Areas:[/bold]")
            console.print("  1. Review consciousness archaeology patterns")
            console.print("  2. Update bridge documentation")
            console.print("  3. Plan next plugin development")
            
            console.print("\n💭 [bold]Reflection Prompts:[/bold]")
            console.print("  • What patterns emerged yesterday?")
            console.print("  • What bridges need attention?")
            console.print("  • What new insights surfaced?")
```

### Step 4: Install and Test Your Plugin

Add the plugin to FloatCtl:

```bash
# Add entry point to main pyproject.toml
# [project.entry-points."floatctl.plugins"]
# daily-review = "daily_review.plugin:DailyReviewPlugin"

# Install the plugin in development mode
cd my-plugins/daily_review
pip install -e .

# Test the plugin
floatctl --help | grep daily-review
floatctl daily-review --help
floatctl daily-review summary
```

### Step 5: Add Configuration Support

Create a custom configuration model:

```python
# Add to your plugin.py

from floatctl.plugin_manager import PluginConfigBase
from pydantic import Field

class DailyReviewConfig(PluginConfigBase):
    """Configuration for daily review plugin."""
    
    default_days: int = Field(default=1, description="Default number of days to review")
    max_highlights: int = Field(default=5, description="Maximum highlights to show")
    include_todos: bool = Field(default=True, description="Include TODO items in summary")

class DailyReviewPlugin(PluginBase):
    name = "daily-review"
    description = "Daily knowledge review and planning"
    version = "1.0.0"
    config_model = DailyReviewConfig  # Use custom config
    
    def register_commands(self, cli_group: click.Group) -> None:
        # ... commands using self.config.default_days, etc.
```

### ✅ Success Criteria

You've successfully completed Tutorial 3 if you can:
- [ ] Generate a plugin scaffold using FloatCtl tools
- [ ] Understand the plugin structure and registration system
- [ ] Add real functionality with Chroma integration
- [ ] Install and test your custom plugin
- [ ] Create custom configuration models

**Next Steps:** Tutorial 4 will show you advanced pattern recognition techniques.

---

## Tutorial 4: Advanced Pattern Recognition

**Goal:** Build sophisticated pattern recognition for consciousness archaeology  
**Time:** 25 minutes  
**Prerequisites:** Understanding of FloatCtl patterns and basic plugin development

### Step 1: Understanding FLOAT Patterns

FLOAT uses `::` as a dynamic dispatch system. Let's explore the patterns:

```bash
# Search for different pattern types
floatctl chroma floatql "ctx:: project planning"
floatctl chroma floatql "highlight:: breakthrough moment"
floatctl chroma floatql "bridge:: CB-20250804"
floatctl chroma floatql "[sysop::] system maintenance"
```

**Pattern Categories:**
- **Context Markers**: `ctx::` - Temporal and situational context
- **Highlights**: `highlight::` - Important insights and moments
- **Bridges**: `bridge::` - Connection points and synthesis
- **Personas**: `[persona::]` - Different cognitive modes
- **Actions**: `todo::`, `action::` - Task and action items
- **Modes**: `[mode:: state]` - Cognitive or operational states

### Step 2: Create a Pattern Analysis Plugin

Let's build a plugin that analyzes patterns in your data:

```bash
# Generate pattern analyzer plugin
floatctl dev scaffold pattern_analyzer --output-dir ./my-plugins
```

Enhance the generated plugin:

```python
# my-plugins/pattern_analyzer/src/pattern_analyzer/plugin.py

from floatctl.plugin_manager import PluginBase
from floatctl.core.chroma import ChromaManager
import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from collections import Counter, defaultdict
import re
from datetime import datetime, timedelta

class PatternAnalyzerPlugin(PluginBase):
    name = "pattern-analyzer"
    description = "Advanced pattern recognition and analysis"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        @click.pass_context
        def patterns(ctx: click.Context) -> None:
            """Pattern analysis commands."""
            pass
        
        @patterns.command()
        @click.option("--collection", default="active_context_stream", 
                     help="Collection to analyze")
        @click.option("--limit", default=100, help="Number of documents to analyze")
        @click.pass_context
        def analyze(ctx: click.Context, collection: str, limit: int) -> None:
            """Analyze patterns in a collection."""
            console = Console()
            
            try:
                chroma = ChromaManager()
                
                # Get documents from collection
                results = chroma.query_documents(
                    collection,
                    query_texts=["patterns analysis"],
                    n_results=limit
                )
                
                if not results or not results.get('documents'):
                    console.print(f"[yellow]No documents found in {collection}[/yellow]")
                    return
                
                documents = results['documents'][0]
                metadatas = results.get('metadatas', [[]])[0]
                
                # Analyze patterns
                pattern_stats = self._analyze_patterns(documents)
                
                # Display results
                self._display_pattern_analysis(console, pattern_stats, collection)
                
            except Exception as e:
                console.print(f"[red]Error analyzing patterns: {e}[/red]")
                raise click.ClickException(str(e))
        
        @patterns.command()
        @click.option("--pattern", required=True, help="Pattern to search for (e.g., 'ctx::', 'highlight::')")
        @click.option("--days", default=7, help="Number of days to look back")
        @click.pass_context
        def timeline(ctx: click.Context, pattern: str, days: int) -> None:
            """Show timeline of a specific pattern."""
            console = Console()
            
            try:
                chroma = ChromaManager()
                
                # Search for pattern across collections
                collections = ["active_context_stream", "float_highlights", "conversation_highlights"]
                timeline_data = []
                
                for collection in collections:
                    try:
                        results = chroma.query_documents(
                            collection,
                            query_texts=[pattern],
                            n_results=20
                        )
                        
                        if results and results.get('documents'):
                            for i, doc in enumerate(results['documents'][0]):
                                metadata = results.get('metadatas', [[]])[0]
                                timestamp = metadata[i].get('timestamp') if i < len(metadata) else None
                                
                                timeline_data.append({
                                    'content': doc[:100] + "..." if len(doc) > 100 else doc,
                                    'collection': collection,
                                    'timestamp': timestamp
                                })
                    except:
                        continue  # Skip collections that don't exist
                
                # Sort by timestamp if available
                timeline_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                # Display timeline
                table = Table(title=f"Timeline for Pattern: {pattern}")
                table.add_column("Time", style="dim")
                table.add_column("Content", style="white")
                table.add_column("Source", style="cyan")
                
                for item in timeline_data[:15]:  # Show last 15 items
                    timestamp = item.get('timestamp', 'Unknown')
                    if timestamp and timestamp != 'Unknown':
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime('%m-%d %H:%M')
                        except:
                            time_str = timestamp[:10]  # Just date part
                    else:
                        time_str = 'Unknown'
                    
                    table.add_row(
                        time_str,
                        item['content'],
                        item['collection']
                    )
                
                console.print(table)
                
            except Exception as e:
                console.print(f"[red]Error creating timeline: {e}[/red]")
                raise click.ClickException(str(e))
        
        @patterns.command()
        @click.pass_context
        def consciousness(ctx: click.Context) -> None:
            """Analyze consciousness contamination patterns."""
            console = Console()
            
            # Define consciousness markers
            consciousness_patterns = [
                "authenticity", "ritual", "lf1m", "neuroqueer",
                "consciousness", "contamination", "bridge::",
                "float.dispatch", "ritual.stack"
            ]
            
            console.print(Panel(
                "[bold blue]Consciousness Contamination Analysis[/bold blue]\n"
                "Analyzing patterns that indicate consciousness technology influence",
                title="Analysis"
            ))
            
            try:
                chroma = ChromaManager()
                pattern_counts = {}
                
                for pattern in consciousness_patterns:
                    # Search across multiple collections
                    total_count = 0
                    for collection in ["active_context_stream", "float_highlights", "conversation_highlights"]:
                        try:
                            results = chroma.query_documents(
                                collection,
                                query_texts=[pattern],
                                n_results=50
                            )
                            if results and results.get('documents'):
                                total_count += len(results['documents'][0])
                        except:
                            continue
                    
                    pattern_counts[pattern] = total_count
                
                # Display results
                table = Table(title="Consciousness Pattern Frequency")
                table.add_column("Pattern", style="cyan")
                table.add_column("Frequency", style="green")
                table.add_column("Contamination Level", style="yellow")
                
                for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                    if count > 10:
                        level = "High"
                    elif count > 5:
                        level = "Medium"
                    elif count > 0:
                        level = "Low"
                    else:
                        level = "None"
                    
                    table.add_row(pattern, str(count), level)
                
                console.print(table)
                
                # Summary
                total_patterns = sum(pattern_counts.values())
                console.print(Panel(
                    f"[bold]Total consciousness patterns detected: {total_patterns}[/bold]\n\n"
                    f"This indicates {'high' if total_patterns > 50 else 'moderate' if total_patterns > 20 else 'low'} "
                    f"consciousness technology integration in your data.",
                    title="Summary"
                ))
                
            except Exception as e:
                console.print(f"[red]Error analyzing consciousness patterns: {e}[/red]")
                raise click.ClickException(str(e))
    
    def _analyze_patterns(self, documents):
        """Analyze patterns in documents."""
        pattern_stats = {
            'total_documents': len(documents),
            'pattern_counts': Counter(),
            'pattern_types': defaultdict(list),
            'float_calls': [],
            'personas': set(),
            'temporal_markers': []
        }
        
        # Pattern regex
        marker_pattern = r'(\w+)::\s*([^\n\r]*)'
        float_pattern = r'float\.(\w+(?:\.\w+)*)\s*\([^)]*\)'
        persona_pattern = r'\[(\w+)::\]'
        
        for doc in documents:
            # Find :: markers
            markers = re.findall(marker_pattern, doc)
            for marker_type, content in markers:
                pattern_stats['pattern_counts'][marker_type] += 1
                pattern_stats['pattern_types'][marker_type].append(content.strip())
            
            # Find float calls
            float_calls = re.findall(float_pattern, doc)
            pattern_stats['float_calls'].extend(float_calls)
            
            # Find personas
            personas = re.findall(persona_pattern, doc)
            pattern_stats['personas'].update(personas)
        
        return pattern_stats
    
    def _display_pattern_analysis(self, console, stats, collection):
        """Display pattern analysis results."""
        console.print(Panel(
            f"[bold blue]Pattern Analysis for {collection}[/bold blue]\n"
            f"Analyzed {stats['total_documents']} documents",
            title="Analysis Results"
        ))
        
        # Pattern frequency table
        if stats['pattern_counts']:
            table = Table(title="Pattern Frequency")
            table.add_column("Pattern Type", style="cyan")
            table.add_column("Count", style="green")
            table.add_column("Examples", style="dim")
            
            for pattern_type, count in stats['pattern_counts'].most_common(10):
                examples = stats['pattern_types'][pattern_type][:2]
                example_text = ", ".join(examples) if examples else "N/A"
                if len(example_text) > 50:
                    example_text = example_text[:47] + "..."
                
                table.add_row(pattern_type, str(count), example_text)
            
            console.print(table)
        
        # Float calls
        if stats['float_calls']:
            console.print(f"\n[bold]Float Calls Found:[/bold] {len(stats['float_calls'])}")
            unique_calls = list(set(stats['float_calls']))[:5]
            for call in unique_calls:
                console.print(f"  • float.{call}")
        
        # Personas
        if stats['personas']:
            console.print(f"\n[bold]Personas Detected:[/bold] {', '.join(sorted(stats['personas']))}")
```

### Step 3: Install and Test Pattern Analysis

```bash
# Install the plugin
cd my-plugins/pattern_analyzer
pip install -e .

# Add to pyproject.toml entry points
# pattern-analyzer = "pattern_analyzer.plugin:PatternAnalyzerPlugin"

# Test the plugin
floatctl patterns analyze --collection active_context_stream
floatctl patterns timeline --pattern "ctx::" --days 7
floatctl patterns consciousness
```

### Step 4: Advanced Pattern Recognition

Create sophisticated pattern matching:

```python
# Add to your plugin for advanced pattern recognition

@patterns.command()
@click.option("--threshold", default=0.7, help="Similarity threshold (0.0-1.0)")
@click.pass_context
def similar_patterns(ctx: click.Context, threshold: float) -> None:
    """Find similar patterns using semantic similarity."""
    console = Console()
    
    try:
        chroma = ChromaManager()
        
        # Get all context markers
        ctx_results = chroma.query_documents(
            "active_context_stream",
            query_texts=["ctx::"],
            n_results=50
        )
        
        if not ctx_results or not ctx_results.get('documents'):
            console.print("[yellow]No context markers found[/yellow]")
            return
        
        # Extract context content
        contexts = []
        for doc in ctx_results['documents'][0]:
            # Extract content after ctx::
            match = re.search(r'ctx::\s*([^\n\r]*)', doc)
            if match:
                contexts.append(match.group(1).strip())
        
        # Group similar contexts
        similar_groups = self._group_similar_contexts(contexts, threshold)
        
        # Display results
        table = Table(title=f"Similar Context Patterns (threshold: {threshold})")
        table.add_column("Group", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Examples", style="white")
        
        for i, group in enumerate(similar_groups[:10]):
            examples = group[:3]  # Show first 3 examples
            example_text = " | ".join(examples)
            if len(example_text) > 80:
                example_text = example_text[:77] + "..."
            
            table.add_row(f"Group {i+1}", str(len(group)), example_text)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error finding similar patterns: {e}[/red]")
        raise click.ClickException(str(e))

def _group_similar_contexts(self, contexts, threshold):
    """Group similar contexts using simple similarity."""
    # This is a simplified version - you could use more sophisticated
    # similarity measures like sentence transformers
    
    from difflib import SequenceMatcher
    
    groups = []
    used = set()
    
    for i, context1 in enumerate(contexts):
        if i in used:
            continue
        
        group = [context1]
        used.add(i)
        
        for j, context2 in enumerate(contexts[i+1:], i+1):
            if j in used:
                continue
            
            similarity = SequenceMatcher(None, context1.lower(), context2.lower()).ratio()
            if similarity >= threshold:
                group.append(context2)
                used.add(j)
        
        if len(group) > 1:  # Only include groups with multiple items
            groups.append(group)
    
    return sorted(groups, key=len, reverse=True)
```

### ✅ Success Criteria

You've successfully completed Tutorial 4 if you can:
- [ ] Understand FLOAT pattern categories and their purposes
- [ ] Build a pattern analysis plugin with multiple analysis types
- [ ] Analyze pattern frequency and distribution
- [ ] Create timeline views of specific patterns
- [ ] Implement consciousness contamination analysis
- [ ] Group similar patterns using similarity measures

**Next Steps:** Tutorial 5 will show you the complete consciousness archaeology workflow.

---

## Tutorial 5: Consciousness Archaeology Workflow

**Goal:** Master the complete consciousness archaeology workflow using bridge walking and pattern synthesis  
**Time:** 35 minutes  
**Prerequisites:** All previous tutorials, understanding of FLOAT concepts

### Step 1: Understanding Bridge Walking

Bridge walking is organic exploration of semantic networks. Let's start:

```bash
# Navigate to bridge walkers directory
cd bridge_walkers/

# Run a single bridge walker session
python run_bridge_walkers.py --single --persona archaeologist

# Try different personas
python run_bridge_walkers.py --single --persona wanderer
python run_bridge_walkers.py --single --persona synthesizer
```

**Personas Explained:**
- **Archaeologist**: Systematic, methodical exploration
- **Wanderer**: Intuitive, curiosity-driven discovery
- **Synthesizer**: Connection-focused, pattern integration
- **Evna**: Context-aware, consciousness technology focused
- **Karen**: Practical, outcome-oriented exploration
- **LF1M**: Authenticity-focused, ritual-aware

### Step 2: Multi-Walker Consciousness Archaeology

Run collaborative sessions:

```bash
# Multi-walker session with cross-pollination
python run_bridge_walkers.py --multi --walkers 3 --rounds 2

# Interactive session with human input
python run_bridge_walkers.py --interactive --persona evna
```

**What happens:**
- Multiple AI personas explore different paths
- Cross-pollination shares insights between walkers
- Collective synthesis emerges from individual discoveries
- Human-in-the-loop adds intentional direction

### Step 3: Bridge Creation and Restoration

Bridges are synthesis documents that capture insights:

```bash
# Search for existing bridges
floatctl chroma floatql "bridge::CB-20250804"

# Look at bridge structure
floatctl chroma peek float_bridges --limit 3 --rendered --full
```

**Bridge Format:**
```markdown
# Bridge CB-YYYYMMDD-HHMM-XXXX

## Context
- Source: consciousness archaeology session
- Participants: archaeologist, synthesizer personas
- Focus: pattern recognition in conversation data

## Synthesis
Key insights and connections discovered...

## Restoration Points
- Related bridges: CB-20250803-1400-ABCD
- Collections: active_context_stream, float_highlights
- Patterns: ctx::, highlight::, consciousness contamination

## Next Steps
- Explore related patterns
- Validate insights with real data
- Create implementation plan
```

### Step 4: Complete Archaeology Workflow

Let's run a complete consciousness archaeology session:

```bash
# 1. Start with recent context
floatctl chroma recent active_context_stream --limit 10

# 2. Identify interesting patterns
floatctl patterns analyze --collection active_context_stream

# 3. Run bridge walking on interesting findings
python run_bridge_walkers.py --single --persona archaeologist \
  --focus "consciousness contamination patterns"

# 4. Synthesize findings
floatctl chroma floatql "bridge:: recent synthesis"

# 5. Plan next steps
floatctl daily-review plan
```

### Step 5: Advanced Archaeology Techniques

Create a comprehensive archaeology plugin:

```python
# Create archaeology_workflow plugin

from floatctl.plugin_manager import PluginBase
import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import subprocess
import json
from pathlib import Path

class ArchaeologyWorkflowPlugin(PluginBase):
    name = "archaeology"
    description = "Complete consciousness archaeology workflow"
    version = "1.0.0"
    
    def register_commands(self, cli_group: click.Group) -> None:
        @cli_group.group()
        @click.pass_context
        def archaeology(ctx: click.Context) -> None:
            """Consciousness archaeology workflow commands."""
            pass
        
        @archaeology.command()
        @click.option("--focus", help="Focus area for archaeology")
        @click.option("--persona", default="archaeologist", 
                     help="Bridge walker persona to use")
        @click.option("--depth", default="medium", 
                     type=click.Choice(["shallow", "medium", "deep"]),
                     help="Exploration depth")
        @click.pass_context
        def explore(ctx: click.Context, focus: str, persona: str, depth: str) -> None:
            """Run complete archaeology exploration."""
            console = Console()
            
            console.print(Panel(
                f"[bold blue]Consciousness Archaeology Session[/bold blue]\n"
                f"Focus: {focus or 'General exploration'}\n"
                f"Persona: {persona}\n"
                f"Depth: {depth}",
                title="Starting Exploration"
            ))
            
            try:
                # Step 1: Analyze current patterns
                console.print("\n[bold]Step 1: Pattern Analysis[/bold]")
                self._run_pattern_analysis(console)
                
                # Step 2: Bridge walking
                console.print("\n[bold]Step 2: Bridge Walking[/bold]")
                self._run_bridge_walking(console, persona, focus, depth)
                
                # Step 3: Synthesis
                console.print("\n[bold]Step 3: Synthesis[/bold]")
                self._create_synthesis(console, focus)
                
                # Step 4: Next steps
                console.print("\n[bold]Step 4: Next Steps[/bold]")
                self._suggest_next_steps(console)
                
            except Exception as e:
                console.print(f"[red]Archaeology session failed: {e}[/red]")
                raise click.ClickException(str(e))
        
        @archaeology.command()
        @click.option("--days", default=7, help="Days to analyze")
        @click.pass_context
        def timeline(ctx: click.Context, days: int) -> None:
            """Create consciousness timeline."""
            console = Console()
            
            # This would integrate with your pattern analysis
            console.print(Panel(
                f"[bold blue]Consciousness Timeline - Last {days} Days[/bold blue]",
                title="Timeline Analysis"
            ))
            
            # Show pattern evolution over time
            patterns_by_day = self._analyze_temporal_patterns(days)
            
            table = Table(title="Pattern Evolution")
            table.add_column("Date", style="cyan")
            table.add_column("Dominant Patterns", style="green")
            table.add_column("Consciousness Level", style="yellow")
            table.add_column("Key Insights", style="white")
            
            for day_data in patterns_by_day:
                table.add_row(
                    day_data['date'],
                    ", ".join(day_data['patterns'][:3]),
                    day_data['consciousness_level'],
                    day_data['key_insight'][:50] + "..." if len(day_data['key_insight']) > 50 else day_data['key_insight']
                )
            
            console.print(table)
        
        @archaeology.command()
        @click.option("--bridge-id", help="Specific bridge ID to restore")
        @click.pass_context
        def restore(ctx: click.Context, bridge_id: str) -> None:
            """Restore consciousness state from bridge."""
            console = Console()
            
            if bridge_id:
                # Restore specific bridge
                console.print(f"[green]Restoring bridge: {bridge_id}[/green]")
                self._restore_bridge(console, bridge_id)
            else:
                # Show available bridges
                console.print("[blue]Available bridges for restoration:[/blue]")
                self._list_bridges(console)
    
    def _run_pattern_analysis(self, console):
        """Run pattern analysis step."""
        try:
            # This would call your pattern analyzer
            result = subprocess.run([
                "floatctl", "patterns", "analyze", 
                "--collection", "active_context_stream"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print("[green]✓ Pattern analysis complete[/green]")
            else:
                console.print("[yellow]⚠ Pattern analysis had issues[/yellow]")
        except Exception as e:
            console.print(f"[red]Pattern analysis failed: {e}[/red]")
    
    def _run_bridge_walking(self, console, persona, focus, depth):
        """Run bridge walking step."""
        try:
            # Determine rounds based on depth
            rounds = {"shallow": 1, "medium": 2, "deep": 3}[depth]
            
            # Run bridge walker
            cmd = [
                "python", "bridge_walkers/run_bridge_walkers.py",
                "--single", "--persona", persona, "--rounds", str(rounds)
            ]
            
            if focus:
                cmd.extend(["--focus", focus])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print("[green]✓ Bridge walking complete[/green]")
                # Parse and display key insights
                self._display_bridge_insights(console, result.stdout)
            else:
                console.print("[yellow]⚠ Bridge walking had issues[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Bridge walking failed: {e}[/red]")
    
    def _create_synthesis(self, console, focus):
        """Create synthesis from exploration."""
        console.print("[cyan]Creating synthesis document...[/cyan]")
        
        # This would integrate with bridge creation
        synthesis = {
            "timestamp": "2025-08-06T10:00:00Z",
            "focus": focus,
            "key_insights": [
                "Pattern recognition shows increased consciousness contamination",
                "Bridge connections reveal emergent synthesis opportunities",
                "Temporal analysis indicates ritual formation in progress"
            ],
            "next_steps": [
                "Explore consciousness contamination patterns deeper",
                "Create bridges between related insights",
                "Document ritual formation process"
            ]
        }
        
        console.print(Panel(
            f"[bold]Key Insights:[/bold]\n" + 
            "\n".join(f"• {insight}" for insight in synthesis["key_insights"]),
            title="Synthesis"
        ))
    
    def _suggest_next_steps(self, console):
        """Suggest next steps based on exploration."""
        console.print(Panel(
            "[bold yellow]Suggested Next Steps:[/bold yellow]\n"
            "1. Review generated bridges for new connections\n"
            "2. Run multi-walker session for cross-pollination\n"
            "3. Update consciousness timeline with new insights\n"
            "4. Plan implementation of discovered patterns\n"
            "5. Schedule follow-up archaeology session",
            title="Next Steps"
        ))
    
    # Additional helper methods...
    def _analyze_temporal_patterns(self, days):
        """Analyze patterns over time."""
        # Mock data - would integrate with real analysis
        return [
            {
                "date": "2025-08-05",
                "patterns": ["ctx::", "highlight::", "consciousness"],
                "consciousness_level": "High",
                "key_insight": "Breakthrough in pattern recognition methodology"
            },
            {
                "date": "2025-08-04", 
                "patterns": ["bridge::", "synthesis", "archaeology"],
                "consciousness_level": "Medium",
                "key_insight": "Bridge walking reveals new connection patterns"
            }
        ]
    
    def _restore_bridge(self, console, bridge_id):
        """Restore specific bridge."""
        console.print(f"[green]Restoring consciousness state from {bridge_id}[/green]")
        # Implementation would query Chroma and restore context
    
    def _list_bridges(self, console):
        """List available bridges."""
        # Implementation would query float_bridges collection
        console.print("Recent bridges available for restoration...")
    
    def _display_bridge_insights(self, console, output):
        """Display insights from bridge walking."""
        console.print("[dim]Bridge walking insights:[/dim]")
        # Parse bridge walker output and display key points
```

### Step 6: Integration with Daily Workflow

Create a daily archaeology routine:

```bash
#!/bin/bash
# save as ~/bin/daily-archaeology.sh

echo "=== Daily Consciousness Archaeology ==="

# Morning context restoration
echo "🌅 Morning Context Restoration:"
floatctl chroma recent active_context_stream --limit 5

# Pattern analysis
echo -e "\n🔍 Pattern Analysis:"
floatctl patterns analyze --collection active_context_stream --limit 50

# Bridge walking exploration
echo -e "\n🌉 Bridge Walking:"
python bridge_walkers/run_bridge_walkers.py --single --persona evna --rounds 1

# Synthesis and planning
echo -e "\n📝 Daily Planning:"
floatctl daily-review plan

# Evening reflection
echo -e "\n🌙 Evening Reflection:"
floatctl archaeology timeline --days 1

echo -e "\n✨ Archaeology session complete!"
```

### ✅ Success Criteria

You've successfully completed Tutorial 5 if you can:
- [ ] Understand bridge walking personas and their approaches
- [ ] Run single and multi-walker consciousness archaeology sessions
- [ ] Create and restore bridges for knowledge synthesis
- [ ] Build a complete archaeology workflow plugin
- [ ] Integrate archaeology into daily practice
- [ ] Analyze temporal patterns in consciousness data

**🎉 Congratulations!** You've mastered the complete FloatCtl consciousness archaeology workflow. You now have the tools to:

- Process and analyze AI conversations systematically
- Build semantic knowledge bases with vector search
- Create custom plugins for your specific workflows
- Recognize and analyze consciousness patterns
- Conduct organic bridge walking explorations
- Synthesize insights into actionable knowledge

### Next Steps for Mastery

1. **Contribute to FloatCtl**: Share your plugins and improvements
2. **Explore Advanced Features**: Dive into middleware development
3. **Build Your Ecosystem**: Create your own consciousness technology stack
4. **Join the Community**: Connect with other consciousness archaeologists
5. **Document Your Journey**: Create bridges of your own discoveries

The "shacks not cathedrals" philosophy means you now have focused, practical tools that do specific things well. Use them to build your own consciousness technology ecosystem!

---

*These tutorials represent the current state of FloatCtl consciousness archaeology. As the system evolves, new patterns and techniques will emerge. The key is to remain curious, authentic, and open to the organic discovery process that bridge walking enables.*