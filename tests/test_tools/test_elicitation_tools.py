"""Tests for interactive user elicitation tools."""

import mcp.types as types
import pytest
from mcp.shared.exceptions import McpError

from kortex_mcp.tools import elicitation_tools


class MockElicitationResult:
    """Mock for FastMCP ElicitationResult."""

    def __init__(self, action: str, data=None):
        self.action = action
        self.data = data


class MockContext:
    """Mock for FastMCP Context with elicit method."""

    def __init__(self, action="accept", response_data=None):
        self.action = action
        self.response_data = response_data

    async def elicit(self, message: str, response_type):
        """Mock elicit method that returns appropriate data based on response_type."""
        # If response_type is a dataclass, create an instance with mock data
        if hasattr(response_type, "__dataclass_fields__"):
            # It's a dataclass - instantiate it with response_data
            data = response_type(**self.response_data) if self.response_data else None
        else:
            # It's a simple type or list
            data = self.response_data

        return MockElicitationResult(self.action, data)


class MockContextNoElicitation:
    """Mock for FastMCP Context that doesn't support elicitation."""

    async def elicit(self, message: str, response_type):
        """Mock elicit method that raises McpError for unsupported elicitation."""
        error_data = types.ErrorData(
            code=types.INVALID_REQUEST, message="Elicitation not supported"
        )
        raise McpError(error_data)


@pytest.fixture
def mock_ctx_accept():
    """Create a mock context that accepts by default."""
    return MockContext(action="accept")


@pytest.fixture
def mock_ctx_decline():
    """Create a mock context that declines."""
    return MockContext(action="decline")


@pytest.fixture
def mock_ctx_cancel():
    """Create a mock context that cancels."""
    return MockContext(action="cancel")


class TestAskOpenEnded:
    """Test ask_open_ended function."""

    @pytest.mark.asyncio
    async def test_ask_open_ended_accept(self, mock_ctx_accept):
        """Test asking an open-ended question when user accepts."""
        mock_ctx_accept.response_data = {
            "information": "My feature should handle user authentication"
        }

        result = await elicitation_tools.ask_open_ended(
            mock_ctx_accept, "What should this feature do?"
        )

        assert result == "User provided: My feature should handle user authentication"

    @pytest.mark.asyncio
    async def test_ask_open_ended_decline(self, mock_ctx_decline):
        """Test asking an open-ended question when user declines."""
        result = await elicitation_tools.ask_open_ended(
            mock_ctx_decline, "What should this feature do?"
        )

        assert result == "User declined to provide information"

    @pytest.mark.asyncio
    async def test_ask_open_ended_cancel(self, mock_ctx_cancel):
        """Test asking an open-ended question when user cancels."""
        result = await elicitation_tools.ask_open_ended(
            mock_ctx_cancel, "What should this feature do?"
        )

        assert result == "Request cancelled by user"

    @pytest.mark.asyncio
    async def test_ask_open_ended_empty_question(self, mock_ctx_accept):
        """Test that empty question raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            await elicitation_tools.ask_open_ended(mock_ctx_accept, "")

    @pytest.mark.asyncio
    async def test_ask_open_ended_whitespace_only(self, mock_ctx_accept):
        """Test that whitespace-only question raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            await elicitation_tools.ask_open_ended(mock_ctx_accept, "   ")

    @pytest.mark.asyncio
    async def test_ask_open_ended_detailed_response(self, mock_ctx_accept):
        """Test with detailed user response."""
        mock_ctx_accept.response_data = {
            "information": "We need JWT tokens with 24-hour expiry, refresh tokens with 30-day expiry, and secure HTTP-only cookies"
        }

        result = await elicitation_tools.ask_open_ended(
            mock_ctx_accept, "What authentication approach should we use?"
        )

        assert "JWT tokens" in result
        assert "24-hour expiry" in result


