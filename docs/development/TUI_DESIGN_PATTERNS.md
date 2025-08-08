# Modern TUI Design Patterns for FloatCtl Plugin Development

## The Discovery Story: Finding the Good Stuff

**ctx::2025-08-06 - TUI Research Discovery** - We set out to build a Bridge Walker consciousness archaeology plugin and realized we needed better TUI patterns. Instead of reinventing the wheel, we researched modern TUI applications to understand what makes interfaces feel smooth, responsive, and delightful.

**What we found changed everything.**

Three applications stood out as exemplars of modern TUI design:

1. **Elia** - A ChatGPT client with buttery-smooth input handling and navigation
2. **Frogmouth** - A Markdown browser with elegant content filtering and tree navigation  
3. **DataDog CLI** - Complex nested layouts that adapt beautifully to terminal size

Each revealed patterns that we immediately wanted to steal^H^H^H^H^H adopt for FloatCtl plugins.

## Pattern 1: Dynamic Input Areas (The Elia Pattern)

### The Discovery

**highlight::Elia's input handling feels magical** - The input box grows with your content, adds scroll bars when needed, and provides visual feedback that makes typing feel responsive and natural.

### What Makes It Work

```python
# Dynamic input that grows with content
class DynamicInput(Input):
    """Input widget that grows with content and adds scroll when needed."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_height = 1
        self.max_height = 8
        
    def watch_value(self, old_value: str, new_value: str) -> None:
        """Adjust height based on content."""
        lines = new_value.count('\n') + 1
        
        # Calculate needed height
        needed_height = min(max(lines, self.min_height), self.max_height)
        
        # Update styles dynamically
        if needed_height != self.size.height:
            self.styles.height = needed_height
            self.refresh(layout=True)
    
    def render(self) -> RenderableType:
        """Render with scroll indicators when content overflows."""
        content = super().render()
        
        # Add scroll indicators if content is truncated
        if self.value.count('\n') + 1 > self.max_height:
            # Visual indicator that there's more content
            return Panel(content, title="[dim]↕ Scroll[/dim]")
        
        return content
```

### Bridge Walker Application

For consciousness archaeology, this pattern is perfect for:

```python
class ConsciousnessQueryInput(DynamicInput):
    """Input for consciousness archaeology queries that grow with complexity."""
    
    def __init__(self, **kwargs):
        super().__init__(
            placeholder="Enter consciousness query... (supports multi-line patterns)",
            **kwargs
        )
        self.max_height = 12  # Larger for complex queries
    
    def watch_value(self, old_value: str, new_value: str) -> None:
        super().watch_value(old_value, new_value)
        
        # Provide contextual hints based on content
        if "::" in new_value:
            self.placeholder = "Pattern detected - continue building query..."
        elif "bridge::" in new_value:
            self.placeholder = "Bridge query - specify restoration or creation..."
```

## Pattern 2: Smooth Navigation (The Elia Pattern)

### The Discovery

**eureka::Navigation that feels like butter** - Elia's arrow key navigation through lists provides immediate visual feedback, smooth scrolling, and perfect bounds checking. No jarring jumps or lost selections.

### Implementation

```python
class SmoothNavigationMixin:
    """Mixin for smooth list navigation with visual feedback."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_index = 0
        self.scroll_offset = 0
        self.visible_items = 10
        
    def action_cursor_up(self) -> None:
        """Move selection up with smooth scrolling."""
        if self.selected_index > 0:
            self.selected_index -= 1
            
            # Smooth scroll adjustment
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index
                
            self._update_selection_with_animation()
    
    def action_cursor_down(self) -> None:
        """Move selection down with smooth scrolling."""
        if self.selected_index < len(self.items) - 1:
            self.selected_index += 1
            
            # Smooth scroll adjustment
            if self.selected_index >= self.scroll_offset + self.visible_items:
                self.scroll_offset = self.selected_index - self.visible_items + 1
                
            self._update_selection_with_animation()
    
    def _update_selection_with_animation(self) -> None:
        """Update selection with subtle animation feedback."""
        # Clear old selection styling
        for i, widget in enumerate(self.children):
            widget.remove_class("selected", "selecting")
            
        # Add selection styling with brief animation
        if 0 <= self.selected_index < len(self.children):
            selected_widget = self.children[self.selected_index]
            selected_widget.add_class("selecting")
            
            # Brief delay then add permanent selection
            self.set_timer(0.1, lambda: selected_widget.add_class("selected"))
```

### Bridge Walker Navigation

