"""
Integration tests for end-to-end code generation.

These tests use the actual OpenRouter API with Sonnet 4.5 to generate
real code from weather API examples.

IMPORTANT: These tests require:
- OPENROUTER_API_KEY environment variable set
- Active internet connection
- Valid API credits

Run with: pytest tests/integration/test_code_generation.py -v
Skip with: pytest tests/integration/test_code_generation.py -v -m "not integration"
"""

import os
import ast
from pathlib import Path

import pytest

from edgar_analyzer.services.code_generator import CodeGeneratorService
from edgar_analyzer.services.example_parser import ExampleParser
from edgar_analyzer.models.project_config import (
    ProjectConfig,
    ProjectMetadata,
    DataSourceConfig,
    DataSourceType,
    AuthConfig,
    AuthType,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    ExampleConfig,
)


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def weather_examples():
    """Weather API example pairs for testing."""
    return [
        {
            "input": {
                "name": "London",
                "main": {
                    "temp": 15.5,
                    "feels_like": 14.2,
                    "pressure": 1013,
                    "humidity": 72
                },
                "weather": [
                    {
                        "id": 500,
                        "main": "Rain",
                        "description": "light rain"
                    }
                ],
                "wind": {
                    "speed": 4.5
                }
            },
            "output": {
                "city": "London",
                "temperature_c": 15.5,
                "conditions": "light rain",
                "humidity": 72
            }
        },
        {
            "input": {
                "name": "Tokyo",
                "main": {
                    "temp": 22.3,
                    "feels_like": 21.8,
                    "pressure": 1015,
                    "humidity": 65
                },
                "weather": [
                    {
                        "id": 800,
                        "main": "Clear",
                        "description": "clear sky"
                    }
                ],
                "wind": {
                    "speed": 2.1
                }
            },
            "output": {
                "city": "Tokyo",
                "temperature_c": 22.3,
                "conditions": "clear sky",
                "humidity": 65
            }
        },
        {
            "input": {
                "name": "New York",
                "main": {
                    "temp": 8.0,
                    "feels_like": 5.5,
                    "pressure": 1020,
                    "humidity": 45
                },
                "weather": [
                    {
                        "id": 801,
                        "main": "Clouds",
                        "description": "few clouds"
                    }
                ],
                "wind": {
                    "speed": 6.2
                }
            },
            "output": {
                "city": "New York",
                "temperature_c": 8.0,
                "conditions": "few clouds",
                "humidity": 45
            }
        }
    ]


@pytest.fixture
def weather_project_config():
    """Weather API project configuration."""
    return ProjectConfig(
        project=ProjectMetadata(
            name="weather_extractor",
            description="Extract current weather data from OpenWeatherMap API",
            version="1.0.0",
            tags=["weather", "api", "integration-test"]
        ),
        data_sources=[
            DataSourceConfig(
                type=DataSourceType.API,
                name="openweather_api",
                endpoint="https://api.openweathermap.org/data/2.5/weather",
                auth=AuthConfig(
                    type=AuthType.API_KEY,
                    key="${OPENWEATHER_API_KEY}",
                    param_name="appid"
                ),
                parameters={
                    "units": "metric"
                }
            )
        ],
        examples=[
            ExampleConfig(
                input=ex["input"],
                output=ex["output"]
            ) for ex in [
                {
                    "input": {
                        "name": "London",
                        "main": {"temp": 15.5, "humidity": 72},
                        "weather": [{"description": "light rain"}]
                    },
                    "output": {
                        "city": "London",
                        "temperature_c": 15.5,
                        "conditions": "light rain",
                        "humidity": 72
                    }
                }
            ]
        ],
        output=OutputConfig(
            formats=[
                OutputDestinationConfig(
                    type=OutputFormat.JSON,
                    path="output/weather.json"
                )
            ]
        )
    )


