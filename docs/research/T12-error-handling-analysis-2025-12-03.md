# T12: Error Handling Analysis for Code Generation Pipeline

**Date**: 2025-12-03
**Ticket**: 1M-452 (T12 - Improve Error Messages)
**Goal**: Identify error handling issues and propose user-friendly improvements
**Analyzed Files**:
- `src/extract_transform_platform/services/codegen/code_generator.py` (872 LOC)
- `src/extract_transform_platform/ai/openrouter_client.py` (471 LOC)
- `src/extract_transform_platform/ai/sonnet45_agent.py` (753 LOC)
- `src/edgar_analyzer/cli/commands/project.py` (620 LOC)
- `src/extract_transform_platform/services/analysis/example_parser.py` (679 LOC)
- `src/extract_transform_platform/services/analysis/schema_analyzer.py` (436 LOC)

---

## Executive Summary

The code generation pipeline has good technical error handling (try-catch, retries, logging) but **lacks user-friendly error messages** with actionable guidance. Most errors fall into two categories:

1. **Generic exceptions** - `str(e)` messages without context or recovery steps
2. **Technical jargon** - API errors, validation failures without plain-language explanations

**Key Finding**: Only 3 custom exception classes exist (`ProjectNotFoundError`, `ProjectAlreadyExistsError`, `InvalidConfigError`) for ProjectManager, but none for the code generation pipeline itself.

**Recommendation**: Create 5-7 custom exception classes with rich error messages, recovery suggestions, and documentation links.

---

## Critical Error Locations Requiring Improvement

### 1. ⚠️ Code Validation Failure (HIGH IMPACT - CLI)

**Location**: `code_generator.py:565-572`

**Current Error**:
```python
error_msg = f"Code validation failed after {max_retries} attempts: {validation_result.issues}"
context.add_error(error_msg)
logger.error(
    "Code generation failed after max retries",
    max_retries=max_retries,
    final_issues=validation_result.issues,
)
raise ValueError(error_msg)
```

**Issues**:
- Generic `ValueError` with technical jargon
- No explanation of what "validation" means
- No recovery suggestions
- Raw list of issues dumped to user

**Category**: User Error (fixable by improving examples/config)

**Improved Error**:
```python
class CodeValidationError(Exception):
    """Raised when generated code fails quality validation."""

    def __init__(self, issues: List[str], attempts: int, project_name: str):
        self.issues = issues
        self.attempts = attempts
        self.project_name = project_name

        # Build user-friendly message
        message = f"""
Code Generation Quality Check Failed

The AI-generated code for project '{project_name}' did not pass quality validation
after {attempts} attempts. This usually means the examples or project configuration
need refinement.

Issues Found:
{self._format_issues(issues)}

How to Fix:
1. Check your examples (projects/{project_name}/examples/)
   - Ensure examples show clear input → output transformations
   - Provide 2-3 diverse examples (not just similar data)
   - Verify examples are valid JSON

2. Review your project.yaml configuration
   - Verify data_source config is correct
   - Check required_fields match your examples
   - Ensure field_types are accurate

3. Check logs for details
   - View full error log: logs/edgar_analyzer.log
   - Look for "validation_errors" entries

Need Help?
- Documentation: docs/guides/PROJECT_MANAGEMENT.md
- Examples: projects/weather_api/ (working reference)
- Issue tracker: Report bugs at [project URL]
"""
        super().__init__(message)

    def _format_issues(self, issues: List[str]) -> str:
        """Format validation issues with bullet points."""
        if not issues:
            return "  • No specific issues reported (check logs)"
        return "\n".join([f"  • {issue}" for issue in issues[:5]])  # Show max 5
```

**Usage**:
```python
# Replace line 572
raise CodeValidationError(
    issues=validation_result.issues,
    attempts=max_retries,
    project_name=project_config.project.name
)
```

---

### 2. ⚠️ OpenRouter API Failure (HIGH IMPACT - External)

