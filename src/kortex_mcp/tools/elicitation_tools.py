"""Interactive user elicitation tools for Kortex MCP Server.

This module provides MCP tools for asking clarifying questions to resolve
ambiguities in requirements. Follows the FastMCP ctx.elicit() pattern.

The tools use dataclass response types and return descriptive strings
based on user actions (accept, decline, cancel).

Note: Elicitation requires the MCP client to support elicitation capability
and provide an elicitation_handler. If the client doesn't support elicitation,
the tools will return a message indicating this limitation.

Example:
    ```python
    # In an AI assistant conversation:
    # AI: I'll ask the user what authentication method to use
    result = await ask_single_select(
        ctx,
        "Which authentication method should we use?",
        ["OAuth2", "JWT", "API Key", "Basic Auth"]
    )
    # Returns: "Selected: OAuth2" or "User declined to select" etc.
    ```
"""

from dataclasses import dataclass
from typing import Any, cast

from fastmcp import Context
from mcp.shared.exceptions import McpError

from ..utils.logging import get_logger

logger = get_logger(__name__)


# Message returned when client doesn't support elicitation
ELICITATION_NOT_SUPPORTED_MSG = (
    "Elicitation is not supported by the current MCP client. "
    "To use interactive questioning, the client must support elicitation capability "
    "and provide an elicitation_handler. "
    "Please provide the information directly in your request instead."
)


async def ask_open_ended(ctx: Context, question: str) -> str:
    """Request information from user in natural language.

    Asks a free-form question and collects the user's response.
    This is useful for gathering detailed information, explanations,
    or clarifications that don't fit into predefined options.

    Args:
        ctx: FastMCP Context object for elicitation
        question: Detailed but brief question to ask the user

    Returns:
        Descriptive string with the result:
        - "User provided: {response}" if accepted
        - "User declined to provide information" if declined
        - "Request cancelled by user" if cancelled
        - Elicitation not supported message if client doesn't support it

    Raises:
        ValueError: If question is empty or whitespace only

    Example:
        >>> result = await ask_open_ended(
        ...     ctx,
        ...     "What should the authentication timeout be?"
        ... )
        >>> # Returns: "User provided: 30 minutes for better UX"
    """
    if not question or not question.strip():
        logger.error("ask_open_ended called with empty question")
        raise ValueError("Question cannot be empty")

    logger.info(f"Asking open-ended question: '{question}'")

    @dataclass
    class UserResponse:
        """Response container for open-ended questions."""

        information: str

    try:
        result = await ctx.elicit(
            message=question,
            response_type=UserResponse,  # type: ignore[arg-type]
        )

        if result.action == "accept":
            # Cast the data to expected type - when action is "accept" data is populated
            data = cast(Any, result.data)
            information = data.information if hasattr(data, "information") else str(data)
            logger.debug(f"User accepted open-ended question. Response length: {len(information)}")
            return f"User provided: {information}"
        elif result.action == "decline":
            logger.info("User declined open-ended question")
            return "User declined to provide information"
        else:  # cancel
            logger.info("User cancelled open-ended question")
            return "Request cancelled by user"
    except McpError as e:
        # Handle case when client doesn't support elicitation
        if "Elicitation not supported" in str(e):
            logger.warning(f"Elicitation not supported by client. Question was: '{question}'")
            return f"{ELICITATION_NOT_SUPPORTED_MSG}\n\nOriginal question: {question}"
        logger.error(f"MCP error in ask_open_ended: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error in ask_open_ended: {str(e)}", exc_info=True)
        raise


async def ask_single_select(ctx: Context, question: str, options: list[str]) -> str:
    """Ask user to select one option from provided choices.

    Presents the user with multiple options and asks them to select one.
    This is useful for choices between known alternatives, such as
    framework selection, architecture patterns, or implementation approaches.

    Args:
        ctx: FastMCP Context object for elicitation
        question: Detailed but brief question to ask the user
        options: List of detailed but brief options for the user to choose from

    Returns:
        Descriptive string with the result:
        - "Selected: {option}" if accepted
        - "User declined to select an option" if declined
        - "Selection cancelled by user" if cancelled
        - Elicitation not supported message if client doesn't support it

    Raises:
        ValueError: If question is empty or no options provided

    Example:
        >>> result = await ask_single_select(
        ...     ctx,
        ...     "Which dependency injection framework?",
        ...     ["Koin", "Kodein", "Hilt", "Manual DI"]
        ... )
        >>> # Returns: "Selected: Koin"
    """
    if not question or not question.strip():
        logger.error("ask_single_select called with empty question")
        raise ValueError("Question cannot be empty")

    if not options or len(options) == 0:
        logger.error("ask_single_select called with no options")
        raise ValueError("Options are required for single-select questions")

    logger.info(f"Asking single-select question: '{question}' with {len(options)} options")

    @dataclass
    class OptionSelection:
        """Response container for single-select questions."""

        selected_option: str

    # Format options for display
    options_text = "\n".join([f"{i + 1}. {opt}" for i, opt in enumerate(options)])
    elicitation_message = f"{question}\n\nOptions:\n{options_text}\n\nPlease select an option by entering its number or text:"

    try:
        result = await ctx.elicit(
            message=elicitation_message,
            response_type=OptionSelection,  # type: ignore[arg-type]
        )

        if result.action == "accept":
            # Cast the data to expected type - when action is "accept" data is populated
            data = cast(Any, result.data)
            selected = data.selected_option if hasattr(data, "selected_option") else str(data)
            logger.debug(f"User selected option: {selected}")
            return f"Selected: {selected}"
        elif result.action == "decline":
            logger.info("User declined single-select question")
            return "User declined to select an option"
        else:
            logger.info("User cancelled single-select question")
            return "Selection cancelled by user"
    except McpError as e:
        # Handle case when client doesn't support elicitation
        if "Elicitation not supported" in str(e):
            logger.warning(f"Elicitation not supported by client. Question was: '{question}'")
            return (
                f"{ELICITATION_NOT_SUPPORTED_MSG}\n\n"
                f"Original question: {question}\n"
                f"Options: {', '.join(options)}"
            )
        logger.error(f"MCP error in ask_single_select: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error in ask_single_select: {str(e)}", exc_info=True)
        raise
