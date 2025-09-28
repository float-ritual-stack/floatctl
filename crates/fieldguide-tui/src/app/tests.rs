use std::time::{Duration, Instant};

use super::*;

fn make_app() -> AppState {
    let guide = FieldGuide::sample();
    AppState::new(guide, ViewMode::Normal, None, Duration::from_millis(250))
}

#[test]
fn expanding_marks_dirty_and_state() {
    let mut app = make_app();
    let section_id = app.focused_section().unwrap().id.clone();
    app.apply(UiCmd::ExpandSection {
        section_id: section_id.clone(),
        action: ExpandAction::Collapse,
    })
    .unwrap();
    assert!(!app.is_expanded(&section_id));
    assert!(app.dirty().contains(Dirty::DATA));
}

#[test]
fn change_view_mode_updates_state() {
    let mut app = make_app();
    app.apply(UiCmd::ChangeViewMode {
        mode: ViewMode::Compact,
    })
    .unwrap();
    assert_eq!(app.view_mode(), ViewMode::Compact);
    assert!(app.dirty().contains(Dirty::LAYOUT));
}

#[test]
fn highlight_clears_after_duration() {
    let mut app = make_app();
    let section_id = app.focused_section().unwrap().id.clone();
    app.apply(UiCmd::HighlightSection {
        section_id: Some(section_id.clone()),
        duration_ms: Some(10),
    })
    .unwrap();
    assert!(app.highlight().is_some());
    std::thread::sleep(Duration::from_millis(15));
    app.clear_expired_highlight(Instant::now());
    assert!(app.highlight().is_none());
}

#[test]
fn invalid_section_returns_error() {
    let mut app = make_app();
    let err = app
        .apply(UiCmd::ExpandSection {
            section_id: "missing".to_string(),
            action: ExpandAction::Toggle,
        })
        .unwrap_err();
    assert!(matches!(err, UiError::UnknownSection(id) if id == "missing"));
}

#[test]
fn dirty_flags_clear_after_take() {
    let mut app = make_app();
    assert!(app.take_dirty().contains(Dirty::ALL));
    let dirty = app.take_dirty();
    assert_eq!(dirty, Dirty::NONE);
}
