# External Artifacts Directory Support - Research Analysis

**Date**: 2025-11-29
**Researcher**: Claude (Research Agent)
**Status**: Requirements Analysis Complete
**Classification**: Actionable (Implementation Required)

---

## Executive Summary

This research analyzes requirements for implementing external artifacts directory support in the EDGAR platform, enabling users to store projects and outputs outside the repository (e.g., `~/edgar_projects/`) instead of in-repo `projects/` and `output/` directories.

**Key Findings**:
- ✅ Platform already has centralized configuration via `AppSettings` (Pydantic model)
- ✅ Environment variable pattern exists (`EDGAR_TEMPLATES_DIR` precedent)
- ✅ Services use dependency injection for paths (easy to modify)
- ⚠️ Hardcoded "projects" default in CLI commands (4 occurrences)
- ⚠️ Project-level `output/` subdirectories created during project creation

**Recommendation**: Implement `EDGAR_ARTIFACTS_DIR` environment variable with graceful fallback to in-repo defaults. Low complexity, high user value.

---

## 1. Current Directory Usage Analysis

### 1.1 Primary Directories

| Directory | Purpose | Current Location | References |
|-----------|---------|------------------|------------|
| `output/` | Global report outputs (Excel, JSON, CSV) | Repo root | `AppSettings.output_dir` (line 59) |
| `projects/` | Project workspaces (user-created) | Repo root | CLI `--output-dir` default (4 locations) |
| `projects/{name}/output/` | Per-project outputs | Inside each project | Created by `project create` command |
| `data/cache/` | API response cache | Repo root | `CacheSettings.cache_dir` |
| `data/checkpoints/` | Analysis checkpoints | Repo root | `RuntimeConfig.checkpoint_dir` |

### 1.2 Path Reference Breakdown

#### Configuration Layer (`src/edgar_analyzer/config/settings.py`)
```python
class AppSettings(BaseModel):
    output_dir: str = Field(default="output")  # Line 59 - Global outputs
    data_dir: str = Field(default="data")      # Line 58 - Cache & checkpoints
```

**Current Behavior**:
- Paths are relative to current working directory (CWD)
- No environment variable support for `output_dir` or `projects/`
- `ConfigService._ensure_directories()` creates these automatically

#### CLI Layer (`src/edgar_analyzer/cli/commands/project.py`)
```python
# Line 61 - create command
@click.option("--output-dir", default="projects")

# Line 195 - list command
@click.option("--output-dir", default="projects")

# Line 283 - delete command
@click.option("--output-dir", default="projects")

# Line 339 - validate command
@click.option("--output-dir", default="projects")
```

**Current Behavior**:
- Hardcoded `"projects"` default in 4 CLI commands
- Users can override via `--output-dir` flag, but not via environment variable
- Project creation (`line 124`): Creates `{project}/output/` subdirectory

#### Service Layer
**Report Services** (`report_service.py`, `enhanced_report_service.py`, `checkpoint_report_service.py`):
```python
self._output_dir = Path(config.settings.output_dir)  # From AppSettings
output_path = self._output_dir / filepath
```

**Code Generator** (`code_generator.py`):
```python
project_dir = self.base_dir / project_name  # base_dir passed to __init__
```

**Current Behavior**:
- Services rely on injected configuration
- No hardcoded paths in service layer ✅
- Easy to modify via configuration changes

### 1.3 Environment Variable Precedent

**Existing Pattern** (`src/edgar_analyzer/cli/commands/project.py`, line 31):
```python
def get_templates_dir() -> Path:
    if env_path := os.getenv("EDGAR_TEMPLATES_DIR"):
        return Path(env_path)
    return Path(__file__).parent.parent.parent.parent.parent / "templates"
```

**Pattern**: Check environment variable → Fallback to default
**Usage**: Currently used for templates directory (testing override)

---

## 2. Current Path Handling Patterns

### 2.1 Configuration Loading Flow

```
1. AppSettings (Pydantic) → Defaults: output="output", data="data"
2. ConfigService.__init__() → Loads AppSettings
3. ConfigService._ensure_directories() → Creates directories
4. Services injected with ConfigService → Access via config.settings.output_dir
```

