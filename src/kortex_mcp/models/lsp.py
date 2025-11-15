"""LSP protocol data models.

This module defines data structures for Language Server Protocol
requests and responses.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
from pathlib import Path


@dataclass
class Position:
    """Position in a text document (LSP spec).

    Attributes:
        line: Line position (0-based)
        character: Character offset on a line (0-based, UTF-16 code units)

    Example:
        >>> pos = Position(line=10, character=5)
    """
    line: int
    character: int

    def to_dict(self) -> Dict[str, int]:
        """Convert to LSP protocol dictionary.

        Returns:
            Dictionary with line and character keys
        """
        return {"line": self.line, "character": self.character}


@dataclass
class Range:
    """Range in a text document (LSP spec).

    Attributes:
        start: Start position
        end: End position

    Example:
        >>> range = Range(
        ...     start=Position(10, 5),
        ...     end=Position(10, 15)
        ... )
    """
    start: Position
    end: Position

    def to_dict(self) -> Dict[str, Dict[str, int]]:
        """Convert to LSP protocol dictionary.

        Returns:
            Dictionary with start and end position dicts
        """
        return {
            "start": self.start.to_dict(),
            "end": self.end.to_dict()
        }


@dataclass
class Location:
    """Location in a workspace (LSP spec).

    Attributes:
        uri: Document URI (file:// URI)
        range: Range in the document

    Example:
        >>> location = Location(
        ...     uri="file:///path/to/file.kt",
        ...     range=Range(Position(10, 5), Position(10, 15))
        ... )
    """
    uri: str
    range: Range

    def to_dict(self) -> Dict[str, Any]:
        """Convert to LSP protocol dictionary.

        Returns:
            Dictionary with uri and range
        """
        return {
            "uri": self.uri,
            "range": self.range.to_dict()
        }

    def get_path(self) -> Path:
        """Extract file path from URI.

        Returns:
            Path object from the URI

        Example:
            >>> location.get_path()
            Path('/path/to/file.kt')
        """
        # Remove file:// prefix
        path_str = self.uri
        if path_str.startswith("file://"):
            path_str = path_str[7:]
        return Path(path_str)


@dataclass
class TextDocumentIdentifier:
    """Identifies a text document (LSP spec).

    Attributes:
        uri: Document URI

    Example:
        >>> doc = TextDocumentIdentifier(uri="file:///path/to/file.kt")
    """
    uri: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to LSP protocol dictionary.

        Returns:
            Dictionary with uri key
        """
        return {"uri": self.uri}


@dataclass
class TextDocumentPositionParams:
    """Parameters for text document position requests (LSP spec).

    Used for requests like goto definition, hover, etc.

    Attributes:
        textDocument: Document identifier
        position: Position in document

    Example:
        >>> params = TextDocumentPositionParams(
        ...     textDocument=TextDocumentIdentifier("file:///path/to/file.kt"),
        ...     position=Position(10, 5)
        ... )
    """
    textDocument: TextDocumentIdentifier
    position: Position

    def to_dict(self) -> Dict[str, Any]:
        """Convert to LSP protocol dictionary.

        Returns:
            Dictionary with textDocument and position
        """
        return {
            "textDocument": self.textDocument.to_dict(),
            "position": self.position.to_dict()
        }


@dataclass
class SymbolInformation:
    """Symbol information from workspace/symbol request (LSP spec).

    Attributes:
        name: Symbol name
        kind: Symbol kind (integer from LSP SymbolKind enum)
        location: Symbol location
        containerName: Name of containing symbol (optional)

    Example:
        >>> symbol_info = SymbolInformation(
        ...     name="MyClass",
        ...     kind=5,  # Class
        ...     location=location,
        ...     containerName="com.example"
        ... )
    """
    name: str
    kind: int
    location: Location
    containerName: Optional[str] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SymbolInformation":
        """Create from LSP protocol dictionary.

        Args:
            data: Dictionary from LSP response

        Returns:
            SymbolInformation instance
        """
        location_data = data["location"]
        range_data = location_data["range"]
        
        return SymbolInformation(
            name=data["name"],
            kind=data["kind"],
            location=Location(
                uri=location_data["uri"],
                range=Range(
                    start=Position(**range_data["start"]),
                    end=Position(**range_data["end"])
                )
            ),
            containerName=data.get("containerName")
        )


@dataclass
class ReferenceParams:
    """Parameters for textDocument/references request (LSP spec).

    Attributes:
        textDocument: Document identifier
        position: Position of the symbol
        includeDeclaration: Include declaration in results

    Example:
        >>> params = ReferenceParams(
        ...     textDocument=TextDocumentIdentifier("file:///path/to/file.kt"),
        ...     position=Position(10, 5),
        ...     includeDeclaration=True
        ... )
    """
    textDocument: TextDocumentIdentifier
    position: Position
    includeDeclaration: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to LSP protocol dictionary.

        Returns:
            Dictionary for LSP request
        """
        return {
            "textDocument": self.textDocument.to_dict(),
            "position": self.position.to_dict(),
            "context": {"includeDeclaration": self.includeDeclaration}
        }


@dataclass
class WorkspaceEdit:
    """Workspace edit for code modifications (LSP spec).

    Attributes:
        changes: Map of document URI to list of text edits

    Example:
        >>> edit = WorkspaceEdit(
        ...     changes={
        ...         "file:///path/to/file.kt": [text_edit1, text_edit2]
        ...     }
        ... )
    """
    changes: Dict[str, List["TextEdit"]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to LSP protocol dictionary.

        Returns:
            Dictionary for LSP workspace/applyEdit
        """
        return {
            "changes": {
                uri: [edit.to_dict() for edit in edits]
                for uri, edits in self.changes.items()
            }
        }


@dataclass
class TextEdit:
    """Text edit for document modification (LSP spec).

    Attributes:
        range: Range to replace
        newText: New text for the range

    Example:
        >>> edit = TextEdit(
        ...     range=Range(Position(10, 0), Position(10, 10)),
        ...     newText="new content"
        ... )
    """
    range: Range
    newText: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to LSP protocol dictionary.

        Returns:
            Dictionary with range and newText
        """
        return {
            "range": self.range.to_dict(),
            "newText": self.newText
        }


# LSP SymbolKind enum values
class LSPSymbolKind:
    """LSP SymbolKind enum values."""
    File = 1
    Module = 2
    Namespace = 3
    Package = 4
    Class = 5
    Method = 6
    Property = 7
    Field = 8
    Constructor = 9
    Enum = 10
    Interface = 11
    Function = 12
    Variable = 13
    Constant = 14
    String = 15
    Number = 16
    Boolean = 17
    Array = 18
    Object = 19
    Key = 20
    Null = 21
    EnumMember = 22
    Struct = 23
    Event = 24
    Operator = 25
    TypeParameter = 26
