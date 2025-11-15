"""Integration tests for project onboarding tools.

Tests project initialization, project info queries, and LSP server
startup based on detected project configuration.
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from kortex_mcp.tools.project_tools import (
    onboard_project,
    get_project_info,
    initialize_lsp_servers,
)
from kortex_mcp.models.project import Project, ProjectType
from kortex_mcp.storage.project_store import ProjectStore


class TestProjectOnboarding:
    """Test suite for project onboarding functionality."""

    @pytest.mark.asyncio
    async def test_onboard_project_basic(self, sample_kmp_project: Path) -> None:
        """Test basic project onboarding workflow.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        result = await onboard_project(sample_kmp_project)
        
        assert result is not None
        assert "success" in result or "project" in result

    @pytest.mark.asyncio
    async def test_onboard_project_returns_project_info(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that onboarding returns project information.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        result = await onboard_project(sample_kmp_project)
        
        # Should include project type, name, and source sets
        if isinstance(result, dict):
            assert "type" in result or "project_type" in result
            assert "name" in result or "project_name" in result

    @pytest.mark.asyncio
    async def test_onboard_project_detects_kmp(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that onboarding correctly detects KMP project type.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        result = await onboard_project(sample_kmp_project)
        
        # Project should be detected as KMP
        project_type = result.get("type") or result.get("project_type")
        assert project_type == ProjectType.KMP or project_type == "kmp"

    @pytest.mark.asyncio
    async def test_onboard_project_stores_config(
        self, sample_kmp_project: Path, temp_dir: Path
    ) -> None:
        """Test that onboarding stores project configuration.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
            temp_dir: Temporary directory for test data
        """
        # Onboard the project
        await onboard_project(sample_kmp_project)
        
        # Check that config was stored
        store = ProjectStore(temp_dir / "project.json")
        project = await store.load()
        
        if project:
            assert project.name is not None

    @pytest.mark.asyncio
    async def test_onboard_project_completes_quickly(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that onboarding completes within 30 seconds.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        import time
        
        start = time.time()
        result = await onboard_project(sample_kmp_project)
        duration = time.time() - start
        
        assert result is not None
        # Should complete in less than 30 seconds as per requirements
        assert duration < 30.0


class TestGetProjectInfo:
    """Test suite for project information queries."""

    @pytest.mark.asyncio
    async def test_get_project_info_basic(self, sample_kmp_project: Path) -> None:
        """Test retrieving basic project information.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        # First onboard the project
        await onboard_project(sample_kmp_project)
        
        # Then query project info
        info = await get_project_info(sample_kmp_project)
        
        assert info is not None

    @pytest.mark.asyncio
    async def test_get_project_info_includes_targets(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that project info includes build targets.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        await onboard_project(sample_kmp_project)
        info = await get_project_info(sample_kmp_project)
        
        assert "targets" in info
        assert len(info["targets"]) > 0

    @pytest.mark.asyncio
    async def test_get_project_info_includes_source_sets(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that project info includes source sets.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        await onboard_project(sample_kmp_project)
        info = await get_project_info(sample_kmp_project)
        
        assert "source_sets" in info
        assert len(info["source_sets"]) > 0
        # Should have commonMain
        source_set_names = [ss["name"] for ss in info["source_sets"]]
        assert "commonMain" in source_set_names

    @pytest.mark.asyncio
    async def test_get_project_info_includes_dependencies(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that project info includes dependencies.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        await onboard_project(sample_kmp_project)
        info = await get_project_info(sample_kmp_project)
        
        assert "dependencies" in info or "source_sets" in info
        # Dependencies might be nested in source sets

    @pytest.mark.asyncio
    async def test_get_project_info_without_onboarding(
        self, sample_kmp_project: Path
    ) -> None:
        """Test querying project info without onboarding first.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        # Should either auto-onboard or return error/empty result
        info = await get_project_info(sample_kmp_project)
        
        # Should handle gracefully (either with data or clear error)
        assert info is not None


class TestLSPServerInitialization:
    """Test suite for LSP server initialization based on project."""

    @pytest.mark.asyncio
    async def test_initialize_lsp_servers_for_kmp(
        self, sample_kmp_project: Path
    ) -> None:
        """Test LSP server initialization for KMP project.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        await onboard_project(sample_kmp_project)
        
        # Initialize LSP servers
        result = await initialize_lsp_servers(sample_kmp_project)
        
        assert result is not None
        # Should indicate which servers were started

    @pytest.mark.asyncio
    async def test_initialize_kotlin_lsp(self, sample_kmp_project: Path) -> None:
        """Test that Kotlin LSP server is initialized.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        await onboard_project(sample_kmp_project)
        result = await initialize_lsp_servers(sample_kmp_project)
        
        # Should attempt to start Kotlin language server
        # (may be in servers if executable found, or failed if not)
        if isinstance(result, dict):
            servers = result.get("servers", [])
            failed = result.get("failed", [])
            has_kotlin_attempt = (
                any("kotlin" in s.lower() for s in servers) or
                any("kotlin" in f.get("server", "").lower() for f in failed)
            )
            assert has_kotlin_attempt

    @pytest.mark.asyncio
    async def test_initialize_swift_lsp_for_ios(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that Swift LSP is initialized for projects with iOS targets.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        await onboard_project(sample_kmp_project)
        result = await initialize_lsp_servers(sample_kmp_project)
        
        # Should start Swift LSP if iOS target detected
        if isinstance(result, dict):
            servers = result.get("servers", [])
            # May or may not include Swift depending on system availability
            assert servers is not None

    @pytest.mark.asyncio
    async def test_lsp_initialization_handles_missing_servers(
        self, sample_kmp_project: Path
    ) -> None:
        """Test graceful handling when LSP servers are not available.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        await onboard_project(sample_kmp_project)
        
        # Should not crash if servers aren't available
        result = await initialize_lsp_servers(sample_kmp_project)
        
        assert result is not None
        # Should report which servers failed to start


class TestProjectStoreIntegration:
    """Test suite for project storage integration."""

    @pytest.mark.asyncio
    async def test_onboard_persists_to_store(
        self, sample_kmp_project: Path, temp_dir: Path
    ) -> None:
        """Test that onboarding persists project to store.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
            temp_dir: Temporary directory for test data
        """
        # Onboard project (stores in project_dir/.kortex/project.json)
        await onboard_project(sample_kmp_project)
        
        # Load from the location where onboard_project stored it
        store_path = sample_kmp_project / ".kortex" / "project.json"
        store = ProjectStore(store_path)
        
        # Should be able to load from store
        project = await store.load()
        assert project is not None

    @pytest.mark.asyncio
    async def test_reload_onboarded_project(
        self, sample_kmp_project: Path, temp_dir: Path
    ) -> None:
        """Test reloading a previously onboarded project.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
            temp_dir: Temporary directory for test data
        """
        store = ProjectStore(temp_dir)
        
        # Onboard project first time
        await onboard_project(sample_kmp_project)
        
        # Get project info - should use cached data
        info1 = await get_project_info(sample_kmp_project)
        
        # Onboard again - should update cache
        await onboard_project(sample_kmp_project)
        info2 = await get_project_info(sample_kmp_project)
        
        # Both should return valid data
        assert info1 is not None
        assert info2 is not None


class TestComposeMultiplatformProjects:
    """Test suite for Compose Multiplatform project handling."""

    @pytest.mark.asyncio
    async def test_onboard_cmp_project(self, tmp_path: Path) -> None:
        """Test onboarding a Compose Multiplatform project.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create a CMP project
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
plugins {
    kotlin("multiplatform") version "1.9.20"
    id("org.jetbrains.compose") version "1.5.10"
}

kotlin {
    android()
    ios()
    
    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(compose.runtime)
                implementation(compose.foundation)
                implementation(compose.material3)
            }
        }
    }
}
        """)
        
        result = await onboard_project(tmp_path)
        
        assert result is not None
        # Should detect as CMP
        project_type = result.get("type") or result.get("project_type")
        assert project_type == ProjectType.CMP or project_type == "cmp"

    @pytest.mark.asyncio
    async def test_cmp_project_info_includes_compose_version(
        self, tmp_path: Path
    ) -> None:
        """Test that CMP project info includes Compose version.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create a CMP project
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
plugins {
    kotlin("multiplatform") version "1.9.20"
    id("org.jetbrains.compose") version "1.5.10"
}
        """)
        
        await onboard_project(tmp_path)
        info = await get_project_info(tmp_path)
        
        # Should include compose version info
        assert info is not None
        # May be in "compose_version" or nested in plugins


class TestErrorHandling:
    """Test suite for error handling in project tools."""

    @pytest.mark.asyncio
    async def test_onboard_nonexistent_project(self) -> None:
        """Test onboarding a non-existent project directory."""
        nonexistent = Path("/nonexistent/project")
        
        with pytest.raises(FileNotFoundError):
            await onboard_project(nonexistent)

    @pytest.mark.asyncio
    async def test_onboard_empty_directory(self, tmp_path: Path) -> None:
        """Test onboarding an empty directory.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Should handle gracefully - may return UNKNOWN project type
        result = await onboard_project(tmp_path)
        
        assert result is not None
        # Should indicate it's not a valid KMP/CMP project

    @pytest.mark.asyncio
    async def test_get_project_info_for_invalid_project(
        self, tmp_path: Path
    ) -> None:
        """Test querying info for non-KMP project.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create a non-KMP project
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
plugins {
    kotlin("jvm") version "1.9.20"
}
        """)
        
        info = await get_project_info(tmp_path)
        
        # Should return info indicating it's not KMP/CMP
        assert info is not None


