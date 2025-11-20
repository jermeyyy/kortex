"""Specification and elicitation data models.

This module defines data structures for specifications, requirements,
and interactive user elicitation questions used in planning mode.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class QuestionType(Enum):
    """Types of questions for user elicitation.

    Values:
        OPEN_ENDED: Free-form text response
        SINGLE_SELECT: Choose one option from a list
        MULTI_SELECT: Choose multiple options from a list
    """
    OPEN_ENDED = "open_ended"
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"


class PlatformContext(Enum):
    """Platform-specific contexts for targeted questions.

    Values:
        ANDROID: Android-specific implementation details
        IOS: iOS-specific implementation details
        DESKTOP: Desktop (JVM) specific implementation details
        WEB: Web (JS/Wasm) specific implementation details
        COMMON: Common/shared implementation details
        CROSS_PLATFORM: Questions relevant across platforms
    """
    ANDROID = "android"
    IOS = "ios"
    DESKTOP = "desktop"
    WEB = "web"
    COMMON = "common"
    CROSS_PLATFORM = "cross_platform"


@dataclass
class ElicitationQuestion:
    """A question to ask the user for clarification or decision-making.

    Attributes:
        question: The question text to present to the user
        question_type: Type of question (open-ended, single-select, multi-select)
        options: List of options for select-type questions (empty for open-ended)
        response: User's response (text for open-ended, selected option(s) for select)
        context: Optional context about why this question is being asked
        platform_context: Platform-specific context if applicable
        category: Optional category for organizing questions
        metadata: Additional metadata

    Example:
        >>> question = ElicitationQuestion(
        ...     question="Which dependency injection framework should we use?",
        ...     question_type=QuestionType.SINGLE_SELECT,
        ...     options=["Koin", "Kodein", "Manual DI"],
        ...     context="The project needs DI for managing dependencies"
        ... )
        >>> # After user responds
        >>> question.response = "Koin"
    """
    question: str
    question_type: QuestionType
    options: list[str] = field(default_factory=list)
    response: str | list[str] | None = None
    context: str | None = None
    platform_context: PlatformContext | None = None
    category: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> bool:
        """Validate the question structure.

        Returns:
            True if valid, False otherwise

        Example:
            >>> question = ElicitationQuestion(
            ...     question="Choose a framework",
            ...     question_type=QuestionType.SINGLE_SELECT,
            ...     options=["Option A", "Option B"]
            ... )
            >>> question.validate()
            True
        """
        # Question text must not be empty
        if not self.question or not self.question.strip():
            return False

        # Select-type questions must have options
        if self.question_type in (QuestionType.SINGLE_SELECT, QuestionType.MULTI_SELECT):
            if not self.options or len(self.options) == 0:
                return False

        # Open-ended questions should not have options
        if self.question_type == QuestionType.OPEN_ENDED:
            if self.options and len(self.options) > 0:
                return False

        return True

    def validate_response(self) -> bool:
        """Validate that the response matches the question type.

        Returns:
            True if response is valid for this question type

        Example:
            >>> question = ElicitationQuestion(
            ...     question="Select one",
            ...     question_type=QuestionType.SINGLE_SELECT,
            ...     options=["A", "B", "C"],
            ...     response="A"
            ... )
            >>> question.validate_response()
            True
        """
        if self.response is None:
            return False

        if self.question_type == QuestionType.OPEN_ENDED:
            # Response should be a non-empty string
            return isinstance(self.response, str) and bool(self.response.strip())

        elif self.question_type == QuestionType.SINGLE_SELECT:
            # Response should be a string matching one of the options
            return isinstance(self.response, str) and self.response in self.options

        elif self.question_type == QuestionType.MULTI_SELECT:
            # Response should be a list of strings, all matching options
            if not isinstance(self.response, list):
                return False
            return all(isinstance(r, str) and r in self.options for r in self.response)

        return False  # type: ignore

    def to_dict(self) -> dict[str, Any]:
        """Convert question to dictionary for serialization.

        Returns:
            Dictionary representation

        Example:
            >>> data = question.to_dict()
            >>> print(data["question_type"])
            'single_select'
        """
        return {
            "question": self.question,
            "question_type": self.question_type.value,
            "options": self.options,
            "response": self.response,
            "context": self.context,
            "platform_context": self.platform_context.value if self.platform_context else None,
            "category": self.category,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ElicitationQuestion":
        """Create ElicitationQuestion from dictionary.

        Args:
            data: Dictionary with question data

        Returns:
            ElicitationQuestion instance

        Example:
            >>> data = {
            ...     "question": "What framework?",
            ...     "question_type": "single_select",
            ...     "options": ["A", "B"]
            ... }
            >>> question = ElicitationQuestion.from_dict(data)
        """
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()

        platform_context = None
        if data.get("platform_context"):
            platform_context = PlatformContext(data["platform_context"])

        return ElicitationQuestion(
            question=data["question"],
            question_type=QuestionType(data["question_type"]),
            options=data.get("options", []),
            response=data.get("response"),
            context=data.get("context"),
            platform_context=platform_context,
            category=data.get("category"),
            metadata=data.get("metadata", {}),
            created_at=created_at,
        )


@dataclass
class UserStory:
    """A user story in a specification.

    Attributes:
        id: Unique identifier
        title: Story title
        description: Story description
        priority: Priority level (P1, P2, P3)
        acceptance_criteria: List of acceptance criteria
        status: Implementation status
        metadata: Additional metadata

    Example:
        >>> story = UserStory(
        ...     id="US-001",
        ...     title="User Authentication",
        ...     description="As a user, I want to log in...",
        ...     priority="P1",
        ...     acceptance_criteria=["Can login with valid credentials"]
        ... )
    """
    id: str
    title: str
    description: str
    priority: str = "P2"
    acceptance_criteria: list[str] = field(default_factory=list)
    status: str = "draft"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Requirement:
    """A functional or non-functional requirement.

    Attributes:
        id: Unique identifier
        type: Requirement type (functional, non-functional, constraint)
        description: Requirement description
        rationale: Why this requirement exists
        user_stories: Related user story IDs
        status: Implementation status
        metadata: Additional metadata

    Example:
        >>> req = Requirement(
        ...     id="REQ-001",
        ...     type="functional",
        ...     description="System must authenticate users",
        ...     rationale="Security requirement"
        ... )
    """
    id: str
    type: str
    description: str
    rationale: str | None = None
    user_stories: list[str] = field(default_factory=list)
    status: str = "draft"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Specification:
    """A feature specification document.

    Attributes:
        id: Unique identifier
        title: Specification title
        description: High-level description
        user_stories: List of user stories
        requirements: List of requirements
        open_questions: Questions that need answers during refinement
        status: Specification status
        created_at: Creation timestamp
        updated_at: Last update timestamp
        metadata: Additional metadata

    Example:
        >>> spec = Specification(
        ...     id="SPEC-001",
        ...     title="Authentication Feature",
        ...     description="Add user authentication to the app",
        ...     user_stories=[story],
        ...     requirements=[req]
        ... )
    """
    id: str
    title: str
    description: str
    user_stories: list[UserStory] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    status: str = "draft"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert specification to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "user_stories": [
                {
                    "id": s.id,
                    "title": s.title,
                    "description": s.description,
                    "priority": s.priority,
                    "acceptance_criteria": s.acceptance_criteria,
                    "status": s.status,
                    "metadata": s.metadata,
                }
                for s in self.user_stories
            ],
            "requirements": [
                {
                    "id": r.id,
                    "type": r.type,
                    "description": r.description,
                    "rationale": r.rationale,
                    "user_stories": r.user_stories,
                    "status": r.status,
                    "metadata": r.metadata,
                }
                for r in self.requirements
            ],
            "open_questions": self.open_questions,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
