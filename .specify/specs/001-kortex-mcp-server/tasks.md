# Tasks: Kortex MCP Server - KMP/CMP Coding Assistant

**Input**: Design documents from `.specify/specs/001-kortex-mcp-server/`
**Prerequisites**: plan.md ✓, spec.md ✓

**Tests**: Tests are included as per project requirements (80%+ coverage target specified in plan.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Project uses single project structure:
- `src/kortex_mcp/` - Source code
- `tests/` - Test files
- `.specify/specs/001-kortex-mcp-server/` - Design documents

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create directory structure per plan.md (src/kortex_mcp/{tools,lsp,analyzers,models,storage,utils}, tests/)
- [X] T002 Update pyproject.toml with dev dependencies (pytest-cov, pytest-mock, mypy, ruff)
- [X] T003 [P] Create .gitignore with Python patterns (__pycache__, .pytest_cache, .mypy_cache, .venv)
- [X] T004 [P] Create pytest.ini with asyncio_mode=auto and test paths configuration
- [X] T005 [P] Create README.md with project overview, setup instructions, and usage examples

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create base logging configuration in src/kortex_mcp/utils/logging.py
- [X] T007 [P] Create file utilities module in src/kortex_mcp/utils/file_utils.py (path handling, file operations)
- [X] T008 [P] Create async utilities module in src/kortex_mcp/utils/async_utils.py (async helpers, timeout decorators)
- [X] T009 Create core data models in src/kortex_mcp/models/project.py (Project, SourceSet dataclasses with full type hints)
- [X] T010 [P] Create symbol models in src/kortex_mcp/models/symbol.py (Symbol, CodeLocation dataclasses)
- [X] T011 [P] Create LSP type models in src/kortex_mcp/models/lsp.py (LSP request/response types)
- [X] T012 Create base LSP client in src/kortex_mcp/lsp/client.py (async subprocess communication, JSON-RPC)
- [X] T013 Create LSP manager in src/kortex_mcp/lsp/manager.py (lifecycle management, health checks, auto-restart)
- [X] T014 Create LSP types module in src/kortex_mcp/lsp/types.py (LSP protocol type conversions)
- [X] T015 Create memory models in src/kortex_mcp/models/memory.py (Memory, MemoryCategory dataclasses)
- [X] T016 Create memory storage in src/kortex_mcp/storage/memory_store.py (JSON-based persistence)
- [X] T017 Create project storage in src/kortex_mcp/storage/project_store.py (project config persistence)
- [X] T018 Create FastMCP server setup in src/kortex_mcp/server.py (server initialization, lifecycle hooks)
- [X] T019 Create base tool class in src/kortex_mcp/tools/base.py (common tool functionality, error handling)
- [X] T020 Create test fixtures directory tests/fixtures/ with sample KMP project structure
- [X] T021 [P] Create pytest conftest.py with async fixtures and mock LSP server factory
- [X] T022 [P] Setup mypy configuration in pyproject.toml (strict mode, ignore missing imports for external libs)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - LSP-Based Symbol Navigation (Priority: P1) 🎯 MVP

**Goal**: Enable symbol search, navigation, and reference finding across KMP source sets

**Independent Test**: Can search for "Repository" class and navigate to its definition with file path and line number

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T023 [P] [US1] Unit test for LSP client initialization in tests/test_lsp/test_client.py
- [X] T024 [P] [US1] Unit test for workspace symbol search in tests/test_lsp/test_client.py
- [X] T025 [P] [US1] Integration test for symbol search tool in tests/test_tools/test_lsp_tools.py
- [X] T026 [P] [US1] Integration test for find references tool in tests/test_tools/test_lsp_tools.py

### Implementation for User Story 1

- [ ] T027 [P] [US1] Implement Kotlin LSP server integration in src/kortex_mcp/lsp/kotlin_server.py (startup command, initialization params)
- [ ] T028 [US1] Add workspace symbol search to LSP client in src/kortex_mcp/lsp/client.py (textDocument/documentSymbol request)
- [ ] T029 [US1] Add go-to-definition support in src/kortex_mcp/lsp/client.py (textDocument/definition request)
- [ ] T030 [US1] Add find references support in src/kortex_mcp/lsp/client.py (textDocument/references request)
- [ ] T031 [US1] Implement symbol search MCP tool in src/kortex_mcp/tools/lsp_tools.py (async tool with query parameter)
- [ ] T032 [US1] Implement go-to-definition MCP tool in src/kortex_mcp/tools/lsp_tools.py
- [ ] T033 [US1] Implement find references MCP tool in src/kortex_mcp/tools/lsp_tools.py
- [ ] T034 [US1] Register LSP tools with FastMCP server in src/kortex_mcp/server.py
- [ ] T035 [US1] Add error handling and timeout logic to LSP tools in src/kortex_mcp/tools/lsp_tools.py
- [ ] T036 [US1] Add comprehensive pydoc to all US1 functions and classes

**Checkpoint**: At this point, User Story 1 should be fully functional - can search symbols and navigate code in KMP projects

---

## Phase 4: User Story 2 - Cross-Platform Code Understanding (Priority: P1)

**Goal**: Enable understanding of Kotlin/Swift/Objective-C interop and cross-platform symbol resolution

**Independent Test**: Can query "how is SharedRepository used in Swift" and receive accurate usage information

### Tests for User Story 2

- [ ] T037 [P] [US2] Unit test for Swift LSP server integration in tests/test_lsp/test_swift_server.py
- [ ] T038 [P] [US2] Unit test for Objective-C LSP server integration in tests/test_lsp/test_objc_server.py
- [ ] T039 [P] [US2] Integration test for cross-platform symbol resolution in tests/test_tools/test_lsp_tools.py
- [ ] T040 [P] [US2] Integration test for expect/actual navigation in tests/test_analyzers/test_kmp_analyzer.py

### Implementation for User Story 2

- [ ] T041 [P] [US2] Implement Swift LSP server integration in src/kortex_mcp/lsp/swift_server.py (SourceKit-LSP configuration)
- [ ] T042 [P] [US2] Implement Objective-C LSP server integration in src/kortex_mcp/lsp/objc_server.py (clangd configuration)
- [ ] T043 [US2] Add multi-LSP support to manager in src/kortex_mcp/lsp/manager.py (handle multiple language servers)
- [ ] T044 [US2] Create KMP analyzer in src/kortex_mcp/analyzers/kmp_analyzer.py (expect/actual detection, source set analysis)
- [ ] T045 [US2] Implement expect/actual pair detection in src/kortex_mcp/analyzers/kmp_analyzer.py
- [ ] T046 [US2] Implement cross-language symbol lookup in src/kortex_mcp/tools/lsp_tools.py (query Kotlin then Swift/ObjC)
- [ ] T047 [US2] Add expect/actual navigation tool in src/kortex_mcp/tools/lsp_tools.py
- [ ] T048 [US2] Add comprehensive pydoc to all US2 functions and classes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - can navigate cross-platform code

---

## Phase 5: User Story 3 - Project Onboarding (Priority: P1)

**Goal**: Automatically detect and configure KMP/CMP projects with source sets and dependencies

**Independent Test**: Can initialize assistant in KMP project directory and verify it correctly identifies source sets and targets

### Tests for User Story 3

- [ ] T049 [P] [US3] Unit test for Gradle parser in tests/test_utils/test_gradle_parser.py
- [ ] T050 [P] [US3] Integration test for project analyzer in tests/test_analyzers/test_project_analyzer.py
- [ ] T051 [P] [US3] Integration test for project onboarding tool in tests/test_tools/test_project_tools.py
- [ ] T052 [P] [US3] Test with sample CMP project fixture in tests/fixtures/sample_cmp_project/

### Implementation for User Story 3

- [ ] T053 [P] [US3] Create Gradle parser in src/kortex_mcp/utils/gradle_parser.py (regex-based build.gradle.kts parsing)
- [ ] T054 [US3] Implement source set detection in src/kortex_mcp/utils/gradle_parser.py (extract sourceSets block)
- [ ] T055 [US3] Implement dependency extraction in src/kortex_mcp/utils/gradle_parser.py (parse dependencies block)
- [ ] T056 [US3] Create project analyzer in src/kortex_mcp/analyzers/project_analyzer.py (recursive build file scanning)
- [ ] T057 [US3] Implement KMP project detection in src/kortex_mcp/analyzers/project_analyzer.py (detect kotlin("multiplatform") plugin)
- [ ] T058 [US3] Implement CMP project detection in src/kortex_mcp/analyzers/project_analyzer.py (detect compose.multiplatform)
- [ ] T059 [US3] Create project onboarding tool in src/kortex_mcp/tools/project_tools.py (async tool for project initialization)
- [ ] T060 [US3] Implement project info query tool in src/kortex_mcp/tools/project_tools.py (return targets, source sets, dependencies)
- [ ] T061 [US3] Store project configuration using project_store in src/kortex_mcp/storage/project_store.py
- [ ] T062 [US3] Initialize LSP servers based on detected project in src/kortex_mcp/tools/project_tools.py
- [ ] T063 [US3] Add comprehensive pydoc to all US3 functions and classes

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work - can onboard projects and navigate symbols

---

## Phase 6: User Story 7 - Editing Mode with Symbolic Modification (Priority: P1)

**Goal**: Enable precise code modifications using LSP symbol-level operations

**Independent Test**: Can request "add new method to UserRepository class" and verify system adds method with correct formatting

### Tests for User Story 7

- [ ] T064 [P] [US7] Unit test for code edit operations in tests/test_tools/test_editing_tools.py
- [ ] T065 [P] [US7] Integration test for add method operation in tests/test_tools/test_editing_tools.py
- [ ] T066 [P] [US7] Integration test for rename symbol operation in tests/test_tools/test_editing_tools.py
- [ ] T067 [P] [US7] Test expect/actual consistency maintenance in tests/test_tools/test_editing_tools.py

### Implementation for User Story 7

- [ ] T068 [US7] Add text edits support to LSP client in src/kortex_mcp/lsp/client.py (textDocument/didChange, workspace/applyEdit)
- [ ] T069 [US7] Add rename symbol support in src/kortex_mcp/lsp/client.py (textDocument/rename request)
- [ ] T070 [US7] Implement symbol insertion logic in src/kortex_mcp/analyzers/kmp_analyzer.py (find insertion point using AST)
- [ ] T071 [US7] Create editing tools module in src/kortex_mcp/tools/editing_tools.py (add_method, modify_method, delete_method)
- [ ] T072 [US7] Implement add method tool in src/kortex_mcp/tools/editing_tools.py (async tool with class name, method signature)
- [ ] T073 [US7] Implement rename symbol tool in src/kortex_mcp/tools/editing_tools.py (rename with all references)
- [ ] T074 [US7] Add expect/actual consistency check in src/kortex_mcp/analyzers/kmp_analyzer.py (validate paired declarations)
- [ ] T075 [US7] Implement formatting preservation in src/kortex_mcp/tools/editing_tools.py (maintain indentation, style)
- [ ] T076 [US7] Add comprehensive pydoc to all US7 functions and classes

**Checkpoint**: All P1 user stories complete - MVP fully functional with navigation and editing

---

## Phase 7: User Story 4 - Memory System (Priority: P2)

**Goal**: Store and retrieve project-specific knowledge (patterns, decisions, preferences)

**Independent Test**: Can store memory "use Koin for DI", then query and verify assistant recalls this preference

### Tests for User Story 4

- [ ] T077 [P] [US4] Unit test for memory models in tests/test_models/test_models.py
- [ ] T078 [P] [US4] Unit test for memory store operations in tests/test_storage/test_memory_store.py
- [ ] T079 [P] [US4] Integration test for memory tools in tests/test_tools/test_memory_tools.py
- [ ] T080 [P] [US4] Test memory retrieval and application in tests/test_tools/test_memory_tools.py

### Implementation for User Story 4

- [ ] T081 [P] [US4] Implement memory category enum in src/kortex_mcp/models/memory.py (architecture, patterns, preferences, etc.)
- [ ] T082 [US4] Add memory validation logic in src/kortex_mcp/models/memory.py (validate category, content)
- [ ] T083 [US4] Implement memory CRUD operations in src/kortex_mcp/storage/memory_store.py (create, read, update, delete)
- [ ] T084 [US4] Add memory search and filtering in src/kortex_mcp/storage/memory_store.py (by category, timestamp, content)
- [ ] T085 [US4] Create memory management tools in src/kortex_mcp/tools/memory_tools.py (store_memory, query_memory, list_memories)
- [ ] T086 [US4] Implement memory application logic in src/kortex_mcp/tools/memory_tools.py (apply memories to suggestions)
- [ ] T087 [US4] Add memory timestamp tracking in src/kortex_mcp/storage/memory_store.py (created_at, last_accessed)
- [ ] T088 [US4] Add comprehensive pydoc to all US4 functions and classes

**Checkpoint**: Memory system operational - can store and recall project knowledge

---

## Phase 8: User Story 5 - Interactive User Elicitation (Priority: P2)

**Goal**: Ask clarifying questions to resolve ambiguities in requirements

**Independent Test**: Request "plan auth feature" and verify system asks about auth methods, storage, platform-specific requirements

### Tests for User Story 5

- [ ] T089 [P] [US5] Unit test for elicitation question models in tests/test_models/test_models.py
- [ ] T090 [P] [US5] Integration test for ask_user tool in tests/test_tools/test_elicitation_tools.py
- [ ] T091 [P] [US5] Test question type handling (open-ended, single-select, multi-select) in tests/test_tools/test_elicitation_tools.py

### Implementation for User Story 5

- [ ] T092 [P] [US5] Create elicitation question model in src/kortex_mcp/models/specification.py (question, type, options, response)
- [ ] T093 [US5] Implement ask_user MCP tool in src/kortex_mcp/tools/elicitation_tools.py (async tool with question, options)
- [ ] T094 [US5] Add question type support in src/kortex_mcp/tools/elicitation_tools.py (open-ended, single-select, multi-select)
- [ ] T095 [US5] Implement response storage in src/kortex_mcp/tools/elicitation_tools.py (store in spec or memory)
- [ ] T096 [US5] Add platform-specific question templates in src/kortex_mcp/tools/elicitation_tools.py (iOS vs Android questions)
- [ ] T097 [US5] Add comprehensive pydoc to all US5 functions and classes

**Checkpoint**: Elicitation system working - can ask clarifying questions interactively

---

## Phase 9: User Story 6 - Planning Mode with Spec-Driven Development (Priority: P2)

**Goal**: Create and refine specifications following SpecKit template structure

**Independent Test**: Enter planning mode for "offline sync", create spec, verify stored in .kortex/specs/ with proper structure

### Tests for User Story 6

- [ ] T098 [P] [US6] Unit test for specification models in tests/test_models/test_models.py
- [ ] T099 [P] [US6] Unit test for spec storage in tests/test_storage/test_spec_store.py
- [ ] T100 [P] [US6] Integration test for planning tools in tests/test_tools/test_planning_tools.py
- [ ] T101 [P] [US6] Test spec refinement workflow in tests/test_tools/test_planning_tools.py

### Implementation for User Story 6

- [ ] T102 [P] [US6] Create specification models in src/kortex_mcp/models/specification.py (Specification, UserStory, Requirement)
- [ ] T103 [US6] Implement spec storage in src/kortex_mcp/storage/spec_store.py (Markdown-based with SpecKit structure)
- [ ] T104 [US6] Create planning mode tool in src/kortex_mcp/tools/planning_tools.py (create_spec, refine_spec, analyze_spec)
- [ ] T105 [US6] Implement SpecKit template generation in src/kortex_mcp/tools/planning_tools.py (user stories, requirements, success criteria)
- [ ] T106 [US6] Add spec analysis logic in src/kortex_mcp/tools/planning_tools.py (completeness, clarity, consistency checks)
- [ ] T107 [US6] Implement spec dependency detection in src/kortex_mcp/tools/planning_tools.py (identify conflicting specs)
- [ ] T108 [US6] Add task breakdown from spec in src/kortex_mcp/tools/planning_tools.py (generate tasks.md from plan.md)
- [ ] T109 [US6] Add comprehensive pydoc to all US6 functions and classes

**Checkpoint**: Planning mode operational - can create and refine specifications

---

## Phase 10: User Story 8 - CMP UI Pattern Recognition (Priority: P3)

**Goal**: Recognize CMP-specific patterns (composables, navigation, state management)

**Independent Test**: Query "how is navigation handled" and verify system identifies Voyager/Decompose and patterns

### Tests for User Story 8

- [ ] T110 [P] [US8] Unit test for CMP analyzer in tests/test_analyzers/test_cmp_analyzer.py
- [ ] T111 [P] [US8] Test composable function detection in tests/test_analyzers/test_cmp_analyzer.py
- [ ] T112 [P] [US8] Test navigation library detection in tests/test_analyzers/test_cmp_analyzer.py

### Implementation for User Story 8

- [ ] T113 [P] [US8] Create CMP analyzer in src/kortex_mcp/analyzers/cmp_analyzer.py (composable detection, state analysis)
- [ ] T114 [US8] Implement composable function detection in src/kortex_mcp/analyzers/cmp_analyzer.py (find @Composable annotations)
- [ ] T115 [US8] Add state management pattern detection in src/kortex_mcp/analyzers/cmp_analyzer.py (remember, mutableStateOf, ViewModel)
- [ ] T116 [US8] Implement navigation library detection in src/kortex_mcp/analyzers/cmp_analyzer.py (Voyager, Decompose patterns)
- [ ] T117 [US8] Add Material3 theme analysis in src/kortex_mcp/analyzers/cmp_analyzer.py (colors, typography, shapes)
- [ ] T118 [US8] Create CMP pattern query tool in src/kortex_mcp/tools/project_tools.py (query composables, navigation, themes)
- [ ] T119 [US8] Add comprehensive pydoc to all US8 functions and classes

**Checkpoint**: All user stories complete - full feature set implemented

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T120 [P] Add comprehensive logging to all tools in src/kortex_mcp/tools/ (debug, info, error levels)
- [ ] T121 [P] Add performance monitoring in src/kortex_mcp/utils/async_utils.py (track operation timing)
- [ ] T122 Add LSP server crash recovery testing in tests/test_lsp/test_manager.py
- [ ] T123 [P] Create user documentation in docs/README.md (installation, usage, examples)
- [ ] T124 [P] Create API documentation in docs/API.md (all tools, parameters, examples)
- [ ] T125 [P] Add example KMP project in examples/sample-kmp/ with documentation
- [ ] T126 Add integration test for complete workflow in tests/test_integration.py (onboard → search → edit → memory)
- [ ] T127 Run mypy type checking and fix all type errors across codebase
- [ ] T128 Run ruff linting and fix all style issues across codebase
- [ ] T129 Measure code coverage and ensure 80%+ target achieved
- [ ] T130 Performance optimization pass (caching, async improvements)
- [ ] T131 Security review (input validation, LSP command injection prevention)
- [ ] T132 Run quickstart.md validation scenarios from specs/001-kortex-mcp-server/quickstart.md
- [ ] T133 Create CONTRIBUTING.md with development guidelines
- [ ] T134 [P] Update README.md with complete feature list and examples

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-10)**: All depend on Foundational phase completion
  - P1 stories (US1, US2, US3, US7) are critical for MVP
  - P2 stories (US4, US5, US6) add enhanced functionality
  - P3 stories (US8) are nice-to-have
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (Symbol Navigation)**: Foundation only - no other story dependencies
- **US2 (Cross-Platform)**: Depends on US1 (extends LSP tools) - but can start after Foundation
- **US3 (Onboarding)**: Foundation only - can be developed in parallel with US1/US2
- **US7 (Editing)**: Depends on US1 (uses symbol navigation) - build after US1 complete
- **US4 (Memory)**: Foundation only - independent of other stories
- **US5 (Elicitation)**: Foundation only - independent of other stories
- **US6 (Planning)**: May use US5 (elicitation) and US4 (memory) - build after those if desired
- **US8 (CMP Patterns)**: Depends on US3 (project analysis) - build after US3 complete

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before analyzers
- Analyzers before tools
- Tools before server registration
- Core implementation before integration
- Story complete (checkpoint verified) before moving to next priority

