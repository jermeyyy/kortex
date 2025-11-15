"""Kortex MCP Server - KMP/CMP Coding Assistant.

This module provides the FastMCP server setup with initialization
and lifecycle management for the Kortex coding assistant.
"""

import asyncio
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .utils.logging import get_logger
from .lsp.manager import LSPManager
from .storage.memory_store import MemoryStore
from .storage.project_store import ProjectStore


logger = get_logger(__name__)


# Create FastMCP server instance
mcp = FastMCP("Kortex")


# Global instances (initialized on demand)
_lsp_manager: Optional[LSPManager] = None
_memory_store: Optional[MemoryStore] = None
_project_store: Optional[ProjectStore] = None
_initialized = False


async def initialize_server() -> None:
    """Initialize server components.

    Sets up LSP manager, memory store, and project store.
    Should be called before using any server functionality.
    """
    global _lsp_manager, _memory_store, _project_store, _initialized
    
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


if __name__ == "__main__":
    mcp.run()


