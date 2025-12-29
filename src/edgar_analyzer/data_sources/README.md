# Data Source Abstraction Layer

Generic abstraction for all data sources with built-in caching, rate limiting, and retry logic.

## Overview

The data source abstraction layer provides a common interface (`IDataSource`) for accessing data from various sources:

- **API sources**: REST APIs with authentication and headers
- **Jina.ai**: Web content extraction (clean markdown)
- **File sources**: Local files (JSON, YAML, CSV, text)
- **URL sources**: Simple HTTP/HTTPS fetching
- **EDGAR sources**: (Future) SEC EDGAR-specific wrappers

All sources include:

- ✅ Automatic caching with TTL
- ✅ Rate limiting (token bucket)
- ✅ Retry logic with exponential backoff
- ✅ Configuration validation
- ✅ Comprehensive error handling

## Quick Start

### API Source

```python
from edgar_analyzer.data_sources import APIDataSource

# Create API source with auth
api = APIDataSource(
    base_url="https://api.example.com",
    auth_token="your_token_here",
    rate_limit_per_minute=60
)

# Fetch data
data = await api.fetch(endpoint="users/123", params={"include": "profile"})
```

### Jina.ai Source (Web Content Extraction)

```python
from edgar_analyzer.data_sources import JinaDataSource
import os

# Create Jina source (auto-detects rate limit from API key)
jina = JinaDataSource(api_key=os.getenv("JINA_API_KEY"))

# Extract clean markdown from any URL
result = await jina.fetch("https://news.ycombinator.com")
print(result['title'])      # Page title
print(result['content'])    # Clean markdown content
```

### File Source

```python
from edgar_analyzer.data_sources import FileDataSource
from pathlib import Path

# JSON file
file_source = FileDataSource(Path("data/config.json"))
config = await file_source.fetch()

# CSV file (requires pandas)
csv_source = FileDataSource(Path("data/companies.csv"))
result = await csv_source.fetch()
rows = result['rows']  # List of dicts
```

### URL Source

```python
from edgar_analyzer.data_sources import URLDataSource

# Simple HTTP fetching
url_source = URLDataSource()

# Fetch JSON
data = await url_source.fetch("https://api.ipify.org?format=json")

# Fetch text
result = await url_source.fetch("https://example.com/robots.txt")
print(result['content'])
```

## Common Interface (IDataSource Protocol)

All data sources implement this protocol:

```python
class IDataSource(Protocol):
    async def fetch(self, **kwargs) -> Dict[str, Any]:
        """Fetch data from the source."""
        ...

    async def validate_config(self) -> bool:
        """Validate source configuration."""
        ...

    def get_cache_key(self, **kwargs) -> str:
        """Generate cache key for this request."""
        ...
```

## Built-in Features

### 1. Caching

All sources support automatic caching with TTL:

```python
api = APIDataSource(
    base_url="https://api.example.com",
    cache_enabled=True,
    cache_ttl_seconds=3600  # 1 hour
)

# First call - fetches from API
data1 = await api.fetch("users/123")

# Second call - returns cached result (instant)
data2 = await api.fetch("users/123")

# Check cache stats
stats = api.get_cache_stats()
print(stats['size'])  # Number of cached entries

# Clear cache
api.clear_cache()
```

### 2. Rate Limiting

Token bucket rate limiting prevents API abuse:

```python
api = APIDataSource(
    base_url="https://api.example.com",
    rate_limit_per_minute=60  # Max 60 requests per minute
)

# Makes 100 requests, automatically throttled to 60/min
for i in range(100):
    data = await api.fetch(f"users/{i}")
```

### 3. Retry Logic

Automatic retry with exponential backoff:

```python
api = APIDataSource(
    base_url="https://api.example.com",
    max_retries=3,
    retry_backoff_factor=2.0  # Wait: 1s, 2s, 4s
)

# Automatically retries on network errors
data = await api.fetch("users/123")
```

## Configuration Options

### BaseDataSource Parameters

All data sources inherit these settings:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cache_enabled` | `True` | Enable response caching |
| `cache_ttl_seconds` | `3600` | Cache time-to-live (1 hour) |
| `rate_limit_per_minute` | `60` | Max requests per minute |
| `max_retries` | `3` | Retry attempts on failure |
| `retry_backoff_factor` | `2.0` | Exponential backoff multiplier |

### APIDataSource Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | Required | API base URL |
| `headers` | `{}` | Custom HTTP headers |
| `auth_token` | `None` | Bearer token for auth |
| `timeout_seconds` | `30.0` | Request timeout |

### JinaDataSource Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | `None` | Jina.ai API key (optional) |
| `base_url` | `https://r.jina.ai` | Jina Reader API URL |
| `timeout_seconds` | `30.0` | Request timeout |

**Note**: Rate limit auto-configured:
- Without API key: 20 requests/min (free tier)
- With API key: 200 requests/min (paid tier)

### FileDataSource Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `file_path` | Required | Path to file |
| `encoding` | `utf-8` | File encoding |

