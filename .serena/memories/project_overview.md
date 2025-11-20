# Kortex Project Overview

## Core Mission
**Kortex** is a specialized **MCP (Model Context Protocol) Server** designed to act as an intelligent coding assistant for **Kotlin Multiplatform (KMP)** and **Compose Multiplatform (CMP)** projects. It bridges the gap between AI assistants and KMP codebases by providing deep, semantic understanding through LSP integration.

## Key Capabilities (User Stories)
The project is structured around 8 core user stories:
1.  **LSP-Based Symbol Navigation (P1)**: Precise navigation to classes, functions, and properties across source sets (`commonMain`, `androidMain`, `iosMain`).
2.  **Cross-Platform Code Understanding (P1)**: Understanding Kotlin/Swift/Objective-C interop and `expect`/`actual` relationships.
3.  **Project Onboarding (P1)**: Automatic detection and configuration of KMP/CMP projects, source sets, and dependencies.
4.  **Memory System (P2)**: Persisting project-specific knowledge (decisions, patterns, preferences) to `~/.kortex/memories`.
5.  **Interactive User Elicitation (P2)**: Proactively asking clarifying questions to resolve ambiguity in requirements.
6.  **Planning Mode (P2)**: Creating and refining structured feature specifications (SpecKit format) before implementation.
7.  **Editing Mode (P1)**: Precise, symbolic code modification (add/rename/delete) using LSP.
8.  **CMP UI Pattern Recognition (P3)**: Understanding Compose Multiplatform patterns (state, navigation, theming).

## Current Status (as of Nov 2025)
- **MVP Complete**: All P1 user stories (Navigation, Cross-Platform, Onboarding, Editing) are implemented.
- **P2 Complete**: Memory, Elicitation, and Planning modes are implemented.
- **Pending**: CMP UI Pattern Recognition (US8) and final Polish (Phase 11).

## Architecture & Design
The system is built on **FastMCP 2.0** and follows a modular, service-oriented architecture:

### Core Components (`src/kortex_mcp`)
- **Server (`server.py`)**: Entry point, manages lifecycle and tool registration.
- **LSP Layer (`lsp/`)**:
  - **`LSPManager`**: Orchestrates `LSPClient` instances (Kotlin, Swift, ObjC) as separate async subprocesses.
  - **`LSPClient`**: Handles JSON-RPC communication via stdio.
- **Analysis Layer (`analyzers/`)**:
  - **`KMPAnalyzer`**: Understands KMP project structure and `expect`/`actual` linking.
  - **`ProjectAnalyzer`**: Scans `build.gradle.kts` (using regex) to detect source sets.
- **Storage Layer (`storage/`)**:
  - **`MemoryStore`**: JSON-based persistence for project memories.
  - **`SpecStore`**: Markdown-based persistence for specifications.
- **Tools Layer (`tools/`)**:
  - **`LSPTools`**: Symbol search, navigation.
  - **`EditingTools`**: Symbolic code edits.
  - **`PlanningTools`**: Spec management.
  - **`ElicitationTools`**: Interactive questioning (`ask_user`).

### Key Technical Decisions
- **Async First**: All I/O operations use `async`/`await` to prevent blocking the MCP server.
- **Process Isolation**: LSP servers run as separate processes to ensure stability.
- **No AST for Gradle**: Gradle parsing uses regex for simplicity and speed, avoiding full AST complexity.
- **SpecKit Integration**: Planning mode produces Markdown specs compatible with the SpecKit workflow.
