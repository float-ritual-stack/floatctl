mod app;
mod mcp;
mod model;
mod ui;

use std::io::stdout;
use std::time::Duration;

use anyhow::Result;
use app::{apply, App, UiCmd};
use crossbeam_channel::unbounded;
use crossterm::event::{self, Event, KeyCode, KeyEventKind};
use crossterm::execute;
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
};
use ratatui::backend::CrosstermBackend;
use ratatui::Terminal;

struct TerminalGuard;

impl TerminalGuard {
    fn new() -> Result<Self> {
        enable_raw_mode()?;
        execute!(stdout(), EnterAlternateScreen)?;
        Ok(Self)
    }
}

impl Drop for TerminalGuard {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let _ = execute!(stdout(), LeaveAlternateScreen);
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let guide = model::FieldGuide::sample();
    let mut app = App::new(guide);
    let (tx, rx) = unbounded::<UiCmd>();

    let mcp_tx = tx.clone();
    let mcp_handle = tokio::spawn(async move {
        if let Err(err) = mcp::run_mcp(mcp_tx).await {
            eprintln!("MCP server error: {err:?}");
        }
    });

    let _guard = TerminalGuard::new()?;
    let mut terminal = Terminal::new(CrosstermBackend::new(stdout()))?;
    terminal.clear()?;

    let mut should_exit = false;
    while !should_exit {
        while let Ok(cmd) = rx.try_recv() {
            apply(&mut app, cmd);
        }
        app.clear_expired_highlight();
        terminal.draw(|frame| ui::draw(frame, &app))?;

        if event::poll(Duration::from_millis(50))? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    match key.code {
                        KeyCode::Char('q') => should_exit = true,
                        KeyCode::Char('e') => {
                            app.view_mode = app.view_mode.cycle();
                        }
                        KeyCode::Char('h') => {
                            app.highlight(None, Some(800));
                        }
                        KeyCode::Char(' ') | KeyCode::Enter => {
                            if let Some(id) = app.focused_section_id().map(|s| s.to_string()) {
                                app.toggle_section(&id, "toggle");
                            }
                        }
                        KeyCode::Down | KeyCode::Char('j') => {
                            app.cycle_focus(1);
                        }
                        KeyCode::Up | KeyCode::Char('k') => {
                            app.cycle_focus(-1);
                        }
                        _ => {}
                    }
                }
            }
        }
    }

    drop(terminal);
    drop(_guard);

    mcp_handle.abort();
    let _ = mcp_handle.await;

    Ok(())
}
