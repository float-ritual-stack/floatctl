use std::collections::{BTreeSet, HashMap};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

use indexmap::IndexMap;
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;

const ENV_DATA_PATH: &str = "SYSOP_BBS_DATA";
const EMBEDDED_SEED: &str = include_str!("../data/seed.json");

/// High level structure describing the bulletin board state consumed by the TUI.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BbsData {
    pub title: String,
    #[serde(default)]
    pub summary: Option<String>,
    #[serde(default)]
    pub tabs: Vec<Tab>,
    #[serde(default)]
    pub keymaps: Vec<Keymap>,
    #[serde(default)]
    pub theme: Option<ThemeConfig>,
}

impl BbsData {
    /// Returns the embedded seed data packaged with the crate.
    pub fn embedded() -> Result<Self, BbsError> {
        serde_json::from_str(EMBEDDED_SEED).map_err(|source| BbsError::ParseEmbedded { source })
    }

    /// Resolves the effective theme, falling back to the default dark theme.
    pub fn resolve_theme(&self) -> Result<Theme, BbsError> {
        match &self.theme {
            Some(config) => Theme::from_config(config.clone()),
            None => Ok(Theme::default_dark()),
        }
    }

    /// Helper for consumers that only need the tab list.
    pub fn tabs(&self) -> &[Tab] {
        &self.tabs
    }

    /// Helper for consumers that need mutable tab access.
    pub fn tabs_mut(&mut self) -> &mut [Tab] {
        &mut self.tabs
    }

    /// Helper returning keymaps.
    pub fn keymaps(&self) -> &[Keymap] {
        &self.keymaps
    }
}

/// Load `BbsData` from the provided CLI path, the `SYSOP_BBS_DATA` environment variable,
/// or the embedded seed.
pub fn load_data(cli_path: Option<PathBuf>) -> Result<BbsData, BbsError> {
    if let Some(path) = cli_path {
        return load_from_path(&path);
    }

    if let Ok(env_path) = env::var(ENV_DATA_PATH) {
        let env_path = env_path.trim();
        if !env_path.is_empty() {
            return load_from_path(Path::new(env_path));
        }
    }

    BbsData::embedded()
}

fn load_from_path(path: &Path) -> Result<BbsData, BbsError> {
    let contents = fs::read_to_string(path).map_err(|source| BbsError::Read {
        path: path.to_path_buf(),
        source,
    })?;
    serde_json::from_str(&contents).map_err(|source| BbsError::Parse {
        path: path.to_path_buf(),
        source,
    })
}

/// A logical tab rendered in the primary navigation rail.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Tab {
    pub id: String,
    pub label: String,
    #[serde(default)]
    pub icon: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub pills: Vec<PillConfig>,
    pub views: Vec<View>,
}

impl Tab {
    /// Convenience accessor returning the first view of a particular kind.
    pub fn find_view(&self, view_type: ViewType) -> Option<&View> {
        self.views.iter().find(|view| view.kind.matches(view_type))
    }
}

/// A specific layout the TUI can render inside a tab.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct View {
    pub id: String,
    pub label: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(rename = "view")]
    pub kind: ViewKind,
    #[serde(default)]
    pub data: Value,
    #[serde(default)]
    pub pills: Vec<PillConfig>,
    #[serde(default)]
    pub keymap: Option<String>,
}

impl View {
    pub fn is(&self, view_type: ViewType) -> bool {
        self.kind.matches(view_type)
    }
}

/// Known view types supported by the renderer.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Hash, Ord, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ViewType {
    Tabs,
    Cards,
    FilterList,
    GridToggle,
    Router,
    Overlay,
    Markdown,
    Timeline,
    ActivityStream,
    Theme,
}

impl ViewType {
    pub const fn all() -> &'static [ViewType] {
        &[
            ViewType::Tabs,
            ViewType::Cards,
            ViewType::FilterList,
            ViewType::GridToggle,
            ViewType::Router,
            ViewType::Overlay,
            ViewType::Markdown,
            ViewType::Timeline,
            ViewType::ActivityStream,
            ViewType::Theme,
        ]
    }
}

impl std::fmt::Display for ViewType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let label = match self {
            ViewType::Tabs => "tabs",
            ViewType::Cards => "cards",
            ViewType::FilterList => "filter_list",
            ViewType::GridToggle => "grid_toggle",
            ViewType::Router => "router",
            ViewType::Overlay => "overlay",
            ViewType::Markdown => "markdown",
            ViewType::Timeline => "timeline",
            ViewType::ActivityStream => "activity_stream",
            ViewType::Theme => "theme",
        };
        f.write_str(label)
    }
}

