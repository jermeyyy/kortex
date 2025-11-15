# Feature Specification: Kortex MCP Server - KMP/CMP Coding Assistant

**Feature Branch**: `main`  
**Created**: 2025-11-15  
**Status**: Draft  
**Input**: Build coding assistant similar to Serena coding assistant but tailored to usage with KMP and CMP mobile app projects with LSP integration, project onboarding, memories, symbolic search, user elicitation, and planning/editing modes

## User Scenarios & Testing *(mandatory)*

### User Story 1 - LSP-Based Symbol Navigation in KMP Projects (Priority: P1)

As a developer working on a Kotlin Multiplatform project, I need to find and navigate to specific code symbols (classes, functions, properties) across source sets without manually searching through files, so I can understand and modify code efficiently.

**Why this priority**: Core capability that differentiates this from basic file-based assistants. Essential for working with KMP's multi-source-set structure (commonMain, androidMain, iosMain, etc.).

**Independent Test**: Can be fully tested by opening a KMP project, requesting "find class NetworkRepository" and verifying the assistant locates it in the correct source set with file path and line number.

**Acceptance Scenarios**:

1. **Given** a KMP project with Kotlin code, **When** user requests to find a symbol by name, **Then** system returns symbol location(s) across all source sets with file paths and line numbers
2. **Given** a symbol location, **When** user requests references to that symbol, **Then** system returns all places where symbol is used across the project
3. **Given** a Kotlin class, **When** user requests implementations or subclasses, **Then** system returns all implementing/extending classes across source sets
4. **Given** a function call site, **When** user requests to go to definition, **Then** system navigates to the actual implementation considering expect/actual declarations

---

### User Story 2 - Cross-Platform Code Understanding with Swift/Objective-C (Priority: P1)

As a developer working on KMP projects with iOS integration, I need to understand how Kotlin code is consumed by Swift/Objective-C code and vice versa, so I can ensure proper interop and debug cross-platform issues.

**Why this priority**: KMP projects inherently involve iOS native code. Understanding the boundary between Kotlin and Swift/Objective-C is critical for effective development.

**Independent Test**: Can be tested by analyzing a KMP project with iOS implementation, querying "how is SharedRepository used in Swift" and receiving accurate usage information from Swift/Objective-C files.

**Acceptance Scenarios**:

1. **Given** a KMP project with iOS implementation, **When** user queries about Kotlin class usage in Swift, **Then** system analyzes Swift code using LSP and shows how Kotlin classes are consumed
2. **Given** Swift/Objective-C code calling Kotlin, **When** user requests to see the Kotlin implementation, **Then** system navigates to the corresponding Kotlin expect/actual declarations
3. **Given** an expect declaration in Kotlin, **When** user queries implementations, **Then** system shows both the actual Kotlin implementations and any Swift/Objective-C bridging code

---

### User Story 3 - Project Onboarding and Context Building (Priority: P1)

As a developer starting with a new KMP/CMP codebase, I need the assistant to automatically understand the project structure, dependencies, and architecture patterns, so I can get productive quickly without manual configuration.

**Why this priority**: Foundational capability that enables all other features. Without proper project understanding, LSP and analysis features cannot work correctly.

**Independent Test**: Can be tested by initializing assistant in a KMP project directory and verifying it correctly identifies source sets, build files, dependencies, and project type (KMP/CMP).

**Acceptance Scenarios**:

1. **Given** a KMP/CMP project directory, **When** user initializes the project, **Then** system scans for build.gradle.kts files, identifies source sets, catalogs dependencies, and stores project structure
2. **Given** project structure information, **When** user asks "what targets does this project support", **Then** system accurately reports Android, iOS, Desktop, Web, etc.
3. **Given** a Compose Multiplatform project, **When** system analyzes dependencies, **Then** it identifies Compose version, platform-specific UI libraries, and navigation patterns used
4. **Given** project onboarding completion, **When** user queries about project conventions, **Then** system provides information about package structure, naming patterns, and architectural patterns

