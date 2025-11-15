# Implementation Plan: Kortex MCP Server - KMP/CMP Coding Assistant

**Branch**: `main` | **Date**: 2025-11-15 | **Spec**: `.specify/specs/001-kortex-mcp-server.md`
**Input**: Build coding assistant similar to Serena with LSP integration, project onboarding, memories, symbolic search, user elicitation, and planning/editing modes for KMP/CMP projects

## Summary

Kortex is an MCP server that provides AI coding assistants with advanced capabilities for working with Kotlin Multiplatform (KMP) and Compose Multiplatform (CMP) projects. It combines Serena's LSP-based symbolic code analysis with SpecKit's specification-driven development workflow, enhanced with KMP/CMP domain knowledge and interactive user elicitation.

**Core Technical Approach**:
- FastMCP 2.0 for MCP server implementation with async tool support
- Language Server Protocol (LSP) integration for Kotlin, Swift, and Objective-C
- Async/await pattern throughout for non-blocking operations
- Modular architecture following SOLID principles
- Type-safe dataclasses for all data models
- Comprehensive pydoc documentation for all public APIs

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: 
- FastMCP >=2.11.0,<3.0.0 (MCP server framework)
- (TBD in Phase 0: LSP client library selection)
**Storage**: File-based (JSON for memories/project config, Markdown for specifications)  
**Testing**: pytest with pytest-asyncio for async test support  
**Target Platform**: Cross-platform (macOS, Linux, Windows) - runs as MCP server  
**Project Type**: Single project (MCP server with multiple subsystems)  
**Performance Goals**: 
- Project onboarding: <30 seconds for standard KMP projects
- Symbol search: <2 seconds for 10,000 symbols
- LSP operations: <1 second for 90% of requests
**Constraints**: 
- Must handle LSP server crashes gracefully with auto-restart
- Memory efficient for large codebases (50,000+ LOC)
- Non-blocking async operations for all I/O
**Scale/Scope**: 
- Support 3 language servers initially (Kotlin, Swift, Objective-C)
- Handle projects with 50,000+ lines of code
- Maintain performance with 10+ concurrent tool operations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Modern Python Standards (Article I)
- [ ] Using Python 3.10+ features (match statements, structural pattern matching)?
- [ ] All functions/classes have type hints?
- [ ] Using async/await for I/O operations?
- [ ] Using dataclasses or Pydantic for data structures?

### ✅ SOLID Principles (Article II)
- [ ] Single Responsibility: Each module has one clear purpose?
- [ ] Open/Closed: Design extensible for new LSP servers without modification?
- [ ] Dependency Inversion: Depending on abstractions (interfaces) not concrete implementations?

### ✅ Documentation Requirements (Article III) - NON-NEGOTIABLE
- [ ] Every function has pydoc with Args, Returns, Raises?
- [ ] Every class has descriptive docstring?
- [ ] Every module has module-level docstring?

### ✅ Modularity (Article IV)
- [ ] Clear separation: MCP tools | LSP managers | Analyzers | Models?
- [ ] No circular dependencies?
- [ ] Each module independently testable?

### ✅ Testing Requirements (Article V)
- [ ] Target 80%+ code coverage?
- [ ] Async tests using pytest-asyncio?
- [ ] Test structure mirrors source structure?

## Project Structure

### Documentation (this feature)

```text
.specify/
├── specs/
│   └── 001-kortex-mcp-server.md    # Feature specification
├── memory/
│   └── constitution.md              # Project constitution
└── templates/
    ├── spec-template.md
    └── plan-template.md

specs/001-kortex-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0: LSP library analysis, architecture patterns
├── data-model.md        # Phase 1: Core entities and relationships
├── quickstart.md        # Phase 1: Key validation scenarios
└── contracts/           # Phase 1: MCP tool contracts
    ├── lsp_tools.md
    ├── memory_tools.md
    ├── planning_tools.md
    └── elicitation_tools.md
```

### Source Code (repository root)

