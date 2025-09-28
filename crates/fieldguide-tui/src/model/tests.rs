use super::*;

#[test]
fn sample_contains_expected_sections() {
    let guide = FieldGuide::sample();
    assert_eq!(guide.sections.len(), 2);
    assert_eq!(guide.sections[0].id, "mirc-patterns");
    assert_eq!(guide.sections[1].id, "redux-evolution");
}

#[test]
fn entries_preserve_signal_order() {
    let guide = FieldGuide::sample();
    let first_section = &guide.sections[0];
    let first_entry = &first_section.entries[0];
    assert_eq!(first_entry.signals.first().unwrap(), "on *:TEXT:");
    assert_eq!(first_entry.signals.last().unwrap(), "contextual routing");
}

#[test]
fn meta_strings_are_non_empty() {
    let guide = FieldGuide::sample();
    assert!(!guide.meta.title.is_empty());
    assert!(!guide.meta.subtitle.is_empty());
    assert!(!guide.meta.version.is_empty());
    assert!(!guide.meta.context.is_empty());
}
