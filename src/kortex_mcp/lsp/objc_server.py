"""Objective-C Language Server integration (clangd).

This module provides configuration and setup for clangd,
which provides LSP capabilities for Objective-C and C++ projects
in Kotlin Multiplatform projects with iOS implementations.
"""

from pathlib import Path
from typing import Optional, Dict, List
import shutil

from .client import LSPClient
from ..utils.logging import get_logger


logger = get_logger(__name__)


class ObjCLSPServer:
    """Objective-C Language Server (clangd) manager.
    
    Handles configuration and lifecycle of clangd for Objective-C code
    analysis in KMP projects with iOS implementations.
    
    Attributes:
        client: Underlying LSP client instance
        workspace_path: Path to workspace root
        language_id: Language identifier ("objective-c")
        
    Example:
        >>> server = ObjCLSPServer(workspace_path=Path("/project"))
        >>> await server.start()
        >>> symbols = await server.search_symbols("SharedRepository")
        >>> await server.stop()
    """
    
    def __init__(
        self,
        workspace_path: Path,
        clangd_path: Optional[str] = None,
        clangd_args: Optional[List[str]] = None,
    ):
        """Initialize Objective-C LSP server.
        
        Args:
            workspace_path: Path to workspace root (KMP project with iOS code)
            clangd_path: Custom clangd command path (default: auto-detect)
            clangd_args: Additional clangd arguments (default: basic config)
            
        Raises:
            FileNotFoundError: If clangd not found and required
        """
        self.workspace_path = workspace_path
        self.language_id = "objective-c"
        
        # Auto-detect clangd if not provided
        if clangd_path is None:
            clangd_path = self._find_clangd()
        
        self.command = clangd_path
        
        # Default clangd arguments
        if clangd_args is None:
            clangd_args = [
                "--background-index",  # Build index in background
                "--header-insertion=never",  # Don't auto-insert headers
            ]
        
        self.args = clangd_args
        
        # Create LSP client with Objective-C-specific configuration
        self.client = LSPClient(
            command=self.command,
            args=self.args,
            workspace_path=workspace_path,
            env=self._get_environment_vars(),
        )
    
    def _find_clangd(self) -> str:
        """Find clangd executable.
        
        Returns:
            Path to clangd executable
            
        Raises:
            FileNotFoundError: If server executable not found
        """
        # Try common installation locations
        candidates = [
            "clangd",  # In PATH
            "/usr/bin/clangd",
            "/usr/local/bin/clangd",
            "/opt/homebrew/bin/clangd",
            "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clangd",
        ]
        
        for candidate in candidates:
            if Path(candidate).exists() or shutil.which(candidate):
                logger.info(f"Found clangd: {candidate}")
                return candidate
        
        # If not found, return default and let subprocess fail with better error
        logger.warning("clangd not found in standard locations")
        return "clangd"
    
    def _get_environment_vars(self) -> Dict[str, str]:
        """Get environment variables for clangd.
        
        Returns:
            Dictionary of environment variables
        """
        import os
        
        env = os.environ.copy()
        
        # Add Objective-C/clang-specific environment configuration
        # clangd may need DEVELOPER_DIR for Xcode SDK access
        if "DEVELOPER_DIR" not in env:
            xcode_path = "/Applications/Xcode.app/Contents/Developer"
            if Path(xcode_path).exists():
                env["DEVELOPER_DIR"] = xcode_path
        
        return env
    
    def get_initialization_options(self) -> Dict:
        """Get clangd-specific initialization options.
        
        Returns:
            Dictionary of initialization options for clangd
        """
        # clangd initialization options
        return {
            "compilationDatabasePath": str(self.workspace_path / "build"),
            "fallbackFlags": [
                "-isysroot",
                "/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk",
                "-I/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/usr/include",
                "-fobjc-arc",  # Enable ARC
                "-fmodules",  # Enable modules
            ]
        }
    
    async def start(self) -> None:
        """Start the clangd server.
        
        Raises:
            RuntimeError: If server fails to start
            asyncio.TimeoutError: If initialization times out
            
        Example:
            >>> await server.start()
        """
        logger.info(f"Starting clangd for workspace: {self.workspace_path}")
        await self.client.start()
        self.client._initialized = True
        logger.info("clangd started successfully")
    
    async def stop(self) -> None:
        """Stop the clangd server.
        
        Example:
            >>> await server.stop()
        """
        logger.info("Stopping clangd")
        await self.client.stop()
        logger.info("clangd stopped")
    
    def supports_file(self, file_path: Path) -> bool:
        """Check if server supports given file type.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file is an Objective-C file (.m, .h, .mm)
            
        Example:
            >>> server.supports_file(Path("MyClass.m"))
            True
            >>> server.supports_file(Path("MyClass.h"))
            True
            >>> server.supports_file(Path("MyClass.swift"))
            False
        """
        suffix = file_path.suffix.lower()
        return suffix in [".m", ".h", ".mm"]
    
    async def workspace_symbol(self, query: str) -> List[Dict]:
        """Search for symbols in Objective-C files.
        
        Args:
            query: Symbol search query (e.g., "SharedRepository")
            
        Returns:
            List of SymbolInformation dictionaries
            
        Raises:
            RuntimeError: If server is not running
            
        Example:
            >>> symbols = await server.workspace_symbol("Repository")
            >>> for symbol in symbols:
            ...     print(f"{symbol['name']} at {symbol['location']['uri']}")
        """
        if not self.is_running():
            raise RuntimeError("clangd is not running")
        
        # Use client's workspace_symbols method
        symbols = await self.client.workspace_symbols(query)
        
        # Convert to dict format for easier consumption
        return [
            {
                "name": sym.name,
                "kind": sym.kind,
                "location": {
                    "uri": sym.location.uri,
                    "range": {
                        "start": {
                            "line": sym.location.range.start.line,
                            "character": sym.location.range.start.character
                        },
                        "end": {
                            "line": sym.location.range.end.line,
                            "character": sym.location.range.end.character
                        }
                    }
                },
                "containerName": sym.containerName
            }
            for sym in symbols
        ]
    
    async def goto_definition(self, file_path: Path, position: Dict) -> Optional[Dict]:
        """Go to definition of symbol at position.
        
        Args:
            file_path: Path to Objective-C file
            position: Position dictionary with 'line' and 'character'
            
        Returns:
            Location dictionary or None if not found
            
        Raises:
            RuntimeError: If server is not running
            ValueError: If file is not an Objective-C file
            
        Example:
            >>> location = await server.goto_definition(
            ...     Path("MyClass.m"),
            ...     {"line": 10, "character": 5}
            ... )
        """
        if not self.is_running():
            raise RuntimeError("clangd is not running")
        
        if not self.supports_file(file_path):
            raise ValueError(f"File {file_path} is not an Objective-C file")
        
        # Use client's go_to_definition method
        location = await self.client.go_to_definition(
            file_uri=file_path.as_uri(),
            line=position["line"],
            character=position["character"]
        )
        
        # Convert Location object to dict if found
        if location:
            return {
                "uri": location.uri,
                "range": {
                    "start": {
                        "line": location.range.start.line,
                        "character": location.range.start.character
                    },
                    "end": {
                        "line": location.range.end.line,
                        "character": location.range.end.character
                    }
                }
            }
        return None
    
    def is_running(self) -> bool:
        """Check if clangd server is running.
        
        Returns:
            True if server process is active
            
        Example:
            >>> if server.is_running():
            ...     symbols = await server.workspace_symbol("Foo")
        """
        return (
            self.client.process is not None 
            and self.client.process.returncode is None
            and self.client._initialized
        )
    
    async def find_references(self, file_path: Path, position: Dict) -> List[Dict]:
        """Find all references to symbol at position.
        
        Args:
            file_path: Path to Objective-C file
            position: Position dictionary with 'line' and 'character'
            
        Returns:
            List of Location dictionaries
            
        Raises:
            RuntimeError: If server is not running
            ValueError: If file is not an Objective-C file
            
        Example:
            >>> refs = await server.find_references(
            ...     Path("MyClass.m"),
            ...     {"line": 10, "character": 5}
            ... )
        """
        if not self.is_running():
            raise RuntimeError("clangd is not running")
        
        if not self.supports_file(file_path):
            raise ValueError(f"File {file_path} is not an Objective-C file")
        
        # Use client's find_references method
        locations = await self.client.find_references(
            file_uri=file_path.as_uri(),
            line=position["line"],
            character=position["character"],
            include_declaration=True
        )
        
        # Convert Location objects to dicts
        return [
            {
                "uri": loc.uri,
                "range": {
                    "start": {
                        "line": loc.range.start.line,
                        "character": loc.range.start.character
                    },
                    "end": {
                        "line": loc.range.end.line,
                        "character": loc.range.end.character
                    }
                }
            }
            for loc in locations
        ]
