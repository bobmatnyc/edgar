"""
Unit tests for project configuration schema validation.

Tests all Pydantic models, validation rules, and edge cases for the
project.yaml configuration system.
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from edgar_analyzer.models.project_config import (
    AuthConfig,
    AuthType,
    CacheConfig,
    DataSourceConfig,
    DataSourceType,
    ErrorStrategy,
    ExampleConfig,
    FieldConstraint,
    FieldType,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    ProjectConfig,
    ProjectMetadata,
    RateLimitConfig,
    RuntimeConfig,
    ValidationConfig,
)

# ============================================================================
# PROJECT METADATA TESTS
# ============================================================================


class TestProjectMetadata:
    """Test project metadata validation."""

    def test_valid_metadata(self):
        """Test valid project metadata."""
        metadata = ProjectMetadata(
            name="test_project",
            description="Test description",
            version="1.0.0",
            author="Test Author",
        )
        assert metadata.name == "test_project"
        assert metadata.version == "1.0.0"

    def test_name_lowercase_conversion(self):
        """Test that project names are converted to lowercase."""
        metadata = ProjectMetadata(name="TestProject")
        assert metadata.name == "testproject"

    def test_name_with_underscores(self):
        """Test that underscores are allowed in project names."""
        metadata = ProjectMetadata(name="test_project_2024")
        assert metadata.name == "test_project_2024"

    def test_name_with_hyphens(self):
        """Test that hyphens are allowed in project names."""
        metadata = ProjectMetadata(name="test-project-2024")
        assert metadata.name == "test-project-2024"

    def test_invalid_name_with_spaces(self):
        """Test that spaces in names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectMetadata(name="test project")
        assert "alphanumeric" in str(exc_info.value).lower()

    def test_invalid_name_with_special_chars(self):
        """Test that special characters are rejected."""
        with pytest.raises(ValidationError):
            ProjectMetadata(name="test@project!")

    def test_empty_name(self):
        """Test that empty names are rejected."""
        with pytest.raises(ValidationError):
            ProjectMetadata(name="")

    def test_default_timestamps(self):
        """Test that timestamps are auto-generated."""
        metadata = ProjectMetadata(name="test")
        assert isinstance(metadata.created, datetime)
        assert isinstance(metadata.updated, datetime)

    def test_tags_list(self):
        """Test that tags are properly stored."""
        metadata = ProjectMetadata(name="test", tags=["tag1", "tag2", "tag3"])
        assert len(metadata.tags) == 3
        assert "tag1" in metadata.tags


# ============================================================================
# AUTHENTICATION CONFIGURATION TESTS
# ============================================================================


class TestAuthConfig:
    """Test authentication configuration."""

    def test_no_auth(self):
        """Test no authentication configuration."""
        auth = AuthConfig(type=AuthType.NONE)
        assert auth.type == AuthType.NONE
        assert auth.key is None

    def test_api_key_auth(self):
        """Test API key authentication."""
        auth = AuthConfig(type=AuthType.API_KEY, key="${API_KEY}", param_name="apikey")
        assert auth.type == AuthType.API_KEY
        assert auth.key == "${API_KEY}"
        assert auth.param_name == "apikey"

    def test_bearer_token_auth(self):
        """Test bearer token authentication."""
        auth = AuthConfig(
            type=AuthType.BEARER_TOKEN, key="${TOKEN}", header_name="Authorization"
        )
        assert auth.type == AuthType.BEARER_TOKEN
        assert auth.header_name == "Authorization"

    def test_basic_auth(self):
        """Test basic authentication."""
        auth = AuthConfig(
            type=AuthType.BASIC_AUTH, username="user", password="${PASSWORD}"
        )
        assert auth.type == AuthType.BASIC_AUTH
        assert auth.username == "user"
        assert auth.password == "${PASSWORD}"

    def test_env_var_syntax(self):
        """Test environment variable syntax validation."""
        # Should accept ${VAR} syntax
        auth = AuthConfig(type=AuthType.API_KEY, key="${MY_API_KEY}")
        assert auth.key.startswith("${")

    def test_plaintext_secret_warning(self):
        """Test that plaintext secrets generate warnings (not errors)."""
        # This should not raise an error, but may log a warning
        auth = AuthConfig(type=AuthType.API_KEY, key="plaintext_key_12345")
        assert auth.key == "plaintext_key_12345"


