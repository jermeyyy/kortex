"""Testing analyzer for Kotlin Multiplatform projects.

This module provides analysis capabilities for detecting testing frameworks,
libraries, and patterns used in KMP projects.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..utils.logging import get_logger
from .base import AnalysisResult, BaseAnalyzer

logger = get_logger(__name__)


# Testing framework patterns in Gradle dependencies
TESTING_FRAMEWORK_PATTERNS: dict[str, list[str]] = {
    "kotlin.test": [
        "org.jetbrains.kotlin:kotlin-test",
        "kotlin-test",
        "kotlin-test-common",
        "kotlin-test-annotations-common",
        "kotlin-test-junit",
        "kotlin-test-junit5",
    ],
    "junit4": [
        "junit:junit",
        "org.junit.vintage:junit-vintage-engine",
    ],
    "junit5": [
        "org.junit.jupiter:junit-jupiter",
        "org.junit.jupiter:junit-jupiter-api",
        "org.junit.jupiter:junit-jupiter-engine",
        "org.junit.jupiter:junit-jupiter-params",
    ],
    "kotest": [
        "io.kotest:kotest-runner",
        "io.kotest:kotest-framework",
        "io.kotest:kotest-assertions-core",
        "io.kotest:kotest-property",
    ],
    "robolectric": [
        "org.robolectric:robolectric",
    ],
}

# Mock library patterns
MOCK_LIBRARY_PATTERNS: dict[str, dict[str, Any]] = {
    "mockk": {
        "patterns": [
            "io.mockk:mockk",
            "io.mockk:mockk-android",
            "io.mockk:mockk-common",
        ],
        "multiplatform": True,
    },
    "mockito": {
        "patterns": [
            "org.mockito:mockito-core",
            "org.mockito:mockito-inline",
            "org.mockito:mockito-android",
            "org.mockito.kotlin:mockito-kotlin",
        ],
        "multiplatform": False,
    },
    "mockk-common": {
        "patterns": [
            "io.mockk:mockk-common",
        ],
        "multiplatform": True,
    },
}

# Assertion library patterns
ASSERTION_LIBRARY_PATTERNS: dict[str, list[str]] = {
    "google-truth": [
        "com.google.truth:truth",
        "com.google.truth.extensions:truth-java8-extension",
    ],
    "assertj": [
        "org.assertj:assertj-core",
    ],
    "strikt": [
        "io.strikt:strikt-core",
        "io.strikt:strikt-jvm",
    ],
    "kotest-assertions": [
        "io.kotest:kotest-assertions-core",
        "io.kotest:kotest-assertions-shared",
        "io.kotest:kotest-assertions-json",
    ],
}

# Testing utility patterns
TESTING_UTILITY_PATTERNS: dict[str, dict[str, Any]] = {
    "turbine": {
        "patterns": [
            "app.cash.turbine:turbine",
        ],
        "category": "flow_testing",
    },
    "kotlinx-coroutines-test": {
        "patterns": [
            "org.jetbrains.kotlinx:kotlinx-coroutines-test",
        ],
        "category": "coroutine_testing",
    },
    "androidx-test": {
        "patterns": [
            "androidx.test:core",
            "androidx.test:runner",
            "androidx.test:rules",
            "androidx.test.ext:junit",
            "androidx.test.espresso:espresso-core",
        ],
        "category": "android_testing",
    },
}

# Coverage tool patterns
COVERAGE_TOOL_PATTERNS: dict[str, list[str]] = {
    "kover": [
        "org.jetbrains.kotlinx.kover",
        "kotlinx-kover",
    ],
    "jacoco": [
        "org.jacoco:jacoco",
        "jacoco",
    ],
}

# Import patterns for detecting frameworks from source code
IMPORT_PATTERNS: dict[str, dict[str, list[str]]] = {
    "frameworks": {
        "kotlin.test": ["kotlin.test"],
        "junit4": ["org.junit.Test", "org.junit.Assert", "org.junit.Before", "org.junit.After"],
        "junit5": ["org.junit.jupiter", "org.junit.jupiter.api"],
        "kotest": ["io.kotest"],
        "robolectric": ["org.robolectric"],
        "xctest": ["XCTest"],
    },
    "mocking": {
        "mockk": ["io.mockk"],
        "mockito": ["org.mockito"],
    },
    "assertions": {
        "google-truth": ["com.google.common.truth"],
        "assertj": ["org.assertj"],
        "strikt": ["strikt.api", "strikt.assertions"],
        "kotest-assertions": ["io.kotest.matchers", "io.kotest.assertions"],
    },
    "utilities": {
        "turbine": ["app.cash.turbine"],
        "kotlinx-coroutines-test": ["kotlinx.coroutines.test"],
    },
}


class TestingAnalyzer(BaseAnalyzer):
    """Analyzer for detecting testing setup in Kotlin Multiplatform projects.

    Scans project structure, build files, and source code to identify:
    - Test directory structure and organization
    - Testing frameworks (kotlin.test, JUnit, Kotest, etc.)
    - Mock libraries (MockK, Mockito)
    - Assertion libraries (Truth, AssertJ, Strikt, etc.)
    - Testing utilities (Turbine, coroutines-test)
    - Test naming conventions
    - Coverage configuration (Kover, JaCoCo)

    Attributes:
        project_root: Path to the root directory of the project being analyzed.

    Example:
        >>> analyzer = TestingAnalyzer(Path("/path/to/project"))
        >>> result = await analyzer.analyze()
        >>> if result.success:
        ...     print(result.data["frameworks"]["primary"])  # "kotlin.test"
        ...     print(result.data["mocking"]["library"])  # "mockk"
    """

    @property
    def name(self) -> str:
        """Get the name of this analyzer.

        Returns:
            Human-readable name identifying this analyzer.
        """
        return "testing"

    def get_memory_category(self) -> str:
        """Get the memory category for storing analysis results.

        Returns:
            String identifier for the category under which analysis
            results should be stored in the memory system.
        """
        return "testing_setup"

    async def analyze(self) -> AnalysisResult:
        """Analyze the project to detect testing setup and configuration.

        Scans build.gradle.kts files, test source directories, and test files
        to identify the testing frameworks, libraries, and patterns used.

        Returns:
            AnalysisResult containing detected testing setup:
            {
                "test_structure": {...},
                "frameworks": {...},
                "mocking": {...},
                "assertions": {...},
                "utilities": {...},
                "naming_patterns": {...},
                "coverage": {...}
            }

        Example:
            >>> result = await analyzer.analyze()
            >>> print(result.data["frameworks"]["primary"])
        """
        try:
            logger.info(f"Analyzing testing setup for project: {self.project_root}")
            warnings: list[str] = []

            # Analyze test directory structure
            test_structure = self._analyze_test_structure()

            # Scan Gradle files for test dependencies
            gradle_deps = await self._scan_gradle_dependencies()

            # Scan test files for import patterns
            import_deps = await self._scan_test_imports()

            # Detect testing frameworks
            frameworks = self._detect_frameworks(gradle_deps, import_deps)

            # Detect mock libraries
            mocking = self._detect_mocking_libraries(gradle_deps, import_deps)

            # Detect assertion libraries
            assertions = self._detect_assertion_libraries(gradle_deps, import_deps)

            # Detect testing utilities
            utilities = self._detect_utilities(gradle_deps, import_deps)

            # Analyze test naming conventions
            naming_patterns = await self._analyze_naming_patterns()

            # Detect coverage configuration
            coverage = await self._detect_coverage_config()

            # Add warnings for missing configurations
            if not frameworks.get("detected"):
                warnings.append("No testing frameworks detected")
            if test_structure.get("total_test_files", 0) == 0:
                warnings.append("No test files found in the project")

            result_data = {
                "test_structure": test_structure,
                "frameworks": frameworks,
                "mocking": mocking,
                "assertions": assertions,
                "utilities": utilities,
                "naming_patterns": naming_patterns,
                "coverage": coverage,
            }

            logger.info(
                f"Testing analysis complete. Found {len(frameworks.get('detected', []))} frameworks, "
                f"{test_structure.get('total_test_files', 0)} test files."
            )

            if warnings:
                return AnalysisResult(
                    analyzer_name=self.name,
                    success=True,
                    data=result_data,
                    errors=[],
                    warnings=warnings,
                )
            return self._create_success_result(result_data)

        except Exception as e:
            logger.error(f"Error analyzing testing setup: {e}")
            return self._create_error_result(
                errors=[f"Failed to analyze testing setup: {str(e)}"]
            )

    def _analyze_test_structure(self) -> dict[str, Any]:
        """Analyze test directory structure and organization.

        Returns:
            Dictionary containing test structure information:
            {
                "source_sets": {...},
                "total_test_files": int,
                "organization": str
            }
        """
        source_sets: dict[str, dict[str, Any]] = {}
        total_files = 0

        # Standard KMP test source set patterns
        test_source_set_patterns = [
            ("commonTest", "src/commonTest/kotlin"),
            ("androidTest", "src/androidTest/kotlin"),
            ("androidUnitTest", "src/androidUnitTest/kotlin"),
            ("androidInstrumentedTest", "src/androidInstrumentedTest/kotlin"),
            ("iosTest", "src/iosTest/kotlin"),
            ("iosSimulatorArm64Test", "src/iosSimulatorArm64Test/kotlin"),
            ("iosX64Test", "src/iosX64Test/kotlin"),
            ("jvmTest", "src/jvmTest/kotlin"),
            ("jsTest", "src/jsTest/kotlin"),
            ("desktopTest", "src/desktopTest/kotlin"),
            ("macosTest", "src/macosTest/kotlin"),
            ("linuxTest", "src/linuxTest/kotlin"),
            ("mingwTest", "src/mingwTest/kotlin"),
            ("nativeTest", "src/nativeTest/kotlin"),
            # Also check standard Java test directories
            ("test", "src/test/kotlin"),
            ("test_java", "src/test/java"),
        ]

        for source_set_name, relative_path in test_source_set_patterns:
            test_dir = self.project_root / relative_path
            if test_dir.exists() and test_dir.is_dir():
                # Count test files
                kt_files = list(test_dir.rglob("*.kt"))
                java_files = list(test_dir.rglob("*.java"))
                file_count = len(kt_files) + len(java_files)

                if file_count > 0:
                    source_sets[source_set_name] = {
                        "path": relative_path,
                        "file_count": file_count,
                        "kotlin_files": len(kt_files),
                        "java_files": len(java_files),
                    }
                    total_files += file_count

        # Determine organization pattern
        organization = self._detect_test_organization(source_sets)

        return {
            "source_sets": source_sets,
            "total_test_files": total_files,
            "organization": organization,
        }

    def _detect_test_organization(
        self, source_sets: dict[str, dict[str, Any]]
    ) -> str:
        """Detect the test organization pattern used in the project.

        Args:
            source_sets: Dictionary of detected source sets.

        Returns:
            String describing the organization pattern:
            - "by_feature": Tests organized by feature/module
            - "by_layer": Tests organized by architectural layer
            - "flat": Flat test structure
            - "unknown": Could not determine pattern
        """
        if not source_sets:
            return "unknown"

        # Check for feature-based organization by looking for nested directories
        for source_set_info in source_sets.values():
            test_path = self.project_root / source_set_info["path"]
            if test_path.exists():
                # Count subdirectories (excluding hidden)
                subdirs = [
                    d for d in test_path.iterdir()
                    if d.is_dir() and not d.name.startswith(".")
                ]
                if len(subdirs) > 2:
                    # Check if subdirs have feature-like names
                    feature_keywords = [
                        "feature", "domain", "data", "presentation",
                        "ui", "repository", "usecase", "viewmodel"
                    ]
                    for subdir in subdirs:
                        subdir_name = subdir.name.lower()
                        for keyword in feature_keywords:
                            if keyword in subdir_name:
                                return "by_feature"
                    
                    # Check for layer-based organization
                    layer_names = {"domain", "data", "presentation", "ui", "core"}
                    subdir_names = {d.name.lower() for d in subdirs}
                    if len(subdir_names.intersection(layer_names)) >= 2:
                        return "by_layer"
                    
                    return "by_feature"

        return "flat"

    async def _scan_gradle_dependencies(self) -> dict[str, list[str]]:
        """Scan Gradle files for test dependencies.

        Returns:
            Dictionary mapping category to list of detected artifact patterns.
        """
        deps: dict[str, list[str]] = {
            "frameworks": [],
            "mocking": [],
            "assertions": [],
            "utilities": [],
            "coverage": [],
        }

        # Find all build.gradle.kts files
        gradle_files = list(self.project_root.rglob("build.gradle.kts"))
        gradle_files.extend(self.project_root.rglob("build.gradle"))

        for gradle_file in gradle_files:
            try:
                content = gradle_file.read_text(encoding="utf-8")
                self._parse_gradle_test_deps(content, deps)
            except Exception as e:
                logger.warning(f"Error reading {gradle_file}: {e}")

        return deps

    def _parse_gradle_test_deps(
        self, content: str, deps: dict[str, list[str]]
    ) -> None:
        """Parse test dependencies from Gradle file content.

        Args:
            content: Gradle file content.
            deps: Dictionary to populate with detected dependencies.
        """
        # Pattern for dependency declarations
        dep_pattern = re.compile(
            r'(?:testImplementation|androidTestImplementation|commonTestImplementation|'
            r'testCompileOnly|testRuntimeOnly)\s*\(\s*["\']([^"\']+)["\']',
            re.MULTILINE | re.IGNORECASE
        )

        for match in dep_pattern.finditer(content):
            artifact = match.group(1)
            self._categorize_test_dependency(artifact, deps)

        # Check for coverage plugins
        for tool, patterns in COVERAGE_TOOL_PATTERNS.items():
            for pattern in patterns:
                if pattern in content:
                    if tool not in deps["coverage"]:
                        deps["coverage"].append(tool)

    def _categorize_test_dependency(
        self, artifact: str, deps: dict[str, list[str]]
    ) -> None:
        """Categorize a test dependency into the appropriate category.

        Args:
            artifact: Maven artifact specification.
            deps: Dictionary to populate with categorized dependency.
        """
        artifact_lower = artifact.lower()

        # Check testing frameworks
        for framework, patterns in TESTING_FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in artifact_lower:
                    if framework not in deps["frameworks"]:
                        deps["frameworks"].append(framework)
                    return

        # Check mock libraries
        for library, info in MOCK_LIBRARY_PATTERNS.items():
            for pattern in info["patterns"]:
                if pattern.lower() in artifact_lower:
                    if library not in deps["mocking"]:
                        deps["mocking"].append(library)
                    return

        # Check assertion libraries
        for library, patterns in ASSERTION_LIBRARY_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in artifact_lower:
                    if library not in deps["assertions"]:
                        deps["assertions"].append(library)
                    return

        # Check testing utilities
        for utility, info in TESTING_UTILITY_PATTERNS.items():
            for pattern in info["patterns"]:
                if pattern.lower() in artifact_lower:
                    if utility not in deps["utilities"]:
                        deps["utilities"].append(utility)
                    return

    async def _scan_test_imports(self) -> dict[str, set[str]]:
        """Scan test files for import statements to detect frameworks.

        Returns:
            Dictionary mapping category to set of detected frameworks.
        """
        import_deps: dict[str, set[str]] = {
            "frameworks": set(),
            "mocking": set(),
            "assertions": set(),
            "utilities": set(),
        }

        # Find all test Kotlin files
        test_patterns = [
            "src/*Test*/kotlin/**/*.kt",
            "src/test/kotlin/**/*.kt",
            "src/test/java/**/*.java",
        ]

        test_files: list[Path] = []
        for pattern in test_patterns:
            test_files.extend(self.project_root.glob(pattern))

        for test_file in test_files:
            try:
                content = test_file.read_text(encoding="utf-8")
                self._parse_test_imports(content, import_deps)
            except Exception as e:
                logger.warning(f"Error reading {test_file}: {e}")

        return import_deps

    def _parse_test_imports(
        self, content: str, import_deps: dict[str, set[str]]
    ) -> None:
        """Parse import statements from test file content.

        Args:
            content: Test file content.
            import_deps: Dictionary to populate with detected frameworks.
        """
        import_pattern = re.compile(r'^import\s+([a-zA-Z0-9_.]+)', re.MULTILINE)

        for match in import_pattern.finditer(content):
            import_statement = match.group(1)

            for category, frameworks in IMPORT_PATTERNS.items():
                for framework, patterns in frameworks.items():
                    for pattern in patterns:
                        if import_statement.startswith(pattern):
                            import_deps[category].add(framework)
                            break

    def _detect_frameworks(
        self,
        gradle_deps: dict[str, list[str]],
        import_deps: dict[str, set[str]],
    ) -> dict[str, Any]:
        """Detect testing frameworks from dependencies and imports.

        Args:
            gradle_deps: Dependencies detected from Gradle files.
            import_deps: Frameworks detected from import statements.

        Returns:
            Dictionary with framework information.
        """
        detected = set(gradle_deps.get("frameworks", []))
        detected.update(import_deps.get("frameworks", set()))

        # Determine primary framework (preference order)
        primary = None
        preference_order = ["kotlin.test", "kotest", "junit5", "junit4"]
        for framework in preference_order:
            if framework in detected:
                primary = framework
                break

        if not primary and detected:
            primary = list(detected)[0]

        return {
            "primary": primary,
            "detected": list(detected),
        }

    def _detect_mocking_libraries(
        self,
        gradle_deps: dict[str, list[str]],
        import_deps: dict[str, set[str]],
    ) -> dict[str, Any]:
        """Detect mocking libraries from dependencies and imports.

        Args:
            gradle_deps: Dependencies detected from Gradle files.
            import_deps: Frameworks detected from import statements.

        Returns:
            Dictionary with mocking library information.
        """
        detected = set(gradle_deps.get("mocking", []))
        detected.update(import_deps.get("mocking", set()))

        if not detected:
            return {
                "library": None,
                "multiplatform": False,
            }

        # Prefer MockK for multiplatform projects
        library = None
        multiplatform = False
        if "mockk" in detected or "mockk-common" in detected:
            library = "mockk"
            multiplatform = True
        elif "mockito" in detected:
            library = "mockito"
            multiplatform = False

        return {
            "library": library,
            "multiplatform": multiplatform,
            "detected": list(detected),
        }

    def _detect_assertion_libraries(
        self,
        gradle_deps: dict[str, list[str]],
        import_deps: dict[str, set[str]],
    ) -> dict[str, Any]:
        """Detect assertion libraries from dependencies and imports.

        Args:
            gradle_deps: Dependencies detected from Gradle files.
            import_deps: Frameworks detected from import statements.

        Returns:
            Dictionary with assertion library information.
        """
        detected = set(gradle_deps.get("assertions", []))
        detected.update(import_deps.get("assertions", set()))

        return {
            "libraries": list(detected),
        }

    def _detect_utilities(
        self,
        gradle_deps: dict[str, list[str]],
        import_deps: dict[str, set[str]],
    ) -> dict[str, Any]:
        """Detect testing utilities from dependencies and imports.

        Args:
            gradle_deps: Dependencies detected from Gradle files.
            import_deps: Frameworks detected from import statements.

        Returns:
            Dictionary with utilities information.
        """
        detected = set(gradle_deps.get("utilities", []))
        detected.update(import_deps.get("utilities", set()))

        result: dict[str, Any] = {}

        if "turbine" in detected:
            result["flow_testing"] = "turbine"

        if "kotlinx-coroutines-test" in detected:
            result["coroutine_testing"] = "kotlinx-coroutines-test"

        if "androidx-test" in detected:
            result["android_testing"] = "androidx-test"

        result["detected"] = list(detected)

        return result

    async def _analyze_naming_patterns(self) -> dict[str, Any]:
        """Analyze test naming conventions used in the project.

        Returns:
            Dictionary with naming pattern information:
            {
                "style": str,
                "examples": list[str]
            }
        """
        # Naming pattern matchers
        patterns = {
            "should_when": re.compile(
                r'(?:fun\s+)?[`"]?should[_\s].*[_\s]when[_\s].*[`"]?',
                re.IGNORECASE
            ),
            "test_prefix": re.compile(
                r'(?:fun\s+)?test[A-Z_]',
                re.IGNORECASE
            ),
            "given_when_then": re.compile(
                r'(?:fun\s+)?[`"]?given[_\s].*[_\s]when[_\s].*[_\s]then[_\s].*[`"]?',
                re.IGNORECASE
            ),
            "backtick_descriptive": re.compile(
                r'fun\s+`[^`]+`'
            ),
            "suffix_test": re.compile(
                r'(?:fun\s+)?[a-z][a-zA-Z]*Test\s*\(',
                re.IGNORECASE
            ),
        }

        pattern_counts: dict[str, int] = {name: 0 for name in patterns}
        examples: dict[str, list[str]] = {name: [] for name in patterns}

        # Find test files
        test_patterns = [
            "src/*Test*/kotlin/**/*.kt",
            "src/test/kotlin/**/*.kt",
        ]

        test_files: list[Path] = []
        for pattern in test_patterns:
            test_files.extend(self.project_root.glob(pattern))

        for test_file in test_files:
            try:
                content = test_file.read_text(encoding="utf-8")
                # Extract function names
                func_pattern = re.compile(r'fun\s+(`[^`]+`|[a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
                
                for func_match in func_pattern.finditer(content):
                    func_name = func_match.group(1)
                    func_line = func_match.group(0)

                    for pattern_name, regex in patterns.items():
                        if regex.search(func_line) or regex.search(func_name):
                            pattern_counts[pattern_name] += 1
                            if len(examples[pattern_name]) < 3:
                                # Clean up the example
                                clean_name = func_name.strip('`')
                                examples[pattern_name].append(clean_name)
                            break

            except Exception as e:
                logger.warning(f"Error analyzing naming patterns in {test_file}: {e}")

        # Determine primary style
        primary_style = None
        max_count = 0
        for pattern_name, count in pattern_counts.items():
            if count > max_count:
                max_count = count
                primary_style = pattern_name

        # Get examples for primary style
        primary_examples = examples.get(primary_style, []) if primary_style else []

        return {
            "style": primary_style,
            "examples": primary_examples,
            "pattern_distribution": {
                name: count for name, count in pattern_counts.items() if count > 0
            },
        }

    async def _detect_coverage_config(self) -> dict[str, Any]:
        """Detect coverage configuration in the project.

        Returns:
            Dictionary with coverage tool information:
            {
                "tool": str | None,
                "configured": bool
            }
        """
        detected_tool = None
        configured = False

        # Check build.gradle.kts files for coverage plugins
        gradle_files = list(self.project_root.rglob("build.gradle.kts"))
        gradle_files.extend(self.project_root.rglob("build.gradle"))

        for gradle_file in gradle_files:
            try:
                content = gradle_file.read_text(encoding="utf-8")

                # Check for Kover
                kover_patterns = [
                    r'id\s*\(\s*["\']org\.jetbrains\.kotlinx\.kover["\']\s*\)',
                    r'kotlin\s*\(\s*["\']kover["\']\s*\)',
                    r'kover\s*\{',
                    r'koverReport\s*\{',
                ]
                for pattern in kover_patterns:
                    if re.search(pattern, content):
                        detected_tool = "kover"
                        configured = True
                        break

                if detected_tool:
                    break

                # Check for JaCoCo
                jacoco_patterns = [
                    r'id\s*\(\s*["\']jacoco["\']\s*\)',
                    r'apply\s*plugin:\s*["\']jacoco["\']',
                    r'jacoco\s*\{',
                    r'jacocoTestReport\s*\{',
                ]
                for pattern in jacoco_patterns:
                    if re.search(pattern, content):
                        detected_tool = "jacoco"
                        configured = True
                        break

            except Exception as e:
                logger.warning(f"Error reading {gradle_file} for coverage config: {e}")

        return {
            "tool": detected_tool,
            "configured": configured,
        }

    def get_test_files_for_source_set(
        self, source_set: str
    ) -> list[Path]:
        """Get all test files for a specific source set.

        Args:
            source_set: Name of the source set (e.g., "commonTest", "androidTest").

        Returns:
            List of paths to test files.

        Example:
            >>> files = analyzer.get_test_files_for_source_set("commonTest")
            >>> for f in files:
            ...     print(f.name)
        """
        source_set_paths = {
            "commonTest": "src/commonTest/kotlin",
            "androidTest": "src/androidTest/kotlin",
            "androidUnitTest": "src/androidUnitTest/kotlin",
            "iosTest": "src/iosTest/kotlin",
            "jvmTest": "src/jvmTest/kotlin",
            "jsTest": "src/jsTest/kotlin",
            "test": "src/test/kotlin",
        }

        path = source_set_paths.get(source_set)
        if not path:
            return []

        test_dir = self.project_root / path
        if not test_dir.exists():
            return []

        return list(test_dir.rglob("*.kt"))

    def is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file.

        Args:
            file_path: Path to check.

        Returns:
            True if the file is in a test source set.

        Example:
            >>> is_test = analyzer.is_test_file(Path("src/commonTest/kotlin/MyTest.kt"))
            >>> print(is_test)  # True
        """
        path_str = str(file_path)
        test_indicators = [
            "/test/",
            "/Test/",
            "Test.kt",
            "Tests.kt",
            "Spec.kt",
        ]
        return any(indicator in path_str for indicator in test_indicators)
