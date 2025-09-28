# fieldguide-tui

`fieldguide-tui` is a Ratatui-powered terminal application that renders the Pattern Dispatch Evolution field guide while exposing MCP tools over stdio. Launch it locally and connect any MCP-capable client to automate navigation, view mode changes, and section highlights.

## Build & Run

```bash
cargo run
```

The application boots the UI and an MCP server on stdio. Attach an MCP inspector or client that speaks the Model Context Protocol to issue tool calls.

## Key Bindings

- `Space` / `Enter` — Toggle the focused section open or closed.
- `e` — Cycle the view mode (Normal → Compact → Expanded).
- `↑` / `↓` or `j` / `k` — Move focus between sections.
- `h` — Briefly highlight the focused section.
- `q` — Quit the application.

## MCP Tool Calls

Send JSON-RPC tool requests with the following payload shapes:

```json
{
  "name": "expand_section",
  "arguments": {
    "section_id": "mirc-patterns",
    "action": "expand"
  }
}
```

```json
{
  "name": "change_view_mode",
  "arguments": {
    "mode": "expanded"
  }
}
```

```json
{
  "name": "highlight_section",
  "arguments": {
    "section_id": null,
    "duration_ms": 500
  }
}
```

- `expand_section` accepts `action` values `expand`, `collapse`, or `toggle` (default `toggle`).
- `change_view_mode` accepts `normal`, `compact`, or `expanded`.
- `highlight_section` takes an optional `section_id`; pass `null` to clear the highlight, and optionally provide `duration_ms` for temporary highlights.
