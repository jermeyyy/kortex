"""Dependency analyzer for detecting project dependencies and module structure.

This module provides the DependencyAnalyzer class that detects module dependencies,
external dependencies, and version catalog configurations in KMP/CMP projects.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base import AnalysisResult, BaseAnalyzer
from ..utils.logging import get_logger

logger = get_logger(__name__)


# Dependency category mappings based on artifact group/name patterns
DEPENDENCY_CATEGORIES: dict[str, list[str]] = {
    "kotlin_standard": [
        "org.jetbrains.kotlin:",
        "org.jetbrains.kotlinx:",
    ],
    "android_jetpack": [
        "androidx.",
        "com.google.android.material:",
    ],
    "compose": [
        "org.jetbrains.compose",
        "androidx.compose",
    ],
    "networking": [
        "io.ktor",
        "com.squareup.retrofit2:",
        "com.squareup.okhttp3:",
    ],
    "database": [
        "app.cash.sqldelight",
        "androidx.room:",
        "io.realm:",
    ],
    "serialization": [
        "org.jetbrains.kotlinx:kotlinx-serialization",
        "com.squareup.moshi:",
        "com.google.code.gson:",
    ],
    "dependency_injection": [
        "io.insert-koin:",
        "org.koin:",
        "com.google.dagger:",
        "io.github.nicofilliol:kodein",
    ],
    "image_loading": [
        "io.coil-kt",
        "com.github.bumptech.glide:",
        "com.squareup.picasso:",
    ],
    "logging": [
        "com.jakewharton.timber:",
        "io.github.aakira:napier:",
        "co.touchlab:kermit:",
    ],
    "testing": [
        "junit:",
        "org.junit.",
        "io.kotest:",
        "io.mockk:",
        "app.cash.turbine:",
        "org.jetbrains.kotlin:kotlin-test",
    ],
    "navigation": [
        "cafe.adriel.voyager:",
        "com.arkivanov.decompose:",
        "androidx.navigation:",
    ],
    "datetime": [
        "org.jetbrains.kotlinx:kotlinx-datetime",
    ],
    "crypto": [
        "org.bouncycastle:",
        "com.soywiz.korlibs.krypto:",
    ],
    "storage": [
        "com.russhwolf:multiplatform-settings",
        "androidx.datastore:",
    ],
}


@dataclass
class ExternalDependency:
    """Represents an external dependency artifact.

    Attributes:
        group: Maven group ID (e.g., "org.jetbrains.kotlinx").
        name: Artifact name (e.g., "kotlinx-coroutines-core").
        version: Version string or None if from version catalog.
        configurations: List of source sets/configurations using this dependency.
        category: Categorized type of dependency.
        raw_declaration: Original declaration string from build file.
    """

    group: str
    name: str
    version: str | None = None
    configurations: list[str] = field(default_factory=list)
    category: str = "other"
    raw_declaration: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "group": self.group,
            "name": self.name,
            "version": self.version,
            "configurations": self.configurations,
            "category": self.category,
        }


class DependencyAnalyzer(BaseAnalyzer):
    """Analyzer for detecting dependencies and module structure in KMP/CMP projects.

    Analyzes Gradle build files to detect:
    - Module structure from settings.gradle.kts
    - Inter-module dependencies (project references)
    - External dependencies from build.gradle.kts files
    - Version catalog configuration from libs.versions.toml
    - Dependency categorization by type/purpose

    This analyzer produces structured data suitable for understanding
    project dependencies and generating dependency documentation.

    Attributes:
        project_root: Path to the root directory of the project being analyzed.

    Example:
        >>> analyzer = DependencyAnalyzer(Path("/path/to/kmp-project"))
        >>> result = await analyzer.analyze()
        >>> print(result.data["modules"])
        ['app', 'core', 'feature-home']
        >>> print(result.data["dependency_count"])
        45
    """

    # Regex patterns for parsing Gradle files
    INCLUDE_PATTERN = re.compile(
        r'include\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    PROJECT_DEP_PATTERN = re.compile(
        r'(?:implementation|api|compileOnly|runtimeOnly|testImplementation)\s*\(\s*'
        r'project\s*\(\s*["\']:([^"\']+)["\']\s*\)\s*\)',
        re.MULTILINE
    )

    # Standard dependency: implementation("group:artifact:version")
    STANDARD_DEP_PATTERN = re.compile(
        r'(?P<config>implementation|api|compileOnly|runtimeOnly|testImplementation|'
        r'androidTestImplementation|debugImplementation|releaseImplementation)\s*\(\s*'
        r'["\'](?P<coords>[^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    # Version catalog dependency: implementation(libs.some.lib)
    CATALOG_DEP_PATTERN = re.compile(
        r'(?P<config>implementation|api|compileOnly|runtimeOnly|testImplementation|'
        r'androidTestImplementation|debugImplementation|releaseImplementation)\s*\(\s*'
        r'(?P<catalog>libs\.[a-zA-Z0-9_.]+)\s*\)',
        re.MULTILINE
    )

    # Source set block detection for context
    SOURCE_SET_PATTERN = re.compile(
        r'val\s+(\w+)\s+by\s+(?:getting|creating)\s*\{',
        re.MULTILINE
    )

    # Version catalog TOML patterns
    TOML_VERSION_PATTERN = re.compile(
        r'^([a-zA-Z0-9_-]+)\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    TOML_LIBRARY_PATTERN = re.compile(
        r'^([a-zA-Z0-9_-]+)\s*=\s*\{\s*'
        r'(?:group\s*=\s*["\']([^"\']+)["\']\s*,\s*)?'
        r'(?:module\s*=\s*["\']([^"\']+)["\']\s*,?\s*)?'
        r'(?:name\s*=\s*["\']([^"\']+)["\']\s*,?\s*)?'
        r'(?:version(?:\.ref)?\s*=\s*["\']([^"\']+)["\'])?\s*\}',
        re.MULTILINE
    )

    # Simple TOML library: lib = "group:artifact:version"
    TOML_LIBRARY_SIMPLE_PATTERN = re.compile(
        r'^([a-zA-Z0-9_-]+)\s*=\s*["\']([^"\']+:[^"\']+)["\']',
        re.MULTILINE
    )

    @property
    def name(self) -> str:
        """Get the name of this analyzer.

        Returns:
            Human-readable name identifying this analyzer.
        """
        return "dependencies"

    def get_memory_category(self) -> str:
        """Get the memory category for storing analysis results.

        Returns:
            String identifier for the category under which analysis
            results should be stored in the memory system.
        """
        return "dependencies"

    async def analyze(self) -> AnalysisResult:
        """Analyze the project to detect dependencies and module structure.

        Scans settings.gradle.kts for module definitions, build.gradle.kts
        files for dependency declarations, and gradle/libs.versions.toml
        for version catalog configuration.

        Returns:
            AnalysisResult containing:
            {
                "modules": [...],
                "module_graph": {...},
                "external_dependencies": [...],
                "version_catalog": {...},
                "dependency_count": int,
                "categories": {...}
            }

        Example:
            >>> result = await analyzer.analyze()
            >>> print(result.data["modules"])
            ['app', 'core', 'data']
        """
        try:
            logger.info(f"Analyzing dependencies for project: {self.project_root}")
            warnings: list[str] = []

            # Parse modules from settings.gradle.kts
            modules = self._parse_modules()
            logger.debug(f"Found {len(modules)} modules: {modules}")

            # Build module dependency graph
            module_graph = await self._build_module_graph(modules)
            logger.debug(f"Built module graph with {len(module_graph)} entries")

            # Parse version catalog if exists
            version_catalog = self._parse_version_catalog()
            if version_catalog.get("versions") or version_catalog.get("libraries"):
                logger.debug(
                    f"Parsed version catalog: {len(version_catalog.get('versions', {}))} versions, "
                    f"{len(version_catalog.get('libraries', {}))} libraries"
                )

            # Parse all external dependencies
            external_deps = await self._parse_external_dependencies(version_catalog)
            logger.debug(f"Found {len(external_deps)} external dependencies")

            # Categorize dependencies
            categories = self._categorize_dependencies(external_deps)

            # Prepare result data
            data = {
                "modules": modules,
                "module_graph": module_graph,
                "external_dependencies": [dep.to_dict() for dep in external_deps],
                "version_catalog": version_catalog,
                "dependency_count": len(external_deps),
                "categories": {
                    cat: [dep.to_dict() for dep in deps]
                    for cat, deps in categories.items()
                },
            }

            logger.info(
                f"Dependency analysis complete. Found {len(modules)} modules, "
                f"{len(external_deps)} external dependencies."
            )

            result = self._create_success_result(data)
            result.warnings = warnings
            return result

        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
            return self._create_error_result(
                errors=[f"Failed to analyze dependencies: {str(e)}"]
            )

    def _parse_modules(self) -> list[str]:
        """Parse module definitions from settings.gradle.kts.

        Looks for include() statements in settings.gradle.kts to identify
        all modules in the project.

        Returns:
            List of module names/paths (e.g., ["app", "core", "feature:home"]).
        """
        modules: list[str] = []

        # Try both settings.gradle.kts and settings.gradle
        settings_files = [
            self.project_root / "settings.gradle.kts",
            self.project_root / "settings.gradle",
        ]

        for settings_file in settings_files:
            if settings_file.exists():
                try:
                    content = settings_file.read_text(encoding="utf-8")
                    matches = self.INCLUDE_PATTERN.findall(content)
                    for match in matches:
                        # Remove leading colon if present
                        module_name = match.lstrip(":")
                        if module_name and module_name not in modules:
                            modules.append(module_name)
                    logger.debug(f"Parsed modules from {settings_file.name}: {modules}")
                except Exception as e:
                    logger.warning(f"Error reading {settings_file}: {e}")

        return modules

    async def _build_module_graph(
        self,
        modules: list[str]
    ) -> dict[str, list[str]]:
        """Build dependency graph between project modules.

        Analyzes build.gradle.kts files in each module to find
        project() dependencies between modules.

        Args:
            modules: List of module names to analyze.

        Returns:
            Dictionary mapping module name to list of modules it depends on.
        """
        module_graph: dict[str, list[str]] = {}

        # For each module, find its build.gradle.kts and parse project dependencies
        for module in modules:
            # Convert module path to directory path (feature:home -> feature/home)
            module_path = module.replace(":", "/")
            build_files = [
                self.project_root / module_path / "build.gradle.kts",
                self.project_root / module_path / "build.gradle",
            ]

            for build_file in build_files:
                if build_file.exists():
                    deps = self._parse_project_dependencies(build_file)
                    if deps:
                        module_graph[module] = deps
                    break

        return module_graph

    def _parse_project_dependencies(self, build_file: Path) -> list[str]:
        """Parse project() dependencies from a build file.

        Args:
            build_file: Path to the build.gradle.kts file.

        Returns:
            List of module names this module depends on.
        """
        dependencies: list[str] = []

        try:
            content = build_file.read_text(encoding="utf-8")
            matches = self.PROJECT_DEP_PATTERN.findall(content)
            for match in matches:
                # Remove leading colon
                module_name = match.lstrip(":")
                if module_name and module_name not in dependencies:
                    dependencies.append(module_name)
        except Exception as e:
            logger.warning(f"Error parsing project dependencies from {build_file}: {e}")

        return dependencies

    def _parse_version_catalog(self) -> dict[str, Any]:
        """Parse version catalog from gradle/libs.versions.toml.

        Returns:
            Dictionary containing:
            {
                "versions": {"kotlin": "1.9.20", ...},
                "libraries": {"kotlinx-coroutines": {"group": "...", ...}, ...}
            }
        """
        catalog: dict[str, Any] = {
            "versions": {},
            "libraries": {},
            "bundles": {},
            "plugins": {},
        }

        toml_file = self.project_root / "gradle" / "libs.versions.toml"
        if not toml_file.exists():
            return catalog

        try:
            content = toml_file.read_text(encoding="utf-8")
            current_section: str | None = None

            for line in content.split("\n"):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Detect section headers
                if line.startswith("["):
                    section = line.strip("[]").lower()
                    if section in ("versions", "libraries", "bundles", "plugins"):
                        current_section = section
                    continue

                # Parse content based on current section
                if current_section == "versions":
                    match = self.TOML_VERSION_PATTERN.match(line)
                    if match:
                        key, value = match.groups()
                        catalog["versions"][key] = value

                elif current_section == "libraries":
                    # Try complex format first
                    match = self.TOML_LIBRARY_PATTERN.match(line)
                    if match:
                        key, group, module, name, version_ref = match.groups()
                        # module might be "group:artifact" format
                        if module and ":" in module:
                            parts = module.split(":")
                            group = parts[0]
                            name = parts[1] if len(parts) > 1 else name
                        catalog["libraries"][key] = {
                            "group": group,
                            "name": name or module,
                            "version_ref": version_ref,
                        }
                    else:
                        # Try simple format: lib = "group:artifact:version"
                        match = self.TOML_LIBRARY_SIMPLE_PATTERN.match(line)
                        if match:
                            key, coords = match.groups()
                            parts = coords.split(":")
                            catalog["libraries"][key] = {
                                "group": parts[0] if len(parts) > 0 else "",
                                "name": parts[1] if len(parts) > 1 else "",
                                "version": parts[2] if len(parts) > 2 else None,
                            }

        except Exception as e:
            logger.warning(f"Error parsing version catalog: {e}")

        return catalog

    async def _parse_external_dependencies(
        self,
        version_catalog: dict[str, Any]
    ) -> list[ExternalDependency]:
        """Parse all external dependencies from build.gradle.kts files.

        Args:
            version_catalog: Parsed version catalog for resolving libs.xxx references.

        Returns:
            List of ExternalDependency objects.
        """
        all_deps: dict[str, ExternalDependency] = {}  # Key: "group:name"

        # Find all build.gradle.kts files
        gradle_files = list(self.project_root.rglob("build.gradle.kts"))
        gradle_files.extend(list(self.project_root.rglob("build.gradle")))

        for gradle_file in gradle_files:
            try:
                file_deps = self._parse_gradle_dependencies(
                    gradle_file,
                    version_catalog
                )
                # Merge dependencies
                for dep in file_deps:
                    key = f"{dep.group}:{dep.name}"
                    if key in all_deps:
                        # Merge configurations
                        existing = all_deps[key]
                        for config in dep.configurations:
                            if config not in existing.configurations:
                                existing.configurations.append(config)
                        # Update version if we now have one
                        if dep.version and not existing.version:
                            existing.version = dep.version
                    else:
                        all_deps[key] = dep

            except Exception as e:
                logger.warning(f"Error parsing dependencies from {gradle_file}: {e}")

        return list(all_deps.values())

    def _parse_gradle_dependencies(
        self,
        gradle_file: Path,
        version_catalog: dict[str, Any]
    ) -> list[ExternalDependency]:
        """Parse dependencies from a single Gradle build file.

        Handles multiple declaration styles:
        - Standard: implementation("group:name:version")
        - Version catalog: implementation(libs.some.lib)
        - Various configurations: api, compileOnly, testImplementation, etc.

        Args:
            gradle_file: Path to the build.gradle.kts file.
            version_catalog: Parsed version catalog for resolving references.

        Returns:
            List of ExternalDependency objects found in this file.
        """
        dependencies: list[ExternalDependency] = []

        try:
            content = gradle_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading {gradle_file}: {e}")
            return dependencies

        # Detect current source set context
        current_source_set = self._detect_source_set_context(content)

        # Parse standard dependencies
        for match in self.STANDARD_DEP_PATTERN.finditer(content):
            config = match.group("config")
            coords = match.group("coords")

            # Skip project() references
            if coords.startswith(":") or "project(" in coords:
                continue

            dep = self._parse_dependency_coords(
                coords,
                config,
                current_source_set,
                content[:match.start()]
            )
            if dep:
                dependencies.append(dep)

        # Parse version catalog dependencies
        for match in self.CATALOG_DEP_PATTERN.finditer(content):
            config = match.group("config")
            catalog_ref = match.group("catalog")

            dep = self._resolve_catalog_dependency(
                catalog_ref,
                config,
                version_catalog,
                current_source_set,
                content[:match.start()]
            )
            if dep:
                dependencies.append(dep)

        return dependencies

    def _detect_source_set_context(self, content: str) -> str:
        """Detect the default source set context from file content.

        Args:
            content: Full file content.

        Returns:
            Default source set name (e.g., "commonMain") or "main".
        """
        # Check for KMP source set structure
        if "sourceSets" in content:
            match = self.SOURCE_SET_PATTERN.search(content)
            if match:
                return match.group(1)
        return "main"

    def _get_source_set_for_position(
        self,
        content_before: str,
        default_source_set: str
    ) -> str:
        """Determine source set context for a dependency position.

        Args:
            content_before: Content before the dependency declaration.
            default_source_set: Default source set to return.

        Returns:
            Source set name for the dependency context.
        """
        # Find the last source set declaration before this position
        matches = list(self.SOURCE_SET_PATTERN.finditer(content_before))
        if matches:
            return matches[-1].group(1)
        return default_source_set

    def _parse_dependency_coords(
        self,
        coords: str,
        config: str,
        default_source_set: str,
        content_before: str
    ) -> ExternalDependency | None:
        """Parse dependency coordinates into an ExternalDependency.

        Args:
            coords: Maven coordinates (e.g., "org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3").
            config: Gradle configuration (e.g., "implementation").
            default_source_set: Default source set context.
            content_before: Content before this declaration for context detection.

        Returns:
            ExternalDependency object or None if parsing fails.
        """
        parts = coords.split(":")

        if len(parts) < 2:
            return None

        group = parts[0]
        name = parts[1]
        version = parts[2] if len(parts) > 2 else None

        # Determine source set context
        source_set = self._get_source_set_for_position(
            content_before,
            default_source_set
        )

        # Determine category
        category = self._categorize_single_dependency(group, name)

        return ExternalDependency(
            group=group,
            name=name,
            version=version,
            configurations=[source_set],
            category=category,
            raw_declaration=coords,
        )

    def _resolve_catalog_dependency(
        self,
        catalog_ref: str,
        config: str,
        version_catalog: dict[str, Any],
        default_source_set: str,
        content_before: str
    ) -> ExternalDependency | None:
        """Resolve a version catalog reference to an ExternalDependency.

        Args:
            catalog_ref: Catalog reference (e.g., "libs.kotlinx.coroutines").
            config: Gradle configuration.
            version_catalog: Parsed version catalog.
            default_source_set: Default source set context.
            content_before: Content before this declaration.

        Returns:
            ExternalDependency object or None if resolution fails.
        """
        # Convert libs.kotlinx.coroutines to catalog key
        # Remove "libs." prefix and convert dots to dashes
        if not catalog_ref.startswith("libs."):
            return None

        ref_key = catalog_ref[5:]  # Remove "libs."
        # Try both dot and dash variations
        possible_keys = [
            ref_key,
            ref_key.replace(".", "-"),
            ref_key.replace("-", "."),
        ]

        libraries = version_catalog.get("libraries", {})
        versions = version_catalog.get("versions", {})

        for key in possible_keys:
            if key in libraries:
                lib_info = libraries[key]
                group = lib_info.get("group", "")
                name = lib_info.get("name", "")
                version = lib_info.get("version")

                # Resolve version reference
                if not version:
                    version_ref = lib_info.get("version_ref")
                    if version_ref and version_ref in versions:
                        version = versions[version_ref]

                if group and name:
                    source_set = self._get_source_set_for_position(
                        content_before,
                        default_source_set
                    )
                    category = self._categorize_single_dependency(group, name)

                    return ExternalDependency(
                        group=group,
                        name=name,
                        version=version,
                        configurations=[source_set],
                        category=category,
                        raw_declaration=catalog_ref,
                    )

        # Catalog reference not found - create placeholder
        logger.debug(f"Could not resolve catalog reference: {catalog_ref}")
        source_set = self._get_source_set_for_position(
            content_before,
            default_source_set
        )
        return ExternalDependency(
            group="",
            name=catalog_ref,
            version=None,
            configurations=[source_set],
            category="unknown",
            raw_declaration=catalog_ref,
        )

    def _categorize_single_dependency(
        self,
        group: str,
        name: str
    ) -> str:
        """Categorize a single dependency based on group and artifact name.

        Args:
            group: Maven group ID.
            name: Artifact name.

        Returns:
            Category string (e.g., "kotlin_standard", "networking").
        """
        full_coords = f"{group}:{name}"

        for category, patterns in DEPENDENCY_CATEGORIES.items():
            for pattern in patterns:
                if pattern in full_coords or group.startswith(pattern.rstrip(":")):
                    return category

        return "other"

    def _categorize_dependencies(
        self,
        dependencies: list[ExternalDependency]
    ) -> dict[str, list[ExternalDependency]]:
        """Organize dependencies by category.

        Args:
            dependencies: List of all dependencies.

        Returns:
            Dictionary mapping category to list of dependencies.
        """
        categories: dict[str, list[ExternalDependency]] = {}

        for dep in dependencies:
            category = dep.category
            if category not in categories:
                categories[category] = []
            categories[category].append(dep)

        return categories

    def get_module_dependents(
        self,
        module: str,
        module_graph: dict[str, list[str]]
    ) -> list[str]:
        """Find all modules that depend on a given module.

        Args:
            module: Module name to find dependents for.
            module_graph: Module dependency graph from analyze().

        Returns:
            List of module names that depend on the given module.

        Example:
            >>> dependents = analyzer.get_module_dependents("core", result.data["module_graph"])
            >>> print(dependents)  # ["app", "feature-home"]
        """
        dependents = []
        for mod, deps in module_graph.items():
            if module in deps:
                dependents.append(mod)
        return dependents

    def get_dependencies_by_category(
        self,
        category: str,
        analysis_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Get all dependencies in a specific category.

        Args:
            category: Category name (e.g., "networking", "database").
            analysis_data: Analysis result data from analyze().

        Returns:
            List of dependency dictionaries in the category.

        Example:
            >>> result = await analyzer.analyze()
            >>> networking_deps = analyzer.get_dependencies_by_category(
            ...     "networking", result.data
            ... )
        """
        categories = analysis_data.get("categories", {})
        return categories.get(category, [])

    def find_dependency(
        self,
        artifact_pattern: str,
        analysis_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Find dependencies matching a pattern.

        Args:
            artifact_pattern: Pattern to match against group:name.
            analysis_data: Analysis result data from analyze().

        Returns:
            List of matching dependency dictionaries.

        Example:
            >>> ktor_deps = analyzer.find_dependency("ktor", result.data)
        """
        matches = []
        for dep in analysis_data.get("external_dependencies", []):
            full_coords = f"{dep.get('group', '')}:{dep.get('name', '')}"
            if artifact_pattern.lower() in full_coords.lower():
                matches.append(dep)
        return matches
