# Conversations Plugin - CLAUDE.md

This file provides AI-specific guidance for working with the Conversations plugin.

## Overview

The Conversations plugin processes Claude AI conversation exports, extracting patterns, metadata, and creating searchable markdown files with YAML frontmatter.

## Pattern Extraction

### Marker Patterns (`::`)
The plugin extracts inline annotations using the `::` syntax:
```
ctx:: timestamp or context marker
highlight:: important content to remember
mode:: cognitive state (e.g., "deep focus", "exploration")
project:: project association
claude:: conversation URL
start_time:: message timestamp
```

### FLOAT Function Calls
Recognizes and extracts FLOAT system calls:
```
float.dispatch({...})
float.context.restore(...)
float.context.restore.surgical(...)
float.bridge.create(...)
```

### Tool Usage Tracking
Automatically tracks all AI assistant tool usage:
- MCP tool calls (mcp__*)
- Standard tools (Read, Write, Bash, etc.)
- Creates separate `.tool_calls.jsonl` files

## File Naming Conventions

### Clean Format
```
YYYY-MM-DD - Title.md
```

Examples:
- `2025-07-13 - Consciousness Bootstrap Protocol.md`
- `2025-07-14 - FLOAT Pattern Extraction.md`

### Duplicate Handling
- Appends numbers for conflicts: `Title-2.md`, `Title-3.md`
- Strips redundant date prefixes from titles

## YAML Frontmatter Structure

```yaml
---
conversation_title: "Clean title without date"
conversation_id: UUID
conversation_src: https://claude.ai/chat/UUID
conversation_created: ISO timestamp
conversation_updated: ISO timestamp
conversation_dates:
  - YYYY-MM-DD (list of unique dates)
markers:
  - type: "marker_type"
    content: "marker content"
    lines: [line_numbers]
float_calls:
  - call: "function.name"
    content: "arguments if any"
    lines: [line_numbers]
tools_used: ['tool1', 'tool2']
total_lines: number
---
```

## Tool Call Extraction

### Reference Format
In markdown files, tool calls are replaced with:
```
{Tool Call: tool_id → filename:line}
{Tool Result: tool_id → filename:line}
```

### JSONL Structure
```json
{
  "id": "toolu_01ABC",
  "type": "tool_use",
  "name": "ToolName",
  "input": {...},
  "message_index": 1,
  "content_index": 1,
  "sender": "assistant",
  "created_at": "ISO timestamp",
  "line_number": 123
}
```

## Processing Tips

### Large Files
- Use `--filter-after` to process recent conversations
- Consider `--by-date` organization for many files
- Tool extraction prevents markdown bloat

### Pattern Search
After processing, use grep to find patterns:
```bash
# Find context markers
grep -n "ctx::" output/*.md

# Find specific tool usage
grep -l "chroma_query" output/*.tool_calls.jsonl

# Find float dispatches
grep -A2 "float_calls:" output/*.md
```

### Integration Points
- Extracted patterns feed into Chroma indexing
- Tool calls support analysis workflows
- YAML frontmatter enables Dataview queries in Obsidian
- Line numbers facilitate navigation in long conversations

## Common Issues

### Timezone Handling
- All timestamps normalized to UTC
- Naive datetimes assumed to be UTC
- Use `--filter-after YYYY-MM-DD` for date filtering

### Memory Usage
- Large export files processed in streaming mode
- Pattern extraction is memory-efficient
- Consider splitting very large exports

### Character Encoding
- UTF-8 encoding throughout
- Special characters in titles sanitized
- Emoji and Unicode preserved in content