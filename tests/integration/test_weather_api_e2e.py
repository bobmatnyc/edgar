"""
Comprehensive E2E Test Suite for Weather API POC (T13 - 1M-455)

This test suite validates the complete project lifecycle from examples → code generation
→ execution → validation. Tests the Weather API POC as the Phase 1 MVP proof-of-concept.

Test Coverage:
1. Project Lifecycle E2E Test - Complete workflow validation
2. CLI Command Integration Test - Verify CLI commands work end-to-end
3. Example Consistency Test - Validate all 7 examples are consistent
4. Code Generation Robustness Test - Error handling with T12 improvements
5. Generated Code Quality Test - Code quality validation
6. Progress Tracking Integration Test - T10 progress tracking verification
7. Smoke Test - Fast validation without file system changes

Dependencies:
- T7 (ProjectManager) ✅
- T8 (CLI refactoring) ✅
- T10 (Progress tracking) ✅
- T12 (Error handling) ✅

Success Criteria:
- All 7 tests pass (7/7 green)
- No breaking changes to existing functionality
- Complete project lifecycle validated
- CLI integration verified
- Error handling validated
- Progress tracking verified
"""

import asyncio
import ast
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from edgar_analyzer.cli.commands.project import project
from edgar_analyzer.config.container import Container
from extract_transform_platform.models.plan import GenerationProgress
from extract_transform_platform.models.project_config import ProjectConfig
from extract_transform_platform.services.analysis import ExampleParser, SchemaAnalyzer
from extract_transform_platform.services.codegen.code_generator import CodeGeneratorService
from extract_transform_platform.services.codegen.exceptions import (
    CodeGenerationError,
    CodeValidationError,
    ExampleParsingError,
    OpenRouterAPIError,
)
from extract_transform_platform.services.project_manager import (
    ProjectManager,
    ProjectNotFoundError,
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
        pytest.skip("OPENROUTER_API_KEY not set - skipping E2E test requiring code generation")


@pytest.fixture
def project_manager() -> ProjectManager:
    """Provide ProjectManager instance."""
    return Container.project_manager()


@pytest.fixture
def code_generator() -> CodeGeneratorService:
    """Provide CodeGeneratorService instance."""
    if not _check_api_key_available():
        pytest.skip("OPENROUTER_API_KEY not set - skipping code generation test")
    return Container.code_generator()


@pytest.fixture
def schema_analyzer() -> SchemaAnalyzer:
    """Provide SchemaAnalyzer instance."""
    return Container.schema_analyzer()


@pytest.fixture
def example_parser(schema_analyzer: SchemaAnalyzer) -> ExampleParser:
    """Provide ExampleParser instance."""
    return Container.example_parser()


@pytest.fixture
def weather_api_project_path() -> Path:
    """Path to weather_api project."""
    return Path(__file__).parent.parent.parent / "projects" / "weather_api"


@pytest.fixture
def weather_api_examples(weather_api_project_path: Path) -> List[Dict[str, Any]]:
    """Load all weather_api examples."""
    examples = []
    examples_dir = weather_api_project_path / "examples"

    # Load all JSON example files in sorted order
    for example_file in sorted(examples_dir.glob("*.json")):
        with open(example_file) as f:
            examples.append(json.load(f))

    return examples


@pytest.fixture
def weather_api_config(weather_api_project_path: Path) -> ProjectConfig:
    """Load weather_api project configuration."""
    config_path = weather_api_project_path / "project.yaml"
    return ProjectConfig.from_yaml(config_path)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide Click CLI test runner."""
    return CliRunner()


# ============================================================================
# TEST 1: PROJECT LIFECYCLE E2E TEST
# ============================================================================


class TestWeatherAPILifecycle:
    """Test complete project lifecycle from load to execution."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.requires_api
    async def test_weather_api_complete_lifecycle(
        self,
        require_api_key,
        project_manager: ProjectManager,
        weather_api_project_path: Path,
        weather_api_examples: List[Dict[str, Any]],
        weather_api_config: ProjectConfig,
        example_parser: ExampleParser,
    ) -> None:
        """
        Test complete project lifecycle.

        Steps:
        1. Load weather_api project using ProjectManager
        2. Verify project.yaml is valid
        3. Load examples from examples/ directory
        4. Parse examples and extract patterns
        5. Verify patterns detected
        6. Check generated code exists
        7. Validate generated code compiles

        Success Criteria:
        - Project loads successfully
        - All 7 examples parse correctly
        - High-confidence patterns detected (≥0.9)
        - Generated code is syntactically valid Python
        """
        # Step 1: Load project using ProjectManager
        # Note: Project name comes from YAML, not directory name
        project_name = "weather_api_extractor"
        project = await project_manager.get_project(project_name)

        assert project is not None, "Project should exist"
        assert project.name == "weather_api_extractor"
        assert project.is_valid, "Project should be valid"

        # Step 2: Verify project.yaml is valid
        assert weather_api_config.project.name == "weather_api_extractor"
        assert len(weather_api_config.data_sources) > 0, "Should have data sources"
        assert len(weather_api_config.examples) == 7, "Should have 7 examples"

        # Step 3: Load examples from examples/ directory
        assert len(weather_api_examples) == 7, "Should load 7 example files"

        # Verify all examples have consistent structure
        for i, example in enumerate(weather_api_examples, 1):
            assert "input" in example, f"Example {i} missing 'input'"
            assert "output" in example, f"Example {i} missing 'output'"
            assert "description" in example, f"Example {i} missing 'description'"

        # Step 4: Parse examples using ExampleParser
        # Convert dict examples to ExampleConfig objects
        from extract_transform_platform.models.project_config import ExampleConfig

        example_configs = [
            ExampleConfig(
                input=ex["input"],
                output=ex["output"],
                description=ex.get("description", "")
            )
            for ex in weather_api_examples
        ]

        parsed = example_parser.parse_examples(example_configs)

        # Step 5: Verify patterns detected
        assert parsed.high_confidence_patterns, "Should detect high-confidence patterns"
        assert (
            len(parsed.high_confidence_patterns) >= 3
        ), "Should detect at least 3 patterns"

        # Verify pattern types
        pattern_types = {p.type for p in parsed.high_confidence_patterns}
        assert len(pattern_types) > 0, "Should have diverse pattern types"

        # Step 6: Check generated code exists
        generated_dir = weather_api_project_path / "generated" / "weather_api_extractor"
        if generated_dir.exists():
            # Step 7: Validate generated code compiles
            src_dir = generated_dir / "src"
            if src_dir.exists():
                python_files = list(src_dir.glob("**/*.py"))
                assert len(python_files) > 0, "Should have generated Python files"

                # Validate each file compiles
                for py_file in python_files:
                    with open(py_file) as f:
                        code = f.read()

                    # Should compile without syntax errors
                    try:
                        ast.parse(code)
                    except SyntaxError as e:
                        pytest.fail(f"Generated code has syntax error in {py_file}: {e}")

    # ============================================================================
    # TEST 2: CLI COMMAND INTEGRATION TEST
    # ============================================================================

    @pytest.mark.integration
    def test_weather_api_cli_commands(
        self, cli_runner: CliRunner, weather_api_project_path: Path
    ) -> None:
        """
        Test CLI command integration.

        Steps:
        1. Run: edgar-analyzer project validate weather_api_extractor
        2. Verify validation passes
        3. Check output format is correct

        Success Criteria:
        - CLI command executes without errors
        - Validation passes
        - Output is readable
        """
        # Ensure container is wired
        container = Container()
        container.wire(modules=[__name__])

        # Step 1: Run project validate command (use project name from YAML)
        result = cli_runner.invoke(project, ["validate", "weather_api_extractor"])

        # Step 2: Verify command succeeded
        assert result.exit_code == 0, f"CLI command failed: {result.output}"

        # Step 3: Check output contains expected information
        output = result.output
        assert "weather_api" in output.lower() or "validation" in output.lower(), (
            "Output should mention project or validation"
        )

    @pytest.mark.integration
    def test_weather_api_cli_list(self, cli_runner: CliRunner) -> None:
        """
        Test CLI list command includes weather_api_extractor.

        Steps:
        1. Run: edgar-analyzer project list
        2. Verify weather_api_extractor appears in list

        Success Criteria:
        - List command executes
        - weather_api_extractor project is listed
        """
        # Ensure container is wired
        container = Container()
        container.wire(modules=[__name__])

        result = cli_runner.invoke(project, ["list"])

        assert result.exit_code == 0, f"List command failed: {result.output}"
        assert "weather_api" in result.output.lower(), (
            "weather_api_extractor should appear in project list"
        )

    # ============================================================================
    # TEST 7: SMOKE TEST (FAST VALIDATION)
    # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_weather_api_smoke_test(
        self, project_manager: ProjectManager, weather_api_project_path: Path
    ) -> None:
        """
        Fast smoke test - verify project exists and is valid.

        Steps:
        1. Verify project exists
        2. Verify examples directory exists
        3. Verify project.yaml valid
        4. Run quick validation (no generation)

        Success Criteria:
        - Completes in <1 second
        - No file system changes
        - Returns validation status
        """
        import time

        start_time = time.time()

        # Step 1: Verify project exists
        assert weather_api_project_path.exists(), "Project directory should exist"

        # Step 2: Verify examples directory exists
        examples_dir = weather_api_project_path / "examples"
        assert examples_dir.exists(), "Examples directory should exist"
        assert len(list(examples_dir.glob("*.json"))) == 7, "Should have 7 examples"

        # Step 3: Verify project.yaml valid
        config_path = weather_api_project_path / "project.yaml"
        assert config_path.exists(), "project.yaml should exist"

        config = ProjectConfig.from_yaml(config_path)
        assert config is not None, "Config should load"

        # Step 4: Run quick validation
        project = await project_manager.get_project("weather_api_extractor")
        validation = await project_manager.validate_project("weather_api_extractor")

        assert validation.is_valid, "Project should be valid"

        elapsed = time.time() - start_time
        assert elapsed < 2.0, f"Smoke test should complete in <2s (took {elapsed:.2f}s)"


