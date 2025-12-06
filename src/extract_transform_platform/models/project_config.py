"""
Project configuration models for the general-purpose extract & transform platform.

This module defines the complete schema for project.yaml configuration files,
supporting multiple data source types, transformations, and output formats.

Design Decisions:
- **YAML over JSON**: Human-readable, supports comments, widely adopted for config
- **Pydantic for Validation**: Strong typing, automatic validation, IDE support
- **Environment Variables**: ${VAR} syntax for secrets (prevents credential leakage)
- **Example-Based Learning**: Input/output pairs teach Sonnet 4.5 transformations
- **Extensibility**: Plugin-based source types for easy extension

Example Usage:
    >>> from pathlib import Path
    >>> config = ProjectConfig.from_yaml(Path("project.yaml"))
    >>> config.validate()
    >>> for source in config.data_sources:
    ...     print(f"Source: {source.name} ({source.type})")
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

# ============================================================================
# ENUMERATIONS
# ============================================================================


class DataSourceType(str, Enum):
    """Supported data source types.

    Extensibility: Add new source types by extending this enum and implementing
    corresponding handler in src/edgar_analyzer/extractors/.
    """

    FILE = "file"  # Local file (CSV, JSON, XML, etc.)
    URL = "url"  # Web resource (HTML, API endpoint)
    API = "api"  # REST API with parameters
    JINA = "jina"  # Jina.ai web reader API
    EDGAR = "edgar"  # SEC EDGAR-specific API


class AuthType(str, Enum):
    """Authentication methods for data sources."""

    NONE = "none"  # No authentication
    API_KEY = "api_key"  # API key in header or parameter
    BEARER_TOKEN = "bearer"  # Bearer token authentication
    BASIC_AUTH = "basic"  # HTTP Basic Authentication
    OAUTH2 = "oauth2"  # OAuth 2.0 (future extension)


class OutputFormat(str, Enum):
    """Supported output formats."""

    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PARQUET = "parquet"
    DATABASE = "database"


class ErrorStrategy(str, Enum):
    """Error handling strategies during extraction."""

    FAIL_FAST = "fail_fast"  # Stop on first error
    CONTINUE = "continue"  # Log errors and continue
    SKIP_INVALID = "skip_invalid"  # Skip invalid records


class FieldType(str, Enum):
    """Supported field data types for validation."""

    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "bool"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"
    DICT = "dict"


# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================


class AuthConfig(BaseModel):
    """Authentication configuration for data sources.

    Supports multiple authentication methods with secure secret management.
    Environment variables prevent credential leakage in version control.

    Example:
        >>> auth = AuthConfig(
        ...     type=AuthType.API_KEY,
        ...     key="${OPENWEATHER_API_KEY}",
        ...     param_name="appid"
        ... )
    """

    type: AuthType = Field(default=AuthType.NONE, description="Authentication method")
    key: Optional[str] = Field(
        None, description="API key or token (use ${ENV_VAR} syntax for secrets)"
    )
    param_name: Optional[str] = Field(
        None, description="Parameter name for API key (e.g., 'appid', 'api_key')"
    )
    header_name: Optional[str] = Field(
        None, description="Header name for token (e.g., 'Authorization', 'X-API-Key')"
    )
    username: Optional[str] = Field(None, description="Username for basic auth")
    password: Optional[str] = Field(
        None, description="Password for basic auth (use ${ENV_VAR})"
    )

    @field_validator("key", "password")
    @classmethod
    def validate_secrets(cls, v: Optional[str]) -> Optional[str]:
        """Warn if secrets are not using environment variables."""
        if v and not v.startswith("${"):
            # Warning: not a hard error to allow testing
            pass
        return v


# ============================================================================
# CACHING CONFIGURATION
# ============================================================================


class CacheConfig(BaseModel):
    """Caching configuration for data sources.

    Reduces API calls and improves performance for repeated queries.

    Trade-offs:
    - **Performance**: Cached responses = instant (vs. API latency)
    - **Freshness**: Stale data risk (mitigated by TTL)
    - **Storage**: Disk space usage (mitigated by max_size)

    Example:
        >>> cache = CacheConfig(enabled=True, ttl=3600, max_size_mb=100)
    """

    enabled: bool = Field(default=True, description="Enable response caching")
    ttl: int = Field(
        default=3600, description="Time-to-live in seconds (default: 1 hour)"
    )
    max_size_mb: Optional[int] = Field(None, description="Maximum cache size in MB")
    cache_dir: str = Field(default="data/cache", description="Cache directory path")

    @field_validator("ttl")
    @classmethod
    def validate_ttl(cls, v: int) -> int:
        """Ensure reasonable TTL values."""
        if v < 0:
            raise ValueError("TTL must be non-negative")
        if v > 86400 * 7:  # 7 days
            # Warning for long TTL (data freshness concern)
            pass
        return v


# ============================================================================
# RATE LIMITING CONFIGURATION
# ============================================================================


class RateLimitConfig(BaseModel):
    """Rate limiting configuration for API sources.

    Prevents API quota exhaustion and respects service limits.

    Design Decision: Implemented as requests/second rather than complex
    token bucket algorithm for simplicity. Sufficient for most APIs.

    Example:
        >>> rate_limit = RateLimitConfig(requests_per_second=1, burst_size=5)
    """

    requests_per_second: float = Field(
        default=1.0, description="Maximum requests per second"
    )
    burst_size: Optional[int] = Field(
        None, description="Burst allowance for request spikes"
    )

    @field_validator("requests_per_second")
    @classmethod
    def validate_rate(cls, v: float) -> float:
        """Ensure positive rate."""
        if v <= 0:
            raise ValueError("requests_per_second must be positive")
        return v


# ============================================================================
# DATA SOURCE CONFIGURATION
# ============================================================================


class DataSourceConfig(BaseModel):
    """Configuration for a single data source.

    Supports multiple source types with extensible architecture.
    Each source type may have specific configuration requirements.

    Extensibility: Add new source types by:
    1. Adding to DataSourceType enum
    2. Creating handler in src/edgar_analyzer/extractors/
    3. Adding source-specific options to this model

    Example:
        >>> source = DataSourceConfig(
        ...     type=DataSourceType.API,
        ...     name="weather_api",
        ...     endpoint="https://api.openweathermap.org/data/2.5/weather",
        ...     auth=AuthConfig(type=AuthType.API_KEY, key="${API_KEY}"),
        ...     parameters={"units": "metric"}
        ... )
    """

    type: DataSourceType = Field(..., description="Data source type")
    name: str = Field(
        ..., description="Unique source name (used in references and logging)"
    )
    # Source location (one required based on type)
    endpoint: Optional[str] = Field(
        None, description="API endpoint URL (for API sources)"
    )
    url: Optional[str] = Field(None, description="Web URL (for URL sources)")
    file_path: Optional[str] = Field(None, description="File path (for FILE sources)")
    # Authentication
    auth: AuthConfig = Field(
        default_factory=lambda: AuthConfig(type=AuthType.NONE),
        description="Authentication configuration",
    )
    # Request parameters
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Query parameters or request options (supports ${VAR} templating)",
    )
    headers: Dict[str, str] = Field(
        default_factory=dict, description="Custom HTTP headers"
    )
    # Performance and reliability
    cache: CacheConfig = Field(
        default_factory=CacheConfig, description="Caching configuration"
    )
    rate_limit: Optional[RateLimitConfig] = Field(
        None, description="Rate limiting configuration"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(
        default=3, description="Maximum retry attempts for failed requests"
    )
    # Source-specific options
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Source-type-specific options"
    )

    @model_validator(mode="after")
    def validate_source_location(self) -> "DataSourceConfig":
        """Ensure appropriate location field is provided for source type."""
        if self.type == DataSourceType.API and not self.endpoint:
            raise ValueError("API sources require 'endpoint' field")
        if self.type == DataSourceType.URL and not self.url:
            raise ValueError("URL sources require 'url' field")
        if self.type == DataSourceType.FILE and not self.file_path:
            raise ValueError("FILE sources require 'file_path' field")

        return self


# ============================================================================
# EXAMPLE-BASED LEARNING CONFIGURATION
# ============================================================================


class ExampleConfig(BaseModel):
    """Example input/output pair for teaching transformations to Sonnet 4.5.

    Design Decision: Example-based learning > rule-based transformations.

    Why Examples Work Better:
    - **Intuitive**: Easier for users to provide examples than write rules
    - **Flexible**: Handles complex transformations without programming
    - **Self-Documenting**: Examples serve as documentation
    - **LLM-Native**: Leverages Sonnet 4.5's pattern recognition

    Trade-offs:
    - Requires quality examples (garbage in = garbage out)
    - May need multiple examples for edge cases
    - Less deterministic than explicit rules

    Example:
        >>> example = ExampleConfig(
        ...     input={"temp": 15.5, "weather": [{"desc": "rain"}]},
        ...     output={"temperature_c": 15.5, "conditions": "rain"}
        ... )
    """

    input: Dict[str, Any] = Field(
        ..., description="Example input data (raw API response, file content, etc.)"
    )
    output: Dict[str, Any] = Field(
        ..., description="Expected output structure after transformation"
    )
    description: Optional[str] = Field(
        None, description="Optional description of what this example demonstrates"
    )

    @field_validator("input", "output")
    @classmethod
    def validate_non_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure examples are not empty."""
        if not v:
            raise ValueError("Examples must contain data")
        return v


# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================


class FieldConstraint(BaseModel):
    """Validation constraints for a single field.

    Example:
        >>> constraint = FieldConstraint(min=0, max=100, pattern=r"^\\d+$")
    """

    min: Optional[Union[int, float]] = Field(
        None, description="Minimum value (numeric fields)"
    )
    max: Optional[Union[int, float]] = Field(
        None, description="Maximum value (numeric fields)"
    )
    min_length: Optional[int] = Field(None, description="Minimum string length")
    max_length: Optional[int] = Field(None, description="Maximum string length")
    pattern: Optional[str] = Field(None, description="Regex pattern for validation")
    allowed_values: Optional[List[Any]] = Field(
        None, description="List of allowed values (enum-like validation)"
    )


class ValidationConfig(BaseModel):
    """Data validation rules for extracted data.

    Ensures data quality and catches extraction errors early.

    Example:
        >>> validation = ValidationConfig(
        ...     required_fields=["city", "temperature"],
        ...     field_types={"temperature": FieldType.FLOAT},
        ...     constraints={"temperature": FieldConstraint(min=-50, max=60)}
        ... )
    """

    required_fields: List[str] = Field(
        default_factory=list, description="List of required output fields"
    )
    field_types: Dict[str, FieldType] = Field(
        default_factory=dict, description="Expected type for each field"
    )
    constraints: Dict[str, FieldConstraint] = Field(
        default_factory=dict, description="Validation constraints per field"
    )
    allow_extra_fields: bool = Field(
        default=True, description="Allow fields not defined in validation schema"
    )


# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================


class OutputDestinationConfig(BaseModel):
    """Configuration for a single output destination.

    Supports multiple output formats simultaneously.

    Example:
        >>> output = OutputDestinationConfig(
        ...     type=OutputFormat.CSV,
        ...     path="output/weather.csv",
        ...     include_timestamp=True
        ... )
    """

    type: OutputFormat = Field(..., description="Output format")
    path: str = Field(..., description="Output file path or database connection string")
    include_timestamp: bool = Field(
        default=False, description="Include timestamp in filename"
    )
    pretty_print: bool = Field(
        default=False, description="Pretty-print JSON output (JSON format only)"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Format-specific options (e.g., CSV delimiter, Excel sheet name)",
    )


class OutputConfig(BaseModel):
    """Output configuration for extraction results.

    Example:
        >>> output = OutputConfig(
            formats=[
                OutputDestinationConfig(type=OutputFormat.CSV, path="output.csv"),
                OutputDestinationConfig(type=OutputFormat.JSON, path="output.json")
            ]
        ... )
    """

    formats: List[OutputDestinationConfig] = Field(
        default_factory=list, description="List of output destinations"
    )

    @field_validator("formats")
    @classmethod
    def validate_at_least_one_format(
        cls, v: List[OutputDestinationConfig]
    ) -> List[OutputDestinationConfig]:
        """Ensure at least one output format is configured."""
        if not v:
            raise ValueError("At least one output format must be configured")
        return v


