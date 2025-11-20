# Kortex Project Onboarding Guide

## 1. Project Purpose
**Kortex** is an MCP (Model Context Protocol) server designed to act as an intelligent coding assistant for **Kotlin Multiplatform (KMP)** and **Compose Multiplatform (CMP)** projects. It bridges the gap between AI assistants and KMP codebases by providing:
- **LSP-Based Symbol Navigation**: Deep understanding of code structure across platforms (Android, iOS, Desktop).
- **Cross-Platform Awareness**: Handling of Kotlin, Swift, and Objective-C interop.
- **Project Onboarding**: Automatic detection and configuration of KMP/CMP projects.
- **Symbolic Editing**: Precise code manipulation using LSP symbols.

## 2. Tech Stack
- **Language**: Python 3.10+
- **Core Framework**: `fastmcp` (for MCP server implementation)
- **Testing**: `pytest`, `pytest-asyncio`, `pytest-cov`
- **Linting & Formatting**: `ruff`
- **Type Checking**: `mypy` (strict mode)
- **Package Management**: `uv` (recommended) or `pip`

## 3. Code Structure
The project source is located in `src/kortex_mcp/`. Key modules include:

- **`src/kortex_mcp/server.py`**: Entry point for the MCP server.
- **`src/kortex_mcp/tools/`**: Implementation of MCP tools exposed to the AI.
  - `lsp_tools.py`: Tools for symbol navigation and analysis.
  - `editing_tools.py`: Tools for code modification.
  - `project_tools.py`: Tools for project management and onboarding.
- **`src/kortex_mcp/lsp/`**: Logic for interacting with Language Servers (Kotlin, Swift, ObjC).
- **`src/kortex_mcp/analyzers/`**: Analyzers for KMP project structure and dependencies.
- **`src/kortex_mcp/models/`**: Pydantic/Dataclass models for internal data structures (Symbols, Projects, etc.).
- **`src/kortex_mcp/storage/`**: Persistence layer for memory and project state.
- **`tests/`**: Comprehensive test suite mirroring the source structure.
- **`examples/`**: Sample KMP projects for testing and demonstration.

## 4. Development Commands

### Installation
Using `uv` (recommended):
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```
Using `pip`:
```bash
pip install -e ".[dev]"
```

### Running the Server
```bash
python -m kortex_mcp.server
```

### Running Tests
Run all tests:
```bash
pytest
```
Run with coverage:
```bash
pytest --cov=src/kortex_mcp --cov-report=html
```

### Linting & Formatting
Check for linting errors:
```bash
ruff check src/ tests/
```
Format code:
```bash
ruff format src/ tests/
```

### Type Checking
Run static type analysis:
```bash
mypy src/kortex_mcp
```

## 5. Code Style & Conventions
- **Type Hints**: Mandatory for all functions and classes. The project uses `mypy` in strict mode.
- **Docstrings**: Public APIs must have **Google-style** docstrings.
- **Formatting**: Code must be formatted with `ruff` (which replaces black and isort).
- **Naming**: Standard Python naming conventions (snake_case for functions/variables, PascalCase for classes).

## 6. Contribution Guidelines
- **Process**: Create a feature branch -> Write tests -> Implement changes -> Ensure tests pass -> Submit PR.
- **Testing**: New features must include tests. Maintain high test coverage.
- **License**: Contributions are licensed under the project's license.
