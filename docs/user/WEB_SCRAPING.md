# Web Scraping Guide

**Platform**: `extract_transform_platform` (Generic Extract & Transform Platform)
**Data Source**: JinaDataSource + URLDataSource
**Status**: Batch 1 Complete (100% code reuse from EDGAR)

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [JinaDataSource - JS-Heavy Sites](#jinadatasource---js-heavy-sites)
- [URLDataSource - Simple GET Requests](#urldatasource---simple-get-requests)
- [Choosing the Right Tool](#choosing-the-right-tool)
- [Advanced Examples](#advanced-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The platform provides **two web scraping tools** optimized for different use cases:

| Tool | Use Case | JavaScript Support | Authentication | Rate Limiting |
|------|----------|-------------------|----------------|---------------|
| **JinaDataSource** | JS-heavy sites (SPAs, React, Vue, Angular) | ✅ Yes (executes JS) | Optional API key | Free + Paid tiers |
| **URLDataSource** | Simple static sites, public APIs | ❌ No | ❌ No | None (use APIDataSource) |

**Key Capabilities**:
- 🌐 **JavaScript execution** (Jina.ai renders dynamic content)
- 📄 **Markdown conversion** (clean text extraction)
- 🔓 **Free tier available** (20-200 requests/hour)
- 🚀 **Production-ready** (error handling, retries)

---

## Quick Start

### 1. Install Dependencies

```bash
# Platform should already have requests installed
pip install requests

# Verify installation
python -c "from extract_transform_platform.data_sources.web import JinaDataSource; print('OK')"
```

### 2. Get Jina.ai API Key (Optional but Recommended)

```bash
# 1. Visit https://jina.ai and sign up for free
# 2. Get your API key from the dashboard
# 3. Set environment variable
export JINA_API_KEY="jina-xxxxxxxxxxxx"

# Or add to .env file
echo "JINA_API_KEY=jina-xxxxxxxxxxxx" >> .env
```

**Rate Limits**:
- **No API key**: 20 requests/hour
- **Free tier (with key)**: 200 requests/hour
- **Paid tier**: Higher limits (see Jina.ai pricing)

### 3. Your First Scrape

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os

# Scrape a JavaScript-heavy site
jina_source = JinaDataSource(
    url="https://example-react-app.com/products",
    api_key=os.getenv("JINA_API_KEY")
)

# Read content (JavaScript executed, rendered as markdown)
result = jina_source.read()

# Access scraped data
print(f"Title: {result['title']}")
print(f"Content: {result['content'][:200]}...")
print(f"Description: {result['description']}")
```

---

## JinaDataSource - JS-Heavy Sites

**Use Case**: Scrape single-page applications (SPAs) and dynamic content loaded via JavaScript.

### Basic Usage

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os

# Create Jina data source
jina_source = JinaDataSource(
    url="https://example.com/dynamic-page",
    api_key=os.getenv("JINA_API_KEY")  # Optional
)

# Scrape content
data = jina_source.read()

# Result structure:
# {
#     'content': '# Page Title\n\nMain content in markdown...',
#     'title': 'Page Title',
#     'description': 'Page description meta tag',
#     'url': 'https://example.com/dynamic-page',
#     'publishedTime': '2024-01-15T10:30:00Z'  # If available
# }
```

### Example: Scrape Product Catalog (React SPA)

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os
import re

# Scrape e-commerce product page
jina_source = JinaDataSource(
    url="https://example-store.com/products",
    api_key=os.getenv("JINA_API_KEY")
)

result = jina_source.read()

# Parse markdown content for product information
content = result['content']

# Extract product names (example pattern)
product_pattern = r"## ([^\n]+)\nPrice: \$([0-9.]+)"
products = re.findall(product_pattern, content)

# Process products
for name, price in products:
    print(f"Product: {name}, Price: ${price}")

# Result:
# Product: Widget A, Price: $19.99
# Product: Widget B, Price: $29.99
```

### Example: Scrape News Article (AJAX Content)

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os

# Scrape news article with dynamic comments
jina_source = JinaDataSource(
    url="https://news-site.com/article/12345",
    api_key=os.getenv("JINA_API_KEY")
)

result = jina_source.read()

# Access article metadata
print(f"Title: {result['title']}")
print(f"Published: {result.get('publishedTime', 'Unknown')}")
print(f"Description: {result['description']}")

# Access full article content (markdown)
article_text = result['content']
print(f"\nArticle Content:\n{article_text}")

# Parse comments or other dynamic sections
# (Use additional regex or AI to extract structured data from markdown)
```

### Features

- ✅ **JavaScript Execution**: Renders React, Vue, Angular apps
- ✅ **AJAX/Fetch/XHR**: Waits for dynamic content to load
- ✅ **Markdown Conversion**: Clean, structured text output
- ✅ **Metadata Extraction**: Title, description, publish date
- ✅ **Error Handling**: Automatic retries, detailed error messages
- ✅ **Rate Limiting**: Respects Jina.ai tier limits

### API Response Format

```python
{
    "content": str,        # Main page content in markdown
    "title": str,          # Page title (<title> tag)
    "description": str,    # Meta description
    "url": str,            # Final URL (after redirects)
    "publishedTime": str   # Publication timestamp (if available)
}
```

---

## URLDataSource - Simple GET Requests

**Use Case**: Fetch data from simple static sites or public JSON APIs (no JavaScript required).

### Basic Usage

```python
from extract_transform_platform.data_sources.web import URLDataSource

# Fetch JSON data
url_source = URLDataSource(
    url="https://api.example.com/data.json"
)

# Auto-detects JSON and parses
data = url_source.read()  # Returns List[Dict[str, Any]]

# Fetch plain text
text_source = URLDataSource(
    url="https://example.com/document.txt"
)

content = text_source.read()  # Returns str
```

### Example: Fetch Public API Data

```python
from extract_transform_platform.data_sources.web import URLDataSource

# Fetch public JSON API (no authentication)
url_source = URLDataSource(
    url="https://jsonplaceholder.typicode.com/users"
)

# Read JSON array
users = url_source.read()
# [
#     {"id": 1, "name": "Leanne Graham", "email": "Sincere@april.biz", ...},
#     {"id": 2, "name": "Ervin Howell", "email": "Shanna@melissa.tv", ...},
#     ...
# ]

# Process users
for user in users:
    print(f"User: {user['name']} ({user['email']})")

# Get schema
schema = url_source.get_schema()
# {"id": <class 'int'>, "name": <class 'str'>, "email": <class 'str'>, ...}
```

### Example: Fetch Static HTML Page

```python
from extract_transform_platform.data_sources.web import URLDataSource

# Fetch static HTML page
url_source = URLDataSource(
    url="https://example.com/page.html"
)

# Read HTML content as text
html_content = url_source.read()  # Returns str

# Parse HTML (use BeautifulSoup or regex)
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_content, 'html.parser')
title = soup.find('title').text
print(f"Page Title: {title}")
```

### Features

- ✅ **Simple HTTP GET**: No authentication required
- ✅ **Content-Type Detection**: Auto-detects JSON, text
- ✅ **JSON Parsing**: Automatic parsing to List[Dict]
- ✅ **Timeout Support**: Configurable request timeout
- ✅ **Error Handling**: Detailed error messages

---

## Choosing the Right Tool

### Decision Matrix

```
Is the site JavaScript-heavy (SPA, React, Vue, Angular)?
├─ YES → Use JinaDataSource
│   ├─ Need to scrape dynamic content? → JinaDataSource ✓
│   └─ Content loads via AJAX/fetch? → JinaDataSource ✓
│
└─ NO → Is it a simple static site or API?
    ├─ Public JSON API (no auth) → URLDataSource ✓
    ├─ Static HTML page → URLDataSource ✓
    └─ Requires authentication → APIDataSource (see Platform Usage Guide)
```

### Tool Comparison

| Feature | JinaDataSource | URLDataSource | APIDataSource |
|---------|----------------|---------------|---------------|
| **JavaScript Execution** | ✅ Yes | ❌ No | ❌ No |
| **Authentication** | Optional (API key) | ❌ No | ✅ Yes |
| **Rate Limiting** | ✅ Built-in | ❌ No | ✅ Yes |
| **Caching** | ❌ No | ❌ No | ✅ Yes |
| **HTTP Methods** | GET only (via Jina) | GET only | All (GET/POST/PUT/DELETE) |
| **Best For** | SPAs, dynamic content | Static sites, public APIs | Authenticated APIs |

**Recommendation**:
- **JinaDataSource**: JS-heavy sites (React, Vue, Angular, SPAs)
- **URLDataSource**: Simple GET requests (static HTML, public JSON APIs)
- **APIDataSource**: Authenticated APIs with rate limiting/caching

---

## Advanced Examples

### Example 1: Scrape Search Results Page

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os
import re

# Scrape search results (dynamic loading)
jina_source = JinaDataSource(
    url="https://example.com/search?q=widgets",
    api_key=os.getenv("JINA_API_KEY")
)

result = jina_source.read()

# Parse markdown content for search results
content = result['content']

# Example: Extract results (pattern depends on site structure)
result_pattern = r"\*\*([^*]+)\*\*\n([^\n]+)"
matches = re.findall(result_pattern, content)

for title, description in matches:
    print(f"Result: {title}")
    print(f"Description: {description}\n")
```

### Example 2: Monitor Website Changes

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os
import hashlib
import time

def monitor_page(url, interval=3600):
    """Monitor page for changes (check every hour)"""
    previous_hash = None

    while True:
        # Scrape page
        jina_source = JinaDataSource(
            url=url,
            api_key=os.getenv("JINA_API_KEY")
        )

        result = jina_source.read()
        content = result['content']

        # Hash content to detect changes
        current_hash = hashlib.sha256(content.encode()).hexdigest()

        if previous_hash and current_hash != previous_hash:
            print(f"🔔 Page changed! URL: {url}")
            # Send notification, save diff, etc.
        else:
            print(f"✓ No changes detected. URL: {url}")

        previous_hash = current_hash
        time.sleep(interval)

# Monitor product page for price changes
monitor_page("https://example-store.com/product/123", interval=3600)
```

### Example 3: Batch Scraping with Rate Limiting

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os
import time

def scrape_urls_batch(urls, delay=3):
    """Scrape multiple URLs with rate limiting"""
    results = []

    for url in urls:
        try:
            jina_source = JinaDataSource(
                url=url,
                api_key=os.getenv("JINA_API_KEY")
            )

            result = jina_source.read()
            results.append({
                "url": url,
                "title": result['title'],
                "content": result['content']
            })

            print(f"✓ Scraped: {url}")

            # Respect rate limits (wait between requests)
            time.sleep(delay)

        except Exception as e:
            print(f"✗ Failed: {url} - {e}")
            results.append({
                "url": url,
                "error": str(e)
            })

    return results

# Scrape multiple product pages
product_urls = [
    "https://store.com/product/1",
    "https://store.com/product/2",
    "https://store.com/product/3"
]

results = scrape_urls_batch(product_urls, delay=3)
```

---

## Best Practices

### 1. Respect Rate Limits

**Free tier limits**:
- No API key: 20 requests/hour
- With API key: 200 requests/hour

**Best practices**:
```python
import time

# Add delay between requests
time.sleep(3)  # Wait 3 seconds between requests

# Track request count
request_count = 0
start_time = time.time()

if request_count >= 200 and time.time() - start_time < 3600:
    print("Rate limit reached, waiting...")
    time.sleep(60)
```

### 2. Handle Errors Gracefully

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os

try:
    jina_source = JinaDataSource(
        url="https://example.com/page",
        api_key=os.getenv("JINA_API_KEY")
    )

    result = jina_source.read()

except ValueError as e:
    print(f"Invalid URL or request: {e}")
except Exception as e:
    print(f"Scraping failed: {e}")
    # Log error, retry, or skip
```

### 3. Parse Markdown Content Efficiently

```python
import re

def extract_links(markdown_content):
    """Extract links from markdown"""
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    return re.findall(link_pattern, markdown_content)

def extract_headers(markdown_content):
    """Extract headers from markdown"""
    header_pattern = r"^#{1,6} (.+)$"
    return re.findall(header_pattern, markdown_content, re.MULTILINE)

# Usage
result = jina_source.read()
content = result['content']

links = extract_links(content)
headers = extract_headers(content)

print(f"Found {len(links)} links")
print(f"Found {len(headers)} headers")
```

### 4. Cache Results to Save Requests

```python
import json
import hashlib
import os

def cache_result(url, result):
    """Cache scraping result to file"""
    cache_dir = "data/cache/scraping"
    os.makedirs(cache_dir, exist_ok=True)

    # Generate cache filename from URL hash
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = f"{cache_dir}/{url_hash}.json"

    with open(cache_file, 'w') as f:
        json.dump(result, f)

def get_cached_result(url, max_age=3600):
    """Get cached result if fresh"""
    cache_dir = "data/cache/scraping"
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = f"{cache_dir}/{url_hash}.json"

    if os.path.exists(cache_file):
        # Check file age
        file_age = time.time() - os.path.getmtime(cache_file)

        if file_age < max_age:
            with open(cache_file, 'r') as f:
                return json.load(f)

    return None

# Usage
url = "https://example.com/page"

# Check cache first
result = get_cached_result(url, max_age=3600)

if result is None:
    # Not cached or stale, scrape fresh
    jina_source = JinaDataSource(url=url, api_key=os.getenv("JINA_API_KEY"))
    result = jina_source.read()
    cache_result(url, result)
```

---

## Troubleshooting

### Issue 1: Rate Limit Exceeded

**Error**: `429 Too Many Requests` or `Rate limit exceeded`

**Solution**:
```python
import time

# Add delay between requests
time.sleep(5)  # Wait 5 seconds

# Or use exponential backoff
def scrape_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            jina_source = JinaDataSource(url=url, api_key=os.getenv("JINA_API_KEY"))
            return jina_source.read()
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                wait_time = 2 ** attempt * 5  # Exponential backoff
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

    raise Exception("Max retries exceeded")
```

### Issue 2: Content Not Rendered

**Problem**: JavaScript content not appearing in scraped results

**Solution**:
1. **Verify URL**: Make sure URL loads JavaScript content in browser
2. **Check Jina.ai status**: Sometimes Jina.ai may have issues rendering certain sites
3. **Try alternative**: Some sites block automated browsers

```python
# Check what Jina.ai sees
result = jina_source.read()
print("Content length:", len(result['content']))
print("First 500 chars:", result['content'][:500])

# If content is empty or incomplete, the site may block Jina.ai
```

### Issue 3: Invalid API Key

**Error**: `401 Unauthorized` or `Invalid API key`

**Solution**:
```python
import os

# Verify API key is set
api_key = os.getenv("JINA_API_KEY")

if not api_key:
    raise ValueError("JINA_API_KEY environment variable not set")

print(f"Using API key: {api_key[:10]}...")

# Test with a simple request
jina_source = JinaDataSource(
    url="https://example.com",
    api_key=api_key
)

try:
    result = jina_source.read()
    print("API key is valid ✓")
except Exception as e:
    print(f"API key test failed: {e}")
```

### Issue 4: Timeout Errors

**Error**: `requests.exceptions.Timeout`

**Solution**:
```python
from extract_transform_platform.data_sources.web import JinaDataSource

# Increase timeout for slow sites
jina_source = JinaDataSource(
    url="https://slow-site.com/page",
    api_key=os.getenv("JINA_API_KEY"),
    timeout=60  # 60 seconds (default is 30)
)

result = jina_source.read()
```

---

## Next Steps

### Learn More

1. **Platform Usage Guide**: Complete platform documentation
   - [Platform Usage Guide](PLATFORM_USAGE.md)

2. **Platform API Reference**: Detailed API documentation
   - [Platform API Reference](../api/PLATFORM_API.md)

3. **Platform Migration**: Migrate from EDGAR imports
   - [Platform Migration Guide](PLATFORM_MIGRATION.md)

### Advanced Topics

- **AI-Powered Data Extraction**: Use OpenRouterClient to parse markdown content
- **Batch Processing**: Process multiple URLs efficiently
- **Data Transformation**: Transform scraped data with example-driven workflows
- **Project Templates**: Create reusable scraping projects

---

## Summary

**Web Scraping Capabilities**:
- ✅ JavaScript execution (JinaDataSource renders SPAs)
- ✅ Static site scraping (URLDataSource for simple GET requests)
- ✅ Free tier available (20-200 requests/hour)
- ✅ Markdown conversion (clean text extraction)
- ✅ Error handling with retries
- ✅ 100% code reuse from EDGAR (240 LOC JinaDataSource, 190 LOC URLDataSource)

**Quick Commands**:
```python
# JavaScript-heavy site (React, Vue, Angular)
from extract_transform_platform.data_sources.web import JinaDataSource
jina_source = JinaDataSource(url="https://spa-site.com", api_key=os.getenv("JINA_API_KEY"))
result = jina_source.read()

# Simple static site or public API
from extract_transform_platform.data_sources.web import URLDataSource
url_source = URLDataSource(url="https://api.example.com/data.json")
data = url_source.read()
```

**Need Help?** See [Platform Usage Guide](PLATFORM_USAGE.md) or [Platform API Reference](../api/PLATFORM_API.md)