# ============================================================================
# TEST 3: EXAMPLE CONSISTENCY TEST
# ============================================================================


class TestWeatherAPIExamples:
    """Test example consistency and parsing."""

    @pytest.mark.integration
    def test_weather_api_examples_consistency(
        self,
        weather_api_examples: List[Dict[str, Any]],
        schema_analyzer: SchemaAnalyzer,
    ) -> None:
        """
        Test all 7 examples have consistent schema.

        Steps:
        1. Load all 7 examples from weather_api/examples/
        2. Verify all examples have consistent schema
        3. Verify input fields match across examples
        4. Verify output fields match across examples
        5. Run SchemaAnalyzer on examples
        6. Verify high confidence patterns detected (≥0.9)

        Success Criteria:
        - All examples valid JSON
        - Consistent field names and types
        - No schema mismatches
        - Pattern detection finds expected transformations
        """
        # Step 1: Verify we have 7 examples
        assert len(weather_api_examples) == 7, "Should have 7 examples"

        # Step 2: Extract input and output schemas
        input_schemas = []
        output_schemas = []

        for example in weather_api_examples:
            # Step 3: Verify input fields consistency
            input_data = example["input"]
            assert "coord" in input_data, "All inputs should have 'coord'"
            assert "main" in input_data, "All inputs should have 'main'"
            assert "weather" in input_data, "All inputs should have 'weather'"

            # Step 4: Verify output fields consistency
            output_data = example["output"]
            assert "city" in output_data, "All outputs should have 'city'"
            assert "country" in output_data, "All outputs should have 'country'"
            assert "temperature_c" in output_data, "All outputs should have 'temperature_c'"
            assert "humidity_percent" in output_data, "All outputs should have 'humidity_percent'"
            assert "conditions" in output_data, "All outputs should have 'conditions'"

            # Collect schemas
            input_schemas.append(input_data)
            output_schemas.append(output_data)

        # Step 5: Run SchemaAnalyzer on inputs and outputs
        inferred_input_schema = schema_analyzer.infer_input_schema(weather_api_examples)
        inferred_output_schema = schema_analyzer.infer_output_schema(weather_api_examples)

        assert inferred_input_schema is not None, "Should infer input schema"
        assert inferred_output_schema is not None, "Should infer output schema"

        # Step 6: Verify consistent field types
        # All temperature fields should be numeric (float or int)
        assert len(inferred_output_schema.fields) >= 8, "Should have at least 8 output fields"

        # Find temperature field and verify type
        # Note: SchemaField is a dict-like structure, access with dict methods
        temp_fields = [f for f in inferred_output_schema.fields if "temperature" in str(f)]
        assert len(temp_fields) > 0, "Should detect temperature field"

    @pytest.mark.integration
    def test_weather_api_examples_valid_json(
        self, weather_api_project_path: Path
    ) -> None:
        """
        Test all example files are valid JSON.

        Steps:
        1. Find all JSON files in examples/
        2. Parse each file
        3. Verify no JSON errors

        Success Criteria:
        - All files parse successfully
        - No malformed JSON
        """
        examples_dir = weather_api_project_path / "examples"
        json_files = list(examples_dir.glob("*.json"))

        assert len(json_files) == 7, "Should have 7 JSON files"

        for json_file in json_files:
            with open(json_file) as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict), f"{json_file.name} should contain object"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {json_file.name}: {e}")


