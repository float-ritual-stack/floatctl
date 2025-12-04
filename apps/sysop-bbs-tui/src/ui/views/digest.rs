use ratatui::layout::Rect;
use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem};
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::{DigestEntry, ViewData};

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    if let ViewData::Digest { entries } = &app.current_view().kind {
        let items: Vec<_> = entries.iter().map(digest_item).collect();
        let list = List::new(items).block(Block::default().title("Digest").borders(Borders::ALL));
        frame.render_widget(list, area);
    }
}

fn digest_item(entry: &DigestEntry) -> ListItem<'_> {
    ListItem::new(vec![
        Line::from(format!("{} — {}", entry.timestamp, entry.headline)),
        Line::from(format!("   {}", entry.context)),
    ])
}