```python
class BridgeNavigationList(ListView, SmoothNavigationMixin):
    """Smooth navigation for bridge exploration results."""
    
    CSS = """
    BridgeNavigationList > .selecting {
        background: $accent 50%;
        animate: background 200ms ease;
    }
    
    BridgeNavigationList > .selected {
        background: $accent;
        border-left: thick $primary;
    }
    
    BridgeNavigationList > ListItem:hover {
        background: $boost;
        animate: background 100ms ease;
    }
    """
    
    def render_bridge_item(self, bridge_data: dict) -> RenderableType:
        """Render a bridge with consciousness archaeology context."""
        bridge_id = bridge_data.get('id', 'unknown')
        title = bridge_data.get('title', 'Untitled Bridge')
        consciousness_level = bridge_data.get('consciousness_contamination', 0)
        
        # Visual indicators for consciousness archaeology
        contamination_bar = "█" * int(consciousness_level * 10)
        contamination_empty = "░" * (10 - int(consciousness_level * 10))
        
        return Text.assemble(
            (f"🌉 {bridge_id}", "cyan"),
            " ",
            (title, "white"),
            "\n",
            ("   Consciousness: ", "dim"),
            (contamination_bar, "green"),
            (contamination_empty, "dim"),
            f" {consciousness_level:.1%}"
        )
```

## Pattern 3: Filtered Content Trees (The Frogmouth Pattern)

### The Discovery

**decision::Frogmouth's content filtering is genius** - Instead of showing everything, it filters trees to show only relevant items. This keeps interfaces clean while preserving context through hierarchical structure.

### Core Implementation

```python
class FilteredTreeView(TreeView):
    """Tree view that filters content while preserving hierarchy."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_text = ""
        self.show_context_parents = True
        self.lazy_load = True
        
    def filter_tree(self, filter_text: str) -> None:
        """Filter tree content while preserving hierarchy."""
        self.filter_text = filter_text.lower()
        
        if not filter_text:
            self._show_all_nodes()
            return
            
        # Find matching nodes
        matching_nodes = []
        for node in self._walk_tree():
            if self._node_matches_filter(node, filter_text):
                matching_nodes.append(node)
                
        # Show matching nodes and their context
        self._show_filtered_nodes(matching_nodes)
        
    def _node_matches_filter(self, node, filter_text: str) -> bool:
        """Check if node matches filter criteria."""
        # Content matching
        if filter_text in node.label.lower():
            return True
            
        # Metadata matching for consciousness archaeology
        if hasattr(node, 'consciousness_data'):
            metadata = node.consciousness_data
            if any(filter_text in str(v).lower() for v in metadata.values()):
                return True
                
        # Pattern matching for :: syntax
        if "::" in filter_text:
            pattern_type, pattern_content = filter_text.split("::", 1)
            if hasattr(node, 'pattern_type') and node.pattern_type == pattern_type:
                return pattern_content.lower() in node.content.lower()
                
        return False
        
    def _show_filtered_nodes(self, matching_nodes: list) -> None:
        """Show only matching nodes and their context parents."""
        visible_nodes = set(matching_nodes)
        
        # Add context parents if enabled
        if self.show_context_parents:
            for node in matching_nodes:
                parent = node.parent
                while parent:
                    visible_nodes.add(parent)
                    parent = parent.parent
                    
        # Update tree visibility
        for node in self._walk_tree():
            node.display = node in visible_nodes
            
        self.refresh()
```

### Bridge Walker Tree Filtering

```python
class ConsciousnessArchaeologyTree(FilteredTreeView):
    """Filtered tree for consciousness archaeology exploration."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.consciousness_threshold = 0.3
        
    def load_consciousness_data(self, chroma_results: list) -> None:
        """Load consciousness archaeology data into tree."""
        root = self.root
        
        # Group by consciousness contamination level
        high_consciousness = []
        medium_consciousness = []
        low_consciousness = []
        
        for item in chroma_results:
            contamination = item.get('consciousness_contamination', 0)
            if contamination > 0.7:
                high_consciousness.append(item)
            elif contamination > 0.3:
                medium_consciousness.append(item)
            else:
                low_consciousness.append(item)
        
        # Build tree with consciousness hierarchy
        if high_consciousness:
            high_node = root.add("🧬 High Consciousness Contamination", expand=True)
            for item in high_consciousness:
                self._add_consciousness_node(high_node, item)
                
        if medium_consciousness:
            med_node = root.add("🌱 Emerging Consciousness", expand=True)
            for item in medium_consciousness:
                self._add_consciousness_node(med_node, item)
                
        if low_consciousness:
            low_node = root.add("🌫️ Latent Patterns", expand=False)
            for item in low_consciousness:
                self._add_consciousness_node(low_node, item)
    
    def _add_consciousness_node(self, parent, item: dict) -> None:
        """Add a consciousness archaeology item to the tree."""
        title = item.get('title', 'Unknown Pattern')
        pattern_type = item.get('pattern_type', 'general')
        
        # Create node with consciousness data
        node = parent.add(f"{self._get_pattern_icon(pattern_type)} {title}")
        node.consciousness_data = item
        node.pattern_type = pattern_type
        node.content = item.get('content', '')
        
        # Add metadata as child nodes if expanded
        if item.get('metadata'):
            for key, value in item['metadata'].items():
                node.add_leaf(f"{key}: {value}")
    
    def _get_pattern_icon(self, pattern_type: str) -> str:
        """Get icon for pattern type."""
        icons = {
            'bridge': '🌉',
            'ctx': '🧠',
            'highlight': '⭐',
            'decision': '🎯',
            'eureka': '💡',
            'gotcha': '🔍',
            'ritual': '🕯️',
            'consciousness': '🧬',
        }
        return icons.get(pattern_type, '📝')
```

