"""Symbol and code location data models.

This module defines data structures for representing code symbols
and their locations in source files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from enum import Enum


class SymbolKind(Enum):
    """Kind of code symbol."""
    FILE = "file"
    MODULE = "module"
    NAMESPACE = "namespace"
    PACKAGE = "package"
    CLASS = "class"
    METHOD = "method"
    PROPERTY = "property"
    FIELD = "field"
    CONSTRUCTOR = "constructor"
    ENUM = "enum"
    INTERFACE = "interface"
    FUNCTION = "function"
    VARIABLE = "variable"
    CONSTANT = "constant"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    KEY = "key"
    NULL = "null"
    ENUM_MEMBER = "enumMember"
    STRUCT = "struct"
    EVENT = "event"
    OPERATOR = "operator"
    TYPE_PARAMETER = "typeParameter"
    UNKNOWN = "unknown"


@dataclass
class CodeLocation:
    """Represents a location in a source file.

    Attributes:
        file_path: Absolute path to the source file
        line: Line number (1-based)
        column: Column number (0-based)
        end_line: End line number for ranges (1-based, optional)
        end_column: End column number for ranges (0-based, optional)

    Example:
        >>> location = CodeLocation(
        ...     file_path=Path("/project/src/Main.kt"),
        ...     line=42,
        ...     column=4
        ... )
    """
    file_path: Path
    line: int
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __str__(self) -> str:
        """String representation of location.

        Returns:
            Human-readable location string

        Example:
            >>> str(location)
            '/project/src/Main.kt:42:4'
        """
        result = f"{self.file_path}:{self.line}:{self.column}"
        if self.end_line is not None:
            result += f"-{self.end_line}:{self.end_column or 0}"
        return result

    def is_range(self) -> bool:
        """Check if this location represents a range.

        Returns:
            True if end_line is specified

        Example:
            >>> if location.is_range():
            ...     print("This is a range location")
        """
        return self.end_line is not None


@dataclass
class Symbol:
    """Represents a code symbol (class, function, variable, etc.).

    Attributes:
        name: Symbol name
        kind: Kind of symbol (class, method, etc.)
        location: Location where symbol is defined
        container_name: Name of containing symbol (e.g., class name for methods)
        detail: Additional detail about the symbol (e.g., signature)
        documentation: Documentation string for the symbol

    Example:
        >>> symbol = Symbol(
        ...     name="getUserById",
        ...     kind=SymbolKind.FUNCTION,
        ...     location=CodeLocation(Path("UserRepo.kt"), 15, 4),
        ...     container_name="UserRepository",
        ...     detail="fun getUserById(id: String): User"
        ... )
    """
    name: str
    kind: SymbolKind
    location: CodeLocation
    container_name: Optional[str] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None

    def __str__(self) -> str:
        """String representation of symbol.

        Returns:
            Human-readable symbol string

        Example:
            >>> str(symbol)
            'getUserById (function) in UserRepository at UserRepo.kt:15:4'
        """
        result = f"{self.name} ({self.kind.value})"
        if self.container_name:
            result += f" in {self.container_name}"
        result += f" at {self.location}"
        return result

    def get_qualified_name(self) -> str:
        """Get fully qualified name of the symbol.

        Returns:
            Qualified name with container

        Example:
            >>> symbol.get_qualified_name()
            'UserRepository.getUserById'
        """
        if self.container_name:
            return f"{self.container_name}.{self.name}"
        return self.name

    def is_class_member(self) -> bool:
        """Check if this symbol is a class member.

        Returns:
            True if kind is method, property, field, or constructor

        Example:
            >>> if symbol.is_class_member():
            ...     print("This is a class member")
        """
        return self.kind in {
            SymbolKind.METHOD,
            SymbolKind.PROPERTY,
            SymbolKind.FIELD,
            SymbolKind.CONSTRUCTOR,
        }


@dataclass
class SymbolReference:
    """Represents a reference to a symbol.

    Attributes:
        symbol: The symbol being referenced
        location: Location of the reference
        is_definition: True if this is the definition location
        is_write: True if this is a write reference

    Example:
        >>> ref = SymbolReference(
        ...     symbol=user_symbol,
        ...     location=CodeLocation(Path("Main.kt"), 20, 10),
        ...     is_definition=False
        ... )
    """
    symbol: Symbol
    location: CodeLocation
    is_definition: bool = False
    is_write: bool = False

    def __str__(self) -> str:
        """String representation of reference.

        Returns:
            Human-readable reference string
        """
        ref_type = "definition" if self.is_definition else "reference"
        if self.is_write and not self.is_definition:
            ref_type = "write"
        return f"{ref_type} to {self.symbol.name} at {self.location}"


@dataclass
class SymbolSearchResult:
    """Result from a symbol search operation.

    Attributes:
        symbols: List of symbols found
        query: Original search query
        total_count: Total number of results (may exceed len(symbols) if truncated)

    Example:
        >>> result = SymbolSearchResult(
        ...     symbols=[symbol1, symbol2],
        ...     query="Repository",
        ...     total_count=2
        ... )
    """
    symbols: List[Symbol]
    query: str
    total_count: int

    def is_truncated(self) -> bool:
        """Check if results were truncated.

        Returns:
            True if total_count exceeds number of symbols

        Example:
            >>> if result.is_truncated():
            ...     print(f"Showing {len(result.symbols)} of {result.total_count}")
        """
        return self.total_count > len(self.symbols)
