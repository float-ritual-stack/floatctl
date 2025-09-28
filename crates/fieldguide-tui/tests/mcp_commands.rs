use crossbeam_channel::unbounded;

use fieldguide_tui::app::{ExpandAction, UiCmd, ViewMode};
use fieldguide_tui::mcp::api::{ChannelControlSink, ControlSink, MockControlSink};

#[test]
fn mock_control_captures_commands() {
    let sink = MockControlSink::default();
    sink.expand_section("section-a", ExpandAction::Expand)
        .unwrap();
    sink.change_view_mode(ViewMode::Compact).unwrap();
    sink.highlight_section(Some("section-b"), Some(300))
        .unwrap();
    let commands = sink.take();
    assert!(commands.iter().any(|cmd| matches!(
        cmd,
        UiCmd::ExpandSection {
            section_id,
            action: ExpandAction::Expand,
        } if section_id == "section-a"
    )));
    assert!(commands.iter().any(|cmd| matches!(
        cmd,
        UiCmd::ChangeViewMode {
            mode: ViewMode::Compact
        }
    )));
    assert!(commands.iter().any(|cmd| matches!(
        cmd,
        UiCmd::HighlightSection {
            section_id: Some(id),
            duration_ms: Some(300),
        } if id == "section-b"
    )));
}

#[test]
fn channel_sink_forwards_to_ui() {
    let (tx, rx) = unbounded();
    let sink = ChannelControlSink::new(tx);
    sink.expand_section("redux-evolution", ExpandAction::Toggle)
        .unwrap();
    sink.change_view_mode(ViewMode::Expanded).unwrap();
    let first = rx.recv().unwrap();
    match first {
        UiCmd::ExpandSection { section_id, action } => {
            assert_eq!(section_id, "redux-evolution");
            assert_eq!(action, ExpandAction::Toggle);
        }
        other => panic!("unexpected command: {other:?}"),
    }
    let second = rx.recv().unwrap();
    assert!(matches!(
        second,
        UiCmd::ChangeViewMode {
            mode: ViewMode::Expanded
        }
    ));
}