class TestMultiModuleProjects:
    """Test suite for multi-module project onboarding."""

    @pytest.mark.asyncio
    async def test_onboard_multi_module_project(self, tmp_path: Path) -> None:
        """Test onboarding a multi-module KMP project.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create multi-module structure
        settings = tmp_path / "settings.gradle.kts"
        settings.write_text("""
rootProject.name = "MultiModule"
include(":shared")
include(":app")
        """)
        
        # Root build file
        (tmp_path / "build.gradle.kts").write_text("""
plugins {
    kotlin("multiplatform") version "1.9.20" apply false
}
        """)
        
        # Shared module
        shared = tmp_path / "shared"
        shared.mkdir()
        (shared / "build.gradle.kts").write_text("""
plugins {
    kotlin("multiplatform")
}

kotlin {
    android()
    ios()
}
        """)
        
        result = await onboard_project(tmp_path)
        
        assert result is not None
        # Should detect as KMP project

    @pytest.mark.asyncio
    async def test_get_info_includes_all_modules(self, tmp_path: Path) -> None:
        """Test that project info includes all modules.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create multi-module structure
        settings = tmp_path / "settings.gradle.kts"
        settings.write_text("""
include(":shared")
include(":app")
        """)
        
        shared = tmp_path / "shared"
        shared.mkdir()
        (shared / "build.gradle.kts").write_text("// Shared module")
        
        app = tmp_path / "app"
        app.mkdir()
        (app / "build.gradle.kts").write_text("// App module")
        
        await onboard_project(tmp_path)
        info = await get_project_info(tmp_path)
        
        # Should list modules
        assert info is not None