```text
src/kortex_mcp/
├── __init__.py                      # Package exports
├── server.py                        # FastMCP server setup and lifecycle
│
├── tools/                           # MCP tool implementations
│   ├── __init__.py
│   ├── base.py                      # Base tool class with common functionality
│   ├── lsp_tools.py                 # Symbol search, navigation, references
│   ├── project_tools.py             # Project onboarding and analysis
│   ├── memory_tools.py              # Memory CRUD operations
│   ├── planning_tools.py            # Specification and planning mode
│   ├── editing_tools.py             # Code modification tools
│   └── elicitation_tools.py         # ask_user tool implementation
│
├── lsp/                             # LSP integration layer
│   ├── __init__.py
│   ├── client.py                    # Base LSP client with async communication
│   ├── manager.py                   # LSP server lifecycle management
│   ├── kotlin_server.py             # Kotlin LSP server integration
│   ├── swift_server.py              # Swift (SourceKit-LSP) integration
│   ├── objc_server.py               # Objective-C (clangd) integration
│   └── types.py                     # LSP type definitions and conversions
│
├── analyzers/                       # Code analysis logic
│   ├── __init__.py
│   ├── base_analyzer.py             # Base analyzer interface
│   ├── kmp_analyzer.py              # KMP-specific analysis (source sets, expect/actual)
│   ├── cmp_analyzer.py              # CMP-specific analysis (composables, navigation)
│   └── project_analyzer.py          # Project structure analysis
│
├── models/                          # Data models
│   ├── __init__.py
│   ├── project.py                   # Project, SourceSet models
│   ├── symbol.py                    # Symbol, CodeLocation models
│   ├── memory.py                    # Memory, MemoryCategory models
│   ├── specification.py             # Specification, UserStory, Requirement models
│   └── lsp.py                       # LSP-specific models
│
├── storage/                         # Persistence layer
│   ├── __init__.py
│   ├── memory_store.py              # Memory storage (JSON)
│   ├── project_store.py             # Project configuration storage
│   └── spec_store.py                # Specification storage (Markdown)
│
└── utils/                           # Utility functions
    ├── __init__.py
    ├── file_utils.py                # File operations, path handling
    ├── gradle_parser.py             # Gradle build file parsing
    ├── logging.py                   # Logging configuration
    └── async_utils.py               # Async helpers

tests/
├── __init__.py
├── conftest.py                      # Pytest fixtures and configuration
│
├── test_tools/                      # Tool tests
│   ├── test_lsp_tools.py
│   ├── test_project_tools.py
│   ├── test_memory_tools.py
│   ├── test_planning_tools.py
│   └── test_elicitation_tools.py
│
├── test_lsp/                        # LSP integration tests
│   ├── test_client.py
│   ├── test_manager.py
│   ├── test_kotlin_server.py
│   └── test_swift_server.py
│
├── test_analyzers/                  # Analyzer tests
│   ├── test_kmp_analyzer.py
│   ├── test_cmp_analyzer.py
│   └── test_project_analyzer.py
│
├── test_models/                     # Model tests
│   └── test_models.py
│
├── test_storage/                    # Storage tests
│   ├── test_memory_store.py
│   └── test_spec_store.py
│
└── fixtures/                        # Test fixtures
    ├── sample_kmp_project/          # Minimal KMP project for testing
    │   ├── build.gradle.kts
    │   ├── src/
    │   │   ├── commonMain/
    │   │   ├── androidMain/
    │   │   └── iosMain/
    │   └── gradle/
    └── sample_cmp_project/          # Minimal CMP project for testing
```

**Structure Decision**: Single project structure with clear modular separation. The architecture follows a layered approach:

1. **Tools Layer** (`tools/`): MCP tool implementations that expose functionality to AI agents
2. **LSP Layer** (`lsp/`): Language server integration and communication
3. **Analysis Layer** (`analyzers/`): Domain-specific code analysis logic
4. **Model Layer** (`models/`): Data structures and domain models
5. **Storage Layer** (`storage/`): Persistence and serialization
6. **Utilities** (`utils/`): Cross-cutting concerns and helpers

This structure enables:
- Clear separation of concerns (SOLID principle)
- Easy addition of new LSP servers without modifying existing code (Open/Closed)
- Independent testing of each layer
- Reusability of components across different tools

## Complexity Tracking

> **No violations - all gates passed**

## Phase -1: Pre-Implementation Gates

### Simplicity Gate (Constitution Article - Keep It Simple)
- [ ] Using ≤3 primary subsystems (Tools, LSP, Analysis)?
- [ ] No future-proofing beyond current requirements?
- [ ] Architecture can be explained in 5 minutes?

**Status**: ✅ PASS - Three clear subsystems, minimal abstractions

