# Code Style and Conventions (The Constitution)

The project adheres to a strict **Constitution** that mandates modern Python standards and specific architectural gates.

## Language Standards (Article I)
- **Python 3.10+**: Usage of modern features (match statements, structural pattern matching) is required.
- **Type Hints**: **Mandatory** for all function signatures and class attributes.
- **Async/Await**: Required for all I/O operations.
- **Data Structures**: Use `dataclasses` or `Pydantic` models.
- **String Formatting**: F-strings only.

## SOLID Principles (Article II)
- **Single Responsibility**: Each module has one clear purpose.
- **Open/Closed**: Design extensible for new LSP servers without modification.
- **Dependency Inversion**: Depend on abstractions (interfaces), not concrete implementations.

## Documentation (Article III) - NON-NEGOTIABLE
- **Pydoc**: Every function must have a docstring with `Args`, `Returns`, and `Raises` sections.
- **Module/Class Docs**: Required for all modules and classes.
- **Inline Comments**: Required for complex logic.

## Modularity (Article IV)
- **Clear Separation**: Tools | LSP Managers | Analyzers | Models.
- **No Circular Dependencies**: Strictly enforced.
- **Independent Testing**: Each module must be testable in isolation.

## Testing (Article V)
- **Coverage**: Minimum **80%** target.
- **Framework**: `pytest` with `pytest-asyncio`.
- **Structure**: Test files must mirror the source directory structure.
- **Mocking**: All external dependencies (LSP servers, file I/O) must be mocked in unit tests.

## Configuration
- **Linting**: `ruff` is used with strict rules (checking `E`, `W`, `F`, `I`, `B`, `C4`, `UP`).
- **Type Checking**: `mypy` is configured in `strict` mode.
