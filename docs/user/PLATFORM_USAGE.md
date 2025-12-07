# Platform Usage Guide

**Platform**: `extract_transform_platform` (Generic Extract & Transform Platform)
**Status**: Phase 2 - Core Architecture Complete
**Code Reuse**: 83% from EDGAR (exceeds 70% target)

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Data Sources](#data-sources)
- [AI Integration](#ai-integration)
- [Example Workflows](#example-workflows)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)

---

## Overview

The Extract & Transform Platform provides a **general-purpose framework** for:
- **File transformation** (Excel, PDF, DOCX, PPTX → structured data)
- **Web scraping** (JS-heavy sites with Jina.ai)
- **API integration** (REST APIs → structured data)
- **Example-driven workflows** (2-3 examples → automatic transformation code)

**Key Features**:
- 🔄 Example-driven transformation (minimal user input)
- 📊 Multi-format support (Excel, PDF, CSV, JSON, YAML)
- 🤖 AI-powered pattern detection (OpenRouter integration)
- 🧪 Automatic test generation (pytest + validations)
- 📦 Type-safe code generation (Pydantic models)

---

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd edgar

# Install in development mode
pip install -e ".[dev]"

# Verify installation
python -c "from extract_transform_platform import __version__; print(__version__)"
```

### Your First Transformation

**Step 1: Import Platform Components**

```python
from extract_transform_platform.data_sources.file import ExcelDataSource
from extract_transform_platform.models import ProjectConfig

# Create data source
excel_source = ExcelDataSource(
    file_path="data/input.xlsx",
    sheet_name=0,
    header_row=0
)

# Read data
data = excel_source.read()
print(f"Loaded {len(data)} rows")
```

**Step 2: Set Up Project**

```bash
# Create project directory
mkdir -p projects/my_transform/{input,examples,output}

# Copy your Excel file
cp ~/Downloads/data.xlsx projects/my_transform/input/

# Create project config
cat > projects/my_transform/project.yaml <<EOF
name: My Transform
data_source:
  type: excel
  config:
    file_path: input/data.xlsx
    sheet_name: 0
    header_row: 0
examples:
  - examples/row1.json
  - examples/row2.json
EOF
```

**Step 3: Create Examples**

```json
# projects/my_transform/examples/row1.json
{
  "id": "E1001",
  "full_name": "Alice Johnson",
  "dept": "Engineering",
  "hired": "2020-03-15",
  "annual_salary_usd": 95000.0,
  "manager": true
}
```

**Step 4: Run Analysis**

```bash
# Analyze project (detects transformation patterns)
python -m edgar_analyzer analyze-project projects/my_transform/

# Generate extraction code
python -m edgar_analyzer generate-code projects/my_transform/

# Run extraction
python -m edgar_analyzer run-extraction projects/my_transform/
```

---

## Core Concepts

### 1. Data Sources

**BaseDataSource**: Abstract base class for all data sources

```python
from extract_transform_platform.core import BaseDataSource, IDataSource
from typing import List, Dict, Any

class MyDataSource(BaseDataSource):
    """Custom data source implementation"""

    def read(self) -> List[Dict[str, Any]]:
        """Read and return data as list of dicts"""
        # Implementation here
        pass

    def get_schema(self) -> Dict[str, type]:
        """Return schema with field names and types"""
        # Implementation here
        pass
```

### 2. Example-Driven Transformation

**Core Principle**: Provide 2-3 examples → platform generates transformation code

**Example**:
```python
# Source data (Excel row)
{
  "employee_id": "E1001",
  "first_name": "Alice",
  "last_name": "Johnson",
  "salary": 95000
}

# Your desired output (example)
{
  "id": "E1001",
  "full_name": "Alice Johnson",
  "annual_salary_usd": 95000.0
}

# Platform generates transformation code automatically:
# - Field renaming (employee_id → id)
# - String concatenation (first_name + last_name → full_name)
# - Type conversion (int → float)
```

### 3. AI Integration

**OpenRouter Client**: AI-powered pattern detection

```python
from extract_transform_platform.ai import OpenRouterClient, OpenRouterConfig

# Configure client
config = OpenRouterConfig(
    api_key="sk-or-v1-...",
    default_model="anthropic/claude-3.5-sonnet",
    temperature=0.3
)

client = OpenRouterClient(config)

# Detect patterns
response = await client.chat_completion(
    messages=[
        {"role": "user", "content": "Analyze these transformation patterns..."}
    ]
)
```

---

## Data Sources

### File Data Sources

#### Excel Data Source

**Use Case**: Transform Excel spreadsheets (.xlsx, .xls) → structured JSON

```python
from extract_transform_platform.data_sources.file import ExcelDataSource

# Basic usage
excel_source = ExcelDataSource(
    file_path="data/employees.xlsx",
    sheet_name=0,        # First sheet (0-indexed)
    header_row=0,        # First row as header
)

# Read data
data = excel_source.read()  # List[Dict[str, Any]]
schema = excel_source.get_schema()  # Dict[str, type]

# Advanced usage
excel_source = ExcelDataSource(
    file_path="data/employees.xlsx",
    sheet_name="Employees",  # Sheet by name
    header_row=2,           # Third row as header (0-indexed)
    skip_rows=[0, 1],       # Skip first two rows
)
```

**Features**:
- ✅ Automatic type inference (int, float, str, date, bool)
- ✅ NaN handling (converts to None for JSON compatibility)
- ✅ Multiple sheet support (by index or name)
- ✅ Schema detection (field names + types)
- ✅ Performance optimized (<50ms for 100 rows)

**See Also**: [Excel File Transform Guide](EXCEL_FILE_TRANSFORM.md)

---

#### PDF Data Source

**Use Case**: Extract tables from PDF files → structured JSON

```python
from extract_transform_platform.data_sources.file import PDFDataSource

# Basic usage (lines strategy)
pdf_source = PDFDataSource(
    file_path="invoices/invoice_001.pdf",
    page_number=0,           # First page
    table_strategy="lines",  # Best for bordered tables
)

# Read data
data = pdf_source.read()  # List[Dict[str, Any]]

# Advanced usage (with bounding box)
pdf_source = PDFDataSource(
    file_path="invoices/invoice_001.pdf",
    page_number=0,
    table_strategy="text",   # Best for borderless tables
    bounding_box=(50, 100, 550, 700),  # (x0, y0, x1, y1)
)
```

**Table Strategies**:
- **`lines`**: Bordered tables (invoices, reports)
- **`text`**: Borderless tables (plain text layouts)
- **`mixed`**: Hybrid approach (partially bordered)

**Features**:
- ✅ Multiple extraction strategies
- ✅ Bounding box support (target specific regions)
- ✅ Currency parsing ($15.00 → 15.00)
- ✅ Automatic type inference
- ✅ Page-specific extraction

**See Also**: [PDF File Transform Guide](PDF_FILE_TRANSFORM.md)

---

#### CSV Data Source (Legacy Alias)

**Note**: `CSVDataSource` is a legacy alias for `FileDataSource`. Use `FileDataSource` for new code.

**Use Case**: Transform CSV/JSON/YAML files → structured data

```python
# ✅ NEW (Platform - preferred)
from extract_transform_platform.data_sources.file import FileDataSource

# CSV files
csv_source = FileDataSource(
    file_path="data/users.csv",
    source_type="csv"
)

# JSON files
json_source = FileDataSource(
    file_path="data/users.json",
    source_type="json"
)

# YAML files
yaml_source = FileDataSource(
    file_path="data/config.yaml",
    source_type="yaml"
)

# Read data
data = csv_source.read()  # List[Dict[str, Any]]
```

**Features**:
- ✅ Multi-format support (CSV, JSON, YAML, text)
- ✅ Schema detection
- ✅ Type inference
- ✅ Error handling
- ✅ 100% code reuse from EDGAR (290 LOC platform + 30 LOC wrapper)

**Migration Note**: Both `CSVDataSource` and `FileDataSource` work identically. Prefer `FileDataSource` for consistency.

---

#### File Data Source (Complete)

**Use Case**: Universal file parser for CSV, JSON, YAML, and text files
**Status**: Batch 1 complete (290 LOC platform + 30 LOC wrapper, 100% code reuse)

```python
from extract_transform_platform.data_sources.file import FileDataSource

# CSV with automatic type inference
csv_source = FileDataSource(
    file_path="data/employees.csv",
    source_type="csv"
)

# JSON with nested objects
json_source = FileDataSource(
    file_path="data/api_response.json",
    source_type="json"
)

# YAML configuration files
yaml_source = FileDataSource(
    file_path="config/settings.yaml",
    source_type="yaml"
)

# Plain text files
text_source = FileDataSource(
    file_path="logs/output.txt",
    source_type="text"
)

# Read data
data = csv_source.read()  # List[Dict[str, Any]]
schema = csv_source.get_schema()  # Dict[str, type]
```

**Supported Formats**:
- `"csv"` - Comma-separated values (with header row)
- `"json"` - JSON arrays of objects
- `"yaml"` - YAML files (single document or list)
- `"text"` - Plain text files (returns raw string)

**Features**:
- ✅ Automatic schema detection (field names + types)
- ✅ Type inference (int, float, str, bool, date)
- ✅ Header detection (CSV)
- ✅ Nested object support (JSON, YAML)
- ✅ Encoding detection (UTF-8, Latin-1, etc.)
- ✅ Error handling with detailed messages

**Example: CSV with Type Inference**
```python
from extract_transform_platform.data_sources.file import FileDataSource

# Source CSV: data/employees.csv
# employee_id,first_name,last_name,salary,hire_date
# E1001,Alice,Johnson,95000,2020-03-15
# E1002,Bob,Smith,87500,2021-06-01

csv_source = FileDataSource(
    file_path="data/employees.csv",
    source_type="csv"
)

# Get schema (automatic type detection)
schema = csv_source.get_schema()
# {
#     "employee_id": <class 'str'>,
#     "first_name": <class 'str'>,
#     "last_name": <class 'str'>,
#     "salary": <class 'int'>,
#     "hire_date": <class 'str'>  # Can be parsed as date
# }

# Read data
data = csv_source.read()
# [
#     {
#         "employee_id": "E1001",
#         "first_name": "Alice",
#         "last_name": "Johnson",
#         "salary": 95000,
#         "hire_date": "2020-03-15"
#     },
#     {
#         "employee_id": "E1002",
#         "first_name": "Bob",
#         "last_name": "Smith",
#         "salary": 87500,
#         "hire_date": "2021-06-01"
#     }
# ]
```

**Migration from EDGAR**:
```python
# ❌ OLD (EDGAR - still works with deprecation warning)
from edgar_analyzer.data_sources.file_source import FileDataSource

# ✅ NEW (Platform - preferred)
from extract_transform_platform.data_sources.file import FileDataSource
```

---

### Web Data Sources

#### API Data Source

**Use Case**: Fetch data from REST APIs with authentication and rate limiting
**Status**: Batch 1 complete (239 LOC platform + 42 LOC wrapper, 100% code reuse)

```python
from extract_transform_platform.data_sources.web import APIDataSource
import os

# Basic GET request
api_source = APIDataSource(
    url="https://api.example.com/users",
    method="GET",
    headers={"Authorization": f"Bearer {os.getenv('API_KEY')}"}
)

# POST request with data
api_source = APIDataSource(
    url="https://api.example.com/search",
    method="POST",
    headers={"Content-Type": "application/json"},
    data={"query": "employees", "limit": 100}
)

# GET with query parameters
api_source = APIDataSource(
    url="https://api.example.com/users",
    method="GET",
    params={"page": 1, "limit": 50},
    headers={"Authorization": f"Bearer {os.getenv('API_KEY')}"}
)

# Read data
data = api_source.read()  # List[Dict[str, Any]]
schema = api_source.get_schema()  # Dict[str, type]
```

**Features**:
- ✅ HTTP methods (GET, POST, PUT, DELETE, PATCH)
- ✅ Authentication support (Bearer tokens, API keys, custom headers)
- ✅ Query parameters (GET requests)
- ✅ Request body (JSON, form data)
- ✅ Rate limiting (configurable requests per second)
- ✅ Response caching (file-based cache)
- ✅ Automatic retry with exponential backoff
- ✅ Timeout handling
- ✅ Error handling with detailed messages
- ✅ Schema detection from response

**Example: Weather API Integration**
```python
from extract_transform_platform.data_sources.web import APIDataSource
import os

# Fetch 7-day weather forecast
weather_source = APIDataSource(
    url="https://api.openweathermap.org/data/2.5/forecast",
    method="GET",
    params={
        "q": "San Francisco",
        "appid": os.getenv("OPENWEATHER_API_KEY"),
        "units": "metric",
        "cnt": 7
    }
)

# Read forecast data
data = weather_source.read()
# Returns list of forecast objects with temperature, humidity, etc.

# Get schema
schema = weather_source.get_schema()
# Auto-detected from API response structure
```

**Rate Limiting**:
```python
from extract_transform_platform.data_sources.web import APIDataSource

# Configure rate limiting (max 10 requests per second)
api_source = APIDataSource(
    url="https://api.example.com/data",
    method="GET",
    rate_limit=10,  # Requests per second
    headers={"Authorization": "Bearer token123"}
)
```

**Caching**:
```python
from extract_transform_platform.data_sources.web import APIDataSource

# Enable response caching (default: 1 hour)
api_source = APIDataSource(
    url="https://api.example.com/data",
    method="GET",
    cache_ttl=3600,  # Cache for 1 hour
    headers={"Authorization": "Bearer token123"}
)

# Subsequent calls return cached data (if fresh)
data = api_source.read()  # Cached response
```

**Migration from EDGAR**:
```python
# ❌ OLD (EDGAR - still works with deprecation warning)
from edgar_analyzer.data_sources.api_source import APIDataSource

# ✅ NEW (Platform - preferred)
from extract_transform_platform.data_sources.web import APIDataSource
```

---

#### URL Data Source

**Use Case**: Simple HTTP GET requests with content-type detection
**Status**: Batch 1 complete (190 LOC platform + 29 LOC wrapper, 100% code reuse)

```python
from extract_transform_platform.data_sources.web import URLDataSource

# Fetch JSON data
url_source = URLDataSource(
    url="https://api.example.com/data.json"
)

# Read data (auto-detects JSON)
data = url_source.read()  # List[Dict[str, Any]]

# Fetch plain text
text_source = URLDataSource(
    url="https://example.com/document.txt"
)

# Read text content
content = text_source.read()  # str
```

**Features**:
- ✅ Simple HTTP GET requests (no auth required)
- ✅ Automatic content-type detection (JSON, text)
- ✅ JSON parsing (returns List[Dict])
- ✅ Text content extraction (returns str)
- ✅ Error handling with detailed messages
- ✅ Timeout support

**Example: Fetch Public JSON Data**
```python
from extract_transform_platform.data_sources.web import URLDataSource

# Fetch public API data (no authentication)
url_source = URLDataSource(
    url="https://jsonplaceholder.typicode.com/users"
)

# Read JSON array
users = url_source.read()
# [
#     {"id": 1, "name": "Leanne Graham", "email": "..."},
#     {"id": 2, "name": "Ervin Howell", "email": "..."},
#     ...
# ]

# Get schema
schema = url_source.get_schema()
# {"id": <class 'int'>, "name": <class 'str'>, "email": <class 'str'>, ...}
```

**When to Use URLDataSource vs APIDataSource**:
- **URLDataSource**: Simple GET requests, public APIs, no auth required
- **APIDataSource**: Complex requests, authentication, rate limiting, caching, retries

---

#### Jina Data Source

**Use Case**: Scrape JS-heavy websites using Jina.ai API
**Status**: Batch 1 complete (240 LOC platform + 46 LOC wrapper, 100% code reuse + 1 bug fix)

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os

# Basic usage (with API key)
jina_source = JinaDataSource(
    url="https://example.com/dynamic-content",
    api_key=os.getenv("JINA_API_KEY")  # Recommended (higher rate limits)
)

# Free tier (no API key required)
jina_free = JinaDataSource(
    url="https://example.com/spa-app"
    # No api_key = uses free tier (limited requests/day)
)

# Read data (returns markdown + structured data)
data = jina_source.read()  # Dict with 'content', 'title', 'description', etc.
```

**Features**:
- ✅ JavaScript execution (renders dynamic content like a browser)
- ✅ Markdown conversion (clean text extraction from HTML)
- ✅ API key support (optional, free tier available)
- ✅ Rate limiting (free: 20 req/hour, paid: higher limits)
- ✅ Single-page application (SPA) support
- ✅ AJAX/fetch/XHR handling
- ✅ Error handling with retry logic
- ✅ Content extraction (title, description, main content)

**Use Cases**:
- ✅ Single-page applications (React, Vue, Angular)
- ✅ Dynamic content loaded via JavaScript
- ✅ Interactive websites with AJAX
- ✅ Modern web frameworks
- ✅ Sites that don't work with traditional scrapers

**Example: Scrape React SPA**
```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os

# Scrape a React single-page application
jina_source = JinaDataSource(
    url="https://example-react-app.com/products",
    api_key=os.getenv("JINA_API_KEY")
)

# Read rendered content (JavaScript executed)
result = jina_source.read()
# {
#     'content': '# Products\n\n## Widget A\nPrice: $19.99\n\n## Widget B\nPrice: $29.99',
#     'title': 'Products - Example Store',
#     'description': 'Browse our product catalog',
#     'url': 'https://example-react-app.com/products',
#     'publishedTime': '2024-01-15T10:30:00Z'
# }

# Parse markdown content for structured data
# (Use additional parsing logic or AI to extract product information)
```

**API Key Configuration**:
```bash
# 1. Get free API key from https://jina.ai
# 2. Set environment variable
export JINA_API_KEY="jina-xxxxxxxxxxxx"

# 3. Or use .env file
echo "JINA_API_KEY=jina-xxxxxxxxxxxx" >> .env
```

**Rate Limits**:
- **Free tier** (no API key): 20 requests/hour
- **Free tier** (with API key): 200 requests/hour
- **Paid tier**: Higher limits (check Jina.ai pricing)

**Error Handling**:
```python
from extract_transform_platform.data_sources.web import JinaDataSource

try:
    jina_source = JinaDataSource(
        url="https://example.com/spa",
        api_key=os.getenv("JINA_API_KEY")
    )
    data = jina_source.read()
except ValueError as e:
    print(f"Invalid URL or request: {e}")
except Exception as e:
    print(f"Scraping failed: {e}")
```

**See Also**: [Web Scraping Guide](WEB_SCRAPING.md) for detailed tutorials and best practices

---

## AI Integration

### OpenRouter Client

**Purpose**: AI-powered pattern detection and code generation

#### Basic Usage

```python
from extract_transform_platform.ai import OpenRouterClient, OpenRouterConfig

# Configure client
config = OpenRouterConfig(
    api_key="sk-or-v1-...",
    default_model="anthropic/claude-3.5-sonnet",
    temperature=0.3,
    max_tokens=4000
)

client = OpenRouterClient(config)

# Chat completion
response = await client.chat_completion(
    messages=[
        {
            "role": "system",
            "content": "You are a data transformation expert."
        },
        {
            "role": "user",
            "content": "Analyze these transformation patterns..."
        }
    ]
)

print(response["content"])
```

#### Pattern Detection

```python
from extract_transform_platform.ai import PromptTemplates

# Load templates
templates = PromptTemplates()

# Detect transformation patterns
source_data = {"employee_id": "E1001", "first_name": "Alice", "last_name": "Johnson"}
target_data = {"id": "E1001", "full_name": "Alice Johnson"}

prompt = templates.detect_patterns(
    source_schema=source_data,
    target_schema=target_data,
    examples=[source_data, target_data]
)

# Send to OpenRouter
response = await client.chat_completion(
    messages=[{"role": "user", "content": prompt}]
)

# Parse detected patterns
patterns = parse_patterns(response["content"])
```

#### Configuration

```python
from extract_transform_platform.ai import AIConfig, load_ai_config

# Load from environment
config = load_ai_config()

# Or create manually
config = AIConfig(
    openrouter=OpenRouterConfig(
        api_key="sk-or-v1-...",
        default_model="anthropic/claude-3.5-sonnet",
        temperature=0.3
    )
)
```

---

## Example Workflows

### Workflow 1: Excel → JSON Transformation

**Use Case**: Transform employee roster from Excel to JSON

```python
from extract_transform_platform.data_sources.file import ExcelDataSource
from extract_transform_platform.models import ProjectConfig

# 1. Read Excel file
excel_source = ExcelDataSource(
    file_path="data/employees.xlsx",
    sheet_name=0,
    header_row=0
)

data = excel_source.read()
print(f"Loaded {len(data)} employees")

# 2. Define transformation (via examples)
source_example = data[0]  # First row
target_example = {
    "id": source_example["employee_id"],
    "full_name": f"{source_example['first_name']} {source_example['last_name']}",
    "annual_salary_usd": float(source_example["salary"])
}

# 3. Generate transformation code (AI-powered)
# (See analyze-project and generate-code commands)

# 4. Run transformation
# (See run-extraction command)
```

---

### Workflow 2: PDF Invoice Extraction

**Use Case**: Extract line items from PDF invoices

```python
from extract_transform_platform.data_sources.file import PDFDataSource

# 1. Read PDF table
pdf_source = PDFDataSource(
    file_path="invoices/invoice_001.pdf",
    page_number=0,
    table_strategy="lines"
)

data = pdf_source.read()
print(f"Extracted {len(data)} line items")

# 2. Define transformation (via examples)
source_example = data[0]
target_example = {
    "product": source_example["Item"],
    "qty": int(source_example["Quantity"]),
    "unit_price_usd": parse_currency(source_example["Unit Price"]),
    "line_total_usd": parse_currency(source_example["Total"])
}

# 3. Generate transformation code
# (See PDF File Transform Guide)
```

---

### Workflow 3: API Data Fetching

**Use Case**: Fetch weather data from API and transform

```python
from extract_transform_platform.data_sources.web import APIDataSource
import os

# 1. Fetch data from API
api_source = APIDataSource(
    url="https://api.weather.com/v1/forecast",
    method="GET",
    headers={"Authorization": f"Bearer {os.getenv('WEATHER_API_KEY')}"},
    params={"location": "San Francisco", "days": 7}
)

data = api_source.read()
print(f"Fetched {len(data)} forecast days")

# 2. Define transformation
# (Transform API response to desired format)
```

---

### Workflow 4: Web Scraping (JS-Heavy Sites)

**Use Case**: Scrape dynamic content from single-page application

```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os

# 1. Scrape dynamic content
jina_source = JinaDataSource(
    url="https://example.com/products",
    api_key=os.getenv("JINA_API_KEY")
)

data = jina_source.read()
print(f"Scraped content length: {len(data)} chars")

# 2. Parse and transform
# (Extract structured data from markdown)
```

---

## Schema Analysis & Pattern Detection

### Schema Analyzer

**Purpose**: Infer and compare schemas from example data to identify transformation patterns.

#### Basic Schema Inference

```python
from extract_transform_platform.services.analysis import SchemaAnalyzer
from extract_transform_platform.models.patterns import FieldTypeEnum

# Create analyzer
analyzer = SchemaAnalyzer()

# Sample data
examples = [
    {
        "input": {"employee_id": "E1001", "salary": 95000, "hired": "2020-03-15"},
        "output": {"id": "E1001", "annual_salary_usd": 95000.0, "hire_date": "2020-03-15"}
    },
    {
        "input": {"employee_id": "E1002", "salary": 87500, "hired": "2021-06-01"},
        "output": {"id": "E1002", "annual_salary_usd": 87500.0, "hire_date": "2021-06-01"}
    }
]

# Infer input schema
input_schema = analyzer.infer_input_schema(examples)
# Schema(
#     fields={
#         "employee_id": SchemaField(name="employee_id", type=FieldTypeEnum.STRING),
#         "salary": SchemaField(name="salary", type=FieldTypeEnum.INTEGER),
#         "hired": SchemaField(name="hired", type=FieldTypeEnum.STRING)
#     }
# )

# Infer output schema
output_schema = analyzer.infer_output_schema(examples)
# Schema(
#     fields={
#         "id": SchemaField(name="id", type=FieldTypeEnum.STRING),
#         "annual_salary_usd": SchemaField(name="annual_salary_usd", type=FieldTypeEnum.FLOAT),
#         "hire_date": SchemaField(name="hire_date", type=FieldTypeEnum.STRING)
#     }
# )
```

#### Schema Comparison

```python
from extract_transform_platform.services.analysis import SchemaAnalyzer

analyzer = SchemaAnalyzer()

# Compare schemas to find differences
differences = analyzer.compare_schemas(input_schema, output_schema)

# Differences include:
# - Field renames: employee_id → id, hired → hire_date
# - Type changes: salary (INTEGER) → annual_salary_usd (FLOAT)
# - Added fields
# - Removed fields

for diff in differences:
    print(f"{diff.type}: {diff.description}")
# Output:
# field_rename: employee_id → id
# field_rename: hired → hire_date
# type_change: salary (INTEGER) → annual_salary_usd (FLOAT)
```

#### Nested Structure Analysis

```python
from extract_transform_platform.services.analysis import SchemaAnalyzer

analyzer = SchemaAnalyzer()

# Nested data example
examples = [
    {
        "input": {
            "name": "Alice",
            "address": {
                "city": "London",
                "country": "UK"
            }
        },
        "output": {
            "full_name": "Alice",
            "location": "London, UK"
        }
    }
]

# Analyze nested structure
input_schema = analyzer.infer_input_schema(examples)
# Field paths: "name", "address.city", "address.country"

output_schema = analyzer.infer_output_schema(examples)
# Field paths: "full_name", "location"

# Schema analyzer uses dot notation for nested fields
```

**Performance**: <100ms for 10 examples with 50 fields each

---

### Example Parser

**Purpose**: Extract transformation patterns from input/output example pairs.

#### Basic Pattern Extraction

```python
from extract_transform_platform.services.analysis import ExampleParser, SchemaAnalyzer
from extract_transform_platform.models.patterns import PatternType

# Create analyzer and parser
analyzer = SchemaAnalyzer()
parser = ExampleParser(analyzer)

# Provide 2-3 transformation examples
examples = [
    ExampleConfig(
        input={"employee_id": "E1001", "first_name": "Alice", "last_name": "Johnson"},
        output={"id": "E1001", "full_name": "Alice Johnson"}
    ),
    ExampleConfig(
        input={"employee_id": "E1002", "first_name": "Bob", "last_name": "Smith"},
        output={"id": "E1002", "full_name": "Bob Smith"}
    )
]

# Parse examples to detect patterns
parsed = parser.parse_examples(examples)

# Access detected patterns
for pattern in parsed.patterns:
    print(f"{pattern.type}: {pattern.confidence:.2f}")
    print(f"  {pattern.source_path} → {pattern.target_path}")
    print(f"  Transformation: {pattern.transformation}")

# Output:
# FIELD_MAPPING: 1.00
#   employee_id → id
#   Transformation: Direct field rename
# CONCATENATION: 1.00
#   first_name + last_name → full_name
#   Transformation: Concatenate with space separator
```

#### Confidence Scoring

```python
from extract_transform_platform.services.analysis import ExampleParser

parser = ExampleParser(analyzer)
parsed = parser.parse_examples(examples)

# High-confidence patterns (≥0.9)
high_confidence = parsed.high_confidence_patterns
print(f"High confidence patterns: {len(high_confidence)}")

# Medium-confidence patterns (0.7-0.89)
medium_confidence = parsed.medium_confidence_patterns
print(f"Medium confidence patterns: {len(medium_confidence)}")

# Low-confidence patterns (<0.7)
low_confidence = parsed.low_confidence_patterns
print(f"Low confidence patterns: {len(low_confidence)}")

# Confidence is based on:
# - Consistency across examples (all examples show same pattern)
# - Type compatibility (source and target types match expected)
# - Pattern complexity (simpler patterns = higher confidence)
```

#### Pattern Types Detected

```python
from extract_transform_platform.models.patterns import PatternType

# Example Parser can detect 14 pattern types:

# 1. FIELD_MAPPING - Direct field mapping
pattern = Pattern(
    type=PatternType.FIELD_MAPPING,
    source_path="employee_id",
    target_path="id"
)

# 2. CONCATENATION - String concatenation
pattern = Pattern(
    type=PatternType.CONCATENATION,
    source_path="first_name + last_name",
    target_path="full_name"
)

# 3. TYPE_CONVERSION - Type conversions
pattern = Pattern(
    type=PatternType.TYPE_CONVERSION,
    source_path="salary",
    target_path="annual_salary_usd",
    transformation="int → float"
)

# 4. BOOLEAN_CONVERSION - Boolean normalization
pattern = Pattern(
    type=PatternType.BOOLEAN_CONVERSION,
    source_path="is_manager",
    target_path="manager",
    transformation="'Yes'/'No' → true/false"
)

# 5. VALUE_MAPPING - Discrete value mapping
pattern = Pattern(
    type=PatternType.VALUE_MAPPING,
    source_path="status_code",
    target_path="status",
    transformation="'A' → 'Active', 'I' → 'Inactive'"
)

# 6. FIELD_EXTRACTION - Substring extraction
pattern = Pattern(
    type=PatternType.FIELD_EXTRACTION,
    source_path="email",
    target_path="domain",
    transformation="Extract domain from email"
)

# 7. NESTED_ACCESS - Nested object access
pattern = Pattern(
    type=PatternType.NESTED_ACCESS,
    source_path="address.city",
    target_path="city"
)

# 8. LIST_AGGREGATION - List operations
pattern = Pattern(
    type=PatternType.LIST_AGGREGATION,
    source_path="scores",
    target_path="average_score",
    transformation="Average of list values"
)

# 9. CONDITIONAL - Conditional logic
pattern = Pattern(
    type=PatternType.CONDITIONAL,
    source_path="age",
    target_path="adult",
    transformation="age >= 18 → true, else false"
)

# 10. DATE_PARSING - Date/time parsing
pattern = Pattern(
    type=PatternType.DATE_PARSING,
    source_path="hire_date_str",
    target_path="hire_date",
    transformation="Parse date from string"
)

# 11. MATH_OPERATION - Mathematical operations
pattern = Pattern(
    type=PatternType.MATH_OPERATION,
    source_path="quantity * unit_price",
    target_path="total",
    transformation="Multiplication"
)

# 12. STRING_FORMATTING - String formatting
pattern = Pattern(
    type=PatternType.STRING_FORMATTING,
    source_path="first_name + last_name",
    target_path="display_name",
    transformation="Format as 'Last, First'"
)

# 13. DEFAULT_VALUE - Default value handling
pattern = Pattern(
    type=PatternType.DEFAULT_VALUE,
    source_path="optional_field",
    target_path="required_field",
    transformation="Use default if null/missing"
)

# 14. CUSTOM - Custom transformations
pattern = Pattern(
    type=PatternType.CUSTOM,
    source_path="complex_input",
    target_path="complex_output",
    transformation="Custom logic (describe here)"
)
```

**See Also**: [Pattern Detection Guide](PATTERN_DETECTION.md) for detailed explanations of all pattern types.

---

### Pattern Models

**Purpose**: Define transformation pattern data structures for AI code generation.

#### Pattern Model

```python
from extract_transform_platform.models.patterns import Pattern, PatternType

# Create a transformation pattern
pattern = Pattern(
    type=PatternType.FIELD_MAPPING,
    confidence=1.0,
    source_path="employee_id",
    target_path="id",
    transformation="Direct field rename",
    examples=[("E1001", "E1001"), ("E1002", "E1002")]
)

# Access pattern properties
print(f"Type: {pattern.type}")
print(f"Confidence: {pattern.confidence}")
print(f"Source: {pattern.source_path}")
print(f"Target: {pattern.target_path}")
```

#### Schema Model

```python
from extract_transform_platform.models.patterns import Schema, SchemaField, FieldTypeEnum

# Create a schema
schema = Schema(
    fields={
        "id": SchemaField(
            name="id",
            type=FieldTypeEnum.STRING,
            required=True,
            nullable=False
        ),
        "salary": SchemaField(
            name="salary",
            type=FieldTypeEnum.FLOAT,
            required=True,
            nullable=False
        )
    }
)

# Access schema fields
for field_name, field in schema.fields.items():
    print(f"{field_name}: {field.type.value}")
```

#### Parsed Examples Model

```python
from extract_transform_platform.models.patterns import ParsedExamples

# Result from ExampleParser.parse_examples()
parsed = ParsedExamples(
    input_schema=input_schema,
    output_schema=output_schema,
    patterns=[pattern1, pattern2, pattern3],
    examples_count=3
)

# Access parsed results
print(f"Input schema fields: {len(parsed.input_schema.fields)}")
print(f"Output schema fields: {len(parsed.output_schema.fields)}")
print(f"Detected patterns: {len(parsed.patterns)}")
print(f"Examples analyzed: {parsed.examples_count}")

# Filter by confidence
high_confidence = parsed.high_confidence_patterns  # ≥0.9
medium_confidence = parsed.medium_confidence_patterns  # 0.7-0.89
low_confidence = parsed.low_confidence_patterns  # <0.7
```

---

### End-to-End Example-Driven Workflow

**Complete workflow**: From examples → patterns → code generation

```python
from extract_transform_platform.services.analysis import SchemaAnalyzer, ExampleParser
from extract_transform_platform.models.patterns import PatternType
from extract_transform_platform.data_sources.file import ExcelDataSource

# Step 1: Load source data
excel_source = ExcelDataSource(
    file_path="data/employees.xlsx",
    sheet_name=0
)
source_data = excel_source.read()

# Step 2: Define transformation examples
examples = [
    ExampleConfig(
        input=source_data[0],  # First row
        output={
            "id": source_data[0]["employee_id"],
            "full_name": f"{source_data[0]['first_name']} {source_data[0]['last_name']}",
            "annual_salary_usd": float(source_data[0]["salary"])
        }
    ),
    ExampleConfig(
        input=source_data[1],  # Second row
        output={
            "id": source_data[1]["employee_id"],
            "full_name": f"{source_data[1]['first_name']} {source_data[1]['last_name']}",
            "annual_salary_usd": float(source_data[1]["salary"])
        }
    )
]

# Step 3: Analyze and extract patterns
analyzer = SchemaAnalyzer()
parser = ExampleParser(analyzer)
parsed = parser.parse_examples(examples)

# Step 4: Review detected patterns
print(f"Detected {len(parsed.patterns)} patterns:")
for pattern in parsed.high_confidence_patterns:
    print(f"  {pattern.type}: {pattern.transformation}")

# Step 5: Use patterns for AI code generation
# (Patterns are passed to OpenRouter for Sonnet 4.5 code generation)
# See generate-code command for full workflow
```

**Performance**: End-to-end analysis <500ms for 10 examples with 50 fields

---

## Advanced Features

### Custom Data Sources

**Create custom data source** for specialized formats:

```python
from extract_transform_platform.core import BaseDataSource
from typing import List, Dict, Any

class DatabaseDataSource(BaseDataSource):
    """Extract data from SQL database"""

    def __init__(self, connection_string: str, query: str):
        self.connection_string = connection_string
        self.query = query

    def read(self) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        # Connect to database
        # Execute query
        # Return results as list of dicts
        pass

    def get_schema(self) -> Dict[str, type]:
        """Infer schema from query results"""
        # Get column names and types
        pass

# Usage
db_source = DatabaseDataSource(
    connection_string="postgresql://user:pass@host/db",
    query="SELECT * FROM employees"
)

data = db_source.read()
```

---

### Transformation Pattern Detection

**Supported Pattern Types**:

| Type | Example | Detection |
|------|---------|-----------|
| **Field Rename** | `employee_id` → `id` | Schema comparison |
| **Concatenation** | `first_name + last_name` → `full_name` | Value matching |
| **Type Convert** | `95000` (int) → `95000.0` (float) | Type change |
| **Boolean** | `"Yes"` → `true` | Pattern recognition |
| **Value Mapping** | `"A"` → `"Active"` | Discrete mapping |
| **Field Extract** | `"alice@ex.com"` → `"ex.com"` | Substring patterns |

**Example**:

```python
from extract_transform_platform.ai import PromptTemplates

templates = PromptTemplates()

# Detect patterns from examples
patterns = templates.detect_patterns(
    source_schema={
        "employee_id": "str",
        "first_name": "str",
        "last_name": "str",
        "salary": "int"
    },
    target_schema={
        "id": "str",
        "full_name": "str",
        "annual_salary_usd": "float"
    },
    examples=[
        {
            "source": {"employee_id": "E1001", "first_name": "Alice", "last_name": "Johnson", "salary": 95000},
            "target": {"id": "E1001", "full_name": "Alice Johnson", "annual_salary_usd": 95000.0}
        }
    ]
)

# patterns will include:
# - field_rename: employee_id → id
# - concatenation: first_name + last_name → full_name
# - type_convert: salary (int) → annual_salary_usd (float)
```

---

### Code Generation

**Generate type-safe extraction code**:

```python
from extract_transform_platform.codegen import CodeGenerator

generator = CodeGenerator()

# Generate extractor class
code = generator.generate_extractor(
    class_name="EmployeeExtractor",
    source_schema={"employee_id": "str", "first_name": "str", "last_name": "str"},
    target_schema={"id": "str", "full_name": "str"},
    patterns=[
        {"type": "field_rename", "from": "employee_id", "to": "id"},
        {"type": "concatenation", "fields": ["first_name", "last_name"], "to": "full_name"}
    ]
)

# Generated code includes:
# - Pydantic models (SourceModel, TargetModel)
# - Transform function (transform_row)
# - Batch transform (transform_batch)
# - pytest tests (test_transform)
```

---

## Best Practices

### 1. Data Source Selection

**Choose the right data source**:

| Format | Data Source | Best For |
|--------|-------------|----------|
| **Excel** (.xlsx, .xls) | `ExcelDataSource` | Spreadsheets, tabular data |
| **PDF** (.pdf) | `PDFDataSource` | Invoices, reports with tables |
| **CSV** (.csv) | `CSVDataSource` | Simple tabular data |
| **JSON** (.json) | `CSVDataSource` | Structured API responses |
| **REST API** | `APIDataSource` | Live data, webhooks |
| **Web Pages** | `JinaDataSource` | JS-heavy sites, SPAs |

---

### 2. Example Quality

**Provide high-quality examples**:

✅ **Good Examples**:
- Cover all transformation types
- Include edge cases (nulls, special characters)
- Representative of actual data
- 2-3 examples minimum

❌ **Poor Examples**:
- Only happy path (no edge cases)
- Incomplete transformations
- Non-representative data
- Only 1 example

---

### 3. Error Handling

**Handle errors gracefully**:

```python
from extract_transform_platform.data_sources.file import ExcelDataSource

try:
    excel_source = ExcelDataSource(
        file_path="data/employees.xlsx",
        sheet_name=0
    )
    data = excel_source.read()
except FileNotFoundError:
    print("Excel file not found")
except ValueError as e:
    print(f"Invalid data: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

### 4. Performance Optimization

**Optimize for large datasets**:

```python
# ❌ Bad (loads entire file into memory)
data = excel_source.read()
for row in data:
    process(row)

# ✅ Good (process in chunks)
for chunk in excel_source.read_chunks(chunk_size=1000):
    process_batch(chunk)
```

---

### 5. Testing

**Write comprehensive tests**:

```python
import pytest
from extract_transform_platform.data_sources.file import ExcelDataSource

def test_excel_source_read():
    """Test ExcelDataSource reads data correctly"""
    source = ExcelDataSource(
        file_path="tests/fixtures/employees.xlsx",
        sheet_name=0
    )

    data = source.read()

    assert len(data) == 100
    assert "employee_id" in data[0]
    assert data[0]["employee_id"] == "E1001"

def test_excel_source_schema():
    """Test ExcelDataSource detects schema correctly"""
    source = ExcelDataSource(
        file_path="tests/fixtures/employees.xlsx",
        sheet_name=0
    )

    schema = source.get_schema()

    assert schema["employee_id"] == str
    assert schema["salary"] == int
```

---

## Next Steps

### Learn More

1. **Migration Guide**: Migrate from EDGAR to platform
   - [Platform Migration Guide](PLATFORM_MIGRATION.md)

2. **API Reference**: Detailed API documentation
   - [Platform API Reference](../api/PLATFORM_API.md)

3. **Excel Workflows**: Excel-specific transformations
   - [Excel File Transform Guide](EXCEL_FILE_TRANSFORM.md)

4. **PDF Workflows**: PDF table extraction
   - [PDF File Transform Guide](PDF_FILE_TRANSFORM.md)

### Contribute

Join platform development:
- [Linear Project](https://linear.app/1m-hyperdev/project/edgar-%E2%86%92-general-purpose-extract-and-transform-platform-e4cb3518b13e/issues)
- [GitHub Repository](https://github.com/your-org/edgar)

---

## Summary

**Platform Capabilities**:
- ✅ Multi-format support (Excel, PDF, CSV, JSON, API, Web)
- ✅ Example-driven transformation (2-3 examples → code)
- ✅ AI-powered pattern detection (OpenRouter integration)
- ✅ Type-safe code generation (Pydantic models)
- ✅ Comprehensive testing (132/132 passing)

**Quick Commands**:
```bash
# Install platform
pip install -e ".[dev]"

# Create project
mkdir -p projects/my_transform/{input,examples,output}

# Analyze and generate code
python -m edgar_analyzer analyze-project projects/my_transform/
python -m edgar_analyzer generate-code projects/my_transform/

# Run extraction
python -m edgar_analyzer run-extraction projects/my_transform/
```

**Need Help?** See [Platform API Reference](../api/PLATFORM_API.md) or [Platform Migration Guide](PLATFORM_MIGRATION.md)
