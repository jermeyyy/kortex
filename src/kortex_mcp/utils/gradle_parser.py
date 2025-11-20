"""Gradle build file parser for KMP/CMP projects.

This module provides regex-based parsing of build.gradle.kts files to extract
project configuration including plugins, source sets, dependencies, and targets.
"""

import re
from pathlib import Path
from typing import Any

from ..models.project import SourceSet, SourceSetType, Target
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GradleParser:
    """Parser for Gradle build.gradle.kts files.

    Uses regex patterns to extract project configuration from Kotlin DSL
    build files without requiring Gradle execution.

    Attributes:
        build_file: Path to the build.gradle.kts file

    Example:
        >>> parser = GradleParser(Path("build.gradle.kts"))
        >>> result = parser.parse()
        >>> print(result["plugins"])
    """

    def __init__(self, build_file: Path):
        """Initialize Gradle parser.

        Args:
            build_file: Path to build.gradle.kts file

        Raises:
            FileNotFoundError: If build file doesn't exist
        """
        if not build_file.exists():
            raise FileNotFoundError(f"Build file not found: {build_file}")

        self.build_file = build_file
        self._content: str | None = None

    def _read_content(self) -> str:
        """Read and cache build file content.

        Returns:
            Build file content as string
        """
        if self._content is None:
            self._content = self.build_file.read_text()
        return self._content

    def _remove_comments(self, content: str) -> str:
        """Remove comments from Gradle file.

        Args:
            content: Original content

        Returns:
            Content with comments removed
        """
        # Remove single-line comments
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content

    def parse(self) -> dict[str, Any]:
        """Parse build file and extract all configuration.

        Returns:
            Dictionary with plugins, source_sets, targets, dependencies

        Example:
            >>> parser = GradleParser(Path("build.gradle.kts"))
            >>> result = parser.parse()
            >>> print(result.keys())
            dict_keys(['plugins', 'source_sets', 'targets', 'dependencies'])
        """
        content = self._read_content()
        content = self._remove_comments(content)

        return {
            "plugins": self._extract_plugins(content),
            "source_sets": self._extract_source_sets(content),
            "targets": self._extract_targets(content),
            "dependencies": self._extract_all_dependencies(content),
        }

    def _extract_plugins(self, content: str) -> list[str]:
        """Extract plugin declarations.

        Args:
            content: Build file content

        Returns:
            List of plugin identifiers
        """
        plugins: list[str] = []

        # Find plugins block
        plugins_block_match = re.search(
            r'plugins\s*\{(.*?)\}',
            content,
            re.DOTALL
        )

        if not plugins_block_match:
            return plugins

        plugins_block = plugins_block_match.group(1)

        # Extract kotlin("multiplatform")
        if re.search(r'kotlin\s*\(\s*["\']multiplatform["\']\s*\)', plugins_block):
            plugins.append("kotlin-multiplatform")

        # Extract id("org.jetbrains.compose")
        if re.search(r'id\s*\(\s*["\']org\.jetbrains\.compose["\']\s*\)', plugins_block):
            plugins.append("org.jetbrains.compose")

        # Extract other id() plugins
        for match in re.finditer(r'id\s*\(\s*["\']([^"\']+)["\']\s*\)', plugins_block):
            plugin_id = match.group(1)
            if plugin_id not in plugins:
                plugins.append(plugin_id)

        return plugins

    def _extract_source_sets(self, content: str) -> list[SourceSet]:
        """Extract source set configurations.

        Args:
            content: Build file content

        Returns:
            List of SourceSet objects
        """
        source_sets: list[SourceSet] = []

        # Find sourceSets block within kotlin block using balanced braces
        source_sets_match = re.search(
            r'sourceSets\s*\{',
            content
        )

        if not source_sets_match:
            return source_sets

        # Extract the sourceSets block with balanced braces
        start_pos = source_sets_match.end()
        brace_count = 1
        end_pos = start_pos

        while end_pos < len(content) and brace_count > 0:
            if content[end_pos] == '{':
                brace_count += 1
            elif content[end_pos] == '}':
                brace_count -= 1
            end_pos += 1

        source_sets_block = content[start_pos:end_pos-1]

        # Extract individual source sets with balanced braces
        # Pattern: val <name> by getting/creating {
        pattern = r'val\s+(\w+)\s+by\s+(getting|creating)\s*\{'

        for match in re.finditer(pattern, source_sets_block):
            name = match.group(1)
            block_start = match.end()

            # Find the matching closing brace for this source set
            brace_count = 1
            pos = block_start
            while pos < len(source_sets_block) and brace_count > 0:
                if source_sets_block[pos] == '{':
                    brace_count += 1
                elif source_sets_block[pos] == '}':
                    brace_count -= 1
                pos += 1

            source_set_content = source_sets_block[block_start:pos-1]

            # Extract dependencies
            dependencies = self._extract_source_set_dependencies(source_set_content)

            # Extract dependsOn
            depends_on = self._extract_depends_on(source_set_content)

            source_set = SourceSet(
                name=name,
                type=SourceSetType.UNKNOWN,  # Will be inferred by __post_init__
                dependencies=dependencies,
                depends_on=depends_on
            )

            source_sets.append(source_set)

        return source_sets

    def _extract_source_set_dependencies(self, content: str) -> list[str]:
        """Extract dependencies from a source set block.

        Args:
            content: Source set block content

        Returns:
            List of dependency strings
        """
        dependencies: list[str] = []

        # Find dependencies block
        deps_match = re.search(
            r'dependencies\s*\{(.*?)\}',
            content,
            re.DOTALL
        )

        if not deps_match:
            return dependencies

        deps_block = deps_match.group(1)

        # Extract implementation/api dependencies
        for match in re.finditer(
            r'(implementation|api|compileOnly|runtimeOnly)\s*\(\s*["\']([^"\']+)["\']\s*\)',
            deps_block
        ):
            dep = match.group(2)
            dependencies.append(dep)

        # Extract kotlin("test") style
        for match in re.finditer(
            r'(implementation|api)\s*\(\s*kotlin\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\)',
            deps_block
        ):
            dep = f"kotlin-{match.group(2)}"
            dependencies.append(dep)

        # Extract compose dependencies
        for match in re.finditer(
            r'(implementation|api)\s*\(\s*compose\.(\w+(?:\.\w+)*)\s*\)',
            deps_block
        ):
            dep = f"compose.{match.group(2)}"
            dependencies.append(dep)

        return dependencies

    def _extract_depends_on(self, content: str) -> list[str]:
        """Extract dependsOn relationships from source set block.

        Args:
            content: Source set block content

        Returns:
            List of source set names this depends on
        """
        depends_on = []

        # Pattern: dependsOn(commonMain)
        for match in re.finditer(r'dependsOn\s*\(\s*(\w+)\s*\)', content):
            depends_on.append(match.group(1))

        return depends_on

    def _extract_targets(self, content: str) -> list[Target]:
        """Extract build targets.

        Args:
            content: Build file content

        Returns:
            List of Target objects
        """
        targets: list[Target] = []

        # Find kotlin block
        kotlin_block_match = re.search(
            r'kotlin\s*\{(.*?)\n\}',
            content,
            re.DOTALL
        )

        if not kotlin_block_match:
            return targets

        kotlin_block = kotlin_block_match.group(1)

        # Extract android target
        if re.search(r'\bandroid\s*\(\s*\)', kotlin_block) or \
           re.search(r'\bandroidTarget\s*\(\s*\)', kotlin_block):
            targets.append(Target(
                name="android",
                platform="android",
                source_sets=["commonMain", "androidMain"]
            ))

        # Extract iOS targets
        for match in re.finditer(r'\b(ios(?:X64|Arm64|SimulatorArm64)?)\s*\(\s*\)', kotlin_block):
            target_name = match.group(1)
            targets.append(Target(
                name=target_name,
                platform="ios",
                source_sets=["commonMain", "iosMain"]
            ))

        # Extract JVM/desktop targets
        for match in re.finditer(r'\b(jvm|desktop)\s*\(\s*(?:["\'](\w+)["\']\s*)?\)', kotlin_block):
            target_name = match.group(2) if match.group(2) else match.group(1)
            targets.append(Target(
                name=target_name,
                platform="jvm",
                source_sets=["commonMain", "jvmMain"]
            ))

        # Extract JS targets
        if re.search(r'\bjs\s*\(', kotlin_block):
            targets.append(Target(
                name="js",
                platform="js",
                source_sets=["commonMain", "jsMain"]
            ))

        return targets

    def _extract_all_dependencies(self, content: str) -> list[str]:
        """Extract all dependencies from the build file.

        Args:
            content: Build file content

        Returns:
            List of all dependency strings
        """
        dependencies = []

        # Extract from all dependencies blocks
        for match in re.finditer(
            r'dependencies\s*\{(.*?)\}',
            content,
            re.DOTALL
        ):
            deps_block = match.group(1)

            # Extract standard dependencies
            for dep_match in re.finditer(
                r'(implementation|api|compileOnly|runtimeOnly|testImplementation)\s*\(\s*["\']([^"\']+)["\']\s*\)',
                deps_block
            ):
                dep = dep_match.group(2)
                if dep not in dependencies:
                    dependencies.append(dep)

            # Extract kotlin() style
            for dep_match in re.finditer(
                r'(implementation|api|testImplementation)\s*\(\s*kotlin\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\)',
                deps_block
            ):
                dep = f"kotlin-{dep_match.group(2)}"
                if dep not in dependencies:
                    dependencies.append(dep)

        return dependencies


