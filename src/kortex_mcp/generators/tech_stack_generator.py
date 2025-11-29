"""Generator for technology stack memory content.

This module provides the TechStackMemoryGenerator class that transforms
technology stack analysis data into structured, markdown-formatted memory
content for AI agents.
"""

from typing import Any

from kortex_mcp.generators.base import BaseMemoryGenerator


# Mapping of category keys to human-readable names
CATEGORY_DISPLAY_NAMES: dict[str, str] = {
    "di": "Dependency Injection",
    "networking": "Networking",
    "database": "Database",
    "serialization": "Serialization",
    "image_loading": "Image Loading",
    "navigation": "Navigation",
    "testing": "Testing",
    "logging": "Logging",
    "ui": "UI Framework",
}

# Mapping of framework keys to human-readable names
FRAMEWORK_DISPLAY_NAMES: dict[str, str] = {
    "koin": "Koin",
    "hilt": "Hilt",
    "dagger": "Dagger",
    "kodein": "Kodein",
    "ktor": "Ktor Client",
    "retrofit": "Retrofit",
    "okhttp": "OkHttp",
    "room": "Room",
    "sqldelight": "SQLDelight",
    "realm": "Realm",
    "kotlinx_serialization": "kotlinx.serialization",
    "moshi": "Moshi",
    "gson": "Gson",
    "coil": "Coil",
    "glide": "Glide",
    "picasso": "Picasso",
    "compose_navigation": "Compose Navigation",
    "voyager": "Voyager",
    "decompose": "Decompose",
    "junit": "JUnit",
    "kotest": "Kotest",
    "mockk": "MockK",
    "turbine": "Turbine",
    "kotlin_test": "kotlin.test",
    "timber": "Timber",
    "napier": "Napier",
    "kermit": "Kermit",
    "compose": "Compose Multiplatform",
}


