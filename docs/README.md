# Kortex MCP Server User Guide

Kortex is an advanced AI coding assistant for Kotlin Multiplatform (KMP) and Compose Multiplatform (CMP) projects. It integrates with the Language Server Protocol (LSP) to provide precise, symbol-aware code navigation, editing, and analysis.

## Installation

### Prerequisites

- Python 3.10 or higher
- Kotlin Language Server (for Kotlin support)
- SourceKit-LSP (for Swift/Objective-C support, optional)
- `uv` or `pip` for package management

### Installing Kortex

1. Clone the repository:
   ```bash
   git clone https://github.com/jermeyyy/kortex.git
   cd kortex
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Configure Language Servers:
   - Ensure `kotlin-language-server` is in your PATH.
   - Ensure `sourcekit-lsp` is in your PATH (if on macOS/Linux).

## Usage

### Starting the Server

You can run Kortex as a FastMCP server:

```bash
# Using python module
python -m kortex_mcp.server

# Using fastmcp CLI (dev mode)
fastmcp dev src/kortex_mcp/server.py
```

### Connecting to Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kortex": {
      "command": "python",
      "args": ["-m", "kortex_mcp.server"]
    }
  }
}
```

## Features

### 1. Project Onboarding
Kortex automatically detects KMP/CMP project structures, source sets, and dependencies.
- **Tool**: `onboard_project`
- **Usage**: "Analyze this project" or "Onboard the current project"

### 2. Symbol Navigation (LSP)
Search for classes, functions, and variables across your codebase.
- **Tools**: `search_symbols`, `get_definition`, `get_references`
- **Usage**: "Where is the Repository class defined?", "Find usages of getUser"

### 3. Cross-Platform Understanding
Navigate between Kotlin (Common/Android) and Swift/Objective-C (iOS) code.
- **Tools**: `cross_language_symbol_lookup`, `navigate_expect_actual`
- **Usage**: "How is this Kotlin repository used in Swift?", "Go to the actual implementation of Platform"

### 4. Code Editing
Perform precise, symbol-aware code modifications.
- **Tools**: `add_method`, `rename_symbol`
- **Usage**: "Add a validate method to the User class", "Rename fetchUser to fetchUserProfile"

### 5. Memory System
Kortex remembers project-specific patterns, decisions, and preferences.
- **Tools**: `store_memory`, `query_memories`
- **Usage**: "Remember that we use Koin for DI", "What are the project conventions for error handling?"

### 6. Planning Mode
Create and refine specifications before implementation.
- **Tools**: `create_spec`, `refine_spec`
- **Usage**: "Let's plan the offline sync feature", "Create a spec for user authentication"

### 7. User Elicitation
Kortex asks clarifying questions when requirements are ambiguous.
- **Tools**: `ask_open_ended`, `ask_single_select`
- **Usage**: Kortex will automatically ask you questions when needed.

> **Note**: User elicitation requires the MCP client to support the elicitation capability (introduced in MCP spec and FastMCP 2.10.0+). If your client doesn't support elicitation (such as older versions of Claude Desktop), the tools will return a helpful message indicating the limitation instead of failing. In this case, you should provide the information directly in your request.

## Troubleshooting

### LSP Server Issues
If symbol search isn't working:
1. Check if `kotlin-language-server` is running.
2. Check Kortex logs for LSP connection errors.
3. Restart the Kortex server.

### Memory Issues
Memories are stored in `.kortex/memories/` in your project root. You can manually inspect these JSON files if needed.
