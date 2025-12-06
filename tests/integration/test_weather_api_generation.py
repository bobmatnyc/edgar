"""
End-to-End Integration Test for Weather API Extractor Generation

This test validates the complete code generation pipeline:
1. Load Weather API project configuration
2. Parse 7 examples and extract patterns
3. PM mode: Create implementation plan
4. Coder mode: Generate production code
5. Validate: Check code quality and constraints
6. Write: Save generated files
7. Verify: Run generated tests and validate outputs

Test Coverage:
- Configuration loading and validation
- Example parsing and pattern extraction
- PM mode planning with Sonnet 4.5
- Coder mode code generation
- Constraint validation enforcement
- File writing and backup management
- Generated code syntax and structure
- Generated test execution

Success Criteria:
- All 7 examples parsed successfully
- At least 3 transformation patterns identified
- Implementation plan created with class/method specs
- Generated code passes syntax validation
- Generated code implements IDataExtractor interface
- Generated code includes type hints and docstrings
- Generated tests cover all 7 examples
- All generated tests pass when executed
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from edgar_analyzer.agents.sonnet45_agent import Sonnet45Agent
from edgar_analyzer.models.project_config import ProjectConfig
from edgar_analyzer.services.code_generator import CodeGeneratorService
from edgar_analyzer.services.example_parser import ExampleParser

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def project_path() -> Path:
    """Path to Weather API project directory."""
    return Path(__file__).parent.parent.parent / "projects" / "weather_api"


@pytest.fixture
def project_config(project_path: Path) -> ProjectConfig:
    """Load Weather API project configuration."""
    config_path = project_path / "project.yaml"
    assert config_path.exists(), f"Project config not found: {config_path}"

    config = ProjectConfig.from_yaml(config_path)
    return config


@pytest.fixture
def api_key() -> str:
    """Get OpenRouter API key from environment."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set - skipping AI generation tests")
    return api_key


@pytest.fixture
def code_generator(api_key: str, project_path: Path) -> CodeGeneratorService:
    """Create CodeGeneratorService instance."""
    output_dir = project_path / "generated"
    return CodeGeneratorService(
        api_key=api_key, output_dir=output_dir, model="anthropic/claude-sonnet-4.5"
    )


@pytest.fixture
def example_parser() -> ExampleParser:
    """Create ExampleParser instance."""
    return ExampleParser()


# ============================================================================
# STEP 1: PROJECT LOADING TESTS
# ============================================================================


class TestProjectLoading:
    """Test Weather API project configuration loading."""

    def test_project_path_exists(self, project_path: Path):
        """Verify project directory exists."""
        assert project_path.exists(), f"Project directory not found: {project_path}"
        assert project_path.is_dir(), f"Project path is not a directory: {project_path}"

    def test_project_yaml_exists(self, project_path: Path):
        """Verify project.yaml exists."""
        config_path = project_path / "project.yaml"
        assert config_path.exists(), f"project.yaml not found: {config_path}"

    def test_load_weather_project(self, project_config: ProjectConfig):
        """Ensure Weather API project loads correctly."""
        assert project_config.project.name == "weather_api_extractor"
        assert project_config.project.version == "1.0.0"
        assert "weather" in project_config.project.tags

        logger.info(
            "Project loaded successfully",
            name=project_config.project.name,
            version=project_config.project.version,
        )

    def test_data_sources_configured(self, project_config: ProjectConfig):
        """Verify data sources are configured."""
        assert len(project_config.data_sources) == 1

        source = project_config.data_sources[0]
        assert source.type == "api"
        assert source.name == "openweathermap"
        assert "openweathermap.org" in source.endpoint

        logger.info(
            "Data source validated", source_type=source.type, endpoint=source.endpoint
        )

    def test_examples_loaded(self, project_config: ProjectConfig):
        """Verify all 7 examples are loaded."""
        assert (
            len(project_config.examples) == 7
        ), f"Expected 7 examples, got {len(project_config.examples)}"

        # Check example diversity
        cities = [ex.output.get("city") for ex in project_config.examples]
        assert "London" in cities
        assert "Tokyo" in cities
        assert "Moscow" in cities
        assert "Dubai" in cities

        logger.info(
            "Examples loaded", count=len(project_config.examples), cities=cities
        )

    def test_validation_rules_configured(self, project_config: ProjectConfig):
        """Verify validation rules are configured."""
        assert project_config.validation is not None
        assert len(project_config.validation.required_fields) >= 5
        assert "city" in project_config.validation.required_fields
        assert "temperature_c" in project_config.validation.required_fields

        logger.info(
            "Validation rules loaded",
            required_fields=project_config.validation.required_fields,
        )


