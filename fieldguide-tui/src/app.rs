use std::collections::HashSet;
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

#[derive(Debug, Clone)]
pub struct HighlightState {
    pub section_id: Option<String>,
    pub expires_at: Option<Instant>,
}

#[derive(Debug, Clone)]
pub struct App {
    pub guide: FieldGuide,
    pub expanded: HashSet<String>,
    pub focused_index: usize,
    pub view_mode: ViewMode,
    pub highlight: Option<HighlightState>,
}

impl App {
    pub fn new(guide: FieldGuide) -> Self {
        let expanded = guide
            .sections
            .get(0)
            .map(|section| HashSet::from([section.id.clone()]))
            .unwrap_or_default();
        Self {
            guide,
            expanded,
            focused_index: 0,
            view_mode: ViewMode::Normal,
            highlight: None,
        }
    }

    pub fn toggle_section(&mut self, section_id: &str, action: &str) {
        let should_expand = match action {
            "expand" => true,
            "collapse" => false,
            "toggle" => !self.expanded.contains(section_id),
            _ => return,
        };

        if should_expand {
            self.expanded.insert(section_id.to_string());
        } else {
            self.expanded.remove(section_id);
        }
    }

    pub fn set_view(&mut self, mode: &str) {
        self.view_mode = match mode {
            "normal" => ViewMode::Normal,
            "compact" => ViewMode::Compact,
            "expanded" => ViewMode::Expanded,
            _ => self.view_mode,
        };
    }

    pub fn cycle_focus(&mut self, delta: isize) {
        if self.guide.sections.is_empty() {
            return;
        }
        let len = self.guide.sections.len() as isize;
        let new_index = (self.focused_index as isize + delta).rem_euclid(len);
        self.focused_index = new_index as usize;
    }

    pub fn focused_section_id(&self) -> Option<&str> {
        self.guide
            .sections
            .get(self.focused_index)
            .map(|section| section.id.as_str())
    }

    pub fn highlight(&mut self, section_id: Option<String>, duration_ms: Option<u64>) {
        if section_id.is_none() && duration_ms.is_none() {
            self.highlight = None;
            return;
        }
        let resolved_id = section_id.or_else(|| {
            self.guide
                .sections
                .get(self.focused_index)
                .map(|s| s.id.clone())
        });
        if resolved_id.is_none() {
            self.highlight = None;
            return;
        }
        let expires_at = duration_ms.map(|ms| Instant::now() + Duration::from_millis(ms));
        self.highlight = Some(HighlightState {
            section_id: resolved_id,
            expires_at,
        });
    }

    pub fn clear_expired_highlight(&mut self) {
        if let Some(highlight) = &self.highlight {
            if let Some(expires_at) = highlight.expires_at {
                if Instant::now() >= expires_at {
                    self.highlight = None;
                }
            }
        }
    }
}

pub fn apply(app: &mut App, cmd: UiCmd) {
    match cmd {
        UiCmd::ExpandSection { section_id, action } => app.toggle_section(&section_id, &action),
        UiCmd::ChangeViewMode { mode } => app.set_view(&mode),
        UiCmd::HighlightSection {
            section_id,
            duration_ms,
        } => app.highlight(section_id, duration_ms),
    }
}
