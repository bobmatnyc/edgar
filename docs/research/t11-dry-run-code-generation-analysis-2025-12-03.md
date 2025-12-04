# T11 Dry-Run Mode Code Generation Analysis

**Research Date**: 2025-12-03
**Ticket**: 1M-453 (T11 - Implement Dry-Run Mode for Code Generation)
**Purpose**: Analyze code generation pipeline to inform dry-run implementation

---

## Executive Summary

The code generation pipeline is well-structured for adding dry-run mode with minimal changes. The `write_files` parameter already exists in `CodeGeneratorService.generate()`, providing 90% of the dry-run functionality. Implementation requires:

1. **CLI Integration** (Primary): Add `--dry-run` flag to trigger `write_files=False`
2. **Enhanced Feedback** (Secondary): Improve dry-run output for user visibility
3. **Test Coverage** (Tertiary): Add dry-run-specific test cases

**Key Finding**: Dry-run mode is already functional via `write_files=False` parameter. The main task is adding CLI interface and improving user feedback.

---

## 1. Code Generation Pipeline Architecture

### 1.1 Entry Point: CodeGeneratorService.generate()

**Location**: `src/extract_transform_platform/services/codegen/code_generator.py:311`

**Method Signature**:
```python
async def generate(
    self,
    examples: List[Dict[str, Any]],
    project_config: ProjectConfig,
    validate: bool = True,
    write_files: bool = True,  # <-- DRY-RUN PARAMETER
    max_retries: int = 3,
    on_progress: Optional[Callable[[GenerationProgress], None]] = None,
) -> GenerationContext
```

**7-Step Pipeline** (T10 - Progress Tracking):
1. Parse examples and extract patterns (ExampleParser)
2. PM mode: Create implementation plan (Sonnet45Agent.plan)
3. Coder mode: Generate code (Sonnet45Agent.code)
4. Validate generated code (CodeValidator) - skippable via `validate=False`
5. Write files to disk (CodeWriter) - **skippable via `write_files=False`**
6. Run tests (pytest) - currently skipped
7. Finalize generation context

**Returns**: `GenerationContext` with:
- `plan: PlanSpec` - PM mode output
- `generated_code: GeneratedCode` - Coder mode output
- `errors: List[str]` - Error messages
- `warnings: List[str]` - Warnings
- `generation_duration_seconds: float` - Total time
- `is_complete: bool` - Success status

---

### 1.2 File Writing Logic

**Location**: `src/extract_transform_platform/services/codegen/code_generator.py:637-670`

**Current Implementation**:
```python
# STEP 5/7: Write generated files
step_start = time.time()
if write_files:
    report_progress(5, "Write generated files to disk", "in_progress")
    logger.info("Step 5/7: Writing files")

    paths = self.writer.write(
        code, project_config.project.name, backup=True
    )
    output_dir = self.writer.base_dir / project_config.project.name

    code.add_metadata("output_paths", {k: str(v) for k, v in paths.items()})

    step_elapsed = time.time() - step_start
    logger.info(
        "Files written",
        files=len(paths),
        directory=str(output_dir),
        elapsed=f"{step_elapsed:.2f}s",
    )
    report_progress(
        5,
        "Write generated files to disk",
        "completed",
        step_elapsed,
        message=f"Wrote {len(paths)} files",
    )
else:
    output_dir = None
    report_progress(
        5,
        "Write generated files to disk",
        "skipped",
        0.0,
        message="File writing disabled",  # <-- DRY-RUN MESSAGE
    )
```

**Key Observations**:
- ✅ `write_files=False` already skips file writing
- ✅ Progress tracking reports "skipped" status
- ✅ Generated code still available in `context.generated_code`
- ❌ Progress message is generic ("File writing disabled")
- ❌ No explicit dry-run output for user visibility

---

### 1.3 CodeWriter Class

**Location**: `src/extract_transform_platform/services/codegen/code_generator.py:177-256`

