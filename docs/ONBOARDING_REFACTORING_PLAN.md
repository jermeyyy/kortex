# Onboarding Tool - Refactoring Plan

## Executive Summary

This document outlines the refactoring plan for the Kortex onboarding tool. The goal is to transform the current basic project analysis into a comprehensive onboarding system that:

1. **Analyzes** project structure, architecture, and technological stack
2. **Generates** separate memories for different aspects (auto-generated on onboarding)
3. **Provides** agent-readable markdown output via `read_memory` tool
4. **Supports** both Kotlin ecosystem and Swift/iOS for full multiplatform coverage
5. **Allows** regenerating specific memory categories on demand

---

## Design Decisions

Based on user requirements:

| Decision | Choice |
|----------|--------|
| Memory generation | Auto-generate all memories on onboarding + allow regenerating specific ones |
| Storage format | JSON storage (internal) + markdown output on demand via `read_memory` tool |
| Memory scope | Project-level only (stored in `.kortex/`) |
| Tech stack scope | Kotlin ecosystem + Swift/iOS (full multiplatform) |

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               MCP Server                                         │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────────────────────┐   │
│  │ onboard_project │  │ regenerate_memory│  │ read_memory (returns markdown) │   │
│  └───────┬────────┘  └────────┬─────────┘  └─────────────┬──────────────────┘   │
└──────────┼────────────────────┼──────────────────────────┼──────────────────────┘
           │                    │                          │
           ▼                    ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Onboarding Coordinator                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  orchestrates analysis → coordinates generators → manages memory storage  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└───────────┬──────────────────────────────────────────────────────────────────────┘
            │
            ├──────────────────────┬──────────────────────┬─────────────────────┐
            ▼                      ▼                      ▼                     ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐
│ Project Structure │  │   Tech Stack      │  │   Architecture    │  │  Platform       │
│    Analyzer       │  │    Analyzer       │  │     Analyzer      │  │   Analyzer      │
│ ─────────────────│  │ ─────────────────│  │ ─────────────────│  │ ───────────────│
│ • Gradle parsing  │  │ • DI framework   │  │ • MVVM/MVI/etc   │  │ • Android       │
│ • Source sets     │  │ • Networking     │  │ • Layer detection │  │ • iOS/Swift     │
│ • Targets         │  │ • Database       │  │ • Module roles    │  │ • Desktop       │
│ • Build files     │  │ • UI framework   │  │ • Dependency flow │  │ • Web           │
│ • Dependencies    │  │ • Testing        │  │ • Patterns        │  │                 │
└─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘  └───────┬─────────┘
          │                      │                      │                    │
          ▼                      ▼                      ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Memory Generator Factory                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │StructureMemory  │  │ TechStackMemory │  │ArchitectureMemory│  │PlatformMemory │ │
│  │   Generator     │  │   Generator     │  │    Generator     │  │  Generator  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└───────────┬──────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Memory Storage (.kortex/memories/)                        │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  project_structure.json  tech_stack.json  architecture.json  ios.json    │   │
│  │  android.json            dependencies.json  coding_patterns.json  ...    │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Memory Categories

The following memories will be auto-generated during onboarding:

| Memory | Description | Source Analysis |
|--------|-------------|-----------------|
| `project_structure` | Project layout, modules, source sets, build files | ProjectStructureAnalyzer |
| `tech_stack` | Frameworks, libraries, and tools used | TechStackAnalyzer |
| `architecture` | Design patterns, layering, module organization | ArchitectureAnalyzer |
| `dependencies` | Dependency graph, versions, relationships | DependencyAnalyzer |
| `android_platform` | Android-specific configs, manifest, resources | AndroidAnalyzer |
| `ios_platform` | iOS-specific configs, plist, Swift interop | iOSAnalyzer |
| `coding_patterns` | Code conventions, naming, styling detected | PatternAnalyzer |
| `build_configuration` | Build variants, flavors, signing | BuildConfigAnalyzer |
| `testing_setup` | Testing frameworks, conventions, coverage | TestingAnalyzer |

---

## Implementation Phases

### Phase 1: Core Infrastructure Refactoring

#### 1.1 Create Analyzer Base Class

```python
# src/kortex_mcp/analyzers/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class AnalysisResult:
    """Base result from any analyzer."""
    analyzer_name: str
    success: bool
    data: dict[str, Any]
    errors: list[str]
    warnings: list[str]

class BaseAnalyzer(ABC):
    """Base class for all project analyzers."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Analyzer name for identification."""
        pass
    
    @abstractmethod
    async def analyze(self) -> AnalysisResult:
        """Perform analysis and return results."""
        pass
    
    @abstractmethod
    def get_memory_category(self) -> str:
        """Return the memory category this analyzer populates."""
        pass
```