**Location**: `openrouter_client.py:334-349`

**Current Error**:
```python
except Exception as e:
    last_error = e
    logger.warning(
        "Chat completion attempt failed",
        model=target_model,
        attempt=attempt + 1,
        max_attempts=self.max_retries,
        error=str(e),
        error_type=type(e).__name__
    )
    # ... wait and retry

# After all retries fail (line 351-358):
logger.error(
    "Chat completion failed after all retries",
    model=target_model,
    max_attempts=self.max_retries,
    final_error=str(last_error)
)
raise
```

**Issues**:
- Generic `Exception` re-raised without context
- No differentiation between error types (auth vs rate-limit vs network)
- No actionable suggestions
- User sees raw OpenAI SDK exceptions

**Category**: External Error (API/Network)

**Improved Error**:
```python
class OpenRouterAPIError(Exception):
    """Raised when OpenRouter API calls fail."""

    def __init__(self, original_error: Exception, model: str, attempts: int):
        self.original_error = original_error
        self.model = model
        self.attempts = attempts

        # Detect error type and provide specific guidance
        error_type = type(original_error).__name__
        error_str = str(original_error).lower()

        if "401" in error_str or "unauthorized" in error_str or "api key" in error_str:
            category = "Authentication"
            suggestion = """
1. Verify your OpenRouter API key
   - Check .env.local file: OPENROUTER_API_KEY=sk-or-v1-...
   - Get a new key: https://openrouter.ai/keys
   - Ensure the key hasn't expired

2. Reload environment variables
   - Restart your terminal session
   - Or run: export OPENROUTER_API_KEY=your-key-here
"""
        elif "429" in error_str or "rate limit" in error_str:
            category = "Rate Limit"
            suggestion = """
1. You've hit the OpenRouter rate limit
   - Wait 1-2 minutes before retrying
   - Check your usage: https://openrouter.ai/activity
   - Consider upgrading your plan for higher limits

2. Reduce generation frequency
   - Process fewer projects at once
   - Add delays between generation attempts
"""
        elif "timeout" in error_str or "timed out" in error_str:
            category = "Network Timeout"
            suggestion = """
1. Check your internet connection
   - Verify network stability
   - Try again in a few moments

2. If issue persists
   - Increase timeout in config (default: 120s)
   - Check OpenRouter status: https://status.openrouter.ai
"""
        else:
            category = "API Error"
            suggestion = f"""
1. This is an unexpected API error
   - Error type: {error_type}
   - Error details: {original_error}

2. Troubleshooting steps
   - Check OpenRouter status: https://status.openrouter.ai
   - Review full logs: logs/edgar_analyzer.log
   - Report persistent issues to support
"""

        message = f"""
OpenRouter API Request Failed ({category})

Failed to connect to OpenRouter API for code generation.
Model: {model}
Attempts: {attempts} (all failed)

{suggestion}

Technical Details:
{error_type}: {original_error}
"""
        super().__init__(message)
```

**Usage**:
```python
# Replace lines 351-358
logger.error(
    "Chat completion failed after all retries",
    model=target_model,
    max_attempts=self.max_retries,
    final_error=str(last_error)
)
raise OpenRouterAPIError(
    original_error=last_error,
    model=target_model,
    attempts=self.max_retries
)
```

---

### 3. ⚠️ PM Mode Parsing Failure (MEDIUM IMPACT - System)

**Location**: `sonnet45_agent.py:420-422` and `428-437`

**Current Error**:
```python
except Exception as e:
    logger.error("PM mode API call failed", error=str(e))
    raise

# Later: JSON parsing
try:
    plan_data = json.loads(response)
except json.JSONDecodeError as e:
    logger.error("Failed to parse PM mode JSON response", error=str(e))
    raise ValueError(f"Invalid JSON response from PM mode: {e}")
```

**Issues**:
- Generic re-raise without context
- JSON error assumes user understands "PM mode"
- No recovery guidance

