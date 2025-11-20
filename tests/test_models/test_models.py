"""Unit tests for specification and elicitation models."""

from datetime import datetime

from kortex_mcp.models.specification import (
    ElicitationQuestion,
    PlatformContext,
    QuestionType,
    Requirement,
    Specification,
    UserStory,
)


class TestElicitationQuestion:
    """Test ElicitationQuestion model."""

    def test_create_open_ended_question(self):
        """Test creating an open-ended question."""
        question = ElicitationQuestion(
            question="What should the feature do?",
            question_type=QuestionType.OPEN_ENDED,
        )

        assert question.question == "What should the feature do?"
        assert question.question_type == QuestionType.OPEN_ENDED
        assert question.options == []
        assert question.response is None

    def test_create_single_select_question(self):
        """Test creating a single-select question."""
        question = ElicitationQuestion(
            question="Which framework?",
            question_type=QuestionType.SINGLE_SELECT,
            options=["Koin", "Kodein", "Manual"],
        )

        assert question.question == "Which framework?"
        assert question.question_type == QuestionType.SINGLE_SELECT
        assert len(question.options) == 3
        assert "Koin" in question.options

    def test_create_multi_select_question(self):
        """Test creating a multi-select question."""
        question = ElicitationQuestion(
            question="Which platforms?",
            question_type=QuestionType.MULTI_SELECT,
            options=["Android", "iOS", "Desktop", "Web"],
            context="Select all that apply",
        )

        assert question.question_type == QuestionType.MULTI_SELECT
        assert len(question.options) == 4
        assert question.context == "Select all that apply"

    def test_question_with_platform_context(self):
        """Test question with platform-specific context."""
        question = ElicitationQuestion(
            question="Where to store tokens?",
            question_type=QuestionType.SINGLE_SELECT,
            options=["Keychain", "UserDefaults"],
            platform_context=PlatformContext.IOS,
        )

        assert question.platform_context == PlatformContext.IOS

    def test_validate_valid_open_ended(self):
        """Test validation passes for valid open-ended question."""
        question = ElicitationQuestion(
            question="Describe the feature",
            question_type=QuestionType.OPEN_ENDED,
        )

        assert question.validate() is True

    def test_validate_valid_single_select(self):
        """Test validation passes for valid single-select question."""
        question = ElicitationQuestion(
            question="Choose one",
            question_type=QuestionType.SINGLE_SELECT,
            options=["Option A", "Option B"],
        )

        assert question.validate() is True

    def test_validate_invalid_empty_question(self):
        """Test validation fails for empty question text."""
        question = ElicitationQuestion(
            question="",
            question_type=QuestionType.OPEN_ENDED,
        )

        assert question.validate() is False

    def test_validate_invalid_select_without_options(self):
        """Test validation fails for select question without options."""
        question = ElicitationQuestion(
            question="Choose something",
            question_type=QuestionType.SINGLE_SELECT,
            options=[],
        )

        assert question.validate() is False

    def test_validate_invalid_open_ended_with_options(self):
        """Test validation fails for open-ended question with options."""
        question = ElicitationQuestion(
            question="Describe something",
            question_type=QuestionType.OPEN_ENDED,
            options=["This", "Should", "Not", "Be", "Here"],
        )

        assert question.validate() is False

    def test_validate_response_open_ended_valid(self):
        """Test response validation for valid open-ended response."""
        question = ElicitationQuestion(
            question="What do you think?",
            question_type=QuestionType.OPEN_ENDED,
            response="I think this is great!",
        )

        assert question.validate_response() is True

    def test_validate_response_open_ended_empty(self):
        """Test response validation fails for empty open-ended response."""
        question = ElicitationQuestion(
            question="What do you think?",
            question_type=QuestionType.OPEN_ENDED,
            response="",
        )

        assert question.validate_response() is False

    def test_validate_response_single_select_valid(self):
        """Test response validation for valid single-select response."""
        question = ElicitationQuestion(
            question="Choose one",
            question_type=QuestionType.SINGLE_SELECT,
            options=["A", "B", "C"],
            response="B",
        )

        assert question.validate_response() is True

    def test_validate_response_single_select_invalid(self):
        """Test response validation fails for invalid single-select response."""
        question = ElicitationQuestion(
            question="Choose one",
            question_type=QuestionType.SINGLE_SELECT,
            options=["A", "B", "C"],
            response="D",  # Not in options
        )

        assert question.validate_response() is False

    def test_validate_response_multi_select_valid(self):
        """Test response validation for valid multi-select response."""
        question = ElicitationQuestion(
            question="Choose multiple",
            question_type=QuestionType.MULTI_SELECT,
            options=["A", "B", "C", "D"],
            response=["A", "C"],
        )

        assert question.validate_response() is True

    def test_validate_response_multi_select_invalid(self):
        """Test response validation fails for invalid multi-select response."""
        question = ElicitationQuestion(
            question="Choose multiple",
            question_type=QuestionType.MULTI_SELECT,
            options=["A", "B", "C"],
            response=["A", "D"],  # D not in options
        )

        assert question.validate_response() is False

    def test_validate_response_multi_select_not_list(self):
        """Test response validation fails when multi-select response is not a list."""
        question = ElicitationQuestion(
            question="Choose multiple",
            question_type=QuestionType.MULTI_SELECT,
            options=["A", "B", "C"],
            response="A",  # Should be a list
        )

        assert question.validate_response() is False

    def test_to_dict(self):
        """Test converting question to dictionary."""
        question = ElicitationQuestion(
            question="Test question",
            question_type=QuestionType.SINGLE_SELECT,
            options=["A", "B"],
            response="A",
            context="Test context",
            platform_context=PlatformContext.ANDROID,
            category="testing",
        )

        data = question.to_dict()

        assert data["question"] == "Test question"
        assert data["question_type"] == "single_select"
        assert data["options"] == ["A", "B"]
        assert data["response"] == "A"
        assert data["context"] == "Test context"
        assert data["platform_context"] == "android"
        assert data["category"] == "testing"
        assert "created_at" in data

    def test_from_dict(self):
        """Test creating question from dictionary."""
        data = {
            "question": "Test question",
            "question_type": "multi_select",
            "options": ["X", "Y", "Z"],
            "response": ["X", "Z"],
            "context": "Test context",
            "platform_context": "ios",
            "category": "testing",
            "created_at": datetime.now().isoformat(),
        }

        question = ElicitationQuestion.from_dict(data)

        assert question.question == "Test question"
        assert question.question_type == QuestionType.MULTI_SELECT
        assert question.options == ["X", "Y", "Z"]
        assert question.response == ["X", "Z"]
        assert question.context == "Test context"
        assert question.platform_context == PlatformContext.IOS
        assert question.category == "testing"

    def test_from_dict_minimal(self):
        """Test creating question from minimal dictionary."""
        data = {
            "question": "Minimal question",
            "question_type": "open_ended",
        }

        question = ElicitationQuestion.from_dict(data)

        assert question.question == "Minimal question"
        assert question.question_type == QuestionType.OPEN_ENDED
        assert question.options == []
        assert question.response is None
        assert question.platform_context is None

    def test_serialization_roundtrip(self):
        """Test that serialization and deserialization preserves data."""
        original = ElicitationQuestion(
            question="Round trip test",
            question_type=QuestionType.SINGLE_SELECT,
            options=["One", "Two", "Three"],
            response="Two",
            context="Testing serialization",
            category="test",
        )

        data = original.to_dict()
        restored = ElicitationQuestion.from_dict(data)

        assert restored.question == original.question
        assert restored.question_type == original.question_type
        assert restored.options == original.options
        assert restored.response == original.response
        assert restored.context == original.context
        assert restored.category == original.category


