# Chroma Plugin - CLAUDE.md

This file provides AI-specific guidance for working with the Chroma plugin.

## Overview

The Chroma plugin provides vector database integration for FLOAT, with a custom FloatQL query language that understands FLOAT-specific patterns.

## FloatQL Query Patterns

### Marker Detection
```python
# Patterns to recognize:
"ctx::" -> context markers
"highlight::" -> highlight annotations  
"mode::" -> cognitive state markers
"bridge::" -> bridge references
```

### Persona Recognition
```python
# FLOAT personas in brackets:
"[sysop::]" -> system operator persona
"[karen::]" -> translator persona
"[evna::]" -> emotional logic persona
"[lf1m::]" -> little fucker persona
```

### Bridge ID Format
```
bridge::CB-YYYYMMDD-HHMM-XXXX
- CB = Context Bridge
- Date/time stamp
- 4-char unique identifier
```

### Temporal Parsing
- "yesterday" -> previous day
- "last week" -> 7 days ago
- "July 13" -> specific date parsing
- "last 24 hours" -> time range

## Collection Routing Strategy

### High-Value Collections
1. **active_context_stream** - 36-hour rolling window, well-chunked
2. **float_bridges** - Refined synthesis documents
3. **float_highlights** - Key moments and insights
4. **float_dispatch_bay** - Mixed content, query carefully

### Query Optimization
- Start with n_results=3-5 to avoid token explosion
- Use metadata filters when possible
- Prefer surgical queries over comprehensive searches

## Common Query Examples

```bash
# Find recent context
floatctl chroma floatql "ctx:: from yesterday"

# Find specific bridge
floatctl chroma floatql "bridge::CB-20250713-0130-M3SS"

# Find persona-specific content
floatctl chroma floatql "[sysop::] infrastructure"

# Rendered output for bridges
floatctl chroma floatql "bridge:: meeting notes" --rendered
```

## Error Handling

### Token Limit Exceeded
- Reduce n_results
- Use --preview-length to limit content
- Query more specific collections

### No Results Found
- Check collection exists with `floatctl chroma list`
- Broaden temporal filters
- Try alternate marker syntax

## Integration with FLOAT Ecosystem

The Chroma plugin is designed to work with:
- Bridge restoration workflows
- Context stream navigation
- Highlight extraction
- Dispatch bay queries

When working with bridges, always check for restoration commands in the metadata.