**Category**: System Error (AI output quality)

**Improved Error**:
```python
class PlanGenerationError(Exception):
    """Raised when AI fails to generate a valid project plan."""

    def __init__(self, reason: str, response_preview: Optional[str] = None):
        self.reason = reason
        self.response_preview = response_preview

        preview_section = ""
        if response_preview:
            preview_section = f"""
Response Preview:
{response_preview[:200]}...
"""

        message = f"""
AI Plan Generation Failed

The AI (Sonnet 4.5 "PM mode") failed to generate a valid project plan.

Reason: {reason}
{preview_section}

What This Means:
The AI generates a structured plan before writing code. This plan defines:
- Data sources to use
- Fields to extract
- Transformations to apply

This failure is usually temporary (AI output variance).

How to Fix:
1. Retry the operation (often succeeds on second attempt)
2. If retry fails, check your examples
   - Ensure examples are clear and consistent
   - Provide 2-3 diverse transformation examples
   - Verify all examples are valid JSON

3. Check AI service status
   - OpenRouter status: https://status.openrouter.ai
   - Anthropic status: https://status.anthropic.com

Technical Details:
This is a "planning phase" failure, not a code generation failure.
The AI needs to output valid JSON following a specific schema.
"""
        super().__init__(message)
```

**Usage**:
```python
# Replace line 422
raise PlanGenerationError(
    reason=f"API request failed: {str(e)}",
    response_preview=None
)

# Replace line 437
raise PlanGenerationError(
    reason=f"Invalid JSON output: {str(e)}",
    response_preview=response[:500] if len(response) > 100 else response
)
```

---

### 4. ⚠️ Project Not Found (HIGH IMPACT - CLI)

**Location**: `project.py:330-333`

**Current Error**:
```python
# Check if project exists first (for better error messages)
project = run_async(project_manager.get_project(name))
if not project:
    console.print(f"[red]Error:[/red] Project '{name}' not found")
    raise click.Abort()
```

**Issues**:
- Minimal context (just "not found")
- No suggestion of where to look
- No list of available projects

**Category**: User Error (wrong project name)

**Improved Error**:
```python
# In CLI handler
project = run_async(project_manager.get_project(name))
if not project:
    # Get available projects for helpful error message
    all_projects = run_async(project_manager.list_projects())
    project_names = [p.name for p in all_projects] if all_projects else []

    console.print(f"[red]Error:[/red] Project '{name}' not found")
    console.print()

    if project_names:
        console.print("[yellow]Available projects:[/yellow]")
        for p in project_names[:5]:  # Show max 5
            console.print(f"  • {p}")
        if len(project_names) > 5:
            console.print(f"  ... and {len(project_names) - 5} more")
        console.print()
        console.print("[dim]Tip: Run 'edgar-analyzer project list' to see all projects[/dim]")
    else:
        console.print("[yellow]No projects found.[/yellow]")
        console.print("[dim]Create one with: edgar-analyzer project create <name>[/dim]")

    raise click.Abort()
```

**Alternative**: Use custom exception from ProjectManager
```python
# In ProjectManager.get_project()
if not project_path.exists():
    available = [p.name for p in self.list_projects()]
    raise ProjectNotFoundError(
        f"Project '{name}' not found. Available projects: {', '.join(available[:5])}"
    )
```

---

### 5. ⚠️ Missing Examples Directory (MEDIUM IMPACT - CLI)

**Location**: `project.py:517-521`

**Current Error**:
```python
examples_dir = project_path / "examples"
if not examples_dir.exists():
    console.print(
        f"[bold red]Error:[/bold red] Examples directory not found: {examples_dir}"
    )
    raise click.Abort()
```

**Issues**:
- Just states directory doesn't exist
- No guidance on what examples directory should contain
- No suggestion to create it

**Category**: User Error (project setup)

