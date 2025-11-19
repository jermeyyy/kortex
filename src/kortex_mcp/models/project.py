"""Project and source set data models.

This module defines the core data structures for representing KMP/CMP projects,
including source sets, targets, and dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ProjectType(Enum):
    """Type of multiplatform project."""
    KMP = "kmp"  # Kotlin Multiplatform
    CMP = "cmp"  # Compose Multiplatform
    UNKNOWN = "unknown"


class SourceSetType(Enum):
    """Type of source set in a KMP project."""
    COMMON = "common"
    ANDROID = "android"
    IOS = "ios"
    DESKTOP = "desktop"
    WEB = "web"
    NATIVE = "native"
    JVM = "jvm"
    JS = "js"
    WASM = "wasm"
    UNKNOWN = "unknown"


@dataclass
class SourceSet:
    """Represents a source set in a KMP project.

    A source set is a collection of source files and resources that
    target a specific platform or set of platforms.

    Attributes:
        name: Name of the source set (e.g., "commonMain", "androidMain")
        type: Type classification of the source set
        source_dirs: List of source code directories
        resource_dirs: List of resource directories
        dependencies: List of dependency identifiers
        depends_on: Names of source sets this one depends on

    Example:
        >>> source_set = SourceSet(
        ...     name="commonMain",
        ...     type=SourceSetType.COMMON,
        ...     source_dirs=[Path("src/commonMain/kotlin")],
        ...     dependencies=["org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3"]
        ... )
    """
    name: str
    type: SourceSetType
    source_dirs: list[Path] = field(default_factory=list)
    resource_dirs: list[Path] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Infer source set type from name if UNKNOWN."""
        if self.type == SourceSetType.UNKNOWN:
            self.type = self._infer_type_from_name()

    def _infer_type_from_name(self) -> SourceSetType:
        """Infer source set type from its name.

        Returns:
            Inferred SourceSetType based on name patterns
        """
        name_lower = self.name.lower()

        if "common" in name_lower:
            return SourceSetType.COMMON
        elif "android" in name_lower:
            return SourceSetType.ANDROID
        elif "ios" in name_lower:
            return SourceSetType.IOS
        elif "desktop" in name_lower or "jvm" in name_lower:
            return SourceSetType.DESKTOP
        elif "web" in name_lower or "js" in name_lower:
            return SourceSetType.WEB
        elif "native" in name_lower:
            return SourceSetType.NATIVE
        elif "wasm" in name_lower:
            return SourceSetType.WASM

        return SourceSetType.UNKNOWN


@dataclass
class Target:
    """Represents a build target in a KMP project.

    Attributes:
        name: Name of the target (e.g., "android", "iosX64")
        platform: Platform this target builds for
        source_sets: Names of source sets included in this target

    Example:
        >>> target = Target(
        ...     name="android",
        ...     platform="android",
        ...     source_sets=["commonMain", "androidMain"]
        ... )
    """
    name: str
    platform: str
    source_sets: list[str] = field(default_factory=list)


@dataclass
class Project:
    """Represents a KMP/CMP project.

    This is the main data structure for project configuration,
    containing all information about source sets, targets, and dependencies.

    Attributes:
        name: Project name
        root_path: Absolute path to project root directory
        type: Type of project (KMP or CMP)
        source_sets: Dictionary of source set name to SourceSet
        targets: List of build targets
        gradle_version: Gradle version used by project
        kotlin_version: Kotlin version used by project
        compose_version: Compose Multiplatform version (if CMP project)
        build_files: Paths to build.gradle.kts files in project

    Example:
        >>> project = Project(
        ...     name="MyKMPApp",
        ...     root_path=Path("/path/to/project"),
        ...     type=ProjectType.CMP,
        ...     source_sets={"commonMain": common_source_set},
        ...     kotlin_version="1.9.20",
        ...     compose_version="1.5.10"
        ... )
    """
    name: str
    root_path: Path
    type: ProjectType = ProjectType.UNKNOWN
    source_sets: dict[str, SourceSet] = field(default_factory=dict)
    targets: list[Target] = field(default_factory=list)
    gradle_version: str | None = None
    kotlin_version: str | None = None
    compose_version: str | None = None
    build_files: list[Path] = field(default_factory=list)

    def get_source_set(self, name: str) -> SourceSet | None:
        """Get a source set by name.

        Args:
            name: Name of the source set

        Returns:
            SourceSet if found, None otherwise

        Example:
            >>> common = project.get_source_set("commonMain")
            >>> if common:
            ...     print(common.source_dirs)
        """
        return self.source_sets.get(name)

    def get_all_source_dirs(self) -> set[Path]:
        """Get all source directories across all source sets.

        Returns:
            Set of all source directory paths

        Example:
            >>> all_dirs = project.get_all_source_dirs()
            >>> for dir in all_dirs:
            ...     print(dir)
        """
        dirs: set[Path] = set()
        for source_set in self.source_sets.values():
            dirs.update(source_set.source_dirs)
        return dirs

    def get_common_source_sets(self) -> list[SourceSet]:
        """Get all common/shared source sets.

        Returns:
            List of source sets with COMMON type

        Example:
            >>> common_sets = project.get_common_source_sets()
            >>> for ss in common_sets:
            ...     print(ss.name)
        """
        return [
            ss for ss in self.source_sets.values()
            if ss.type == SourceSetType.COMMON
        ]

    def get_platform_source_sets(self, platform: SourceSetType) -> list[SourceSet]:
        """Get all source sets for a specific platform.

        Args:
            platform: Platform type to filter by

        Returns:
            List of source sets matching the platform

        Example:
            >>> android_sets = project.get_platform_source_sets(SourceSetType.ANDROID)
        """
        return [
            ss for ss in self.source_sets.values()
            if ss.type == platform
        ]

    def is_cmp_project(self) -> bool:
        """Check if this is a Compose Multiplatform project.

        Returns:
            True if project type is CMP

        Example:
            >>> if project.is_cmp_project():
            ...     print("This is a Compose Multiplatform project")
        """
        return self.type == ProjectType.CMP

    def has_target(self, target_name: str) -> bool:
        """Check if project has a specific target.

        Args:
            target_name: Name of target to check for

        Returns:
            True if target exists in project

        Example:
            >>> if project.has_target("ios"):
            ...     print("iOS target is configured")
        """
        return any(t.name == target_name for t in self.targets)
