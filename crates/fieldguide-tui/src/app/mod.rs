use std::borrow::Cow;
use std::collections::HashSet;
use std::time::{Duration, Instant};

use crate::error::UiError;
use crate::model::{FieldGuide, Section};

pub mod dirty;
#[cfg(test)]
mod tests;

use dirty::Dirty;

#[derive(Clone, Copy, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ViewMode {
    Normal,
    Compact,
    Expanded,
}

impl ViewMode {
    #[must_use]
    pub fn cycle(self) -> Self {
        match self {
            ViewMode::Normal => ViewMode::Compact,
            ViewMode::Compact => ViewMode::Expanded,
            ViewMode::Expanded => ViewMode::Normal,
        }
    }

    #[must_use]
    pub fn as_str(self) -> &'static str {
        match self {
            ViewMode::Normal => "normal",
            ViewMode::Compact => "compact",
            ViewMode::Expanded => "expanded",
        }
    }

    pub fn try_from_str(value: &str) -> Result<Self, UiError> {
        match value {
            "normal" => Ok(ViewMode::Normal),
            "compact" => Ok(ViewMode::Compact),
            "expanded" => Ok(ViewMode::Expanded),
            other => Err(UiError::InvalidViewMode(other.to_string())),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ExpandAction {
    Expand,
    Collapse,
    Toggle,
}

impl ExpandAction {
    pub fn try_from_str(value: &str) -> Result<Self, UiError> {
        match value {
            "expand" => Ok(Self::Expand),
            "collapse" => Ok(Self::Collapse),
            "toggle" => Ok(Self::Toggle),
            other => Err(UiError::InvalidExpandAction(other.to_string())),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum StatusKind {
    Info,
    Warn,
    Error,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StatusMessage {
    pub kind: StatusKind,
    pub text: String,
    pub timestamp: Instant,
}

impl StatusMessage {
    pub fn info<T: Into<String>>(text: T) -> Self {
        Self {
            kind: StatusKind::Info,
            text: text.into(),
            timestamp: Instant::now(),
        }
    }

    pub fn warn<T: Into<String>>(text: T) -> Self {
        Self {
            kind: StatusKind::Warn,
            text: text.into(),
            timestamp: Instant::now(),
        }
    }

    pub fn error<T: Into<String>>(text: T) -> Self {
        Self {
            kind: StatusKind::Error,
            text: text.into(),
            timestamp: Instant::now(),
        }
    }
}

#[derive(Clone, Debug, Default)]
pub(crate) struct EntryCache {
    pub pattern: String,
    pub description: String,
    pub signals: Vec<String>,
    pub protocol: String,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct SectionCache {
    pub header: String,
    pub entries: Vec<EntryCache>,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct RenderCache {
    pub sections: Vec<SectionCache>,
}

impl RenderCache {
    fn rebuild(&mut self, guide: &FieldGuide) {
        self.sections.clear();
        self.sections.reserve(guide.sections.len());
        for section in &guide.sections {
            let icon = match section.icon.as_str() {
                "circle" => "●",
                "square" => "■",
                other => other,
            };
            let header = format!("{} {}", icon, section.title);
            let entries = section
                .entries
                .iter()
                .map(|entry| EntryCache {
                    pattern: entry.pattern.clone(),
                    description: entry.description.clone(),
                    signals: entry.signals.clone(),
                    protocol: entry.protocol.clone(),
                })
                .collect();
            self.sections.push(SectionCache { header, entries });
        }
    }

    pub(crate) fn section(&self, index: usize) -> Option<&SectionCache> {
        self.sections.get(index)
    }
}

#[derive(Clone, Debug)]
pub struct HighlightState {
    pub section_id: String,
    pub expires_at: Option<Instant>,
}

#[derive(Clone, Debug)]
pub enum UiCmd {
    ExpandSection {
        section_id: String,
        action: ExpandAction,
    },
    ChangeViewMode {
        mode: ViewMode,
    },
    HighlightSection {
        section_id: Option<String>,
        duration_ms: Option<u64>,
    },
    SetStatus(StatusMessage),
    McpConnected(bool),
}

#[derive(Clone, Debug)]
pub struct AppState {
    guide: FieldGuide,
    expanded: HashSet<String>,
    focused_index: usize,
    view_mode: ViewMode,
    highlight: Option<HighlightState>,
    status: Option<StatusMessage>,
    dirty: Dirty,
    cache: RenderCache,
    tick_interval: Duration,
    highlight_duration: Option<Duration>,
    last_tick: Instant,
    mcp_connected: bool,
}

impl AppState {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        guide: FieldGuide,
        initial_view: ViewMode,
        focused_section: Option<&str>,
        tick_interval: Duration,
    ) -> Self {
        let mut cache = RenderCache::default();
        cache.rebuild(&guide);
        let mut expanded = HashSet::new();
        if let Some(first) = guide.sections.first() {
            expanded.insert(first.id.clone());
        }
        let focused_index = focused_section
            .and_then(|id| guide.sections.iter().position(|section| section.id == id))
            .unwrap_or(0);
        Self {
            guide,
            expanded,
            focused_index,
            view_mode: initial_view,
            highlight: None,
            status: None,
            dirty: Dirty::ALL,
            cache,
            tick_interval,
            highlight_duration: None,
            last_tick: Instant::now(),
            mcp_connected: true,
        }
    }

    pub fn has_section(&self, section_id: &str) -> bool {
        self.guide
            .sections
            .iter()
            .any(|section| section.id == section_id)
    }

    pub fn guide(&self) -> &FieldGuide {
        &self.guide
    }

    pub(crate) fn cache(&self) -> &RenderCache {
        &self.cache
    }

    pub fn view_mode(&self) -> ViewMode {
        self.view_mode
    }

    pub fn focused_section(&self) -> Option<&Section> {
        self.guide.sections.get(self.focused_index)
    }

    pub fn focused_index(&self) -> usize {
        self.focused_index
    }

    pub fn is_expanded(&self, section_id: &str) -> bool {
        self.expanded.contains(section_id)
    }

    pub fn dirty(&self) -> Dirty {
        self.dirty
    }

    pub fn take_dirty(&mut self) -> Dirty {
        let dirty = self.dirty;
        self.dirty = Dirty::NONE;
        dirty
    }

    pub fn tick_interval(&self) -> Duration {
        self.tick_interval
    }

    pub fn highlight(&self) -> Option<&HighlightState> {
        self.highlight.as_ref()
    }

    pub fn status(&self) -> Option<&StatusMessage> {
        self.status.as_ref()
    }

    pub fn mcp_connected(&self) -> bool {
        self.mcp_connected
    }

    pub fn set_tick_interval(&mut self, interval: Duration) {
        if self.tick_interval != interval {
            self.tick_interval = interval;
            self.dirty |= Dirty::STATUS;
        }
    }

    pub fn apply(&mut self, cmd: UiCmd) -> Result<(), UiError> {
        match cmd {
            UiCmd::ExpandSection { section_id, action } => {
                self.toggle_section(&section_id, action)?;
            }
            UiCmd::ChangeViewMode { mode } => {
                self.set_view(mode);
            }
            UiCmd::HighlightSection {
                section_id,
                duration_ms,
            } => {
                self.highlight_section(section_id.as_deref(), duration_ms)?;
            }
            UiCmd::SetStatus(status) => {
                self.status = Some(status);
                self.dirty |= Dirty::STATUS;
            }
            UiCmd::McpConnected(flag) => {
                if self.mcp_connected != flag {
                    self.mcp_connected = flag;
                    let message = if flag {
                        StatusMessage::info("MCP reconnected")
                    } else {
                        StatusMessage::warn("MCP disconnected")
                    };
                    self.status = Some(message);
                    self.dirty |= Dirty::STATUS;
                }
            }
        }
        Ok(())
    }

    pub fn cycle_focus(&mut self, delta: isize) {
        if self.guide.sections.is_empty() {
            return;
        }
        let len = self.guide.sections.len() as isize;
        let new_index = (self.focused_index as isize + delta).rem_euclid(len);
        if self.focused_index != new_index as usize {
            self.focused_index = new_index as usize;
            self.dirty |= Dirty::LAYOUT | Dirty::HIGHLIGHT;
        }
    }

    pub fn focus_by_id(&mut self, section_id: &str) -> Result<(), UiError> {
        if let Some(index) = self
            .guide
            .sections
            .iter()
            .position(|section| section.id == section_id)
        {
            if self.focused_index != index {
                self.focused_index = index;
                self.dirty |= Dirty::LAYOUT | Dirty::HIGHLIGHT;
            }
            Ok(())
        } else {
            Err(UiError::UnknownSection(section_id.to_string()))
        }
    }

    pub fn clear_status_if_older_than(&mut self, limit: Duration) {
        if let Some(status) = &self.status {
            if status.timestamp.elapsed() > limit {
                self.status = None;
                self.dirty |= Dirty::STATUS;
            }
        }
    }

    fn toggle_section(&mut self, section_id: &str, action: ExpandAction) -> Result<(), UiError> {
        if !self.has_section(section_id) {
            return Err(UiError::UnknownSection(section_id.to_string()));
        }
        let should_expand = match action {
            ExpandAction::Expand => true,
            ExpandAction::Collapse => false,
            ExpandAction::Toggle => !self.expanded.contains(section_id),
        };
        let changed = if should_expand {
            self.expanded.insert(section_id.to_string())
        } else {
            self.expanded.remove(section_id)
        };
        if changed {
            self.dirty |= Dirty::LAYOUT | Dirty::DATA;
        }
        Ok(())
    }

    fn set_view(&mut self, mode: ViewMode) {
        if self.view_mode != mode {
            self.view_mode = mode;
            self.dirty |= Dirty::LAYOUT | Dirty::DATA | Dirty::STATUS;
        }
    }

    fn highlight_section(
        &mut self,
        section_id: Option<&str>,
        duration_ms: Option<u64>,
    ) -> Result<(), UiError> {
        let resolved_id = section_id.map(Cow::Borrowed).or_else(|| {
            self.focused_section()
                .map(|section| Cow::Borrowed(section.id.as_str()))
        });
        let Some(section_id) = resolved_id else {
            self.highlight = None;
            self.highlight_duration = None;
            self.dirty |= Dirty::HIGHLIGHT;
            return Ok(());
        };
        if !self.has_section(&section_id) {
            return Err(UiError::UnknownSection(section_id.into_owned()));
        }
        let expires_at = duration_ms
            .map(|ms| {
                if ms == 0 {
                    return Err(UiError::InvalidDuration(ms));
                }
                Ok(Instant::now() + Duration::from_millis(ms))
            })
            .transpose()?;
        self.highlight = Some(HighlightState {
            section_id: section_id.into_owned(),
            expires_at,
        });
        self.highlight_duration = duration_ms.map(Duration::from_millis);
        self.dirty |= Dirty::HIGHLIGHT | Dirty::STATUS;
        Ok(())
    }

    pub fn clear_expired_highlight(&mut self, now: Instant) {
        if let Some(highlight) = &self.highlight {
            if let Some(expiry) = highlight.expires_at {
                if now >= expiry {
                    self.highlight = None;
                    self.highlight_duration = None;
                    self.dirty |= Dirty::HIGHLIGHT;
                }
            }
        }
    }

    pub fn mark_tick(&mut self, now: Instant) {
        if now.duration_since(self.last_tick) >= self.tick_interval {
            self.last_tick = now;
            self.clear_expired_highlight(now);
        }
    }

    pub fn set_status_message(&mut self, status: StatusMessage) {
        self.status = Some(status);
        self.dirty |= Dirty::STATUS;
    }
}
