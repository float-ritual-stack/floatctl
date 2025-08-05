# Changelog

All notable changes to FloatCtl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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