#### 1.2 Create Memory Generator Base Class

```python
# src/kortex_mcp/generators/base.py

from abc import ABC, abstractmethod
from typing import Any

class BaseMemoryGenerator(ABC):
    """Base class for memory generators."""
    
    @property
    @abstractmethod
    def memory_id(self) -> str:
        """Unique identifier for the memory."""
        pass
    
    @property
    @abstractmethod
    def memory_title(self) -> str:
        """Human-readable title."""
        pass
    
    @abstractmethod
    def generate_content(self, analysis_data: dict[str, Any]) -> str:
        """Generate memory content from analysis data."""
        pass
    
    @abstractmethod
    def to_markdown(self, memory_data: dict[str, Any]) -> str:
        """Convert stored memory to agent-readable markdown."""
        pass
```

#### 1.3 Create Onboarding Coordinator

```python
# src/kortex_mcp/coordinators/onboarding.py

class OnboardingCoordinator:
    """Orchestrates the entire onboarding process."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.analyzers: list[BaseAnalyzer] = []
        self.generators: dict[str, BaseMemoryGenerator] = {}
        self.memory_store: MemoryStore = None
    
    async def onboard(self) -> OnboardingResult:
        """Run full onboarding process."""
        pass
    
    async def regenerate_memory(self, memory_id: str) -> RegenerateResult:
        """Regenerate a specific memory category."""
        pass
    
    def get_available_memories(self) -> list[str]:
        """List available memory categories."""
        pass
```

---

### Phase 2: Implement Analyzers

#### 2.1 Project Structure Analyzer (Refactor Existing)

**File:** `src/kortex_mcp/analyzers/structure_analyzer.py`

Refactor existing `ProjectAnalyzer` to:
- Inherit from `BaseAnalyzer`
- Return `AnalysisResult` instead of `Project`
- Better multi-module support
- Version catalog (`libs.versions.toml`) parsing

**Extracted Information:**
- Project name and type (KMP/CMP)
- Module structure and hierarchy
- Source sets with types and paths
- Build targets and platforms
- Build file locations
- Gradle wrapper version

#### 2.2 Tech Stack Analyzer (New)

**File:** `src/kortex_mcp/analyzers/tech_stack_analyzer.py`

Detect frameworks and libraries by scanning:
- `build.gradle.kts` dependencies
- Import statements in source files
- Configuration files

**Detection Targets:**

| Category | Frameworks to Detect |
|----------|---------------------|
| DI | Koin, Hilt, Dagger, Kodein |
| Networking | Ktor, Retrofit, OkHttp |
| Database | Room, SQLDelight, Realm |
| Serialization | kotlinx.serialization, Moshi, Gson |
| Image Loading | Coil, Glide, Picasso |
| Navigation | Compose Navigation, Voyager, Decompose |
| State Management | StateFlow, MutableState, MVI libraries |
| Testing | JUnit, Kotest, MockK, Turbine |
| Logging | Timber, Napier, Kermit |
| Analytics | Firebase, Amplitude |

#### 2.3 Architecture Analyzer (New)

**File:** `src/kortex_mcp/analyzers/architecture_analyzer.py`

Analyze code structure to detect:

**Design Patterns:**
- MVVM (ViewModel + State classes)
- MVI (Intent/Action + State + Effect)
- MVP (Presenter + View interfaces)
- Clean Architecture (use cases, repositories)
- Repository pattern

**Detection Heuristics:**
```python
patterns = {
    "mvvm": ["ViewModel", "UiState", "StateFlow"],
    "mvi": ["Intent", "Action", "Effect", "State", "Reducer"],
    "clean_architecture": ["UseCase", "Repository", "DataSource", "Mapper"],
    "repository": ["Repository", "Dao", "DataSource"]
}
```

**Module Role Detection:**
- `:core` modules → shared utilities
- `:feature:*` → feature modules
- `:data` → data layer
- `:domain` → domain layer
- `:app` → application module

#### 2.4 Dependency Analyzer (New)

**File:** `src/kortex_mcp/analyzers/dependency_analyzer.py`

**Analysis Targets:**
- Parse all dependency declarations
- Build dependency graph between modules
- Identify dependency versions
- Detect version conflicts
- Map dependencies to categories