**Class Structure**:
```python
class CodeWriter:
    """Write generated code to files with safety checks."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize code writer."""
        self.base_dir = base_dir or Path("./generated")

    def write(
        self, code: GeneratedCode, project_name: str, backup: bool = True
    ) -> Dict[str, Path]:
        """Write generated code to files."""
        # Create project directory
        project_dir = self.base_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Write each file
        for name, content in [
            ("extractor", code.extractor_code),
            ("models", code.models_code),
            ("test_extractor", code.tests_code),
        ]:
            file_path = project_dir / f"{name}.py"

            # Backup existing file
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(
                    f".py.bak.{int(datetime.now().timestamp())}"
                )
                file_path.rename(backup_path)

            # Write new file
            with open(file_path, "w") as f:
                f.write(content)

            paths[name] = file_path

        # Write __init__.py
        init_path = project_dir / "__init__.py"
        with open(init_path, "w") as f:
            f.write(f'"""Generated extractor for {project_name}"""\n')
        paths["init"] = init_path

        return paths
```

**Files Written**:
1. `extractor.py` - Main data extractor implementation
2. `models.py` - Pydantic models for data structures
3. `test_extractor.py` - Pytest test suite
4. `__init__.py` - Package initialization

**File Locations**:
- Base directory: `self.writer.base_dir` (default: `./generated`)
- Project directory: `base_dir / project_name`
- Full path example: `./generated/weather_api/extractor.py`

---

## 2. Progress Tracking Integration (T10)

### 2.1 GenerationProgress Dataclass

**Location**: `src/extract_transform_platform/models/plan.py:371-457`

**Structure**:
```python
class GenerationProgress(BaseModel):
    """Progress tracking for code generation pipeline."""

    current_step: int = Field(..., ge=1)
    total_steps: int = Field(..., ge=1)
    step_name: str = Field(...)
    status: str = Field(...)  # "pending", "in_progress", "completed", "failed", "skipped"
    elapsed_time: float = Field(default=0.0, ge=0.0)
    message: Optional[str] = Field(None)

    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage (0.0 to 100.0)."""
        if self.total_steps == 0:
            return 0.0
        completed = (
            self.current_step - 1 if self.status != "completed" else self.current_step
        )
        return (completed / self.total_steps) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if pipeline is complete."""
        return self.current_step == self.total_steps and self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if current step failed."""
        return self.status == "failed"
```

**Status Values**:
- `"pending"` - Step has not started yet
- `"in_progress"` - Step is currently executing
- `"completed"` - Step finished successfully
- `"failed"` - Step failed with error
- `"skipped"` - Step was skipped (e.g., validation disabled, **dry-run mode**)

**Integration Point for Dry-Run**:
- Progress callback already reports "skipped" status when `write_files=False`
- Message field can be enhanced: `"File writing disabled"` → `"Dry-run mode: preview only (no files written)"`

---

### 2.2 Progress Callback Mechanism

**Usage Example** (from tests):
```python
progress_updates: List[GenerationProgress] = []

def on_progress(progress: GenerationProgress):
    progress_updates.append(progress)
    print(f"[{progress.current_step}/{progress.total_steps}] "
          f"{progress.step_name} - {progress.status} "
          f"({progress.progress_percentage:.1f}%)")
    if progress.message:
        print(f"    {progress.message}")

context = await service.generate(
    examples=examples,
    project_config=config,
    write_files=False,  # DRY-RUN
    on_progress=on_progress
)
```

**Output for Dry-Run**:
```
[1/7] Parse examples and extract patterns - in_progress (0.0%)
[1/7] Parse examples and extract patterns - completed (14.3%)
[2/7] PM mode: Create implementation plan - in_progress (14.3%)
[2/7] PM mode: Create implementation plan - completed (28.6%)
[3/7] Coder mode: Generate production code - in_progress (28.6%)
[3/7] Coder mode: Generate production code - completed (42.9%)
    Generated 245 lines of code
[4/7] Validate code quality - in_progress (42.9%)
[4/7] Validate code quality - completed (57.1%)
    Quality score: 0.95
[5/7] Write generated files to disk - skipped (57.1%)
    File writing disabled  # <-- ENHANCE THIS MESSAGE
[6/7] Generate test suite - in_progress (57.1%)
[6/7] Generate test suite - completed (71.4%)
    Tests included in generated code
[7/7] Finalize generation and record metadata - in_progress (71.4%)
[7/7] Finalize generation and record metadata - completed (100.0%)
    Total duration: 4.2s
```

