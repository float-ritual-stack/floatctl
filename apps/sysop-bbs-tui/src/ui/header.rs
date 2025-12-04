use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Paragraph};

use crate::AppState;

use super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    let header = Paragraph::new(vec![
        Line::from(vec![
            Span::styled(app.data().title.as_str(), Theme::header()),
            Span::raw("  "),
            Span::styled(app.data().subtitle.as_str(), Theme::subtitle()),
        ]),
        Line::from(vec![
            Span::styled("active view: ", Theme::subtitle()),
            Span::styled(format!("{:?}", app.data().active_view), Theme::header()),
        ]),
    ])
    .block(Block::default().borders(Borders::BOTTOM));
    frame.render_widget(header, area);
}
