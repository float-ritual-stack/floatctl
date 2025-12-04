use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Paragraph};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::ViewData;

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::MultisiteTiles { sites } = &app.current_view().kind {
        let count = sites.len().max(1);
        let pct = ((100 / count).max(1)) as u16;
        let constraints = vec![Constraint::Percentage(pct); count];
        let columns = Layout::default()
            .direction(Direction::Horizontal)
            .constraints(constraints)
            .split(area);

        for (rect, site) in columns.iter().zip(sites.iter()) {
            let block = Block::default()
                .title(Span::styled(site.handle.as_str(), Theme::header()))
                .borders(Borders::ALL);
            let text = Paragraph::new(vec![
                Line::from(site.url.as_str()),
                Line::from(vec![Span::styled(site.status.as_str(), Theme::subtitle())]),
            ])
            .block(block);
            frame.render_widget(text, *rect);
        }
    }
}
