use ratatui::layout::{Constraint, Rect};
use ratatui::widgets::{Block, Borders, Row, Table};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{DevtoolCommand, ViewData};

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Devtools { commands } = &app.current_view().kind {
        let rows: Vec<_> = commands.iter().map(command_row).collect();
        let table = Table::new(
            rows,
            [
                Constraint::Percentage(20),
                Constraint::Percentage(40),
                Constraint::Percentage(40),
            ],
        )
        .block(Block::default().title("Devtools").borders(Borders::ALL));
        frame.render_widget(table, area);
    }
}

fn command_row(command: &DevtoolCommand) -> Row<'_> {
    Row::new(vec![
        command.name.clone(),
        command.synopsis.clone(),
        command.command.clone(),
    ])
}
