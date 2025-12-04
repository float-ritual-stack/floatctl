use ratatui::layout::{Constraint, Rect};
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Paragraph, Row, Table};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::ViewData;

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Board { board } = &app.current_view().kind {
        let header = Paragraph::new(vec![Line::from(vec![
            Span::styled(board.name.as_str(), Theme::header()),
            Span::raw("  "),
            Span::styled(board.description.as_str(), Theme::subtitle()),
        ])])
        .block(Block::default().borders(Borders::BOTTOM));
        let chunks = ratatui::layout::Layout::default()
            .direction(ratatui::layout::Direction::Vertical)
            .constraints([Constraint::Length(3), Constraint::Min(0)])
            .split(area);
        frame.render_widget(header, chunks[0]);

        let rows: Vec<_> = board
            .threads
            .iter()
            .map(|thread| {
                Row::new(vec![
                    thread.subject.clone(),
                    thread.author.clone(),
                    thread.replies.to_string(),
                    thread.last_updated.clone(),
                ])
            })
            .collect();
        let table = Table::new(
            rows,
            [
                Constraint::Percentage(40),
                Constraint::Percentage(20),
                Constraint::Percentage(20),
                Constraint::Percentage(20),
            ],
        )
        .block(Block::default().title("Threads").borders(Borders::ALL));
        frame.render_widget(table, chunks[1]);
    }
}
