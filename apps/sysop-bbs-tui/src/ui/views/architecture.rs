use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{ArchitectureSection, ViewData};

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Architecture { sections } = &app.current_view().kind {
        let items: Vec<_> = sections.iter().map(section_item).collect();
        let list =
            List::new(items).block(Block::default().title("Architecture").borders(Borders::ALL));
        frame.render_widget(list, area);
    }
}

fn section_item(section: &ArchitectureSection) -> ListItem<'_> {
    let mut lines = Vec::new();
    lines.push(Line::from(Span::styled(
        section.name.as_str(),
        Theme::header(),
    )));
    for note in &section.notes {
        lines.push(Line::from(format!(" - {}", note)));
    }
    ListItem::new(lines)
}