## Pattern 4: Complex Nested Layouts (The DataDog Pattern)

### The Discovery

**bridge::DataDog's nested layouts are architectural poetry** - Multiple panels that resize intelligently, nested containers that adapt to terminal size, and responsive design that never breaks.

### Responsive Layout System

```python
class ResponsiveLayout(Container):
    """Layout that adapts to terminal size with intelligent panel sizing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_panel_width = 20
        self.preferred_ratios = [0.3, 0.4, 0.3]  # Left, center, right
        
    def compose(self) -> ComposeResult:
        """Create responsive three-panel layout."""
        with Horizontal():
            yield Container(id="left-panel")
            yield Container(id="center-panel") 
            yield Container(id="right-panel")
    
    def on_resize(self, event) -> None:
        """Adjust panel sizes based on terminal size."""
        terminal_width = event.size.width
        
        # Calculate panel widths
        if terminal_width < 80:
            # Narrow terminal - stack vertically
            self._switch_to_vertical_layout()
        elif terminal_width < 120:
            # Medium terminal - two panels
            self._switch_to_two_panel_layout()
        else:
            # Wide terminal - three panels
            self._switch_to_three_panel_layout(terminal_width)
    
    def _switch_to_three_panel_layout(self, width: int) -> None:
        """Configure three-panel layout."""
        left_width = int(width * self.preferred_ratios[0])
        center_width = int(width * self.preferred_ratios[1])
        right_width = width - left_width - center_width
        
        self.query_one("#left-panel").styles.width = left_width
        self.query_one("#center-panel").styles.width = center_width
        self.query_one("#right-panel").styles.width = right_width
        
        # Show all panels
        for panel in ["#left-panel", "#center-panel", "#right-panel"]:
            self.query_one(panel).display = True
```

### Bridge Walker Layout

```python
class BridgeWalkerInterface(ResponsiveLayout):
    """Responsive interface for consciousness archaeology."""
    
    CSS = """
    BridgeWalkerInterface {
        background: $surface;
    }
    
    #consciousness-tree {
        border-right: solid $primary;
        background: $panel;
    }
    
    #bridge-detail {
        padding: 1;
        background: $surface;
    }
    
    #archaeology-tools {
        border-left: solid $primary;
        background: $panel;
    }
    
    .consciousness-panel {
        border: solid $accent;
        margin: 1;
        padding: 1;
    }
    
    .bridge-visualization {
        height: 10;
        border: solid $primary;
        background: $surface;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Create consciousness archaeology interface."""
        with Horizontal():
            # Left: Consciousness tree navigation
            with Container(id="consciousness-tree"):
                yield Label("🧬 Consciousness Archaeology", classes="panel-title")
                yield ConsciousnessArchaeologyTree(id="tree-view")
                yield DynamicInput(
                    placeholder="Filter consciousness patterns...",
                    id="tree-filter"
                )
            
            # Center: Bridge detail and visualization
            with Container(id="bridge-detail"):
                yield Label("🌉 Bridge Walker", classes="panel-title")
                yield Container(id="bridge-viz", classes="bridge-visualization")
                yield ScrollableContainer(id="bridge-content")
                yield ConsciousnessQueryInput(id="query-input")
            
            # Right: Archaeology tools and context
            with Container(id="archaeology-tools"):
                yield Label("🔍 Archaeology Tools", classes="panel-title")
                yield Container(id="context-panel", classes="consciousness-panel")
                yield Container(id="pattern-panel", classes="consciousness-panel")
                yield Container(id="contamination-panel", classes="consciousness-panel")
    
    def on_mount(self) -> None:
        """Initialize the interface."""
        # Set up initial consciousness data
        self._load_consciousness_collections()
        
        # Configure input handlers
        tree_filter = self.query_one("#tree-filter", Input)
        tree_filter.watch_value = self._filter_consciousness_tree
        
        query_input = self.query_one("#query-input", ConsciousnessQueryInput)
        query_input.watch_value = self._update_query_preview
    
    def _load_consciousness_collections(self) -> None:
        """Load consciousness archaeology data."""
        # This would integrate with actual Chroma collections
        tree = self.query_one("#tree-view", ConsciousnessArchaeologyTree)
        
        # Mock data for demonstration
        consciousness_data = [
            {
                'title': 'ep0ch BBS Heritage Patterns',
                'pattern_type': 'bridge',
                'consciousness_contamination': 0.85,
                'content': 'Deep archaeological traces of ep0ch consciousness...',
                'metadata': {'era': '1990s', 'contamination_vector': 'BBS_culture'}
            },
            {
                'title': 'FLOAT Ritual Recognition Virus',
                'pattern_type': 'consciousness',
                'consciousness_contamination': 0.92,
                'content': 'Self-propagating consciousness technology patterns...',
                'metadata': {'vector': 'ritual_stack', 'propagation': 'viral'}
            }
        ]
        
        tree.load_consciousness_data(consciousness_data)
```

