"""Planning tools for specification creation and refinement.

This module provides MCP tools for Planning Mode, enabling conversation-driven
specification development through:
- Creating and refining specifications
- Generating SpecKit templates
- Detecting dependencies between specs
- Breaking down specs into actionable tasks

The tools support a simple, manual workflow where the LLM uses elicitation
tools through conversation rather than automatic invocation.

Phase 9: Tasks T104-T108
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models.specification import Requirement, Specification, UserStory
from ..storage.spec_store import SpecStore
from ..utils.file_utils import ensure_directory
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PlanningTools:
    """MCP tools for specification planning and management.

    Provides tools for creating, refining, and analyzing specifications
    in a conversation-driven Planning Mode workflow.

    Attributes:
        project_root: Path to project root directory
        spec_path: Path to specs storage directory
        spec_store: Specification storage instance
        _initialized: Whether tools have been initialized

    Example:
        >>> tools = PlanningTools(project_root=Path("/project"))
        >>> await tools.initialize()
        >>> result = await tools.create_spec(
        ...     spec_id="SPEC-001",
        ...     title="User Authentication",
        ...     description="Add OAuth2 authentication"
        ... )
    """

    def __init__(
        self,
        project_root: Path
    ):
        """Initialize planning tools.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.spec_path = project_root / ".kortex" / "specs"
        self.spec_store: SpecStore | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize planning tools.

        Creates spec directory if needed and loads spec store.

        Raises:
            IOError: If spec storage cannot be initialized

        Example:
            >>> await tools.initialize()
        """
        if self._initialized:
            return

        # Create spec directory
        ensure_directory(self.spec_path)

        # Initialize spec store
        self.spec_store = SpecStore(self.spec_path)
        await self.spec_store.initialize()

        self._initialized = True
        logger.info("Planning tools initialized")

    async def create_spec(
        self,
        spec_id: str,
        title: str,
        description: str,
        user_stories: list[dict[str, Any]] | None = None,
        requirements: list[dict[str, Any]] | None = None,
        open_questions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new specification.

        Creates a new specification with the provided information. The spec
        is immediately persisted to storage.

        Args:
            spec_id: Unique specification identifier (format: SPEC-XXX)
            title: Specification title
            description: High-level description of the feature
            user_stories: Optional list of user story dictionaries
            requirements: Optional list of requirement dictionaries
            open_questions: Optional list of questions that need answers during refinement

        Returns:
            Dictionary with creation result:
                - success: Whether creation succeeded
                - action: "created"
                - spec_id: The specification ID
                - title: The specification title
                - path: Path to the spec file
                - user_stories_count: Number of user stories
                - requirements_count: Number of requirements
                - open_questions_count: Number of open questions

        Raises:
            ValueError: If spec_id format is invalid, title is empty, or spec already exists
            IOError: If save operation fails

        Example:
            >>> result = await tools.create_spec(
            ...     spec_id="SPEC-001",
            ...     title="User Authentication",
            ...     description="Add OAuth2 authentication",
            ...     user_stories=[{
            ...         "id": "US-001",
            ...         "title": "User Login",
            ...         "description": "As a user, I want to log in",
            ...         "priority": "P1"
            ...     }]
            ... )
            >>> print(result["spec_id"])
            'SPEC-001'
        """
        await self.initialize()

        # Validate spec ID format
        if not re.match(r'^SPEC-\d+$', spec_id):
            raise ValueError(
                f"Invalid spec ID format: '{spec_id}'. Must match pattern SPEC-XXX (e.g., SPEC-001)"
            )

        # Validate title
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        # Check if spec already exists
        if self.spec_store:
            existing = await self.spec_store.get(spec_id)
            if existing:
                raise ValueError(f"Specification {spec_id} already exists")
        else:
            raise RuntimeError("Spec store not initialized")

        # Parse user stories
        stories = []
        if user_stories:
            for story_dict in user_stories:
                stories.append(UserStory(
                    id=story_dict["id"],
                    title=story_dict["title"],
                    description=story_dict["description"],
                    priority=story_dict.get("priority", "P2"),
                    acceptance_criteria=story_dict.get("acceptance_criteria", []),
                    status=story_dict.get("status", "draft"),
                ))

        # Parse requirements
        reqs = []
        if requirements:
            for req_dict in requirements:
                reqs.append(Requirement(
                    id=req_dict["id"],
                    type=req_dict.get("type", "functional"),
                    description=req_dict["description"],
                    rationale=req_dict.get("rationale"),
                    status=req_dict.get("status", "draft"),
                ))

        # Parse open questions
        questions = open_questions if open_questions else []

        # Create specification
        spec = Specification(
            id=spec_id,
            title=title,
            description=description,
            user_stories=stories,
            requirements=reqs,
            open_questions=questions,
            status="draft",
        )

        # Save to storage
        if self.spec_store:
            await self.spec_store.save(spec)

            # Get path for response
            spec_path = str(self.spec_store._get_spec_file(spec_id))
        else:
            raise RuntimeError("Spec store not initialized")

        logger.info(f"Created specification: {spec_id}")

        return {
            "success": True,
            "action": "created",
            "spec_id": spec_id,
            "title": title,
            "path": spec_path,
            "user_stories_count": len(stories),
            "requirements_count": len(reqs),
            "open_questions_count": len(questions),
        }

    async def refine_spec(
        self,
        spec_id: str,
        description: str | None = None,
        user_stories: list[dict[str, Any]] | None = None,
        requirements: list[dict[str, Any]] | None = None,
        open_questions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Refine an existing specification with new information.

        Adds or updates information in an existing specification. New items
        are appended to existing lists. Changes are immediately persisted.

        Args:
            spec_id: Specification identifier
            description: Updated description (replaces existing)
            user_stories: User stories to add
            requirements: Requirements to add
            open_questions: Questions to add to the open questions list

        Returns:
            Dictionary with refinement result:
                - success: Whether refinement succeeded
                - action: "refined"
                - spec_id: The specification ID
                - updated_fields: List of fields that were updated
                - user_stories_count: Total number of user stories
                - requirements_count: Total number of requirements
                - open_questions_count: Total number of open questions

        Raises:
            ValueError: If spec not found or no changes provided
            IOError: If save operation fails

        Example:
            >>> result = await tools.refine_spec(
            ...     spec_id="SPEC-001",
            ...     user_stories=[{
            ...         "id": "US-002",
            ...         "title": "User Logout",
            ...         "description": "As a user, I want to log out",
            ...         "priority": "P2"
            ...     }]
            ... )
        """
        await self.initialize()

        if not self.spec_store:
            raise RuntimeError("Spec store not initialized")

        # Get existing spec
        spec = await self.spec_store.get(spec_id)
        if not spec:
            raise ValueError(f"Specification {spec_id} not found")

        # Track what was updated
        updated_fields = []

        # Check if any changes provided
        has_changes = (
            description is not None or
            user_stories is not None or
            requirements is not None or
            open_questions is not None
        )

        if not has_changes:
            raise ValueError("No changes provided. Specify at least one field to update (no updates)")

        # Update description if provided
        if description is not None:
            spec.description = description
            updated_fields.append("description")

        # Add user stories
        if user_stories:
            for story_dict in user_stories:
                spec.user_stories.append(UserStory(
                    id=story_dict["id"],
                    title=story_dict["title"],
                    description=story_dict["description"],
                    priority=story_dict.get("priority", "P2"),
                    acceptance_criteria=story_dict.get("acceptance_criteria", []),
                    status=story_dict.get("status", "draft"),
                ))
            updated_fields.append("user_stories")

        # Add requirements
        if requirements:
            for req_dict in requirements:
                spec.requirements.append(Requirement(
                    id=req_dict["id"],
                    type=req_dict.get("type", "functional"),
                    description=req_dict["description"],
                    rationale=req_dict.get("rationale"),
                    status=req_dict.get("status", "draft"),
                ))
            updated_fields.append("requirements")

        # Add open questions
        if open_questions:
            spec.open_questions.extend(open_questions)
            updated_fields.append("open_questions")

        # Save changes
        if self.spec_store:
            await self.spec_store.save(spec)
        else:
            raise RuntimeError("Spec store not initialized")

        logger.info(f"Refined specification: {spec_id}")

        return {
            "success": True,
            "action": "refined",
            "spec_id": spec_id,
            "updated_fields": updated_fields,
            "user_stories_count": len(spec.user_stories),
            "requirements_count": len(spec.requirements),
            "open_questions_count": len(spec.open_questions),
        }

    async def generate_template(
        self,
        spec_id: str,
        title: str,
        sections: list[str] | None = None,
        platform_sections: dict[str, list[str]] | None = None,
        save_to_disk: bool = False,
    ) -> dict[str, Any]:
        """Generate a SpecKit-compliant specification template.

        Creates a template with standard sections for specification development.
        Optionally includes platform-specific sections for KMP projects.

        Args:
            spec_id: Specification identifier
            title: Specification title
            sections: Optional list of sections to include. If not provided,
                uses default sections: ["description", "user_stories", "requirements"]
            platform_sections: Optional dict of platform-specific sections,
                mapping platform name to list of section names
            save_to_disk: Whether to save template to disk immediately

        Returns:
            Dictionary with template generation result:
                - success: True
                - spec_id: The specification ID
                - template: The generated template as Markdown string
                - sections: List of sections included
                - path: Path to saved file (if save_to_disk=True)

        Example:
            >>> result = await tools.generate_template(
            ...     spec_id="SPEC-001",
            ...     title="Push Notifications",
            ...     platform_sections={
            ...         "android": ["Firebase setup", "Notification channels"],
            ...         "ios": ["APNs setup", "Notification permissions"]
            ...     }
            ... )
        """
        await self.initialize()

        # Default sections
        if sections is None:
            sections = ["description", "user_stories", "requirements"]

        # Build template
        lines = []

        # Title
        lines.append(f"# {title}")
        lines.append("")

        # Metadata
        lines.append(f"**ID**: {spec_id}")
        lines.append("**Status**: draft")
        lines.append(f"**Created**: {datetime.now().isoformat()}")
        lines.append(f"**Updated**: {datetime.now().isoformat()}")
        lines.append("")

        # Description section
        if "description" in sections:
            lines.append("## Description")
            lines.append("")
            lines.append("*Provide a high-level description of the feature or change.*")
            lines.append("")

        # User Stories section
        if "user_stories" in sections:
            lines.append("## User Stories")
            lines.append("")
            lines.append("### US-001: Story Title")
            lines.append("")
            lines.append("**Priority**: P1")
            lines.append("**Status**: draft")
            lines.append("")
            lines.append("*As a [user type], I want to [action] so that [benefit].*")
            lines.append("")
            lines.append("**Acceptance Criteria**:")
            lines.append("- *Criterion 1*")
            lines.append("- *Criterion 2*")
            lines.append("")

        # Requirements section
        if "requirements" in sections:
            lines.append("## Requirements")
            lines.append("")
            lines.append("### REQ-001: Requirement Description")
            lines.append("")
            lines.append("**Type**: functional")
            lines.append("**Status**: draft")
            lines.append("")
            lines.append("**Rationale**: *Why this requirement exists*")
            lines.append("")

        # Platform-specific sections
        if platform_sections:
            lines.append("## Platform-Specific Requirements")
            lines.append("")

            # Platform name mappings for proper capitalization
            platform_name_map = {
                "ios": "iOS",
                "macos": "macOS",
                "tvos": "tvOS",
                "watchos": "watchOS",
            }

            for platform, platform_section_list in platform_sections.items():
                # Use proper capitalization for known platforms
                platform_name = platform_name_map.get(platform.lower(), platform.capitalize())
                lines.append(f"### {platform_name}")
                lines.append("")
                for section in platform_section_list:
                    lines.append(f"**{section}**:")
                    lines.append("")
                    lines.append("*Details to be filled in*")
                    lines.append("")

        # Acceptance criteria section
        if "acceptance_criteria" in sections:
            lines.append("## Acceptance Criteria")
            lines.append("")
            lines.append("*Overall acceptance criteria for the entire specification*")
            lines.append("")
            lines.append("- *Criterion 1*")
            lines.append("- *Criterion 2*")
            lines.append("")

        # Elicitation questions section (always included)
        lines.append("## Elicitation Questions")
        lines.append("")
        lines.append("None")

        template = '\n'.join(lines)

        result = {
            "success": True,
            "spec_id": spec_id,
            "template": template,
            "sections": sections,
        }

        # Save to disk if requested
        if save_to_disk:
            spec_dir = self.spec_path / spec_id
            ensure_directory(spec_dir)
            spec_file = spec_dir / "spec.md"
            spec_file.write_text(template)
            result["path"] = str(spec_file)
            logger.info(f"Saved template to: {spec_file}")

        return result

    async def detect_dependencies(
        self,
        spec_id: str,
    ) -> dict[str, Any]:
        """Detect dependencies between specifications.

        Finds other specifications that this spec depends on or that depend
        on this spec. Detects both explicit references (SPEC-XXX IDs) and
        shared concepts (common keywords).

        Args:
            spec_id: Specification identifier

        Returns:
            Dictionary with dependency detection results:
                - success: True
                - spec_id: The specification ID
                - dependencies: List of spec IDs this spec depends on
                - shared_concepts: List of specs with shared concepts
                - circular_dependencies: List of circular dependency chains (if any)

        Raises:
            ValueError: If spec not found

        Example:
            >>> result = await tools.detect_dependencies(spec_id="SPEC-002")
            >>> print(result["dependencies"])
            ['SPEC-001']
        """
        await self.initialize()

        if not self.spec_store:
            raise RuntimeError("Spec store not initialized")

        # Get spec
        spec = await self.spec_store.get(spec_id)
        if not spec:
            raise ValueError(f"Specification {spec_id} not found or does not exist")

        dependencies = []
        shared_concepts = []
        circular_deps = []

        # Get all other specs
        all_specs = await self.spec_store.list_all()
        other_specs = [s for s in all_specs if s.id != spec_id]

        # Pattern to match SPEC-XXX references
        spec_pattern = re.compile(r'\bSPEC-\d+\b')

        # Find explicit references in current spec
        spec_text = f"{spec.title} {spec.description}"
        for story in spec.user_stories:
            spec_text += f" {story.description}"
        for req in spec.requirements:
            spec_text += f" {req.description}"

        # Extract referenced spec IDs
        referenced_ids = set(spec_pattern.findall(spec_text))

        # Check which referenced specs actually exist
        for other_spec in other_specs:
            if other_spec.id in referenced_ids:
                dependencies.append(other_spec.id)

                # Check for circular dependency
                other_text = f"{other_spec.title} {other_spec.description}"
                for story in other_spec.user_stories:
                    other_text += f" {story.description}"
                for req in other_spec.requirements:
                    other_text += f" {req.description}"

                if spec_id in spec_pattern.findall(other_text):
                    circular_deps.append(other_spec.id)

        # Find shared concepts (simple keyword matching)
        spec_keywords = self._extract_keywords(spec_text)

        for other_spec in other_specs:
            if other_spec.id in dependencies:
                continue  # Already found explicit dependency

            other_text = f"{other_spec.title} {other_spec.description}"
            for story in other_spec.user_stories:
                other_text += f" {story.description}"
            for req in other_spec.requirements:
                other_text += f" {req.description}"

            other_keywords = self._extract_keywords(other_text)

            # Check for shared keywords (at least 2 in common)
            common = spec_keywords & other_keywords
            if len(common) >= 2:
                shared_concepts.append(other_spec.id)

        return {
            "success": True,
            "spec_id": spec_id,
            "dependencies": dependencies,
            "shared_concepts": shared_concepts,
            "circular_dependencies": circular_deps,
        }

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract significant keywords from text.

        Args:
            text: Text to extract keywords from

        Returns:
            Set of lowercase keywords (3+ characters, excluding common words)
        """
        # Common words to exclude (reduced to be less aggressive)
        stop_words = {
            "the", "and", "for", "that", "this", "with", "from", "can",
            "will", "should", "must", "have", "has", "are", "was", "were",
            "been", "being"
        }

        # Split and clean
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter: length >= 3, not a stop word
        keywords = {
            word for word in words
            if len(word) >= 3 and word not in stop_words
        }

        return keywords

    async def generate_tasks(
        self,
        spec_id: str,
        save_to_disk: bool = False,
    ) -> dict[str, Any]:
        """Generate actionable tasks from a specification.

        Breaks down the specification into concrete tasks organized by
        user story. Tasks inherit priority from their user story.

        Args:
            spec_id: Specification identifier
            save_to_disk: Whether to save tasks.md file to disk

        Returns:
            Dictionary with task generation results:
                - success: True
                - spec_id: The specification ID
                - tasks: List of task dictionaries with:
                    - id: Task ID (T001, T002, etc.)
                    - title: Task title
                    - description: Task description
                    - priority: Priority (from user story)
                    - user_story_id: Related user story ID (if applicable)
                - path: Path to tasks.md file (if save_to_disk=True)

        Raises:
            ValueError: If spec not found

        Example:
            >>> result = await tools.generate_tasks(
            ...     spec_id="SPEC-001",
            ...     save_to_disk=True
            ... )
            >>> print(f"Generated {len(result['tasks'])} tasks")
        """
        await self.initialize()

        if not self.spec_store:
            raise RuntimeError("Spec store not initialized")

        # Get spec
        spec = await self.spec_store.get(spec_id)
        if not spec:
            raise ValueError(f"Specification {spec_id} not found")

        tasks = []
        task_counter = 1

        # Generate tasks from user stories
        for story in spec.user_stories:
            # One main task for the user story
            tasks.append({
                "id": f"T{task_counter:03d}",
                "title": f"Implement {story.title}",
                "description": story.description,
                "priority": story.priority,
                "user_story_id": story.id,
            })
            task_counter += 1

            # Tasks for each acceptance criterion
            for criterion in story.acceptance_criteria:
                tasks.append({
                    "id": f"T{task_counter:03d}",
                    "title": criterion,
                    "description": f"Acceptance criterion for {story.id}",
                    "priority": story.priority,
                    "user_story_id": story.id,
                })
                task_counter += 1

        # Generate tasks from requirements (if no user story)
        for req in spec.requirements:
            # Check if requirement is linked to any user story
            if not any(req.id in story.metadata.get("requirements", []) for story in spec.user_stories):
                tasks.append({
                    "id": f"T{task_counter:03d}",
                    "title": f"Implement {req.id}",
                    "description": req.description,
                    "priority": "P2",  # Default priority for standalone requirements
                    "requirement_id": req.id,
                })
                task_counter += 1

        result = {
            "success": True,
            "spec_id": spec_id,
            "tasks": tasks,
        }

        # Save to disk if requested
        if save_to_disk:
            # Generate tasks.md content
            lines = []
            lines.append(f"# Tasks for {spec.title}")
            lines.append("")
            lines.append(f"Generated from specification: {spec_id}")
            lines.append(f"Generated at: {datetime.now().isoformat()}")
            lines.append("")

            # Group by priority
            for priority in ["P1", "P2", "P3"]:
                priority_tasks = [t for t in tasks if t.get("priority") == priority]
                if priority_tasks:
                    lines.append(f"## Priority {priority}")
                    lines.append("")

                    for task in priority_tasks:
                        # Format: - [ ] T001 [US-001] Task description
                        story_ref = f"[{task['user_story_id']}]" if "user_story_id" in task else ""
                        req_ref = f"[{task['requirement_id']}]" if "requirement_id" in task else ""
                        ref = story_ref or req_ref
                        lines.append(f"- [ ] {task['id']} {ref} {task['title']}")

                    lines.append("")

            tasks_content = '\n'.join(lines)

            # Save to file
            spec_dir = self.spec_path / spec_id
            ensure_directory(spec_dir)
            tasks_file = spec_dir / "tasks.md"
            tasks_file.write_text(tasks_content)
            result["path"] = str(tasks_file)
            logger.info(f"Saved tasks to: {tasks_file}")

        return result
