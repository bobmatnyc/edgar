# SEC EDGAR API - Standalone Data Source

## Overview

The `edgar_api` module provides a simple, standalone function for fetching SEC filings without requiring dependency injection setup. This is ideal for recipe scripts and lightweight automation tasks.

## Key Features

- **No DI Required**: Simple function-based API
- **Rate Limiting**: Automatic 8 req/sec (SEC allows 10/sec)
- **Error Handling**: Graceful failure with error messages in results
- **Async/Await**: Concurrent fetching for multiple companies
- **Retry Logic**: Exponential backoff for transient failures
- **User-Agent Compliance**: SEC-required User-Agent with email

## Installation

Already included in `edgar-analyzer` package. No additional dependencies needed.

## Usage

### Basic Example

```python
import asyncio
from edgar_analyzer.data_sources import fetch_company_filings

async def main():
    companies = [
        {"cik": "0000320193", "name": "Apple Inc.", "ticker": "AAPL"},
        {"cik": "0001018724", "name": "Amazon.com Inc.", "ticker": "AMZN"},
    ]

    filings = await fetch_company_filings(
        companies=companies,
        filing_type="10-K",
        year=2023,
        email="your-email@example.com"  # Required by SEC
    )

    for filing in filings:
        if not filing.get("error"):
            print(f"{filing['company']}: {filing['filing_date']}")

asyncio.run(main())
```

### Supported Filing Types

- **10-K**: Annual reports
- **DEF 14A**: Proxy statements (executive compensation)
- Any other SEC filing type (8-K, 10-Q, etc.)

### Function Signature

```python
async def fetch_company_filings(
    companies: list[dict[str, Any]],
    filing_type: str,
    year: int = 2023,
    email: str = "contact@example.com",
) -> list[dict[str, Any]]
```

**Parameters:**
- `companies`: List of company dicts with 'cik', 'name', 'ticker'
- `filing_type`: Filing type to fetch (e.g., "10-K", "DEF 14A")
- `year`: Target fiscal year
- `email`: Contact email for SEC User-Agent header (required by SEC)

**Returns:**
List of filing dicts with:
- `cik`: Company CIK (10 digits, zero-padded)
- `company`: Company name
- `filing_type`: Filing type
- `filing_date`: Filing date (YYYY-MM-DD) or None if not found
- `accession_number`: SEC accession number or None
- `html`: Filing HTML content or None
- `error`: Error message if fetch failed (optional field)

### Error Handling

Errors are captured in the result dict, not raised as exceptions:

```python
filings = await fetch_company_filings(companies, "10-K", 2023)

for filing in filings:
    if filing.get("error"):
        print(f"Error for {filing['company']}: {filing['error']}")
    else:
        print(f"Success for {filing['company']}")
```

### Common Error Types

- **CIK not found**: Invalid CIK number
- **No filing found**: No filing of specified type for target year
- **HTTP errors**: Network issues, SEC API downtime
- **Timeout**: Request exceeded 30 second timeout

## Rate Limiting

The module automatically enforces SEC's rate limits:

- **Limit**: 8 requests/second (SEC allows 10/sec, we use 8 for safety)
- **Implementation**: `SecRateLimiter` class with async wait
- **Per-request delay**: 0.125 seconds (1/8 second)

## SEC API Endpoints

### Submissions Metadata
```
https://data.sec.gov/submissions/CIK{cik:010d}.json
```

Returns company filing history with:
- Filing forms (10-K, DEF 14A, etc.)
- Filing dates
- Accession numbers

### Filing Content
```
https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}
```

Returns full filing content (HTML/text).

## Comparison to EdgarApiService

| Feature | `fetch_company_filings` | `EdgarApiService` |
|---------|-------------------------|-------------------|
| DI Required | No | Yes |
| Caching | No | Yes (optional) |
| Use Case | Recipes, scripts | Production apps |
| Complexity | Low | High |
| Rate Limiting | Built-in | Built-in |
| Error Handling | Results-based | Exception-based |

## When to Use

**Use `fetch_company_filings` for:**
- Recipe scripts
- One-off data extraction
- Lightweight automation
- Prototyping

**Use `EdgarApiService` for:**
- Production applications
- Long-running services
- When caching is needed
- Complex orchestration

## Performance

- **Concurrent**: Fetches multiple companies in parallel
- **Rate Limited**: Automatic throttling to 8 req/sec
- **Retry Logic**: 3 attempts with exponential backoff
- **Timeout**: 30 seconds per request

### Example Performance

Fetching 10 companies (10-K filings):
- **Time**: ~15-20 seconds (rate limiting + network latency)
- **Requests**: 2 per company (metadata + content) = 20 total
- **Rate**: 8 req/sec = 20 requests / 8 = 2.5 seconds minimum

## Examples

See `examples/fetch_filings_example.py` for complete examples:
- Fetching 10-K annual reports
- Fetching DEF 14A proxy statements
- Error handling patterns

## Logging

Uses `structlog` for structured logging:

```python
2025-12-31 08:10:26 [info] Fetching filing cik=0000320193 company='Apple Inc.'
2025-12-31 08:10:26 [info] Filing fetch complete failed=0 success=2 total=2
```

Log levels:
- **INFO**: High-level operations (fetching, completion)
- **DEBUG**: Detailed request/response info
- **WARNING**: Missing filings, retries
- **ERROR**: Fetch failures, exceptions

## SEC User-Agent Requirements

The SEC requires a User-Agent header with contact information:

> "To ensure equitable access, please provide your contact information in the User-Agent header. If you do not provide this, the SEC may block your access."

This module automatically includes:
```
User-Agent: EdgarAnalyzer/0.2.2 (your-email@example.com)
```

Always provide a valid email address in the `email` parameter.

## License

MIT License - Part of the edgar-analyzer project.
