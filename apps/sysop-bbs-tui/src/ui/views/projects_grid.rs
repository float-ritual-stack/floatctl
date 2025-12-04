use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Cell, List, ListItem, ListState, Paragraph, Row, Table};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{LayoutMode, Project, ProjectStatus, ViewData};

use super::super::shared::pills::pill;
use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::ProjectsGrid { projects, .. } = &app.current_view().kind {
        let layout = Layout::default()
            .direction(Direction::Vertical)
            .constraints([Constraint::Length(3), Constraint::Min(0)])
            .split(area);

        render_search(frame, layout[0], app);
        let filtered = app.filtered_projects(projects);
        match app.layout_mode() {
            LayoutMode::Grid => render_grid(frame, layout[1], &filtered, app),
            LayoutMode::List => render_list(frame, layout[1], &filtered, app),
        }
    }
}

fn render_search(frame: &mut Frame, area: Rect, app: &AppState) {
    let mut spans = vec![
        Span::styled("Layout: ", Theme::subtitle()),
        Span::styled(format!("{:?}", app.layout_mode()), Theme::header()),
        Span::raw("  "),
        Span::styled("Search: ", Theme::subtitle()),
        Span::styled(app.project_search(), Theme::header()),
    ];
    if app.search_active() {
        spans.push(Span::styled(" ▌", Theme::header()));
    }
    let paragraph =
        Paragraph::new(Line::from(spans)).block(Block::default().borders(Borders::BOTTOM));
    frame.render_widget(paragraph, area);
}

fn render_grid(frame: &mut Frame, area: Rect, projects: &[&Project], app: &AppState) {
    let columns = ((area.width as usize) / 30).max(1);
    let pct = (100 / columns).max(1) as u16;
    let column_constraints = vec![Constraint::Percentage(pct); columns];
    let mut rows = Vec::new();
    for (idx, chunk) in projects.chunks(columns).enumerate() {
        let cells: Vec<_> = chunk
            .iter()
            .map(|project| Cell::from(grid_cell(project)))
            .collect();
        let mut row = Row::new(cells).height(5);
        let start = idx * columns;
        let end = start + chunk.len();
        if (start..end).contains(&app.project_selection()) {
            row = row.style(Theme::highlight());
        }
        rows.push(row);
    }
    let table = Table::new(rows, column_constraints)
        .block(Block::default().title("Project grid").borders(Borders::ALL));
    frame.render_widget(table, area);
}

fn grid_cell(project: &Project) -> Vec<Line<'_>> {
    vec![
        Line::from(Span::styled(project.name.as_str(), Theme::header())),
        Line::from(project.description.as_str()),
        Line::from(tags_line(project)),
    ]
}

fn tags_line(project: &Project) -> Vec<Span<'static>> {
    project
        .tags
        .iter()
        .map(|tag| pill(tag.clone(), Theme::ACCENT))
        .collect()
}

fn render_list(frame: &mut Frame, area: Rect, projects: &[&Project], app: &AppState) {
    let items: Vec<_> = projects.iter().map(|project| list_item(project)).collect();
    let list = List::new(items)
        .block(Block::default().title("Project list").borders(Borders::ALL))
        .highlight_style(Theme::highlight());
    let mut state = ListState::default();
    state.select(Some(app.project_selection()));
    frame.render_stateful_widget(list, area, &mut state);
}

fn list_item(project: &Project) -> ListItem<'_> {
    let mut lines = Vec::new();
    lines.push(Line::from(vec![
        Span::styled(project.name.as_str(), Theme::header()),
        Span::raw(" "),
        Span::styled(status_label(project.status), Theme::subtitle()),
    ]));
    lines.push(Line::from(project.description.as_str()));
    lines.push(Line::from(tags_line(project)));
    ListItem::new(lines)
}

fn status_label(status: ProjectStatus) -> &'static str {
    match status {
        ProjectStatus::Exploring => "exploring",
        ProjectStatus::Active => "active",
        ProjectStatus::Maintenance => "maintenance",
        ProjectStatus::Archived => "archived",
    }
}
