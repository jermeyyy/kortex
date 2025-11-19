"""Kortex MCP Server - KMP/CMP Coding Assistant.

This module provides the FastMCP server setup with initialization
and lifecycle management for the Kortex coding assistant.
"""

from pathlib import Path
from typing import Any

from fastmcp import Context, FastMCP

from .lsp.manager import LSPManager
from .storage.memory_store import MemoryStore
from .storage.project_store import ProjectStore
from .storage.spec_store import SpecStore
from .tools import elicitation_tools, project_tools
from .tools.editing_tools import EditingTools
from .tools.lsp_tools import LSPTools
from .tools.memory_tools import MemoryTools
from .tools.planning_tools import PlanningTools
from .utils.logging import get_logger

logger = get_logger(__name__)


# Create FastMCP server instance
mcp = FastMCP("Kortex")


# Global instances (initialized on demand)
_lsp_manager: LSPManager | None = None
_memory_store: MemoryStore | None = None
_project_store: ProjectStore | None = None
_spec_store: SpecStore | None = None
_lsp_tools: LSPTools | None = None
_memory_tools: MemoryTools | None = None
_editing_tools: EditingTools | None = None
_planning_tools: PlanningTools | None = None
_initialized = False


async def initialize_server() -> None:
    """Initialize server components.

    Sets up LSP manager, memory store, project store, spec store, and planning tools.
    Should be called before using any server functionality.
    """
    global _lsp_manager, _memory_store, _project_store, _spec_store, _lsp_tools, _memory_tools, _editing_tools, _planning_tools, _initialized

    if _initialized:
        return

    logger.info("Initializing Kortex server")

    try:
        # Initialize LSP manager
        _lsp_manager = LSPManager(
            health_check_interval=30.0,
            max_restart_attempts=3
        )
        logger.info("LSP manager initialized")

        # Initialize memory store
        memory_store_path = Path.home() / ".kortex" / "memories"
        _memory_store = MemoryStore(memory_store_path)
        await _memory_store.initialize()
        logger.info(f"Memory store initialized at {memory_store_path}")

        # Initialize project store
        project_store_path = Path.home() / ".kortex" / "project.json"
        _project_store = ProjectStore(project_store_path)
        logger.info(f"Project store configured at {project_store_path}")

        # Initialize LSP tools
        _lsp_tools = LSPTools(_lsp_manager)
        logger.info("LSP tools initialized")

        # Initialize memory tools
        _memory_tools = MemoryTools(project_root=Path.cwd())
        await _memory_tools.initialize()
        logger.info("Memory tools initialized")

        # Initialize editing tools
        # Note: KMP analyzer will be needed for editing tools, but it's created on demand in tools
        # For now we pass None and let tools handle it or create a shared one
        # Ideally we should have a global KMPAnalyzer if needed
        _editing_tools = EditingTools(_lsp_manager)
        logger.info("Editing tools initialized")

        # Initialize spec store
        spec_store_path = Path.home() / ".kortex" / "specs"
        _spec_store = SpecStore(spec_store_path)
        logger.info(f"Spec store configured at {spec_store_path}")

        # Initialize planning tools
        _planning_tools = PlanningTools(project_root=Path.cwd())
        await _planning_tools.initialize()
        logger.info("Planning tools initialized")

        _initialized = True
        logger.info("Kortex server initialization complete")

    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise


async def shutdown_server() -> None:
    """Shutdown server components.

    Cleanly stops all LSP servers and saves state.
    Should be called before server exits.
    """
    global _lsp_manager, _initialized

    if not _initialized:
        return

    logger.info("Shutting down Kortex server")

    try:
        # Stop all LSP servers
        if _lsp_manager:
            await _lsp_manager.stop_all()
            logger.info("LSP servers stopped")

        _initialized = False
        logger.info("Kortex server shutdown complete")

    except Exception as e:
        logger.error(f"Error during server shutdown: {e}")


async def ensure_initialized() -> None:
    """Ensure server is initialized."""
    if not _initialized:
        await initialize_server()


def get_lsp_manager() -> LSPManager:
    """Get the global LSP manager instance.

    Returns:
        LSP manager instance

    Raises:
        RuntimeError: If server not initialized
    """
    if _lsp_manager is None:
        raise RuntimeError("Server not initialized. Call initialize_server() first.")
    return _lsp_manager