### Parallel Opportunities

- **Phase 1**: T003, T004, T005 can run in parallel
- **Phase 2**: T007+T008, T010+T011, T015+T016+T017, T019+T020+T021+T022 can run in parallel
- **US1 Tests**: T023, T024, T025, T026 can run in parallel
- **US1 Implementation**: T027, T028+T029+T030 can run in parallel after T027
- **US2 Tests**: T037, T038, T039, T040 can run in parallel
- **US2 Implementation**: T041, T042 can run in parallel
- **US3 Tests**: T049, T050, T051, T052 can run in parallel
- **US3 Implementation**: T053 standalone first, then T056+T057+T058 parallel after T053
- **US4, US5, US6, US8**: Can be developed in parallel by different developers after their dependencies are met
- **Polish**: T120, T121, T123, T124, T125, T133, T134 can run in parallel

### Recommended Execution Strategy

**MVP Focus (P1 Only)**:
1. Phase 1 (Setup) → Phase 2 (Foundation) - ~2-3 days
2. US1 (Symbol Navigation) - ~3-4 days
3. US2 (Cross-Platform) - ~3-4 days
4. US3 (Onboarding) - ~3-4 days
5. US7 (Editing) - ~4-5 days
6. Basic Polish (logging, docs, testing) - ~2-3 days
**Total MVP**: ~17-23 days for single developer

