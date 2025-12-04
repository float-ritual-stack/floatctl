mod architecture;
mod ast;
mod board;
mod boards;
mod boot;
mod concept_explorer;
mod daily;
mod devtools;
mod digest;
mod essays;
mod ghostline_viewer;
mod multisite_tiles;
mod projects_grid;
mod unknown;

use ratatui::layout::Rect;
use ratatui::Frame;

use crate::AppState;
use bbs_core::model::ViewId;

pub fn render(frame: &mut Frame, area: Rect, app: &AppState) {
    match app.current_view().id {
        ViewId::Boot => boot::render(frame, area, app),
        ViewId::Digest => digest::render(frame, area, app),
        ViewId::ProjectsGrid => projects_grid::render(frame, area, app),
        ViewId::Boards => boards::render(frame, area, app),
        ViewId::Board => board::render(frame, area, app),
        ViewId::Daily => daily::render(frame, area, app),
        ViewId::Essays => essays::render(frame, area, app),
        ViewId::Architecture => architecture::render(frame, area, app),
        ViewId::ConceptExplorer => concept_explorer::render(frame, area, app),
        ViewId::GhostlineViewer => ghostline_viewer::render(frame, area, app),
        ViewId::Devtools => devtools::render(frame, area, app),
        ViewId::Ast => ast::render(frame, area, app),
        ViewId::MultisiteTiles => multisite_tiles::render(frame, area, app),
        ViewId::Unknown => unknown::render(frame, area, app),
    }
}
