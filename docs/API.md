# Kortex MCP Server API Documentation

This document describes the MCP tools exposed by the Kortex server.

## Project Tools

### `onboard_project`
Analyzes a KMP/CMP project and initializes the assistant.
- **Arguments**:
  - `project_path` (string): Absolute path to the project root.
- **Returns**: Project configuration including source sets, targets, and dependencies.

### `get_project_info`
Retrieves information about the currently active project.
- **Arguments**:
  - `project_path` (string): Absolute path to the project root.
- **Returns**: Project details (name, type, source sets).

### `list_source_sets`
List project source sets.
- **Arguments**:
  - `project_path` (string): Absolute path to the project root.
- **Returns**: List of source sets.

### `list_targets`
List project targets.
- **Arguments**:
  - `project_path` (string): Absolute path to the project root.
- **Returns**: List of targets.

### `detect_project_type`
Detect project type.
- **Arguments**:
  - `project_path` (string): Absolute path to the project root.
- **Returns**: Project type (KMP, CMP, etc.).

## LSP Tools

### `search_symbols`
Search for symbols across the workspace.
- **Arguments**:
  - `query` (string): The symbol name to search for.
  - `language` (string, optional): Language to search in (default: "kotlin").
- **Returns**: List of matching symbols with locations.

### `goto_definition`
Go to the definition of a symbol.
- **Arguments**:
  - `file` (string): Absolute path to the file.
  - `line` (int): Line number (0-based).
  - `character` (int): Character position (0-based).
  - `language` (string, optional): Language (default: "kotlin").
- **Returns**: Location of the definition.

### `find_references`
Find all references to a symbol.
- **Arguments**:
  - `file` (string): Absolute path to the file.
  - `line` (int): Line number (0-based).
  - `character` (int): Character position (0-based).
  - `include_declaration` (bool, optional): Include declaration (default: True).
  - `language` (string, optional): Language (default: "kotlin").
- **Returns**: List of locations where the symbol is referenced.

## Memory Tools

### `store_memory`
Store a new memory or update an existing one.
- **Arguments**:
  - `category` (string): Memory category (architecture, patterns, preferences, etc.).
  - `title` (string): Short descriptive title.
  - `content` (string): Memory content/description.
  - `tags` (list[string], optional): Tags for filtering.
  - `metadata` (dict, optional): Additional metadata.
  - `memory_id` (string, optional): ID for updating existing memory.
- **Returns**: Success status and memory details.

### `query_memories`
Query memories by content, category, or tags.
- **Arguments**:
  - `query` (string, optional): Text to search for.
  - `category` (string, optional): Filter by category.
  - `tags` (list[string], optional): Filter by tags.
  - `limit` (int, optional): Maximum number of results (default: 10).
- **Returns**: Matching memories.

### `list_memories`
List memories.
- **Arguments**:
  - `category` (string, optional): Optional category filter.
- **Returns**: List of memories.

## Editing Tools

### `add_method`
Add a method to a class using LSP-guided insertion.
- **Arguments**:
  - `class_name` (string): Name of the target class.
  - `method_signature` (string): Method signature.
  - `method_body` (string): Method implementation code.
  - `file_path` (string, optional): Optional file path.
  - `language` (string, optional): Language (default: "kotlin").
- **Returns**: Result details.

### `rename_symbol`
Rename a symbol and all its references using LSP.
- **Arguments**:
  - `file` (string): File path containing the symbol.
  - `line` (int): Line number (0-based).
  - `character` (int): Character position (0-based).
  - `new_name` (string): New name for the symbol.
  - `language` (string, optional): Language (default: "kotlin").
- **Returns**: Rename results.

### `validate_expect_actual_consistency`
Validate that expect/actual pairs are consistent.
- **Arguments**:
  - `symbol_name` (string): Name of the expect/actual symbol.
- **Returns**: Validation results.

## Elicitation Tools

### `ask_open_ended`
Request information from user in natural language.
- **Arguments**:
  - `question` (string): Question to ask.
- **Returns**: User response.

### `ask_single_select`
Ask user to select one option from provided choices.
- **Arguments**:
  - `question` (string): Question to ask.
  - `options` (list[string]): List of options.
- **Returns**: Selected option.

## Planning Tools

### `create_spec`
Create a new specification.
- **Arguments**:
  - `spec_id` (string): Unique specification ID.
  - `title` (string): Specification title.
  - `description` (string): High-level description.
  - `user_stories` (list[dict], optional): User stories.
  - `requirements` (list[dict], optional): Requirements.
  - `open_questions` (list[string], optional): Open questions.
- **Returns**: Creation result.

### `refine_spec`
Refine an existing specification.
- **Arguments**:
  - `spec_id` (string): Specification ID.
  - `description` (string, optional): Updated description.
  - `user_stories` (list[dict], optional): User stories to add.
  - `requirements` (list[dict], optional): Requirements to add.
  - `open_questions` (list[string], optional): Questions to add.
- **Returns**: Refinement result.

### `generate_template`
Generate a SpecKit-compliant specification template.
- **Arguments**:
  - `spec_id` (string): Specification ID.
  - `title` (string): Specification title.
  - `sections` (list[string], optional): Sections to include.
  - `platform_sections` (dict, optional): Platform-specific sections.
  - `save_to_disk` (bool, optional): Save to disk (default: False).
- **Returns**: Generated template.

### `detect_dependencies`
Detect dependencies between specifications.
- **Arguments**:
  - `spec_id` (string): Specification ID.
- **Returns**: Dependency detection results.

### `generate_tasks`
Generate actionable tasks from a specification.
- **Arguments**:
  - `spec_id` (string): Specification ID.
  - `save_to_disk` (bool, optional): Save tasks.md (default: False).
- **Returns**: Task generation results.
