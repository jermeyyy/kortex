"""Logging configuration for Kortex MCP Server.

This module provides centralized logging configuration with support for
different log levels and formatted output.
"""

import logging
import sys
from pathlib import Path


def setup_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
    format_string: str | None = None,
) -> None:
    """Configure logging for the application.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to log file for file output
        format_string: Custom format string for log messages

    Example:
        >>> setup_logging(level=logging.DEBUG)
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Operation completed")
    """
    return logging.getLogger(name)


# Default logger for the package
logger = get_logger("kortex_mcp")
