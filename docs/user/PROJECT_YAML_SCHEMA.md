# Project YAML Schema Documentation

**Schema Version**: 1.0.0
**Implementation**: `src/edgar_analyzer/models/project_config.py`
**Status**: ✅ Production-Ready (validated with weather_api project)

## Table of Contents
- [Overview](#overview)
- [Complete Schema Structure](#complete-schema-structure)
- [Section Details](#section-details)
  - [Project Metadata](#project-metadata)
  - [Data Sources](#data-sources)
  - [Examples](#examples)
  - [Validation Rules](#validation-rules)
  - [Output Configuration](#output-configuration)
  - [Runtime Settings](#runtime-settings)
- [Field Reference](#field-reference)
- [Validation Rules](#validation-rules-1)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)

---

## Overview

The `project.yaml` schema defines the complete configuration for example-driven data extraction projects. It uses **Pydantic** for strong typing and validation, ensuring configuration correctness before execution.

### Design Philosophy
- **Declarative**: Describe WHAT to extract, not HOW
- **Self-Contained**: Single file contains all configuration
- **Portable**: No hardcoded paths or credentials
- **Testable**: Validation ensures correctness before execution

### Key Features
- Environment variable substitution for secrets (`${VAR_NAME}`)
- Multi-source data integration (API, file, URL, EDGAR, Jina)
- Example-based transformation learning (Sonnet 4.5)
- Comprehensive validation with constraints
- Multiple output format support (CSV, JSON, Excel, Parquet)
- Built-in caching and rate limiting
- Checkpoint-based resumable execution

---

## Complete Schema Structure

```yaml
# Project Metadata
project:
  name: string                    # Required: lowercase, alphanumeric, underscores/hyphens
  description: string             # Optional
  version: string                 # Default: "1.0.0"
  author: string                  # Optional
  tags: [string]                  # Optional: for categorization

# Data Sources (at least 1 required)
data_sources:
  - type: file|url|api|jina|edgar  # Required
    name: string                    # Required: unique identifier

    # Source location (one required based on type)
    endpoint: string                # For API sources
    url: string                     # For URL sources
    file_path: string               # For FILE sources

    # Authentication (optional)
    auth:
      type: none|api_key|bearer|basic|oauth2
      key: string                   # Use ${ENV_VAR} for secrets
      param_name: string            # For API key parameter
      header_name: string           # For token header
      username: string              # For basic auth
      password: string              # Use ${ENV_VAR}

    # Request configuration
    parameters: {key: value}        # Query parameters or options
    headers: {key: value}           # Custom HTTP headers

    # Performance and reliability
    cache:
      enabled: bool                 # Default: true
      ttl: int                      # Seconds, default: 3600
      max_size_mb: int              # Optional
      cache_dir: string             # Default: "data/cache"

    rate_limit:
      requests_per_second: float    # Default: 1.0
      burst_size: int               # Optional burst allowance

    timeout: int                    # Seconds, default: 30
    max_retries: int                # Default: 3

    # Source-specific options
    options: {key: value}           # Type-specific configuration

# Examples (recommended: 5+ for quality)
examples:
  - input: {any}                    # Raw input data structure
    output: {any}                   # Expected output structure
    description: string             # Optional: what this example demonstrates

# Validation Rules
validation:
  required_fields: [string]         # Fields that must exist in output

  field_types:                      # Expected types
    field_name: str|int|float|decimal|bool|date|datetime|list|dict

  constraints:                      # Value constraints
    field_name:
      min: number                   # Minimum value (numeric)
      max: number                   # Maximum value (numeric)
      min_length: int               # Minimum string length
      max_length: int               # Maximum string length
      pattern: string               # Regex pattern
      allowed_values: [any]         # Enum-like validation

  allow_extra_fields: bool          # Default: true

# Output Configuration (at least 1 format required)
output:
  formats:
    - type: csv|json|excel|parquet|database
      path: string                  # Output file path or connection string
      include_timestamp: bool       # Default: false
      pretty_print: bool            # Default: false (JSON only)
      options: {key: value}         # Format-specific options

# Runtime Execution Settings
runtime:
  log_level: DEBUG|INFO|WARNING|ERROR|CRITICAL  # Default: INFO
  parallel: bool                    # Default: false
  max_workers: int                  # Default: 4
  error_strategy: fail_fast|continue|skip_invalid  # Default: continue

  checkpoint_enabled: bool          # Default: false
  checkpoint_interval: int          # Save every N records, default: 10
  checkpoint_dir: string            # Default: "data/checkpoints"
```

---

## Section Details

### Project Metadata

**Purpose**: Identifies and describes the project.

```yaml
project:
  name: weather_api_extractor
  description: Extract current weather data from OpenWeatherMap API
  version: 1.0.0
  author: Platform MVP Team
  tags:
    - weather
    - api
    - mvp
```

**Validation Rules**:
- `name`: Required, lowercase, alphanumeric with underscores/hyphens only
- `version`: Recommended to follow semantic versioning (X.Y.Z)
- `tags`: Optional, used for categorization and search

---

### Data Sources

**Purpose**: Defines where to retrieve data from.

#### API Source Example
```yaml
data_sources:
  - type: api
    name: openweathermap
    endpoint: https://api.openweathermap.org/data/2.5/weather

    auth:
      type: api_key
      key: ${OPENWEATHER_API_KEY}
      param_name: appid

    parameters:
      units: metric

    headers:
      User-Agent: WeatherExtractorMVP/1.0

    cache:
      enabled: true
      ttl: 1800  # 30 minutes
      cache_dir: data/cache/weather

    rate_limit:
      requests_per_second: 0.5
      burst_size: 3

    timeout: 10
    max_retries: 3
```

#### Supported Source Types

| Type | Description | Required Fields | Use Case |
|------|-------------|-----------------|----------|
| `file` | Local files | `file_path` | CSV, JSON, XML files |
| `url` | Web resources | `url` | Web scraping, HTML pages |
| `api` | REST APIs | `endpoint` | API integrations |
| `jina` | Jina.ai reader | `url` | Web content extraction |
| `edgar` | SEC EDGAR | `endpoint` | SEC filings |

#### Authentication Types

| Type | Required Fields | Description |
|------|-----------------|-------------|
| `none` | - | No authentication |
| `api_key` | `key`, `param_name` or `header_name` | API key in parameter or header |
| `bearer` | `key`, `header_name` | Bearer token authentication |
| `basic` | `username`, `password` | HTTP Basic Auth |
| `oauth2` | TBD | OAuth 2.0 (future) |

**Security Note**: Always use environment variable syntax for secrets:
```yaml
auth:
  key: ${API_KEY}  # ✅ Correct
  key: "abc123"    # ❌ Insecure - hardcoded secret
```

---

### Examples

**Purpose**: Teach the AI how to transform input to output through examples.

```yaml
examples:
  - input:
      coord: {lon: -0.1257, lat: 51.5085}
      weather: [{id: 500, main: Rain, description: light rain}]
      main: {temp: 15.5, feels_like: 14.2, humidity: 72}
      name: London
    output:
      city: London
      temperature_c: 15.5
      feels_like_c: 14.2
      humidity_percent: 72
      conditions: light rain
    description: "Rainy temperate climate - demonstrates nested field extraction"
```

**Recommendations**:
- Provide **5-7 diverse examples** for best quality
- Cover **edge cases**: negative values, missing fields, extreme ranges
- Include **description** to explain what each example demonstrates
- Ensure examples match **validation schema** (required fields, types)

**Why Examples Work**:
- More intuitive than writing transformation rules
- Self-documenting (examples serve as specification)
- Leverages Sonnet 4.5's pattern recognition capabilities

---

### Validation Rules

**Purpose**: Ensure data quality and catch extraction errors.

```yaml
validation:
  required_fields:
    - city
    - temperature_c
    - humidity_percent

  field_types:
    city: str
    country: str
    temperature_c: float
    humidity_percent: int
    conditions: str

  constraints:
    temperature_c:
      min: -60.0
      max: 60.0
    humidity_percent:
      min: 0
      max: 100
    city:
      min_length: 2
      max_length: 100

  allow_extra_fields: true
```

**Supported Field Types**:
- `str`: String
- `int`: Integer
- `float`: Floating point
- `decimal`: Decimal (high precision)
- `bool`: Boolean
- `date`: Date only
- `datetime`: Date and time
- `list`: Array/list
- `dict`: Dictionary/object

**Constraint Types**:
- **Numeric**: `min`, `max`
- **String**: `min_length`, `max_length`, `pattern` (regex)
- **Enum**: `allowed_values` (list of valid values)

---

### Output Configuration

**Purpose**: Defines output format(s) and destination(s).

```yaml
output:
  formats:
    # CSV output
    - type: csv
      path: output/weather_data.csv
      include_timestamp: false
      options:
        delimiter: ","
        quoting: minimal

    # JSON output
    - type: json
      path: output/weather_data.json
      pretty_print: true
      include_timestamp: false
```

**Supported Output Formats**:

| Format | Extension | Options | Use Case |
|--------|-----------|---------|----------|
| `csv` | `.csv` | `delimiter`, `quoting` | Data analysis, Excel import |
| `json` | `.json` | `pretty_print` | API integration, web apps |
| `excel` | `.xlsx` | `sheet_name` | Business reporting |
| `parquet` | `.parquet` | `compression` | Big data, analytics |
| `database` | - | `connection_string` | Persistent storage |

**Multiple Outputs**: You can specify multiple output formats to generate CSV, JSON, and Excel simultaneously.

---

### Runtime Settings

**Purpose**: Controls execution behavior.

```yaml
runtime:
  log_level: INFO
  parallel: false
  max_workers: 1
  error_strategy: continue

  checkpoint_enabled: false
  checkpoint_interval: 10
  checkpoint_dir: data/checkpoints/weather
```

**Configuration Options**:

| Field | Values | Default | Description |
|-------|--------|---------|-------------|
| `log_level` | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO | Logging verbosity |
| `parallel` | true/false | false | Enable parallel processing |
| `max_workers` | 1-32 | 4 | Thread/process count |
| `error_strategy` | fail_fast, continue, skip_invalid | continue | Error handling |
| `checkpoint_enabled` | true/false | false | Enable checkpointing |
| `checkpoint_interval` | integer | 10 | Records between checkpoints |

**Error Strategies**:
- `fail_fast`: Stop on first error (useful for debugging)
- `continue`: Log errors and continue (recommended for production)
- `skip_invalid`: Skip invalid records, continue with valid ones

**Trade-offs**:
- **Parallel Processing**: Faster but higher memory usage
- **Checkpointing**: Resume capability but disk I/O overhead
- **Fail-Fast**: Quick error detection but may miss partial results

---

## Field Reference

### Required vs Optional Fields

#### Minimal Valid Configuration
```yaml
project:
  name: my_project  # REQUIRED

data_sources:
  - type: api       # REQUIRED
    name: api1      # REQUIRED
    endpoint: https://api.example.com  # REQUIRED (for API type)

output:
  formats:
    - type: json    # REQUIRED
      path: output.json  # REQUIRED
```

#### Full Configuration (All Optional Fields)
See [Complete Schema Structure](#complete-schema-structure) above.

---

## Validation Rules

### Schema-Level Validation (Pydantic)

1. **At least one data source** must be configured
2. **Data source names must be unique**
3. **At least one output format** must be configured
4. **Source type must match location field**:
   - `api` → requires `endpoint`
   - `url` → requires `url`
   - `file` → requires `file_path`
5. **Project name** must be alphanumeric (underscores/hyphens allowed)

### Comprehensive Validation (`validate_comprehensive()`)

Additional checks beyond Pydantic:

**Errors** (prevent execution):
- None currently (all critical checks in Pydantic)

**Warnings** (impact quality):
- Plaintext secrets (not using `${VAR}` syntax)
- Required fields missing from examples
- Fewer than 2 examples provided

**Recommendations** (best practices):
- Provide 2-3+ examples for better quality
- Enable checkpointing for parallel processing

---

## Usage Examples

### Loading and Validating

```python
from pathlib import Path
from edgar_analyzer.models.project_config import ProjectConfig

# Load from YAML file
config = ProjectConfig.from_yaml(Path("project.yaml"))

# Access configuration
print(f"Project: {config.project.name}")
print(f"Data sources: {len(config.data_sources)}")
print(f"Examples: {len(config.examples)}")

# Run comprehensive validation
results = config.validate_comprehensive()
if results['errors']:
    print("Errors:", results['errors'])
if results['warnings']:
    print("Warnings:", results['warnings'])
```

### Creating Programmatically

```python
from edgar_analyzer.models.project_config import (
    ProjectConfig,
    ProjectMetadata,
    DataSourceConfig,
    DataSourceType,
    AuthConfig,
    AuthType,
    ExampleConfig,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
)

config = ProjectConfig(
    project=ProjectMetadata(
        name="test_project",
        description="Test description",
        version="1.0.0"
    ),
    data_sources=[
        DataSourceConfig(
            type=DataSourceType.API,
            name="test_api",
            endpoint="https://api.example.com",
            auth=AuthConfig(
                type=AuthType.API_KEY,
                key="${API_KEY}",
                param_name="apikey"
            )
        )
    ],
    examples=[
        ExampleConfig(
            input={"raw": "data"},
            output={"clean": "data"}
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

# Save to YAML
config.to_yaml(Path("new_project.yaml"))
```

### Validating Existing Project

```python
from pathlib import Path
from edgar_analyzer.models.project_config import ProjectConfig

# Validate weather API project
try:
    config = ProjectConfig.from_yaml(Path("projects/weather_api/project.yaml"))
    print("✅ Valid project configuration")

    # Check comprehensive validation
    results = config.validate_comprehensive()
    print(f"Warnings: {len(results['warnings'])}")
    print(f"Recommendations: {len(results['recommendations'])}")

except ValidationError as e:
    print(f"❌ Invalid configuration: {e}")
```

---

## Best Practices

### Security
1. **Never hardcode secrets** - always use environment variables:
   ```yaml
   auth:
     key: ${OPENWEATHER_API_KEY}  # ✅ Correct
   ```

2. **Use .env.example** to document required environment variables:
   ```bash
   # .env.example
   OPENWEATHER_API_KEY=your_api_key_here
   ```

3. **Gitignore sensitive files**:
   ```
   .env
   .env.local
   data/cache/
   ```

### Performance
1. **Enable caching** for API sources to reduce calls:
   ```yaml
   cache:
     enabled: true
     ttl: 1800  # 30 minutes
   ```

2. **Configure rate limiting** to respect API limits:
   ```yaml
   rate_limit:
     requests_per_second: 0.5
     burst_size: 3
   ```

3. **Use parallel processing** for large datasets:
   ```yaml
   runtime:
     parallel: true
     max_workers: 4
   ```

### Data Quality
1. **Provide diverse examples** (5-7 recommended):
   - Cover edge cases (negative values, nulls, extremes)
   - Represent different scenarios (weather conditions, locations, etc.)
   - Include description for each example

2. **Define validation rules**:
   ```yaml
   validation:
     required_fields: [city, temperature, humidity]
     constraints:
       temperature_c: {min: -60, max: 60}
       humidity_percent: {min: 0, max: 100}
   ```

3. **Use field type definitions**:
   ```yaml
   field_types:
     temperature_c: float
     humidity_percent: int
     city: str
   ```

### Maintainability
1. **Document examples** with descriptions:
   ```yaml
   examples:
     - input: {...}
       output: {...}
       description: "Demonstrates nested field extraction and array handling"
   ```

2. **Use semantic versioning** for `project.version`:
   ```yaml
   project:
     version: 1.0.0  # Major.Minor.Patch
   ```

3. **Add tags** for categorization:
   ```yaml
   project:
     tags: [weather, api, mvp, proof-of-concept]
   ```

### Error Handling
1. **Use appropriate error strategy**:
   - `fail_fast` for development/debugging
   - `continue` for production (log errors)
   - `skip_invalid` for partial data extraction

2. **Enable checkpointing** for long-running extractions:
   ```yaml
   runtime:
     checkpoint_enabled: true
     checkpoint_interval: 10
   ```

3. **Configure retries** for reliability:
   ```yaml
   data_sources:
     - timeout: 10
       max_retries: 3
   ```

---

## Schema Evolution

### Current Version: 1.0.0

**Supported**:
- ✅ Multiple data source types (file, url, api, jina, edgar)
- ✅ Multiple authentication methods (none, api_key, bearer, basic)
- ✅ Example-based transformation learning
- ✅ Comprehensive validation with constraints
- ✅ Multiple output formats (csv, json, excel, parquet, database)
- ✅ Caching and rate limiting
- ✅ Checkpointing for resumable execution
- ✅ Parallel processing support

**Future Extensions** (planned):
- OAuth2 authentication
- Custom transformation functions
- Conditional field extraction
- Data enrichment pipelines
- Webhook notifications
- Cloud storage outputs (S3, GCS)

### Extensibility

To add new source types:
1. Add to `DataSourceType` enum in `project_config.py`
2. Implement handler in `src/edgar_analyzer/extractors/`
3. Add source-specific validation in `DataSourceConfig.validate_source_location()`
4. Update documentation

---

## Troubleshooting

### Common Validation Errors

**1. Missing required field for source type**
```
ValidationError: API sources require 'endpoint' field
```
**Solution**: Add the appropriate location field for the source type.

**2. Empty data sources list**
```
ValidationError: At least one data source must be configured
```
**Solution**: Add at least one data source to the `data_sources` list.

**3. Duplicate source names**
```
ValidationError: Data source names must be unique
```
**Solution**: Ensure each data source has a unique `name` field.

**4. Invalid project name**
```
ValidationError: Project name must be alphanumeric (underscores/hyphens allowed)
```
**Solution**: Use only letters, numbers, underscores, and hyphens in project name.

### Validation Script

Use the validation script to check project configuration:

```bash
cd projects/weather_api
python3 validate_project.py
```

This performs comprehensive checks including:
- File structure validation
- Schema compliance
- Example format and content
- Configuration quality
- Documentation completeness

---

## Related Documentation

- **Project Structure**: [docs/architecture/PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md)
- **Weather API Template**: [projects/weather_api/README.md](../projects/weather_api/README.md)
- **Quick Start Guide**: [docs/guides/QUICK_START.md](guides/QUICK_START.md)
- **Pydantic Models**: [src/edgar_analyzer/models/project_config.py](../src/edgar_analyzer/models/project_config.py)

---

## Summary

The Project YAML Schema provides a complete, type-safe configuration system for example-driven data extraction. Key strengths:

✅ **Production-Ready**: Validated with weather_api project
✅ **Strongly Typed**: Pydantic validation ensures correctness
✅ **Secure**: Environment variable substitution for secrets
✅ **Flexible**: Supports multiple sources, formats, and patterns
✅ **Self-Documenting**: Examples serve as transformation specification
✅ **Extensible**: Plugin-based architecture for new sources

**Next Steps**:
1. Review weather_api/project.yaml for complete example
2. Run validation script to verify your configuration
3. Use Pydantic models for programmatic access
4. Extend schema for custom source types as needed