# ============================================================================
# CACHE CONFIGURATION TESTS
# ============================================================================


class TestCacheConfig:
    """Test caching configuration."""

    def test_default_cache_config(self):
        """Test default cache configuration."""
        cache = CacheConfig()
        assert cache.enabled is True
        assert cache.ttl == 3600
        assert cache.cache_dir == "data/cache"

    def test_custom_cache_config(self):
        """Test custom cache configuration."""
        cache = CacheConfig(
            enabled=True, ttl=7200, max_size_mb=50, cache_dir="custom/cache"
        )
        assert cache.ttl == 7200
        assert cache.max_size_mb == 50

    def test_negative_ttl_rejected(self):
        """Test that negative TTL is rejected."""
        with pytest.raises(ValidationError):
            CacheConfig(ttl=-100)

    def test_zero_ttl_allowed(self):
        """Test that zero TTL (no caching) is allowed."""
        cache = CacheConfig(ttl=0)
        assert cache.ttl == 0

    def test_very_long_ttl_allowed(self):
        """Test that long TTL values are allowed (with warning)."""
        cache = CacheConfig(ttl=86400 * 30)  # 30 days
        assert cache.ttl == 86400 * 30


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================


class TestRateLimitConfig:
    """Test rate limiting configuration."""

    def test_default_rate_limit(self):
        """Test default rate limiting."""
        rate_limit = RateLimitConfig()
        assert rate_limit.requests_per_second == 1.0

    def test_custom_rate_limit(self):
        """Test custom rate limiting."""
        rate_limit = RateLimitConfig(requests_per_second=2.5, burst_size=10)
        assert rate_limit.requests_per_second == 2.5
        assert rate_limit.burst_size == 10

    def test_zero_rate_rejected(self):
        """Test that zero requests per second is rejected."""
        with pytest.raises(ValidationError):
            RateLimitConfig(requests_per_second=0)

    def test_negative_rate_rejected(self):
        """Test that negative rate is rejected."""
        with pytest.raises(ValidationError):
            RateLimitConfig(requests_per_second=-1)

    def test_fractional_rate_allowed(self):
        """Test that fractional rates are allowed."""
        rate_limit = RateLimitConfig(requests_per_second=0.5)
        assert rate_limit.requests_per_second == 0.5


# ============================================================================
# DATA SOURCE CONFIGURATION TESTS
# ============================================================================


class TestDataSourceConfig:
    """Test data source configuration."""

    def test_api_source_valid(self):
        """Test valid API data source."""
        source = DataSourceConfig(
            type=DataSourceType.API,
            name="test_api",
            endpoint="https://api.example.com/data",
            auth=AuthConfig(type=AuthType.API_KEY, key="${KEY}"),
        )
        assert source.type == DataSourceType.API
        assert source.endpoint is not None

    def test_api_source_missing_endpoint(self):
        """Test that API source requires endpoint."""
        with pytest.raises(ValidationError) as exc_info:
            DataSourceConfig(
                type=DataSourceType.API,
                name="test_api",
                # Missing endpoint
            )
        assert "endpoint" in str(exc_info.value).lower()

    def test_url_source_valid(self):
        """Test valid URL data source."""
        source = DataSourceConfig(
            type=DataSourceType.URL, name="test_url", url="https://example.com/page"
        )
        assert source.type == DataSourceType.URL
        assert source.url is not None

    def test_url_source_missing_url(self):
        """Test that URL source requires url field."""
        with pytest.raises(ValidationError):
            DataSourceConfig(
                type=DataSourceType.URL,
                name="test_url",
                # Missing url
            )

    def test_file_source_valid(self):
        """Test valid file data source."""
        source = DataSourceConfig(
            type=DataSourceType.FILE, name="test_file", file_path="data/input.csv"
        )
        assert source.type == DataSourceType.FILE
        assert source.file_path is not None

    def test_file_source_missing_path(self):
        """Test that file source requires file_path."""
        with pytest.raises(ValidationError):
            DataSourceConfig(
                type=DataSourceType.FILE,
                name="test_file",
                # Missing file_path
            )

    def test_source_with_parameters(self):
        """Test data source with parameters."""
        source = DataSourceConfig(
            type=DataSourceType.API,
            name="test",
            endpoint="https://api.example.com",
            parameters={"format": "json", "limit": 100},
        )
        assert source.parameters["format"] == "json"
        assert source.parameters["limit"] == 100

    def test_source_with_headers(self):
        """Test data source with custom headers."""
        source = DataSourceConfig(
            type=DataSourceType.API,
            name="test",
            endpoint="https://api.example.com",
            headers={"User-Agent": "TestBot/1.0"},
        )
        assert source.headers["User-Agent"] == "TestBot/1.0"

    def test_source_with_cache(self):
        """Test data source with cache configuration."""
        source = DataSourceConfig(
            type=DataSourceType.API,
            name="test",
            endpoint="https://api.example.com",
            cache=CacheConfig(ttl=7200),
        )
        assert source.cache.ttl == 7200

    def test_source_with_rate_limit(self):
        """Test data source with rate limiting."""
        source = DataSourceConfig(
            type=DataSourceType.API,
            name="test",
            endpoint="https://api.example.com",
            rate_limit=RateLimitConfig(requests_per_second=2),
        )
        assert source.rate_limit.requests_per_second == 2