# ============================================================================
# RUNTIME CONFIGURATION
# ============================================================================


class RuntimeConfig(BaseModel):
    """Runtime execution configuration.

    Controls how the extraction pipeline executes.

    Trade-offs:
    - **Parallel Processing**: Faster but higher memory usage
    - **Fail-Fast**: Faster failure detection but may miss partial results
    - **Checkpointing**: Resume capability but disk I/O overhead

    Example:
        >>> runtime = RuntimeConfig(
        ...     log_level="DEBUG",
        ...     parallel=True,
        ...     max_workers=4,
        ...     error_strategy=ErrorStrategy.CONTINUE
        ... )
    """

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    parallel: bool = Field(
        default=False, description="Enable parallel processing for multiple records"
    )
    max_workers: int = Field(
        default=4, description="Maximum worker threads/processes for parallel execution"
    )
    error_strategy: ErrorStrategy = Field(
        default=ErrorStrategy.CONTINUE,
        description="How to handle errors during extraction",
    )
    checkpoint_enabled: bool = Field(
        default=False, description="Enable checkpointing for resumable extraction"
    )
    checkpoint_interval: int = Field(
        default=10, description="Save checkpoint every N records"
    )
    checkpoint_dir: str = Field(
        default="data/checkpoints", description="Directory for checkpoint files"
    )

    @field_validator("max_workers")
    @classmethod
    def validate_max_workers(cls, v: int) -> int:
        """Ensure reasonable worker count."""
        if v < 1:
            raise ValueError("max_workers must be at least 1")
        if v > 32:
            # Warning: excessive parallelism may cause resource issues
            pass
        return v


# ============================================================================
# PROJECT METADATA
# ============================================================================


class ProjectMetadata(BaseModel):
    """Project metadata and description.

    Example:
        >>> metadata = ProjectMetadata(
        ...     name="weather_extractor",
        ...     description="Extract weather data",
        ...     version="1.0.0",
        ...     author="Platform User",
        ...     tags=["weather", "api"]
        ... )
    """

    name: str = Field(..., description="Project name (lowercase, underscores allowed)")
    description: str = Field(default="", description="Project description")
    version: str = Field(
        default="1.0.0", description="Project version (semver recommended)"
    )
    author: Optional[str] = Field(None, description="Author name or organization")
    created: datetime = Field(
        default_factory=datetime.now, description="Project creation timestamp"
    )
    updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags for categorization and search"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure project name is valid identifier."""
        if not v:
            raise ValueError("Project name cannot be empty")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Project name must be alphanumeric (underscores/hyphens allowed)"
            )
        return v.lower()


# ============================================================================
# ROOT PROJECT CONFIGURATION
# ============================================================================