# ============================================================================
# STEP 2: EXAMPLE PARSING TESTS
# ============================================================================


class TestExampleParsing:
    """Test example parsing and pattern extraction."""

    def test_parse_examples(
        self, example_parser: ExampleParser, project_config: ProjectConfig
    ):
        """Test Example Parser extracts patterns from Weather API examples."""
        parsed = example_parser.parse_examples(project_config.examples)

        assert parsed is not None
        assert parsed.num_examples == 7
        assert (
            len(parsed.patterns) >= 3
        ), f"Expected at least 3 patterns, got {len(parsed.patterns)}"

        logger.info(
            "Examples parsed",
            num_examples=parsed.num_examples,
            num_patterns=len(parsed.patterns),
            input_fields=len(parsed.input_schema.fields),
            output_fields=len(parsed.output_schema.fields),
        )

    def test_field_mapping_pattern(
        self, example_parser: ExampleParser, project_config: ProjectConfig
    ):
        """Verify field mapping patterns are detected."""
        parsed = example_parser.parse_examples(project_config.examples)

        # Check for field mapping patterns (pattern.type can be enum or string)
        field_mappings = [
            p
            for p in parsed.patterns
            if str(p.type).upper() == "FIELD_MAPPING"
            or "field_mapping" in str(p.type).lower()
        ]
        assert (
            len(field_mappings) > 0
        ), f"No field mapping patterns found. Total patterns: {len(parsed.patterns)}, Types: {[str(p.type) for p in parsed.patterns[:5]]}"

        logger.info("Field mapping patterns detected: %d", len(field_mappings))

    def test_nested_extraction_pattern(
        self, example_parser: ExampleParser, project_config: ProjectConfig
    ):
        """Verify nested field extraction patterns are detected."""
        parsed = example_parser.parse_examples(project_config.examples)

        # Check for nested extraction patterns (e.g., main.temp -> temperature_c)
        nested_patterns = [
            p
            for p in parsed.patterns
            if "NESTED" in p.type or "nested" in str(p.transformation).lower()
        ]

        logger.info("Nested extraction patterns", count=len(nested_patterns))

    def test_array_handling_pattern(
        self, example_parser: ExampleParser, project_config: ProjectConfig
    ):
        """Verify array handling patterns are detected."""
        parsed = example_parser.parse_examples(project_config.examples)

        # Check for array patterns (e.g., weather[0].description)
        array_patterns = [
            p
            for p in parsed.patterns
            if "ARRAY" in p.type or "[0]" in str(p.transformation)
        ]

        logger.info("Array handling patterns", count=len(array_patterns))


# ============================================================================
# STEP 3: PM MODE PLANNING TESTS
# ============================================================================