# ============================================================================
# EXAMPLE CONFIGURATION TESTS
# ============================================================================


class TestExampleConfig:
    """Test example-based learning configuration."""

    def test_valid_example(self):
        """Test valid example configuration."""
        example = ExampleConfig(
            input={"raw_field": "value"},
            output={"clean_field": "value"},
            description="Test example",
        )
        assert example.input["raw_field"] == "value"
        assert example.output["clean_field"] == "value"

    def test_empty_input_rejected(self):
        """Test that empty input is rejected."""
        with pytest.raises(ValidationError):
            ExampleConfig(input={}, output={"field": "value"})

    def test_empty_output_rejected(self):
        """Test that empty output is rejected."""
        with pytest.raises(ValidationError):
            ExampleConfig(input={"field": "value"}, output={})

    def test_nested_structures(self):
        """Test examples with nested structures."""
        example = ExampleConfig(
            input={
                "user": {"name": "John", "email": "john@example.com"},
                "data": {"value": 42},
            },
            output={"user_name": "John", "user_email": "john@example.com", "value": 42},
        )
        assert example.input["user"]["name"] == "John"
        assert example.output["user_name"] == "John"


# ============================================================================
# VALIDATION CONFIGURATION TESTS
# ============================================================================


class TestValidationConfig:
    """Test validation configuration."""

    def test_empty_validation(self):
        """Test empty validation configuration."""
        validation = ValidationConfig()
        assert len(validation.required_fields) == 0
        assert len(validation.field_types) == 0

    def test_required_fields(self):
        """Test required fields configuration."""
        validation = ValidationConfig(required_fields=["field1", "field2"])
        assert "field1" in validation.required_fields
        assert "field2" in validation.required_fields

    def test_field_types(self):
        """Test field type definitions."""
        validation = ValidationConfig(
            field_types={
                "name": FieldType.STRING,
                "age": FieldType.INTEGER,
                "price": FieldType.FLOAT,
            }
        )
        assert validation.field_types["name"] == FieldType.STRING
        assert validation.field_types["age"] == FieldType.INTEGER

    def test_field_constraints(self):
        """Test field constraints."""
        validation = ValidationConfig(
            constraints={
                "age": FieldConstraint(min=0, max=150),
                "email": FieldConstraint(pattern=r"^.+@.+\..+$"),
            }
        )
        assert validation.constraints["age"].min == 0
        assert validation.constraints["age"].max == 150
        assert validation.constraints["email"].pattern is not None


# ============================================================================
# OUTPUT CONFIGURATION TESTS
# ============================================================================