**Output:**
```python
{
    "modules": ["app", "core", "feature-home"],
    "inter_module_deps": {
        "app": ["core", "feature-home"],
        "feature-home": ["core"]
    },
    "external_deps": {
        "kotlinx-coroutines": "1.7.3",
        "ktor-client": "2.3.0"
    },
    "categories": {
        "networking": ["ktor-client-core", "ktor-client-json"],
        "di": ["koin-core", "koin-android"]
    }
}
```

#### 2.5 Android Platform Analyzer (New)

**File:** `src/kortex_mcp/analyzers/android_analyzer.py`

**Analysis Targets:**
- `AndroidManifest.xml` parsing
  - Permissions
  - Activities, Services, Receivers
  - Application configuration
- Resource structure (`res/`)
- ProGuard/R8 rules
- Build variants and flavors
- Min/Target SDK versions

#### 2.6 iOS Platform Analyzer (New)

**File:** `src/kortex_mcp/analyzers/ios_analyzer.py`

**Analysis Targets:**
- `Info.plist` parsing
  - Bundle identifier
  - Capabilities
  - Privacy descriptions
- Swift files in `iosMain/`
- Swift/Kotlin interop patterns
- CocoaPods/SPM dependencies
- Xcode project structure (if present)

#### 2.7 Pattern Analyzer (New)

**File:** `src/kortex_mcp/analyzers/pattern_analyzer.py`

**Analysis Targets:**
- Naming conventions (camelCase, snake_case)
- Package/directory structure patterns
- Import organization
- Code formatting (detected indentation, etc.)
- Common code patterns used

#### 2.8 Testing Analyzer (New)

**File:** `src/kortex_mcp/analyzers/testing_analyzer.py`

**Analysis Targets:**
- Test directory structure
- Testing frameworks used
- Test naming conventions
- Mock libraries
- Test coverage configuration

---

### Phase 3: Implement Memory Generators

Each analyzer has a corresponding memory generator:

#### 3.1 Structure Memory Generator

**Input:** Structure analysis result
**Output Memory:**
```markdown
# Project Structure: {project_name}

## Overview
- **Type:** Kotlin Multiplatform (KMP)
- **Kotlin Version:** 1.9.20
- **Compose Version:** 1.5.10

## Modules
| Module | Type | Dependencies |
|--------|------|--------------|
| :app | Application | :core, :feature-home |
| :core | Library | - |

## Source Sets
- **commonMain** - Shared Kotlin code
- **androidMain** - Android-specific code
- **iosMain** - iOS-specific code

## Build Files
- `/build.gradle.kts` (root)
- `/app/build.gradle.kts`
...
```

#### 3.2 Tech Stack Memory Generator

**Output Memory:**
```markdown
# Tech Stack

## Dependency Injection
- **Framework:** Koin 3.5.0
- **Usage:** Used across all modules for DI

## Networking
- **Framework:** Ktor Client 2.3.0
- **Features:** JSON serialization, logging

## Database
- **Framework:** SQLDelight 2.0.0
- **Platforms:** Android, iOS, Desktop

## UI
- **Framework:** Compose Multiplatform
- **Navigation:** Voyager
...
```

#### 3.3 Architecture Memory Generator

**Output Memory:**
```markdown
# Architecture Overview

## Design Pattern
- **Pattern:** MVVM with Clean Architecture
- **State Management:** StateFlow-based

## Layers
### Presentation Layer
- ViewModels in `:feature-*` modules
- Compose UI with state hoisting

### Domain Layer
- Use cases in `:domain` module
- Business logic separated from UI

### Data Layer
- Repositories in `:data` module
- Remote and local data sources
...
```

---

### Phase 4: Update MCP Tools

#### 4.1 Refactor `onboard_project` Tool

```python
@mcp.tool()
async def onboard_project(project_path: str) -> dict[str, Any]:
    """
    Onboard a project: analyze structure, tech stack, architecture,
    and generate memories for agent use.
    
    Returns summary of generated memories.
    """
    coordinator = OnboardingCoordinator(Path(project_path))
    result = await coordinator.onboard()
    return {
        "success": result.success,
        "project_name": result.project_name,
        "memories_generated": result.memories,
        "warnings": result.warnings
    }
```

#### 4.2 Add `regenerate_memory` Tool

```python
@mcp.tool()
async def regenerate_memory(
    project_path: str,
    memory_id: str
) -> dict[str, Any]:
    """
    Regenerate a specific memory category.
    
    Args:
        project_path: Path to project root
        memory_id: ID of memory to regenerate (e.g., "tech_stack", "architecture")
    """
    coordinator = OnboardingCoordinator(Path(project_path))
    result = await coordinator.regenerate_memory(memory_id)
    return result.to_dict()
```