def parse_build_file(build_file: Path) -> dict[str, Any]:
    """Parse a build.gradle.kts file.

    Convenience function that creates a parser and parses the file.

    Args:
        build_file: Path to build.gradle.kts file

    Returns:
        Dictionary with parsed configuration

    Raises:
        FileNotFoundError: If build file doesn't exist

    Example:
        >>> result = parse_build_file(Path("build.gradle.kts"))
        >>> print(result["plugins"])
        ['kotlin-multiplatform']
    """
    parser = GradleParser(build_file)
    return parser.parse()


def extract_plugins(build_file: Path) -> list[str]:
    """Extract plugin list from build file.

    Args:
        build_file: Path to build.gradle.kts file

    Returns:
        List of plugin identifiers

    Example:
        >>> plugins = extract_plugins(Path("build.gradle.kts"))
        >>> "kotlin-multiplatform" in plugins
        True
    """
    parser = GradleParser(build_file)
    content = parser._read_content()
    content = parser._remove_comments(content)
    return parser._extract_plugins(content)


def extract_source_sets(build_file: Path) -> list[SourceSet]:
    """Extract source sets from build file.

    Args:
        build_file: Path to build.gradle.kts file

    Returns:
        List of SourceSet objects

    Example:
        >>> source_sets = extract_source_sets(Path("build.gradle.kts"))
        >>> common = next(ss for ss in source_sets if ss.name == "commonMain")
        >>> print(common.type)
        SourceSetType.COMMON
    """
    parser = GradleParser(build_file)
    content = parser._read_content()
    content = parser._remove_comments(content)
    return parser._extract_source_sets(content)


def extract_dependencies(build_file: Path, include_test: bool = False) -> list[str]:
    """Extract dependencies from build file.

    Args:
        build_file: Path to build.gradle.kts file
        include_test: Whether to include test dependencies

    Returns:
        List of dependency strings

    Example:
        >>> deps = extract_dependencies(Path("build.gradle.kts"))
        >>> any("coroutines" in d for d in deps)
        True
    """
    parser = GradleParser(build_file)
    content = parser._read_content()
    content = parser._remove_comments(content)
    dependencies = parser._extract_all_dependencies(content)

    if not include_test:
        # Filter out test dependencies
        dependencies = [d for d in dependencies if "test" not in d.lower()]

    return dependencies


def extract_targets(build_file: Path) -> list[Target]:
    """Extract build targets from build file.

    Args:
        build_file: Path to build.gradle.kts file

    Returns:
        List of Target objects

    Example:
        >>> targets = extract_targets(Path("build.gradle.kts"))
        >>> android = next(t for t in targets if t.name == "android")
        >>> print(android.platform)
        'android'
    """
    parser = GradleParser(build_file)
    content = parser._read_content()
    content = parser._remove_comments(content)
    return parser._extract_targets(content)
