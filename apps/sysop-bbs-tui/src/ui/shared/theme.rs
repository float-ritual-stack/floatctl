use ratatui::style::{Color, Style};

pub struct Theme;

impl Theme {
    pub const FG: Color = Color::Cyan;
    pub const MUTED: Color = Color::DarkGray;
    pub const ACCENT: Color = Color::Magenta;
    pub fn header() -> Style {
        Style::default()
            .fg(Self::FG)
            .add_modifier(ratatui::style::Modifier::BOLD)
    }

    pub fn subtitle() -> Style {
        Style::default().fg(Self::MUTED)
    }

    pub fn highlight() -> Style {
        Style::default()
            .fg(Color::Black)
            .bg(Self::ACCENT)
            .add_modifier(ratatui::style::Modifier::BOLD)
    }
}
