use std::path::PathBuf;

use anyhow::Result;
use bbs_sandbox::{load_board, print_tab_summary};
use clap::Parser;

#[derive(Parser, Debug)]
#[command(about = "Inspect the primary navigation tabs", author, version)]
struct Cli {
    /// Optional override for the board JSON file.
    #[arg(long)]
    data: Option<PathBuf>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let board = load_board(cli.data)?;
    print_tab_summary(&board);
    Ok(())
}