**Full Feature Set**:
- After MVP, add P2 stories (US4, US5, US6) - ~10-12 days
- Add P3 story (US8) - ~3-4 days
- Complete Polish phase - ~3-4 days
**Total Full**: ~33-43 days for single developer

**Parallel Team (3 developers)**:
- Foundation: All together (~2-3 days)
- Dev A: US1+US7 (~7-9 days)
- Dev B: US2+US8 (~6-8 days)
- Dev C: US3+US4+US5+US6 (~13-15 days)
- Polish: All together (~3-4 days)
**Total Parallel**: ~15-19 days

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup (~1 day)
2. Complete Phase 2: Foundational (~2 days) - CRITICAL
3. Complete US1: Symbol Navigation (~3-4 days)
4. Complete US2: Cross-Platform (~3-4 days)
5. Complete US3: Onboarding (~3-4 days)
6. Complete US7: Editing (~4-5 days)
7. Basic Polish: Logging, docs, testing (~2-3 days)
8. **STOP and VALIDATE**: Test all P1 functionality end-to-end
9. Deploy/demo MVP

**MVP Delivers**:
- Full LSP integration for Kotlin, Swift, Objective-C
- Symbol search, navigation, references across platforms
- Project onboarding and analysis
- Code editing with symbolic modifications
- Core functionality validated and documented

