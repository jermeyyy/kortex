"""Architecture Memory Generator for creating architecture overview memories.

This module provides the generator for transforming architecture analysis data
into structured memory content describing design patterns, module roles, and
layer structure of the project.
"""

from typing import Any

from kortex_mcp.generators.base import BaseMemoryGenerator


class ArchitectureMemoryGenerator(BaseMemoryGenerator):
    """Generator for architecture overview memories.

    This generator transforms raw architecture analysis data into a
    comprehensive memory document that describes the project's architecture,
    including:
    - Design patterns used (MVVM, MVP, MVI, Clean Architecture, etc.)
    - Pattern evidence found in the codebase
    - Module roles and their responsibilities
    - Layer structure and organization

    The generated memory helps AI agents understand the architectural
    decisions in the project and make informed implementation choices.

    Example:
        >>> generator = ArchitectureMemoryGenerator()
        >>> analysis_data = {
        ...     "design_pattern": {
        ...         "primary_pattern": "mvvm",
        ...         "confidence": 0.85,
        ...         "additional_patterns": ["repository", "clean_architecture"]
        ...     },
        ...     "pattern_evidence": {
        ...         "mvvm": {"viewmodels": ["HomeViewModel"], "states": ["HomeUiState"]},
        ...     },
        ...     "modules": [
        ...         {"name": ":app", "role": "application", "description": "Main app entry point"}
        ...     ],
        ...     "layers": [
        ...         {"name": "Presentation Layer", "location": "feature-*/ui", "contents": [...]}
        ...     ]
        ... }
        >>> content = generator.generate_content(analysis_data)
        >>> markdown = generator.to_markdown(content)
    """

    @property
    def memory_id(self) -> str:
        """Unique identifier for architecture memories.

        Returns:
            str: The identifier "architecture".
        """
        return "architecture"

    @property
    def memory_title(self) -> str:
        """Human-readable title for the memory.

        Returns:
            str: The title "Architecture Overview".
        """
        return "Architecture Overview"

    @property
    def memory_category(self) -> str:
        """Category for organizing architecture memories.

        Returns:
            str: The category "architecture".
        """
        return "architecture"

    def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured memory content from architecture analysis data.

        Transforms raw architecture analysis results into a normalized
        dictionary containing design pattern info, module roles, and layer structure.

        Args:
            analysis_data: Dictionary containing architecture analysis results.
                Expected structure:
                {
                    "design_pattern": {
                        "primary_pattern": "mvvm",
                        "confidence": 0.85,
                        "additional_patterns": ["repository", "clean_architecture"]
                    },
                    "pattern_evidence": {
                        "mvvm": {
                            "viewmodels": ["HomeViewModel", "SettingsViewModel"],
                            "states": ["HomeUiState", "SettingsUiState"],
                            "description": "Uses StateFlow for state management"
                        },
                        "repository": {
                            "interfaces": ["UserRepository", "ProductRepository"],
                            "description": "Found implementations in data layer"
                        }
                    },
                    "modules": [
                        {
                            "name": ":app",
                            "role": "Application",
                            "description": "Main application entry point"
                        }
                    ],
                    "layers": [
                        {
                            "name": "Presentation Layer",
                            "location": "feature-*/ui, app/ui",
                            "contents": ["ViewModels", "Composables", "UI State"],
                            "pattern": "MVVM with state hoisting"
                        }
                    ],
                    "recommendations": [
                        "Follow MVVM pattern for all new features",
                        "Keep business logic in domain layer"
                    ]
                }

        Returns:
            dict[str, Any]: Structured memory content with keys:
                - design_pattern: Primary pattern info with confidence
                - pattern_evidence: Evidence supporting detected patterns
                - modules: List of module roles and descriptions
                - layers: Layer structure information
                - recommendations: Architecture recommendations

        Raises:
            ValueError: If analysis_data is None.
        """
        if analysis_data is None:
            raise ValueError("Analysis data cannot be None")

        # Extract design pattern information
        design_pattern_data = analysis_data.get("design_pattern", {})
        design_pattern = {
            "primary_pattern": design_pattern_data.get("primary_pattern"),
            "primary_pattern_display": self._get_pattern_display_name(
                design_pattern_data.get("primary_pattern")
            ),
            "confidence": design_pattern_data.get("confidence"),
            "additional_patterns": design_pattern_data.get("additional_patterns", []),
            "additional_patterns_display": [
                self._get_pattern_display_name(p)
                for p in design_pattern_data.get("additional_patterns", [])
            ],
        }

        # Extract pattern evidence
        pattern_evidence = {}
        raw_evidence = analysis_data.get("pattern_evidence", {})
        for pattern_key, evidence in raw_evidence.items():
            if isinstance(evidence, dict):
                pattern_evidence[pattern_key] = {
                    "display_name": self._get_pattern_display_name(pattern_key),
                    **evidence,
                }

        # Extract module information
        modules = []
        for module_data in analysis_data.get("modules", []):
            if isinstance(module_data, dict):
                modules.append({
                    "name": module_data.get("name", ""),
                    "role": module_data.get("role", ""),
                    "description": module_data.get("description", ""),
                })

        # Extract layer structure
        layers = []
        for layer_data in analysis_data.get("layers", []):
            if isinstance(layer_data, dict):
                layers.append({
                    "name": layer_data.get("name", ""),
                    "location": layer_data.get("location", ""),
                    "contents": layer_data.get("contents", []),
                    "pattern": layer_data.get("pattern", ""),
                })

        # Extract recommendations
        recommendations = analysis_data.get("recommendations", [])

        return {
            "design_pattern": design_pattern,
            "pattern_evidence": pattern_evidence,
            "modules": modules,
            "layers": layers,
            "recommendations": recommendations,
        }

    def _get_pattern_display_name(self, pattern: str | None) -> str:
        """Get the display name for an architecture pattern.

        Args:
            pattern: Pattern key name.

        Returns:
            str: Human-readable pattern name.
        """
        if not pattern:
            return "Unknown"

        display_names = {
            "mvvm": "MVVM",
            "mvp": "MVP",
            "mvi": "MVI",
            "mvc": "MVC",
            "repository": "Repository Pattern",
            "clean_architecture": "Clean Architecture",
            "hexagonal": "Hexagonal Architecture",
            "layered": "Layered Architecture",
            "modular": "Modular Architecture",
            "feature_based": "Feature-Based Architecture",
        }
        return display_names.get(pattern.lower(), pattern.replace("_", " ").title())

    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert structured memory content to markdown format.

        Creates a well-formatted markdown document describing the architecture,
        suitable for consumption by AI agents.

        Args:
            memory_data: Structured memory content as returned by generate_content.
                Expected keys: design_pattern, pattern_evidence, modules, layers,
                recommendations.

        Returns:
            str: Markdown-formatted string representation of the architecture.

        Raises:
            ValueError: If memory_data is None or missing required fields.
        """
        if not memory_data:
            raise ValueError("Memory data cannot be empty")

        sections = []

        # Main title
        sections.append("# Architecture Overview")

        # Design Pattern section
        design_pattern_content = self._build_design_pattern_section(
            memory_data.get("design_pattern", {})
        )
        if design_pattern_content:
            sections.append(self._format_section("Design Pattern", design_pattern_content))

        # Pattern Evidence section
        pattern_evidence_content = self._build_pattern_evidence_section(
            memory_data.get("pattern_evidence", {})
        )
        if pattern_evidence_content:
            sections.append(self._format_section("Pattern Evidence", pattern_evidence_content))

        # Module Roles section
        modules_content = self._build_modules_section(memory_data.get("modules", []))
        if modules_content:
            sections.append(self._format_section("Module Roles", modules_content))

        # Layer Structure section
        layers_content = self._build_layers_section(memory_data.get("layers", []))
        if layers_content:
            sections.append(self._format_section("Layer Structure", layers_content))

        # Recommendations section
        recommendations_content = self._build_recommendations_section(
            memory_data.get("recommendations", [])
        )
        if recommendations_content:
            sections.append(self._format_section("Recommendations", recommendations_content))

        return "\n\n".join(sections)

    def _build_design_pattern_section(self, design_pattern: dict[str, Any]) -> str:
        """Build the design pattern section content.

        Args:
            design_pattern: Dictionary containing design pattern information.

        Returns:
            str: Formatted design pattern content.
        """
        if not design_pattern:
            return ""

        lines = []

        # Primary pattern
        primary_pattern = design_pattern.get("primary_pattern_display")
        if primary_pattern:
            lines.append(f"- **Primary Pattern:** {primary_pattern}")

        # Confidence
        confidence = design_pattern.get("confidence")
        if confidence is not None:
            # Convert to percentage if it's a decimal
            if isinstance(confidence, float) and confidence <= 1.0:
                confidence_pct = int(confidence * 100)
            else:
                confidence_pct = int(confidence)
            lines.append(f"- **Confidence:** {confidence_pct}%")

        # Additional patterns
        additional_patterns = design_pattern.get("additional_patterns_display", [])
        if additional_patterns:
            lines.append(f"- **Additional Patterns:** {', '.join(additional_patterns)}")

        return "\n".join(lines)

    def _build_pattern_evidence_section(self, pattern_evidence: dict[str, Any]) -> str:
        """Build the pattern evidence section content.

        Args:
            pattern_evidence: Dictionary mapping pattern keys to evidence data.

        Returns:
            str: Formatted pattern evidence content with subsections.
        """
        if not pattern_evidence:
            return ""

        subsections = []

        for pattern_key, evidence in pattern_evidence.items():
            if not isinstance(evidence, dict):
                continue

            display_name = evidence.get("display_name", pattern_key.upper())
            evidence_lines = [f"### {display_name}"]

            # ViewModels
            viewmodels = evidence.get("viewmodels", [])
            if viewmodels:
                formatted_vms = ", ".join(f"`{vm}`" for vm in viewmodels)
                evidence_lines.append(f"- Found ViewModel classes: {formatted_vms}")

            # States
            states = evidence.get("states", [])
            if states:
                formatted_states = ", ".join(f"`{s}`" for s in states)
                evidence_lines.append(f"- Found State classes: {formatted_states}")

            # Interfaces (for Repository pattern)
            interfaces = evidence.get("interfaces", [])
            if interfaces:
                formatted_interfaces = ", ".join(f"`{i}`" for i in interfaces)
                evidence_lines.append(f"- Found Repository interfaces: {formatted_interfaces}")

            # Description
            description = evidence.get("description")
            if description:
                evidence_lines.append(f"- {description}")

            subsections.append("\n".join(evidence_lines))

        return "\n\n".join(subsections)

    def _build_modules_section(self, modules: list[dict[str, Any]]) -> str:
        """Build the module roles section as a table.

        Args:
            modules: List of module dictionaries.

        Returns:
            str: Formatted module roles table.
        """
        if not modules:
            return ""

        headers = ["Module", "Role", "Description"]
        rows = []

        for module in modules:
            name = module.get("name", "")
            role = module.get("role", "")
            description = module.get("description", "")
            rows.append([name, role, description])

        return self._format_table(headers, rows)

    def _build_layers_section(self, layers: list[dict[str, Any]]) -> str:
        """Build the layer structure section with subsections.

        Args:
            layers: List of layer dictionaries.

        Returns:
            str: Formatted layer structure content.
        """
        if not layers:
            return ""

        subsections = []

        for layer in layers:
            name = layer.get("name", "")
            if not name:
                continue

            layer_lines = [f"### {name}"]

            # Location
            location = layer.get("location")
            if location:
                layer_lines.append(f"- Location: `{location}`")

            # Contents
            contents = layer.get("contents", [])
            if contents:
                layer_lines.append(f"- Contains: {', '.join(contents)}")

            # Pattern
            pattern = layer.get("pattern")
            if pattern:
                layer_lines.append(f"- Pattern: {pattern}")

            subsections.append("\n".join(layer_lines))

        return "\n\n".join(subsections)

    def _build_recommendations_section(self, recommendations: list[str]) -> str:
        """Build the recommendations section.

        Args:
            recommendations: List of recommendation strings.

        Returns:
            str: Formatted recommendations as bullet points.
        """
        if not recommendations:
            return ""

        return "\n".join(f"- {rec}" for rec in recommendations)
