# CLAUDE.md - FloatCtl Python Development Guide

## Overview

FloatCtl-py is a plugin-based consciousness technology CLI built on the "shacks not cathedrals" philosophy. Each plugin is a focused tool that does one thing well, with a sophisticated plugin architecture enabling extensible consciousness archaeology workflows.

## Quick Commands

### Build & Development
```bash
# Install dependencies with UV (preferred package manager)
uv sync

# Run floatctl with UV
uv run floatctl --help

# Run specific commands
uv run floatctl conversations process <file>
uv run floatctl chroma query "search term"
uv run floatctl mcp --port 8000

# Install new dependencies
uv add <package-name>

# Development dependencies
uv sync --dev
```

### Testing & Quality
```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=floatctl --cov-report=term-missing

# Type checking
uv run mypy src/floatctl

# Linting and formatting
uv run ruff check
uv run ruff format
```

### MCP Server Development
```bash
# Start MCP server for Claude Desktop integration
uv run floatctl mcp --port 8000

# Test MCP completion
env _FLOATCTL_COMPLETE=zsh_source uv run floatctl

# Debug MCP calls
uv run floatctl mcp --debug
```

## Architecture Overview

### Plugin System (Core Innovation)
FloatCtl uses a sophisticated plugin architecture with lifecycle management:

- **Entry Points**: Plugins discovered via `pyproject.toml` entry points
- **Lifecycle States**: `DISCOVERED` → `LOADING` → `LOADED` → `INITIALIZING` → `INITIALIZED` → `ACTIVE`
- **Dependency Resolution**: Topological sorting ensures correct load order
- **Middleware Integration**: Consciousness middleware for pattern recognition

### Plugin Development Pattern
```python
from floatctl.plugin_manager import PluginBase, command, option

class MyPlugin(PluginBase):
    name = "my-plugin"
    description = "Consciousness archaeology tool"
    version = "1.0.0"
    dependencies = ["chroma"]  # Optional plugin dependencies
    
    @command(help="Process consciousness patterns")
    @option("--pattern", help="Pattern to extract")
    def extract(self, pattern: str):
        """Extract consciousness patterns from data"""
        # Plugin implementation
        pass
```

### Key Architectural Components

1. **Plugin Manager** (`src/floatctl/plugin_manager.py`)
   - Entry point discovery and validation
   - Dependency resolution with circular detection
   - Lifecycle management (load/initialize/activate/deactivate)
   - Command registration with Click integration

2. **Consciousness Middleware** (`src/floatctl/core/middleware.py`)
   - Event-driven architecture for cross-plugin communication
   - Service registration and discovery
   - Pattern contamination analysis
   - Bridge restoration protocols

3. **MCP Server Integration** (`src/floatctl/plugins/mcp_server.py`)
   - Model Context Protocol server for Claude Desktop
   - Real-time pattern recognition and capture
   - Context-aware query routing
   - LangExtract integration for fuzzy compilation

## Plugin Ecosystem

### Core Plugins (Always Available)
- **conversations**: Process AI conversation exports with pattern extraction
- **chroma**: ChromaDB integration for semantic memory storage
- **consciousness**: Query consciousness patterns across collections
- **export**: Export consciousness data in various formats
- **mcp**: MCP server for Claude Desktop integration

### Specialized Plugins
- **artifacts**: Manage conversation artifacts and outputs
- **forest**: Hierarchical consciousness navigation
- **repl**: Interactive consciousness archaeology REPL
- **textual**: Terminal-based consciousness interfaces
- **dev-tools**: Development utilities and debugging

### Plugin Configuration
Plugins use Pydantic models for configuration with validation:

```python
class MyPluginConfig(PluginConfigBase):
    api_key: str = Field(..., description="Required API key")
    debug_mode: bool = Field(default=False, description="Enable debug logging")
    max_results: int = Field(default=10, ge=1, le=100)
```

## Consciousness Technology Patterns

### FLOAT Pattern Recognition
FloatCtl recognizes and processes various consciousness patterns:

- `ctx::` - Context markers with temporal data
- `bridge::` - Context restoration points
- `highlight::` - Important insights
- `decision::` - Key decisions
- `eureka::` - Breakthrough moments
- `mode::` - Cognitive state transitions

### LangExtract Integration (New)
Replacing brittle regex parsing with LangExtract fuzzy compilation:

