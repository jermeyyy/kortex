"""Kortex MCP Server - KMP/CMP Coding Assistant.

This module provides the FastMCP server setup with initialization
and lifecycle management for the Kortex coding assistant.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastmcp import FastMCP

from .utils.logging import get_logger
from .lsp.manager import LSPManager
from .storage.memory_store import MemoryStore
from .storage.project_store import ProjectStore
from .tools.lsp_tools import LSPTools


logger = get_logger(__name__)


# Create FastMCP server instance
mcp = FastMCP("Kortex")


# Global instances (initialized on demand)
_lsp_manager: Optional[LSPManager] = None
_memory_store: Optional[MemoryStore] = None
_project_store: Optional[ProjectStore] = None
_lsp_tools: Optional[LSPTools] = None
_initialized = False


async def initialize_server() -> None:
    """Initialize server components.

    Sets up LSP manager, memory store, and project store.
    Should be called before using any server functionality.
    """
    global _lsp_manager, _memory_store, _project_store, _lsp_tools, _initialized
    
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


if __name__ == "__main__":
    mcp.run()
