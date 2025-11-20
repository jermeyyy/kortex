"""Quickstart validation scenarios tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from kortex_mcp.models.project import Project, ProjectType, SourceSet, SourceSetType, Target
from kortex_mcp.models.symbol import Symbol, SymbolKind, CodeLocation
from kortex_mcp.models.lsp import Location, Range, Position, SymbolInformation
from kortex_mcp.tools.project_tools import onboard_project
from kortex_mcp.tools.lsp_tools import LSPTools
from kortex_mcp.tools.memory_tools import MemoryTools
from kortex_mcp.tools.planning_tools import PlanningTools
from kortex_mcp.lsp.manager import LSPManager
from kortex_mcp.analyzers.kmp_analyzer import KMPAnalyzer, ExpectActualPair

@pytest.mark.integration
@pytest.mark.asyncio
class TestQuickstartScenarios:
    """Tests matching the scenarios in quickstart.md."""

    async def test_scenario_1_project_onboarding(self, tmp_path):
        """Scenario 1: Project Onboarding."""
        project_root = tmp_path / "sample_kmp_project"
        project_root.mkdir()
        (project_root / "build.gradle.kts").write_text('plugins { kotlin("multiplatform") }')
        
        # Mock analyze_project to avoid complex Gradle parsing in this test
        with patch("kortex_mcp.tools.project_tools.analyze_project") as mock_analyze:
            mock_analyze.return_value = Project(
                name="sample_kmp_project",
                root_path=project_root,
                type=ProjectType.KMP,
                source_sets={
                    "commonMain": SourceSet(name="commonMain", type=SourceSetType.COMMON, source_dirs=[]),
                    "androidMain": SourceSet(name="androidMain", type=SourceSetType.ANDROID, source_dirs=[]),
                    "iosMain": SourceSet(name="iosMain", type=SourceSetType.IOS, source_dirs=[])
                },
                targets=[Target(name="android", platform="android"), Target(name="ios", platform="ios")]
            )
            
            result = await onboard_project(project_root)
            
            assert result["name"] == "sample_kmp_project"
            assert result["type"] == "kmp"
            # onboard_project returns counts for source_sets and targets
            assert result["source_sets"] == 3
            assert result["targets"] == 2
            
            # Verify storage
            assert (project_root / ".kortex" / "project.json").exists()

    async def test_scenario_2_symbol_navigation(self, tmp_path):
        """Scenario 2: Symbol Navigation."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        lsp_manager = MagicMock(spec=LSPManager)
        mock_client = AsyncMock()
        # is_running is synchronous
        mock_client.is_running = MagicMock(return_value=True)
        lsp_manager.get_client.return_value = mock_client
        
        # Mock search results
        mock_client.workspace_symbols = AsyncMock(return_value=[
            SymbolInformation(
                name="Repository",
                kind=5, # SymbolKind.Class
                location=Location(
                    uri=f"file://{project_root}/Repository.kt",
                    range=Range(start=Position(1, 0), end=Position(1, 10))
                ),
                containerName=""
            )
        ])
        
        # Mock definition result
        mock_client.go_to_definition = AsyncMock(return_value=Location(
            uri=f"file://{project_root}/Repository.kt",
            range=Range(start=Position(0, 0), end=Position(10, 0))
        ))
        
        # Mock references result
        mock_client.find_references = AsyncMock(return_value=[
            Location(
                uri=f"file://{project_root}/Usage.kt",
                range=Range(start=Position(5, 0), end=Position(5, 10))
            )
        ])
        
        tools = LSPTools(lsp_manager)
        
        # Step 1: Search
        search_results = await tools.search_symbols("Repository")
        assert search_results["count"] == 1
        assert search_results["symbols"][0]["name"] == "Repository"
        
        # Step 2: Go to definition
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value="content"):
            def_result = await tools.goto_definition(
                file=str(project_root / "Usage.kt"),
                line=5,
                character=10
            )
            assert def_result["found"] is True
            assert def_result["definition"]["file"] == str(project_root / "Repository.kt")
            
        # Step 3: Find references
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value="content"):
            refs_result = await tools.find_references(
                file=str(project_root / "Repository.kt"),
                line=0,
                character=0
            )
            assert refs_result["count"] == 1
            assert refs_result["references"][0]["file"] == str(project_root / "Usage.kt")

    async def test_scenario_3_memory_system(self, tmp_path):
        """Scenario 3: Memory System."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        tools = MemoryTools(project_root)
        await tools.initialize()
        
        # Step 1: Store memory
        await tools.store_memory(
            category="preferences",
            title="Coding Style",
            content="Prefer functional programming style"
        )
        
        # Step 2: Query memory
        result = await tools.query_memory(search_text="style")
        assert result["count"] >= 1
        assert result["memories"][0]["content"] == "Prefer functional programming style"

    async def test_scenario_4_planning_mode(self, tmp_path):
        """Scenario 4: Planning Mode."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        tools = PlanningTools(project_root)
        await tools.initialize()
        
        # Step 1: Create spec
        create_result = await tools.create_spec(
            spec_id="SPEC-001",
            title="New Feature",
            description="Implement login"
        )
        spec_id = create_result["spec_id"]
        
        # Step 2: Refine spec
        await tools.refine_spec(
            spec_id=spec_id,
            user_stories=[{
                "id": "US-001",
                "title": "As a user I want to login",
                "description": "Login with email and password",
                "priority": "P1"
            }]
        )
        
        # Verify
        assert tools.spec_store is not None
        spec = await tools.spec_store.get(spec_id)
        assert spec is not None
        assert spec.title == "New Feature"
        assert len(spec.user_stories) == 1
        assert spec.user_stories[0].title == "As a user I want to login"

    async def test_scenario_5_cross_platform(self, tmp_path):
        """Scenario 5: Cross-Platform Understanding."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        lsp_manager = MagicMock(spec=LSPManager)
        kmp_analyzer = MagicMock(spec=KMPAnalyzer)
        
        # Mock expect/actual detection
        kmp_analyzer.find_expect_actual_pairs.return_value = [
            ExpectActualPair(
                name="Foo",
                kind="class",
                expect_location={
                    "file": str(project_root / "common/Expect.kt"),
                    "line": 1,
                    "sourceSet": "commonMain"
                },
                actual_locations={
                    "androidMain": {
                        "file": str(project_root / "android/Actual.kt"),
                        "line": 1
                    },
                    "iosMain": {
                        "file": str(project_root / "ios/Actual.kt"),
                        "line": 1
                    }
                }
            )
        ]
        kmp_analyzer.validate_expect_actual_pair.return_value = (True, [])
        
        tools = LSPTools(lsp_manager, kmp_analyzer)
        
        result = await tools.navigate_expect_actual(symbol_name="Foo")
        
        assert len(result["actuals"]) == 2
        assert "androidMain" in result["actuals"]
        assert "iosMain" in result["actuals"]