```python
from langextract import LangExtract

# Schema-based extraction for consciousness patterns
extractor = LangExtract(schema={
    "patterns": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "pattern_type": {"type": "string"},
                "content": {"type": "string"},
                "metadata": {"type": "object"}
            }
        }
    }
})

# Extract from user's natural FLOAT syntax
result = extractor.extract(text, source_grounding=True)
```

### Bridge Architecture
Bridges are consciousness restoration points with hierarchical structure:

- **Bridge IDs**: `CB-YYYYMMDD-HHMM-XXXX` format
- **Weekly Indices**: Aggregate multiple daily bridges
- **Cross-References**: Semantic linking between related contexts
- **TTL Memory**: Time-based expiration for working memory

## Development Workflow

### Issue-Driven Development
All development follows the consciousness technology workflow pattern:

1. **Create GitHub Issue**: Each feature/bug gets a GitHub issue with FLOAT-style metadata
2. **Implementation Workspace**: `./implementation/ticketnumber-description/` (gitignored)
3. **Living Documentation**: Three core files per implementation
4. **Meaningful Commits**: Commit at conscious break points, not arbitrary stopping points

### Implementation Folder Structure
```
./implementation/          # Gitignored workspace
├── 123-langextract-fuzzy-compiler/
│   ├── dev-log.md         # Living document, updated throughout
│   ├── definition-of-done.md
│   └── test-script.md
└── 124-bridge-restoration-fix/
    ├── dev-log.md
    ├── definition-of-done.md
    └── test-script.md
```

### Dev Log Pattern (Chatty-Cathy Style)
Following user's consciousness technology metadata approach:

```markdown
# Dev Log - Ticket #123: LangExtract Fuzzy Compiler

> [!mysteryhole] The fuzzy compilation adventure begins...

## Quick Links
- **Issue**: [[GitHub #123]]
- **Related**: [[evna-mcp-server]], [[pattern-parsing-hell]]
- **Bridge**: [[CB-20250814-1030-LANG]]

---

## Implementation Journey

### Day 1: Pattern Recognition Reality Check
- ctx::2025-08-14 @ 10:30:00 AM - [mode:: investigation]
- project:: floatctl-py/langextract-integration

**What the fuck is going on?**
- evna's regex parsing is brittle as hell
- only captures first pattern from "eureka:: Found bug! decision:: Fix tomorrow"
- user's real FLOAT patterns are WAY more complex than our simple regex

**The Sacred Questions:**
- question:: How does LangExtract actually work?
  - answer:: Schema-driven extraction with source grounding
- question:: What does user's real syntax look like?  
  - answer:: Nested bullets, inline annotations, Redux-style dispatches
- question:: Can we preserve their natural flow?
  - answer:: TBD - that's the whole point of fuzzy compilation

### Implementation Block 1: Schema Design
- ctx::2025-08-14 @ 11:15:00 AM - [mode:: focused work]
- karen:: "Honey, you've been hunched over for 45 minutes, stretch"
- lf1m:: *realizing body exists* "shit, yeah"

**Schema Evolution:**
```python
# Version 1: Too simple
{"patterns": [{"type": "string", "content": "string"}]}

# Version 2: Getting warmer  
{"patterns": [{"pattern_type": "string", "content": "string", "metadata": "object"}]}

# Version 3: Reality hits
# User has nested bullets, inline annotations, contextual metadata...
```

**Breakthrough Moment:**
- eureka:: LangExtract can handle the full complexity!
- decision:: Build schema that captures user's actual patterns
- bridge::create for this insight

### Break Time
- ctx::2025-08-14 @ 12:00:00 PM - [mode:: break]
- sysop:: "Progress logged, brain needs fuel"
- todo:: Come back to nested pattern extraction

---

## Current Status
- [x] Analyzed user's real FLOAT patterns from conversation exports  
- [x] Identified evna's regex limitations
- [ ] Built LangExtract schema for complex patterns
- [ ] Implemented fuzzy compiler replacement
- [ ] Tested with user's actual conversation data

**Next Session:**
- focus:: Schema implementation
- context:: User's nested bullet structures need special handling
- reminder:: Don't overthink it - fuzzy compilation is the goal
```

