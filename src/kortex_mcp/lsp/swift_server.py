"""Swift Language Server integration (SourceKit-LSP).

This module provides configuration and setup for SourceKit-LSP,
which provides LSP capabilities for Swift projects and iOS code
in Kotlin Multiplatform projects.
"""

import shutil
from pathlib import Path

from ..utils.logging import get_logger
from .client import LSPClient

logger = get_logger(__name__)


class SwiftLSPServer:
    """Swift Language Server (SourceKit-LSP) manager.

    Handles configuration and lifecycle of SourceKit-LSP for Swift code
    analysis in KMP projects with iOS implementations.

    Attributes:
        client: Underlying LSP client instance
        workspace_path: Path to workspace root
        language_id: Language identifier ("swift")

    Example:
        >>> server = SwiftLSPServer(workspace_path=Path("/project"))
        >>> await server.start()
        >>> symbols = await server.search_symbols("SharedRepository")
        >>> await server.stop()
    """

    def __init__(
        self,
        workspace_path: Path,
        sourcekit_path: str | None = None,
    ):
        """Initialize Swift LSP server.

        Args:
            workspace_path: Path to workspace root (KMP project with iOS code)
            sourcekit_path: Custom SourceKit-LSP command path (default: auto-detect)

        Raises:
            FileNotFoundError: If SourceKit-LSP not found and required
        """
        self.workspace_path = workspace_path
        self.language_id = "swift"

        # Auto-detect SourceKit-LSP if not provided
        if sourcekit_path is None:
            sourcekit_path = self._find_sourcekit_lsp()

        self.command = sourcekit_path

        # Create LSP client with Swift-specific configuration
        self.client = LSPClient(
            command=self.command,
            args=[],  # SourceKit-LSP uses stdio by default
            workspace_path=workspace_path,
            env=self._get_environment_vars(),
        )

    def _find_sourcekit_lsp(self) -> str:
        """Find SourceKit-LSP executable.

        Returns:
            Path to sourcekit-lsp executable

        Raises:
            FileNotFoundError: If server executable not found
        """
        # Try common installation locations
        candidates = [
            "sourcekit-lsp",  # In PATH
            "/usr/bin/sourcekit-lsp",
            "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/sourcekit-lsp",
            str(Path.home() / "Library" / "Developer" / "Toolchains" / "swift-latest.xctoolchain" / "usr" / "bin" / "sourcekit-lsp"),
        ]

        for candidate in candidates:
            if Path(candidate).exists() or shutil.which(candidate):
                logger.info(f"Found SourceKit-LSP: {candidate}")
                return candidate

        # If not found, return default and let subprocess fail with better error
        logger.warning("SourceKit-LSP not found in standard locations")
        return "sourcekit-lsp"

    def _get_environment_vars(self) -> dict[str, str]:
        """Get environment variables for SourceKit-LSP.

        Returns:
            Dictionary of environment variables
        """
        import os

        env = os.environ.copy()

        # Add Swift-specific environment configuration
        # SourceKit-LSP may need DEVELOPER_DIR set
        if "DEVELOPER_DIR" not in env:
            xcode_path = "/Applications/Xcode.app/Contents/Developer"
            if Path(xcode_path).exists():
                env["DEVELOPER_DIR"] = xcode_path

        return env

    def get_initialization_options(self) -> dict:
        """Get Swift-specific initialization options.

        Returns:
            Dictionary of initialization options for SourceKit-LSP
        """
        # SourceKit-LSP initialization options
        return {
            "capabilities": {
                "workspace": {
                    "configuration": True,
                    "workspaceFolders": True,
                }
            }
        }

    async def start(self) -> None:
        """Start the SourceKit-LSP server.

        Raises:
            RuntimeError: If server fails to start
            asyncio.TimeoutError: If initialization times out

        Example:
            >>> await server.start()
        """
        logger.info(f"Starting SourceKit-LSP for workspace: {self.workspace_path}")
        await self.client.start()
        self.client._initialized = True
        logger.info("SourceKit-LSP started successfully")

    async def stop(self) -> None:
        """Stop the SourceKit-LSP server.

        Example:
            >>> await server.stop()
        """
        logger.info("Stopping SourceKit-LSP")
        await self.client.stop()
        logger.info("SourceKit-LSP stopped")

    def supports_file(self, file_path: Path) -> bool:
        """Check if server supports given file type.

        Args:
            file_path: Path to file to check

        Returns:
            True if file is a Swift file (.swift)

        Example:
            >>> server.supports_file(Path("MyClass.swift"))
            True
            >>> server.supports_file(Path("MyClass.kt"))
            False
        """
        return file_path.suffix.lower() == ".swift"

    async def workspace_symbol(self, query: str) -> list[dict]:
        """Search for symbols in Swift files.

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
            raise RuntimeError("SourceKit-LSP is not running")

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

    async def goto_definition(self, file_path: Path, position: dict) -> dict | None:
        """Go to definition of symbol at position.

        Args:
            file_path: Path to Swift file
            position: Position dictionary with 'line' and 'character'

        Returns:
            Location dictionary or None if not found

        Raises:
            RuntimeError: If server is not running
            ValueError: If file is not a Swift file

        Example:
            >>> location = await server.goto_definition(
            ...     Path("MyClass.swift"),
            ...     {"line": 10, "character": 5}
            ... )
        """
        if not self.is_running():
            raise RuntimeError("SourceKit-LSP is not running")

        if not self.supports_file(file_path):
            raise ValueError(f"File {file_path} is not a Swift file")

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
        """Check if SourceKit-LSP server is running.

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

    async def find_references(self, file_path: Path, position: dict) -> list[dict]:
        """Find all references to symbol at position.

        Args:
            file_path: Path to Swift file
            position: Position dictionary with 'line' and 'character'

        Returns:
            List of Location dictionaries

        Raises:
            RuntimeError: If server is not running
            ValueError: If file is not a Swift file

        Example:
            >>> refs = await server.find_references(
            ...     Path("MyClass.swift"),
            ...     {"line": 10, "character": 5}
            ... )
        """
        if not self.is_running():
            raise RuntimeError("SourceKit-LSP is not running")

        if not self.supports_file(file_path):
            raise ValueError(f"File {file_path} is not a Swift file")

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
