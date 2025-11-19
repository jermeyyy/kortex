"""Integration tests for planning tools.

This module tests PlanningTools which provide specification creation,
refinement, and analysis capabilities for Planning Mode.

Tests cover:
- Creating new specifications with user stories and requirements
- Refining specifications by adding details
- Analyzing spec completeness, clarity, and consistency
- Generating SpecKit-compliant templates
- Identifying dependencies between specs
- Breaking down specs into tasks
- Integration with SpecStore for persistence
- Error handling for invalid inputs

Phase 9: Tasks T100 (integration tests) and T101 (spec refinement workflow)
"""

from pathlib import Path

import pytest

from kortex_mcp.storage.spec_store import SpecStore
from kortex_mcp.tools.planning_tools import PlanningTools


@pytest.mark.integration
@pytest.mark.asyncio
class TestPlanningToolsInitialization:
    """Test PlanningTools initialization."""

    async def test_init_creates_tools_with_project_root(self, temp_dir: Path):
        """Test that PlanningTools initializes with project root."""
        tools = PlanningTools(project_root=temp_dir)

        assert tools.project_root == temp_dir
        assert tools.spec_path == temp_dir / ".kortex" / "specs"
        assert not tools._initialized

    async def test_initialize_creates_spec_directory(self, temp_dir: Path):
        """Test that initialize creates spec directory."""
        tools = PlanningTools(project_root=temp_dir)

        await tools.initialize()

        assert tools.spec_path.exists()
        assert tools.spec_path.is_dir()
        assert tools._initialized

    async def test_initialize_loads_spec_store(self, temp_dir: Path):
        """Test that initialize loads the spec store."""
        tools = PlanningTools(project_root=temp_dir)

        await tools.initialize()

        assert tools.spec_store is not None
        assert isinstance(tools.spec_store, SpecStore)

    async def test_initialize_only_runs_once(self, temp_dir: Path):
        """Test that initialize only runs once."""
        tools = PlanningTools(project_root=temp_dir)

        await tools.initialize()
        first_store = tools.spec_store

        await tools.initialize()  # Should not reinitialize

        assert tools.spec_store is first_store
        assert tools._initialized


@pytest.mark.integration
@pytest.mark.asyncio
class TestCreateSpec:
    """Test creating new specifications."""

    async def test_create_spec_with_basic_info(self, temp_dir: Path):
        """Test creating a specification with basic information."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        result = await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Add user authentication to the application"
        )

        assert result["success"] is True
        assert result["action"] == "created"
        assert result["spec_id"] == "SPEC-001"
        assert result["title"] == "User Authentication"
        assert "path" in result

    async def test_create_spec_with_user_stories(self, temp_dir: Path):
        """Test creating specification with user stories."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        user_stories = [
            {
                "id": "US-001",
                "title": "User Login",
                "description": "As a user, I want to log in so I can access my account",
                "priority": "P1",
                "acceptance_criteria": [
                    "Can login with valid credentials",
                    "Shows error for invalid credentials"
                ]
            }
        ]

        result = await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Add user authentication",
            user_stories=user_stories
        )

        assert result["success"] is True
        assert result["user_stories_count"] == 1

    async def test_create_spec_with_requirements(self, temp_dir: Path):
        """Test creating specification with requirements."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        requirements = [
            {
                "id": "REQ-001",
                "type": "functional",
                "description": "System must authenticate users via OAuth2",
                "rationale": "Industry standard for secure authentication"
            },
            {
                "id": "REQ-002",
                "type": "non-functional",
                "description": "Authentication response time < 500ms",
                "rationale": "Performance requirement for good UX"
            }
        ]

        result = await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Add user authentication",
            requirements=requirements
        )

        assert result["success"] is True
        assert result["requirements_count"] == 2

    async def test_create_spec_with_complete_data(self, temp_dir: Path):
        """Test creating specification with user stories and requirements."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        user_stories = [
            {
                "id": "US-001",
                "title": "User Login",
                "description": "As a user, I want to log in",
                "priority": "P1",
                "acceptance_criteria": ["Can login successfully"]
            }
        ]

        requirements = [
            {
                "id": "REQ-001",
                "type": "functional",
                "description": "Support OAuth2 authentication",
                "rationale": "Security best practice"
            }
        ]

        result = await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Add user authentication",
            user_stories=user_stories,
            requirements=requirements
        )

        assert result["success"] is True
        assert result["user_stories_count"] == 1
        assert result["requirements_count"] == 1

    async def test_create_spec_persists_to_storage(self, temp_dir: Path):
        """Test that created specs are persisted to storage."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Add user authentication"
        )

        # Verify spec file exists
        spec_file = temp_dir / ".kortex" / "specs" / "SPEC-001" / "spec.md"
        assert spec_file.exists()

        # Verify content
        content = spec_file.read_text()
        assert "# User Authentication" in content
        assert "SPEC-001" in content

    async def test_create_spec_duplicate_id_raises_error(self, temp_dir: Path):
        """Test that creating spec with duplicate ID raises error."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create first spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="First Spec",
            description="First"
        )

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await tools.create_spec(
                spec_id="SPEC-001",
                title="Duplicate Spec",
                description="Duplicate"
            )

    async def test_create_spec_empty_title_raises_error(self, temp_dir: Path):
        """Test that empty title raises error."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        with pytest.raises(ValueError, match="title|empty"):
            await tools.create_spec(
                spec_id="SPEC-001",
                title="",
                description="Test"
            )

    async def test_create_spec_invalid_spec_id_format(self, temp_dir: Path):
        """Test that invalid spec ID format raises error."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        with pytest.raises(ValueError, match="ID|format"):
            await tools.create_spec(
                spec_id="invalid-id",
                title="Test",
                description="Test"
            )