class TestUserStory:
    """Test UserStory model."""

    def test_create_user_story(self):
        """Test creating a user story."""
        story = UserStory(
            id="US-001",
            title="User Authentication",
            description="As a user, I want to log in",
            priority="P1",
            acceptance_criteria=["Can login with valid credentials"],
        )

        assert story.id == "US-001"
        assert story.title == "User Authentication"
        assert story.priority == "P1"
        assert len(story.acceptance_criteria) == 1
        assert story.status == "draft"

    def test_user_story_defaults(self):
        """Test user story default values."""
        story = UserStory(
            id="US-002",
            title="Some feature",
            description="Description",
        )

        assert story.priority == "P2"
        assert story.acceptance_criteria == []
        assert story.status == "draft"


class TestRequirement:
    """Test Requirement model."""

    def test_create_requirement(self):
        """Test creating a requirement."""
        req = Requirement(
            id="REQ-001",
            type="functional",
            description="System must authenticate users",
            rationale="Security requirement",
            user_stories=["US-001"],
        )

        assert req.id == "REQ-001"
        assert req.type == "functional"
        assert req.rationale == "Security requirement"
        assert "US-001" in req.user_stories

    def test_requirement_defaults(self):
        """Test requirement default values."""
        req = Requirement(
            id="REQ-002",
            type="non-functional",
            description="Performance requirement",
        )

        assert req.rationale is None
        assert req.user_stories == []
        assert req.status == "draft"


