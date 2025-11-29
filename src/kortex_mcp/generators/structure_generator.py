"""Structure memory generator for Kortex.

This module provides a generator that transforms project structure analysis
data into a well-formatted memory document describing the project's
module organization, source sets, and build configuration.
"""

from typing import Any

from .base import BaseMemoryGenerator


class StructureMemoryGenerator(BaseMemoryGenerator):
    """Generator for project structure memories.

    This generator transforms raw structure analysis data into a comprehensive
    memory document that describes the project's organization, including:
    - Module structure and types
    - Source sets and their dependencies
    - Build targets and platforms
    - Build configuration files

    The generated memory helps AI agents understand the project's layout
    and make informed decisions about code organization.

    Example:
        >>> generator = StructureMemoryGenerator()
        >>> analysis_data = {
        ...     "project_name": "MyApp",
        ...     "project_type": "Kotlin Multiplatform (KMP)",
        ...     "modules": [{"name": "app", "type": "Application", "targets": ["android", "ios"]}],
        ... }
        >>> content = generator.generate_content(analysis_data)
        >>> markdown = generator.to_markdown(content)
    """

    @property
    def memory_id(self) -> str:
        """Unique identifier for project structure memories.

        Returns:
            str: The identifier "project_structure".
        """
        return "project_structure"

    @property
    def memory_title(self) -> str:
        """Human-readable title for the memory.

        Returns:
            str: The title "Project Structure".
        """
        return "Project Structure"

    @property
    def memory_category(self) -> str:
        """Category for organizing structure memories.

        Returns:
            str: The category "project_structure".
        """
        return "project_structure"

    def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured memory content from structure analysis data.

        Transforms raw structure analysis results into a normalized dictionary
        containing project overview, modules, source sets, build targets, and
        build files.

        Args:
            analysis_data: Dictionary containing structure analysis results.
                Expected keys:
                - project_name: Name of the project
                - project_type: Type of project (e.g., "Kotlin Multiplatform (KMP)")
                - kotlin_version: Kotlin version used
                - compose_version: Compose version (if applicable)
                - gradle_version: Gradle version used
                - modules: List of module definitions
                - source_sets: List of source set configurations
                - build_targets: List of build targets
                - build_files: List of build file paths

        Returns:
            dict[str, Any]: Structured memory content with keys:
                - overview: Project metadata and versions
                - modules: List of module information
                - source_sets: List of source set configurations
                - build_targets: List of target platforms
                - build_files: List of build file paths

        Raises:
            ValueError: If analysis_data is None or empty.
        """
        if not analysis_data:
            raise ValueError("Analysis data cannot be empty")

        # Extract overview information
        overview = {
            "project_name": analysis_data.get("project_name", "Unknown"),
            "project_type": analysis_data.get("project_type", "Unknown"),
            "kotlin_version": analysis_data.get("kotlin_version"),
            "compose_version": analysis_data.get("compose_version"),
            "gradle_version": analysis_data.get("gradle_version"),
        }

        # Extract modules
        modules = []
        for module in analysis_data.get("modules", []):
            modules.append({
                "name": module.get("name", "Unknown"),
                "type": module.get("type", "Unknown"),
                "targets": module.get("targets", []),
            })

        # Extract source sets
        source_sets = []
        for source_set in analysis_data.get("source_sets", []):
            source_sets.append({
                "name": source_set.get("name", "Unknown"),
                "type": source_set.get("type", "Unknown"),
                "path": source_set.get("path"),
                "dependencies": source_set.get("dependencies", []),
                "depends_on": source_set.get("depends_on", []),
            })

        # Extract build targets
        build_targets = []
        for target in analysis_data.get("build_targets", []):
            build_targets.append({
                "target": target.get("target", "Unknown"),
                "platform": target.get("platform", "Unknown"),
            })

        # Extract build files
        build_files = analysis_data.get("build_files", [])

        return {
            "overview": overview,
            "modules": modules,
            "source_sets": source_sets,
            "build_targets": build_targets,
            "build_files": build_files,
        }

    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert structured memory content to markdown format.

        Creates a well-formatted markdown document describing the project
        structure, suitable for consumption by AI agents.

        Args:
            memory_data: Structured memory content as returned by generate_content.
                Expected keys: overview, modules, source_sets, build_targets, build_files.

        Returns:
            str: Markdown-formatted string representation of the project structure.

        Raises:
            ValueError: If memory_data is None or missing required fields.
        """
        if not memory_data:
            raise ValueError("Memory data cannot be empty")

        sections = []

        # Main title
        overview = memory_data.get("overview", {})
        project_name = overview.get("project_name", "Unknown")
        sections.append(f"# Project Structure: {project_name}")

        # Overview section
        overview_content = self._build_overview_section(overview)
        if overview_content:
            sections.append(self._format_section("Overview", overview_content))

        # Modules section
        modules_content = self._build_modules_section(memory_data.get("modules", []))
        if modules_content:
            sections.append(self._format_section("Modules", modules_content))

        # Source Sets section
        source_sets_content = self._build_source_sets_section(
            memory_data.get("source_sets", [])
        )
        if source_sets_content:
            sections.append(self._format_section("Source Sets", source_sets_content))

        # Build Targets section
        build_targets_content = self._build_targets_section(
            memory_data.get("build_targets", [])
        )
        if build_targets_content:
            sections.append(self._format_section("Build Targets", build_targets_content))

        # Build Files section
        build_files_content = self._build_files_section(
            memory_data.get("build_files", [])
        )
        if build_files_content:
            sections.append(self._format_section("Build Files", build_files_content))

        return "\n\n".join(sections)

    def _build_overview_section(self, overview: dict[str, Any]) -> str:
        """Build the overview section content.

        Args:
            overview: Dictionary containing project overview information.

        Returns:
            str: Formatted overview content with key-value pairs.
        """
        lines = []

        if overview.get("project_type"):
            lines.append(f"- **Project Type:** {overview['project_type']}")

        if overview.get("kotlin_version"):
            lines.append(f"- **Kotlin Version:** {overview['kotlin_version']}")

        if overview.get("compose_version"):
            lines.append(f"- **Compose Version:** {overview['compose_version']}")

        if overview.get("gradle_version"):
            lines.append(f"- **Gradle Version:** {overview['gradle_version']}")

        return "\n".join(lines)

    def _build_modules_section(self, modules: list[dict[str, Any]]) -> str:
        """Build the modules section content.

        Args:
            modules: List of module dictionaries with name, type, and targets.

        Returns:
            str: Formatted modules table.
        """
        if not modules:
            return ""

        headers = ["Module", "Type", "Targets"]
        rows = []

        for module in modules:
            targets = module.get("targets", [])
            targets_str = ", ".join(targets) if targets else "-"
            rows.append([
                module.get("name", "Unknown"),
                module.get("type", "Unknown"),
                targets_str,
            ])

        return self._format_table(headers, rows)

    def _build_source_sets_section(self, source_sets: list[dict[str, Any]]) -> str:
        """Build the source sets section content.

        Args:
            source_sets: List of source set dictionaries.

        Returns:
            str: Formatted source sets with subsections for each set.
        """
        if not source_sets:
            return ""

        subsections = []

        for source_set in source_sets:
            name = source_set.get("name", "Unknown")
            lines = []

            if source_set.get("type"):
                lines.append(f"- **Type:** {source_set['type']}")

            if source_set.get("path"):
                lines.append(f"- **Path:** `{source_set['path']}`")

            dependencies = source_set.get("dependencies", [])
            if dependencies:
                deps_str = ", ".join(dependencies)
                lines.append(f"- **Dependencies:** {deps_str}")

            depends_on = source_set.get("depends_on", [])
            if depends_on:
                deps_str = ", ".join(depends_on)
                lines.append(f"- **Depends On:** {deps_str}")

            if lines:
                subsection_content = "\n".join(lines)
                subsections.append(f"### {name}\n{subsection_content}")

        return "\n\n".join(subsections)

    def _build_targets_section(self, build_targets: list[dict[str, Any]]) -> str:
        """Build the build targets section content.

        Args:
            build_targets: List of build target dictionaries.

        Returns:
            str: Formatted build targets table.
        """
        if not build_targets:
            return ""

        headers = ["Target", "Platform"]
        rows = []

        for target in build_targets:
            rows.append([
                target.get("target", "Unknown"),
                target.get("platform", "Unknown"),
            ])

        return self._format_table(headers, rows)

    def _build_files_section(self, build_files: list[str]) -> str:
        """Build the build files section content.

        Args:
            build_files: List of build file paths.

        Returns:
            str: Formatted build files list.
        """
        if not build_files:
            return ""

        lines = [f"- `{file_path}`" for file_path in build_files]
        return "\n".join(lines)
