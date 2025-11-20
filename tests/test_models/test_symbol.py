import pytest
from pathlib import Path
from kortex_mcp.models.symbol import Symbol, SymbolKind, CodeLocation

class TestCodeLocation:
    def test_create_location(self):
        loc = CodeLocation(
            file_path=Path("/test/file.kt"),
            line=10,
            column=5
        )
        assert loc.file_path == Path("/test/file.kt")
        assert loc.line == 10
        assert loc.column == 5
        assert loc.end_line is None
        assert not loc.is_range()

    def test_create_range_location(self):
        loc = CodeLocation(
            file_path=Path("/test/file.kt"),
            line=10,
            column=5,
            end_line=12,
            end_column=0
        )
        assert loc.end_line == 12
        assert loc.is_range()

    def test_string_representation(self):
        loc = CodeLocation(
            file_path=Path("/test/file.kt"),
            line=10,
            column=5
        )
        assert str(loc) == "/test/file.kt:10:5"

    def test_range_string_representation(self):
        loc = CodeLocation(
            file_path=Path("/test/file.kt"),
            line=10,
            column=5,
            end_line=12,
            end_column=0
        )
        assert str(loc) == "/test/file.kt:10:5-12:0"

class TestSymbol:
    def test_create_symbol(self):
        loc = CodeLocation(Path("/test/file.kt"), 10)
        sym = Symbol(
            name="MyClass",
            kind=SymbolKind.CLASS,
            location=loc
        )
        assert sym.name == "MyClass"
        assert sym.kind == SymbolKind.CLASS
        assert sym.location == loc
        assert sym.container_name is None

    def test_symbol_with_container(self):
        loc = CodeLocation(Path("/test/file.kt"), 10)
        sym = Symbol(
            name="myMethod",
            kind=SymbolKind.METHOD,
            location=loc,
            container_name="MyClass"
        )
        assert sym.container_name == "MyClass"

    def test_symbol_kind_values(self):
        assert SymbolKind.CLASS.value == "class"
        assert SymbolKind.METHOD.value == "method"
        assert SymbolKind.UNKNOWN.value == "unknown"
