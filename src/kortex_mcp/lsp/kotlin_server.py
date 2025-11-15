"""Kotlin Language Server integration.

This module provides configuration and setup for the Kotlin Language Server,
which provides LSP capabilities for Kotlin and KMP projects.
"""

from pathlib import Path
from typing import Optional, Dict, List
import shutil

from .client import LSPClient
from ..utils.logging import get_logger


logger = get_logger(__name__)


class KotlinLSPServer:
    """Kotlin Language Server manager.
    
    Handles configuration and lifecycle of the Kotlin Language Server
    for KMP project navigation and code intelligence.
    
    Attributes:
        client: Underlying LSP client instance
        workspace_path: Path to workspace root
        
    Example:
        >>> server = KotlinLSPServer(workspace_path=Path("/project"))
        >>> await server.start()
        >>> symbols = await server.search_symbols("Repository")
        >>> await server.stop()
    """
    
    def __init__(
        self,
        workspace_path: Path,
        server_command: Optional[str] = None,
    ):
        """Initialize Kotlin LSP server.
        
        Args:
            workspace_path: Path to workspace root (KMP project)
            server_command: Custom server command (default: auto-detect)
            
        Raises:
            FileNotFoundError: If Kotlin language server not found
        """
        self.workspace_path = workspace_path
        
        # Auto-detect Kotlin language server if not provided
        if server_command is None:
            server_command = self._find_kotlin_language_server()
        
        self.server_command = server_command
        
        # Create LSP client with Kotlin-specific configuration
        self.client = LSPClient(
            command=self.server_command,
            args=[],  # Kotlin LS uses stdio by default
            workspace_path=workspace_path,
            env=self._get_environment_vars(),
        )
    
    def _find_kotlin_language_server(self) -> str:
        """Find Kotlin language server executable.
        
        Returns:
            Path to kotlin-lsp executable
            
        Raises:
            FileNotFoundError: If server executable not found
        """
        # Try common installation locations
        candidates = [
            "kotlin-lsp",  # In PATH (modern installation)
            "kotlin-language-server",  # Legacy name
            "kotlin-language-server.bat",  # Windows
            str(Path.home() / ".local" / "bin" / "kotlin-lsp"),
            "/opt/homebrew/bin/kotlin-lsp",
            "/usr/local/bin/kotlin-lsp",
            str(Path.home() / ".local" / "bin" / "kotlin-language-server"),
            "/usr/local/bin/kotlin-language-server",
            "/opt/homebrew/bin/kotlin-language-server",
        ]
        
        for candidate in candidates:
            if shutil.which(candidate):
                logger.info(f"Found Kotlin language server: {candidate}")
                return candidate
        
        # If not found, return default and let subprocess fail with better error
        logger.warning("Kotlin language server not found in PATH")
        return "kotlin-lsp"
    
    def _get_environment_vars(self) -> Dict[str, str]:
        """Get environment variables for Kotlin language server.
        
        Returns:
            Dictionary of environment variables
        """
        import os
        
        env = os.environ.copy()
        
        # Add any Kotlin-specific environment configuration
        # For example, Java home or Kotlin compiler paths
        if "JAVA_HOME" not in env:
            # Try to find Java
            java_home = shutil.which("java")
            if java_home:
                env["JAVA_HOME"] = str(Path(java_home).parent.parent)
        
        return env
    
    async def start(self) -> None:
        """Start the Kotlin language server.
        
        Raises:
            RuntimeError: If server fails to start
            asyncio.TimeoutError: If initialization times out
            
        Example:
            >>> await server.start()
        """
        logger.info(f"Starting Kotlin language server for workspace: {self.workspace_path}")
        await self.client.start()
        logger.info("Kotlin language server started successfully")
    
    async def stop(self) -> None:
        """Stop the Kotlin language server.
        
        Example:
            >>> await server.stop()
        """
        logger.info("Stopping Kotlin language server")
        await self.client.stop()
        logger.info("Kotlin language server stopped")
    
    async def search_symbols(self, query: str) -> List[Dict]:
        """Search for symbols in the workspace.
        
        Args:
            query: Symbol search query (e.g., "Repository")
            
        Returns:
            List of symbols with metadata
            
        Raises:
            RuntimeError: If server is not running
            
        Example:
            >>> symbols = await server.search_symbols("Repository")
            >>> for symbol in symbols:
            ...     print(f"{symbol['name']} at {symbol['file']}:{symbol['line']}")
        """
        symbols = await self.client.workspace_symbols(query)
        
        # Convert to user-friendly format
        results = []
        for symbol in symbols:
            # Convert URI to file path
            file_path = symbol.location.uri
            if file_path.startswith("file://"):
                file_path = file_path[7:]  # Remove file:// prefix
            
            results.append({
                "name": symbol.name,
                "kind": self._symbol_kind_to_string(symbol.kind),
                "file": file_path,
                "line": symbol.location.range.start.line,
                "character": symbol.location.range.start.character,
                "container": symbol.containerName or "",
            })
        
        return results
    
    def _symbol_kind_to_string(self, kind: int) -> str:
        """Convert LSP symbol kind integer to readable string.
        
        Args:
            kind: LSP SymbolKind integer
            
        Returns:
            Human-readable symbol kind
        """
        # LSP SymbolKind enumeration
        kinds = {
            1: "file",
            2: "module",
            3: "namespace",
            4: "package",
            5: "class",
            6: "method",
            7: "property",
            8: "field",
            9: "constructor",
            10: "enum",
            11: "interface",
            12: "function",
            13: "variable",
            14: "constant",
            15: "string",
            16: "number",
            17: "boolean",
            18: "array",
            19: "object",
            20: "key",
            21: "null",
            22: "enum_member",
            23: "struct",
            24: "event",
            25: "operator",
            26: "type_parameter",
        }
        return kinds.get(kind, "unknown")
    
    def is_running(self) -> bool:
        """Check if Kotlin language server is running.
        
        Returns:
            True if server is running
            
        Example:
            >>> if server.is_running():
            ...     print("Server ready")
        """
        return self.client.is_running()
