use std::path::PathBuf;

use anyhow::Result;
use bbs_core::{self, self_check, BbsData, ViewType};

/// Load bulletin board data, respecting CLI overrides.
pub fn load_board(path: Option<PathBuf>) -> Result<BbsData> {
    Ok(bbs_core::load_data(path)?)
}

/// Run the self-check suite against the provided board data.
pub fn run_self_check(data: &BbsData, require_custom: bool) -> Result<self_check::SelfCheckReport> {
    let report = self_check::run(data);
    report.ensure_complete_with_options(ViewType::all(), require_custom)?;
    Ok(report)
}

/// Convenience wrapper to load data from disk strictly for self-checking.
pub fn run_self_check_from_path(
    path: PathBuf,
    require_custom: bool,
) -> Result<self_check::SelfCheckReport> {
    let data = bbs_core::load_data(Some(path))?;
    run_self_check(&data, require_custom)
}

/// Print a concise tab summary used by the demo binaries.
pub fn print_tab_summary(data: &BbsData) {
    println!("{}", data.title);
    if let Some(summary) = &data.summary {
        println!("{summary}\n");
    }
    for (index, tab) in data.tabs().iter().enumerate() {
        println!("{:>2}. {} ({})", index + 1, tab.label, tab.id);
        for view in &tab.views {
            let view_label = match &view.kind {
                bbs_core::ViewKind::Known(kind) => kind.to_string(),
                bbs_core::ViewKind::Custom(custom) => format!("custom:{custom}"),
            };
            println!("      - {view_label} :: {}", view.label);
        }
    }
}

/// Render a single pill to demonstrate theming.
pub fn preview_pill(label: &str, theme: &bbs_core::Theme) {
    use ratatui::style::Style;
    use ratatui::text::Span;

    let pill = bbs_core::PillConfig {
        label: label.into(),
        tone: bbs_core::PillTone::Accent,
        description: None,
    };
    let rendered = bbs_core::render_pill(&pill, theme);
    let Span { content, style } = rendered
        .spans
        .first()
        .cloned()
        .unwrap_or_else(|| Span::styled(label.to_string(), Style::default()));
    println!("{content} (fg={:?} bg={:?})", style.fg, style.bg);
}

/// Format a dispatch summary used in the router demo.
pub fn describe_dispatch(data: &BbsData) {
    println!("Dispatch coverage:\n");
    for tab in data.tabs() {
        for view in &tab.views {
            match &view.kind {
                bbs_core::ViewKind::Known(kind) => println!("- {} -> {}", tab.id, kind),
                bbs_core::ViewKind::Custom(custom) => {
                    println!("- {} -> custom({})", tab.id, custom)
                }
            }
        }
    }
}
