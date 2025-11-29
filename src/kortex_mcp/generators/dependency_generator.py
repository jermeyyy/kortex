"""Dependency memory generator for creating structured dependency documentation.

This module provides the DependencyMemoryGenerator class that transforms
raw dependency analysis data into structured memory content describing
project dependencies, including module dependencies and external libraries.
"""

from typing import Any

from kortex_mcp.generators.base import BaseMemoryGenerator

# Category display names for external dependencies
DEPENDENCY_CATEGORY_DISPLAY_NAMES = {
    "kotlin_standard": "Kotlin Standard",
    "networking": "Networking",
    "database": "Database",
    "testing": "Testing",
    "di": "Dependency Injection",
    "serialization": "Serialization",
    "ui": "UI Framework",
    "navigation": "Navigation",
    "logging": "Logging",
    "analytics": "Analytics",
    "image_loading": "Image Loading",
    "compose": "Compose",
    "coroutines": "Coroutines",
    "other": "Other",
}


class DependencyMemoryGenerator(BaseMemoryGenerator):
    """Generator for project dependency memories.

    This generator transforms raw dependency analysis data into a
    comprehensive memory document that describes the project's dependencies,
    including:
    - Module dependency graph
    - Internal module dependencies
    - External dependencies by category
    - Version catalog information

    The generated memory helps AI agents understand the project's dependency
    structure and make informed decisions about code organization and imports.

    Example:
        >>> generator = DependencyMemoryGenerator()
        >>> analysis_data = {
        ...     "modules": [
        ...         {"name": "app", "dependencies": ["core", "feature-home"]},
        ...         {"name": "core", "dependencies": []},
        ...     ],
        ...     "external_dependencies": {
        ...         "kotlin_standard": [
        ...             {"artifact": "kotlinx-coroutines-core", "version": "1.7.3"},
        ...         ],
        ...     },
        ... }
        >>> content = generator.generate_content(analysis_data)
        >>> markdown = generator.to_markdown(content)
    """

    @property
    def memory_id(self) -> str:
        """Unique identifier for dependency memories.

        Returns:
            str: The identifier "dependencies".
        """
        return "dependencies"

    @property
    def memory_title(self) -> str:
        """Human-readable title for the memory.

        Returns:
            str: The title "Project Dependencies".
        """
        return "Project Dependencies"

    @property
    def memory_category(self) -> str:
        """Category for organizing dependency memories.

        Returns:
            str: The category "dependencies".
        """
        return "dependencies"

    def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured memory content from dependency analysis data.

        Transforms raw dependency analysis results into a normalized
        dictionary containing module and external dependency information.

        Args:
            analysis_data: Dictionary containing dependency analysis results.
                Expected structure:
                {
                    "modules": [
                        {"name": "app", "dependencies": ["core", "feature"]},
                        ...
                    ],
                    "external_dependencies": {
                        "kotlin_standard": [
                            {"artifact": "kotlinx-coroutines-core", "version": "1.7.3"},
                            ...
                        ],
                        ...
                    },
                    "version_catalog": {
                        "path": "gradle/libs.versions.toml",
                        "versions": {"kotlin": "1.9.20", ...}
                    }
                }

        Returns:
            dict[str, Any]: Structured memory content with keys:
                - modules: List of module dictionaries with dependencies
                - external_dependencies: Dict of dependencies by category
                - version_catalog: Version catalog information
                - total_modules: Total number of modules
                - total_external_dependencies: Total external dependency count

        Raises:
            ValueError: If analysis_data is None.
        """
        if analysis_data is None:
            raise ValueError("Analysis data cannot be None")

        modules = analysis_data.get("modules", [])
        external_deps = analysis_data.get("external_dependencies", {})
        version_catalog = analysis_data.get("version_catalog", {})

        # Normalize modules data
        normalized_modules = []
        for module in modules:
            if isinstance(module, dict):
                normalized_modules.append({
                    "name": module.get("name", "unknown"),
                    "dependencies": module.get("dependencies", []),
                })

        # Count total external dependencies
        total_external = sum(
            len(deps) for deps in external_deps.values() if isinstance(deps, list)
        )

        return {
            "modules": normalized_modules,
            "external_dependencies": external_deps,
            "version_catalog": version_catalog,
            "total_modules": len(normalized_modules),
            "total_external_dependencies": total_external,
        }

    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert structured memory content to markdown format.

        Creates a well-formatted markdown document describing the project
        dependencies, suitable for consumption by AI agents.

        Args:
            memory_data: Structured memory content as returned by generate_content.
                Expected keys: modules, external_dependencies, version_catalog,
                total_modules, total_external_dependencies.

        Returns:
            str: Markdown-formatted string representation of the dependencies.

        Raises:
            ValueError: If memory_data is None or missing required fields.
        """
        if not memory_data:
            raise ValueError("Memory data cannot be empty")

        sections = []

        # Main title
        sections.append("# Project Dependencies")

        # Overview section
        overview_content = self._build_overview_section(memory_data)
        sections.append(self._format_section("Overview", overview_content))

        # Module dependency graph
        modules = memory_data.get("modules", [])
        if modules:
            graph_content = self._build_dependency_graph(modules)
            sections.append(self._format_section("Module Dependency Graph", graph_content))

            # Modules table
            modules_table = self._build_modules_table(modules)
            sections.append(self._format_section("Modules", modules_table))

        # External dependencies by category
        external_deps = memory_data.get("external_dependencies", {})
        if external_deps:
            external_section = self._build_external_dependencies_section(external_deps)
            sections.append(self._format_section("External Dependencies by Category", external_section))

        # Version catalog section
        version_catalog = memory_data.get("version_catalog", {})
        if version_catalog:
            catalog_section = self._build_version_catalog_section(version_catalog)
            sections.append(self._format_section("Version Catalog", catalog_section))

        return "\n\n".join(sections)

    def _build_overview_section(self, memory_data: dict[str, Any]) -> str:
        """Build the overview section content.

        Args:
            memory_data: The full memory data dictionary.

        Returns:
            str: Formatted overview content.
        """
        total_modules = memory_data.get("total_modules", 0)
        total_external = memory_data.get("total_external_dependencies", 0)

        lines = [
            f"- **Total Modules:** {total_modules}",
            f"- **Total External Dependencies:** {total_external}",
        ]
        return "\n".join(lines)

    def _build_dependency_graph(self, modules: list[dict[str, Any]]) -> str:
        """Build a text-based dependency graph.

        Creates a tree-like visualization of module dependencies.

        Args:
            modules: List of module dictionaries with name and dependencies.

        Returns:
            str: Text-based dependency graph wrapped in a code block.
        """
        if not modules:
            return "No modules found."

        # Build a mapping of module names to their dependencies
        module_deps = {m["name"]: m.get("dependencies", []) for m in modules}

        # Find root modules (modules that are not dependencies of others)
        all_deps = set()
        for deps in module_deps.values():
            all_deps.update(deps)

        root_modules = [name for name in module_deps.keys() if name not in all_deps]

        # If no root found, use the first module
        if not root_modules:
            root_modules = [modules[0]["name"]] if modules else []

        # Build the tree for each root
        lines = []
        for i, root in enumerate(root_modules):
            if i > 0:
                lines.append("")  # Add blank line between roots
            self._build_tree_lines(root, module_deps, set(), lines, "", True)

        graph_text = "\n".join(lines) if lines else "No dependency graph available."
        return f"```\n{graph_text}\n```"

    def _build_tree_lines(
        self,
        module_name: str,
        module_deps: dict[str, list[str]],
        visited: set[str],
        lines: list[str],
        prefix: str = "",
        is_root: bool = False,
    ) -> None:
        """Build tree lines for a module and its dependencies recursively.

        Args:
            module_name: Name of the current module.
            module_deps: Mapping of module names to their dependencies.
            visited: Set of already visited modules (to prevent cycles).
            lines: List to append formatted tree lines to.
            prefix: Current line prefix for indentation.
            is_root: Whether this is a root node (no connector).
        """
        # Add current module
        if is_root:
            lines.append(module_name)
        else:
            lines.append(f"{prefix}{module_name}")

        # Prevent cycles
        if module_name in visited:
            return
        visited.add(module_name)

        # Get dependencies
        deps = module_deps.get(module_name, [])
        if not deps:
            return

        # Add children
        for i, dep in enumerate(deps):
            is_last = i == len(deps) - 1
            connector = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            # Add the dependency line
            lines.append(f"{prefix}{connector}{dep}")

            # Recursively add sub-dependencies (if not already visited)
            if dep not in visited and dep in module_deps:
                sub_deps = module_deps.get(dep, [])
                for j, sub_dep in enumerate(sub_deps):
                    sub_is_last = j == len(sub_deps) - 1
                    sub_connector = "└── " if sub_is_last else "├── "
                    lines.append(f"{child_prefix}{sub_connector}{sub_dep}")

    def _build_modules_table(self, modules: list[dict[str, Any]]) -> str:
        """Build a markdown table of modules and their dependencies.

        Args:
            modules: List of module dictionaries.

        Returns:
            str: Markdown-formatted table.
        """
        headers = ["Module", "Dependencies"]
        rows = []

        for module in modules:
            name = module.get("name", "unknown")
            deps = module.get("dependencies", [])
            deps_str = ", ".join(deps) if deps else "-"
            rows.append([name, deps_str])

        return self._format_table(headers, rows)

    def _build_external_dependencies_section(
        self, external_deps: dict[str, Any]
    ) -> str:
        """Build the external dependencies section with category subsections.

        Args:
            external_deps: Dictionary mapping categories to lists of dependencies.

        Returns:
            str: Formatted external dependencies content.
        """
        sections = []

        for category_key, deps in external_deps.items():
            if not isinstance(deps, list) or not deps:
                continue

            display_name = DEPENDENCY_CATEGORY_DISPLAY_NAMES.get(
                category_key, category_key.replace("_", " ").title()
            )

            # Build table for this category
            headers = ["Artifact", "Version"]
            rows = []

            for dep in deps:
                if isinstance(dep, dict):
                    artifact = dep.get("artifact", "unknown")
                    version = dep.get("version", "-")
                    rows.append([artifact, version])
                elif isinstance(dep, str):
                    rows.append([dep, "-"])

            if rows:
                table = self._format_table(headers, rows)
                sections.append(f"### {display_name}\n{table}")

        return "\n\n".join(sections) if sections else "No external dependencies found."

    def _build_version_catalog_section(self, version_catalog: dict[str, Any]) -> str:
        """Build the version catalog section.

        Args:
            version_catalog: Dictionary containing version catalog information.

        Returns:
            str: Formatted version catalog content.
        """
        lines = []

        # Catalog path
        path = version_catalog.get("path", "")
        if path:
            lines.append(f"Using Gradle Version Catalog: `{path}`")
            lines.append("")

        # Key versions
        versions = version_catalog.get("versions", {})
        if versions:
            lines.append("### Key Versions")

            # Build a list of key versions
            for name, version in versions.items():
                lines.append(f"- {name} = {version}")

        return "\n".join(lines) if lines else "No version catalog information available."
