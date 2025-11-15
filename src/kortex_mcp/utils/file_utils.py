"""File system utilities for Kortex MCP Server.

This module provides utilities for path handling, file operations,
and working with KMP/CMP project structures.
"""

from pathlib import Path
from typing import Optional, List
import os


def find_project_root(start_path: Path, markers: Optional[List[str]] = None) -> Optional[Path]:
    """Find the project root directory by looking for marker files.

    Args:
        start_path: Directory to start searching from
        markers: List of marker files/directories that indicate project root
                (default: ["build.gradle.kts", "settings.gradle.kts", ".git"])

    Returns:
        Path to project root if found, None otherwise

    Example:
        >>> root = find_project_root(Path("/path/to/project/src/main"))
        >>> print(root)  # /path/to/project
    """
    if markers is None:
        markers = ["build.gradle.kts", "settings.gradle.kts", ".git"]

    current = start_path.resolve()
    
    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return current
        current = current.parent
    
    return None


def find_build_files(root_path: Path, filename: str = "build.gradle.kts") -> List[Path]:
    """Find all build files in a project directory tree.

    Args:
        root_path: Root directory to search from
        filename: Name of build file to search for (default: "build.gradle.kts")

    Returns:
        List of paths to build files found

    Example:
        >>> builds = find_build_files(Path("/project"))
        >>> for build in builds:
        ...     print(build)
    """
    build_files: List[Path] = []
    
    for root, dirs, files in os.walk(root_path):
        # Skip common directories that shouldn't contain build files
        dirs[:] = [d for d in dirs if d not in {'.git', '.gradle', 'build', '.idea', 'node_modules'}]
        
        if filename in files:
            build_files.append(Path(root) / filename)
    
    return build_files


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists

    Returns:
        The path that was ensured to exist

    Example:
        >>> dir_path = ensure_directory(Path("/tmp/kortex/data"))
        >>> assert dir_path.exists()
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_kotlin_file(path: Path) -> bool:
    """Check if a file is a Kotlin source file.

    Args:
        path: Path to check

    Returns:
        True if file has .kt or .kts extension

    Example:
        >>> is_kotlin_file(Path("Main.kt"))
        True
        >>> is_kotlin_file(Path("build.gradle.kts"))
        True
    """
    return path.suffix in {".kt", ".kts"}


def is_swift_file(path: Path) -> bool:
    """Check if a file is a Swift source file.

    Args:
        path: Path to check

    Returns:
        True if file has .swift extension

    Example:
        >>> is_swift_file(Path("ViewController.swift"))
        True
    """
    return path.suffix == ".swift"


def is_objc_file(path: Path) -> bool:
    """Check if a file is an Objective-C source file.

    Args:
        path: Path to check

    Returns:
        True if file has .m, .mm, or .h extension

    Example:
        >>> is_objc_file(Path("AppDelegate.m"))
        True
    """
    return path.suffix in {".m", ".mm", ".h"}


def get_relative_path(path: Path, base: Path) -> Path:
    """Get relative path from base to path.

    Args:
        path: Target path
        base: Base path to compute relative path from

    Returns:
        Relative path from base to path

    Raises:
        ValueError: If path is not relative to base

    Example:
        >>> rel = get_relative_path(Path("/a/b/c/file.kt"), Path("/a/b"))
        >>> print(rel)  # c/file.kt
    """
    try:
        return path.relative_to(base)
    except ValueError as e:
        raise ValueError(f"Path {path} is not relative to {base}") from e


def read_file_safe(path: Path, encoding: str = "utf-8") -> Optional[str]:
    """Safely read a file, returning None on error.

    Args:
        path: Path to file to read
        encoding: File encoding (default: utf-8)

    Returns:
        File contents as string, or None if read fails

    Example:
        >>> content = read_file_safe(Path("config.txt"))
        >>> if content:
        ...     print(content)
    """
    try:
        return path.read_text(encoding=encoding)
    except (IOError, OSError, UnicodeDecodeError):
        return None


def write_file_safe(path: Path, content: str, encoding: str = "utf-8") -> bool:
    """Safely write content to a file.

    Args:
        path: Path to file to write
        content: Content to write
        encoding: File encoding (default: utf-8)

    Returns:
        True if write succeeded, False otherwise

    Example:
        >>> success = write_file_safe(Path("output.txt"), "Hello, World!")
        >>> assert success
    """
    try:
        ensure_directory(path.parent)
        path.write_text(content, encoding=encoding)
        return True
    except (IOError, OSError):
        return False