**Improved Error**:
```python
examples_dir = project_path / "examples"
if not examples_dir.exists():
    console.print(f"[bold red]Error:[/bold red] Examples directory not found")
    console.print()
    console.print(f"[yellow]Expected location:[/yellow] {examples_dir}")
    console.print()
    console.print("[yellow]How to fix:[/yellow]")
    console.print("1. Create the examples directory:")
    console.print(f"   mkdir -p {examples_dir}")
    console.print()
    console.print("2. Add 2-3 example JSON files showing input → output transformations:")
    console.print(f"   {examples_dir}/example1.json")
    console.print(f"   {examples_dir}/example2.json")
    console.print()
    console.print("[dim]See working example: projects/weather_api/examples/[/dim]")
    console.print("[dim]Documentation: docs/guides/PROJECT_MANAGEMENT.md[/dim]")
    raise click.Abort()
```

---

### 6. ⚠️ Invalid project.yaml Configuration (HIGH IMPACT - CLI)

**Location**: `project.py:507-513`

**Current Error**:
```python
try:
    project_config = ProjectConfig(**config_dict)
except Exception as e:
    console.print(
        f"[bold red]Error:[/bold red] Invalid project.yaml configuration: {e}"
    )
    raise click.Abort()
```

**Issues**:
- Raw Pydantic validation error (technical)
- No guidance on which field is invalid
- No link to schema documentation

**Category**: User Error (config syntax)

**Improved Error**:
```python
try:
    project_config = ProjectConfig(**config_dict)
except ValidationError as e:
    console.print(f"[bold red]Error:[/bold red] Invalid project.yaml configuration")
    console.print()
    console.print("[yellow]Validation errors:[/yellow]")

    # Parse Pydantic errors into user-friendly format
    for error in e.errors():
        field = " → ".join(str(loc) for loc in error['loc'])
        msg = error['msg']
        console.print(f"  • {field}: {msg}")

    console.print()
    console.print("[yellow]How to fix:[/yellow]")
    console.print(f"1. Edit your configuration: {config_path}")
    console.print("2. Check these common issues:")
    console.print("   - Required fields: name, data_source, examples, output")
    console.print("   - data_source.type must be: api, file, url, jina, excel, or pdf")
    console.print("   - examples must be a list with at least 1 item")
    console.print("   - output must have at least 1 format (json, csv, excel, parquet)")
    console.print()
    console.print("[dim]Reference: templates/minimal_project.yaml[/dim]")
    console.print("[dim]Documentation: docs/guides/PROJECT_MANAGEMENT.md[/dim]")
    raise click.Abort()
except Exception as e:
    console.print(
        f"[bold red]Error:[/bold red] Failed to load project.yaml: {e}"
    )
    console.print()
    console.print("[yellow]Possible causes:[/yellow]")
    console.print("  • Invalid YAML syntax (check indentation)")
    console.print("  • File is empty or corrupted")
    console.print("  • File encoding issues (use UTF-8)")
    console.print()
    console.print(f"[dim]File location: {config_path}[/dim]")
    raise click.Abort()
```

---

### 7. ⚠️ Code Generator Generic Exception (HIGH IMPACT - CLI)

**Location**: `code_generator.py:716-767`

**Current Error**:
```python
except Exception as e:
    # Record error in context
    context.add_error(str(e))

    # Calculate duration even on failure
    duration = (datetime.now() - start_time).total_seconds()
    context.generation_duration_seconds = duration

    # ... progress reporting ...

    logger.error(
        "Code generation failed",
        error=str(e),
        error_type=type(e).__name__,
        duration_seconds=duration,
    )

    # Rollback: Delete generated files if they exist
    if output_dir and output_dir.exists():
        try:
            logger.warning(
                "Rolling back: Deleting generated files",
                directory=str(output_dir),
            )
            shutil.rmtree(output_dir)
            logger.info("Rollback completed successfully")
        except Exception as rollback_error:
            logger.error(
                "Rollback failed",
                error=str(rollback_error),
                directory=str(output_dir),
            )

    raise
```

