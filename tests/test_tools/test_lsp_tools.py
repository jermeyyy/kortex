"""Integration tests for LSP-based MCP tools.

These tests verify end-to-end functionality of LSP tools including
symbol search, go-to-definition, and find references.

NOTE: These tests are written BEFORE implementation (TDD approach)
and will FAIL until T027-T035 are implemented.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from kortex_mcp.lsp.client import LSPClient
from kortex_mcp.lsp.manager import LSPManager
from kortex_mcp.models.lsp import Location, Position, Range, SymbolInformation
from kortex_mcp.tools.lsp_tools import LSPTools
from kortex_mcp.tools.base import ToolValidationError
from kortex_mcp.analyzers.kmp_analyzer import KMPAnalyzer



@pytest.mark.integration
@pytest.mark.asyncio
class TestSymbolSearchTool:
    """Integration tests for symbol search MCP tool.

    Tests the complete flow from MCP tool invocation through LSP client
    to symbol search results.
    """

    async def test_symbol_search_tool_exists(self):
        """Test that symbol search tool is registered with MCP server."""
        # Mock dependencies
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager)
        
        assert hasattr(tools, "search_symbols")
        assert callable(tools.search_symbols)

    async def test_symbol_search_with_query_parameter(self):
        """Test symbol search tool with query parameter."""
        # Mock LSP client with symbol data
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.workspace_symbols = AsyncMock(return_value=[
            SymbolInformation(
                name="Repository",
                kind=5,  # Class
                location=Location(
                    uri="file:///test/Repository.kt",
                    range=Range(
                        start=Position(line=10, character=0),
                        end=Position(line=20, character=0)
                    )
                ),
                containerName="com.example.kmp"
            ),
            SymbolInformation(
                name="UserRepository",
                kind=5,
                location=Location(
                    uri="file:///test/UserRepository.kt",
                    range=Range(
                        start=Position(line=5, character=0),
                        end=Position(line=15, character=0)
                    )
                ),
                containerName="com.example.kmp.data"
            )
        ])
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        result = await tools.search_symbols("Repository")
        
        assert result["count"] == 2
        assert len(result["symbols"]) == 2
        assert result["symbols"][0]["name"] == "Repository"
        assert result["symbols"][0]["kind"] == "class"

    async def test_symbol_search_returns_formatted_results(self):
        """Test that symbol search tool returns properly formatted results."""
        # Mock LSP client with symbol data
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.workspace_symbols = AsyncMock(return_value=[
            SymbolInformation(
                name="Repository",
                kind=5,  # Class
                location=Location(
                    uri="file:///test/Repository.kt",
                    range=Range(
                        start=Position(line=10, character=0),
                        end=Position(line=20, character=0)
                    )
                ),
                containerName="com.example.kmp"
            )
        ])
    
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
    
        tools = LSPTools(mock_manager)
        result = await tools.search_symbols("Repository")
    
        symbol = result["symbols"][0]
        assert "name" in symbol
        assert "kind" in symbol
        assert "file" in symbol
        assert "line" in symbol
        assert "container" in symbol
    
        assert symbol["file"] == "/test/Repository.kt"
        assert symbol["line"] == 10  # 0-based line number
        assert symbol["container"] == "com.example.kmp"

@pytest.mark.integration
@pytest.mark.asyncio
class TestFindReferencesTool:
    """Integration tests for find references MCP tool.

    Tests finding all references to a symbol across the workspace.
    """

    async def test_find_references_tool_exists(self):
        """Test that find references tool is registered."""
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager)
        
        assert hasattr(tools, "find_references")
        assert callable(tools.find_references)

    async def test_find_references_with_file_and_position(self):
        """Test find references with file path and position."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[
            Location(
                uri="file:///test/Usage1.kt",
                range=Range(
                    start=Position(line=10, character=0),
                    end=Position(line=10, character=10)
                )
            ),
            Location(
                uri="file:///test/Usage2.kt",
                range=Range(
                    start=Position(line=20, character=0),
                    end=Position(line=20, character=10)
                )
            )
        ])
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            result = await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10
            )
        
        assert result["count"] == 2
        assert len(result["references"]) == 2
        assert result["references"][0]["file"] == "/test/Usage1.kt"
        assert result["references"][0]["line"] == 10

    async def test_find_references_returns_all_locations(self):
        """Test find references returns all reference locations."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[
            Location(
                uri="file:///test/Usage1.kt",
                range=Range(
                    start=Position(line=10, character=0),
                    end=Position(line=10, character=10)
                )
            ),
            Location(
                uri="file:///test/Usage2.kt",
                range=Range(
                    start=Position(line=20, character=0),
                    end=Position(line=20, character=10)
                )
            )
        ])
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            result = await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10
            )
        
        assert len(result["references"]) == 2
        assert result["references"][0]["file"] == "/test/Usage1.kt"
        assert result["references"][1]["file"] == "/test/Usage2.kt"

    async def test_find_references_handles_no_references(self):
        """Test find references when symbol has no references."""
        # Mock LSP client returning empty list
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[])
    
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
    
        tools = LSPTools(mock_manager)
    
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            result = await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10
            )
        
        assert result["count"] == 0
        assert len(result["references"]) == 0

    async def test_find_references_includes_declaration_by_default(self):
        """Test that find references includes declaration by default."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[])
    
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
    
        tools = LSPTools(mock_manager)
    
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10
            )
            
            # Verify client was called with includeDeclaration=True
            mock_client.find_references.assert_called_once()
            args = mock_client.find_references.call_args
            assert args[0][3] is True  # 4th argument is include_declaration

    async def test_find_references_can_exclude_declaration(self):
        """Test find references can exclude declaration location."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[])
    
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
    
        tools = LSPTools(mock_manager)
    
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10,
                include_declaration=False
            )
            
            # Verify client was called with includeDeclaration=False
            mock_client.find_references.assert_called_once()
            args = mock_client.find_references.call_args
            assert args[0][3] is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestGoToDefinitionTool:
    """Integration tests for go-to-definition MCP tool.

    Tests navigation from a symbol usage to its definition location.
    """

    async def test_goto_definition_tool_exists(self):
        """Test that go-to-definition tool is registered."""
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager)
        
        assert hasattr(tools, "goto_definition")
        assert callable(tools.goto_definition)

    async def test_goto_definition_with_file_and_position(self):
        """Test go-to-definition with file path and position."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.go_to_definition = AsyncMock(return_value=Location(
            uri="file:///test/Repository.kt",
            range=Range(
                start=Position(line=10, character=0),
                end=Position(line=20, character=0)
            )
        ))
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        
        # Mock file existence check
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            result = await tools.goto_definition(
                file="/test/Usage.kt",
                line=5,
                character=10
            )
        
        assert result["found"] is True
        assert result["definition"]["file"] == "/test/Repository.kt"
        assert result["definition"]["line"] == 10

    async def test_goto_definition_returns_location(self):
        """Test go-to-definition returns proper location format."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.go_to_definition = AsyncMock(return_value=Location(
            uri="file:///test/Repository.kt",
            range=Range(
                start=Position(line=10, character=0),
                end=Position(line=20, character=0)
            )
        ))
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            result = await tools.goto_definition(
                file="/test/Usage.kt",
                line=5,
                character=10
            )
        
        assert "definition" in result
        assert result["definition"]["file"] == "/test/Repository.kt"

    async def test_goto_definition_handles_no_definition(self):
        """Test go-to-definition when symbol has no definition."""
        # Mock LSP client returning None
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.go_to_definition = AsyncMock(return_value=None)
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            result = await tools.goto_definition(
                file="/test/Usage.kt",
                line=5,
                character=10
            )
        
        assert result["found"] is False
        assert result["definition"] is None

    async def test_goto_definition_validates_file_exists(self):
        """Test go-to-definition validates file exists."""
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager)
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: False)
            
            with pytest.raises(ToolValidationError):
                await tools.goto_definition(
                    file="/test/NonExistent.kt",
                    line=5,
                    character=10
                )

    async def test_goto_definition_validates_position(self):
        """Test go-to-definition validates line and character."""
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager)
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            
            with pytest.raises(ToolValidationError):
                await tools.goto_definition(
                    file="/test/Usage.kt",
                    line=-1,
                    character=10
                )

    async def test_goto_definition_converts_file_to_uri(self):
        """Test that tool converts file path to proper file:// URI."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.go_to_definition = AsyncMock(return_value=None)
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            await tools.goto_definition(
                file="/test/Usage.kt",
                line=5,
                character=10
            )
            
            # Verify client was called with correct URI
            mock_client.go_to_definition.assert_called_once()
            args = mock_client.go_to_definition.call_args
            assert "file:///test/Usage.kt" in str(args)





