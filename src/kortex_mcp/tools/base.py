"""Base tool class for MCP tools.

This module provides common functionality and error handling for all
MCP tools in the Kortex server.
"""

import asyncio
from typing import Any, Dict, Optional, Callable
from functools import wraps
from datetime import datetime

from ..utils.logging import get_logger


logger = get_logger(__name__)


class ToolError(Exception):
    """Base exception for tool errors.

    Attributes:
        message: Error message
        details: Optional error details
        tool_name: Name of the tool that raised the error
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        tool_name: Optional[str] = None
    ):
        """Initialize tool error.

        Args:
            message: Error message
            details: Optional error details
            tool_name: Name of the tool
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.tool_name = tool_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary.

        Returns:
            Dictionary with error information
        """
        result: Dict[str, Any] = {
            "error": self.message,
            "details": self.details,
        }
        if self.tool_name:
            result["tool"] = self.tool_name
        return result


class ToolTimeout(ToolError):
    """Exception raised when a tool operation times out."""

    def __init__(self, tool_name: str, timeout: float):
        """Initialize timeout error.

        Args:
            tool_name: Name of the tool
            timeout: Timeout duration in seconds
        """
        super().__init__(
            f"Tool '{tool_name}' timed out after {timeout} seconds",
            details={"timeout": timeout},
            tool_name=tool_name
        )


class ToolValidationError(ToolError):
    """Exception raised when tool input validation fails."""

    def __init__(self, tool_name: str, field: str, reason: str):
        """Initialize validation error.

        Args:
            tool_name: Name of the tool
            field: Field that failed validation
            reason: Reason for validation failure
        """
        super().__init__(
            f"Validation failed for field '{field}': {reason}",
            details={"field": field, "reason": reason},
            tool_name=tool_name
        )


def with_timeout(timeout: float = 30.0):
    """Decorator to add timeout to async tool functions.

    Args:
        timeout: Timeout in seconds (default: 30.0)

    Returns:
        Decorator function

    Example:
        >>> @with_timeout(timeout=10.0)
        ... async def my_tool():
        ...     await some_operation()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                tool_name = func.__name__
                logger.error(f"Tool '{tool_name}' timed out after {timeout}s")
                raise ToolTimeout(tool_name, timeout)
        return wrapper
    return decorator


def with_error_handling(tool_name: str):
    """Decorator to add error handling to tool functions.

    Catches exceptions and converts them to ToolError.

    Args:
        tool_name: Name of the tool

    Returns:
        Decorator function

    Example:
        >>> @with_error_handling("my_tool")
        ... async def my_tool():
        ...     # Tool implementation
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ToolError:
                # Re-raise tool errors
                raise
            except Exception as e:
                logger.error(f"Error in tool '{tool_name}': {e}")
                raise ToolError(
                    f"Tool execution failed: {str(e)}",
                    details={"error_type": type(e).__name__},
                    tool_name=tool_name
                ) from e
        return wrapper
    return decorator


def log_tool_execution(func: Callable) -> Callable:
    """Decorator to log tool execution.

    Logs start and end of tool execution with timing information.

    Args:
        func: Tool function to wrap

    Returns:
        Wrapped function

    Example:
        >>> @log_tool_execution
        ... async def my_tool():
        ...     # Tool implementation
        ...     pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        tool_name = func.__name__
        start_time = datetime.now()
        
        logger.info(f"Starting tool: {tool_name}")
        logger.debug(f"Tool args: {args}, kwargs: {kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Tool '{tool_name}' completed in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Tool '{tool_name}' failed after {duration:.2f}s: {e}"
            )
            raise
    
    return wrapper


class BaseTool:
    """Base class for MCP tools.

    Provides common functionality for all tools including error handling,
    logging, and validation.

    Attributes:
        name: Tool name
        description: Tool description
        timeout: Default timeout for tool operations

    Example:
        >>> class MyTool(BaseTool):
        ...     def __init__(self):
        ...         super().__init__(
        ...             name="my_tool",
        ...             description="My custom tool"
        ...         )
        ...
        ...     async def execute(self, **kwargs):
        ...         # Tool implementation
        ...         pass
    """

    def __init__(
        self,
        name: str,
        description: str,
        timeout: float = 30.0
    ):
        """Initialize base tool.

        Args:
            name: Tool name
            description: Tool description
            timeout: Default timeout in seconds
        """
        self.name = name
        self.description = description
        self.timeout = timeout
        self.logger = get_logger(f"tools.{name}")

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool.

        This method should be overridden by subclasses.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool result

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate tool parameters.

        Override this method to add parameter validation.

        Args:
            params: Parameters to validate

        Raises:
            ToolValidationError: If validation fails
        """
        pass

    async def run(self, **kwargs: Any) -> Any:
        """Run the tool with error handling and logging.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool result

        Raises:
            ToolError: If tool execution fails
        """
        start_time = datetime.now()
        
        self.logger.info(f"Running tool: {self.name}")
        self.logger.debug(f"Parameters: {kwargs}")
        
        try:
            # Validate parameters
            self.validate_params(kwargs)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self.execute(**kwargs),
                timeout=self.timeout
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Tool '{self.name}' completed in {duration:.2f}s")
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(
                f"Tool '{self.name}' timed out after {self.timeout}s"
            )
            raise ToolTimeout(self.name, self.timeout)
            
        except ToolError:
            # Re-raise tool errors
            raise
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                f"Tool '{self.name}' failed after {duration:.2f}s: {e}"
            )
            raise ToolError(
                f"Tool execution failed: {str(e)}",
                details={"error_type": type(e).__name__},
                tool_name=self.name
            ) from e

    def __str__(self) -> str:
        """String representation of tool.

        Returns:
            Tool name and description
        """
        return f"{self.name}: {self.description}"