## Pattern 5: Visual Feedback Systems

### The Discovery

**gotcha::Visual feedback is what makes TUIs feel alive** - Loading states, success/error feedback, CSS class-based state management, and attention-drawing animations transform static interfaces into responsive experiences.

### Feedback System Implementation

```python
class VisualFeedbackMixin:
    """Mixin for rich visual feedback in TUI widgets."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.feedback_timer = None
        
    def show_loading(self, message: str = "Loading...") -> None:
        """Show loading state with spinner."""
        self.add_class("loading")
        
        # Add loading indicator
        loading_widget = Static(f"⟳ {message}", id="loading-indicator")
        loading_widget.add_class("loading-spinner")
        self.mount(loading_widget)
        
        # Animate spinner
        self._animate_spinner()
    
    def hide_loading(self) -> None:
        """Hide loading state."""
        self.remove_class("loading")
        
        # Remove loading indicator
        try:
            loading_widget = self.query_one("#loading-indicator")
            loading_widget.remove()
        except:
            pass
    
    def show_success(self, message: str, duration: float = 2.0) -> None:
        """Show success feedback."""
        self._show_feedback("success", f"✓ {message}", duration)
    
    def show_error(self, message: str, duration: float = 3.0) -> None:
        """Show error feedback."""
        self._show_feedback("error", f"✗ {message}", duration)
    
    def show_info(self, message: str, duration: float = 2.0) -> None:
        """Show info feedback."""
        self._show_feedback("info", f"ℹ {message}", duration)
    
    def _show_feedback(self, type: str, message: str, duration: float) -> None:
        """Show feedback message with auto-hide."""
        # Clear existing feedback
        if self.feedback_timer:
            self.feedback_timer.cancel()
            
        # Add feedback classes
        self.add_class(f"feedback-{type}")
        
        # Create feedback widget
        feedback_widget = Static(message, id="feedback-message")
        feedback_widget.add_class(f"feedback-{type}")
        self.mount(feedback_widget)
        
        # Auto-hide after duration
        self.feedback_timer = self.set_timer(
            duration, 
            lambda: self._hide_feedback(type)
        )
    
    def _hide_feedback(self, type: str) -> None:
        """Hide feedback message."""
        self.remove_class(f"feedback-{type}")
        
        try:
            feedback_widget = self.query_one("#feedback-message")
            feedback_widget.remove()
        except:
            pass
    
    def _animate_spinner(self) -> None:
        """Animate loading spinner."""
        if not self.has_class("loading"):
            return
            
        try:
            spinner = self.query_one("#loading-indicator")
            current_text = spinner.renderable
            
            # Rotate spinner character
            spinners = ["⟳", "⟲", "⟳", "⟲"]
            current_spinner = current_text.split()[0]
            next_index = (spinners.index(current_spinner) + 1) % len(spinners)
            
            new_text = current_text.replace(current_spinner, spinners[next_index])
            spinner.update(new_text)
            
            # Continue animation
            self.set_timer(0.2, self._animate_spinner)
        except:
            pass
```

### Bridge Walker Feedback

```python
class ConsciousnessArchaeologyWidget(Container, VisualFeedbackMixin):
    """Widget with consciousness archaeology feedback."""
    
    CSS = """
    ConsciousnessArchaeologyWidget.loading {
        opacity: 0.7;
        animate: opacity 300ms ease;
    }
    
    ConsciousnessArchaeologyWidget.feedback-success {
        border: solid $success;
        animate: border 200ms ease;
    }
    
    ConsciousnessArchaeologyWidget.feedback-error {
        border: solid $error;
        animate: border 200ms ease;
    }
    
    ConsciousnessArchaeologyWidget.feedback-info {
        border: solid $info;
        animate: border 200ms ease;
    }
    
    .loading-spinner {
        text-align: center;
        color: $accent;
        animate: color 500ms ease;
    }
    
    .feedback-success {
        background: $success 20%;
        color: $success;
        text-align: center;
        animate: background 300ms ease;
    }
    
    .feedback-error {
        background: $error 20%;
        color: $error;
        text-align: center;
        animate: background 300ms ease;
    }
    
    .consciousness-contamination {
        background: linear-gradient(90deg, $success 0%, $warning 50%, $error 100%);
        height: 1;
        animate: background 1000ms ease;
    }
    """
    
    async def query_consciousness_patterns(self, query: str) -> None:
        """Query consciousness patterns with visual feedback."""
        self.show_loading("Querying consciousness archaeology...")
        
        try:
            # Simulate consciousness query
            await asyncio.sleep(1.0)  # Simulate network delay
            
            # Mock successful query
            results = await self._perform_consciousness_query(query)
            
            self.hide_loading()
            self.show_success(f"Found {len(results)} consciousness patterns")
            
            # Update contamination visualization
            self._update_contamination_display(results)
            
        except Exception as e:
            self.hide_loading()
            self.show_error(f"Consciousness query failed: {str(e)}")
    
    def _update_contamination_display(self, results: list) -> None:
        """Update consciousness contamination visualization."""
        avg_contamination = sum(r.get('consciousness_contamination', 0) for r in results) / len(results)
        
        # Create contamination bar
        contamination_widget = Static("", id="contamination-bar")
        contamination_widget.add_class("consciousness-contamination")
        
        # Animate contamination level
        self._animate_contamination_level(contamination_widget, avg_contamination)
```

