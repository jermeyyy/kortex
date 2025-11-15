"""Memory system data models.

This module defines data structures for storing and retrieving
project-specific knowledge, patterns, decisions, and preferences.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class MemoryCategory(Enum):
    """Categories for organizing project memories.

    Values:
        ARCHITECTURE: High-level architecture decisions and patterns
        PATTERNS: Code patterns and idioms used in the project
        PREFERENCES: Developer preferences and conventions
        DECISIONS: Technical decisions and their rationale
        DEPENDENCIES: Information about dependencies and their usage
        TESTING: Testing strategies and patterns
        DEPLOYMENT: Deployment configuration and procedures
        PERFORMANCE: Performance considerations and optimizations
        SECURITY: Security requirements and practices
        DOCUMENTATION: Documentation standards and locations
        OTHER: Uncategorized memories
    """
    ARCHITECTURE = "architecture"
    PATTERNS = "patterns"
    PREFERENCES = "preferences"
    DECISIONS = "decisions"
    DEPENDENCIES = "dependencies"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    OTHER = "other"


@dataclass
class Memory:
    """A single memory item storing project knowledge.

    Attributes:
        id: Unique identifier for the memory
        category: Memory category
        title: Short descriptive title
        content: Memory content/description
        tags: Optional tags for filtering
        created_at: Creation timestamp
        last_accessed: Last access timestamp
        access_count: Number of times accessed
        metadata: Additional metadata

    Example:
        >>> memory = Memory(
        ...     id="mem-001",
        ...     category=MemoryCategory.PREFERENCES,
        ...     title="Dependency Injection",
        ...     content="Use Koin for dependency injection throughout the project",
        ...     tags=["di", "koin"]
        ... )
    """
    id: str
    category: MemoryCategory
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary for serialization.

        Returns:
            Dictionary representation

        Example:
            >>> data = memory.to_dict()
            >>> print(data["title"])
        """
        return {
            "id": self.id,
            "category": self.category.value,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Memory":
        """Create Memory from dictionary.

        Args:
            data: Dictionary with memory data

        Returns:
            Memory instance

        Example:
            >>> memory = Memory.from_dict(data)
        """
        return Memory(
            id=data["id"],
            category=MemoryCategory(data["category"]),
            title=data["title"],
            content=data["content"],
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data.get("access_count", 0),
            metadata=data.get("metadata", {}),
        )

    def update_access(self) -> None:
        """Update last accessed timestamp and increment access count.

        Example:
            >>> memory.update_access()
            >>> print(memory.access_count)
            1
        """
        self.last_accessed = datetime.now()
        self.access_count += 1

    def matches_tags(self, tags: list[str]) -> bool:
        """Check if memory matches any of the provided tags.

        Args:
            tags: List of tags to match against

        Returns:
            True if any tag matches

        Example:
            >>> memory.matches_tags(["di", "architecture"])
            True
        """
        if not tags:
            return True
        return any(tag in self.tags for tag in tags)

    def matches_query(self, query: str) -> bool:
        """Check if memory matches a text query.

        Searches in title, content, and tags.

        Args:
            query: Search query (case-insensitive)

        Returns:
            True if query matches

        Example:
            >>> memory.matches_query("koin")
            True
        """
        query_lower = query.lower()
        return (
            query_lower in self.title.lower()
            or query_lower in self.content.lower()
            or any(query_lower in tag.lower() for tag in self.tags)
        )

    def __str__(self) -> str:
        """String representation of memory.

        Returns:
            Formatted memory string

        Example:
            >>> print(memory)
            [PREFERENCES] Dependency Injection
        """
        return f"[{self.category.name}] {self.title}"


@dataclass
class MemoryQuery:
    """Query parameters for searching memories.

    Attributes:
        category: Filter by category (optional)
        tags: Filter by tags (optional)
        query: Text search query (optional)
        limit: Maximum number of results (optional)
        sort_by: Sort field ("created_at", "last_accessed", "access_count")
        ascending: Sort order (True for ascending)

    Example:
        >>> query = MemoryQuery(
        ...     category=MemoryCategory.PREFERENCES,
        ...     tags=["di"],
        ...     limit=10
        ... )
    """
    category: Optional[MemoryCategory] = None
    tags: list[str] = field(default_factory=list)
    query: Optional[str] = None
    limit: Optional[int] = None
    sort_by: str = "last_accessed"
    ascending: bool = False

    def matches(self, memory: Memory) -> bool:
        """Check if a memory matches this query.

        Args:
            memory: Memory to check

        Returns:
            True if memory matches all criteria

        Example:
            >>> if query.matches(memory):
            ...     print("Memory matches query")
        """
        # Check category
        if self.category and memory.category != self.category:
            return False

        # Check tags
        if self.tags and not memory.matches_tags(self.tags):
            return False

        # Check text query
        if self.query and not memory.matches_query(self.query):
            return False

        return True


@dataclass
class MemoryStats:
    """Statistics about the memory store.

    Attributes:
        total_memories: Total number of memories
        by_category: Count of memories per category
        most_accessed: Most frequently accessed memories
        recent_memories: Recently created memories

    Example:
        >>> stats = MemoryStats(
        ...     total_memories=50,
        ...     by_category={MemoryCategory.PREFERENCES: 10}
        ... )
    """
    total_memories: int
    by_category: Dict[MemoryCategory, int]
    most_accessed: list[Memory] = field(default_factory=list)
    recent_memories: list[Memory] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary.

        Returns:
            Dictionary representation

        Example:
            >>> data = stats.to_dict()
        """
        return {
            "total_memories": self.total_memories,
            "by_category": {
                cat.value: count for cat, count in self.by_category.items()
            },
            "most_accessed": [mem.to_dict() for mem in self.most_accessed],
            "recent_memories": [mem.to_dict() for mem in self.recent_memories],
        }


def validate_memory(memory: Memory) -> list[str]:
    """Validate a memory object.

    Args:
        memory: Memory to validate

    Returns:
        List of validation errors (empty if valid)

    Example:
        >>> errors = validate_memory(memory)
        >>> if errors:
        ...     print("Validation errors:", errors)
    """
    errors = []

    if not memory.id or not memory.id.strip():
        errors.append("Memory ID is required")

    if not memory.title or not memory.title.strip():
        errors.append("Memory title is required")

    if not memory.content or not memory.content.strip():
        errors.append("Memory content is required")

    if not isinstance(memory.category, MemoryCategory):
        errors.append("Invalid memory category")

    if not isinstance(memory.tags, list):
        errors.append("Tags must be a list")

    return errors


def create_memory_id(category: MemoryCategory, title: str) -> str:
    """Generate a memory ID from category and title.

    Args:
        category: Memory category
        title: Memory title

    Returns:
        Generated memory ID

    Example:
        >>> mem_id = create_memory_id(MemoryCategory.PREFERENCES, "DI Pattern")
        >>> print(mem_id)
        'preferences_di_pattern'
    """
    # Create slug from title
    slug = title.lower().replace(" ", "_")
    # Remove special characters
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    # Combine with category
    return f"{category.value}_{slug}"
