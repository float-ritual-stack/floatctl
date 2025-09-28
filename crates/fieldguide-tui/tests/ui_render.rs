use std::time::Duration;

use fieldguide_tui::app::{AppState, ViewMode};
use fieldguide_tui::model::FieldGuide;
use fieldguide_tui::ui;
use ratatui::backend::TestBackend;
use ratatui::Terminal;

#[test]
fn render_produces_fieldguide_header() {
    let backend = TestBackend::new(80, 24);
    let mut terminal = Terminal::new(backend).expect("terminal");
    let guide = FieldGuide::sample();
    let app = AppState::new(guide, ViewMode::Normal, None, Duration::from_millis(200));
    terminal
        .draw(|frame| ui::draw(frame, &app))
        .expect("draw should succeed");
    let buffer = terminal.backend().buffer().clone();
    let mut header_symbols = String::new();
    let max_x = buffer.area().width.min(40);
    for x in 1..max_x {
        if let Some(cell) = buffer.cell((x, 1)) {
            header_symbols.push_str(cell.symbol().as_ref());
        }
    }
    assert!(header_symbols.contains("PATTERN"));
}
