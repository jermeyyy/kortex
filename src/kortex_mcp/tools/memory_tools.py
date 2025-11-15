"""Memory management MCP tools.

This module provides MCP tools for storing, querying, and applying
project memories to enhance AI assistance with project-specific knowledge.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.memory import (
    Memory, MemoryCategory, MemoryQuery, MemoryStats,
    create_memory_id, validate_memory
)
from ..storage.memory_store import MemoryStore
from ..utils.logging import get_logger


logger = get_logger(__name__)


class MemoryTools:
    """MCP tools for memory management.

    Provides tools for storing project knowledge, preferences, and patterns
    that can be recalled to provide context-aware assistance.

    Attributes:
        store: Memory storage instance
        project_root: Path to project root directory

    Example:
        >>> tools = MemoryTools(project_root=Path("/project"))
        >>> await tools.initialize()
        >>> result = await tools.store_memory(
        ...     category="preferences",
        ...     title="DI Framework",
        ...     content="Use Koin for dependency injection",
        ...     tags=["di", "koin"]
        ... )
    """

    def __init__(self, project_root: Path):
        """Initialize memory tools.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.memory_path = project_root / ".kortex" / "memories"
        self.store = MemoryStore(self.memory_path)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize memory storage.

        Creates memory directory if needed and loads existing memories.

        Raises:
            IOError: If memory storage cannot be initialized

        Example:
            >>> await tools.initialize()
        """
        if not self._initialized:
            await self.store.initialize()
            self._initialized = True
            logger.info("Memory tools initialized")

    async def store_memory(
        self,
        category: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store a new memory or update an existing one.

        Args:
            category: Memory category (architecture, patterns, preferences, etc.)
            title: Short descriptive title
            content: Memory content/description
            tags: Optional list of tags for filtering
            metadata: Optional additional metadata
            memory_id: Optional ID for updating existing memory

        Returns:
            Dictionary with success status and memory details

        Raises:
            ValueError: If category is invalid or memory validation fails
            IOError: If save operation fails

        Example:
            >>> result = await tools.store_memory(
            ...     category="preferences",
            ...     title="DI Framework",
            ...     content="Use Koin for dependency injection throughout the project",
            ...     tags=["di", "koin", "architecture"]
            ... )
            >>> print(result["memory_id"])
        """
        await self.initialize()

        # Validate and convert category
        try:
            mem_category = MemoryCategory(category.lower())
        except ValueError:
            valid_categories = [c.value for c in MemoryCategory]
            raise ValueError(
                f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"
            )

        # Create or get memory ID
        if memory_id is None:
            memory_id = create_memory_id(mem_category, title)

        # Check if updating existing memory
        existing = await self.store.get(memory_id)
        
        if existing:
            # Update existing memory
            existing.title = title
            existing.content = content
            existing.tags = tags or []
            existing.metadata = metadata or {}
            existing.last_accessed = datetime.now()
            memory = existing
            action = "updated"
        else:
            # Create new memory
            memory = Memory(
                id=memory_id,
                category=mem_category,
                title=title,
                content=content,
                tags=tags or [],
                metadata=metadata or {},
            )
            action = "created"

        # Save memory
        await self.store.save(memory)

        logger.info(f"Memory {action}: {memory_id}")

        return {
            "success": True,
            "action": action,
            "memory_id": memory_id,
            "category": category,
            "title": title,
            "message": f"Memory '{title}' {action} successfully",
        }

    async def query_memory(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search_text: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Query memories with filtering and search.

        Args:
            category: Optional category filter
            tags: Optional tags to filter by
            search_text: Optional text to search in title/content
            limit: Optional maximum number of results

        Returns:
            Dictionary with matching memories

        Example:
            >>> result = await tools.query_memory(
            ...     category="preferences",
            ...     tags=["di"],
            ...     limit=10
            ... )
            >>> for mem in result["memories"]:
            ...     print(f"{mem['title']}: {mem['content']}")
        """
        await self.initialize()

        # Build query
        query = MemoryQuery()

        if category:
            try:
                query.category = MemoryCategory(category.lower())
            except ValueError:
                valid_categories = [c.value for c in MemoryCategory]
                raise ValueError(
                    f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"
                )

        if tags:
            query.tags = tags

        if search_text:
            query.query = search_text

        if limit:
            query.limit = limit

        # Execute search
        memories = await self.store.search(query)

        # Convert to dictionaries
        results = []
        for memory in memories:
            results.append({
                "id": memory.id,
                "category": memory.category.value,
                "title": memory.title,
                "content": memory.content,
                "tags": memory.tags,
                "created_at": memory.created_at.isoformat(),
                "last_accessed": memory.last_accessed.isoformat(),
                "access_count": memory.access_count,
            })

        logger.debug(f"Memory query returned {len(results)} results")

        return {
            "success": True,
            "count": len(results),
            "memories": results,
        }

    async def list_memories(
        self,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all memories, optionally filtered by category.

        Args:
            category: Optional category to filter by

        Returns:
            Dictionary with list of memories

        Example:
            >>> result = await tools.list_memories(category="architecture")
            >>> print(f"Found {result['count']} architecture decisions")
        """
        await self.initialize()

        if category:
            # List by category
            try:
                mem_category = MemoryCategory(category.lower())
            except ValueError:
                valid_categories = [c.value for c in MemoryCategory]
                raise ValueError(
                    f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"
                )

            memories = await self.store.list_by_category(mem_category)
        else:
            # List all
            memories = await self.store.get_all()

        # Convert to dictionaries
        results = []
        for memory in memories:
            results.append({
                "id": memory.id,
                "category": memory.category.value,
                "title": memory.title,
                "content": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content,
                "tags": memory.tags,
                "created_at": memory.created_at.isoformat(),
            })

        return {
            "success": True,
            "count": len(results),
            "memories": results,
        }

    async def get_memory(self, memory_id: str) -> Dict[str, Any]:
        """Get a specific memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Dictionary with memory details

        Raises:
            ValueError: If memory not found

        Example:
            >>> result = await tools.get_memory("pref_001")
            >>> print(result["memory"]["content"])
        """
        await self.initialize()

        memory = await self.store.get(memory_id)

        if not memory:
            raise ValueError(f"Memory not found: {memory_id}")

        # Note: store.get() already updates access tracking

        return {
            "success": True,
            "memory": {
                "id": memory.id,
                "category": memory.category.value,
                "title": memory.title,
                "content": memory.content,
                "tags": memory.tags,
                "created_at": memory.created_at.isoformat(),
                "last_accessed": memory.last_accessed.isoformat(),
                "access_count": memory.access_count,
                "metadata": memory.metadata,
            },
        }

    async def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory.

        Args:
            memory_id: Memory identifier

        Returns:
            Dictionary with success status

        Example:
            >>> result = await tools.delete_memory("pref_001")
            >>> print(result["message"])
        """
        await self.initialize()

        success = await self.store.delete(memory_id)

        if success:
            logger.info(f"Deleted memory: {memory_id}")
            return {
                "success": True,
                "message": f"Memory {memory_id} deleted successfully",
            }
        else:
            raise ValueError(f"Memory not found: {memory_id}")

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories.

        Returns:
            Dictionary with memory statistics

        Example:
            >>> stats = await tools.get_memory_stats()
            >>> print(f"Total memories: {stats['total_memories']}")
            >>> print(f"By category: {stats['by_category']}")
        """
        await self.initialize()

        stats = await self.store.get_stats()

        return {
            "success": True,
            "total_memories": stats.total_memories,
            "by_category": {k.value: v for k, v in stats.by_category.items()},
            "most_accessed": [
                {"id": m.id, "title": m.title, "access_count": m.access_count}
                for m in stats.most_accessed[:10]
            ],
            "recent_memories": [
                {"id": m.id, "title": m.title, "created_at": m.created_at.isoformat()}
                for m in stats.recent_memories[:10]
            ],
        }

    async def apply_memories_to_context(
        self,
        context_type: str,
        context_keywords: Optional[List[str]] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Retrieve relevant memories to enrich AI context.

        This function helps apply project-specific knowledge to AI suggestions
        by finding memories relevant to the current context.

        Args:
            context_type: Type of context (e.g., "architecture", "patterns", "implementation")
            context_keywords: Optional keywords to help find relevant memories
            limit: Maximum number of memories to return

        Returns:
            Dictionary with relevant memories and application suggestions

        Example:
            >>> result = await tools.apply_memories_to_context(
            ...     context_type="architecture",
            ...     context_keywords=["di", "viewmodel"],
            ...     limit=5
            ... )
            >>> for mem in result["relevant_memories"]:
            ...     print(f"Consider: {mem['title']}")
        """
        await self.initialize()

        relevant_memories: List[Memory] = []

        # Try to map context_type to category
        category_mapping = {
            "architecture": MemoryCategory.ARCHITECTURE,
            "patterns": MemoryCategory.PATTERNS,
            "preferences": MemoryCategory.PREFERENCES,
            "implementation": MemoryCategory.PATTERNS,
            "testing": MemoryCategory.TESTING,
            "deployment": MemoryCategory.DEPLOYMENT,
            "performance": MemoryCategory.PERFORMANCE,
            "security": MemoryCategory.SECURITY,
        }

        category = category_mapping.get(context_type.lower())

        if category:
            # Get memories by category
            cat_memories = await self.store.list_by_category(category)
            relevant_memories.extend(cat_memories)

        # If we have keywords, also search by tags
        if context_keywords:
            tagged_memories = await self.store.list_by_tags(context_keywords)
            # Add unique memories
            existing_ids = {m.id for m in relevant_memories}
            for mem in tagged_memories:
                if mem.id not in existing_ids:
                    relevant_memories.append(mem)

        # Sort by relevance (most recently accessed first, then by access count)
        relevant_memories.sort(
            key=lambda m: (m.last_accessed, m.access_count),
            reverse=True
        )

        # Limit results
        relevant_memories = relevant_memories[:limit]

        # Update access tracking for retrieved memories
        for memory in relevant_memories:
            memory.last_accessed = datetime.now()
            memory.access_count += 1
            await self.store.save(memory)

        # Convert to response format
        memories_data = []
        for memory in relevant_memories:
            memories_data.append({
                "id": memory.id,
                "category": memory.category.value,
                "title": memory.title,
                "content": memory.content,
                "tags": memory.tags,
                "relevance_score": memory.access_count,  # Simple relevance based on usage
            })

        # Generate application suggestions
        suggestions = []
        for memory in relevant_memories:
            suggestions.append(
                f"[{memory.category.value.upper()}] {memory.title}: {memory.content}"
            )

        logger.debug(f"Applied {len(relevant_memories)} memories to context '{context_type}'")

        return {
            "success": True,
            "context_type": context_type,
            "relevant_memories": memories_data,
            "count": len(memories_data),
            "suggestions": suggestions,
            "message": f"Found {len(memories_data)} relevant memories for {context_type} context",
        }

    async def clear_all_memories(self) -> Dict[str, Any]:
        """Clear all stored memories.

        **Warning**: This operation cannot be undone.

        Returns:
            Dictionary with success status

        Example:
            >>> result = await tools.clear_all_memories()
            >>> print(result["message"])
        """
        await self.initialize()

        await self.store.clear()

        logger.warning("All memories cleared")

        return {
            "success": True,
            "message": "All memories have been cleared",
        }
