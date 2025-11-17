"""Interactive user elicitation tools for Kortex MCP Server.

This module provides MCP tools for asking clarifying questions to resolve
ambiguities in requirements. Follows the FastMCP ctx.elicit() pattern.

The tools use dataclass response types and return descriptive strings
based on user actions (accept, decline, cancel).

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
from typing import List
from fastmcp import Context


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
        raise ValueError("Question cannot be empty")
    
    @dataclass
    class UserResponse:
        """Response container for open-ended questions."""
        information: str
    
    result = await ctx.elicit(
        message=question,
        response_type=UserResponse
    )
    
    if result.action == "accept":
        return f"User provided: {result.data.information}"
    elif result.action == "decline":
        return "User declined to provide information"
    else:  # cancel
        return "Request cancelled by user"


async def ask_single_select(
    ctx: Context,
    question: str,
    options: List[str]
) -> str:
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
        raise ValueError("Question cannot be empty")
    
    if not options or len(options) == 0:
        raise ValueError("Options are required for single-select questions")
    
    @dataclass
    class OptionSelection:
        """Response container for single-select questions."""
        selected_option: str
    
    # Format options for display
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    elicitation_message = f"{question}\n\nOptions:\n{options_text}\n\nPlease select an option by entering its number or text:"
    
    result = await ctx.elicit(
        message=elicitation_message,
        response_type=OptionSelection
    )
    
    if result.action == "accept":
        return f"Selected: {result.data.selected_option}"
    elif result.action == "decline":
        return "User declined to select an option"
    else:  # cancel
        return "Selection cancelled by user"