/// Wraps both known and custom views in a single type for ergonomic dispatch.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(from = "ViewKindSerdeHelper", into = "ViewKindSerdeHelper")]
pub enum ViewKind {
    Known(ViewType),
    Custom(String),
}

impl ViewKind {
    pub fn matches(&self, view_type: ViewType) -> bool {
        matches!(self, ViewKind::Known(kind) if *kind == view_type)
    }
}

#[derive(Serialize, Deserialize)]
#[serde(untagged)]
enum ViewKindSerdeHelper {
    Known(ViewType),
    Custom(String),
}

impl From<ViewKindSerdeHelper> for ViewKind {
    fn from(value: ViewKindSerdeHelper) -> Self {
        match value {
            ViewKindSerdeHelper::Known(kind) => ViewKind::Known(kind),
            ViewKindSerdeHelper::Custom(custom) => ViewKind::Custom(custom),
        }
    }
}

impl From<ViewKind> for ViewKindSerdeHelper {
    fn from(value: ViewKind) -> Self {
        match value {
            ViewKind::Known(kind) => ViewKindSerdeHelper::Known(kind),
            ViewKind::Custom(custom) => ViewKindSerdeHelper::Custom(custom),
        }
    }
}

/// Pills represent concise status chips rendered inline with copy.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PillConfig {
    pub label: String,
    #[serde(default)]
    pub tone: PillTone,
    #[serde(default)]
    pub description: Option<String>,
}

impl PillConfig {
    pub fn render(&self, theme: &Theme) -> Line<'static> {
        render_pill(self, theme)
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, Eq, PartialEq, Default)]
#[serde(rename_all = "snake_case")]
pub enum PillTone {
    #[default]
    Neutral,
    Accent,
    Success,
    Warning,
    Danger,
    Info,
}

/// Keybinding metadata describing interactive affordances.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Keymap {
    pub context: String,
    #[serde(default)]
    pub description: Option<String>,
    pub actions: Vec<KeyAction>,
}

impl Keymap {
    pub fn action(&self, id: &str) -> Option<&KeyAction> {
        self.actions.iter().find(|action| action.id == id)
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct KeyAction {
    pub id: String,
    pub description: String,
    #[serde(default)]
    pub keys: Vec<String>,
    #[serde(default)]
    pub group: Option<String>,
    #[serde(default)]
    pub mode: Option<String>,
}

/// Declarative theme description loaded from JSON.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ThemeConfig {
    pub name: String,
    pub palette: PaletteConfig,
    #[serde(default)]
    pub pills: PillThemeConfig,
    #[serde(default)]
    pub accents: HashMap<String, String>,
}

/// Resolved theme with concrete Ratatui styles ready for rendering.
#[derive(Clone, Debug)]
pub struct Theme {
    pub name: String,
    pub palette: Palette,
    pub pills: PillTheme,
    pub accents: IndexMap<String, Color>,
}

impl Theme {
    pub fn from_config(config: ThemeConfig) -> Result<Self, BbsError> {
        let palette = Palette::from_config(config.palette)?;
        let pills = PillTheme::from_config(&config.pills)?;
        let mut accents = IndexMap::new();
        for (key, value) in config.accents {
            accents.insert(key, parse_color(&value)?);
        }
        Ok(Self {
            name: config.name,
            palette,
            pills,
            accents,
        })
    }

    pub fn default_dark() -> Self {
        let palette = Palette {
            background: Color::Rgb(15, 16, 20),
            foreground: Color::Rgb(224, 225, 232),
            primary: Color::Rgb(116, 192, 252),
            secondary: Color::Rgb(160, 174, 192),
            accent: Color::Rgb(255, 99, 195),
        };
        let pills = PillTheme {
            background: Color::Rgb(40, 45, 65),
            foreground: Color::Rgb(228, 231, 244),
            border: Color::Rgb(116, 192, 252),
            modifiers: vec![Modifier::BOLD],
        };
        Self {
            name: "nocturne".into(),
            palette,
            pills,
            accents: IndexMap::new(),
        }
    }

    pub fn default_light() -> Self {
        let palette = Palette {
            background: Color::Rgb(250, 250, 252),
            foreground: Color::Rgb(44, 47, 51),
            primary: Color::Rgb(47, 111, 183),
            secondary: Color::Rgb(90, 105, 120),
            accent: Color::Rgb(188, 80, 144),
        };
        let pills = PillTheme {
            background: Color::Rgb(228, 234, 255),
            foreground: Color::Rgb(47, 58, 94),
            border: Color::Rgb(47, 111, 183),
            modifiers: vec![Modifier::BOLD],
        };
        Self {
            name: "daybreak".into(),
            palette,
            pills,
            accents: IndexMap::new(),
        }
    }

