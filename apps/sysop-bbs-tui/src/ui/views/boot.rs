use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{BootPhase, ViewData};

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Boot { phases } = &app.current_view().kind {
        let chunks = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([Constraint::Percentage(60), Constraint::Percentage(40)])
            .split(area);

        let list_items: Vec<_> = phases.iter().map(phase_item).collect();
        let list = List::new(list_items)
            .block(Block::default().title("Boot phases").borders(Borders::ALL));
        frame.render_widget(list, chunks[0]);

        let detail = Paragraph::new(
            "Space to ground into ops rituals. Use Enter to log command stubs in other views.",
        )
        .style(Theme::subtitle());
        frame.render_widget(detail, chunks[1]);
    }
}

fn phase_item(phase: &BootPhase) -> ListItem<'_> {
    let mut lines = vec![Line::from(format!("• {}", phase.label))];
    for detail in &phase.details {
        lines.push(Line::from(format!("  - {}", detail)));
    }
    ListItem::new(lines)
}