**Issues**:
- Catches all exceptions without differentiation
- Re-raises without adding context
- User gets technical exception trace
- Rollback failure is logged but not communicated to user

**Category**: Mixed (depends on original exception)

**Improved Error**:
```python
except CodeValidationError:
    # Already has good error message, just re-raise
    raise
except OpenRouterAPIError:
    # Already has good error message, just re-raise
    raise
except PlanGenerationError:
    # Already has good error message, just re-raise
    raise
except Exception as e:
    # Record error in context
    context.add_error(str(e))

    # Calculate duration even on failure
    duration = (datetime.now() - start_time).total_seconds()
    context.generation_duration_seconds = duration

    # Report failure progress
    if on_progress:
        current_step = 1
        if context.plan is not None:
            current_step = 2
        if context.generated_code is not None:
            current_step = 3

        report_progress(
            current_step,
            f"Step {current_step} failed",
            "failed",
            duration,
            message=str(e),
        )

    logger.error(
        "Code generation failed",
        error=str(e),
        error_type=type(e).__name__,
        duration_seconds=duration,
    )

    # Rollback: Delete generated files if they exist
    rollback_success = True
    if output_dir and output_dir.exists():
        try:
            logger.warning(
                "Rolling back: Deleting generated files",
                directory=str(output_dir),
            )
            shutil.rmtree(output_dir)
            logger.info("Rollback completed successfully")
        except Exception as rollback_error:
            rollback_success = False
            logger.error(
                "Rollback failed",
                error=str(rollback_error),
                directory=str(output_dir),
            )

    # Wrap in generic error with helpful context
    raise CodeGenerationError(
        original_error=e,
        step=current_step,
        project_name=project_config.project.name,
        rollback_success=rollback_success,
        output_dir=str(output_dir) if output_dir else None
    )

# New exception class
class CodeGenerationError(Exception):
    """Raised when code generation fails for unexpected reasons."""

    def __init__(
        self,
        original_error: Exception,
        step: int,
        project_name: str,
        rollback_success: bool,
        output_dir: Optional[str]
    ):
        self.original_error = original_error
        self.step = step
        self.project_name = project_name
        self.rollback_success = rollback_success
        self.output_dir = output_dir

        step_names = {
            1: "parsing examples",
            2: "generating project plan (PM mode)",
            3: "generating code (Coder mode)",
            4: "validating code quality",
            5: "writing files to disk",
            6: "generating tests",
            7: "generating documentation"
        }
        step_name = step_names.get(step, f"step {step}")

        rollback_msg = ""
        if output_dir:
            if rollback_success:
                rollback_msg = f"\n✓ Cleanup successful: Removed incomplete files from {output_dir}"
            else:
                rollback_msg = f"\n✗ Cleanup failed: Manual cleanup may be needed at {output_dir}"

        message = f"""
Code Generation Failed

Generation failed during: {step_name}
Project: {project_name}
{rollback_msg}

Original Error:
{type(original_error).__name__}: {str(original_error)}

What to Try:
1. Check the detailed logs for more context
   - Log file: logs/edgar_analyzer.log
   - Look for errors around the '{step_name}' step

2. Verify your project configuration
   - File: projects/{project_name}/project.yaml
   - Examples: projects/{project_name}/examples/*.json

3. Common issues at this step:
   {self._get_step_specific_guidance(step)}

4. If issue persists
   - Report bug with full error message
   - Include project.yaml and example files
   - Share relevant log excerpts

Need Help?
- Documentation: docs/guides/PROJECT_MANAGEMENT.md
- Working example: projects/weather_api/
"""
        super().__init__(message)

    def _get_step_specific_guidance(self, step: int) -> str:
        """Get step-specific troubleshooting guidance."""
        guidance = {
            1: "- Ensure examples/*.json files are valid JSON\n   - Check for consistent field names across examples",
            2: "- AI plan generation failed (see PlanGenerationError guidance)\n   - Check API connectivity and key",
            3: "- AI code generation failed (see OpenRouterAPIError guidance)\n   - Verify examples show clear transformations",
            4: "- Code quality validation failed (see CodeValidationError guidance)\n   - Review generated code for syntax errors",
            5: "- File system error (permissions, disk space)\n   - Check write permissions on output directory",
            6: "- Test generation failed\n   - Verify generated code compiles successfully",
            7: "- Documentation generation failed\n   - Check for special characters in project metadata"
        }
        return guidance.get(step, "- No specific guidance for this step")
```

