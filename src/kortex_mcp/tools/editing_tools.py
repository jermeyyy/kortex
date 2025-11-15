"""Editing tools for symbolic code modification.

This module provides MCP tools for making precise code changes using
LSP symbol-level operations rather than text replacement. Includes
tools for adding methods, renaming symbols, and maintaining expect/actual
consistency in Kotlin Multiplatform projects.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import re

from ..lsp.manager import LSPManager
from ..analyzers.kmp_analyzer import KMPAnalyzer
from ..models.lsp import TextEdit, Range, Position, WorkspaceEdit
from ..utils.logging import get_logger
from .base import with_timeout, ToolError, ToolValidationError


logger = get_logger(__name__)


class EditingTools:
    """Container for code editing MCP tools.
    
    Provides tools for adding methods to classes, renaming symbols,
    and maintaining code consistency in KMP projects.
    """
    
    def __init__(
        self,
        lsp_manager: LSPManager,
        kmp_analyzer: Optional[KMPAnalyzer] = None
    ):
        """Initialize editing tools.
        
        Args:
            lsp_manager: LSP manager instance for server communication
            kmp_analyzer: Optional KMP analyzer for expect/actual handling
        """
        self.lsp_manager = lsp_manager
        self.kmp_analyzer = kmp_analyzer
    
    @with_timeout(60.0)
    async def add_method(
        self,
        class_name: str,
        method_signature: str,
        method_body: str,
        file_path: Optional[str] = None,
        language: str = "kotlin"
    ) -> Dict[str, Any]:
        """Add a method to a class using LSP-guided insertion.
        
        MCP Tool for adding a new method to an existing class. Uses LSP to
        locate the class and determine the appropriate insertion point, then
        inserts the method with proper formatting and indentation.
        
        Args:
            class_name: Name of the target class
            method_signature: Method signature (e.g., "fun getData(): List<String>")
            method_body: Method implementation code
            file_path: Optional file path if class location is known
            language: Language server to use (default: "kotlin")
            
        Returns:
            Dictionary with result details:
            {
                "success": bool,
                "class": str,
                "file": str,
                "line": int,
                "method": str
            }
            
        Raises:
            ToolValidationError: If parameters are invalid
            ToolError: If operation fails
            
        Example:
            >>> tools = EditingTools(manager, analyzer)
            >>> result = await tools.add_method(
            ...     class_name="UserRepository",
            ...     method_signature="fun deleteUser(id: String): Boolean",
            ...     method_body="return database.delete(id)"
            ... )
            >>> print(f"Added method to {result['file']}:{result['line']}")
        """
        # Validate inputs
        if not class_name or not class_name.strip():
            raise ToolValidationError(
                tool_name="add_method",
                field="class_name",
                reason="Class name cannot be empty"
            )
        
        if not method_signature or not method_signature.strip():
            raise ToolValidationError(
                tool_name="add_method",
                field="method_signature",
                reason="Method signature cannot be empty"
            )
        
        class_name = class_name.strip()
        method_signature = method_signature.strip()
        method_body = method_body.strip() if method_body else ""
        
        logger.info(f"Adding method to class '{class_name}'")
        
        try:
            # Get LSP client
            client = self.lsp_manager.get_client(language)
            if not client or not client.is_running():
                raise ToolError(
                    f"LSP server for '{language}' is not available",
                    details={"language": language},
                    tool_name="add_method"
                )
            
            # Find the class if file_path not provided
            target_file = None
            if file_path:
                target_file = Path(file_path)
            else:
                # Search for class using LSP
                symbols = await client.workspace_symbols(class_name)
                class_symbols = [s for s in symbols if s.name == class_name and s.kind == 5]  # kind 5 = class
                
                if not class_symbols:
                    raise ToolError(
                        f"Class '{class_name}' not found",
                        details={"class_name": class_name},
                        tool_name="add_method"
                    )
                
                # Use first match
                file_uri = class_symbols[0].location.uri
                if file_uri.startswith("file://"):
                    file_uri = file_uri[7:]
                target_file = Path(file_uri)
            
            if not target_file.exists():
                raise ToolError(
                    f"File not found: {target_file}",
                    details={"file": str(target_file)},
                    tool_name="add_method"
                )
            
            # Find insertion point
            if not self.kmp_analyzer:
                raise ToolError(
                    "KMP analyzer not configured",
                    details={},
                    tool_name="add_method"
                )
            
            insertion_point = self.kmp_analyzer.find_class_insertion_point(
                target_file,
                class_name
            )
            
            if not insertion_point:
                raise ToolError(
                    f"Could not find insertion point in class '{class_name}'",
                    details={"class": class_name, "file": str(target_file)},
                    tool_name="add_method"
                )
            
            # Detect indentation style
            indent_style = self.kmp_analyzer.detect_indentation_style(target_file)
            
            # Format method with proper indentation
            indentation = insertion_point["indentation"]
            method_lines = self._format_method(
                method_signature,
                method_body,
                indentation,
                indent_style
            )
            
            # Create text edit
            insert_line = insertion_point["line"]
            new_text = "\n" + method_lines + "\n"
            
            text_edit = TextEdit(
                range=Range(
                    start=Position(line=insert_line, character=0),
                    end=Position(line=insert_line, character=0)
                ),
                newText=new_text
            )
            
            # Apply edit
            file_uri = f"file://{target_file.absolute()}"
            workspace_edit = WorkspaceEdit(changes={file_uri: [text_edit]})
            
            success = await client.apply_workspace_edit(workspace_edit)
            
            if success:
                logger.info(f"Successfully added method to {class_name} at {target_file}:{insert_line}")
                return {
                    "success": True,
                    "class": class_name,
                    "file": str(target_file),
                    "line": insert_line,
                    "method": method_signature
                }
            else:
                raise ToolError(
                    "Failed to apply workspace edit",
                    details={"class": class_name, "file": str(target_file)},
                    tool_name="add_method"
                )
                
        except ToolValidationError:
            raise
        except ToolError:
            raise
        except Exception as e:
            logger.error(f"Error adding method: {e}")
            raise ToolError(
                f"Failed to add method: {str(e)}",
                details={"class": class_name},
                tool_name="add_method"
            ) from e
    
    def _format_method(
        self,
        signature: str,
        body: str,
        base_indentation: str,
        indent_style: Dict[str, Any]
    ) -> str:
        """Format method code with proper indentation.
        
        Args:
            signature: Method signature
            body: Method body code
            base_indentation: Base indentation for the method
            indent_style: Indentation style dict from analyzer
            
        Returns:
            Formatted method code
        """
        # Determine indent unit
        if indent_style["type"] == "tabs":
            indent_unit = "\t"
        else:
            indent_unit = " " * indent_style["size"]
        
        # Format method
        lines = []
        lines.append(f"{base_indentation}{signature} {{")
        
        if body:
            # Process body lines
            body_lines = body.split("\n")
            for line in body_lines:
                if line.strip():
                    lines.append(f"{base_indentation}{indent_unit}{line}")
                else:
                    lines.append("")
        
        lines.append(f"{base_indentation}}}")
        
        return "\n".join(lines)
    
    @with_timeout(45.0)
    async def rename_symbol(
        self,
        file: str,
        line: int,
        character: int,
        new_name: str,
        language: str = "kotlin"
    ) -> Dict[str, Any]:
        """Rename a symbol and all its references using LSP.
        
        MCP Tool for renaming symbols across the entire codebase. Uses LSP
        rename operation to find and update all references to the symbol,
        ensuring consistency across all source sets.
        
        Args:
            file: File path containing the symbol
            line: Line number of symbol (0-based)
            character: Character position in line (0-based)
            new_name: New name for the symbol
            language: Language server to use (default: "kotlin")
            
        Returns:
            Dictionary with rename results:
            {
                "success": bool,
                "old_name": str,  # If detectable
                "new_name": str,
                "changes": [
                    {"file": str, "edits": int}
                ],
                "total_changes": int
            }
            
        Raises:
            ToolValidationError: If parameters are invalid
            ToolError: If operation fails
            
        Example:
            >>> result = await tools.rename_symbol(
            ...     file="/project/Repository.kt",
            ...     line=10,
            ...     character=15,
            ...     new_name="DataRepository"
            ... )
            >>> print(f"Renamed in {result['total_changes']} locations")
        """
        # Validate inputs
        if not file or not file.strip():
            raise ToolValidationError(
                tool_name="rename_symbol",
                field="file",
                reason="File path cannot be empty"
            )
        
        if line < 0:
            raise ToolValidationError(
                tool_name="rename_symbol",
                field="line",
                reason="Line number must be >= 0"
            )
        
        if character < 0:
            raise ToolValidationError(
                tool_name="rename_symbol",
                field="character",
                reason="Character position must be >= 0"
            )
        
        if not new_name or not new_name.strip():
            raise ToolValidationError(
                tool_name="rename_symbol",
                field="new_name",
                reason="New name cannot be empty"
            )
        
        # Validate new name is valid Kotlin identifier
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', new_name.strip()):
            raise ToolValidationError(
                tool_name="rename_symbol",
                field="new_name",
                reason=f"'{new_name}' is not a valid Kotlin identifier"
            )
        
        file_path = Path(file)
        if not file_path.exists():
            raise ToolValidationError(
                tool_name="rename_symbol",
                field="file",
                reason=f"File does not exist: {file}"
            )
        
        new_name = new_name.strip()
        
        logger.info(f"Renaming symbol at {file}:{line}:{character} to '{new_name}'")
        
        try:
            # Get LSP client
            client = self.lsp_manager.get_client(language)
            if not client or not client.is_running():
                raise ToolError(
                    f"LSP server for '{language}' is not available",
                    details={"language": language},
                    tool_name="rename_symbol"
                )
            
            # Convert to file URI
            file_uri = f"file://{file_path.absolute()}"
            
            # Request rename from LSP
            workspace_edit = await client.rename_symbol(
                file_uri=file_uri,
                line=line,
                character=character,
                new_name=new_name
            )
            
            if not workspace_edit:
                raise ToolError(
                    "No rename operation available at this location",
                    details={"file": file, "line": line, "character": character},
                    tool_name="rename_symbol"
                )
            
            # Apply the rename
            success = await client.apply_workspace_edit(workspace_edit)
            
            if success:
                # Count changes
                changes_summary = []
                total_edits = 0
                
                for uri, edits in workspace_edit.changes.items():
                    file_path = uri.replace("file://", "")
                    edit_count = len(edits)
                    total_edits += edit_count
                    changes_summary.append({
                        "file": file_path,
                        "edits": edit_count
                    })
                
                logger.info(f"Renamed symbol to '{new_name}' in {len(changes_summary)} file(s)")
                
                return {
                    "success": True,
                    "new_name": new_name,
                    "changes": changes_summary,
                    "total_changes": total_edits
                }
            else:
                raise ToolError(
                    "Failed to apply rename operation",
                    details={"new_name": new_name},
                    tool_name="rename_symbol"
                )
                
        except ToolValidationError:
            raise
        except ToolError:
            raise
        except Exception as e:
            logger.error(f"Error renaming symbol: {e}")
            raise ToolError(
                f"Failed to rename symbol: {str(e)}",
                details={"file": file, "new_name": new_name},
                tool_name="rename_symbol"
            ) from e
    
    async def validate_expect_actual_consistency(
        self,
        symbol_name: str
    ) -> Dict[str, Any]:
        """Validate that expect/actual pairs are consistent after edits.
        
        Checks that expect declarations and their actual implementations
        have matching signatures and no missing implementations.
        
        Args:
            symbol_name: Name of the expect/actual symbol to validate
            
        Returns:
            Validation results:
            {
                "valid": bool,
                "symbol": str,
                "issues": List[str],
                "expect": Dict,
                "actuals": Dict
            }
            
        Raises:
            ToolValidationError: If analyzer not configured or symbol invalid
            
        Example:
            >>> result = await tools.validate_expect_actual_consistency("Platform")
            >>> if not result["valid"]:
            ...     for issue in result["issues"]:
            ...         print(f"Issue: {issue}")
        """
        if not self.kmp_analyzer:
            raise ToolValidationError(
                tool_name="validate_expect_actual_consistency",
                field="kmp_analyzer",
                reason="KMP analyzer not configured"
            )
        
        if not symbol_name or not symbol_name.strip():
            raise ToolValidationError(
                tool_name="validate_expect_actual_consistency",
                field="symbol_name",
                reason="Symbol name cannot be empty"
            )
        
        symbol_name = symbol_name.strip()
        
        logger.info(f"Validating expect/actual consistency for '{symbol_name}'")
        
        try:
            # Find expect/actual pairs
            pairs = await self.kmp_analyzer.find_expect_actual_pairs(symbol_name)
            
            if not pairs:
                return {
                    "valid": True,
                    "symbol": symbol_name,
                    "issues": [],
                    "expect": None,
                    "actuals": {}
                }
            
            # Validate first pair (should only be one for given name)
            pair = pairs[0]
            is_valid, issues = self.kmp_analyzer.validate_expect_actual_pair(pair)
            
            return {
                "valid": is_valid,
                "symbol": pair.name,
                "issues": issues,
                "expect": pair.expect_location,
                "actuals": pair.actual_locations
            }
            
        except Exception as e:
            logger.error(f"Error validating expect/actual: {e}")
            raise ToolError(
                f"Failed to validate expect/actual: {str(e)}",
                details={"symbol": symbol_name},
                tool_name="validate_expect_actual_consistency"
            ) from e
