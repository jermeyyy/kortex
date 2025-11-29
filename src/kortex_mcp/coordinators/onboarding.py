"""Onboarding coordinator for orchestrating project analysis and memory generation.

This module provides the OnboardingCoordinator class that manages the complete
onboarding workflow: running analyzers, generating memories, and storing results.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from kortex_mcp.analyzers.base import AnalysisResult, BaseAnalyzer
from kortex_mcp.analyzers.structure_analyzer import StructureAnalyzer
from kortex_mcp.analyzers.tech_stack_analyzer import TechStackAnalyzer
from kortex_mcp.analyzers.architecture_analyzer import ArchitectureAnalyzer
from kortex_mcp.analyzers.dependency_analyzer import DependencyAnalyzer
from kortex_mcp.analyzers.android_analyzer import AndroidAnalyzer
from kortex_mcp.analyzers.ios_analyzer import iOSAnalyzer
from kortex_mcp.analyzers.pattern_analyzer import PatternAnalyzer
from kortex_mcp.analyzers.testing_analyzer import TestingAnalyzer
from kortex_mcp.generators.base import BaseMemoryGenerator
from kortex_mcp.generators.structure_generator import StructureMemoryGenerator
from kortex_mcp.generators.tech_stack_generator import TechStackMemoryGenerator
from kortex_mcp.generators.architecture_generator import ArchitectureMemoryGenerator
from kortex_mcp.generators.dependency_generator import DependencyMemoryGenerator
from kortex_mcp.generators.android_generator import AndroidMemoryGenerator
from kortex_mcp.generators.ios_generator import iOSMemoryGenerator
from kortex_mcp.generators.pattern_generator import PatternMemoryGenerator
from kortex_mcp.generators.testing_generator import TestingMemoryGenerator
from kortex_mcp.models.memory import Memory, MemoryCategory
from kortex_mcp.storage.memory_store import MemoryStore

logger = logging.getLogger(__name__)


@dataclass
class OnboardingResult:
    """Result of the onboarding process.

    Contains information about the overall success of onboarding,
    which memories were generated, and any errors or warnings encountered.

    Attributes:
        success: Whether the onboarding completed successfully.
        project_name: Name of the onboarded project.
        memories_generated: List of memory IDs that were successfully generated.
        errors: List of error messages encountered during onboarding.
        warnings: List of warning messages generated during onboarding.

    Example:
        >>> result = OnboardingResult(
        ...     success=True,
        ...     project_name="my-kmp-project",
        ...     memories_generated=["tech_stack", "architecture"],
        ...     errors=[],
        ...     warnings=["No iOS source set found"]
        ... )
    """

    success: bool
    project_name: str
    memories_generated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class RegenerateResult:
    """Result of regenerating a specific memory.

    Attributes:
        success: Whether the regeneration was successful.
        memory_id: ID of the memory that was regenerated.
        error: Error message if regeneration failed, None otherwise.

    Example:
        >>> result = RegenerateResult(
        ...     success=True,
        ...     memory_id="tech_stack",
        ...     error=None
        ... )
    """

    success: bool
    memory_id: str
    error: Optional[str] = None


class OnboardingCoordinator:
    """Coordinator for managing the project onboarding process.

    Orchestrates the execution of analyzers and memory generators to
    create a comprehensive knowledge base about a project.

    The onboarding process:
    1. Initialize the memory store
    2. Run all registered analyzers to collect project information
    3. Generate memories using registered generators
    4. Store generated memories for future reference

    Attributes:
        project_root: Path to the project being onboarded.
        analyzers: List of registered analyzers to run.
        generators: Dictionary mapping memory IDs to their generators.
        memory_store: Store for persisting generated memories.

    Example:
        >>> coordinator = OnboardingCoordinator(Path("/path/to/project"))
        >>> await coordinator.initialize()
        >>> coordinator.register_analyzer(KMPAnalyzer(project_root))
        >>> coordinator.register_generator("tech_stack", TechStackGenerator())
        >>> result = await coordinator.onboard()
        >>> print(f"Generated {len(result.memories_generated)} memories")
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the onboarding coordinator.

        Args:
            project_root: Path to the root directory of the project to onboard.
        """
        self.project_root = project_root
        self.analyzers: list[BaseAnalyzer] = []
        self.generators: dict[str, BaseMemoryGenerator] = {}
        self._memory_store: MemoryStore | None = None
        self._initialized = False
        self._register_default_components()

    def _register_default_components(self) -> None:
        """Register all default analyzers and generators.

        This method sets up the standard set of analyzers and generators
        used for project onboarding. Each analyzer collects specific
        information about the project, and each generator creates
        memory content from the analysis results.
        """
        # Register analyzers
        self.register_analyzer(StructureAnalyzer(self.project_root))
        self.register_analyzer(TechStackAnalyzer(self.project_root))
        self.register_analyzer(ArchitectureAnalyzer(self.project_root))
        self.register_analyzer(DependencyAnalyzer(self.project_root))
        self.register_analyzer(AndroidAnalyzer(self.project_root))
        self.register_analyzer(iOSAnalyzer(self.project_root))
        self.register_analyzer(PatternAnalyzer(self.project_root))
        self.register_analyzer(TestingAnalyzer(self.project_root))

        # Register generators with their memory IDs
        self.register_generator("project_structure", StructureMemoryGenerator())
        self.register_generator("tech_stack", TechStackMemoryGenerator())
        self.register_generator("architecture", ArchitectureMemoryGenerator())
        self.register_generator("dependencies", DependencyMemoryGenerator())
        self.register_generator("android_platform", AndroidMemoryGenerator())
        self.register_generator("ios_platform", iOSMemoryGenerator())
        self.register_generator("coding_patterns", PatternMemoryGenerator())
        self.register_generator("testing_setup", TestingMemoryGenerator())

    @property
    def memory_store(self) -> MemoryStore:
        """Get the memory store.

        Returns:
            The initialized MemoryStore instance.

        Raises:
            RuntimeError: If the coordinator has not been initialized.
        """
        if self._memory_store is None:
            raise RuntimeError(
                "OnboardingCoordinator not initialized. Call initialize() first."
            )
        return self._memory_store

    async def initialize(self) -> None:
        """Initialize the coordinator and memory store.

        Creates the memory storage directory and loads any existing memories.
        Must be called before running onboarding operations.

        Example:
            >>> coordinator = OnboardingCoordinator(project_root)
            >>> await coordinator.initialize()
        """
        if self._initialized:
            logger.debug("OnboardingCoordinator already initialized")
            return

        logger.info(f"Initializing OnboardingCoordinator for {self.project_root}")

        # Create memory store in project's .kortex directory
        storage_path = self.project_root / ".kortex" / "memories"
        self._memory_store = MemoryStore(storage_path)
        await self._memory_store.initialize()

        self._initialized = True
        logger.info("OnboardingCoordinator initialized successfully")

    def register_analyzer(self, analyzer: BaseAnalyzer) -> None:
        """Register an analyzer to be run during onboarding.

        Args:
            analyzer: The analyzer instance to register.

        Example:
            >>> coordinator.register_analyzer(KMPAnalyzer(project_root))
            >>> coordinator.register_analyzer(ProjectAnalyzer(project_root))
        """
        logger.debug(f"Registering analyzer: {analyzer.name}")
        self.analyzers.append(analyzer)

    def register_generator(
        self, memory_id: str, generator: BaseMemoryGenerator
    ) -> None:
        """Register a memory generator for a specific memory type.

        Args:
            memory_id: Unique identifier for the memory this generator produces.
            generator: The generator instance to register.

        Example:
            >>> coordinator.register_generator("tech_stack", TechStackGenerator())
            >>> coordinator.register_generator("architecture", ArchitectureGenerator())
        """
        logger.debug(f"Registering generator for memory: {memory_id}")
        self.generators[memory_id] = generator

    def get_available_memories(self) -> list[str]:
        """Get list of registered memory IDs.

        Returns:
            List of memory IDs that can be generated by registered generators.

        Example:
            >>> memories = coordinator.get_available_memories()
            >>> print(memories)  # ['tech_stack', 'architecture', 'patterns']
        """
        return list(self.generators.keys())

    async def onboard(self) -> OnboardingResult:
        """Run the complete onboarding process.

        Executes all registered analyzers, collects their results,
        generates memories using registered generators, and stores them.

        Returns:
            OnboardingResult containing success status, generated memories,
            and any errors or warnings encountered.

        Raises:
            RuntimeError: If the coordinator has not been initialized.

        Example:
            >>> result = await coordinator.onboard()
            >>> if result.success:
            ...     print(f"Generated {len(result.memories_generated)} memories")
            ... else:
            ...     print(f"Errors: {result.errors}")
        """
        if not self._initialized:
            raise RuntimeError(
                "OnboardingCoordinator not initialized. Call initialize() first."
            )

        logger.info(f"Starting onboarding for project: {self.project_root}")
        start_time = datetime.now()

        project_name = self.project_root.name
        errors: list[str] = []
        warnings: list[str] = []
        memories_generated: list[str] = []

        # Run all analyzers and collect results
        analysis_data: dict[str, Any] = {}
        analysis_results: list[AnalysisResult] = []

        logger.info(f"Running {len(self.analyzers)} analyzers")
        for analyzer in self.analyzers:
            result = await self._run_analyzer(analyzer)
            analysis_results.append(result)

            if result.success:
                # Merge analyzer data into combined analysis data
                analysis_data[analyzer.name] = result.data
                warnings.extend(result.warnings)
            else:
                errors.extend(result.errors)
                warnings.extend(result.warnings)
                logger.warning(
                    f"Analyzer {analyzer.name} failed: {result.errors}"
                )

        # Generate memories using collected analysis data
        logger.info(f"Generating {len(self.generators)} memories")
        for memory_id, generator in self.generators.items():
            success = await self._generate_memory(memory_id, analysis_data)
            if success:
                memories_generated.append(memory_id)
            else:
                errors.append(f"Failed to generate memory: {memory_id}")

        # Determine overall success
        # Success if at least one memory was generated and no critical errors
        success = len(memories_generated) > 0 and len(errors) == 0

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Onboarding completed in {elapsed:.2f}s. "
            f"Generated {len(memories_generated)} memories, "
            f"{len(errors)} errors, {len(warnings)} warnings"
        )

        return OnboardingResult(
            success=success,
            project_name=project_name,
            memories_generated=memories_generated,
            errors=errors,
            warnings=warnings,
        )

    async def regenerate_memory(self, memory_id: str) -> RegenerateResult:
        """Regenerate a specific memory.

        Re-runs the necessary analyzers and regenerates the specified memory.
        Useful when project structure has changed or analysis needs updating.

        Args:
            memory_id: ID of the memory to regenerate.

        Returns:
            RegenerateResult indicating success or failure.

        Raises:
            RuntimeError: If the coordinator has not been initialized.

        Example:
            >>> result = await coordinator.regenerate_memory("tech_stack")
            >>> if result.success:
            ...     print("Memory regenerated successfully")
            ... else:
            ...     print(f"Error: {result.error}")
        """
        if not self._initialized:
            raise RuntimeError(
                "OnboardingCoordinator not initialized. Call initialize() first."
            )

        logger.info(f"Regenerating memory: {memory_id}")

        # Check if generator exists for this memory
        if memory_id not in self.generators:
            error_msg = f"No generator registered for memory: {memory_id}"
            logger.error(error_msg)
            return RegenerateResult(
                success=False,
                memory_id=memory_id,
                error=error_msg,
            )

        # Run all analyzers to get fresh data
        analysis_data: dict[str, Any] = {}
        for analyzer in self.analyzers:
            result = await self._run_analyzer(analyzer)
            if result.success:
                analysis_data[analyzer.name] = result.data

        # Generate the specific memory
        try:
            success = await self._generate_memory(memory_id, analysis_data)
            if success:
                logger.info(f"Successfully regenerated memory: {memory_id}")
                return RegenerateResult(
                    success=True,
                    memory_id=memory_id,
                    error=None,
                )
            else:
                error_msg = f"Failed to generate memory content for: {memory_id}"
                logger.error(error_msg)
                return RegenerateResult(
                    success=False,
                    memory_id=memory_id,
                    error=error_msg,
                )
        except Exception as e:
            error_msg = f"Exception while regenerating memory {memory_id}: {e}"
            logger.exception(error_msg)
            return RegenerateResult(
                success=False,
                memory_id=memory_id,
                error=error_msg,
            )

    async def _run_analyzer(self, analyzer: BaseAnalyzer) -> AnalysisResult:
        """Run a single analyzer with error handling.

        Wraps the analyzer execution in a try-except block to ensure
        that failures in one analyzer don't affect others.

        Args:
            analyzer: The analyzer to run.

        Returns:
            AnalysisResult from the analyzer, or an error result if the
            analyzer raised an exception.
        """
        logger.debug(f"Running analyzer: {analyzer.name}")

        try:
            result = await analyzer.analyze()
            logger.debug(
                f"Analyzer {analyzer.name} completed: "
                f"success={result.success}, "
                f"warnings={len(result.warnings)}"
            )
            return result
        except Exception as e:
            error_msg = f"Analyzer {analyzer.name} raised exception: {e}"
            logger.exception(error_msg)
            return AnalysisResult(
                analyzer_name=analyzer.name,
                success=False,
                data={},
                errors=[error_msg],
                warnings=[],
            )

    async def _generate_memory(
        self, memory_id: str, analysis_data: dict[str, Any]
    ) -> bool:
        """Generate and store a single memory.

        Uses the registered generator to create memory content from
        analysis data and stores it in the memory store.

        Args:
            memory_id: ID of the memory to generate.
            analysis_data: Combined data from all analyzers.

        Returns:
            True if the memory was successfully generated and stored,
            False otherwise.
        """
        logger.debug(f"Generating memory: {memory_id}")

        generator = self.generators.get(memory_id)
        if generator is None:
            logger.error(f"No generator found for memory: {memory_id}")
            return False

        try:
            # Generate structured content from analysis data
            content_data = generator.generate_content(analysis_data)

            # Convert to markdown for storage
            markdown_content = generator.to_markdown(content_data)

            # Determine memory category from generator
            try:
                category = MemoryCategory(generator.memory_category)
            except ValueError:
                logger.warning(
                    f"Unknown memory category '{generator.memory_category}', "
                    f"using OTHER"
                )
                category = MemoryCategory.OTHER

            # Create or update the memory in the store
            memory = await self.memory_store.create_or_update(
                category=category,
                title=generator.memory_title,
                content=markdown_content,
                tags=[memory_id, generator.memory_category],
                memory_id=memory_id,
            )

            logger.debug(f"Memory {memory_id} stored successfully: {memory}")
            return True

        except Exception as e:
            logger.exception(f"Failed to generate memory {memory_id}: {e}")
            return False