---

## 3. CLI Command Structure

### 3.1 Current CLI Commands

**Location**: `src/edgar_analyzer/cli/commands/project.py`

**Existing Commands**:
```python
@project.command()
def create(name: str, template: str, description: str, output_dir: str):
    """Create a new project."""
    # Uses ProjectManager service

@project.command()
def list(output_dir: str, format: str):
    """List all projects."""
    # Uses ProjectManager service

@project.command()
def delete(name: str, output_dir: str, force: bool):
    """Delete a project."""
    # Uses ProjectManager service

@project.command()
def validate(name: str, output_dir: str, verbose: bool):
    """Validate project configuration."""
    # Uses ProjectManager service
```

**Missing Command**: `generate` (or `generate-code`)

---

### 3.2 Recommended CLI Command

**Add to**: `src/edgar_analyzer/cli/commands/project.py`

**Proposed Implementation**:
```python
@project.command()
@click.argument("name")
@click.option(
    "--output-dir",
    type=click.Path(path_type=str),
    default=None,
    help="Projects directory (default: $EDGAR_ARTIFACTS_DIR/projects or ./projects)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview generated code without writing files (dry-run mode)",
)
@click.option(
    "--no-validate",
    is_flag=True,
    default=False,
    help="Skip code validation (faster, but may produce invalid code)",
)
@click.option(
    "--max-retries",
    type=int,
    default=3,
    help="Maximum retry attempts for validation failures (default: 3)",
)
@click.option(
    "--show-progress",
    is_flag=True,
    default=True,
    help="Show real-time progress updates (default: enabled)",
)
@inject
def generate(
    name: str,
    output_dir: Optional[str],
    dry_run: bool,
    no_validate: bool,
    max_retries: int,
    show_progress: bool,
    project_manager: ProjectManager = Provide[Container.project_manager],
):
    """Generate extraction code from project examples.

    Examples:
        # Standard generation
        $ edgar-analyzer project generate weather_api

        # Dry-run mode (preview only)
        $ edgar-analyzer project generate weather_api --dry-run

        # Skip validation for faster generation
        $ edgar-analyzer project generate weather_api --no-validate

        # Custom output directory
        $ edgar-analyzer project generate weather_api --output-dir /tmp/projects
    """
    console.print(f"\n[bold]Generating code for project:[/bold] {name}\n")

    # Resolve output directory
    if output_dir:
        projects_dir = Path(output_dir)
    else:
        projects_dir = project_manager.projects_dir

    project_path = projects_dir / name

    # Load project
    try:
        project = run_async(project_manager.load_project(name))
    except ProjectNotFoundError:
        console.print(f"[red]Error:[/red] Project '{name}' not found at {project_path}")
        console.print("\nRun: [cyan]edgar-analyzer project list[/cyan] to see available projects")
        raise click.Abort()

    # Dry-run notification
    if dry_run:
        console.print(Panel(
            "[yellow]DRY-RUN MODE[/yellow]\n\n"
            "Code will be generated but NOT written to disk.\n"
            "Use this to preview generated code before committing.",
            title="🔍 Preview Mode",
            border_style="yellow"
        ))

    # Progress callback
    def on_progress(progress: GenerationProgress):
        if show_progress:
            status_emoji = {
                "pending": "⏳",
                "in_progress": "⚙️",
                "completed": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }.get(progress.status, "▶️")

            console.print(
                f"{status_emoji} [{progress.current_step}/{progress.total_steps}] "
                f"{progress.step_name} - [bold]{progress.status.upper()}[/bold] "
                f"({progress.progress_percentage:.1f}%)"
            )
            if progress.message:
                console.print(f"    [dim]{progress.message}[/dim]")

    # Generate code
    try:
        from extract_transform_platform.services.codegen.code_generator import (
            CodeGeneratorService,
        )

        service = CodeGeneratorService(
            output_dir=project_path / "generated"
        )

        context = run_async(
            service.generate(
                examples=project.config.examples,
                project_config=project.config,
                validate=not no_validate,
                write_files=not dry_run,  # <-- DRY-RUN CONTROL
                max_retries=max_retries,
                on_progress=on_progress if show_progress else None,
            )
        )

        # Success
        if context.is_complete:
            console.print(
                f"\n[green]✓[/green] Code generation completed successfully "
                f"({context.generation_duration_seconds:.1f}s)\n"
            )

            # Dry-run summary
            if dry_run:
                console.print(Panel(
                    f"[bold]Generated Code Summary (Preview Only)[/bold]\n\n"
                    f"• Total Lines: [cyan]{context.generated_code.total_lines}[/cyan]\n"
                    f"• Extractor Code: {len(context.generated_code.extractor_code)} chars\n"
                    f"• Models Code: {len(context.generated_code.models_code)} chars\n"
                    f"• Tests Code: {len(context.generated_code.tests_code)} chars\n\n"
                    f"[yellow]No files were written (dry-run mode)[/yellow]\n\n"
                    f"To write files, run:\n"
                    f"  [cyan]edgar-analyzer project generate {name}[/cyan]",
                    title="📋 Generation Preview",
                    border_style="blue"
                ))

                # Optional: Show code snippets
                if context.generated_code:
                    console.print("\n[bold]Extractor Code Preview:[/bold]")
                    # Show first 20 lines
                    lines = context.generated_code.extractor_code.split('\n')[:20]
                    for i, line in enumerate(lines, 1):
                        console.print(f"  {i:3d} | {line}")
                    if len(context.generated_code.extractor_code.split('\n')) > 20:
                        console.print("  ... (truncated)")

            # Standard output
            else:
                output_paths = context.generated_code.metadata.get("output_paths", {})
                console.print("[bold]Generated Files:[/bold]")
                for file_type, file_path in output_paths.items():
                    console.print(f"  • {file_type}: [cyan]{file_path}[/cyan]")

                console.print(
                    f"\n[dim]Next steps:[/dim]\n"
                    f"  1. Review generated code in [cyan]{project_path / 'generated'}[/cyan]\n"
                    f"  2. Run tests: [cyan]pytest {project_path / 'generated'}[/cyan]\n"
                    f"  3. Extract data: [cyan]python {project_path / 'generated' / 'extractor.py'}[/cyan]\n"
                )

        else:
            console.print(f"[red]✗[/red] Code generation failed\n")
            for error in context.errors:
                console.print(f"  • [red]{error}[/red]")

    except Exception as e:
        console.print(f"[red]Error during code generation:[/red] {str(e)}")
        raise
```

