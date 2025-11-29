"""Analyzers for code analysis in Kotlin Multiplatform projects.

This package provides analyzers for KMP/CMP-specific patterns and structures.
"""

from .android_analyzer import AndroidAnalyzer
from .architecture_analyzer import ArchitectureAnalyzer, PatternEvidence
from .base import AnalysisResult, BaseAnalyzer
from .dependency_analyzer import DependencyAnalyzer, ExternalDependency
from .ios_analyzer import iOSAnalyzer
from .kmp_analyzer import ExpectActualPair, KMPAnalyzer
from .pattern_analyzer import PatternAnalyzer
from .project_analyzer import ProjectAnalyzer, analyze_project, detect_project_type
from .structure_analyzer import StructureAnalyzer
from .tech_stack_analyzer import TechStackAnalyzer
from .testing_analyzer import TestingAnalyzer

__all__ = [
    "AnalysisResult",
    "AndroidAnalyzer",
    "ArchitectureAnalyzer",
    "BaseAnalyzer",
    "DependencyAnalyzer",
    "ExpectActualPair",
    "ExternalDependency",
    "iOSAnalyzer",
    "KMPAnalyzer",
    "PatternAnalyzer",
    "PatternEvidence",
    "ProjectAnalyzer",
    "StructureAnalyzer",
    "TechStackAnalyzer",
    "TestingAnalyzer",
    "analyze_project",
    "detect_project_type",
]
