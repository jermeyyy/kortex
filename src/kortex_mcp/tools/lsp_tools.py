"""LSP-based MCP tools for code navigation.

This module provides MCP tools for symbol search, go-to-definition,
and find references using Language Server Protocol.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio

from ..lsp.manager import LSPManager
from ..models.lsp import Location
from ..analyzers.kmp_analyzer import KMPAnalyzer
from ..utils.logging import get_logger
from .base import with_timeout, ToolError, ToolValidationError


logger = get_logger(__name__)


class LSPTools:
    """Container for LSP-based MCP tools.
    
    Provides symbol search, navigation, and reference finding functionality
    using LSP servers managed by LSPManager.
    """
    
    def __init__(self, lsp_manager: LSPManager, kmp_analyzer: Optional[KMPAnalyzer] = None):
        """Initialize LSP tools.
        
        Args:
            lsp_manager: LSP manager instance for server lifecycle
            kmp_analyzer: Optional KMP analyzer for expect/actual detection
        """
        self.lsp_manager = lsp_manager
        self.kmp_analyzer = kmp_analyzer
    
    @with_timeout(30.0)
    async def search_symbols(
        self,
        query: str,
        language: str = "kotlin"
    ) -> Dict[str, Any]:
        """Search for symbols across the workspace.
        
        MCP Tool for workspace-wide symbol search using LSP.
        
        Args:
            query: Symbol name to search for (e.g., "Repository")
            language: Language server to use (default: "kotlin")
            
        Returns:
            Dictionary with search results:
            {
                "symbols": [
                    {
                        "name": str,
                        "kind": str,
                        "file": str,
                        "line": int,
                        "character": int,
                        "container": str
                    }
                ],
                "count": int,
                "query": str
            }
            
        Raises:
            ToolValidationError: If query is empty
            ToolError: If LSP server is not available
            
        Example:
            >>> tools = LSPTools(manager)
            >>> result = await tools.search_symbols("Repository")
            >>> print(f"Found {result['count']} symbols")
            >>> for symbol in result['symbols']:
            ...     print(f"{symbol['name']} at {symbol['file']}:{symbol['line']}")
        """
        # Validate input
        if not query or not query.strip():
            raise ToolValidationError(
                tool_name="search_symbols",
                field="query",
                reason="Query cannot be empty"
            )
        
        query = query.strip()
        
        logger.info(f"Searching for symbols: '{query}' (language: {language})")
        
        try:
            # Get LSP client for the language
            client = self.lsp_manager.get_client(language)
            
            if not client:
                raise ToolError(
                    f"LSP server for '{language}' is not available",
                    details={"language": language},
                    tool_name="search_symbols"
                )
            
            if not client.is_running():
                raise ToolError(
                    f"LSP server for '{language}' is not running",
                    details={"language": language},
                    tool_name="search_symbols"
                )
            
            # Search for symbols
            symbols = await client.workspace_symbols(query)
            
            # Format results
            formatted_symbols = []
            for symbol in symbols:
                # Convert URI to path
                file_path = symbol.location.uri
                if file_path.startswith("file://"):
                    file_path = file_path[7:]
                
                formatted_symbols.append({
                    "name": symbol.name,
                    "kind": self._format_symbol_kind(symbol.kind),
                    "file": file_path,
                    "line": symbol.location.range.start.line,
                    "character": symbol.location.range.start.character,
                    "container": symbol.containerName or ""
                })
            
            result = {
                "symbols": formatted_symbols,
                "count": len(formatted_symbols),
                "query": query
            }
            
            logger.info(f"Found {len(formatted_symbols)} symbols matching '{query}'")
            return result
            
        except ToolValidationError:
            raise
        except ToolError:
            raise
        except Exception as e:
            logger.error(f"Error searching symbols: {e}")
            raise ToolError(
                f"Failed to search symbols: {str(e)}",
                details={"query": query, "language": language},
                tool_name="search_symbols"
            ) from e
    
    @with_timeout(30.0)
    async def goto_definition(
        self,
        file: str,
        line: int,
        character: int,
        language: str = "kotlin"
    ) -> Dict[str, Any]:
        """Navigate to symbol definition.
        
        MCP Tool for go-to-definition using LSP.
        
        Args:
            file: File path or URI
            line: Line number (0-based)
            character: Character position (0-based)
            language: Language server to use (default: "kotlin")
            
        Returns:
            Dictionary with definition location:
            {
                "found": bool,
                "definition": {
                    "file": str,
                    "line": int,
                    "character": int,
                    "symbol": str  # Optional
                } or None
            }
            
        Raises:
            ToolValidationError: If file doesn't exist or position is invalid
            ToolError: If LSP server is not available
            
        Example:
            >>> result = await tools.goto_definition(
            ...     file="/project/Repository.kt",
            ...     line=15,
            ...     character=10
            ... )
            >>> if result['found']:
            ...     defn = result['definition']
            ...     print(f"Definition at {defn['file']}:{defn['line']}")
        """
        # Validate inputs
        if line < 0:
            raise ToolValidationError(
                tool_name="goto_definition",
                field="line",
                reason="Line number must be >= 0"
            )
        
        if character < 0:
            raise ToolValidationError(
                tool_name="goto_definition",
                field="character",
                reason="Character position must be >= 0"
            )
        
        # Convert file path to URI
        file_uri = self._path_to_uri(file)
        
        # Check if file exists
        file_path = Path(file)
        if not file_path.exists():
            raise ToolValidationError(
                tool_name="goto_definition",
                field="file",
                reason=f"File does not exist: {file}"
            )
        
        logger.info(f"Finding definition at {file}:{line}:{character} (language: {language})")
        
        try:
            # Get LSP client
            client = self.lsp_manager.get_client(language)
            
            if not client or not client.is_running():
                raise ToolError(
                    f"LSP server for '{language}' is not available",
                    details={"language": language},
                    tool_name="goto_definition"
                )
            
            # Request definition
            location = await client.go_to_definition(file_uri, line, character)
            
            if location:
                # Convert URI to path
                def_file = location.uri
                if def_file.startswith("file://"):
                    def_file = def_file[7:]
                
                result = {
                    "found": True,
                    "definition": {
                        "file": def_file,
                        "line": location.range.start.line,
                        "character": location.range.start.character
                    }
                }
                
                logger.info(f"Definition found at {def_file}:{location.range.start.line}")
                return result
            else:
                logger.info("No definition found")
                return {
                    "found": False,
                    "definition": None
                }
                
        except ToolValidationError:
            raise
        except ToolError:
            raise
        except Exception as e:
            logger.error(f"Error finding definition: {e}")
            raise ToolError(
                f"Failed to find definition: {str(e)}",
                details={"file": file, "line": line, "character": character},
                tool_name="goto_definition"
            ) from e
    
    @with_timeout(30.0)
    async def find_references(
        self,
        file: str,
        line: int,
        character: int,
        include_declaration: bool = True,
        language: str = "kotlin"
    ) -> Dict[str, Any]:
        """Find all references to a symbol.
        
        MCP Tool for finding symbol references using LSP.
        
        Args:
            file: File path or URI
            line: Line number (0-based)
            character: Character position (0-based)
            include_declaration: Include the symbol declaration (default: True)
            language: Language server to use (default: "kotlin")
            
        Returns:
            Dictionary with reference locations:
            {
                "references": [
                    {
                        "file": str,
                        "line": int,
                        "character": int
                    }
                ],
                "count": int
            }
            
        Raises:
            ToolValidationError: If file doesn't exist or position is invalid
            ToolError: If LSP server is not available
            
        Example:
            >>> result = await tools.find_references(
            ...     file="/project/Repository.kt",
            ...     line=15,
            ...     character=10
            ... )
            >>> print(f"Found {result['count']} references")
            >>> for ref in result['references']:
            ...     print(f"  {ref['file']}:{ref['line']}")
        """
        # Validate inputs
        if line < 0:
            raise ToolValidationError(
                tool_name="find_references",
                field="line",
                reason="Line number must be >= 0"
            )
        
        if character < 0:
            raise ToolValidationError(
                tool_name="find_references",
                field="character",
                reason="Character position must be >= 0"
            )
        
        # Convert file path to URI
        file_uri = self._path_to_uri(file)
        
        # Check if file exists
        file_path = Path(file)
        if not file_path.exists():
            raise ToolValidationError(
                tool_name="find_references",
                field="file",
                reason=f"File does not exist: {file}"
            )
        
        logger.info(f"Finding references at {file}:{line}:{character} (language: {language})")
        
        try:
            # Get LSP client
            client = self.lsp_manager.get_client(language)
            
            if not client or not client.is_running():
                raise ToolError(
                    f"LSP server for '{language}' is not available",
                    details={"language": language},
                    tool_name="find_references"
                )
            
            # Request references
            locations = await client.find_references(
                file_uri,
                line,
                character,
                include_declaration
            )
            
            # Format results
            formatted_refs = []
            for location in locations:
                # Convert URI to path
                ref_file = location.uri
                if ref_file.startswith("file://"):
                    ref_file = ref_file[7:]
                
                formatted_refs.append({
                    "file": ref_file,
                    "line": location.range.start.line,
                    "character": location.range.start.character
                })
            
            result = {
                "references": formatted_refs,
                "count": len(formatted_refs)
            }
            
            logger.info(f"Found {len(formatted_refs)} references")
            return result
            
        except ToolValidationError:
            raise
        except ToolError:
            raise
        except Exception as e:
            logger.error(f"Error finding references: {e}")
            raise ToolError(
                f"Failed to find references: {str(e)}",
                details={"file": file, "line": line, "character": character},
                tool_name="find_references"
            ) from e
    
    def _format_symbol_kind(self, kind: int) -> str:
        """Convert LSP symbol kind integer to readable string.
        
        Args:
            kind: LSP SymbolKind integer
            
        Returns:
            Human-readable symbol kind
        """
        kinds = {
            1: "file", 2: "module", 3: "namespace", 4: "package",
            5: "class", 6: "method", 7: "property", 8: "field",
            9: "constructor", 10: "enum", 11: "interface", 12: "function",
            13: "variable", 14: "constant", 15: "string", 16: "number",
            17: "boolean", 18: "array", 19: "object", 20: "key",
            21: "null", 22: "enum_member", 23: "struct", 24: "event",
            25: "operator", 26: "type_parameter",
        }
        return kinds.get(kind, "unknown")
    
    def _path_to_uri(self, path: str) -> str:
        """Convert file path to file:// URI.
        
        Args:
            path: File path (absolute or relative)
            
        Returns:
            file:// URI
        """
        if path.startswith("file://"):
            return path
        
        # Convert to absolute path
        abs_path = Path(path).resolve()
        return f"file://{abs_path}"

    @with_timeout(45.0)
    async def cross_language_symbol_lookup(
        self,
        query: str,
        languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search for symbols across multiple languages (Kotlin, Swift, Objective-C).
        
        MCP Tool for cross-platform symbol search that queries multiple LSP servers
        to find symbol definitions across Kotlin, Swift, and Objective-C codebases.
        
        Args:
            query: Symbol name to search for (e.g., "SharedRepository")
            languages: List of languages to search (default: ["kotlin", "swift", "objective-c"])
            
        Returns:
            Dictionary with results grouped by language:
            {
                "query": str,
                "total_count": int,
                "results": {
                    "kotlin": [...],
                    "swift": [...],
                    "objective-c": [...]
                }
            }
            
        Raises:
            ToolValidationError: If query is empty
            ToolError: If no LSP servers are available
            
        Example:
            >>> tools = LSPTools(manager, analyzer)
            >>> result = await tools.cross_language_symbol_lookup("SharedRepository")
            >>> print(f"Found in {len(result['results'])} languages")
            >>> for lang, symbols in result['results'].items():
            ...     print(f"{lang}: {len(symbols)} symbols")
        """
        # Validate input
        if not query or not query.strip():
            raise ToolValidationError(
                tool_name="cross_language_symbol_lookup",
                field="query",
                reason="Query cannot be empty"
            )
        
        query = query.strip()
        
        # Default to all supported languages
        if languages is None:
            languages = ["kotlin", "swift", "objective-c"]
        
        logger.info(f"Cross-language symbol lookup: '{query}' across {languages}")
        
        results = {}
        total_count = 0
        errors = []
        
        # Query each language server
        for language in languages:
            try:
                client = self.lsp_manager.get_client(language)
                
                if not client or not client.is_running():
                    logger.warning(f"LSP server for '{language}' is not available, skipping")
                    errors.append(f"{language}: server not available")
                    results[language] = []
                    continue
                
                # Search for symbols
                symbols = await client.workspace_symbols(query)
                
                # Format results
                formatted_symbols = []
                for symbol in symbols:
                    # Convert URI to path
                    file_path = symbol.location.uri
                    if file_path.startswith("file://"):
                        file_path = file_path[7:]
                    
                    formatted_symbols.append({
                        "name": symbol.name,
                        "kind": self._format_symbol_kind(symbol.kind),
                        "file": file_path,
                        "line": symbol.location.range.start.line,
                        "character": symbol.location.range.start.character,
                        "container": symbol.containerName or "",
                        "language": language
                    })
                
                results[language] = formatted_symbols
                total_count += len(formatted_symbols)
                logger.info(f"Found {len(formatted_symbols)} symbols in {language}")
                
            except Exception as e:
                logger.error(f"Error searching {language}: {e}")
                errors.append(f"{language}: {str(e)}")
                results[language] = []
        
        # Check if any results were found
        if total_count == 0 and len(errors) == len(languages):
            raise ToolError(
                "No LSP servers available for cross-language search",
                details={"languages": languages, "errors": errors},
                tool_name="cross_language_symbol_lookup"
            )
        
        result = {
            "query": query,
            "total_count": total_count,
            "results": results
        }
        
        if errors:
            result["errors"] = errors
        
        logger.info(f"Cross-language lookup complete: {total_count} total symbols")
        return result

    @with_timeout(30.0)
    async def navigate_expect_actual(
        self,
        symbol_name: str
    ) -> Dict[str, Any]:
        """Navigate between expect declarations and actual implementations.
        
        MCP Tool for finding expect/actual pairs in Kotlin Multiplatform projects.
        Given a symbol name, finds the expect declaration in commonMain and all
        actual implementations across platform-specific source sets.
        
        Args:
            symbol_name: Name of the expect/actual symbol (e.g., "Platform")
            
        Returns:
            Dictionary with expect location and actual implementations:
            {
                "symbol": str,
                "expect": {
                    "file": str,
                    "line": int,
                    "sourceSet": "commonMain",
                    "signature": str
                },
                "actuals": {
                    "androidMain": {...},
                    "iosMain": {...}
                },
                "validation": {
                    "is_valid": bool,
                    "issues": [str]
                }
            }
            
        Raises:
            ToolValidationError: If symbol_name is empty or analyzer not configured
            ToolError: If symbol not found or analysis fails
            
        Example:
            >>> tools = LSPTools(manager, analyzer)
            >>> result = await tools.navigate_expect_actual("Platform")
            >>> print(f"Expect: {result['expect']['file']}")
            >>> for source_set, actual in result['actuals'].items():
            ...     print(f"Actual ({source_set}): {actual['file']}")
        """
        # Validate input
        if not symbol_name or not symbol_name.strip():
            raise ToolValidationError(
                tool_name="navigate_expect_actual",
                field="symbol_name",
                reason="Symbol name cannot be empty"
            )
        
        if not self.kmp_analyzer:
            raise ToolValidationError(
                tool_name="navigate_expect_actual",
                field="kmp_analyzer",
                reason="KMP analyzer not configured. This tool requires a KMP project context."
            )
        
        symbol_name = symbol_name.strip()
        
        logger.info(f"Navigating expect/actual for: '{symbol_name}'")
        
        try:
            # Find expect/actual pairs for this symbol
            pairs = await self.kmp_analyzer.find_expect_actual_pairs(symbol_name)
            
            if not pairs:
                raise ToolError(
                    f"No expect/actual pairs found for symbol '{symbol_name}'",
                    details={"symbol": symbol_name},
                    tool_name="navigate_expect_actual"
                )
            
            # Use the first pair (should be only one for a given symbol name)
            pair = pairs[0]
            
            # Validate the pair
            is_valid, issues = self.kmp_analyzer.validate_expect_actual_pair(pair)
            
            result = {
                "symbol": pair.name,
                "kind": pair.kind,
                "expect": pair.expect_location,
                "actuals": pair.actual_locations,
                "validation": {
                    "is_valid": is_valid,
                    "issues": issues
                }
            }
            
            logger.info(
                f"Found expect/actual pair for '{symbol_name}': "
                f"{len(pair.actual_locations)} actual implementations"
            )
            return result
            
        except ToolValidationError:
            raise
        except ToolError:
            raise
        except Exception as e:
            logger.error(f"Error navigating expect/actual: {e}")
            raise ToolError(
                f"Failed to navigate expect/actual for '{symbol_name}': {str(e)}",
                details={"symbol": symbol_name},
                tool_name="navigate_expect_actual"
            ) from e
