use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{BoardSummary, ViewData};

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Boards { boards } = &app.current_view().kind {
        let items: Vec<_> = boards.iter().map(board_item).collect();
        let list = List::new(items).block(Block::default().title("Boards").borders(Borders::ALL));
        frame.render_widget(list, area);
    }
}

fn board_item(board: &BoardSummary) -> ListItem<'_> {
    ListItem::new(vec![
        Line::from(vec![
            Span::styled(board.name.as_str(), Theme::header()),
            Span::raw("  "),
            Span::styled(format!("unread: {}", board.unread), Theme::subtitle()),
        ]),
        Line::from(board.description.as_str()),
    ])
}
