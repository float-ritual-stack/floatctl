use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::prelude::*;
use ratatui::text::Text;
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};

use crate::app::{App, ViewMode};

pub fn draw(frame: &mut Frame, app: &App) {
    // Layout guidance mirrors Ratatui layout docs. See https://docs.rs/ratatui/latest/ratatui/layout/struct.Layout.html
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(5),
            Constraint::Min(5),
            Constraint::Length(1),
        ])
        .split(frame.area());

    draw_header(frame, chunks[0], app);
    draw_sections(frame, chunks[1], app);
    draw_footer(frame, chunks[2], app);
}

fn draw_header(frame: &mut Frame, area: Rect, app: &App) {
    let meta = &app.guide.meta;
    let text = vec![
        Line::from(vec![
            Span::styled(&meta.title, Style::default().add_modifier(Modifier::BOLD)),
            Span::raw("  "),
            Span::styled(&meta.version, Style::default().fg(Color::Cyan)),
        ]),
        Line::from(Span::raw(&meta.subtitle)),
        Line::from(Span::styled(
            &meta.context,
            Style::default().fg(Color::DarkGray),
        )),
    ];

    let block = Block::default().borders(Borders::BOTTOM);
    frame.render_widget(
        Paragraph::new(text).block(block).wrap(Wrap { trim: true }),
        area,
    );
}

fn draw_sections(frame: &mut Frame, area: Rect, app: &App) {
    let section_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints(
            app.guide
                .sections
                .iter()
                .map(|_| Constraint::Min(3))
                .collect::<Vec<_>>(),
        )
        .split(area);

    let highlight_id = app
        .highlight
        .as_ref()
        .and_then(|hl| hl.section_id.clone())
        .or_else(|| {
            app.guide
                .sections
                .get(app.focused_index)
                .map(|s| s.id.clone())
        });

    for (index, section) in app.guide.sections.iter().enumerate() {
        let chunk = section_chunks.get(index).copied().unwrap_or(area);
        let is_focused = index == app.focused_index;
        let is_expanded = app.expanded.contains(&section.id);
        let is_highlighted = highlight_id
            .as_ref()
            .map(|target| target == &section.id)
            .unwrap_or(false)
            && app.highlight.is_some();

        let mut title_spans = vec![Span::styled(
            format!("{} {}", section.icon, section.title),
            Style::default()
                .fg(color_for(&section.color))
                .add_modifier(Modifier::BOLD),
        )];
        if is_focused {
            title_spans.push(Span::raw("  [focused]"));
        }
        if is_highlighted {
            title_spans.push(Span::styled(
                "  ⮞ highlighted",
                Style::default()
                    .fg(Color::Yellow)
                    .add_modifier(Modifier::BOLD),
            ));
        }

        let mut lines = vec![Line::from(title_spans)];

        if is_expanded {
            for entry in &section.entries {
                let entry_lines = match app.view_mode {
                    ViewMode::Normal => vec![
                        Line::from(Span::styled(
                            format!("• {}", entry.pattern),
                            Style::default().add_modifier(Modifier::BOLD),
                        )),
                        Line::from(Span::raw(format!("  {}", entry.description))),
                        Line::from(Span::styled(
                            format!("  Signals: {}", entry.signals.join(", ")),
                            Style::default().fg(Color::Gray),
                        )),
                    ],
                    ViewMode::Compact => vec![Line::from(Span::raw(format!(
                        "• {} — {}",
                        entry.pattern,
                        entry.signals.join(", ")
                    )))],
                    ViewMode::Expanded => vec![
                        Line::from(Span::styled(
                            format!("• {}", entry.pattern),
                            Style::default().add_modifier(Modifier::BOLD),
                        )),
                        Line::from(Span::raw(format!("  {}", entry.description))),
                        Line::from(Span::styled(
                            format!("  Signals: {}", entry.signals.join(", ")),
                            Style::default().fg(Color::Gray),
                        )),
                        Line::from(Span::styled(
                            format!("  Protocol: {}", entry.protocol),
                            Style::default().fg(Color::LightBlue),
                        )),
                    ],
                };
                lines.extend(entry_lines);
            }
        }

        let block = Block::default()
            .borders(Borders::ALL)
            .border_style(if is_focused {
                Style::default().fg(Color::White)
            } else {
                Style::default().fg(Color::DarkGray)
            });
        let paragraph = Paragraph::new(Text::from(lines))
            .block(block)
            .wrap(Wrap { trim: true });
        frame.render_widget(paragraph, chunk);
    }
}

fn draw_footer(frame: &mut Frame, area: Rect, app: &App) {
    let view = match app.view_mode {
        ViewMode::Normal => "Normal",
        ViewMode::Compact => "Compact",
        ViewMode::Expanded => "Expanded",
    };
    let text = vec![Line::from(vec![
        Span::raw("[Space/Enter] toggle | [e] cycle view | [h] highlight | [q] quit"),
        Span::raw("    "),
        Span::styled(format!("View: {}", view), Style::default().fg(Color::Cyan)),
    ])];

    // Terminal cleanup references crossterm alternate screen/raw mode docs.
    // https://docs.rs/crossterm/latest/crossterm/terminal/struct.EnterAlternateScreen.html
    frame.render_widget(Paragraph::new(text), area);
}

fn color_for(name: &str) -> Color {
    match name.to_ascii_lowercase().as_str() {
        "cyan" => Color::Cyan,
        "purple" => Color::Magenta,
        _ => Color::White,
    }
}
