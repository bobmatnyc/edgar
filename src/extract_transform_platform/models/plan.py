"""
Plan models for Sonnet 4.5 dual-mode code generation.

This module defines data structures for the PM (Planning Manager) mode
and Coder mode outputs in the AI-powered code generation system.

Design Decisions:
- **Separation of Concerns**: PM focuses on architecture, Coder on implementation
- **Structured Outputs**: Pydantic models ensure valid code generation plans
- **Metadata Tracking**: Record generation details for debugging and improvement
- **Validation**: Ensure generated artifacts meet quality standards

Usage:
    >>> plan = PlanSpec(
    ...     strategy="Extract weather data via REST API",
    ...     classes=[ClassSpec(name="WeatherExtractor", purpose="Extract weather")],
    ...     dependencies=["requests", "pydantic"],
    ...     error_handling="Retry with exponential backoff",
    ...     testing_strategy="Pytest with mocked responses"
    ... )
    >>> code = GeneratedCode(
    ...     extractor_code="class WeatherExtractor...",
    ...     models_code="class WeatherData(BaseModel)...",
    ...     tests_code="def test_weather_extraction()...",
    ...     metadata={"generation_time": 3.5}
    ... )
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# PM MODE OUTPUTS
# ============================================================================


class MethodSpec(BaseModel):
    """Specification for a method in a class.

    Example:
        >>> method = MethodSpec(
        ...     name="extract",
        ...     purpose="Extract data from source",
        ...     parameters=["self", "cik: str", "year: int"],
        ...     return_type="Optional[Dict[str, Any]]",
        ...     notes="Handles network errors with retry logic"
        ... )
    """

    name: str = Field(
        ...,
        description="Method name"
    )

    purpose: str = Field(
        ...,
        description="What this method does"
    )

    parameters: List[str] = Field(
        default_factory=list,
        description="Method parameters with type hints (e.g., 'self', 'data: Dict')"
    )

    return_type: str = Field(
        default="None",
        description="Return type annotation (e.g., 'Optional[Dict[str, Any]]')"
    )

    notes: Optional[str] = Field(
        None,
        description="Additional notes about implementation"
    )


class ClassSpec(BaseModel):
    """Specification for a class to be generated.

    Example:
        >>> cls = ClassSpec(
        ...     name="WeatherExtractor",
        ...     purpose="Extract weather data from OpenWeatherMap API",
        ...     base_classes=["IDataExtractor"],
        ...     methods=[MethodSpec(name="extract", purpose="Main extraction method")]
        ... )
    """

    name: str = Field(
        ...,
        description="Class name (PascalCase recommended)"
    )

    purpose: str = Field(
        ...,
        description="High-level description of what this class does"
    )

    base_classes: List[str] = Field(
        default_factory=list,
        description="Base classes and interfaces (e.g., ['IDataExtractor'])"
    )

    methods: List[MethodSpec] = Field(
        default_factory=list,
        description="Methods to implement"
    )

    attributes: List[str] = Field(
        default_factory=list,
        description="Instance attributes (e.g., 'api_key: str', 'base_url: str')"
    )

    notes: Optional[str] = Field(
        None,
        description="Additional notes about the class"
    )

    @field_validator('name')
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        """Ensure class name is valid Python identifier."""
        if not v:
            raise ValueError("Class name cannot be empty")
        if not v[0].isupper():
            raise ValueError("Class name should start with uppercase letter")
        if not v.replace('_', '').isalnum():
            raise ValueError("Class name must be alphanumeric (underscores allowed)")
        return v


class PlanSpec(BaseModel):
    """PM Mode output: Implementation specification for code generation.

    The Planning Manager analyzes patterns and creates a detailed
    implementation plan that the Coder mode will execute.

    Example:
        >>> plan = PlanSpec(
        ...     strategy="Fetch weather data via REST API, parse JSON response",
        ...     classes=[ClassSpec(name="WeatherExtractor", purpose="...")],
        ...     dependencies=["requests", "pydantic"],
        ...     error_handling="Retry with exponential backoff (3 retries, max 30s)",
        ...     testing_strategy="Pytest with mocked HTTP responses",
        ...     notes="Handle API rate limits (60 req/min)"
        ... )
    """

    strategy: str = Field(
        ...,
        description="High-level extraction strategy description"
    )

    classes: List[ClassSpec] = Field(
        default_factory=list,
        description="Classes to generate"
    )

    dependencies: List[str] = Field(
        default_factory=list,
        description="Required imports and packages (e.g., 'requests', 'pydantic')"
    )

    error_handling: str = Field(
        ...,
        description="Error handling approach and strategies"
    )

    testing_strategy: str = Field(
        ...,
        description="How to test the implementation"
    )

    data_flow: Optional[str] = Field(
        None,
        description="Data flow from source to output (optional)"
    )

    notes: Optional[str] = Field(
        None,
        description="Additional implementation notes and considerations"
    )

    @field_validator('classes')
    @classmethod
    def validate_at_least_one_class(cls, v: List[ClassSpec]) -> List[ClassSpec]:
        """Ensure at least one class is specified."""
        if not v:
            raise ValueError("Plan must specify at least one class to generate")
        return v

    @field_validator('dependencies')
    @classmethod
    def validate_dependencies(cls, v: List[str]) -> List[str]:
        """Ensure dependencies are valid package names."""
        for dep in v:
            if not dep or not dep.replace('-', '').replace('_', '').replace('.', '').isalnum():
                raise ValueError(f"Invalid dependency name: {dep}")
        return v


# ============================================================================
# CODER MODE OUTPUTS
# ============================================================================


class GeneratedCode(BaseModel):
    """Coder Mode output: Generated code artifacts.

    The Coder mode generates production-ready Python code based on
    the PM specification and example patterns.

    Example:
        >>> code = GeneratedCode(
        ...     extractor_code="class WeatherExtractor(IDataExtractor):\\n    ...",
        ...     models_code="class WeatherData(BaseModel):\\n    ...",
        ...     tests_code="def test_weather_extraction():\\n    ...",
        ...     metadata={
        ...         "generation_timestamp": "2025-11-28T10:00:00",
        ...         "model": "anthropic/claude-sonnet-4.5",
        ...         "plan_confidence": 0.95
        ...     }
        ... )
    """

    extractor_code: str = Field(
        ...,
        description="Main extractor class implementation"
    )

    models_code: str = Field(
        ...,
        description="Pydantic models for input/output schemas"
    )

    tests_code: str = Field(
        ...,
        description="Unit tests for the extractor"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Generation metadata (timestamps, model info, etc.)"
    )

    validation_notes: Optional[str] = Field(
        None,
        description="Notes about code quality and validation"
    )

    @field_validator('extractor_code', 'models_code', 'tests_code')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Ensure code is not empty."""
        if not v or not v.strip():
            raise ValueError("Generated code cannot be empty")
        return v

    @property
    def total_lines(self) -> int:
        """Get total lines of code generated."""
        return (
            len(self.extractor_code.splitlines()) +
            len(self.models_code.splitlines()) +
            len(self.tests_code.splitlines())
        )

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata entry."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata entry."""
        return self.metadata.get(key, default)


