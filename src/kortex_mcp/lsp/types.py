"""LSP protocol type conversions and utilities.

This module provides utility functions for converting between internal
data models and LSP protocol types, as well as helper functions for
working with LSP data structures.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import quote, unquote

from ..models.lsp import (
    Position, Range, Location, TextDocumentIdentifier,
    TextDocumentPositionParams, SymbolInformation, ReferenceParams,
    WorkspaceEdit, TextEdit, LSPSymbolKind
)


def path_to_uri(path: Path) -> str:
    """Convert file path to LSP file URI.

    Args:
        path: File system path

    Returns:
        file:// URI string

    Example:
        >>> path_to_uri(Path("/path/to/file.kt"))
        'file:///path/to/file.kt'
    """
    # Convert to absolute path and ensure forward slashes
    abs_path = path.resolve()
    path_str = abs_path.as_posix()
    
    # Encode special characters but keep forward slashes
    encoded = quote(path_str, safe='/')
    
    # Add file:// prefix
    return f"file://{encoded}"


def uri_to_path(uri: str) -> Path:
    """Convert LSP file URI to file path.

    Args:
        uri: file:// URI string

    Returns:
        Path object

    Example:
        >>> uri_to_path("file:///path/to/file.kt")
        Path('/path/to/file.kt')
    """
    # Remove file:// prefix
    if uri.startswith("file://"):
        uri = uri[7:]
    
    # Decode URL encoding
    decoded = unquote(uri)
    
    return Path(decoded)


def create_text_document_identifier(path: Path) -> TextDocumentIdentifier:
    """Create TextDocumentIdentifier from file path.

    Args:
        path: File path

    Returns:
        TextDocumentIdentifier for the file

    Example:
        >>> doc_id = create_text_document_identifier(Path("/path/to/file.kt"))
    """
    return TextDocumentIdentifier(uri=path_to_uri(path))


def create_position(line: int, character: int) -> Position:
    """Create Position object.

    Args:
        line: Line number (0-based)
        character: Character offset (0-based)

    Returns:
        Position object

    Example:
        >>> pos = create_position(10, 5)
    """
    return Position(line=line, character=character)


def create_range(
    start_line: int,
    start_char: int,
    end_line: int,
    end_char: int
) -> Range:
    """Create Range object.

    Args:
        start_line: Start line (0-based)
        start_char: Start character (0-based)
        end_line: End line (0-based)
        end_char: End character (0-based)

    Returns:
        Range object

    Example:
        >>> range = create_range(10, 5, 10, 15)
    """
    return Range(
        start=Position(line=start_line, character=start_char),
        end=Position(line=end_line, character=end_char)
    )


def create_location(path: Path, range: Range) -> Location:
    """Create Location object from path and range.

    Args:
        path: File path
        range: Range in the file

    Returns:
        Location object

    Example:
        >>> location = create_location(
        ...     Path("/path/to/file.kt"),
        ...     create_range(10, 5, 10, 15)
        ... )
    """
    return Location(uri=path_to_uri(path), range=range)


def create_text_document_position_params(
    path: Path,
    line: int,
    character: int
) -> TextDocumentPositionParams:
    """Create TextDocumentPositionParams.

    Args:
        path: File path
        line: Line number (0-based)
        character: Character offset (0-based)

    Returns:
        TextDocumentPositionParams object

    Example:
        >>> params = create_text_document_position_params(
        ...     Path("/path/to/file.kt"), 10, 5
        ... )
    """
    return TextDocumentPositionParams(
        textDocument=create_text_document_identifier(path),
        position=create_position(line, character)
    )


def create_reference_params(
    path: Path,
    line: int,
    character: int,
    include_declaration: bool = True
) -> ReferenceParams:
    """Create ReferenceParams for finding references.

    Args:
        path: File path
        line: Line number (0-based)
        character: Character offset (0-based)
        include_declaration: Include symbol declaration in results

    Returns:
        ReferenceParams object

    Example:
        >>> params = create_reference_params(
        ...     Path("/path/to/file.kt"), 10, 5
        ... )
    """
    return ReferenceParams(
        textDocument=create_text_document_identifier(path),
        position=create_position(line, character),
        includeDeclaration=include_declaration
    )


def symbol_kind_to_string(kind: int) -> str:
    """Convert LSP SymbolKind integer to readable string.

    Args:
        kind: LSP SymbolKind integer value

    Returns:
        Human-readable symbol kind name

    Example:
        >>> symbol_kind_to_string(5)
        'Class'
        >>> symbol_kind_to_string(12)
        'Function'
    """
    kind_map = {
        LSPSymbolKind.File: "File",
        LSPSymbolKind.Module: "Module",
        LSPSymbolKind.Namespace: "Namespace",
        LSPSymbolKind.Package: "Package",
        LSPSymbolKind.Class: "Class",
        LSPSymbolKind.Method: "Method",
        LSPSymbolKind.Property: "Property",
        LSPSymbolKind.Field: "Field",
        LSPSymbolKind.Constructor: "Constructor",
        LSPSymbolKind.Enum: "Enum",
        LSPSymbolKind.Interface: "Interface",
        LSPSymbolKind.Function: "Function",
        LSPSymbolKind.Variable: "Variable",
        LSPSymbolKind.Constant: "Constant",
        LSPSymbolKind.String: "String",
        LSPSymbolKind.Number: "Number",
        LSPSymbolKind.Boolean: "Boolean",
        LSPSymbolKind.Array: "Array",
        LSPSymbolKind.Object: "Object",
        LSPSymbolKind.Key: "Key",
        LSPSymbolKind.Null: "Null",
        LSPSymbolKind.EnumMember: "EnumMember",
        LSPSymbolKind.Struct: "Struct",
        LSPSymbolKind.Event: "Event",
        LSPSymbolKind.Operator: "Operator",
        LSPSymbolKind.TypeParameter: "TypeParameter",
    }
    return kind_map.get(kind, f"Unknown({kind})")


def format_symbol_info(symbol: SymbolInformation) -> str:
    """Format symbol information as human-readable string.

    Args:
        symbol: Symbol information

    Returns:
        Formatted string with symbol details

    Example:
        >>> formatted = format_symbol_info(symbol)
        >>> print(formatted)
        'MyClass (Class) at /path/to/file.kt:10:5'
    """
    kind = symbol_kind_to_string(symbol.kind)
    path = uri_to_path(symbol.location.uri)
    line = symbol.location.range.start.line + 1  # Convert to 1-based
    char = symbol.location.range.start.character + 1  # Convert to 1-based
    
    result = f"{symbol.name} ({kind}) at {path}:{line}:{char}"
    
    if symbol.containerName:
        result = f"{result} in {symbol.containerName}"
    
    return result


def format_location(location: Location) -> str:
    """Format location as human-readable string.

    Args:
        location: Location object

    Returns:
        Formatted string with file path and position

    Example:
        >>> formatted = format_location(location)
        >>> print(formatted)
        '/path/to/file.kt:10:5-10:15'
    """
    path = uri_to_path(location.uri)
    start = location.range.start
    end = location.range.end
    
    start_line = start.line + 1  # Convert to 1-based
    start_char = start.character + 1
    end_line = end.line + 1
    end_char = end.character + 1
    
    return f"{path}:{start_line}:{start_char}-{end_line}:{end_char}"


def parse_location_string(location_str: str) -> Optional[tuple[Path, int, int]]:
    """Parse location string to path, line, and character.

    Args:
        location_str: Location string like "/path/to/file.kt:10:5"

    Returns:
        Tuple of (path, line, character) or None if invalid

    Example:
        >>> path, line, char = parse_location_string("/path/to/file.kt:10:5")
        >>> print(f"{path} at line {line}, char {char}")
        /path/to/file.kt at line 10, char 5
    """
    try:
        # Split path and position
        parts = location_str.rsplit(':', 2)
        if len(parts) != 3:
            return None
        
        path = Path(parts[0])
        line = int(parts[1]) - 1  # Convert to 0-based
        char = int(parts[2]) - 1  # Convert to 0-based
        
        return (path, line, char)
    except (ValueError, IndexError):
        return None


def create_text_edit(
    start_line: int,
    start_char: int,
    end_line: int,
    end_char: int,
    new_text: str
) -> TextEdit:
    """Create TextEdit object.

    Args:
        start_line: Start line (0-based)
        start_char: Start character (0-based)
        end_line: End line (0-based)
        end_char: End character (0-based)
        new_text: Replacement text

    Returns:
        TextEdit object

    Example:
        >>> edit = create_text_edit(10, 5, 10, 15, "newText")
    """
    return TextEdit(
        range=create_range(start_line, start_char, end_line, end_char),
        newText=new_text
    )


def create_workspace_edit(
    edits_by_file: Dict[Path, List[TextEdit]]
) -> WorkspaceEdit:
    """Create WorkspaceEdit from file paths and edits.

    Args:
        edits_by_file: Map of file paths to list of text edits

    Returns:
        WorkspaceEdit object

    Example:
        >>> edit = create_workspace_edit({
        ...     Path("/path/to/file.kt"): [edit1, edit2]
        ... })
    """
    changes = {
        path_to_uri(path): edits
        for path, edits in edits_by_file.items()
    }
    return WorkspaceEdit(changes=changes)


def normalize_line_endings(text: str) -> str:
    """Normalize line endings to LF (\\n).

    Args:
        text: Text with potentially mixed line endings

    Returns:
        Text with normalized line endings

    Example:
        >>> normalized = normalize_line_endings("line1\\r\\nline2\\r\\nline3")
    """
    return text.replace('\r\n', '\n').replace('\r', '\n')


def offset_to_position(text: str, offset: int) -> Position:
    """Convert byte offset to line/character position.

    Args:
        text: Document text
        offset: Byte offset in the text

    Returns:
        Position object

    Example:
        >>> pos = offset_to_position("line1\\nline2\\nline3", 12)
    """
    lines = text[:offset].split('\n')
    line = len(lines) - 1
    character = len(lines[-1]) if lines else 0
    return Position(line=line, character=character)


def position_to_offset(text: str, position: Position) -> int:
    """Convert line/character position to byte offset.

    Args:
        text: Document text
        position: Position in the document

    Returns:
        Byte offset

    Example:
        >>> offset = position_to_offset("line1\\nline2\\nline3", Position(1, 0))
    """
    lines = text.split('\n')
    offset = 0
    
    # Add length of all lines before target line
    for i in range(min(position.line, len(lines))):
        offset += len(lines[i]) + 1  # +1 for newline
    
    # Add character offset within target line
    if position.line < len(lines):
        offset += min(position.character, len(lines[position.line]))
    
    return offset