@pytest.fixture
def code_generator():
    """Create CodeGeneratorService instance."""
    # Use environment variable for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set - skipping integration test")

    return CodeGeneratorService(
        api_key=api_key,
        output_dir=Path("./generated_test"),
        model="anthropic/claude-sonnet-4.5"
    )


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_weather_extractor(
    code_generator,
    weather_examples,
    weather_project_config
):
    """
    Test end-to-end code generation for weather extractor.

    This test generates a complete weather extractor using real API calls
    to Sonnet 4.5, validating the entire pipeline.
    """
    # Generate code
    context = await code_generator.generate(
        examples=weather_examples,
        project_config=weather_project_config,
        validate=True,
        write_files=True
    )

    # Verify context
    assert context.is_complete
    assert not context.has_errors
    assert context.plan is not None
    assert context.generated_code is not None

    # Verify plan
    plan = context.plan
    assert len(plan.classes) >= 1
    assert any("extractor" in cls.name.lower() for cls in plan.classes)
    assert "requests" in plan.dependencies or "httpx" in plan.dependencies
    assert "pydantic" in plan.dependencies

    # Verify generated code
    code = context.generated_code
    assert code.total_lines > 100  # Should be substantial

    # Verify extractor code
    assert "IDataExtractor" in code.extractor_code or "extract" in code.extractor_code
    assert "async def extract" in code.extractor_code
    assert "structlog" in code.extractor_code or "logging" in code.extractor_code

    # Verify models code
    assert "BaseModel" in code.models_code
    assert "Field" in code.models_code or "field" in code.models_code

    # Verify tests code
    assert "pytest" in code.tests_code
    assert "def test_" in code.tests_code
    assert "@pytest.mark.asyncio" in code.tests_code or "async def test_" in code.tests_code

    # Verify metadata
    assert code.metadata.get("model") == "anthropic/claude-sonnet-4.5"
    assert code.metadata.get("pattern_count", 0) > 0
    assert code.metadata.get("example_count") == len(weather_examples)

    print(f"\n✅ Generated {code.total_lines} lines of code in {context.generation_duration_seconds:.2f}s")
    print(f"   - Extractor: {len(code.extractor_code.splitlines())} lines")
    print(f"   - Models: {len(code.models_code.splitlines())} lines")
    print(f"   - Tests: {len(code.tests_code.splitlines())} lines")


@pytest.mark.asyncio
async def test_generated_code_is_valid_python(
    code_generator,
    weather_examples,
    weather_project_config
):
    """Test that generated code is syntactically valid Python."""
    context = await code_generator.generate(
        examples=weather_examples,
        project_config=weather_project_config,
        validate=True,
        write_files=False
    )

    code = context.generated_code

    # Parse each code artifact to verify syntax
    for name, code_str in [
        ("extractor", code.extractor_code),
        ("models", code.models_code),
        ("tests", code.tests_code)
    ]:
        try:
            ast.parse(code_str)
            print(f"✅ {name}.py has valid Python syntax")
        except SyntaxError as e:
            pytest.fail(f"{name}.py has syntax error: {e}")


@pytest.mark.asyncio
async def test_generated_code_has_type_hints(
    code_generator,
    weather_examples,
    weather_project_config
):
    """Test that generated code includes type hints."""
    context = await code_generator.generate(
        examples=weather_examples,
        project_config=weather_project_config,
        validate=True,
        write_files=False
    )

    code = context.generated_code

    # Parse and check for type annotations
    tree = ast.parse(code.extractor_code)

    has_annotations = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check return annotation
            if node.returns is not None:
                has_annotations = True
                print(f"✅ Found type annotation on {node.name}()")
                break
            # Check parameter annotations
            for arg in node.args.args:
                if arg.annotation is not None:
                    has_annotations = True
                    print(f"✅ Found type annotation on parameter: {arg.arg}")
                    break

    assert has_annotations, "Generated code should include type hints"


@pytest.mark.asyncio
async def test_generated_code_has_docstrings(
    code_generator,
    weather_examples,
    weather_project_config
):
    """Test that generated code includes docstrings."""
    context = await code_generator.generate(
        examples=weather_examples,
        project_config=weather_project_config,
        validate=True,
        write_files=False
    )

    code = context.generated_code

    # Check for docstrings
    assert '"""' in code.extractor_code or "'''" in code.extractor_code
    print("✅ Extractor code includes docstrings")

    assert '"""' in code.models_code or "'''" in code.models_code
    print("✅ Models code includes docstrings")


