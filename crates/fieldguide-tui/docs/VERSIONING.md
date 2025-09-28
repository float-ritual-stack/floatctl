# Versioning Policy

- The crate is developed against stable Rust 1.78+ and CI should verify with `cargo fmt`, `cargo clippy -- -D warnings`, and `cargo test`.
- Dependency versions are pinned to explicit patch releases to guarantee repeatable builds; upgrades must be accompanied by lockfile updates and validation notes in this document.
- Minor releases increment when MCP tool signatures or UI configuration compatibility changes; patch releases cover bug fixes, perf, or documentation tweaks.
- Breaking MCP tool signature changes require explicit mention in `docs/CHANGELOG.md` and coordination with downstream automation.
- Compatibility is maintained with Ratatui 0.28.x and Crossterm 0.28.x per upstream guidance.
