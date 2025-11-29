"""Base analyzer infrastructure for the Kortex project.

This module provides the foundational classes for building code analyzers
that can examine and report on various aspects of a codebase.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AnalysisResult:
    """Result of an analysis operation.

    Contains the outcome of an analyzer run, including any data produced,
    errors encountered, and warnings generated during analysis.

    Attributes:
        analyzer_name: Name of the analyzer that produced this result.
        success: Whether the analysis completed successfully.
        data: Dictionary containing analysis results and findings.
        errors: List of error messages encountered during analysis.
        warnings: List of warning messages generated during analysis.

    Example:
        >>> result = AnalysisResult(
        ...     analyzer_name="KMPAnalyzer",
        ...     success=True,
        ...     data={"source_sets": ["commonMain", "androidMain"]},
        ...     errors=[],
        ...     warnings=["No iOS source set found"]
        ... )
        >>> print(result.to_dict())
    """

    analyzer_name: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the analysis result to a dictionary.

        Returns:
            Dictionary representation of the analysis result suitable
            for JSON serialization or storage.

        Example:
            >>> result = AnalysisResult(
            ...     analyzer_name="TestAnalyzer",
            ...     success=True,
            ...     data={"count": 42}
            ... )
            >>> result.to_dict()
            {'analyzer_name': 'TestAnalyzer', 'success': True, 'data': {'count': 42}, 'errors': [], 'warnings': []}
        """
        return {
            "analyzer_name": self.analyzer_name,
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class BaseAnalyzer(ABC):
    """Abstract base class for all code analyzers.

    Provides a common interface and helper methods for implementing
    code analyzers that examine project structure, patterns, and quality.

    Subclasses must implement the abstract methods to provide specific
    analysis functionality.

    Attributes:
        project_root: Path to the root directory of the project being analyzed.

    Example:
        >>> class MyAnalyzer(BaseAnalyzer):
        ...     @property
        ...     def name(self) -> str:
        ...         return "MyAnalyzer"
        ...
        ...     async def analyze(self) -> AnalysisResult:
        ...         # Perform analysis
        ...         return self._create_success_result({"files_analyzed": 10})
        ...
        ...     def get_memory_category(self) -> str:
        ...         return "my_analysis"
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the analyzer with a project root path.

        Args:
            project_root: Path to the root directory of the project to analyze.
                         This path will be used as the base for all file operations.
        """
        self.project_root = project_root

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this analyzer.

        Returns:
            Human-readable name identifying this analyzer.
            Used for logging and result identification.
        """
        ...

    @abstractmethod
    async def analyze(self) -> AnalysisResult:
        """Perform the analysis operation.

        This method should implement the core analysis logic,
        examining the project and collecting relevant information.

        Returns:
            AnalysisResult containing the findings, any errors,
            and warnings generated during analysis.

        Raises:
            Any exceptions should be caught and returned as errors
            in the AnalysisResult rather than being raised.
        """
        ...

    @abstractmethod
    def get_memory_category(self) -> str:
        """Get the memory category for storing analysis results.

        Returns:
            String identifier for the category under which analysis
            results should be stored in the memory system.
            Used for organizing and retrieving cached analysis data.
        """
        ...

    def _create_success_result(self, data: dict[str, Any]) -> AnalysisResult:
        """Create a successful analysis result.

        Helper method to construct an AnalysisResult indicating
        successful completion with the provided data.

        Args:
            data: Dictionary containing the analysis findings and results.

        Returns:
            AnalysisResult with success=True and the provided data.

        Example:
            >>> result = self._create_success_result({"patterns_found": 5})
            >>> result.success
            True
        """
        return AnalysisResult(
            analyzer_name=self.name,
            success=True,
            data=data,
            errors=[],
            warnings=[],
        )

    def _create_error_result(
        self,
        errors: list[str],
        warnings: list[str] | None = None,
    ) -> AnalysisResult:
        """Create a failed analysis result.

        Helper method to construct an AnalysisResult indicating
        analysis failure with error and warning messages.

        Args:
            errors: List of error messages describing what went wrong.
            warnings: Optional list of warning messages. Defaults to empty list.

        Returns:
            AnalysisResult with success=False and the provided error/warning messages.

        Example:
            >>> result = self._create_error_result(
            ...     errors=["File not found: config.yml"],
            ...     warnings=["Using default configuration"]
            ... )
            >>> result.success
            False
        """
        return AnalysisResult(
            analyzer_name=self.name,
            success=False,
            data={},
            errors=errors,
            warnings=warnings if warnings is not None else [],
        )
