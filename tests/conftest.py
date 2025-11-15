"""Pytest configuration and fixtures for Kortex tests."""

import asyncio
import pytest
from pathlib import Path
from typing import AsyncGenerator, Generator
import tempfile
import shutil

from kortex_mcp.lsp.client import LSPClient
from kortex_mcp.lsp.manager import LSPManager
from kortex_mcp.storage.memory_store import MemoryStore
from kortex_mcp.storage.project_store import ProjectStore
from kortex_mcp.models.project import Project, SourceSet, ProjectType, SourceSetType


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests.

    Yields:
        Path to temporary directory
    """
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def fixtures_dir() -> Path:
    """Get path to test fixtures directory.

    Returns:
        Path to fixtures directory
    """
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_kmp_project(fixtures_dir: Path) -> Path:
    """Get path to sample KMP project fixture.

    Args:
        fixtures_dir: Fixtures directory path

    Returns:
        Path to sample KMP project
    """
    return fixtures_dir / "sample_kmp_project"


@pytest.fixture
def sample_cmp_project(fixtures_dir: Path) -> Path:
    """Get path to sample CMP project fixture.

    Args:
        fixtures_dir: Fixtures directory path

    Returns:
        Path to sample CMP project
    """
    return fixtures_dir / "sample_cmp_project"


@pytest.fixture
async def memory_store(temp_dir: Path) -> AsyncGenerator[MemoryStore, None]:
    """Create a temporary memory store for testing.

    Args:
        temp_dir: Temporary directory path

    Yields:
        Initialized MemoryStore instance
    """
    store_path = temp_dir / "memories"
    store = MemoryStore(store_path)
    await store.initialize()
    yield store
    # Cleanup
    if store_path.exists():
        await store.clear()


@pytest.fixture
async def project_store(temp_dir: Path) -> ProjectStore:
    """Create a temporary project store for testing.

    Args:
        temp_dir: Temporary directory path

    Returns:
        ProjectStore instance
    """
    store_path = temp_dir / "project.json"
    return ProjectStore(store_path)


@pytest.fixture
def sample_project(sample_kmp_project: Path) -> Project:
    """Create a sample Project instance for testing.

    Args:
        sample_kmp_project: Path to sample KMP project

    Returns:
        Project instance with sample data
    """
    return Project(
        name="SampleKMPProject",
        root_path=sample_kmp_project,
        type=ProjectType.KMP,
        source_sets={
            "commonMain": SourceSet(
                name="commonMain",
                type=SourceSetType.COMMON,
                source_dirs=[sample_kmp_project / "src/commonMain/kotlin"],
                dependencies=[
                    "org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3",
                    "org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0",
                ]
            ),
            "androidMain": SourceSet(
                name="androidMain",
                type=SourceSetType.ANDROID,
                source_dirs=[sample_kmp_project / "src/androidMain/kotlin"],
                dependencies=["androidx.core:core-ktx:1.12.0"],
                depends_on=["commonMain"]
            ),
            "iosMain": SourceSet(
                name="iosMain",
                type=SourceSetType.IOS,
                source_dirs=[sample_kmp_project / "src/iosMain/kotlin"],
                depends_on=["commonMain"]
            ),
        },
        kotlin_version="1.9.20",
        build_files=[sample_kmp_project / "build.gradle.kts"],
    )


@pytest.fixture
async def lsp_manager() -> AsyncGenerator[LSPManager, None]:
    """Create an LSP manager for testing.

    Yields:
        LSPManager instance
    """
    manager = LSPManager(health_check_interval=5.0, max_restart_attempts=2)
    yield manager
    # Cleanup - stop all servers
    await manager.stop_all()


class MockLSPClient(LSPClient):
    """Mock LSP client for testing without actual language server."""

    def __init__(self):
        """Initialize mock LSP client."""
        super().__init__(
            command="mock-lsp-server",
            workspace_path=Path("/mock/workspace")
        )
        self._mock_initialized = False

    async def start(self) -> None:
        """Mock start method."""
        self._mock_initialized = True

    async def stop(self) -> None:
        """Mock stop method."""
        self._mock_initialized = False

    def is_running(self) -> bool:
        """Mock is_running method."""
        return self._mock_initialized

    async def workspace_symbols(self, query: str) -> list:
        """Mock workspace_symbols method."""
        # Return some mock symbols
        from kortex_mcp.models.lsp import SymbolInformation, Location, Range, Position
        
        return [
            SymbolInformation(
                name="Repository",
                kind=5,  # Class
                location=Location(
                    uri="file:///mock/Repository.kt",
                    range=Range(
                        start=Position(line=5, character=0),
                        end=Position(line=10, character=0)
                    )
                ),
                containerName="com.example.kmp"
            )
        ]


@pytest.fixture
def mock_lsp_client() -> MockLSPClient:
    """Create a mock LSP client for testing.

    Returns:
        Mock LSP client instance
    """
    return MockLSPClient()


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests.

    Yields:
        Event loop instance
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Add markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