class TechStackMemoryGenerator(BaseMemoryGenerator):
    """Generator for technology stack memories.

    This generator transforms raw technology stack analysis data into a
    comprehensive memory document that describes the project's tech stack,
    including:
    - Dependency injection frameworks
    - Networking libraries
    - Database solutions
    - Serialization frameworks
    - UI and navigation frameworks
    - Testing libraries
    - Logging solutions

    The generated memory helps AI agents understand which frameworks and
    libraries are used in the project and make informed decisions about
    code implementation patterns.

    Example:
        >>> generator = TechStackMemoryGenerator()
        >>> analysis_data = {
        ...     "di": {"framework": "koin", "version": "3.5.0", "artifacts": [...]},
        ...     "networking": {"framework": "ktor", "version": "2.3.0", "artifacts": [...]},
        ... }
        >>> content = generator.generate_content(analysis_data)
        >>> markdown = generator.to_markdown(content)
    """

    @property
    def memory_id(self) -> str:
        """Unique identifier for technology stack memories.

        Returns:
            str: The identifier "tech_stack".
        """
        return "tech_stack"

    @property
    def memory_title(self) -> str:
        """Human-readable title for the memory.

        Returns:
            str: The title "Technology Stack".
        """
        return "Technology Stack"

    @property
    def memory_category(self) -> str:
        """Category for organizing technology stack memories.

        Returns:
            str: The category "tech_stack".
        """
        return "tech_stack"

    def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured memory content from tech stack analysis data.

        Transforms raw technology stack analysis results into a normalized
        dictionary containing categorized framework information.

        Args:
            analysis_data: Dictionary containing tech stack analysis results.
                Expected structure:
                {
                    "di": {"framework": "koin", "version": "3.5.0", "artifacts": [...]},
                    "networking": {"framework": "ktor", "version": "2.3.0", "artifacts": [...]},
                    ...
                }

        Returns:
            dict[str, Any]: Structured memory content with keys:
                - categories: List of category dictionaries with framework info
                - development_notes: List of development recommendations

        Raises:
            ValueError: If analysis_data is None.
        """
        if analysis_data is None:
            raise ValueError("Analysis data cannot be None")

        categories = []

        # Process each detected category
        for category_key, category_data in analysis_data.items():
            if not isinstance(category_data, dict):
                continue

            framework = category_data.get("framework")
            if not framework:
                continue

            category_info = {
                "key": category_key,
                "display_name": CATEGORY_DISPLAY_NAMES.get(category_key, category_key.replace("_", " ").title()),
                "framework": framework,
                "framework_display_name": FRAMEWORK_DISPLAY_NAMES.get(framework, framework.title()),
                "version": category_data.get("version"),
                "artifacts": category_data.get("artifacts", []),
                "source": category_data.get("source", "unknown"),
                "additional_frameworks": category_data.get("additional_frameworks", []),
            }
            categories.append(category_info)

        # Generate development notes based on detected frameworks
        development_notes = self._generate_development_notes(categories)

        return {
            "categories": categories,
            "development_notes": development_notes,
        }

    def _generate_development_notes(self, categories: list[dict[str, Any]]) -> list[str]:
        """Generate development notes based on detected frameworks.

        Args:
            categories: List of category dictionaries with framework info.

        Returns:
            list[str]: List of development recommendations.
        """
        notes = []

        # Create a mapping for quick lookup
        framework_map = {cat["key"]: cat["framework"] for cat in categories}

        # Add framework-specific notes
        if "di" in framework_map:
            framework = framework_map["di"]
            display_name = FRAMEWORK_DISPLAY_NAMES.get(framework, framework.title())
            notes.append(f"Use {display_name} for all dependency injection")

        if "networking" in framework_map:
            framework = framework_map["networking"]
            display_name = FRAMEWORK_DISPLAY_NAMES.get(framework, framework.title())
            notes.append(f"Prefer {display_name} for network calls")

        if "database" in framework_map:
            framework = framework_map["database"]
            display_name = FRAMEWORK_DISPLAY_NAMES.get(framework, framework.title())
            notes.append(f"Use {display_name} for local persistence")

        if "serialization" in framework_map:
            framework = framework_map["serialization"]
            display_name = FRAMEWORK_DISPLAY_NAMES.get(framework, framework.title())
            notes.append(f"Use {display_name} for JSON serialization")

        if "testing" in framework_map:
            framework = framework_map["testing"]
            display_name = FRAMEWORK_DISPLAY_NAMES.get(framework, framework.title())
            notes.append(f"Write tests using {display_name}")

        return notes

    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert structured memory content to markdown format.

        Creates a well-formatted markdown document describing the technology
        stack, suitable for consumption by AI agents.

        Args:
            memory_data: Structured memory content as returned by generate_content.
                Expected keys: categories, development_notes.

        Returns:
            str: Markdown-formatted string representation of the technology stack.

        Raises:
            ValueError: If memory_data is None or missing required fields.
        """
        if not memory_data:
            raise ValueError("Memory data cannot be empty")

        sections = []

        # Main title
        sections.append("# Technology Stack")

        # Overview section
        overview_content = "This document describes the technology stack used in this project."
        sections.append(self._format_section("Overview", overview_content))

        # Process each category
        categories = memory_data.get("categories", [])

        # Separate testing from other categories for special formatting
        testing_categories = [c for c in categories if c["key"] == "testing"]
        other_categories = [c for c in categories if c["key"] != "testing"]

        # Add regular category sections
        for category in other_categories:
            category_content = self._build_category_section(category)
            if category_content:
                sections.append(self._format_section(category["display_name"], category_content))

        # Add testing section with table format
        if testing_categories:
            testing_content = self._build_testing_section(testing_categories[0])
            if testing_content:
                sections.append(self._format_section("Testing", testing_content))

        # Add development notes section
        dev_notes = memory_data.get("development_notes", [])
        if dev_notes:
            notes_content = self._build_development_notes_section(dev_notes)
            sections.append(self._format_section("Development Notes", notes_content))

        return "\n\n".join(sections)

    def _build_category_section(self, category: dict[str, Any]) -> str:
        """Build the content for a category section.

        Args:
            category: Dictionary containing category information.

        Returns:
            str: Formatted category content.
        """
        lines = []

        # Framework name
        framework_display = category.get("framework_display_name", category.get("framework", "Unknown"))
        lines.append(f"- **Framework:** {framework_display}")

        # Version
        version = category.get("version")
        if version:
            lines.append(f"- **Version:** {version}")

        # Artifacts
        artifacts = category.get("artifacts", [])
        if artifacts:
            lines.append("- **Artifacts:**")
            for artifact in artifacts:
                lines.append(f"  - `{artifact}`")

        # Additional frameworks
        additional = category.get("additional_frameworks", [])
        if additional:
            additional_display: list[str] = [
                FRAMEWORK_DISPLAY_NAMES.get(f, f.title() if f else "Unknown")
                for f in additional if f
            ]
            if additional_display:
                lines.append(f"- **Also detected:** {', '.join(additional_display)}")

        return "\n".join(lines)

    def _build_testing_section(self, category: dict[str, Any]) -> str:
        """Build the testing section with table format.

        Args:
            category: Dictionary containing testing category information.

        Returns:
            str: Formatted testing section with table.
        """
        # Primary framework info
        framework = category.get("framework", "")
        framework_display = category.get("framework_display_name", framework)
        version = category.get("version")

        # Build table data
        headers = ["Library", "Version", "Purpose"]
        rows: list[list[str]] = []

        # Add primary framework
        if framework:
            purpose = self._get_framework_purpose(framework)
            rows.append([str(framework_display or framework), version or "-", purpose])

        # Add additional frameworks
        additional = category.get("additional_frameworks", [])
        for add_framework in additional:
            if add_framework:
                add_display = FRAMEWORK_DISPLAY_NAMES.get(add_framework) or add_framework.title()
                add_purpose = self._get_framework_purpose(add_framework)
                rows.append([add_display, "-", add_purpose])

        return self._format_table(headers, rows)

    def _get_framework_purpose(self, framework: str) -> str:
        """Get the purpose description for a framework.

        Args:
            framework: Framework key name.

        Returns:
            str: Purpose description.
        """
        purposes = {
            "junit": "Unit testing",
            "kotest": "Testing framework",
            "mockk": "Mocking",
            "turbine": "Flow testing",
            "kotlin_test": "Unit testing",
        }
        return purposes.get(framework, "Testing")

    def _build_development_notes_section(self, notes: list[str]) -> str:
        """Build the development notes section.

        Args:
            notes: List of development notes.

        Returns:
            str: Formatted development notes.
        """
        lines = [f"- {note}" for note in notes]
        return "\n".join(lines)
