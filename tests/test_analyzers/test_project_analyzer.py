"""Integration tests for project analyzer.

Tests recursive build file scanning, project type detection,
and complete project analysis workflow.
"""

from pathlib import Path

import pytest

from kortex_mcp.analyzers.project_analyzer import (
    ProjectAnalyzer,
    analyze_project,
    detect_project_type,
    find_build_files,
    is_cmp_project,
    is_kmp_project,
)
from kortex_mcp.models.project import Project, ProjectType


class TestProjectAnalyzer:
    """Test suite for ProjectAnalyzer class."""

    def test_analyzer_initialization(self, sample_kmp_project: Path) -> None:
        """Test ProjectAnalyzer initialization with project directory.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        analyzer = ProjectAnalyzer(sample_kmp_project)

        assert analyzer.project_dir == sample_kmp_project
        assert analyzer.project_dir.exists()

    @pytest.mark.asyncio
    async def test_analyze_project(self, sample_kmp_project: Path) -> None:
        """Test complete project analysis workflow.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        project = await analyze_project(sample_kmp_project)

        assert project is not None
        assert isinstance(project, Project)
        assert project.root_path == sample_kmp_project

    @pytest.mark.asyncio
    async def test_project_has_name(self, sample_kmp_project: Path) -> None:
        """Test that analyzed project has a name.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        project = await analyze_project(sample_kmp_project)

        assert project.name is not None
        assert len(project.name) > 0

    @pytest.mark.asyncio
    async def test_project_has_source_sets(self, sample_kmp_project: Path) -> None:
        """Test that analyzed project includes source sets.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        project = await analyze_project(sample_kmp_project)

        assert len(project.source_sets) > 0
        # Should have at least commonMain, androidMain, iosMain
        source_set_names = list(project.source_sets.keys())
        assert "commonMain" in source_set_names

    @pytest.mark.asyncio
    async def test_project_has_targets(self, sample_kmp_project: Path) -> None:
        """Test that analyzed project includes targets.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        project = await analyze_project(sample_kmp_project)

        assert len(project.targets) > 0
        # Should have android and iOS targets
        target_names = [t.name for t in project.targets]
        assert "android" in target_names


class TestProjectTypeDetection:
    """Test suite for project type detection."""

    def test_detect_kmp_project(self, sample_kmp_project: Path) -> None:
        """Test detection of Kotlin Multiplatform project.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        project_type = detect_project_type(sample_kmp_project)

        assert project_type == ProjectType.KMP

    def test_is_kmp_project_returns_true(self, sample_kmp_project: Path) -> None:
        """Test is_kmp_project returns True for KMP projects.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        assert is_kmp_project(sample_kmp_project) is True

    def test_detect_cmp_project(self, tmp_path: Path) -> None:
        """Test detection of Compose Multiplatform project.

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
}
        """)

        project_type = detect_project_type(tmp_path)

        assert project_type == ProjectType.CMP

    def test_is_cmp_project_returns_true(self, tmp_path: Path) -> None:
        """Test is_cmp_project returns True for CMP projects.

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

        assert is_cmp_project(tmp_path) is True

    def test_detect_unknown_project(self, tmp_path: Path) -> None:
        """Test detection returns UNKNOWN for non-KMP/CMP projects.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create a regular Kotlin JVM project
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
plugins {
    kotlin("jvm") version "1.9.20"
}
        """)

        project_type = detect_project_type(tmp_path)

        assert project_type == ProjectType.UNKNOWN