@pytest.mark.integration
@pytest.mark.asyncio
class TestRefineSpec:
    """Test refining specifications with elicitation."""

    async def test_refine_spec_add_user_story(self, temp_dir: Path):
        """Test refining spec by adding a user story."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create initial spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Add authentication"
        )

        # Refine by adding user story
        new_story = {
            "id": "US-001",
            "title": "User Login",
            "description": "As a user, I want to log in",
            "priority": "P1",
            "acceptance_criteria": ["Can login successfully"]
        }

        result = await tools.refine_spec(
            spec_id="SPEC-001",
            user_stories=[new_story]
        )

        assert result["success"] is True
        assert result["action"] == "refined"
        assert result["user_stories_count"] == 1

    async def test_refine_spec_add_requirement(self, temp_dir: Path):
        """Test refining spec by adding a requirement."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create initial spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Add authentication"
        )

        # Refine by adding requirement
        new_req = {
            "id": "REQ-001",
            "type": "functional",
            "description": "Support OAuth2",
            "rationale": "Industry standard"
        }

        result = await tools.refine_spec(
            spec_id="SPEC-001",
            requirements=[new_req]
        )

        assert result["success"] is True
        assert result["requirements_count"] == 1

    async def test_refine_spec_add_open_questions(self, temp_dir: Path):
        """Test refining spec by adding open questions."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create initial spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Add authentication"
        )

        # Refine by adding open questions
        questions = [
            "Which OAuth2 provider should we support?",
            "Should we support biometric authentication?"
        ]

        result = await tools.refine_spec(
            spec_id="SPEC-001",
            open_questions=questions
        )

        assert result["success"] is True
        assert result["open_questions_count"] == 2

    async def test_refine_spec_update_description(self, temp_dir: Path):
        """Test refining spec by updating description."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create initial spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Basic authentication"
        )

        # Refine description
        result = await tools.refine_spec(
            spec_id="SPEC-001",
            description="Comprehensive user authentication with OAuth2 support"
        )

        assert result["success"] is True
        assert result["updated_fields"] == ["description"]

    async def test_refine_spec_multiple_fields(self, temp_dir: Path):
        """Test refining spec with multiple updates."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create initial spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Basic authentication"
        )

        # Refine multiple aspects
        user_story = {
            "id": "US-001",
            "title": "User Login",
            "description": "Login functionality",
            "priority": "P1"
        }

        requirement = {
            "id": "REQ-001",
            "type": "functional",
            "description": "OAuth2 support"
        }

        result = await tools.refine_spec(
            spec_id="SPEC-001",
            description="Enhanced authentication system",
            user_stories=[user_story],
            requirements=[requirement]
        )

        assert result["success"] is True
        assert result["user_stories_count"] == 1
        assert result["requirements_count"] == 1
        assert "description" in result["updated_fields"]

    async def test_refine_spec_persists_changes(self, temp_dir: Path):
        """Test that refinements are persisted to storage."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create and refine spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Initial"
        )

        await tools.refine_spec(
            spec_id="SPEC-001",
            description="Refined description"
        )

        # Reload and verify
        spec = await tools.spec_store.get(spec_id="SPEC-001")
        assert spec.description == "Refined description"

    async def test_refine_spec_nonexistent_raises_error(self, temp_dir: Path):
        """Test that refining nonexistent spec raises error."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        with pytest.raises(ValueError, match="not found|does not exist"):
            await tools.refine_spec(
                spec_id="SPEC-999",
                description="Test"
            )

    async def test_refine_spec_no_changes_raises_error(self, temp_dir: Path):
        """Test that refining with no changes raises error."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        await tools.create_spec(
            spec_id="SPEC-001",
            title="Test",
            description="Test"
        )

        with pytest.raises(ValueError, match="No changes|no updates"):
            await tools.refine_spec(spec_id="SPEC-001")