---

### User Story 4 - Memory System for Project-Specific Knowledge (Priority: P2)

As a developer working on a long-running KMP project, I need the assistant to remember important decisions, patterns, and preferences specific to this project, so I don't have to repeat context in every interaction.

**Why this priority**: Significantly improves user experience and maintains consistency across development sessions. Not immediately critical but essential for practical long-term use.

**Independent Test**: Can be tested by storing a memory like "use Koin for dependency injection", then in a new session asking about DI and verifying the assistant recalls and applies this preference.

**Acceptance Scenarios**:

1. **Given** an ongoing development session, **When** user states a project preference or decision, **Then** system stores it as a project memory with timestamp and context
2. **Given** stored project memories, **When** user asks for code generation or suggestions, **Then** system applies remembered patterns and preferences automatically
3. **Given** stored architectural decisions, **When** new developer queries about "how we handle navigation", **Then** system retrieves and explains the documented approach
4. **Given** conflicting information, **When** system detects memory conflict with new input, **Then** it prompts user to clarify and updates memory accordingly

---

### User Story 5 - Interactive User Elicitation for Requirements (Priority: P2)

As a developer planning a new feature, I need the assistant to ask clarifying questions about requirements and design choices, so I can make informed decisions and avoid ambiguity.

**Why this priority**: Prevents implementation of incorrect or incomplete features. Critical for planning mode but not needed for basic code navigation and editing.

**Independent Test**: Can be tested by requesting "plan a new authentication feature" and verifying system asks relevant questions about auth methods, storage, platform-specific requirements, etc.

**Acceptance Scenarios**:

1. **Given** a high-level feature request, **When** system detects ambiguity or missing information, **Then** it uses ask_user tool to present structured questions (open-ended or multiple choice)
2. **Given** platform-specific considerations, **When** planning a KMP feature, **Then** system asks about platform-specific requirements (iOS keychain vs Android keystore for auth, etc.)
3. **Given** multiple valid architectural approaches, **When** user provides incomplete direction, **Then** system presents options with trade-offs and asks user to select
4. **Given** user responses to questions, **When** building specifications, **Then** system incorporates answers into detailed requirements and stores them as memories

---

### User Story 6 - Planning Mode with Spec-Driven Development (Priority: P2)

As a developer planning a complex feature, I need to create and refine detailed specifications before implementation, so I can think through architecture, identify dependencies, and get feedback before writing code.

**Why this priority**: Enables structured development approach and reduces rework. Especially valuable for complex features but not essential for small changes.

**Independent Test**: Can be tested by entering planning mode for "add offline sync", creating a spec file with requirements and architecture, refining it through iterations, and then verifying the spec is stored and can be used for implementation.

**Acceptance Scenarios**:

1. **Given** planning mode activated, **When** user describes a feature, **Then** system creates a structured specification document with user stories, requirements, and success criteria
2. **Given** a draft specification, **When** user requests refinement, **Then** system uses elicitation questions to fill gaps and improve clarity
3. **Given** a refined specification, **When** system analyzes against project context, **Then** it identifies architectural implications, required changes to existing code, and implementation complexity
4. **Given** multiple feature specifications, **When** user queries dependencies, **Then** system shows which specs depend on or conflict with each other
5. **Given** an approved specification, **When** transitioning to editing mode, **Then** system breaks down spec into actionable implementation tasks

---

### User Story 7 - Editing Mode with Symbolic Code Modification (Priority: P1)

As a developer implementing a feature, I need to make precise code changes using symbol-level operations rather than text replacement, so changes are accurate and respect code structure.

**Why this priority**: Core implementation capability. Without this, the assistant cannot reliably modify code in complex KMP projects.

**Independent Test**: Can be tested by requesting "add a new method to UserRepository class" and verifying system uses LSP to find the exact class, determines proper insertion point, and adds method with correct indentation and context.

