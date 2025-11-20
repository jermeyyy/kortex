# Suggested Development Commands

## Installation
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

## Running the Server
```bash
python -m kortex_mcp.server
```

## Running Tests
Run all tests:
```bash
pytest
```
Run with coverage:
```bash
pytest --cov=src/kortex_mcp --cov-report=html
```

## Linting & Formatting
Check for linting errors:
```bash
ruff check src/ tests/
```
Format code:
```bash
ruff format src/ tests/
```

## Type Checking
Run static type analysis:
```bash
mypy src/kortex_mcp
```
