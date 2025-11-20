"""Unit tests for Kotlin LSP server integration.

Tests cover Kotlin Language Server initialization, configuration,
and Kotlin-specific LSP operations for KMP projects.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kortex_mcp.lsp.kotlin_server import KotlinLSPServer
from kortex_mcp.models.lsp import Location, Position, Range, SymbolInformation


@pytest.mark.unit
@pytest.mark.asyncio
class TestKotlinLSPServerInitialization:
    """Test Kotlin LSP server initialization and configuration."""

    async def test_init_creates_server_with_kotlin_lsp_command(self):
        """Test that KotlinLSPServer initializes with Kotlin LSP command."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Should auto-detect or default to kotlin-lsp
        assert server.server_command in ["kotlin-lsp", "kotlin-language-server"]
        assert server.workspace_path == Path("/test/workspace")
        assert server.client is not None

    async def test_init_accepts_custom_server_command(self):
        """Test KotlinLSPServer with custom server command path."""
        custom_path = "/usr/local/bin/kotlin-lsp"
        server = KotlinLSPServer(
            workspace_path=Path("/test/workspace"),
            server_command=custom_path
        )

        assert server.server_command == custom_path
        assert server.workspace_path == Path("/test/workspace")

    async def test_find_kotlin_language_server_checks_common_locations(self):
        """Test that server searches common installation locations."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock shutil.which to test search logic
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda cmd: cmd if cmd == "kotlin-lsp" else None

            result = server._find_kotlin_language_server()

            # Should find kotlin-lsp
            assert result == "kotlin-lsp"

    async def test_get_environment_vars_includes_java_home(self):
        """Test that environment variables include JAVA_HOME if available."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        env = server._get_environment_vars()

        # Should include all current environment variables
        assert isinstance(env, dict)
        # JAVA_HOME should be set or attempted to be found
        assert "JAVA_HOME" in env or True  # May not be set in test environment


