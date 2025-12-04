use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::Tabs;

use crate::AppState;

use super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    let titles: Vec<_> = app
        .tabs()
        .iter()
        .map(|tab| Line::from(tab.label.clone()))
        .collect();

    let tabs = Tabs::new(titles)
        .block(ratatui::widgets::Block::default())
        .select(app.tab_index())
        .style(Theme::subtitle())
        .highlight_style(Theme::highlight())
        .divider(Span::styled("│", Theme::subtitle()));

    frame.render_widget(tabs, area);
}