**Key Features**:
1. ✅ `--dry-run` flag triggers `write_files=False`
2. ✅ Rich console output with progress tracking
3. ✅ Dry-run summary panel with code statistics
4. ✅ Code preview (first 20 lines of extractor)
5. ✅ Clear distinction between dry-run and standard output
6. ✅ Next steps guidance for both modes

---

## 4. Test Strategy

### 4.1 Existing Test Coverage

**Location**: `tests/unit/services/test_code_generator_progress.py`

**Current Tests** (T10 - Progress Tracking):
- ✅ Progress tracking for successful generation
- ✅ Progress callback invocation at each step
- ✅ Step timing and elapsed time tracking
- ✅ Error handling with rollback
- ✅ Validation skipping (`validate=False`)
- ✅ File writing skipping (`write_files=False`) - **DRY-RUN TEST**
- ✅ Edge cases and error scenarios

**Relevant Test** (Line 450):
```python
async def test_generation_without_progress_callback(
    self,
    temp_output_dir,
    sample_project_config,
    sample_examples,
    sample_parsed_examples,
    sample_plan,
    sample_generated_code,
):
    """Test generation without progress callback (should not fail)."""
    # ... mock setup ...

    service = CodeGeneratorService(output_dir=temp_output_dir)
    context = await service.generate(
        examples=sample_examples,
        project_config=sample_project_config,
        validate=True,
        write_files=True,  # <-- Change to False for dry-run test
        on_progress=None,
    )

    assert context.is_complete
    assert context.generated_code is not None
```

