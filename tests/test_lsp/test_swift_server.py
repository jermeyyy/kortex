"""Unit tests for Swift LSP server (SourceKit-LSP) integration.

Tests cover Swift LSP server initialization, configuration,
and Swift-specific LSP operations.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from kortex_mcp.lsp.swift_server import SwiftLSPServer
from kortex_mcp.models.lsp import Position, Range, Location, SymbolInformation


@pytest.mark.unit
@pytest.mark.asyncio
class TestSwiftLSPServerInitialization:
    """Test Swift LSP server initialization and configuration."""

    async def test_init_creates_server_with_sourcekit_lsp_command(self):
        """Test that SwiftLSPServer initializes with SourceKit-LSP command."""
        server = SwiftLSPServer(workspace_path=Path("/test/workspace"))
        
        assert server.command == "sourcekit-lsp"
        assert server.workspace_path == Path("/test/workspace")
        assert server.language_id == "swift"

    async def test_init_accepts_custom_sourcekit_path(self):
        """Test SwiftLSPServer with custom SourceKit-LSP binary path."""
        custom_path = "/usr/local/bin/sourcekit-lsp"
        server = SwiftLSPServer(
            workspace_path=Path("/test/workspace"),
            sourcekit_path=custom_path
        )
        
        assert server.command == custom_path
        assert server.workspace_path == Path("/test/workspace")

    async def test_get_initialization_options_returns_swift_config(self):
        """Test that Swift-specific initialization options are correct."""
        server = SwiftLSPServer(workspace_path=Path("/test/workspace"))
        options = server.get_initialization_options()
        
        # Swift LSP may have specific config for Swift projects
        assert isinstance(options, dict)
        # SourceKit-LSP specific configuration
        assert "capabilities" in options or options == {}


@pytest.mark.unit
@pytest.mark.asyncio
class TestSwiftLSPServerOperations:
    """Test Swift LSP server operations."""

    async def test_start_initializes_sourcekit_lsp(self):
        """Test that start() initializes SourceKit-LSP server."""
        server = SwiftLSPServer(workspace_path=Path("/test/workspace"))
        
        # Mock subprocess creation
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()
        mock_process.stderr = AsyncMock()
        mock_process.returncode = None
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch.object(server, '_read_responses', return_value=asyncio.Future()):
                with patch.object(server, '_initialize', return_value=None):
                    await server.start()
                    
                    assert server.process == mock_process
                    assert server._initialized is True

    async def test_supports_swift_file_types(self):
        """Test that server correctly identifies Swift file types."""
        server = SwiftLSPServer(workspace_path=Path("/test/workspace"))
        
        assert server.supports_file(Path("MyClass.swift"))
        assert not server.supports_file(Path("MyClass.kt"))
        assert not server.supports_file(Path("MyClass.java"))

    async def test_symbol_search_in_swift_files(self):
        """Test workspace symbol search in Swift files."""
        server = SwiftLSPServer(workspace_path=Path("/test/workspace"))
        
        # Mock the request method
        mock_symbols = [
            {
                "name": "SharedRepository",
                "kind": 5,  # Class
                "location": {
                    "uri": "file:///test/workspace/ios/SharedRepository.swift",
                    "range": {
                        "start": {"line": 10, "character": 0},
                        "end": {"line": 50, "character": 1}
                    }
                }
            }
        ]
        
        with patch.object(server, 'request', return_value=mock_symbols):
            symbols = await server.workspace_symbol("SharedRepository")
            
            assert len(symbols) == 1
            assert symbols[0].name == "SharedRepository"
            assert symbols[0].location.uri.endswith("SharedRepository.swift")


@pytest.mark.unit
@pytest.mark.asyncio
class TestSwiftLSPServerErrorHandling:
    """Test Swift LSP server error handling."""

    async def test_handles_sourcekit_not_found(self):
        """Test error handling when SourceKit-LSP is not found."""
        server = SwiftLSPServer(workspace_path=Path("/test/workspace"))
        
        with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError("sourcekit-lsp not found")):
            with pytest.raises(RuntimeError, match="Failed to start LSP server"):
                await server.start()

    async def test_handles_invalid_swift_project(self):
        """Test handling of invalid Swift project structure."""
        server = SwiftLSPServer(workspace_path=Path("/nonexistent"))
        
        # Should still initialize but may have limited functionality
        assert server.workspace_path == Path("/nonexistent")

    async def test_handles_swift_compilation_errors(self):
        """Test that server can still provide symbols despite compilation errors."""
        server = SwiftLSPServer(workspace_path=Path("/test/workspace"))
        
        # Mock symbol search that returns results even with errors
        mock_symbols = []
        
        with patch.object(server, 'request', return_value=mock_symbols):
            symbols = await server.workspace_symbol("NonExistent")
            
            # Should return empty list, not raise exception
            assert symbols == []


@pytest.mark.integration
@pytest.mark.asyncio
class TestSwiftLSPServerIntegration:
    """Integration tests for Swift LSP server with real SourceKit-LSP."""

    @pytest.mark.skipif(True, reason="Requires SourceKit-LSP installed")
    async def test_real_sourcekit_initialization(self):
        """Test real SourceKit-LSP initialization (requires installation)."""
        server = SwiftLSPServer(workspace_path=Path.cwd())
        
        try:
            await server.start()
            assert server.is_running()
        finally:
            await server.stop()

    @pytest.mark.skipif(True, reason="Requires Swift project")
    async def test_real_swift_symbol_search(self):
        """Test real symbol search in Swift project (requires Swift files)."""
        # This would require an actual Swift project
        pass
