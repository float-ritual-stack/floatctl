use anyhow::Result;
use crossbeam_channel::Sender;
use rmcp::handler::server::router::tool::ToolRouter;
use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{
    CallToolResult, Content, Implementation, ProtocolVersion, ServerCapabilities, ServerInfo,
};
use rmcp::schemars::{self, JsonSchema};
use rmcp::service::ServiceExt;
use rmcp::transport::stdio;
use rmcp::{tool, tool_handler, tool_router, ErrorData as McpError};
use serde::Deserialize;

use crate::app::UiCmd;

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
struct ExpandParams {
    section_id: String,
    #[serde(default)]
    action: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
struct ViewParams {
    mode: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
struct HighlightParams {
    #[serde(default)]
    section_id: Option<String>,
    #[serde(default)]
    duration_ms: Option<u64>,
}

pub struct UiService {
    tx: Sender<UiCmd>,
    tool_router: ToolRouter<Self>,
}

impl UiService {
    pub fn new(tx: Sender<UiCmd>) -> Self {
        Self {
            tx,
            tool_router: Self::tool_router(),
        }
    }

    fn send_cmd(&self, cmd: UiCmd) -> Result<(), McpError> {
        self.tx
            .send(cmd)
            .map_err(|_| McpError::internal_error("UI channel closed", None))
    }
}

// Tool registration follows rmcp server macro guidance: https://docs.rs/rmcp/latest
#[tool_router]
impl UiService {
    #[tool(
        name = "expand_section",
        description = "Expand, collapse, or toggle a section"
    )]
    async fn expand_section(
        &self,
        Parameters(params): Parameters<ExpandParams>,
    ) -> Result<CallToolResult, McpError> {
        let action = params.action.unwrap_or_else(|| "toggle".to_string());
        self.send_cmd(UiCmd::ExpandSection {
            section_id: params.section_id,
            action,
        })?;
        Ok(CallToolResult::success(vec![Content::text("ok")]))
    }

    #[tool(name = "change_view_mode", description = "Change the view mode")]
    async fn change_view_mode(
        &self,
        Parameters(params): Parameters<ViewParams>,
    ) -> Result<CallToolResult, McpError> {
        self.send_cmd(UiCmd::ChangeViewMode { mode: params.mode })?;
        Ok(CallToolResult::success(vec![Content::text("ok")]))
    }

    #[tool(
        name = "highlight_section",
        description = "Highlight a section for the UI"
    )]
    async fn highlight_section(
        &self,
        Parameters(params): Parameters<HighlightParams>,
    ) -> Result<CallToolResult, McpError> {
        self.send_cmd(UiCmd::HighlightSection {
            section_id: params.section_id,
            duration_ms: params.duration_ms,
        })?;
        Ok(CallToolResult::success(vec![Content::text("ok")]))
    }
}

#[tool_handler]
impl rmcp::handler::server::ServerHandler for UiService {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            protocol_version: ProtocolVersion::LATEST,
            capabilities: ServerCapabilities::builder().enable_tools().build(),
            server_info: Implementation::from_build_env(),
            instructions: Some("Field Guide UI bridge exposing view controls".to_string()),
        }
    }
}

pub async fn run_mcp(tx: Sender<UiCmd>) -> Result<()> {
    let service = UiService::new(tx);
    let running = service
        .serve(stdio())
        .await
        .map_err(|err| anyhow::anyhow!(err))?;
    let _ = running
        .waiting()
        .await
        .map_err(|err| anyhow::anyhow!(err))?;
    Ok(())
}