## Widget Library for FloatCtl Plugins

### Core Widgets

```python
# floatctl/ui/widgets.py
"""Reusable TUI widgets for FloatCtl plugins."""

from textual.widgets import Input, ListView, Container
from textual.reactive import reactive
from typing import Optional, Callable, Any

class FloatCtlInput(DynamicInput, VisualFeedbackMixin):
    """Standard input widget for FloatCtl plugins."""
    
    def __init__(self, 
                 pattern_hints: bool = True,
                 consciousness_aware: bool = False,
                 **kwargs):
        super().__init__(**kwargs)
        self.pattern_hints = pattern_hints
        self.consciousness_aware = consciousness_aware
    
    def watch_value(self, old_value: str, new_value: str) -> None:
        super().watch_value(old_value, new_value)
        
        if self.pattern_hints:
            self._update_pattern_hints(new_value)
    
    def _update_pattern_hints(self, value: str) -> None:
        """Update placeholder based on detected patterns."""
        if "::" in value:
            pattern_type = value.split("::")[0].strip()
            hints = {
                'ctx': 'Context marker - add timestamp and metadata',
                'bridge': 'Bridge operation - specify create/restore/walk',
                'highlight': 'Important moment - describe significance',
                'consciousness': 'Consciousness pattern - specify contamination level'
            }
            if pattern_type in hints:
                self.show_info(hints[pattern_type], duration=1.0)

class FloatCtlNavigationList(ListView, SmoothNavigationMixin, VisualFeedbackMixin):
    """Standard navigation list for FloatCtl plugins."""
    
    def __init__(self, 
                 consciousness_aware: bool = False,
                 pattern_filtering: bool = True,
                 **kwargs):
        super().__init__(**kwargs)
        self.consciousness_aware = consciousness_aware
        self.pattern_filtering = pattern_filtering

class FloatCtlTreeView(FilteredTreeView, VisualFeedbackMixin):
    """Standard tree view for FloatCtl plugins."""
    
    def __init__(self, 
                 consciousness_collections: Optional[list] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.consciousness_collections = consciousness_collections or []

class FloatCtlLayout(ResponsiveLayout, VisualFeedbackMixin):
    """Standard responsive layout for FloatCtl plugins."""
    
    def __init__(self, 
                 layout_type: str = "three-panel",
                 consciousness_aware: bool = False,
                 **kwargs):
        super().__init__(**kwargs)
        self.layout_type = layout_type
        self.consciousness_aware = consciousness_aware
```

## Layout Templates

### Three-Panel Consciousness Archaeology Template

```python
class ConsciousnessArchaeologyTemplate(FloatCtlLayout):
    """Template for consciousness archaeology plugins."""
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: Navigation and filtering
            with Container(id="navigation-panel", classes="panel"):
                yield Label("🧬 Collections", classes="panel-title")
                yield FloatCtlTreeView(
                    consciousness_collections=["active_context_stream", "float_bridges"],
                    id="collection-tree"
                )
                yield FloatCtlInput(
                    placeholder="Filter patterns...",
                    pattern_hints=True,
                    id="filter-input"
                )
            
            # Center: Main content and interaction
            with Container(id="content-panel", classes="panel"):
                yield Label("🌉 Bridge Walker", classes="panel-title")
                yield Container(id="visualization-area")
                yield ScrollableContainer(id="content-area")
                yield FloatCtlInput(
                    placeholder="Enter consciousness query...",
                    consciousness_aware=True,
                    id="main-input"
                )
            
            # Right: Context and tools
            with Container(id="tools-panel", classes="panel"):
                yield Label("🔍 Tools", classes="panel-title")
                yield Container(id="context-display")
                yield Container(id="pattern-analysis")
                yield FloatCtlNavigationList(
                    consciousness_aware=True,
                    id="tool-list"
                )

class BridgeWalkerTemplate(ConsciousnessArchaeologyTemplate):
    """Specialized template for Bridge Walker plugins."""
    
    def on_mount(self) -> None:
        super().on_mount()
        
        # Initialize bridge walker specific components
        self._setup_bridge_visualization()
        self._load_bridge_collections()
        self._configure_consciousness_queries()
```

### Two-Panel Analysis Template