**Acceptance Scenarios**:

1. **Given** a request to add a method to a class, **When** system locates the class via LSP, **Then** it inserts method at appropriate location (after existing methods, before companion object, etc.)
2. **Given** an expect declaration update, **When** system modifies it, **Then** it also updates all actual implementations across platforms maintaining consistency
3. **Given** a request to rename a symbol, **When** system performs rename, **Then** it updates all references across all source sets including Swift/Objective-C interop layers
4. **Given** a composable function modification, **When** updating parameters or state, **Then** system updates call sites and state management code consistently
5. **Given** dependency injection updates, **When** adding new dependencies to a class, **Then** system updates DI configuration and injection points

---

### User Story 8 - Compose Multiplatform UI Pattern Recognition (Priority: P3)

As a developer working with Compose Multiplatform, I need the assistant to understand CMP-specific patterns (state management, navigation, theming, resources), so it can provide contextually appropriate suggestions.

**Why this priority**: Nice-to-have enhancement that improves CMP development experience but not blocking for basic functionality.

**Independent Test**: Can be tested by querying "how is navigation handled in this project" in a CMP project using Voyager/Decompose and verifying system identifies the navigation library and patterns used.

**Acceptance Scenarios**:

1. **Given** a CMP project, **When** analyzing composable functions, **Then** system identifies state management patterns (remember, mutableStateOf, ViewModel, etc.)
2. **Given** navigation implementation, **When** queried, **Then** system identifies navigation library (Voyager, Decompose, etc.) and explains routing patterns
3. **Given** theme definitions, **When** analyzing Material3 usage, **Then** system shows how colors, typography, and shapes are defined and used across platforms
4. **Given** resource usage, **When** analyzing images/strings, **Then** system understands Compose Resources library and platform-specific resource access

---

### Edge Cases

- What happens when LSP server fails to start or crashes during operation?
- How does system handle projects with custom Gradle configurations that don't follow standard KMP structure?
- What happens when Swift/Objective-C files use Kotlin classes that have been refactored or renamed?
- How does system behave when working with partial or broken code that doesn't compile?
- What happens when multiple source sets define the same symbol name (name shadowing)?
- How does system handle very large projects (1000+ files) where symbol searches might be slow?
- What happens when working offline without access to external LSP binaries or documentation?
- How does system differentiate between expect/actual pairs vs regular classes with similar names?

## Requirements *(mandatory)*

### Functional Requirements

**LSP Integration:**

- **FR-001**: System MUST integrate with Kotlin Language Server for symbol resolution, navigation, and code analysis
- **FR-002**: System MUST integrate with Swift Language Server (SourceKit-LSP) for iOS code analysis
- **FR-003**: System MUST integrate with Objective-C Language Server (clangd) for legacy iOS code analysis
- **FR-004**: System MUST support LSP operations: goto definition, find references, find implementations, document symbols, workspace symbols, hover info, and code actions
- **FR-005**: System MUST handle LSP server lifecycle (start, stop, restart, health checks)
- **FR-006**: System MUST maintain LSP workspace state synchronized with file system changes

**Project Onboarding:**

- **FR-007**: System MUST detect KMP projects by scanning for build.gradle.kts files with Kotlin Multiplatform plugin
- **FR-008**: System MUST identify all source sets (commonMain, androidMain, iosMain, jvmMain, jsMain, etc.) from Gradle configuration
- **FR-009**: System MUST catalog project dependencies including versions and platform-specific dependencies
- **FR-010**: System MUST identify Compose Multiplatform usage and version
- **FR-011**: System MUST detect project structure patterns (package organization, module structure, architectural layers)
- **FR-012**: System MUST store project configuration in persistent storage for future sessions

**Memory System:**