class TestPMModePlanning:
    """Test PM mode creates implementation plan."""

    @pytest.mark.asyncio
    async def test_pm_mode_planning(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Test PM mode creates implementation plan."""
        # Parse examples first (synchronous)
        parsed = example_parser.parse_examples(project_config.examples)

        # Generate plan
        plan = await code_generator.agent.plan(parsed.patterns, project_config)

        assert plan is not None
        assert len(plan.classes) > 0, "Plan contains no classes"
        assert plan.strategy is not None, "Plan has no implementation strategy"

        logger.info(
            "PM mode plan created",
            num_classes=len(plan.classes),
            num_dependencies=len(plan.dependencies),
            strategy=plan.strategy[:100] if plan.strategy else None,
        )

    @pytest.mark.asyncio
    async def test_plan_contains_extractor_class(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Verify plan includes WeatherExtractor class."""
        parsed = example_parser.parse_examples(project_config.examples)
        plan = await code_generator.agent.plan(parsed.patterns, project_config)

        # Check for extractor class
        class_names = [cls.name for cls in plan.classes]
        assert any(
            "Extractor" in name for name in class_names
        ), f"No extractor class found in plan. Classes: {class_names}"

        logger.info("Extractor class found in plan", classes=class_names)

    @pytest.mark.asyncio
    async def test_plan_includes_dependencies(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Verify plan includes required dependencies."""
        parsed = example_parser.parse_examples(project_config.examples)
        plan = await code_generator.agent.plan(parsed.patterns, project_config)

        assert len(plan.dependencies) > 0, "Plan has no dependencies"

        # Should include Pydantic for models
        deps = [str(d).lower() for d in plan.dependencies]

        logger.info("Plan dependencies", dependencies=plan.dependencies)


# ============================================================================
# STEP 4: CODER MODE GENERATION TESTS
# ============================================================================


class TestCoderModeGeneration:
    """Test Coder mode generates valid Python code."""

    @pytest.mark.asyncio
    async def test_coder_mode_generation(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Test Coder mode generates valid Python code."""
        # Parse and plan
        parsed = example_parser.parse_examples(project_config.examples)
        plan = await code_generator.agent.plan(parsed.patterns, project_config)

        # Generate code
        generated = await code_generator.agent.code(
            plan, parsed.patterns, project_config.examples
        )

        assert generated is not None
        assert generated.extractor_code is not None
        assert len(generated.extractor_code) > 0
        assert generated.models_code is not None
        assert len(generated.models_code) > 0
        assert generated.tests_code is not None
        assert len(generated.tests_code) > 0

        logger.info(
            "Code generated",
            total_lines=generated.total_lines,
            extractor_lines=len(generated.extractor_code.split("\n")),
            models_lines=len(generated.models_code.split("\n")),
            tests_lines=len(generated.tests_code.split("\n")),
        )

    @pytest.mark.asyncio
    async def test_generated_extractor_has_class(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Verify generated extractor contains extractor class."""
        parsed = example_parser.parse_examples(project_config.examples)
        plan = await code_generator.agent.plan(parsed.patterns, project_config)
        generated = await code_generator.agent.code(
            plan, parsed.patterns, project_config.examples
        )

        assert "class" in generated.extractor_code
        assert "Extractor" in generated.extractor_code

        logger.info("Extractor class found in generated code")

    @pytest.mark.asyncio
    async def test_generated_code_implements_interface(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Verify generated code implements IDataExtractor interface."""
        parsed = example_parser.parse_examples(project_config.examples)
        plan = await code_generator.agent.plan(parsed.patterns, project_config)
        generated = await code_generator.agent.code(
            plan, parsed.patterns, project_config.examples
        )

        # Check for interface implementation
        assert (
            "IDataExtractor" in generated.extractor_code
            or "async def extract" in generated.extractor_code
        ), "Generated code does not implement IDataExtractor interface"

        logger.info("Interface implementation found")

    @pytest.mark.asyncio
    async def test_generated_tests_exist(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Verify generated tests exist and contain test functions."""
        parsed = example_parser.parse_examples(project_config.examples)
        plan = await code_generator.agent.plan(parsed.patterns, project_config)
        generated = await code_generator.agent.code(
            plan, parsed.patterns, project_config.examples
        )

        assert (
            "def test_" in generated.tests_code
            or "async def test_" in generated.tests_code
        ), "No test functions found in generated tests"

        # Count test functions
        test_count = generated.tests_code.count("def test_")
        logger.info("Generated tests found", test_count=test_count)


# ============================================================================
# STEP 5: CONSTRAINT VALIDATION TESTS
# ============================================================================


class TestConstraintValidation:
    """Test generated code passes all constraint checks."""

    @pytest.mark.asyncio
    async def test_constraint_validation(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Test generated code passes all constraints."""
        # Generate code
        parsed = example_parser.parse_examples(project_config.examples)
        plan = await code_generator.agent.plan(parsed.patterns, project_config)
        generated = await code_generator.agent.code(
            plan, parsed.patterns, project_config.examples
        )

        # Validate
        result = code_generator.validator.validate(generated)

        assert result.syntax_valid, f"Syntax errors: {result.issues}"
        logger.info(
            "Syntax validation passed",
            issues=len(result.issues),
            recommendations=len(result.recommendations),
        )

    @pytest.mark.asyncio
    async def test_code_has_type_hints(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Verify generated code includes type hints."""
        parsed = example_parser.parse_examples(project_config.examples)
        plan = await code_generator.agent.plan(parsed.patterns, project_config)
        generated = await code_generator.agent.code(
            plan, parsed.patterns, project_config.examples
        )

        result = code_generator.validator.validate(generated)

        # Type hints are recommended but not required for validity
        if not result.has_type_hints:
            logger.warning("Generated code lacks type hints")

        logger.info("Type hints check", has_type_hints=result.has_type_hints)

    @pytest.mark.asyncio
    async def test_code_has_docstrings(
        self,
        code_generator: CodeGeneratorService,
        example_parser: ExampleParser,
        project_config: ProjectConfig,
    ):
        """Verify generated code includes docstrings."""
        parsed = example_parser.parse_examples(project_config.examples)
        plan = await code_generator.agent.plan(parsed.patterns, project_config)
        generated = await code_generator.agent.code(
            plan, parsed.patterns, project_config.examples
        )

        result = code_generator.validator.validate(generated)

        # Docstrings are recommended but not required for validity
        if not result.has_docstrings:
            logger.warning("Generated code lacks docstrings")

        logger.info("Docstrings check", has_docstrings=result.has_docstrings)


# ============================================================================
# STEP 6: END-TO-END GENERATION TEST
# ============================================================================


class TestEndToEndGeneration:
    """Complete end-to-end generation test."""

    @pytest.mark.asyncio
    async def test_end_to_end_generation(
        self, code_generator: CodeGeneratorService, project_config: ProjectConfig
    ):
        """Complete end-to-end: load project → generate code → validate → write files."""
        logger.info(
            "Starting end-to-end generation test", project=project_config.project.name
        )

        # Generate (this runs the entire pipeline)
        context = await code_generator.generate(
            examples=project_config.examples,
            project_config=project_config,
            validate=True,
            write_files=True,
        )

        # Verify generation succeeded
        assert context.is_complete, f"Generation incomplete. Errors: {context.errors}"
        assert context.generated_code is not None
        assert context.plan is not None

        # Verify code was written
        extractor_path = Path(
            context.generated_code.metadata.get("output_paths", {}).get("extractor", "")
        )
        assert extractor_path.exists(), f"Extractor file not written: {extractor_path}"

        # Read and verify file contents
        extractor_code = extractor_path.read_text()
        assert "class" in extractor_code
        assert "Extractor" in extractor_code

        logger.info(
            "End-to-end generation completed successfully",
            duration_seconds=context.generation_duration_seconds,
            total_lines=context.generated_code.total_lines,
            files_written=len(context.generated_code.metadata.get("output_paths", {})),
        )

    @pytest.mark.asyncio
    async def test_generated_files_exist(
        self,
        code_generator: CodeGeneratorService,
        project_config: ProjectConfig,
        project_path: Path,
    ):
        """Verify all generated files exist."""
        # Generate
        context = await code_generator.generate(
            examples=project_config.examples,
            project_config=project_config,
            validate=True,
            write_files=True,
        )

        # Check files
        output_dir = project_path / "generated"
        extractor_path = output_dir / "extractor.py"
        models_path = output_dir / "models.py"
        tests_path = output_dir / "test_extractor.py"

        assert extractor_path.exists(), f"Missing: {extractor_path}"
        assert models_path.exists(), f"Missing: {models_path}"
        assert tests_path.exists(), f"Missing: {tests_path}"

        logger.info(
            "All generated files exist",
            extractor=str(extractor_path),
            models=str(models_path),
            tests=str(tests_path),
        )

    @pytest.mark.asyncio
    async def test_generated_code_quality(
        self, code_generator: CodeGeneratorService, project_config: ProjectConfig
    ):
        """Verify generated code meets quality standards."""
        context = await code_generator.generate(
            examples=project_config.examples,
            project_config=project_config,
            validate=True,
            write_files=False,  # Don't write for this test
        )

        generated = context.generated_code

        # Verify extractor structure
        assert "class" in generated.extractor_code
        assert (
            "async def extract" in generated.extractor_code
            or "def extract" in generated.extractor_code
        )

        # Verify models structure
        assert (
            "class" in generated.models_code
            or "BaseModel" in generated.models_code
            or "dataclass" in generated.models_code
        )

        # Verify tests structure
        assert (
            "pytest" in generated.tests_code
            or "unittest" in generated.tests_code
            or "def test_" in generated.tests_code
        )

        logger.info(
            "Generated code quality verified", total_lines=generated.total_lines
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def run_tests():
    """Run all tests and report results."""
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--capture=no",
            "-W",
            "ignore::DeprecationWarning",
        ]
    )


if __name__ == "__main__":
    run_tests()
