use std::io;
use std::path::PathBuf;

use thiserror::Error;

#[derive(Debug, Error)]
pub enum UiError {
    #[error("unknown section id '{0}'")]
    UnknownSection(String),
    #[error("invalid view mode '{0}'")]
    InvalidViewMode(String),
    #[error("invalid expand action '{0}'")]
    InvalidExpandAction(String),
    #[error("invalid highlight duration '{0}' ms")]
    InvalidDuration(u64),
}

#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("failed to read config at {path:?}: {source}")]
    Read { path: PathBuf, source: io::Error },
    #[error("failed to parse config at {path:?}: {source}")]
    ParseToml {
        path: PathBuf,
        source: toml::de::Error,
    },
}

#[derive(Debug, Error)]
pub enum PersistError {
    #[error("failed to read state at {path:?}: {source}")]
    Read { path: PathBuf, source: io::Error },
    #[error("failed to create state directory {path:?}: {source}")]
    CreateDir { path: PathBuf, source: io::Error },
    #[error("failed to parse state at {path:?}: {source}")]
    Parse {
        path: PathBuf,
        source: serde_json::Error,
    },
    #[error("failed to write state at {path:?}: {source}")]
    Write { path: PathBuf, source: io::Error },
}

#[derive(Debug, Error)]
pub enum McpServerError {
    #[error("mcp channel closed")]
    ChannelClosed,
    #[error("validation failed: {0}")]
    Validation(String),
    #[error("transport error: {0}")]
    Transport(String),
}

pub type Result<T> = std::result::Result<T, anyhow::Error>;
