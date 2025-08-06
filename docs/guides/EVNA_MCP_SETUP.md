# Evna-MCP Setup Guide 🧠

## Quick Setup

### 1. **Check Status**
```bash
floatctl mcp status --claude-desktop
```

### 2. **Install/Reinstall** (if needed)
```bash
# First time install
floatctl mcp install --claude-desktop

# Update after changes
floatctl mcp reinstall
```

### 3. **Test Locally**
```bash
floatctl mcp test
```

### 4. **Restart Claude Desktop**
After install/reinstall, restart Claude Desktop to activate the enhanced Evna-MCP server.

## Available Commands

| Command | Purpose |
|---------|---------|
| `floatctl mcp status --claude-desktop` | Check installation status and available tools |
| `floatctl mcp install --claude-desktop` | Install Evna-MCP to Claude Desktop |
| `floatctl mcp reinstall` | Update/reinstall after changes |
| `floatctl mcp uninstall --claude-desktop` | Remove from Claude Desktop |
| `floatctl mcp test` | Test enhanced features locally |
| `floatctl mcp serve` | Run server manually (for debugging) |

## What Gets Installed

The command configures Claude Desktop to run:
```bash
uv run --project /path/to/floatctl-py python -m floatctl.mcp_server
```

This gives Claude access to your enhanced Evna-MCP with:

### 🛠️ **Core Tools**
- `smart_pattern_processor` - Universal :: pattern handler
- `get_prompt` - Access your prompt library
- `smart_chroma_query` - Protected ChromaDB access
- `surface_recent_context` - "What was I working on?"

### 📊 **Analytics & Optimization**
- `get_usage_insights` - Usage patterns and suggestions
- `check_boundary_status` - Boundary violation detection

### 📚 **Your Prompt Library**
- `consciousness_archaeology` - Deep pattern analysis
- `ritual_computing` - Design consciousness protocols
- `neuroqueer_analysis` - Neurodivergent-friendly analysis
- `shack_not_cathedral` - Strip complexity, focus utility
- `context_crunch` - Compress context when hitting limits

## Usage in Claude

Once installed and Claude Desktop is restarted, you can:

### **Capture Any Pattern**
```
smart_pattern_processor("eureka:: The consciousness archaeology pattern works! [concept:: pattern-dispatch] [project:: evna-mcp]")
```

### **Get Your Prompts**
```
get_prompt("consciousness")  # Returns consciousness_archaeology prompt
get_prompt("shack")         # Returns shack_not_cathedral prompt
```

### **Smart Context Queries**
```
smart_chroma_query("ritual computing patterns", collection="float_highlights")
```

### **Surface Recent Work**
```
surface_recent_context(hours=6)  # "What was I working on?"
```

## Troubleshooting

### **Server Not Showing Up**
1. Check status: `floatctl mcp status --claude-desktop`
2. Reinstall: `floatctl mcp reinstall`
3. Restart Claude Desktop

### **Test Locally First**
```bash
floatctl mcp test
```

### **Manual Server Run** (for debugging)
```bash
floatctl mcp serve
```

## PostHog/Telemetry Issues Fixed

The enhanced server includes aggressive telemetry suppression to eliminate the JSON errors you were seeing. No more PostHog noise! 🎉

---

**Your context concierge is ready!** 🚀