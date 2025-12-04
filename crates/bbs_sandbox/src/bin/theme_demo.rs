use std::path::PathBuf;

use anyhow::Result;
use bbs_core::Theme;
use bbs_sandbox::{load_board, preview_pill};
use clap::Parser;

#[derive(Parser, Debug)]
#[command(
    about = "Demonstrate theme helpers and pill rendering",
    author,
    version
)]
struct Cli {
    #[arg(long)]
    data: Option<PathBuf>,
    #[arg(long)]
    light: bool,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let board = load_board(cli.data)?;
    let theme = if cli.light {
        Theme::default_light()
    } else {
        board.resolve_theme()?
    };

    println!("Theme: {}", theme.name);
    println!(
        "Palette => background {:?}, foreground {:?}, primary {:?}, secondary {:?}, accent {:?}",
        theme.palette.background,
        theme.palette.foreground,
        theme.palette.primary,
        theme.palette.secondary,
        theme.palette.accent
    );

    if !theme.accents.is_empty() {
        println!("Accents:");
        for (key, colour) in &theme.accents {
            println!(" - {key}: {:?}", colour);
        }
    }

    println!("\nPill preview:");
    preview_pill("Demo", &theme);

    Ok(())
}
