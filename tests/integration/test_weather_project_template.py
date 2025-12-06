"""
Integration tests for Weather API project template.

Tests the complete project template including:
- project.yaml loading and validation
- Example file parsing
- Configuration correctness
- Example diversity
- Schema compliance

This ensures the Weather API template is ready for code generation.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from edgar_analyzer.models.project_config import (
    AuthType,
    DataSourceType,
    OutputFormat,
    ProjectConfig,
)

# Path to Weather API project
WEATHER_PROJECT_DIR = Path(__file__).parent.parent.parent / "projects" / "weather_api"


class TestWeatherProjectStructure:
    """Test project file structure and completeness."""

    def test_project_directory_exists(self):
        """Test that weather_api project directory exists."""
        assert (
            WEATHER_PROJECT_DIR.exists()
        ), f"Project directory not found: {WEATHER_PROJECT_DIR}"
        assert WEATHER_PROJECT_DIR.is_dir(), "Project path is not a directory"

    def test_required_files_exist(self):
        """Test that all required files are present."""
        required_files = [
            "project.yaml",
            "README.md",
            ".env.example",
            "validate_project.py",
        ]

        for filename in required_files:
            file_path = WEATHER_PROJECT_DIR / filename
            assert file_path.exists(), f"Required file missing: {filename}"

    def test_required_directories_exist(self):
        """Test that all required directories exist."""
        required_dirs = [
            "examples",
            "generated",
            "output",
        ]

        for dirname in required_dirs:
            dir_path = WEATHER_PROJECT_DIR / dirname
            assert dir_path.exists(), f"Required directory missing: {dirname}"
            assert dir_path.is_dir(), f"Path is not a directory: {dirname}"

    def test_example_files_exist(self):
        """Test that all example JSON files exist."""
        example_files = [
            "london.json",
            "tokyo.json",
            "moscow.json",
            "dubai.json",
            "oslo.json",
            "singapore.json",
            "new_york.json",
        ]

        examples_dir = WEATHER_PROJECT_DIR / "examples"
        for filename in example_files:
            file_path = examples_dir / filename
            assert file_path.exists(), f"Example file missing: {filename}"


class TestProjectYAML:
    """Test project.yaml configuration."""

    @pytest.fixture
    def project_config(self) -> ProjectConfig:
        """Load and return project configuration."""
        yaml_path = WEATHER_PROJECT_DIR / "project.yaml"
        return ProjectConfig.from_yaml(yaml_path)

    def test_yaml_loads_successfully(self, project_config):
        """Test that project.yaml loads without errors."""
        assert project_config is not None
        assert isinstance(project_config, ProjectConfig)

    def test_project_metadata(self, project_config):
        """Test project metadata is correct."""
        assert project_config.project.name == "weather_api_extractor"
        assert "weather" in project_config.project.description.lower()
        assert project_config.project.version == "1.0.0"

    def test_data_source_configuration(self, project_config):
        """Test data source is properly configured."""
        assert len(project_config.data_sources) > 0

        # Find OpenWeatherMap source
        weather_source = next(
            (s for s in project_config.data_sources if s.name == "openweathermap"), None
        )
        assert weather_source is not None, "OpenWeatherMap source not found"

        # Validate source configuration
        assert weather_source.type == DataSourceType.API
        assert "openweathermap.org" in weather_source.endpoint
        assert weather_source.auth.type == AuthType.API_KEY
        assert weather_source.auth.key == "${OPENWEATHER_API_KEY}"
        assert weather_source.auth.param_name == "appid"

    def test_caching_configuration(self, project_config):
        """Test that caching is properly configured."""
        weather_source = next(
            (s for s in project_config.data_sources if s.name == "openweathermap"), None
        )
        assert weather_source is not None

        assert weather_source.cache.enabled is True
        assert (
            weather_source.cache.ttl >= 600
        ), "Cache TTL should be at least 10 minutes"

    def test_rate_limiting_configuration(self, project_config):
        """Test rate limiting is configured."""
        weather_source = next(
            (s for s in project_config.data_sources if s.name == "openweathermap"), None
        )
        assert weather_source is not None
        assert weather_source.rate_limit is not None
        assert (
            weather_source.rate_limit.requests_per_second <= 1.0
        ), "Rate limit should respect free tier (60/min = 1/sec)"

    def test_examples_provided(self, project_config):
        """Test that examples are provided."""
        assert (
            len(project_config.examples) >= 5
        ), "At least 5 examples required for diversity"

    def test_validation_rules(self, project_config):
        """Test validation rules are configured."""
        # Required fields
        assert len(project_config.validation.required_fields) >= 3
        assert "city" in project_config.validation.required_fields
        assert "temperature_c" in project_config.validation.required_fields

        # Field types
        assert len(project_config.validation.field_types) > 0

        # Constraints
        assert "temperature_c" in project_config.validation.constraints
        temp_constraint = project_config.validation.constraints["temperature_c"]
        assert temp_constraint.min is not None
        assert temp_constraint.max is not None
        assert temp_constraint.min < temp_constraint.max

    def test_output_configuration(self, project_config):
        """Test output formats are configured."""
        assert len(project_config.output.formats) >= 1

        # Check for CSV and JSON outputs
        formats = [f.type for f in project_config.output.formats]
        assert OutputFormat.CSV in formats or OutputFormat.JSON in formats


class TestExampleFiles:
    """Test individual example JSON files."""

    @pytest.fixture
    def example_files(self) -> list[Path]:
        """Get list of all example files."""
        examples_dir = WEATHER_PROJECT_DIR / "examples"
        return list(examples_dir.glob("*.json"))

    def test_all_examples_are_valid_json(self, example_files):
        """Test that all example files contain valid JSON."""
        for file_path in example_files:
            with open(file_path, "r") as f:
                try:
                    data = json.load(f)
                    assert isinstance(
                        data, dict
                    ), f"{file_path.name}: Root must be object"
                except json.JSONDecodeError as e:
                    pytest.fail(f"{file_path.name}: Invalid JSON - {e}")

    def test_examples_have_required_structure(self, example_files):
        """Test that examples have input/output structure."""
        for file_path in example_files:
            with open(file_path, "r") as f:
                data = json.load(f)

            assert "input" in data, f"{file_path.name}: Missing 'input' field"
            assert "output" in data, f"{file_path.name}: Missing 'output' field"
            assert isinstance(
                data["input"], dict
            ), f"{file_path.name}: 'input' must be object"
            assert isinstance(
                data["output"], dict
            ), f"{file_path.name}: 'output' must be object"

    def test_input_structure_matches_api(self, example_files):
        """Test that input structure matches OpenWeatherMap API response."""
        required_input_fields = ["coord", "weather", "main", "name"]

        for file_path in example_files:
            with open(file_path, "r") as f:
                data = json.load(f)

            input_data = data["input"]
            for field in required_input_fields:
                assert (
                    field in input_data
                ), f"{file_path.name}: Input missing required field '{field}'"

            # Validate nested structures
            assert (
                "lat" in input_data["coord"]
            ), f"{file_path.name}: coord missing 'lat'"
            assert (
                "lon" in input_data["coord"]
            ), f"{file_path.name}: coord missing 'lon'"
            assert isinstance(
                input_data["weather"], list
            ), f"{file_path.name}: 'weather' must be array"
            assert (
                "temp" in input_data["main"]
            ), f"{file_path.name}: main missing 'temp'"
            assert (
                "humidity" in input_data["main"]
            ), f"{file_path.name}: main missing 'humidity'"

    def test_output_structure_is_consistent(self, example_files):
        """Test that all outputs have consistent structure."""
        required_output_fields = [
            "city",
            "country",
            "temperature_c",
            "humidity_percent",
            "conditions",
        ]

        for file_path in example_files:
            with open(file_path, "r") as f:
                data = json.load(f)

            output_data = data["output"]
            for field in required_output_fields:
                assert (
                    field in output_data
                ), f"{file_path.name}: Output missing required field '{field}'"

    def test_output_field_types(self, example_files):
        """Test that output fields have correct types."""
        for file_path in example_files:
            with open(file_path, "r") as f:
                data = json.load(f)

            output = data["output"]

            # String fields
            assert isinstance(
                output["city"], str
            ), f"{file_path.name}: city must be string"
            assert isinstance(
                output["country"], str
            ), f"{file_path.name}: country must be string"
            assert isinstance(
                output["conditions"], str
            ), f"{file_path.name}: conditions must be string"

            # Numeric fields
            assert isinstance(
                output["temperature_c"], (int, float)
            ), f"{file_path.name}: temperature_c must be numeric"
            assert isinstance(
                output["humidity_percent"], int
            ), f"{file_path.name}: humidity_percent must be int"


class TestExampleDiversity:
    """Test example diversity and coverage."""

    @pytest.fixture
    def project_config(self) -> ProjectConfig:
        """Load project configuration."""
        yaml_path = WEATHER_PROJECT_DIR / "project.yaml"
        return ProjectConfig.from_yaml(yaml_path)

    def test_temperature_range_coverage(self, project_config):
        """Test that examples cover wide temperature range."""
        temperatures = [
            example.output.get("temperature_c", 0)
            for example in project_config.examples
        ]

        temp_range = max(temperatures) - min(temperatures)
        assert (
            temp_range >= 30
        ), f"Temperature range too narrow: {temp_range}°C (expected: ≥30°C)"

    def test_negative_temperature_coverage(self, project_config):
        """Test that examples include negative temperatures."""
        temperatures = [
            example.output.get("temperature_c", 0)
            for example in project_config.examples
        ]

        has_negative = any(t < 0 for t in temperatures)
        assert (
            has_negative
        ), "Examples should include negative temperatures (cold climate)"

    def test_high_temperature_coverage(self, project_config):
        """Test that examples include high temperatures."""
        temperatures = [
            example.output.get("temperature_c", 0)
            for example in project_config.examples
        ]

        has_high_temp = any(t > 30 for t in temperatures)
        assert has_high_temp, "Examples should include temperatures >30°C (hot climate)"

    def test_humidity_range_coverage(self, project_config):
        """Test that examples cover wide humidity range."""
        humidities = [
            example.output.get("humidity_percent", 50)
            for example in project_config.examples
        ]

        humidity_range = max(humidities) - min(humidities)
        assert (
            humidity_range >= 40
        ), f"Humidity range too narrow: {humidity_range}% (expected: ≥40%)"

    def test_weather_condition_diversity(self, project_config):
        """Test that examples cover diverse weather conditions."""
        conditions = [
            example.output.get("conditions", "").lower()
            for example in project_config.examples
        ]

        # Check for key condition types
        condition_coverage = {
            "rain": any("rain" in c for c in conditions),
            "snow": any("snow" in c for c in conditions),
            "clear": any("clear" in c for c in conditions),
            "clouds": any("cloud" in c for c in conditions),
        }

        covered_count = sum(condition_coverage.values())
        assert (
            covered_count >= 3
        ), f"Only {covered_count}/4 condition types covered (expected: ≥3)"

    def test_example_count(self, project_config):
        """Test that sufficient examples are provided."""
        assert (
            len(project_config.examples) >= 5
        ), "At least 5 examples required for good diversity"
        assert (
            len(project_config.examples) <= 20
        ), "Too many examples may slow down code generation"


class TestValidationRules:
    """Test validation rule configuration."""

    @pytest.fixture
    def project_config(self) -> ProjectConfig:
        """Load project configuration."""
        yaml_path = WEATHER_PROJECT_DIR / "project.yaml"
        return ProjectConfig.from_yaml(yaml_path)

    def test_temperature_constraints(self, project_config):
        """Test temperature validation constraints."""
        assert "temperature_c" in project_config.validation.constraints

        temp_constraint = project_config.validation.constraints["temperature_c"]
        assert temp_constraint.min is not None
        assert temp_constraint.max is not None

        # Reasonable extreme weather bounds
        assert temp_constraint.min <= -50, "Min temp should allow extreme cold"
        assert temp_constraint.max >= 50, "Max temp should allow extreme heat"

    def test_humidity_constraints(self, project_config):
        """Test humidity validation constraints."""
        assert "humidity_percent" in project_config.validation.constraints

        humidity_constraint = project_config.validation.constraints["humidity_percent"]
        assert humidity_constraint.min == 0, "Humidity min should be 0"
        assert humidity_constraint.max == 100, "Humidity max should be 100"

    def test_pressure_constraints(self, project_config):
        """Test pressure validation constraints."""
        assert "pressure_hpa" in project_config.validation.constraints

        pressure_constraint = project_config.validation.constraints["pressure_hpa"]
        assert pressure_constraint.min is not None
        assert pressure_constraint.max is not None

        # Realistic atmospheric pressure bounds
        assert pressure_constraint.min <= 900, "Min pressure too high"
        assert pressure_constraint.max >= 1050, "Max pressure too low"


class TestDocumentation:
    """Test documentation completeness."""

    def test_readme_exists_and_not_empty(self):
        """Test that README exists and has content."""
        readme_path = WEATHER_PROJECT_DIR / "README.md"
        assert readme_path.exists(), "README.md not found"

        with open(readme_path, "r") as f:
            content = f.read()

        assert (
            len(content) > 1000
        ), "README is too short (expected: comprehensive guide)"

    def test_readme_has_required_sections(self):
        """Test that README has all required sections."""
        readme_path = WEATHER_PROJECT_DIR / "README.md"
        with open(readme_path, "r") as f:
            content = f.read().lower()

        required_sections = [
            "overview",
            "quick start",
            "example",
            "usage",
            "output",
            "configuration",
        ]

        for section in required_sections:
            assert section in content, f"README missing section: {section}"

    def test_env_example_has_api_key(self):
        """Test that .env.example includes API key placeholder."""
        env_path = WEATHER_PROJECT_DIR / ".env.example"
        assert env_path.exists(), ".env.example not found"

        with open(env_path, "r") as f:
            content = f.read()

        assert (
            "OPENWEATHER_API_KEY" in content
        ), ".env.example missing OPENWEATHER_API_KEY"
        assert (
            "your_api_key_here" in content or "your_key" in content.lower()
        ), ".env.example should have placeholder value"


class TestProjectReadiness:
    """Test that project is ready for code generation."""

    @pytest.fixture
    def project_config(self) -> ProjectConfig:
        """Load project configuration."""
        yaml_path = WEATHER_PROJECT_DIR / "project.yaml"
        return ProjectConfig.from_yaml(yaml_path)

    def test_comprehensive_validation_passes(self, project_config):
        """Test that comprehensive validation passes."""
        results = project_config.validate_comprehensive()

        # Should have no critical errors
        assert (
            len(results["errors"]) == 0
        ), f"Validation errors found: {results['errors']}"

        # Warnings are acceptable but should be minimal
        assert (
            len(results["warnings"]) <= 3
        ), f"Too many warnings: {results['warnings']}"

    def test_examples_match_validation_rules(self, project_config):
        """Test that all examples satisfy validation rules."""
        for i, example in enumerate(project_config.examples):
            output = example.output

            # Check required fields
            for field in project_config.validation.required_fields:
                assert field in output, f"Example {i}: Missing required field '{field}'"

            # Check constraints
            for field, constraint in project_config.validation.constraints.items():
                if field in output:
                    value = output[field]

                    if constraint.min is not None:
                        assert (
                            value >= constraint.min
                        ), f"Example {i}: {field}={value} < min={constraint.min}"

                    if constraint.max is not None:
                        assert (
                            value <= constraint.max
                        ), f"Example {i}: {field}={value} > max={constraint.max}"

    def test_ready_for_code_generation(self, project_config):
        """Test that project meets all requirements for code generation."""
        # Checklist for code generation readiness
        checks = {
            "has_data_source": len(project_config.data_sources) > 0,
            "has_examples": len(project_config.examples) >= 5,
            "has_validation": len(project_config.validation.required_fields) > 0,
            "has_output": len(project_config.output.formats) > 0,
            "has_auth": any(
                s.auth.type != AuthType.NONE for s in project_config.data_sources
            ),
        }

        failed_checks = [name for name, passed in checks.items() if not passed]
        assert (
            not failed_checks
        ), f"Project not ready for code generation. Failed checks: {failed_checks}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
