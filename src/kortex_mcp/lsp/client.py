"""Base LSP client for communication with language servers.

This module provides the core LSP client functionality for starting,
managing, and communicating with language servers via JSON-RPC.
"""

import asyncio
import json
from asyncio.subprocess import Process
from pathlib import Path
from typing import Any

from ..models.lsp import (
    Location,
    Position,
    Range,
    SymbolInformation,
    TextEdit,
    WorkspaceEdit,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class LSPClient:
    """Base Language Server Protocol client.

    Handles JSON-RPC communication with language servers over stdio.

    Attributes:
        command: Command to start the language server
        args: Arguments for the language server command
        workspace_path: Path to workspace root
        process: Subprocess running the language server
        request_id: Counter for JSON-RPC request IDs
        pending_requests: Map of request ID to Future for responses

    Example:
        >>> client = LSPClient(
        ...     command="kotlin-language-server",
        ...     workspace_path=Path("/project")
        ... )
        >>> await client.start()
        >>> symbols = await client.workspace_symbols("Repository")
        >>> await client.stop()
    """

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        workspace_path: Path | None = None,
        env: dict[str, str] | None = None,
    ):
        """Initialize LSP client.

        Args:
            command: Command to start language server
            args: Command line arguments
            workspace_path: Workspace root directory
            env: Environment variables for the process
        """
        self.command = command
        self.args = args or []
        self.workspace_path = workspace_path
        self.env = env
        self.process: Process | None = None
        self.request_id = 0
        self.pending_requests: dict[int, asyncio.Future] = {}
        self._read_task: asyncio.Task | None = None
        self._initialized = False

    async def start(self) -> None:
        """Start the language server process.

        Raises:
            RuntimeError: If process fails to start
            asyncio.TimeoutError: If initialization times out

        Example:
            >>> await client.start()
        """
        logger.info(f"Starting LSP server: {self.command} {' '.join(self.args)}")

        try:
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.env,
            )
        except Exception as e:
            logger.error(f"Failed to start LSP server: {e}")
            raise RuntimeError(f"Failed to start LSP server: {e}") from e

        # Start reading responses
        self._read_task = asyncio.create_task(self._read_responses())

        # Initialize the language server
        await self._initialize()
        logger.info("LSP server started and initialized")

    async def stop(self) -> None:
        """Stop the language server process.

        Example:
            >>> await client.stop()
        """
        logger.info("Stopping LSP server")

        if not self.process:
            return

        # Send shutdown request
        try:
            await self._send_request("shutdown", {})
            await self._send_notification("exit", {})
        except Exception as e:
            logger.warning(f"Error during LSP shutdown: {e}")

        # Wait for process to exit
        try:
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("LSP server did not exit gracefully, terminating")
            if self.process:
                self.process.terminate()
                await self.process.wait()

        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        self.process = None
        self._initialized = False
        logger.info("LSP server stopped")

    async def _initialize(self) -> None:
        """Send initialize request to language server.

        Raises:
            RuntimeError: If initialization fails
        """
        workspace_uri = f"file://{self.workspace_path}" if self.workspace_path else None

        init_params = {
            "processId": None,
            "rootUri": workspace_uri,
            "capabilities": {
                "textDocument": {
                    "synchronization": {
                        "didOpen": True,
                        "didChange": True,
                        "didClose": True,
                    },
                    "definition": {"dynamicRegistration": False},
                    "references": {"dynamicRegistration": False},
                    "documentSymbol": {"dynamicRegistration": False},
                },
                "workspace": {
                    "symbol": {"dynamicRegistration": False},
                    "applyEdit": True,
                },
            },
        }

        try:
            response = await self._send_request("initialize", init_params)
            logger.debug(f"Initialize response: {response}")

            # Send initialized notification
            await self._send_notification("initialized", {})
            self._initialized = True

        except Exception as e:
            logger.error(f"LSP initialization failed: {e}")
            raise RuntimeError(f"LSP initialization failed: {e}") from e

    async def _send_request(self, method: str, params: dict[str, Any]) -> Any:
        """Send JSON-RPC request and wait for response.

        Args:
            method: LSP method name
            params: Method parameters

        Returns:
            Response result

        Raises:
            RuntimeError: If server is not running
            Exception: If request fails
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("LSP server is not running")

        self.request_id += 1
        request_id = self.request_id

        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self.pending_requests[request_id] = future

        # Send request
        await self._write_message(message)

        # Wait for response (with timeout)
        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise
        except Exception:
            self.pending_requests.pop(request_id, None)
            raise

    async def _send_notification(self, method: str, params: dict[str, Any]) -> None:
        """Send JSON-RPC notification (no response expected).

        Args:
            method: LSP method name
            params: Method parameters

        Raises:
            RuntimeError: If server is not running
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("LSP server is not running")

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        await self._write_message(message)

    async def _write_message(self, message: dict[str, Any]) -> None:
        """Write JSON-RPC message to server stdin.

        Args:
            message: Message to send

        Raises:
            RuntimeError: If server is not running
        """
        if not self.process or not self.process.stdin:
            raise RuntimeError("LSP server is not running")

        content = json.dumps(message)
        content_bytes = content.encode("utf-8")

        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
        header_bytes = header.encode("utf-8")

        self.process.stdin.write(header_bytes + content_bytes)
        await self.process.stdin.drain()

    async def _read_responses(self) -> None:
        """Read and process responses from server stdout."""
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                # Read headers
                headers = {}
                while True:
                    line = await self.process.stdout.readline()
                    if not line:
                        return

                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        break

                    if ":" in line_str:
                        key, value = line_str.split(":", 1)
                        headers[key.strip()] = value.strip()

                # Read content
                content_length = int(headers.get("Content-Length", 0))
                if content_length == 0:
                    continue

                content_bytes = await self.process.stdout.readexactly(content_length)
                content = content_bytes.decode("utf-8")

                try:
                    message = json.loads(content)
                    await self._handle_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON message: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading LSP responses: {e}")

    async def _handle_message(self, message: dict[str, Any]) -> None:
        """Handle incoming message from server.

        Args:
            message: JSON-RPC message
        """
        if "id" in message:
            # Response to a request
            request_id = message["id"]
            future = self.pending_requests.pop(request_id, None)

            if future and not future.done():
                if "error" in message:
                    error = message["error"]
                    future.set_exception(
                        Exception(f"LSP error: {error.get('message', 'Unknown error')}")
                    )
                else:
                    future.set_result(message.get("result"))
        else:
            # Notification from server
            method = message.get("method", "")
            if method.startswith("window/"):
                # Log server messages
                params = message.get("params", {})
                logger.debug(f"Server message: {method} - {params}")

    async def workspace_symbols(self, query: str) -> list[SymbolInformation]:
        """Search for symbols in the workspace.

        Args:
            query: Symbol search query

        Returns:
            List of symbol information

        Example:
            >>> symbols = await client.workspace_symbols("Repository")
            >>> for symbol in symbols:
            ...     print(symbol.name, symbol.location.uri)
        """
        if not self._initialized:
            raise RuntimeError("LSP client not initialized")

        result = await self._send_request("workspace/symbol", {"query": query})

        if not result:
            return []

        return [SymbolInformation.from_dict(item) for item in result]

    async def go_to_definition(
        self,
        file_uri: str,
        line: int,
        character: int
    ) -> Location | None:
        """Get definition location for symbol at position.

        Args:
            file_uri: URI of the document (e.g., "file:///path/to/file.kt")
            line: Line number (0-indexed)
            character: Character position (0-indexed)

        Returns:
            Location of definition, or None if not found

        Raises:
            RuntimeError: If client is not initialized

        Example:
            >>> location = await client.go_to_definition(
            ...     "file:///project/Repository.kt",
            ...     line=15,
            ...     character=10
            ... )
            >>> if location:
            ...     print(f"Definition at {location.uri}:{location.range.start.line}")
        """
        if not self._initialized:
            raise RuntimeError("LSP client not initialized")

        params = {
            "textDocument": {"uri": file_uri},
            "position": {"line": line, "character": character}
        }

        result = await self._send_request("textDocument/definition", params)

        if not result:
            return None

        # Result can be Location, Location[], or LocationLink[]
        # Handle single Location response
        if isinstance(result, dict):
            return self._parse_location(result)

        # Handle array of Locations - return first one
        if isinstance(result, list) and len(result) > 0:
            item = result[0]
            # Check if it's LocationLink (has targetUri/targetRange)
            if "targetUri" in item:
                range_data = item["targetRange"]
                return Location(
                    uri=item["targetUri"],
                    range=Range(
                        start=Position(**range_data["start"]),
                        end=Position(**range_data["end"])
                    )
                )
            # Otherwise it's a Location
            return self._parse_location(item)

        return None

    async def find_references(
        self,
        file_uri: str,
        line: int,
        character: int,
        include_declaration: bool = True
    ) -> list[Location]:
        """Find all references to symbol at position.

        Args:
            file_uri: URI of the document (e.g., "file:///path/to/file.kt")
            line: Line number (0-indexed)
            character: Character position (0-indexed)
            include_declaration: Include the declaration in results

        Returns:
            List of reference locations

        Raises:
            RuntimeError: If client is not initialized

        Example:
            >>> references = await client.find_references(
            ...     "file:///project/Repository.kt",
            ...     line=15,
            ...     character=10
            ... )
            >>> for ref in references:
            ...     print(f"Reference at {ref.uri}:{ref.range.start.line}")
        """
        if not self._initialized:
            raise RuntimeError("LSP client not initialized")

        params = {
            "textDocument": {"uri": file_uri},
            "position": {"line": line, "character": character},
            "context": {"includeDeclaration": include_declaration}
        }

        result = await self._send_request("textDocument/references", params)

        if not result:
            return []

        return [self._parse_location(item) for item in result]

    async def document_symbols(self, file_uri: str) -> list[SymbolInformation]:
        """Get all symbols in a document.

        Args:
            file_uri: URI of the document (e.g., "file:///path/to/file.kt")

        Returns:
            List of symbol information for the document

        Raises:
            RuntimeError: If client is not initialized

        Example:
            >>> symbols = await client.document_symbols("file:///project/Repository.kt")
            >>> for symbol in symbols:
            ...     print(f"{symbol.name} ({symbol.kind}) at line {symbol.location.range.start.line}")
        """
        if not self._initialized:
            raise RuntimeError("LSP client not initialized")

        params = {"textDocument": {"uri": file_uri}}

        result = await self._send_request("textDocument/documentSymbol", params)

        if not result:
            return []

        # DocumentSymbol has a different structure than SymbolInformation
        # We'll convert DocumentSymbol to SymbolInformation format
        symbols = []
        for item in result:
            # Check if it's already SymbolInformation (has location)
            if "location" in item:
                symbols.append(SymbolInformation.from_dict(item))
            # Otherwise it's DocumentSymbol (has range instead of location)
            elif "range" in item:
                range_data = item["range"]
                symbols.append(SymbolInformation(
                    name=item["name"],
                    kind=item["kind"],
                    location=Location(
                        uri=file_uri,
                        range=Range(
                            start=Position(**range_data["start"]),
                            end=Position(**range_data["end"])
                        )
                    ),
                    containerName=item.get("containerName")
                ))

        return symbols

    def _parse_location(self, data: dict[str, Any]) -> Location:
        """Parse Location from LSP response dictionary.

        Args:
            data: Dictionary with uri and range

        Returns:
            Location instance
        """
        range_data = data["range"]
        return Location(
            uri=data["uri"],
            range=Range(
                start=Position(**range_data["start"]),
                end=Position(**range_data["end"])
            )
        )

    def is_running(self) -> bool:
        """Check if language server is running.

        Returns:
            True if server process is running

        Example:
            >>> if client.is_running():
            ...     print("Server is ready")
        """
        return self.process is not None and self.process.returncode is None

    async def rename_symbol(
        self,
        file_uri: str,
        line: int,
        character: int,
        new_name: str
    ) -> WorkspaceEdit | None:
        """Rename symbol at position using LSP.

        Args:
            file_uri: Document URI (file:// format)
            line: Line number (0-based)
            character: Character position (0-based)
            new_name: New name for the symbol

        Returns:
            WorkspaceEdit with all rename changes, or None if not found

        Raises:
            RuntimeError: If LSP server is not running

        Example:
            >>> edit = await client.rename_symbol(
            ...     "file:///project/MyClass.kt",
            ...     line=10,
            ...     character=15,
            ...     new_name="NewClassName"
            ... )
            >>> if edit:
            ...     # Apply the edit
            ...     await client.apply_workspace_edit(edit)
        """
        if not self.is_running():
            raise RuntimeError("LSP server is not running")

        logger.info(f"Renaming symbol at {file_uri}:{line}:{character} to '{new_name}'")

        result = await self._send_request(
            method="textDocument/rename",
            params={
                "textDocument": {"uri": file_uri},
                "position": {"line": line, "character": character},
                "newName": new_name
            }
        )

        if not result:
            logger.warning(f"No rename result for symbol at {file_uri}:{line}:{character}")
            return None

        # Parse WorkspaceEdit from result
        if "changes" in result:
            changes = {}
            for uri, edits in result["changes"].items():
                text_edits = []
                for edit_data in edits:
                    range_data = edit_data["range"]
                    text_edit = TextEdit(
                        range=Range(
                            start=Position(**range_data["start"]),
                            end=Position(**range_data["end"])
                        ),
                        newText=edit_data["newText"]
                    )
                    text_edits.append(text_edit)
                changes[uri] = text_edits

            workspace_edit = WorkspaceEdit(changes=changes)
            logger.info(f"Rename will affect {len(changes)} file(s)")
            return workspace_edit

        return None

    async def apply_workspace_edit(self, edit: WorkspaceEdit) -> bool:
        """Apply workspace edit to files.

        Args:
            edit: WorkspaceEdit with changes to apply

        Returns:
            True if edit was applied successfully

        Raises:
            RuntimeError: If LSP server is not running
            IOError: If file operations fail

        Example:
            >>> workspace_edit = WorkspaceEdit(changes={...})
            >>> success = await client.apply_workspace_edit(workspace_edit)
        """
        if not self.is_running():
            raise RuntimeError("LSP server is not running")

        logger.info(f"Applying workspace edit to {len(edit.changes)} file(s)")

        try:
            # Send workspace/applyEdit request to server
            result = await self._send_request(
                method="workspace/applyEdit",
                params={
                    "edit": edit.to_dict()
                }
            )

            if result and result.get("applied", False):
                logger.info("Workspace edit applied successfully")
                return True
            else:
                failure_reason = result.get("failureReason", "Unknown") if result else "No response"
                logger.error(f"Workspace edit failed: {failure_reason}")
                return False

        except Exception as e:
            logger.error(f"Error applying workspace edit: {e}")
            raise OSError(f"Failed to apply workspace edit: {e}") from e

    async def did_change_document(
        self,
        file_uri: str,
        content: str,
        version: int = 1
    ) -> None:
        """Notify LSP server of document content change.

        Args:
            file_uri: Document URI (file:// format)
            content: Full new content of the document
            version: Document version number (increments with each change)

        Raises:
            RuntimeError: If LSP server is not running

        Example:
            >>> await client.did_change_document(
            ...     "file:///project/MyClass.kt",
            ...     new_content,
            ...     version=2
            ... )
        """
        if not self.is_running():
            raise RuntimeError("LSP server is not running")

        logger.debug(f"Sending textDocument/didChange for {file_uri} (v{version})")

        # Send textDocument/didChange notification (no response expected)
        await self.notify(
            method="textDocument/didChange",
            params={
                "textDocument": {
                    "uri": file_uri,
                    "version": version
                },
                "contentChanges": [
                    {
                        "text": content
                    }
                ]
            }
        )

    async def notify(self, method: str, params: dict[str, Any]) -> None:
        """Send JSON-RPC notification (no response expected).

        Args:
            method: LSP method name
            params: Method parameters

        Raises:
            RuntimeError: If LSP server is not running

        Example:
            >>> await client.notify("textDocument/didOpen", {...})
        """
        if not self.is_running():
            raise RuntimeError("LSP server is not running")

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        await self._write_message(message)