class TestAskSingleSelect:
    """Test ask_single_select function."""

    @pytest.mark.asyncio
    async def test_ask_single_select_accept(self, mock_ctx_accept):
        """Test asking a single-select question when user accepts."""
        mock_ctx_accept.response_data = {"selected_option": "Koin"}

        result = await elicitation_tools.ask_single_select(
            mock_ctx_accept, "Which framework?", ["Koin", "Kodein", "Hilt", "Manual"]
        )

        assert result == "Selected: Koin"

    @pytest.mark.asyncio
    async def test_ask_single_select_decline(self, mock_ctx_decline):
        """Test single-select question when user declines."""
        result = await elicitation_tools.ask_single_select(
            mock_ctx_decline, "Which framework?", ["Koin", "Kodein"]
        )

        assert result == "User declined to select an option"

    @pytest.mark.asyncio
    async def test_ask_single_select_cancel(self, mock_ctx_cancel):
        """Test single-select question when user cancels."""
        result = await elicitation_tools.ask_single_select(
            mock_ctx_cancel, "Which framework?", ["Koin", "Kodein"]
        )

        assert result == "Selection cancelled by user"

    @pytest.mark.asyncio
    async def test_ask_single_select_empty_question(self, mock_ctx_accept):
        """Test that empty question raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            await elicitation_tools.ask_single_select(mock_ctx_accept, "", ["A", "B"])

    @pytest.mark.asyncio
    async def test_ask_single_select_no_options(self, mock_ctx_accept):
        """Test that no options raises ValueError."""
        with pytest.raises(ValueError, match="Options are required"):
            await elicitation_tools.ask_single_select(mock_ctx_accept, "Choose one", [])

    @pytest.mark.asyncio
    async def test_ask_single_select_many_options(self, mock_ctx_accept):
        """Test single-select with many options."""
        options = [f"Option {i}" for i in range(10)]
        mock_ctx_accept.response_data = {"selected_option": "Option 5"}

        result = await elicitation_tools.ask_single_select(
            mock_ctx_accept, "Choose one option from the list", options
        )

        assert result == "Selected: Option 5"

    @pytest.mark.asyncio
    async def test_ask_single_select_with_detailed_options(self, mock_ctx_accept):
        """Test single-select with detailed option descriptions."""
        options = [
            "Koin - Lightweight Kotlin DI",
            "Hilt - Android DI built on Dagger",
            "Kodein - Pure Kotlin DI framework",
            "Manual - No framework, manual dependency management",
        ]
        mock_ctx_accept.response_data = {"selected_option": "Koin - Lightweight Kotlin DI"}

        result = await elicitation_tools.ask_single_select(
            mock_ctx_accept, "Which dependency injection approach?", options
        )

        assert result == "Selected: Koin - Lightweight Kotlin DI"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_question_with_special_characters(self, mock_ctx_accept):
        """Test questions with special characters."""
        mock_ctx_accept.response_data = {"information": "Use OAuth2.0 with PKCE"}

        result = await elicitation_tools.ask_open_ended(
            mock_ctx_accept, "What auth method? (e.g., OAuth2, JWT, etc.)"
        )

        assert "OAuth2.0" in result

    @pytest.mark.asyncio
    async def test_single_option_list(self, mock_ctx_accept):
        """Test single-select with only one option."""
        mock_ctx_accept.response_data = {"selected_option": "Only Option"}

        result = await elicitation_tools.ask_single_select(
            mock_ctx_accept, "Only one choice available:", ["Only Option"]
        )

        assert result == "Selected: Only Option"

    @pytest.mark.asyncio
    async def test_unicode_in_responses(self, mock_ctx_accept):
        """Test handling of unicode characters."""
        mock_ctx_accept.response_data = {"information": "Use 🔐 encryption with ✅ validation"}

        result = await elicitation_tools.ask_open_ended(mock_ctx_accept, "What security measures?")

        assert "🔐" in result
        assert "✅" in result

    @pytest.mark.asyncio
    async def test_multiline_response(self, mock_ctx_accept):
        """Test handling of multiline responses."""
        multiline_response = """We should use:
1. JWT for authentication
2. Refresh tokens for sessions
3. Secure HTTP-only cookies"""

        mock_ctx_accept.response_data = {"information": multiline_response}

        result = await elicitation_tools.ask_open_ended(
            mock_ctx_accept, "Describe the auth approach:"
        )

        assert "JWT" in result
        assert "Refresh tokens" in result
        assert "HTTP-only cookies" in result


class TestElicitationNotSupported:
    """Test graceful handling when client doesn't support elicitation."""

    @pytest.fixture
    def mock_ctx_no_elicitation(self):
        """Create a mock context that doesn't support elicitation."""
        return MockContextNoElicitation()

    @pytest.mark.asyncio
    async def test_ask_open_ended_no_elicitation_support(self, mock_ctx_no_elicitation):
        """Test ask_open_ended returns helpful message when elicitation not supported."""
        result = await elicitation_tools.ask_open_ended(
            mock_ctx_no_elicitation, "What authentication method should we use?"
        )

        # Should return a helpful message instead of raising an error
        assert "Elicitation is not supported" in result
        assert "elicitation_handler" in result
        assert "What authentication method should we use?" in result

    @pytest.mark.asyncio
    async def test_ask_single_select_no_elicitation_support(self, mock_ctx_no_elicitation):
        """Test ask_single_select returns helpful message when elicitation not supported."""
        options = ["OAuth2", "JWT", "API Key"]
        result = await elicitation_tools.ask_single_select(
            mock_ctx_no_elicitation, "Which authentication method?", options
        )

        # Should return a helpful message instead of raising an error
        assert "Elicitation is not supported" in result
        assert "elicitation_handler" in result
        assert "Which authentication method?" in result
        # Options should be included in the message
        assert "OAuth2" in result
        assert "JWT" in result
        assert "API Key" in result

    @pytest.mark.asyncio
    async def test_no_elicitation_message_content(self, mock_ctx_no_elicitation):
        """Test that the no-elicitation message provides actionable guidance."""
        result = await elicitation_tools.ask_open_ended(mock_ctx_no_elicitation, "Test question")

        # Should tell user how to proceed
        assert (
            "provide the information directly" in result.lower() or "elicitation_handler" in result
        )