---

### 4.2 Recommended Dry-Run Tests

**Add to**: `tests/unit/services/test_code_generator_progress.py`

**Test Cases**:
```python
class TestDryRunMode:
    """Test dry-run mode (write_files=False)."""

    @pytest.mark.asyncio
    async def test_dry_run_generates_code_without_writing_files(
        self,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that dry-run mode generates code but doesn't write files."""
        progress_updates: List[GenerationProgress] = []

        def on_progress(progress: GenerationProgress):
            progress_updates.append(progress)

        with patch(...):  # Mock dependencies
            service = CodeGeneratorService(output_dir=temp_output_dir)
            context = await service.generate(
                examples=sample_examples,
                project_config=sample_project_config,
                validate=True,
                write_files=False,  # DRY-RUN
                on_progress=on_progress,
            )

        # Verify code was generated
        assert context.is_complete
        assert context.generated_code is not None
        assert context.generated_code.extractor_code
        assert context.generated_code.models_code
        assert context.generated_code.tests_code

        # Verify files were NOT written
        project_dir = temp_output_dir / "test_project"
        assert not project_dir.exists(), "Dry-run should not create project directory"

        # Verify progress tracking
        skipped_step = [p for p in progress_updates if p.status == "skipped"]
        assert len(skipped_step) == 1
        assert skipped_step[0].step_name == "Write generated files to disk"
        assert "File writing disabled" in skipped_step[0].message

    @pytest.mark.asyncio
    async def test_dry_run_with_validation_failure_does_not_rollback(
        self,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that dry-run mode doesn't trigger rollback on failure (no files to delete)."""
        with patch(...):  # Mock validation to fail
            service = CodeGeneratorService(output_dir=temp_output_dir)

            with pytest.raises(ValueError, match="Code validation failed"):
                await service.generate(
                    examples=sample_examples,
                    project_config=sample_project_config,
                    validate=True,
                    write_files=False,  # DRY-RUN
                    max_retries=1,
                )

        # Verify no files were created (no rollback needed)
        project_dir = temp_output_dir / "test_project"
        assert not project_dir.exists()

    @pytest.mark.asyncio
    async def test_dry_run_returns_generated_code_in_context(
        self,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that dry-run mode returns GeneratedCode in context."""
        with patch(...):
            service = CodeGeneratorService(output_dir=temp_output_dir)
            context = await service.generate(
                examples=sample_examples,
                project_config=sample_project_config,
                validate=True,
                write_files=False,  # DRY-RUN
            )

        # Verify GeneratedCode is accessible
        assert context.generated_code is not None
        assert isinstance(context.generated_code.extractor_code, str)
        assert len(context.generated_code.extractor_code) > 0

        # Verify metadata is empty (no output paths)
        output_paths = context.generated_code.metadata.get("output_paths", {})
        assert len(output_paths) == 0, "Dry-run should not record output paths"
```

**Add to**: `tests/integration/test_cli_generate.py` (new file)

**CLI Integration Test**:
```python
import subprocess
import tempfile
from pathlib import Path

def test_cli_generate_dry_run():
    """Test CLI generate command with --dry-run flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        projects_dir = Path(tmpdir) / "projects"
        projects_dir.mkdir()

        # Create test project
        project_path = projects_dir / "test_weather"
        project_path.mkdir()
        (project_path / "project.yaml").write_text(...)  # Sample config

        # Run dry-run
        result = subprocess.run(
            [
                "edgar-analyzer", "project", "generate", "test_weather",
                "--output-dir", str(projects_dir),
                "--dry-run"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "DRY-RUN MODE" in result.stdout
        assert "No files were written" in result.stdout

        # Verify no files created
        generated_dir = project_path / "generated"
        assert not generated_dir.exists()
```

---

## 5. Implementation Recommendations

### 5.1 Priority 1: CLI Command (Required)

**Task**: Add `project generate` command with `--dry-run` flag

