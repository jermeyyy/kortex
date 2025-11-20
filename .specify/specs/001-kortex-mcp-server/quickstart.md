# Quickstart Validation Scenarios

This document defines key user journeys to validate the Kortex MCP Server.

## Scenario 1: Project Onboarding

**Goal**: Verify that Kortex can detect and configure a KMP project.

**Steps**:
1. Call `onboard_project` with the path to `tests/fixtures/sample_kmp_project`.
2. Verify the returned project info contains:
   - Name: "sample_kmp_project"
   - Type: "kmp"
   - Source Sets: "commonMain", "androidMain", "iosMain"
   - Targets: "android", "ios"

**Expected Outcome**:
- Tool returns success with correct project metadata.
- Project configuration is stored in `.kortex/project.json`.

## Scenario 2: Symbol Navigation

**Goal**: Verify symbol search and navigation.

**Steps**:
1. Call `search_symbols` with query "Repository".
2. Call `goto_definition` with a file and position from the search results.
3. Call `find_references` on the symbol.

**Expected Outcome**:
- `search_symbols` returns a list of matching symbols with locations.
- `goto_definition` returns the exact location of the definition.
- `find_references` returns a list of usages across the project.

## Scenario 3: Memory System

**Goal**: Verify memory storage and retrieval.

**Steps**:
1. Call `store_memory` with category "preference" and content "Prefer functional programming style".
2. Call `query_memory` with query "style".

**Expected Outcome**:
- `store_memory` returns success.
- `query_memory` returns the stored memory.

## Scenario 4: Planning Mode

**Goal**: Verify specification creation.

**Steps**:
1. Call `create_spec` with title "New Feature" and description "Implement login".
2. Call `refine_spec` to add a user story.

**Expected Outcome**:
- `create_spec` creates a new spec file in `.kortex/specs/`.
- `refine_spec` updates the spec file with the new user story.

## Scenario 5: Cross-Platform Understanding

**Goal**: Verify expect/actual navigation.

**Steps**:
1. Call `navigate_expect_actual` on an `expect` declaration.

**Expected Outcome**:
- Tool returns the locations of corresponding `actual` declarations in platform-specific source sets.
