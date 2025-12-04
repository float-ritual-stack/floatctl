use std::path::PathBuf;

use anyhow::{Context, Result};
use bbs_core::ViewType;
use bbs_sandbox::load_board;
use clap::Parser;

#[derive(Parser, Debug)]
#[command(about = "Inspect grid toggle layout", author, version)]
struct Cli {
    #[arg(long)]
    data: Option<PathBuf>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let board = load_board(cli.data)?;
    let grid_view = board
        .tabs()
        .iter()
        .find_map(|tab| tab.find_view(ViewType::GridToggle))
        .context("grid_toggle view not found")?;

    println!("Grid toggle :: {}", grid_view.label);
    if let Some(columns) = grid_view
        .data
        .get("columns")
        .and_then(|value| value.as_array())
    {
        let labels = columns
            .iter()
            .filter_map(|value| value.as_str())
            .collect::<Vec<_>>()
            .join(" | ");
        println!("Columns: {labels}");
    }

    if let Some(rows) = grid_view
        .data
        .get("rows")
        .and_then(|value| value.as_array())
    {
        println!("Rows:");
        for row in rows {
            if let Some(row) = row.as_array() {
                let cells = row
                    .iter()
                    .filter_map(|value| value.as_str())
                    .collect::<Vec<_>>()
                    .join(" | ");
                println!("  {cells}");
            }
        }
    }

    if let Some(toggles) = grid_view
        .data
        .get("toggles")
        .and_then(|value| value.as_array())
    {
        println!("\nToggles:");
        for toggle in toggles {
            let label = toggle
                .get("label")
                .and_then(|value| value.as_str())
                .unwrap_or("<toggle>");
            let active = toggle
                .get("active")
                .and_then(|value| value.as_bool())
                .unwrap_or(false);
            println!("  [{:>3}] {label}", if active { "on" } else { "off" });
        }
    }

    Ok(())
}