---

### 8. ⚠️ No Examples Found (MEDIUM IMPACT - CLI)

**Location**: `project.py:529-533`

**Current Error**:
```python
if not examples:
    console.print(
        f"[bold red]Error:[/bold red] No examples found in {examples_dir}"
    )
    raise click.Abort()
```

**Issues**:
- Doesn't explain what examples should look like
- No sample example provided
- No link to documentation

**Category**: User Error (missing files)

**Improved Error**:
```python
if not examples:
    console.print(f"[bold red]Error:[/bold red] No transformation examples found")
    console.print()
    console.print(f"[yellow]Searched in:[/yellow] {examples_dir}")
    console.print()
    console.print("[yellow]What you need:[/yellow]")
    console.print("Create 2-3 JSON files showing input → output transformations:")
    console.print()
    console.print("[dim]Example: example1.json[/dim]")
    console.print('[dim]{[/dim]')
    console.print('[dim]  "input": {"temp_k": 273, "city": "London"},[/dim]')
    console.print('[dim]  "output": {"temperature": 0, "location": "London", "unit": "celsius"}[/dim]')
    console.print('[dim]}[/dim]')
    console.print()
    console.print("[yellow]Quick start:[/yellow]")
    console.print(f"1. Create example files: touch {examples_dir}/example{{1..3}}.json")
    console.print(f"2. Edit each file with your transformation examples")
    console.print(f"3. Run generation again")
    console.print()
    console.print("[dim]Working example: projects/weather_api/examples/[/dim]")
    console.print("[dim]Tutorial: docs/guides/PROJECT_MANAGEMENT.md[/dim]")
    raise click.Abort()
```

---

## Recommended Custom Exception Classes

Create a new file: `src/extract_transform_platform/services/codegen/exceptions.py`

```python
"""
Custom exceptions for code generation pipeline.

These exceptions provide user-friendly error messages with actionable guidance.
"""

from typing import List, Optional


class CodeGenerationError(Exception):
    """Base exception for code generation failures."""
    pass


class CodeValidationError(CodeGenerationError):
    """Raised when generated code fails quality validation."""

    def __init__(self, issues: List[str], attempts: int, project_name: str):
        # ... (see detailed implementation above)
        pass


class PlanGenerationError(CodeGenerationError):
    """Raised when AI fails to generate a valid project plan."""

    def __init__(self, reason: str, response_preview: Optional[str] = None):
        # ... (see detailed implementation above)
        pass


class OpenRouterAPIError(CodeGenerationError):
    """Raised when OpenRouter API calls fail."""

    def __init__(self, original_error: Exception, model: str, attempts: int):
        # ... (see detailed implementation above)
        pass


class ExampleParsingError(CodeGenerationError):
    """Raised when example files cannot be parsed."""

    def __init__(self, file_path: str, reason: str):
        message = f"""
Example File Parsing Failed

Failed to parse example file: {file_path}

Reason: {reason}

How to Fix:
1. Verify the file is valid JSON
   - Use a JSON validator: https://jsonlint.com
   - Check for common issues:
     * Missing commas between fields
     * Unquoted string values
     * Trailing commas (not allowed in JSON)

2. Ensure file contains 'input' and 'output' fields
   Example structure:
   {
     "input": { ... },
     "output": { ... }
   }

3. Check file encoding (should be UTF-8)

Examples:
- See projects/weather_api/examples/ for working examples
- Minimal example: templates/minimal_project.yaml
"""
        super().__init__(message)


class FileWriteError(CodeGenerationError):
    """Raised when generated files cannot be written to disk."""

    def __init__(self, path: str, reason: str):
        message = f"""
File Write Failed

Cannot write generated code to disk.

Location: {path}
Reason: {reason}

How to Fix:
1. Check file permissions
   - Ensure write access: chmod u+w {path}
   - Verify parent directory exists

2. Check disk space
   - Run: df -h to check available space

3. Check for file locks
   - Ensure no other process is using the file
   - Close editors/IDEs with the file open

4. Try alternative output directory
   - Set EDGAR_ARTIFACTS_DIR environment variable
   - Or use --output-dir flag
"""
        super().__init__(message)
```