class TestOutputConfig:
    """Test output configuration."""

    def test_valid_output_config(self):
        """Test valid output configuration."""
        output = OutputConfig(
            formats=[
                OutputDestinationConfig(type=OutputFormat.CSV, path="output/data.csv")
            ]
        )
        assert len(output.formats) == 1
        assert output.formats[0].type == OutputFormat.CSV

    def test_multiple_output_formats(self):
        """Test multiple output formats."""
        output = OutputConfig(
            formats=[
                OutputDestinationConfig(type=OutputFormat.CSV, path="output.csv"),
                OutputDestinationConfig(type=OutputFormat.JSON, path="output.json"),
                OutputDestinationConfig(type=OutputFormat.EXCEL, path="output.xlsx"),
            ]
        )
        assert len(output.formats) == 3

    def test_empty_formats_rejected(self):
        """Test that empty formats list is rejected."""
        with pytest.raises(ValidationError):
            OutputConfig(formats=[])

    def test_output_with_timestamp(self):
        """Test output with timestamp option."""
        output = OutputConfig(
            formats=[
                OutputDestinationConfig(
                    type=OutputFormat.CSV, path="output.csv", include_timestamp=True
                )
            ]
        )
        assert output.formats[0].include_timestamp is True

    def test_json_pretty_print(self):
        """Test JSON pretty print option."""
        output = OutputConfig(
            formats=[
                OutputDestinationConfig(
                    type=OutputFormat.JSON, path="output.json", pretty_print=True
                )
            ]
        )
        assert output.formats[0].pretty_print is True


# ============================================================================
# RUNTIME CONFIGURATION TESTS
# ============================================================================


class TestRuntimeConfig:
    """Test runtime configuration."""

    def test_default_runtime_config(self):
        """Test default runtime configuration."""
        runtime = RuntimeConfig()
        assert runtime.log_level == "INFO"
        assert runtime.parallel is False
        assert runtime.error_strategy == ErrorStrategy.CONTINUE

    def test_custom_runtime_config(self):
        """Test custom runtime configuration."""
        runtime = RuntimeConfig(
            log_level="DEBUG",
            parallel=True,
            max_workers=8,
            error_strategy=ErrorStrategy.FAIL_FAST,
        )
        assert runtime.log_level == "DEBUG"
        assert runtime.parallel is True
        assert runtime.max_workers == 8

    def test_checkpoint_config(self):
        """Test checkpoint configuration."""
        runtime = RuntimeConfig(
            checkpoint_enabled=True, checkpoint_interval=5, checkpoint_dir="checkpoints"
        )
        assert runtime.checkpoint_enabled is True
        assert runtime.checkpoint_interval == 5

    def test_invalid_max_workers(self):
        """Test that zero workers is rejected."""
        with pytest.raises(ValidationError):
            RuntimeConfig(max_workers=0)

    def test_negative_max_workers_rejected(self):
        """Test that negative workers is rejected."""
        with pytest.raises(ValidationError):
            RuntimeConfig(max_workers=-1)


# ============================================================================
# FULL PROJECT CONFIGURATION TESTS
# ============================================================================