- **FR-013**: System MUST store project-specific memories including architectural decisions, coding patterns, and user preferences
- **FR-014**: System MUST associate memories with specific projects using project root path as identifier
- **FR-015**: System MUST timestamp all memories and track when they were last accessed
- **FR-016**: System MUST allow user to query, update, and delete memories
- **FR-017**: System MUST automatically apply relevant memories when generating code or providing suggestions
- **FR-018**: System MUST support memory categories: architecture, patterns, preferences, decisions, conventions

**Symbolic Search:**

- **FR-019**: System MUST search for symbols by name across entire project using LSP workspace symbols
- **FR-020**: System MUST filter search results by symbol type (class, function, property, enum, etc.)
- **FR-021**: System MUST search for symbol references and show all usage locations
- **FR-022**: System MUST find implementations of interfaces and expect declarations
- **FR-023**: System MUST support fuzzy matching for symbol names
- **FR-024**: System MUST return symbol results with file path, line number, and surrounding context

**User Elicitation:**

- **FR-025**: System MUST provide ask_user tool for interactive questioning
- **FR-026**: ask_user tool MUST support multiple question types: open-ended text, single-select options, multi-select options
- **FR-027**: System MUST use elicitation when detecting ambiguous requirements or missing critical information
- **FR-028**: System MUST present platform-specific questions for cross-platform features (iOS vs Android implementations)
- **FR-029**: System MUST store elicitation responses as part of feature specification or project memory

**Planning Mode:**

- **FR-030**: System MUST provide planning mode that creates structured specification documents
- **FR-031**: Planning mode MUST follow SpecKit specification template structure (user stories, requirements, success criteria)
- **FR-032**: System MUST support spec refinement through iterative questioning and analysis
- **FR-033**: System MUST analyze specifications for completeness, clarity, and consistency
- **FR-034**: System MUST identify dependencies and conflicts between different feature specifications
- **FR-035**: System MUST store specifications in .specify/specs/ directory with version control
- **FR-036**: System MUST allow transition from planning mode to editing mode with task breakdown

**Editing Mode:**

- **FR-037**: System MUST provide editing mode for implementation based on specifications or direct requests
- **FR-038**: Editing mode MUST use LSP for symbol-level code modifications
- **FR-039**: System MUST support operations: add method/property, modify method, delete method, rename symbol, extract function, inline function
- **FR-040**: System MUST maintain expect/actual consistency when modifying platform-specific code
- **FR-041**: System MUST update all symbol references when performing renames or signature changes
- **FR-042**: System MUST preserve code formatting and indentation using language-specific conventions
- **FR-043**: System MUST validate changes using LSP diagnostics before finalizing

**KMP/CMP Domain Knowledge:**

- **FR-044**: System MUST understand KMP source set hierarchy and target relationships
- **FR-045**: System MUST recognize expect/actual declarations and their relationships
- **FR-046**: System MUST understand Kotlin/Native memory model implications for iOS development
- **FR-047**: System MUST recognize Compose Multiplatform composable functions and state management patterns
- **FR-048**: System MUST understand common KMP libraries (Ktor, SQLDelight, Koin, kotlinx.serialization, etc.)
- **FR-049**: System MUST understand common CMP libraries (Voyager, Decompose, Compose Resources, Material3, etc.)

### Key Entities

