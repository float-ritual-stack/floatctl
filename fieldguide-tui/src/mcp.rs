use anyhow::Result;
use crossbeam_channel::Sender;
use rmcp::{
    handler::server::{router::tool::ToolRouter, tool::parse_json_object, ServerHandler},
    model::{CallToolResult, JsonObject},
    serve_server, tool, tool_handler, tool_router, transport, ErrorData as McpError,
};
use serde::Deserialize;

use crate::app::UiCmd;

#[derive(Debug, Deserialize)]
pub struct ExpandParams {
    pub section_id: String,
    #[serde(default = "default_action")]
    pub action: String,
}

fn default_action() -> String {
    "toggle".to_string()
}

#[derive(Debug, Deserialize)]
pub struct ViewParams {
    pub mode: String,
}

#[derive(Debug, Deserialize)]
pub struct HighlightParams {
    #[serde(default)]
    pub section_id: Option<String>,
    #[serde(default)]
    pub duration_ms: Option<u64>,
}

#[derive(Debug, Clone)]
pub struct UiService {
    pub tx: Sender<UiCmd>,
    pub tool_router: ToolRouter<Self>,
}

impl UiService {
    pub fn new(tx: Sender<UiCmd>) -> Self {
        Self {
            tx,
            tool_router: Self::tool_router(),
        }
    }
}

#[tool_router]
impl UiService {
    /// MCP tool wiring follows rmcp server docs: https://docs.rs/rmcp/latest
    #[tool(description = "Expand, collapse, or toggle a section by id")]
    async fn expand_section(&self, args: JsonObject) -> Result<CallToolResult, McpError> {
        let params: ExpandParams = parse_json_object(args)?;
        let _ = self.tx.send(UiCmd::ExpandSection {
            section_id: params.section_id,
            action: params.action,
        });
        Ok(CallToolResult::success(Vec::new()))
    }

    #[tool(description = "Change the active view mode")]
    async fn change_view_mode(&self, args: JsonObject) -> Result<CallToolResult, McpError> {
        let params: ViewParams = parse_json_object(args)?;
        let _ = self.tx.send(UiCmd::ChangeViewMode { mode: params.mode });
        Ok(CallToolResult::success(Vec::new()))
    }

    #[tool(description = "Highlight a section for an optional duration")]
    async fn highlight_section(&self, args: JsonObject) -> Result<CallToolResult, McpError> {
        let params: HighlightParams = parse_json_object(args)?;
        let _ = self.tx.send(UiCmd::HighlightSection {
            section_id: params.section_id,
            duration_ms: params.duration_ms,
        });
        Ok(CallToolResult::success(Vec::new()))
    }
}

#[tool_handler(router = self.tool_router)]
impl ServerHandler for UiService {}

pub async fn run_mcp(tx: Sender<UiCmd>) -> Result<()> {
    let service = UiService::new(tx);
    // Serving over stdio per rmcp examples.
    // https://github.com/modelcontextprotocol/rust-sdk
    serve_server(service, transport::stdio()).await?;
    Ok(())
}
