use std::time::Instant;

use ratatui::layout::{Constraint, Direction, Layout};
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};
use ratatui::Frame;

use crate::app::{App, ViewMode};
use crate::model::Section;

pub fn draw(frame: &mut Frame<'_>, app: &App) {
    let now = Instant::now();
    let guide = app.guide();
    // Layout strategy per Ratatui layout guide: https://docs.rs/ratatui/latest/ratatui/layout/index.html
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(5),
            Constraint::Min(0),
            Constraint::Length(3),
        ])
        .split(frame.area());

    frame.render_widget(
        render_header(
            guide.meta.title.as_str(),
            guide.meta.subtitle.as_str(),
            guide.meta.version.as_str(),
            guide.meta.context.as_str(),
        ),
        chunks[0],
    );

    if app.sections_len() > 0 {
        let section_constraints = vec![Constraint::Min(3); app.sections_len()];
        let section_chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints(section_constraints)
            .split(chunks[1]);

        for (index, section) in guide.sections.iter().enumerate() {
            let area = section_chunks.get(index).copied().unwrap_or(chunks[1]);
            let widget = render_section(section, index, app, now);
            frame.render_widget(widget, area);
        }
    } else {
        frame.render_widget(
            Paragraph::new("No sections available").block(Block::default().borders(Borders::ALL)),
            chunks[1],
        );
    }

    frame.render_widget(render_footer(app.view_mode()), chunks[2]);
}

fn render_header<'a>(
    title: &'a str,
    subtitle: &'a str,
    version: &'a str,
    context: &'a str,
) -> Paragraph<'a> {
    let mut lines = Vec::new();
    lines.push(Line::from(vec![Span::styled(
        title,
        Style::default().add_modifier(Modifier::BOLD),
    )]));
    lines.push(Line::from(subtitle));
    lines.push(Line::from(format!("version: {}", version)));
    lines.push(Line::from(format!("context: {}", context)));

    Paragraph::new(lines)
        .block(Block::default().title("Field Guide").borders(Borders::ALL))
        .wrap(Wrap { trim: true })
}

fn render_section<'a>(
    section: &'a Section,
    index: usize,
    app: &'a App,
    now: Instant,
) -> Paragraph<'a> {
    let expanded = app.is_expanded(&section.id);
    let mut lines = Vec::new();

    let icon = icon_for(section.icon.as_str());
    let header = format!("{} {}", icon, section.title);
    lines.push(Line::from(vec![Span::styled(
        header,
        Style::default().add_modifier(Modifier::BOLD),
    )]));

    if expanded {
        let view_mode = app.view_mode();
        for entry in &section.entries {
            let mut entry_lines = Vec::new();
            entry_lines.push(Line::from(vec![Span::styled(
                format!("• {}", entry.pattern),
                Style::default().add_modifier(Modifier::BOLD),
            )]));
            match view_mode {
                ViewMode::Compact => {
                    entry_lines.push(Line::from(format!("signals: {}", entry.signals.join(", "))));
                }
                ViewMode::Normal => {
                    entry_lines.push(Line::from(entry.description.as_str()));
                    entry_lines.push(Line::from(format!("signals: {}", entry.signals.join(", "))));
                }
                ViewMode::Expanded => {
                    entry_lines.push(Line::from(entry.description.as_str()));
                    entry_lines.push(Line::from(format!("signals: {}", entry.signals.join(", "))));
                    entry_lines.push(Line::from(format!("protocol: {}", entry.protocol)));
                }
            }
            lines.extend(entry_lines);
            lines.push(Line::default());
        }
    } else {
        lines.push(Line::from("(collapsed)"));
    }

    let mut block = Block::default()
        .borders(Borders::ALL)
        .title(Line::from(vec![Span::styled(
            format!("{} {}", icon, section.title),
            Style::default().fg(color_from_name(section.color.as_str())),
        )]));

    let mut border_style = Style::default();
    if app.focus_index() == index {
        border_style = border_style.add_modifier(Modifier::BOLD);
    }
    if app.is_highlighted(&section.id, now) {
        border_style = border_style.fg(Color::Yellow);
    }
    block = block.border_style(border_style).style(Style::default());

    Paragraph::new(lines).block(block).wrap(Wrap { trim: true })
}

fn render_footer(view_mode: ViewMode) -> Paragraph<'static> {
    let help = vec![
        Span::raw("Keys:"),
        Span::raw(" [Space/Enter] toggle"),
        Span::raw(" [↑/↓ or j/k] focus"),
        Span::raw(" [e] cycle view"),
        Span::raw(" [h] highlight"),
        Span::raw(" [q] quit"),
    ];
    let line = Line::from(vec![
        Span::styled(
            format!("View: {}", view_mode),
            Style::default().add_modifier(Modifier::BOLD),
        ),
        Span::raw("  "),
    ]);

    let lines = vec![line, Line::from(help)];
    Paragraph::new(lines)
        .block(Block::default().title("Status").borders(Borders::ALL))
        .wrap(Wrap { trim: true })
}

fn icon_for(icon: &str) -> &str {
    match icon {
        "circle" => "●",
        "square" => "■",
        _ => "•",
    }
}

fn color_from_name(name: &str) -> Color {
    match name.to_lowercase().as_str() {
        "red" => Color::Red,
        "green" => Color::Green,
        "blue" => Color::Blue,
        "cyan" => Color::Cyan,
        "magenta" | "purple" => Color::Magenta,
        "yellow" => Color::Yellow,
        _ => Color::White,
    }
}