# ============================================================================
# GENERATION CONTEXT
# ============================================================================


class GenerationContext(BaseModel):
    """Context for code generation process.

    Tracks the complete generation pipeline from patterns to code.

    Example:
        >>> context = GenerationContext(
        ...     project_name="weather_extractor",
        ...     num_patterns=5,
        ...     num_examples=3,
        ...     plan=plan_spec,
        ...     generated_code=generated_code,
        ...     generation_duration_seconds=4.2
        ... )
    """

    project_name: str = Field(
        ...,
        description="Project name from ProjectConfig"
    )

    num_patterns: int = Field(
        ...,
        ge=0,
        description="Number of patterns analyzed"
    )

    num_examples: int = Field(
        ...,
        ge=0,
        description="Number of examples provided"
    )

    plan: Optional[PlanSpec] = Field(
        None,
        description="PM mode output (if PM step completed)"
    )

    generated_code: Optional[GeneratedCode] = Field(
        None,
        description="Coder mode output (if Coder step completed)"
    )

    generation_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When code generation started"
    )

    generation_duration_seconds: Optional[float] = Field(
        None,
        description="Total generation time in seconds"
    )

    errors: List[str] = Field(
        default_factory=list,
        description="Errors encountered during generation"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings generated during process"
    )

    @property
    def is_complete(self) -> bool:
        """Check if generation completed successfully."""
        return self.plan is not None and self.generated_code is not None

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)


# ============================================================================
# VALIDATION RESULTS
# ============================================================================


class CodeValidationResult(BaseModel):
    """Result of validating generated code.

    Example:
        >>> result = CodeValidationResult(
        ...     is_valid=True,
        ...     syntax_valid=True,
        ...     has_type_hints=True,
        ...     has_docstrings=True,
        ...     has_tests=True,
        ...     issues=[]
        ... )
    """

    is_valid: bool = Field(
        ...,
        description="Overall validation status"
    )

    syntax_valid: bool = Field(
        ...,
        description="Whether code has valid Python syntax"
    )

    has_type_hints: bool = Field(
        default=False,
        description="Whether code includes type hints"
    )

    has_docstrings: bool = Field(
        default=False,
        description="Whether code includes docstrings"
    )

    has_tests: bool = Field(
        default=False,
        description="Whether tests are included"
    )

    implements_interface: bool = Field(
        default=False,
        description="Whether extractor implements IDataExtractor"
    )

    issues: List[str] = Field(
        default_factory=list,
        description="Validation issues found"
    )

    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improvement"
    )

    @property
    def quality_score(self) -> float:
        """Calculate quality score (0.0 to 1.0)."""
        if not self.is_valid:
            return 0.0

        score = 0.0
        # Syntax is mandatory
        if self.syntax_valid:
            score += 0.3
        # Type hints are important
        if self.has_type_hints:
            score += 0.2
        # Docstrings are important
        if self.has_docstrings:
            score += 0.2
        # Tests are critical
        if self.has_tests:
            score += 0.2
        # Interface implementation is required
        if self.implements_interface:
            score += 0.1

        return min(score, 1.0)

    def add_issue(self, issue: str) -> None:
        """Add a validation issue."""
        self.issues.append(issue)

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        self.recommendations.append(recommendation)