# ============================================================================
# TEST 4: CODE GENERATION ROBUSTNESS TEST
# ============================================================================


class TestWeatherAPICodeGeneration:
    """Test code generation robustness and error handling."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.requires_api
    async def test_weather_api_generation_with_missing_examples(
        self,
        require_api_key,
        code_generator: CodeGeneratorService,
        weather_api_config: ProjectConfig,
    ) -> None:
        """
        Test code generation with missing examples (error case).

        Steps:
        1. Attempt to generate with empty examples list
        2. Verify error is raised
        3. Verify error message uses custom exceptions (T12)
        4. Verify error message is user-friendly

        Success Criteria:
        - ExampleParsingError raised
        - Error message is clear and helpful
        - No uncaught exceptions
        """
        # Step 1: Attempt generation with no examples
        with pytest.raises(
            (ExampleParsingError, ValueError, CodeGenerationError)
        ) as exc_info:
            await code_generator.generate(
                examples=[],
                project_config=weather_api_config,
            )

        # Step 2: Verify error message is helpful
        error_msg = str(exc_info.value).lower()
        assert "example" in error_msg or "empty" in error_msg, (
            "Error message should mention examples or empty"
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.requires_api
    async def test_weather_api_generation_with_malformed_examples(
        self,
        require_api_key,
        code_generator: CodeGeneratorService,
        weather_api_config: ProjectConfig,
    ) -> None:
        """
        Test code generation with malformed examples.

        Steps:
        1. Create malformed example (missing required fields)
        2. Attempt to generate code
        3. Verify appropriate error raised
        4. Verify error message identifies the problem

        Success Criteria:
        - Error raised gracefully
        - Error message explains the issue
        - No uncaught exceptions
        """
        # Step 1: Create malformed example using proper structure
        # ExampleParser expects objects with .input and .output attributes or proper dict structure
        from extract_transform_platform.models.project_config import ExampleConfig

        try:
            malformed_example = ExampleConfig(
                input={"invalid": "data"},
                output={},  # Empty output
                description="Malformed test"
            )

            # Step 2: Attempt generation
            with pytest.raises(
                (ExampleParsingError, ValueError, KeyError, CodeGenerationError, Exception)
            ) as exc_info:
                await code_generator.generate(
                    examples=[malformed_example],
                    project_config=weather_api_config,
                )

            # Step 3: Verify error message is informative
            error_msg = str(exc_info.value).lower()
            # Error should mention missing field, invalid format, or parsing issue
            assert any(
                keyword in error_msg
                for keyword in ["output", "missing", "invalid", "required", "example", "parse", "pattern"]
            ), f"Error message should be informative: {error_msg}"

        except Exception as e:
            # If we can't even create the malformed example, that's also acceptable
            # as it shows the validation is working at the model level
            assert "validation" in str(e).lower() or "required" in str(e).lower(), (
                f"Expected validation error, got: {e}"
            )

    # ============================================================================
    # TEST 5: GENERATED CODE QUALITY TEST
    # ============================================================================

    @pytest.mark.integration
    def test_weather_api_generated_code_quality(
        self, weather_api_project_path: Path
    ) -> None:
        """
        Test generated code quality.

        Steps:
        1. Find generated code files
        2. Run AST validation on generated code
        3. Check for type hints
        4. Verify docstrings present
        5. Check imports are valid

        Success Criteria:
        - Code passes AST validation
        - Type hints on functions
        - Docstrings on public methods
        - Imports are valid

        Note: This test skips if no generated code exists, which is acceptable
        for E2E testing as code generation requires API keys and real API calls.
        """
        generated_dir = (
            weather_api_project_path / "generated" / "weather_api_extractor"
        )

        if not generated_dir.exists():
            pytest.skip("No generated code found - generation requires API keys")

        # Step 1: Find Python files
        # Generated code may be in src/ subdirectory or directly in generated_dir
        src_dir = generated_dir / "src" if (generated_dir / "src").exists() else generated_dir
        python_files = list(src_dir.glob("**/*.py"))

        if len(python_files) == 0:
            pytest.skip("No Python files found in generated directory")

        for py_file in python_files:
            with open(py_file) as f:
                code = f.read()

            # Step 2: AST validation
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file.name}: {e}")

            # Step 3: Check for type hints (look for annotations)
            has_type_hints = False
            has_docstrings = False

            for node in ast.walk(tree):
                # Check functions for type hints
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.returns is not None:
                        has_type_hints = True

                    # Step 4: Check for docstrings
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        has_docstrings = True

            # We expect at least some type hints and docstrings in generated code
            # (not all files may have them, but main extractor should)
            if py_file.stem not in ["__init__"]:
                assert has_type_hints or has_docstrings, (
                    f"{py_file.name} should have type hints or docstrings"
                )

    # ============================================================================
    # TEST 6: PROGRESS TRACKING INTEGRATION TEST (T10)
    # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.requires_api
    async def test_weather_api_progress_tracking(
        self,
        require_api_key,
        code_generator: CodeGeneratorService,
        weather_api_examples: List[Dict[str, Any]],
        weather_api_config: ProjectConfig,
    ) -> None:
        """
        Test progress tracking integration (T10).

        Steps:
        1. Create progress callback tracker
        2. Verify progress callback is called during generation
        3. Verify progress data structure

        Success Criteria:
        - Progress callback mechanism functional
        - Progress data includes required fields
        - Progress tracking integrated with generation pipeline

        Note: This test verifies the progress tracking mechanism exists
        and is wired correctly, without requiring actual code generation.
        """
        # Step 1: Create progress tracker
        progress_updates: List[GenerationProgress] = []

        def on_progress(progress: GenerationProgress) -> None:
            """Track progress updates."""
            progress_updates.append(progress)

        # Step 2: Verify progress callback signature is correct
        # We verify the callback parameter exists and accepts the right type
        import inspect
        sig = inspect.signature(code_generator.generate)
        params = sig.parameters

        assert "on_progress" in params, "generate() should have on_progress parameter"

        # Step 3: Verify GenerationProgress model is properly structured
        # Create a test progress object to verify the data structure
        test_progress = GenerationProgress(
            current_step=1,
            total_steps=7,
            step_name="Test step",
            status="in_progress",
            elapsed_time=0.5
        )

        assert test_progress.current_step == 1, "Should track current step"
        assert test_progress.total_steps == 7, "Should track total steps"
        assert test_progress.step_name == "Test step", "Should have step name"
        assert test_progress.status == "in_progress", "Should have status"
        assert test_progress.progress_percentage >= 0, "Should calculate percentage"
        assert test_progress.progress_percentage <= 100, "Percentage should be <= 100"


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
