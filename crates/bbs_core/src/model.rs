use std::collections::BTreeMap;

use anyhow::Result;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataModel {
    pub title: String,
    pub subtitle: String,
    pub active_view: ViewId,
    pub tabs: Vec<Tab>,
    pub overlays: Vec<Overlay>,
    pub views: Vec<ViewState>,
}

impl DataModel {
    pub fn view(&self, id: ViewId) -> Option<&ViewState> {
        self.views.iter().find(|view| view.id == id)
    }

    pub fn to_lookup(&self) -> BTreeMap<ViewId, &ViewState> {
        let mut map = BTreeMap::new();
        for view in &self.views {
            map.insert(view.id, view);
        }
        map
    }

    pub fn validate(&self) -> Result<()> {
        let mut errors = Vec::new();
        for expected in ViewId::ALL {
            if self.view(expected).is_none() {
                errors.push(format!("missing view: {expected:?}"));
            }
        }

        if self.tabs.is_empty() {
            errors.push("no tabs declared".to_string());
        }

        if !errors.is_empty() {
            return Err(ModelError::ValidationFailed { errors }.into());
        }

        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash, Copy)]
#[serde(rename_all = "snake_case")]
pub enum ViewId {
    Boot,
    Digest,
    ProjectsGrid,
    Boards,
    Board,
    Daily,
    Essays,
    Architecture,
    ConceptExplorer,
    GhostlineViewer,
    Devtools,
    Ast,
    MultisiteTiles,
    Unknown,
}

impl ViewId {
    pub const ALL: [ViewId; 14] = [
        ViewId::Boot,
        ViewId::Digest,
        ViewId::ProjectsGrid,
        ViewId::Boards,
        ViewId::Board,
        ViewId::Daily,
        ViewId::Essays,
        ViewId::Architecture,
        ViewId::ConceptExplorer,
        ViewId::GhostlineViewer,
        ViewId::Devtools,
        ViewId::Ast,
        ViewId::MultisiteTiles,
        ViewId::Unknown,
    ];
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tab {
    pub id: ViewId,
    pub label: String,
    pub hint: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Overlay {
    pub title: String,
    pub body: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViewState {
    pub id: ViewId,
    pub title: String,
    pub summary: String,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(flatten)]
    pub kind: ViewData,
}

impl ViewState {
    pub fn projects(&self) -> Option<&[Project]> {
        match &self.kind {
            ViewData::ProjectsGrid { projects, .. } => Some(projects.as_slice()),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ViewData {
    Boot {
        phases: Vec<BootPhase>,
    },
    Digest {
        entries: Vec<DigestEntry>,
    },
    ProjectsGrid {
        projects: Vec<Project>,
        default_layout: LayoutMode,
    },
    Boards {
        boards: Vec<BoardSummary>,
    },
    Board {
        board: BoardDetail,
    },
    Daily {
        entries: Vec<DailyEntry>,
    },
    Essays {
        essays: Vec<EssayEntry>,
    },
    Architecture {
        sections: Vec<ArchitectureSection>,
    },
    ConceptExplorer {
        concepts: Vec<ConceptCard>,
    },
    GhostlineViewer {
        streams: Vec<GhostlineEntry>,
    },
    Devtools {
        commands: Vec<DevtoolCommand>,
    },
    Ast {
        nodes: Vec<AstNode>,
    },
    MultisiteTiles {
        sites: Vec<SiteTile>,
    },
    Unknown {
        note: String,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BootPhase {
    pub label: String,
    pub details: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DigestEntry {
    pub headline: String,
    pub context: String,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub name: String,
    pub description: String,
    #[serde(default)]
    pub tags: Vec<String>,
    pub status: ProjectStatus,
    #[serde(default)]
    pub links: Vec<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProjectStatus {
    Exploring,
    Active,
    Maintenance,
    Archived,
}

#[derive(Debug, Clone, Serialize, Deserialize, Copy, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum LayoutMode {
    Grid,
    List,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoardSummary {
    pub name: String,
    pub description: String,
    pub unread: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoardDetail {
    pub name: String,
    pub description: String,
    pub threads: Vec<ThreadEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThreadEntry {
    pub subject: String,
    pub author: String,
    pub replies: usize,
    pub last_updated: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DailyEntry {
    pub title: String,
    pub status: String,
    pub actions: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EssayEntry {
    pub title: String,
    pub abstract_text: String,
    pub ready: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArchitectureSection {
    pub name: String,
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConceptCard {
    pub name: String,
    pub description: String,
    pub energy: u8,
    pub category: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GhostlineEntry {
    pub channel: String,
    pub payload: String,
    pub hint: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevtoolCommand {
    pub name: String,
    pub synopsis: String,
    pub command: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AstNode {
    pub label: String,
    pub depth: usize,
    pub details: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SiteTile {
    pub handle: String,
    pub url: String,
    pub status: String,
}

#[derive(Debug, Error)]
pub enum ModelError {
    #[error("validation failed: {errors:?}")]
    ValidationFailed { errors: Vec<String> },

    #[error("view lookup failed for {0:?}")]
    ViewMissing(ViewId),
}

pub fn view_lookup<'a>(model: &'a DataModel) -> BTreeMap<ViewId, &'a ViewState> {
    model.to_lookup()
}