def get_memory_store() -> MemoryStore:
    """Get the global memory store instance.

    Returns:
        Memory store instance

    Raises:
        RuntimeError: If server not initialized
    """
    if _memory_store is None:
        raise RuntimeError("Server not initialized. Call initialize_server() first.")
    return _memory_store


def get_project_store() -> ProjectStore:
    """Get the global project store instance.

    Returns:
        Project store instance

    Raises:
        RuntimeError: If server not initialized
    """
    if _project_store is None:
        raise RuntimeError("Server not initialized. Call initialize_server() first.")
    return _project_store


def get_lsp_tools() -> LSPTools:
    """Get the global LSP tools instance.

    Returns:
        LSP tools instance

    Raises:
        RuntimeError: If server not initialized
    """
    if _lsp_tools is None:
        raise RuntimeError("Server not initialized. Call initialize_server() first.")
    return _lsp_tools


def get_memory_tools() -> MemoryTools:
    """Get the global memory tools instance.

    Returns:
        Memory tools instance

    Raises:
        RuntimeError: If server not initialized
    """
    if _memory_tools is None:
        raise RuntimeError("Server not initialized. Call initialize_server() first.")
    return _memory_tools


def get_editing_tools() -> EditingTools:
    """Get the global editing tools instance.

    Returns:
        Editing tools instance

    Raises:
        RuntimeError: If server not initialized
    """
    if _editing_tools is None:
        raise RuntimeError("Server not initialized. Call initialize_server() first.")
    return _editing_tools


def get_planning_tools() -> PlanningTools:
    """Get the global planning tools instance.

    Returns:
        Planning tools instance

    Raises:
        RuntimeError: If server not initialized
    """
    if _planning_tools is None:
        raise RuntimeError("Server not initialized. Call initialize_server() first.")
    return _planning_tools


# ===== MCP Tool Endpoints =====

@mcp.tool()
async def search_symbols(query: str, language: str = "kotlin") -> dict[str, Any]:
    """Search for symbols across the workspace.

    Searches for classes, functions, methods, and other symbols in the codebase
    using Language Server Protocol.

    Args:
        query: Symbol name to search for (e.g., "Repository", "UserViewModel")
        language: Programming language to search in (default: "kotlin")

    Returns:
        Dictionary containing:
        - symbols: List of found symbols with name, kind, file location, and line number
        - count: Total number of symbols found
        - query: The search query used

    Example:
        >>> result = await search_symbols("Repository")
        >>> print(f"Found {result['count']} symbols")
    """
    logger.info(f"Tool 'search_symbols' called with query='{query}', language='{language}'")
    await ensure_initialized()
    tools = get_lsp_tools()
    return await tools.search_symbols(query, language)  # type: ignore


@mcp.tool()
async def goto_definition(
    file: str,
    line: int,
    character: int,
    language: str = "kotlin"
) -> dict[str, Any]:
    """Navigate to the definition of a symbol.

    Given a position in a file, finds where the symbol at that position
    is defined using Language Server Protocol.

    Args:
        file: Absolute path to the file
        line: Line number (0-based) where the symbol is located
        character: Character position (0-based) in the line
        language: Programming language (default: "kotlin")

    Returns:
        Dictionary containing:
        - found: Boolean indicating if definition was found
        - definition: Location of definition with file, line, and character (if found)

    Example:
        >>> result = await goto_definition("/project/App.kt", 15, 10)
        >>> if result['found']:
        ...     print(f"Definition at {result['definition']['file']}")
    """
    logger.info(f"Tool 'goto_definition' called for {file}:{line}:{character}")
    await ensure_initialized()
    tools = get_lsp_tools()
    return await tools.goto_definition(file, line, character, language)  # type: ignore


@mcp.tool()
async def find_references(
    file: str,
    line: int,
    character: int,
    include_declaration: bool = True,
    language: str = "kotlin"
) -> dict[str, Any]:
    """Find all references to a symbol.

    Given a position in a file, finds all places where that symbol
    is referenced throughout the codebase using Language Server Protocol.

    Args:
        file: Absolute path to the file
        line: Line number (0-based) where the symbol is located
        character: Character position (0-based) in the line
        include_declaration: Whether to include the declaration in results (default: True)
        language: Programming language (default: "kotlin")

    Returns:
        Dictionary containing:
        - references: List of reference locations with file, line, and character
        - count: Total number of references found

    Example:
        >>> result = await find_references("/project/Repository.kt", 10, 5)
        >>> print(f"Found {result['count']} references")
        >>> for ref in result['references']:
        ...     print(f"  {ref['file']}:{ref['line']}")
    """
    logger.info(f"Tool 'find_references' called for {file}:{line}:{character}")
    await ensure_initialized()
    tools = get_lsp_tools()
    return await tools.find_references(file, line, character, include_declaration, language)  # type: ignore


