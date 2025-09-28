# fieldguide-tui

A Ratatui + Crossterm terminal application that renders the Pattern Dispatch Field Guide and exposes Model Context Protocol (MCP) controls over stdio. The crate ships with a Tokio runtime, configurable render cadence, dirty-flag based redraws, and persistence for the last focused section and view mode.

## Features

- Ratatui UI with header/body/footer layout and highlight overlays
- View modes (`normal`, `compact`, `expanded`) toggled via keyboard or MCP tool
- Dirty flag rendering to avoid redundant redraws during idle periods
- MCP stdio server (rmcp) exposing expand, view, and highlight tools
- Configurable tick interval, theme placeholder, and keybinding overrides via TOML
- Last used view mode and focused section persisted in `$HOME/.local/state/floatctl/fieldguide-tui/state.json`
- Structured status line with MCP connection state and recent events
- Logging via `env_logger` (set `RUST_LOG=fieldguide_tui=debug` for verbose output)

## Keybindings

| Key | Action |
| --- | ------ |
| `Space` / `Enter` | Toggle the focused section |
| `e` | Cycle view mode |
| `h` | Highlight the focused section for 1.5s |
| `j` / `Down` | Move focus down |
| `k` / `Up` | Move focus up |
| `q` | Quit |

## Configuration

Optional config is loaded from `~/.config/floatctl/fieldguide-tui.toml`. Example:

```toml
# ~/.config/floatctl/fieldguide-tui.toml
tick_interval_ms = 200
initial_view_mode = "compact"

[keybindings]
cycle_view = "e"

[theme]
# Future expansion for theme handling
```

Persisted UI state is written on clean exit to `~/.local/state/floatctl/fieldguide-tui/state.json`.

## MCP Tools

The stdio server exposes the following tools:

1. `expand_section(section_id, action="expand"|"collapse"|"toggle")`
2. `change_view_mode(mode="normal"|"compact"|"expanded")`
3. `highlight_section(section_id=null, duration_ms?)`

Invalid parameters surface structured errors back to the caller and surface a status line update in the UI.

## Testing

```bash
# from the crate directory (crates/fieldguide-tui)
cargo fmt --all
cargo clippy --all-targets -- -D warnings
cargo test

# or from the repo root using explicit manifests
cargo fmt --manifest-path crates/fieldguide-tui/Cargo.toml
cargo clippy --manifest-path crates/fieldguide-tui/Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path crates/fieldguide-tui/Cargo.toml
```

Render tests use Ratatui's `TestBackend` to ensure layouts remain stable, and integration tests validate MCP control sinks.