### Incremental Delivery

1. MVP (P1) → Validate → Deploy
2. Add US4 (Memory) → Test independently → Deploy
3. Add US5 (Elicitation) → Test independently → Deploy
4. Add US6 (Planning) → Test independently → Deploy
5. Add US8 (CMP Patterns) → Test independently → Deploy
6. Each story adds value without breaking previous functionality

### Parallel Team Strategy

With 3 developers after Foundation phase:

**Developer A - Core LSP**:
- US1 (Symbol Navigation)
- US7 (Editing Mode)

**Developer B - Platform Integration**:
- US2 (Cross-Platform Understanding)
- US8 (CMP Pattern Recognition)

**Developer C - Higher-Level Features**:
- US3 (Project Onboarding)
- US4 (Memory System)
- US5 (User Elicitation)
- US6 (Planning Mode)

All converge for Polish phase.

---

## Validation Checklist

Before considering each phase complete:

### Phase 2 (Foundation) Checklist
- [ ] All base models defined with full type hints and pydoc
- [ ] LSP client can start/stop/restart Kotlin language server
- [ ] Memory store can save and load JSON files
- [ ] FastMCP server initializes without errors
- [ ] All 80+ type hints verified with mypy
- [ ] Test fixtures include valid KMP project structure

### User Story Checkpoints

