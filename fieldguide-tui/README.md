# fieldguide-tui

## Build & Run

```bash
cd fieldguide-tui
cargo run
```

## Keymap

- `Space` / `Enter`: Toggle the focused section open or closed.
- `e`: Cycle view mode between Normal → Compact → Expanded.
- `h`: Briefly highlight the focused section (800 ms).
- `j` / `Down`: Move focus to the next section.
- `k` / `Up`: Move focus to the previous section.
- `q`: Quit.

## MCP Tool Calls

All tools are exposed over stdio via the Model Context Protocol.

### expand_section

```json
{
  "name": "expand_section",
  "arguments": {
    "section_id": "mirc-patterns",
    "action": "expand"
  }
}
```

### change_view_mode

```json
{
  "name": "change_view_mode",
  "arguments": {
    "mode": "compact"
  }
}
```

### highlight_section

```json
{
  "name": "highlight_section",
  "arguments": {
    "section_id": "redux-evolution",
    "duration_ms": 1500
  }
}
```
