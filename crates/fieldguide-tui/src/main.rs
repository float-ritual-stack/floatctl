use std::io;
use std::time::{Duration, Instant};

use anyhow::Result;
use crossbeam_channel::{unbounded, Receiver};
use crossterm::event::{self, Event, KeyCode, KeyEventKind};
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
};
use crossterm::{execute, ExecutableCommand};
use log::{info, warn};
use ratatui::backend::CrosstermBackend;
use ratatui::Terminal;

use fieldguide_tui::app::dirty::Dirty;
use fieldguide_tui::app::{AppState, ExpandAction, StatusMessage, UiCmd};
use fieldguide_tui::config::Config;
use fieldguide_tui::mcp::server::run_mcp;
use fieldguide_tui::model::FieldGuide;
use fieldguide_tui::state_persist::{
    load_last_run, restore_focus, restore_view_mode, save_last_run, LastRunState,
};
use fieldguide_tui::ui;

struct TerminalGuard;

impl TerminalGuard {
    fn enter() -> Result<Self> {
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        stdout.execute(EnterAlternateScreen)?;
        Ok(Self)
    }
}

impl Drop for TerminalGuard {
    fn drop(&mut self) {
        if let Err(err) = disable_raw_mode() {
            warn!("failed to disable raw mode: {err}");
        }
        if let Err(err) = execute!(io::stdout(), LeaveAlternateScreen) {
            warn!("failed to leave alternate screen: {err}");
        }
    }
}

fn handle_key(app: &mut AppState, key: KeyCode) {
    match key {
        KeyCode::Char('q') => {
            app.set_status_message(StatusMessage::info("Exiting"));
        }
        KeyCode::Char('e') | KeyCode::Char('E') => {
            let next = app.view_mode().cycle();
            if let Err(err) = app.apply(UiCmd::ChangeViewMode { mode: next }) {
                app.set_status_message(StatusMessage::error(err.to_string()));
            }
        }
        KeyCode::Char('h') | KeyCode::Char('H') => {
            if let Err(err) = app.apply(UiCmd::HighlightSection {
                section_id: None,
                duration_ms: Some(1_500),
            }) {
                app.set_status_message(StatusMessage::error(err.to_string()));
            }
        }
        KeyCode::Enter | KeyCode::Char(' ') => {
            if let Some(section) = app.focused_section() {
                if let Err(err) = app.apply(UiCmd::ExpandSection {
                    section_id: section.id.clone(),
                    action: ExpandAction::Toggle,
                }) {
                    app.set_status_message(StatusMessage::error(err.to_string()));
                }
            }
        }
        KeyCode::Down | KeyCode::Char('j') => app.cycle_focus(1),
        KeyCode::Up | KeyCode::Char('k') => app.cycle_focus(-1),
        _ => {}
    }
}

fn drain_channel(rx: &Receiver<UiCmd>, app: &mut AppState) {
    while let Ok(cmd) = rx.try_recv() {
        if let Err(err) = app.apply(cmd) {
            warn!("ui command failed: {err}");
            app.set_status_message(StatusMessage::warn(err.to_string()));
        }
    }
}

fn persist_state(app: &AppState) {
    let state = LastRunState::from_app(app);
    if let Err(err) = save_last_run(&state) {
        warn!("failed to persist last run state: {err}");
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();
    info!("starting fieldguide-tui");
    let config = match Config::load() {
        Ok(config) => config,
        Err(err) => {
            warn!("failed to load config: {err}; using defaults");
            Config::default()
        }
    };
    let last_state = match load_last_run() {
        Ok(state) => state,
        Err(err) => {
            warn!("failed to load persisted state: {err}");
            None
        }
    };
    let guide = FieldGuide::sample();
    let initial_view = restore_view_mode(last_state.as_ref(), config.resolved_view_mode());
    let focus = restore_focus(last_state.as_ref());
    let tick_interval = Duration::from_millis(config.tick_interval_ms.max(60));
    let mut app = AppState::new(guide, initial_view, focus, tick_interval);
    let (tx, rx) = unbounded::<UiCmd>();
    let mcp_handle = tokio::spawn(run_mcp(tx.clone()));
    let _guard = TerminalGuard::enter()?;
    let mut terminal = Terminal::new(CrosstermBackend::new(io::stdout()))?;
    terminal.clear()?;
    loop {
        drain_channel(&rx, &mut app);
        if app.dirty() != Dirty::NONE {
            terminal.draw(|frame| ui::draw(frame, &app))?;
            app.take_dirty();
        }
        app.clear_status_if_older_than(Duration::from_secs(5));
        let poll_timeout = app.tick_interval();
        if event::poll(poll_timeout)? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    let should_exit = matches!(key.code, KeyCode::Char('q'));
                    handle_key(&mut app, key.code);
                    if should_exit {
                        break;
                    }
                }
            }
        }
        app.mark_tick(Instant::now());
        if mcp_handle.is_finished() && app.mcp_connected() {
            let _ = app.apply(UiCmd::McpConnected(false));
        }
    }
    persist_state(&app);
    drop(terminal);
    drop(_guard);
    if !mcp_handle.is_finished() {
        mcp_handle.abort();
    }
    match mcp_handle.await {
        Ok(Ok(())) => {}
        Ok(Err(err)) => warn!("mcp server exited with error: {err}"),
        Err(join_err) => warn!("mcp task join error: {join_err}"),
    }
    Ok(())
}
