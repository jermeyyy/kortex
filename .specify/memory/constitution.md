# Kortex MCP Server Constitution

## Core Principles

### I. Modern Python Standards
All code must adhere to modern Python standards and best practices:
- Python 3.10+ features and syntax
- Type hints for all function signatures and class attributes
- Async/await for I/O operations
- Dataclasses or Pydantic models for data structures
- Context managers for resource management
- F-strings for string formatting

### II. Design Principles (SOLID, KISS, DRY)
Code must follow established software engineering principles:

**SOLID Principles:**
- **Single Responsibility**: Each class/function has one clear purpose
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable for base types
- **Interface Segregation**: Clients shouldn't depend on unused interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

**Additional Principles:**
- **KISS (Keep It Simple, Stupid)**: Simplicity over cleverness
- **DRY (Don't Repeat Yourself)**: No code duplication
- **YAGNI (You Aren't Gonna Need It)**: Build what's needed now

### III. Documentation Requirements (NON-NEGOTIABLE)
Every code element must be documented:
- **All functions**: Complete pydoc strings with Args, Returns, Raises
- **All classes**: Docstring describing purpose and usage
- **All modules**: Module-level docstring explaining contents
- **Complex logic**: Inline comments for non-obvious code
- **Type hints**: All parameters and return values typed

**Pydoc Format:**
```python
def function_name(param: Type) -> ReturnType:
    """
    Brief one-line description.
    
    Longer description if needed, explaining behavior,
    edge cases, and important details.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When and why this is raised
    """
```

### IV. Modularity and Code Organization
Code must be organized into clear, focused modules:
- **Separation of Concerns**: MCP tools, KMP/CMP logic, utilities separated
- **Single Purpose Modules**: Each module has one clear responsibility
- **Clear Dependencies**: Explicit imports, avoid circular dependencies
- **Reusable Components**: Extract common functionality into utilities
- **Testable Units**: All modules independently testable

**Directory Structure:**
```
src/kortex_mcp/
├── __init__.py           # Package exports
├── server.py             # MCP server setup
├── tools/                # MCP tool implementations
│   ├── __init__.py
│   ├── kmp/              # KMP-specific tools
│   └── cmp/              # CMP-specific tools
├── analyzers/            # Code analysis logic
│   ├── __init__.py
│   ├── kmp_analyzer.py
│   └── cmp_analyzer.py
├── generators/           # Code generation logic
│   ├── __init__.py
│   ├── templates/
│   └── generator.py
├── models/               # Data models
│   └── __init__.py
└── utils/                # Utility functions
    └── __init__.py
```

### V. Testing Requirements
All code must be tested:
- **Unit Tests**: Every function/class has corresponding tests
- **Test Coverage**: Minimum 80% code coverage target
- **Async Tests**: Use pytest-asyncio for async code
- **Test Organization**: Mirror source structure in tests/
- **Fixtures**: Use pytest fixtures for setup/teardown
- **Mocking**: Mock external dependencies appropriately

### VI. FastMCP Best Practices
MCP server implementation must follow FastMCP standards:
- **Tool Registration**: Use `@mcp.tool()` decorator
- **Resource Registration**: Use `@mcp.resource()` decorator
- **Type Safety**: All tool parameters properly typed
- **Error Handling**: Graceful error handling in all tools
- **Documentation**: Tools must have clear descriptions
- **Async Pattern**: All tools implemented as async functions

### VII. KMP/CMP Domain Knowledge
Code must reflect accurate understanding of target technologies:
- **KMP Terminology**: Use correct terms (KMP, not KMM)
- **CMP Terminology**: Distinguish Compose Multiplatform from KMP
- **Source Sets**: Understand commonMain, androidMain, iosMain, etc.
- **Expect/Actual**: Know platform-specific implementation patterns
- **Build System**: Understand Gradle Kotlin DSL
- **Target Platforms**: Android, iOS, Desktop, Web (JS/Wasm)

## Code Quality Standards

### Static Analysis
- **Type Checking**: MyPy with strict mode
- **Linting**: Ruff for code quality
- **Formatting**: Black for consistent style
- **Import Sorting**: isort for organized imports

### Error Handling
- **Explicit Exceptions**: Raise specific exception types
- **Error Messages**: Clear, actionable error messages
- **Logging**: Use structured logging (not print statements)
- **Recovery**: Graceful degradation where possible

### Performance
- **Async I/O**: Use async for all I/O operations
- **Resource Management**: Proper cleanup with context managers
- **Lazy Loading**: Load resources only when needed
- **Caching**: Cache expensive computations appropriately

## Development Workflow

### Code Review Requirements
- All changes via pull requests
- Code must pass all tests
- Type checking must pass
- Documentation must be updated
- No commented-out code
- No debug print statements

### Git Practices
- **Commits**: Clear, descriptive commit messages
- **Branches**: Feature branches from main
- **History**: Clean, logical commit history
- **Tags**: Version tags for releases

### Testing Gates
- All tests must pass before merge
- Type checking must pass
- Linting must pass
- Coverage must not decrease

## Technology Constraints

### Required Dependencies
- **FastMCP**: >=2.11.0,<3.0.0 for MCP server
- **Python**: >=3.10 for modern features
- **pytest**: For testing framework
- **pytest-asyncio**: For async test support

### Prohibited Practices
- ❌ No global state (except MCP server instance)
- ❌ No monkey patching
- ❌ No eval() or exec()
- ❌ No mutable default arguments
- ❌ No bare except clauses
- ❌ No import *
- ❌ No print() in production code (use logging)

## Project-Specific Rules

### MCP Server Architecture
- Single `mcp` instance in `server.py`
- Tools organized by domain (KMP/CMP)
- Clear separation: tools → analyzers → models
- No business logic in tool functions (delegate to services)

### Naming Conventions
- **Files**: snake_case.py
- **Classes**: PascalCase
- **Functions**: snake_case
- **Constants**: UPPER_SNAKE_CASE
- **Private**: Prefix with underscore (_private)
- **Tools**: Descriptive verb_noun (analyze_kmp_project)

### Configuration Management
- No hardcoded values
- Environment variables for settings
- Configuration models with validation
- Sensible defaults provided

## Governance

### Constitution Authority
This constitution supersedes all other practices and guidelines. When in doubt, refer to this document.

### Compliance
- All code reviews must verify constitutional compliance
- Deviations must be documented and justified
- Technical debt must be tracked and addressed
- Complexity must be justified with clear benefit

### Amendment Process
1. Propose amendment with rationale
2. Document impact on existing code
3. Create migration plan if needed
4. Update this document
5. Communicate changes to team

### Enforcement
- Automated checks in CI/CD pipeline
- Manual review for architectural compliance
- Regular constitution review meetings
- Living document - update as needed

---

**Version**: 1.0.0  
**Ratified**: 2025-11-15  
**Last Amended**: 2025-11-15  
**Next Review**: 2026-02-15
