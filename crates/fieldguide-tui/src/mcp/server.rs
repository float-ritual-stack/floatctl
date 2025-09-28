use std::sync::Arc;

use anyhow::Result;
use crossbeam_channel::Sender;
use log::{error, info, warn};
use rmcp::{
    handler::server::{router::tool::ToolRouter, tool::parse_json_object, ServerHandler},
    model::{CallToolResult, Content},
    serve_server, tool, tool_handler, tool_router, transport,
};
use serde::Deserialize;

use crate::app::{ExpandAction, StatusMessage, UiCmd, ViewMode};
use crate::error::UiError;

use super::api::{ChannelControlSink, ControlSink};

#[derive(Debug, Deserialize)]
struct ExpandParams {
    section_id: String,
    #[serde(default = "default_action")]
    action: String,
}

fn default_action() -> String {
    "toggle".to_string()
}

#[derive(Debug, Deserialize)]
struct ViewParams {
    mode: String,
}

#[derive(Debug, Deserialize)]
struct HighlightParams {
    #[serde(default)]
    section_id: Option<String>,
    #[serde(default)]
    duration_ms: Option<u64>,
}

#[derive(Clone)]
pub struct UiService {
    control: Arc<dyn ControlSink>,
    status_tx: Sender<UiCmd>,
    pub tool_router: ToolRouter<Self>,
}

impl UiService {
    pub fn new(control: ChannelControlSink) -> Self {
        let status_tx = control.sender();
        Self {
            control: Arc::new(control),
            status_tx,
            tool_router: Self::tool_router(),
        }
    }

    fn report_status(&self, message: StatusMessage) {
        if let Err(err) = self.status_tx.send(UiCmd::SetStatus(message)) {
            warn!("failed to send status to ui: {err}");
        }
    }

    fn report_error(&self, message: impl Into<String>) -> CallToolResult {
        let text = message.into();
        self.report_status(StatusMessage::error(text.clone()));
        CallToolResult::error(vec![Content::text(text)])
    }

    fn report_info(&self, message: impl Into<String>) {
        self.report_status(StatusMessage::info(message));
    }

    fn parse_action(&self, action: &str) -> Result<ExpandAction, CallToolResult> {
        ExpandAction::try_from_str(action).map_err(|err| self.report_error(err.to_string()))
    }

    fn parse_view_mode(&self, mode: &str) -> Result<ViewMode, CallToolResult> {
        ViewMode::try_from_str(mode).map_err(|err| self.report_error(err.to_string()))
    }

    fn validate_duration(&self, duration: Option<u64>) -> Result<Option<u64>, CallToolResult> {
        if let Some(ms) = duration {
            if ms == 0 {
                let err = UiError::InvalidDuration(ms);
                return Err(self.report_error(err.to_string()));
            }
        }
        Ok(duration)
    }
}

#[tool_router]
impl UiService {
    /// MCP tool wiring references the rmcp documentation for stdio transport usage.
    /// https://docs.rs/rmcp/latest/rmcp/handler/server/index.html
    #[tool(description = "Expand, collapse, or toggle a section by id")]
    async fn expand_section(
        &self,
        args: rmcp::model::JsonObject,
    ) -> Result<CallToolResult, rmcp::ErrorData> {
        let params: ExpandParams = parse_json_object(args)?;
        let action = match self.parse_action(&params.action) {
            Ok(action) => action,
            Err(result) => return Ok(result),
        };
        match self.control.expand_section(&params.section_id, action) {
            Ok(_) => {
                self.report_info(format!("Section {} -> {:?}", params.section_id, action));
                Ok(CallToolResult::success(Vec::new()))
            }
            Err(err) => {
                error!("expand_section failed: {err}");
                Ok(self.report_error(err.to_string()))
            }
        }
    }

    #[tool(description = "Change the active view mode")]
    async fn change_view_mode(
        &self,
        args: rmcp::model::JsonObject,
    ) -> Result<CallToolResult, rmcp::ErrorData> {
        let params: ViewParams = parse_json_object(args)?;
        let mode = match self.parse_view_mode(&params.mode) {
            Ok(mode) => mode,
            Err(result) => return Ok(result),
        };
        match self.control.change_view_mode(mode) {
            Ok(_) => {
                self.report_info(format!("View mode -> {}", mode.as_str()));
                Ok(CallToolResult::success(Vec::new()))
            }
            Err(err) => {
                error!("change_view_mode failed: {err}");
                Ok(self.report_error(err.to_string()))
            }
        }
    }

    #[tool(description = "Highlight a section for an optional duration")]
    async fn highlight_section(
        &self,
        args: rmcp::model::JsonObject,
    ) -> Result<CallToolResult, rmcp::ErrorData> {
        let params: HighlightParams = parse_json_object(args)?;
        let duration = match self.validate_duration(params.duration_ms) {
            Ok(duration) => duration,
            Err(result) => return Ok(result),
        };
        match self
            .control
            .highlight_section(params.section_id.as_deref(), duration)
        {
            Ok(_) => Ok(CallToolResult::success(Vec::new())),
            Err(err) => {
                error!("highlight_section failed: {err}");
                Ok(self.report_error(err.to_string()))
            }
        }
    }
}

#[tool_handler(router = self.tool_router)]
impl ServerHandler for UiService {}

pub async fn run_mcp(tx: Sender<UiCmd>) -> Result<()> {
    let control = ChannelControlSink::new(tx);
    let service = UiService::new(control);
    info!("starting MCP stdio server");
    if let Err(err) = serve_server(service, transport::stdio()).await {
        error!("mcp server error: {err}");
    }
    Ok(())
}
