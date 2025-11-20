# Contributing to Kortex

Thank you for your interest in contributing to Kortex! We welcome contributions from the community to help make this the best AI coding assistant for Kotlin Multiplatform.

## Development Setup

1. **Prerequisites**:
   - Python 3.10+
   - `uv` or `pip`
   - Kotlin Language Server (for testing LSP integration)

2. **Clone and Install**:
   ```bash
   git clone https://github.com/jermeyyy/kortex.git
   cd kortex
   pip install -e ".[dev]"
   ```

3. **Run Tests**:
   ```bash
   pytest tests/
   ```

## Code Style

We follow strict code style guidelines to ensure maintainability:

- **Type Hints**: All functions and classes must have type hints.
- **Docstrings**: All public APIs must have Google-style docstrings.
- **Linting**: We use `ruff` for linting and formatting.
  ```bash
  ruff check src/
  ruff format src/
  ```
- **Type Checking**: We use `mypy` for static type checking.
  ```bash
  mypy src/kortex_mcp
  ```

## Pull Request Process

1. Create a new branch for your feature or fix.
2. Write tests for your changes.
3. Ensure all tests pass and coverage is maintained.
4. Submit a Pull Request with a clear description of your changes.

## Project Structure

- `src/kortex_mcp/`: Source code
  - `tools/`: MCP tool implementations
  - `lsp/`: Language Server Protocol integration
  - `analyzers/`: Code analysis logic
  - `models/`: Data models
  - `storage/`: Persistence layer
- `tests/`: Test suite

## License

By contributing, you agree that your contributions will be licensed under the project's license.
