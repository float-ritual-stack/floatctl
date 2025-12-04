use std::borrow::Cow;

use ratatui::prelude::*;

pub fn pill<'a>(text: impl Into<Cow<'a, str>>, fg: Color) -> Span<'a> {
    Span::styled(
        format!(" {} ", text.into()),
        Style::default()
            .fg(fg)
            .bg(Color::Black)
            .add_modifier(Modifier::BOLD),
    )
}
