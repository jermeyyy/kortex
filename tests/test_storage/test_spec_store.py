"""Unit tests for specification storage.

Tests cover SpecStore operations including:
- Store initialization and directory structure
- Saving specifications as Markdown
- Loading specifications from Markdown
- Listing specifications
- Deleting specifications
- Searching/filtering specifications
- Error handling and concurrent access
"""

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from kortex_mcp.models.specification import (
    Requirement,
    Specification,
    UserStory,
)
from kortex_mcp.storage.spec_store import SpecStore


@pytest.mark.unit
@pytest.mark.asyncio
class TestSpecStoreInitialization:
    """Test SpecStore initialization."""

    async def test_init_creates_store_with_storage_path(self, temp_dir: Path):
        """Test that SpecStore initializes with correct storage path."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)

        assert store.storage_path == storage_path
        assert store.specs == {}
        assert not store._initialized

    async def test_initialize_creates_specs_directory(self, temp_dir: Path):
        """Test that initialize creates specs directory structure."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)

        await store.initialize()

        assert storage_path.exists()
        assert storage_path.is_dir()
        assert store._initialized

    async def test_initialize_loads_existing_specs(self, temp_dir: Path):
        """Test that initialize loads existing specifications from disk."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)

        # Create a spec manually on disk
        spec_dir = storage_path / "SPEC-001"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("""# Authentication Feature

**ID**: SPEC-001
**Status**: draft
**Created**: 2024-01-01T12:00:00
**Updated**: 2024-01-01T12:00:00

## Description

Add user authentication to the app

## User Stories

### US-001: User Login

**Priority**: P1
**Status**: draft

As a user, I want to log in so that I can access my account.

**Acceptance Criteria**:
- Can login with valid credentials
- Shows error for invalid credentials

## Requirements

### REQ-001: Authentication API

**Type**: functional
**Status**: draft

System must authenticate users via secure API

**Rationale**: Security requirement

## Elicitation Questions

