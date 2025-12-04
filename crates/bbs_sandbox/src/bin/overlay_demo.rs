use std::path::PathBuf;

use anyhow::{Context, Result};
use bbs_core::ViewType;
use bbs_sandbox::load_board;
use clap::Parser;

#[derive(Parser, Debug)]
#[command(about = "Visualise overlay payloads", author, version)]
struct Cli {
    #[arg(long)]
    data: Option<PathBuf>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let board = load_board(cli.data)?;
    let overlay_view = board
        .tabs()
        .iter()
        .find_map(|tab| tab.find_view(ViewType::Overlay))
        .context("overlay view not found")?;

    println!("Overlay :: {}", overlay_view.label);
    let data = &overlay_view.data;
    let title = data
        .get("title")
        .and_then(|value| value.as_str())
        .unwrap_or("Overlay");
    let body = data
        .get("body")
        .and_then(|value| value.as_str())
        .unwrap_or_default();
    println!("Title: {title}\nBody: {body}\n");

    if let Some(actions) = data.get("actions").and_then(|value| value.as_array()) {
        println!("Actions:");
        for action in actions {
            if let Some(action) = action.as_str() {
                println!(" - {action}");
            }
        }
    }

    Ok(())
}
