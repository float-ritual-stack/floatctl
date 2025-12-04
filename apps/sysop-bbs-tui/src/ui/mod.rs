pub mod header;
pub mod overlay;
pub mod shared;
pub mod tab_bar;
pub mod views;

use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::prelude::*;

use crate::AppState;

pub fn render(frame: &mut Frame, app: &AppState) {
    let root = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Length(1),
            Constraint::Min(0),
        ])
        .split(frame.size());

    header::render(frame, root[0], app);
    tab_bar::render(frame, root[1], app);
    views::render(frame, root[2], app);

    if app.overlay_visible() {
        overlay::render(frame, frame.size(), app);
    }
}

pub fn centered_rect(percent_x: u16, percent_y: u16, area: Rect) -> Rect {
    let popup_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints(
            [
                Constraint::Percentage((100 - percent_y) / 2),
                Constraint::Percentage(percent_y),
                Constraint::Percentage((100 - percent_y) / 2),
            ]
            .as_ref(),
        )
        .split(area);

    Layout::default()
        .direction(Direction::Horizontal)
        .constraints(
            [
                Constraint::Percentage((100 - percent_x) / 2),
                Constraint::Percentage(percent_x),
                Constraint::Percentage((100 - percent_x) / 2),
            ]
            .as_ref(),
        )
        .split(popup_layout[1])[1]
}