None
""")

        await store.initialize()

        assert len(store.specs) == 1
        assert "SPEC-001" in store.specs
        spec = store.specs["SPEC-001"]
        assert spec.title == "Authentication Feature"
        assert spec.description == "Add user authentication to the app"

    async def test_initialize_only_runs_once(self, temp_dir: Path):
        """Test that initialize only runs once."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)

        await store.initialize()
        initial_state = store._initialized

        await store.initialize()  # Should not reinitialize

        assert store._initialized == initial_state

    async def test_initialize_handles_empty_directory(self, temp_dir: Path):
        """Test initialize with empty specs directory."""
        storage_path = temp_dir / ".kortex" / "specs"
        storage_path.mkdir(parents=True)
        store = SpecStore(storage_path=storage_path)

        await store.initialize()

        assert store._initialized
        assert len(store.specs) == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestSpecStoreSave:
    """Test saving specifications."""

    async def test_save_creates_new_spec(self, temp_dir: Path):
        """Test saving a new specification."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        spec = Specification(
            id="SPEC-001",
            title="Authentication Feature",
            description="Add user authentication to the app",
            status="draft"
        )

        await store.save(spec)

        # Check in-memory cache
        assert "SPEC-001" in store.specs
        assert store.specs["SPEC-001"] == spec

        # Check file exists
        spec_file = storage_path / "SPEC-001" / "spec.md"
        assert spec_file.exists()

        # Check file content
        content = spec_file.read_text()
        assert "# Authentication Feature" in content
        assert "**ID**: SPEC-001" in content
        assert "Add user authentication to the app" in content

    async def test_save_updates_existing_spec(self, temp_dir: Path):
        """Test updating an existing specification."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create initial spec
        spec = Specification(
            id="SPEC-001",
            title="Authentication Feature",
            description="Initial description",
            status="draft"
        )
        await store.save(spec)

        # Update spec
        spec.description = "Updated description"
        spec.status = "in-progress"
        await store.save(spec)

        # Verify update
        loaded_spec = store.specs["SPEC-001"]
        assert loaded_spec.description == "Updated description"
        assert loaded_spec.status == "in-progress"

        # Verify file updated
        spec_file = storage_path / "SPEC-001" / "spec.md"
        content = spec_file.read_text()
        assert "Updated description" in content

    async def test_save_spec_with_user_stories(self, temp_dir: Path):
        """Test saving specification with user stories."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        story = UserStory(
            id="US-001",
            title="User Login",
            description="As a user, I want to log in",
            priority="P1",
            acceptance_criteria=["Can login with valid credentials"],
            status="draft"
        )

        spec = Specification(
            id="SPEC-001",
            title="Authentication Feature",
            description="Add user authentication",
            user_stories=[story],
            status="draft"
        )

        await store.save(spec)

        # Verify user story in file
        spec_file = storage_path / "SPEC-001" / "spec.md"
        content = spec_file.read_text()
        assert "## User Stories" in content
        assert "### US-001: User Login" in content
        assert "**Priority**: P1" in content
        assert "As a user, I want to log in" in content

    async def test_save_spec_with_requirements(self, temp_dir: Path):
        """Test saving specification with requirements."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        requirement = Requirement(
            id="REQ-001",
            type="functional",
            description="System must authenticate users",
            rationale="Security requirement",
            status="draft"
        )

        spec = Specification(
            id="SPEC-001",
            title="Authentication Feature",
            description="Add user authentication",
            requirements=[requirement],
            status="draft"
        )

        await store.save(spec)

        # Verify requirement in file
        spec_file = storage_path / "SPEC-001" / "spec.md"
        content = spec_file.read_text()
        assert "## Requirements" in content
        assert "### REQ-001:" in content
        assert "**Type**: functional" in content
        assert "System must authenticate users" in content

    async def test_save_spec_with_open_questions(self, temp_dir: Path):
        """Test saving specification with open questions."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        spec = Specification(
            id="SPEC-001",
            title="Architecture Decisions",
            description="Technical architecture",
            open_questions=[
                "Which DI framework should we use?",
                "Should we use Compose or XML layouts?"
            ],
            status="draft"
        )

        await store.save(spec)

        # Verify questions in file
        spec_file = storage_path / "SPEC-001" / "spec.md"
        content = spec_file.read_text()
        assert "## Open Questions" in content
        assert "Which DI framework should we use?" in content
        assert "Should we use Compose or XML layouts?" in content

    async def test_save_creates_spec_directory(self, temp_dir: Path):
        """Test that save creates spec directory if it doesn't exist."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        spec = Specification(
            id="SPEC-NEW",
            title="New Feature",
            description="A new feature",
            status="draft"
        )

        await store.save(spec)

        spec_dir = storage_path / "SPEC-NEW"
        assert spec_dir.exists()
        assert spec_dir.is_dir()

    async def test_save_with_concurrent_access(self, temp_dir: Path):
        """Test concurrent save operations are thread-safe."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        async def save_spec(spec_id: str):
            spec = Specification(
                id=spec_id,
                title=f"Feature {spec_id}",
                description=f"Description for {spec_id}",
                status="draft"
            )
            await store.save(spec)

        # Save multiple specs concurrently
        await asyncio.gather(
            save_spec("SPEC-001"),
            save_spec("SPEC-002"),
            save_spec("SPEC-003")
        )

        # All specs should be saved
        assert len(store.specs) == 3
        assert "SPEC-001" in store.specs
        assert "SPEC-002" in store.specs
        assert "SPEC-003" in store.specs

    async def test_save_handles_io_error(self, temp_dir: Path):
        """Test save handles IO errors gracefully."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        spec = Specification(
            id="SPEC-001",
            title="Test Feature",
            description="Test",
            status="draft"
        )

        # Mock file write to raise IOError
        with patch("pathlib.Path.write_text", side_effect=OSError("Disk full")):
            with pytest.raises(IOError, match="Failed to save specification"):
                await store.save(spec)


