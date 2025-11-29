"""Pattern analyzer for detecting coding conventions and patterns in Kotlin projects.

This module provides the PatternAnalyzer class for detecting naming conventions,
code style preferences, package structure patterns, and common Kotlin patterns
used throughout a codebase.
"""

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .base import AnalysisResult, BaseAnalyzer

logger = logging.getLogger(__name__)


class PatternAnalyzer(BaseAnalyzer):
    """Analyzer for detecting coding patterns and conventions in Kotlin projects.

    Analyzes Kotlin source files to detect:
    - Naming conventions (classes, functions, variables, files, packages)
    - Code style (indentation, line length, import organization, brace style)
    - Package structure (organization style, common package names)
    - Kotlin patterns (data classes, sealed classes, extension functions,
      coroutines, object declarations)

    The analyzer samples files from different directories to provide
    a statistical overview of the codebase conventions.

    Attributes:
        project_root: Path to the root directory of the project being analyzed.

    Example:
        >>> analyzer = PatternAnalyzer(Path("/path/to/kotlin-project"))
        >>> result = await analyzer.analyze()
        >>> print(result.data["naming_conventions"]["classes"])
        "PascalCase"
        >>> print(result.data["kotlin_patterns"]["data_classes"]["count"])
        45
    """

    # Maximum number of files to sample for analysis
    MAX_SAMPLE_FILES = 25

    # Regex patterns for detecting naming conventions
    CLASS_NAME_PATTERN = re.compile(r'^\s*(?:data\s+|sealed\s+|abstract\s+|open\s+|inner\s+|enum\s+)*class\s+(\w+)', re.MULTILINE)
    INTERFACE_NAME_PATTERN = re.compile(r'^\s*(?:fun\s+)?interface\s+(\w+)', re.MULTILINE)
    OBJECT_NAME_PATTERN = re.compile(r'^\s*(?:companion\s+)?object\s+(\w+)', re.MULTILINE)
    FUNCTION_NAME_PATTERN = re.compile(r'^\s*(?:private\s+|protected\s+|internal\s+|public\s+|override\s+|suspend\s+|inline\s+|operator\s+)*fun\s+(?:<[^>]+>\s+)?(\w+)', re.MULTILINE)
    VARIABLE_NAME_PATTERN = re.compile(r'^\s*(?:private\s+|protected\s+|internal\s+|public\s+|override\s+|const\s+|lateinit\s+)*(?:val|var)\s+(\w+)', re.MULTILINE)
    CONST_PATTERN = re.compile(r'^\s*(?:private\s+|internal\s+|public\s+)*const\s+val\s+(\w+)', re.MULTILINE)
    PACKAGE_PATTERN = re.compile(r'^package\s+([\w.]+)', re.MULTILINE)

    # Patterns for detecting Kotlin-specific constructs
    DATA_CLASS_PATTERN = re.compile(r'^\s*data\s+class\s+\w+', re.MULTILINE)
    SEALED_CLASS_PATTERN = re.compile(r'^\s*sealed\s+(?:class|interface)\s+\w+', re.MULTILINE)
    EXTENSION_FUNCTION_PATTERN = re.compile(r'^\s*(?:private\s+|internal\s+|public\s+)?(?:inline\s+)?(?:suspend\s+)?fun\s+(?:<[^>]+>\s+)?[\w<>?,\s]+\.(\w+)\s*\(', re.MULTILINE)
    SUSPEND_FUNCTION_PATTERN = re.compile(r'^\s*(?:private\s+|protected\s+|internal\s+|public\s+|override\s+)?suspend\s+fun\s+', re.MULTILINE)
    FLOW_USAGE_PATTERN = re.compile(r'\b(?:Flow|MutableStateFlow|StateFlow|SharedFlow|MutableSharedFlow|flow\s*\{|channelFlow\s*\{|callbackFlow\s*\{)\b')
    OBJECT_DECLARATION_PATTERN = re.compile(r'^\s*(?!companion\s+)object\s+(\w+)\s*(?::|{)', re.MULTILINE)
    COMPANION_OBJECT_PATTERN = re.compile(r'^\s*companion\s+object', re.MULTILINE)

    # Factory and builder patterns
    FACTORY_PATTERN = re.compile(r'(?:fun\s+\w*[Ff]actory|object\s+\w*Factory|class\s+\w+Factory)', re.MULTILINE)
    BUILDER_PATTERN = re.compile(r'(?:class\s+\w+Builder|fun\s+\w*[Bb]uilder|\.build\(\))', re.MULTILINE)

    @property
    def name(self) -> str:
        """Get the name of this analyzer.

        Returns:
            Human-readable name identifying this analyzer.
        """
        return "patterns"

    def get_memory_category(self) -> str:
        """Get the memory category for storing analysis results.

        Returns:
            String identifier for the category under which analysis
            results should be stored in the memory system.
        """
        return "coding_patterns"

    async def analyze(self) -> AnalysisResult:
        """Analyze coding patterns and conventions in the project.

        Samples Kotlin files from different directories and analyzes them
        to detect naming conventions, code style, package structure,
        and common Kotlin patterns.

        Returns:
            AnalysisResult containing:
            {
                "naming_conventions": {...},
                "code_style": {...},
                "package_structure": {...},
                "kotlin_patterns": {...},
                "samples_analyzed": int
            }

        Example:
            >>> result = await analyzer.analyze()
            >>> print(result.data["naming_conventions"]["classes"])
            "PascalCase"
        """
        try:
            logger.info(f"Analyzing coding patterns for project: {self.project_root}")
            warnings: list[str] = []

            # Find and sample Kotlin files
            kotlin_files = self._find_kotlin_files()
            if not kotlin_files:
                logger.warning("No Kotlin files found in project")
                warnings.append("No Kotlin files found in this project")
                return AnalysisResult(
                    analyzer_name=self.name,
                    success=True,
                    data={
                        "naming_conventions": {},
                        "code_style": {},
                        "package_structure": {},
                        "kotlin_patterns": {},
                        "samples_analyzed": 0,
                    },
                    warnings=warnings,
                )

            # Sample files from different directories for diversity
            sampled_files = self._sample_files(kotlin_files)
            logger.info(f"Sampling {len(sampled_files)} Kotlin files for analysis")

            # Read and analyze file contents
            file_contents: list[tuple[Path, str]] = []
            for file_path in sampled_files:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    file_contents.append((file_path, content))
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")
                    warnings.append(f"Failed to read file: {file_path.name}")

            if not file_contents:
                warnings.append("Could not read any Kotlin files")
                return AnalysisResult(
                    analyzer_name=self.name,
                    success=True,
                    data={
                        "naming_conventions": {},
                        "code_style": {},
                        "package_structure": {},
                        "kotlin_patterns": {},
                        "samples_analyzed": 0,
                    },
                    warnings=warnings,
                )

            # Analyze patterns
            naming_conventions = self._analyze_naming_conventions(file_contents)
            code_style = self._analyze_code_style(file_contents)
            package_structure = self._analyze_package_structure(file_contents, kotlin_files)
            kotlin_patterns = self._analyze_kotlin_patterns(file_contents)

            result_data = {
                "naming_conventions": naming_conventions,
                "code_style": code_style,
                "package_structure": package_structure,
                "kotlin_patterns": kotlin_patterns,
                "samples_analyzed": len(file_contents),
            }

            return AnalysisResult(
                analyzer_name=self.name,
                success=True,
                data=result_data,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}", exc_info=True)
            return self._create_error_result(
                errors=[f"Pattern analysis failed: {str(e)}"],
            )

    def _find_kotlin_files(self) -> list[Path]:
        """Find all Kotlin files in the project.

        Returns:
            List of paths to Kotlin files.
        """
        kotlin_files: list[Path] = []

        # Search in common source directories
        search_dirs = [
            self.project_root / "src",
            self.project_root / "app" / "src",
            self.project_root / "shared" / "src",
            self.project_root / "composeApp" / "src",
        ]

        for search_dir in search_dirs:
            if search_dir.exists():
                kotlin_files.extend(search_dir.rglob("*.kt"))

        # Also search project root if no files found
        if not kotlin_files:
            kotlin_files = list(self.project_root.rglob("*.kt"))

        # Filter out test files and build directories
        filtered_files = [
            f for f in kotlin_files
            if "build" not in f.parts
            and ".gradle" not in str(f)
            and "Test" not in f.name
            and "test" not in f.parts
        ]

        return filtered_files

    def _sample_files(self, files: list[Path]) -> list[Path]:
        """Sample files from different directories for diverse analysis.

        Attempts to get files from different packages/directories to ensure
        the analysis represents the entire codebase.

        Args:
            files: List of all Kotlin files found.

        Returns:
            Sampled list of files (up to MAX_SAMPLE_FILES).
        """
        if len(files) <= self.MAX_SAMPLE_FILES:
            return files

        # Group files by their parent directory
        dir_files: dict[Path, list[Path]] = {}
        for f in files:
            parent = f.parent
            if parent not in dir_files:
                dir_files[parent] = []
            dir_files[parent].append(f)

        # Sample from each directory proportionally
        sampled: list[Path] = []
        dirs = list(dir_files.keys())

        # First pass: take at least one file from each directory
        for d in dirs:
            if len(sampled) >= self.MAX_SAMPLE_FILES:
                break
            sampled.append(dir_files[d][0])

        # Second pass: fill remaining slots proportionally
        remaining = self.MAX_SAMPLE_FILES - len(sampled)
        if remaining > 0:
            # Sort directories by file count (more files = more samples)
            dirs_by_count = sorted(dirs, key=lambda d: len(dir_files[d]), reverse=True)
            for d in dirs_by_count:
                if remaining <= 0:
                    break
                # Take additional files from this directory
                available = [f for f in dir_files[d] if f not in sampled]
                take = min(len(available), remaining // len(dirs_by_count) + 1)
                sampled.extend(available[:take])
                remaining -= take

        return sampled[:self.MAX_SAMPLE_FILES]

    def _analyze_naming_conventions(
        self, file_contents: list[tuple[Path, str]]
    ) -> dict[str, Any]:
        """Analyze naming conventions used in the codebase.

        Args:
            file_contents: List of tuples (file_path, file_content).

        Returns:
            Dictionary with detected naming conventions.
        """
        class_names: list[str] = []
        interface_names: list[str] = []
        object_names: list[str] = []
        function_names: list[str] = []
        variable_names: list[str] = []
        constant_names: list[str] = []
        file_names: list[str] = []
        package_names: list[str] = []

        for file_path, content in file_contents:
            file_names.append(file_path.stem)

            # Extract names
            class_names.extend(self.CLASS_NAME_PATTERN.findall(content))
            interface_names.extend(self.INTERFACE_NAME_PATTERN.findall(content))
            object_names.extend(self.OBJECT_NAME_PATTERN.findall(content))
            function_names.extend(self.FUNCTION_NAME_PATTERN.findall(content))
            variable_names.extend(self.VARIABLE_NAME_PATTERN.findall(content))
            constant_names.extend(self.CONST_PATTERN.findall(content))

            # Extract package names (last segment)
            packages = self.PACKAGE_PATTERN.findall(content)
            for pkg in packages:
                package_names.append(pkg.split(".")[-1])

        return {
            "classes": self._detect_naming_style(class_names + interface_names + object_names, "PascalCase"),
            "functions": self._detect_naming_style(function_names, "camelCase"),
            "variables": self._detect_naming_style(variable_names, "camelCase"),
            "constants": self._detect_naming_style(constant_names, "SCREAMING_SNAKE_CASE"),
            "files": self._detect_naming_style(file_names, "PascalCase"),
            "packages": self._detect_naming_style(package_names, "lowercase"),
        }

    def _detect_naming_style(self, names: list[str], default: str) -> str:
        """Detect the predominant naming style from a list of names.

        Args:
            names: List of identifier names to analyze.
            default: Default style to return if no names or undetermined.

        Returns:
            Detected naming style string.
        """
        if not names:
            return default

        style_counts = Counter()

        for name in names:
            if not name or name.startswith("_"):
                continue

            style = self._classify_naming_style(name)
            if style:
                style_counts[style] += 1

        if not style_counts:
            return default

        # Return the most common style
        return style_counts.most_common(1)[0][0]

    def _classify_naming_style(self, name: str) -> str | None:
        """Classify a single name into a naming style.

        Args:
            name: Identifier name to classify.

        Returns:
            Naming style string or None if unclassifiable.
        """
        if not name:
            return None

        # Skip single character names
        if len(name) <= 1:
            return None

        # Check for SCREAMING_SNAKE_CASE (all uppercase with underscores)
        if re.match(r'^[A-Z][A-Z0-9_]*$', name):
            return "SCREAMING_SNAKE_CASE"

        # Check for snake_case (lowercase with underscores)
        if re.match(r'^[a-z][a-z0-9_]*$', name) and '_' in name:
            return "snake_case"

        # Check for PascalCase (starts with uppercase, no underscores)
        if re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
            return "PascalCase"

        # Check for camelCase (starts with lowercase, has uppercase)
        if re.match(r'^[a-z][a-zA-Z0-9]*$', name) and any(c.isupper() for c in name):
            return "camelCase"

        # Check for lowercase (all lowercase, no underscores)
        if re.match(r'^[a-z][a-z0-9]*$', name):
            return "lowercase"

        return None

    def _analyze_code_style(
        self, file_contents: list[tuple[Path, str]]
    ) -> dict[str, Any]:
        """Analyze code style preferences in the codebase.

        Args:
            file_contents: List of tuples (file_path, file_content).

        Returns:
            Dictionary with detected code style preferences.
        """
        indentation_counts: Counter[tuple[str, int]] = Counter()
        line_lengths: list[int] = []
        import_styles: Counter[str] = Counter()
        brace_styles: Counter[str] = Counter()

        for _, content in file_contents:
            lines = content.split("\n")

            # Analyze indentation
            for line in lines:
                if line and not line.isspace():
                    leading = len(line) - len(line.lstrip())
                    if leading > 0:
                        if line[0] == '\t':
                            indentation_counts[("tabs", 1)] += 1
                        else:
                            # Detect indent size (typically 2 or 4 spaces)
                            indentation_counts[("spaces", leading)] += 1

            # Analyze line lengths (non-empty, non-comment lines)
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("//") and not stripped.startswith("/*"):
                    line_lengths.append(len(line))

            # Analyze import organization
            import_style = self._detect_import_style(content)
            if import_style:
                import_styles[import_style] += 1

            # Analyze brace style
            brace_style = self._detect_brace_style(content)
            if brace_style:
                brace_styles[brace_style] += 1

        # Determine indentation preference
        indent_type = "spaces"
        indent_size = 4
        if indentation_counts:
            # Find most common indentation
            most_common_indent = indentation_counts.most_common(1)[0][0]
            indent_type = most_common_indent[0]
            if indent_type == "spaces":
                # Find the most common small indent (likely the base indent)
                space_indents = [k[1] for k in indentation_counts.keys() if k[0] == "spaces"]
                if space_indents:
                    # Find GCD of common indents to determine base indent size
                    common_sizes = [s for s in space_indents if s in [2, 4, 8]]
                    if common_sizes:
                        indent_size = min(common_sizes)

        # Determine max line length
        max_line_length = 120  # default
        if line_lengths:
            # Use 95th percentile to avoid outliers
            sorted_lengths = sorted(line_lengths)
            idx_95 = int(len(sorted_lengths) * 0.95)
            max_observed = sorted_lengths[idx_95] if idx_95 < len(sorted_lengths) else sorted_lengths[-1]
            # Round to common line length values
            if max_observed <= 80:
                max_line_length = 80
            elif max_observed <= 100:
                max_line_length = 100
            elif max_observed <= 120:
                max_line_length = 120
            else:
                max_line_length = 140

        return {
            "indentation": {"type": indent_type, "size": indent_size},
            "max_line_length": max_line_length,
            "import_style": import_styles.most_common(1)[0][0] if import_styles else "ungrouped",
            "brace_style": brace_styles.most_common(1)[0][0] if brace_styles else "same_line",
        }

    def _detect_import_style(self, content: str) -> str | None:
        """Detect the import organization style in a file.

        Args:
            content: File content to analyze.

        Returns:
            Import style string or None if no imports found.
        """
        import_pattern = re.compile(r'^import\s+([\w.]+)', re.MULTILINE)
        imports = import_pattern.findall(content)

        if len(imports) < 3:
            return None

        # Check if imports are alphabetically sorted
        is_alphabetical = imports == sorted(imports)

        # Check if imports are grouped (look for blank lines between import groups)
        import_section = re.search(r'(^import\s+.*(?:\n(?:import\s+.*|\s*))*)', content, re.MULTILINE)
        if import_section:
            import_block = import_section.group(1)
            has_groups = '\n\n' in import_block or re.search(r'\nimport\s+\w+\.\w+.*\n\s*\nimport', import_block)

            if has_groups:
                return "grouped"
            elif is_alphabetical:
                return "alphabetical"

        return "ungrouped"

    def _detect_brace_style(self, content: str) -> str | None:
        """Detect the brace style used in the code.

        Args:
            content: File content to analyze.

        Returns:
            Brace style string or None if undetermined.
        """
        # Check for same-line braces (K&R style): "fun foo() {"
        same_line_pattern = re.compile(r'(?:fun|class|interface|object|if|else|for|while|when|try|catch)\s*.*\s*\{$', re.MULTILINE)
        same_line_count = len(same_line_pattern.findall(content))

        # Check for next-line braces (Allman style)
        next_line_pattern = re.compile(r'(?:fun|class|interface|object)\s*[^{]*\n\s*\{', re.MULTILINE)
        next_line_count = len(next_line_pattern.findall(content))

        if same_line_count == 0 and next_line_count == 0:
            return None

        return "same_line" if same_line_count >= next_line_count else "next_line"

    def _analyze_package_structure(
        self,
        file_contents: list[tuple[Path, str]],
        all_kotlin_files: list[Path],
    ) -> dict[str, Any]:
        """Analyze the package structure and organization.

        Args:
            file_contents: List of tuples (file_path, file_content).
            all_kotlin_files: All Kotlin files found in the project.

        Returns:
            Dictionary with package structure information.
        """
        packages: list[str] = []
        package_segments: Counter[str] = Counter()

        for _, content in file_contents:
            pkg_matches = self.PACKAGE_PATTERN.findall(content)
            for pkg in pkg_matches:
                packages.append(pkg)
                # Count each segment
                for segment in pkg.split("."):
                    package_segments[segment] += 1

        # Detect organization style
        organization = self._detect_organization_style(packages, all_kotlin_files)

        # Find common package names (excluding common prefixes like com, org, etc.)
        common_prefixes = {"com", "org", "net", "io", "app", "main", "kotlin", "java"}
        meaningful_segments = [
            seg for seg, count in package_segments.most_common(20)
            if seg.lower() not in common_prefixes and len(seg) > 2
        ]

        return {
            "organization": organization,
            "common_packages": meaningful_segments[:10],
        }

    def _detect_organization_style(
        self, packages: list[str], all_files: list[Path]
    ) -> str:
        """Detect whether the project uses feature-based or layer-based organization.

        Args:
            packages: List of package names found.
            all_files: All Kotlin files in the project.

        Returns:
            Organization style string.
        """
        # Feature-based indicators
        feature_patterns = {"feature", "features", "screen", "screens", "page", "pages"}
        # Layer-based indicators
        layer_patterns = {"data", "domain", "presentation", "ui", "repository", "usecase", "model", "view", "viewmodel"}

        feature_score = 0
        layer_score = 0

        # Check packages
        for pkg in packages:
            segments = set(pkg.lower().split("."))
            feature_score += len(segments & feature_patterns)
            layer_score += len(segments & layer_patterns)

        # Check directory structure
        for file_path in all_files[:50]:  # Sample files
            parts = set(p.lower() for p in file_path.parts)
            feature_score += len(parts & feature_patterns)
            layer_score += len(parts & layer_patterns)

        if feature_score > layer_score * 1.5:
            return "feature_based"
        elif layer_score > feature_score * 1.5:
            return "layer_based"
        else:
            return "mixed"

    def _analyze_kotlin_patterns(
        self, file_contents: list[tuple[Path, str]]
    ) -> dict[str, Any]:
        """Analyze Kotlin-specific patterns and constructs.

        Args:
            file_contents: List of tuples (file_path, file_content).

        Returns:
            Dictionary with Kotlin pattern statistics.
        """
        total_classes = 0
        data_classes = 0
        sealed_classes = 0
        extension_functions = 0
        suspend_functions = 0
        flow_usages = 0
        object_declarations = 0
        total_functions = 0
        factory_patterns = 0
        builder_patterns = 0
        companion_objects = 0

        for _, content in file_contents:
            # Count classes
            class_count = len(self.CLASS_NAME_PATTERN.findall(content))
            interface_count = len(self.INTERFACE_NAME_PATTERN.findall(content))
            total_classes += class_count + interface_count

            # Count data classes
            data_classes += len(self.DATA_CLASS_PATTERN.findall(content))

            # Count sealed classes/interfaces
            sealed_classes += len(self.SEALED_CLASS_PATTERN.findall(content))

            # Count functions
            func_count = len(self.FUNCTION_NAME_PATTERN.findall(content))
            total_functions += func_count

            # Count extension functions
            extension_functions += len(self.EXTENSION_FUNCTION_PATTERN.findall(content))

            # Count suspend functions
            suspend_functions += len(self.SUSPEND_FUNCTION_PATTERN.findall(content))

            # Count Flow usage
            flow_usages += len(self.FLOW_USAGE_PATTERN.findall(content))

            # Count object declarations (singletons)
            object_declarations += len(self.OBJECT_DECLARATION_PATTERN.findall(content))

            # Count companion objects
            companion_objects += len(self.COMPANION_OBJECT_PATTERN.findall(content))

            # Detect factory pattern
            factory_patterns += len(self.FACTORY_PATTERN.findall(content))

            # Detect builder pattern
            builder_patterns += len(self.BUILDER_PATTERN.findall(content))

        # Calculate percentages (avoid division by zero)
        def calc_percentage(count: int, total: int) -> float:
            return round(count / total, 2) if total > 0 else 0.0

        return {
            "data_classes": {
                "count": data_classes,
                "percentage": calc_percentage(data_classes, total_classes),
            },
            "sealed_classes": {
                "count": sealed_classes,
                "percentage": calc_percentage(sealed_classes, total_classes),
            },
            "extension_functions": {
                "count": extension_functions,
                "percentage": calc_percentage(extension_functions, total_functions),
            },
            "coroutines": {
                "suspend_functions": suspend_functions,
                "flow_usage": flow_usages,
            },
            "objects": {
                "count": object_declarations,
                "companion_objects": companion_objects,
                "percentage": calc_percentage(object_declarations, total_classes),
            },
            "design_patterns": {
                "factory_pattern": factory_patterns,
                "builder_pattern": builder_patterns,
            },
        }
