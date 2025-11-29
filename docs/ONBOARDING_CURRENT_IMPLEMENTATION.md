# Onboarding Tool - Current Implementation Summary

## Overview

The current onboarding functionality in Kortex MCP is designed to analyze Kotlin Multiplatform (KMP) and Compose Multiplatform (CMP) projects, storing project configuration for later retrieval. The implementation is spread across multiple modules with distinct responsibilities.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            MCP Server (server.py)                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │  onboard_project │  │ get_project_info │  │ list_source_sets/etc  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └───────────┬───────────┘  │
└───────────┼──────────────────────┼───────────────────────┼──────────────┘
            │                      │                       │
            ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Project Tools (tools/project_tools.py)               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │  onboard_project │  │ get_project_info │  │  list_xxx_tool funcs  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └───────────────────────┘  │
└───────────┼──────────────────────┼───────────────────────────────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 Analyzers (analyzers/project_analyzer.py)                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  ProjectAnalyzer.analyze() → Project                                │ │
│  │    ├── _find_build_files()                                          │ │
│  │    ├── _detect_project_type()                                       │ │
│  │    ├── _extract_project_name()                                      │ │
│  │    └── _extract_versions()                                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────────┬─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Gradle Parser (utils/gradle_parser.py)                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  GradleParser.parse() → {plugins, source_sets, targets, deps}      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Storage (storage/project_store.py)                    │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  ProjectStore.save/load() → .kortex/project.json                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. MCP Tools (server.py)

The server exposes the following MCP tools for onboarding:

| Tool | Description | Returns |
|------|-------------|---------|
| `onboard_project` | Main onboarding entry point | Success status, project summary |
| `get_project_info` | Get detailed project information | Full project details |
| `list_source_sets` | List project source sets | Source set names and types |
| `list_targets` | List build targets | Target platforms |
| `detect_project_type` | Quick project type detection | KMP/CMP/UNKNOWN |

### 2. Project Tools (tools/project_tools.py)

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `onboard_project(project_path)` | Analyzes project, stores config to `.kortex/project.json` |
| `get_project_info(project_path)` | Retrieves info (auto-onboards if not found) |
| `start_lsp_servers(project_path)` | Initializes language servers based on project |
| `onboard_project_tool()` | MCP wrapper returning JSON |
| `get_project_info_tool()` | MCP wrapper returning JSON |
| `list_source_sets_tool()` | MCP wrapper for source sets |
| `list_targets_tool()` | MCP wrapper for targets |
| `detect_project_type_tool()` | MCP wrapper for type detection |

**Onboarding Flow:**
```python
async def onboard_project(project_path: str) -> dict:
    1. Validate directory exists
    2. Call analyze_project() 
    3. Store result via ProjectStore.save()
    4. Return summary {success, name, type, source_sets, targets}
```

### 3. Project Analyzer (analyzers/project_analyzer.py)

**Class: `ProjectAnalyzer`**

Responsible for analyzing KMP/CMP project structure by parsing Gradle build files.

| Method | Description |
|--------|-------------|
| `analyze()` | Main entry - returns `Project` instance |
| `_find_build_files()` | Finds all `build.gradle.kts` files recursively |
| `_find_root_build_file()` | Identifies the root build file |
| `_detect_project_type()` | Detects KMP vs CMP from plugins |
| `_extract_project_name()` | Gets name from `settings.gradle.kts` |
| `_extract_versions()` | Extracts Kotlin/Compose versions |

**Convenience Functions:**
- `analyze_project(path)` - Async wrapper
- `detect_project_type(path)` - Quick sync detection
- `is_kmp_project(path)` / `is_cmp_project(path)` - Boolean checks

### 4. KMP Analyzer (analyzers/kmp_analyzer.py)

**Class: `KMPAnalyzer`**

Specialized analyzer for KMP-specific features.

| Method | Description |
|--------|-------------|
| `find_expect_declarations()` | Finds `expect` declarations in commonMain |
| `find_actual_implementations()` | Finds `actual` implementations across platforms |
| `find_expect_actual_pairs()` | Matches expect with actuals |
| `validate_expect_actual_pair()` | Validates consistency |
| `find_missing_actuals()` | Lists source sets missing implementations |
| `get_source_set_from_path()` | Identifies source set from file path |
| `detect_indentation_style()` | Detects code style settings |

**Note:** KMPAnalyzer is NOT currently integrated into the onboarding flow.

### 5. Gradle Parser (utils/gradle_parser.py)

**Class: `GradleParser`**

Regex-based parser for `build.gradle.kts` files.

| Method | Description |
|--------|-------------|
| `parse()` | Returns `{plugins, source_sets, targets, dependencies}` |
| `_extract_plugins()` | Extracts plugin declarations |
| `_extract_source_sets()` | Extracts source set configurations |
| `_extract_targets()` | Extracts build targets |
| `_extract_all_dependencies()` | Extracts dependencies |

### 6. Project Store (storage/project_store.py)

**Class: `ProjectStore`**

Handles persistence of project configuration.

| Method | Description |
|--------|-------------|
| `save(project)` | Saves to `.kortex/project.json` |
| `load()` | Loads from `.kortex/project.json` |
| `exists()` | Checks if config exists |
| `delete()` | Removes config file |
| `update(fields)` | Updates specific fields |

### 7. Data Models (models/project.py)

