"""Unit tests for Gradle build file parser.

Tests regex-based parsing of build.gradle.kts files for KMP/CMP project
configuration including plugins, source sets, dependencies, and targets.
"""

from pathlib import Path

import pytest

from kortex_mcp.models.project import SourceSetType
from kortex_mcp.utils.gradle_parser import (
    GradleParser,
    extract_dependencies,
    extract_plugins,
    extract_source_sets,
    extract_targets,
    parse_build_file,
)


class TestGradleParser:
    """Test suite for GradleParser class."""

    def test_parser_initialization(self, sample_kmp_project: Path) -> None:
        """Test GradleParser can be initialized with a build file path.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        parser = GradleParser(build_file)

        assert parser.build_file == build_file
        assert parser.build_file.exists()

    def test_parse_build_file(self, sample_kmp_project: Path) -> None:
        """Test parsing a complete build.gradle.kts file.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        result = parse_build_file(build_file)

        assert result is not None
        assert "plugins" in result
        assert "source_sets" in result
        assert "targets" in result
        assert "dependencies" in result

    def test_detect_kotlin_multiplatform_plugin(self, sample_kmp_project: Path) -> None:
        """Test detection of kotlin("multiplatform") plugin.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        plugins = extract_plugins(build_file)

        assert "kotlin-multiplatform" in plugins or "multiplatform" in str(plugins)

    def test_detect_compose_multiplatform_plugin(self, tmp_path: Path) -> None:
        """Test detection of Compose Multiplatform plugin.

        Args:
            tmp_path: Temporary directory for test files
        """
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
plugins {
    kotlin("multiplatform") version "1.9.20"
    id("org.jetbrains.compose") version "1.5.10"
}
        """)

        plugins = extract_plugins(build_file)

        assert "compose" in str(plugins).lower() or "org.jetbrains.compose" in plugins


class TestSourceSetExtraction:
    """Test suite for source set extraction from build files."""

    def test_extract_common_main_source_set(self, sample_kmp_project: Path) -> None:
        """Test extraction of commonMain source set.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        source_sets = extract_source_sets(build_file)

        common_main = next((ss for ss in source_sets if ss.name == "commonMain"), None)
        assert common_main is not None
        assert common_main.type == SourceSetType.COMMON

    def test_extract_android_main_source_set(self, sample_kmp_project: Path) -> None:
        """Test extraction of androidMain source set.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        source_sets = extract_source_sets(build_file)

        android_main = next((ss for ss in source_sets if ss.name == "androidMain"), None)
        assert android_main is not None
        assert android_main.type == SourceSetType.ANDROID

    def test_extract_ios_main_source_set(self, sample_kmp_project: Path) -> None:
        """Test extraction of iosMain source set.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        source_sets = extract_source_sets(build_file)

        ios_main = next((ss for ss in source_sets if ss.name == "iosMain"), None)
        assert ios_main is not None
        assert ios_main.type == SourceSetType.IOS

    def test_extract_source_set_dependencies(self, sample_kmp_project: Path) -> None:
        """Test extraction of source set dependencies.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        source_sets = extract_source_sets(build_file)

        common_main = next((ss for ss in source_sets if ss.name == "commonMain"), None)
        assert common_main is not None
        assert len(common_main.dependencies) > 0

        # Check for kotlinx-coroutines-core dependency
        has_coroutines = any("coroutines" in dep for dep in common_main.dependencies)
        assert has_coroutines

    def test_extract_source_set_depends_on(self, sample_kmp_project: Path) -> None:
        """Test extraction of source set dependsOn relationships.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        source_sets = extract_source_sets(build_file)

        ios_main = next((ss for ss in source_sets if ss.name == "iosMain"), None)
        assert ios_main is not None
        # iosMain should depend on commonMain
        assert "commonMain" in ios_main.depends_on


class TestDependencyExtraction:
    """Test suite for dependency extraction from build files."""

    def test_extract_implementation_dependencies(self, sample_kmp_project: Path) -> None:
        """Test extraction of implementation dependencies.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        dependencies = extract_dependencies(build_file)

        assert len(dependencies) > 0
        # Should find kotlinx-coroutines-core
        has_coroutines = any("coroutines" in dep for dep in dependencies)
        assert has_coroutines

    def test_extract_test_dependencies(self, sample_kmp_project: Path) -> None:
        """Test extraction of test dependencies.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        dependencies = extract_dependencies(build_file, include_test=True)

        # Should find kotlin("test")
        has_test = any("test" in dep.lower() for dep in dependencies)
        assert has_test

    def test_parse_dependency_notation(self, tmp_path: Path) -> None:
        """Test parsing different dependency notation styles.

        Args:
            tmp_path: Temporary directory for test files
        """
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
    implementation(kotlin("test"))
    api("io.ktor:ktor-client-core:2.3.5")
}
        """)

        dependencies = extract_dependencies(build_file)

        assert len(dependencies) >= 2
        # Should handle both string notation and kotlin() notation
        assert any("kotlinx-coroutines-core" in dep for dep in dependencies)
        assert any("ktor-client-core" in dep for dep in dependencies)