### Anti-Abstraction Gate (Constitution Article - YAGNI)
- [ ] Using LSP directly without unnecessary wrappers?
- [ ] Single representation per entity (no parallel class hierarchies)?
- [ ] Abstractions only where multiple implementations exist (LSP servers)?

**Status**: ✅ PASS - Minimal abstractions, only BaseAnalyzer and LSP client base

### Testability Gate (Constitution Article - Testing)
- [ ] All LSP operations mockable?
- [ ] File I/O injectable/mockable?
- [ ] Each module testable in isolation?

**Status**: ✅ PASS - Async operations easily mockable, clear interfaces

## Phase 0: Research & Technical Validation

**Purpose**: Resolve NEEDS CLARIFICATION items and validate technical approach

**Prerequisites**: None

**Research Tasks**:

1. **LSP Library Selection**
   - Research Python LSP client libraries (pygls, python-lsp-client, lsprotocol)
   - Evaluate async support, type safety, and maintenance status
   - Decision criteria: async-first, type hints, active maintenance
   - **Output**: `research.md` section on LSP library choice with rationale

2. **Kotlin Language Server Investigation**
   - Identify official Kotlin Language Server (kotlin-language-server)
   - Document installation requirements and startup command
   - Test basic LSP operations (initialize, symbol search, references)
   - **Output**: `research.md` section on Kotlin LS setup

3. **Swift SourceKit-LSP Integration**
   - Research SourceKit-LSP availability on different platforms
   - Document macOS vs Linux considerations
   - Test Swift/Objective-C interop symbol resolution
   - **Output**: `research.md` section on Swift LS setup

4. **Gradle Build File Parsing**
   - Research Gradle Kotlin DSL parsing approaches
   - Evaluate: regex patterns vs AST parsing vs Gradle tooling API
   - Decision: Likely regex-based for build.gradle.kts source set detection
   - **Output**: `research.md` section on Gradle parsing strategy

5. **FastMCP Tool Patterns**
   - Study FastMCP 2.0 tool registration patterns
   - Document async tool implementation best practices
   - Review error handling and timeout strategies
   - **Output**: `research.md` section on FastMCP patterns

6. **Async Architecture Patterns**
   - Research asyncio best practices for LSP communication
   - Study async context managers for LSP server lifecycle
   - Plan async queue patterns for concurrent requests
   - **Output**: `research.md` section on async architecture

7. **Memory Storage Format**
   - Decide JSON vs YAML vs custom format for memories
   - Plan schema for memory categories and metadata
   - Design file structure for project-specific memories
   - **Output**: `research.md` section on memory storage design

**Output**: `research.md` with comprehensive technical decisions

**Checkpoint**: All NEEDS CLARIFICATION resolved - proceed to Phase 1

---

## Phase 1: Core Design & Contracts

**Prerequisites**: `research.md` complete

**Design Tasks**:

1. **Data Model Design**
   - Define all dataclasses with type hints
   - Document relationships between entities
   - Specify validation rules
   - **Output**: `data-model.md`

2. **MCP Tool Contracts**
   - Define tool signatures (parameters, return types, descriptions)
   - Document expected behavior and error cases
   - Specify async patterns for each tool
   - **Output**: `contracts/*.md` files

3. **Validation Scenarios**
   - Extract key user journeys from spec
   - Define end-to-end validation scenarios
   - Specify expected outcomes for each scenario
   - **Output**: `quickstart.md`

4. **LSP Server Lifecycle**
   - Design startup/shutdown sequences
   - Plan health check and restart logic
   - Define error recovery strategies
   - **Output**: Part of `data-model.md`

**Phase 1 Deliverables**:
- `data-model.md` - All entities, relationships, validation rules
- `contracts/lsp_tools.md` - LSP tool contracts
- `contracts/memory_tools.md` - Memory tool contracts
- `contracts/planning_tools.md` - Planning mode tool contracts
- `contracts/elicitation_tools.md` - User elicitation tool contracts
- `quickstart.md` - Key validation scenarios

**Re-check Constitution Gates**: Verify design maintains simplicity and testability

---

## Phase 2: Implementation Phases

**Note**: Detailed task breakdown will be generated by `/speckit.tasks` command

### Foundation Phase (Blocking Prerequisites)

**Must complete before any user stories**:

- FastMCP server setup with lifecycle management
- Base LSP client implementation with async communication
- LSP manager with server lifecycle (start, stop, health check, restart)
- Core data models (Project, Symbol, CodeLocation, Memory)
- File-based storage layer (memory store, project store)
- Logging configuration and error handling infrastructure
- Test fixtures (sample KMP/CMP projects)
- Pytest configuration with async support

