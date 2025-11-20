"""Project analyzer for KMP/CMP project detection and analysis.

This module provides functionality to analyze Kotlin Multiplatform and Compose
Multiplatform projects, including recursive build file scanning, project type
detection, and extraction of project metadata.
"""

import asyncio
import re
from pathlib import Path

from ..models.project import Project, ProjectType
from ..utils.gradle_parser import parse_build_file
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ProjectAnalyzer:
    """Analyzer for KMP/CMP projects.

    Recursively scans project directories to find build files, detect project
    type, and extract project configuration.

    Attributes:
        project_dir: Root directory of the project

    Example:
        >>> analyzer = ProjectAnalyzer(Path("/path/to/project"))
        >>> project = await analyzer.analyze()
        >>> print(project.type)
    """

    def __init__(self, project_dir: Path):
        """Initialize project analyzer.

        Args:
            project_dir: Path to project root directory

        Raises:
            FileNotFoundError: If project directory doesn't exist
        """
        if not project_dir.exists():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")

        if not project_dir.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {project_dir}")

        self.project_dir = project_dir

    async def analyze(self) -> Project:
        """Analyze the project and extract configuration.

        Returns:
            Project instance with extracted configuration

        Example:
            >>> project = await analyzer.analyze()
            >>> assert project.type != ProjectType.UNKNOWN
        """
        logger.info(f"Analyzing project at: {self.project_dir}")

        # Find all build files
        build_files = await self._find_build_files()
        logger.debug(f"Found {len(build_files)} build files")

        if not build_files:
            logger.warning("No build.gradle.kts files found")
            return self._create_unknown_project()

        # Analyze the root build file
        root_build_file = self._find_root_build_file(build_files)

        if not root_build_file:
            logger.warning("No root build file found")
            return self._create_unknown_project()

        # Parse build configuration
        try:
            build_config = parse_build_file(root_build_file)
        except Exception as e:
            logger.error(f"Failed to parse build file: {e}")
            return self._create_unknown_project()

        # Detect project type
        project_type = self._detect_project_type(build_config["plugins"])

        # Extract project name from settings.gradle.kts or directory name
        project_name = await self._extract_project_name()

        # Extract version information
        versions = self._extract_versions(build_config["plugins"])

        # Build source sets dict
        source_sets_dict = {ss.name: ss for ss in build_config["source_sets"]}

        # Create project instance
        project = Project(
            name=project_name,
            root_path=self.project_dir,
            type=project_type,
            source_sets=source_sets_dict,
            targets=build_config["targets"],
            kotlin_version=versions.get("kotlin"),
            compose_version=versions.get("compose"),
            build_files=[root_build_file]
        )

        logger.info(
            f"Analysis complete: {project.name} ({project.type.value}), "
            f"{len(project.source_sets)} source sets, {len(project.targets)} targets"
        )

        return project

    async def _find_build_files(self) -> list[Path]:
        """Find all build.gradle.kts files in the project.

        Returns:
            List of paths to build.gradle.kts files

        Example:
            >>> files = await analyzer._find_build_files()
            >>> assert all(f.name == "build.gradle.kts" for f in files)
        """
        build_files = []

        # Use asyncio to scan directory
        def scan_dir(directory: Path) -> list[Path]:
            found = []
            try:
                for item in directory.iterdir():
                    # Skip build output directories
                    if item.name in [".gradle", "build", ".idea", ".git"]:
                        continue

                    if item.is_file() and item.name == "build.gradle.kts":
                        found.append(item)
                    elif item.is_dir():
                        found.extend(scan_dir(item))
            except PermissionError:
                logger.debug(f"Permission denied: {directory}")

            return found

        build_files = await asyncio.to_thread(scan_dir, self.project_dir)
        return build_files

    def _find_root_build_file(self, build_files: list[Path]) -> Path | None:
        """Find the root build.gradle.kts file from a list of build files.

        Args:
            build_files: List of build file paths

        Returns:
            Path to root build file, or None if not found

        Example:
            >>> root = analyzer._find_root_build_file(build_files)
            >>> assert root.parent == analyzer.project_dir
        """
        # Root build file is the one directly in project directory
        for build_file in build_files:
            if build_file.parent == self.project_dir:
                return build_file

        # If no direct child, return the first one
        return build_files[0] if build_files else None

    def _detect_project_type(self, plugins: list[str]) -> ProjectType:
        """Detect project type from plugin list.

        Args:
            plugins: List of plugin identifiers

        Returns:
            Detected ProjectType

        Example:
            >>> ptype = analyzer._detect_project_type(["kotlin-multiplatform"])
            >>> assert ptype == ProjectType.KMP
        """
        plugins_str = " ".join(plugins).lower()

        # Check for Compose Multiplatform
        if "compose" in plugins_str or "org.jetbrains.compose" in plugins_str:
            logger.debug("Detected Compose Multiplatform project")
            return ProjectType.CMP

        # Check for Kotlin Multiplatform
        if "multiplatform" in plugins_str or "kotlin-multiplatform" in plugins_str:
            logger.debug("Detected Kotlin Multiplatform project")
            return ProjectType.KMP

        logger.debug("Unknown project type")
        return ProjectType.UNKNOWN

    async def _extract_project_name(self) -> str:
        """Extract project name from settings.gradle.kts or use directory name.

        Returns:
            Project name

        Example:
            >>> name = await analyzer._extract_project_name()
            >>> assert len(name) > 0
        """
        settings_file = self.project_dir / "settings.gradle.kts"

        if settings_file.exists():
            try:
                content = await asyncio.to_thread(settings_file.read_text)
                # Look for rootProject.name = "..."
                match = re.search(r'rootProject\.name\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except Exception as e:
                logger.debug(f"Failed to read settings file: {e}")

        # Fall back to directory name
        return self.project_dir.name

    def _extract_versions(self, plugins: list[str]) -> dict[str, str]:
        """Extract version information from plugins.

        Args:
            plugins: List of plugin identifiers

        Returns:
            Dictionary of component to version mappings

        Example:
            >>> versions = analyzer._extract_versions(plugins)
            >>> assert "kotlin" in versions
        """
        versions = {}

        for plugin in plugins:
            # Extract Kotlin version
            if "kotlin" in plugin:
                # Try to extract version from plugin string if present
                version_match = re.search(r'version\s*["\']([^"\']+)["\']', plugin)
                if version_match:
                    versions["kotlin"] = version_match.group(1)

            # Extract Compose version
            if "compose" in plugin.lower():
                version_match = re.search(r'version\s*["\']([^"\']+)["\']', plugin)
                if version_match:
                    versions["compose"] = version_match.group(1)

        return versions

    def _create_unknown_project(self) -> Project:
        """Create a Project instance for an unknown/invalid project.

        Returns:
            Project with UNKNOWN type

        Example:
            >>> project = analyzer._create_unknown_project()
            >>> assert project.type == ProjectType.UNKNOWN
        """
        return Project(
            name=self.project_dir.name,
            root_path=self.project_dir,
            type=ProjectType.UNKNOWN
        )


async def analyze_project(project_dir: Path) -> Project:
    """Analyze a project directory.

    Convenience function for analyzing a project without creating an analyzer instance.

    Args:
        project_dir: Path to project root directory

    Returns:
        Analyzed Project instance

    Raises:
        FileNotFoundError: If project directory doesn't exist

    Example:
        >>> project = await analyze_project(Path("/path/to/project"))
        >>> print(f"{project.name}: {project.type.value}")
    """
    analyzer = ProjectAnalyzer(project_dir)
    return await analyzer.analyze()


def detect_project_type(project_dir: Path) -> ProjectType:
    """Detect project type from directory.

    Synchronous function to quickly detect project type without full analysis.

    Args:
        project_dir: Path to project root directory

    Returns:
        Detected ProjectType

    Example:
        >>> ptype = detect_project_type(Path("/path/to/project"))
        >>> if ptype == ProjectType.KMP:
        ...     print("Kotlin Multiplatform project")
    """
    build_file = project_dir / "build.gradle.kts"

    if not build_file.exists():
        return ProjectType.UNKNOWN

    try:
        content = build_file.read_text()

        # Check for Compose
        if re.search(r'org\.jetbrains\.compose', content) or \
           re.search(r'id\s*\(\s*["\']compose["\']', content):
            return ProjectType.CMP

        # Check for Kotlin Multiplatform
        if re.search(r'kotlin\s*\(\s*["\']multiplatform["\']', content):
            return ProjectType.KMP

    except Exception as e:
        logger.debug(f"Error reading build file: {e}")

    return ProjectType.UNKNOWN


def find_build_files(project_dir: Path) -> list[Path]:
    """Find all build.gradle.kts files in a project directory.

    Synchronous function to locate build files.

    Args:
        project_dir: Path to project root directory

    Returns:
        List of build file paths

    Example:
        >>> files = find_build_files(Path("/path/to/project"))
        >>> print(f"Found {len(files)} build files")
    """
    build_files = []

    def scan_dir(directory: Path) -> None:
        try:
            for item in directory.iterdir():
                # Skip build output directories
                if item.name in [".gradle", "build", ".idea", ".git", ".venv", "node_modules"]:
                    continue

                if item.is_file() and item.name == "build.gradle.kts":
                    build_files.append(item)
                elif item.is_dir():
                    scan_dir(item)
        except PermissionError:
            logger.debug(f"Permission denied: {directory}")

    scan_dir(project_dir)
    return build_files


def is_kmp_project(project_dir: Path) -> bool:
    """Check if directory contains a Kotlin Multiplatform project.

    Args:
        project_dir: Path to project root directory

    Returns:
        True if KMP project detected

    Example:
        >>> if is_kmp_project(Path("/path/to/project")):
        ...     print("This is a KMP project")
    """
    ptype = detect_project_type(project_dir)
    return ptype in (ProjectType.KMP, ProjectType.CMP)


def is_cmp_project(project_dir: Path) -> bool:
    """Check if directory contains a Compose Multiplatform project.

    Args:
        project_dir: Path to project root directory

    Returns:
        True if CMP project detected

    Example:
        >>> if is_cmp_project(Path("/path/to/project")):
        ...     print("This is a CMP project")
    """
    ptype = detect_project_type(project_dir)
    return ptype == ProjectType.CMP
