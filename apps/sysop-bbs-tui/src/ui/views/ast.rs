use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{AstNode, ViewData};

use super::super::shared::theme::Theme;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Ast { nodes } = &app.current_view().kind {
        let items: Vec<_> = nodes.iter().map(ast_item).collect();
        let list =
            List::new(items).block(Block::default().title("Parser AST").borders(Borders::ALL));
        frame.render_widget(list, area);
    }
}

fn ast_item(node: &AstNode) -> ListItem<'_> {
    let indent = "  ".repeat(node.depth);
    ListItem::new(vec![Line::from(vec![
        Span::raw(format!("{}{}", indent, node.label)),
        Span::raw("  "),
        Span::styled(node.details.as_str(), Theme::subtitle()),
    ])])
}