### 2.2 Path Resolution

| Component | Resolution Method | Example |
|-----------|------------------|---------|
| Global outputs | `Path(config.settings.output_dir)` | `output/report.xlsx` |
| Projects root | CLI `--output-dir` parameter | `projects/my_project/` |
| Per-project output | `{project_path}/output/` | `projects/weather_api/output/data.json` |
| Cache | `Path(config.cache.cache_dir)` | `data/cache/response.json` |
| Checkpoints | `Path(config.runtime.checkpoint_dir)` | `data/checkpoints/checkpoint.json` |

**Key Insight**: Services use relative paths from config, CLI uses parameter defaults.

### 2.3 Directory Creation Timing

1. **App Startup** (`ConfigService._ensure_directories()`):
   - Creates `output/`, `data/cache/`, `data/checkpoints/`, `logs/`
   - Happens before any user commands

2. **Project Creation** (`project create` command):
   - Creates `projects/{name}/` (if doesn't exist)
   - Creates subdirectories: `examples/`, `src/`, `tests/`, `output/`

3. **Report Generation** (Service layer):
   - Uses pre-created `output/` directory
   - Writes directly: `self._output_dir / filename`

---

## 3. External Directory Support Design

### 3.1 Environment Variable Approach

**Primary Variable**: `EDGAR_ARTIFACTS_DIR`

**Behavior**:
```bash
# If set: All artifacts go to external directory
export EDGAR_ARTIFACTS_DIR=~/edgar_projects
# Structure:
# ~/edgar_projects/
#   ├── output/          # Global reports
#   ├── projects/        # User projects
#   ├── cache/           # API cache (optional)
#   └── checkpoints/     # Analysis checkpoints (optional)

# If not set: Use in-repo defaults (backward compatible)
# project-root/
#   ├── output/
#   ├── projects/
#   └── data/
#       ├── cache/
#       └── checkpoints/
```

**Rationale**:
- Single variable controls all artifact storage
- Clean separation: Code (repo) vs. Data (external)
- Easy to set globally (`~/.bashrc`) or per-session

### 3.2 Alternative: Granular Variables

**Optional Enhancement** (Phase 2):
```bash
EDGAR_PROJECTS_DIR=~/my_projects        # Override projects/ only
EDGAR_OUTPUT_DIR=~/reports              # Override output/ only
EDGAR_CACHE_DIR=/tmp/edgar_cache        # Override cache/ only
```

**Trade-offs**:
- ✅ Maximum flexibility
- ❌ Increased complexity
- ❌ Multiple variables to document

**Recommendation**: Start with `EDGAR_ARTIFACTS_DIR`, add granular variables if users request.

### 3.3 Fallback Behavior Matrix

| Scenario | EDGAR_ARTIFACTS_DIR | Behavior |
|----------|---------------------|----------|
| Not set | (undefined) | Use in-repo defaults (`output/`, `projects/`) |
| Set to directory | `~/edgar_projects` | Use external directory with structure |
| Set but doesn't exist | `~/missing` | Create directory + subdirectories (with user warning) |
| Set to invalid path | `/root/no_perms` | Error: "Cannot create artifacts directory" → Exit |

### 3.4 Directory Structure in External Location

When `EDGAR_ARTIFACTS_DIR` is set:
```
$EDGAR_ARTIFACTS_DIR/
├── output/                  # Global reports (Excel, JSON, CSV)
│   ├── enhanced_fortune500_analysis_2023.xlsx
│   ├── checkpoint_analysis_2023_abc123.xlsx
│   └── quality_test_2023.xlsx
├── projects/                # User-created project workspaces
│   ├── weather_api/
│   │   ├── project.yaml
│   │   ├── examples/
│   │   ├── src/
│   │   ├── tests/
│   │   └── output/          # Per-project outputs
│   ├── employee_roster/
│   └── invoice_transform/
├── cache/                   # API response cache (optional)
│   └── edgar_api/
│       └── response_*.json
└── checkpoints/             # Analysis checkpoints (optional)
    └── checkpoint_*.json
```

**Notes**:
- Maintains same structure as in-repo layout
- `cache/` and `checkpoints/` optional (can stay in-repo if user prefers)
- Project-level `output/` subdirectories preserved

---

## 4. Required Changes

### 4.1 Configuration Layer

**File**: `src/edgar_analyzer/config/settings.py`

**Changes**:
1. Add `artifacts_base_dir` field to `AppSettings`
2. Update `_ensure_directories()` to use artifacts base
3. Add environment variable loader

**Implementation**:
```python
class AppSettings(BaseModel):
    # NEW: Base directory for all artifacts (from env var)
    artifacts_base_dir: Optional[str] = Field(
        default=None,
        description="Base directory for artifacts (env: EDGAR_ARTIFACTS_DIR)"
    )

    # MODIFIED: Relative to artifacts_base_dir if set
    data_dir: str = Field(default="data")
    output_dir: str = Field(default="output")

    @classmethod
    def from_environment(cls) -> "AppSettings":
        """Load settings from environment variables."""
        artifacts_base = os.getenv("EDGAR_ARTIFACTS_DIR")
        return cls(artifacts_base_dir=artifacts_base)

    def get_absolute_path(self, relative_path: str) -> Path:
        """Resolve absolute path for artifact directory."""
        if self.artifacts_base_dir:
            return Path(self.artifacts_base_dir) / relative_path
        return Path(relative_path)  # CWD-relative (legacy)

class ConfigService:
    def __init__(self, settings: Optional[AppSettings] = None):
        # Use environment-aware settings by default
        self._settings = settings or AppSettings.from_environment()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        base = self._settings.artifacts_base_dir or "."

        # Warn user if creating external directory
        if self._settings.artifacts_base_dir:
            base_path = Path(base)
            if not base_path.exists():
                logger.warning(
                    f"Creating external artifacts directory: {base_path}"
                )

        directories = [
            self._settings.get_absolute_path(self._settings.data_dir),
            self._settings.get_absolute_path(self._settings.output_dir),
            self._settings.get_absolute_path(self._settings.cache.cache_dir),
            # ... etc
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
```

**Impact**: Central change, affects all services via dependency injection.

### 4.2 CLI Layer

**File**: `src/edgar_analyzer/cli/commands/project.py`

**Changes**:
1. Update `--output-dir` default from hardcoded `"projects"` to environment-aware
2. Add helper function `get_projects_dir()` (similar to `get_templates_dir()`)

**Implementation**:
```python
def get_projects_dir() -> Path:
    """Get the projects directory, allowing override via environment variable.

    Returns:
        Path to projects directory (external or in-repo)
    """
    artifacts_base = os.getenv("EDGAR_ARTIFACTS_DIR")
    if artifacts_base:
        return Path(artifacts_base) / "projects"
    return Path("projects")  # In-repo default

@project.command()
@click.argument("name")
@click.option(
    "--output-dir",
    type=click.Path(path_type=str),
    default=None,  # CHANGED: No hardcoded default
    help="Directory to create project in (default: $EDGAR_ARTIFACTS_DIR/projects or ./projects)",
)
def create(name: str, template: str, description: str, output_dir: str):
    # Use get_projects_dir() if output_dir not specified
    output_path = Path(output_dir) if output_dir else get_projects_dir()
    project_path = output_path / name
    # ... rest of implementation
```

**Apply to**:
- `project create` (line 61)
- `project list` (line 195)
- `project delete` (line 283)
- `project validate` (line 339)

**Impact**: CLI respects environment variable, maintains backward compatibility via fallback.

### 4.3 Service Layer

**Files**:
- `src/edgar_analyzer/services/report_service.py`
- `src/edgar_analyzer/services/enhanced_report_service.py`
- `src/edgar_analyzer/services/checkpoint_report_service.py`
- `src/edgar_analyzer/services/sample_report_generator.py`
- `src/edgar_analyzer/validation/quality_reporter.py`

**Changes**: None required! Services use `config.settings.output_dir`, which will automatically resolve to external path via `AppSettings.get_absolute_path()`.

**Validation**:
```python
# Current code (report_service.py, line 32):
self._output_dir = Path(config.settings.output_dir)

# After AppSettings change, this will automatically resolve to:
# - External: $EDGAR_ARTIFACTS_DIR/output
# - In-repo: ./output
```

**Impact**: Zero changes needed (configuration injection handles it).

### 4.4 Code Generator

**File**: `src/edgar_analyzer/services/code_generator.py`

**Current State**:
```python
class CodeGenerator:
    def __init__(self, base_dir: Path = Path("generated")):
        self.base_dir = base_dir
```

**Change Required**: Update callers to pass `get_projects_dir() / "generated"` instead of hardcoded `Path("generated")`.

**Impact**: Low (caller-side change only, service itself is path-agnostic).

### 4.5 Documentation

**Files to Update**:
1. `CLAUDE.md` - Add environment variable to Quick Start
2. `docs/guides/QUICK_START.md` - Add setup instructions
3. `docs/guides/EXCEL_FILE_TRANSFORM.md` - Update project creation examples
4. `docs/guides/PDF_FILE_TRANSFORM.md` - Update project creation examples
5. **NEW**: `docs/guides/EXTERNAL_ARTIFACTS.md` - Complete guide

**New Guide Contents**:
```markdown
# Using External Artifacts Directory

Store all EDGAR platform outputs outside the repository.

## Setup

1. Set environment variable (add to `~/.bashrc` or `~/.zshrc`):
   ```bash
   export EDGAR_ARTIFACTS_DIR=~/edgar_projects
   ```

2. Restart terminal or source profile:
   ```bash
   source ~/.bashrc
   ```

3. Verify:
   ```bash
   echo $EDGAR_ARTIFACTS_DIR
   # Expected: /Users/you/edgar_projects
   ```

4. Run any command (directory created automatically):
   ```bash
   edgar-analyzer project create my-api --template weather
   # Creates: ~/edgar_projects/projects/my-api/
   ```

## Directory Structure

Your external directory will contain:
- `output/` - All generated reports
- `projects/` - Your project workspaces
- `cache/` - API response cache (optional)
- `checkpoints/` - Analysis checkpoints (optional)

## Benefits

- ✅ Clean repository (no large data files in git)
- ✅ Unlimited storage (external disk/drive)
- ✅ Easy backup (backup one directory)
- ✅ Shared across repo clones
- ✅ Environment-specific (dev/prod separation)

## Fallback

If `EDGAR_ARTIFACTS_DIR` is not set, the platform uses in-repo directories:
- `./output/`
- `./projects/`
- `./data/cache/`
- `./data/checkpoints/`
```

---

## 5. Implementation Approach

### 5.1 Phased Rollout

**Phase 1: Core Infrastructure** (1-2 hours)
1. Update `AppSettings` with `artifacts_base_dir` and `from_environment()`
2. Update `ConfigService._ensure_directories()`
3. Add `get_absolute_path()` helper method
4. Add user warning for external directory creation

**Phase 2: CLI Integration** (1 hour)
1. Add `get_projects_dir()` helper function
2. Update 4 project commands to use helper
3. Update `--output-dir` help text

**Phase 3: Testing** (1-2 hours)
1. Unit tests for `AppSettings.get_absolute_path()`
2. Integration tests for CLI commands
3. Test external directory creation
4. Test fallback to in-repo defaults

**Phase 4: Documentation** (1 hour)
1. Create `docs/guides/EXTERNAL_ARTIFACTS.md`
2. Update CLAUDE.md Quick Start
3. Update existing file transform guides

**Total Effort**: 4-6 hours

### 5.2 Backward Compatibility Strategy

**Guarantee**: Existing users (without `EDGAR_ARTIFACTS_DIR`) experience zero changes.

**Compatibility Matrix**:
| User Scenario | Before | After | Status |
|---------------|--------|-------|--------|
| No env var set | Uses `./output`, `./projects` | Uses `./output`, `./projects` | ✅ Identical |
| Env var set | (not supported) | Uses external directory | ✅ New feature |
| `--output-dir` flag | Works | Works (overrides env var) | ✅ Preserved |

**Migration Path**:
```bash
# 1. User currently has in-repo artifacts
ls output/  # Files exist
ls projects/  # Projects exist

# 2. User sets env var
export EDGAR_ARTIFACTS_DIR=~/edgar_projects

# 3. User can move existing files (optional)
mkdir -p ~/edgar_projects
mv output ~/edgar_projects/
mv projects ~/edgar_projects/

# 4. Platform automatically uses external directory
edgar-analyzer project list
# Lists projects from ~/edgar_projects/projects/
```

### 5.3 Error Handling

**Scenario 1**: External directory doesn't exist
```
Action: Create directory + warn user
Log: "Creating external artifacts directory: ~/edgar_projects"
```

**Scenario 2**: External directory not writable
```
Action: Error + exit
Message: "Cannot create artifacts directory: Permission denied at ~/edgar_projects"
Exit code: 1
```

**Scenario 3**: Env var points to file (not directory)
```
Action: Error + exit
Message: "EDGAR_ARTIFACTS_DIR must be a directory, not a file: ~/file.txt"
Exit code: 1
```

**Scenario 4**: Env var is empty string
```
Action: Treat as unset (use in-repo defaults)
Log: "EDGAR_ARTIFACTS_DIR is empty, using in-repo defaults"
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**File**: `tests/unit/config/test_settings.py`

**Tests**:
1. `test_artifacts_base_dir_from_env(monkeypatch)`
   - Set `EDGAR_ARTIFACTS_DIR` → Assert `artifacts_base_dir` is set
2. `test_artifacts_base_dir_not_set(monkeypatch)`
   - Unset env var → Assert `artifacts_base_dir` is `None`
3. `test_get_absolute_path_with_base()`
   - `artifacts_base_dir="/tmp"` → `get_absolute_path("output")` = `/tmp/output`
4. `test_get_absolute_path_without_base()`
   - `artifacts_base_dir=None` → `get_absolute_path("output")` = `./output`
5. `test_ensure_directories_external(tmp_path, monkeypatch)`
   - Set env var to `tmp_path` → Assert directories created in external location

### 6.2 Integration Tests

**File**: `tests/integration/test_external_artifacts.py`

**Tests**:
1. `test_project_create_external_directory(tmp_path, monkeypatch)`
   - Set `EDGAR_ARTIFACTS_DIR` → Create project → Assert in external location
2. `test_project_list_external_directory(tmp_path, monkeypatch)`
   - Create projects in external dir → List → Assert found
3. `test_report_generation_external_output(tmp_path, monkeypatch)`
   - Generate report → Assert saved to `$EDGAR_ARTIFACTS_DIR/output/`
4. `test_fallback_to_in_repo_defaults(monkeypatch)`
   - Unset env var → Create project → Assert in `./projects/`

### 6.3 CLI Tests

**File**: `tests/unit/test_project_command.py`

**Tests**:
1. `test_get_projects_dir_with_env(monkeypatch)`
   - Set env var → Assert returns external path
2. `test_get_projects_dir_without_env(monkeypatch)`
   - Unset env var → Assert returns `Path("projects")`
3. `test_create_project_respects_env(runner, tmp_path, monkeypatch)`
   - Set env var → Run `project create` → Assert project in external dir

### 6.4 Manual Testing Checklist

- [ ] Set `EDGAR_ARTIFACTS_DIR=~/test_artifacts`
- [ ] Run `edgar-analyzer project create test-proj --template minimal`
- [ ] Verify: `~/test_artifacts/projects/test-proj/` exists
- [ ] Run `edgar-analyzer project list`
- [ ] Verify: Lists `test-proj`
- [ ] Generate report: `edgar-analyzer sample-report --limit 1`
- [ ] Verify: Report in `~/test_artifacts/output/`
- [ ] Unset env var: `unset EDGAR_ARTIFACTS_DIR`
- [ ] Run `edgar-analyzer project create in-repo-proj --template minimal`
- [ ] Verify: `./projects/in-repo-proj/` exists
- [ ] Run `edgar-analyzer project list`
- [ ] Verify: Lists both `test-proj` (external) and `in-repo-proj` (in-repo)

---

## 7. Files Requiring Modification

### 7.1 Core Changes (Required)

| File | LOC Changed | Complexity | Priority |
|------|-------------|------------|----------|
| `src/edgar_analyzer/config/settings.py` | +30 | Medium | Critical |
| `src/edgar_analyzer/cli/commands/project.py` | +15 | Low | Critical |

**Total**: ~45 LOC

### 7.2 Documentation (Required)

| File | Type | Priority |
|------|------|----------|
| `docs/guides/EXTERNAL_ARTIFACTS.md` | New file (~200 lines) | Critical |
| `CLAUDE.md` | Update Quick Start section | High |
| `docs/guides/QUICK_START.md` | Add environment setup | High |
| `docs/guides/EXCEL_FILE_TRANSFORM.md` | Update examples | Medium |
| `docs/guides/PDF_FILE_TRANSFORM.md` | Update examples | Medium |

### 7.3 Testing (Required)

| File | Type | Priority |
|------|------|----------|
| `tests/unit/config/test_settings.py` | Unit tests (+5 tests) | Critical |
| `tests/integration/test_external_artifacts.py` | Integration tests (+4 tests) | High |
| `tests/unit/test_project_command.py` | CLI tests (+3 tests) | High |

---

## 8. Acceptance Criteria

### 8.1 Functional Requirements

- ✅ Environment variable `EDGAR_ARTIFACTS_DIR` supported
- ✅ Falls back to in-repo directories if not set
- ✅ All project operations respect external directory
- ✅ All report outputs go to external directory
- ✅ External directory created automatically (with warning)
- ✅ Graceful error handling for invalid paths

### 8.2 Non-Functional Requirements

- ✅ Backward compatible (no breaking changes)
- ✅ Zero changes for existing users (without env var)
- ✅ CLI flags (`--output-dir`) still work (override env var)
- ✅ Clear error messages for invalid configurations
- ✅ Comprehensive documentation

### 8.3 Testing Requirements

- ✅ Unit tests: 80%+ coverage for new code
- ✅ Integration tests: 4+ scenarios
- ✅ Manual testing: All checklist items passed
- ✅ Backward compatibility: Verified with existing projects

---

## 9. Benefits & Trade-offs

### 9.1 Benefits

**User Benefits**:
- ✅ Clean repository (no large data files in git)
- ✅ Unlimited storage (external disk/drive)
- ✅ Easy backup (single directory)
- ✅ Shared artifacts across repo clones
- ✅ Environment-specific separation (dev/prod)

**Developer Benefits**:
- ✅ Centralized configuration (via `AppSettings`)
- ✅ No service layer changes (DI handles it)
- ✅ Follows existing patterns (`EDGAR_TEMPLATES_DIR`)
- ✅ Low complexity (single env var)

### 9.2 Trade-offs

**Minimal Complexity**:
- 🟡 Adds one environment variable to document
- 🟡 Users must understand environment variable concept
- 🟡 Debugging: User may forget where artifacts are stored

**Mitigation**:
- ✅ Clear documentation with examples
- ✅ CLI commands log artifact directory location
- ✅ Add `--show-config` command to display paths

### 9.3 Risks

**Risk 1**: User sets env var but forgets
```
Symptom: "Where are my files?"
Mitigation: Add logging to CLI:
  "Using external artifacts directory: ~/edgar_projects"
```

**Risk 2**: User moves repo but env var still points to old location
```
Symptom: Files not found after repo move
Mitigation: Document in guide: "Update EDGAR_ARTIFACTS_DIR if you move repo"
```

**Risk 3**: Permissions issue in external directory
```
Symptom: "Permission denied" error
Mitigation: Graceful error message with suggested fix:
  "Cannot write to ~/edgar_projects. Check permissions with: ls -ld ~/edgar_projects"
```

---

## 10. Future Enhancements (Out of Scope)

### 10.1 Granular Directory Variables (Phase 2)
```bash
EDGAR_PROJECTS_DIR=~/my_projects
EDGAR_OUTPUT_DIR=~/reports
EDGAR_CACHE_DIR=/tmp/edgar_cache
```

**Complexity**: Medium (3 additional variables)
**User Demand**: Wait for feedback

### 10.2 Configuration File Support
```yaml
# ~/.edgar/config.yaml
artifacts:
  base_dir: ~/edgar_projects
  projects_dir: ~/my_projects  # Override
  output_dir: ~/reports         # Override
```

**Complexity**: Medium (YAML parsing, priority resolution)
**User Demand**: Wait for feedback

### 10.3 CLI Config Command
```bash
edgar-analyzer config set artifacts-dir ~/edgar_projects
edgar-analyzer config show
# Output:
#   Artifacts Directory: ~/edgar_projects
#   Projects Directory: ~/edgar_projects/projects
#   Output Directory: ~/edgar_projects/output
```

**Complexity**: Low (read/write config file)
**User Demand**: Nice-to-have, not critical

---

## 11. Recommendations

### 11.1 Implementation Priority: **HIGH**

**Rationale**:
- Low implementation cost (4-6 hours)
- High user value (clean repo, unlimited storage)
- Aligns with platform vision (general-purpose, production-ready)
- No breaking changes (backward compatible)

### 11.2 Suggested Timeline

**Week 1**:
- Day 1: Implement Phase 1 (Core Infrastructure)
- Day 2: Implement Phase 2 (CLI Integration)
- Day 3: Implement Phase 3 (Testing)
- Day 4: Implement Phase 4 (Documentation)
- Day 5: Code review + refinements

**Week 2**:
- User testing with external directory
- Gather feedback for Phase 2 enhancements

### 11.3 Next Steps

1. **Approval**: Get user approval for `EDGAR_ARTIFACTS_DIR` approach
2. **Create Issue**: Create Linear issue for implementation
3. **Implement**: Follow phased rollout (Phases 1-4)
4. **Test**: Run manual testing checklist
5. **Document**: Complete documentation updates
6. **Release**: Deploy with release notes

---

## 12. Appendix

### 12.1 Code References

**Current Path Handling**:
- `src/edgar_analyzer/config/settings.py` (lines 58-59): `output_dir`, `data_dir` defaults
- `src/edgar_analyzer/cli/commands/project.py` (lines 61, 195, 283, 339): Hardcoded `"projects"` default
- `src/edgar_analyzer/services/report_service.py` (line 32): `self._output_dir = Path(config.settings.output_dir)`

**Environment Variable Precedent**:
- `src/edgar_analyzer/cli/commands/project.py` (line 31): `EDGAR_TEMPLATES_DIR` pattern

**Service Dependency Injection**:
- All report services use `config.settings.output_dir` (no hardcoded paths)

### 12.2 Directory Size Estimates

**Typical Usage**:
- `output/`: 50-500 MB (Excel reports, JSON exports)
- `projects/`: 10-100 MB (user projects, generated code)
- `cache/`: 100-1000 MB (API responses)
- `checkpoints/`: 50-500 MB (analysis checkpoints)

**Total**: 210 MB - 2.1 GB (depends on usage)

**Recommendation**: External directory on separate drive with 10+ GB free space.

### 12.3 Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Project overview with user preferences
- [Excel File Transform Guide](../guides/EXCEL_FILE_TRANSFORM.md) - Project creation workflow
- [PDF File Transform Guide](../guides/PDF_FILE_TRANSFORM.md) - Project creation workflow
- [Quick Start Guide](../guides/QUICK_START.md) - Setup instructions

---

## 13. Research Metadata

**Research Classification**: Actionable (Implementation Required)

**Work Type**: Infrastructure Enhancement (Non-Breaking)

**Estimated Implementation Effort**: 4-6 hours

**User Impact**: High (addresses explicit user preference)

**Technical Complexity**: Low (centralized config, DI pattern, backward compatible)

**Risk Level**: Low (fallback to in-repo defaults, no breaking changes)

**Ticket Integration**: Ready for Linear issue creation under Epic `edgar-e4cb3518b13e`

---

**End of Research Document**