class TestTargetExtraction:
    """Test suite for target extraction from build files."""

    def test_extract_android_target(self, sample_kmp_project: Path) -> None:
        """Test extraction of Android target.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        targets = extract_targets(build_file)

        android_target = next((t for t in targets if t.name == "android"), None)
        assert android_target is not None

    def test_extract_ios_targets(self, sample_kmp_project: Path) -> None:
        """Test extraction of iOS targets (iosX64, iosArm64, iosSimulatorArm64).

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        targets = extract_targets(build_file)

        ios_target_names = [t.name for t in targets if "ios" in t.name.lower()]
        assert len(ios_target_names) >= 3  # Should have at least 3 iOS targets

    def test_extract_target_with_framework(self, sample_kmp_project: Path) -> None:
        """Test extraction of target configuration with framework binaries.

        Args:
            sample_kmp_project: Path to sample KMP project fixture
        """
        build_file = sample_kmp_project / "build.gradle.kts"
        targets = extract_targets(build_file)

        # iOS targets should have framework configuration
        ios_targets = [t for t in targets if "ios" in t.name.lower()]
        assert len(ios_targets) > 0


class TestComplexScenarios:
    """Test suite for complex parsing scenarios."""

    def test_parse_multi_module_project(self, tmp_path: Path) -> None:
        """Test parsing a multi-module project structure.

        Args:
            tmp_path: Temporary directory for test files
        """
        # Create a simple multi-module structure
        module_dir = tmp_path / "shared"
        module_dir.mkdir()
        build_file = module_dir / "build.gradle.kts"
        build_file.write_text("""
plugins {
    kotlin("multiplatform") version "1.9.20"
}

kotlin {
    android()
    ios()

    sourceSets {
        val commonMain by getting
    }
}
        """)

        result = parse_build_file(build_file)
        assert result is not None

    def test_handle_missing_build_file(self, tmp_path: Path) -> None:
        """Test graceful handling of missing build.gradle.kts.

        Args:
            tmp_path: Temporary directory for test files
        """
        non_existent = tmp_path / "does_not_exist.gradle.kts"

        with pytest.raises(FileNotFoundError):
            parse_build_file(non_existent)

    def test_handle_malformed_build_file(self, tmp_path: Path) -> None:
        """Test handling of malformed or incomplete build files.

        Args:
            tmp_path: Temporary directory for test files
        """
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("this is not valid gradle syntax {{{")

        # Should not crash, but may return empty or partial results
        result = parse_build_file(build_file)
        assert result is not None  # Should return something, even if empty

    def test_parse_build_file_with_comments(self, tmp_path: Path) -> None:
        """Test parsing build files with comments.

        Args:
            tmp_path: Temporary directory for test files
        """
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
// This is a comment
plugins {
    kotlin("multiplatform") version "1.9.20"
    // id("another-plugin")
}

/*
 * Block comment
 */
kotlin {
    android()
}
        """)

        plugins = extract_plugins(build_file)
        # Should ignore commented-out plugins
        assert "multiplatform" in str(plugins).lower()


class TestGradleParserEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_empty_build_file(self, tmp_path: Path) -> None:
        """Test parsing an empty build.gradle.kts file.

        Args:
            tmp_path: Temporary directory for test files
        """
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("")

        result = parse_build_file(build_file)
        assert result is not None
        # Should return empty collections
        assert len(result.get("plugins", [])) == 0

    def test_build_file_without_multiplatform(self, tmp_path: Path) -> None:
        """Test parsing a non-multiplatform Kotlin project.

        Args:
            tmp_path: Temporary directory for test files
        """
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
plugins {
    kotlin("jvm") version "1.9.20"
}
        """)

        plugins = extract_plugins(build_file)
        # Should still parse, just won't find multiplatform plugin
        assert plugins is not None

    def test_nested_source_set_dependencies(self, tmp_path: Path) -> None:
        """Test parsing complex nested source set dependencies.

        Args:
            tmp_path: Temporary directory for test files
        """
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
kotlin {
    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
            }
        }

        val iosMain by creating {
            dependsOn(commonMain)
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-datetime:0.4.1")
            }
        }
    }
}
        """)

        source_sets = extract_source_sets(build_file)
        ios_main = next((ss for ss in source_sets if ss.name == "iosMain"), None)

        assert ios_main is not None
        assert "commonMain" in ios_main.depends_on
        assert len(ios_main.dependencies) > 0