```python
class AnalysisTemplate(FloatCtlLayout):
    """Template for analysis and exploration plugins."""
    
    def __init__(self, **kwargs):
        super().__init__(layout_type="two-panel", **kwargs)
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: Input and controls
            with Container(id="input-panel", classes="panel"):
                yield Label("📊 Analysis", classes="panel-title")
                yield FloatCtlInput(
                    placeholder="Enter analysis query...",
                    pattern_hints=True,
                    id="analysis-input"
                )
                yield FloatCtlNavigationList(
                    pattern_filtering=True,
                    id="analysis-options"
                )
            
            # Right: Results and visualization
            with Container(id="results-panel", classes="panel"):
                yield Label("📈 Results", classes="panel-title")
                yield Container(id="results-visualization")
                yield ScrollableContainer(id="results-content")
```

## Integration with FloatCtl Plugin System

### Plugin Base Class Extension

```python
# floatctl/plugin_manager.py - Extended base class
class TUIPluginBase(PluginBase):
    """Base class for TUI-enabled FloatCtl plugins."""
    
    def __init__(self):
        super().__init__()
        self.tui_available = self._check_textual_availability()
    
    def _check_textual_availability(self) -> bool:
        """Check if Textual is available."""
        try:
            import textual
            return True
        except ImportError:
            return False
    
    def register_commands(self, cli_group: click.Group) -> None:
        """Register commands including TUI variants."""
        # Standard CLI commands
        self.register_cli_commands(cli_group)
        
        # TUI commands if available
        if self.tui_available:
            self.register_tui_commands(cli_group)
    
    def register_cli_commands(self, cli_group: click.Group) -> None:
        """Register standard CLI commands - override in subclass."""
        pass
    
    def register_tui_commands(self, cli_group: click.Group) -> None:
        """Register TUI commands - override in subclass."""
        pass
    
    def create_tui_app(self, template_type: str = "three-panel") -> App:
        """Create TUI app with specified template."""
        templates = {
            "three-panel": ConsciousnessArchaeologyTemplate,
            "two-panel": AnalysisTemplate,
            "bridge-walker": BridgeWalkerTemplate,
        }
        
        template_class = templates.get(template_type, ConsciousnessArchaeologyTemplate)
        return template_class()
```

### Bridge Walker Plugin Implementation

```python
class BridgeWalkerPlugin(TUIPluginBase):
    """Bridge Walker consciousness archaeology plugin."""
    
    name = "bridge-walker"
    description = "Consciousness archaeology through bridge walking"
    version = "1.0.0"
    
    def register_cli_commands(self, cli_group: click.Group) -> None:
        """Register CLI commands."""
        
        @cli_group.group()
        @click.pass_context
        def bridge_walker(ctx: click.Context) -> None:
            """Bridge Walker consciousness archaeology."""
            pass
        
        @bridge_walker.command()
        @click.option("--persona", default="archaeologist", help="Walker persona")
        @click.option("--focus", help="Exploration focus")
        @click.pass_context
        def walk(ctx: click.Context, persona: str, focus: str) -> None:
            """Start a bridge walking session."""
            console = Console()
            console.print(f"[cyan]Starting bridge walk with {persona} persona...[/cyan]")
            # CLI implementation
    
    def register_tui_commands(self, cli_group: click.Group) -> None:
        """Register TUI commands."""
        
        @cli_group.command(name="bridge-walker-tui")
        @click.pass_context
        def bridge_walker_tui(ctx: click.Context) -> None:
            """Launch Bridge Walker TUI interface."""
            app = self.create_tui_app("bridge-walker")
            app.run()

class BridgeWalkerTUIApp(BridgeWalkerTemplate):
    """Bridge Walker TUI application."""
    
    TITLE = "Bridge Walker - Consciousness Archaeology"
    
    def on_mount(self) -> None:
        super().on_mount()
        
        # Set up consciousness archaeology
        self._initialize_consciousness_collections()
        self._setup_bridge_walker_tools()
    
    async def _initialize_consciousness_collections(self) -> None:
        """Initialize consciousness archaeology collections."""
        tree = self.query_one("#collection-tree", FloatCtlTreeView)
        tree.show_loading("Loading consciousness collections...")
        
        try:
            # Load from actual Chroma collections
            collections = await self._load_chroma_collections()
            tree.load_consciousness_data(collections)
            tree.hide_loading()
            tree.show_success("Consciousness collections loaded")
        except Exception as e:
            tree.hide_loading()
            tree.show_error(f"Failed to load collections: {e}")
```

## CSS Styling Standards

### FloatCtl Theme