# ===== Project Tool Endpoints =====

@mcp.tool()
async def onboard_project(project_path: str) -> str:
    """Onboard a new KMP/CMP project.

    Analyzes the project, detects configuration, stores it, and initializes
    LSP servers as appropriate.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with onboarding results including project type, name, and status

    Example:
        >>> result = await onboard_project("/path/to/project")
    """
    logger.info(f"Tool 'onboard_project' called for path: {project_path}")
    return await project_tools.onboard_project_tool(project_path)


@mcp.tool()
async def get_project_info(project_path: str) -> str:
    """Get information about a project.

    Retrieves project configuration including targets, source sets, and dependencies.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with project information

    Example:
        >>> info = await get_project_info("/path/to/project")
    """
    logger.info(f"Tool 'get_project_info' called for path: {project_path}")
    return await project_tools.get_project_info_tool(project_path)


@mcp.tool()
async def list_source_sets(project_path: str) -> str:
    """List project source sets.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with source set list

    Example:
        >>> sets = await list_source_sets("/path/to/project")
    """
    logger.info(f"Tool 'list_source_sets' called for path: {project_path}")
    return await project_tools.list_source_sets_tool(project_path)


@mcp.tool()
async def list_targets(project_path: str) -> str:
    """List project targets.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with target list

    Example:
        >>> targets = await list_targets("/path/to/project")
    """
    logger.info(f"Tool 'list_targets' called for path: {project_path}")
    return await project_tools.list_targets_tool(project_path)


@mcp.tool()
async def detect_project_type(project_path: str) -> str:
    """Detect project type.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with project type

    Example:
        >>> ptype = await detect_project_type("/path/to/project")
    """
    logger.info(f"Tool 'detect_project_type' called for path: {project_path}")
    return await project_tools.detect_project_type_tool(project_path)


# ===== Memory Tool Endpoints =====

@mcp.tool()
async def store_memory(
    category: str,
    title: str,
    content: str,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    memory_id: str | None = None,
) -> dict[str, Any]:
    """Store a new memory or update an existing one.

    Args:
        category: Memory category (architecture, patterns, preferences, etc.)
        title: Short descriptive title
        content: Memory content/description
        tags: Optional list of tags for filtering
        metadata: Optional additional metadata
        memory_id: Optional ID for updating existing memory

    Returns:
        Dictionary with success status and memory details

    Example:
        >>> result = await store_memory(
        ...     category="preferences",
        ...     title="DI Framework",
        ...     content="Use Koin for dependency injection"
        ... )
    """
    logger.info(f"Tool 'store_memory' called with title='{title}'")
    await ensure_initialized()
    tools = get_memory_tools()
    return await tools.store_memory(
        category=category,
        title=title,
        content=content,
        tags=tags,
        metadata=metadata,
        memory_id=memory_id
    )


