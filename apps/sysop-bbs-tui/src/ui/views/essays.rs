use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{EssayEntry, ViewData};

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Essays { essays } = &app.current_view().kind {
        let items: Vec<_> = essays.iter().map(essay_item).collect();
        let list =
            List::new(items).block(Block::default().title("Essay drafts").borders(Borders::ALL));
        frame.render_widget(list, area);
    }
}

fn essay_item(essay: &EssayEntry) -> ListItem<'_> {
    ListItem::new(vec![
        Line::from(vec![
            Span::styled(essay.title.as_str(), Theme::header()),
            Span::raw("  "),
            Span::styled(
                if essay.ready { "ready" } else { "draft" },
                Theme::subtitle(),
            ),
        ]),
        Line::from(essay.abstract_text.as_str()),
    ])
}
