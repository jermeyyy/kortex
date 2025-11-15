"""Unit tests for LSP Manager functionality.

Tests cover LSP manager initialization, server lifecycle management,
health monitoring, and multi-server coordination.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from kortex_mcp.lsp.manager import LSPManager
from kortex_mcp.lsp.client import LSPClient


@pytest.mark.unit
@pytest.mark.asyncio
class TestLSPManagerInitialization:
    """Test LSP manager initialization and configuration."""

    async def test_init_creates_manager_with_defaults(self):
        """Test that LSPManager initializes with correct default values."""
        manager = LSPManager()
        
        assert manager.clients == {}
        assert manager.health_check_interval == 30.0
        assert manager.max_restart_attempts == 3
        assert manager.restart_counts == {}
        assert manager.last_health_check == {}
        assert manager._health_check_task is None
        assert manager._running is False

    async def test_init_accepts_custom_config(self):
        """Test LSPManager initialization with custom configuration."""
        manager = LSPManager(
            health_check_interval=60.0,
            max_restart_attempts=5
        )
        
        assert manager.health_check_interval == 60.0
        assert manager.max_restart_attempts == 5


@pytest.mark.unit
@pytest.mark.asyncio
class TestLSPManagerServerLifecycle:
    """Test server lifecycle management."""

    async def test_start_server_creates_client(self):
        """Test that start_server creates and initializes a client."""
        manager = LSPManager()
        
        # Mock client creation and initialization
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            MockClient.return_value = mock_client
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server",
                workspace_path=Path("/test/workspace")
            )
            
            # Verify client was created and started
            MockClient.assert_called_once_with(
                command="kotlin-language-server",
                args=None,
                workspace_path=Path("/test/workspace"),
                env=None
            )
            mock_client.start.assert_called_once()
            
            # Verify client was registered
            assert "kotlin" in manager.clients
            assert manager.restart_counts["kotlin"] == 0
            assert "kotlin" in manager.last_health_check

    async def test_start_server_raises_on_duplicate_language_id(self):
        """Test that starting duplicate language_id raises ValueError."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            MockClient.return_value = mock_client
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            
            # Try to start again with same ID
            with pytest.raises(ValueError, match="already exists"):
                await manager.start_server(
                    language_id="kotlin",
                    command="kotlin-language-server"
                )

    async def test_start_server_starts_health_check_task(self):
        """Test that starting first server initiates health check loop."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            MockClient.return_value = mock_client
            
            with patch.object(manager, '_health_check_loop', return_value=asyncio.Future()) as mock_health:
                await manager.start_server(
                    language_id="kotlin",
                    command="kotlin-language-server"
                )
                
                assert manager._running is True
                assert manager._health_check_task is not None

    async def test_stop_server_stops_client(self):
        """Test that stop_server properly stops and cleans up client."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            MockClient.return_value = mock_client
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            
            await manager.stop_server("kotlin")
            
            # Verify client was stopped
            mock_client.stop.assert_called_once()
            
            # Verify cleanup
            assert "kotlin" not in manager.clients
            assert "kotlin" not in manager.restart_counts
            assert "kotlin" not in manager.last_health_check

    async def test_stop_server_handles_nonexistent_server(self):
        """Test that stopping nonexistent server doesn't raise error."""
        manager = LSPManager()
        
        # Should not raise
        await manager.stop_server("nonexistent")

    async def test_stop_all_stops_all_servers(self):
        """Test that stop_all stops all running servers."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client1 = AsyncMock(spec=LSPClient)
            mock_client2 = AsyncMock(spec=LSPClient)
            MockClient.side_effect = [mock_client1, mock_client2]
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            await manager.start_server(
                language_id="swift",
                command="sourcekit-lsp"
            )
            
            await manager.stop_all()
            
            # Verify all clients stopped
            mock_client1.stop.assert_called_once()
            mock_client2.stop.assert_called_once()
            
            # Verify cleanup
            assert len(manager.clients) == 0
            assert manager._running is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestLSPManagerClientAccess:
    """Test client access and status checking."""

    async def test_get_client_returns_existing_client(self):
        """Test that get_client returns the correct client."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            MockClient.return_value = mock_client
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            
            client = manager.get_client("kotlin")
            assert client == mock_client

    async def test_get_client_returns_none_for_nonexistent(self):
        """Test that get_client returns None for nonexistent client."""
        manager = LSPManager()
        
        client = manager.get_client("nonexistent")
        assert client is None

    async def test_is_running_returns_true_for_active_server(self):
        """Test that is_running correctly identifies active server."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            mock_process = MagicMock()
            mock_process.returncode = None
            mock_client.process = mock_process
            mock_client._initialized = True
            mock_client.is_running = Mock(return_value=True)  # Mock is_running method
            MockClient.return_value = mock_client
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            
            assert manager.is_running("kotlin") is True

    async def test_is_running_returns_false_for_stopped_server(self):
        """Test that is_running returns False for stopped server."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            mock_process = MagicMock()
            mock_process.returncode = 0  # Exited
            mock_client.process = mock_process
            mock_client._initialized = False
            mock_client.is_running = Mock(return_value=False)  # Mock is_running method
            MockClient.return_value = mock_client
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            
            assert manager.is_running("kotlin") is False

    async def test_is_running_returns_false_for_nonexistent_server(self):
        """Test that is_running returns False for nonexistent server."""
        manager = LSPManager()
        
        assert manager.is_running("nonexistent") is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestLSPManagerMultipleServers:
    """Test managing multiple language servers simultaneously."""

    async def test_manage_multiple_servers_independently(self):
        """Test managing Kotlin, Swift, and Objective-C servers together."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            # Create three different mock clients
            mock_clients = {
                "kotlin": AsyncMock(spec=LSPClient),
                "swift": AsyncMock(spec=LSPClient),
                "objc": AsyncMock(spec=LSPClient)
            }
            MockClient.side_effect = list(mock_clients.values())
            
            # Start all servers
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            await manager.start_server(
                language_id="swift",
                command="sourcekit-lsp"
            )
            await manager.start_server(
                language_id="objc",
                command="clangd"
            )
            
            # Verify all are registered
            assert len(manager.clients) == 3
            assert "kotlin" in manager.clients
            assert "swift" in manager.clients
            assert "objc" in manager.clients
            
            # Stop one server
            await manager.stop_server("swift")
            
            # Verify only swift was stopped
            assert len(manager.clients) == 2
            assert "kotlin" in manager.clients
            assert "objc" in manager.clients
            mock_clients["swift"].stop.assert_called_once()
            mock_clients["kotlin"].stop.assert_not_called()
            mock_clients["objc"].stop.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
class TestLSPManagerErrorHandling:
    """Test error handling and recovery."""

    async def test_start_server_handles_initialization_failure(self):
        """Test that start_server handles client initialization failures."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            mock_client.start.side_effect = RuntimeError("Failed to start")
            MockClient.return_value = mock_client
            
            with pytest.raises(RuntimeError, match="Failed to start"):
                await manager.start_server(
                    language_id="kotlin",
                    command="kotlin-language-server"
                )
            
            # Verify client was not registered
            assert "kotlin" not in manager.clients

    async def test_stop_server_handles_shutdown_errors(self):
        """Test that stop_server handles errors during shutdown gracefully."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            MockClient.return_value = mock_client
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            
            # Make stop raise an error
            mock_client.stop.side_effect = Exception("Stop failed")
            
            # Should not raise, but should clean up
            await manager.stop_server("kotlin")
            
            # Verify cleanup occurred despite error
            assert "kotlin" not in manager.clients


@pytest.mark.unit
@pytest.mark.asyncio  
class TestLSPManagerHealthChecks:
    """Test health monitoring functionality."""

    async def test_health_check_detects_crashed_server(self):
        """Test that health check detects crashed servers."""
        manager = LSPManager(health_check_interval=0.1)  # Fast checks for testing
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            mock_process = MagicMock()
            mock_process.returncode = None  # Initially running
            mock_client.process = mock_process
            mock_client._initialized = True
            mock_client.is_running = Mock(return_value=True)  # Initially returns True
            MockClient.return_value = mock_client
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            
            # Simulate crash
            mock_process.returncode = 1
            mock_client._initialized = False
            mock_client.is_running = Mock(return_value=False)  # Now returns False
            
            # Wait for health check to detect crash
            await asyncio.sleep(0.2)
            
            # Health check should have detected the crash
            # (actual restart logic would depend on implementation)
            assert manager.is_running("kotlin") is False

    async def test_get_status_returns_server_info(self):
        """Test that get_status returns correct server information."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client = AsyncMock(spec=LSPClient)
            mock_process = MagicMock()
            mock_process.returncode = None
            mock_client.process = mock_process
            mock_client._initialized = True
            mock_client.is_running = Mock(return_value=True)
            MockClient.return_value = mock_client
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            
            status = manager.get_status()
            
            assert status is not None
            assert "kotlin" in status
            assert status["kotlin"]["running"] is True
            assert status["kotlin"]["restart_count"] == 0

    async def test_get_all_status_returns_all_servers(self):
        """Test that get_status returns info for all servers."""
        manager = LSPManager()
        
        with patch('kortex_mcp.lsp.manager.LSPClient') as MockClient:
            mock_client1 = AsyncMock(spec=LSPClient)
            mock_client2 = AsyncMock(spec=LSPClient)
            
            # Setup both clients as running
            for client in [mock_client1, mock_client2]:
                mock_process = MagicMock()
                mock_process.returncode = None
                client.process = mock_process
                client._initialized = True
                client.is_running = Mock(return_value=True)
            
            MockClient.side_effect = [mock_client1, mock_client2]
            
            await manager.start_server(
                language_id="kotlin",
                command="kotlin-language-server"
            )
            await manager.start_server(
                language_id="swift",
                command="sourcekit-lsp"
            )
            
            all_status = manager.get_status()
            
            assert len(all_status) == 2
            assert "kotlin" in all_status
            assert "swift" in all_status
            assert all_status["kotlin"]["running"] is True
            assert all_status["swift"]["running"] is True