#### 4.3 Update `read_memory` Tool

Modify to return markdown format:

```python
@mcp.tool()
async def read_memory(
    project_path: str,
    memory_id: str
) -> dict[str, Any]:
    """
    Read a memory in agent-readable markdown format.
    """
    store = MemoryStore(Path(project_path) / ".kortex" / "memories")
    memory = await store.get(memory_id)
    
    # Get appropriate generator for markdown conversion
    generator = get_generator_for_memory(memory_id)
    markdown_content = generator.to_markdown(memory.to_dict())
    
    return {
        "memory_id": memory_id,
        "title": memory.title,
        "content": markdown_content,  # Markdown format
        "last_updated": memory.last_accessed.isoformat()
    }
```

#### 4.4 Add `list_project_memories` Tool

```python
@mcp.tool()
async def list_project_memories(project_path: str) -> dict[str, Any]:
    """
    List all available memories for a project.
    """
    store = MemoryStore(Path(project_path) / ".kortex" / "memories")
    memories = await store.get_all()
    return {
        "memories": [
            {
                "id": m.id,
                "title": m.title,
                "category": m.category.value,
                "last_updated": m.last_accessed.isoformat()
            }
            for m in memories
        ]
    }
```

---

### Phase 5: Storage Updates

#### 5.1 Update Memory Model

Add fields for onboarding-specific metadata:

```python
@dataclass
class Memory:
    id: str
    category: MemoryCategory
    title: str
    content: str  # JSON-serializable structured content
    markdown_template: str  # Template for markdown generation
    tags: list[str]
    created_at: datetime
    last_accessed: datetime
    access_count: int
    metadata: dict[str, Any]
    source_analyzer: str  # Which analyzer generated this
    version: int  # For tracking regeneration
```

#### 5.2 Add New Memory Categories

```python
class MemoryCategory(Enum):
    # Existing
    ARCHITECTURE = "architecture"
    PATTERNS = "patterns"
    PREFERENCES = "preferences"
    DECISIONS = "decisions"
    DEPENDENCIES = "dependencies"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    OTHER = "other"
    
    # New for onboarding
    PROJECT_STRUCTURE = "project_structure"
    TECH_STACK = "tech_stack"
    ANDROID_PLATFORM = "android_platform"
    IOS_PLATFORM = "ios_platform"
    CODING_PATTERNS = "coding_patterns"
    BUILD_CONFIG = "build_config"
```

---

## File Structure After Refactoring

```
src/kortex_mcp/
├── analyzers/
│   ├── __init__.py
│   ├── base.py                    # NEW: BaseAnalyzer class
│   ├── structure_analyzer.py      # REFACTORED from project_analyzer.py
│   ├── tech_stack_analyzer.py     # NEW
│   ├── architecture_analyzer.py   # NEW
│   ├── dependency_analyzer.py     # NEW
│   ├── android_analyzer.py        # NEW
│   ├── ios_analyzer.py            # NEW
│   ├── pattern_analyzer.py        # NEW
│   ├── testing_analyzer.py        # NEW
│   └── kmp_analyzer.py            # KEEP (integrate better)
├── generators/
│   ├── __init__.py                # NEW
│   ├── base.py                    # NEW: BaseMemoryGenerator
│   ├── structure_generator.py     # NEW
│   ├── tech_stack_generator.py    # NEW
│   ├── architecture_generator.py  # NEW
│   ├── dependency_generator.py    # NEW
│   ├── android_generator.py       # NEW
│   ├── ios_generator.py           # NEW
│   ├── pattern_generator.py       # NEW
│   └── testing_generator.py       # NEW
├── coordinators/
│   ├── __init__.py                # NEW
│   └── onboarding.py              # NEW: OnboardingCoordinator
├── tools/
│   ├── project_tools.py           # REFACTOR: Update to use coordinator
│   ├── memory_tools.py            # UPDATE: Add markdown output
│   └── ...
├── models/
│   ├── memory.py                  # UPDATE: Add new categories/fields
│   └── ...
└── ...
```

---

## Migration Strategy

### Step 1: Non-Breaking Infrastructure
1. Create `base.py` files with abstract classes
2. Create `generators/` directory structure
3. Create `coordinators/` directory structure
4. Add new memory categories (backward compatible)

### Step 2: Implement New Analyzers
1. Implement `TechStackAnalyzer`
2. Implement `ArchitectureAnalyzer`
3. Implement `DependencyAnalyzer`
4. Implement `AndroidAnalyzer`
5. Implement `iOSAnalyzer`
6. Implement `PatternAnalyzer`
7. Implement `TestingAnalyzer`

