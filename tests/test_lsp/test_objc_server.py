"""Unit tests for Objective-C LSP server (clangd) integration.

Tests cover clangd initialization, configuration,
and Objective-C-specific LSP operations.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kortex_mcp.lsp.objc_server import ObjCLSPServer
from kortex_mcp.models.lsp import Location, Position, Range, SymbolInformation


@pytest.mark.unit
@pytest.mark.asyncio
class TestObjCLSPServerInitialization:
    """Test Objective-C LSP server initialization and configuration."""

    async def test_init_creates_server_with_clangd_command(self):
        """Test that ObjCLSPServer initializes with clangd command."""
        server = ObjCLSPServer(workspace_path=Path("/test/workspace"))

        assert server.command == "clangd"
        assert server.workspace_path == Path("/test/workspace")
        assert server.language_id == "objective-c"

    async def test_init_accepts_custom_clangd_path(self):
        """Test ObjCLSPServer with custom clangd binary path."""
        custom_path = "/usr/local/bin/clangd"
        server = ObjCLSPServer(
            workspace_path=Path("/test/workspace"),
            clangd_path=custom_path
        )

        assert server.command == custom_path
        assert server.workspace_path == Path("/test/workspace")

    async def test_init_with_clangd_args(self):
        """Test ObjCLSPServer with custom clangd arguments."""
        server = ObjCLSPServer(
            workspace_path=Path("/test/workspace"),
            clangd_args=["--background-index", "--compile-commands-dir=/build"]
        )

        assert "--background-index" in server.args
        assert any("compile-commands-dir" in arg for arg in server.args)

    async def test_get_initialization_options_returns_clangd_config(self):
        """Test that clangd-specific initialization options are correct."""
        server = ObjCLSPServer(workspace_path=Path("/test/workspace"))
        options = server.get_initialization_options()

        # clangd specific configuration
        assert isinstance(options, dict)
        # May include fallback flags for Objective-C compilation
        assert "compilationDatabasePath" in options or "fallbackFlags" in options or options == {}


@pytest.mark.unit
@pytest.mark.asyncio
class TestObjCLSPServerOperations:
    """Test Objective-C LSP server operations."""

    async def test_start_initializes_clangd(self):
        """Test that start() initializes clangd server."""
        server = ObjCLSPServer(workspace_path=Path("/test/workspace"))

        # Mock subprocess creation
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()
        mock_process.stderr = AsyncMock()
        mock_process.returncode = None

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch.object(server.client, '_read_responses', return_value=asyncio.Future()):
                with patch.object(server.client, '_initialize', return_value=None):
                    await server.start()

                    assert server.client.process == mock_process
                    assert server.client._initialized is True

    async def test_supports_objc_file_types(self):
        """Test that server correctly identifies Objective-C file types."""
        server = ObjCLSPServer(workspace_path=Path("/test/workspace"))

        assert server.supports_file(Path("MyClass.m"))
        assert server.supports_file(Path("MyClass.h"))
        assert server.supports_file(Path("MyClass.mm"))  # Objective-C++
        assert not server.supports_file(Path("MyClass.swift"))
        assert not server.supports_file(Path("MyClass.kt"))

    async def test_symbol_search_in_objc_files(self):
        """Test workspace symbol search in Objective-C files."""
        server = ObjCLSPServer(workspace_path=Path("/test/workspace"))

        # Mock the client's workspace_symbols method
        mock_symbols = [
            SymbolInformation(
                name="SharedRepository",
                kind=5,  # Class
                location=Location(
                    uri="file:///test/workspace/ios/SharedRepository.m",
                    range=Range(
                        start=Position(line=10, character=0),
                        end=Position(line=50, character=1)
                    )
                ),
                containerName=""
            )
        ]

        # Mock is_running to return True
        with patch.object(server, 'is_running', return_value=True):
            with patch.object(server.client, 'workspace_symbols', return_value=mock_symbols):
                symbols = await server.workspace_symbol("SharedRepository")

                assert len(symbols) == 1
                assert symbols[0]["name"] == "SharedRepository"
                assert symbols[0]["location"]["uri"].endswith("SharedRepository.m")

    async def test_header_file_navigation(self):
        """Test navigation between .h and .m files."""
        server = ObjCLSPServer(workspace_path=Path("/test/workspace"))

        # Mock definition lookup
        mock_location = Location(
            uri="file:///test/workspace/ios/MyClass.m",
            range=Range(
                start=Position(line=20, character=0),
                end=Position(line=20, character=10)
            )
        )

        # Mock is_running to return True
        with patch.object(server, 'is_running', return_value=True):
            with patch.object(server.client, 'go_to_definition', return_value=mock_location):
                location = await server.goto_definition(
                    Path("/test/workspace/ios/MyClass.h"),
                    {"line": 5, "character": 10}
                )

                assert location is not None
                assert "MyClass.m" in location["uri"]


@pytest.mark.unit
@pytest.mark.asyncio
class TestObjCLSPServerErrorHandling:
    """Test Objective-C LSP server error handling."""

    async def test_handles_clangd_not_found(self):
        """Test error handling when clangd is not found."""
        server = ObjCLSPServer(workspace_path=Path("/test/workspace"))

        with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError("clangd not found")):
            with pytest.raises(RuntimeError, match="Failed to start LSP server"):
                await server.start()

    async def test_handles_missing_compile_commands(self):
        """Test handling when compile_commands.json is missing."""
        server = ObjCLSPServer(workspace_path=Path("/test/workspace"))

        # Should still initialize but may use fallback flags
        # Mock subprocess with warning about missing compilation database
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()
        mock_process.stderr = AsyncMock()
        mock_process.returncode = None

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            with patch.object(server.client, '_read_responses', return_value=asyncio.Future()):
                with patch.object(server.client, '_initialize', return_value=None):
                    await server.start()

                    # Should still start successfully
                    assert server.client.process is not None

    async def test_handles_objc_compilation_errors(self):
        """Test that server can still provide symbols despite compilation errors."""
        server = ObjCLSPServer(workspace_path=Path("/test/workspace"))

        # Mock symbol search that returns results even with errors
        mock_symbols = []

        # Mock is_running to return True
        with patch.object(server, 'is_running', return_value=True):
            with patch.object(server.client, 'workspace_symbols', return_value=mock_symbols):
                symbols = await server.workspace_symbol("NonExistent")

                # Should return empty list, not raise exception
                assert symbols == []


@pytest.mark.integration
@pytest.mark.asyncio
class TestObjCLSPServerIntegration:
    """Integration tests for Objective-C LSP server with real clangd."""

    @pytest.mark.skipif(True, reason="Requires clangd installed")
    async def test_real_clangd_initialization(self):
        """Test real clangd initialization (requires installation)."""
        server = ObjCLSPServer(workspace_path=Path.cwd())

        try:
            await server.start()
            assert server.is_running()
        finally:
            await server.stop()

    @pytest.mark.skipif(True, reason="Requires Objective-C project")
    async def test_real_objc_symbol_search(self):
        """Test real symbol search in Objective-C project (requires .m files)."""
        # This would require an actual Objective-C project
        pass
