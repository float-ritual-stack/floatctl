mod self_check;
mod ui;

use std::fs;
use std::io::{self, Stdout};
use std::path::PathBuf;
use std::time::{Duration, Instant};

use anyhow::{Context, Result};
use bbs_core::model::{
    DataModel, LayoutMode, Project, ProjectStatus, Tab, ViewData, ViewId, ViewState,
};
use bbs_core::seed::seed_model;
use clap::{ArgAction, Parser};
use crossterm::event::{self, Event, KeyCode, KeyEventKind, KeyModifiers};
use crossterm::terminal::{disable_raw_mode, enable_raw_mode};
use crossterm::{execute, terminal};
use ratatui::backend::CrosstermBackend;
use ratatui::Terminal;
use tracing::{error, info};

#[derive(Parser, Debug)]
#[command(
    author,
    version,
    about = "SysOp BBS terminal UI",
    propagate_version = true
)]
struct Cli {
    /// Path to a JSON file containing a DataModel payload.
    #[arg(long)]
    data_path: Option<PathBuf>,

    /// Inline JSON payload (overrides path and env sources)
    #[arg(long)]
    data_inline: Option<String>,

    /// Run self-check verification and exit.
    #[arg(long, action = ArgAction::SetTrue)]
    check: bool,
}

fn load_model(cli: &Cli) -> Result<DataModel> {
    if let Some(inline) = &cli.data_inline {
        return parse_payload(inline);
    }

    if let Some(path) = &cli.data_path {
        let body = fs::read_to_string(path)
            .with_context(|| format!("failed to read data file: {}", path.display()))?;
        return parse_payload(&body);
    }

    if let Ok(env_payload) = std::env::var("SYSOP_BBS_DATA") {
        return parse_payload(&env_payload);
    }

    Ok(seed_model())
}

fn parse_payload(payload: &str) -> Result<DataModel> {
    serde_json::from_str(payload).context("failed to parse DataModel JSON")
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .try_init()
        .ok();

    let cli = Cli::parse();
    let model = load_model(&cli)?;
    model.validate()?;

    if cli.check {
        return self_check::run_checks(&model);
    }

    let mut app = AppState::new(model);
    run_terminal(&mut app)
}

fn run_terminal(app: &mut AppState) -> Result<()> {
    enable_raw_mode().context("failed to enable raw mode")?;
    let mut stdout = io::stdout();
    execute!(
        stdout,
        terminal::EnterAlternateScreen,
        crossterm::event::EnableMouseCapture
    )
    .context("failed to enter alternate screen")?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend).context("failed to init terminal")?;
    terminal.clear()?;

    let res = event_loop(&mut terminal, app);

    disable_raw_mode().ok();
    if let Err(err) = execute!(
        terminal.backend_mut(),
        terminal::LeaveAlternateScreen,
        crossterm::event::DisableMouseCapture
    ) {
        error!(error = %err, "failed to restore terminal state");
    }
    terminal.show_cursor().ok();

    res
}

fn event_loop(terminal: &mut Terminal<CrosstermBackend<Stdout>>, app: &mut AppState) -> Result<()> {
    let tick_rate = Duration::from_millis(200);
    let mut last_tick = Instant::now();

    loop {
        terminal
            .draw(|frame| ui::render(frame, app))
            .context("render failure")?;

        let timeout = tick_rate
            .checked_sub(last_tick.elapsed())
            .unwrap_or_else(|| Duration::from_secs(0));

        if event::poll(timeout).context("event poll failed")? {
            match event::read()? {
                Event::Key(event) if event.kind != KeyEventKind::Release => {
                    if handle_key_event(app, event)? {
                        break;
                    }
                }
                Event::Resize(width, height) => {
                    app.on_resize(width, height);
                }
                _ => {}
            }
        }

        if last_tick.elapsed() >= tick_rate {
            app.on_tick();
            last_tick = Instant::now();
        }
    }

    Ok(())
}

fn handle_key_event(app: &mut AppState, event: crossterm::event::KeyEvent) -> Result<bool> {
    if event.modifiers.contains(KeyModifiers::CONTROL) {
        if matches!(event.code, KeyCode::Char('c')) {
            return Ok(true);
        }
    }

    match event.code {
        KeyCode::Esc => {
            if app.escape_modal() {
                return Ok(false);
            }
            return Ok(true);
        }
        KeyCode::Char('q') => return Ok(true),
        KeyCode::Tab => app.next_tab(),
        KeyCode::BackTab => app.previous_tab(),
        KeyCode::Char('?') => app.toggle_overlay(),
        KeyCode::Char('g') => app.toggle_layout(),
        KeyCode::Char('/') => app.begin_search(),
        KeyCode::Enter => app.log_enter(),
        KeyCode::Char(ch) => {
            if app.handle_character(ch) {
                return Ok(false);
            }
        }
        KeyCode::Backspace => app.handle_backspace(),
        KeyCode::Left => app.move_selection(-1),
        KeyCode::Right => app.move_selection(1),
        KeyCode::Up => app.move_selection(-1),
        KeyCode::Down => app.move_selection(1),
        _ => {}
    }

    Ok(false)
}

pub struct AppState {
    model: DataModel,
    tab_index: usize,
    overlay_visible: bool,
    size: (u16, u16),
    layout_mode: LayoutMode,
    project_search: String,
    search_active: bool,
    project_selection: usize,
}

impl AppState {
    pub fn data(&self) -> &DataModel {
        &self.model
    }

    pub fn tabs(&self) -> &[Tab] {
        &self.model.tabs
    }

