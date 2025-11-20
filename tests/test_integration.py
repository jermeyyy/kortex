"""Integration tests for complete Kortex workflow.

Tests the end-to-end flow of:
1. Onboarding a project
2. Searching for symbols
3. Editing code
4. Storing memories
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kortex_mcp.analyzers.kmp_analyzer import KMPAnalyzer
from kortex_mcp.lsp.manager import LSPManager
from kortex_mcp.models.project import Project, ProjectType, SourceSet, SourceSetType
from kortex_mcp.tools.editing_tools import EditingTools
from kortex_mcp.tools.lsp_tools import LSPTools
from kortex_mcp.tools.memory_tools import MemoryTools
from kortex_mcp.tools.project_tools import onboard_project


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_workflow(tmp_path):
    """Test the complete Kortex workflow."""

    # 1. Setup Project Structure
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / "build.gradle.kts").write_text('plugins { kotlin("multiplatform") }')
    (project_root / "src" / "commonMain" / "kotlin").mkdir(parents=True)
    (project_root / "src" / "commonMain" / "kotlin" / "User.kt").write_text(
        "class User {\n    fun getName(): String = \"Test\"\n}"
    )

    # 2. Onboard Project
    # Mock analyze_project to return a valid project without running full analysis
    with patch("kortex_mcp.tools.project_tools.analyze_project") as mock_analyze:
        mock_analyze.return_value = Project(
            name="test_project",
            root_path=project_root,
            type=ProjectType.KMP,
            source_sets={
                "commonMain": SourceSet(
                    name="commonMain",
                    type=SourceSetType.COMMON,
                    source_dirs=[project_root/"src"/"commonMain"]
                )
            }
        )

        onboard_result = await onboard_project(project_root)
        assert onboard_result["name"] == "test_project"
        assert onboard_result["type"] == "kmp"

    # 3. Setup Tools with Mocked LSP
    lsp_manager = LSPManager()
    mock_client = MagicMock()
    mock_client.is_running.return_value = True

    # Mock symbol search response
    mock_symbol = MagicMock()
    mock_symbol.name = "User"
    mock_symbol.kind = 5
    mock_symbol.location.uri = f"file://{project_root}/src/commonMain/kotlin/User.kt"
    mock_symbol.location.range.start.line = 0
    mock_symbol.location.range.start.character = 0
    mock_symbol.location.range.end.line = 2
    mock_symbol.location.range.end.character = 1
    mock_symbol.containerName = ""

    mock_client.workspace_symbols = AsyncMock()
    mock_client.workspace_symbols.return_value = [mock_symbol]
    # Mock apply_edit response
    mock_client.apply_workspace_edit = AsyncMock()
    mock_client.apply_workspace_edit.return_value = True

    lsp_manager.clients["kotlin"] = mock_client

    kmp_analyzer = KMPAnalyzer(project_root)
    lsp_tools = LSPTools(lsp_manager, kmp_analyzer)
    editing_tools = EditingTools(lsp_manager, kmp_analyzer)
    memory_tools = MemoryTools(project_root)
    await memory_tools.initialize()

    # 4. Search Symbols
    search_result = await lsp_tools.search_symbols("User")
    assert search_result["count"] == 1
    assert search_result["symbols"][0]["name"] == "User"

    # 5. Edit Code (Add Method)
    # Mock file reading for AST analysis in editing tools
    with patch.object(kmp_analyzer, 'find_class_insertion_point', return_value={"line": 1, "indentation": "    "}):
        with patch.object(kmp_analyzer, 'detect_indentation_style', return_value={"type": "spaces", "size": 4}):
            await editing_tools.add_method(
                class_name="User",
                method_signature="fun getEmail(): String",
                method_body='return "test@example.com"'
            )

            # Verify LSP client was called with edit
            mock_client.apply_workspace_edit.assert_called_once()

    # 6. Store Memory
    await memory_tools.store_memory(
        category="patterns",
        title="User Model",
        content="User class is the core model",
        tags=["model", "core"]
    )

    # 7. Query Memory
    result = await memory_tools.query_memory(search_text="User")
    memories = result["memories"]
    assert len(memories) >= 1
    assert memories[0]["title"] == "User Model"

    # Cleanup
    await lsp_manager.stop_all()
