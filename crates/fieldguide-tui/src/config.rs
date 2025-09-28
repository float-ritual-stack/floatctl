use std::env;
use std::fs;
use std::path::{Path, PathBuf};

use log::debug;
use serde::{Deserialize, Serialize};

use crate::app::ViewMode;
use crate::error::ConfigError;

#[derive(Clone, Debug, Deserialize, Serialize, Default)]
pub struct KeyBindingsConfig {
    pub toggle: Option<String>,
    pub cycle_view: Option<String>,
    pub highlight: Option<String>,
    pub quit: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize, Default)]
#[serde(rename_all = "lowercase")]
pub enum Theme {
    Light,
    #[default]
    Dark,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Config {
    #[serde(default = "default_tick_interval")]
    pub tick_interval_ms: u64,
    #[serde(default = "default_view_mode")]
    pub initial_view_mode: String,
    #[serde(default)]
    pub keybindings: Option<KeyBindingsConfig>,
    #[serde(default)]
    pub theme: Theme,
}

fn default_tick_interval() -> u64 {
    250
}

fn default_view_mode() -> String {
    "normal".to_string()
}

impl Default for Config {
    fn default() -> Self {
        Self {
            tick_interval_ms: default_tick_interval(),
            initial_view_mode: default_view_mode(),
            keybindings: None,
            theme: Theme::default(),
        }
    }
}

impl Config {
    pub fn load() -> Result<Self, ConfigError> {
        let path = config_file_path();
        if !path.exists() {
            debug!("config file missing at {:?}; using defaults", path);
            return Ok(Self::default());
        }
        let data = fs::read_to_string(&path).map_err(|source| ConfigError::Read {
            path: path.clone(),
            source,
        })?;
        let config: Self = toml::from_str(&data).map_err(|source| ConfigError::ParseToml {
            path: path.clone(),
            source,
        })?;
        Ok(config)
    }

    pub fn resolved_view_mode(&self) -> ViewMode {
        ViewMode::try_from_str(&self.initial_view_mode).unwrap_or(ViewMode::Normal)
    }
}

fn home_dir() -> PathBuf {
    env::var("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("."))
}

pub fn config_file_path() -> PathBuf {
    home_dir()
        .join(".config")
        .join("floatctl")
        .join("fieldguide-tui.toml")
}

pub fn ensure_state_dir() -> PathBuf {
    home_dir().join(".local").join("state").join("floatctl")
}

pub fn state_file_path() -> PathBuf {
    ensure_state_dir().join("fieldguide-tui").join("state.json")
}

pub fn ensure_parent_dir(path: &Path) -> Result<(), ConfigError> {
    if let Some(parent) = path.parent() {
        if !parent.exists() {
            std::fs::create_dir_all(parent).map_err(|source| ConfigError::Read {
                path: parent.to_path_buf(),
                source,
            })?;
        }
    }
    Ok(())
}
