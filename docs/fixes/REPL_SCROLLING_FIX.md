# REPL Scrolling Implementation

## The Problem
The interactive REPL outliner didn't have scrolling functionality - when entries went off the page, users couldn't view them even though they could navigate to them with Alt+↑/↓.

## The Solution

### 1. Viewport-Based Rendering
Added viewport tracking to only render entries visible on screen:

```python
# Track viewport position
self.viewport_top = 0
self.viewport_height = 20  # Calculated dynamically

# Only render entries within viewport
for i in range(self.viewport_top, viewport_end):
    # Render entry
```

### 2. Auto-Scrolling
The selected entry is always kept visible when navigating:

```python
def ensure_selected_visible(self):
    if self.selected < self.viewport_top:
        # Scroll up to show selected
        self.viewport_top = self.selected
    elif self.selected >= self.viewport_top + self.viewport_height:
        # Scroll down to show selected
        self.viewport_top = self.selected - self.viewport_height + 1
```

### 3. Manual Scrolling Controls
Added keyboard shortcuts for scrolling:
- **Page Up/Page Down**: Scroll by full page
- **Home**: Jump to first entry
- **End**: Jump to last entry
- **Alt+↑/↓**: Navigate entries (with auto-scroll)

### 4. Visual Indicators
Added scroll indicators to show when content exists outside viewport:
```
  ↑ 10 more entries above ↑
  
  [visible entries]
  
  ↓ 25 more entries below ↓
```

### 5. Dynamic Height Calculation
The viewport height adjusts based on terminal size:
```python
height = app.output.get_size().rows
# Subtract fixed UI elements
self.viewport_height = max(5, height - 8 - get_input_height())
```

## Testing
Created test script that generates 50 entries to test scrolling:
```bash
python test_repl_scrolling.py
uv run floatctl repl
```

## Result
The REPL outliner now supports unlimited entries with smooth scrolling, maintaining the hierarchical outliner concept while being usable with large amounts of content.

## Future Ideas
- Mouse wheel support for scrolling
- Smooth scrolling animations
- Jump to search results
- Folding/collapsing of indented sections
- Minimap showing scroll position