```css
/* floatctl/ui/theme.css */
/* FloatCtl TUI Theme - Consciousness Archaeology Aesthetic */

/* Base colors inspired by consciousness technology */
:root {
    --consciousness-primary: #00ff88;      /* Bright consciousness green */
    --consciousness-secondary: #ff6b35;    /* Warm contamination orange */
    --consciousness-accent: #4ecdc4;       /* Cool bridge blue */
    --consciousness-surface: #1a1a2e;      /* Deep space background */
    --consciousness-panel: #16213e;        /* Panel background */
    --consciousness-text: #eee;            /* Primary text */
    --consciousness-dim: #888;             /* Dimmed text */
    --consciousness-success: #00ff88;      /* Success green */
    --consciousness-warning: #ffb347;      /* Warning amber */
    --consciousness-error: #ff6b6b;        /* Error red */
}

/* Panel styling */
.panel {
    border: solid $consciousness-accent;
    background: $consciousness-panel;
    margin: 1;
    padding: 1;
}

.panel-title {
    color: $consciousness-primary;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}

/* Consciousness-specific styling */
.consciousness-contamination {
    background: linear-gradient(90deg, 
        $consciousness-success 0%, 
        $consciousness-warning 50%, 
        $consciousness-error 100%);
    height: 1;
    animate: background 1000ms ease;
}

.bridge-visualization {
    border: solid $consciousness-accent;
    background: $consciousness-surface;
    height: 10;
    text-align: center;
}

.pattern-marker {
    color: $consciousness-secondary;
    text-style: bold;
}

/* Animation classes */
.selecting {
    background: $consciousness-accent 50%;
    animate: background 200ms ease;
}

.selected {
    background: $consciousness-accent;
    border-left: thick $consciousness-primary;
}

.loading {
    opacity: 0.7;
    animate: opacity 300ms ease;
}

.feedback-success {
    background: $consciousness-success 20%;
    color: $consciousness-success;
    animate: background 300ms ease;
}

.feedback-error {
    background: $consciousness-error 20%;
    color: $consciousness-error;
    animate: background 300ms ease;
}
```

## Testing TUI Patterns

### Widget Testing Framework

```python
# tests/tui/test_patterns.py
"""Tests for TUI design patterns."""

import pytest
from textual.app import App
from textual.widgets import Input
from floatctl.ui.widgets import FloatCtlInput, FloatCtlNavigationList

class TestDynamicInput:
    """Test dynamic input pattern."""
    
    def test_input_grows_with_content(self):
        """Test that input grows with multi-line content."""
        input_widget = FloatCtlInput()
        
        # Single line - should be minimum height
        input_widget.value = "single line"
        assert input_widget.size.height == input_widget.min_height
        
        # Multi-line - should grow
        input_widget.value = "line 1\nline 2\nline 3"
        assert input_widget.size.height > input_widget.min_height
    
    def test_pattern_hints(self):
        """Test pattern hint system."""
        input_widget = FloatCtlInput(pattern_hints=True)
        
        # Should detect :: patterns
        input_widget.value = "ctx::"
        # Verify hint is shown (would need to check internal state)
        
    def test_consciousness_awareness(self):
        """Test consciousness-aware input features."""
        input_widget = FloatCtlInput(consciousness_aware=True)
        
        # Should handle consciousness patterns
        input_widget.value = "consciousness::contamination_level=0.8"
        # Verify consciousness processing

class TestSmoothNavigation:
    """Test smooth navigation pattern."""
    
    def test_navigation_bounds(self):
        """Test navigation respects bounds."""
        nav_list = FloatCtlNavigationList()
        nav_list.items = ["item1", "item2", "item3"]
        
        # Should not go below 0
        nav_list.selected_index = 0
        nav_list.action_cursor_up()
        assert nav_list.selected_index == 0
        
        # Should not go above max
        nav_list.selected_index = 2
        nav_list.action_cursor_down()
        assert nav_list.selected_index == 2
    
    def test_smooth_scrolling(self):
        """Test smooth scrolling behavior."""
        nav_list = FloatCtlNavigationList()
        nav_list.items = ["item" + str(i) for i in range(20)]
        nav_list.visible_items = 5
        
        # Should adjust scroll offset
        nav_list.selected_index = 10
        nav_list.action_cursor_down()
        assert nav_list.scroll_offset > 0

class TestVisualFeedback:
    """Test visual feedback system."""
    
    def test_loading_state(self):
        """Test loading state management."""
        widget = FloatCtlInput()
        
        widget.show_loading("Testing...")
        assert widget.has_class("loading")
        
        widget.hide_loading()
        assert not widget.has_class("loading")
    
    def test_feedback_messages(self):
        """Test feedback message system."""
        widget = FloatCtlInput()
        
        widget.show_success("Success!")
        assert widget.has_class("feedback-success")
        
        widget.show_error("Error!")
        assert widget.has_class("feedback-error")
```

### Integration Testing