**Files to Modify**:
- `src/edgar_analyzer/cli/commands/project.py` - Add `generate()` command

**Implementation Steps**:
1. Copy proposed CLI command implementation (Section 3.2)
2. Add imports: `CodeGeneratorService`, `GenerationProgress`
3. Register command with `@project.command()` decorator
4. Test manually: `edgar-analyzer project generate weather_api --dry-run`

**Estimated Effort**: 2-3 hours

---

### 5.2 Priority 2: Enhanced Dry-Run Feedback (Recommended)

**Task**: Improve progress message for dry-run mode

**Files to Modify**:
- `src/extract_transform_platform/services/codegen/code_generator.py:669`

**Current Code**:
```python
else:
    output_dir = None
    report_progress(
        5,
        "Write generated files to disk",
        "skipped",
        0.0,
        message="File writing disabled",  # <-- GENERIC
    )
```

**Enhanced Code**:
```python
else:
    output_dir = None
    report_progress(
        5,
        "Write generated files to disk",
        "skipped",
        0.0,
        message="Dry-run mode: preview only (no files written)",  # <-- EXPLICIT
    )
```

**Estimated Effort**: 15 minutes

---

### 5.3 Priority 3: Test Coverage (Recommended)

**Task**: Add dry-run-specific test cases

**Files to Create/Modify**:
- `tests/unit/services/test_code_generator_progress.py` - Add `TestDryRunMode` class
- `tests/integration/test_cli_generate.py` - Add CLI integration test

**Test Cases**:
1. Dry-run generates code without writing files
2. Dry-run with validation failure doesn't rollback
3. Dry-run returns GeneratedCode in context
4. CLI `--dry-run` flag works correctly

**Estimated Effort**: 2-3 hours

---

### 5.4 Priority 4: Documentation (Optional)

**Task**: Update user documentation with dry-run examples

**Files to Modify**:
- `docs/guides/CLI_USAGE.md` - Add `project generate` command documentation
- `CLAUDE.md` - Add dry-run workflow to Quick Reference Commands

**Content**:
```markdown
### Generate Code (with Dry-Run)

# Preview generated code without writing files
edgar-analyzer project generate my_project --dry-run

# Generate and write files
edgar-analyzer project generate my_project

# Skip validation for faster generation
edgar-analyzer project generate my_project --no-validate
```

**Estimated Effort**: 1 hour

---

## 6. Key Findings Summary

### 6.1 Code Generation Entry Points

| Component | Location | Line | Purpose |
|-----------|----------|------|---------|
| **CodeGeneratorService.generate()** | `code_generator.py` | 311 | Main entry point with `write_files` parameter |
| **CodeWriter.write()** | `code_generator.py` | 197 | File writing logic (skipped when `write_files=False`) |
| **Step 5 (Write Files)** | `code_generator.py` | 637-670 | Conditional file writing with progress tracking |

---

### 6.2 File Write Locations

| File | Path Template | Example |
|------|---------------|---------|
| **Extractor** | `{base_dir}/{project_name}/extractor.py` | `./generated/weather_api/extractor.py` |
| **Models** | `{base_dir}/{project_name}/models.py` | `./generated/weather_api/models.py` |
| **Tests** | `{base_dir}/{project_name}/test_extractor.py` | `./generated/weather_api/test_extractor.py` |
| **Init** | `{base_dir}/{project_name}/__init__.py` | `./generated/weather_api/__init__.py` |

**Default Base Directory**: `./generated` (configurable via `CodeGeneratorService(output_dir=...)`)

---

### 6.3 Return Values and Structures

**GenerationContext** (returned by `generate()`):
```python
@dataclass
class GenerationContext:
    project_name: str
    num_patterns: int
    num_examples: int
    plan: Optional[PlanSpec]
    generated_code: Optional[GeneratedCode]  # <-- CONTAINS CODE
    generation_timestamp: datetime
    generation_duration_seconds: Optional[float]
    errors: List[str]
    warnings: List[str]

    @property
    def is_complete(self) -> bool:
        return self.plan is not None and self.generated_code is not None
```

