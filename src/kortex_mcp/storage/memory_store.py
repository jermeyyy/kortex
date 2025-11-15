"""Memory storage with JSON-based persistence.

This module provides persistent storage for project memories using
JSON files.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from ..utils.logging import get_logger
from ..utils.file_utils import ensure_directory
from ..models.memory import (
    Memory, MemoryCategory, MemoryQuery, MemoryStats,
    validate_memory, create_memory_id
)


logger = get_logger(__name__)


class MemoryStore:
    """Persistent storage for project memories.

    Stores memories in JSON format with support for CRUD operations,
    search, and filtering.

    Attributes:
        storage_path: Path to the memories directory
        memories: In-memory cache of loaded memories
        _lock: Async lock for thread-safe operations

    Example:
        >>> store = MemoryStore(Path(".kortex/memories"))
        >>> await store.initialize()
        >>> memory = Memory(...)
        >>> await store.save(memory)
        >>> results = await store.search(MemoryQuery(category=MemoryCategory.PREFERENCES))
    """

    def __init__(self, storage_path: Path):
        """Initialize memory store.

        Args:
            storage_path: Directory path for storing memories
        """
        self.storage_path = storage_path
        self.memories: Dict[str, Memory] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize storage and load existing memories.

        Creates storage directory if it doesn't exist and loads
        all memories from disk.

        Raises:
            IOError: If storage directory cannot be created

        Example:
            >>> await store.initialize()
        """
        logger.info(f"Initializing memory store at {self.storage_path}")
        
        # Create storage directory
        ensure_directory(self.storage_path)
        
        # Load existing memories
        await self._load_all()
        
        self._initialized = True
        logger.info(f"Memory store initialized with {len(self.memories)} memories")

    async def _load_all(self) -> None:
        """Load all memories from disk."""
        if not self.storage_path.exists():
            return

        # Get all JSON files
        memory_files = list(self.storage_path.glob("*.json"))
        
        for file_path in memory_files:
            try:
                # Read JSON file (synchronous is fine for local files)
                data = json.loads(file_path.read_text())
                memory = Memory.from_dict(data)
                self.memories[memory.id] = memory
            except Exception as e:
                logger.error(f"Failed to load memory from {file_path}: {e}")

    def _get_memory_path(self, memory_id: str) -> Path:
        """Get file path for a memory.

        Args:
            memory_id: Memory identifier

        Returns:
            Path to the memory file
        """
        return self.storage_path / f"{memory_id}.json"

    async def save(self, memory: Memory) -> None:
        """Save a memory to storage.

        Creates a new memory or updates an existing one.

        Args:
            memory: Memory to save

        Raises:
            ValueError: If memory validation fails
            IOError: If save operation fails

        Example:
            >>> memory = Memory(
            ...     id="pref_001",
            ...     category=MemoryCategory.PREFERENCES,
            ...     title="DI Framework",
            ...     content="Use Koin for dependency injection"
            ... )
            >>> await store.save(memory)
        """
        # Validate memory
        errors = validate_memory(memory)
        if errors:
            raise ValueError(f"Invalid memory: {', '.join(errors)}")

        async with self._lock:
            self._save_unlocked(memory)

    def _save_unlocked(self, memory: Memory) -> None:
        """Internal save method without locking (assumes lock is held).
        
        Args:
            memory: Memory to save
        """
        # Save to disk
        file_path = self._get_memory_path(memory.id)
        data = memory.to_dict()
        
        try:
            # Write JSON file (synchronous is fine for local files)
            file_path.write_text(json.dumps(data, indent=2))
            # Update in-memory cache
            self.memories[memory.id] = memory
            logger.debug(f"Saved memory: {memory.id}")
        except Exception as e:
            logger.error(f"Failed to save memory {memory.id}: {e}")
            raise IOError(f"Failed to save memory: {e}") from e

    async def get(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID.

        Updates access timestamp and count.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory instance or None if not found

        Example:
            >>> memory = await store.get("pref_001")
            >>> if memory:
            ...     print(memory.content)
        """
        async with self._lock:
            memory = self.memories.get(memory_id)
            
            if memory:
                # Update access tracking
                memory.update_access()
                # Save updated memory using internal method (lock already held)
                self._save_unlocked(memory)
            
            return memory

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory.

        Args:
            memory_id: Memory identifier

        Returns:
            True if deleted, False if not found

        Example:
            >>> deleted = await store.delete("pref_001")
        """
        async with self._lock:
            if memory_id not in self.memories:
                return False

            # Delete from disk
            file_path = self._get_memory_path(memory_id)
            try:
                if file_path.exists():
                    file_path.unlink()
                
                # Remove from cache
                del self.memories[memory_id]
                logger.debug(f"Deleted memory: {memory_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete memory {memory_id}: {e}")
                return False

    async def search(self, query: MemoryQuery) -> List[Memory]:
        """Search for memories matching query criteria.

        Args:
            query: Query parameters

        Returns:
            List of matching memories

        Example:
            >>> query = MemoryQuery(
            ...     category=MemoryCategory.PREFERENCES,
            ...     tags=["di"],
            ...     limit=10
            ... )
            >>> results = await store.search(query)
        """
        async with self._lock:
            # Filter memories
            results = [
                memory for memory in self.memories.values()
                if query.matches(memory)
            ]

            # Sort results
            if query.sort_by == "created_at":
                results.sort(
                    key=lambda m: m.created_at,
                    reverse=not query.ascending
                )
            elif query.sort_by == "last_accessed":
                results.sort(
                    key=lambda m: m.last_accessed,
                    reverse=not query.ascending
                )
            elif query.sort_by == "access_count":
                results.sort(
                    key=lambda m: m.access_count,
                    reverse=not query.ascending
                )

            # Apply limit
            if query.limit and query.limit > 0:
                results = results[:query.limit]

            return results

    async def list_by_category(
        self,
        category: MemoryCategory
    ) -> List[Memory]:
        """List all memories in a category.

        Args:
            category: Memory category

        Returns:
            List of memories in the category

        Example:
            >>> memories = await store.list_by_category(MemoryCategory.PREFERENCES)
        """
        query = MemoryQuery(category=category)
        return await self.search(query)

    async def list_by_tags(self, tags: List[str]) -> List[Memory]:
        """List memories matching any of the given tags.

        Args:
            tags: List of tags to match

        Returns:
            List of matching memories

        Example:
            >>> memories = await store.list_by_tags(["di", "architecture"])
        """
        query = MemoryQuery(tags=tags)
        return await self.search(query)

    async def get_all(self) -> List[Memory]:
        """Get all memories.

        Returns:
            List of all memories

        Example:
            >>> all_memories = await store.get_all()
        """
        async with self._lock:
            return list(self.memories.values())

    async def get_stats(self) -> MemoryStats:
        """Get statistics about stored memories.

        Returns:
            MemoryStats object with statistics

        Example:
            >>> stats = await store.get_stats()
            >>> print(f"Total: {stats.total_memories}")
        """
        async with self._lock:
            # Count by category
            by_category: Dict[MemoryCategory, int] = {}
            for memory in self.memories.values():
                by_category[memory.category] = by_category.get(memory.category, 0) + 1

            # Most accessed (top 10)
            most_accessed = sorted(
                self.memories.values(),
                key=lambda m: m.access_count,
                reverse=True
            )[:10]

            # Recent memories (last 10)
            recent = sorted(
                self.memories.values(),
                key=lambda m: m.created_at,
                reverse=True
            )[:10]

            return MemoryStats(
                total_memories=len(self.memories),
                by_category=by_category,
                most_accessed=most_accessed,
                recent_memories=recent,
            )

    async def clear(self) -> None:
        """Clear all memories.

        Deletes all memory files and clears the cache.

        Example:
            >>> await store.clear()
        """
        async with self._lock:
            # Delete all files
            for memory_id in list(self.memories.keys()):
                file_path = self._get_memory_path(memory_id)
                try:
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete memory file {file_path}: {e}")

            # Clear cache
            self.memories.clear()
            logger.info("Memory store cleared")

    async def create_or_update(
        self,
        category: MemoryCategory,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        memory_id: Optional[str] = None,
    ) -> Memory:
        """Create a new memory or update existing one.

        Args:
            category: Memory category
            title: Memory title
            content: Memory content
            tags: Optional tags
            memory_id: Optional memory ID (generated if not provided)

        Returns:
            Created or updated Memory

        Example:
            >>> memory = await store.create_or_update(
            ...     category=MemoryCategory.PREFERENCES,
            ...     title="DI Framework",
            ...     content="Use Koin for DI",
            ...     tags=["di", "koin"]
            ... )
        """
        if not memory_id:
            memory_id = create_memory_id(category, title)

        # Check if memory exists
        existing = await self.get(memory_id)
        
        if existing:
            # Update existing
            existing.title = title
            existing.content = content
            existing.tags = tags or []
            existing.category = category
            memory = existing
        else:
            # Create new
            memory = Memory(
                id=memory_id,
                category=category,
                title=title,
                content=content,
                tags=tags or [],
            )

        await self.save(memory)
        return memory

    def is_initialized(self) -> bool:
        """Check if store is initialized.

        Returns:
            True if initialized

        Example:
            >>> if store.is_initialized():
            ...     print("Store ready")
        """
        return self._initialized
