"""Project onboarding and management tools.

This module provides MCP tools for project onboarding, querying project
information, and initializing LSP servers based on detected project configuration.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..utils.logging import get_logger
from ..analyzers.project_analyzer import ProjectAnalyzer, analyze_project, detect_project_type
from ..storage.project_store import ProjectStore
from ..models.project import Project, ProjectType
from ..lsp.manager import LSPManager
from ..lsp.kotlin_server import KotlinLSPServer


logger = get_logger(__name__)


async def onboard_project(project_dir: Path) -> Dict[str, Any]:
    """Onboard a new KMP/CMP project.

    Analyzes the project, detects configuration, stores it, and initializes
    LSP servers as appropriate.

    Args:
        project_dir: Path to project root directory

    Returns:
        Dictionary with onboarding results including project type, name, and status

    Raises:
        FileNotFoundError: If project directory doesn't exist

    Example:
        >>> result = await onboard_project(Path("/path/to/project"))
        >>> print(f"Onboarded {result['name']} as {result['type']}")
    """
    logger.info(f"Onboarding project: {project_dir}")

    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    # Analyze project
    project = await analyze_project(project_dir)

    # Store project configuration
    store_path = project_dir / ".kortex" / "project.json"
    store = ProjectStore(store_path)
    await store.save(project)

    logger.info(f"Project {project.name} onboarded successfully")

    return {
        "success": True,
        "name": project.name,
        "type": project.type.value,
        "project_type": project.type,
        "source_sets": len(project.source_sets),
        "targets": len(project.targets),
        "message": f"Successfully onboarded {project.name} ({project.type.value})"
    }


async def get_project_info(project_dir: Path) -> Dict[str, Any]:
    """Get information about a project.

    Retrieves project configuration including targets, source sets, and dependencies.
    If project hasn't been onboarded, performs onboarding first.

    Args:
        project_dir: Path to project root directory

    Returns:
        Dictionary with project information

    Example:
        >>> info = await get_project_info(Path("/path/to/project"))
        >>> for target in info["targets"]:
        ...     print(f"Target: {target['name']}")
    """
    logger.debug(f"Getting project info for: {project_dir}")

    # Try to load from store first
    store_path = project_dir / ".kortex" / "project.json"
    store = ProjectStore(store_path)
    project = await store.load()

    # If not found, onboard the project
    if project is None:
        logger.debug("Project not in store, analyzing...")
        project = await analyze_project(project_dir)
        await store.save(project)

    # Convert to dictionary format
    return {
        "name": project.name,
        "type": project.type.value,
        "root_path": str(project.root_path),
        "targets": [
            {
                "name": t.name,
                "platform": t.platform,
                "source_sets": t.source_sets
            }
            for t in project.targets
        ],
        "source_sets": [
            {
                "name": ss.name,
                "type": ss.type.value,
                "dependencies": ss.dependencies,
                "depends_on": ss.depends_on,
                "source_dirs": [str(d) for d in ss.source_dirs],
                "resource_dirs": [str(d) for d in ss.resource_dirs]
            }
            for ss in project.source_sets.values()
        ],
        "dependencies": list(set(
            dep
            for ss in project.source_sets.values()
            for dep in ss.dependencies
        )),
        "kotlin_version": project.kotlin_version,
        "compose_version": project.compose_version
    }


async def initialize_lsp_servers(project_dir: Path) -> Dict[str, Any]:
    """Initialize LSP servers based on project configuration.

    Starts appropriate language servers (Kotlin, Swift, Objective-C) based on
    the detected project targets.

    Args:
        project_dir: Path to project root directory

    Returns:
        Dictionary with information about started servers

    Example:
        >>> result = await initialize_lsp_servers(Path("/path/to/project"))
        >>> print(f"Started {len(result['servers'])} LSP servers")
    """
    logger.info(f"Initializing LSP servers for: {project_dir}")

    # Get or analyze project
    store_path = project_dir / ".kortex" / "project.json"
    store = ProjectStore(store_path)
    project = await store.load()

    if project is None:
        project = await analyze_project(project_dir)

    started_servers = []
    failed_servers = []

    # Always start Kotlin LSP for KMP/CMP projects
    # Note: Kotlin LSP handles .gradle.kts files as they are Kotlin Script
    if project.type in (ProjectType.KMP, ProjectType.CMP):
        try:
            kotlin_server = KotlinLSPServer(workspace_path=project_dir)
            manager = LSPManager()
            
            # Start the Kotlin LSP server
            await kotlin_server.start()
            started_servers.append("kotlin")
            logger.info("Kotlin LSP server started")
        except Exception as e:
            logger.error(f"Failed to start Kotlin LSP: {e}")
            failed_servers.append({"server": "kotlin", "error": str(e)})

    # Check if we need Swift LSP (for iOS targets)
    has_ios_target = any("ios" in t.platform.lower() for t in project.targets)
    
    if has_ios_target:
        try:
            # Import here to avoid circular dependency
            from ..lsp.swift_server import SwiftLSPServer
            
            swift_server = SwiftLSPServer(workspace_path=project_dir)
            
            # Start the Swift LSP server
            await swift_server.start()
            started_servers.append("swift")
            logger.info("Swift LSP server started")
        except Exception as e:
            logger.warning(f"Swift LSP not available: {e}")
            # Swift is optional, don't treat as failure

    logger.info(f"LSP initialization complete: {len(started_servers)} servers started")

    return {
        "servers": started_servers,
        "failed": failed_servers,
        "project_type": project.type.value
    }


# MCP Tool definitions for FastMCP integration
# These will be registered with the FastMCP server


async def onboard_project_tool(project_path: str) -> str:
    """MCP tool to onboard a KMP/CMP project.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with onboarding results

    Example:
        >>> result = await onboard_project_tool("/path/to/project")
    """
    import json
    
    project_dir = Path(project_path).expanduser().resolve()
    result = await onboard_project(project_dir)
    return json.dumps(result, indent=2)


async def get_project_info_tool(project_path: str) -> str:
    """MCP tool to get project information.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with project information

    Example:
        >>> info = await get_project_info_tool("/path/to/project")
    """
    import json
    
    project_dir = Path(project_path).expanduser().resolve()
    info = await get_project_info(project_dir)
    return json.dumps(info, indent=2)


async def list_source_sets_tool(project_path: str) -> str:
    """MCP tool to list project source sets.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with source set list

    Example:
        >>> sets = await list_source_sets_tool("/path/to/project")
    """
    import json
    
    project_dir = Path(project_path).expanduser().resolve()
    info = await get_project_info(project_dir)
    
    source_sets = info["source_sets"]
    return json.dumps({
        "source_sets": source_sets,
        "count": len(source_sets)
    }, indent=2)


async def list_targets_tool(project_path: str) -> str:
    """MCP tool to list project targets.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with target list

    Example:
        >>> targets = await list_targets_tool("/path/to/project")
    """
    import json
    
    project_dir = Path(project_path).expanduser().resolve()
    info = await get_project_info(project_dir)
    
    targets = info["targets"]
    return json.dumps({
        "targets": targets,
        "count": len(targets)
    }, indent=2)


async def detect_project_type_tool(project_path: str) -> str:
    """MCP tool to detect project type.

    Args:
        project_path: Path to project root directory

    Returns:
        JSON string with project type

    Example:
        >>> ptype = await detect_project_type_tool("/path/to/project")
    """
    import json
    
    project_dir = Path(project_path).expanduser().resolve()
    ptype = detect_project_type(project_dir)
    
    return json.dumps({
        "path": str(project_dir),
        "type": ptype.value,
        "is_kmp": ptype in (ProjectType.KMP, ProjectType.CMP),
        "is_cmp": ptype == ProjectType.CMP
    }, indent=2)