    pub fn pill_style(&self) -> Style {
        self.pills.style()
    }

    pub fn pill_style_for_tone(&self, tone: PillTone) -> Style {
        self.pills.style_for_tone(tone, self)
    }

    pub fn background_style(&self) -> Style {
        Style::default()
            .bg(self.palette.background)
            .fg(self.palette.foreground)
    }

    pub fn accent_color(&self, key: &str) -> Option<Color> {
        self.accents.get(key).copied()
    }
}

#[derive(Clone, Debug)]
pub struct Palette {
    pub background: Color,
    pub foreground: Color,
    pub primary: Color,
    pub secondary: Color,
    pub accent: Color,
}

impl Palette {
    fn from_config(config: PaletteConfig) -> Result<Self, BbsError> {
        Ok(Self {
            background: parse_color(&config.background)?,
            foreground: parse_color(&config.foreground)?,
            primary: parse_color(&config.primary)?,
            secondary: parse_color(&config.secondary)?,
            accent: parse_color(&config.accent)?,
        })
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PaletteConfig {
    pub background: String,
    pub foreground: String,
    pub primary: String,
    pub secondary: String,
    pub accent: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PillThemeConfig {
    #[serde(default = "PillThemeConfig::default_background")]
    pub background: String,
    #[serde(default = "PillThemeConfig::default_foreground")]
    pub foreground: String,
    #[serde(default = "PillThemeConfig::default_border")]
    pub border: String,
    #[serde(default)]
    pub modifiers: Vec<String>,
}

impl Default for PillThemeConfig {
    fn default() -> Self {
        Self {
            background: Self::default_background(),
            foreground: Self::default_foreground(),
            border: Self::default_border(),
            modifiers: vec!["bold".into()],
        }
    }
}

impl PillThemeConfig {
    fn default_background() -> String {
        "#1d2538".into()
    }

    fn default_foreground() -> String {
        "#e4e7f4".into()
    }

    fn default_border() -> String {
        "#74c0fc".into()
    }
}

#[derive(Clone, Debug)]
pub struct PillTheme {
    pub background: Color,
    pub foreground: Color,
    pub border: Color,
    pub modifiers: Vec<Modifier>,
}

impl PillTheme {
    fn from_config(config: &PillThemeConfig) -> Result<Self, BbsError> {
        let modifiers = config
            .modifiers
            .iter()
            .filter_map(|modifier| match modifier.as_str() {
                "bold" => Some(Modifier::BOLD),
                "italic" => Some(Modifier::ITALIC),
                "underlined" => Some(Modifier::UNDERLINED),
                "dim" => Some(Modifier::DIM),
                "reversed" => Some(Modifier::REVERSED),
                _ => None,
            })
            .collect();
        Ok(Self {
            background: parse_color(&config.background)?,
            foreground: parse_color(&config.foreground)?,
            border: parse_color(&config.border)?,
            modifiers,
        })
    }

    fn style(&self) -> Style {
        let mut style = Style::default().bg(self.background).fg(self.foreground);
        for modifier in &self.modifiers {
            style = style.add_modifier(*modifier);
        }
        style
    }

    fn style_for_tone(&self, tone: PillTone, theme: &Theme) -> Style {
        let base = self.style();
        let accent = match tone {
            PillTone::Neutral => theme.palette.secondary,
            PillTone::Accent => theme.palette.accent,
            PillTone::Success => Color::Rgb(68, 207, 141),
            PillTone::Warning => Color::Rgb(255, 196, 107),
            PillTone::Danger => Color::Rgb(252, 129, 129),
            PillTone::Info => theme.palette.primary,
        };
        base.bg(accent)
    }
}

/// Render a pill using the supplied theme configuration.
pub fn render_pill(pill: &PillConfig, theme: &Theme) -> Line<'static> {
    let style = theme.pill_style_for_tone(pill.tone);
    let span = Span::styled(format!(" {} ", pill.label), style);
    Line::from(span)
}

fn parse_color(value: &str) -> Result<Color, BbsError> {
    let value = value.trim();
    if let Some(stripped) = value.strip_prefix('#') {
        if stripped.len() == 6 {
            if let Ok(rgb) = u32::from_str_radix(stripped, 16) {
                let r = ((rgb >> 16) & 0xFF) as u8;
                let g = ((rgb >> 8) & 0xFF) as u8;
                let b = (rgb & 0xFF) as u8;
                return Ok(Color::Rgb(r, g, b));
            }
        }
        return Err(BbsError::InvalidTheme(format!(
            "invalid hex colour: {value}"
        )));
    }

    let lowered = value.to_ascii_lowercase();
    let color = match lowered.as_str() {
        "black" => Color::Black,
        "red" => Color::Red,
        "green" => Color::Green,
        "yellow" => Color::Yellow,
        "blue" => Color::Blue,
        "magenta" => Color::Magenta,
        "cyan" => Color::Cyan,
        "gray" | "grey" => Color::Gray,
        "white" => Color::White,
        _ => {
            return Err(BbsError::InvalidTheme(format!(
                "unsupported colour: {value}"
            )))
        }
    };
    Ok(color)
}

/// Domain specific errors surfaced to the TUI layer.
#[derive(Debug, Error)]
pub enum BbsError {
    #[error("failed to read data file {path:?}")]
    Read {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },
    #[error("failed to parse JSON from {path:?}")]
    Parse {
        path: PathBuf,
        #[source]
        source: serde_json::Error,
    },
    #[error("failed to parse embedded seed data")]
    ParseEmbedded {
        #[source]
        source: serde_json::Error,
    },
    #[error("invalid theme configuration: {0}")]
    InvalidTheme(String),
    #[error("self-check failed: {0}")]
    SelfCheck(String),
}

/// A small harness used by demos and automated checks to ensure data coverage.
pub mod self_check {
    use super::*;

    pub const MIN_TABS: usize = 10;

    #[derive(Clone, Debug, Default)]
    pub struct SelfCheckReport {
        pub tab_count: usize,
        pub encountered: BTreeSet<ViewType>,
        pub custom_views: BTreeSet<String>,
    }

    impl SelfCheckReport {
        pub fn missing_views(&self, required: &[ViewType]) -> Vec<ViewType> {
            required
                .iter()
                .copied()
                .filter(|view| !self.encountered.contains(view))
                .collect()
        }

        pub fn has_custom(&self) -> bool {
            !self.custom_views.is_empty()
        }

        pub fn ensure_complete(&self, required: &[ViewType]) -> Result<(), BbsError> {
            self.ensure_complete_with_options(required, true)
        }

        pub fn ensure_complete_with_options(
            &self,
            required: &[ViewType],
            require_custom: bool,
        ) -> Result<(), BbsError> {
            if self.tab_count < MIN_TABS {
                return Err(BbsError::SelfCheck(format!(
                    "expected at least {MIN_TABS} tabs, found {}",
                    self.tab_count
                )));
            }

            let missing = self.missing_views(required);
            if !missing.is_empty() {
                let list = missing
                    .into_iter()
                    .map(|view| view.to_string())
                    .collect::<Vec<_>>()
                    .join(", ");
                return Err(BbsError::SelfCheck(format!(
                    "missing coverage for view types: {list}"
                )));
            }

            if require_custom && !self.has_custom() {
                return Err(BbsError::SelfCheck(
                    "expected at least one unsupported view to exercise fallback dispatch".into(),
                ));
            }

            Ok(())
        }
    }

    pub fn run(data: &BbsData) -> SelfCheckReport {
        let mut report = SelfCheckReport {
            tab_count: data.tabs.len(),
            ..Default::default()
        };
        for tab in &data.tabs {
            for view in &tab.views {
                match &view.kind {
                    ViewKind::Known(kind) => {
                        report.encountered.insert(*kind);
                    }
                    ViewKind::Custom(value) => {
                        report.custom_views.insert(value.clone());
                    }
                }
            }
        }
        report
    }

    pub fn run_from_path(path: &Path) -> Result<SelfCheckReport, BbsError> {
        let data = super::load_from_path(path)?;
        Ok(run(&data))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn embedded_seed_loads() {
        let data = BbsData::embedded().expect("seed data");
        assert!(!data.tabs.is_empty());
    }

    #[test]
    fn load_from_env() {
        let temp_dir = tempfile::tempdir().expect("tempdir");
        let path = temp_dir.path().join("bbs.json");
        fs::write(&path, EMBEDDED_SEED).expect("write seed");

        std::env::set_var(ENV_DATA_PATH, &path);
        let loaded = load_data(None).expect("load from env");
        assert!(!loaded.tabs.is_empty());
        std::env::remove_var(ENV_DATA_PATH);
    }
}