@pytest.mark.unit
@pytest.mark.asyncio
class TestSpecStoreLoad:
    """Test loading specifications."""

    async def test_load_reads_spec_from_markdown(self, temp_dir: Path):
        """Test loading specification from Markdown file."""
        storage_path = temp_dir / ".kortex" / "specs"
        spec_dir = storage_path / "SPEC-001"
        spec_dir.mkdir(parents=True)

        # Create markdown file
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("""# Authentication Feature

**ID**: SPEC-001
**Status**: draft
**Created**: 2024-01-01T12:00:00
**Updated**: 2024-01-01T12:00:00

## Description

Add user authentication to the app

## User Stories

None

## Requirements

None

## Elicitation Questions

None
""")

        store = SpecStore(storage_path=storage_path)
        spec = await store._load_spec_from_file(spec_file)

        assert spec is not None
        assert spec.id == "SPEC-001"
        assert spec.title == "Authentication Feature"
        assert spec.description == "Add user authentication to the app"
        assert spec.status == "draft"

    async def test_load_parses_user_stories(self, temp_dir: Path):
        """Test loading specification with user stories."""
        storage_path = temp_dir / ".kortex" / "specs"
        spec_dir = storage_path / "SPEC-001"
        spec_dir.mkdir(parents=True)

        spec_file = spec_dir / "spec.md"
        spec_file.write_text("""# Test Feature

**ID**: SPEC-001
**Status**: draft
**Created**: 2024-01-01T12:00:00
**Updated**: 2024-01-01T12:00:00

## Description

Test description

## User Stories

### US-001: User Login

**Priority**: P1
**Status**: draft

As a user, I want to log in

**Acceptance Criteria**:
- Can login with valid credentials
- Shows error for invalid credentials

## Requirements

None

## Elicitation Questions

None
""")

        store = SpecStore(storage_path=storage_path)
        spec = await store._load_spec_from_file(spec_file)

        assert len(spec.user_stories) == 1
        story = spec.user_stories[0]
        assert story.id == "US-001"
        assert story.title == "User Login"
        assert story.priority == "P1"
        assert len(story.acceptance_criteria) == 2

    async def test_load_parses_requirements(self, temp_dir: Path):
        """Test loading specification with requirements."""
        storage_path = temp_dir / ".kortex" / "specs"
        spec_dir = storage_path / "SPEC-001"
        spec_dir.mkdir(parents=True)

        spec_file = spec_dir / "spec.md"
        spec_file.write_text("""# Test Feature

**ID**: SPEC-001
**Status**: draft
**Created**: 2024-01-01T12:00:00
**Updated**: 2024-01-01T12:00:00

## Description

Test description

## User Stories

None

## Requirements

### REQ-001: Authentication API

**Type**: functional
**Status**: draft

System must authenticate users

**Rationale**: Security requirement

## Elicitation Questions

None
""")

        store = SpecStore(storage_path=storage_path)
        spec = await store._load_spec_from_file(spec_file)

        assert len(spec.requirements) == 1
        req = spec.requirements[0]
        assert req.id == "REQ-001"
        assert req.type == "functional"
        assert req.description == "System must authenticate users"
        assert req.rationale == "Security requirement"

    async def test_load_handles_malformed_markdown(self, temp_dir: Path):
        """Test loading handles malformed Markdown gracefully."""
        storage_path = temp_dir / ".kortex" / "specs"
        spec_dir = storage_path / "SPEC-001"
        spec_dir.mkdir(parents=True)

        spec_file = spec_dir / "spec.md"
        spec_file.write_text("Invalid markdown content")

        store = SpecStore(storage_path=storage_path)
        spec = await store._load_spec_from_file(spec_file)

        # Should return None or raise an error
        assert spec is None

    async def test_load_handles_missing_file(self, temp_dir: Path):
        """Test loading handles missing file."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)

        spec_file = storage_path / "SPEC-MISSING" / "spec.md"
        spec = await store._load_spec_from_file(spec_file)

        assert spec is None

    async def test_get_returns_spec_by_id(self, temp_dir: Path):
        """Test get method returns specification by ID."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Save a spec
        spec = Specification(
            id="SPEC-001",
            title="Test Feature",
            description="Test description",
            status="draft"
        )
        await store.save(spec)

        # Get it back
        retrieved = await store.get("SPEC-001")

        assert retrieved is not None
        assert retrieved.id == "SPEC-001"
        assert retrieved.title == "Test Feature"

    async def test_get_returns_none_for_unknown_id(self, temp_dir: Path):
        """Test get returns None for unknown spec ID."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        retrieved = await store.get("SPEC-UNKNOWN")

        assert retrieved is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestSpecStoreList:
    """Test listing specifications."""

    async def test_list_returns_all_specs(self, temp_dir: Path):
        """Test list returns all specifications."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create multiple specs
        for i in range(1, 4):
            spec = Specification(
                id=f"SPEC-00{i}",
                title=f"Feature {i}",
                description=f"Description {i}",
                status="draft"
            )
            await store.save(spec)

        # List all
        specs = await store.list_all()

        assert len(specs) == 3
        assert all(isinstance(s, Specification) for s in specs)
        spec_ids = [s.id for s in specs]
        assert "SPEC-001" in spec_ids
        assert "SPEC-002" in spec_ids
        assert "SPEC-003" in spec_ids

    async def test_list_returns_empty_for_no_specs(self, temp_dir: Path):
        """Test list returns empty list when no specs exist."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        specs = await store.list_all()

        assert specs == []

    async def test_list_by_status(self, temp_dir: Path):
        """Test listing specifications by status."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create specs with different statuses
        await store.save(Specification(
            id="SPEC-001",
            title="Draft Feature",
            description="Test",
            status="draft"
        ))
        await store.save(Specification(
            id="SPEC-002",
            title="In Progress Feature",
            description="Test",
            status="in-progress"
        ))
        await store.save(Specification(
            id="SPEC-003",
            title="Another Draft",
            description="Test",
            status="draft"
        ))

        # List by status
        draft_specs = await store.list_by_status("draft")

        assert len(draft_specs) == 2
        assert all(s.status == "draft" for s in draft_specs)

    async def test_get_all_specs_thread_safe(self, temp_dir: Path):
        """Test get_all is thread-safe."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Add some specs
        for i in range(1, 4):
            spec = Specification(
                id=f"SPEC-00{i}",
                title=f"Feature {i}",
                description=f"Description {i}",
                status="draft"
            )
            await store.save(spec)

        # Get all multiple times concurrently
        results = await asyncio.gather(
            store.list_all(),
            store.list_all(),
            store.list_all()
        )

        # All results should be the same
        assert all(len(r) == 3 for r in results)


@pytest.mark.unit
@pytest.mark.asyncio
class TestSpecStoreDelete:
    """Test deleting specifications."""

    async def test_delete_removes_spec(self, temp_dir: Path):
        """Test deleting a specification."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create spec
        spec = Specification(
            id="SPEC-001",
            title="Test Feature",
            description="Test",
            status="draft"
        )
        await store.save(spec)

        # Delete it
        result = await store.delete("SPEC-001")

        assert result is True
        assert "SPEC-001" not in store.specs

        # File should be removed
        spec_file = storage_path / "SPEC-001" / "spec.md"
        assert not spec_file.exists()

    async def test_delete_removes_spec_directory(self, temp_dir: Path):
        """Test delete removes the entire spec directory."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create spec
        spec = Specification(
            id="SPEC-001",
            title="Test Feature",
            description="Test",
            status="draft"
        )
        await store.save(spec)

        # Delete it
        await store.delete("SPEC-001")

        # Directory should be removed
        spec_dir = storage_path / "SPEC-001"
        assert not spec_dir.exists()

    async def test_delete_returns_false_for_unknown_id(self, temp_dir: Path):
        """Test delete returns False for unknown spec ID."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        result = await store.delete("SPEC-UNKNOWN")

        assert result is False

    async def test_delete_handles_io_error(self, temp_dir: Path):
        """Test delete handles IO errors gracefully."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create spec
        spec = Specification(
            id="SPEC-001",
            title="Test Feature",
            description="Test",
            status="draft"
        )
        await store.save(spec)

        # Mock file removal to raise error
        with patch("shutil.rmtree", side_effect=OSError("Permission denied")):
            result = await store.delete("SPEC-001")

            # Should return False but not crash
            assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestSpecStoreSearch:
    """Test searching and filtering specifications."""

    async def test_search_by_title(self, temp_dir: Path):
        """Test searching specifications by title."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create specs
        await store.save(Specification(
            id="SPEC-001",
            title="Authentication Feature",
            description="Test",
            status="draft"
        ))
        await store.save(Specification(
            id="SPEC-002",
            title="Payment Integration",
            description="Test",
            status="draft"
        ))

        # Search by title
        results = await store.search(title_contains="Authentication")

        assert len(results) == 1
        assert results[0].id == "SPEC-001"

    async def test_search_by_status(self, temp_dir: Path):
        """Test searching specifications by status."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create specs with different statuses
        await store.save(Specification(
            id="SPEC-001",
            title="Feature 1",
            description="Test",
            status="draft"
        ))
        await store.save(Specification(
            id="SPEC-002",
            title="Feature 2",
            description="Test",
            status="in-progress"
        ))

        # Search by status
        results = await store.search(status="in-progress")

        assert len(results) == 1
        assert results[0].status == "in-progress"

    async def test_search_by_description(self, temp_dir: Path):
        """Test searching specifications by description."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create specs
        await store.save(Specification(
            id="SPEC-001",
            title="Feature 1",
            description="Add user authentication with OAuth",
            status="draft"
        ))
        await store.save(Specification(
            id="SPEC-002",
            title="Feature 2",
            description="Implement payment processing",
            status="draft"
        ))

        # Search by description
        results = await store.search(description_contains="authentication")

        assert len(results) == 1
        assert results[0].id == "SPEC-001"

    async def test_search_with_multiple_criteria(self, temp_dir: Path):
        """Test searching with multiple criteria."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create specs
        await store.save(Specification(
            id="SPEC-001",
            title="Authentication Feature",
            description="Add OAuth authentication",
            status="draft"
        ))
        await store.save(Specification(
            id="SPEC-002",
            title="Authentication API",
            description="Backend API for auth",
            status="in-progress"
        ))

        # Search with multiple criteria
        results = await store.search(
            title_contains="Authentication",
            status="in-progress"
        )

        assert len(results) == 1
        assert results[0].id == "SPEC-002"

    async def test_search_returns_empty_for_no_matches(self, temp_dir: Path):
        """Test search returns empty list when no matches found."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create a spec
        await store.save(Specification(
            id="SPEC-001",
            title="Feature",
            description="Test",
            status="draft"
        ))

        # Search for non-existent content
        results = await store.search(title_contains="NonExistent")

        assert results == []

    async def test_search_is_case_insensitive(self, temp_dir: Path):
        """Test search is case-insensitive."""
        storage_path = temp_dir / ".kortex" / "specs"
        store = SpecStore(storage_path=storage_path)
        await store.initialize()

        # Create spec
        await store.save(Specification(
            id="SPEC-001",
            title="Authentication Feature",
            description="Test",
            status="draft"
        ))

        # Search with different case
        results = await store.search(title_contains="authentication")

        assert len(results) == 1
        assert results[0].id == "SPEC-001"
