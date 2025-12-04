use std::path::PathBuf;

use anyhow::{Context, Result};
use bbs_core::ViewType;
use bbs_sandbox::load_board;
use clap::Parser;

#[derive(Parser, Debug)]
#[command(about = "Render card stack metadata", author, version)]
struct Cli {
    #[arg(long)]
    data: Option<PathBuf>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let board = load_board(cli.data)?;
    let cards_view = board
        .tabs()
        .iter()
        .find_map(|tab| tab.find_view(ViewType::Cards))
        .context("cards view not found")?;

    println!("Card deck :: {}", cards_view.label);
    let cards = cards_view
        .data
        .get("cards")
        .and_then(|value| value.as_array())
        .context("cards array missing")?;

    for card in cards {
        let title = card
            .get("title")
            .and_then(|value| value.as_str())
            .unwrap_or("Untitled");
        let status = card
            .get("status")
            .and_then(|value| value.as_str())
            .unwrap_or("unknown");
        println!("- {title} [{status}]");
        if let Some(body) = card.get("body").and_then(|value| value.as_str()) {
            println!("  {body}");
        }
        if let Some(meta) = card.get("meta").and_then(|value| value.as_array()) {
            let meta = meta
                .iter()
                .filter_map(|value| value.as_str())
                .collect::<Vec<_>>()
                .join(", ");
            if !meta.is_empty() {
                println!("  meta: {meta}");
            }
        }
    }

    Ok(())
}