@mcp.tool()
async def query_memories(
    query: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Query memories by content, category, or tags.

    Args:
        query: Text to search for in title and content
        category: Filter by category
        tags: Filter by tags (must match all provided tags)
        limit: Maximum number of results

    Returns:
        Dictionary with matching memories

    Example:
        >>> result = await query_memories(
        ...     category="patterns",
        ...     tags=["mvvm"]
        ... )
    """
    logger.info(f"Tool 'query_memories' called with query='{query}'")
    await ensure_initialized()
    tools = get_memory_tools()
    return await tools.query_memory(
        search_text=query,
        category=category,
        tags=tags,
        limit=limit
    )


@mcp.tool()
async def list_memories(
    category: str | None = None,
) -> dict[str, Any]:
    """List memories.

    Args:
        category: Optional category filter

    Returns:
        Dictionary with list of memories and total count

    Example:
        >>> result = await list_memories(category="architecture")
    """
    logger.info(f"Tool 'list_memories' called")
    await ensure_initialized()
    tools = get_memory_tools()
    return await tools.list_memories(
        category=category
    )


# ===== Editing Tool Endpoints =====

@mcp.tool()
async def add_method(
    class_name: str,
    method_signature: str,
    method_body: str,
    file_path: str | None = None,
    language: str = "kotlin"
) -> dict[str, Any]:
    """Add a method to a class using LSP-guided insertion.

    Args:
        class_name: Name of the target class
        method_signature: Method signature (e.g., "fun getData(): List<String>")
        method_body: Method implementation code
        file_path: Optional file path if class location is known
        language: Language server to use (default: "kotlin")

    Returns:
        Dictionary with result details

    Example:
        >>> result = await add_method(
        ...     class_name="UserRepository",
        ...     method_signature="fun deleteUser(id: String): Boolean",
        ...     method_body="return database.delete(id)"
        ... )
    """
    logger.info(f"Tool 'add_method' called for class='{class_name}'")
    await ensure_initialized()
    tools = get_editing_tools()
    return await tools.add_method(
        class_name=class_name,
        method_signature=method_signature,
        method_body=method_body,
        file_path=file_path,
        language=language
    )


@mcp.tool()
async def rename_symbol(
    file: str,
    line: int,
    character: int,
    new_name: str,
    language: str = "kotlin"
) -> dict[str, Any]:
    """Rename a symbol and all its references using LSP.

    Args:
        file: File path containing the symbol
        line: Line number of symbol (0-based)
        character: Character position in line (0-based)
        new_name: New name for the symbol
        language: Language server to use (default: "kotlin")

    Returns:
        Dictionary with rename results

    Example:
        >>> result = await rename_symbol(
        ...     file="/project/Repository.kt",
        ...     line=10,
        ...     character=15,
        ...     new_name="DataRepository"
        ... )
    """
    logger.info(f"Tool 'rename_symbol' called for {file}:{line}:{character}")
    await ensure_initialized()
    tools = get_editing_tools()
    return await tools.rename_symbol(
        file=file,
        line=line,
        character=character,
        new_name=new_name,
        language=language
    )


@mcp.tool()
async def validate_expect_actual_consistency(
    symbol_name: str
) -> dict[str, Any]:
    """Validate that expect/actual pairs are consistent after edits.

    Args:
        symbol_name: Name of the expect/actual symbol to validate

    Returns:
        Validation results

    Example:
        >>> result = await validate_expect_actual_consistency("Platform")
    """
    logger.info(f"Tool 'validate_expect_actual_consistency' called for symbol='{symbol_name}'")
    await ensure_initialized()
    tools = get_editing_tools()
    return await tools.validate_expect_actual_consistency(symbol_name)


# ===== User Elicitation Tool Endpoints =====

@mcp.tool()
async def ask_open_ended(ctx: Context, question: str) -> str:
    """Request information from user in natural language.

    Asks a free-form question and collects the user's response.
    This is useful for gathering detailed information, explanations,
    or clarifications that don't fit into predefined options.

    Use this tool when you need:
    - Detailed explanations or descriptions
    - User preferences or opinions
    - Technical specifications or requirements
    - Any information that can't be captured by multiple choice

    Args:
        question: Detailed but brief question to ask the user

    Returns:
        String with the result:
        - "User provided: {response}" if the user answered
        - "User declined to provide information" if declined
        - "Request cancelled by user" if cancelled

    Example:
        >>> # During a feature planning conversation
        >>> result = await ask_open_ended(
        ...     ctx,
        ...     "What should the authentication timeout be and why?"
        ... )
        >>> # Returns: "User provided: 30 minutes for better UX on slow networks"
    """
    logger.info(f"Tool 'ask_open_ended' called with question='{question}'")
    return await elicitation_tools.ask_open_ended(ctx, question)


@mcp.tool()
async def ask_single_select(
    ctx: Context,
    question: str,
    options: list[str]
) -> str:
    """Ask user to select one option from provided choices.

    Presents the user with multiple options and asks them to select one.
    This is useful for choices between known alternatives.

    Use this tool when you need to:
    - Choose between framework options (e.g., Koin vs Hilt)
    - Select architecture patterns (e.g., MVVM vs MVI)
    - Pick implementation approaches
    - Make decisions between well-defined alternatives

    Args:
        question: Detailed but brief question to ask the user
        options: List of detailed but brief options for the user to choose from

    Returns:
        String with the result:
        - "Selected: {option}" if the user made a selection
        - "User declined to select an option" if declined
        - "Selection cancelled by user" if cancelled

    Example:
        >>> # During architecture planning
        >>> result = await ask_single_select(
        ...     ctx,
        ...     "Which dependency injection framework should we use?",
        ...     ["Koin", "Kodein", "Hilt", "Manual DI"]
        ... )
        >>> # Returns: "Selected: Koin"
    """
    logger.info(f"Tool 'ask_single_select' called with question='{question}'")
    return await elicitation_tools.ask_single_select(ctx, question, options)


# ===== Planning Tool Endpoints =====

@mcp.tool()
async def create_spec(
    spec_id: str,
    title: str,
    description: str,
    user_stories: list[dict[str, Any]] | None = None,
    requirements: list[dict[str, Any]] | None = None,
    open_questions: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new specification for Planning Mode.

    Creates a new specification with the provided information. Use this tool
    to document features or changes through conversation with the user.

    The spec_id must follow the format SPEC-XXX (e.g., SPEC-001, SPEC-042).
    After creation, you can refine the spec by adding more details.

    Args:
        spec_id: Unique specification ID (format: SPEC-XXX)
        title: Specification title (e.g., "User Authentication")
        description: High-level description of the feature
        user_stories: Optional list of user story dicts with fields:
            - id: Story ID (e.g., "US-001")
            - title: Story title
            - description: Story description
            - priority: "P1" (high), "P2" (medium), or "P3" (low)
            - acceptance_criteria: List of criteria strings (optional)
            - status: "draft", "in_progress", "completed" (optional)
        requirements: Optional list of requirement dicts with fields:
            - id: Requirement ID (e.g., "REQ-001")
            - type: "functional", "non_functional", "technical" (optional)
            - description: Requirement description
            - rationale: Why this requirement exists (optional)
            - status: "draft", "approved", "implemented" (optional)
        open_questions: Optional list of questions that need answers during refinement.
            Use elicitation tools (ask_open_ended, ask_single_select) to get answers
            from the user, then use refine_spec to add more details.

    Returns:
        Dictionary with creation result:
        - success: Whether creation succeeded
        - spec_id: The specification ID
        - title: The specification title
        - path: Path to the spec file
        - user_stories_count: Number of user stories
        - requirements_count: Number of requirements
        - open_questions_count: Number of open questions

    Example:
        >>> result = await create_spec(
        ...     spec_id="SPEC-001",
        ...     title="User Authentication",
        ...     description="Add OAuth2 authentication to the app",
        ...     open_questions=[
        ...         "What OAuth2 provider should we use?",
        ...         "Should we support offline mode?"
        ...     ]
        ... )
    """
    logger.info(f"Tool 'create_spec' called for spec_id='{spec_id}'")
    await ensure_initialized()
    tools = get_planning_tools()
    return await tools.create_spec(
        spec_id=spec_id,
        title=title,
        description=description,
        user_stories=user_stories,
        requirements=requirements,
        open_questions=open_questions,
    )


@mcp.tool()
async def refine_spec(
    spec_id: str,
    description: str | None = None,
    user_stories: list[dict[str, Any]] | None = None,
    requirements: list[dict[str, Any]] | None = None,
    open_questions: list[str] | None = None,
) -> dict[str, Any]:
    """Refine an existing specification with new information.

    Adds or updates information in an existing specification. Use this to
    incrementally build out the specification through conversation.

    At least one field must be provided. New items are appended to existing lists.
    If description is provided, it replaces the existing description.

    When you see open questions in a spec, use elicitation tools to gather
    answers from the user, then update the spec with the answers.

    Args:
        spec_id: Specification ID to refine
        description: Updated description (replaces existing, optional)
        user_stories: User stories to add (see create_spec for format, optional)
        requirements: Requirements to add (see create_spec for format, optional)
        open_questions: Questions to add to the open questions list (optional)

    Returns:
        Dictionary with refinement result:
        - success: Whether refinement succeeded
        - spec_id: The specification ID
        - updated_fields: List of fields that were updated
        - user_stories_count: Total number of user stories
        - requirements_count: Total number of requirements
        - open_questions_count: Total number of open questions

    Example:
        >>> # After getting answer from user via ask_open_ended
        >>> result = await refine_spec(
        ...     spec_id="SPEC-001",
        ...     user_stories=[{
        ...         "id": "US-002",
        ...         "title": "User Logout",
        ...         "description": "As a user, I want to log out securely",
        ...         "priority": "P2"
        ...     }]
        ... )
    """
    logger.info(f"Tool 'refine_spec' called for spec_id='{spec_id}'")
    await ensure_initialized()
    tools = get_planning_tools()
    return await tools.refine_spec(
        spec_id=spec_id,
        description=description,
        user_stories=user_stories,
        requirements=requirements,
        open_questions=open_questions,
    )


@mcp.tool()
async def generate_template(
    spec_id: str,
    title: str,
    sections: list[str] | None = None,
    platform_sections: dict[str, list[str]] | None = None,
    save_to_disk: bool = False,
) -> dict[str, Any]:
    """Generate a SpecKit-compliant specification template.

    Creates a Markdown template with standard sections for specification
    development. Optionally includes platform-specific sections for KMP projects.

    This is useful for starting a new specification with a standard structure.

    Args:
        spec_id: Specification ID for the template
        title: Specification title
        sections: Optional list of sections to include. Default sections:
            ["description", "user_stories", "requirements"]
            Other available sections: "acceptance_criteria"
        platform_sections: Optional dict mapping platform names to section lists.
            Example: {"android": ["Firebase setup"], "ios": ["APNs setup"]}
        save_to_disk: Whether to save template to disk immediately (default: False)

    Returns:
        Dictionary with template result:
        - success: True
        - spec_id: The specification ID
        - template: The generated template as Markdown string
        - sections: List of sections included
        - path: Path to saved file (if save_to_disk=True)

    Example:
        >>> result = await generate_template(
        ...     spec_id="SPEC-002",
        ...     title="Push Notifications",
        ...     platform_sections={
        ...         "android": ["Firebase setup", "Notification channels"],
        ...         "ios": ["APNs setup", "Notification permissions"]
        ...     },
        ...     save_to_disk=True
        ... )
    """
    logger.info(f"Tool 'generate_template' called for spec_id='{spec_id}'")
    await ensure_initialized()
    tools = get_planning_tools()
    return await tools.generate_template(
        spec_id=spec_id,
        title=title,
        sections=sections,
        platform_sections=platform_sections,
        save_to_disk=save_to_disk,
    )


@mcp.tool()
async def detect_dependencies(
    spec_id: str,
) -> dict[str, Any]:
    """Detect dependencies between specifications.

    Finds other specifications that this spec depends on or that depend
    on this spec. Detects both explicit references (SPEC-XXX IDs) and
    shared concepts (common keywords).

    Use this to understand how specifications relate to each other and
    identify potential circular dependencies.

    Args:
        spec_id: Specification ID to analyze

    Returns:
        Dictionary with dependency detection results:
        - success: True
        - spec_id: The specification ID
        - dependencies: List of spec IDs this spec depends on
        - shared_concepts: List of specs with shared concepts
        - circular_dependencies: List of circular dependency chains (if any)

    Example:
        >>> result = await detect_dependencies(spec_id="SPEC-002")
        >>> if result["dependencies"]:
        ...     print(f"Depends on: {result['dependencies']}")
        >>> if result["circular_dependencies"]:
        ...     print(f"Warning: Circular dependency detected!")
    """
    logger.info(f"Tool 'detect_dependencies' called for spec_id='{spec_id}'")
    await ensure_initialized()
    tools = get_planning_tools()
    return await tools.detect_dependencies(spec_id=spec_id)


@mcp.tool()
async def generate_tasks(
    spec_id: str,
    save_to_disk: bool = False,
) -> dict[str, Any]:
    """Generate actionable tasks from a specification.

    Breaks down the specification into concrete tasks organized by user story.
    Tasks inherit priority from their user story. Use this to convert a
    specification into implementation tasks.

    Args:
        spec_id: Specification ID to generate tasks from
        save_to_disk: Whether to save tasks.md file to disk (default: False)

    Returns:
        Dictionary with task generation results:
        - success: True
        - spec_id: The specification ID
        - tasks: List of task dictionaries with:
            - id: Task ID (T001, T002, etc.)
            - title: Task title
            - description: Task description
            - priority: Priority (from user story)
            - user_story_id: Related user story ID (if applicable)
            - requirement_id: Related requirement ID (if applicable)
        - path: Path to tasks.md file (if save_to_disk=True)

    Example:
        >>> result = await generate_tasks(
        ...     spec_id="SPEC-001",
        ...     save_to_disk=True
        ... )
        >>> print(f"Generated {len(result['tasks'])} tasks")
        >>> for task in result['tasks']:
        ...     print(f"  {task['id']}: {task['title']}")
    """
    logger.info(f"Tool 'generate_tasks' called for spec_id='{spec_id}'")
    await ensure_initialized()
    tools = get_planning_tools()
    return await tools.generate_tasks(
        spec_id=spec_id,
        save_to_disk=save_to_disk,
    )


if __name__ == "__main__":
    mcp.run()