**US1 Complete When**:
- [ ] Can search for "Repository" and get results with file paths
- [ ] Can navigate to symbol definition with exact line number
- [ ] Can find all references to a function across source sets
- [ ] All tests passing (unit + integration)
- [ ] Test coverage ≥80% for US1 modules

**US2 Complete When**:
- [ ] Swift LSP server starts and responds to requests
- [ ] Can resolve Kotlin class usage in Swift files
- [ ] Expect/actual pairs correctly identified
- [ ] Cross-language navigation works in both directions
- [ ] All tests passing, coverage ≥80%

**US3 Complete When**:
- [ ] Can detect KMP project in <30 seconds
- [ ] Correctly identifies all source sets (commonMain, androidMain, iosMain)
- [ ] Extracts dependencies from build.gradle.kts
- [ ] Stores project configuration persistently
- [ ] All tests passing, coverage ≥80%

**US7 Complete When**:
- [ ] Can add method to class with correct formatting
- [ ] Symbol rename updates all references
- [ ] Expect/actual declarations stay consistent
- [ ] Code formatting preserved (indentation, style)
- [ ] All tests passing, coverage ≥80%

**US4 Complete When**:
- [ ] Can store memory with category and retrieve it
- [ ] Memories persist across sessions
- [ ] Can query memories by category
- [ ] Timestamp tracking working (created_at, last_accessed)
- [ ] All tests passing, coverage ≥80%

