# Task Completion Workflow

When a task is completed, ensure the following steps are taken before considering the work done, adhering to the project's strict Constitution and Validation Checklist:

## Pre-Implementation
1.  **Write Tests First**: Tests MUST be written and FAIL before implementation begins (TDD).
2.  **Define Models**: Create data models with full type hints before logic.

## Implementation & Verification
1.  **Format Code**: Run `ruff format src/ tests/` to ensure code style compliance.
2.  **Lint Code**: Run `ruff check src/ tests/` to catch any linting errors.
3.  **Type Check**: Run `mypy src/kortex_mcp` to verify type safety (Strict Mode).
4.  **Run Tests**: Run `pytest` to ensure no regressions were introduced.
5.  **Verify Documentation**: Ensure all new functions/classes have Google-style docstrings with `Args`, `Returns`, and `Raises`.
6.  **Check Coverage**: Ensure new code has tests and maintains the 80% coverage target.

## Final Check
- **Zero Errors**: No mypy errors, no ruff errors, no failing tests.
- **Independent Validation**: Verify the feature works in isolation (e.g., using a sample project).
