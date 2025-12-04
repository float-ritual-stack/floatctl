use std::path::PathBuf;

use anyhow::{Context, Result};
use bbs_core::ViewType;
use bbs_sandbox::load_board;
use clap::Parser;

#[derive(Parser, Debug)]
#[command(about = "Showcase filter list interactions", author, version)]
struct Cli {
    #[arg(long)]
    data: Option<PathBuf>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let board = load_board(cli.data)?;

    let filter_view = board
        .tabs()
        .iter()
        .find_map(|tab| tab.find_view(ViewType::FilterList))
        .context("filter_list view not found")?;

    println!("Filter list :: {}", filter_view.label);
    let options = filter_view
        .data
        .get("options")
        .and_then(|value| value.as_array())
        .context("options array missing")?;

    for option in options {
        let label = option
            .get("label")
            .and_then(|value| value.as_str())
            .unwrap_or("<missing>");
        let count = option
            .get("count")
            .and_then(|value| value.as_i64())
            .unwrap_or(0);
        println!(" - {label} ({count})");
    }

    if let Some(selected) = filter_view
        .data
        .get("selected")
        .and_then(|value| value.as_str())
    {
        println!("\nSelected filter: {selected}");
    }

    if let Some(filters) = filter_view
        .data
        .get("filters")
        .and_then(|value| value.as_array())
    {
        if !filters.is_empty() {
            println!("Active tokens:");
            for token in filters {
                if let Some(token) = token.as_str() {
                    println!("   • {token}");
                }
            }
        }
    }

    Ok(())
}