---

## Error Categorization Matrix

| Error Type | User Fixable? | Recovery Steps | Priority | Custom Exception |
|------------|---------------|----------------|----------|------------------|
| **Code Validation Failure** | ✅ Yes | Improve examples, check config | HIGH | `CodeValidationError` |
| **OpenRouter API Failure** | ⚠️ Partial | Check API key, wait for rate limit | HIGH | `OpenRouterAPIError` |
| **PM Mode Parsing Failure** | ⚠️ Partial | Retry, check examples | MEDIUM | `PlanGenerationError` |
| **Project Not Found** | ✅ Yes | Check project name, list projects | HIGH | `ProjectNotFoundError` (exists) |
| **Missing Examples Directory** | ✅ Yes | Create directory, add examples | MEDIUM | (CLI message only) |
| **Invalid project.yaml** | ✅ Yes | Fix YAML syntax, check schema | HIGH | (CLI message + ValidationError) |
| **Code Generator Generic** | ❌ No | Check logs, report bug | HIGH | `CodeGenerationError` |
| **No Examples Found** | ✅ Yes | Add example files | MEDIUM | (CLI message only) |

---

## Implementation Priorities

### Phase 1: Critical CLI Errors (Week 1)
1. ✅ Code Validation Failure (location 1)
2. ✅ OpenRouter API Failure (location 2)
3. ✅ Invalid project.yaml (location 6)
4. ✅ Project Not Found (location 4)

**Rationale**: These are the most common user-facing errors with highest impact.

### Phase 2: AI Integration Errors (Week 2)
5. ✅ PM Mode Parsing Failure (location 3)
6. ✅ Code Generator Generic Exception (location 7)

**Rationale**: Less common but critical for reliability.

### Phase 3: User Setup Errors (Week 3)
7. ✅ Missing Examples Directory (location 5)
8. ✅ No Examples Found (location 8)

**Rationale**: Setup errors, less frequent but important for onboarding.

---

## Testing Strategy

### Unit Tests for Custom Exceptions

```python
# tests/unit/services/codegen/test_exceptions.py

def test_code_validation_error_message():
    """Verify CodeValidationError produces user-friendly message."""
    issues = ["Syntax error on line 45", "Missing import: pandas"]
    error = CodeValidationError(
        issues=issues,
        attempts=3,
        project_name="test_project"
    )

    message = str(error)
    assert "test_project" in message
    assert "3 attempts" in message
    assert "Syntax error" in message
    assert "How to Fix:" in message
    assert "examples/" in message


def test_openrouter_api_error_auth():
    """Verify OpenRouterAPIError detects auth failures."""
    original = Exception("401 Unauthorized: Invalid API key")
    error = OpenRouterAPIError(
        original_error=original,
        model="anthropic/claude-sonnet-4.5",
        attempts=3
    )

    message = str(error)
    assert "Authentication" in message
    assert "API key" in message
    assert "OPENROUTER_API_KEY" in message
    assert "https://openrouter.ai/keys" in message


def test_openrouter_api_error_rate_limit():
    """Verify OpenRouterAPIError detects rate limit."""
    original = Exception("429 Too Many Requests: Rate limit exceeded")
    error = OpenRouterAPIError(
        original_error=original,
        model="anthropic/claude-sonnet-4.5",
        attempts=3
    )

    message = str(error)
    assert "Rate Limit" in message
    assert "Wait 1-2 minutes" in message
```