@pytest.mark.asyncio
async def test_generated_tests_reference_examples(
    code_generator,
    weather_examples,
    weather_project_config
):
    """Test that generated tests reference the provided examples."""
    context = await code_generator.generate(
        examples=weather_examples,
        project_config=weather_project_config,
        validate=True,
        write_files=False
    )

    code = context.generated_code

    # Check if test code mentions example cities
    cities = ["London", "Tokyo", "New York"]
    mentioned_cities = [city for city in cities if city in code.tests_code]

    assert len(mentioned_cities) > 0, "Tests should reference example data"
    print(f"✅ Tests reference examples: {mentioned_cities}")


@pytest.mark.asyncio
async def test_files_written_to_disk(
    code_generator,
    weather_examples,
    weather_project_config,
    tmp_path
):
    """Test that generated code is written to disk correctly."""
    # Use temporary directory
    code_generator.writer.base_dir = tmp_path

    context = await code_generator.generate(
        examples=weather_examples,
        project_config=weather_project_config,
        validate=True,
        write_files=True
    )

    # Verify files exist
    project_dir = tmp_path / "weather_extractor"
    assert project_dir.exists()

    extractor_file = project_dir / "extractor.py"
    models_file = project_dir / "models.py"
    tests_file = project_dir / "test_extractor.py"
    init_file = project_dir / "__init__.py"

    assert extractor_file.exists(), "extractor.py should be created"
    assert models_file.exists(), "models.py should be created"
    assert tests_file.exists(), "test_extractor.py should be created"
    assert init_file.exists(), "__init__.py should be created"

    # Verify file contents match generated code
    with open(extractor_file, 'r') as f:
        assert f.read() == context.generated_code.extractor_code

    print(f"✅ All files written to {project_dir}")


@pytest.mark.asyncio
async def test_minimal_examples_still_generates(code_generator):
    """Test that code generation works with minimal examples."""
    minimal_examples = [
        {
            "input": {"value": 10},
            "output": {"result": 20}
        }
    ]

    minimal_config = ProjectConfig(
        project=ProjectMetadata(name="minimal_test"),
        data_sources=[
            DataSourceConfig(
                type=DataSourceType.API,
                name="test_api",
                endpoint="https://api.example.com"
            )
        ],
        output=OutputConfig(
            formats=[
                OutputDestinationConfig(
                    type=OutputFormat.JSON,
                    path="output.json"
                )
            ]
        )
    )

    context = await code_generator.generate(
        examples=minimal_examples,
        project_config=minimal_config,
        validate=True,
        write_files=False
    )

    assert context.is_complete
    assert context.generated_code.total_lines > 50
    print("✅ Minimal examples successfully generated code")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generation_performance(
    code_generator,
    weather_examples,
    weather_project_config
):
    """Test that code generation completes in reasonable time."""
    context = await code_generator.generate(
        examples=weather_examples,
        project_config=weather_project_config,
        validate=True,
        write_files=False
    )

    duration = context.generation_duration_seconds

    # Should complete in under 60 seconds (generous for API calls)
    assert duration < 60, f"Generation took {duration}s (expected < 60s)"
    print(f"✅ Generation completed in {duration:.2f}s")


