# Project YAML Quick Reference

**Schema Version**: 1.0.0 | [Full Documentation](PROJECT_YAML_SCHEMA.md)

## Minimal Configuration

```yaml
project:
  name: my_project

data_sources:
  - type: api
    name: my_api
    endpoint: https://api.example.com

output:
  formats:
    - type: json
      path: output.json
```

## Complete Template

```yaml
project:
  name: project_name          # Required: lowercase, alphanumeric, _/-
  description: string         # Optional
  version: 1.0.0              # Recommended: semantic versioning
  author: string              # Optional
  tags: [string]              # Optional: categorization

data_sources:
  - type: api                 # file|url|api|jina|edgar
    name: unique_name         # Required: unique identifier
    endpoint: string          # For API (url for URL, file_path for FILE)

    auth:                     # Optional
      type: api_key           # none|api_key|bearer|basic|oauth2
      key: ${API_KEY}         # Use ${VAR} for secrets
      param_name: apikey      # Or header_name for header auth

    parameters: {}            # Optional: query parameters
    headers: {}               # Optional: custom headers

    cache:                    # Optional
      enabled: true
      ttl: 3600               # Seconds
      cache_dir: data/cache

    rate_limit:               # Optional
      requests_per_second: 1.0
      burst_size: 5

    timeout: 30               # Seconds
    max_retries: 3

examples:                     # Recommended: 5-7 for quality
  - input: {}                 # Raw data structure
    output: {}                # Expected output
    description: string       # Optional: what this demonstrates

validation:
  required_fields: [string]   # Must exist in output

  field_types:                # Expected types
    field_name: str|int|float|bool|date|datetime|list|dict

  constraints:                # Value constraints
    field_name:
      min: number             # Min value (numeric)
      max: number             # Max value (numeric)
      min_length: int         # Min string length
      max_length: int         # Max string length
      pattern: regex          # Regex pattern
      allowed_values: [any]   # Enum validation

  allow_extra_fields: true

output:
  formats:                    # At least 1 required
    - type: csv|json|excel|parquet|database
      path: string            # File path or connection string
      include_timestamp: false
      pretty_print: false     # JSON only
      options: {}             # Format-specific

runtime:
  log_level: INFO             # DEBUG|INFO|WARNING|ERROR|CRITICAL
  parallel: false             # Enable parallel processing
  max_workers: 4              # Thread/process count
  error_strategy: continue    # fail_fast|continue|skip_invalid

  checkpoint_enabled: false   # Enable checkpointing
  checkpoint_interval: 10     # Save every N records
  checkpoint_dir: data/checkpoints
```

## Common Patterns

### API with Authentication
```yaml
data_sources:
  - type: api
    name: weather_api
    endpoint: https://api.openweathermap.org/data/2.5/weather
    auth:
      type: api_key
      key: ${OPENWEATHER_API_KEY}
      param_name: appid
    parameters:
      units: metric
    cache:
      enabled: true
      ttl: 1800
    rate_limit:
      requests_per_second: 0.5
```

### File Source
```yaml
data_sources:
  - type: file
    name: csv_data
    file_path: data/input.csv
```

### Multiple Outputs
```yaml
output:
  formats:
    - type: csv
      path: output/data.csv
    - type: json
      path: output/data.json
      pretty_print: true
    - type: excel
      path: output/data.xlsx
```

### Validation with Constraints
```yaml
validation:
  required_fields:
    - temperature
    - humidity
    - city

  field_types:
    temperature: float
    humidity: int
    city: str

  constraints:
    temperature:
      min: -60.0
      max: 60.0
    humidity:
      min: 0
      max: 100
    city:
      min_length: 2
```

## Quick Validation

### Python
```python
from pathlib import Path
from edgar_analyzer.models.project_config import ProjectConfig

# Load and validate
config = ProjectConfig.from_yaml(Path("project.yaml"))

# Comprehensive validation
results = config.validate_comprehensive()
print(f"Errors: {len(results['errors'])}")
print(f"Warnings: {len(results['warnings'])}")
```

### CLI
```bash
cd projects/your_project
python3 validate_project.py
```

## Field Types Reference

| Type | Description | Example |
|------|-------------|---------|
| `str` | String | `"London"` |
| `int` | Integer | `42` |
| `float` | Float | `15.5` |
| `decimal` | High precision | `3.14159` |
| `bool` | Boolean | `true` |
| `date` | Date only | `2024-01-15` |
| `datetime` | Date+time | `2024-01-15T10:30:00Z` |
| `list` | Array | `[1, 2, 3]` |
| `dict` | Object | `{key: value}` |

## Error Strategies

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `fail_fast` | Stop on first error | Development/debugging |
| `continue` | Log errors, continue | Production (recommended) |
| `skip_invalid` | Skip invalid records | Partial data extraction |

## Security Checklist

- ✅ Use `${ENV_VAR}` for all secrets
- ✅ Create `.env.example` with placeholder values
- ✅ Add `.env` to `.gitignore`
- ✅ Never commit actual API keys
- ✅ Use `.env.local` for local secrets

## Common Mistakes

❌ **Hardcoded secrets**
```yaml
auth:
  key: "abc123def456"  # WRONG
```
✅ **Environment variables**
```yaml
auth:
  key: ${API_KEY}  # CORRECT
```

---

❌ **Wrong location field for source type**
```yaml
data_sources:
  - type: api
    url: https://...  # WRONG - should be 'endpoint'
```
✅ **Correct location field**
```yaml
data_sources:
  - type: api
    endpoint: https://...  # CORRECT
```

---

❌ **No output formats**
```yaml
output:
  formats: []  # WRONG - at least 1 required
```
✅ **At least one output**
```yaml
output:
  formats:
    - type: json
      path: output.json  # CORRECT
```

## Links

- **Full Schema Documentation**: [PROJECT_YAML_SCHEMA.md](PROJECT_YAML_SCHEMA.md)
- **Weather API Example**: [projects/weather_api/project.yaml](../projects/weather_api/project.yaml)
- **Pydantic Models**: [src/edgar_analyzer/models/project_config.py](../src/edgar_analyzer/models/project_config.py)