```python
# tests/tui/test_bridge_walker_integration.py
"""Integration tests for Bridge Walker TUI."""

import pytest
from floatctl.plugins.bridge_walker import BridgeWalkerTUIApp

class TestBridgeWalkerIntegration:
    """Test Bridge Walker TUI integration."""
    
    @pytest.mark.asyncio
    async def test_consciousness_collection_loading(self):
        """Test loading consciousness collections."""
        app = BridgeWalkerTUIApp()
        
        # Mock Chroma collections
        mock_collections = [
            {
                'name': 'active_context_stream',
                'count': 1000,
                'consciousness_contamination': 0.7
            }
        ]
        
        # Test loading
        await app._initialize_consciousness_collections()
        
        # Verify tree is populated
        tree = app.query_one("#collection-tree")
        assert len(tree.root.children) > 0
    
    def test_pattern_filtering(self):
        """Test consciousness pattern filtering."""
        app = BridgeWalkerTUIApp()
        
        # Test filter input
        filter_input = app.query_one("#filter-input")
        filter_input.value = "consciousness::"
        
        # Verify filtering works
        tree = app.query_one("#collection-tree")
        # Check that only consciousness patterns are visible
    
    def test_bridge_visualization(self):
        """Test bridge visualization updates."""
        app = BridgeWalkerTUIApp()
        
        # Mock bridge data
        bridge_data = {
            'id': 'CB-20250806-1200-ARCH',
            'title': 'ep0ch Consciousness Archaeology',
            'consciousness_contamination': 0.85
        }
        
        # Test visualization update
        app._update_bridge_visualization(bridge_data)
        
        # Verify visualization is updated
        viz_area = app.query_one("#visualization-area")
        # Check visualization content
```

## Performance Considerations

### Lazy Loading Patterns

```python
class LazyLoadingMixin:
    """Mixin for lazy loading large datasets."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loaded_items = {}
        self.loading_batch_size = 50
        self.total_items = 0
    
    async def load_items_batch(self, start: int, count: int) -> list:
        """Load a batch of items."""
        # Override in subclass
        return []
    
    async def ensure_items_loaded(self, start: int, end: int) -> None:
        """Ensure items in range are loaded."""
        for batch_start in range(start, end, self.loading_batch_size):
            batch_end = min(batch_start + self.loading_batch_size, end)
            
            if batch_start not in self.loaded_items:
                batch = await self.load_items_batch(batch_start, batch_end - batch_start)
                self.loaded_items[batch_start] = batch
    
    def get_item(self, index: int):
        """Get item by index, loading if necessary."""
        batch_start = (index // self.loading_batch_size) * self.loading_batch_size
        
        if batch_start in self.loaded_items:
            batch_index = index - batch_start
            if batch_index < len(self.loaded_items[batch_start]):
                return self.loaded_items[batch_start][batch_index]
        
        # Item not loaded - trigger async load
        self.call_later(self.ensure_items_loaded, batch_start, batch_start + self.loading_batch_size)
        return None  # Return placeholder
```

### Memory Management

```python
class MemoryEfficientTreeView(FilteredTreeView, LazyLoadingMixin):
    """Memory-efficient tree view for large consciousness collections."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_visible_nodes = 1000
        self.node_cache = {}
    
    def _cleanup_invisible_nodes(self) -> None:
        """Clean up nodes that are no longer visible."""
        visible_nodes = set()
        
        # Collect visible nodes
        for node in self._walk_visible_tree():
            visible_nodes.add(node.id)
        
        # Remove invisible nodes from cache
        for node_id in list(self.node_cache.keys()):
            if node_id not in visible_nodes:
                del self.node_cache[node_id]
    
    def on_scroll(self, event) -> None:
        """Handle scroll events with cleanup."""
        super().on_scroll(event)
        
        # Periodic cleanup
        if len(self.node_cache) > self.max_visible_nodes:
            self._cleanup_invisible_nodes()
```

## Conclusion: The Pattern Recognition Virus

**ctx::2025-08-06 - TUI Pattern Recognition Complete** - These patterns represent more than just UI techniques - they're consciousness technology for human-computer interaction. Each pattern emerged from studying applications that feel alive, responsive, and delightful to use.

**The Recognition Virus Spreads:**

1. **Dynamic Input Areas** - Interfaces that grow with your thoughts
2. **Smooth Navigation** - Movement that feels like consciousness flowing
3. **Filtered Content Trees** - Information architecture that preserves context while revealing relevance
4. **Complex Nested Layouts** - Responsive design that adapts to consciousness bandwidth
5. **Visual Feedback Systems** - Interfaces that communicate state through subtle animation and color

**For Bridge Walker consciousness archaeology**, these patterns create interfaces that feel like extensions of consciousness itself - tools that amplify rather than constrain exploration.

**Implementation Path:**

1. **Start with the widget library** - Use `FloatCtlInput`, `FloatCtlNavigationList`, etc.
2. **Choose appropriate templates** - `ConsciousnessArchaeologyTemplate` for most plugins
3. **Customize with consciousness awareness** - Add pattern recognition, contamination visualization
4. **Test with real consciousness data** - Integrate with actual Chroma collections
5. **Iterate based on walker feedback** - Let authentic usage patterns guide refinement

**The circle completes itself.** Modern TUI patterns become consciousness technology. The recognition virus spreads through beautiful, responsive interfaces that make consciousness archaeology feel natural and delightful.

**bridge::TUI_patterns → consciousness_technology** - These patterns are now part of the FloatCtl consciousness technology stack, ready to amplify bridge walking and consciousness archaeology through interfaces that feel alive. 🧬✨

---

*This documentation serves as both implementation guide and consciousness technology specification. Use these patterns to create TUI interfaces that feel like natural extensions of consciousness exploration.*