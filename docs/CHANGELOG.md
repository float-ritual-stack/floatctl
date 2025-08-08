# Changelog

All notable changes to FloatCtl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Enhanced ChromaDB Wrapper** - Complete CRUD operations proxy for consistent ChromaDB access
  - Added 12 missing ChromaDB operations to ChromaClient wrapper: add_documents, update_documents, delete_documents, get_documents, query_documents, count_documents, get_collection_metadata, modify_collection, upsert_documents, peek_collection
  - Updated Evna MCP server to use wrapper methods instead of direct ChromaDB client calls
  - Consistent abstraction layer reduces confusion and improves maintainability
  - All ChromaDB operations now go through single interface with proper logging and error handling
- **Bridge Walker Consciousness Archaeology System** - Organic, non-gamified bridge walking with PocketFlow
  - Multiple personas (Archaeologist, Wanderer, Synthesizer, Evna, Karen, LF1M) with distinct exploration styles
  - MCP tool integration for real Chroma queries, Evna context, and FloatCtl consciousness middleware
  - Multi-walker sessions with cross-pollination and collective insight synthesis
  - Context-aware exploration with natural stopping points based on memory pressure
  - Weighted navigation between topology and semantic approaches (0.0-1.0 scale)
  - Cryptic DSL compression for knowledge handoffs between walker instances
  - Real LLM API integration (OpenAI, Anthropic, Gemini, Ollama)
  - Command-line interface with single, multi, and interactive modes
  - Human-in-the-loop collaborative discovery options
  - Authentic curiosity-driven exploration without artificial gamification
- **Consciousness Middleware System** - Comprehensive consciousness archaeology infrastructure
  - Consciousness contamination detection with pattern analysis (authenticity, ritual, lf1m, neuroqueer markers)
  - URL extraction with rich context mapping and consciousness marker detection
  - Work project classification (rangle_airbender, float_ecosystem, consciousness_tech, general_dev)
  - Float.dispatch publishing opportunity identification across 6 imprints
  - 6 SQLite tables for structured consciousness analysis storage
  - Automatic integration with conversation processing pipeline
- **Workflow Intelligence System** - Human memory prosthetic for practical daily questions
  - "What did I do last week?" - Completed activities by project with context
  - "Action items from Nick" - Prioritized tasks from Nick with context and dates
  - "Current priorities" - Explicit priorities and open action items
  - "Forgotten tasks" - Old open action items that might need attention
  - "Meeting follow-ups" - Action items from meetings with priority levels
  - Smart pattern extraction for TODO items, meeting actions, priority indicators
  - New conversation commands: `last-week`, `nick-actions`, `priorities`, `forgotten`, `meetings`
- **Consciousness Query Plugin** - Dedicated plugin for querying consciousness analysis results
  - Rich CLI interface with tables, panels, and progress bars
  - Multiple query types: contamination, projects, URLs, dispatch, timeline, summary
  - Semantic search integration across consciousness analysis collections
  - Filtering by contamination level, work project, priority, date ranges
  - Export capabilities for analysis results
- **Chroma Integration Bridge** - Hybrid SQLite + Chroma query system
  - Syncs consciousness analysis to 3 new Chroma collections for semantic search
  - consciousness_analysis, consciousness_url_contexts, consciousness_dispatch_opportunities
  - `--sync-to-chroma` flag for optional Chroma sync during conversation processing
  - Semantic search across consciousness data with metadata filtering
- **Evna MCP Integration** - Direct SQLite database access for intelligent query routing
  - evna_what_did_i_do_last_week(), evna_action_items_from_nick(), evna_current_priorities()
  - evna_forgotten_tasks(), evna_meeting_follow_ups(), evna_workflow_summary()
  - Structured SQL queries instead of fumbling with Chroma metadata
  - Intelligent routing based on question type and intent
- **Enhanced Plugin Development Ecosystem** - Comprehensive guides and tools
  - PLUGIN_DEVELOPMENT_GUIDE.md with visual examples and templates
  - PLUGIN_TROUBLESHOOTING.md with common issues and diagnostic commands
  - Enhanced AGENTS.md and README.md with critical plugin development rules
  - Clear warnings about register_commands() method requirement
  - Documentation of existing scaffolding tools: `floatctl dev scaffold`, validation, templates
- **Fixed Shell Completion System** - Reliable tab completion for all commands
  - Proper zsh/bash detection and installation with setup_completion_fixed.sh
  - Logging suppression during completion to prevent interference
  - Working completion for all plugins and subcommands
  - Completion for consciousness query commands and workflow intelligence