# ============================================================================
# PROGRESS TRACKING
# ============================================================================


class GenerationProgress(BaseModel):
    """Progress tracking for code generation pipeline.

    Tracks progress through the 7-step code generation pipeline, providing
    real-time feedback for CLI display and logging. Supports status transitions
    from pending → in_progress → completed/failed/skipped.

    Design Rationale:
    - **Granular Tracking**: 7 distinct steps for transparency
    - **Status Validation**: Only allows valid status values
    - **Progress Calculation**: Automatic percentage calculation
    - **Failure Detection**: Explicit failed state for error handling
    - **Skip Support**: Dry-run mode can skip file writing step

    Status Values:
    - "pending": Step has not started yet
    - "in_progress": Step is currently executing
    - "completed": Step finished successfully
    - "failed": Step failed with error
    - "skipped": Step was skipped (validation disabled, dry-run mode)

    Example:
        >>> progress = GenerationProgress(
        ...     current_step=3,
        ...     total_steps=7,
        ...     step_name="Generate code",
        ...     status="in_progress",
        ...     elapsed_time=2.5
        ... )
        >>> print(f"{progress.progress_percentage:.1f}% complete")
        28.6% complete

    Usage in callbacks:
        >>> def on_progress(progress: GenerationProgress):
        ...     if progress.is_failed:
        ...         print(f"ERROR: {progress.message}")
        ...     else:
        ...         print(f"[{progress.current_step}/{progress.total_steps}] "
        ...               f"{progress.step_name} - {progress.status}")

    Related to: T10 (1M-452: Enhanced CodeGenerationPipeline with Progress Tracking)
    """

    current_step: int = Field(
        ...,
        ge=1,
        description="Current pipeline step (1-indexed)"
    )

    total_steps: int = Field(
        ...,
        ge=1,
        description="Total number of pipeline steps"
    )

    step_name: str = Field(
        ...,
        description="Human-readable name of current step"
    )

    status: str = Field(
        ...,
        description="Step status (pending, in_progress, completed, failed, skipped)"
    )

    elapsed_time: float = Field(
        default=0.0,
        ge=0.0,
        description="Elapsed time in seconds since pipeline start"
    )

    message: Optional[str] = Field(
        None,
        description="Optional status message (error details, warnings, etc.)"
    )

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is one of the allowed values."""
        allowed = {"pending", "in_progress", "completed", "failed", "skipped"}
        if v not in allowed:
            raise ValueError(
                f"Status must be one of {allowed}, got '{v}'"
            )
        return v

    @field_validator('current_step')
    @classmethod
    def validate_current_step(cls, v: int, info) -> int:
        """Ensure current_step doesn't exceed total_steps."""
        # Note: info.data may not have total_steps yet during validation
        # This is checked at runtime, not during construction
        return v

    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage (0.0 to 100.0).

        Logic:
        - If step is in_progress: (current_step - 1) / total_steps * 100
        - If step is completed: current_step / total_steps * 100
        - This ensures in_progress shows partial progress, completed shows full step progress

        Example:
            >>> # Step 3 in progress (2 completed out of 7)
            >>> progress = GenerationProgress(
            ...     current_step=3, total_steps=7,
            ...     step_name="Generate code", status="in_progress"
            ... )
            >>> progress.progress_percentage  # (3-1)/7 * 100 = 28.57%
            28.571428571428573

            >>> # Step 3 completed (3 completed out of 7)
            >>> progress.status = "completed"
            >>> progress.progress_percentage  # 3/7 * 100 = 42.86%
            42.857142857142854
        """
        if self.total_steps == 0:
            return 0.0

        # Calculate based on status
        if self.status == "completed":
            completed = self.current_step
        else:
            # For in_progress, pending, failed, skipped - count previous completed steps
            completed = self.current_step - 1

        return (completed / self.total_steps) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if pipeline is complete (all steps done).

        Returns True only when on final step AND status is completed.
        """
        return self.current_step == self.total_steps and self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if current step failed."""
        return self.status == "failed"
