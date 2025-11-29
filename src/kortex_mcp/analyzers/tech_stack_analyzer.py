"""Tech stack analyzer for detecting frameworks and libraries in KMP projects.

This module provides analysis capabilities for identifying the technology stack
used in a Kotlin Multiplatform project, including dependency injection frameworks,
networking libraries, database solutions, and other common libraries.
"""

import logging
import re
from pathlib import Path
from typing import Any

from .base import AnalysisResult, BaseAnalyzer

logger = logging.getLogger(__name__)


# Framework detection patterns organized by category
FRAMEWORK_PATTERNS: dict[str, dict[str, list[str]]] = {
    "di": {
        "koin": ["org.koin", "io.insert-koin"],
        "hilt": ["dagger.hilt"],
        "dagger": ["com.google.dagger"],
        "kodein": ["org.kodein.di"],
    },
    "networking": {
        "ktor": ["io.ktor"],
        "retrofit": ["com.squareup.retrofit2"],
        "okhttp": ["com.squareup.okhttp3"],
    },
    "database": {
        "room": ["androidx.room"],
        "sqldelight": ["app.cash.sqldelight", "com.squareup.sqldelight"],
        "realm": ["io.realm"],
    },
    "serialization": {
        "kotlinx_serialization": ["org.jetbrains.kotlinx:kotlinx-serialization"],
        "moshi": ["com.squareup.moshi"],
        "gson": ["com.google.code.gson"],
    },
    "image_loading": {
        "coil": ["io.coil-kt"],
        "glide": ["com.github.bumptech.glide"],
        "picasso": ["com.squareup.picasso"],
    },
    "navigation": {
        "compose_navigation": ["androidx.navigation"],
        "voyager": ["cafe.adriel.voyager"],
        "decompose": ["com.arkivanov.decompose"],
    },
    "testing": {
        "junit": ["junit:junit", "org.junit"],
        "kotest": ["io.kotest"],
        "mockk": ["io.mockk"],
        "turbine": ["app.cash.turbine"],
    },
    "logging": {
        "timber": ["com.jakewharton.timber"],
        "napier": ["io.github.aakira"],
        "kermit": ["co.touchlab.kermit"],
    },
}

# Import patterns for detecting frameworks in Kotlin source files
IMPORT_PATTERNS: dict[str, dict[str, list[str]]] = {
    "di": {
        "koin": ["org.koin"],
        "hilt": ["dagger.hilt"],
        "dagger": ["dagger."],
        "kodein": ["org.kodein.di"],
    },
    "networking": {
        "ktor": ["io.ktor"],
        "retrofit": ["retrofit2."],
        "okhttp": ["okhttp3."],
    },
    "database": {
        "room": ["androidx.room"],
        "sqldelight": ["app.cash.sqldelight", "com.squareup.sqldelight"],
        "realm": ["io.realm"],
    },
    "serialization": {
        "kotlinx_serialization": ["kotlinx.serialization"],
        "moshi": ["com.squareup.moshi"],
        "gson": ["com.google.gson"],
    },
    "image_loading": {
        "coil": ["coil."],
        "glide": ["com.bumptech.glide"],
        "picasso": ["com.squareup.picasso"],
    },
    "navigation": {
        "compose_navigation": ["androidx.navigation"],
        "voyager": ["cafe.adriel.voyager"],
        "decompose": ["com.arkivanov.decompose"],
    },
    "testing": {
        "junit": ["org.junit"],
        "kotest": ["io.kotest"],
        "mockk": ["io.mockk"],
        "turbine": ["app.cash.turbine"],
    },
    "logging": {
        "timber": ["timber.log"],
        "napier": ["io.github.aakira"],
        "kermit": ["co.touchlab.kermit"],
    },
}