@pytest.mark.integration
@pytest.mark.asyncio
class TestFindReferencesTool:
    """Integration tests for find references MCP tool.

    Tests finding all references to a symbol across the workspace.
    """

    async def test_find_references_tool_exists(self):
        """Test that find references tool is registered."""
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager)
        
        assert hasattr(tools, "find_references")
        assert callable(tools.find_references)

    async def test_find_references_with_file_and_position(self):
        """Test find references with file path and position."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[
            Location(
                uri="file:///test/Usage1.kt",
                range=Range(
                    start=Position(line=10, character=0),
                    end=Position(line=10, character=10)
                )
            ),
            Location(
                uri="file:///test/Usage2.kt",
                range=Range(
                    start=Position(line=20, character=0),
                    end=Position(line=20, character=10)
                )
            )
        ])
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            result = await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10
            )
        
        assert result["count"] == 2
        assert len(result["references"]) == 2
        assert result["references"][0]["file"] == "/test/Usage1.kt"
        assert result["references"][0]["line"] == 10

    async def test_find_references_returns_all_locations(self):
        """Test find references returns all reference locations."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[
            Location(
                uri="file:///test/Usage1.kt",
                range=Range(
                    start=Position(line=10, character=0),
                    end=Position(line=10, character=10)
                )
            ),
            Location(
                uri="file:///test/Usage2.kt",
                range=Range(
                    start=Position(line=20, character=0),
                    end=Position(line=20, character=10)
                )
            )
        ])
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            result = await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10
            )
        
        assert len(result["references"]) == 2
        assert result["references"][0]["file"] == "/test/Usage1.kt"
        assert result["references"][1]["file"] == "/test/Usage2.kt"

    async def test_find_references_handles_no_references(self):
        """Test find references when symbol has no references."""
        # Mock LSP client returning empty list
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[])
    
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
    
        tools = LSPTools(mock_manager)
    
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            result = await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10
            )
        
        assert result["count"] == 0
        assert len(result["references"]) == 0

    async def test_find_references_includes_declaration_by_default(self):
        """Test that find references includes declaration by default."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[])
    
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
    
        tools = LSPTools(mock_manager)
    
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10
            )
            
            # Verify client was called with includeDeclaration=True
            mock_client.find_references.assert_called_once()
            args = mock_client.find_references.call_args
            assert args[0][3] is True  # 4th argument is include_declaration

    async def test_find_references_can_exclude_declaration(self):
        """Test find references can exclude declaration location."""
        # Mock LSP client
        mock_client = AsyncMock(spec=LSPClient)
        mock_client.find_references = AsyncMock(return_value=[])
    
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
    
        tools = LSPTools(mock_manager)
    
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
            m.setattr("pathlib.Path.read_text", lambda self, encoding: "content")
            
            await tools.find_references(
                file="/test/Def.kt",
                line=5,
                character=10,
                include_declaration=False
            )
            
            # Verify client was called with includeDeclaration=False
            mock_client.find_references.assert_called_once()
            args = mock_client.find_references.call_args
            assert args[0][3] is False

    async def test_find_references_validates_file_exists(self):
        """Test find references validates file exists."""
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager)
    
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: False)
    
            with pytest.raises(ToolValidationError):
                await tools.find_references(
                    file="/test/NonExistent.kt",
                    line=5,
                    character=10
                )

    async def test_find_references_validates_position(self):
        """Test find references validates line and character."""
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager)
    
        with pytest.MonkeyPatch.context() as m:
            m.setattr("pathlib.Path.exists", lambda self: True)
    
            with pytest.raises(ToolValidationError):
                await tools.find_references(
                    file="/test/Def.kt",
                    line=-1,
                    character=10
                )


    async def test_find_references_groups_by_file(self):
        """Test find references can group results by file."""
        # Optional enhancement: Group references by file
        # {
        #     "by_file": {
        #         "/path/to/file1.kt": [{"line": 10, "character": 5}, ...],
        #         "/path/to/file2.kt": [{"line": 20, "character": 10}]
        #     }
        # }

        pytest.skip("Optional feature - may be implemented later")

    async def test_find_references_handles_cross_platform(self):
        """Test find references works across KMP source sets."""
        # Should find references in commonMain, androidMain, iosMain
        # This tests the multi-LSP capability

        pytest.skip("Cross-platform feature - will be tested after multi-LSP support")


@pytest.mark.integration
@pytest.mark.asyncio
class TestLSPToolsErrorHandling:
    """Integration tests for error handling across LSP tools."""

    async def test_tools_handle_lsp_server_crash(self):
        """Test that tools handle LSP server crashes gracefully."""
        # Mock LSP manager with crashed server
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.side_effect = Exception("Server crashed")
        
        tools = LSPTools(mock_manager)
        
        from kortex_mcp.tools.base import ToolError
        with pytest.raises(ToolError):
            await tools.search_symbols("Repository")

    async def test_tools_timeout_after_configured_duration(self):
        """Test that tools timeout after configured duration."""
        # Mock LSP client that hangs
        mock_client = AsyncMock(spec=LSPClient)
        async def hang(*args, **kwargs):
            await asyncio.sleep(1.0)
            return []
            
        mock_client.workspace_symbols = AsyncMock(side_effect=hang)
        
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.return_value = mock_client
        
        tools = LSPTools(mock_manager)
        
        # We can't easily change the timeout of the decorated function
        # So we'll mock asyncio.wait_for to raise TimeoutError
        with pytest.MonkeyPatch.context() as m:
            async def mock_wait_for(fut, timeout):
                raise asyncio.TimeoutError()
                
            m.setattr("asyncio.wait_for", mock_wait_for)
            
            from kortex_mcp.tools.base import ToolTimeout
            with pytest.raises(ToolTimeout):
                await tools.search_symbols("Repository")

    async def test_tools_log_errors_appropriately(self):
        """Test that tools log errors with appropriate context."""
        # Should use logger from utils/logging.py
        mock_manager = MagicMock(spec=LSPManager)
        mock_manager.get_client.side_effect = Exception("Test error")
        
        tools = LSPTools(mock_manager)
        
        with pytest.raises(Exception):
            await tools.search_symbols("Repository")

        # Should include tool name, parameters, and error details

        pytest.skip("Logging will be implemented in T035")

    async def test_tools_return_consistent_error_format(self):
        """Test that all tools return consistent error format."""
        # Expected error format (from base.py):
        # {
        #     "error": "Error message",
        #     "details": {...},
        #     "tool": "tool_name"
        # }

        pytest.skip("Error format will be implemented in T035")


@pytest.mark.integration
@pytest.mark.asyncio
class TestLSPToolsWithRealProject:
    """Integration tests using real KMP project fixture."""

    async def test_symbol_search_in_kmp_project(self, sample_kmp_project):
        """Test symbol search in real KMP project fixture."""
        # Use sample_kmp_project fixture
        # Search for "Repository" class
        # Expected: Find Repository in commonMain, AndroidRepository in androidMain, etc.

        pytest.skip("Will test with real LSP server after implementation")

    async def test_goto_definition_across_source_sets(self, sample_kmp_project):
        """Test go-to-definition from platform-specific to common code."""
        # Navigate from androidMain usage to commonMain definition
        # Tests that LSP correctly handles KMP project structure

        pytest.skip("Will test with real LSP server after implementation")

    async def test_find_references_across_source_sets(self, sample_kmp_project):
        """Test find references across different source sets."""
        # Find all references to a common interface
        # Should find usages in commonMain, androidMain, iosMain

        pytest.skip("Will test with real LSP server after implementation")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
class TestLSPToolsPerformance:
    """Performance tests for LSP tools."""

    async def test_symbol_search_completes_within_timeout(self):
        """Test symbol search completes within 2 seconds."""
        # Performance goal from plan.md: <2 seconds for 10,000 symbols

        pytest.skip("Performance testing after implementation")

    async def test_goto_definition_completes_quickly(self):
        """Test go-to-definition completes within 1 second."""
        # Performance goal: <1 second for 90% of requests

        pytest.skip("Performance testing after implementation")

    async def test_find_references_handles_large_codebase(self):
        """Test find references in large codebase (50,000+ LOC)."""
        # Scale goal from plan.md: Handle 50,000+ LOC

        pytest.skip("Performance testing with large project after implementation")


# Helper functions for testing

def create_mock_symbol(
    name: str,
    kind: int,
    file: str,
    line: int,
    container: str | None = None
) -> SymbolInformation:
    """Create a mock SymbolInformation for testing.

    Args:
        name: Symbol name
        kind: Symbol kind (LSP SymbolKind)
        file: File path
        line: Line number
        container: Container name

    Returns:
        SymbolInformation instance
    """
    return SymbolInformation(
        name=name,
        kind=kind,
        location=Location(
            uri=f"file://{file}",
            range=Range(
                start=Position(line=line, character=0),
                end=Position(line=line + 1, character=0)
            )
        ),
        containerName=container
    )


def create_mock_location(file: str, line: int, character: int = 0) -> Location:
    """Create a mock Location for testing.

    Args:
        file: File path
        line: Line number
        character: Character offset

    Returns:
        Location instance
    """
    return Location(
        uri=f"file://{file}",
        range=Range(
            start=Position(line=line, character=character),
            end=Position(line=line, character=character + 1)
        )
    )


@pytest.mark.integration
@pytest.mark.asyncio
class TestCrossPlatformSymbolResolution:
    """Integration tests for cross-platform symbol resolution (T039).

    Tests the ability to search for and resolve symbols across Kotlin,
    Swift, and Objective-C codebases, understanding interop relationships.
    """

    async def test_cross_language_symbol_search_kotlin_to_swift(self):
        """Test searching for Kotlin symbols used in Swift code."""
        # Expected: Tool can find Kotlin class and show Swift usage
        # Given a Kotlin class "SharedRepository" in commonMain
        # When querying its usage in Swift files
        # Then return Swift call sites

        pytest.skip("Cross-platform tool not implemented yet - will be implemented in T046")

    async def test_cross_language_symbol_search_swift_to_kotlin(self):
        """Test finding Kotlin implementation from Swift usage."""
        # Expected: From Swift call site, navigate to Kotlin definition
        # Given Swift code calling a Kotlin class
        # When requesting go-to-definition
        # Then navigate to actual Kotlin implementation

        pytest.skip("Cross-platform tool not implemented yet - will be implemented in T046")

    async def test_cross_language_symbol_search_multiple_lsp_servers(self):
        """Test querying symbols across multiple active LSP servers."""
        # Mock multiple LSP servers (Kotlin, Swift)
        mock_kotlin_client = AsyncMock(spec=LSPClient)
        mock_kotlin_client.workspace_symbols = AsyncMock(return_value=[
            SymbolInformation(
                name="SharedRepository",
                kind=5,
                location=Location(
                    uri="file:///test/commonMain/SharedRepository.kt",
                    range=Range(
                        start=Position(line=10, character=0),
                        end=Position(line=50, character=0)
                    )
                ),
                containerName="com.example.shared"
            )
        ])

        mock_swift_client = AsyncMock(spec=LSPClient)
        mock_swift_client.workspace_symbols = AsyncMock(return_value=[
            SymbolInformation(
                name="SharedRepository",
                kind=5,
                location=Location(
                    uri="file:///test/iosMain/SharedRepository.swift",
                    range=Range(
                        start=Position(line=5, character=0),
                        end=Position(line=15, character=0)
                    )
                ),
                containerName="SharedModule"
            )
        ])

        # Expected: Cross-platform tool should query all relevant LSP servers
        # and aggregate results showing symbols from both Kotlin and Swift

        pytest.skip("Cross-platform tool not implemented yet - will be implemented in T046")

    async def test_cross_language_handles_objc_interop(self):
        """Test handling Objective-C interop with Kotlin."""
        # Expected: Can find Objective-C usage of Kotlin classes
        # Kotlin classes exposed via @objc annotations

        pytest.skip("Cross-platform tool not implemented yet - will be implemented in T046")

    async def test_cross_language_respects_platform_boundaries(self):
        """Test that cross-platform search respects platform-specific code."""
        # Expected: Understand that androidMain code is not visible to iOS
        # Only commonMain and iosMain are relevant for Swift interop

        pytest.skip("Cross-platform tool not implemented yet - will be implemented in T046")

    async def test_cross_language_handles_no_swift_lsp(self):
        """Test graceful handling when Swift LSP is not available."""
        # Expected: If only Kotlin LSP is running, tool should still work
        # but report limited cross-platform information

        pytest.skip("Cross-platform tool not implemented yet - will be implemented in T046")


@pytest.mark.integration
@pytest.mark.asyncio
class TestExpectActualNavigation:
    """Integration tests for expect/actual navigation tool."""

    async def test_find_actual_implementations_for_expect(self):
        """Test finding actual implementations for an expect declaration."""
        # Mock KMP analyzer
        mock_analyzer = AsyncMock(spec=KMPAnalyzer)
        mock_analyzer.find_expect_actual_pairs = AsyncMock(return_value=[
            MagicMock(
                name="Platform",
                kind="class",
                expect_location={"file": "/test/common/Platform.kt", "line": 5},
                actual_locations={
                    "androidMain": {
                        "file": "/test/android/Platform.kt",
                        "line": 10,
                        "kind": "class"
                    },
                    "iosMain": {
                        "file": "/test/ios/Platform.kt",
                        "line": 15,
                        "kind": "class"
                    }
                }
            )
        ])
        mock_analyzer.validate_expect_actual_pair = MagicMock(return_value=(True, []))
        
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager, mock_analyzer)
        
        result = await tools.navigate_expect_actual(
            symbol_name="Platform"
        )
        
        assert "actuals" in result
        assert "androidMain" in result["actuals"]
        assert "iosMain" in result["actuals"]
        assert result["actuals"]["androidMain"]["file"] == "/test/android/Platform.kt"

    async def test_navigate_from_actual_to_expect(self):
        """Test navigating from actual implementation to expect declaration."""
        # Mock KMP analyzer
        mock_analyzer = AsyncMock(spec=KMPAnalyzer)
        mock_analyzer.find_expect_actual_pairs = AsyncMock(return_value=[
            MagicMock(
                name="Platform",
                kind="class",
                expect_location={"file": "/test/common/Platform.kt", "line": 5},
                actual_locations={}
            )
        ])
        mock_analyzer.validate_expect_actual_pair = MagicMock(return_value=(True, []))
        
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager, mock_analyzer)
        
        result = await tools.navigate_expect_actual(
            symbol_name="Platform"
        )
        
        assert "expect" in result
        assert result["expect"]["file"] == "/test/common/Platform.kt"
        assert result["expect"]["line"] == 5

    async def test_expect_actual_for_functions(self):
        """Test expect/actual navigation for functions."""
        # Mock KMP analyzer
        mock_analyzer = AsyncMock(spec=KMPAnalyzer)
        mock_analyzer.find_expect_actual_pairs = AsyncMock(return_value=[
            MagicMock(
                name="getPlatformName",
                kind="function",
                expect_location={"file": "/test/common/Utils.kt", "line": 5},
                actual_locations={
                    "jvmMain": {
                        "file": "/test/jvm/Utils.kt",
                        "line": 20,
                        "kind": "function"
                    }
                }
            )
        ])
        mock_analyzer.validate_expect_actual_pair = MagicMock(return_value=(True, []))
        
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager, mock_analyzer)
        
        result = await tools.navigate_expect_actual(
            symbol_name="getPlatformName"
        )
        
        assert "jvmMain" in result["actuals"]
        assert result["actuals"]["jvmMain"]["kind"] == "function"

    async def test_expect_actual_for_properties(self):
        """Test expect/actual navigation for properties."""
        # Mock KMP analyzer
        mock_analyzer = AsyncMock(spec=KMPAnalyzer)
        mock_analyzer.find_expect_actual_pairs = AsyncMock(return_value=[
            MagicMock(
                name="platformVersion",
                kind="property",
                expect_location={"file": "/test/common/Config.kt", "line": 5},
                actual_locations={
                    "jsMain": {
                        "file": "/test/js/Config.kt",
                        "line": 8,
                        "kind": "property"
                    }
                }
            )
        ])
        mock_analyzer.validate_expect_actual_pair = MagicMock(return_value=(True, []))
        
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager, mock_analyzer)
        
        result = await tools.navigate_expect_actual(
            symbol_name="platformVersion"
        )
        
        assert "jsMain" in result["actuals"]
        assert result["actuals"]["jsMain"]["kind"] == "property"

    async def test_expect_actual_handles_mismatched_signatures(self):
        """Test handling of mismatched expect/actual signatures."""
        # This is handled by KMPAnalyzer validation, tool should report it
        # Optional: Tool could return validation warnings

        pytest.skip("Validation feature - may be implemented later")

    async def test_expect_actual_with_typealiases(self):
        """Test expect/actual navigation with typealiases."""
        # actual typealias MyClass = java.util.Date

        pytest.skip("Advanced feature - may be implemented later")

    async def test_expect_actual_detects_missing_implementations(self):
        """Test detection of missing actual implementations."""
        # Mock KMP analyzer
        mock_analyzer = AsyncMock(spec=KMPAnalyzer)
        mock_analyzer.find_expect_actual_pairs = AsyncMock(return_value=[
            MagicMock(
                name="Platform",
                kind="class",
                expect_location={"file": "/test/common/Platform.kt", "line": 5},
                actual_locations={}
            )
        ])
        mock_analyzer.validate_expect_actual_pair = MagicMock(return_value=(False, ["Missing actual for iosMain"]))
        
        mock_manager = MagicMock(spec=LSPManager)
        tools = LSPTools(mock_manager, mock_analyzer)
        
        result = await tools.navigate_expect_actual(
            symbol_name="Platform"
        )
        
        assert result["validation"]["is_valid"] is False
        assert "Missing actual for iosMain" in result["validation"]["issues"]

    async def test_expect_actual_groups_by_source_set(self):
        """Test grouping of actuals by source set."""
        # Already covered by test_find_actual_implementations_for_expect
        pass