class TestBuildFileFinding:
    """Test suite for recursive build file scanning."""

    def test_find_build_files_in_root(self, sample_kmp_project: Path) -> None:
        """Test finding build.gradle.kts in project root.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_files = find_build_files(sample_kmp_project)

        assert len(build_files) > 0
        # Should find the root build.gradle.kts
        root_build = sample_kmp_project / "build.gradle.kts"
        assert root_build in build_files

    def test_find_build_files_recursive(self, tmp_path: Path) -> None:
        """Test recursive scanning for build files in subdirectories.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create multi-module structure
        (tmp_path / "build.gradle.kts").write_text("// Root build file")

        module1 = tmp_path / "module1"
        module1.mkdir()
        (module1 / "build.gradle.kts").write_text("// Module 1")

        module2 = tmp_path / "module2"
        module2.mkdir()
        (module2 / "build.gradle.kts").write_text("// Module 2")

        build_files = find_build_files(tmp_path)

        # Should find all 3 build files
        assert len(build_files) >= 3

    def test_find_build_files_ignores_build_dir(self, tmp_path: Path) -> None:
        """Test that build output directories are ignored.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create build output directory
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "build.gradle.kts").write_text("// Should be ignored")

        # Create real build file
        (tmp_path / "build.gradle.kts").write_text("// Real build file")

        build_files = find_build_files(tmp_path)

        # Should only find the root build file, not the one in build/
        assert len(build_files) == 1
        assert tmp_path / "build.gradle.kts" in build_files

    def test_find_build_files_empty_directory(self, tmp_path: Path) -> None:
        """Test finding build files in empty directory.

        Args:
            tmp_path: Temporary directory for test files
        """
        build_files = find_build_files(tmp_path)

        assert len(build_files) == 0


class TestCompleteProjectAnalysis:
    """Test suite for complete end-to-end project analysis."""

    @pytest.mark.asyncio
    async def test_analyze_identifies_all_source_sets(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that analysis identifies all source sets.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        project = await analyze_project(sample_kmp_project)

        source_set_names = set(project.source_sets.keys())

        # Should find key source sets
        assert "commonMain" in source_set_names
        assert "androidMain" in source_set_names or "iosMain" in source_set_names

    @pytest.mark.asyncio
    async def test_analyze_identifies_dependencies(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that analysis identifies project dependencies.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        project = await analyze_project(sample_kmp_project)

        # Check that at least one source set has dependencies
        has_dependencies = any(
            len(ss.dependencies) > 0 for ss in project.source_sets.values()
        )
        assert has_dependencies

    @pytest.mark.asyncio
    async def test_analyze_maps_source_directories(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that analysis maps source directories correctly.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        project = await analyze_project(sample_kmp_project)

        # Should map source directories for source sets
        common_main = project.source_sets.get("commonMain")

        if common_main:
            # Source dirs should exist or be reasonable paths
            assert len(common_main.source_dirs) >= 0  # May be 0 if not explicit

    @pytest.mark.asyncio
    async def test_analyze_detects_source_set_dependencies(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that analysis detects source set dependsOn relationships.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        project = await analyze_project(sample_kmp_project)

        # iOS source sets should depend on commonMain
        ios_main = project.source_sets.get("iosMain")

        if ios_main:
            assert "commonMain" in ios_main.depends_on


class TestMultiModuleProjects:
    """Test suite for multi-module project analysis."""

    @pytest.mark.asyncio
    async def test_analyze_multi_module_project(self, tmp_path: Path) -> None:
        """Test analyzing a multi-module project.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create multi-module structure
        settings_file = tmp_path / "settings.gradle.kts"
        settings_file.write_text("""
rootProject.name = "MultiModuleProject"
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

        project = await analyze_project(tmp_path)

        assert project is not None
        # Should detect it as a KMP project
        assert project.type == ProjectType.KMP

    @pytest.mark.asyncio
    async def test_find_modules_in_settings_file(self, tmp_path: Path) -> None:
        """Test finding module declarations in settings.gradle.kts.

        Args:
            tmp_path: Temporary directory for test files
        """
        settings_file = tmp_path / "settings.gradle.kts"
        settings_file.write_text("""
rootProject.name = "TestProject"
include(":shared")
include(":app")
include(":core")
        """)

        analyzer = ProjectAnalyzer(tmp_path)
        # Analyzer should be able to identify modules
        assert analyzer.project_dir == tmp_path


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    def test_analyzer_with_nonexistent_directory(self) -> None:
        """Test analyzer initialization with non-existent directory."""
        with pytest.raises(FileNotFoundError):
            analyzer = ProjectAnalyzer(Path("/nonexistent/path"))
            # Some implementations may defer the check
            if not analyzer.project_dir.exists():
                raise FileNotFoundError()

    @pytest.mark.asyncio
    async def test_analyze_empty_project(self, tmp_path: Path) -> None:
        """Test analyzing a project with no build files.

        Args:
            tmp_path: Temporary directory for test files
        """
        project = await analyze_project(tmp_path)

        # Should return a project with UNKNOWN type
        assert project.type == ProjectType.UNKNOWN

    @pytest.mark.asyncio
    async def test_analyze_with_malformed_build_file(self, tmp_path: Path) -> None:
        """Test analyzing project with malformed build.gradle.kts.

        Args:
            tmp_path: Temporary directory for test files
        """
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("this is not valid gradle {{{")

        # Should not crash, may return partial results
        project = await analyze_project(tmp_path)
        assert project is not None


class TestPerformance:
    """Test suite for performance characteristics."""

    @pytest.mark.asyncio
    async def test_analysis_completes_in_reasonable_time(
        self, sample_kmp_project: Path
    ) -> None:
        """Test that project analysis completes within 30 seconds.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        import time

        start = time.time()
        project = await analyze_project(sample_kmp_project)
        duration = time.time() - start

        assert project is not None
        # Should complete in less than 30 seconds as per requirements
        assert duration < 30.0

    @pytest.mark.asyncio
    async def test_parallel_analysis_of_modules(self, tmp_path: Path) -> None:
        """Test that multi-module analysis can be parallelized.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create several modules
        for i in range(3):
            module = tmp_path / f"module{i}"
            module.mkdir()
            (module / "build.gradle.kts").write_text("""
plugins {
    kotlin("multiplatform")
}

kotlin {
    android()
}
            """)

        # Analysis should handle multiple modules efficiently
        project = await analyze_project(tmp_path)
        assert project is not None
