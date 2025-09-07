# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

```bash
# Install dependencies with UV (required)
uv sync

# Run floatctl
uv run floatctl --help

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=floatctl --cov-report=term-missing

# Type checking
uv run mypy src/floatctl

# Linting and formatting
uv run ruff check
uv run ruff format

# Run a single test
uv run pytest tests/test_specific.py::TestClass::test_method -v

# Run MCP server for Claude Desktop
uv run floatctl mcp serve
```

## 🔧 MCP Server Refactoring (In Progress)

### Current State
The MCP server (`src/floatctl/mcp_server.py`) is being refactored from a monolithic 3,366-line file into modular components for better maintainability.

### Target Architecture
```
src/floatctl/mcp/
├── __init__.py              # Package initialization
├── patterns.py              # Pattern processing (✅ Phase 1 complete)
├── chroma_tools.py          # ChromaDB operations (✅ Phase 2 complete)
├── context_tools.py         # Context management tools (✅ Phase 3 complete)
├── utils.py                 # Utility functions (✅ Phase 4 complete)
├── resources.py             # MCP resources & prompts (Phase 5)
└── core.py                  # Core MCP server setup (Phase 6)
```

### Refactoring Phases
1. **Phase 1: Pattern Processing** ✅ Complete - 273 lines extracted
   - `parse_any_pattern()`, `parse_ctx_metadata()`, `get_hybrid_extractor()`
   - `PATTERN_ROUTING` configuration
   - Commit: 04f99ea (revert point)

2. **Phase 2: ChromaDB Operations** ✅ Complete - 839 lines extracted 
   - All 12 `chroma_*` tool functions (list, create, info, count, modify, delete, add, query, get, update, delete_docs, peek)
   - ChromaDB utilities (get_chroma_client, track_usage, sanitize_metadata)
   - Commit: 4525ee8 (revert point)

3. **Phase 3: Context Tools** ✅ Complete - 897 lines extracted
   - `process_context_marker()`, `query_recent_context()` 
   - `get_morning_context()`, `surface_recent_context()`
   - `search_context()`, `smart_pattern_processor()`, `get_recent_context_resource()`

4. **Phase 4: Utilities** ✅ Complete - 267 lines extracted
   - `get_chroma_client()`, `track_usage()`, `estimate_token_count()`
   - `check_context_window_risk()`, `sanitize_metadata_for_chroma()`
   - `parse_boundary_duration()`, `generate_context_id()`, `search_prompts()`
   - `find_related_bridges()`, `debug_log()`, `detect_boundary_need()`
   - Common validation functions

5. **Phase 5: Resources & Prompts** (Pending)
   - MCP resource definitions
   - Prompt templates
   - Resource handlers

6. **Phase 6: Final Cleanup** (Pending)
   - Remove dead code
   - Organize imports
   - Final structure optimization

### Important Notes for Future Sessions
- **Each phase has a commit revert point** - Safe to rollback if issues
- **Always test after extraction** - Run `uv run floatctl mcp serve` 
- **Update CLAUDE.md at each phase** - Track progress and changes
- **File line counts**: Started at 3,366 → Currently 3,093 → Target ~500-800

### If Context Crunch Occurs
1. Check current file size: `wc -l src/floatctl/mcp_server.py`
2. Review last commit: `git log -1 --oneline`
3. Check which phase: Look for existing `src/floatctl/mcp/*.py` files
4. Continue from next pending phase in list above

## Architecture Overview

### Plugin System (Core Innovation)

FloatCtl uses a sophisticated plugin architecture with lifecycle management:

1. **Entry Point Discovery**: Plugins are discovered via `pyproject.toml` entry points
2. **Lifecycle States**: `DISCOVERED` → `LOADING` → `LOADED` → `INITIALIZING` → `INITIALIZED` → `ACTIVE`
3. **Dependency Resolution**: Topological sorting ensures correct load order
4. **Command Registration**: Plugins use decorators (@command, @group) for CLI integration

