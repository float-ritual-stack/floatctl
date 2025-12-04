use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{DailyEntry, ViewData};

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Daily { entries } = &app.current_view().kind {
        let items: Vec<_> = entries.iter().map(daily_item).collect();
        let list = List::new(items).block(
            Block::default()
                .title("Daily rituals")
                .borders(Borders::ALL),
        );
        frame.render_widget(list, area);
    }
}

fn daily_item(entry: &DailyEntry) -> ListItem<'_> {
    let mut lines = Vec::new();
    lines.push(Line::from(vec![
        Span::styled(entry.title.as_str(), Theme::header()),
        Span::raw("  "),
        Span::styled(entry.status.as_str(), Theme::subtitle()),
    ]));
    for action in &entry.actions {
        lines.push(Line::from(format!(" - {}", action)));
    }
    ListItem::new(lines)
}