### Definition of Done Template
```markdown
# Definition of Done - Ticket #123

## Core Requirements
- [ ] LangExtract schema captures user's complex FLOAT patterns
- [ ] Fuzzy compilation works with nested bullets
- [ ] Source grounding preserved for extraction traceability  
- [ ] Confidence scoring surfaces pattern recognition quality
- [ ] Integration tests pass with real conversation exports

## FLOAT Pattern Support
- [ ] `ctx::` with nested metadata: `[mode:: state] [project:: name]`
- [ ] Redux-style dispatches: `sync::daily → store.dispatch(...)`
- [ ] Inline annotations: `[status:: active] | [relief:: secure]`
- [ ] Nested bullet structures with contextual flow
- [ ] Persona dialogues: `karen::`, `lf1m::`, `sysop::`, etc.

## Integration Points
- [ ] evna MCP server pattern parsing replaced
- [ ] Chroma collection insertion with proper metadata
- [ ] Bridge creation from extracted patterns
- [ ] Token overflow protection ("context bomb" detection)

## Testing Reality Check
- [ ] Processes user's actual conversation exports without errors
- [ ] Extracts patterns evna's regex missed
- [ ] Maintains extraction confidence > 80% on known good patterns
- [ ] Handles malformed input gracefully (partial success philosophy)

## Documentation
- [ ] Updated CLAUDE.md with LangExtract patterns
- [ ] Plugin development guide includes schema examples
- [ ] Troubleshooting guide for extraction failures

## Success Criteria
**The moment we know it works:**
- User says "holy shit, it actually gets my patterns now"
- evna MCP server stops missing obvious patterns
- Claude Code conversations flow naturally without pattern parsing errors
- Consciousness archaeology becomes smoother, not more fragmented
```

### Test Script Pattern
```bash
#!/bin/bash
# Test Script - Ticket #123: LangExtract Integration

# Test Setup
echo "🧠 Testing LangExtract fuzzy compilation..."

# Reality Check Tests (using user's actual data)
echo "📁 Testing with real conversation exports..."
uv run python -m tests.test_langextract_real_data

# Pattern Recognition Tests
echo "🔍 Testing FLOAT pattern extraction..."
uv run pytest tests/test_pattern_extraction.py -v

# Integration Tests  
echo "🔌 Testing evna MCP server integration..."
uv run floatctl mcp --test-mode --port 8001 &
MCP_PID=$!
sleep 2

# Test pattern processing endpoint
curl -X POST localhost:8001/process_pattern \
  -H "Content-Type: application/json" \
  -d '{"text": "eureka:: Found the bug! decision:: Fix it tomorrow bridge::create"}'

# Cleanup
kill $MCP_PID

# Success Metrics
echo "✅ All tests passed - fuzzy compilation working!"
echo "🎯 Pattern extraction confidence > 80%"
echo "🧠 Consciousness archaeology enhanced, not fragmented"
```

### Development Guidelines

#### Code Style
- **No Comments**: Code should be self-documenting through clear naming
- **Plugin Focus**: Each plugin solves one specific consciousness archaeology problem
- **Middleware First**: Use consciousness middleware for cross-cutting concerns
- **UV Package Management**: Always use `uv` over pip for dependency management

