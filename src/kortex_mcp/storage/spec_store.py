"""Specification storage with Markdown-based persistence.

This module provides persistent storage for specifications using
Markdown files following the SpecKit template structure.
"""

import asyncio
import shutil
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from ..utils.logging import get_logger
from ..utils.file_utils import ensure_directory
from ..models.specification import (
    Specification, UserStory, Requirement
)


logger = get_logger(__name__)


class SpecStore:
    """Persistent storage for specifications.

    Stores specifications in Markdown format following the SpecKit template,
    with support for CRUD operations, search, and filtering.

    Attributes:
        storage_path: Path to the specs directory
        specs: In-memory cache of loaded specifications
        _lock: Async lock for thread-safe operations
        _initialized: Whether the store has been initialized

    Example:
        >>> store = SpecStore(Path(".kortex/specs"))
        >>> await store.initialize()
        >>> spec = Specification(...)
        >>> await store.save(spec)
        >>> results = await store.search(title_contains="Authentication")
    """

    def __init__(self, storage_path: Path):
        """Initialize spec store.

        Args:
            storage_path: Directory path for storing specifications
        """
        self.storage_path = storage_path
        self.specs: Dict[str, Specification] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize storage and load existing specifications.

        Creates storage directory if it doesn't exist and loads
        all specifications from disk.

        Raises:
            IOError: If storage directory cannot be created

        Example:
            >>> await store.initialize()
        """
        if self._initialized:
            return

        logger.info(f"Initializing spec store at {self.storage_path}")
        
        # Create storage directory
        ensure_directory(self.storage_path)
        
        # Load existing specs
        await self._load_all()
        
        self._initialized = True
        logger.info(f"Spec store initialized with {len(self.specs)} specifications")

    async def _load_all(self) -> None:
        """Load all specifications from disk."""
        if not self.storage_path.exists():
            return

        # Get all spec directories
        for spec_dir in self.storage_path.iterdir():
            if not spec_dir.is_dir():
                continue
            
            spec_file = spec_dir / "spec.md"
            if not spec_file.exists():
                continue
            
            try:
                spec = await self._load_spec_from_file(spec_file)
                if spec:
                    self.specs[spec.id] = spec
            except Exception as e:
                logger.error(f"Failed to load spec from {spec_file}: {e}")

    async def _load_spec_from_file(self, file_path: Path) -> Optional[Specification]:
        """Load specification from Markdown file.

        Args:
            file_path: Path to the spec.md file

        Returns:
            Specification instance or None if parsing fails
        """
        if not file_path.exists():
            return None

        try:
            content = file_path.read_text()
            return self._parse_markdown(content)
        except Exception as e:
            logger.error(f"Failed to parse spec file {file_path}: {e}")
            return None

    def _parse_markdown(self, content: str) -> Optional[Specification]:
        """Parse Markdown content to Specification object.

        Args:
            content: Markdown content

        Returns:
            Specification instance or None if parsing fails
        """
        try:
            lines = content.split('\n')
            
            # Parse title (first line after any leading whitespace)
            title = None
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            
            if not title:
                return None

            # Parse metadata
            spec_id = None
            status = "draft"
            created_at = datetime.now()
            updated_at = datetime.now()

            for i, line in enumerate(lines):
                if line.startswith('**ID**:'):
                    spec_id = line.split(':', 1)[1].strip()
                elif line.startswith('**Status**:'):
                    status = line.split(':', 1)[1].strip()
                elif line.startswith('**Created**:'):
                    try:
                        created_at = datetime.fromisoformat(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith('**Updated**:'):
                    try:
                        updated_at = datetime.fromisoformat(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass

            if not spec_id:
                return None

            # Parse description
            description = self._extract_section_content(lines, "## Description")

            # Parse user stories
            user_stories = self._parse_user_stories(lines)

            # Parse requirements
            requirements = self._parse_requirements(lines)

            # Parse open questions
            open_questions = self._parse_open_questions(lines)

            return Specification(
                id=spec_id,
                title=title,
                description=description,
                user_stories=user_stories,
                requirements=requirements,
                open_questions=open_questions,
                status=status,
                created_at=created_at,
                updated_at=updated_at
            )

        except Exception as e:
            logger.error(f"Failed to parse markdown: {e}")
            return None

    def _extract_section_content(self, lines: List[str], section_header: str) -> str:
        """Extract content of a section between headers.

        Args:
            lines: All lines in the document
            section_header: The section header to find (e.g., "## Description")

        Returns:
            Section content as a string
        """
        content_lines = []
        in_section = False
        
        for line in lines:
            if line.startswith(section_header):
                in_section = True
                continue
            elif in_section and line.startswith('##'):
                # Hit next section
                break
            elif in_section and line.strip():
                content_lines.append(line)
        
        return '\n'.join(content_lines).strip()

    def _parse_user_stories(self, lines: List[str]) -> List[UserStory]:
        """Parse user stories from Markdown lines.

        Args:
            lines: All lines in the document

        Returns:
            List of UserStory objects
        """
        stories = []
        in_stories_section = False
        current_story = None
        current_story_id = None
        current_story_title = None
        story_description_lines = []
        acceptance_criteria = []
        priority = "P2"
        story_status = "draft"
        in_acceptance_criteria = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if line.startswith('## User Stories'):
                in_stories_section = True
                i += 1
                continue
            elif in_stories_section and line.startswith('## ') and not line.startswith('### '):
                # End of user stories section (new level-2 section)
                if current_story_id and current_story_title:
                    stories.append(UserStory(
                        id=current_story_id,
                        title=current_story_title,
                        description='\n'.join(story_description_lines).strip(),
                        priority=priority,
                        acceptance_criteria=acceptance_criteria,
                        status=story_status
                    ))
                    current_story_id = None  # Clear to prevent double-saving
                break
            elif in_stories_section and line.startswith('### '):
                # Save previous story if exists
                if current_story_id and current_story_title:
                    stories.append(UserStory(
                        id=current_story_id,
                        title=current_story_title,
                        description='\n'.join(story_description_lines).strip(),
                        priority=priority,
                        acceptance_criteria=acceptance_criteria,
                        status=story_status
                    ))
                
                # Parse new story header
                story_header = line[4:].strip()
                if ':' in story_header:
                    current_story_id, current_story_title = story_header.split(':', 1)
                    current_story_id = current_story_id.strip()
                    current_story_title = current_story_title.strip()
                    story_description_lines = []
                    acceptance_criteria = []
                    priority = "P2"
                    story_status = "draft"
                    in_acceptance_criteria = False
            elif in_stories_section and current_story_id:
                if line.startswith('**Priority**:'):
                    priority = line.split(':', 1)[1].strip()
                    in_acceptance_criteria = False
                elif line.startswith('**Status**:'):
                    story_status = line.split(':', 1)[1].strip()
                    in_acceptance_criteria = False
                elif line.startswith('**Acceptance Criteria**:'):
                    in_acceptance_criteria = True
                elif in_acceptance_criteria and line.startswith('- '):
                    acceptance_criteria.append(line[2:].strip())
                elif line.strip() and not line.startswith('**') and not in_acceptance_criteria:
                    story_description_lines.append(line)
            elif in_stories_section and line.strip().lower() == "none":
                # No user stories
                break
            
            i += 1
        
        # Save last story if exists
        if in_stories_section and current_story_id and current_story_title:
            stories.append(UserStory(
                id=current_story_id,
                title=current_story_title,
                description='\n'.join(story_description_lines).strip(),
                priority=priority,
                acceptance_criteria=acceptance_criteria,
                status=story_status
            ))
        
        return stories

    def _parse_requirements(self, lines: List[str]) -> List[Requirement]:
        """Parse requirements from Markdown lines.

        Args:
            lines: All lines in the document

        Returns:
            List of Requirement objects
        """
        requirements = []
        in_requirements_section = False
        current_req_id = None
        current_req_title = None
        req_description_lines = []
        req_type = "functional"
        rationale = None
        req_status = "draft"
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if line.startswith('## Requirements'):
                in_requirements_section = True
                i += 1
                continue
            elif in_requirements_section and line.startswith('## ') and not line.startswith('### '):
                # End of requirements section (new level-2 section)
                if current_req_id:
                    # Use title as description if no separate description found
                    description = '\n'.join(req_description_lines).strip() or current_req_title or ""
                    if description:
                        requirements.append(Requirement(
                            id=current_req_id,
                            type=req_type,
                            description=description,
                            rationale=rationale,
                            status=req_status
                        ))
                    current_req_id = None  # Clear to prevent double-saving
                break
            elif in_requirements_section and line.startswith('### '):
                # Save previous requirement if exists
                if current_req_id:
                    # Use title as description if no separate description found
                    description = '\n'.join(req_description_lines).strip() or current_req_title or ""
                    if description:
                        requirements.append(Requirement(
                            id=current_req_id,
                            type=req_type,
                            description=description,
                            rationale=rationale,
                            status=req_status
                        ))
                
                # Parse new requirement header
                req_header = line[4:].strip()
                if ':' in req_header:
                    current_req_id, current_req_title = req_header.split(':', 1)
                    current_req_id = current_req_id.strip()
                    current_req_title = current_req_title.strip()
                    req_description_lines = []
                    req_type = "functional"
                    rationale = None
                    req_status = "draft"
            elif in_requirements_section and current_req_id:
                if line.startswith('**Type**:'):
                    req_type = line.split(':', 1)[1].strip()
                elif line.startswith('**Status**:'):
                    req_status = line.split(':', 1)[1].strip()
                elif line.startswith('**Rationale**:'):
                    rationale = line.split(':', 1)[1].strip()
                elif line.strip() and not line.startswith('**'):
                    req_description_lines.append(line)
            elif in_requirements_section and line.strip().lower() == "none":
                # No requirements
                break
            
            i += 1
        
        # Save last requirement if exists
        if in_requirements_section and current_req_id:
            # Use title as description if no separate description found
            description = '\n'.join(req_description_lines).strip() or current_req_title or ""
            if description:
                requirements.append(Requirement(
                    id=current_req_id,
                    type=req_type,
                    description=description,
                    rationale=rationale,
                    status=req_status
                ))
        
        return requirements

    def _parse_open_questions(self, lines: List[str]) -> List[str]:
        """Parse open questions from Markdown lines.

        Args:
            lines: All lines in the document

        Returns:
            List of question strings
        """
        questions = []
        in_questions_section = False
        
        for line in lines:
            if line.startswith('## Open Questions'):
                in_questions_section = True
                continue
            elif in_questions_section and line.startswith('## '):
                # End of questions section
                break
            elif in_questions_section and line.strip().lower() == "none":
                # No questions
                break
            elif in_questions_section and line.startswith('- '):
                # Parse question
                question = line[2:].strip()
                if question:
                    questions.append(question)
        
        return questions

    def _get_spec_dir(self, spec_id: str) -> Path:
        """Get directory path for a specification.

        Args:
            spec_id: Specification identifier

        Returns:
            Path to the spec directory
        """
        return self.storage_path / spec_id

    def _get_spec_file(self, spec_id: str) -> Path:
        """Get file path for a specification.

        Args:
            spec_id: Specification identifier

        Returns:
            Path to the spec.md file
        """
        return self._get_spec_dir(spec_id) / "spec.md"

    def _format_markdown(self, spec: Specification) -> str:
        """Format specification as Markdown.

        Args:
            spec: Specification to format

        Returns:
            Markdown string
        """
        lines = []
        
        # Title
        lines.append(f"# {spec.title}")
        lines.append("")
        
        # Metadata
        lines.append(f"**ID**: {spec.id}")
        lines.append(f"**Status**: {spec.status}")
        lines.append(f"**Created**: {spec.created_at.isoformat()}")
        lines.append(f"**Updated**: {spec.updated_at.isoformat()}")
        lines.append("")
        
        # Description
        lines.append("## Description")
        lines.append("")
        lines.append(spec.description)
        lines.append("")
        
        # User Stories
        lines.append("## User Stories")
        lines.append("")
        if spec.user_stories:
            for story in spec.user_stories:
                lines.append(f"### {story.id}: {story.title}")
                lines.append("")
                lines.append(f"**Priority**: {story.priority}")
                lines.append(f"**Status**: {story.status}")
                lines.append("")
                lines.append(story.description)
                lines.append("")
                if story.acceptance_criteria:
                    lines.append("**Acceptance Criteria**:")
                    for criterion in story.acceptance_criteria:
                        lines.append(f"- {criterion}")
                    lines.append("")
        else:
            lines.append("None")
            lines.append("")
        
        # Requirements
        lines.append("## Requirements")
        lines.append("")
        if spec.requirements:
            for req in spec.requirements:
                lines.append(f"### {req.id}: {req.description}")
                lines.append("")
                lines.append(f"**Type**: {req.type}")
                lines.append(f"**Status**: {req.status}")
                lines.append("")
                if req.rationale:
                    lines.append(f"**Rationale**: {req.rationale}")
                    lines.append("")
        else:
            lines.append("None")
            lines.append("")
        
        # Open Questions
        lines.append("## Open Questions")
        lines.append("")
        if spec.open_questions:
            for question in spec.open_questions:
                lines.append(f"- {question}")
        else:
            lines.append("None")
        
        return '\n'.join(lines)

    async def save(self, spec: Specification) -> None:
        """Save a specification to storage.

        Creates a new specification or updates an existing one.

        Args:
            spec: Specification to save

        Raises:
            IOError: If save operation fails

        Example:
            >>> spec = Specification(
            ...     id="SPEC-001",
            ...     title="Authentication Feature",
            ...     description="Add user authentication to the app",
            ...     status="draft"
            ... )
            >>> await store.save(spec)
        """
        async with self._lock:
            try:
                # Update timestamp
                spec.updated_at = datetime.now()
                
                # Create spec directory
                spec_dir = self._get_spec_dir(spec.id)
                ensure_directory(spec_dir)
                
                # Format as markdown
                markdown = self._format_markdown(spec)
                
                # Write to file
                spec_file = self._get_spec_file(spec.id)
                spec_file.write_text(markdown)
                
                # Update in-memory cache
                self.specs[spec.id] = spec
                
                logger.debug(f"Saved specification: {spec.id}")
                
            except Exception as e:
                logger.error(f"Failed to save specification {spec.id}: {e}")
                raise IOError(f"Failed to save specification: {e}") from e

    async def load(self, spec_id: str) -> Optional[Specification]:
        """Load a specification from storage.

        Args:
            spec_id: Specification identifier

        Returns:
            Specification instance or None if not found

        Example:
            >>> spec = await store.load("SPEC-001")
        """
        spec_file = self._get_spec_file(spec_id)
        return await self._load_spec_from_file(spec_file)

    async def get(self, spec_id: str) -> Optional[Specification]:
        """Get a specification by ID from cache.

        Args:
            spec_id: Specification identifier

        Returns:
            Specification instance or None if not found

        Example:
            >>> spec = await store.get("SPEC-001")
            >>> if spec:
            ...     print(spec.title)
        """
        async with self._lock:
            return self.specs.get(spec_id)

    async def list_all(self, status: Optional[str] = None) -> List[Specification]:
        """List all specifications.

        Args:
            status: Optional status filter

        Returns:
            List of specifications

        Example:
            >>> specs = await store.list_all()
            >>> draft_specs = await store.list_all(status="draft")
        """
        async with self._lock:
            specs = list(self.specs.values())
            
            if status:
                specs = [s for s in specs if s.status == status]
            
            return specs

    async def list_by_status(self, status: str) -> List[Specification]:
        """List specifications by status.

        Args:
            status: Status to filter by

        Returns:
            List of specifications with the given status

        Example:
            >>> specs = await store.list_by_status("draft")
        """
        return await self.list_all(status=status)

    async def delete(self, spec_id: str) -> bool:
        """Delete a specification.

        Args:
            spec_id: Specification identifier

        Returns:
            True if deleted, False if not found

        Example:
            >>> deleted = await store.delete("SPEC-001")
        """
        async with self._lock:
            if spec_id not in self.specs:
                return False

            try:
                # Delete directory
                spec_dir = self._get_spec_dir(spec_id)
                if spec_dir.exists():
                    shutil.rmtree(spec_dir)
                
                # Remove from cache
                del self.specs[spec_id]
                logger.debug(f"Deleted specification: {spec_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete specification {spec_id}: {e}")
                return False

    async def search(
        self,
        title_contains: Optional[str] = None,
        description_contains: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Specification]:
        """Search specifications by various criteria.

        Search is case-insensitive.

        Args:
            title_contains: Search for specs with title containing this text
            description_contains: Search for specs with description containing this text
            status: Filter by status

        Returns:
            List of matching specifications

        Example:
            >>> results = await store.search(title_contains="Authentication")
            >>> results = await store.search(
            ...     title_contains="Auth",
            ...     status="in-progress"
            ... )
        """
        async with self._lock:
            results = list(self.specs.values())
            
            # Filter by title
            if title_contains:
                title_lower = title_contains.lower()
                results = [
                    s for s in results 
                    if title_lower in s.title.lower()
                ]
            
            # Filter by description
            if description_contains:
                desc_lower = description_contains.lower()
                results = [
                    s for s in results 
                    if desc_lower in s.description.lower()
                ]
            
            # Filter by status
            if status:
                results = [s for s in results if s.status == status]
            
            return results
