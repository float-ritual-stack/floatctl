mod app;
mod mcp;
mod model;
mod ui;

use std::io::stdout;
use std::time::{Duration, Instant};

use anyhow::Result;
use app::{apply, App, UiCmd};
use crossbeam_channel::unbounded;
use crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind};
use crossterm::execute;
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
};
use ratatui::backend::CrosstermBackend;
use ratatui::Terminal;
use tokio::task::JoinHandle;

struct TerminalGuard;

impl TerminalGuard {
    fn enter() -> Result<Self> {
        // Raw mode and alternate screen handling per Crossterm docs: https://docs.rs/crossterm/latest/crossterm/terminal/
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
    let (tx, rx) = unbounded();
    let mcp_tx = tx.clone();
    let mcp_handle: JoinHandle<()> = tokio::spawn(async move {
        if let Err(err) = mcp::run_mcp(mcp_tx).await {
            eprintln!("MCP server error: {err:?}");
        }
    });

    let _guard = TerminalGuard::enter()?;
    let backend = CrosstermBackend::new(stdout());
    let mut terminal = Terminal::new(backend)?;
    terminal.clear()?;

    let mut last_tick = Instant::now();
    let tick_rate = Duration::from_millis(100);
    let highlight_duration = Duration::from_millis(800);

    loop {
        drain_commands(&rx, &mut app);
        terminal.draw(|frame| ui::draw(frame, &app))?;

        if app.should_quit() {
            break;
        }

        let now = Instant::now();
        app.update_highlight(now);

        let timeout = tick_rate
            .checked_sub(last_tick.elapsed())
            .unwrap_or_else(|| Duration::from_millis(0));

        if event::poll(timeout)? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    handle_key(key, &mut app, highlight_duration);
                }
            }
        }

        if last_tick.elapsed() >= tick_rate {
            last_tick = Instant::now();
        }
    }

    terminal.show_cursor()?;
    mcp_handle.abort();
    let _ = mcp_handle.await;
    Ok(())
}

fn drain_commands(rx: &crossbeam_channel::Receiver<UiCmd>, app: &mut App) {
    while let Ok(cmd) = rx.try_recv() {
        apply(app, cmd);
    }
}

fn handle_key(event: KeyEvent, app: &mut App, highlight_duration: Duration) {
    match event.code {
        KeyCode::Char('q') => app.mark_quit(),
        KeyCode::Char('e') => app.cycle_view(),
        KeyCode::Char('h') => {
            if let Some(id) = app.focused_section_id().map(|s| s.to_string()) {
                app.highlight(Some(id), Some(highlight_duration));
            }
        }
        KeyCode::Enter | KeyCode::Char(' ') => app.toggle_focused(),
        KeyCode::Down | KeyCode::Char('j') => app.focus_next(),
        KeyCode::Up | KeyCode::Char('k') => app.focus_prev(),
        _ => {}
    }
}