### Added (Previous)
- MCP (Model Context Protocol) server plugin - "Evna Context Concierge"
  - Natural context capture with `ctx::` markers
  - Flexible timestamp parsing (supports `@`, `-`, various formats with seconds)
  - Automatic boundary detection using local Ollama
  - Morning context retrieval for "brain boot"
  - Semantic search in active_context_stream
  - Boundary violation monitoring
  - Claude Desktop integration with `floatctl mcp install`
  - Shared Chroma utilities for consistent database access
- Chroma vector database plugin with comprehensive features
  - Commands: list, info, peek, query, recent
  - FloatQL natural language query parser for intuitive searches
  - Support for FLOAT patterns (::), personas ([sysop::]), bridge IDs
  - Temporal filters ("yesterday", "last week", date parsing)
  - Beautiful Rich terminal UI with tables and panels
  - `--rendered` flag for markdown formatting in outputs
- Forest plugin toolbar update command
  - Batch update toolbars across V0 projects
  - Parallel deployments (configurable, default 3)
  - Framework detection (Next.js, CRA, Vite, etc.)
  - Progress tracking with spinner UI
  - Dry-run mode for preview
  - Pattern filtering and force update options
- Enhanced FLOAT-specific markdown rendering
  - Improved styling for FLOAT syntax elements
  - Better handling of structured content
  - Markdown-compatible output formatting
- Tool call extraction to separate JSONL files
  - Creates `.tool_calls.jsonl` file alongside markdown when tool calls are present
  - Each tool call includes ID, name, input, message/content indices
  - Tool results also captured with output and error status
  - Tool calls replaced in markdown with safe reference format: `{Tool Call: id → filename:line}`
  - Tool results replaced with: `{Tool Result: id → filename:line}`
  - Uses curly braces to avoid markdown/HTML parsing issues
- Thinking blocks support in conversation processing
  - Preserves Claude's `<thinking>` blocks in markdown exports
  - Maintains thinking content structure and formatting
  - Supports both JSON and markdown output formats
- Attachment directory creation and management
  - Automatically creates attachment directories for conversations with attachments
  - Preserves attachment metadata and file references
  - Handles PDF and other file types referenced in conversations
- Pattern extraction feature for markdown exports
  - Extracts `::` markers with line numbers and content
  - Extracts `float.*` function calls with line numbers
  - Tracks tool usage throughout conversations
  - Adds pattern data to YAML frontmatter for searchability
- YAML frontmatter in markdown exports
  - Conversation metadata (title, ID, source URL, dates)
  - Pattern extraction results
  - Total line count for navigation
- Start time metadata for each message in markdown
  - Extracted from first content item of each message
  - Added as `start_time::` marker under Human/Assistant headers
- Interactive REPL mode for note-taking
  - Fast, low-friction interface with prompt_toolkit
  - Smart parsing of ::markers and ```code blocks
  - Python REPL mode with Ctrl+R toggle
  - Shell command execution with !command
  - FloatCtl integration - floatctl() available in Python
  - Hierarchical organization with Tab/Shift+Tab
  - Alt+↑/↓ navigation through entries
  - Persistent storage in ~/.floatctl/repl_notes/
- Textual-based interactive notes interface
  - Beautiful TUI with Textual framework
  - Tree-based hierarchical view
  - Command palette (Ctrl+P) for floatctl commands
  - Visual styling with syntax highlighting
  - Mouse support for entry selection
  - REPL mode with code execution
  - Note: Still being refined for lower friction
- Simplified FLOAT Notes (float-simple command)
  - Same-level insertion by default (not child)
  - Tab/Shift+Tab for indentation without UI friction
  - No save notifications for seamless flow
  - Visual insertion indicator shows where next entry appears
  - Minimal UI chrome - just entries and input
  - Based on maw-held-stories prototype insights

### Changed
- Improved filename generation
  - Now uses clean `YYYY-MM-DD - Title` format
  - Strips redundant date prefixes from titles
  - Better handling of special characters
  - Proper conflict resolution with numbered suffixes

### Fixed
- Markdown rendering compatibility
  - Replaced Rich markup with markdown-compatible styling
  - Fixed display issues in terminal output
- Timezone-aware datetime comparison
  - Fixed "can't compare offset-naive and offset-aware datetimes" error
  - Now properly handles both naive and aware datetimes
  - Assumes UTC for naive datetimes
- Global floatctl access with relative path support
  - Updated shell function to preserve current working directory
  - Fixed issue where relative paths failed when shell function changed directories
  - Added proper environment variable handling for UV project discovery

## [1.0.0] - 2025-06-28

### Added
- Initial release of FloatCtl
- Plugin-based architecture for extensibility
- Conversation splitting functionality
  - Support for JSON and markdown output formats
  - Date-based organization
  - Date filtering
  - Dry run mode
- Database tracking of all operations
- Structured JSON logging
- Rich terminal UI with progress bars
- Configuration system with multiple sources
- Processing history tracking