"""Unit tests for LSP client functionality.

Tests cover LSP client initialization, connection establishment,
workspace symbol search, and error handling.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json

from kortex_mcp.lsp.client import LSPClient
from kortex_mcp.models.lsp import (
    Position, Range, Location, SymbolInformation
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestLSPClientInitialization:
    """Test LSP client initialization and lifecycle."""

    async def test_init_creates_client_with_defaults(self):
        """Test that LSPClient initializes with correct default values."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        assert client.command == "kotlin-language-server"
        assert client.args == []
        assert client.workspace_path == Path("/test/workspace")
        assert client.env is None
        assert client.process is None
        assert client.request_id == 0
        assert client.pending_requests == {}
        assert client._read_task is None
        assert client._initialized is False

    async def test_init_creates_client_with_custom_args(self):
        """Test LSPClient initialization with custom arguments."""
        client = LSPClient(
            command="kotlin-language-server",
            args=["--stdio", "--log-level=debug"],
            workspace_path=Path("/test/workspace"),
            env={"PATH": "/custom/path"}
        )
        
        assert client.args == ["--stdio", "--log-level=debug"]
        assert client.env == {"PATH": "/custom/path"}

    async def test_start_creates_subprocess(self):
        """Test that start() creates subprocess and initializes server."""
        client = LSPClient(
            command="echo",  # Use simple command for testing
            workspace_path=Path("/test/workspace")
        )
        
        # Mock subprocess creation and initialization
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()
        mock_process.stderr = AsyncMock()
        mock_process.returncode = None
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process) as mock_exec:
            with patch.object(client, '_read_responses', return_value=asyncio.Future()) as mock_read:
                with patch.object(client, '_initialize', return_value=None) as mock_init:
                    await client.start()
                    
                    # Verify subprocess was created with correct parameters
                    mock_exec.assert_called_once_with(
                        "echo",
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env=None,
                    )
                    
                    # Verify initialization was called
                    mock_init.assert_called_once()
                    
                    # Verify process is set
                    assert client.process == mock_process

    async def test_start_raises_on_subprocess_failure(self):
        """Test that start() raises RuntimeError if subprocess creation fails."""
        client = LSPClient(
            command="nonexistent-command",
            workspace_path=Path("/test/workspace")
        )
        
        with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError("Command not found")):
            with pytest.raises(RuntimeError, match="Failed to start LSP server"):
                await client.start()

    async def test_initialize_sends_correct_params(self):
        """Test that _initialize() sends correct initialization parameters."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Mock _send_request and _send_notification
        with patch.object(client, '_send_request', return_value={"capabilities": {}}) as mock_request:
            with patch.object(client, '_send_notification') as mock_notification:
                await client._initialize()
                
                # Verify initialize request
                call_args = mock_request.call_args
                assert call_args[0][0] == "initialize"
                
                init_params = call_args[0][1]
                assert init_params["processId"] is None
                assert init_params["rootUri"] == "file:///test/workspace"
                assert "textDocument" in init_params["capabilities"]
                assert "workspace" in init_params["capabilities"]
                
                # Verify textDocument capabilities
                text_doc_caps = init_params["capabilities"]["textDocument"]
                assert text_doc_caps["synchronization"]["didOpen"] is True
                assert text_doc_caps["synchronization"]["didChange"] is True
                assert text_doc_caps["definition"]["dynamicRegistration"] is False
                assert text_doc_caps["references"]["dynamicRegistration"] is False
                assert text_doc_caps["documentSymbol"]["dynamicRegistration"] is False
                
                # Verify workspace capabilities
                workspace_caps = init_params["capabilities"]["workspace"]
                assert workspace_caps["symbol"]["dynamicRegistration"] is False
                assert workspace_caps["applyEdit"] is True
                
                # Verify initialized notification was sent
                mock_notification.assert_called_once_with("initialized", {})
                
                # Verify client is marked as initialized
                assert client._initialized is True

    async def test_initialize_handles_failure(self):
        """Test that _initialize() raises RuntimeError on failure."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        with patch.object(client, '_send_request', side_effect=Exception("Connection failed")):
            with pytest.raises(RuntimeError, match="LSP initialization failed"):
                await client._initialize()
            
            assert client._initialized is False

    async def test_stop_sends_shutdown_and_exit(self):
        """Test that stop() sends shutdown request and exit notification."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Mock process and tasks
        mock_process = MagicMock()
        mock_process.wait = AsyncMock(return_value=None)
        mock_process.terminate = Mock()
        mock_process.returncode = 0
        
        # Create a real task that can be cancelled
        async def dummy_read():
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                pass
        
        mock_read_task = asyncio.create_task(dummy_read())
        
        client.process = mock_process
        client._read_task = mock_read_task
        client._initialized = True
        
        with patch.object(client, '_send_request') as mock_request:
            with patch.object(client, '_send_notification') as mock_notification:
                await client.stop()
                
                # Verify shutdown sequence
                mock_request.assert_called_once_with("shutdown", {})
                mock_notification.assert_called_once_with("exit", {})
                
                # Verify process wait was called
                mock_process.wait.assert_called_once()
                
                # Verify read task was cancelled
                assert mock_read_task.cancelled()
                
                # Verify cleanup
                assert client.process is None
                assert client._initialized is False

    async def test_stop_terminates_on_timeout(self):
        """Test that stop() terminates process if graceful shutdown times out."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Mock process that times out
        mock_process = MagicMock()
        mock_process.terminate = Mock()
        
        # Create a real task that can be cancelled
        async def dummy_read():
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                pass
        
        mock_read_task = asyncio.create_task(dummy_read())
        
        client.process = mock_process
        client._read_task = mock_read_task
        
        with patch.object(client, '_send_request'):
            with patch.object(client, '_send_notification'):
                # Mock the first wait to raise timeout, second to succeed
                call_count = 0
                async def mock_wait():
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise asyncio.TimeoutError()
                    return None
                
                mock_process.wait = mock_wait
                
                await client.stop()
                
                # Verify terminate was called
                mock_process.terminate.assert_called_once()

    async def test_stop_handles_no_process(self):
        """Test that stop() handles case when process is None."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Should not raise
        await client.stop()

    async def test_is_running_returns_true_when_process_active(self):
        """Test is_running() returns True when process is active."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        mock_process = MagicMock()
        mock_process.returncode = None
        client.process = mock_process
        
        assert client.is_running() is True

    async def test_is_running_returns_false_when_process_none(self):
        """Test is_running() returns False when process is None."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        assert client.is_running() is False

    async def test_is_running_returns_false_when_process_exited(self):
        """Test is_running() returns False when process has exited."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        mock_process = MagicMock()
        mock_process.returncode = 0
        client.process = mock_process
        
        assert client.is_running() is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestLSPClientWorkspaceSymbols:
    """Test workspace symbol search functionality."""

    async def test_workspace_symbols_sends_correct_request(self):
        """Test that workspace_symbols() sends correct LSP request."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        client._initialized = True
        
        # Mock response with symbol data
        mock_symbols = [
            {
                "name": "Repository",
                "kind": 5,  # Class
                "location": {
                    "uri": "file:///test/workspace/Repository.kt",
                    "range": {
                        "start": {"line": 10, "character": 0},
                        "end": {"line": 20, "character": 0}
                    }
                },
                "containerName": "com.example.kmp"
            },
            {
                "name": "UserRepository",
                "kind": 5,
                "location": {
                    "uri": "file:///test/workspace/UserRepository.kt",
                    "range": {
                        "start": {"line": 5, "character": 0},
                        "end": {"line": 15, "character": 0}
                    }
                },
                "containerName": "com.example.kmp"
            }
        ]
        
        with patch.object(client, '_send_request', return_value=mock_symbols) as mock_request:
            symbols = await client.workspace_symbols("Repository")
            
            # Verify request was sent
            mock_request.assert_called_once_with("workspace/symbol", {"query": "Repository"})
            
            # Verify symbols were parsed correctly
            assert len(symbols) == 2
            assert isinstance(symbols[0], SymbolInformation)
            assert symbols[0].name == "Repository"
            assert symbols[0].kind == 5
            assert symbols[0].containerName == "com.example.kmp"
            assert symbols[1].name == "UserRepository"

    async def test_workspace_symbols_returns_empty_list_on_no_results(self):
        """Test workspace_symbols() returns empty list when no symbols found."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        client._initialized = True
        
        with patch.object(client, '_send_request', return_value=None):
            symbols = await client.workspace_symbols("NonExistent")
            
            assert symbols == []

    async def test_workspace_symbols_raises_when_not_initialized(self):
        """Test workspace_symbols() raises RuntimeError when client not initialized."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Client not initialized
        assert client._initialized is False
        
        with pytest.raises(RuntimeError, match="LSP client not initialized"):
            await client.workspace_symbols("Repository")

    async def test_workspace_symbols_handles_empty_response(self):
        """Test workspace_symbols() handles empty array response."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        client._initialized = True
        
        with patch.object(client, '_send_request', return_value=[]):
            symbols = await client.workspace_symbols("Repository")
            
            assert symbols == []


