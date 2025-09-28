use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Clear, Paragraph, Wrap};
use ratatui::Frame;

use crate::app::{AppState, StatusKind, StatusMessage, ViewMode};

fn section_color(color: &str) -> Color {
    match color {
        "cyan" => Color::Cyan,
        "purple" => Color::Magenta,
        "yellow" => Color::Yellow,
        _ => Color::White,
    }
}

fn render_header(f: &mut Frame, area: Rect, app: &AppState) {
    let meta = &app.guide().meta;
    let text = vec![
        Line::from(vec![
            Span::styled(&meta.title, Style::default().add_modifier(Modifier::BOLD)),
            Span::raw("  "),
            Span::styled(&meta.subtitle, Style::default().fg(Color::Gray)),
        ]),
        Line::from(vec![
            Span::raw(&meta.version),
            Span::raw(" · "),
            Span::raw(&meta.context),
        ]),
    ];
    let paragraph =
        Paragraph::new(text).block(Block::default().borders(Borders::ALL).title("Field Guide"));
    f.render_widget(paragraph, area);
}

fn render_section<'a>(
    section: &'a crate::model::Section,
    index: usize,
    app: &'a AppState,
) -> Paragraph<'a> {
    let cache_section = app
        .cache()
        .section(index)
        .expect("cache matches guide sections");
    let mut lines = Vec::new();
    lines.push(Line::from(Span::styled(
        cache_section.header.as_str(),
        Style::default().add_modifier(Modifier::BOLD),
    )));
    if app.is_expanded(&section.id) {
        for entry in &cache_section.entries {
            lines.push(Line::from(Span::styled(
                format!("  • {}", entry.pattern),
                Style::default().fg(Color::Yellow),
            )));
            if matches!(app.view_mode(), ViewMode::Normal | ViewMode::Expanded) {
                lines.push(Line::from(Span::raw(format!("    {}", entry.description))));
            }
            if matches!(app.view_mode(), ViewMode::Expanded) {
                lines.push(Line::from(Span::raw(format!(
                    "    Signals: {}",
                    entry.signals.join(", ")
                ))));
                lines.push(Line::from(Span::raw(format!(
                    "    Protocol: {}",
                    entry.protocol
                ))));
            }
        }
    }
    Paragraph::new(lines)
        .style(Style::default().fg(section_color(&section.color)))
        .wrap(Wrap { trim: true })
}

fn render_body(f: &mut Frame, area: Rect, app: &AppState) {
    if app.guide().sections.is_empty() {
        let empty = Paragraph::new("No sections").block(Block::default().borders(Borders::ALL));
        f.render_widget(empty, area);
        return;
    }
    let section_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints(
            app.guide()
                .sections
                .iter()
                .map(|_| Constraint::Ratio(1, app.guide().sections.len() as u32))
                .collect::<Vec<_>>(),
        )
        // Layout grid follows Ratatui layout docs.
        // https://docs.rs/ratatui/latest/ratatui/layout/struct.Layout.html
        .split(area);
    for (index, section) in app.guide().sections.iter().enumerate() {
        let chunk = section_chunks[index];
        let mut paragraph = render_section(section, index, app);
        if app.focused_index() == index {
            paragraph = paragraph.block(Block::default().borders(Borders::ALL).title("Focused"));
        }
        if let Some(highlight) = app.highlight() {
            if highlight.section_id == section.id {
                paragraph = paragraph.style(Style::default().bg(Color::DarkGray));
                f.render_widget(Clear, chunk);
                f.render_widget(paragraph, chunk);
                continue;
            }
        }
        f.render_widget(paragraph, chunk);
    }
}

fn status_line(app: &AppState) -> String {
    let mut parts = Vec::new();
    let mode = format!("Mode: {}", app.view_mode().as_str());
    parts.push(mode);
    parts.push(if app.mcp_connected() {
        "MCP: connected".to_string()
    } else {
        "MCP: disconnected".to_string()
    });
    parts.join(" | ")
}

fn render_footer(f: &mut Frame, area: Rect, app: &AppState) {
    let help = "Keys: Space/Enter toggle · e cycle view · h highlight · q quit";
    let footer = Paragraph::new(vec![Line::from(help), Line::from(status_line(app))])
        .block(Block::default().borders(Borders::ALL).title("Status"));
    f.render_widget(footer, area);
}

fn render_status_overlay(f: &mut Frame, area: Rect, status: &StatusMessage) {
    let style = match status.kind {
        StatusKind::Info => Style::default().fg(Color::Green),
        StatusKind::Warn => Style::default().fg(Color::Yellow),
        StatusKind::Error => Style::default().fg(Color::Red),
    };
    let paragraph = Paragraph::new(Line::from(Span::styled(status.text.clone(), style)))
        .block(Block::default().borders(Borders::ALL).title("Last Event"));
    f.render_widget(Clear, area);
    f.render_widget(paragraph, area);
}

pub fn draw(f: &mut Frame, app: &AppState) {
    let layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(5),
            Constraint::Min(5),
            Constraint::Length(3),
        ])
        .split(f.area());
    render_header(f, layout[0], app);
    render_body(f, layout[1], app);
    render_footer(f, layout[2], app);
    if let Some(status) = app.status() {
        let area = Rect {
            x: layout[2].x,
            y: layout[2].y.saturating_sub(3),
            width: layout[2].width,
            height: 3,
        };
        render_status_overlay(f, area, status);
    }
}

// Crossterm cleanup is handled in main when leaving the alternate screen.
// https://docs.rs/crossterm/latest/crossterm/terminal/struct.EnterAlternateScreen.html
