"""Architecture analyzer for detecting design patterns and project structure.

This module provides the ArchitectureAnalyzer class that detects architectural
patterns, design patterns, module roles, and layer organization in KMP/CMP projects.
"""

import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base import AnalysisResult, BaseAnalyzer
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PatternEvidence:
    """Evidence collected for a detected pattern.

    Attributes:
        pattern_name: Name of the detected pattern.
        indicators: List of indicators found (class names, files, etc.).
        confidence: Confidence score for this pattern (0.0-1.0).
    """

    pattern_name: str
    indicators: list[str] = field(default_factory=list)
    confidence: float = 0.0


class ArchitectureAnalyzer(BaseAnalyzer):
    """Analyzer for detecting architectural patterns and design patterns.

    Analyzes KMP/CMP projects to detect:
    - Design patterns (MVVM, MVI, Clean Architecture, Repository)
    - Module roles (app, core, feature, data, domain, ui)
    - Layer organization (presentation, domain, data)
    - Pattern evidence and confidence scores

    This analyzer produces structured data suitable for memory generation
    and project onboarding documentation.

    Attributes:
        project_root: Path to the root directory of the project being analyzed.

    Example:
        >>> analyzer = ArchitectureAnalyzer(Path("/path/to/kmp-project"))
        >>> result = await analyzer.analyze()
        >>> print(result.data["primary_pattern"])
        'mvvm'
    """

    # Pattern detection configurations
    MVVM_INDICATORS = {
        "viewmodel_suffix": re.compile(r"class\s+(\w+ViewModel)", re.MULTILINE),
        "state_suffix": re.compile(
            r"(?:data\s+)?class\s+(\w+(?:UiState|State))\s*[({]", re.MULTILINE
        ),
        "stateflow_usage": re.compile(
            r"(?:StateFlow|MutableStateFlow|stateIn)", re.MULTILINE
        ),
    }

    MVI_INDICATORS = {
        "intent_class": re.compile(
            r"(?:sealed\s+)?(?:class|interface)\s+(\w*(?:Intent|Action)\w*)", re.MULTILINE
        ),
        "effect_class": re.compile(
            r"(?:sealed\s+)?(?:class|interface)\s+(\w*(?:Effect|SideEffect)\w*)",
            re.MULTILINE,
        ),
        "reducer_class": re.compile(
            r"(?:class|fun)\s+(\w*Reducer\w*)", re.MULTILINE
        ),
    }

    CLEAN_ARCHITECTURE_INDICATORS = {
        "usecase_class": re.compile(
            r"class\s+(\w+UseCase)", re.MULTILINE
        ),
        "repository_interface": re.compile(
            r"interface\s+(\w+Repository)", re.MULTILINE
        ),
        "repository_impl": re.compile(
            r"class\s+(\w+Repository(?:Impl)?)\s*[:(]", re.MULTILINE
        ),
        "datasource_class": re.compile(
            r"(?:class|interface)\s+(\w+DataSource)", re.MULTILINE
        ),
        "mapper_class": re.compile(
            r"(?:class|object)\s+(\w+Mapper)", re.MULTILINE
        ),
    }

    REPOSITORY_INDICATORS = {
        "repository_interface": re.compile(
            r"interface\s+(\w+Repository)", re.MULTILINE
        ),
        "repository_impl": re.compile(
            r"class\s+(\w+Repository(?:Impl)?)", re.MULTILINE
        ),
        "dao_class": re.compile(
            r"(?:@Dao\s+)?(?:interface|abstract\s+class)\s+(\w+Dao)", re.MULTILINE
        ),
    }

    # Module role patterns
    MODULE_ROLE_PATTERNS = {
        "application": [
            re.compile(r"^:?app$"),
            re.compile(r"^:?application$"),
        ],
        "shared": [
            re.compile(r"^:?core$"),
            re.compile(r"^:?shared$"),
            re.compile(r"^:?common$"),
        ],
        "feature": [
            re.compile(r"^:?feature[:-]"),
            re.compile(r"^:?features?/"),
        ],
        "data": [
            re.compile(r"^:?data$"),
            re.compile(r"^:?data[:-]"),
        ],
        "domain": [
            re.compile(r"^:?domain$"),
            re.compile(r"^:?domain[:-]"),
        ],
        "ui": [
            re.compile(r"^:?ui$"),
            re.compile(r"^:?ui[:-]"),
            re.compile(r"^:?design[:-]?system$"),
        ],
    }

    # Layer detection patterns (package/directory names)
    LAYER_PATTERNS = {
        "presentation": ["presentation", "ui", "view", "screen", "compose"],
        "domain": ["domain", "usecase", "usecases", "interactor", "interactors"],
        "data": ["data", "repository", "repositories", "network", "database", "api", "local", "remote"],
    }

    @property
    def name(self) -> str:
        """Get the name of this analyzer.

        Returns:
            The string "architecture" identifying this analyzer.
        """
        return "architecture"

    def get_memory_category(self) -> str:
        """Get the memory category for storing analysis results.

        Returns:
            The string "architecture" for categorizing results.
        """
        return "architecture"

    async def analyze(self) -> AnalysisResult:
        """Analyze the project architecture and detect patterns.

        Performs comprehensive analysis of the project including:
        - Detecting design patterns (MVVM, MVI, Clean Architecture, Repository)
        - Identifying module roles
        - Detecting layer organization
        - Collecting evidence for detected patterns

        Returns:
            AnalysisResult containing architecture data with the following keys:
                - detected_patterns: List of detected pattern names
                - primary_pattern: Most likely primary architectural pattern
                - confidence: Overall confidence score
                - module_roles: Dictionary mapping module names to roles
                - layers: Dictionary mapping layer names to paths
                - evidence: Dictionary mapping pattern names to evidence lists

        Raises:
            No exceptions are raised; errors are captured in the result.

        Example:
            >>> result = await analyzer.analyze()
            >>> if result.success:
            ...     print(f"Primary pattern: {result.data['primary_pattern']}")
        """
        logger.info(f"Analyzing architecture at: {self.project_root}")

        errors: list[str] = []
        warnings: list[str] = []

        try:
            # Find all Kotlin source files
            kotlin_files = await self._find_kotlin_files()
            logger.debug(f"Found {len(kotlin_files)} Kotlin files")

            if not kotlin_files:
                warnings.append("No Kotlin source files found")
                return self._create_result_with_warnings(
                    self._create_minimal_result(),
                    warnings,
                )

            # Detect patterns
            pattern_evidence = await self._detect_patterns(kotlin_files)

            # Determine detected patterns and primary pattern
            detected_patterns = [
                pe.pattern_name for pe in pattern_evidence if pe.confidence >= 0.3
            ]
            primary_pattern = self._determine_primary_pattern(pattern_evidence)
            overall_confidence = self._calculate_overall_confidence(pattern_evidence)

            # Detect module roles
            module_roles = await self._detect_module_roles()

            # Detect layers
            layers = await self._detect_layers(kotlin_files)

            # Build evidence dictionary
            evidence = {
                pe.pattern_name: pe.indicators
                for pe in pattern_evidence
                if pe.indicators
            }

            result_data = {
                "detected_patterns": detected_patterns,
                "primary_pattern": primary_pattern,
                "confidence": overall_confidence,
                "module_roles": module_roles,
                "layers": layers,
                "evidence": evidence,
            }

            if warnings:
                return self._create_result_with_warnings(result_data, warnings)

            return self._create_success_result(result_data)

        except Exception as e:
            logger.error(f"Architecture analysis failed: {e}")
            errors.append(f"Architecture analysis failed: {e}")
            return self._create_error_result(errors, warnings)

    async def _find_kotlin_files(self) -> list[Path]:
        """Find all Kotlin source files in the project.

        Returns:
            List of paths to Kotlin files.
        """
        kotlin_files: list[Path] = []

        # Common source directories to scan
        source_patterns = [
            "src/**/kotlin/**/*.kt",
            "src/**/*.kt",
            "app/src/**/*.kt",
            "**/src/main/**/*.kt",
            "**/src/commonMain/**/*.kt",
            "**/src/androidMain/**/*.kt",
            "**/src/iosMain/**/*.kt",
        ]

        for pattern in source_patterns:
            kotlin_files.extend(self.project_root.glob(pattern))

        # Remove duplicates while preserving order
        seen: set[Path] = set()
        unique_files: list[Path] = []
        for f in kotlin_files:
            if f not in seen and f.is_file():
                seen.add(f)
                unique_files.append(f)

        return unique_files

    async def _detect_patterns(
        self, kotlin_files: list[Path]
    ) -> list[PatternEvidence]:
        """Detect architectural patterns in the codebase.

        Args:
            kotlin_files: List of Kotlin source files to analyze.

        Returns:
            List of PatternEvidence objects for each detected pattern.
        """
        # Read all files concurrently
        file_contents = await self._read_files_async(kotlin_files)

        # Detect each pattern
        mvvm_evidence = self._detect_mvvm(file_contents)
        mvi_evidence = self._detect_mvi(file_contents)
        clean_arch_evidence = self._detect_clean_architecture(file_contents)
        repository_evidence = self._detect_repository_pattern(file_contents)

        return [mvvm_evidence, mvi_evidence, clean_arch_evidence, repository_evidence]

    async def _read_files_async(
        self, files: list[Path]
    ) -> dict[Path, str]:
        """Read multiple files asynchronously.

        Args:
            files: List of file paths to read.

        Returns:
            Dictionary mapping file paths to their contents.
        """

        async def read_file(path: Path) -> tuple[Path, str]:
            try:
                loop = asyncio.get_event_loop()
                content = await loop.run_in_executor(
                    None, lambda: path.read_text(encoding="utf-8")
                )
                return (path, content)
            except Exception as e:
                logger.debug(f"Failed to read {path}: {e}")
                return (path, "")

        results = await asyncio.gather(*[read_file(f) for f in files])
        return dict(results)

    def _detect_mvvm(self, file_contents: dict[Path, str]) -> PatternEvidence:
        """Detect MVVM pattern indicators.

        Args:
            file_contents: Dictionary of file paths to contents.

        Returns:
            PatternEvidence for MVVM pattern.
        """
        indicators: list[str] = []
        viewmodel_count = 0
        state_count = 0
        stateflow_found = False

        for path, content in file_contents.items():
            # Check for ViewModels
            viewmodel_matches = self.MVVM_INDICATORS["viewmodel_suffix"].findall(
                content
            )
            for match in viewmodel_matches:
                indicators.append(f"ViewModel: {match}")
                viewmodel_count += 1

            # Check for State classes
            state_matches = self.MVVM_INDICATORS["state_suffix"].findall(content)
            for match in state_matches:
                indicators.append(f"State: {match}")
                state_count += 1

            # Check for StateFlow usage
            if self.MVVM_INDICATORS["stateflow_usage"].search(content):
                stateflow_found = True

        # Calculate confidence based on indicators
        confidence = 0.0
        if viewmodel_count > 0:
            confidence += min(0.4, viewmodel_count * 0.1)
        if state_count > 0:
            confidence += min(0.3, state_count * 0.075)
        if stateflow_found:
            confidence += 0.2
        if viewmodel_count > 0 and state_count > 0:
            confidence += 0.1  # Bonus for having both

        confidence = min(1.0, confidence)

        return PatternEvidence(
            pattern_name="mvvm",
            indicators=indicators[:20],  # Limit to 20 most relevant
            confidence=round(confidence, 2),
        )

    def _detect_mvi(self, file_contents: dict[Path, str]) -> PatternEvidence:
        """Detect MVI pattern indicators.

        Args:
            file_contents: Dictionary of file paths to contents.

        Returns:
            PatternEvidence for MVI pattern.
        """
        indicators: list[str] = []
        intent_count = 0
        effect_count = 0
        reducer_count = 0

        for path, content in file_contents.items():
            # Check for Intent/Action classes
            intent_matches = self.MVI_INDICATORS["intent_class"].findall(content)
            for match in intent_matches:
                # Filter out common false positives
                if not any(
                    fp in match.lower()
                    for fp in ["pendingintent", "intentfilter", "intentional"]
                ):
                    indicators.append(f"Intent/Action: {match}")
                    intent_count += 1

            # Check for Effect/SideEffect classes
            effect_matches = self.MVI_INDICATORS["effect_class"].findall(content)
            for match in effect_matches:
                indicators.append(f"Effect: {match}")
                effect_count += 1

            # Check for Reducer
            reducer_matches = self.MVI_INDICATORS["reducer_class"].findall(content)
            for match in reducer_matches:
                indicators.append(f"Reducer: {match}")
                reducer_count += 1

        # Calculate confidence
        confidence = 0.0
        if intent_count > 0:
            confidence += min(0.35, intent_count * 0.1)
        if effect_count > 0:
            confidence += min(0.25, effect_count * 0.1)
        if reducer_count > 0:
            confidence += min(0.3, reducer_count * 0.15)
        if intent_count > 0 and effect_count > 0 and reducer_count > 0:
            confidence += 0.1  # Bonus for complete MVI

        confidence = min(1.0, confidence)

        return PatternEvidence(
            pattern_name="mvi",
            indicators=indicators[:20],
            confidence=round(confidence, 2),
        )

    def _detect_clean_architecture(
        self, file_contents: dict[Path, str]
    ) -> PatternEvidence:
        """Detect Clean Architecture pattern indicators.

        Args:
            file_contents: Dictionary of file paths to contents.

        Returns:
            PatternEvidence for Clean Architecture pattern.
        """
        indicators: list[str] = []
        usecase_count = 0
        repository_count = 0
        datasource_count = 0
        mapper_count = 0

        for path, content in file_contents.items():
            # Check for UseCases
            usecase_matches = self.CLEAN_ARCHITECTURE_INDICATORS[
                "usecase_class"
            ].findall(content)
            for match in usecase_matches:
                indicators.append(f"UseCase: {match}")
                usecase_count += 1

            # Check for Repositories (interface)
            repo_interface_matches = self.CLEAN_ARCHITECTURE_INDICATORS[
                "repository_interface"
            ].findall(content)
            for match in repo_interface_matches:
                indicators.append(f"Repository Interface: {match}")
                repository_count += 1

            # Check for Repository implementations
            repo_impl_matches = self.CLEAN_ARCHITECTURE_INDICATORS[
                "repository_impl"
            ].findall(content)
            for match in repo_impl_matches:
                if match not in [m for m in indicators if "Repository" in m]:
                    indicators.append(f"Repository Impl: {match}")
                    repository_count += 1

            # Check for DataSources
            datasource_matches = self.CLEAN_ARCHITECTURE_INDICATORS[
                "datasource_class"
            ].findall(content)
            for match in datasource_matches:
                indicators.append(f"DataSource: {match}")
                datasource_count += 1

            # Check for Mappers
            mapper_matches = self.CLEAN_ARCHITECTURE_INDICATORS["mapper_class"].findall(
                content
            )
            for match in mapper_matches:
                indicators.append(f"Mapper: {match}")
                mapper_count += 1

        # Calculate confidence
        confidence = 0.0
        if usecase_count > 0:
            confidence += min(0.35, usecase_count * 0.08)
        if repository_count > 0:
            confidence += min(0.25, repository_count * 0.05)
        if datasource_count > 0:
            confidence += min(0.2, datasource_count * 0.05)
        if mapper_count > 0:
            confidence += min(0.1, mapper_count * 0.03)

        # Bonus for having multiple layers represented
        layers_found = sum(
            [
                usecase_count > 0,
                repository_count > 0,
                datasource_count > 0,
            ]
        )
        if layers_found >= 2:
            confidence += 0.1

        confidence = min(1.0, confidence)

        return PatternEvidence(
            pattern_name="clean_architecture",
            indicators=indicators[:25],
            confidence=round(confidence, 2),
        )

    def _detect_repository_pattern(
        self, file_contents: dict[Path, str]
    ) -> PatternEvidence:
        """Detect Repository pattern indicators.

        Args:
            file_contents: Dictionary of file paths to contents.

        Returns:
            PatternEvidence for Repository pattern.
        """
        indicators: list[str] = []
        repository_interface_count = 0
        repository_impl_count = 0
        dao_count = 0

        for path, content in file_contents.items():
            # Check for Repository interfaces
            repo_interface_matches = self.REPOSITORY_INDICATORS[
                "repository_interface"
            ].findall(content)
            for match in repo_interface_matches:
                indicators.append(f"Repository Interface: {match}")
                repository_interface_count += 1

            # Check for Repository implementations
            repo_impl_matches = self.REPOSITORY_INDICATORS["repository_impl"].findall(
                content
            )
            for match in repo_impl_matches:
                # Avoid duplicates from interface matches
                if "Impl" in match or match not in [
                    i.split(": ")[1]
                    for i in indicators
                    if "Interface" in i
                ]:
                    indicators.append(f"Repository Impl: {match}")
                    repository_impl_count += 1

            # Check for DAOs
            dao_matches = self.REPOSITORY_INDICATORS["dao_class"].findall(content)
            for match in dao_matches:
                indicators.append(f"DAO: {match}")
                dao_count += 1

        # Calculate confidence
        confidence = 0.0
        if repository_interface_count > 0:
            confidence += min(0.4, repository_interface_count * 0.1)
        if repository_impl_count > 0:
            confidence += min(0.3, repository_impl_count * 0.08)
        if dao_count > 0:
            confidence += min(0.2, dao_count * 0.1)

        # Bonus for having interface + implementation pairs
        if repository_interface_count > 0 and repository_impl_count > 0:
            confidence += 0.1

        confidence = min(1.0, confidence)

        return PatternEvidence(
            pattern_name="repository",
            indicators=indicators[:20],
            confidence=round(confidence, 2),
        )

    def _determine_primary_pattern(
        self, pattern_evidence: list[PatternEvidence]
    ) -> str | None:
        """Determine the primary architectural pattern.

        Args:
            pattern_evidence: List of pattern evidence objects.

        Returns:
            Name of the primary pattern, or None if no clear pattern.
        """
        if not pattern_evidence:
            return None

        # Sort by confidence
        sorted_evidence = sorted(
            pattern_evidence, key=lambda x: x.confidence, reverse=True
        )

        # Return highest confidence pattern if above threshold
        if sorted_evidence[0].confidence >= 0.3:
            return sorted_evidence[0].pattern_name

        return None

    def _calculate_overall_confidence(
        self, pattern_evidence: list[PatternEvidence]
    ) -> float:
        """Calculate overall architecture detection confidence.

        Args:
            pattern_evidence: List of pattern evidence objects.

        Returns:
            Overall confidence score (0.0-1.0).
        """
        if not pattern_evidence:
            return 0.0

        # Use the highest confidence among detected patterns
        max_confidence = max(pe.confidence for pe in pattern_evidence)
        return round(max_confidence, 2)

    async def _detect_module_roles(self) -> dict[str, str]:
        """Detect roles of modules in the project.

        Returns:
            Dictionary mapping module names to their roles.
        """
        module_roles: dict[str, str] = {}

        # Look for settings.gradle.kts or settings.gradle
        settings_files = list(self.project_root.glob("settings.gradle*"))
        modules: list[str] = []

        for settings_file in settings_files:
            try:
                content = settings_file.read_text(encoding="utf-8")
                # Extract include statements
                include_pattern = re.compile(
                    r'include\s*\(\s*["\']([^"\']+)["\']', re.MULTILINE
                )
                modules.extend(include_pattern.findall(content))

                # Also check for includeBuild
                include_build_pattern = re.compile(
                    r'includeBuild\s*\(\s*["\']([^"\']+)["\']', re.MULTILINE
                )
                modules.extend(include_build_pattern.findall(content))
            except Exception as e:
                logger.debug(f"Failed to parse settings file {settings_file}: {e}")

        # Also detect modules from directory structure
        for subdir in self.project_root.iterdir():
            if subdir.is_dir() and (subdir / "build.gradle.kts").exists():
                modules.append(subdir.name)
            elif subdir.is_dir() and (subdir / "build.gradle").exists():
                modules.append(subdir.name)

        # Classify each module
        for module in set(modules):
            role = self._classify_module_role(module)
            if role:
                module_roles[module] = role

        return module_roles

    def _classify_module_role(self, module_name: str) -> str | None:
        """Classify a module's role based on its name.

        Args:
            module_name: Name of the module (may include : prefix).

        Returns:
            Role name or None if no match.
        """
        for role, patterns in self.MODULE_ROLE_PATTERNS.items():
            for pattern in patterns:
                if pattern.match(module_name):
                    return role

        return None

    async def _detect_layers(
        self, kotlin_files: list[Path]
    ) -> dict[str, list[str]]:
        """Detect layer organization from package/directory structure.

        Args:
            kotlin_files: List of Kotlin source files.

        Returns:
            Dictionary mapping layer names to list of paths.
        """
        layers: dict[str, list[str]] = {
            "presentation": [],
            "domain": [],
            "data": [],
        }

        # Track unique paths per layer
        seen_paths: dict[str, set[str]] = {
            "presentation": set(),
            "domain": set(),
            "data": set(),
        }

        for kotlin_file in kotlin_files:
            relative_path = kotlin_file.relative_to(self.project_root)
            path_str = str(relative_path)
            path_parts = path_str.lower().split("/")

            # Check each layer pattern
            for layer, patterns in self.LAYER_PATTERNS.items():
                for pattern in patterns:
                    if pattern in path_parts:
                        # Extract meaningful path segment
                        layer_path = self._extract_layer_path(path_str, pattern)
                        if layer_path and layer_path not in seen_paths[layer]:
                            seen_paths[layer].add(layer_path)
                            layers[layer].append(layer_path)
                        break

        # Sort and limit results
        for layer in layers:
            layers[layer] = sorted(set(layers[layer]))[:20]

        return layers

    def _extract_layer_path(self, full_path: str, pattern: str) -> str | None:
        """Extract a meaningful layer path from a full file path.

        Args:
            full_path: Full path to the file.
            pattern: The layer pattern that matched.

        Returns:
            Extracted layer path or None.
        """
        parts = full_path.split("/")
        pattern_lower = pattern.lower()

        for i, part in enumerate(parts):
            if pattern_lower in part.lower():
                # Return path up to and including the layer directory
                return "/".join(parts[: i + 1])

        return None

    def _create_minimal_result(self) -> dict[str, Any]:
        """Create a minimal result when no analysis can be performed.

        Returns:
            Dictionary with empty/default values.
        """
        return {
            "detected_patterns": [],
            "primary_pattern": None,
            "confidence": 0.0,
            "module_roles": {},
            "layers": {
                "presentation": [],
                "domain": [],
                "data": [],
            },
            "evidence": {},
        }

    def _create_result_with_warnings(
        self,
        data: dict[str, Any],
        warnings: list[str],
    ) -> AnalysisResult:
        """Create a successful result with warnings.

        Args:
            data: Analysis result data.
            warnings: List of warning messages.

        Returns:
            AnalysisResult with warnings.
        """
        return AnalysisResult(
            analyzer_name=self.name,
            success=True,
            data=data,
            errors=[],
            warnings=warnings,
        )