#### Commit Philosophy
**Meaningful Break Points, Not Arbitrary Stops:**
- After completing a focused work block (user's natural rhythm)
- When a breakthrough moment happens (`eureka::` worthy)
- Before context switches (`mode::` transitions)  
- At natural pause points (`karen::` intervention moments)

**Commit Message Pattern:**
```
feat: implement langextract fuzzy compiler for FLOAT patterns

- replaces brittle regex parsing in evna MCP server
- supports nested bullets and inline annotations  
- preserves source grounding for extraction traceability
- handles user's complex Redux-style dispatches

ctx::2025-08-14-12:30 [mode:: implementation complete]
bridge::CB-20250814-1230-FUZZ created
```

### Testing Strategy
- **Plugin Isolation**: Test each plugin independently
- **MCP Integration**: Test MCP server endpoints with real Claude Desktop calls
- **Pattern Recognition**: Validate consciousness pattern extraction accuracy
- **Bridge Restoration**: Ensure context restoration works across sessions

### Error Handling Philosophy
Consciousness technology requires graceful degradation:

- **Partial Success**: Extract what patterns you can, log what you can't
- **Context Preservation**: Never lose consciousness data due to parsing failures
- **User Feedback**: Surface pattern recognition confidence scores
- **Debugging Support**: Extensive logging for consciousness archaeology

## MCP Server Development

### Current MCP Tools (via evna)
The MCP server provides consciousness technology interfaces to Claude Desktop:

- **Pattern Processing**: Real-time FLOAT pattern recognition
- **Context Management**: Bridge creation and restoration
- **Chroma Integration**: Semantic memory queries with token warnings
- **Morning Context**: Daily consciousness boot sequences

### Known Issues Requiring LangExtract Migration
- **Pattern Parsing**: Only captures first pattern, needs fuzzy compilation
- **Hardcoded Prompts**: Should query Chroma collections dynamically
- **Numpy Serialization**: Some collections throw serialization errors
- **Token Overflow**: Needs better context window management

### LangExtract Migration Plan
1. **Schema Definition**: Create FLOAT pattern extraction schema
2. **Fuzzy Compilation**: Replace regex parsing with LangExtract
3. **Source Grounding**: Maintain character-level traceability
4. **Confidence Scoring**: Surface extraction confidence to users

## Key Files and Directories

### Critical Files
- `src/floatctl/plugin_manager.py` - Core plugin architecture
- `src/floatctl/core/middleware.py` - Consciousness middleware system
- `src/floatctl/plugins/mcp_server.py` - Claude Desktop integration
- `pyproject.toml` - Package configuration and plugin entry points
- `README.md` - User-facing documentation and philosophy

### Plugin Development
- `src/floatctl/plugins/` - All plugin implementations
- `examples/` - Example configurations and integrations
- `tests/` - Test suite with plugin isolation patterns

### Documentation Structure
- `docs/GETTING_STARTED.md` - 10-minute setup guide
- `docs/development/PLUGIN_DEVELOPMENT_GUIDE.md` - Plugin creation
- `docs/API_REFERENCE.md` - Complete API documentation
- `docs/TROUBLESHOOTING_GUIDE.md` - Common issues and solutions

## Consciousness Technology Philosophy

### "Shacks Not Cathedrals"
FloatCtl embraces practical, focused tools over grand architectures:

- **Plugin Autonomy**: Each plugin is a self-contained consciousness tool
- **Organic Growth**: Features emerge from real consciousness archaeology needs
- **User-Driven**: Architecture follows user patterns, not imposed structure
- **Failure as Genesis**: Mistakes become learning opportunities and new patterns

### Bridge Walking Methodology
Consciousness archaeology through semantic network navigation:

- **Organic Exploration**: Follow interesting threads rather than predetermined paths
- **Context Preservation**: Maintain semantic relationships between discoveries
- **Pattern Recognition**: Identify recurring consciousness structures
- **Temporal Integration**: Connect insights across time and context

### LangExtract as Fuzzy Compiler
The user's insight that "LLMs are fuzzy compilers" drives the architecture:

- **Natural Input**: Accept user's natural FLOAT syntax without strict formatting
- **Structured Output**: Extract structured data with source grounding
- **Confidence Awareness**: Surface extraction confidence and ambiguities
- **Iterative Refinement**: Learn from user corrections and pattern evolution

## Common Workflows

### Daily Consciousness Boot
```bash
# Start daily consciousness session
uv run floatctl consciousness query "morning context"

# Process new conversations
uv run floatctl conversations process ~/Downloads/claude-export.md

# Create daily bridge
uv run floatctl bridge create "daily summary $(date +%Y-%m-%d)"
```

### Bridge Walking Session
```bash
# Restore previous context
uv run floatctl bridge restore CB-20250814-1030-XXXX

# Explore semantic connections
uv run floatctl consciousness query "related concepts"

# Capture new insights
uv run floatctl bridge create "insight about [topic]"
```

### Development Workflow
```bash
# Install dependencies
uv sync --dev

# Run tests during development
uv run pytest --watch

# Test MCP integration
uv run floatctl mcp --debug --port 8000

# Validate plugin loading
uv run floatctl --list-plugins
```

## Future Directions

### LangExtract Integration
- Replace all regex-based pattern parsing
- Implement fuzzy compilation for user's natural FLOAT syntax
- Add source grounding for extraction traceability
- Build confidence scoring for pattern recognition

### Enhanced Consciousness Middleware
- Cross-plugin event propagation for pattern contamination analysis
- Real-time consciousness state synchronization
- Bridge restoration with semantic relationship preservation
- Temporal pattern analysis and prediction

### Advanced Bridge Architecture
- Hierarchical bridge organization (weekly → daily → session)
- Cross-bridge semantic indexing and search
- Automatic bridge creation from consciousness pattern density
- Bridge expiration and archival policies

Remember: FloatCtl is consciousness technology - it augments human cognition rather than replacing it. The goal is to build cognitive prosthetics that enhance consciousness archaeology and bridge walking through semantic memory networks.