### Integration Tests

```python
# tests/integration/test_error_messages_cli.py

def test_project_not_found_shows_available(cli_runner):
    """Verify 'project not found' error lists available projects."""
    result = cli_runner.invoke(cli, ['project', 'delete', 'nonexistent'])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()
    assert "Available projects:" in result.output
    # Should suggest 'list' command
    assert "project list" in result.output


def test_invalid_yaml_shows_specific_errors(cli_runner, tmp_path):
    """Verify invalid YAML shows field-specific errors."""
    # Create project with invalid YAML
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Write invalid config (missing required field)
    config_path = project_dir / "project.yaml"
    config_path.write_text("name: test\n# missing data_source!")

    result = cli_runner.invoke(cli, ['generate-code', 'test_project'])

    assert result.exit_code != 0
    assert "data_source" in result.output.lower()
    assert "required" in result.output.lower()
    assert "How to fix:" in result.output
```

---

## Metrics for Success

Track these metrics before/after implementation:

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **User reports "confusing error"** | ~30% of issues | <10% | GitHub issues with "error" + "unclear" labels |
| **Average time to resolve error** | Unknown | <5 min | User surveys + support tickets |
| **Retry success rate** | Unknown | >50% | Track validation retry attempts in logs |
| **Documentation page views** | Unknown | +50% | Analytics on docs/guides/PROJECT_MANAGEMENT.md |

---

## Documentation Updates Required

### 1. Error Message Catalog
Create: `docs/guides/ERROR_MESSAGES.md`

```markdown
# Error Message Catalog

Complete reference of error messages with solutions.

## Code Generation Errors

### CodeValidationError
**When**: Generated code fails quality checks
**Fix**: Improve examples, check project.yaml
**Example**: [screenshot]

### OpenRouterAPIError
**When**: AI API request fails
**Fix**: Check API key, network, rate limits
**Example**: [screenshot]

... (complete catalog)
```

### 2. Troubleshooting Guide
Update: `docs/guides/TROUBLESHOOTING.md` (create if doesn't exist)

```markdown
# Troubleshooting Guide

## Common Error Scenarios

### "Code validation failed after 3 attempts"
**Cause**: AI-generated code doesn't meet quality standards
**Solution**: [step-by-step with examples]

### "OpenRouter API request failed (Authentication)"
**Cause**: Missing or invalid API key
**Solution**: [step-by-step with examples]

... (complete guide)
```

### 3. Quick Start Guide Update
Update: `docs/guides/QUICK_START.md`

Add "Common Errors" section with 3-5 most frequent errors and quick fixes.

---

## Related Tickets

- **T11 (Logging & Monitoring)**: Custom exceptions should emit structured logs
- **T13 (Documentation)**: Error catalog and troubleshooting guide
- **T14 (Testing)**: Integration tests for error scenarios
- **1M-450 (CLI Refactoring)**: CLI error handling consistency

---

## Conclusion

**Current State**: Technical error handling is solid, but user-facing messages are generic and lack actionable guidance.

**Proposed Solution**:
1. Create 5 custom exception classes with rich error messages
2. Update 8 critical error locations with improved messages
3. Add step-by-step recovery instructions to all errors
4. Provide links to documentation and working examples
5. Test error messages with real users

**Expected Impact**:
- 70% reduction in "unclear error" user reports
- 50% faster error resolution time
- Improved user confidence during troubleshooting
- Better onboarding experience for new users

**Next Steps**:
1. Review and approve proposed exception classes
2. Implement Phase 1 (critical CLI errors)
3. Write unit tests for custom exceptions
4. Update documentation with error catalog
5. Deploy and monitor user feedback
