use std::collections::HashSet;
use std::fmt;
use std::time::{Duration, Instant};

use crate::model::FieldGuide;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ViewMode {
    Normal,
    Compact,
    Expanded,
}

impl ViewMode {
    pub fn cycle(self) -> Self {
        match self {
            ViewMode::Normal => ViewMode::Compact,
            ViewMode::Compact => ViewMode::Expanded,
            ViewMode::Expanded => ViewMode::Normal,
        }
    }
}

impl fmt::Display for ViewMode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ViewMode::Normal => write!(f, "Normal"),
            ViewMode::Compact => write!(f, "Compact"),
            ViewMode::Expanded => write!(f, "Expanded"),
        }
    }
}

impl TryFrom<&str> for ViewMode {
    type Error = ();

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        match value.to_lowercase().as_str() {
            "normal" => Ok(ViewMode::Normal),
            "compact" => Ok(ViewMode::Compact),
            "expanded" => Ok(ViewMode::Expanded),
            _ => Err(()),
        }
    }
}

#[derive(Debug, Clone)]
pub enum UiCmd {
    ExpandSection {
        section_id: String,
        action: String,
    },
    ChangeViewMode {
        mode: String,
    },
    HighlightSection {
        section_id: Option<String>,
        duration_ms: Option<u64>,
    },
}

#[derive(Debug, Clone, Copy)]
pub enum SectionAction {
    Expand,
    Collapse,
    Toggle,
}

impl TryFrom<&str> for SectionAction {
    type Error = ();

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        match value.to_lowercase().as_str() {
            "expand" => Ok(SectionAction::Expand),
            "collapse" => Ok(SectionAction::Collapse),
            "toggle" => Ok(SectionAction::Toggle),
            _ => Err(()),
        }
    }
}

#[derive(Debug, Clone)]
struct HighlightState {
    section_id: Option<String>,
    expires_at: Option<Instant>,
}

impl HighlightState {
    fn new(section_id: Option<String>, expires_at: Option<Instant>) -> Self {
        Self {
            section_id,
            expires_at,
        }
    }

    fn is_active_for(&self, section_id: &str, now: Instant) -> bool {
        if let Some(expiry) = self.expires_at {
            if expiry < now {
                return false;
            }
        }
        match &self.section_id {
            Some(target) => target == section_id,
            None => true,
        }
    }

    fn is_expired(&self, now: Instant) -> bool {
        matches!(self.expires_at, Some(exp) if exp < now)
    }
}

#[derive(Debug)]
pub struct App {
    guide: FieldGuide,
    view_mode: ViewMode,
    expanded: HashSet<String>,
    focus_index: usize,
    highlight: Option<HighlightState>,
    should_quit: bool,
}

impl App {
    pub fn new(guide: FieldGuide) -> Self {
        Self {
            guide,
            view_mode: ViewMode::Normal,
            expanded: HashSet::new(),
            focus_index: 0,
            highlight: None,
            should_quit: false,
        }
    }

    pub fn guide(&self) -> &FieldGuide {
        &self.guide
    }

    pub fn sections_len(&self) -> usize {
        self.guide.sections.len()
    }

    pub fn view_mode(&self) -> ViewMode {
        self.view_mode
    }

    pub fn is_expanded(&self, section_id: &str) -> bool {
        self.expanded.contains(section_id)
    }

    pub fn toggle_section(&mut self, section_id: &str, action: SectionAction) {
        if !self.has_section(section_id) {
            return;
        }

        match action {
            SectionAction::Expand => {
                self.expanded.insert(section_id.to_string());
            }
            SectionAction::Collapse => {
                self.expanded.remove(section_id);
            }
            SectionAction::Toggle => {
                if !self.expanded.insert(section_id.to_string()) {
                    self.expanded.remove(section_id);
                }
            }
        }
    }

    pub fn set_view(&mut self, mode: ViewMode) {
        self.view_mode = mode;
    }

    pub fn highlight(&mut self, section_id: Option<String>, duration: Option<Duration>) {
        if let Some(ref id) = section_id {
            if !self.has_section(id) {
                return;
            }
        }

        let expires_at = duration.map(|d| Instant::now() + d);
        self.highlight = Some(HighlightState::new(section_id, expires_at));
    }

    pub fn clear_highlight(&mut self) {
        self.highlight = None;
    }

    pub fn update_highlight(&mut self, now: Instant) {
        if matches!(self.highlight, Some(ref state) if state.is_expired(now)) {
            self.highlight = None;
        }
    }

    pub fn is_highlighted(&self, section_id: &str, now: Instant) -> bool {
        self.highlight
            .as_ref()
            .map(|state| state.is_active_for(section_id, now))
            .unwrap_or(false)
    }

    pub fn focus_index(&self) -> usize {
        self.focus_index
    }

    pub fn focused_section_id(&self) -> Option<&str> {
        self.guide
            .sections
            .get(self.focus_index)
            .map(|s| s.id.as_str())
    }

    pub fn focus_next(&mut self) {
        if self.sections_len() == 0 {
            return;
        }
        self.focus_index = (self.focus_index + 1) % self.sections_len();
    }

    pub fn focus_prev(&mut self) {
        if self.sections_len() == 0 {
            return;
        }
        if self.focus_index == 0 {
            self.focus_index = self.sections_len() - 1;
        } else {
            self.focus_index -= 1;
        }
    }

    pub fn toggle_focused(&mut self) {
        if let Some(id) = self.focused_section_id().map(|s| s.to_string()) {
            self.toggle_section(&id, SectionAction::Toggle);
        }
    }

    pub fn cycle_view(&mut self) {
        self.view_mode = self.view_mode.cycle();
    }

    pub fn mark_quit(&mut self) {
        self.should_quit = true;
    }

    pub fn should_quit(&self) -> bool {
        self.should_quit
    }

    fn has_section(&self, section_id: &str) -> bool {
        self.guide.sections.iter().any(|s| s.id == section_id)
    }
}

pub fn apply(app: &mut App, cmd: UiCmd) {
    match cmd {
        UiCmd::ExpandSection { section_id, action } => {
            if let Ok(section_action) = SectionAction::try_from(action.as_str()) {
                app.toggle_section(&section_id, section_action);
            }
        }
        UiCmd::ChangeViewMode { mode } => {
            if let Ok(view_mode) = ViewMode::try_from(mode.as_str()) {
                app.set_view(view_mode);
            }
        }
        UiCmd::HighlightSection {
            section_id,
            duration_ms,
        } => {
            if section_id.is_none() {
                app.clear_highlight();
            } else {
                let duration = duration_ms.map(Duration::from_millis);
                app.highlight(section_id, duration);
            }
        }
    }
}
