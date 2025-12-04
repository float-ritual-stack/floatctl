use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Clear, Paragraph};

use crate::AppState;

use super::centered_rect;
use super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let Some(overlay) = app.data().overlays.first() {
        let area = centered_rect(60, 50, area);
        let text: Vec<_> = overlay
            .body
            .iter()
            .map(|line| Line::from(Span::raw(line.clone())))
            .collect();
        let block = Block::default()
            .title(Span::styled(overlay.title.as_str(), Theme::header()))
            .borders(Borders::ALL)
            .border_style(Theme::subtitle());
        frame.render_widget(Clear, area);
        frame.render_widget(Paragraph::new(text).block(block), area);
    }
}
