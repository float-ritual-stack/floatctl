use anyhow::{bail, Result};
use bbs_core::model::{DataModel, ViewData, ViewId};
use tracing::info;

pub fn run_checks(model: &DataModel) -> Result<()> {
    let mut failures = Vec::new();
    for check in checks(model) {
        if check.passed {
            info!(target: "self_check", "check {} ok - {}", check.code, check.summary);
        } else {
            failures.push(format!("{}: {}", check.code, check.summary));
        }
    }

    if failures.is_empty() {
        Ok(())
    } else {
        bail!("self-check failed: {}", failures.join(", "))
    }
}

struct CheckResult {
    code: &'static str,
    summary: String,
    passed: bool,
}

fn checks(model: &DataModel) -> Vec<CheckResult> {
    vec![
        check_required_views(model),
        check_tab_targets(model),
        check_projects_layout(model),
        check_projects_searchability(model),
        check_overlays(model),
        check_digest_content(model),
        check_multisite(model),
    ]
}

fn check_required_views(model: &DataModel) -> CheckResult {
    let missing: Vec<_> = ViewId::ALL
        .into_iter()
        .filter(|id| model.view(*id).is_none())
        .collect();
    CheckResult {
        code: "A",
        summary: if missing.is_empty() {
            "all required views present".to_string()
        } else {
            format!("missing views: {missing:?}")
        },
        passed: missing.is_empty(),
    }
}

fn check_tab_targets(model: &DataModel) -> CheckResult {
    let bad: Vec<_> = model
        .tabs
        .iter()
        .filter(|tab| model.view(tab.id).is_none())
        .map(|tab| tab.label.clone())
        .collect();
    CheckResult {
        code: "B",
        summary: if bad.is_empty() {
            "all tabs wired to views".to_string()
        } else {
            format!("tabs missing views: {bad:?}")
        },
        passed: bad.is_empty(),
    }
}

fn check_projects_layout(model: &DataModel) -> CheckResult {
    let ok = model
        .view(ViewId::ProjectsGrid)
        .and_then(|view| match &view.kind {
            ViewData::ProjectsGrid { projects, .. } => Some(!projects.is_empty()),
            _ => None,
        })
        .unwrap_or(false);
    CheckResult {
        code: "C",
        summary: if ok {
            "projects grid populated".to_string()
        } else {
            "projects grid empty".to_string()
        },
        passed: ok,
    }
}

fn check_projects_searchability(model: &DataModel) -> CheckResult {
    let ok = model
        .view(ViewId::ProjectsGrid)
        .and_then(|view| match &view.kind {
            ViewData::ProjectsGrid { projects, .. } => {
                Some(projects.iter().any(|p| !p.tags.is_empty()))
            }
            _ => None,
        })
        .unwrap_or(false);
    CheckResult {
        code: "D",
        summary: if ok {
            "projects carry tags for search".to_string()
        } else {
            "project tags missing".to_string()
        },
        passed: ok,
    }
}

fn check_overlays(model: &DataModel) -> CheckResult {
    let ok = !model.overlays.is_empty()
        && model
            .overlays
            .iter()
            .all(|overlay| !overlay.body.is_empty());
    CheckResult {
        code: "E",
        summary: if ok {
            "overlay configured".to_string()
        } else {
            "overlay missing entries".to_string()
        },
        passed: ok,
    }
}

fn check_digest_content(model: &DataModel) -> CheckResult {
    let ok = model
        .view(ViewId::Digest)
        .and_then(|view| match &view.kind {
            ViewData::Digest { entries } => Some(!entries.is_empty()),
            _ => None,
        })
        .unwrap_or(false);
    CheckResult {
        code: "F",
        summary: if ok {
            "digest entries available".to_string()
        } else {
            "digest empty".to_string()
        },
        passed: ok,
    }
}

fn check_multisite(model: &DataModel) -> CheckResult {
    let ok = model
        .view(ViewId::MultisiteTiles)
        .and_then(|view| match &view.kind {
            ViewData::MultisiteTiles { sites } => Some(!sites.is_empty()),
            _ => None,
        })
        .unwrap_or(false);
    CheckResult {
        code: "G",
        summary: if ok {
            "multisite tiles seeded".to_string()
        } else {
            "no multisite tiles".to_string()
        },
        passed: ok,
    }
}
