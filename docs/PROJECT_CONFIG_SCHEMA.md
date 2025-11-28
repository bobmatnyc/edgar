# Project Configuration Schema Reference

**Version**: 1.0.0
**Last Updated**: 2024-11-28

This document provides comprehensive reference for the `project.yaml` configuration schema used by the general-purpose extract & transform platform.

---

## Table of Contents

- [Overview](#overview)
- [Schema Structure](#schema-structure)
- [Project Metadata](#project-metadata)
- [Data Sources](#data-sources)
- [Example-Based Learning](#example-based-learning)
- [Validation Rules](#validation-rules)
- [Output Configuration](#output-configuration)
- [Runtime Configuration](#runtime-configuration)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

The `project.yaml` file defines:
- **What** data to extract (sources)
- **How** to transform it (examples)
- **Where** to output results (formats)
- **When** to validate and handle errors (runtime)

### Design Principles

1. **Declarative**: Describe outcomes, not implementation
2. **Self-Contained**: Single file contains all configuration
3. **Portable**: No hardcoded credentials or absolute paths
4. **Testable**: Validation ensures correctness before execution
5. **Extensible**: Plugin-based architecture for new source types

### Why YAML?

- **Human-Readable**: Easy to write and understand
- **Comments**: Document complex configurations inline
- **Widely Supported**: Standard format for config files
- **Type Safe**: Validated by Pydantic models

---

## Schema Structure

```yaml
project:           # REQUIRED: Project metadata
  name: "..."
  description: "..."
  version: "..."

data_sources:      # REQUIRED: At least one source
  - type: api
    name: "..."
    endpoint: "..."

examples:          # RECOMMENDED: 2-3 examples minimum
  - input: {...}
    output: {...}

validation:        # OPTIONAL: Quality checks
  required_fields: [...]
  field_types: {...}

output:            # REQUIRED: At least one format
  formats:
    - type: csv
      path: "..."

runtime:           # OPTIONAL: Execution settings
  log_level: INFO
  parallel: false
```

---

## Project Metadata

### Schema

```yaml
project:
  name: "project_name"              # REQUIRED: Lowercase, underscores allowed
  description: "Brief description"  # OPTIONAL
  version: "1.0.0"                  # OPTIONAL: Default "1.0.0"
  author: "Author Name"             # OPTIONAL
  created: 2024-01-15T10:00:00Z    # AUTO-GENERATED
  updated: 2024-01-15T10:00:00Z    # AUTO-GENERATED
  tags:                             # OPTIONAL: For categorization
    - category1
    - category2
```

### Field Reference

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `name` | string | Yes | Project identifier | Lowercase, alphanumeric + `_-` |
| `description` | string | No | Human-readable description | - |
| `version` | string | No | Version number | Semver recommended |
| `author` | string | No | Author or organization | - |
| `tags` | list[string] | No | Categorization tags | - |

### Examples

```yaml
# Minimal metadata
project:
  name: "weather_extractor"

# Full metadata
project:
  name: "weather_data_pipeline"
  description: "Extract and transform weather data from OpenWeatherMap API"
  version: "2.1.0"
  author: "Data Engineering Team"
  tags:
    - weather
    - api
    - production
```

### Validation Rules

- **Name Format**: Must be alphanumeric with underscores/hyphens only
- **Name Uniqueness**: Not enforced at config level (filesystem-based)
- **Auto-Lowercasing**: Names converted to lowercase automatically

---

## Data Sources

### Supported Source Types

| Type | Use Case | Example |
|------|----------|---------|
| `api` | REST APIs | OpenWeatherMap, GitHub API |
| `url` | Web scraping | Product pages, news articles |
| `file` | Local files | CSV, JSON, XML, Excel |
| `jina` | Web to Markdown | Jina.ai reader service |
| `edgar` | SEC filings | EDGAR API (domain-specific) |

### API Source

```yaml
- type: api
  name: "api_source_name"           # REQUIRED: Unique identifier
  endpoint: "https://api.example.com/v1/data"  # REQUIRED

  # Authentication
  auth:
    type: api_key                   # none | api_key | bearer | basic | oauth2
    key: "${API_KEY}"               # Use env vars for secrets
    param_name: "apikey"            # OR header_name: "X-API-Key"

  # Request parameters
  parameters:
    format: "json"
    limit: 100
    category: "${category}"         # Runtime templating

  # Custom headers
  headers:
    User-Agent: "MyBot/1.0"
    Accept: "application/json"

  # Performance
  cache:
    enabled: true
    ttl: 3600                       # Seconds
    max_size_mb: 100
    cache_dir: "data/cache"

  rate_limit:
    requests_per_second: 2.0
    burst_size: 10

  # Reliability
  timeout: 30                       # Seconds
  max_retries: 3
```

### URL Source (Web Scraping)

```yaml
- type: url
  name: "web_scraper"
  url: "https://example.com/page"

  headers:
    User-Agent: "Mozilla/5.0 (compatible; MyBot/1.0)"

  cache:
    enabled: true
    ttl: 86400  # 24 hours

  options:
    extract_method: "beautifulsoup"  # beautifulsoup | selenium | playwright
    wait_for_element: "#data-table"
    javascript_enabled: false
```

### File Source

```yaml
- type: file
  name: "csv_import"
  file_path: "data/input/source.csv"

  options:
    file_format: "csv"              # csv | json | xml | excel | parquet
    encoding: "utf-8"
    delimiter: ","
    has_header: true
    sheet_name: "Sheet1"            # For Excel files
```

### Jina.ai Source

```yaml
- type: jina
  name: "jina_reader"
  url: "https://example.com/article"

  auth:
    type: bearer
    key: "${JINA_API_KEY}"
    header_name: "Authorization"

  options:
    format: "markdown"              # markdown | html | text
    include_images: true
    include_links: true
```

### Authentication Types

#### No Authentication

```yaml
auth:
  type: none
```

#### API Key (Query Parameter)

```yaml
auth:
  type: api_key
  key: "${API_KEY}"
  param_name: "apikey"
```

#### API Key (Header)

```yaml
auth:
  type: api_key
  key: "${API_KEY}"
  header_name: "X-API-Key"
```

#### Bearer Token

```yaml
auth:
  type: bearer
  key: "${TOKEN}"
  header_name: "Authorization"  # Adds "Bearer ${TOKEN}"
```

#### Basic Authentication

```yaml
auth:
  type: basic
  username: "user"
  password: "${PASSWORD}"
```

---

## Example-Based Learning

### Why Examples?

**Traditional Approach** (Rule-Based):
```yaml
transformations:
  - field: "temperature"
    source: "main.temp"
    type: "float"
  - field: "conditions"
    source: "weather[0].description"
    type: "string"
```

**Example-Based Approach**:
```yaml
examples:
  - input:
      main:
        temp: 15.5
      weather:
        - description: "light rain"
    output:
      temperature: 15.5
      conditions: "light rain"
```

**Advantages**:
- ✅ Intuitive for non-programmers
- ✅ Handles complex nested structures
- ✅ Self-documenting
- ✅ Leverages LLM pattern recognition
- ✅ Flexible for edge cases

### Schema

```yaml
examples:
  - description: "Optional description of this example"  # OPTIONAL
    input:                         # REQUIRED: Raw data structure
      field1: "value1"
      nested:
        field2: "value2"
    output:                        # REQUIRED: Desired output structure
      clean_field1: "value1"
      clean_field2: "value2"
```

### Best Practices

**Quantity**: Provide 2-3 examples minimum
- 1 example: Overfitting risk
- 2-3 examples: Pattern recognition
- 5+ examples: Diminishing returns

**Diversity**: Cover different patterns
- ✅ Typical case
- ✅ Missing optional fields
- ✅ Different data values
- ✅ Edge cases (empty, null, extreme)

**Quality**: Examples should be real
- ❌ Synthetic/fake data
- ✅ Actual API responses
- ✅ Representative samples

### Complete Example

```yaml
examples:
  # Example 1: Typical case
  - description: "Standard successful response"
    input:
      id: 12345
      user:
        name: "John Doe"
        email: "john@example.com"
      data:
        value: 42.5
        timestamp: "2024-01-15T10:30:00Z"
    output:
      record_id: 12345
      user_name: "John Doe"
      user_email: "john@example.com"
      measurement: 42.5
      recorded_at: "2024-01-15T10:30:00Z"

  # Example 2: Missing optional fields
  - description: "Response with missing email"
    input:
      id: 67890
      user:
        name: "Jane Smith"
        # email missing
      data:
        value: 38.2
        timestamp: "2024-01-15T11:00:00Z"
    output:
      record_id: 67890
      user_name: "Jane Smith"
      user_email: null
      measurement: 38.2
      recorded_at: "2024-01-15T11:00:00Z"
```

---

## Validation Rules

### Schema

```yaml
validation:
  required_fields:                 # OPTIONAL: List of required output fields
    - field1
    - field2

  field_types:                     # OPTIONAL: Type definitions
    field1: str
    field2: int
    field3: float

  constraints:                     # OPTIONAL: Field-specific constraints
    field2:
      min: 0
      max: 100
    field1:
      pattern: "^[A-Z]{2,3}$"
      min_length: 2
      max_length: 100

  allow_extra_fields: true         # OPTIONAL: Default true
```

### Field Types

| Type | Description | Example Values |
|------|-------------|----------------|
| `str` | String | `"text"`, `"2024-01-15"` |
| `int` | Integer | `42`, `-10`, `0` |
| `float` | Floating point | `3.14`, `-0.5`, `1.0` |
| `decimal` | Precise decimal | Financial data |
| `bool` | Boolean | `true`, `false` |
| `date` | Date | `"2024-01-15"` |
| `datetime` | Timestamp | `"2024-01-15T10:30:00Z"` |
| `list` | Array | `[1, 2, 3]` |
| `dict` | Object | `{"key": "value"}` |

### Constraints

#### Numeric Constraints

```yaml
constraints:
  temperature_c:
    min: -50.0
    max: 60.0
  age:
    min: 0
    max: 150
```

#### String Constraints

```yaml
constraints:
  name:
    min_length: 1
    max_length: 100
    pattern: "^[A-Za-z ]+$"
  country_code:
    allowed_values: ["US", "UK", "CA", "AU"]
```

#### Complete Example

```yaml
validation:
  required_fields:
    - city
    - temperature_c
    - conditions

  field_types:
    city: str
    temperature_c: float
    humidity_percent: int
    conditions: str

  constraints:
    temperature_c:
      min: -50.0
      max: 60.0
    humidity_percent:
      min: 0
      max: 100
    city:
      min_length: 1
      max_length: 100

  allow_extra_fields: true
```

---

## Output Configuration

### Supported Formats

| Format | Extension | Use Case | Libraries |
|--------|-----------|----------|-----------|
| `csv` | `.csv` | Spreadsheet import, data analysis | pandas |
| `json` | `.json` | API responses, web apps | json |
| `excel` | `.xlsx` | Business reports, presentations | openpyxl |
| `parquet` | `.parquet` | Big data, data warehouses | pyarrow |

### Schema

```yaml
output:
  formats:
    - type: csv                    # REQUIRED: Output format
      path: "output/data.csv"      # REQUIRED: File path
      include_timestamp: false     # OPTIONAL: Add timestamp to filename
      options:                     # OPTIONAL: Format-specific options
        delimiter: ","
        quoting: "minimal"
```

### CSV Output

```yaml
- type: csv
  path: "output/weather_data.csv"
  include_timestamp: true          # → weather_data_2024-01-15_10-30-00.csv
  options:
    delimiter: ","                 # Field separator
    quoting: "minimal"             # minimal | all | non-numeric | none
    index: false                   # Include pandas index
    encoding: "utf-8"              # Character encoding
    line_terminator: "\n"          # Line ending
```

### JSON Output

```yaml
- type: json
  path: "output/weather_data.json"
  pretty_print: true               # Human-readable formatting
  options:
    indent: 2                      # Indentation spaces
    ensure_ascii: false            # Allow unicode characters
    sort_keys: false               # Alphabetize keys
```

### Excel Output

```yaml
- type: excel
  path: "output/weather_data.xlsx"
  options:
    sheet_name: "Weather Data"    # Sheet name
    freeze_panes: "A2"             # Freeze header row
    auto_filter: true              # Enable filtering
    column_widths:                 # Auto-size or fixed widths
      auto: true
```

### Parquet Output

```yaml
- type: parquet
  path: "output/weather_data.parquet"
  options:
    compression: "snappy"          # snappy | gzip | brotli | none
    index: false                   # Include pandas index
```

### Multiple Outputs

```yaml
output:
  formats:
    - type: csv
      path: "output/data.csv"
    - type: json
      path: "output/data.json"
      pretty_print: true
    - type: excel
      path: "reports/data.xlsx"
```

---

## Runtime Configuration

### Schema

```yaml
runtime:
  log_level: INFO                  # DEBUG | INFO | WARNING | ERROR | CRITICAL
  parallel: false                  # Enable parallel processing
  max_workers: 4                   # Worker threads/processes
  error_strategy: continue         # continue | fail_fast | skip_invalid
  checkpoint_enabled: false        # Enable resumable extraction
  checkpoint_interval: 10          # Save every N records
  checkpoint_dir: "data/checkpoints"
```

### Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `log_level` | string | `INFO` | Logging verbosity |
| `parallel` | bool | `false` | Parallel processing |
| `max_workers` | int | `4` | Thread/process count |
| `error_strategy` | enum | `continue` | Error handling |
| `checkpoint_enabled` | bool | `false` | Resumable extraction |
| `checkpoint_interval` | int | `10` | Checkpoint frequency |

### Error Strategies

**`fail_fast`**: Stop on first error
- **Use When**: Data quality critical
- **Trade-off**: Fast failure detection, no partial results

**`continue`**: Log errors and continue
- **Use When**: Partial results acceptable
- **Trade-off**: Complete processing, may miss critical errors

**`skip_invalid`**: Skip invalid records silently
- **Use When**: Large datasets with known issues
- **Trade-off**: Maximum throughput, silent failures

### Examples

```yaml
# Development: Verbose logging, fail fast
runtime:
  log_level: DEBUG
  error_strategy: fail_fast

# Production: Parallel processing with checkpoints
runtime:
  log_level: INFO
  parallel: true
  max_workers: 8
  error_strategy: continue
  checkpoint_enabled: true
  checkpoint_interval: 100

# Large dataset: Maximum performance
runtime:
  log_level: WARNING
  parallel: true
  max_workers: 16
  error_strategy: skip_invalid
```

---

## Complete Examples

### Weather API (Simple)

```yaml
project:
  name: "weather_extractor"
  description: "Extract current weather data"
  version: "1.0.0"

data_sources:
  - type: api
    name: "openweathermap"
    endpoint: "https://api.openweathermap.org/data/2.5/weather"
    auth:
      type: api_key
      key: "${OPENWEATHER_API_KEY}"
      param_name: "appid"
    parameters:
      q: "${city}"
      units: "metric"
    cache:
      enabled: true
      ttl: 3600

examples:
  - input:
      main:
        temp: 15.5
        humidity: 72
      weather:
        - description: "light rain"
    output:
      temperature_c: 15.5
      humidity_percent: 72
      conditions: "light rain"

validation:
  required_fields: ["temperature_c", "conditions"]
  field_types:
    temperature_c: float
    humidity_percent: int

output:
  formats:
    - type: csv
      path: "output/weather.csv"
      include_timestamp: true

runtime:
  log_level: INFO
  error_strategy: continue
```

### Web Scraping (Advanced)

```yaml
project:
  name: "product_scraper"
  description: "Scrape product data from e-commerce sites"
  version: "2.0.0"
  tags: [scraping, products, e-commerce]

data_sources:
  - type: url
    name: "product_page"
    url: "${product_url}"
    headers:
      User-Agent: "Mozilla/5.0 (compatible; ProductBot/1.0)"
    cache:
      enabled: true
      ttl: 86400
    options:
      extract_method: "beautifulsoup"
      wait_for_element: ".product-details"

examples:
  - input:
      html: |
        <div class="product">
          <h1>Widget Pro</h1>
          <span class="price">$29.99</span>
          <div class="rating">4.5 stars</div>
        </div>
    output:
      product_name: "Widget Pro"
      price: 29.99
      currency: "USD"
      rating: 4.5

validation:
  required_fields: ["product_name", "price"]
  constraints:
    price:
      min: 0.01
    rating:
      min: 0.0
      max: 5.0

output:
  formats:
    - type: json
      path: "output/products.json"
      pretty_print: true
    - type: excel
      path: "reports/products.xlsx"
      options:
        sheet_name: "Products"
        freeze_panes: "A2"

runtime:
  log_level: WARNING
  parallel: true
  max_workers: 4
  error_strategy: skip_invalid
  checkpoint_enabled: true
```

---

## Best Practices

### Security

**✅ DO**: Use environment variables for secrets
```yaml
auth:
  key: "${API_KEY}"
```

**❌ DON'T**: Hardcode credentials
```yaml
auth:
  key: "abc123xyz789"  # NEVER DO THIS
```

### Examples

**✅ DO**: Provide diverse, real examples
```yaml
examples:
  - # Typical case
  - # Missing fields
  - # Edge case
```

**❌ DON'T**: Use single synthetic example
```yaml
examples:
  - input: {test: "data"}
    output: {test: "data"}
```

### Performance

**✅ DO**: Enable caching for API sources
```yaml
cache:
  enabled: true
  ttl: 3600
```

**❌ DON'T**: Disable caching without reason
```yaml
cache:
  enabled: false  # Why?
```

### Validation

**✅ DO**: Define required fields and types
```yaml
validation:
  required_fields: ["id", "name"]
  field_types:
    id: int
    name: str
```

**❌ DON'T**: Skip validation entirely
```yaml
validation: {}  # Quality issues
```

---

## Troubleshooting

### Common Issues

#### "Authentication failed"

**Symptom**: 401/403 errors from API
**Cause**: Missing or invalid API key
**Solution**:
1. Check `.env.local` has variable: `API_KEY=your_key_here`
2. Verify `${API_KEY}` syntax in `project.yaml`
3. Test API key manually with `curl`

#### "No examples provided warning"

**Symptom**: Warning during validation
**Cause**: Empty or missing examples section
**Solution**: Add 2-3 quality examples covering typical and edge cases

#### "Rate limit exceeded"

**Symptom**: 429 errors from API
**Cause**: Too many requests
**Solution**: Reduce `requests_per_second` in rate_limit config

#### "Validation error: field required"

**Symptom**: Output validation fails
**Cause**: Examples don't include all required_fields
**Solution**: Ensure examples demonstrate all required output fields

#### "Output file not created"

**Symptom**: No output files after extraction
**Cause**: Directory doesn't exist or permissions issue
**Solution**:
1. Check output directory exists
2. Verify write permissions
3. Check logs for errors

### Validation Checklist

Before running extraction:

- [ ] Project name is lowercase, alphanumeric
- [ ] At least one data source configured
- [ ] Source-specific required fields present (endpoint/url/file_path)
- [ ] Secrets use `${ENV_VAR}` syntax
- [ ] At least 2-3 quality examples provided
- [ ] Required fields match example outputs
- [ ] At least one output format configured
- [ ] Output directories exist

### Debug Commands

```bash
# Validate config without running extraction
python -m edgar_analyzer validate-config project.yaml

# Run with debug logging
LOG_LEVEL=DEBUG python -m edgar_analyzer extract-project project.yaml

# Check environment variables loaded
python -c "import os; print(os.getenv('API_KEY'))"

# Test single example
python -m edgar_analyzer test-example project.yaml --example-index 0
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-11-28 | Initial schema release |

---

## See Also

- [Weather API Example](../templates/weather_api_project.yaml)
- [Template File](../templates/project.yaml.template)
- [Pydantic Models](../src/edgar_analyzer/models/project_config.py)
- [Unit Tests](../tests/unit/config/test_project_schema.py)
