# Data Sources Quick Reference

One-page reference for using the data source abstraction layer.

## Import

```python
from edgar_analyzer.data_sources import (
    APIDataSource,
    JinaDataSource,
    FileDataSource,
    URLDataSource
)
```

## API Source (REST APIs)

```python
# Basic API
api = APIDataSource(base_url="https://api.example.com")
data = await api.fetch(endpoint="users/123")

# With authentication
api = APIDataSource(
    base_url="https://api.example.com",
    auth_token=os.getenv("API_KEY")
)

# With custom headers
api = APIDataSource(
    base_url="https://api.example.com",
    headers={"User-Agent": "MyApp/1.0"}
)

# With rate limiting
api = APIDataSource(
    base_url="https://api.example.com",
    rate_limit_per_minute=60  # SEC EDGAR limit
)
```

## Jina Source (Web Content)

```python
# Load API key from environment
jina = JinaDataSource(api_key=os.getenv("JINA_API_KEY"))

# Extract clean markdown
result = await jina.fetch("https://example.com")
print(result['title'])      # Page title
print(result['content'])    # Clean markdown
```

## File Source

```python
# JSON file
file_source = FileDataSource(Path("data/config.json"))
config = await file_source.fetch()

# CSV file
csv_source = FileDataSource(Path("data/companies.csv"))
result = await csv_source.fetch()
rows = result['rows']  # List of dicts

# Text file
text_source = FileDataSource(Path("README.md"))
result = await text_source.fetch()
content = result['content']
```

## URL Source

```python
# Simple HTTP fetch
url_source = URLDataSource()

# JSON endpoint
data = await url_source.fetch("https://api.ipify.org?format=json")

# Text content
result = await url_source.fetch("https://example.com/robots.txt")
print(result['content'])
```

## Common Settings

All sources support these settings:

```python
source = SomeDataSource(
    cache_enabled=True,           # Enable caching
    cache_ttl_seconds=3600,       # 1 hour cache
    rate_limit_per_minute=60,     # 60 requests/min
    max_retries=3,                # Retry 3 times
    retry_backoff_factor=2.0      # 1s, 2s, 4s
)
```

## Cache Management

```python
# Get cache stats
stats = source.get_cache_stats()
print(f"Cached: {stats['size']} entries")

# Clear cache
source.clear_cache()
```

## Configuration Validation

```python
is_valid = await source.validate_config()
if not is_valid:
    print("Configuration invalid!")
```

## Error Handling

```python
try:
    data = await source.fetch(...)
except httpx.HTTPError as e:
    print(f"HTTP error: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Rate Limits by Source

| Source | Default Rate Limit | Notes |
|--------|-------------------|-------|
| API | 60/min | Configurable |
| Jina (free) | 20/min | Auto-detected |
| Jina (paid) | 200/min | With API key |
| File | Unlimited | Local I/O |
| URL | 60/min | Configurable |

## Common Patterns

### Multi-Source Fetching

```python
async def fetch_all_data(company_id: str):
    api = APIDataSource(base_url="https://api.example.com")
    jina = JinaDataSource()

    api_data = await api.fetch(f"companies/{company_id}")
    web_data = await jina.fetch(api_data['website'])

    return {'api': api_data, 'web': web_data}
```

### Batch Processing

```python
async def process_batch(ids: list[str]):
    api = APIDataSource(
        base_url="https://api.example.com",
        rate_limit_per_minute=60
    )

    results = []
    for id in ids:
        data = await api.fetch(f"items/{id}")
        results.append(data)
    return results
```

### Configuration from .env.local

```python
import os

api = APIDataSource(
    base_url=os.getenv("API_BASE_URL"),
    auth_token=os.getenv("API_KEY")
)

jina = JinaDataSource(
    api_key=os.getenv("JINA_API_KEY")
)
```

## Testing

```bash
# Run all data source tests
pytest tests/unit/test_data_sources.py -v

# Run specific source tests
pytest tests/unit/test_data_sources.py::TestAPIDataSource -v
```

## Demo Script

```bash
# Run comprehensive demo
python examples/data_sources_demo.py
```

## Full Documentation

See: `src/edgar_analyzer/data_sources/README.md`