**Note**: Caching disabled for file sources (files are already local).

### URLDataSource Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `timeout_seconds` | `30.0` | Request timeout |

## Use Cases

### When to Use Which Source?

**APIDataSource** - Use for:
- REST APIs with authentication
- APIs requiring custom headers
- APIs with rate limits
- APIs with query parameters

**JinaDataSource** - Use for:
- Extracting content from web pages
- Converting HTML to clean markdown
- Main content extraction (removes ads, navigation)
- LLM-friendly web content

**FileDataSource** - Use for:
- Local configuration files
- JSON/YAML data files
- CSV datasets
- Text files

**URLDataSource** - Use for:
- Public HTTP endpoints
- Simple GET requests
- No authentication needed
- Quick fetch operations

## Examples

### Example 1: Multi-Source Data Fetching

```python
import asyncio
from edgar_analyzer.data_sources import APIDataSource, JinaDataSource

async def fetch_company_data(ticker: str):
    # Fetch from API
    api = APIDataSource(base_url="https://api.example.com")
    api_data = await api.fetch(f"companies/{ticker}")

    # Fetch from company website
    jina = JinaDataSource()
    web_content = await jina.fetch(api_data['website'])

    return {
        'api_data': api_data,
        'web_content': web_content['content']
    }

data = asyncio.run(fetch_company_data("AAPL"))
```

### Example 2: Batch Processing with Rate Limiting

```python
async def process_companies(tickers: list[str]):
    api = APIDataSource(
        base_url="https://api.example.com",
        rate_limit_per_minute=60  # Throttled automatically
    )

    results = []
    for ticker in tickers:
        data = await api.fetch(f"companies/{ticker}")
        results.append(data)

    return results

# Processes 100 companies, automatically throttled to 60/min
tickers = [f"TICKER{i}" for i in range(100)]
results = asyncio.run(process_companies(tickers))
```

### Example 3: Configuration from Environment

```python
import os
from edgar_analyzer.data_sources import APIDataSource, JinaDataSource

# Load from environment variables
openrouter = APIDataSource(
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    auth_token=os.getenv("OPENROUTER_API_KEY")
)

jina = JinaDataSource(
    api_key=os.getenv("JINA_API_KEY")
)
```

## Testing

Comprehensive test suite included:

```bash
# Run all data source tests
pytest tests/unit/test_data_sources.py -v

# Test specific source
pytest tests/unit/test_data_sources.py::TestAPIDataSource -v

# Test with coverage
pytest tests/unit/test_data_sources.py --cov=src/edgar_analyzer/data_sources
```

## Performance Characteristics

### Time Complexity

- **Cache hit**: O(1) - instant
- **Cache miss**: O(n) where n = response size
- **Rate limiting**: O(1) - token bucket check

### Space Complexity

- **Cache**: O(m) where m = number of cached entries
- **Rate limiter**: O(k) where k = requests in last minute

### Optimization Tips

1. **Enable caching** for repeated requests
2. **Set appropriate TTL** based on data freshness needs
3. **Use rate limiting** to respect API limits
4. **Batch requests** when possible
5. **Clear cache** periodically to free memory

## Architecture

### Design Decisions

**Why Protocol over Abstract Base Class?**
- Structural typing allows duck typing
- No inheritance required
- More flexible for testing

**Why In-Memory Cache?**
- Simple and fast (no network overhead)
- Good for single-process applications
- Trade-off: Not shared across processes
- Future: Add Redis adapter for distributed cache

**Why Token Bucket Rate Limiting?**
- Allows bursts within limits
- Fair and predictable
- Industry standard algorithm

**Why Exponential Backoff?**
- Reduces server load during failures
- Gives transient errors time to resolve
- Configurable backoff factor

### Extension Points

Want to add a new data source? Implement the protocol:

```python
from edgar_analyzer.data_sources import BaseDataSource

class MyCustomSource(BaseDataSource):
    async def fetch(self, **kwargs) -> Dict[str, Any]:
        # Your fetch logic here
        pass

    async def validate_config(self) -> bool:
        # Validate configuration
        pass

    def get_cache_key(self, **kwargs) -> str:
        # Generate cache key
        pass
```

## Future Enhancements

Planned features:

- [ ] Redis cache adapter (distributed caching)
- [ ] GraphQL API source
- [ ] S3/blob storage source
- [ ] Database source (SQL, NoSQL)
- [ ] Streaming support for large responses
- [ ] Circuit breaker pattern
- [ ] Metrics and monitoring
- [ ] Request batching

## Contributing

When adding new data sources:

1. Implement `IDataSource` protocol
2. Extend `BaseDataSource` for common features
3. Add comprehensive tests
4. Document usage in README
5. Add example to `examples/data_sources_demo.py`

## Related Documentation

- [Rate Limiter Implementation](../utils/rate_limiter.py)
- [Base Data Source](base.py)
- [Usage Examples](../../../examples/data_sources_demo.py)
- [Test Suite](../../../tests/unit/test_data_sources.py)

## License

MIT License - See LICENSE file for details