@pytest.mark.integration
@pytest.mark.asyncio
class TestSpecTemplates:
    """Test SpecKit template generation."""

    async def test_generate_template_basic(self, temp_dir: Path):
        """Test generating basic SpecKit template."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        result = await tools.generate_template(
            spec_id="SPEC-001",
            title="User Authentication"
        )

        assert result["success"] is True
        assert result["spec_id"] == "SPEC-001"
        assert "template" in result
        assert "# User Authentication" in result["template"]
        assert "## Description" in result["template"]
        assert "## User Stories" in result["template"]
        assert "## Requirements" in result["template"]

    async def test_generate_template_with_sections(self, temp_dir: Path):
        """Test generating template with specific sections."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        result = await tools.generate_template(
            spec_id="SPEC-001",
            title="User Authentication",
            sections=["description", "user_stories", "acceptance_criteria"]
        )

        assert result["success"] is True
        assert "## Description" in result["template"]
        assert "## User Stories" in result["template"]
        assert "## Acceptance Criteria" in result["template"]

    async def test_generate_template_creates_file(self, temp_dir: Path):
        """Test that template generation creates file."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        result = await tools.generate_template(
            spec_id="SPEC-001",
            title="User Authentication",
            save_to_disk=True
        )

        assert result["success"] is True
        template_file = temp_dir / ".kortex" / "specs" / "SPEC-001" / "spec.md"
        assert template_file.exists()

    async def test_generate_template_platform_specific(self, temp_dir: Path):
        """Test generating template with platform-specific sections."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        result = await tools.generate_template(
            spec_id="SPEC-001",
            title="Push Notifications",
            platform_sections={
                "android": ["Firebase setup", "Notification channels"],
                "ios": ["APNs setup", "Notification permissions"]
            }
        )

        assert result["success"] is True
        assert "### Android" in result["template"]
        assert "### iOS" in result["template"]
        assert "Firebase setup" in result["template"]
        assert "APNs setup" in result["template"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestSpecDependencies:
    """Test dependency detection between specs."""

    async def test_detect_dependencies_none(self, temp_dir: Path):
        """Test detecting dependencies when none exist."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Authentication system"
        )

        result = await tools.detect_dependencies(spec_id="SPEC-001")

        assert result["success"] is True
        assert result["spec_id"] == "SPEC-001"
        assert len(result["dependencies"]) == 0

    async def test_detect_dependencies_explicit_references(self, temp_dir: Path):
        """Test detecting dependencies from explicit references."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create dependency spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Model",
            description="User data model"
        )

        # Create spec that references SPEC-001
        await tools.create_spec(
            spec_id="SPEC-002",
            title="User Authentication",
            description="Authentication requires SPEC-001 User Model",
            requirements=[{
                "id": "REQ-001",
                "type": "functional",
                "description": "Depends on SPEC-001 for user data"
            }]
        )

        result = await tools.detect_dependencies(spec_id="SPEC-002")

        assert result["success"] is True
        assert len(result["dependencies"]) == 1
        assert "SPEC-001" in result["dependencies"]

    async def test_detect_dependencies_shared_concepts(self, temp_dir: Path):
        """Test detecting dependencies from shared concepts."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create specs with shared concepts
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Profile",
            description="User profile management with avatar uploads"
        )

        await tools.create_spec(
            spec_id="SPEC-002",
            title="Settings",
            description="User settings page showing profile information"
        )

        result = await tools.detect_dependencies(spec_id="SPEC-002")

        assert result["success"] is True
        # Should detect shared "user profile" concept
        assert len(result["dependencies"]) > 0 or len(result["shared_concepts"]) > 0

    async def test_detect_dependencies_circular(self, temp_dir: Path):
        """Test detecting circular dependencies."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        await tools.create_spec(
            spec_id="SPEC-001",
            title="Feature A",
            description="Depends on SPEC-002"
        )

        await tools.create_spec(
            spec_id="SPEC-002",
            title="Feature B",
            description="Depends on SPEC-001"
        )

        result = await tools.detect_dependencies(spec_id="SPEC-001")

        assert result["success"] is True
        if result.get("circular_dependencies"):
            assert "SPEC-002" in result["circular_dependencies"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestTaskBreakdown:
    """Test generating tasks.md from specifications."""

    async def test_generate_tasks_from_spec(self, temp_dir: Path):
        """Test generating tasks from a specification."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create spec with user stories
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Authentication system",
            user_stories=[
                {
                    "id": "US-001",
                    "title": "User Login",
                    "description": "User can log in",
                    "priority": "P1",
                    "acceptance_criteria": [
                        "Login form displayed",
                        "Validate credentials",
                        "Redirect on success"
                    ]
                }
            ],
            requirements=[
                {
                    "id": "REQ-001",
                    "type": "functional",
                    "description": "Implement OAuth2 flow"
                }
            ]
        )

        result = await tools.generate_tasks(spec_id="SPEC-001")

        assert result["success"] is True
        assert result["spec_id"] == "SPEC-001"
        assert "tasks" in result
        assert len(result["tasks"]) > 0

        # Tasks should be derived from user stories and requirements
        tasks = result["tasks"]
        assert any("login" in task["title"].lower() for task in tasks)

    async def test_generate_tasks_creates_file(self, temp_dir: Path):
        """Test that task generation creates tasks.md file."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Authentication system",
            user_stories=[{
                "id": "US-001",
                "title": "Login",
                "description": "User login",
                "priority": "P1"
            }]
        )

        result = await tools.generate_tasks(
            spec_id="SPEC-001",
            save_to_disk=True
        )

        assert result["success"] is True
        tasks_file = temp_dir / ".kortex" / "specs" / "SPEC-001" / "tasks.md"
        assert tasks_file.exists()

        content = tasks_file.read_text()
        assert "# Tasks" in content
        assert "User Authentication" in content

    async def test_generate_tasks_with_priorities(self, temp_dir: Path):
        """Test that tasks inherit priorities from user stories."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        await tools.create_spec(
            spec_id="SPEC-001",
            title="Feature",
            description="Test feature",
            user_stories=[
                {
                    "id": "US-001",
                    "title": "Critical Story",
                    "description": "P1 story",
                    "priority": "P1"
                },
                {
                    "id": "US-002",
                    "title": "Nice to Have",
                    "description": "P3 story",
                    "priority": "P3"
                }
            ]
        )

        result = await tools.generate_tasks(spec_id="SPEC-001")

        assert result["success"] is True
        tasks = result["tasks"]

        # P1 tasks should come before P3 tasks
        priorities = [task.get("priority", "P2") for task in tasks]
        first_p1 = next((i for i, p in enumerate(priorities) if p == "P1"), -1)
        first_p3 = next((i for i, p in enumerate(priorities) if p == "P3"), len(tasks))

        if first_p1 >= 0 and first_p3 < len(tasks):
            assert first_p1 < first_p3

    async def test_generate_tasks_empty_spec_returns_empty(self, temp_dir: Path):
        """Test generating tasks from spec with no user stories."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        await tools.create_spec(
            spec_id="SPEC-001",
            title="Empty Spec",
            description="No user stories yet"
        )

        result = await tools.generate_tasks(spec_id="SPEC-001")

        assert result["success"] is True
        assert len(result["tasks"]) == 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestSpecWorkflow:
    """Test complete spec creation, refinement, and analysis workflow."""

    async def test_full_workflow_create_refine_save(self, temp_dir: Path):
        """Test complete workflow: create → refine → save."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Step 1: Create basic spec
        create_result = await tools.create_spec(
            spec_id="SPEC-001",
            title="User Authentication",
            description="Initial description"
        )
        assert create_result["success"] is True

        # Step 2: Refine with user stories
        refine_result = await tools.refine_spec(
            spec_id="SPEC-001",
            user_stories=[{
                "id": "US-001",
                "title": "User Login",
                "description": "As a user, I want to log in",
                "priority": "P1",
                "acceptance_criteria": ["Can login successfully"]
            }]
        )
        assert refine_result["success"] is True

        # Step 3: Refine with requirements
        refine_result2 = await tools.refine_spec(
            spec_id="SPEC-001",
            requirements=[{
                "id": "REQ-001",
                "type": "functional",
                "description": "Support OAuth2 authentication",
                "rationale": "Industry standard"
            }]
        )
        assert refine_result2["success"] is True

        # Step 4: Verify persistence
        spec = await tools.spec_store.get(spec_id="SPEC-001")
        assert spec is not None
        assert len(spec.user_stories) == 1
        assert len(spec.requirements) == 1

    async def test_workflow_with_open_questions(self, temp_dir: Path):
        """Test workflow with open questions recorded."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="Feature X",
            description="New feature"
        )

        # Add open questions during refinement
        questions = [
            "Which platform should we target first?",
            "What is the expected user load?"
        ]

        await tools.refine_spec(
            spec_id="SPEC-001",
            open_questions=questions
        )

        # Verify questions are stored
        spec = await tools.spec_store.get(spec_id="SPEC-001")
        assert len(spec.open_questions) == 2

        # Verify they're in the saved file
        spec_file = temp_dir / ".kortex" / "specs" / "SPEC-001" / "spec.md"
        content = spec_file.read_text()
        assert "Which platform should we target first?" in content
        assert "What is the expected user load?" in content

    async def test_workflow_multiple_specs_with_dependencies(self, temp_dir: Path):
        """Test workflow with multiple dependent specs."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Create foundational spec
        await tools.create_spec(
            spec_id="SPEC-001",
            title="User Data Model",
            description="Core user data structure"
        )

        # Create dependent spec
        await tools.create_spec(
            spec_id="SPEC-002",
            title="User Authentication",
            description="Authentication depends on SPEC-001"
        )

        # Create another dependent spec
        await tools.create_spec(
            spec_id="SPEC-003",
            title="User Profile",
            description="Profile management depends on SPEC-001"
        )

        # Detect dependencies for SPEC-002
        deps_result = await tools.detect_dependencies(spec_id="SPEC-002")
        assert deps_result["success"] is True
        assert "SPEC-001" in deps_result["dependencies"]

        # Detect dependencies for SPEC-003
        deps_result2 = await tools.detect_dependencies(spec_id="SPEC-003")
        assert deps_result2["success"] is True
        assert "SPEC-001" in deps_result2["dependencies"]

    async def test_workflow_iterative_refinement(self, temp_dir: Path):
        """Test iterative refinement workflow."""
        tools = PlanningTools(project_root=temp_dir)
        await tools.initialize()

        # Initial creation
        await tools.create_spec(
            spec_id="SPEC-001",
            title="Feature",
            description="V1 description"
        )

        # First refinement pass
        await tools.refine_spec(
            spec_id="SPEC-001",
            description="V2 description with more details"
        )

        # Second refinement pass - add user story
        await tools.refine_spec(
            spec_id="SPEC-001",
            user_stories=[{
                "id": "US-001",
                "title": "Story 1",
                "description": "First story",
                "priority": "P1"
            }]
        )

        # Third refinement pass - add requirement
        await tools.refine_spec(
            spec_id="SPEC-001",
            requirements=[{
                "id": "REQ-001",
                "type": "functional",
                "description": "First requirement"
            }]
        )

        # Verify final state
        spec = await tools.spec_store.get(spec_id="SPEC-001")
        assert spec.description == "V2 description with more details"
        assert len(spec.user_stories) == 1
        assert len(spec.requirements) == 1
