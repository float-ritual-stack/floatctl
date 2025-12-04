use ratatui::layout::Rect;
use ratatui::widgets::{Block, Borders, Paragraph};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::ViewData;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Unknown { note } = &app.current_view().kind {
        let paragraph = Paragraph::new(note.clone())
            .block(Block::default().title("Unknown view").borders(Borders::ALL));
        frame.render_widget(paragraph, area);
    }
}
