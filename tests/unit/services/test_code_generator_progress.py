"""
Unit tests for CodeGeneratorService with Progress Tracking (T10: 1M-452)

Tests the enhanced code generation pipeline with:
- GenerationProgress dataclass
- Progress callback mechanism
- 7-step pipeline with granular tracking
- Per-step error handling
- Rollback mechanism on failure

Test Coverage:
- Progress tracking for successful generation
- Progress callback invocation at each step
- Step timing and elapsed time tracking
- Error handling with rollback
- Validation skipping
- File writing skipping
- Edge cases and error scenarios

Created: 2025-11-30 (T10 - Enhanced CodeGenerationPipeline)
"""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from extract_transform_platform.models.plan import (
    ClassSpec,
    CodeValidationResult,
    GeneratedCode,
    GenerationContext,
    GenerationProgress,
    MethodSpec,
    PlanSpec,
)
from extract_transform_platform.models.patterns import (
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
    SchemaField,
    FieldTypeEnum,
)
from extract_transform_platform.models.project_config import (
    ProjectConfig,
    ProjectMetadata,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
)
from extract_transform_platform.services.codegen.code_generator import (
    CodeGeneratorService,
    CodeValidator,
    CodeWriter,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================


def _check_api_key_available() -> bool:
    """Check if OPENROUTER_API_KEY is available."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return api_key is not None and api_key.strip() != ""


@pytest.fixture
def require_api_key():
    """Skip test if OPENROUTER_API_KEY is not available."""
    if not _check_api_key_available():
        pytest.skip("OPENROUTER_API_KEY not set - skipping code generation test")


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_project_config():
    """Create sample project configuration."""
    return ProjectConfig(
        project=ProjectMetadata(
            name="test_project",
            description="Test project for code generation",
            version="1.0.0",
        ),
        output=OutputConfig(
            formats=[
                OutputDestinationConfig(
                    type=OutputFormat.JSON,
                    path="output/test_results.json",
                    pretty_print=True,
                )
            ]
        ),
    )


@pytest.fixture
def sample_examples():
    """Create sample transformation examples."""
    return [
        {
            "input": {"temperature": 15.5, "city": "San Francisco"},
            "output": {"temp_celsius": 15.5, "location": "San Francisco"},
        },
        {
            "input": {"temperature": 20.0, "city": "New York"},
            "output": {"temp_celsius": 20.0, "location": "New York"},
        },
    ]


@pytest.fixture
def sample_parsed_examples():
    """Create sample parsed examples."""
    return ParsedExamples(
        patterns=[
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=1.0,
                source_path="temperature",
                target_path="temp_celsius",
                transformation="Direct field mapping",
            ),
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=1.0,
                source_path="city",
                target_path="location",
                transformation="Direct field mapping",
            ),
        ],
        input_schema=Schema(
            fields=[
                SchemaField(
                    name="temperature",
                    field_type=FieldTypeEnum.FLOAT,
                    path="temperature",
                ),
                SchemaField(
                    name="city", field_type=FieldTypeEnum.STRING, path="city"
                ),
            ]
        ),
        output_schema=Schema(
            fields=[
                SchemaField(
                    name="temp_celsius",
                    field_type=FieldTypeEnum.FLOAT,
                    path="temp_celsius",
                ),
                SchemaField(
                    name="location",
                    field_type=FieldTypeEnum.STRING,
                    path="location",
                ),
            ]
        ),
        num_examples=2,
    )


@pytest.fixture
def sample_plan():
    """Create sample implementation plan."""
    return PlanSpec(
        strategy="Extract weather data and transform field names",
        classes=[
            ClassSpec(
                name="WeatherExtractor",
                purpose="Extract and transform weather data",
                methods=[
                    MethodSpec(
                        name="extract",
                        purpose="Extract weather data",
                        parameters=["self", "data: Dict[str, Any]"],
                        return_type="Dict[str, Any]",
                    )
                ],
            )
        ],
        dependencies=["typing"],
        error_handling="Return None on errors",
        testing_strategy="Pytest with sample data",
    )


@pytest.fixture
def sample_generated_code():
    """Create sample generated code."""
    return GeneratedCode(
        extractor_code='class WeatherExtractor:\n    def extract(self, data):\n        return {"temp_celsius": data["temperature"]}',
        models_code="from pydantic import BaseModel\n\nclass WeatherData(BaseModel):\n    temp_celsius: float",
        tests_code='def test_extraction():\n    extractor = WeatherExtractor()\n    result = extractor.extract({"temperature": 15.5})\n    assert result["temp_celsius"] == 15.5',
    )


# ============================================================================
# TEST: GenerationProgress Dataclass
# ============================================================================


class TestGenerationProgress:
    """Test GenerationProgress dataclass functionality."""

    def test_creation_with_valid_status(self):
        """Test creating GenerationProgress with valid status."""
        progress = GenerationProgress(
            current_step=3,
            total_steps=7,
            step_name="Generate code",
            status="in_progress",
            elapsed_time=2.5,
        )

        assert progress.current_step == 3
        assert progress.total_steps == 7
        assert progress.step_name == "Generate code"
        assert progress.status == "in_progress"
        assert progress.elapsed_time == 2.5

    def test_invalid_status_raises_error(self):
        """Test that invalid status values raise validation error."""
        with pytest.raises(ValueError, match="Status must be one of"):
            GenerationProgress(
                current_step=1,
                total_steps=7,
                step_name="Test",
                status="invalid_status",
            )

    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation."""
        # Step 3 in progress (2 completed)
        progress = GenerationProgress(
            current_step=3,
            total_steps=7,
            step_name="Generate code",
            status="in_progress",
        )
        assert progress.progress_percentage == pytest.approx(28.57, rel=0.01)

        # Step 3 completed
        progress_completed = GenerationProgress(
            current_step=3,
            total_steps=7,
            step_name="Generate code",
            status="completed",
        )
        assert progress_completed.progress_percentage == pytest.approx(
            42.86, rel=0.01
        )

    def test_is_complete_property(self):
        """Test is_complete property."""
        # Not complete
        progress = GenerationProgress(
            current_step=5,
            total_steps=7,
            step_name="Write files",
            status="completed",
        )
        assert not progress.is_complete

        # Complete
        progress_complete = GenerationProgress(
            current_step=7,
            total_steps=7,
            step_name="Finalize",
            status="completed",
        )
        assert progress_complete.is_complete

    def test_is_failed_property(self):
        """Test is_failed property."""
        # Failed
        progress_failed = GenerationProgress(
            current_step=3,
            total_steps=7,
            step_name="Generate code",
            status="failed",
            message="Validation error",
        )
        assert progress_failed.is_failed

        # Not failed
        progress_ok = GenerationProgress(
            current_step=3,
            total_steps=7,
            step_name="Generate code",
            status="completed",
        )
        assert not progress_ok.is_failed


# ============================================================================
# TEST: Progress Callback Mechanism
# ============================================================================


class TestProgressCallbacks:
    """Test progress callback invocation during code generation."""

    @pytest.mark.asyncio
    @pytest.mark.requires_api
    async def test_progress_callback_invoked_for_all_steps(
        self,
        require_api_key,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that progress callback is invoked for all 7 steps."""
        # Track progress updates
        progress_updates: List[GenerationProgress] = []

        def on_progress(progress: GenerationProgress):
            progress_updates.append(progress)

        # Mock dependencies
        with patch(
            "extract_transform_platform.services.codegen.code_generator.ExampleParser"
        ) as mock_parser_class:
            with patch(
                "extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"
            ) as mock_agent_class:
                with patch(
                    "extract_transform_platform.services.codegen.code_generator.CodeValidator"
                ) as mock_validator_class:
                    # Setup mocks
                    mock_parser = MagicMock()
                    mock_parser.parse_examples.return_value = (
                        sample_parsed_examples
                    )
                    mock_parser_class.return_value = mock_parser

                    mock_agent = MagicMock()
                    mock_agent.plan = AsyncMock(return_value=sample_plan)
                    mock_agent.code = AsyncMock(
                        return_value=sample_generated_code
                    )
                    mock_agent_class.return_value = mock_agent

                    mock_validator = MagicMock()
                    mock_validation_result = CodeValidationResult(
                        is_valid=True,
                        syntax_valid=True,
                        has_type_hints=True,
                        has_docstrings=True,
                        has_tests=True,
                        implements_interface=True,
                    )
                    mock_validator.validate.return_value = (
                        mock_validation_result
                    )
                    mock_validator_class.return_value = mock_validator

                    # Create service and run generation
                    service = CodeGeneratorService(output_dir=temp_output_dir)
                    context = await service.generate(
                        examples=sample_examples,
                        project_config=sample_project_config,
                        validate=True,
                        write_files=True,
                        on_progress=on_progress,
                    )

        # Verify all 7 steps were reported
        assert len(progress_updates) >= 14  # 7 steps × 2 (in_progress + completed)

        # Verify step sequence
        step_names = [
            "Parse examples and extract patterns",
            "PM mode: Create implementation plan",
            "Coder mode: Generate production code",
            "Validate code quality",
            "Write generated files to disk",
            "Generate test suite",
            "Finalize generation and record metadata",
        ]

        for i, expected_name in enumerate(step_names, start=1):
            # Find in_progress update for this step
            in_progress_updates = [
                p
                for p in progress_updates
                if p.current_step == i and p.status == "in_progress"
            ]
            assert len(in_progress_updates) > 0, f"Missing in_progress for step {i}"
            assert in_progress_updates[0].step_name == expected_name

            # Find completed update for this step
            completed_updates = [
                p
                for p in progress_updates
                if p.current_step == i and p.status == "completed"
            ]
            assert len(completed_updates) > 0, f"Missing completed for step {i}"


    @pytest.mark.asyncio
    @pytest.mark.requires_api
    async def test_progress_callback_not_invoked_when_none(
        self,
        require_api_key,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that no errors occur when on_progress is None."""
        # Mock dependencies
        with patch(
            "extract_transform_platform.services.codegen.code_generator.ExampleParser"
        ) as mock_parser_class:
            with patch(
                "extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"
            ) as mock_agent_class:
                with patch(
                    "extract_transform_platform.services.codegen.code_generator.CodeValidator"
                ) as mock_validator_class:
                    # Setup mocks
                    mock_parser = MagicMock()
                    mock_parser.parse_examples.return_value = (
                        sample_parsed_examples
                    )
                    mock_parser_class.return_value = mock_parser

                    mock_agent = MagicMock()
                    mock_agent.plan = AsyncMock(return_value=sample_plan)
                    mock_agent.code = AsyncMock(
                        return_value=sample_generated_code
                    )
                    mock_agent_class.return_value = mock_agent

                    mock_validator = MagicMock()
                    mock_validation_result = CodeValidationResult(
                        is_valid=True,
                        syntax_valid=True,
                        has_type_hints=True,
                        has_docstrings=True,
                        has_tests=True,
                        implements_interface=True,
                    )
                    mock_validator.validate.return_value = (
                        mock_validation_result
                    )
                    mock_validator_class.return_value = mock_validator

                    # Create service and run generation WITHOUT progress callback
                    service = CodeGeneratorService(output_dir=temp_output_dir)
                    context = await service.generate(
                        examples=sample_examples,
                        project_config=sample_project_config,
                        validate=True,
                        write_files=True,
                        on_progress=None,  # Explicitly None
                    )

        # Should complete successfully
        assert context.is_complete
        assert context.generated_code is not None


# ============================================================================
# TEST: Rollback Mechanism
# ============================================================================


class TestRollbackMechanism:
    """Test rollback mechanism on pipeline failure."""

    @pytest.mark.asyncio
    @pytest.mark.requires_api
    async def test_rollback_deletes_files_on_failure(
        self,
        require_api_key,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that generated files are deleted on failure."""
        # Track progress updates
        progress_updates: List[GenerationProgress] = []

        def on_progress(progress: GenerationProgress):
            progress_updates.append(progress)

        # Mock dependencies with failure in validation
        with patch(
            "extract_transform_platform.services.codegen.code_generator.ExampleParser"
        ) as mock_parser_class:
            with patch(
                "extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"
            ) as mock_agent_class:
                with patch(
                    "extract_transform_platform.services.codegen.code_generator.CodeValidator"
                ) as mock_validator_class:
                    # Setup mocks
                    mock_parser = MagicMock()
                    mock_parser.parse_examples.return_value = (
                        sample_parsed_examples
                    )
                    mock_parser_class.return_value = mock_parser

                    mock_agent = MagicMock()
                    mock_agent.plan = AsyncMock(return_value=sample_plan)
                    mock_agent.code = AsyncMock(
                        return_value=sample_generated_code
                    )
                    mock_agent_class.return_value = mock_agent

                    # Validator always fails
                    mock_validator = MagicMock()
                    mock_validation_result = CodeValidationResult(
                        is_valid=False,  # FAIL
                        syntax_valid=False,
                        issues=["Syntax error on line 5"],
                    )
                    mock_validator.validate.return_value = (
                        mock_validation_result
                    )
                    mock_validator_class.return_value = mock_validator

                    # Create service
                    service = CodeGeneratorService(output_dir=temp_output_dir)

                    # Should raise ValueError after max retries
                    with pytest.raises(
                        ValueError, match="Code validation failed after"
                    ):
                        await service.generate(
                            examples=sample_examples,
                            project_config=sample_project_config,
                            validate=True,
                            write_files=True,
                            max_retries=2,  # Fail after 2 attempts
                            on_progress=on_progress,
                        )

        # Verify output directory was deleted (rollback)
        project_dir = temp_output_dir / "test_project"
        assert not project_dir.exists(), "Rollback should have deleted project directory"

        # Verify failure was reported in progress
        failed_updates = [p for p in progress_updates if p.status == "failed"]
        assert len(failed_updates) > 0, "Should have reported failure"


# ============================================================================
# TEST: Validation and File Writing Skip
# ============================================================================


class TestOptionalSteps:
    """Test skipping optional pipeline steps."""

    @pytest.mark.asyncio
    @pytest.mark.requires_api
    async def test_validation_skipped_when_disabled(
        self,
        require_api_key,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that validation step is skipped when disabled."""
        progress_updates: List[GenerationProgress] = []

        def on_progress(progress: GenerationProgress):
            progress_updates.append(progress)

        # Mock dependencies
        with patch(
            "extract_transform_platform.services.codegen.code_generator.ExampleParser"
        ) as mock_parser_class:
            with patch(
                "extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"
            ) as mock_agent_class:
                # Setup mocks
                mock_parser = MagicMock()
                mock_parser.parse_examples.return_value = sample_parsed_examples
                mock_parser_class.return_value = mock_parser

                mock_agent = MagicMock()
                mock_agent.plan = AsyncMock(return_value=sample_plan)
                mock_agent.code = AsyncMock(return_value=sample_generated_code)
                mock_agent_class.return_value = mock_agent

                # Create service and run generation WITHOUT validation
                service = CodeGeneratorService(output_dir=temp_output_dir)
                context = await service.generate(
                    examples=sample_examples,
                    project_config=sample_project_config,
                    validate=False,  # DISABLED
                    write_files=False,
                    on_progress=on_progress,
                )

        # Verify validation step was skipped
        validation_updates = [
            p for p in progress_updates if p.current_step == 4
        ]
        assert any(
            p.status == "skipped" for p in validation_updates
        ), "Validation should be skipped"

    @pytest.mark.asyncio
    @pytest.mark.requires_api
    async def test_file_writing_skipped_when_disabled(
        self,
        require_api_key,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that file writing step is skipped when disabled."""
        progress_updates: List[GenerationProgress] = []

        def on_progress(progress: GenerationProgress):
            progress_updates.append(progress)

        # Mock dependencies
        with patch(
            "extract_transform_platform.services.codegen.code_generator.ExampleParser"
        ) as mock_parser_class:
            with patch(
                "extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"
            ) as mock_agent_class:
                with patch(
                    "extract_transform_platform.services.codegen.code_generator.CodeValidator"
                ) as mock_validator_class:
                    # Setup mocks
                    mock_parser = MagicMock()
                    mock_parser.parse_examples.return_value = (
                        sample_parsed_examples
                    )
                    mock_parser_class.return_value = mock_parser

                    mock_agent = MagicMock()
                    mock_agent.plan = AsyncMock(return_value=sample_plan)
                    mock_agent.code = AsyncMock(
                        return_value=sample_generated_code
                    )
                    mock_agent_class.return_value = mock_agent

                    mock_validator = MagicMock()
                    mock_validation_result = CodeValidationResult(
                        is_valid=True, syntax_valid=True
                    )
                    mock_validator.validate.return_value = (
                        mock_validation_result
                    )
                    mock_validator_class.return_value = mock_validator

                    # Create service and run generation WITHOUT file writing
                    service = CodeGeneratorService(output_dir=temp_output_dir)
                    context = await service.generate(
                        examples=sample_examples,
                        project_config=sample_project_config,
                        validate=True,
                        write_files=False,  # DISABLED
                        on_progress=on_progress,
                    )

        # Verify file writing step was skipped
        file_writing_updates = [
            p for p in progress_updates if p.current_step == 5
        ]
        assert any(
            p.status == "skipped" for p in file_writing_updates
        ), "File writing should be skipped"

        # Verify no files were created
        project_dir = temp_output_dir / "test_project"
        assert not project_dir.exists(), "No files should be created when write_files=False"


# ============================================================================
# TEST: Dry-Run Mode (T11)
# ============================================================================


class TestDryRunMode:
    """Test dry-run mode (write_files=False) for T11."""

    @pytest.mark.asyncio
    @pytest.mark.requires_api
    async def test_dry_run_generates_code_without_writing(
        self,
        require_api_key,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that dry-run generates code but doesn't write files."""
        # Mock dependencies
        with patch(
            "extract_transform_platform.services.codegen.code_generator.ExampleParser"
        ) as mock_parser_class:
            with patch(
                "extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"
            ) as mock_agent_class:
                with patch(
                    "extract_transform_platform.services.codegen.code_generator.CodeValidator"
                ) as mock_validator_class:
                    # Setup mocks
                    mock_parser = MagicMock()
                    mock_parser.parse_examples.return_value = sample_parsed_examples
                    mock_parser_class.return_value = mock_parser

                    mock_agent = MagicMock()
                    mock_agent.plan = AsyncMock(return_value=sample_plan)
                    mock_agent.code = AsyncMock(return_value=sample_generated_code)
                    mock_agent_class.return_value = mock_agent

                    mock_validator = MagicMock()
                    mock_validation_result = CodeValidationResult(
                        is_valid=True,
                        syntax_valid=True,
                        has_type_hints=True,
                        has_docstrings=True,
                        has_tests=True,
                        implements_interface=True,
                    )
                    mock_validator.validate.return_value = mock_validation_result
                    mock_validator_class.return_value = mock_validator

                    # Create service and run generation in DRY-RUN mode
                    service = CodeGeneratorService(output_dir=temp_output_dir)
                    context = await service.generate(
                        examples=sample_examples,
                        project_config=sample_project_config,
                        validate=True,
                        write_files=False,  # Dry-run
                    )

        # Code should be generated
        assert context.generated_code is not None
        assert context.generated_code.extractor_code
        assert context.generated_code.models_code
        assert context.generated_code.tests_code
        assert context.generated_code.total_lines > 0

        # But files should NOT exist
        project_dir = temp_output_dir / "test_project"
        assert not project_dir.exists(), "Dry-run should not create any files"
        assert not (project_dir / "extractor.py").exists()
        assert not (project_dir / "models.py").exists()
        assert not (project_dir / "test_extractor.py").exists()

    @pytest.mark.asyncio
    @pytest.mark.requires_api
    async def test_dry_run_progress_message(
        self,
        require_api_key,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that dry-run shows correct progress message."""
        progress_messages = []

        def capture_progress(progress):
            if progress.message:
                progress_messages.append(progress.message)

        # Mock dependencies
        with patch(
            "extract_transform_platform.services.codegen.code_generator.ExampleParser"
        ) as mock_parser_class:
            with patch(
                "extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"
            ) as mock_agent_class:
                with patch(
                    "extract_transform_platform.services.codegen.code_generator.CodeValidator"
                ) as mock_validator_class:
                    # Setup mocks
                    mock_parser = MagicMock()
                    mock_parser.parse_examples.return_value = sample_parsed_examples
                    mock_parser_class.return_value = mock_parser

                    mock_agent = MagicMock()
                    mock_agent.plan = AsyncMock(return_value=sample_plan)
                    mock_agent.code = AsyncMock(return_value=sample_generated_code)
                    mock_agent_class.return_value = mock_agent

                    mock_validator = MagicMock()
                    mock_validation_result = CodeValidationResult(
                        is_valid=True, syntax_valid=True
                    )
                    mock_validator.validate.return_value = mock_validation_result
                    mock_validator_class.return_value = mock_validator

                    # Create service
                    service = CodeGeneratorService(output_dir=temp_output_dir)

                    await service.generate(
                        examples=sample_examples,
                        project_config=sample_project_config,
                        validate=True,
                        write_files=False,
                        on_progress=capture_progress,
                    )

        # Should contain dry-run message
        assert any(
            "Dry-run mode" in msg or "preview only" in msg
            for msg in progress_messages
        ), f"Expected dry-run message in: {progress_messages}"

    @pytest.mark.asyncio
    @pytest.mark.requires_api
    async def test_dry_run_with_validation_failure_no_rollback(
        self,
        require_api_key,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that validation failure in dry-run doesn't trigger rollback."""
        # This test verifies that write_files=False prevents rollback attempts
        # (Since no files were written, there's nothing to roll back)

        # Mock dependencies with failing validation
        with patch(
            "extract_transform_platform.services.codegen.code_generator.ExampleParser"
        ) as mock_parser_class:
            with patch(
                "extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"
            ) as mock_agent_class:
                with patch(
                    "extract_transform_platform.services.codegen.code_generator.CodeValidator"
                ) as mock_validator_class:
                    # Setup mocks
                    mock_parser = MagicMock()
                    mock_parser.parse_examples.return_value = sample_parsed_examples
                    mock_parser_class.return_value = mock_parser

                    mock_agent = MagicMock()
                    mock_agent.plan = AsyncMock(return_value=sample_plan)
                    mock_agent.code = AsyncMock(return_value=sample_generated_code)
                    mock_agent_class.return_value = mock_agent

                    # Validator always fails
                    mock_validator = MagicMock()
                    mock_validation_result = CodeValidationResult(
                        is_valid=False,  # FAIL
                        syntax_valid=False,
                        issues=["Syntax error on line 5"],
                    )
                    mock_validator.validate.return_value = mock_validation_result
                    mock_validator_class.return_value = mock_validator

                    # Create service
                    service = CodeGeneratorService(output_dir=temp_output_dir)

                    # Should raise ValueError after max retries
                    with pytest.raises(
                        ValueError, match="Code validation failed after"
                    ):
                        await service.generate(
                            examples=sample_examples,
                            project_config=sample_project_config,
                            validate=True,
                            write_files=False,  # Dry-run
                            max_retries=2,
                        )

        # No rollback should occur because no files were written
        # (This is implicitly tested by the exception being raised)

    @pytest.mark.asyncio
    @pytest.mark.requires_api
    async def test_dry_run_skips_file_writing_step(
        self,
        require_api_key,
        temp_output_dir,
        sample_project_config,
        sample_examples,
        sample_parsed_examples,
        sample_plan,
        sample_generated_code,
    ):
        """Test that dry-run marks file writing step as skipped."""
        progress_updates: List[GenerationProgress] = []

        def on_progress(progress: GenerationProgress):
            progress_updates.append(progress)

        # Mock dependencies
        with patch(
            "extract_transform_platform.services.codegen.code_generator.ExampleParser"
        ) as mock_parser_class:
            with patch(
                "extract_transform_platform.services.codegen.code_generator.Sonnet45Agent"
            ) as mock_agent_class:
                with patch(
                    "extract_transform_platform.services.codegen.code_generator.CodeValidator"
                ) as mock_validator_class:
                    # Setup mocks
                    mock_parser = MagicMock()
                    mock_parser.parse_examples.return_value = sample_parsed_examples
                    mock_parser_class.return_value = mock_parser

                    mock_agent = MagicMock()
                    mock_agent.plan = AsyncMock(return_value=sample_plan)
                    mock_agent.code = AsyncMock(return_value=sample_generated_code)
                    mock_agent_class.return_value = mock_agent

                    mock_validator = MagicMock()
                    mock_validation_result = CodeValidationResult(
                        is_valid=True, syntax_valid=True
                    )
                    mock_validator.validate.return_value = mock_validation_result
                    mock_validator_class.return_value = mock_validator

                    # Create service
                    service = CodeGeneratorService(output_dir=temp_output_dir)

                    await service.generate(
                        examples=sample_examples,
                        project_config=sample_project_config,
                        validate=True,
                        write_files=False,  # Dry-run
                        on_progress=on_progress,
                    )

        # Verify file writing step was skipped
        file_writing_updates = [p for p in progress_updates if p.current_step == 5]
        assert any(
            p.status == "skipped" for p in file_writing_updates
        ), "File writing should be skipped in dry-run mode"