### Step 3: Refactor Existing
1. Refactor `ProjectAnalyzer` → `StructureAnalyzer`
2. Integrate `KMPAnalyzer` into flow
3. Update `GradleParser` for version catalogs

### Step 4: Implement Generators
1. Implement all memory generators
2. Test markdown output quality

### Step 5: Update Tools
1. Update `onboard_project` to use coordinator
2. Add `regenerate_memory` tool
3. Update `read_memory` for markdown output
4. Add `list_project_memories` tool

### Step 6: Update Tests
1. Update existing tests for new structure
2. Add tests for new analyzers
3. Add tests for generators
4. Add integration tests for full onboarding flow

---

## Testing Strategy

### Unit Tests
- Each analyzer tested independently
- Each generator tested with mock data
- Memory store operations tested

### Integration Tests
- Full onboarding flow with test fixtures
- Memory generation and retrieval cycle
- Regeneration of specific memories

### Test Fixtures
- Enhance existing KMP/CMP fixtures
- Add fixtures for different architectures (MVVM, MVI)
- Add fixtures for different tech stacks

---

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| All analyzers produce valid results | Unit tests pass |
| Memories are generated on onboarding | Integration tests pass |
| `read_memory` returns valid markdown | Output validation tests |
| Specific memories can be regenerated | Regeneration tests pass |
| iOS analysis works | iOS fixture tests pass |
| Android analysis works | Android fixture tests pass |
| Performance acceptable | Onboarding < 30s for large projects |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Regex-based parsing failures | Add fallback detection methods |
| Large projects slow to analyze | Add caching, incremental analysis |
| Swift parsing complexity | Start with file-based detection, add AST later |
| Breaking existing functionality | Maintain backward compatibility in phase 1 |

---

## Timeline Estimate

| Phase | Estimated Effort |
|-------|------------------|
| Phase 1: Infrastructure | 2-3 days |
| Phase 2: Analyzers | 5-7 days |
| Phase 3: Generators | 3-4 days |
| Phase 4: MCP Tools | 2-3 days |
| Phase 5: Storage | 1-2 days |
| Testing & Polish | 3-4 days |
| **Total** | **16-23 days** |

---

## Appendix: Example Memory Output

### Example: `tech_stack` Memory (Markdown)

```markdown
# Technology Stack

## Overview
This document describes the technology stack used in **SampleKMPProject**.

## Kotlin Configuration
- **Kotlin Version:** 1.9.20
- **Compose Version:** 1.5.10
- **Coroutines Version:** 1.7.3

## Dependency Injection
| Library | Version | Usage |
|---------|---------|-------|
| Koin Core | 3.5.0 | Multiplatform DI |
| Koin Android | 3.5.0 | Android-specific DI |

## Networking
| Library | Version | Usage |
|---------|---------|-------|
| Ktor Client Core | 2.3.0 | HTTP client |
| Ktor Client JSON | 2.3.0 | JSON serialization |
| Ktor Client Logging | 2.3.0 | Request logging |

## Database
| Library | Version | Usage |
|---------|---------|-------|
| SQLDelight | 2.0.0 | Multiplatform database |

## UI Framework
- **Primary:** Compose Multiplatform
- **Navigation:** Voyager 1.0.0
- **Image Loading:** Coil 2.4.0

## Testing
| Library | Version | Purpose |
|---------|---------|---------|
| Kotlin Test | 1.9.20 | Unit testing |
| Kotest | 5.7.0 | Property testing |
| MockK | 1.13.8 | Mocking |
| Turbine | 1.0.0 | Flow testing |

## Build Tools
- **Gradle Version:** 8.4
- **AGP Version:** 8.1.0
- **KSP Version:** 1.9.20-1.0.14

## Notes for Development
- Use Koin for all dependency injection
- Prefer Ktor for network calls
- Use SQLDelight for local persistence
- All UI should be Compose-based
```

---

## Summary

This refactoring plan transforms the onboarding tool from a basic project analyzer into a comprehensive knowledge extraction system. The key improvements are:

1. **Modular analyzer architecture** - Each aspect analyzed separately
2. **Memory generation** - Automatic creation of agent-readable memories
3. **Markdown output** - Human and agent-friendly format
4. **Full multiplatform coverage** - Kotlin + Swift/iOS analysis
5. **Selective regeneration** - Update specific memories on demand
6. **Extensible design** - Easy to add new analyzers/generators