    pub fn tab_index(&self) -> usize {
        self.tab_index
    }

    pub fn overlay_visible(&self) -> bool {
        self.overlay_visible
    }

    fn new(model: DataModel) -> Self {
        let tab_index = model
            .tabs
            .iter()
            .position(|tab| tab.id == model.active_view)
            .unwrap_or(0);
        let layout_mode = model
            .view(ViewId::ProjectsGrid)
            .and_then(|state| match &state.kind {
                ViewData::ProjectsGrid { default_layout, .. } => Some(*default_layout),
                _ => None,
            })
            .unwrap_or(LayoutMode::Grid);
        Self {
            model,
            tab_index,
            overlay_visible: false,
            size: (0, 0),
            layout_mode,
            project_search: String::new(),
            search_active: false,
            project_selection: 0,
        }
    }

    fn on_tick(&mut self) {}

    fn on_resize(&mut self, width: u16, height: u16) {
        self.size = (width, height);
    }

    pub fn current_view(&self) -> &ViewState {
        let id = self.model.tabs[self.tab_index].id;
        self.model
            .view(id)
            .unwrap_or_else(|| self.model.view(ViewId::Unknown).expect("unknown view"))
    }

    fn next_tab(&mut self) {
        self.tab_index = (self.tab_index + 1) % self.model.tabs.len();
        self.update_active_view();
    }

    fn previous_tab(&mut self) {
        if self.tab_index == 0 {
            self.tab_index = self.model.tabs.len() - 1;
        } else {
            self.tab_index -= 1;
        }
        self.update_active_view();
    }

    fn update_active_view(&mut self) {
        let tab = &self.model.tabs[self.tab_index];
        self.model.active_view = tab.id;
        if tab.id == ViewId::ProjectsGrid {
            if let ViewData::ProjectsGrid { default_layout, .. } = &self.current_view().kind {
                self.layout_mode = *default_layout;
            }
        } else {
            self.search_active = false;
        }
    }

    fn toggle_overlay(&mut self) {
        self.overlay_visible = !self.overlay_visible;
    }

    fn toggle_layout(&mut self) {
        if self.model.active_view != ViewId::ProjectsGrid {
            return;
        }
        self.layout_mode = match self.layout_mode {
            LayoutMode::Grid => LayoutMode::List,
            LayoutMode::List => LayoutMode::Grid,
        };
        self.clamp_project_selection();
    }

    fn begin_search(&mut self) {
        if self.model.active_view == ViewId::ProjectsGrid {
            self.search_active = true;
        }
    }

    fn handle_character(&mut self, ch: char) -> bool {
        if self.search_active {
            if !ch.is_control() {
                self.project_search.push(ch);
                self.clamp_project_selection();
            }
            return true;
        }
        false
    }

    fn handle_backspace(&mut self) {
        if self.search_active {
            self.project_search.pop();
            self.clamp_project_selection();
        }
    }

    fn escape_modal(&mut self) -> bool {
        if self.search_active {
            self.search_active = false;
            return true;
        }
        if self.overlay_visible {
            self.overlay_visible = false;
            return true;
        }
        false
    }

    fn log_enter(&mut self) {
        let view = self.current_view();
        match &view.kind {
            ViewData::ProjectsGrid { projects, .. } => {
                if let Some(project) = self.filtered_projects(projects).get(self.project_selection)
                {
                    info!("command" = %project_command(project), "link" = ?project.links, "enter" = "projects_grid");
                }
            }
            _ => {
                info!("enter" = ?view.id, "summary" = %view.summary);
            }
        }
    }

    pub fn layout_mode(&self) -> LayoutMode {
        self.layout_mode
    }

    pub fn project_search(&self) -> &str {
        &self.project_search
    }

    pub fn search_active(&self) -> bool {
        self.search_active
    }

    pub fn project_selection(&self) -> usize {
        self.project_selection
    }

    pub fn filtered_projects<'a>(&self, projects: &'a [Project]) -> Vec<&'a Project> {
        if self.project_search.is_empty() {
            projects.iter().collect()
        } else {
            let query = self.project_search.to_lowercase();
            projects
                .iter()
                .filter(|project| {
                    project.name.to_lowercase().contains(&query)
                        || project.description.to_lowercase().contains(&query)
                        || project
                            .tags
                            .iter()
                            .any(|tag| tag.to_lowercase().contains(&query))
                })
                .collect()
        }
    }

    fn move_selection(&mut self, delta: isize) {
        if self.model.active_view != ViewId::ProjectsGrid {
            return;
        }
        if let Some(projects) = self.current_view().projects() {
            let total = self.filtered_projects(projects).len();
            if total == 0 {
                self.project_selection = 0;
                return;
            }
            let mut index = self.project_selection as isize + delta;
            if index < 0 {
                index = 0;
            }
            if index as usize >= total {
                index = total.saturating_sub(1) as isize;
            }
            self.project_selection = index as usize;
        }
    }

    fn clamp_project_selection(&mut self) {
        if let Some(projects) = self.current_view().projects() {
            let total = self.filtered_projects(projects).len();
            if total == 0 {
                self.project_selection = 0;
            } else if self.project_selection >= total {
                self.project_selection = total - 1;
            }
        }
    }
}

fn project_command(project: &Project) -> String {
    let prefix = match project.status {
        ProjectStatus::Exploring => "explore",
        ProjectStatus::Active => "activate",
        ProjectStatus::Maintenance => "maintain",
        ProjectStatus::Archived => "archive",
    };
    format!(
        "floatctl projects {} --tag {}",
        prefix,
        project.name.replace(' ', "_")
    )
}
