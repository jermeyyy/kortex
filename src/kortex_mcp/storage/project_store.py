"""Project configuration storage with JSON-based persistence.

This module provides persistent storage for project configuration,
including source sets, targets, and detected project metadata.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from ..models.project import Project, ProjectType, SourceSet, SourceSetType, Target
from ..utils.file_utils import ensure_directory
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ProjectStore:
    """Persistent storage for project configuration.

    Stores project configuration in JSON format with support for
    saving and loading project metadata.

    Attributes:
        storage_path: Path to the project configuration file
        _lock: Async lock for thread-safe operations

    Example:
        >>> store = ProjectStore(Path(".kortex/project.json"))
        >>> await store.save(project)
        >>> loaded = await store.load()
    """

    def __init__(self, storage_path: Path):
        """Initialize project store.

        Args:
            storage_path: Path to project configuration file
        """
        self.storage_path = storage_path
        self._lock = asyncio.Lock()

    async def save(self, project: Project) -> None:
        """Save project configuration to storage.

        Args:
            project: Project to save

        Raises:
            IOError: If save operation fails

        Example:
            >>> await store.save(project)
        """
        logger.info(f"Saving project configuration: {project.name}")

        async with self._lock:
            # Ensure directory exists
            ensure_directory(self.storage_path.parent)

            # Convert to dictionary
            data = self._project_to_dict(project)

            try:
                # Write JSON file
                await asyncio.to_thread(
                    lambda: self.storage_path.write_text(
                        json.dumps(data, indent=2)
                    )
                )
                logger.debug(f"Project configuration saved to {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to save project configuration: {e}")
                raise OSError(f"Failed to save project: {e}") from e

    async def load(self) -> Project | None:
        """Load project configuration from storage.

        Returns:
            Project instance if found, None otherwise

        Example:
            >>> project = await store.load()
            >>> if project:
            ...     print(project.name)
        """
        if not self.storage_path.exists():
            logger.debug("Project configuration file not found")
            return None

        async with self._lock:
            try:
                # Read JSON file
                data = await asyncio.to_thread(
                    lambda: json.loads(self.storage_path.read_text())
                )

                project = self._dict_to_project(data)
                logger.info(f"Loaded project configuration: {project.name}")
                return project

            except Exception as e:
                logger.error(f"Failed to load project configuration: {e}")
                return None

    async def exists(self) -> bool:
        """Check if project configuration exists.

        Returns:
            True if configuration file exists

        Example:
            >>> if await store.exists():
            ...     print("Project already configured")
        """
        return self.storage_path.exists()

    async def delete(self) -> bool:
        """Delete project configuration.

        Returns:
            True if deleted, False if file didn't exist

        Example:
            >>> deleted = await store.delete()
        """
        async with self._lock:
            if not self.storage_path.exists():
                return False

            try:
                self.storage_path.unlink()
                logger.info("Project configuration deleted")
                return True
            except Exception as e:
                logger.error(f"Failed to delete project configuration: {e}")
                return False

    def _project_to_dict(self, project: Project) -> dict[str, Any]:
        """Convert Project to dictionary for serialization.

        Args:
            project: Project to convert

        Returns:
            Dictionary representation
        """
        return {
            "name": project.name,
            "root_path": str(project.root_path),
            "type": project.type.value,
            "source_sets": {
                name: self._source_set_to_dict(ss)
                for name, ss in project.source_sets.items()
            },
            "targets": [self._target_to_dict(t) for t in project.targets],
            "gradle_version": project.gradle_version,
            "kotlin_version": project.kotlin_version,
            "compose_version": project.compose_version,
            "build_files": [str(p) for p in project.build_files],
        }

    def _source_set_to_dict(self, source_set: SourceSet) -> dict[str, Any]:
        """Convert SourceSet to dictionary.

        Args:
            source_set: SourceSet to convert

        Returns:
            Dictionary representation
        """
        return {
            "name": source_set.name,
            "type": source_set.type.value,
            "source_dirs": [str(p) for p in source_set.source_dirs],
            "resource_dirs": [str(p) for p in source_set.resource_dirs],
            "dependencies": source_set.dependencies,
            "depends_on": source_set.depends_on,
        }

    def _target_to_dict(self, target: Target) -> dict[str, Any]:
        """Convert Target to dictionary.

        Args:
            target: Target to convert

        Returns:
            Dictionary representation
        """
        return {
            "name": target.name,
            "platform": target.platform,
            "source_sets": target.source_sets,
        }

    def _dict_to_project(self, data: dict[str, Any]) -> Project:
        """Convert dictionary to Project.

        Args:
            data: Dictionary with project data

        Returns:
            Project instance
        """
        return Project(
            name=data["name"],
            root_path=Path(data["root_path"]),
            type=ProjectType(data["type"]),
            source_sets={
                name: self._dict_to_source_set(ss_data)
                for name, ss_data in data.get("source_sets", {}).items()
            },
            targets=[
                self._dict_to_target(t_data)
                for t_data in data.get("targets", [])
            ],
            gradle_version=data.get("gradle_version"),
            kotlin_version=data.get("kotlin_version"),
            compose_version=data.get("compose_version"),
            build_files=[Path(p) for p in data.get("build_files", [])],
        )

    def _dict_to_source_set(self, data: dict[str, Any]) -> SourceSet:
        """Convert dictionary to SourceSet.

        Args:
            data: Dictionary with source set data

        Returns:
            SourceSet instance
        """
        return SourceSet(
            name=data["name"],
            type=SourceSetType(data["type"]),
            source_dirs=[Path(p) for p in data.get("source_dirs", [])],
            resource_dirs=[Path(p) for p in data.get("resource_dirs", [])],
            dependencies=data.get("dependencies", []),
            depends_on=data.get("depends_on", []),
        )

    def _dict_to_target(self, data: dict[str, Any]) -> Target:
        """Convert dictionary to Target.

        Args:
            data: Dictionary with target data

        Returns:
            Target instance
        """
        return Target(
            name=data["name"],
            platform=data["platform"],
            source_sets=data.get("source_sets", []),
        )

    async def update_partial(self, updates: dict[str, Any]) -> bool:
        """Update specific fields in stored project configuration.

        Args:
            updates: Dictionary with fields to update

        Returns:
            True if update succeeded, False otherwise

        Example:
            >>> await store.update_partial({
            ...     "kotlin_version": "1.9.21",
            ...     "compose_version": "1.5.11"
            ... })
        """
        project = await self.load()
        if not project:
            logger.warning("Cannot update: no project configuration found")
            return False

        # Update fields
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)

        # Save updated project
        try:
            await self.save(project)
            return True
        except Exception as e:
            logger.error(f"Failed to update project configuration: {e}")
            return False

    async def get_project_name(self) -> str | None:
        """Get project name from stored configuration.

        Returns:
            Project name if configuration exists, None otherwise

        Example:
            >>> name = await store.get_project_name()
        """
        project = await self.load()
        return project.name if project else None

    async def get_source_set_names(self) -> list[str]:
        """Get list of source set names from stored configuration.

        Returns:
            List of source set names

        Example:
            >>> source_sets = await store.get_source_set_names()
            >>> print(source_sets)  # ['commonMain', 'androidMain', 'iosMain']
        """
        project = await self.load()
        return list(project.source_sets.keys()) if project else []

    async def get_target_names(self) -> list[str]:
        """Get list of target names from stored configuration.

        Returns:
            List of target names

        Example:
            >>> targets = await store.get_target_names()
            >>> print(targets)  # ['android', 'ios']
        """
        project = await self.load()
        return [t.name for t in project.targets] if project else []