**GeneratedCode** (accessed via `context.generated_code`):
```python
@dataclass
class GeneratedCode:
    extractor_code: str  # Complete extractor.py contents
    models_code: str     # Complete models.py contents
    tests_code: str      # Complete test_extractor.py contents
    metadata: Dict[str, Any]  # {"output_paths": {...}, ...}

    @property
    def total_lines(self) -> int:
        return (
            len(self.extractor_code.split('\n')) +
            len(self.models_code.split('\n')) +
            len(self.tests_code.split('\n'))
        )
```

**Dry-Run Access Pattern**:
```python
context = await service.generate(
    examples=examples,
    project_config=config,
    write_files=False  # DRY-RUN
)

# Access generated code (not written to disk)
extractor_code = context.generated_code.extractor_code
models_code = context.generated_code.models_code
tests_code = context.generated_code.tests_code

# Display preview
print(f"Generated {context.generated_code.total_lines} lines of code")
print("\nExtractor Preview:")
print('\n'.join(extractor_code.split('\n')[:20]))
```

---

### 6.4 Progress Tracking Integration

**GenerationProgress Callback**:
```python
def on_progress(progress: GenerationProgress):
    print(f"[{progress.current_step}/{progress.total_steps}] "
          f"{progress.step_name} - {progress.status}")
    if progress.message:
        print(f"    {progress.message}")

context = await service.generate(
    examples=examples,
    project_config=config,
    write_files=False,  # DRY-RUN
    on_progress=on_progress
)
```

**Dry-Run Progress Output**:
- Step 5 status: `"skipped"`
- Step 5 message: `"File writing disabled"` (enhance to `"Dry-run mode: preview only"`)
- Step 5 percentage: Calculated as if step completed (57.1%)

---

### 6.5 Test Patterns

**Mocking Strategy** (from existing tests):
```python
with patch("extract_transform_platform.services.codegen.code_generator.ExampleParser"):
    with patch("extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"):
        with patch("extract_transform_platform.services.codegen.code_generator.CodeValidator"):
            service = CodeGeneratorService(output_dir=temp_output_dir)
            context = await service.generate(
                examples=sample_examples,
                project_config=sample_project_config,
                write_files=False  # DRY-RUN
            )
```

**Assertions for Dry-Run**:
```python
# Code generated
assert context.is_complete
assert context.generated_code is not None

# Files NOT written
project_dir = temp_output_dir / "test_project"
assert not project_dir.exists()

# Progress tracking
skipped_steps = [p for p in progress_updates if p.status == "skipped"]
assert len(skipped_steps) == 1
assert skipped_steps[0].step_name == "Write generated files to disk"
```

---

## 7. Recommended Implementation Approach

### Phase 1: CLI Integration (Day 1, 3 hours)

1. **Add CLI Command** (2 hours)
   - Copy `generate()` command implementation from Section 3.2
   - Add to `src/edgar_analyzer/cli/commands/project.py`
   - Test manually with `--dry-run` flag

2. **Enhance Progress Message** (30 minutes)
   - Update line 669 in `code_generator.py`
   - Change message to: `"Dry-run mode: preview only (no files written)"`

3. **Manual QA** (30 minutes)
   - Test standard mode: `edgar-analyzer project generate weather_api`
   - Test dry-run mode: `edgar-analyzer project generate weather_api --dry-run`
   - Verify progress output and code preview

---

### Phase 2: Test Coverage (Day 2, 3 hours)

1. **Unit Tests** (2 hours)
   - Add `TestDryRunMode` class to `test_code_generator_progress.py`
   - Implement 3 test cases from Section 4.2
   - Run: `pytest tests/unit/services/test_code_generator_progress.py::TestDryRunMode -v`

2. **Integration Tests** (1 hour)
   - Create `tests/integration/test_cli_generate.py`
   - Add CLI dry-run test (Section 4.2)
   - Run: `pytest tests/integration/test_cli_generate.py -v`

---

### Phase 3: Documentation (Day 3, 1 hour)

1. **Update CLI Guide** (30 minutes)
   - Add `project generate` command to `docs/guides/CLI_USAGE.md`
   - Include dry-run examples