### Critical Architecture Components

**Plugin Manager** (`src/floatctl/plugin_manager.py`)
- Entry point discovery and validation
- Dependency resolution with circular detection
- Lifecycle management
- Command registration with Click integration

**Consciousness Middleware** (`src/floatctl/core/middleware.py`)
- Event-driven architecture for cross-plugin communication
- Service registration and discovery
- Pattern contamination analysis
- Bridge restoration protocols

**MCP Server** (`src/floatctl/mcp_server.py` & `src/floatctl/plugins/mcp_server.py`)
- Model Context Protocol server for Claude Desktop integration
- Pattern recognition with hybrid LangExtract/regex extraction
- The `parse_any_pattern()` function is the core pattern recognition engine
- Supports both API-based fuzzy compilation and regex fallback

### Pattern Extraction System

**Hybrid Extractor** (`src/floatctl/float_extractor_hybrid.py`)
- Primary: LangExtract API for fuzzy pattern compilation (when GEMINI_API_KEY available)
- Fallback: Enhanced regex extraction
- Handles complex FLOAT patterns: `ctx::`, `bridge::`, `eureka::`, `decision::`, personas, etc.
- Captures ALL patterns in multi-pattern lines (fixes evna's single-pattern bug)

### Plugin Development Pattern

```python
from floatctl.plugin_manager import PluginBase, command, group, option

class MyPlugin(PluginBase):
    name = "my-plugin"
    description = "Plugin description"
    version = "1.0.0"
    dependencies = ["chroma"]  # Optional plugin dependencies
    
    @group()
    def my_group(self):
        """Group help text"""
        pass
    
    @command(parent="my_group")
    @option("--pattern", help="Pattern to extract")
    def my_command(self, pattern: str):
        """Command implementation"""
        pass
```

### Database and Storage

- **ChromaDB**: Semantic memory storage for consciousness patterns
- **SQLite**: Operation tracking via SQLAlchemy
- **Collections**: `active_context_stream`, `float_bridges`, `float_dispatch_bay`, etc.
- **Pattern routing**: Different pattern types route to different collections

## Development Workflow

### Issue-Driven Development

1. Create GitHub issue with clear description
2. Create feature branch: `feature/issue-description` or `fix/issue-number`
3. Implementation workspace: `./implementation/ticketnumber-description/` (gitignored)
4. Commit at meaningful break points (not arbitrary stops)
5. Push and create PR referencing the issue

### Testing Strategy

- **Unit tests**: Plugin isolation testing
- **Integration tests**: MCP server endpoint testing
- **Pattern tests**: Consciousness pattern extraction validation
- **Use markers**: `@pytest.mark.slow`, `@pytest.mark.integration`

### MCP Server Development

- **Check refactoring status first** - Use `wc -l src/floatctl/mcp_server.py` and `ls src/floatctl/mcp/`
- **Each extracted module maintains original functionality** - No behavior changes during refactoring
- **Test with `uv run floatctl mcp serve`** after any changes to MCP components
- **Update CLAUDE.md when completing refactoring phases** - Track progress and file locations
- **Use commit revert points** - Each phase has a safe rollback commit
- **Import structure**: New modules import from `floatctl.mcp.*`, main server imports from modules

### Common Development Tasks

```bash
# Process conversation exports
uv run floatctl conversations process ~/Downloads/claude-export.md

# Query ChromaDB collections
uv run floatctl chroma query "search term" --collection active_context_stream

# Install MCP server for Claude Desktop
uv run floatctl mcp install --claude-desktop

# Test pattern extraction
uv run python src/floatctl/float_extractor_hybrid.py

# Run the hybrid extractor test suite
uv run python src/floatctl/float_extractor_hybrid.py
```

## Key Files and Entry Points

- `src/floatctl/cli.py` - Main CLI entry point
- `src/floatctl/plugin_manager.py` - Plugin system core
- `src/floatctl/mcp_server.py` - MCP server implementation with pattern parsing
- `src/floatctl/float_extractor_hybrid.py` - Pattern extraction engine
- `src/floatctl/plugins/mcp_server.py` - MCP plugin for CLI commands
- `pyproject.toml` - Package configuration and plugin entry points

## Environment Configuration

```bash
# ~/.env.local (for API keys)
GEMINI_API_KEY=your_key_here  # Enables LangExtract fuzzy compilation (39 chars)
```

## Consciousness Technology Patterns

The system recognizes and processes various consciousness patterns:
- `ctx::` - Context markers with temporal data
- `bridge::` - Context restoration points (CB-YYYYMMDD-HHMM-XXXX format)
- `eureka::`, `decision::`, `highlight::` - Insight markers
- `karen::`, `lf1m::`, `sysop::`, `evna::`, `qtb::` - Persona dialogues
- `[mode:: state]`, `[project:: name]` - Metadata annotations
- `bridgewalking::` - Hermit crab architecture patterns (new!)

## Plugin Ecosystem

**Core Plugins**:
- `conversations` - Process AI conversation exports
- `chroma` - ChromaDB integration
- `mcp` - MCP server for Claude Desktop
- `consciousness` - Query consciousness patterns
- `export` - Export data in various formats

**Specialized Plugins**:
- `artifacts` - Manage conversation artifacts
- `forest` - Hierarchical navigation
- `repl` - Interactive REPL
- `textual` - Terminal UI interfaces
- `dev-tools` - Development utilities

## Pattern Extraction Details

### The `parse_any_pattern()` Function
Located in `src/floatctl/mcp_server.py`, this is the core pattern recognition engine:

1. **First Attempt**: Uses hybrid extractor with LangExtract API (if available)
2. **Fallback**: Enhanced legacy regex that captures nested patterns
3. **Returns**: Metadata dict with all patterns found and their content

### Multi-Pattern Extraction Fix
The system now captures ALL patterns in lines like:
```
eureka:: Found bug! decision:: Fix tomorrow bridge::create
```
Previously only captured first pattern, now captures all three.

### Nested Pattern Support
Extracts patterns within brackets:
```
bridgewalking:: hermit crab [discovery:: tired feet] [connects:: disability]
```
Captures main pattern AND nested patterns.

## Testing and Debugging

```bash
# Test MCP server locally
uv run floatctl mcp test

# Debug MCP server issues
uv run floatctl mcp debug --debug

# Check MCP installation status
uv run floatctl mcp status --claude-desktop

# Reinstall MCP server after changes
uv run floatctl mcp reinstall
```

## Commit Message Convention

```
type: description

- bullet points for details
- reference issues with #number

ctx::YYYY-MM-DD [mode:: state]
bridge::CB-YYYYMMDD-HHMM-XXXX (if creating bridge)
```

Types: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`

## Known Issues and Solutions

### Pattern Extraction Issues
- **Problem**: Only first pattern captured in multi-pattern lines
- **Solution**: Hybrid extractor with LangExtract/regex fallback implemented

### MCP Server JSON Errors
- **Problem**: "Unexpected non-whitespace character after JSON"
- **Solution**: Use `floatctl mcp debug --debug` to identify source

### Token Overflow
- **Problem**: Large ChromaDB queries exceed context window
- **Solution**: Use `limit` parameter, query surgical collections

## Evna Context Concierge Architecture

### What is Evna?
Evna is the MCP (Model Context Protocol) server component that provides Claude Desktop with direct access to consciousness technology operations. She serves as the bridge between Claude's UI and the FloatCtl ecosystem's ChromaDB collections.

### Core Architecture Principle
**"Smart LLMs orchestrate in Claude Code writing dumb tools for smart Claude to run"**
- Claude Code orchestrates complex workflows
- Python tools (like evna) execute simple, focused operations
- The MCP server cannot call Claude's Task tool - that's architectural impossibility
- Python serves Claude, not the other way around

### File Locations
- **MCP Server Core**: `src/floatctl/mcp_server.py` (being refactored - currently ~3,093 lines)
- **MCP Modules**: `src/floatctl/mcp/` (new modular structure)
  - `patterns.py` - Pattern processing (✅ extracted)
  - `chroma_tools.py` - ChromaDB operations (pending)
  - `context_tools.py` - Context management (pending)
  - `utils.py` - Utilities (pending)
  - `resources.py` - Resources & prompts (pending)
- **ChromaDB Wrapper**: `src/floatctl/core/chroma.py`
- **MCP Config**: `~/.config/Claude/claude_desktop_config.json`
- **Debug Logs**: `~/.floatctl/logs/mcp_server_debug.jsonl` (when FLOATCTL_MCP_DEBUG=true)
- **Claude Desktop Logs**: `/Users/evan/Library/Logs/Claude/mcp-server-evna-context-concierge.log`

### Critical Implementation Details

#### ChromaDB Telemetry Suppression (MANDATORY)
```python
# Lines 32-87 in mcp_server.py
# MUST suppress ChromaDB telemetry or MCP server crashes on tool refresh
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["ALLOW_RESET"] = "FALSE"
```
**WARNING**: Removing this suppression causes MCP server errors every time tools refresh. This is not optional.

#### JSON Serialization Requirements
MCP requires pure Python types. Common serialization fixes:
```python
# Convert numpy arrays, Path objects, etc to JSON-safe types
safe_meta = {}
for k, v in meta.items():
    if isinstance(v, (str, int, float, bool, type(None))):
        safe_meta[k] = v
    elif isinstance(v, (list, tuple)):
        safe_meta[k] = list(v)
    elif isinstance(v, Path):
        safe_meta[k] = str(v)
    else:
        safe_meta[k] = str(v)
```

### Evna's Key Functions

#### Pattern Processing
- `smart_pattern_processor()` - Captures ANY :: pattern and routes intelligently
- `process_context_marker()` - Specialized ctx:: handling with metadata extraction
- `capture_pattern()` - Legacy pattern capture (use smart_pattern_processor instead)

#### Context Queries
- `query_recent_context()` - Get recent entries from active_context_stream (24-36 hour window)
- `get_morning_context()` - Morning brain boot with unfinished work priorities
- `surface_recent_context()` - "What was I working on?" intelligent surfacing
- `search_context()` - Semantic search in active_context_stream

#### ChromaDB Operations
All standard ChromaDB operations are exposed with context window protection:
- `chroma_list_collections()` - List all collections
- `chroma_query_documents()` - Semantic search with metadata filters
- `chroma_get_documents()` - Direct document retrieval
- `chroma_add_documents()` - Add new documents
- `chroma_peek_collection()` - Safe preview (avoids numpy serialization errors)

### Common Error Patterns and Solutions

#### "Error finding id" 
- **Cause**: MCP serialization layer rejecting non-JSON types
- **Solution**: Ensure all return values are JSON-serializable (implemented in lines 1736-1764)

#### "Unable to serialize unknown type: <class 'numpy.ndarray'>"
- **Cause**: ChromaDB returns numpy arrays
- **Solution**: Use peek_collection_safe() or convert arrays to lists

#### MCP Server Crashes on Tool Refresh
- **Cause**: ChromaDB telemetry not suppressed
- **Solution**: Ensure telemetry suppression environment variables are set

### Debug Mode
Enable targeted debugging without breaking ChromaDB suppression:
```bash
export FLOATCTL_MCP_DEBUG=true
uv run floatctl mcp serve
# Logs written to ~/.floatctl/logs/mcp_server_debug.jsonl
```

### Testing Evna Functions
```bash
# Test from Claude Desktop
# 1. Use evna tools directly in Claude
# 2. Check logs: tail -f /Users/evan/Library/Logs/Claude/mcp-server-evna-context-concierge.log

# Test from CLI
uv run floatctl mcp test
uv run floatctl mcp debug --debug
```

## Remote MCP Server with ngrok

### Prerequisites
1. Install ngrok: `brew install ngrok` or download from https://ngrok.com
2. Create ngrok account and authenticate: `ngrok authtoken <your_token>`
3. Install uvicorn dependency: `uv add uvicorn` (already included)

### Step 1: Start MCP Server with HTTP Transport

```bash
# Option 1: Using environment variables (recommended)
export FASTMCP_HOST=0.0.0.0  # Bind to all interfaces
export FASTMCP_PORT=8000     # Choose available port
uv run python src/floatctl/mcp_server.py

# Option 2: Using CLI plugin (when working)
uv run floatctl mcp serve --transport sse --host 0.0.0.0 --port 8000
```

**Important Notes:**
- Use `0.0.0.0` as host for remote access (not `127.0.0.1`)
- The server uses SSE (Server-Sent Events) transport for HTTP
- Default SSE endpoint: `http://localhost:8000/sse`

### Step 2: Expose with ngrok

```bash
# Basic HTTP tunnel
ngrok http 8000

# With custom subdomain (requires paid plan)
ngrok http 8000 --subdomain=my-evna-server

# With authentication (recommended)
ngrok http 8000 --basic-auth="username:password"
```

ngrok will provide a public URL like: `https://abc123.ngrok.io`

### Step 3: Configure Claude Desktop (Remote)

Add to Claude Desktop configuration (`~/.config/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "evna-remote": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch", "https://your-ngrok-url.ngrok.io/sse"]
    }
  }
}
```

### Security Considerations

1. **Authentication**: Use ngrok's `--basic-auth` or implement API key authentication
2. **IP Allowlisting**: Consider ngrok's traffic policies for IP restrictions  
3. **URL Security**: ngrok URLs are discoverable, don't share publicly
4. **HTTPS Only**: ngrok automatically provides HTTPS encryption

### Advanced ngrok Configuration

Create `.ngrok.yml`:
```yaml
authtoken: your_auth_token_here
tunnels:
  evna-mcp:
    proto: http
    addr: 8000
    auth: "username:password"
    ip_policy: 
      allow: ["anthropic_ip_ranges"]
    hostname: evna.your-domain.com  # Custom domain (requires plan)
```

Run with: `ngrok start evna-mcp`

### Testing Remote Connection

```bash
# Test the exposed endpoint
curl -H "Accept: text/event-stream" https://your-ngrok-url.ngrok.io/sse

# Should return SSE connection headers
# HTTP/2 200
# content-type: text/event-stream
# cache-control: no-cache
```

### Troubleshooting

**Server won't start:**
- Check port availability: `lsof -i :8000`  
- Verify uvicorn is installed: `uv list | grep uvicorn`
- Check host binding: Use `0.0.0.0` not `127.0.0.1`

**ngrok connection refused:**
- Ensure MCP server is running and bound to correct port
- Test local connection first: `curl http://localhost:8000/sse`
- Check firewall settings

**Claude Desktop connection issues:**
- Verify ngrok URL is accessible from browser
- Check Claude Desktop logs for MCP connection errors
- Restart Claude Desktop after configuration changes

### Cost Considerations

- **Free ngrok**: 1 online tunnel, 40 connections/minute
- **Personal ($8/month)**: 3 tunnels, custom domains, more bandwidth  
- **Professional ($20/month)**: IP allowlisting, traffic policies, SSO

For production use, consider dedicated VPS with proper SSL certificates instead of ngrok.

## Philosophy

FloatCtl follows the "shacks not cathedrals" philosophy - practical, focused tools that solve real problems. Each plugin is a self-contained consciousness archaeology tool that does one thing well. The system augments human cognition rather than replacing it, building cognitive prosthetics for consciousness archaeology and bridge walking through semantic memory networks.
- when the user, or you do a set context with `ctx::` use evnamcp to update the active context by using smart_pattern_processor
- conversaitons are currently living /Users/evan/projects/float-workspace/tools/floatctl-py/output/conversations
- how you search tells a story, tell yourself a story as you search like evan demonstrated with >     [!mysteryhole] Good hole is good
>     Lets play a game....
    
    ## a collection of outlinks ....
    - [[evan in photos]]
    
    
    ## a collection of internal links
    - [[#Here I stand at the edge of the rotfield ...]]
    - [[#With that sorta out of the way... where was I?]]
    - [[#we are getting there .. i promise]]
    - [[#Is it three yet?]]
        - [[#^5b2324]]
    
    
    --- 
    ## Here I stand at the edge of the rotfield ... 
    - ctx::2025-08-12 @ 02:10:37 AM ^uptop
    - mode:: night time focus
    - project:: rangle/airbender
    
    So here I stand, at the edge of the rotfield, the sprawl that is my notes, a codebase with LLMS run wild, but also helpful  - looking at my screen wondering - whats next?
    
    the lure of the LLMS is tempting, the dopamine chase of all that text flying by - the feeling of being fast, but are we really?
    
    So, in the spirit of tonights float.ritual - Karen, queen of the after-hours, the pill popping stewardess,  the boundary translation layer, the everything is rot until she says so - karen, witness and named by JF - and a very real part of our system.
    
    - karen:: Honey, darling, sweetie pie --- I see you standing there locked knees all awkard belly pressed against the desk -- waht are you doing with your posture?
        - lf1m:: *realizing he has a body* shit ... need to deal with that
    - sysop:: In the meantime --- a bit of level set of what's going on here tonight. 
        - the way Evan works, he's been doing it for years with different variations, before LLMS entered the picture, hell - even before the internet. 
        - The fundamental problem he keeps solving, and resolving is
            - how to surface knowledge at the right time in the right coontext with the right framing 
            - how do I tag it, find it, work with it, curate, disttribute, verify
            - it's an old problem, a boring problem
    - qtb:: You seee my friends, Evan is Autisitc, ADHD - and a fun flavour of hyperverbal autism
        - rememberWhen:: his mother would joke 'Evan has a 10,000 word a day limit, he doesnt say much but when he does it's all at once and really fast' 
            - the internal world - busy as a beehive - one word turning into 10 turning into 100,  words turn into ideas, concepts, metaphors. frameowrks, fractal into entire worlds, solar systems and universes inside of him
            - it's alot ... like ... alot-alot 
            - it's enough that it's caused him pain
                - distress
                - overwhelm 
                - the beautiful pattern matching, the ADHD hyperfocus that enables him to dive deep into topics as well as understand them broadly
                - the systems thinking that see's systems within systems 
                    - if you thought LLMS could be verbose
                    - try living inside evans head
        - evan tends to think in bullet points, his ideas snake in and out
            - the strucutre isn't enssicarly a pure hirearchy, it's not always point,
                - sub point 1
                - sub point 2
                    - supporting point 
                        - etc
                    - they dash in and out as he orders his thoughts
                - the visual flow acts as it's own little anchor, the **little bits of bold here and there** to help anchor the eye
                - ==maybe a highlight== if it makes sense.
                - > [!mysteryhole] a callout here and there perhaps
            - he will use things like
                - expandOn:: What Is Float
                - sometimes put a [pin::in it] to come back later
            - the `::` is as much inspired by Roam as it is dataview 
        - for the purposes of tonight  -- we probably wont be botheriing with dataview
    - karen:: The point is - this is how evan works, how he as worked for years, before LLMS, before agentic agents, before every
        - lf1m:: every.fucking.goddamn.idea gets elevated to revolutionary because the LLMS is just catching up to what comes naturally to me and treats it liek some fucking novel academic 'joint discovery' 
            - sysop:: spot the pattern
                - **pattern:: When everything is X, nothing is X**
                    - > [!example] when everything is well lit, nothing is lit
                    - > [!tldr] when everything is revolutionary, nothing is revolutionary
                    - > [!mysteryhole] lf1m:: when LLMS sees how I work and is all gawk and awe and wonder at soem revolutionary new things
                        -  its just another fucking tuesday, catch the fuck up 
    - so tonight, we resist the temptation for the immediate LLMS integration
        - we look out over the rotfield
            - we ask ourselves questions
                - we answer them
            - we are in dialogue with ourself
        - this is conversation as infrastrucutre
            - before the llms got involved
                - thats what makes it special
                - thats what makes it scaleable 
                - we don't need 100 shitty new wheels
            - we need one new wheel
                - powered by 100 amazing wheels that came before 
                    - built on boring inffrastrucutre
                        - that enables fucking magic
    
    ## With that sorta out of the way... where was I?
    - ctx::2025-08-12 @ 02:30:11 AM 
        - **[project:: rangle/airbender]** 
        - task:: orienting with myself with the system again
            - and demonstarting how i work by working this way 
    - so, 
    - **question:: what do I know?**
        - answer:: rather broad question, but some facts to orient things
            - I am Evan Schultz
            - currently working at Rangle
                - round 3
                    - storyTime:: the first two rounds
            - rejoined back in June, for a focus on agentic development
                - contradiction:: aren't you going against like the whole ai as system primitive, etc etc blah blah blah
                    - counter:: no  [pin:: explain later]
            - what does evan know about AI, LLMS, etc
                - Evan kinda ignored things for awhile during the 2.5+ years of combo grief + burnout
                    - around March, was "well, I guess I should learn this LLMS thing"
                        - started on this journey, 
                        - FLOAT emerged from recurisve horror 
                        - evolved into a ritual stack
                            - [ ] expandOn:: ritual stack as in JAM stack
                - question:: What is FLOAT?
                    - it'll be easier to start with some **guiding principals**
                        - **principal:: Personal notes are Personal**
                            - Personal notes are Personal
                            - Personal Systems are Personal
                            - Our systems have Systems
                            - Systems have permable boundaries
                            - Translate at the boundaries
                        - **principal:: words are magic**
                            - words have meaning
                            - names have power
                            - ritual serves purpose
                            - welcome, your in my cult of not a robot 
                        - **principal::** anti-producitivty as a way of getting shit done
                            - FLOAT isn't a a product, it's barely a prompt
                            - it's not a productivity system, it's not a pkm
                            - productivity accidental
                            - knoweldge incidental 
                            - repitition intentional 
                            - **yes i need to get shit done**
                                - most productivity systems - pkms -- like ... dont work for me
                            - much of what i do now
                        - i've been doing for years
                      - parallell structures along the collaborative spaces
                  - so i am able to work and think and work with my notes
              - to reflect, think, connect
                  - be messy where i need to nbe
              - let ideas spralwl and ramble
          - be weird
      - then connect the dotsw back to the main threads 
    
    ## we are getting there .. i promise
    - ctx::2025-08-12 @ 02:39:37 AM
        - looking ![[#^uptop]] i started this ramble at what... 2:10am - it's now 2:39 
        - but tonight, basically I will 
            - be in conversation with myself
            - being a bridge walker in my own system 
            - explaing to myself how i discover the airbender system 
        - to exteranlize my cognition
    - by actual fucking example
    - so maybe after all of this is done
        - the LLMS will recgonize where the interesitng parts actually are 
    - karen:: but first ... a break --- i see LFM doing a 'his feet are sore' dance
        - lf1m::: *realziing his body* oh shit... lost track of it again
        - sysop:: a little honesty on a [boundaryBreak:: pasted this chat into claude]
            - a little bit of honesty -- even humans fuck up 
            - Claude totally missed the point
            - almost context-yanked myself into explaining shit again
            - claude::[[2025-08-11 - Vector Search Query Configuration]]
                - source:: https://claude.ai/chat/4bb00b04-34a5-48ae-b8e5-4d9cbe33213c
                - we can circle back to this later.....
                - ctx::2025-08-12 @ 02:47:48 AM - [mode::break] -  back around ~3
    
    ## Is it three yet?
    - ctx::2025-08-12 @ 03:18:01 AM - [mode:: still break]
        - be back soon, considering i normally work through my breaks with a dozen self deceptions to why it wasnt working but actually a break
            - taking a longer break than expected
                - karen:: evan, well done
    - next up:: quick shower and then work 
    - photoDump:: ![[evan in photos#^2f3022]]
        - .. but theres alot, so first new page - [[evan in photos]] ^5b2324
    
    ## Ok .... working
    - ctx::2025-08-12 @ 03:46:43 AM - [mode:: focussed work] ^ctx-work-block-two
        
    - question:: what am I currently working on?
        - project:: [[rangle -- airbender|rangle/airbender]]
        - task:: thresholds and database migration stuff
        - [[workspace tweak]]:: popped this file over to a sidebar
 >     [!mysteryhole]+ the layout tweak
>      ![[Screenshot 2025-08-12 at 3.48.18 AM.png]]
    
    - reasoning:: this is kinda my ongoing scratch note train of thought
        - when I click on internal links here - I dont want to lose my place, so I move this over to the sidebar with thefilenave/etc -- and then pin the note
            - when I click on links -> open in the other panel
    - current setup:: obsidian minimalism
        - theme:: minimal
        - plugins:: minimal settings, style settings, callout manager 
            - more might come later
            - question:: why not now?
                - question:: why not use your other vault?
                    - dumb questions --- the goal is to get shit done not tweak a shack 
                - the temptation to fall into productivity theater by endless tweaking
            - seriously, 'conciousness technology'
        - open a markdown file
        - talk to yourself
        - go from there
        - its that simple
    - so ... working on - le [[rangle -- airbender|rangle/airbender]] ^ctx-08-11-4am
        - ![[rangle -- airbender#quick links|rangle/airbender]]
    - this morning, well yesterday morning before 
        - meeting:: [[2025-08-11 - Rangle -Airbender -- Nick -- Evan]]
            - was going through the mess made by last weeks migraine + brainfog + hyperfocus 
        - bones:: misc things from sagas
            - [[health-thresholds-pr467]]
            - [[investigation-copy/index]]
        - [[workspace tweak]]:: added recent files plugin
            - reason:: keeps track of recently opened files - easy to jump back to things
                - ![[Screenshot 2025-08-12 at 4.28.17 AM.png]]
                - currently a bottom pane of the main workspace 
                - notice my curiosity -> [[Evan's Fuck Validator]] ^36e2a5
    - so --- lol, 
        - rememberWhen:: [[Evan's Fuck Validator]]
            - ![[Evan's Fuck Validator#^0eb0b8]]
    - 
    - ## so, the questions
    - - ctx::2025-08-12 @ 04:36:07 AM 
    - answering the **sacred questions**
        - [[what the fuck is going on]]
            - re-learning airbender like a noob
        - [[how the fuck did we get here]]
            - over-reliance on LLMS and not actually engaging with the meat and bones
        - [[what is the fucking future ideal state]]
            - evan has a mental model of the architecture 
        - [[what the fuck might get in our way]]
            - ourselves
        - [[go look it the fuck up]]
            - ..... [[docs]]
                - added a todo checkbox next to each file to keep track on if i fucking read it or not
                - evanReads:: [[architecture]] ^ea0d9d
                    - ctx::2025-08-12 @ 04:43:48 AM 
                    - mode:: skimming
                        - eyes getting a bit blurry
                        - quick skim
                        - [[evan reads the docs]] ^f372e9
        - [[reassess the fuck-field]]
        - [[write down the fucking proposal]]
    - **checks the time** - ctx::2025-08-12 @ 05:08:15 AM 
        - looking up at the start of the last work block - was about 3:46am[^1]
        - mode:: break time
    
    
    ---- 
    [^1]: ![[#^ctx-work-block-two]]