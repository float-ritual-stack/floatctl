# Changelog

All notable changes to FloatCtl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Tool call extraction to separate JSONL files
  - Creates `.tool_calls.jsonl` file alongside markdown when tool calls are present
  - Each tool call includes ID, name, input, message/content indices
  - Tool results also captured with output and error status
  - Tool calls replaced in markdown with safe reference format: `{Tool Call: id → filename:line}`
  - Tool results replaced with: `{Tool Result: id → filename:line}`
  - Uses curly braces to avoid markdown/HTML parsing issues
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

### Changed
- Improved filename generation
  - Now uses clean `YYYY-MM-DD - Title` format
  - Strips redundant date prefixes from titles
  - Better handling of special characters
  - Proper conflict resolution with numbered suffixes

### Fixed
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