class TestProjectConfig:
    """Test complete project configuration."""

    def test_minimal_valid_config(self):
        """Test minimal valid project configuration."""
        config = ProjectConfig(
            project=ProjectMetadata(name="test"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API,
                    name="api1",
                    endpoint="https://api.example.com",
                )
            ],
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(type=OutputFormat.JSON, path="output.json")
                ]
            ),
        )
        assert config.project.name == "test"
        assert len(config.data_sources) == 1
        assert len(config.output.formats) == 1

    def test_full_config(self):
        """Test complete project configuration."""
        config = ProjectConfig(
            project=ProjectMetadata(
                name="full_test", description="Full test", version="1.0.0"
            ),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API,
                    name="api1",
                    endpoint="https://api.example.com",
                    auth=AuthConfig(type=AuthType.API_KEY, key="${API_KEY}"),
                )
            ],
            examples=[ExampleConfig(input={"raw": "data"}, output={"clean": "data"})],
            validation=ValidationConfig(required_fields=["clean"]),
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(type=OutputFormat.CSV, path="output.csv")
                ]
            ),
            runtime=RuntimeConfig(log_level="INFO", parallel=True),
        )
        assert config.project.name == "full_test"
        assert len(config.examples) == 1
        assert config.runtime.parallel is True

    def test_no_data_sources_rejected(self):
        """Test that configuration without data sources is rejected."""
        with pytest.raises(ValidationError):
            ProjectConfig(
                project=ProjectMetadata(name="test"),
                data_sources=[],  # Empty
                output=OutputConfig(
                    formats=[
                        OutputDestinationConfig(
                            type=OutputFormat.JSON, path="output.json"
                        )
                    ]
                ),
            )

    def test_duplicate_source_names_rejected(self):
        """Test that duplicate source names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectConfig(
                project=ProjectMetadata(name="test"),
                data_sources=[
                    DataSourceConfig(
                        type=DataSourceType.API,
                        name="api1",
                        endpoint="https://api.example.com",
                    ),
                    DataSourceConfig(
                        type=DataSourceType.API,
                        name="api1",  # Duplicate name
                        endpoint="https://api2.example.com",
                    ),
                ],
                output=OutputConfig(
                    formats=[
                        OutputDestinationConfig(
                            type=OutputFormat.JSON, path="output.json"
                        )
                    ]
                ),
            )
        assert "unique" in str(exc_info.value).lower()

    def test_comprehensive_validation(self):
        """Test comprehensive validation method."""
        config = ProjectConfig(
            project=ProjectMetadata(name="test"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API,
                    name="api1",
                    endpoint="https://api.example.com",
                    auth=AuthConfig(
                        type=AuthType.API_KEY,
                        key="plaintext_key",  # Should trigger warning
                    ),
                )
            ],
            examples=[],  # No examples - should trigger recommendation
            validation=ValidationConfig(required_fields=["field1", "field2"]),
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(type=OutputFormat.JSON, path="output.json")
                ]
            ),
        )

        results = config.validate_comprehensive()

        # Should have warnings about plaintext key and no examples
        assert len(results["warnings"]) > 0 or len(results["recommendations"]) > 0


# ============================================================================
# YAML SERIALIZATION TESTS
# ============================================================================


class TestYAMLSerialization:
    """Test YAML file loading and saving."""

    def test_from_yaml_valid_file(self, tmp_path):
        """Test loading from valid YAML file."""
        yaml_content = """
project:
  name: test_project
  description: Test
  version: 1.0.0

data_sources:
  - type: api
    name: test_api
    endpoint: https://api.example.com

output:
  formats:
    - type: json
      path: output.json
"""
        yaml_file = tmp_path / "project.yaml"
        yaml_file.write_text(yaml_content)

        config = ProjectConfig.from_yaml(yaml_file)
        assert config.project.name == "test_project"
        assert len(config.data_sources) == 1

    def test_from_yaml_missing_file(self, tmp_path):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            ProjectConfig.from_yaml(tmp_path / "missing.yaml")

    def test_to_yaml(self, tmp_path):
        """Test saving to YAML file."""
        config = ProjectConfig(
            project=ProjectMetadata(name="test"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API,
                    name="api1",
                    endpoint="https://api.example.com",
                )
            ],
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(type=OutputFormat.JSON, path="output.json")
                ]
            ),
        )

        yaml_file = tmp_path / "output.yaml"
        config.to_yaml(yaml_file)

        assert yaml_file.exists()
        # Load it back to verify
        loaded = ProjectConfig.from_yaml(yaml_file)
        assert loaded.project.name == "test"


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_very_long_project_name(self):
        """Test handling of very long project names."""
        long_name = "a" * 1000
        metadata = ProjectMetadata(name=long_name)
        assert metadata.name == long_name.lower()

    def test_unicode_in_project_name(self):
        """Test that unicode characters are rejected."""
        with pytest.raises(ValidationError):
            ProjectMetadata(name="test_🚀_project")

    def test_empty_examples_list(self):
        """Test empty examples list (allowed but warned)."""
        config = ProjectConfig(
            project=ProjectMetadata(name="test"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API,
                    name="api1",
                    endpoint="https://api.example.com",
                )
            ],
            examples=[],  # Empty but allowed
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(type=OutputFormat.JSON, path="output.json")
                ]
            ),
        )
        assert len(config.examples) == 0

    def test_special_characters_in_paths(self):
        """Test paths with special characters."""
        output = OutputConfig(
            formats=[
                OutputDestinationConfig(
                    type=OutputFormat.CSV, path="output/data (2024-01-15).csv"
                )
            ]
        )
        assert "2024-01-15" in output.formats[0].path

    def test_very_high_worker_count(self):
        """Test very high worker count (allowed with warning)."""
        runtime = RuntimeConfig(max_workers=100)
        assert runtime.max_workers == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
