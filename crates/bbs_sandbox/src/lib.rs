use anyhow::Result;
use bbs_core::model::{ConceptCard, DataModel, ViewData, ViewId, ViewState};
use serde::{Deserialize, Serialize};
use tracing::debug;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxReport {
    pub diagnostics: Vec<String>,
}

pub fn synthesize_report(model: &DataModel) -> SandboxReport {
    let mut diagnostics = Vec::new();

    diagnostics.push(format!(
        "active view: {:?} ({} tabs)",
        model.active_view,
        model.tabs.len()
    ));

    if let Some(concepts) = concept_energy(model) {
        diagnostics.push(format!(
            "concept energy avg: {:.1}",
            concepts.iter().map(|card| card.energy as f32).sum::<f32>() / concepts.len() as f32
        ));
    }

    SandboxReport { diagnostics }
}

fn concept_energy(model: &DataModel) -> Option<Vec<ConceptCard>> {
    model
        .view(ViewId::ConceptExplorer)
        .and_then(|view| match &view.kind {
            ViewData::ConceptExplorer { concepts } => Some(concepts.clone()),
            _ => None,
        })
}

pub fn refresh_view(model: &mut DataModel, new_view: ViewState) -> Result<()> {
    if let Some(slot) = model.views.iter_mut().find(|view| view.id == new_view.id) {
        *slot = new_view;
    }
    debug!("sandbox refresh executed");
    Ok(())
}