class TechStackAnalyzer(BaseAnalyzer):
    """Analyzer for detecting technology stack in Kotlin Multiplatform projects.

    Scans build.gradle.kts files and Kotlin source files to identify
    frameworks and libraries used in the project, organized by category.

    Supported categories:
        - di: Dependency Injection (Koin, Hilt, Dagger, Kodein)
        - networking: HTTP clients (Ktor, Retrofit, OkHttp)
        - database: Persistence solutions (Room, SQLDelight, Realm)
        - serialization: Data serialization (kotlinx.serialization, Moshi, Gson)
        - image_loading: Image loading libraries (Coil, Glide, Picasso)
        - navigation: Navigation frameworks (Compose Navigation, Voyager, Decompose)
        - testing: Testing frameworks (JUnit, Kotest, MockK, Turbine)
        - logging: Logging libraries (Timber, Napier, Kermit)

    Attributes:
        project_root: Path to the root directory of the project being analyzed.

    Example:
        >>> analyzer = TechStackAnalyzer(Path("/path/to/project"))
        >>> result = await analyzer.analyze()
        >>> if result.success:
        ...     print(result.data["di"])  # {"framework": "koin", "version": "3.5.0", ...}
    """

    @property
    def name(self) -> str:
        """Get the name of this analyzer.

        Returns:
            Human-readable name identifying this analyzer.
        """
        return "tech_stack"

    def get_memory_category(self) -> str:
        """Get the memory category for storing analysis results.

        Returns:
            String identifier for the category under which analysis
            results should be stored in the memory system.
        """
        return "tech_stack"

    async def analyze(self) -> AnalysisResult:
        """Analyze the project to detect the technology stack.

        Scans build.gradle.kts files for dependency declarations and
        Kotlin source files for import statements to identify the
        frameworks and libraries used in the project.

        Returns:
            AnalysisResult containing detected frameworks organized by category:
            {
                "di": {"framework": "koin", "version": "3.5.0", "artifacts": [...]},
                "networking": {...},
                ...
            }

        Example:
            >>> result = await analyzer.analyze()
            >>> print(result.data["networking"]["framework"])
        """
        try:
            logger.info(f"Analyzing tech stack for project: {self.project_root}")

            # Collect all gradle dependencies
            gradle_deps = await self._scan_gradle_files()

            # Collect imports from Kotlin source files
            import_deps = await self._scan_kotlin_imports()

            # Merge and categorize detected frameworks
            tech_stack = self._categorize_frameworks(gradle_deps, import_deps)

            logger.info(f"Tech stack analysis complete. Found {len(tech_stack)} categories.")
            return self._create_success_result(tech_stack)

        except Exception as e:
            logger.error(f"Error analyzing tech stack: {e}")
            return self._create_error_result(
                errors=[f"Failed to analyze tech stack: {str(e)}"]
            )

    async def _scan_gradle_files(self) -> dict[str, list[dict[str, Any]]]:
        """Scan all build.gradle.kts files for dependencies.

        Returns:
            Dictionary mapping category to list of detected dependencies:
            {
                "di": [{"framework": "koin", "artifact": "...", "version": "..."}],
                ...
            }
        """
        gradle_deps: dict[str, list[dict[str, Any]]] = {}

        # Find all build.gradle.kts files
        gradle_files = list(self.project_root.rglob("build.gradle.kts"))
        logger.debug(f"Found {len(gradle_files)} build.gradle.kts files")

        for gradle_file in gradle_files:
            try:
                file_deps = self._parse_gradle_file(gradle_file)
                for category, deps in file_deps.items():
                    if category not in gradle_deps:
                        gradle_deps[category] = []
                    gradle_deps[category].extend(deps)
            except Exception as e:
                logger.warning(f"Error parsing {gradle_file}: {e}")

        return gradle_deps

    def _parse_gradle_file(self, gradle_file: Path) -> dict[str, list[dict[str, Any]]]:
        """Parse a single build.gradle.kts file for dependencies.

        Args:
            gradle_file: Path to the build.gradle.kts file.

        Returns:
            Dictionary mapping category to list of detected dependencies.
        """
        deps: dict[str, list[dict[str, Any]]] = {}

        try:
            content = gradle_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading {gradle_file}: {e}")
            return deps

        # Pattern to match dependency declarations
        # Matches patterns like:
        # - implementation("group:artifact:version")
        # - implementation("group:artifact") version "1.0.0"
        # - implementation(libs.some.dependency)
        dep_pattern = re.compile(
            r'(?:implementation|api|compileOnly|runtimeOnly|testImplementation|androidTestImplementation)\s*\(\s*'
            r'["\']([^"\']+)["\']'
            r'(?:\s*,\s*["\']([^"\']+)["\'])?\s*\)',
            re.MULTILINE
        )

        # Also match Kotlin DSL style with version catalogs
        catalog_pattern = re.compile(
            r'(?:implementation|api|compileOnly|runtimeOnly|testImplementation|androidTestImplementation)\s*\(\s*'
            r'(libs\.[a-zA-Z0-9_.]+)'
            r'\s*\)',
            re.MULTILINE
        )

        # Parse standard dependencies
        for match in dep_pattern.finditer(content):
            artifact_spec = match.group(1)
            deps_info = self._parse_artifact_spec(artifact_spec)
            if deps_info:
                category = deps_info.get("category")
                if category:
                    if category not in deps:
                        deps[category] = []
                    deps[category].append(deps_info)

        return deps

    def _parse_artifact_spec(self, artifact_spec: str) -> dict[str, Any] | None:
        """Parse an artifact specification to extract framework info.

        Args:
            artifact_spec: Maven artifact specification (e.g., "group:artifact:version")

        Returns:
            Dictionary with framework info or None if not a known framework:
            {"framework": "...", "artifact": "...", "version": "...", "category": "..."}
        """
        # Split artifact spec into components
        parts = artifact_spec.split(":")
        if len(parts) < 2:
            return None

        group = parts[0]
        artifact = parts[1] if len(parts) > 1 else ""
        version = parts[2] if len(parts) > 2 else None

        # Check against known framework patterns
        for category, frameworks in FRAMEWORK_PATTERNS.items():
            for framework_name, patterns in frameworks.items():
                for pattern in patterns:
                    # Check if pattern matches the artifact spec
                    if pattern in artifact_spec or artifact_spec.startswith(pattern):
                        return {
                            "framework": framework_name,
                            "artifact": artifact_spec,
                            "group": group,
                            "artifact_name": artifact,
                            "version": version,
                            "category": category,
                        }

        return None

    async def _scan_kotlin_imports(self) -> dict[str, set[str]]:
        """Scan Kotlin source files for import statements.

        Returns:
            Dictionary mapping category to set of detected framework names.
        """
        import_deps: dict[str, set[str]] = {}

        # Find all Kotlin files
        kotlin_files = list(self.project_root.rglob("*.kt"))
        logger.debug(f"Found {len(kotlin_files)} Kotlin files to scan for imports")

        for kotlin_file in kotlin_files:
            try:
                file_imports = self._parse_kotlin_imports(kotlin_file)
                for category, frameworks in file_imports.items():
                    if category not in import_deps:
                        import_deps[category] = set()
                    import_deps[category].update(frameworks)
            except Exception as e:
                logger.warning(f"Error parsing imports in {kotlin_file}: {e}")

        return import_deps

    def _parse_kotlin_imports(self, kotlin_file: Path) -> dict[str, set[str]]:
        """Parse a Kotlin file for import statements.

        Args:
            kotlin_file: Path to the Kotlin source file.

        Returns:
            Dictionary mapping category to set of detected framework names.
        """
        imports: dict[str, set[str]] = {}

        try:
            content = kotlin_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading {kotlin_file}: {e}")
            return imports

        # Pattern to match import statements
        import_pattern = re.compile(r'^import\s+([a-zA-Z0-9_.]+)', re.MULTILINE)

        for match in import_pattern.finditer(content):
            import_statement = match.group(1)

            # Check against known import patterns
            for category, frameworks in IMPORT_PATTERNS.items():
                for framework_name, patterns in frameworks.items():
                    for pattern in patterns:
                        if import_statement.startswith(pattern):
                            if category not in imports:
                                imports[category] = set()
                            imports[category].add(framework_name)
                            break

        return imports

    def _categorize_frameworks(
        self,
        gradle_deps: dict[str, list[dict[str, Any]]],
        import_deps: dict[str, set[str]],
    ) -> dict[str, dict[str, Any]]:
        """Merge and categorize detected frameworks from all sources.

        Combines information from Gradle dependencies and import statements
        to produce a comprehensive tech stack report.

        Args:
            gradle_deps: Dependencies detected from Gradle files.
            import_deps: Frameworks detected from import statements.

        Returns:
            Dictionary mapping category to framework info:
            {
                "di": {"framework": "koin", "version": "3.5.0", "artifacts": [...]},
                ...
            }
        """
        tech_stack: dict[str, dict[str, Any]] = {}

        # Process Gradle dependencies (primary source - has version info)
        for category, deps in gradle_deps.items():
            if not deps:
                continue

            # Group by framework
            framework_artifacts: dict[str, list[dict[str, Any]]] = {}
            for dep in deps:
                framework = dep.get("framework")
                if framework:
                    if framework not in framework_artifacts:
                        framework_artifacts[framework] = []
                    framework_artifacts[framework].append(dep)

            # Select primary framework for category (one with most artifacts)
            if framework_artifacts:
                primary_framework = max(
                    framework_artifacts.keys(),
                    key=lambda f: len(framework_artifacts[f])
                )
                primary_deps = framework_artifacts[primary_framework]

                # Extract version from first artifact with version
                version = None
                for dep in primary_deps:
                    if dep.get("version"):
                        version = dep["version"]
                        break

                tech_stack[category] = {
                    "framework": primary_framework,
                    "version": version,
                    "artifacts": [dep.get("artifact") for dep in primary_deps],
                    "source": "gradle",
                }

        # Add frameworks detected only from imports (without version info)
        for category, frameworks in import_deps.items():
            if category in tech_stack:
                # Category already has Gradle-detected framework
                # Add import-detected frameworks as additional info
                existing = tech_stack[category]
                import_detected = frameworks - {existing.get("framework")}
                if import_detected:
                    existing["additional_frameworks"] = list(import_detected)
            else:
                # No Gradle detection - use import detection
                if frameworks:
                    # Use the first detected framework
                    primary_framework = list(frameworks)[0]
                    tech_stack[category] = {
                        "framework": primary_framework,
                        "version": None,  # No version info from imports
                        "artifacts": [],
                        "source": "imports",
                    }
                    if len(frameworks) > 1:
                        tech_stack[category]["additional_frameworks"] = list(
                            frameworks - {primary_framework}
                        )

        return tech_stack

    def get_framework_for_category(
        self,
        category: str,
        tech_stack: dict[str, dict[str, Any]]
    ) -> str | None:
        """Get the primary framework for a given category.

        Args:
            category: Category name (e.g., "di", "networking").
            tech_stack: Tech stack data from analyze().

        Returns:
            Framework name or None if category not detected.

        Example:
            >>> result = await analyzer.analyze()
            >>> framework = analyzer.get_framework_for_category("di", result.data)
            >>> print(framework)  # "koin"
        """
        category_data = tech_stack.get(category)
        if category_data:
            return category_data.get("framework")
        return None

    def get_all_artifacts(
        self,
        tech_stack: dict[str, dict[str, Any]]
    ) -> list[str]:
        """Get all detected artifacts across all categories.

        Args:
            tech_stack: Tech stack data from analyze().

        Returns:
            List of all artifact specifications.

        Example:
            >>> result = await analyzer.analyze()
            >>> artifacts = analyzer.get_all_artifacts(result.data)
            >>> for artifact in artifacts:
            ...     print(artifact)
        """
        all_artifacts = []
        for category_data in tech_stack.values():
            artifacts = category_data.get("artifacts", [])
            all_artifacts.extend(artifacts)
        return all_artifacts
