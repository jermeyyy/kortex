"""Pattern memory generator for coding patterns and conventions.

This module provides a generator that transforms raw pattern analysis data
into structured memory content documenting coding patterns and conventions
used in the project.
"""

from typing import Any

from kortex_mcp.generators.base import BaseMemoryGenerator


class PatternMemoryGenerator(BaseMemoryGenerator):
    """Generator for coding patterns and conventions memories.

    This generator transforms raw pattern analysis data into a comprehensive
    memory document that describes the project's coding patterns, including:
    - Naming conventions (classes, functions, variables, constants, etc.)
    - Code style (indentation, line length, import style, brace style)
    - Package structure and organization
    - Kotlin-specific patterns (data classes, sealed classes, extensions, etc.)
    - Coroutine patterns (suspend functions, Flow usage)
    - Design patterns detected in the codebase

    The generated memory helps AI agents understand the coding conventions
    and patterns used in the project to ensure consistent code generation.

    Example:
        >>> generator = PatternMemoryGenerator()
        >>> analysis_data = {
        ...     "naming_conventions": {
        ...         "classes": {"convention": "PascalCase", "example": "UserRepository"},
        ...         ...
        ...     },
        ...     "code_style": {
        ...         "indentation": "4 spaces",
        ...         "max_line_length": 120,
        ...         ...
        ...     },
        ...     ...
        ... }
        >>> content = generator.generate_content(analysis_data)
        >>> markdown = generator.to_markdown(content)
    """

    @property
    def memory_id(self) -> str:
        """Unique identifier for coding patterns memories.

        Returns:
            str: The identifier "coding_patterns".
        """
        return "coding_patterns"

    @property
    def memory_title(self) -> str:
        """Human-readable title for the memory.

        Returns:
            str: The title "Coding Patterns & Conventions".
        """
        return "Coding Patterns & Conventions"

    @property
    def memory_category(self) -> str:
        """Category for organizing coding patterns memories.

        Returns:
            str: The category "coding_patterns".
        """
        return "coding_patterns"

    def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured memory content from pattern analysis data.

        Transforms raw coding pattern analysis results into a normalized
        dictionary containing naming conventions, code style, package structure,
        Kotlin patterns, and design patterns information.

        Args:
            analysis_data: Dictionary containing pattern analysis results.
                Expected structure:
                {
                    "naming_conventions": {
                        "classes": {"convention": "PascalCase", "example": "UserRepository"},
                        "functions": {"convention": "camelCase", "example": "getUserById"},
                        ...
                    },
                    "code_style": {
                        "indentation": "4 spaces",
                        "max_line_length": 120,
                        "import_style": "Grouped (stdlib → third-party → project)",
                        "brace_style": "Same line (K&R)",
                    },
                    "package_structure": {
                        "organization": "Feature-based",
                        "common_packages": ["ui", "data", "domain", "util"],
                    },
                    "kotlin_patterns": {
                        "data_classes": {"count": 45, "percentage": 30},
                        "sealed_classes": {"count": 12, "percentage": 8},
                        ...
                    },
                    "coroutine_patterns": {
                        "suspend_functions": 56,
                        "flow_usage": 34,
                    },
                    "design_patterns": {
                        "factory": True,
                        "builder": False,
                        ...
                    },
                }

        Returns:
            dict[str, Any]: Structured memory content with keys:
                - naming_conventions: Dictionary of element naming conventions
                - code_style: Dictionary of code style settings
                - package_structure: Dictionary of package organization info
                - kotlin_patterns: Dictionary of Kotlin pattern usage statistics
                - coroutine_patterns: Dictionary of coroutine usage statistics
                - design_patterns: Dictionary of detected design patterns
                - recommendations: List of coding recommendations

        Raises:
            ValueError: If analysis_data is None.
        """
        if analysis_data is None:
            raise ValueError("Analysis data cannot be None")

        # Extract naming conventions with defaults
        naming_conventions = self._extract_naming_conventions(
            analysis_data.get("naming_conventions", {})
        )

        # Extract code style with defaults
        code_style = self._extract_code_style(analysis_data.get("code_style", {}))

        # Extract package structure
        package_structure = self._extract_package_structure(
            analysis_data.get("package_structure", {})
        )

        # Extract Kotlin patterns
        kotlin_patterns = self._extract_kotlin_patterns(
            analysis_data.get("kotlin_patterns", {})
        )

        # Extract coroutine patterns
        coroutine_patterns = self._extract_coroutine_patterns(
            analysis_data.get("coroutine_patterns", {})
        )

        # Extract design patterns
        design_patterns = self._extract_design_patterns(
            analysis_data.get("design_patterns", {})
        )

        # Generate recommendations based on analysis
        recommendations = self._generate_recommendations(
            naming_conventions, kotlin_patterns, design_patterns
        )

        return {
            "naming_conventions": naming_conventions,
            "code_style": code_style,
            "package_structure": package_structure,
            "kotlin_patterns": kotlin_patterns,
            "coroutine_patterns": coroutine_patterns,
            "design_patterns": design_patterns,
            "recommendations": recommendations,
        }

    def _extract_naming_conventions(
        self, naming_data: dict[str, Any]
    ) -> dict[str, dict[str, str]]:
        """Extract naming conventions from raw data.

        Args:
            naming_data: Dictionary containing naming convention data.

        Returns:
            dict[str, dict[str, str]]: Normalized naming conventions.
        """
        default_conventions = {
            "classes": {"convention": "PascalCase", "example": "UserRepository"},
            "functions": {"convention": "camelCase", "example": "getUserById"},
            "variables": {"convention": "camelCase", "example": "userName"},
            "constants": {"convention": "SCREAMING_SNAKE", "example": "MAX_RETRY_COUNT"},
            "files": {"convention": "PascalCase", "example": "UserRepository.kt"},
            "packages": {"convention": "lowercase", "example": "com.example.user"},
        }

        result = {}
        for element, defaults in default_conventions.items():
            element_data = naming_data.get(element, {})
            result[element] = {
                "convention": element_data.get("convention", defaults["convention"]),
                "example": element_data.get("example", defaults["example"]),
            }

        return result

    def _extract_code_style(self, style_data: dict[str, Any]) -> dict[str, str]:
        """Extract code style settings from raw data.

        Args:
            style_data: Dictionary containing code style data.

        Returns:
            dict[str, str]: Normalized code style settings.
        """
        return {
            "indentation": style_data.get("indentation", "4 spaces"),
            "max_line_length": str(style_data.get("max_line_length", 120)),
            "import_style": style_data.get(
                "import_style", "Grouped (stdlib → third-party → project)"
            ),
            "brace_style": style_data.get("brace_style", "Same line (K&R)"),
        }

    def _extract_package_structure(
        self, structure_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract package structure information from raw data.

        Args:
            structure_data: Dictionary containing package structure data.

        Returns:
            dict[str, Any]: Normalized package structure information.
        """
        return {
            "organization": structure_data.get("organization", "Feature-based"),
            "common_packages": structure_data.get(
                "common_packages", ["ui", "data", "domain", "util"]
            ),
        }

    def _extract_kotlin_patterns(
        self, patterns_data: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Extract Kotlin pattern usage from raw data.

        Args:
            patterns_data: Dictionary containing Kotlin patterns data.

        Returns:
            dict[str, dict[str, Any]]: Normalized Kotlin pattern statistics.
        """
        default_patterns = {
            "data_classes": {"count": 0, "percentage": 0},
            "sealed_classes": {"count": 0, "percentage": 0},
            "extension_functions": {"count": 0, "percentage": None},
            "object_declarations": {"count": 0, "percentage": 0},
        }

        result = {}
        for pattern, defaults in default_patterns.items():
            pattern_data = patterns_data.get(pattern, {})
            if isinstance(pattern_data, dict):
                result[pattern] = {
                    "count": pattern_data.get("count", defaults["count"]),
                    "percentage": pattern_data.get("percentage", defaults["percentage"]),
                }
            elif isinstance(pattern_data, int):
                result[pattern] = {
                    "count": pattern_data,
                    "percentage": defaults["percentage"],
                }
            else:
                result[pattern] = defaults

        return result

    def _extract_coroutine_patterns(
        self, coroutine_data: dict[str, Any]
    ) -> dict[str, int]:
        """Extract coroutine pattern usage from raw data.

        Args:
            coroutine_data: Dictionary containing coroutine patterns data.

        Returns:
            dict[str, int]: Normalized coroutine pattern statistics.
        """
        return {
            "suspend_functions": coroutine_data.get("suspend_functions", 0),
            "flow_usage": coroutine_data.get("flow_usage", 0),
        }

    def _extract_design_patterns(
        self, patterns_data: dict[str, Any]
    ) -> dict[str, bool]:
        """Extract design pattern detection results from raw data.

        Args:
            patterns_data: Dictionary containing design patterns data.

        Returns:
            dict[str, bool]: Dictionary of detected design patterns.
        """
        known_patterns = [
            "factory",
            "builder",
            "singleton",
            "repository",
            "observer",
            "strategy",
            "adapter",
            "decorator",
        ]

        result = {}
        for pattern in known_patterns:
            result[pattern] = patterns_data.get(pattern, False)

        return result

    def _generate_recommendations(
        self,
        naming_conventions: dict[str, dict[str, str]],
        kotlin_patterns: dict[str, dict[str, Any]],
        design_patterns: dict[str, bool],
    ) -> list[str]:
        """Generate coding recommendations based on analysis.

        Args:
            naming_conventions: Naming convention data.
            kotlin_patterns: Kotlin pattern usage data.
            design_patterns: Design pattern detection data.

        Returns:
            list[str]: List of coding recommendations.
        """
        recommendations = []

        # Naming convention recommendations
        class_convention = naming_conventions.get("classes", {}).get(
            "convention", "PascalCase"
        )
        func_convention = naming_conventions.get("functions", {}).get(
            "convention", "camelCase"
        )
        recommendations.append(f"Follow {class_convention} for class names")
        recommendations.append(f"Use {func_convention} for functions and variables")

        # Kotlin pattern recommendations
        data_classes = kotlin_patterns.get("data_classes", {})
        if data_classes.get("count", 0) > 0:
            recommendations.append("Prefer data classes for DTOs")

        sealed_classes = kotlin_patterns.get("sealed_classes", {})
        if sealed_classes.get("count", 0) > 0:
            recommendations.append("Use sealed classes for state representation")

        return recommendations

    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert structured memory content to markdown format.

        Creates a well-formatted markdown document describing the coding
        patterns and conventions, suitable for consumption by AI agents.

        Args:
            memory_data: Structured memory content as returned by generate_content.
                Expected keys: naming_conventions, code_style, package_structure,
                kotlin_patterns, coroutine_patterns, design_patterns, recommendations.

        Returns:
            str: Markdown-formatted string representation of coding patterns.

        Raises:
            ValueError: If memory_data is None or empty.
        """
        if not memory_data:
            raise ValueError("Memory data cannot be empty")

        sections = []

        # Main title
        sections.append(f"# {self.memory_title}")

        # Naming conventions section
        naming_content = self._build_naming_conventions_section(
            memory_data.get("naming_conventions", {})
        )
        sections.append(self._format_section("Naming Conventions", naming_content))

        # Code style section
        code_style_content = self._build_code_style_section(
            memory_data.get("code_style", {})
        )
        sections.append(self._format_section("Code Style", code_style_content))

        # Package structure section
        package_content = self._build_package_structure_section(
            memory_data.get("package_structure", {})
        )
        sections.append(self._format_section("Package Structure", package_content))

        # Kotlin patterns section
        kotlin_content = self._build_kotlin_patterns_section(
            memory_data.get("kotlin_patterns", {})
        )
        sections.append(self._format_section("Kotlin Patterns Usage", kotlin_content))

        # Coroutine patterns subsection
        coroutine_content = self._build_coroutine_patterns_section(
            memory_data.get("coroutine_patterns", {})
        )
        sections.append(self._format_section("Coroutine Patterns", coroutine_content, level=3))

        # Design patterns subsection
        design_content = self._build_design_patterns_section(
            memory_data.get("design_patterns", {})
        )
        sections.append(self._format_section("Design Patterns", design_content, level=3))

        # Recommendations section
        recommendations = memory_data.get("recommendations", [])
        if recommendations:
            recommendations_content = self._build_recommendations_section(recommendations)
            sections.append(
                self._format_section("Recommendations", recommendations_content)
            )

        return "\n\n".join(sections)

    def _build_naming_conventions_section(
        self, naming_conventions: dict[str, dict[str, str]]
    ) -> str:
        """Build the naming conventions table section.

        Args:
            naming_conventions: Dictionary of naming conventions by element.

        Returns:
            str: Markdown table of naming conventions.
        """
        headers = ["Element", "Convention", "Example"]
        rows = []

        # Define display names for elements
        element_display_names = {
            "classes": "Classes",
            "functions": "Functions",
            "variables": "Variables",
            "constants": "Constants",
            "files": "Files",
            "packages": "Packages",
        }

        for element_key, element_data in naming_conventions.items():
            element_name = element_display_names.get(element_key, element_key.title())
            convention = element_data.get("convention", "-")
            example = element_data.get("example", "-")
            rows.append([element_name, convention, f"`{example}`"])

        return self._format_table(headers, rows)

    def _build_code_style_section(self, code_style: dict[str, str]) -> str:
        """Build the code style section.

        Args:
            code_style: Dictionary of code style settings.

        Returns:
            str: Formatted code style content.
        """
        lines = []

        style_items = {
            "indentation": "Indentation",
            "max_line_length": "Max Line Length",
            "import_style": "Import Style",
            "brace_style": "Brace Style",
        }

        for key, display_name in style_items.items():
            value = code_style.get(key, "-")
            if key == "max_line_length":
                value = f"{value} characters"
            lines.append(f"- **{display_name}:** {value}")

        return "\n".join(lines)

    def _build_package_structure_section(
        self, package_structure: dict[str, Any]
    ) -> str:
        """Build the package structure section.

        Args:
            package_structure: Dictionary of package structure info.

        Returns:
            str: Formatted package structure content.
        """
        lines = []

        organization = package_structure.get("organization", "Feature-based")
        lines.append(f"- **Organization:** {organization}")

        common_packages = package_structure.get("common_packages", [])
        if common_packages:
            packages_str = ", ".join(common_packages)
            lines.append(f"- **Common Packages:** {packages_str}")

        return "\n".join(lines)

    def _build_kotlin_patterns_section(
        self, kotlin_patterns: dict[str, dict[str, Any]]
    ) -> str:
        """Build the Kotlin patterns usage table section.

        Args:
            kotlin_patterns: Dictionary of Kotlin pattern statistics.

        Returns:
            str: Markdown table of Kotlin patterns.
        """
        headers = ["Pattern", "Count", "% of Classes"]
        rows = []

        # Define display names for patterns
        pattern_display_names = {
            "data_classes": "Data Classes",
            "sealed_classes": "Sealed Classes",
            "extension_functions": "Extension Functions",
            "object_declarations": "Object Declarations",
        }

        for pattern_key, pattern_data in kotlin_patterns.items():
            pattern_name = pattern_display_names.get(pattern_key, pattern_key.replace("_", " ").title())
            count = pattern_data.get("count", 0)
            percentage = pattern_data.get("percentage")
            percentage_str = f"{percentage}%" if percentage is not None else "-"
            rows.append([pattern_name, str(count), percentage_str])

        return self._format_table(headers, rows)

    def _build_coroutine_patterns_section(
        self, coroutine_patterns: dict[str, int]
    ) -> str:
        """Build the coroutine patterns section.

        Args:
            coroutine_patterns: Dictionary of coroutine pattern statistics.

        Returns:
            str: Formatted coroutine patterns content.
        """
        lines = []

        suspend_count = coroutine_patterns.get("suspend_functions", 0)
        lines.append(f"- **Suspend Functions:** {suspend_count}")

        flow_count = coroutine_patterns.get("flow_usage", 0)
        lines.append(f"- **Flow Usage:** {flow_count} classes")

        return "\n".join(lines)

    def _build_design_patterns_section(self, design_patterns: dict[str, bool]) -> str:
        """Build the design patterns section.

        Args:
            design_patterns: Dictionary of detected design patterns.

        Returns:
            str: Formatted design patterns content.
        """
        lines = []

        # Define display names for patterns
        pattern_display_names = {
            "factory": "Factory Pattern",
            "builder": "Builder Pattern",
            "singleton": "Singleton Pattern",
            "repository": "Repository Pattern",
            "observer": "Observer Pattern",
            "strategy": "Strategy Pattern",
            "adapter": "Adapter Pattern",
            "decorator": "Decorator Pattern",
        }

        for pattern_key, detected in design_patterns.items():
            pattern_name = pattern_display_names.get(pattern_key, pattern_key.replace("_", " ").title())
            status = "Detected" if detected else "Not detected"
            lines.append(f"- {pattern_name}: {status}")

        return "\n".join(lines)

    def _build_recommendations_section(self, recommendations: list[str]) -> str:
        """Build the recommendations section.

        Args:
            recommendations: List of coding recommendations.

        Returns:
            str: Formatted recommendations content.
        """
        lines = [f"- {rec}" for rec in recommendations]
        return "\n".join(lines)
