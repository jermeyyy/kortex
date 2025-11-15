"""Unit tests for memory management tools.

Tests cover memory CRUD operations, querying, filtering, and
application of memories to AI context.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from kortex_mcp.tools.memory_tools import MemoryTools
from kortex_mcp.models.memory import Memory, MemoryCategory, MemoryStats


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemoryToolsInitialization:
    """Test memory tools initialization."""

    async def test_init_creates_tools_with_project_root(self, temp_dir: Path):
        """Test that MemoryTools initializes with project root."""
        tools = MemoryTools(project_root=temp_dir)
        
        assert tools.project_root == temp_dir
        assert tools.memory_path == temp_dir / ".kortex" / "memories"
        assert not tools._initialized

    async def test_initialize_creates_memory_directory(self, temp_dir: Path):
        """Test that initialize creates memory directory."""
        tools = MemoryTools(project_root=temp_dir)
        
        await tools.initialize()
        
        assert tools.memory_path.exists()
        assert tools._initialized

    async def test_initialize_only_runs_once(self, temp_dir: Path):
        """Test that initialize only runs once."""
        tools = MemoryTools(project_root=temp_dir)
        
        await tools.initialize()
        await tools.initialize()  # Should not reinitialize
        
        assert tools._initialized


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemoryToolsStore:
    """Test storing memories."""

    async def test_store_memory_creates_new_memory(self, temp_dir: Path):
        """Test storing a new memory."""
        tools = MemoryTools(project_root=temp_dir)
        
        result = await tools.store_memory(
            category="preferences",
            title="DI Framework",
            content="Use Koin for dependency injection",
            tags=["di", "koin"]
        )
        
        assert result["success"] is True
        assert result["action"] == "created"
        assert "memory_id" in result
        assert result["category"] == "preferences"
        assert result["title"] == "DI Framework"

    async def test_store_memory_updates_existing(self, temp_dir: Path):
        """Test updating an existing memory."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Create initial memory
        result1 = await tools.store_memory(
            category="preferences",
            title="DI Framework",
            content="Use Koin",
            tags=["di"]
        )
        memory_id = result1["memory_id"]
        
        # Update it
        result2 = await tools.store_memory(
            category="preferences",
            title="DI Framework Updated",
            content="Use Koin for dependency injection",
            tags=["di", "koin"],
            memory_id=memory_id
        )
        
        assert result2["success"] is True
        assert result2["action"] == "updated"
        assert result2["memory_id"] == memory_id

    async def test_store_memory_with_metadata(self, temp_dir: Path):
        """Test storing memory with metadata."""
        tools = MemoryTools(project_root=temp_dir)
        
        result = await tools.store_memory(
            category="architecture",
            title="MVVM Pattern",
            content="Use MVVM for UI layer",
            metadata={"source": "team_discussion", "priority": "high"}
        )
        
        assert result["success"] is True
        assert "memory_id" in result

    async def test_store_memory_invalid_category_raises_error(self, temp_dir: Path):
        """Test that invalid category raises ValueError."""
        tools = MemoryTools(project_root=temp_dir)
        
        with pytest.raises(ValueError, match="Invalid category"):
            await tools.store_memory(
                category="invalid_category",
                title="Test",
                content="Test content"
            )

    async def test_store_memory_empty_title_validation(self, temp_dir: Path):
        """Test that empty title fails validation."""
        tools = MemoryTools(project_root=temp_dir)
        
        with pytest.raises(ValueError):
            await tools.store_memory(
                category="preferences",
                title="",
                content="Test content"
            )


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemoryToolsQuery:
    """Test querying memories."""

    async def test_query_memory_by_category(self, temp_dir: Path):
        """Test querying memories by category."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memories in different categories
        await tools.store_memory(
            category="preferences",
            title="Pref 1",
            content="Content 1",
            tags=["tag1"]
        )
        await tools.store_memory(
            category="architecture",
            title="Arch 1",
            content="Content 2",
            tags=["tag2"]
        )
        
        # Query by category
        result = await tools.query_memory(category="preferences")
        
        assert result["success"] is True
        assert result["count"] == 1
        assert result["memories"][0]["category"] == "preferences"

    async def test_query_memory_by_tags(self, temp_dir: Path):
        """Test querying memories by tags."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memories with different tags
        await tools.store_memory(
            category="preferences",
            title="DI Framework",
            content="Use Koin",
            tags=["di", "koin"]
        )
        await tools.store_memory(
            category="preferences",
            title="Networking",
            content="Use Ktor",
            tags=["networking", "ktor"]
        )
        
        # Query by tags
        result = await tools.query_memory(tags=["di"])
        
        assert result["success"] is True
        assert result["count"] == 1
        assert "koin" in result["memories"][0]["tags"]

    async def test_query_memory_with_search_text(self, temp_dir: Path):
        """Test querying memories with text search."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memories
        await tools.store_memory(
            category="preferences",
            title="DI Framework",
            content="Use Koin for dependency injection",
            tags=["di"]
        )
        await tools.store_memory(
            category="preferences",
            title="Networking",
            content="Use Ktor for HTTP client",
            tags=["networking"]
        )
        
        # Query with search text
        result = await tools.query_memory(search_text="Koin")
        
        assert result["success"] is True
        assert result["count"] >= 1

    async def test_query_memory_with_limit(self, temp_dir: Path):
        """Test querying memories with result limit."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store multiple memories
        for i in range(5):
            await tools.store_memory(
                category="preferences",
                title=f"Preference {i}",
                content=f"Content {i}",
                tags=["test"]
            )
        
        # Query with limit
        result = await tools.query_memory(category="preferences", limit=3)
        
        assert result["success"] is True
        assert result["count"] <= 3

    async def test_query_memory_empty_results(self, temp_dir: Path):
        """Test querying with no matches."""
        tools = MemoryTools(project_root=temp_dir)
        
        result = await tools.query_memory(category="architecture")
        
        assert result["success"] is True
        assert result["count"] == 0
        assert result["memories"] == []


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemoryToolsList:
    """Test listing memories."""

    async def test_list_memories_all(self, temp_dir: Path):
        """Test listing all memories."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memories
        await tools.store_memory(
            category="preferences",
            title="Pref 1",
            content="Content 1"
        )
        await tools.store_memory(
            category="architecture",
            title="Arch 1",
            content="Content 2"
        )
        
        result = await tools.list_memories()
        
        assert result["success"] is True
        assert result["count"] == 2

    async def test_list_memories_by_category(self, temp_dir: Path):
        """Test listing memories filtered by category."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memories
        await tools.store_memory(category="preferences", title="P1", content="C1")
        await tools.store_memory(category="architecture", title="A1", content="C2")
        
        result = await tools.list_memories(category="preferences")
        
        assert result["success"] is True
        assert result["count"] == 1
        assert result["memories"][0]["category"] == "preferences"

    async def test_list_memories_truncates_long_content(self, temp_dir: Path):
        """Test that list truncates long content."""
        tools = MemoryTools(project_root=temp_dir)
        
        long_content = "A" * 200
        await tools.store_memory(
            category="preferences",
            title="Long Content",
            content=long_content
        )
        
        result = await tools.list_memories()
        
        assert result["success"] is True
        assert len(result["memories"][0]["content"]) <= 103  # 100 + "..."


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemoryToolsGet:
    """Test getting specific memories."""

    async def test_get_memory_returns_full_details(self, temp_dir: Path):
        """Test getting a specific memory."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memory
        store_result = await tools.store_memory(
            category="preferences",
            title="DI Framework",
            content="Use Koin for dependency injection",
            tags=["di", "koin"],
            metadata={"priority": "high"}
        )
        memory_id = store_result["memory_id"]
        
        # Get memory
        result = await tools.get_memory(memory_id)
        
        assert result["success"] is True
        assert result["memory"]["id"] == memory_id
        assert result["memory"]["title"] == "DI Framework"
        assert result["memory"]["tags"] == ["di", "koin"]
        assert result["memory"]["metadata"] == {"priority": "high"}

    async def test_get_memory_updates_access_tracking(self, temp_dir: Path):
        """Test that getting a memory updates access tracking."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memory
        store_result = await tools.store_memory(
            category="preferences",
            title="Test",
            content="Content"
        )
        memory_id = store_result["memory_id"]
        
        # Get initial access count (store_memory calls get once to check if exists)
        result0 = await tools.get_memory(memory_id)
        initial_count = result0["memory"]["access_count"]
        
        # Get memory again
        result1 = await tools.get_memory(memory_id)
        
        # Access count should increment
        assert result1["memory"]["access_count"] == initial_count + 1

    async def test_get_memory_not_found_raises_error(self, temp_dir: Path):
        """Test that getting non-existent memory raises error."""
        tools = MemoryTools(project_root=temp_dir)
        await tools.initialize()
        
        with pytest.raises(ValueError, match="Memory not found"):
            await tools.get_memory("nonexistent_id")


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemoryToolsDelete:
    """Test deleting memories."""

    async def test_delete_memory_removes_memory(self, temp_dir: Path):
        """Test deleting a memory."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memory
        store_result = await tools.store_memory(
            category="preferences",
            title="Test",
            content="Content"
        )
        memory_id = store_result["memory_id"]
        
        # Delete memory
        result = await tools.delete_memory(memory_id)
        
        assert result["success"] is True
        assert "deleted successfully" in result["message"]
        
        # Verify it's gone
        with pytest.raises(ValueError):
            await tools.get_memory(memory_id)

    async def test_delete_memory_not_found_raises_error(self, temp_dir: Path):
        """Test deleting non-existent memory raises error."""
        tools = MemoryTools(project_root=temp_dir)
        await tools.initialize()
        
        with pytest.raises(ValueError, match="Memory not found"):
            await tools.delete_memory("nonexistent_id")


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemoryToolsStats:
    """Test memory statistics."""

    async def test_get_memory_stats_returns_statistics(self, temp_dir: Path):
        """Test getting memory statistics."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store some memories
        await tools.store_memory(category="preferences", title="P1", content="C1")
        await tools.store_memory(category="architecture", title="A1", content="C2")
        await tools.store_memory(category="preferences", title="P2", content="C3")
        
        stats = await tools.get_memory_stats()
        
        assert stats["success"] is True
        assert stats["total_memories"] == 3
        assert stats["by_category"]["preferences"] == 2
        assert stats["by_category"]["architecture"] == 1

    async def test_get_memory_stats_empty_store(self, temp_dir: Path):
        """Test stats with empty store."""
        tools = MemoryTools(project_root=temp_dir)
        await tools.initialize()
        
        stats = await tools.get_memory_stats()
        
        assert stats["success"] is True
        assert stats["total_memories"] == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemoryToolsApplyToContext:
    """Test applying memories to context."""

    async def test_apply_memories_by_context_type(self, temp_dir: Path):
        """Test applying memories based on context type."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memories
        await tools.store_memory(
            category="architecture",
            title="MVVM",
            content="Use MVVM pattern",
            tags=["architecture", "pattern"]
        )
        await tools.store_memory(
            category="preferences",
            title="DI",
            content="Use Koin",
            tags=["di"]
        )
        
        result = await tools.apply_memories_to_context(
            context_type="architecture",
            limit=10
        )
        
        assert result["success"] is True
        assert result["count"] >= 1
        assert len(result["relevant_memories"]) >= 1
        assert result["relevant_memories"][0]["category"] == "architecture"

    async def test_apply_memories_with_keywords(self, temp_dir: Path):
        """Test applying memories with keyword filtering."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memories with tags
        await tools.store_memory(
            category="preferences",
            title="DI Framework",
            content="Use Koin",
            tags=["di", "koin"]
        )
        await tools.store_memory(
            category="preferences",
            title="Networking",
            content="Use Ktor",
            tags=["networking"]
        )
        
        result = await tools.apply_memories_to_context(
            context_type="implementation",
            context_keywords=["di"],
            limit=5
        )
        
        assert result["success"] is True
        assert result["count"] >= 1

    async def test_apply_memories_returns_suggestions(self, temp_dir: Path):
        """Test that apply_memories returns formatted suggestions."""
        tools = MemoryTools(project_root=temp_dir)
        
        await tools.store_memory(
            category="architecture",
            title="MVVM",
            content="Use MVVM pattern for UI layer",
            tags=["architecture"]
        )
        
        result = await tools.apply_memories_to_context(
            context_type="architecture",
            limit=10
        )
        
        assert result["success"] is True
        assert "suggestions" in result
        assert len(result["suggestions"]) >= 1
        assert "ARCHITECTURE" in result["suggestions"][0]

    async def test_apply_memories_updates_access_tracking(self, temp_dir: Path):
        """Test that applying memories updates access counts."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memory
        store_result = await tools.store_memory(
            category="architecture",
            title="MVVM",
            content="Use MVVM",
            tags=["arch"]
        )
        memory_id = store_result["memory_id"]
        
        # Apply to context
        await tools.apply_memories_to_context(context_type="architecture")
        
        # Check access count increased
        result = await tools.get_memory(memory_id)
        assert result["memory"]["access_count"] >= 1

    async def test_apply_memories_limits_results(self, temp_dir: Path):
        """Test that apply_memories respects limit parameter."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store many memories
        for i in range(10):
            await tools.store_memory(
                category="architecture",
                title=f"Pattern {i}",
                content=f"Content {i}",
                tags=["arch"]
            )
        
        result = await tools.apply_memories_to_context(
            context_type="architecture",
            limit=3
        )
        
        assert result["count"] <= 3


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemoryToolsClear:
    """Test clearing all memories."""

    async def test_clear_all_memories_removes_all(self, temp_dir: Path):
        """Test clearing all memories."""
        tools = MemoryTools(project_root=temp_dir)
        
        # Store memories
        await tools.store_memory(category="preferences", title="P1", content="C1")
        await tools.store_memory(category="architecture", title="A1", content="C2")
        
        # Clear all
        result = await tools.clear_all_memories()
        
        assert result["success"] is True
        assert "cleared" in result["message"].lower()
        
        # Verify all gone
        stats = await tools.get_memory_stats()
        assert stats["total_memories"] == 0
