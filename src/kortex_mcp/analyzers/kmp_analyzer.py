"""Kotlin Multiplatform analyzer for expect/actual detection and source set analysis.

This module provides analysis capabilities specific to Kotlin Multiplatform projects,
including expect/actual declaration detection, source set identification, and
platform-specific code analysis.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from ..models.project import SourceSet, SourceSetType
from ..utils.logging import get_logger


logger = get_logger(__name__)


@dataclass
class ExpectActualPair:
    """Represents an expect declaration with its actual implementations.
    
    Attributes:
        name: Symbol name (class, function, or property)
        kind: Declaration kind ("class", "function", "property")
        expect_location: Location of expect declaration
        actual_locations: Map of source set to actual location
        signature: Symbol signature for validation
    """
    name: str
    kind: str
    expect_location: Dict[str, Any]
    actual_locations: Dict[str, Dict[str, Any]]
    signature: Optional[str] = None


class KMPAnalyzer:
    """Kotlin Multiplatform project analyzer.
    
    Analyzes KMP project structure, detects expect/actual declarations,
    and provides source set identification and platform-specific code analysis.
    
    Attributes:
        workspace_path: Path to KMP project root
        source_sets: Detected source sets in the project
        
    Example:
        >>> analyzer = KMPAnalyzer(workspace_path=Path("/project"))
        >>> source_set = analyzer.get_source_set_from_path(
        ...     Path("src/commonMain/kotlin/Platform.kt")
        ... )
        >>> expect_actual = await analyzer.find_expect_actual_pairs("Platform")
    """
    
    def __init__(self, workspace_path: Path):
        """Initialize KMP analyzer.
        
        Args:
            workspace_path: Path to KMP project root
        """
        self.workspace_path = workspace_path
        self.source_sets: Dict[str, SourceSet] = {}
        self._detect_source_sets()
    
    def _detect_source_sets(self) -> None:
        """Detect all source sets in the project by scanning directory structure."""
        # Common KMP source set patterns
        source_set_patterns = [
            ("commonMain", SourceSetType.COMMON),
            ("commonTest", SourceSetType.COMMON),
            ("androidMain", SourceSetType.ANDROID),
            ("androidTest", SourceSetType.ANDROID),
            ("iosMain", SourceSetType.IOS),
            ("iosTest", SourceSetType.IOS),
            ("jvmMain", SourceSetType.JVM),
            ("jvmTest", SourceSetType.JVM),
            ("jsMain", SourceSetType.JS),
            ("jsTest", SourceSetType.JS),
            ("desktopMain", SourceSetType.DESKTOP),
            ("desktopTest", SourceSetType.DESKTOP),
        ]
        
        # Scan for source set directories
        if self.workspace_path.exists():
            for pattern, source_type in source_set_patterns:
                # Look for src/{sourceSet} pattern
                src_dir = self.workspace_path / "src" / pattern
                if src_dir.exists() and src_dir.is_dir():
                    # Look for kotlin subdirectory
                    kotlin_dir = src_dir / "kotlin"
                    source_dirs = [kotlin_dir] if kotlin_dir.exists() else [src_dir]
                    
                    self.source_sets[pattern] = SourceSet(
                        name=pattern,
                        type=source_type,
                        source_dirs=source_dirs
                    )
                    logger.debug(f"Detected source set: {pattern} at {src_dir}")
    
    def get_source_set_from_path(self, file_path: Path) -> Optional[SourceSet]:
        """Identify source set from file path.
        
        Args:
            file_path: Path to Kotlin file
            
        Returns:
            SourceSet if identified, None otherwise
            
        Example:
            >>> source_set = analyzer.get_source_set_from_path(
            ...     Path("src/commonMain/kotlin/Platform.kt")
            ... )
            >>> print(source_set.name)  # "commonMain"
        """
        # Extract source set name from path
        # Expected pattern: .../src/{sourceSetName}/kotlin/...
        parts = file_path.parts
        
        try:
            src_index = parts.index("src")
            if src_index + 1 < len(parts):
                source_set_name = parts[src_index + 1]
                return self.source_sets.get(source_set_name)
        except (ValueError, IndexError):
            pass
        
        return None
    
    async def find_expect_declarations(
        self,
        symbol_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find expect declarations in commonMain.
        
        Args:
            symbol_name: Optional filter by symbol name
            
        Returns:
            List of expect declarations with location info
            
        Example:
            >>> expects = await analyzer.find_expect_declarations("Platform")
        """
        expects = []
        
        # Search in commonMain source set
        common_main = self.source_sets.get("commonMain")
        if not common_main:
            logger.warning("commonMain source set not found")
            return expects
        
        # Scan Kotlin files for expect keyword
        kotlin_files = []
        for source_dir in common_main.source_dirs:
            kotlin_files.extend(list(source_dir.rglob("*.kt")))
        
        for file_path in kotlin_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                expect_matches = self._parse_expect_declarations(content, file_path)
                
                # Filter by symbol name if provided
                if symbol_name:
                    expect_matches = [
                        m for m in expect_matches if m["name"] == symbol_name
                    ]
                
                expects.extend(expect_matches)
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
        
        return expects
    
    def _parse_expect_declarations(
        self,
        content: str,
        file_path: Path
    ) -> List[Dict[str, Any]]:
        """Parse expect declarations from Kotlin source code.
        
        Args:
            content: Kotlin source code
            file_path: Path to the file
            
        Returns:
            List of expect declarations with metadata
        """
        expects = []
        lines = content.split("\n")
        
        # Regex patterns for expect declarations
        expect_class_pattern = re.compile(r'^\s*expect\s+class\s+(\w+)')
        expect_fun_pattern = re.compile(r'^\s*expect\s+fun\s+(\w+)')
        expect_val_pattern = re.compile(r'^\s*expect\s+val\s+(\w+)')
        expect_var_pattern = re.compile(r'^\s*expect\s+var\s+(\w+)')
        
        for line_num, line in enumerate(lines, start=1):
            # Check for expect class
            match = expect_class_pattern.search(line)
            if match:
                expects.append({
                    "name": match.group(1),
                    "kind": "class",
                    "file": str(file_path),
                    "line": line_num,
                    "signature": line.strip()
                })
                continue
            
            # Check for expect function
            match = expect_fun_pattern.search(line)
            if match:
                expects.append({
                    "name": match.group(1),
                    "kind": "function",
                    "file": str(file_path),
                    "line": line_num,
                    "signature": line.strip()
                })
                continue
            
            # Check for expect val/var
            match = expect_val_pattern.search(line) or expect_var_pattern.search(line)
            if match:
                expects.append({
                    "name": match.group(1),
                    "kind": "property",
                    "file": str(file_path),
                    "line": line_num,
                    "signature": line.strip()
                })
        
        return expects
    
    async def find_actual_implementations(
        self,
        symbol_name: str,
        symbol_kind: str
    ) -> Dict[str, Dict[str, Any]]:
        """Find actual implementations for an expect declaration.
        
        Args:
            symbol_name: Name of the symbol
            symbol_kind: Kind of symbol ("class", "function", "property")
            
        Returns:
            Map of source set name to actual declaration location
            
        Example:
            >>> actuals = await analyzer.find_actual_implementations(
            ...     "Platform",
            ...     "class"
            ... )
            >>> print(actuals["androidMain"]["file"])
        """
        actuals = {}
        
        # Search in platform-specific source sets (not commonMain)
        platform_source_sets = {
            name: ss for name, ss in self.source_sets.items()
            if not name.startswith("common")
        }
        
        for source_set_name, source_set in platform_source_sets.items():
            kotlin_files = []
            for source_dir in source_set.source_dirs:
                kotlin_files.extend(list(source_dir.rglob("*.kt")))
            
            for file_path in kotlin_files:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    actual_match = self._parse_actual_declaration(
                        content,
                        file_path,
                        symbol_name,
                        symbol_kind
                    )
                    
                    if actual_match:
                        actuals[source_set_name] = actual_match
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
        
        return actuals
    
    def _parse_actual_declaration(
        self,
        content: str,
        file_path: Path,
        symbol_name: str,
        symbol_kind: str
    ) -> Optional[Dict[str, Any]]:
        """Parse actual declaration for a specific symbol.
        
        Args:
            content: Kotlin source code
            file_path: Path to the file
            symbol_name: Name of symbol to find
            symbol_kind: Kind of symbol
            
        Returns:
            Actual declaration metadata if found
        """
        lines = content.split("\n")
        
        # Build pattern based on kind
        if symbol_kind == "class":
            pattern = re.compile(rf'^\s*actual\s+class\s+{re.escape(symbol_name)}\b')
        elif symbol_kind == "function":
            pattern = re.compile(rf'^\s*actual\s+fun\s+{re.escape(symbol_name)}\b')
        elif symbol_kind == "property":
            pattern = re.compile(rf'^\s*actual\s+(val|var)\s+{re.escape(symbol_name)}\b')
        else:
            return None
        
        for line_num, line in enumerate(lines, start=1):
            if pattern.search(line):
                return {
                    "name": symbol_name,
                    "kind": symbol_kind,
                    "file": str(file_path),
                    "line": line_num,
                    "signature": line.strip()
                }
        
        return None
    
    async def find_expect_actual_pairs(
        self,
        symbol_name: Optional[str] = None
    ) -> List[ExpectActualPair]:
        """Find all expect/actual pairs in the project.
        
        Args:
            symbol_name: Optional filter by symbol name
            
        Returns:
            List of ExpectActualPair objects
            
        Example:
            >>> pairs = await analyzer.find_expect_actual_pairs()
            >>> for pair in pairs:
            ...     print(f"{pair.name}: {len(pair.actual_locations)} actuals")
        """
        pairs = []
        
        # Find all expect declarations
        expects = await self.find_expect_declarations(symbol_name)
        
        # For each expect, find its actual implementations
        for expect_decl in expects:
            actuals = await self.find_actual_implementations(
                expect_decl["name"],
                expect_decl["kind"]
            )
            
            pair = ExpectActualPair(
                name=expect_decl["name"],
                kind=expect_decl["kind"],
                expect_location={
                    "file": expect_decl["file"],
                    "line": expect_decl["line"],
                    "sourceSet": "commonMain"
                },
                actual_locations=actuals,
                signature=expect_decl.get("signature")
            )
            
            pairs.append(pair)
        
        return pairs
    
    def validate_expect_actual_pair(
        self,
        pair: ExpectActualPair
    ) -> Tuple[bool, List[str]]:
        """Validate that expect/actual pair is consistent.
        
        Args:
            pair: ExpectActualPair to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
            
        Example:
            >>> is_valid, issues = analyzer.validate_expect_actual_pair(pair)
            >>> if not is_valid:
            ...     for issue in issues:
            ...         print(f"Issue: {issue}")
        """
        issues = []
        
        # Check if any actual implementations exist
        if not pair.actual_locations:
            issues.append(
                f"No actual implementations found for expect {pair.kind} '{pair.name}'"
            )
        
        # Check signature consistency (basic check)
        # More sophisticated signature validation would require AST parsing
        if pair.signature:
            for source_set, actual in pair.actual_locations.items():
                actual_sig = actual.get("signature", "")
                # Remove 'expect' and 'actual' keywords for comparison
                expect_sig_normalized = pair.signature.replace("expect", "").strip()
                actual_sig_normalized = actual_sig.replace("actual", "").strip()
                
                # Basic signature comparison (not perfect, but catches obvious mismatches)
                if expect_sig_normalized != actual_sig_normalized:
                    issues.append(
                        f"Signature mismatch in {source_set}: "
                        f"expect='{expect_sig_normalized}' vs actual='{actual_sig_normalized}'"
                    )
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def is_platform_specific_code(self, file_path: Path) -> bool:
        """Check if file contains platform-specific code.
        
        Args:
            file_path: Path to Kotlin file
            
        Returns:
            True if file is in a platform-specific source set
            
        Example:
            >>> is_platform = analyzer.is_platform_specific_code(
            ...     Path("src/androidMain/kotlin/Android.kt")
            ... )
            >>> print(is_platform)  # True
        """
        source_set = self.get_source_set_from_path(file_path)
        if source_set:
            return source_set.type != SourceSetType.COMMON
        return False
    
    def get_all_source_sets(self) -> List[SourceSet]:
        """Get all detected source sets in the project.
        
        Returns:
            List of SourceSet objects
            
        Example:
            >>> source_sets = analyzer.get_all_source_sets()
            >>> for ss in source_sets:
            ...     print(f"{ss.name}: {ss.type}")
        """
        return list(self.source_sets.values())