### User Story Implementation Phases

Each user story from spec will become an implementation phase:

- **Phase 3**: US1 - LSP-Based Symbol Navigation (P1)
- **Phase 4**: US2 - Cross-Platform Code Understanding (P1)
- **Phase 5**: US3 - Project Onboarding (P1)
- **Phase 6**: US7 - Editing Mode with Symbolic Modification (P1)
- **Phase 7**: US4 - Memory System (P2)
- **Phase 8**: US5 - Interactive User Elicitation (P2)
- **Phase 9**: US6 - Planning Mode with Spec-Driven Development (P2)
- **Phase 10**: US8 - CMP UI Pattern Recognition (P3)

### Polish Phase

- Performance optimization
- Comprehensive error handling
- Documentation (API docs, usage guides)
- Integration testing
- Example projects and tutorials

---

## Key Technical Decisions

### 1. LSP Communication Strategy

**Decision**: Async subprocess-based LSP communication
- LSP servers run as separate processes
- Communication via stdin/stdout using JSON-RPC
- AsyncIO event loop for non-blocking I/O
- Automatic restart on crash with exponential backoff

**Rationale**: 
- Process isolation prevents crashes from affecting main server
- Async I/O essential for handling concurrent LSP requests
- Standard LSP communication pattern proven in Serena

### 2. Memory Storage Format

**Decision**: JSON files with structured schema
- Per-project memory directory: `.kortex/memories/<project_id>/`
- Categories: architecture, patterns, preferences, decisions, conventions
- Schema: `{ "id", "category", "content", "created_at", "last_accessed", "metadata" }`

**Rationale**:
- JSON is human-readable and easy to parse
- File-based storage simple to implement and debug
- Per-project isolation prevents cross-contamination

### 3. Specification Storage Format

**Decision**: Markdown files following SpecKit template structure
- Stored in `.kortex/specs/<feature_id>/`
- Includes: spec.md, plan.md, tasks.md
- Compatible with SpecKit workflow

**Rationale**:
- Markdown is human-friendly and version-control friendly
- SpecKit templates provide proven structure
- Easy integration with existing SpecKit workflows

### 4. Project Structure Detection

**Decision**: Gradle build file parsing with regex patterns
- Scan for `build.gradle.kts` files recursively
- Extract `kotlin("multiplatform")` and `compose.multiplatform` plugins
- Parse source set definitions from `sourceSets` block

**Rationale**:
- Regex sufficient for build file patterns
- No need for full AST parsing complexity
- Fast and reliable for standard KMP project structures

### 5. Error Handling Strategy

**Decision**: Graceful degradation with user-friendly error messages
- LSP server failures: automatic restart with notification
- Parsing errors: return partial results with warnings
- Invalid input: clear error messages with suggested fixes
- All errors logged with context for debugging

**Rationale**:
- Reliability is critical for productive developer workflow
- Users need actionable error messages, not stack traces
- Logging enables debugging production issues

---

## Dependencies

### Production Dependencies

```toml
[project.dependencies]
# Already in pyproject.toml
fastmcp = ">=2.11.0,<3.0.0"  # MCP server framework

# To add in Phase 0 (after research)
<LSP_LIBRARY> = "<version>"   # Python LSP client (TBD)
```

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    # Already in pyproject.toml
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    
    # To add
    "pytest-cov>=4.0.0",         # Code coverage
    "pytest-mock>=3.10.0",       # Mocking support
    "mypy>=1.0.0",               # Type checking
    "ruff>=0.1.0",               # Linting and formatting
]
```

### Additional Dependencies (TBD in Phase 0)

Depending on research outcomes:
- LSP client library (e.g., `pygls`, `lsprotocol`)
- Async utilities (may use built-in `asyncio`)
- JSON schema validation (e.g., `pydantic` if needed beyond dataclasses)

---

## Testing Strategy

### Unit Tests (80%+ coverage target)

- All tools tested in isolation with mocked dependencies
- LSP client/manager tested with mock LSP servers
- Analyzers tested with sample project fixtures
- Models tested for validation and serialization
- Storage layer tested with temporary directories

### Integration Tests

- End-to-end tool execution with real MCP server
- LSP integration with kotlin-language-server in test container
- Project onboarding with sample KMP/CMP projects
- Memory persistence and retrieval
- Specification generation and storage

### Async Testing Patterns

```python
@pytest.mark.asyncio
async def test_symbol_search():
    """Test async symbol search with mocked LSP."""
    mock_lsp = AsyncMock()
    mock_lsp.workspace_symbol.return_value = [...]
    
    tool = SymbolSearchTool(lsp_client=mock_lsp)
    result = await tool.execute(query="Repository")
    
    assert len(result) > 0
    mock_lsp.workspace_symbol.assert_called_once()