class TestSpecification:
    """Test Specification model."""

    def test_create_specification(self):
        """Test creating a specification."""
        story = UserStory(
            id="US-001",
            title="Feature A",
            description="Description A",
        )
        req = Requirement(
            id="REQ-001",
            type="functional",
            description="Requirement A",
        )

        spec = Specification(
            id="SPEC-001",
            title="Authentication Feature",
            description="Add user authentication",
            user_stories=[story],
            requirements=[req],
            open_questions=["Which OAuth2 provider should we use?"],
        )

        assert spec.id == "SPEC-001"
        assert spec.title == "Authentication Feature"
        assert len(spec.user_stories) == 1
        assert len(spec.requirements) == 1
        assert len(spec.open_questions) == 1

    def test_specification_to_dict(self):
        """Test converting specification to dictionary."""
        story = UserStory(
            id="US-001",
            title="Story",
            description="Description",
        )
        spec = Specification(
            id="SPEC-001",
            title="Test Spec",
            description="Test",
            user_stories=[story],
        )

        data = spec.to_dict()

        assert data["id"] == "SPEC-001"
        assert data["title"] == "Test Spec"
        assert len(data["user_stories"]) == 1
        assert data["user_stories"][0]["id"] == "US-001"
        assert "created_at" in data
        assert "updated_at" in data

    def test_specification_defaults(self):
        """Test specification default values."""
        spec = Specification(
            id="SPEC-002",
            title="Minimal Spec",
            description="Minimal",
        )

        assert spec.user_stories == []
        assert spec.requirements == []
        assert spec.open_questions == []
        assert spec.status == "draft"


class TestQuestionType:
    """Test QuestionType enum."""

    def test_question_type_values(self):
        """Test question type enum values."""
        assert QuestionType.OPEN_ENDED.value == "open_ended"
        assert QuestionType.SINGLE_SELECT.value == "single_select"
        assert QuestionType.MULTI_SELECT.value == "multi_select"

    def test_question_type_from_string(self):
        """Test creating question type from string."""
        q_type = QuestionType("single_select")
        assert q_type == QuestionType.SINGLE_SELECT


class TestPlatformContext:
    """Test PlatformContext enum."""

    def test_platform_context_values(self):
        """Test platform context enum values."""
        assert PlatformContext.ANDROID.value == "android"
        assert PlatformContext.IOS.value == "ios"
        assert PlatformContext.DESKTOP.value == "desktop"
        assert PlatformContext.WEB.value == "web"
        assert PlatformContext.COMMON.value == "common"
        assert PlatformContext.CROSS_PLATFORM.value == "cross_platform"

    def test_platform_context_from_string(self):
        """Test creating platform context from string."""
        platform = PlatformContext("ios")
        assert platform == PlatformContext.IOS