**US5 Complete When**:
- [ ] Can send question to user via ask_user tool
- [ ] Supports all question types (open, single-select, multi-select)
- [ ] Response properly stored in spec/memory
- [ ] Platform-specific questions work correctly
- [ ] All tests passing, coverage ≥80%

**US6 Complete When**:
- [ ] Can create specification in SpecKit format
- [ ] Spec stored as Markdown in .kortex/specs/
- [ ] Spec analysis identifies gaps and issues
- [ ] Task breakdown from spec works correctly
- [ ] All tests passing, coverage ≥80%

**US8 Complete When**:
- [ ] Correctly detects @Composable functions
- [ ] Identifies navigation library (Voyager/Decompose)
- [ ] Recognizes state management patterns
- [ ] Theme analysis working (Material3)
- [ ] All tests passing, coverage ≥80%

### Final Validation (Before Release)
- [ ] All 134 tasks complete
- [ ] Overall code coverage ≥80%
- [ ] Zero mypy type errors
- [ ] Zero ruff linting errors
- [ ] All integration tests passing
- [ ] Documentation complete (README, API docs, examples)
- [ ] Performance targets met (see success criteria in spec.md)
- [ ] quickstart.md scenarios all validated
- [ ] Security review complete

---

## Notes

- All async functions use `async/await` pattern consistently
- All public functions have comprehensive pydoc (Args, Returns, Raises, Examples)
- All modules have module-level docstrings
- Type hints required on all function signatures (enforced by mypy)
- LSP servers run as separate processes for isolation
- JSON used for structured storage (memories, project config)
- Markdown used for specifications (SpecKit compatibility)
- Error handling includes graceful degradation and helpful messages
- Logging at appropriate levels (DEBUG for dev, INFO for operations, ERROR for failures)
- Tests mirror source structure (tests/test_tools/ for src/kortex_mcp/tools/)
- Commit after completing each task or logical group
- Stop at checkpoints to validate independently before proceeding