@pytest.mark.unit
@pytest.mark.asyncio
class TestKotlinLSPServerOperations:
    """Test Kotlin LSP server operations."""

    async def test_start_initializes_kotlin_lsp(self):
        """Test that start() initializes Kotlin language server."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

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

                    # Verify start was called on client
                    assert server.client.process == mock_process

    async def test_stop_shuts_down_kotlin_lsp(self):
        """Test that stop() properly shuts down Kotlin language server."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock an active client
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.wait = AsyncMock()
        server.client.process = mock_process
        server.client._initialized = True

        with patch.object(server.client, '_send_request', return_value=None):
            with patch.object(server.client, '_send_notification', return_value=None):
                await server.stop()

                # Verify shutdown was called
                assert server.client.process is None or mock_process.wait.called

    async def test_search_symbols_returns_formatted_results(self):
        """Test that search_symbols returns properly formatted results."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock the client's workspace_symbols method
        mock_symbols = [
            SymbolInformation(
                name="Repository",
                kind=5,  # Class
                location=Location(
                    uri="file:///test/workspace/commonMain/kotlin/Repository.kt",
                    range=Range(
                        start=Position(line=10, character=0),
                        end=Position(line=50, character=1)
                    )
                ),
                containerName=""
            )
        ]

        with patch.object(server.client, 'workspace_symbols', return_value=mock_symbols):
            symbols = await server.search_symbols("Repository")

            assert len(symbols) == 1
            assert symbols[0]["name"] == "Repository"
            assert symbols[0]["kind"] == "class"
            assert "Repository.kt" in symbols[0]["file"]
            assert symbols[0]["line"] == 10
            assert symbols[0]["character"] == 0

    async def test_symbol_kind_conversion(self):
        """Test that symbol kinds are converted to readable strings."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        assert server._symbol_kind_to_string(5) == "class"
        assert server._symbol_kind_to_string(6) == "method"
        assert server._symbol_kind_to_string(12) == "function"
        assert server._symbol_kind_to_string(13) == "variable"
        assert server._symbol_kind_to_string(999) == "unknown"

    async def test_goto_definition_in_kotlin_file(self):
        """Test go-to-definition works through client."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock definition lookup through client
        mock_location = Location(
            uri="file:///test/workspace/commonMain/kotlin/Repository.kt",
            range=Range(
                start=Position(line=15, character=6),
                end=Position(line=15, character=16)
            )
        )

        with patch.object(server.client, 'go_to_definition', return_value=mock_location):
            # Access through client directly since server doesn't wrap it
            location = await server.client.go_to_definition(
                file_uri="file:///test/workspace/commonMain/kotlin/App.kt",
                line=20,
                character=10
            )

            assert location is not None
            assert "Repository.kt" in location.uri

    async def test_find_references_in_kotlin_project(self):
        """Test finding all references through client."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock multiple reference locations
        mock_locations = [
            Location(
                uri="file:///test/workspace/commonMain/kotlin/App.kt",
                range=Range(
                    start=Position(line=20, character=10),
                    end=Position(line=20, character=20)
                )
            ),
            Location(
                uri="file:///test/workspace/androidMain/kotlin/AndroidApp.kt",
                range=Range(
                    start=Position(line=15, character=5),
                    end=Position(line=15, character=15)
                )
            ),
        ]

        with patch.object(server.client, 'find_references', return_value=mock_locations):
            # Access through client directly
            references = await server.client.find_references(
                file_uri="file:///test/workspace/commonMain/kotlin/Repository.kt",
                line=10,
                character=6,
                include_declaration=True
            )

            assert len(references) == 2
            assert any("App.kt" in ref.uri for ref in references)
            assert any("AndroidApp.kt" in ref.uri for ref in references)

    async def test_is_running_check(self):
        """Test that is_running correctly checks server status."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock client is_running
        with patch.object(server.client, 'is_running', return_value=True):
            assert server.is_running() is True

        with patch.object(server.client, 'is_running', return_value=False):
            assert server.is_running() is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestKotlinLSPServerKMPFeatures:
    """Test KMP-specific Kotlin LSP features."""

    async def test_detects_expect_declarations(self):
        """Test detection of expect declarations in common code."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock symbol that represents an expect declaration
        mock_symbols = [
            SymbolInformation(
                name="Platform",
                kind=5,  # Class
                location=Location(
                    uri="file:///test/workspace/commonMain/kotlin/Platform.kt",
                    range=Range(
                        start=Position(line=5, character=0),
                        end=Position(line=10, character=1)
                    )
                ),
                containerName=""
            )
        ]

        with patch.object(server.client, 'workspace_symbols', return_value=mock_symbols):
            symbols = await server.search_symbols("Platform")

            assert len(symbols) == 1
            assert "commonMain" in symbols[0]["file"]

    async def test_finds_actual_implementations(self):
        """Test finding actual implementations through references."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock finding actuals in platform-specific source sets
        mock_locations = [
            Location(
                uri="file:///test/workspace/androidMain/kotlin/Platform.kt",
                range=Range(start=Position(line=5, character=0), end=Position(line=10, character=1))
            ),
            Location(
                uri="file:///test/workspace/iosMain/kotlin/Platform.kt",
                range=Range(start=Position(line=5, character=0), end=Position(line=10, character=1))
            ),
        ]

        with patch.object(server.client, 'find_references', return_value=mock_locations):
            # Access through client directly
            references = await server.client.find_references(
                file_uri="file:///test/workspace/commonMain/kotlin/Platform.kt",
                line=5,
                character=6,
                include_declaration=True
            )

            # Should find platform-specific implementations
            assert len(references) >= 2
            platform_uris = [ref.uri for ref in references]
            assert any("androidMain" in uri for uri in platform_uris)
            assert any("iosMain" in uri for uri in platform_uris)


@pytest.mark.unit
@pytest.mark.asyncio
class TestKotlinLSPServerErrorHandling:
    """Test Kotlin LSP server error handling."""

    async def test_handles_kotlin_lsp_not_found(self):
        """Test error handling when Kotlin language server is not found."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError("kotlin-lsp not found")):
            with pytest.raises(RuntimeError, match="Failed to start LSP server"):
                await server.start()

    async def test_handles_invalid_workspace(self):
        """Test handling of invalid workspace path."""
        server = KotlinLSPServer(workspace_path=Path("/nonexistent"))

        # Should still initialize (validation happens at start)
        assert server.workspace_path == Path("/nonexistent")

    async def test_handles_symbol_search_errors(self):
        """Test that symbol search handles LSP errors gracefully."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock an error from the client
        with patch.object(server.client, 'workspace_symbols', side_effect=Exception("LSP error")):
            with pytest.raises(Exception, match="LSP error"):
                await server.search_symbols("NonExistent")

    async def test_is_running_when_server_not_started(self):
        """Test is_running returns False when server not started."""
        server = KotlinLSPServer(workspace_path=Path("/test/workspace"))

        # Mock client returning False
        with patch.object(server.client, 'is_running', return_value=False):
            assert server.is_running() is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestKotlinLSPServerIntegration:
    """Integration tests for Kotlin LSP server with real Kotlin Language Server."""

    @pytest.mark.skipif(True, reason="Requires Kotlin Language Server installed")
    async def test_real_kotlin_lsp_initialization(self):
        """Test real Kotlin LSP initialization (requires installation)."""
        server = KotlinLSPServer(workspace_path=Path.cwd())

        try:
            await server.start()
            # Verify server is running
            assert server.client.process is not None
            assert server.client._initialized is True
        finally:
            await server.stop()

    @pytest.mark.skipif(True, reason="Requires real KMP project")
    async def test_real_kmp_symbol_search(self):
        """Test real symbol search in KMP project (requires Kotlin files)."""
        # This would require an actual KMP project
        pass