```

### Test Fixtures

- Sample KMP project with commonMain, androidMain, iosMain
- Sample CMP project with Compose UI and navigation
- Mock LSP responses for common operations
- Temporary project directories for storage tests

---

## Success Criteria Validation

How we'll validate each success criterion from spec:

- **SC-001** (Onboarding <30s): Timed integration test
- **SC-002** (Symbol search <2s): Performance benchmark test
- **SC-003** (LSP ops <1s): Latency tracking in integration tests
- **SC-004** (Code mods 98% accurate): Syntax validation after modifications
- **SC-005** (Expect/actual 99% correct): Dedicated test suite for expect/actual pairs
- **SC-006** (Memory latency <500ms): Performance test with timing
- **SC-007** (Planning specs <2 rounds): Manual validation during development
- **SC-008** (Elicitation reduces ambiguity 70%): Qualitative assessment
- **SC-009** (Cross-language navigation 95%): Swift/Kotlin interop test suite
- **SC-010** (Performance at 50K LOC): Large project performance test

---

## Risk Mitigation

### Risk: LSP Server Stability

**Mitigation**:
- Implement automatic restart with exponential backoff
- Health check probes every 30 seconds
- Graceful degradation if LSP unavailable
- Comprehensive logging for debugging crashes

### Risk: Gradle Parsing Complexity

**Mitigation**:
- Start with regex patterns for standard cases
- Document unsupported build configurations
- Provide manual configuration override option
- Collect real-world build files for test coverage

### Risk: Performance with Large Projects

**Mitigation**:
- Implement caching for LSP results
- Lazy loading of project information
- Incremental indexing for symbol search
- Performance benchmarking in CI pipeline

### Risk: Cross-Platform LSP Availability

**Mitigation**:
- Document platform-specific requirements clearly
- Provide installation guides for each LSP server
- Detect missing LSP servers and provide helpful error messages
- Graceful fallback if language server unavailable

---

## Future Enhancements (Out of Current Scope)

Potential future additions (not for initial implementation):

1. **Additional Language Servers**: Java, JavaScript/TypeScript for multiplatform web
2. **Build System Integration**: Direct Gradle integration for dependency resolution
3. **IDE Plugin**: VS Code extension for richer UI
4. **Code Generation**: Template-based code generation for common KMP patterns
5. **Refactoring Tools**: Advanced refactoring operations (extract interface, move to common, etc.)
6. **Project Templates**: Scaffolding for new KMP/CMP projects
7. **Dependency Analysis**: Analyze and suggest dependency updates
8. **Performance Profiling**: Integration with profiling tools

---

## Development Workflow

### Development Commands

```bash
# Setup
cd /Users/jermey/Projects/kortex
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Testing
pytest tests/                      # Run all tests
pytest tests/ --cov=src/kortex_mcp # With coverage
pytest tests/ -v -s                # Verbose with print output
pytest tests/test_tools/           # Specific directory

# Type Checking (add after Phase 0)
mypy src/kortex_mcp

# Linting (add after Phase 0)
ruff check src/
ruff format src/

# Running Server
python -m kortex_mcp.server
# or
fastmcp dev src/kortex_mcp/server.py
```

### Git Workflow

- Main branch: `main`
- Feature branches: `feature/<name>`
- All changes via pull requests
- CI checks: tests, type checking, linting
- Squash commits on merge

---

## Next Steps

1. **Run `/speckit.tasks`** to generate detailed task breakdown from this plan
2. **Complete Phase 0 research** to resolve all technical decisions
3. **Generate data model document** in Phase 1
4. **Implement foundation phase** (LSP client, base models, storage)
5. **Iteratively implement user stories** according to priority (P1, P2, P3)
6. **Validate against success criteria** throughout implementation
7. **Iterate based on feedback** and real-world usage

---

**Plan Version**: 1.0  
**Last Updated**: 2025-11-15  
**Status**: Ready for Task Breakdown