class ProjectConfig(BaseModel):
    """Root project configuration model.

    This is the complete schema for project.yaml files.

    Design Philosophy:
    - **Declarative**: Describe WHAT to extract, not HOW
    - **Self-Contained**: Single file contains all configuration
    - **Portable**: No hardcoded paths or credentials
    - **Testable**: Validation ensures correctness before execution

    Example:
        >>> config = ProjectConfig(
        ...     project=ProjectMetadata(name="my_project"),
        ...     data_sources=[...],
        ...     examples=[...],
        ...     validation=ValidationConfig(...),
        ...     output=OutputConfig(...),
        ...     runtime=RuntimeConfig(...)
        ... )
        >>> config.validate()
    """

    project: ProjectMetadata = Field(..., description="Project metadata")
    data_sources: List[DataSourceConfig] = Field(
        default_factory=list, description="List of data sources to extract from"
    )
    examples: List[ExampleConfig] = Field(
        default_factory=list,
        description="Example input/output pairs for transformation learning",
    )
    validation: ValidationConfig = Field(
        default_factory=ValidationConfig, description="Data validation rules"
    )
    output: OutputConfig = Field(..., description="Output configuration")
    runtime: RuntimeConfig = Field(
        default_factory=RuntimeConfig, description="Runtime execution configuration"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for pattern detection (0.0-1.0)",
    )

    @field_validator("data_sources")
    @classmethod
    def validate_at_least_one_source(
        cls, v: List[DataSourceConfig]
    ) -> List[DataSourceConfig]:
        """Ensure at least one data source is configured."""
        if not v:
            raise ValueError("At least one data source must be configured")
        return v

    @field_validator("data_sources")
    @classmethod
    def validate_unique_source_names(
        cls, v: List[DataSourceConfig]
    ) -> List[DataSourceConfig]:
        """Ensure data source names are unique."""
        names = [source.name for source in v]
        if len(names) != len(set(names)):
            raise ValueError("Data source names must be unique")
        return v

    @field_validator("examples")
    @classmethod
    def validate_examples_provided(cls, v: List[ExampleConfig]) -> List[ExampleConfig]:
        """Recommend providing examples for better transformation quality."""
        if not v:
            # Warning: extraction may be less accurate without examples
            pass
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> "ProjectConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to project.yaml file

        Returns:
            Validated ProjectConfig instance

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValidationError: If configuration is invalid

        Example:
            >>> config = ProjectConfig.from_yaml(Path("project.yaml"))
        """
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file.

        Args:
            path: Destination path for YAML file

        Example:
            >>> config.to_yaml(Path("project.yaml"))
        """
        # Use mode='json' to serialize enums as strings
        data = self.model_dump(mode="json", exclude_none=True)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def validate_comprehensive(self) -> Dict[str, List[str]]:
        """Perform comprehensive validation beyond Pydantic model validation.

        Returns:
            Dictionary mapping validation categories to warning/error messages.
            Empty lists indicate no issues in that category.

        Categories:
        - errors: Critical issues that prevent execution
        - warnings: Non-critical issues that may impact quality
        - recommendations: Best practice suggestions

        Example:
            >>> results = config.validate_comprehensive()
            >>> if results['errors']:
            ...     print("Fix these errors:", results['errors'])
        """
        results = {"errors": [], "warnings": [], "recommendations": []}

        # Check for secrets in plaintext
        for source in self.data_sources:
            if source.auth.key and not source.auth.key.startswith("${"):
                results["warnings"].append(
                    f"Source '{source.name}' has plaintext API key. "
                    f"Use environment variable syntax: ${{VAR_NAME}}"
                )

        # Recommend examples for better quality
        if len(self.examples) < 2:
            results["recommendations"].append(
                "Provide at least 2-3 examples for better transformation quality"
            )

        # Check validation coverage
        if self.validation.required_fields:
            example_fields = set()
            for example in self.examples:
                example_fields.update(example.output.keys())

            missing = set(self.validation.required_fields) - example_fields
            if missing:
                results["warnings"].append(
                    f"Required fields missing from examples: {missing}"
                )

        # Check parallel processing with checkpoint
        if self.runtime.parallel and not self.runtime.checkpoint_enabled:
            results["recommendations"].append(
                "Consider enabling checkpointing for parallel processing "
                "to recover from failures"
            )

        return results


# ============================================================================
# SCHEMA VERSION AND METADATA
# ============================================================================

SCHEMA_VERSION = "1.0.0"
SUPPORTED_SOURCE_TYPES = [t.value for t in DataSourceType]
SUPPORTED_OUTPUT_FORMATS = [f.value for f in OutputFormat]
