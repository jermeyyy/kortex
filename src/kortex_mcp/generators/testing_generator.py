"""Generator for testing setup memory content.

This module provides the TestingMemoryGenerator class that transforms
testing analysis data into structured, markdown-formatted memory
content for AI agents.
"""

from typing import Any

from kortex_mcp.generators.base import BaseMemoryGenerator


class TestingMemoryGenerator(BaseMemoryGenerator):
    """Generator for testing setup memories.

    This generator transforms raw testing analysis data into a comprehensive
    memory document that describes the project's testing configuration,
    including:
    - Test file organization and source sets
    - Testing frameworks (primary and additional)
    - Mocking libraries and multiplatform support
    - Assertion libraries
    - Testing utilities (e.g., Turbine, coroutines-test)
    - Test naming conventions
    - Coverage configuration

    The generated memory helps AI agents understand the testing setup
    and write tests that follow the project's conventions.

    Example:
        >>> generator = TestingMemoryGenerator()
        >>> analysis_data = {
        ...     "test_files_count": 30,
        ...     "test_organization": "By feature",
        ...     "source_sets": [
        ...         {"name": "commonTest", "path": "src/commonTest/kotlin", "files": 15},
        ...     ],
        ...     "frameworks": {"primary": "kotlin.test", "additional": ["JUnit 5", "Kotest"]},
        ...     ...
        ... }
        >>> content = generator.generate_content(analysis_data)
        >>> markdown = generator.to_markdown(content)
    """

    @property
    def memory_id(self) -> str:
        """Unique identifier for testing setup memories.

        Returns:
            str: The identifier "testing_setup".
        """
        return "testing_setup"

    @property
    def memory_title(self) -> str:
        """Human-readable title for the memory.

        Returns:
            str: The title "Testing Setup".
        """
        return "Testing Setup"

    @property
    def memory_category(self) -> str:
        """Category for organizing testing setup memories.

        Returns:
            str: The category "testing_setup".
        """
        return "testing_setup"

    def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured memory content from testing analysis data.

        Transforms raw testing analysis results into a normalized dictionary
        containing testing configuration information.

        Args:
            analysis_data: Dictionary containing testing analysis results.
                Expected structure:
                {
                    "test_files_count": 30,
                    "test_organization": "By feature",
                    "source_sets": [
                        {"name": "commonTest", "path": "src/commonTest/kotlin", "files": 15},
                        ...
                    ],
                    "frameworks": {
                        "primary": "kotlin.test",
                        "additional": ["JUnit 5", "Kotest"]
                    },
                    "mocking": {
                        "library": "MockK",
                        "multiplatform": True
                    },
                    "assertion_libraries": ["Kotest assertions", "Google Truth"],
                    "utilities": [
                        {"name": "Turbine", "purpose": "Flow testing"},
                        ...
                    ],
                    "naming_convention": {
                        "style": "should_when",
                        "example": "should return empty list when no items"
                    },
                    "coverage": {
                        "tool": "Kover",
                        "configured": True
                    },
                    "recommendations": [...]
                }

        Returns:
            dict[str, Any]: Structured memory content with testing information.

        Raises:
            ValueError: If analysis_data is None.
        """
        if analysis_data is None:
            raise ValueError("Analysis data cannot be None")

        # Extract overview information
        overview = {
            "total_test_files": analysis_data.get("test_files_count", 0),
            "test_organization": analysis_data.get("test_organization", "Unknown"),
        }

        # Extract source sets
        source_sets = []
        for source_set in analysis_data.get("source_sets", []):
            source_sets.append({
                "name": source_set.get("name", ""),
                "path": source_set.get("path", ""),
                "files": source_set.get("files", 0),
            })

        # Extract frameworks information
        frameworks_data = analysis_data.get("frameworks", {})
        frameworks = {
            "primary": frameworks_data.get("primary", ""),
            "additional": frameworks_data.get("additional", []),
        }

        # Extract mocking information
        mocking_data = analysis_data.get("mocking", {})
        mocking = {
            "library": mocking_data.get("library", ""),
            "multiplatform": mocking_data.get("multiplatform", False),
        }

        # Extract assertion libraries
        assertion_libraries = analysis_data.get("assertion_libraries", [])

        # Extract utilities
        utilities = []
        for utility in analysis_data.get("utilities", []):
            utilities.append({
                "name": utility.get("name", ""),
                "purpose": utility.get("purpose", ""),
            })

        # Extract naming conventions
        naming_data = analysis_data.get("naming_convention", {})
        naming_convention = {
            "style": naming_data.get("style", ""),
            "example": naming_data.get("example", ""),
        }

        # Extract coverage information
        coverage_data = analysis_data.get("coverage", {})
        coverage = {
            "tool": coverage_data.get("tool", ""),
            "configured": coverage_data.get("configured", False),
        }

        # Extract recommendations
        recommendations = analysis_data.get("recommendations", [])

        return {
            "overview": overview,
            "source_sets": source_sets,
            "frameworks": frameworks,
            "mocking": mocking,
            "assertion_libraries": assertion_libraries,
            "utilities": utilities,
            "naming_convention": naming_convention,
            "coverage": coverage,
            "recommendations": recommendations,
        }

    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert structured memory content to markdown format.

        Transforms the structured memory content into a well-formatted
        markdown document describing the testing setup.

        Args:
            memory_data: Structured memory content as returned by generate_content.

        Returns:
            str: Markdown-formatted string representation of the testing setup.

        Raises:
            ValueError: If memory_data is None.
        """
        if memory_data is None:
            raise ValueError("Memory data cannot be None")

        sections = []

        # Title
        sections.append(f"# {self.memory_title}")

        # Overview section
        overview = memory_data.get("overview", {})
        overview_content = (
            f"- **Total Test Files:** {overview.get('total_test_files', 0)}\n"
            f"- **Test Organization:** {overview.get('test_organization', 'Unknown')}"
        )
        sections.append(self._format_section("Overview", overview_content))

        # Test Source Sets section
        source_sets = memory_data.get("source_sets", [])
        if source_sets:
            rows = [
                [ss.get("name", ""), ss.get("path", ""), str(ss.get("files", 0))]
                for ss in source_sets
            ]
            table = self._format_table(["Source Set", "Path", "Files"], rows)
            sections.append(self._format_section("Test Source Sets", table))

        # Testing Frameworks section
        frameworks = memory_data.get("frameworks", {})
        primary = frameworks.get("primary", "")
        additional = frameworks.get("additional", [])
        frameworks_content = f"- **Primary:** {primary}"
        if additional:
            frameworks_content += f"\n- **Additional:** {', '.join(additional)}"
        sections.append(self._format_section("Testing Frameworks", frameworks_content))

        # Mocking section
        mocking = memory_data.get("mocking", {})
        library = mocking.get("library", "")
        multiplatform = "Yes" if mocking.get("multiplatform", False) else "No"
        if library:
            mocking_content = f"- **Library:** {library}\n- **Multiplatform:** {multiplatform}"
            sections.append(self._format_section("Mocking", mocking_content))

        # Assertion Libraries section
        assertion_libraries = memory_data.get("assertion_libraries", [])
        if assertion_libraries:
            assertions_content = "\n".join(f"- {lib}" for lib in assertion_libraries)
            sections.append(self._format_section("Assertion Libraries", assertions_content))

        # Testing Utilities section
        utilities = memory_data.get("utilities", [])
        if utilities:
            rows = [
                [util.get("name", ""), util.get("purpose", "")]
                for util in utilities
            ]
            table = self._format_table(["Utility", "Purpose"], rows)
            sections.append(self._format_section("Testing Utilities", table))

        # Test Naming Conventions section
        naming = memory_data.get("naming_convention", {})
        style = naming.get("style", "")
        example = naming.get("example", "")
        if style:
            naming_content = f"- **Style:** {style}"
            if example:
                naming_content += f"\n- **Example:** `{example}`"
            sections.append(self._format_section("Test Naming Conventions", naming_content))

        # Coverage section
        coverage = memory_data.get("coverage", {})
        tool = coverage.get("tool", "")
        configured = "Yes" if coverage.get("configured", False) else "No"
        if tool:
            coverage_content = f"- **Tool:** {tool}\n- **Configured:** {configured}"
            sections.append(self._format_section("Coverage", coverage_content))

        # Recommendations section
        recommendations = memory_data.get("recommendations", [])
        if recommendations:
            recommendations_content = "\n".join(f"- {rec}" for rec in recommendations)
            sections.append(self._format_section("Recommendations", recommendations_content))

        return "\n\n".join(sections)