- **Project**: Represents a KMP/CMP codebase with source sets, dependencies, build configuration, and metadata
- **SourceSet**: Represents a Kotlin source set (commonMain, androidMain, etc.) with associated files and dependencies
- **Symbol**: Represents a code entity (class, function, property, etc.) with name, type, location, and references
- **LSPServer**: Represents a language server instance with lifecycle, capabilities, and communication protocol
- **Memory**: Represents stored project knowledge with content, category, timestamp, and access tracking
- **Specification**: Represents a feature specification document with user stories, requirements, tasks, and status
- **CodeLocation**: Represents a position in code with file path, line number, column, and surrounding context
- **ElicitationQuestion**: Represents an interactive question with question type, options (if applicable), and user response

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System can successfully onboard 95% of standard KMP projects (using kotlin-multiplatform plugin) within 30 seconds
- **SC-002**: Symbol search returns results within 2 seconds for projects with up to 10,000 symbols
- **SC-003**: LSP operations (goto definition, find references) complete within 1 second for 90% of requests
- **SC-004**: Code modifications using symbolic editing are 98% accurate (no syntax errors or unintended changes)
- **SC-005**: System correctly identifies and maintains expect/actual relationships in 99% of cases
- **SC-006**: Memory retrieval and application adds less than 500ms latency to any operation
- **SC-007**: Planning mode produces complete specifications that require less than 2 rounds of refinement for 80% of features
- **SC-008**: User elicitation reduces ambiguous requirements by 70% compared to free-form feature descriptions
- **SC-009**: Cross-language navigation (Kotlin to Swift) works correctly for 95% of interop scenarios
- **SC-010**: System maintains performance with projects containing up to 50,000 lines of code across all source sets

### Quality Metrics

- **SC-011**: All LSP integration code has 90%+ test coverage with integration tests for each language server
- **SC-012**: All code modifications preserve existing formatting and style with 100% consistency
- **SC-013**: Zero data loss for project memories and specifications under normal operation
- **SC-014**: System handles LSP server crashes gracefully with automatic restart and user notification
- **SC-015**: Documentation completeness: all public APIs have pydoc strings, all tools have clear descriptions

### User Experience Metrics

- **SC-016**: Users report 50% reduction in time spent searching for code manually
- **SC-017**: Developers successfully implement features from specifications on first attempt 80% of the time
- **SC-018**: User elicitation questions are relevant and valuable in 90% of cases (measured by user feedback)
- **SC-019**: System provides actionable error messages and recovery suggestions for 100% of error scenarios

## Out of Scope

- IDE plugin development (system operates as MCP server, not IDE extension)
- Gradle build execution and project compilation
- Automated testing execution (system assists with test writing but doesn't run tests)
- Git operations and version control (delegated to external tools)
- Deployment and CI/CD pipeline management
- Real-time collaborative editing
- Code generation from UI mockups or designs
- Performance profiling and optimization analysis

## Dependencies & Prerequisites

- Python 3.10+ runtime environment
- FastMCP 2.0+ for MCP server implementation
- Kotlin Language Server (kotlin-language-server) installed and accessible
- SourceKit-LSP for Swift analysis (on macOS or with appropriate configuration)
- clangd for Objective-C analysis
- Git repository context (optional but recommended for specification management)
- Write access to project directory for memory and specification storage

## Technical Considerations (For Planning Phase)

- LSP communication will be implemented over stdio or TCP depending on language server capabilities
- Language servers will run as separate processes with lifecycle management
- Project indexing may require significant initial processing time for large codebases
- Memory storage will use structured format (JSON or similar) for easy querying and updates
- Specification documents will be stored as Markdown following SpecKit templates
- Symbol caching strategy needed for performance with large projects
- Async operations required for LSP calls to avoid blocking MCP tool execution
- Error handling strategy for LSP server failures, timeouts, and invalid responses

## Open Questions (To Be Resolved During Planning)

1. How should system handle projects with multiple modules (multi-module KMP projects)?
2. What is the strategy for updating project context when build files change?
3. How should system prioritize between multiple LSP results when symbols are ambiguous?
4. What is the user interface for memory management (viewing, editing, deleting memories)?
5. Should system automatically detect and suggest memory entries based on recurring patterns?
6. How should specifications be versioned and linked to implemented code?
7. What is the strategy for handling very large symbol search results (pagination, filtering)?
8. Should system support custom LSP server configurations for non-standard setups?
9. How should system handle different Kotlin compiler versions and language features?
10. What is the caching strategy for LSP results to improve performance?
