"""Analyzers for code analysis in Kotlin Multiplatform projects.

This package provides analyzers for KMP/CMP-specific patterns and structures.
"""

from .kmp_analyzer import KMPAnalyzer, ExpectActualPair

__all__ = ["KMPAnalyzer", "ExpectActualPair"]
