use std::sync::{Arc, Mutex};

use anyhow::{anyhow, Result};
use crossbeam_channel::Sender;

use crate::app::{ExpandAction, UiCmd, ViewMode};

pub trait ControlSink: Send + Sync {
    fn expand_section(&self, section_id: &str, action: ExpandAction) -> Result<()>;
    fn change_view_mode(&self, mode: ViewMode) -> Result<()>;
    fn highlight_section(&self, section_id: Option<&str>, duration_ms: Option<u64>) -> Result<()>;
}

#[derive(Clone)]
pub struct ChannelControlSink {
    tx: Sender<UiCmd>,
}

impl ChannelControlSink {
    pub fn new(tx: Sender<UiCmd>) -> Self {
        Self { tx }
    }

    pub fn sender(&self) -> Sender<UiCmd> {
        self.tx.clone()
    }
}

impl ControlSink for ChannelControlSink {
    fn expand_section(&self, section_id: &str, action: ExpandAction) -> Result<()> {
        self.tx
            .send(UiCmd::ExpandSection {
                section_id: section_id.to_string(),
                action,
            })
            .map_err(|err| anyhow!("ui channel closed: {err}"))
    }

    fn change_view_mode(&self, mode: ViewMode) -> Result<()> {
        self.tx
            .send(UiCmd::ChangeViewMode { mode })
            .map_err(|err| anyhow!("ui channel closed: {err}"))
    }

    fn highlight_section(&self, section_id: Option<&str>, duration_ms: Option<u64>) -> Result<()> {
        self.tx
            .send(UiCmd::HighlightSection {
                section_id: section_id.map(ToString::to_string),
                duration_ms,
            })
            .map_err(|err| anyhow!("ui channel closed: {err}"))
    }
}

#[derive(Clone, Default)]
pub struct MockControlSink {
    commands: Arc<Mutex<Vec<UiCmd>>>,
}

impl MockControlSink {
    pub fn take(&self) -> Vec<UiCmd> {
        self.commands
            .lock()
            .map(|mut guard| guard.drain(..).collect())
            .unwrap_or_default()
    }
}

impl ControlSink for MockControlSink {
    fn expand_section(&self, section_id: &str, action: ExpandAction) -> Result<()> {
        if let Ok(mut guard) = self.commands.lock() {
            guard.push(UiCmd::ExpandSection {
                section_id: section_id.to_string(),
                action,
            });
        }
        Ok(())
    }

    fn change_view_mode(&self, mode: ViewMode) -> Result<()> {
        if let Ok(mut guard) = self.commands.lock() {
            guard.push(UiCmd::ChangeViewMode { mode });
        }
        Ok(())
    }

    fn highlight_section(&self, section_id: Option<&str>, duration_ms: Option<u64>) -> Result<()> {
        if let Ok(mut guard) = self.commands.lock() {
            guard.push(UiCmd::HighlightSection {
                section_id: section_id.map(ToString::to_string),
                duration_ms,
            });
        }
        Ok(())
    }
}