@pytest.mark.asyncio
async def test_iterative_refinement_on_validation_failure(
    code_generator,
    weather_examples,
    weather_project_config,
    monkeypatch
):
    """
    Test that generator retries when validation fails.

    This test mocks the validator to fail on the first attempt
    and succeed on the second attempt, verifying the iterative
    refinement loop works correctly.
    """
    from edgar_analyzer.services.code_generator import CodeValidator

    # Track validation calls
    validation_attempts = []

    # Save original validate method
    original_validate = CodeValidator.validate

    def mock_validate(self, code):
        """Mock validation that fails first, then succeeds."""
        attempt_number = len(validation_attempts) + 1
        validation_attempts.append(attempt_number)

        if attempt_number == 1:
            # First attempt: validation failure
            from edgar_analyzer.models.plan import CodeValidationResult
            result = CodeValidationResult(
                is_valid=False,
                syntax_valid=True,
                has_type_hints=False,
                has_docstrings=True,
                has_tests=True,
                implements_interface=True
            )
            result.add_issue("Missing type hints on extract() method")
            result.add_recommendation("Add type hints to all function parameters")
            return result
        else:
            # Second attempt: use real validation (should pass)
            return original_validate(self, code)

    # Patch the validate method
    monkeypatch.setattr(CodeValidator, 'validate', mock_validate)

    # Generate code (should retry and succeed)
    context = await code_generator.generate(
        examples=weather_examples,
        project_config=weather_project_config,
        validate=True,
        write_files=False,
        max_retries=3
    )

    # Verify code generation succeeded
    assert context.is_complete
    assert not context.has_errors
    assert context.generated_code is not None

    # Verify retry happened
    assert len(validation_attempts) == 2, f"Expected 2 validation attempts, got {len(validation_attempts)}"

    # Verify metadata tracks attempts
    assert context.generated_code.metadata.get("generation_attempts") == 2

    print(f"\n✅ Iterative refinement successful: {validation_attempts} validation attempts")


@pytest.mark.asyncio
async def test_max_retries_exceeded(
    code_generator,
    weather_examples,
    weather_project_config,
    monkeypatch
):
    """
    Test that generator fails after max retries.

    This test mocks the validator to always fail, verifying
    that the system respects max_retries and raises an error.
    """
    from edgar_analyzer.services.code_generator import CodeValidator
    from edgar_analyzer.models.plan import CodeValidationResult

    # Track validation calls
    validation_attempts = []

    def mock_validate_always_fail(self, code):
        """Mock validation that always fails."""
        attempt_number = len(validation_attempts) + 1
        validation_attempts.append(attempt_number)

        result = CodeValidationResult(
            is_valid=False,
            syntax_valid=False,
            has_type_hints=False,
            has_docstrings=False,
            has_tests=False,
            implements_interface=False
        )
        result.add_issue(f"Critical syntax error (attempt {attempt_number})")
        result.add_issue("Missing required interface implementation")
        return result

    # Patch the validate method
    monkeypatch.setattr(CodeValidator, 'validate', mock_validate_always_fail)

    # Attempt code generation (should fail after max_retries)
    max_retries = 3

    with pytest.raises(ValueError) as exc_info:
        await code_generator.generate(
            examples=weather_examples,
            project_config=weather_project_config,
            validate=True,
            write_files=False,
            max_retries=max_retries
        )

    # Verify error message
    error_message = str(exc_info.value)
    assert f"failed after {max_retries} attempts" in error_message.lower()

    # Verify all retries were attempted
    assert len(validation_attempts) == max_retries, \
        f"Expected {max_retries} validation attempts, got {len(validation_attempts)}"

    print(f"\n✅ Max retries enforcement works: Failed after {validation_attempts} attempts")


@pytest.mark.asyncio
async def test_validation_disabled_no_retry(
    code_generator,
    weather_examples,
    weather_project_config
):
    """
    Test that validation can be disabled, skipping retry loop.

    When validate=False, code should be accepted on first attempt
    regardless of quality.
    """
    # Generate code with validation disabled
    context = await code_generator.generate(
        examples=weather_examples,
        project_config=weather_project_config,
        validate=False,  # Skip validation
        write_files=False,
        max_retries=3
    )

    # Verify code generation succeeded
    assert context.is_complete
    assert not context.has_errors
    assert context.generated_code is not None

    # Verify only one attempt was made (no retries)
    assert context.generated_code.metadata.get("generation_attempts") == 1

    print("\n✅ Validation disabled: Accepted on first attempt")


if __name__ == "__main__":
    # Allow running integration tests directly
    pytest.main([__file__, "-v", "-s"])
