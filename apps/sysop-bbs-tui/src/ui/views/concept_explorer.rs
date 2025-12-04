use ratatui::layout::{Constraint, Rect};
use ratatui::widgets::{Block, Borders, Row, Table};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{ConceptCard, ViewData};

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::ConceptExplorer { concepts } = &app.current_view().kind {
        let rows: Vec<_> = concepts.iter().map(concept_row).collect();
        let table = Table::new(
            rows,
            [
                Constraint::Percentage(30),
                Constraint::Percentage(50),
                Constraint::Percentage(20),
            ],
        )
        .block(
            Block::default()
                .title("Concept energy")
                .borders(Borders::ALL),
        );
        frame.render_widget(table, area);
    }
}

fn concept_row(concept: &ConceptCard) -> Row<'_> {
    Row::new(vec![
        concept.name.clone(),
        concept.description.clone(),
        format!("{} · {}", concept.energy, concept.category),
    ])
    .style(Theme::subtitle())
}