@pytest.mark.unit
@pytest.mark.asyncio
class TestLSPClientJsonRpc:
    """Test JSON-RPC communication methods."""

    async def test_send_request_creates_proper_message(self):
        """Test _send_request() creates properly formatted JSON-RPC message."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Mock process
        mock_stdin = AsyncMock()
        mock_process = MagicMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process
        
        # Mock write_message and response handling
        written_message = None
        
        async def capture_message(message):
            nonlocal written_message
            written_message = message
            # Immediately resolve the request
            future = client.pending_requests.get(message["id"])
            if future:
                future.set_result({"test": "response"})
        
        with patch.object(client, '_write_message', side_effect=capture_message):
            response = await client._send_request("test/method", {"param": "value"})
            
            # Verify message format
            assert written_message is not None
            assert written_message["jsonrpc"] == "2.0"
            assert "id" in written_message
            assert written_message["method"] == "test/method"
            assert written_message["params"] == {"param": "value"}
            
            # Verify response
            assert response == {"test": "response"}

    async def test_send_request_increments_request_id(self):
        """Test _send_request() increments request ID for each request."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        mock_stdin = AsyncMock()
        mock_process = MagicMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process
        
        request_ids = []
        
        async def capture_id(message):
            request_ids.append(message["id"])
            future = client.pending_requests.get(message["id"])
            if future:
                future.set_result({})
        
        with patch.object(client, '_write_message', side_effect=capture_id):
            await client._send_request("test1", {})
            await client._send_request("test2", {})
            await client._send_request("test3", {})
            
            assert request_ids == [1, 2, 3]

    async def test_send_request_raises_when_no_process(self):
        """Test _send_request() raises RuntimeError when process is None."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        with pytest.raises(RuntimeError, match="LSP server is not running"):
            await client._send_request("test/method", {})

    async def test_send_request_times_out(self):
        """Test _send_request() times out after 30 seconds."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        mock_stdin = AsyncMock()
        mock_process = MagicMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process
        
        # Don't resolve the future - let it timeout
        with patch.object(client, '_write_message'):
            with pytest.raises(asyncio.TimeoutError):
                await client._send_request("test/method", {})
            
            # Verify pending request was cleaned up
            assert len(client.pending_requests) == 0

    async def test_send_notification_creates_proper_message(self):
        """Test _send_notification() creates properly formatted message."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        mock_stdin = AsyncMock()
        mock_process = MagicMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process
        
        written_message = None
        
        async def capture_message(message):
            nonlocal written_message
            written_message = message
        
        with patch.object(client, '_write_message', side_effect=capture_message):
            await client._send_notification("test/notification", {"param": "value"})
            
            # Verify message format (notifications don't have id)
            assert written_message is not None
            assert written_message["jsonrpc"] == "2.0"
            assert "id" not in written_message
            assert written_message["method"] == "test/notification"
            assert written_message["params"] == {"param": "value"}

    async def test_write_message_formats_correctly(self):
        """Test _write_message() formats message with correct headers."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        mock_stdin = AsyncMock()
        mock_process = MagicMock()
        mock_process.stdin = mock_stdin
        client.process = mock_process
        
        test_message = {"jsonrpc": "2.0", "method": "test", "params": {}}
        
        await client._write_message(test_message)
        
        # Verify stdin.write was called
        assert mock_stdin.write.called
        written_data = mock_stdin.write.call_args[0][0]
        
        # Verify format
        written_str = written_data.decode("utf-8")
        assert "Content-Length:" in written_str
        assert "\r\n\r\n" in written_str
        
        # Verify message is valid JSON
        parts = written_str.split("\r\n\r\n")
        message_json = parts[1]
        parsed = json.loads(message_json)
        assert parsed == test_message
        
        # Verify Content-Length is correct
        content_length = len(message_json.encode("utf-8"))
        assert f"Content-Length: {content_length}" in written_str

    async def test_handle_message_resolves_pending_request(self):
        """Test _handle_message() resolves pending request futures."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Create a pending request
        future = asyncio.Future()
        client.pending_requests[42] = future
        
        # Handle response
        response_message = {
            "jsonrpc": "2.0",
            "id": 42,
            "result": {"test": "data"}
        }
        
        await client._handle_message(response_message)
        
        # Verify future was resolved
        assert future.done()
        assert future.result() == {"test": "data"}
        assert 42 not in client.pending_requests

    async def test_handle_message_sets_exception_on_error(self):
        """Test _handle_message() sets exception for error responses."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Create a pending request
        future = asyncio.Future()
        client.pending_requests[42] = future
        
        # Handle error response
        error_message = {
            "jsonrpc": "2.0",
            "id": 42,
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }
        
        await client._handle_message(error_message)
        
        # Verify future has exception
        assert future.done()
        with pytest.raises(Exception, match="LSP error: Method not found"):
            future.result()
        assert 42 not in client.pending_requests

    async def test_handle_message_ignores_unknown_request_id(self):
        """Test _handle_message() safely handles unknown request IDs."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Handle response for unknown request
        response_message = {
            "jsonrpc": "2.0",
            "id": 999,
            "result": {"test": "data"}
        }
        
        # Should not raise
        await client._handle_message(response_message)

    async def test_handle_message_processes_notifications(self):
        """Test _handle_message() handles server notifications."""
        client = LSPClient(
            command="kotlin-language-server",
            workspace_path=Path("/test/workspace")
        )
        
        # Handle notification (no id field)
        notification = {
            "jsonrpc": "2.0",
            "method": "window/logMessage",
            "params": {
                "type": 3,
                "message": "Server started"
            }
        }
        
        # Should not raise
        await client._handle_message(notification)
