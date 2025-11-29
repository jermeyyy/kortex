"""Base Memory Generator class for creating structured memory content.

This module provides the abstract base class for all memory generators.
Memory generators transform analysis data into structured content that
can be stored and consumed by AI agents.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseMemoryGenerator(ABC):
    """Abstract base class for memory generators.

    Memory generators are responsible for transforming raw analysis data
    into structured memory content. Each generator produces a specific
    type of memory (e.g., technology stack, architecture overview).

    Subclasses must implement:
        - memory_id: Unique identifier for this memory type
        - memory_title: Human-readable title for the memory
        - memory_category: Category for organizing memories
        - generate_content: Transform analysis data into structured content
        - to_markdown: Convert structured content to markdown format

    Example:
        >>> class TechStackGenerator(BaseMemoryGenerator):
        ...     @property
        ...     def memory_id(self) -> str:
        ...         return "tech_stack"
        ...
        ...     @property
        ...     def memory_title(self) -> str:
        ...         return "Technology Stack"
        ...
        ...     @property
        ...     def memory_category(self) -> str:
        ...         return "architecture"
        ...
        ...     def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        ...         return {"languages": analysis_data.get("languages", [])}
        ...
        ...     def to_markdown(self, memory_data: dict[str, Any]) -> str:
        ...         return "# Technology Stack\\n..."
    """

    @property
    @abstractmethod
    def memory_id(self) -> str:
        """Unique identifier for this memory type.

        This ID is used to reference and retrieve the memory. It should be
        a lowercase string with underscores (e.g., "tech_stack", "architecture_overview").

        Returns:
            str: The unique memory identifier.
        """
        ...

    @property
    @abstractmethod
    def memory_title(self) -> str:
        """Human-readable title for the memory.

        This title is displayed in user interfaces and memory listings.
        It should be descriptive and readable (e.g., "Technology Stack").

        Returns:
            str: The human-readable memory title.
        """
        ...

    @property
    @abstractmethod
    def memory_category(self) -> str:
        """Category for organizing and storing memories.

        Categories help organize memories into logical groups
        (e.g., "architecture", "dependencies", "patterns").

        Returns:
            str: The memory category.
        """
        ...

    @abstractmethod
    def generate_content(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Generate structured memory content from analysis data.

        This method transforms raw analysis data into a structured dictionary
        that represents the memory content. The output should contain all
        the information needed to create the markdown representation.

        Args:
            analysis_data: Dictionary containing raw analysis results from
                project analyzers. The structure depends on the analyzer
                that produced the data.

        Returns:
            dict[str, Any]: Structured memory content. The structure is
                specific to each generator implementation.

        Raises:
            ValueError: If the analysis data is missing required fields.
        """
        ...

    @abstractmethod
    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert structured memory content to markdown format.

        This method transforms the structured memory content (from generate_content)
        into a markdown string that can be consumed by AI agents. The output
        should be well-formatted and easy to parse.

        Args:
            memory_data: Structured memory content as returned by generate_content.

        Returns:
            str: Markdown-formatted string representation of the memory.

        Raises:
            ValueError: If the memory data is missing required fields.
        """
        ...

    def _format_table(self, headers: list[str], rows: list[list[str]]) -> str:
        """Create a markdown table from headers and rows.

        This helper method creates a properly formatted markdown table
        with alignment separators.

        Args:
            headers: List of column header strings.
            rows: List of rows, where each row is a list of cell values.

        Returns:
            str: Markdown-formatted table string.

        Example:
            >>> generator._format_table(
            ...     headers=["Name", "Version"],
            ...     rows=[["Python", "3.11"], ["Kotlin", "1.9"]]
            ... )
            '| Name | Version |\\n|------|---------|\\n| Python | 3.11 |\\n| Kotlin | 1.9 |'
        """
        if not headers:
            return ""

        # Create header row
        header_row = "| " + " | ".join(headers) + " |"

        # Create separator row with proper alignment
        separator_row = "|" + "|".join("-" * (len(h) + 2) for h in headers) + "|"

        # Create data rows
        data_rows = []
        for row in rows:
            # Ensure row has same number of columns as headers
            padded_row = row + [""] * (len(headers) - len(row))
            data_rows.append("| " + " | ".join(str(cell) for cell in padded_row[:len(headers)]) + " |")

        # Combine all parts
        table_parts = [header_row, separator_row] + data_rows
        return "\n".join(table_parts)

    def _format_section(self, title: str, content: str, level: int = 2) -> str:
        """Create a markdown section with a title and content.

        This helper method creates a properly formatted markdown section
        with the specified heading level.

        Args:
            title: The section title.
            content: The section content (can include markdown formatting).
            level: The heading level (1-6). Defaults to 2.

        Returns:
            str: Markdown-formatted section string.

        Example:
            >>> generator._format_section("Overview", "This is the content.", level=2)
            '## Overview\\n\\nThis is the content.'
        """
        # Clamp level to valid markdown heading range
        level = max(1, min(6, level))

        # Create heading with appropriate number of #
        heading = "#" * level + " " + title

        # Combine heading and content with proper spacing
        return f"{heading}\n\n{content}"
