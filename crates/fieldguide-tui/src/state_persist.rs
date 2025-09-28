use std::fs;
use std::path::PathBuf;

use log::debug;
use serde::{Deserialize, Serialize};

use crate::app::{AppState, ViewMode};
use crate::config::{ensure_state_dir, state_file_path};
use crate::error::PersistError;

#[derive(Clone, Debug, Default, Serialize, Deserialize, PartialEq, Eq)]
pub struct LastRunState {
    pub view_mode: Option<String>,
    pub focused_section: Option<String>,
}

impl LastRunState {
    pub fn from_app(app: &AppState) -> Self {
        Self {
            view_mode: Some(app.view_mode().as_str().to_string()),
            focused_section: app.focused_section().map(|section| section.id.clone()),
        }
    }
}

pub fn load_last_run() -> Result<Option<LastRunState>, PersistError> {
    let path = state_file_path();
    if !path.exists() {
        debug!("state file missing at {:?}", path);
        return Ok(None);
    }
    let data = fs::read_to_string(&path).map_err(|source| PersistError::Read {
        path: path.clone(),
        source,
    })?;
    let state: LastRunState =
        serde_json::from_str(&data).map_err(|source| PersistError::Parse {
            path: path.clone(),
            source,
        })?;
    Ok(Some(state))
}

pub fn save_last_run(state: &LastRunState) -> Result<(), PersistError> {
    let path = state_file_path();
    let dir: PathBuf = path
        .parent()
        .map(PathBuf::from)
        .unwrap_or_else(|| ensure_state_dir().join("fieldguide-tui"));
    if !dir.exists() {
        fs::create_dir_all(&dir).map_err(|source| PersistError::CreateDir {
            path: dir.clone(),
            source,
        })?;
    }
    let payload = serde_json::to_string_pretty(state).map_err(|source| PersistError::Parse {
        path: path.clone(),
        source,
    })?;
    fs::write(&path, payload).map_err(|source| PersistError::Write { path, source })
}

pub fn restore_view_mode(state: Option<&LastRunState>, fallback: ViewMode) -> ViewMode {
    state
        .and_then(|s| s.view_mode.as_deref())
        .and_then(|value| ViewMode::try_from_str(value).ok())
        .unwrap_or(fallback)
}

pub fn restore_focus(state: Option<&LastRunState>) -> Option<&str> {
    state.and_then(|s| s.focused_section.as_deref())
}
