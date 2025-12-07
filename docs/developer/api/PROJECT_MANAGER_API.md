# ProjectManager API Reference

**Module**: `extract_transform_platform.services.project_manager`
**Version**: 0.1.0
**Status**: Production-ready (95% test coverage)
**Ticket**: 1M-449 (T7: Implement ProjectManager Service)

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Methods](#api-methods)
  - [create_project](#create_project)
  - [get_project](#get_project)
  - [list_projects](#list_projects)
  - [delete_project](#delete_project)
  - [validate_project](#validate_project)
  - [get_project_info](#get_project_info)
- [Data Classes](#data-classes)
  - [ProjectInfo](#projectinfo)
  - [ValidationResult](#validationresult)
- [Error Classes](#error-classes)
  - [ProjectNotFoundError](#projectnotfounderror)
  - [ProjectAlreadyExistsError](#projectalreadyexistserror)
  - [InvalidConfigError](#invalidconfigerror)
- [Usage Patterns](#usage-patterns)
- [Configuration](#configuration)
- [Performance](#performance)
- [Best Practices](#best-practices)

---

## Overview

The **ProjectManager** service provides a complete lifecycle management system for projects with CRUD (Create, Read, Update, Delete) operations. It abstracts file-system backed storage with in-memory caching for optimal performance.

### Key Features

- **Project Lifecycle Management**: Complete CRUD operations
- **File-Based Storage**: Projects stored as directories with `project.yaml`
- **In-Memory Caching**: Dict cache for fast repeated access with automatic invalidation
- **Environment Override**: `EDGAR_ARTIFACTS_DIR` for external storage
- **Async API**: Future-proof for non-blocking I/O operations
- **Comprehensive Validation**: Uses `ProjectConfig.validate_comprehensive()`
- **Error Handling**: Graceful handling of malformed configurations
- **Performance Optimized**: <100ms for 100 projects (cached), >80% cache hit rate

### Design Patterns

- **Repository Pattern**: Abstracts project storage from business logic
- **Cache-Aside Pattern**: In-memory cache with lazy loading
- **Factory Pattern**: Template-based project creation (future enhancement)

### Code Reuse

- **ProjectConfig model**: 100% reuse from platform models
- **CompanyService patterns**: 70% reuse (file loading, caching)
- **CLI command patterns**: 50% reuse (directory management, validation)
- **Error handling**: 90% reuse (structlog, exception patterns)

---

## Installation

```python
# Import the ProjectManager service
from extract_transform_platform.services.project_manager import ProjectManager

# Import data classes
from extract_transform_platform.services.project_manager import (
    ProjectInfo,
    ValidationResult
)

# Import exception classes
from extract_transform_platform.services.project_manager import (
    ProjectNotFoundError,
    ProjectAlreadyExistsError,
    InvalidConfigError
)
```

**Requirements**:
- Python 3.11+
- `pyyaml` (for YAML configuration files)
- `pydantic` (for configuration validation)
- `structlog` (for structured logging)

---

## Quick Start

**5-minute example** demonstrating the core functionality:

```python
import asyncio
from extract_transform_platform.services.project_manager import ProjectManager

async def main():
    # Initialize manager (uses default directory)
    manager = ProjectManager()

    # Create a new project
    project = await manager.create_project("my_api", template="weather")
    print(f"✅ Created: {project.name} at {project.path}")

    # List all projects
    projects = await manager.list_projects()
    for p in projects:
        print(f"📁 {p.name}: {p.metadata.get('description', 'No description')}")

    # Get specific project
    project = await manager.get_project("my_api")
    if project:
        print(f"📂 Found project: {project.name}")

    # Validate project
    result = await manager.validate_project("my_api")
    if result.is_valid:
        print("✅ Project is valid")
    else:
        print(f"❌ Errors: {result.errors}")

    # Delete project (cleanup)
    success = await manager.delete_project("my_api")
    if success:
        print("🗑️ Project deleted")

# Run the example
asyncio.run(main())
```

**Expected Output**:
```
✅ Created: my_api at /path/to/projects/my_api
📁 my_api: No description
📂 Found project: my_api
✅ Project is valid
🗑️ Project deleted
```

---

## API Methods

### create_project

Create a new project from template with directory structure and configuration file.

#### Signature

```python
async def create_project(
    self,
    name: str,
    template: Optional[str] = None
) -> ProjectInfo
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Project name (alphanumeric, underscores, hyphens only) |
| `template` | `str` | No | Template name (default: "minimal", future enhancement) |

#### Returns

`ProjectInfo` - Information about the created project

#### Raises

| Exception | When | Description |
|-----------|------|-------------|
| `ValueError` | Invalid name | Name contains invalid characters or is empty |
| `ProjectAlreadyExistsError` | Duplicate | Project with same name already exists |

#### Example

```python
# Create project with default template
project = await manager.create_project("weather_api")
print(f"Created at: {project.path}")

# Create project with specific template (future)
project = await manager.create_project("invoice_extract", template="pdf")

# Verify directory structure
assert (project.path / "examples").exists()
assert (project.path / "src").exists()
assert (project.path / "tests").exists()
assert (project.path / "output").exists()
assert (project.path / "project.yaml").exists()
```

#### Directory Structure Created

```
projects/my_api/
├── project.yaml         # Configuration file
├── examples/            # Example transformations (input/output pairs)
├── src/                 # Generated code
├── tests/               # Generated tests
└── output/              # Extraction results
```

#### Configuration File Created

The `project.yaml` file contains minimal configuration:

```yaml
project:
  name: my_api
  description: ""
  version: 1.0.0
  created: "2025-11-30T12:00:00"
  updated: "2025-11-30T12:00:00"

data_sources:
  - type: api
    name: example_api
    endpoint: https://api.example.com

output:
  formats:
    - type: json
      path: output/data.json
```

---

### get_project

Get project information by name from cache or filesystem.

#### Signature

```python
async def get_project(self, name: str) -> Optional[ProjectInfo]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Project name to retrieve |

#### Returns

- `ProjectInfo` - Project information if found
- `None` - If project does not exist

#### Example

```python
# Get existing project
project = await manager.get_project("weather_api")
if project:
    print(f"Found: {project.name}")
    print(f"Path: {project.path}")
    print(f"Valid: {project.is_valid}")
    print(f"Created: {project.created_at}")
    print(f"Modified: {project.modified_at}")
else:
    print("Project not found")

# Access project metadata
description = project.metadata.get("description", "")
version = project.metadata.get("version", "1.0.0")
tags = project.metadata.get("tags", [])
```

#### Performance

- **Cached access**: <10ms
- **Cache miss**: <100ms (loads all projects)
- **Cache hit rate**: >80% for repeated operations

---

### list_projects

List all projects in the projects directory, sorted by name.

#### Signature

```python
async def list_projects(self) -> List[ProjectInfo]
```

#### Returns

`List[ProjectInfo]` - List of all projects, sorted alphabetically by name

#### Example

```python
# List all projects
projects = await manager.list_projects()

print(f"Total projects: {len(projects)}")
for p in projects:
    print(f"- {p.name}: {p.metadata.get('description')}")

# Filter by validity
valid_projects = [p for p in projects if p.is_valid]
invalid_projects = [p for p in projects if not p.is_valid]

# Filter by tags
tagged_projects = [
    p for p in projects
    if "production" in p.metadata.get("tags", [])
]

# Sort by modified date
recent_projects = sorted(
    projects,
    key=lambda p: p.modified_at or p.created_at,
    reverse=True
)
```

#### Performance

- **Empty directory**: <10ms
- **100 projects (cached)**: <100ms
- **100 projects (uncached)**: <500ms

---

### delete_project

Delete a project and all its contents from the filesystem.

#### Signature

```python
async def delete_project(self, name: str) -> bool
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Project name to delete |

#### Returns

- `True` - Project successfully deleted
- `False` - Project not found

#### Raises

| Exception | When | Description |
|-----------|------|-------------|
| `OSError` | Filesystem error | Permissions, disk errors, etc. |

#### Example

```python
# Delete a project
success = await manager.delete_project("old_project")
if success:
    print("✅ Project deleted successfully")
else:
    print("❌ Project not found")

# Verify deletion
project = await manager.get_project("old_project")
assert project is None  # Project no longer exists

# Safe deletion with error handling
try:
    await manager.delete_project("protected_project")
except OSError as e:
    print(f"❌ Could not delete: {e}")
```

#### Side Effects

- **Invalidates cache**: Forces next `list_projects()` to reload
- **Permanent deletion**: Cannot be undone (no trash/recycle bin)
- **Recursive deletion**: Removes all subdirectories and files

---

### validate_project

Perform comprehensive validation of project configuration and structure.

#### Signature

```python
async def validate_project(self, name: str) -> ValidationResult
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Project name to validate |

#### Returns

`ValidationResult` - Validation result with errors, warnings, recommendations

#### Validation Checks

1. **Project Existence**: Verify project directory exists
2. **YAML Syntax**: Validate `project.yaml` syntax
3. **Configuration Schema**: Validate against `ProjectConfig` model
4. **Directory Structure**: Check for required directories
5. **Example Files**: Verify example files exist
6. **Comprehensive Validation**: Run `ProjectConfig.validate_comprehensive()`

#### Example

```python
# Validate project
result = await manager.validate_project("my_api")

# Check validation status
if result.is_valid:
    print("✅ Project is valid")
else:
    print(f"❌ Project has {len(result.errors)} errors")

# Display errors
if result.has_errors:
    print("Errors:")
    for error in result.errors:
        print(f"  - {error}")

# Display warnings
if result.has_warnings:
    print("Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")

# Display recommendations
if result.recommendations:
    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")

# Serialize for logging/storage
result_dict = result.to_dict()
```

#### Example Output

```python
ValidationResult(
    project_name="my_api",
    is_valid=True,
    errors=[],
    warnings=[
        "Missing directory: examples/",
        "No example files found in examples/"
    ],
    recommendations=[
        "Add at least 2-3 example transformations",
        "Consider adding project description"
    ]
)
```

---

### get_project_info

Get project information (alias for `get_project`). Provided for API consistency.

#### Signature

```python
async def get_project_info(self, name: str) -> Optional[ProjectInfo]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Project name to retrieve |

#### Returns

- `ProjectInfo` - Project information if found
- `None` - If project does not exist

#### Example

```python
# Identical behavior to get_project()
project = await manager.get_project_info("my_api")
```

---

## Data Classes

### ProjectInfo

Lightweight project information for listing and caching.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Project name (unique identifier) |
| `path` | `Path` | Absolute path to project directory |
| `config` | `Optional[ProjectConfig]` | Full project configuration (lazy loaded) |
| `exists` | `bool` | Whether project directory exists |
| `is_valid` | `bool` | Whether project configuration is valid |
| `created_at` | `Optional[datetime]` | Project creation timestamp |
| `modified_at` | `Optional[datetime]` | Last modification timestamp |
| `metadata` | `Dict[str, Any]` | Additional project metadata (description, version, tags) |

#### Methods

##### from_config

Create `ProjectInfo` from `ProjectConfig`.

```python
@classmethod
def from_config(cls, config: ProjectConfig, path: Path) -> "ProjectInfo"
```

**Example**:
```python
config = ProjectConfig.from_yaml(Path("project.yaml"))
info = ProjectInfo.from_config(config, Path("my_project"))
```

##### to_dict

Convert to dictionary for serialization.

```python
def to_dict(self) -> Dict[str, Any]
```

**Example**:
```python
info_dict = project_info.to_dict()
# {
#     "name": "my_project",
#     "path": "/projects/my_project",
#     "exists": True,
#     "is_valid": True,
#     "created_at": "2025-11-30T12:00:00",
#     "modified_at": "2025-11-30T12:30:00",
#     "metadata": {
#         "description": "My project",
#         "version": "1.0.0",
#         "author": "User",
#         "tags": ["api", "weather"]
#     }
# }
```

---

### ValidationResult

Result of project validation with errors, warnings, and recommendations.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `project_name` | `str` | Name of validated project |
| `is_valid` | `bool` | Whether project passed validation (no critical errors) |
| `errors` | `List[str]` | List of critical errors (prevent execution) |
| `warnings` | `List[str]` | List of non-critical issues (don't prevent execution) |
| `recommendations` | `List[str]` | List of best practice suggestions |

#### Properties

##### has_errors

Check if validation found critical errors.

```python
@property
def has_errors(self) -> bool
```

##### has_warnings

Check if validation found warnings.

```python
@property
def has_warnings(self) -> bool
```

#### Methods

##### to_dict

Convert to dictionary for serialization.

```python
def to_dict(self) -> Dict[str, Any]
```

**Example**:
```python
result = await manager.validate_project("my_api")

# Check status
if result.has_errors:
    print("Critical errors found")

if result.has_warnings:
    print("Warnings found")

# Serialize
result_dict = result.to_dict()
# {
#     "project_name": "my_api",
#     "is_valid": False,
#     "errors": ["Configuration file not found: project.yaml"],
#     "warnings": [],
#     "recommendations": []
# }
```

---

## Error Classes

### ProjectNotFoundError

Raised when attempting to access a project that does not exist.

```python
class ProjectNotFoundError(Exception):
    """Raised when project does not exist."""
    pass
```

**When Raised**: Future operations that require existing project

**Example**:
```python
try:
    # Future method that requires project existence
    await manager.update_project("nonexistent")
except ProjectNotFoundError as e:
    print(f"Project not found: {e}")
```

---

### ProjectAlreadyExistsError

Raised when attempting to create a project with an existing name.

```python
class ProjectAlreadyExistsError(Exception):
    """Raised when attempting to create project with existing name."""
    pass
```

**When Raised**: `create_project()` when project directory already exists

**Example**:
```python
try:
    await manager.create_project("existing_project")
except ProjectAlreadyExistsError as e:
    print(f"Project already exists: {e}")
```

---

### InvalidConfigError

Raised when project configuration is invalid or malformed.

```python
class InvalidConfigError(Exception):
    """Raised when project configuration is invalid."""
    pass
```

**When Raised**: Future operations that parse configuration

**Example**:
```python
try:
    # Future method that validates config
    await manager.load_config("bad_project")
except InvalidConfigError as e:
    print(f"Invalid configuration: {e}")
```

---

## Usage Patterns

### Pattern 1: Create → Validate → Use

**Common workflow** for new projects:

```python
async def create_and_validate():
    manager = ProjectManager()

    # Step 1: Create project
    project = await manager.create_project("my_api")
    print(f"Created: {project.name}")

    # Step 2: Validate structure
    result = await manager.validate_project("my_api")
    if not result.is_valid:
        print(f"Errors: {result.errors}")
        return None

    # Step 3: Use project
    return project
```

---

### Pattern 2: List → Filter → Process

**Batch operations** on multiple projects:

```python
async def process_all_projects():
    manager = ProjectManager()

    # Get all projects
    projects = await manager.list_projects()

    # Filter valid projects
    valid_projects = [p for p in projects if p.is_valid]

    # Process each project
    for project in valid_projects:
        result = await manager.validate_project(project.name)
        if result.has_warnings:
            print(f"⚠️ {project.name}: {result.warnings}")
```

---

### Pattern 3: Safe Deletion with Confirmation

**Prevent accidental deletion**:

```python
async def safe_delete(project_name: str):
    manager = ProjectManager()

    # Check if project exists
    project = await manager.get_project(project_name)
    if not project:
        print(f"Project '{project_name}' not found")
        return False

    # Confirm deletion
    confirm = input(f"Delete '{project_name}'? [y/N]: ")
    if confirm.lower() != 'y':
        print("Deletion cancelled")
        return False

    # Delete project
    try:
        success = await manager.delete_project(project_name)
        if success:
            print(f"✅ Deleted: {project_name}")
        return success
    except OSError as e:
        print(f"❌ Error: {e}")
        return False
```

---

### Pattern 4: Environment-Aware Initialization

**Support multiple environments**:

```python
import os
from pathlib import Path

def get_project_manager():
    """Get project manager for current environment."""
    env = os.getenv("ENVIRONMENT", "dev")

    if env == "production":
        # Production: external drive
        return ProjectManager(base_dir=Path("/data/projects"))
    elif env == "ci":
        # CI/CD: temporary directory
        return ProjectManager(base_dir=Path("/tmp/projects"))
    else:
        # Development: use default
        return ProjectManager()
```

---

### Pattern 5: Validation Before Operations

**Ensure project health** before expensive operations:

```python
async def run_extraction(project_name: str):
    manager = ProjectManager()

    # Validate before processing
    result = await manager.validate_project(project_name)

    if result.has_errors:
        print(f"❌ Cannot run extraction: {result.errors}")
        return None

    if result.has_warnings:
        print(f"⚠️ Warnings: {result.warnings}")
        # Continue with warnings

    # Run extraction
    print(f"✅ Running extraction for '{project_name}'...")
    # ... extraction logic ...
```

---

## Configuration

### Environment Variables

#### EDGAR_ARTIFACTS_DIR

**Purpose**: Override default projects directory to use external storage

**Format**: Absolute or relative path (supports `~` expansion)

**Default**: `./projects` (in-repo)

**Example**:
```bash
# Use external drive
export EDGAR_ARTIFACTS_DIR=/Volumes/Data/edgar_artifacts

# Use home directory
export EDGAR_ARTIFACTS_DIR=~/edgar_projects

# Use network storage
export EDGAR_ARTIFACTS_DIR=/mnt/network/projects
```

**Python Usage**:
```python
import os
os.environ["EDGAR_ARTIFACTS_DIR"] = "/path/to/artifacts"

# Manager will use: /path/to/artifacts/projects
manager = ProjectManager()
```

---

### Directory Structure

#### With EDGAR_ARTIFACTS_DIR

```
$EDGAR_ARTIFACTS_DIR/
└── projects/                    # ProjectManager base directory
    ├── weather_api/
    │   ├── project.yaml
    │   ├── examples/
    │   ├── src/
    │   ├── tests/
    │   └── output/
    └── invoice_extract/
        ├── project.yaml
        └── ...
```

#### Without EDGAR_ARTIFACTS_DIR (default)

```
./projects/                      # ProjectManager base directory
├── weather_api/
│   ├── project.yaml
│   ├── examples/
│   ├── src/
│   ├── tests/
│   └── output/
└── invoice_extract/
    ├── project.yaml
    └── ...
```

---

## Performance

### Benchmarks

| Operation | First Call | Cached | Notes |
|-----------|-----------|--------|-------|
| **create_project** | <500ms | N/A | Includes file I/O |
| **get_project** | <100ms | <10ms | Cache hit rate >80% |
| **list_projects** (100) | <500ms | <100ms | Sorts by name |
| **delete_project** | <200ms | N/A | Recursive deletion |
| **validate_project** | <300ms | <200ms | Comprehensive checks |

### Caching Behavior

- **Cache Population**: Triggered by first `list_projects()` or `get_project()` call
- **Cache Invalidation**: Automatic on `create_project()` and `delete_project()`
- **Cache Size**: O(n) where n = number of projects
- **Cache Hit Rate**: >80% for typical workflows

### Memory Usage

| Projects | Cache Size | Notes |
|----------|-----------|-------|
| 10 | ~50 KB | Minimal overhead |
| 100 | ~500 KB | Reasonable for all environments |
| 1,000 | ~5 MB | Still acceptable |

---

## Best Practices

### 1. Use Default Directory for Development

```python
# ✅ Good: Simple, portable
manager = ProjectManager()

# ❌ Avoid: Hardcoded paths
manager = ProjectManager(base_dir=Path("/Users/john/projects"))
```

### 2. Use Environment Variable for Production

```bash
# ✅ Good: Configurable via environment
export EDGAR_ARTIFACTS_DIR=/data/edgar_artifacts
```

### 3. Validate Before Operations

```python
# ✅ Good: Validate first
result = await manager.validate_project("my_api")
if result.is_valid:
    # ... proceed with operations ...

# ❌ Avoid: Assume validity
# ... operations without validation ...
```

### 4. Handle Errors Gracefully

```python
# ✅ Good: Comprehensive error handling
try:
    project = await manager.create_project("new_api")
except ProjectAlreadyExistsError:
    print("Project already exists, using existing")
    project = await manager.get_project("new_api")
except ValueError as e:
    print(f"Invalid project name: {e}")
    return None

# ❌ Avoid: No error handling
project = await manager.create_project("new_api")  # May crash
```

### 5. Use Async/Await Properly

```python
# ✅ Good: Use async/await
async def main():
    manager = ProjectManager()
    projects = await manager.list_projects()

asyncio.run(main())

# ❌ Avoid: Blocking calls (not supported)
manager = ProjectManager()
projects = manager.list_projects()  # Will fail
```

### 6. Clean Up Temporary Projects

```python
# ✅ Good: Clean up after testing
async def test_workflow():
    manager = ProjectManager()
    try:
        project = await manager.create_project("test_project")
        # ... test operations ...
    finally:
        await manager.delete_project("test_project")
```

### 7. Validate Project Names

```python
# ✅ Good: Validate before creation
def is_valid_name(name: str) -> bool:
    return name and name.replace('_', '').replace('-', '').isalnum()

if is_valid_name("my-api"):
    project = await manager.create_project("my-api")

# ❌ Avoid: Invalid characters
# These will raise ValueError:
# - "my api" (spaces)
# - "my@api" (special chars)
# - "my.api" (dots)
```

### 8. Monitor Cache Behavior

```python
# ✅ Good: Log cache misses in production
manager = ProjectManager()
if manager._projects_cache is None:
    logger.info("Cache miss, loading projects from disk")
projects = await manager.list_projects()
```

---

## Related Documentation

- **[Project Management Guide](../guides/PROJECT_MANAGEMENT.md)** - Complete usage guide
- **[Platform API Reference](PLATFORM_API.md)** - Full platform API
- **[ProjectConfig API](../guides/PROJECT_CONFIG.md)** - Configuration reference
- **[Platform Migration Guide](../guides/PLATFORM_MIGRATION.md)** - Migration status

---

**Last Updated**: 2025-11-30
**Status**: Production-ready (45 tests, 95% coverage)
**Ticket**: 1M-449 (T7: Implement ProjectManager Service)