```python
@dataclass
class Project:
    name: str
    root_path: str
    project_type: ProjectType  # KMP, CMP, UNKNOWN
    source_sets: dict[str, SourceSet]
    targets: list[Target]
    gradle_version: str | None
    kotlin_version: str | None
    compose_version: str | None
    build_files: list[str]

class ProjectType(Enum):
    KMP = "kmp"
    CMP = "cmp"
    UNKNOWN = "unknown"

@dataclass
class SourceSet:
    name: str
    type: SourceSetType
    source_dirs: list[str]
    resource_dirs: list[str]
    dependencies: list[str]
    depends_on: list[str]

@dataclass
class Target:
    name: str
    platform: str
    source_sets: list[str]
```

---

## Memory System (Separate from Onboarding)

The project has a separate memory system that is NOT integrated with onboarding:

### Memory Tools (tools/memory_tools.py)

| Tool | Description |
|------|-------------|
| `store_memory` | Create/update a memory |
| `query_memories` | Search memories |
| `list_memories` | List all memories |
| `get_memory` | Get specific memory by ID |
| `get_memory_stats` | Get statistics |

### Memory Storage (storage/memory_store.py)

- Stores memories as JSON files in `.kortex/memories/`
- Each memory is a separate file: `{memory_id}.json`
- Supports categories: ARCHITECTURE, PATTERNS, PREFERENCES, DECISIONS, etc.

### Memory Model (models/memory.py)

```python
@dataclass
class Memory:
    id: str
    category: MemoryCategory
    title: str
    content: str
    tags: list[str]
    created_at: datetime
    last_accessed: datetime
    access_count: int
    metadata: dict[str, Any]
```

---

## Current Onboarding Output

When `onboard_project` is called, it produces:

**Stored in `.kortex/project.json`:**
```json
{
  "name": "sample-project",
  "root_path": "/path/to/project",
  "project_type": "kmp",
  "source_sets": {
    "commonMain": {
      "name": "commonMain",
      "type": "common",
      "source_dirs": ["src/commonMain/kotlin"],
      "resource_dirs": [],
      "dependencies": ["kotlinx-coroutines-core"],
      "depends_on": []
    }
  },
  "targets": [
    {"name": "android", "platform": "android", "source_sets": ["androidMain"]}
  ],
  "kotlin_version": "1.9.20",
  "compose_version": "1.5.10"
}
```

**Returned to caller:**
```python
{
    "success": True,
    "name": "sample-project",
    "type": "kmp",
    "source_sets": 5,
    "targets": 3,
    "message": "Project onboarded successfully"
}
```

---

## Current Limitations

### 1. Limited Analysis Scope

| Missing Analysis | Impact |
|------------------|--------|
| No architecture detection | Can't identify MVVM, MVI, Clean Architecture |
| No tech stack detection | Can't identify DI frameworks, networking libs |
| No dependency analysis | Just lists, doesn't understand dependency tree |
| No code pattern detection | Can't learn project coding conventions |
| No Swift/iOS analysis | Missing half of multiplatform story |

### 2. No Memory Integration

- Onboarding does NOT create memories
- Project info stored separately from memory system
- Agents must manually create memories from project info
- No automatic knowledge extraction for agent use

### 3. Parsing Limitations

| Limitation | Impact |
|------------|--------|
| Regex-based Gradle parsing | Fails on complex DSL |
| No version catalog support | Missing `libs.versions.toml` |
| No buildSrc support | Missing shared build logic |
| Only `.kts` files | No Groovy support |

### 4. Static Analysis Only

- No Gradle task execution
- No resolved dependency tree
- No effective configuration
- No variant-aware analysis

### 5. Single-Use Design

- No incremental updates
- No change detection
- Must re-onboard entire project
- No partial refresh capability

---

## Test Coverage

### Test Files:
- `tests/test_tools/test_project_tools.py` - Main tool tests
- `tests/test_analyzers/test_project_analyzer.py` - Analyzer tests
- `tests/test_analyzers/test_kmp_analyzer.py` - KMP analyzer tests
- `tests/test_utils/test_gradle_parser.py` - Parser tests

### Test Fixtures:
- `tests/fixtures/sample_kmp_project/` - KMP project fixture
- `tests/fixtures/sample_cmp_project/` - CMP project fixture

### Coverage Areas:
- ✅ Basic onboarding workflow
- ✅ Project type detection
- ✅ Source set extraction
- ✅ Target extraction
- ✅ Error handling
- ✅ Multi-module projects
- ❌ Memory generation (not implemented)
- ❌ Tech stack detection (not implemented)
- ❌ Architecture detection (not implemented)

---

## Code Locations Summary

| Component | Location |
|-----------|----------|
| MCP Server | `src/kortex_mcp/server.py` |
| Project Tools | `src/kortex_mcp/tools/project_tools.py` |
| Project Analyzer | `src/kortex_mcp/analyzers/project_analyzer.py` |
| KMP Analyzer | `src/kortex_mcp/analyzers/kmp_analyzer.py` |
| Gradle Parser | `src/kortex_mcp/utils/gradle_parser.py` |
| Project Store | `src/kortex_mcp/storage/project_store.py` |
| Memory Tools | `src/kortex_mcp/tools/memory_tools.py` |
| Memory Store | `src/kortex_mcp/storage/memory_store.py` |
| Project Models | `src/kortex_mcp/models/project.py` |
| Memory Models | `src/kortex_mcp/models/memory.py` |

---

## Summary

The current onboarding implementation provides basic project structure analysis but lacks:

1. **Deep project understanding** - Only surface-level Gradle parsing
2. **Memory generation** - No automatic memory creation for agents
3. **Tech stack analysis** - No framework/library detection
4. **Architecture patterns** - No design pattern recognition
5. **Swift/iOS analysis** - Limited multiplatform coverage
6. **Agent-ready output** - Data not formatted for agent consumption

The memory system exists separately but is not connected to onboarding, requiring manual memory creation by users or agents.
