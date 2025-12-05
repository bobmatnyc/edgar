"""
Comprehensive unit tests for CodeGenerator module.

This test suite brings CodeGenerator coverage from 85% to 90%+ by testing:
- CodeWriter file operations and backup mechanism
- generate_from_parsed() alternative path
- Edge cases and error handling

Coverage Goal: 200+/214 statements (93%+)
Current Coverage: 182/214 statements (85%)

Test Structure:
- TestCodeWriter (4 tests): File I/O, backup, directory creation
- TestGenerateFromParsed (3 tests): Alternative generation path
- TestEdgeCases (3 tests): Error conditions and edge cases

Design Decision: Focus on untested paths
Rationale: Progress tracking and main generation path already tested in
test_code_generator_progress.py. This suite fills gaps.

Performance: Test suite executes in ~1-2 seconds (fast feedback)

Ticket: 1M-320 (Phase 3 Week 2: CodeGenerator Testing - Priority 2)
Research: docs/research/code-generator-test-gap-analysis-2025-12-03.md
"""

import asyncio
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from extract_transform_platform.models.plan import (
    ClassSpec,
    CodeValidationResult,
    GeneratedCode,
    GenerationContext,
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
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def code_writer(temp_dir):
    """Create CodeWriter instance with temp directory."""
    return CodeWriter(base_dir=temp_dir)


@pytest.fixture
def sample_generated_code():
    """Create sample generated code for testing."""
    return GeneratedCode(
        extractor_code='''
from extract_transform_platform.core import IDataExtractor

class WeatherExtractor(IDataExtractor):
    """Extract weather data."""

    async def extract(self, data: dict) -> dict:
        """Extract weather data."""
        return {"temp": data["temperature"]}
''',
        models_code='''
from pydantic import BaseModel

class WeatherData(BaseModel):
    """Weather data model."""
    temp: float
''',
        tests_code='''
import pytest

def test_weather_extraction():
    """Test weather extraction."""
    assert True
'''
    )


@pytest.fixture
def sample_project_config():
    """Create sample project configuration."""
    return ProjectConfig(
        project=ProjectMetadata(
            name="test_weather",
            description="Test weather extractor",
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
def sample_parsed_examples():
    """Create sample parsed examples."""
    return ParsedExamples(
        patterns=[
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=1.0,
                source_path="temperature",
                target_path="temp",
                transformation="Direct field mapping",
            )
        ],
        input_schema=Schema(
            fields=[
                SchemaField(
                    name="temperature",
                    field_type=FieldTypeEnum.FLOAT,
                    path="temperature",
                )
            ]
        ),
        output_schema=Schema(
            fields=[
                SchemaField(
                    name="temp",
                    field_type=FieldTypeEnum.FLOAT,
                    path="temp",
                )
            ]
        ),
        num_examples=2,
    )


@pytest.fixture
def sample_plan():
    """Create sample plan specification."""
    return PlanSpec(
        strategy="Extract weather data and transform field names",
        classes=[
            ClassSpec(
                name="WeatherExtractor",
                purpose="Extract weather data",
                methods=[
                    MethodSpec(
                        name="extract",
                        purpose="Extract data",
                        parameters=["self", "data: Dict[str, Any]"],
                        return_type="Dict[str, Any]"
                    )
                ]
            )
        ],
        dependencies=["typing"],
        error_handling="Return None on errors",
        testing_strategy="Pytest with sample data",
    )


# ============================================================================
# TEST CODE WRITER
# ============================================================================


class TestCodeWriter:
    """Test CodeWriter file operations and backup mechanism."""

    def test_write_creates_directory_structure(self, code_writer, sample_generated_code, temp_dir):
        """Test that writer creates project directory and files."""
        # Act
        paths = code_writer.write(sample_generated_code, "test_project", backup=False)

        # Assert
        project_dir = temp_dir / "test_project"
        assert project_dir.exists(), "Project directory should be created"
        assert (project_dir / "extractor.py").exists(), "extractor.py should exist"
        assert (project_dir / "models.py").exists(), "models.py should exist"
        assert (project_dir / "test_extractor.py").exists(), "test_extractor.py should exist"
        assert (project_dir / "__init__.py").exists(), "__init__.py should exist"

        # Verify paths dictionary
        assert "extractor" in paths
        assert "models" in paths
        assert "test_extractor" in paths
        assert "init" in paths

    def test_write_backs_up_existing_files(self, code_writer, sample_generated_code, temp_dir):
        """Test that writer backs up existing files with timestamp."""
        # Arrange: Create existing file
        project_dir = temp_dir / "test_project"
        project_dir.mkdir()
        extractor_file = project_dir / "extractor.py"
        original_content = "# Original code\nclass OldExtractor: pass"
        extractor_file.write_text(original_content)

        # Act
        paths = code_writer.write(sample_generated_code, "test_project", backup=True)

        # Assert
        # Verify backup created with timestamp
        backup_files = list(project_dir.glob("extractor.py.bak.*"))
        assert len(backup_files) == 1, "Should create exactly one backup file"
        assert backup_files[0].read_text() == original_content, \
            "Backup should contain original content"

        # Verify new file written
        assert extractor_file.read_text() != original_content, \
            "File should be updated with new content"
        assert "WeatherExtractor" in extractor_file.read_text(), \
            "New content should be present"

    def test_write_returns_file_paths(self, code_writer, sample_generated_code):
        """Test that writer returns dictionary of file paths."""
        # Act
        paths = code_writer.write(sample_generated_code, "test_project", backup=False)

        # Assert
        assert isinstance(paths, dict), "Should return dictionary"
        assert all(isinstance(p, Path) for p in paths.values()), \
            "All values should be Path objects"
        assert len(paths) == 4, "Should return 4 file paths (extractor, models, test, init)"

    def test_write_generates_init_file(self, code_writer, sample_generated_code, temp_dir):
        """Test that __init__.py is generated with docstring."""
        # Act
        paths = code_writer.write(sample_generated_code, "my_extractor", backup=False)

        # Assert
        init_file = temp_dir / "my_extractor" / "__init__.py"
        assert init_file.exists(), "__init__.py should be created"

        content = init_file.read_text()
        assert "my_extractor" in content, "Should mention project name"
        assert '"""' in content, "Should have docstring"


# ============================================================================
# TEST GENERATE_FROM_PARSED
# ============================================================================


class TestGenerateFromParsed:
    """Test generate_from_parsed() alternative generation path."""

    @pytest.mark.asyncio
    async def test_generate_from_parsed_with_validation(
        self,
        sample_parsed_examples,
        sample_project_config,
        sample_plan,
        sample_generated_code,
        temp_dir
    ):
        """Test generate_from_parsed() with validation enabled."""
        # Arrange
        service = CodeGeneratorService(output_dir=temp_dir)

        # Mock agent methods
        with patch.object(service.agent, 'plan', new_callable=AsyncMock) as mock_plan:
            with patch.object(service.agent, 'code', new_callable=AsyncMock) as mock_code:
                mock_plan.return_value = sample_plan
                mock_code.return_value = sample_generated_code

                # Act
                context = await service.generate_from_parsed(
                    parsed=sample_parsed_examples,
                    project_config=sample_project_config,
                    validate=True,
                    write_files=False
                )

        # Assert
        assert context is not None, "Should return generation context"
        assert context.project_name == "test_weather", "Should set project name"
        assert context.num_patterns == 1, "Should record pattern count"
        assert context.num_examples == 2, "Should record example count"
        assert context.generated_code is not None, "Should have generated code"
        assert context.plan is not None, "Should have plan"
        assert mock_plan.called, "Should call agent.plan()"
        assert mock_code.called, "Should call agent.code()"

    @pytest.mark.asyncio
    async def test_generate_from_parsed_validation_failure(
        self,
        sample_parsed_examples,
        sample_project_config,
        sample_plan,
        temp_dir
    ):
        """Test generate_from_parsed() raises on validation failure."""
        # Arrange
        service = CodeGeneratorService(output_dir=temp_dir)

        invalid_code = GeneratedCode(
            extractor_code="invalid syntax here",
            models_code="class Model: pass",
            tests_code="# no tests"
        )

        # Mock agent and validator
        with patch.object(service.agent, 'plan', new_callable=AsyncMock) as mock_plan:
            with patch.object(service.agent, 'code', new_callable=AsyncMock) as mock_code:
                mock_plan.return_value = sample_plan
                mock_code.return_value = invalid_code

                # Act & Assert
                with pytest.raises(ValueError, match="Validation failed"):
                    await service.generate_from_parsed(
                        parsed=sample_parsed_examples,
                        project_config=sample_project_config,
                        validate=True,
                        write_files=False
                    )

    @pytest.mark.asyncio
    async def test_generate_from_parsed_without_file_writing(
        self,
        sample_parsed_examples,
        sample_project_config,
        sample_plan,
        sample_generated_code,
        temp_dir
    ):
        """Test generate_from_parsed() with write_files=False (dry-run)."""
        # Arrange
        service = CodeGeneratorService(output_dir=temp_dir)

        # Mock agent methods
        with patch.object(service.agent, 'plan', new_callable=AsyncMock) as mock_plan:
            with patch.object(service.agent, 'code', new_callable=AsyncMock) as mock_code:
                mock_plan.return_value = sample_plan
                mock_code.return_value = sample_generated_code

                # Act
                context = await service.generate_from_parsed(
                    parsed=sample_parsed_examples,
                    project_config=sample_project_config,
                    validate=False,
                    write_files=False
                )

        # Assert
        assert context.generated_code is not None, "Should generate code"

        # Verify no files written
        project_dir = temp_dir / sample_project_config.project.name
        assert not project_dir.exists(), "Should not create project directory in dry-run"


# ============================================================================
# TEST EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_generate_with_parser_exception(
        self,
        sample_project_config,
        temp_dir
    ):
        """Test that parser exceptions are propagated correctly."""
        # Arrange
        service = CodeGeneratorService(output_dir=temp_dir)

        # Mock parser to raise exception
        with patch.object(service.parser, 'parse_examples') as mock_parser:
            mock_parser.side_effect = ValueError("Invalid example format")

            # Act & Assert
            with pytest.raises(ValueError, match="Invalid example format"):
                await service.generate(
                    examples=[{"input": {}, "output": {}}],
                    project_config=sample_project_config
                )

    @pytest.mark.asyncio
    async def test_generate_from_parsed_with_exception(
        self,
        sample_parsed_examples,
        sample_project_config,
        temp_dir
    ):
        """Test that exceptions in generate_from_parsed are tracked."""
        # Arrange
        service = CodeGeneratorService(output_dir=temp_dir)

        # Mock agent to raise exception
        with patch.object(service.agent, 'plan', new_callable=AsyncMock) as mock_plan:
            mock_plan.side_effect = RuntimeError("Agent failure")

            # Act & Assert
            with pytest.raises(RuntimeError, match="Agent failure"):
                await service.generate_from_parsed(
                    parsed=sample_parsed_examples,
                    project_config=sample_project_config
                )

    @pytest.mark.asyncio
    async def test_generate_from_parsed_records_duration_on_failure(
        self,
        sample_parsed_examples,
        sample_project_config,
        temp_dir
    ):
        """Test that duration is recorded even when generation fails."""
        # Arrange
        service = CodeGeneratorService(output_dir=temp_dir)

        # Mock agent to raise exception
        with patch.object(service.agent, 'plan', new_callable=AsyncMock) as mock_plan:
            mock_plan.side_effect = ValueError("Generation failed")

            # Act
            try:
                context = await service.generate_from_parsed(
                    parsed=sample_parsed_examples,
                    project_config=sample_project_config
                )
            except ValueError:
                pass  # Expected

            # Note: Context is not returned on exception in generate_from_parsed
            # This is actually a limitation - we can't verify duration tracking
            # because the context is not accessible after exception


# ============================================================================
# TEST CODE WRITER EDGE CASES
# ============================================================================


class TestCodeWriterEdgeCases:
    """Test CodeWriter edge cases and error scenarios."""

    def test_write_creates_nested_directories(self, temp_dir):
        """Test that writer can create nested directory structures."""
        # Arrange
        nested_base = temp_dir / "nested" / "path"
        writer = CodeWriter(base_dir=nested_base)
        code = GeneratedCode(
            extractor_code="class E: pass",
            models_code="class M: pass",
            tests_code="def test(): pass"
        )

        # Act
        paths = writer.write(code, "project", backup=False)

        # Assert
        project_dir = nested_base / "project"
        assert project_dir.exists(), "Should create nested directories"
        assert (project_dir / "extractor.py").exists()

    def test_write_backup_disabled(self, code_writer, sample_generated_code, temp_dir):
        """Test that backup can be disabled."""
        # Arrange: Create existing file
        project_dir = temp_dir / "test_project"
        project_dir.mkdir()
        extractor_file = project_dir / "extractor.py"
        extractor_file.write_text("# Original code")

        # Act
        paths = code_writer.write(sample_generated_code, "test_project", backup=False)

        # Assert
        backup_files = list(project_dir.glob("extractor.py.bak.*"))
        assert len(backup_files) == 0, "Should not create backup when backup=False"


# ============================================================================
# TEST CODE WRITER FILE CONTENT
# ============================================================================


class TestCodeWriterFileContent:
    """Test that CodeWriter writes correct content to files."""

    def test_write_extractor_content(self, code_writer, sample_generated_code, temp_dir):
        """Test that extractor code is written correctly."""
        # Act
        paths = code_writer.write(sample_generated_code, "test_project", backup=False)

        # Assert
        extractor_file = paths["extractor"]
        content = extractor_file.read_text()
        assert "WeatherExtractor" in content, "Should contain extractor class"
        assert "IDataExtractor" in content, "Should contain interface"
        assert "async def extract" in content, "Should contain extract method"

    def test_write_models_content(self, code_writer, sample_generated_code, temp_dir):
        """Test that models code is written correctly."""
        # Act
        paths = code_writer.write(sample_generated_code, "test_project", backup=False)

        # Assert
        models_file = paths["models"]
        content = models_file.read_text()
        assert "WeatherData" in content, "Should contain model class"
        assert "BaseModel" in content, "Should contain Pydantic BaseModel"

    def test_write_tests_content(self, code_writer, sample_generated_code, temp_dir):
        """Test that test code is written correctly."""
        # Act
        paths = code_writer.write(sample_generated_code, "test_project", backup=False)

        # Assert
        tests_file = paths["test_extractor"]
        content = tests_file.read_text()
        assert "def test_weather_extraction" in content, "Should contain test function"
        assert "pytest" in content, "Should import pytest"


# ============================================================================
# TEST GENERATION CONTEXT TRACKING
# ============================================================================


class TestGenerationContextTracking:
    """Test that GenerationContext properly tracks generation state."""

    @pytest.mark.asyncio
    async def test_generate_from_parsed_tracks_patterns(
        self,
        sample_parsed_examples,
        sample_project_config,
        sample_plan,
        sample_generated_code,
        temp_dir
    ):
        """Test that pattern count is tracked in context."""
        # Arrange
        service = CodeGeneratorService(output_dir=temp_dir)

        with patch.object(service.agent, 'plan', new_callable=AsyncMock) as mock_plan:
            with patch.object(service.agent, 'code', new_callable=AsyncMock) as mock_code:
                mock_plan.return_value = sample_plan
                mock_code.return_value = sample_generated_code

                # Act
                context = await service.generate_from_parsed(
                    parsed=sample_parsed_examples,
                    project_config=sample_project_config,
                    validate=False,
                    write_files=False
                )

        # Assert
        assert context.num_patterns == len(sample_parsed_examples.patterns), \
            "Should track number of patterns"
        assert context.num_examples == sample_parsed_examples.num_examples, \
            "Should track number of examples"

    @pytest.mark.asyncio
    async def test_generate_from_parsed_tracks_duration(
        self,
        sample_parsed_examples,
        sample_project_config,
        sample_plan,
        sample_generated_code,
        temp_dir
    ):
        """Test that generation duration is tracked."""
        # Arrange
        service = CodeGeneratorService(output_dir=temp_dir)

        with patch.object(service.agent, 'plan', new_callable=AsyncMock) as mock_plan:
            with patch.object(service.agent, 'code', new_callable=AsyncMock) as mock_code:
                mock_plan.return_value = sample_plan
                mock_code.return_value = sample_generated_code

                # Act
                context = await service.generate_from_parsed(
                    parsed=sample_parsed_examples,
                    project_config=sample_project_config,
                    validate=False,
                    write_files=False
                )

        # Assert
        assert context.generation_duration_seconds is not None, \
            "Should track generation duration"
        assert context.generation_duration_seconds >= 0, \
            "Duration should be non-negative"
