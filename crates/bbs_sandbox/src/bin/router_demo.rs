use std::path::PathBuf;

use anyhow::Result;
use bbs_sandbox::{describe_dispatch, load_board, run_self_check, run_self_check_from_path};
use clap::Parser;

#[derive(Parser, Debug, Clone)]
#[command(about = "Demonstrate router dispatch and self-checks", author, version)]
struct Cli {
    /// Optional data file for the primary board.
    #[arg(long)]
    data: Option<PathBuf>,
    /// Alternate dataset used for dispatch coverage checks.
    #[arg(long)]
    dynamic: Option<PathBuf>,
    /// Run the automated coverage self-checks.
    #[arg(long)]
    check: bool,
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    if cli.check {
        let board = load_board(cli.data.clone())?;
        let seed_report = run_self_check(&board, false)?;
        println!(
            "Seed dataset: {} tabs, {} known views",
            seed_report.tab_count,
            seed_report.encountered.len()
        );

        let dynamic_path = cli
            .dynamic
            .unwrap_or_else(|| PathBuf::from("testdata/dynamic.json"));
        let dynamic_report = run_self_check_from_path(dynamic_path.clone(), true)?;
        println!(
            "Dynamic dataset: {} tabs, {} known views, custom {:?}",
            dynamic_report.tab_count,
            dynamic_report.encountered.len(),
            dynamic_report.custom_views
        );
        println!("Self-check suite completed successfully.");
        return Ok(());
    }

    let board = load_board(cli.data)?;
    describe_dispatch(&board);
    Ok(())
}
