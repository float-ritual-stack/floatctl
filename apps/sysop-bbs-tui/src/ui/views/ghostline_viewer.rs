use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{GhostlineEntry, ViewData};

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::GhostlineViewer { streams } = &app.current_view().kind {
        let items: Vec<_> = streams.iter().map(ghost_item).collect();
        let list = List::new(items).block(
            Block::default()
                .title("Ghostline".to_string())
                .borders(Borders::ALL),
        );
        frame.render_widget(list, area);
    }
}

fn ghost_item(entry: &GhostlineEntry) -> ListItem<'_> {
    ListItem::new(vec![
        Line::from(vec![
            Span::styled(entry.channel.as_str(), Theme::header()),
            Span::raw("  "),
            Span::styled(entry.hint.as_str(), Theme::subtitle()),
        ]),
        Line::from(entry.payload.as_str()),
    ])
}