2. **Update CLAUDE.md** (30 minutes)
   - Add dry-run workflow to Quick Reference Commands section
   - Update "Common Tasks" with generation examples

---

## 8. Risk Assessment

### Low Risk Areas ✅

1. **Existing Infrastructure**: `write_files=False` parameter already implemented
2. **Progress Tracking**: T10 integration complete and tested
3. **Code Structure**: Clean separation between generation and file writing

### Medium Risk Areas ⚠️

1. **CLI Integration**: New command requires testing with real projects
2. **User Experience**: Dry-run output must be clear and actionable
3. **Error Handling**: Ensure dry-run failures don't trigger rollback

### Mitigation Strategies

1. **Incremental Testing**: Test each phase independently
2. **Manual QA**: Verify user-facing output before finalizing
3. **Rollback Safety**: Confirm dry-run mode doesn't attempt file deletion

---

## 9. Success Criteria

### Functional Requirements ✅

- [ ] CLI command `project generate` accepts `--dry-run` flag
- [ ] Dry-run mode skips file writing (Step 5)
- [ ] Generated code accessible via `context.generated_code`
- [ ] Progress tracking reports "skipped" status
- [ ] User-friendly console output with code preview

### Non-Functional Requirements ✅

- [ ] Test coverage ≥80% for new code
- [ ] Documentation updated with examples
- [ ] No breaking changes to existing API
- [ ] Performance: Dry-run completes <5 seconds (same as standard)

---

## 10. Conclusion

**Summary**: Dry-run mode implementation is straightforward due to existing `write_files` parameter. Primary work involves:

1. **CLI Command** - Add `project generate` with `--dry-run` flag (3 hours)
2. **Enhanced Feedback** - Improve progress message (15 minutes)
3. **Test Coverage** - Add dry-run-specific tests (3 hours)
4. **Documentation** - Update guides with examples (1 hour)

**Total Estimated Effort**: 7-8 hours (1 developer-day)

**Recommended Approach**: Implement CLI command first (Phase 1), validate manually, then add test coverage (Phase 2) and documentation (Phase 3).

---

## Appendix: Code Snippets

### A1: Current File Writing Logic

**Location**: `src/extract_transform_platform/services/codegen/code_generator.py:637-670`

```python
# STEP 5/7: Write generated files
step_start = time.time()
if write_files:
    report_progress(5, "Write generated files to disk", "in_progress")
    logger.info("Step 5/7: Writing files")

    paths = self.writer.write(
        code, project_config.project.name, backup=True
    )
    output_dir = self.writer.base_dir / project_config.project.name

    code.add_metadata("output_paths", {k: str(v) for k, v in paths.items()})

    step_elapsed = time.time() - step_start
    logger.info(
        "Files written",
        files=len(paths),
        directory=str(output_dir),
        elapsed=f"{step_elapsed:.2f}s",
    )
    report_progress(
        5,
        "Write generated files to disk",
        "completed",
        step_elapsed,
        message=f"Wrote {len(paths)} files",
    )
else:
    output_dir = None
    report_progress(
        5,
        "Write generated files to disk",
        "skipped",
        0.0,
        message="File writing disabled",
    )
```

### A2: Proposed CLI Command Skeleton

```python
@project.command()
@click.argument("name")
@click.option("--dry-run", is_flag=True, help="Preview without writing files")
def generate(name: str, dry_run: bool):
    """Generate extraction code from project examples."""
    console.print(f"Generating code for: {name}")

    if dry_run:
        console.print("[yellow]DRY-RUN MODE[/yellow]")

    service = CodeGeneratorService()
    context = run_async(
        service.generate(
            examples=...,
            project_config=...,
            write_files=not dry_run  # <-- KEY LINE
        )
    )

    if dry_run:
        # Show preview
        console.print(f"Generated {context.generated_code.total_lines} lines")
        console.print("[yellow]No files written[/yellow]")
    else:
        # Show output paths
        console.print("Files written:")
        for path in context.generated_code.metadata["output_paths"].values():
            console.print(f"  • {path}")
```

---

**End of Research Document**
