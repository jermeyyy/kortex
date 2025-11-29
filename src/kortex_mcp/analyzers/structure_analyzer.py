"""Structure analyzer for extracting project structure information.

This module provides the StructureAnalyzer class that extracts comprehensive
project structure information from KMP/CMP projects, including modules,
source sets, build targets, and version information.
"""

import asyncio
import re
from pathlib import Path
from typing import Any

from .base import AnalysisResult, BaseAnalyzer
from ..models.project import ProjectType, SourceSetType
from ..utils.gradle_parser import parse_build_file
from ..utils.logging import get_logger

logger = get_logger(__name__)


class StructureAnalyzer(BaseAnalyzer):
    """Analyzer for extracting comprehensive project structure information.

    Analyzes KMP/CMP projects to extract:
    - Project name and type
    - Module hierarchy
    - Source sets with types and paths
    - Build targets and platforms
    - Build file locations
    - Version information (Kotlin, Compose, Gradle wrapper)
    - Version catalog contents

    This analyzer produces structured data suitable for memory generation
    and project onboarding documentation.

    Attributes:
        project_root: Path to the root directory of the project being analyzed.

    Example:
        >>> analyzer = StructureAnalyzer(Path("/path/to/kmp-project"))
        >>> result = await analyzer.analyze()
        >>> print(result.data["project_name"])
        'my-kmp-project'
    """

    @property
    def name(self) -> str:
        """Get the name of this analyzer.

        Returns:
            The string "structure" identifying this analyzer.
        """
        return "structure"

    def get_memory_category(self) -> str:
        """Get the memory category for storing analysis results.

        Returns:
            The string "project_structure" for categorizing results.
        """
        return "project_structure"

    async def analyze(self) -> AnalysisResult:
        """Analyze the project structure and extract configuration.

        Performs comprehensive analysis of the project including:
        - Finding and parsing all build files
        - Detecting project type (KMP/CMP)
        - Extracting module hierarchy
        - Parsing source sets and their configurations
        - Identifying build targets and platforms
        - Extracting version information from various sources

        Returns:
            AnalysisResult containing structured project data with the following keys:
                - project_name: Name of the project
                - project_type: Type of project (kmp/cmp/unknown)
                - modules: List of module definitions with hierarchy
                - source_sets: List of source set configurations
                - targets: List of build targets
                - build_files: List of build file paths
                - versions: Dictionary of version information
                - gradle_wrapper_version: Gradle wrapper version if available
                - version_catalog: Parsed version catalog if available

        Raises:
            No exceptions are raised; errors are captured in the result.

        Example:
            >>> result = await analyzer.analyze()
            >>> if result.success:
            ...     print(f"Found {len(result.data['modules'])} modules")
        """
        logger.info(f"Analyzing project structure at: {self.project_root}")

        errors: list[str] = []
        warnings: list[str] = []

        try:
            # Find all build files
            build_files = await self._find_build_files()
            logger.debug(f"Found {len(build_files)} build files")

            if not build_files:
                warnings.append("No build.gradle.kts files found")
                return self._create_result_with_warnings(
                    self._create_minimal_structure(),
                    warnings,
                )

            # Find and parse root build file
            root_build_file = self._find_root_build_file(build_files)

            if not root_build_file:
                warnings.append("No root build file found")
                return self._create_result_with_warnings(
                    self._create_minimal_structure(),
                    warnings,
                )

            # Parse build configuration
            try:
                build_config = parse_build_file(root_build_file)
            except Exception as e:
                logger.error(f"Failed to parse build file: {e}")
                errors.append(f"Failed to parse root build file: {e}")
                return self._create_error_result(errors, warnings)

            # Detect project type
            project_type = self._detect_project_type(build_config["plugins"])

            # Extract project name
            project_name = await self._extract_project_name()

            # Extract modules
            modules = await self._extract_modules(build_files)

            # Process source sets
            source_sets = self._process_source_sets(build_config["source_sets"])

            # Process targets
            targets = self._process_targets(build_config["targets"])

            # Extract version information
            versions = self._extract_versions(build_config["plugins"])

            # Extract gradle wrapper version
            gradle_wrapper_version = await self._extract_gradle_wrapper_version()
            if gradle_wrapper_version:
                versions["gradle_wrapper"] = gradle_wrapper_version

            # Parse version catalog
            version_catalog = await self._parse_version_catalog()

            # Merge version catalog versions into main versions dict
            if version_catalog and "versions" in version_catalog:
                catalog_versions = version_catalog["versions"]
                if "kotlin" in catalog_versions and "kotlin" not in versions:
                    versions["kotlin"] = catalog_versions["kotlin"]
                if "compose" in catalog_versions and "compose" not in versions:
                    versions["compose"] = catalog_versions.get(
                        "compose",
                        catalog_versions.get("compose-multiplatform"),
                    )

            # Build result data structure
            data: dict[str, Any] = {
                "project_name": project_name,
                "project_type": project_type.value,
                "modules": modules,
                "source_sets": source_sets,
                "targets": targets,
                "build_files": [str(bf) for bf in build_files],
                "versions": versions,
                "version_catalog": version_catalog,
            }

            logger.info(
                f"Structure analysis complete: {project_name} ({project_type.value}), "
                f"{len(modules)} modules, {len(source_sets)} source sets, "
                f"{len(targets)} targets"
            )

            if warnings:
                result = self._create_success_result(data)
                result.warnings = warnings
                return result

            return self._create_success_result(data)

        except Exception as e:
            logger.exception(f"Unexpected error during structure analysis: {e}")
            errors.append(f"Unexpected error: {e}")
            return self._create_error_result(errors, warnings)

    async def _find_build_files(self) -> list[Path]:
        """Find all build.gradle.kts files in the project.

        Recursively scans the project directory for Gradle build files,
        excluding common build output and hidden directories.

        Returns:
            List of paths to build.gradle.kts files found in the project.

        Example:
            >>> files = await analyzer._find_build_files()
            >>> assert all(f.name == "build.gradle.kts" for f in files)
        """
        excluded_dirs = {".gradle", "build", ".idea", ".git", "node_modules", ".kortex"}

        def scan_dir(directory: Path) -> list[Path]:
            """Recursively scan directory for build files."""
            found: list[Path] = []
            try:
                for item in directory.iterdir():
                    if item.name in excluded_dirs:
                        continue

                    if item.is_file() and item.name == "build.gradle.kts":
                        found.append(item)
                    elif item.is_dir():
                        found.extend(scan_dir(item))
            except PermissionError:
                logger.debug(f"Permission denied: {directory}")

            return found

        return await asyncio.to_thread(scan_dir, self.project_root)

    def _find_root_build_file(self, build_files: list[Path]) -> Path | None:
        """Find the root build.gradle.kts file from a list of build files.

        The root build file is the one located directly in the project root
        directory. If not found, returns the first build file as a fallback.

        Args:
            build_files: List of build file paths to search.

        Returns:
            Path to root build file, or None if the list is empty.

        Example:
            >>> root = analyzer._find_root_build_file(build_files)
            >>> if root:
            ...     assert root.parent == analyzer.project_root
        """
        for build_file in build_files:
            if build_file.parent == self.project_root:
                return build_file

        return build_files[0] if build_files else None

    def _detect_project_type(self, plugins: list[str]) -> ProjectType:
        """Detect project type from plugin list.

        Examines the list of Gradle plugins to determine whether the project
        is a Compose Multiplatform (CMP) or Kotlin Multiplatform (KMP) project.

        Args:
            plugins: List of plugin identifiers from the build file.

        Returns:
            ProjectType.CMP if Compose plugins found, ProjectType.KMP if
            multiplatform plugins found, otherwise ProjectType.UNKNOWN.

        Example:
            >>> ptype = analyzer._detect_project_type(["kotlin-multiplatform"])
            >>> assert ptype == ProjectType.KMP
        """
        plugins_str = " ".join(plugins).lower()

        # Check for Compose Multiplatform first (more specific)
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

        Attempts to read the project name from the settings.gradle.kts file.
        Falls back to using the directory name if the settings file is not
        available or doesn't contain a project name.

        Returns:
            Project name string.

        Example:
            >>> name = await analyzer._extract_project_name()
            >>> assert len(name) > 0
        """
        settings_file = self.project_root / "settings.gradle.kts"

        if settings_file.exists():
            try:
                content = await asyncio.to_thread(settings_file.read_text)
                match = re.search(
                    r'rootProject\.name\s*=\s*["\']([^"\']+)["\']',
                    content,
                )
                if match:
                    return match.group(1)
            except Exception as e:
                logger.debug(f"Failed to read settings file: {e}")

        return self.project_root.name

    async def _extract_modules(self, build_files: list[Path]) -> list[dict[str, Any]]:
        """Extract module information from build files.

        Analyzes build file locations to determine module hierarchy and
        extracts module-specific information from each build file.

        Args:
            build_files: List of paths to build.gradle.kts files.

        Returns:
            List of module dictionaries containing:
                - name: Module name
                - path: Relative path from project root
                - build_file: Path to the module's build file
                - is_root: Whether this is the root module
                - parent: Parent module path (if applicable)

        Example:
            >>> modules = await analyzer._extract_modules(build_files)
            >>> root_modules = [m for m in modules if m["is_root"]]
            >>> assert len(root_modules) == 1
        """
        modules: list[dict[str, Any]] = []

        for build_file in build_files:
            relative_path = build_file.parent.relative_to(self.project_root)
            is_root = relative_path == Path(".")

            module: dict[str, Any] = {
                "name": self.project_root.name if is_root else relative_path.name,
                "path": str(relative_path) if not is_root else ".",
                "build_file": str(build_file.relative_to(self.project_root)),
                "is_root": is_root,
            }

            # Determine parent module
            if not is_root and len(relative_path.parts) > 1:
                parent_path = relative_path.parent
                module["parent"] = str(parent_path)
            elif not is_root:
                module["parent"] = "."

            # Try to extract module-specific configuration
            try:
                module_config = parse_build_file(build_file)
                module["plugins"] = module_config.get("plugins", [])
                module["has_source_sets"] = len(module_config.get("source_sets", [])) > 0
                module["targets"] = [t.name for t in module_config.get("targets", [])]
            except Exception as e:
                logger.debug(f"Could not parse module build file {build_file}: {e}")
                module["plugins"] = []
                module["has_source_sets"] = False
                module["targets"] = []

            modules.append(module)

        return modules

    def _process_source_sets(
        self,
        source_sets: list[Any],
    ) -> list[dict[str, Any]]:
        """Process source sets into structured dictionaries.

        Converts SourceSet objects into dictionary format suitable for
        serialization and memory storage.

        Args:
            source_sets: List of SourceSet objects from the parser.

        Returns:
            List of dictionaries containing source set information:
                - name: Source set name
                - type: Source set type value
                - source_dirs: List of source directory paths
                - resource_dirs: List of resource directory paths
                - dependencies: List of dependency strings
                - depends_on: List of dependent source set names

        Example:
            >>> processed = analyzer._process_source_sets(source_sets)
            >>> common = next((s for s in processed if s["name"] == "commonMain"), None)
            >>> assert common is not None
        """
        result: list[dict[str, Any]] = []

        for source_set in source_sets:
            # Infer type from name if needed
            ss_type = source_set.type
            if ss_type == SourceSetType.UNKNOWN:
                ss_type = self._infer_source_set_type(source_set.name)

            # Build expected source directories based on name
            source_dirs = [str(d) for d in source_set.source_dirs]
            if not source_dirs:
                # Add default source directories
                source_dirs = [f"src/{source_set.name}/kotlin"]

            resource_dirs = [str(d) for d in source_set.resource_dirs]
            if not resource_dirs and "Main" in source_set.name:
                resource_dirs = [f"src/{source_set.name}/resources"]

            result.append({
                "name": source_set.name,
                "type": ss_type.value,
                "source_dirs": source_dirs,
                "resource_dirs": resource_dirs,
                "dependencies": source_set.dependencies,
                "depends_on": source_set.depends_on,
            })

        return result

    def _infer_source_set_type(self, name: str) -> SourceSetType:
        """Infer source set type from its name.

        Args:
            name: Source set name to analyze.

        Returns:
            Inferred SourceSetType based on name patterns.

        Example:
            >>> ss_type = analyzer._infer_source_set_type("androidMain")
            >>> assert ss_type == SourceSetType.ANDROID
        """
        name_lower = name.lower()

        if "common" in name_lower:
            return SourceSetType.COMMON
        elif "android" in name_lower:
            return SourceSetType.ANDROID
        elif "ios" in name_lower:
            return SourceSetType.IOS
        elif "desktop" in name_lower:
            return SourceSetType.DESKTOP
        elif "jvm" in name_lower:
            return SourceSetType.JVM
        elif "js" in name_lower:
            return SourceSetType.JS
        elif "web" in name_lower:
            return SourceSetType.WEB
        elif "native" in name_lower:
            return SourceSetType.NATIVE
        elif "wasm" in name_lower:
            return SourceSetType.WASM

        return SourceSetType.UNKNOWN

    def _process_targets(self, targets: list[Any]) -> list[dict[str, Any]]:
        """Process build targets into structured dictionaries.

        Converts Target objects into dictionary format suitable for
        serialization and memory storage.

        Args:
            targets: List of Target objects from the parser.

        Returns:
            List of dictionaries containing target information:
                - name: Target name
                - platform: Platform identifier
                - source_sets: List of associated source set names

        Example:
            >>> processed = analyzer._process_targets(targets)
            >>> android = next((t for t in processed if t["name"] == "android"), None)
            >>> assert android["platform"] == "android"
        """
        return [
            {
                "name": target.name,
                "platform": target.platform,
                "source_sets": target.source_sets,
            }
            for target in targets
        ]

    def _extract_versions(self, plugins: list[str]) -> dict[str, str]:
        """Extract version information from plugins.

        Searches for version declarations in plugin strings and extracts
        Kotlin and Compose versions.

        Args:
            plugins: List of plugin identifier strings.

        Returns:
            Dictionary mapping component names to version strings.
            May include "kotlin" and "compose" keys.

        Example:
            >>> versions = analyzer._extract_versions(plugins)
            >>> if "kotlin" in versions:
            ...     print(f"Kotlin version: {versions['kotlin']}")
        """
        versions: dict[str, str] = {}

        for plugin in plugins:
            plugin_lower = plugin.lower()

            # Extract Kotlin version
            if "kotlin" in plugin_lower:
                version_match = re.search(r'version\s*["\']([^"\']+)["\']', plugin)
                if version_match:
                    versions["kotlin"] = version_match.group(1)

            # Extract Compose version
            if "compose" in plugin_lower:
                version_match = re.search(r'version\s*["\']([^"\']+)["\']', plugin)
                if version_match:
                    versions["compose"] = version_match.group(1)

        return versions

    async def _extract_gradle_wrapper_version(self) -> str | None:
        """Extract Gradle wrapper version from gradle-wrapper.properties.

        Reads the gradle-wrapper.properties file and extracts the Gradle
        version from the distribution URL.

        Returns:
            Gradle version string, or None if not found.

        Example:
            >>> version = await analyzer._extract_gradle_wrapper_version()
            >>> if version:
            ...     print(f"Gradle wrapper: {version}")
        """
        properties_file = (
            self.project_root / "gradle" / "wrapper" / "gradle-wrapper.properties"
        )

        if not properties_file.exists():
            logger.debug("gradle-wrapper.properties not found")
            return None

        try:
            content = await asyncio.to_thread(properties_file.read_text)

            # Look for distributionUrl with version
            # Format: gradle-X.Y.Z-bin.zip or gradle-X.Y.Z-all.zip
            match = re.search(
                r'distributionUrl.*gradle-(\d+\.\d+(?:\.\d+)?)-(?:bin|all)\.zip',
                content,
            )
            if match:
                return match.group(1)

        except Exception as e:
            logger.debug(f"Failed to read gradle-wrapper.properties: {e}")

        return None

    async def _parse_version_catalog(self) -> dict[str, Any] | None:
        """Parse version catalog from libs.versions.toml.

        Reads and parses the Gradle version catalog file if it exists,
        extracting versions, libraries, and plugins sections.

        Returns:
            Dictionary containing parsed version catalog data with keys:
                - versions: Dictionary of version aliases to values
                - libraries: Dictionary of library aliases to definitions
                - plugins: Dictionary of plugin aliases to definitions
            Returns None if the file doesn't exist.

        Example:
            >>> catalog = await analyzer._parse_version_catalog()
            >>> if catalog:
            ...     print(f"Kotlin version: {catalog['versions'].get('kotlin')}")
        """
        catalog_file = self.project_root / "gradle" / "libs.versions.toml"

        if not catalog_file.exists():
            logger.debug("libs.versions.toml not found")
            return None

        try:
            content = await asyncio.to_thread(catalog_file.read_text)
            return self._parse_toml_catalog(content)
        except Exception as e:
            logger.warning(f"Failed to parse version catalog: {e}")
            return None

    def _parse_toml_catalog(self, content: str) -> dict[str, Any]:
        """Parse TOML version catalog content.

        Implements a simple TOML parser for version catalog files.
        Handles the [versions], [libraries], and [plugins] sections.

        Args:
            content: Raw TOML file content.

        Returns:
            Dictionary with versions, libraries, and plugins sections.

        Example:
            >>> content = '[versions]\\nkotlin = "1.9.0"'
            >>> result = analyzer._parse_toml_catalog(content)
            >>> assert result["versions"]["kotlin"] == "1.9.0"
        """
        result: dict[str, Any] = {
            "versions": {},
            "libraries": {},
            "plugins": {},
            "bundles": {},
        }

        current_section: str | None = None

        for line in content.splitlines():
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Check for section header
            section_match = re.match(r'\[(\w+)\]', line)
            if section_match:
                current_section = section_match.group(1)
                continue

            if current_section is None:
                continue

            # Parse key-value pairs
            kv_match = re.match(r'([a-zA-Z0-9_-]+)\s*=\s*(.+)', line)
            if kv_match and current_section in result:
                key = kv_match.group(1).replace("-", "_")
                value = self._parse_toml_value(kv_match.group(2))
                result[current_section][key] = value

        return result

    def _parse_toml_value(self, value: str) -> str | dict[str, str]:
        """Parse a TOML value (string or inline table).

        Args:
            value: Raw TOML value string.

        Returns:
            Parsed value as string or dictionary for inline tables.

        Example:
            >>> analyzer._parse_toml_value('"1.9.0"')
            '1.9.0'
            >>> analyzer._parse_toml_value('{ group = "org.example", name = "lib" }')
            {'group': 'org.example', 'name': 'lib'}
        """
        value = value.strip()

        # Simple string value
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]

        # Inline table
        if value.startswith("{") and value.endswith("}"):
            table_content = value[1:-1]
            table: dict[str, str] = {}

            # Parse inline table entries
            for entry in table_content.split(","):
                entry = entry.strip()
                if "=" in entry:
                    k, v = entry.split("=", 1)
                    k = k.strip().replace("-", "_")
                    v = v.strip()
                    if v.startswith('"') and v.endswith('"'):
                        v = v[1:-1]
                    elif v.startswith("'") and v.endswith("'"):
                        v = v[1:-1]
                    table[k] = v

            return table

        return value

    def _create_minimal_structure(self) -> dict[str, Any]:
        """Create a minimal structure result for unknown projects.

        Returns:
            Dictionary with minimal project structure information.

        Example:
            >>> data = analyzer._create_minimal_structure()
            >>> assert data["project_type"] == "unknown"
        """
        return {
            "project_name": self.project_root.name,
            "project_type": ProjectType.UNKNOWN.value,
            "modules": [],
            "source_sets": [],
            "targets": [],
            "build_files": [],
            "versions": {},
            "version_catalog": None,
        }

    def _create_result_with_warnings(
        self,
        data: dict[str, Any],
        warnings: list[str],
    ) -> AnalysisResult:
        """Create a successful result with warnings.

        Helper method to construct an AnalysisResult that succeeded
        but has warning messages attached.

        Args:
            data: Dictionary containing the analysis findings.
            warnings: List of warning messages.

        Returns:
            AnalysisResult with success=True, provided data, and warnings.

        Example:
            >>> result = analyzer._create_result_with_warnings(
            ...     {"project_name": "test"},
            ...     ["No iOS targets found"]
            ... )
            >>> assert result.success and len(result.warnings) == 1
        """
        return AnalysisResult(
            analyzer_name=self.name,
            success=True,
            data=data,
            errors=[],
            warnings=warnings,
        )
