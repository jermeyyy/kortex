"""Kortex MCP Server - KMP/CMP Coding Assistant.

This module provides the FastMCP server setup with initialization
and lifecycle management for the Kortex coding assistant.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastmcp import FastMCP, Context

from .utils.logging import get_logger
from .lsp.manager import LSPManager
from .storage.memory_store import MemoryStore
from .storage.project_store import ProjectStore
from .storage.spec_store import SpecStore
from .tools.lsp_tools import LSPTools
from .tools.planning_tools import PlanningTools
from .tools import elicitation_tools


logger = get_logger(__name__)


# Create FastMCP server instance
mcp = FastMCP("Kortex")


# Global instances (initialized on demand)
_lsp_manager: Optional[LSPManager] = None
_memory_store: Optional[MemoryStore] = None
_project_store: Optional[ProjectStore] = None
_spec_store: Optional[SpecStore] = None
_lsp_tools: Optional[LSPTools] = None
_planning_tools: Optional[PlanningTools] = None
_initialized = False


async def initialize_server() -> None:
    """Initialize server components.

    Sets up LSP manager, memory store, project store, spec store, and planning tools.
    Should be called before using any server functionality.
    """
    global _lsp_manager, _memory_store, _project_store, _spec_store, _lsp_tools, _planning_tools, _initialized
    
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
async def search_symbols(query: str, language: str = "kotlin") -> Dict[str, Any]:
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
    await ensure_initialized()
    tools = get_lsp_tools()
    return await tools.search_symbols(query, language)


@mcp.tool()
async def goto_definition(
    file: str,
    line: int,
    character: int,
    language: str = "kotlin"
) -> Dict[str, Any]:
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
    await ensure_initialized()
    tools = get_lsp_tools()
    return await tools.goto_definition(file, line, character, language)


@mcp.tool()
async def find_references(
    file: str,
    line: int,
    character: int,
    include_declaration: bool = True,
    language: str = "kotlin"
) -> Dict[str, Any]:
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
    await ensure_initialized()
    tools = get_lsp_tools()
    return await tools.find_references(file, line, character, include_declaration, language)


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
    return await elicitation_tools.ask_open_ended(ctx, question)


@mcp.tool()
async def ask_single_select(
    ctx: Context,
    question: str,
    options: List[str]
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
    return await elicitation_tools.ask_single_select(ctx, question, options)


# ===== Planning Tool Endpoints =====

@mcp.tool()
async def create_spec(
    spec_id: str,
    title: str,
    description: str,
    user_stories: Optional[List[Dict[str, Any]]] = None,
    requirements: Optional[List[Dict[str, Any]]] = None,
    open_questions: Optional[List[str]] = None,
) -> Dict[str, Any]:
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
    description: Optional[str] = None,
    user_stories: Optional[List[Dict[str, Any]]] = None,
    requirements: Optional[List[Dict[str, Any]]] = None,
    open_questions: Optional[List[str]] = None,
) -> Dict[str, Any]:
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
    sections: Optional[List[str]] = None,
    platform_sections: Optional[Dict[str, List[str]]] = None,
    save_to_disk: bool = False,
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
    await ensure_initialized()
    tools = get_planning_tools()
    return await tools.detect_dependencies(spec_id=spec_id)


@mcp.tool()
async def generate_tasks(
    spec_id: str,
    save_to_disk: bool = False,
) -> Dict[str, Any]:
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
    await ensure_initialized()
    tools = get_planning_tools()
    return await tools.generate_tasks(
        spec_id=spec_id,
        save_to_disk=save_to_disk,
    )


if __name__ == "__main__":
    mcp.run()
