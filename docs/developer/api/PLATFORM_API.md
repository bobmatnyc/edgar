# Platform API Reference

**Platform**: `extract_transform_platform`
**Version**: 0.1.0
**Status**: Phase 2 - Core Architecture Complete

## Table of Contents

- [Core Module](#core-module)
- [Data Sources](#data-sources)
  - [File Data Sources](#file-data-sources)
  - [Web Data Sources](#web-data-sources)
- [AI Integration](#ai-integration)
- [Schema Services (Batch 2)](#schema-services-batch-2-)
  - [Pattern Models](#extracttransformplatformmodelspatterns)
  - [Schema Analysis Services](#extracttransformplatformservicesanalysis)
- [Models](#models)
- [Code Generation](#code-generation)
- [Services](#services)
- [Utilities](#utilities)

---

## Core Module

### `extract_transform_platform.core`

Base abstractions for all data sources and platform components.

#### BaseDataSource

**Abstract base class** for all data source implementations.

```python
from extract_transform_platform.core import BaseDataSource
from typing import List, Dict, Any
from abc import abstractmethod

class BaseDataSource:
    """Abstract base class for data sources"""

    @abstractmethod
    def read(self) -> List[Dict[str, Any]]:
        """
        Read and return data from source.

        Returns:
            List[Dict[str, Any]]: List of dictionaries representing data rows

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, type]:
        """
        Get schema of data source with field names and types.

        Returns:
            Dict[str, type]: Field names mapped to Python types

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        pass

    def validate(self) -> bool:
        """
        Validate data source configuration.

        Returns:
            bool: True if valid, False otherwise
        """
        return True
```

**Usage Example**:
```python
from extract_transform_platform.core import BaseDataSource

class CustomDataSource(BaseDataSource):
    def __init__(self, config):
        self.config = config

    def read(self) -> List[Dict[str, Any]]:
        # Implementation
        return [{"field": "value"}]

    def get_schema(self) -> Dict[str, type]:
        # Implementation
        return {"field": str}
```

---

#### IDataSource

**Protocol** defining data source interface (for type checking).

```python
from extract_transform_platform.core import IDataSource
from typing import Protocol, List, Dict, Any

class IDataSource(Protocol):
    """Protocol for data source interface"""

    def read(self) -> List[Dict[str, Any]]:
        """Read data from source"""
        ...

    def get_schema(self) -> Dict[str, type]:
        """Get schema of data source"""
        ...
```

**Usage Example**:
```python
from extract_transform_platform.core import IDataSource

def process_data(source: IDataSource):
    """Process data from any source"""
    data = source.read()
    schema = source.get_schema()
    # Process...
```

---

## Data Sources

### File Data Sources

#### ExcelDataSource

**Read and parse Excel spreadsheets** (.xlsx, .xls).

```python
from extract_transform_platform.data_sources.file import ExcelDataSource
```

**Constructor**:
```python
ExcelDataSource(
    file_path: str,
    sheet_name: Union[int, str] = 0,
    header_row: int = 0,
    skip_rows: Optional[List[int]] = None
)
```

**Parameters**:
- `file_path` (str): Path to Excel file (.xlsx or .xls)
- `sheet_name` (Union[int, str], default=0): Sheet index (0-based) or name
- `header_row` (int, default=0): Row index to use as header (0-based)
- `skip_rows` (Optional[List[int]]): List of row indices to skip

**Methods**:

##### read()

```python
def read() -> List[Dict[str, Any]]:
    """
    Read Excel file and return data as list of dictionaries.

    Returns:
        List[Dict[str, Any]]: Each row as a dictionary

    Raises:
        FileNotFoundError: If Excel file not found
        ValueError: If sheet not found or invalid format
    """
```

##### get_schema()

```python
def get_schema() -> Dict[str, type]:
    """
    Get schema with field names and inferred types.

    Returns:
        Dict[str, type]: Field names mapped to Python types

    Type Mapping:
        - int64 → int
        - float64 → float
        - object (string) → str
        - datetime64 → str (ISO format)
        - bool → bool
    """
```

**Usage Example**:
```python
from extract_transform_platform.data_sources.file import ExcelDataSource

# Basic usage
excel_source = ExcelDataSource(
    file_path="data/employees.xlsx",
    sheet_name=0,
    header_row=0
)

# Read data
data = excel_source.read()
# [
#     {"employee_id": "E1001", "first_name": "Alice", "last_name": "Johnson"},
#     {"employee_id": "E1002", "first_name": "Bob", "last_name": "Smith"}
# ]

# Get schema
schema = excel_source.get_schema()
# {"employee_id": <class 'str'>, "first_name": <class 'str'>, "last_name": <class 'str'>}

# Advanced usage (specific sheet by name)
excel_source = ExcelDataSource(
    file_path="data/employees.xlsx",
    sheet_name="Employees",
    header_row=2,  # Third row as header
    skip_rows=[0, 1]  # Skip first two rows
)
```

**Performance**:
- 100 rows: ~45ms
- 1,000 rows: ~180ms
- 10,000 rows: ~950ms

---

#### PDFDataSource

**Extract tables from PDF files**.

```python
from extract_transform_platform.data_sources.file import PDFDataSource
```

**Constructor**:
```python
PDFDataSource(
    file_path: str,
    page_number: int = 0,
    table_strategy: str = "lines",
    bounding_box: Optional[Tuple[float, float, float, float]] = None
)
```

**Parameters**:
- `file_path` (str): Path to PDF file
- `page_number` (int, default=0): Page index (0-based)
- `table_strategy` (str, default="lines"): Table extraction strategy
  - `"lines"`: Bordered tables (best for invoices, reports)
  - `"text"`: Borderless tables (best for plain text layouts)
  - `"mixed"`: Hybrid approach (partially bordered tables)
- `bounding_box` (Optional[Tuple], default=None): Region to extract `(x0, y0, x1, y1)`

**Methods**:

##### read()

```python
def read() -> List[Dict[str, Any]]:
    """
    Extract table from PDF and return as list of dictionaries.

    Returns:
        List[Dict[str, Any]]: Each row as a dictionary

    Raises:
        FileNotFoundError: If PDF file not found
        ValueError: If no tables found on page
    """
```

##### get_schema()

```python
def get_schema() -> Dict[str, type]:
    """
    Get schema with field names and inferred types.

    Returns:
        Dict[str, type]: Field names mapped to Python types
    """
```

**Usage Example**:
```python
from extract_transform_platform.data_sources.file import PDFDataSource

# Basic usage (lines strategy)
pdf_source = PDFDataSource(
    file_path="invoices/invoice_001.pdf",
    page_number=0,
    table_strategy="lines"
)

# Read data
data = pdf_source.read()
# [
#     {"Item": "Widget A", "Quantity": "2", "Unit Price": "$15.00", "Total": "$30.00"},
#     {"Item": "Service B", "Quantity": "1", "Unit Price": "$50.00", "Total": "$50.00"}
# ]

# Advanced usage (with bounding box)
pdf_source = PDFDataSource(
    file_path="invoices/invoice_001.pdf",
    page_number=0,
    table_strategy="text",
    bounding_box=(50, 100, 550, 700)  # Extract specific region
)

# Get schema
schema = pdf_source.get_schema()
# {"Item": <class 'str'>, "Quantity": <class 'str'>, "Unit Price": <class 'str'>, "Total": <class 'str'>}
```

**Table Strategies**:

| Strategy | Best For | Example Use Cases |
|----------|----------|-------------------|
| `lines` | Bordered tables | Invoices, financial reports, forms |
| `text` | Borderless tables | Plain text tables, simple lists |
| `mixed` | Partially bordered | Complex layouts, mixed formats |

---

#### CSVDataSource (Legacy Alias)

**Note**: `CSVDataSource` is a legacy alias for `FileDataSource`. Use `FileDataSource` for new code.

**Read CSV, JSON, and YAML files** (legacy interface).

```python
from extract_transform_platform.data_sources.file import CSVDataSource  # Legacy
from extract_transform_platform.data_sources.file import FileDataSource  # Preferred
```

**Constructor**:
```python
CSVDataSource(
    file_path: str,
    source_type: str = "csv"
)
```

**Parameters**:
- `file_path` (str): Path to file
- `source_type` (str, default="csv"): File format (`"csv"`, `"json"`, `"yaml"`, `"text"`)

**Methods**: Same as FileDataSource (see below)

---

#### FileDataSource

**Universal file parser for CSV, JSON, YAML, and text files**.
**Status**: Batch 1 complete (290 LOC platform + 30 LOC wrapper, 100% code reuse)

```python
from extract_transform_platform.data_sources.file import FileDataSource
```

**Constructor**:
```python
FileDataSource(
    file_path: str,
    source_type: str = "csv"
)
```

**Parameters**:
- `file_path` (str): Path to file (required)
- `source_type` (str, default="csv"): File format
  - `"csv"`: Comma-separated values (with header row)
  - `"json"`: JSON arrays of objects
  - `"yaml"`: YAML files (single document or list)
  - `"text"`: Plain text files (returns raw string)

**Methods**:

##### read()

```python
def read() -> List[Dict[str, Any]]:
    """
    Read file and return data as list of dictionaries.

    Returns:
        List[Dict[str, Any]]: Each row/object as a dictionary

    Raises:
        FileNotFoundError: If file not found
        ValueError: If invalid format or unsupported source_type
    """
```

##### get_schema()

```python
def get_schema() -> Dict[str, type]:
    """
    Get schema with field names and inferred types.

    Returns:
        Dict[str, type]: Field names mapped to Python types

    Type Inference:
        - int values → int
        - float values → float
        - string values → str
        - boolean values → bool
        - date strings → str (can be parsed as datetime)
    """
```

**Usage Example**:
```python
from extract_transform_platform.data_sources.file import FileDataSource

# CSV files
csv_source = FileDataSource(
    file_path="data/employees.csv",
    source_type="csv"
)
data = csv_source.read()
schema = csv_source.get_schema()

# JSON files
json_source = FileDataSource(
    file_path="data/api_response.json",
    source_type="json"
)
data = json_source.read()

# YAML files
yaml_source = FileDataSource(
    file_path="config/settings.yaml",
    source_type="yaml"
)
data = yaml_source.read()

# Plain text files
text_source = FileDataSource(
    file_path="logs/output.txt",
    source_type="text"
)
content = text_source.read()  # Returns str, not List[Dict]
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

#### APIDataSource

**Fetch data from REST APIs with authentication and rate limiting**.
**Status**: Batch 1 complete (239 LOC platform + 42 LOC wrapper, 100% code reuse)

```python
from extract_transform_platform.data_sources.web import APIDataSource
```

**Constructor**:
```python
APIDataSource(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    rate_limit: Optional[int] = None,
    cache_ttl: Optional[int] = None,
    timeout: int = 30
)
```

**Parameters**:
- `url` (str): API endpoint URL (required)
- `method` (str, default="GET"): HTTP method (GET, POST, PUT, DELETE, PATCH)
- `headers` (Optional[Dict], default=None): Request headers (auth, content-type, etc.)
- `params` (Optional[Dict], default=None): Query parameters (for GET requests)
- `data` (Optional[Dict], default=None): Request body (for POST/PUT requests)
- `rate_limit` (Optional[int], default=None): Max requests per second
- `cache_ttl` (Optional[int], default=None): Cache time-to-live in seconds
- `timeout` (int, default=30): Request timeout in seconds

**Methods**:

##### read()

```python
def read() -> List[Dict[str, Any]]:
    """
    Fetch data from API and return as list of dictionaries.

    Returns:
        List[Dict[str, Any]]: API response data

    Raises:
        requests.RequestException: If API request fails
        ValueError: If response is not valid JSON
        requests.Timeout: If request times out
    """
```

##### get_schema()

```python
def get_schema() -> Dict[str, type]:
    """
    Get schema with field names and inferred types from API response.

    Returns:
        Dict[str, type]: Field names mapped to Python types
    """
```

**Usage Example**:
```python
from extract_transform_platform.data_sources.web import APIDataSource
import os

# GET request with authentication
api_source = APIDataSource(
    url="https://api.example.com/users",
    method="GET",
    headers={"Authorization": f"Bearer {os.getenv('API_KEY')}"}
)

data = api_source.read()
schema = api_source.get_schema()

# POST request with data
api_source = APIDataSource(
    url="https://api.example.com/search",
    method="POST",
    headers={"Content-Type": "application/json"},
    data={"query": "employees", "limit": 100}
)

data = api_source.read()

# GET with query parameters and rate limiting
api_source = APIDataSource(
    url="https://api.example.com/users",
    method="GET",
    params={"page": 1, "limit": 50},
    headers={"Authorization": f"Bearer {os.getenv('API_KEY')}"},
    rate_limit=10,  # Max 10 requests per second
    cache_ttl=3600  # Cache for 1 hour
)

data = api_source.read()
```

**Features**:
- ✅ HTTP methods (GET, POST, PUT, DELETE, PATCH)
- ✅ Authentication (Bearer tokens, API keys, custom headers)
- ✅ Query parameters (GET requests)
- ✅ Request body (JSON, form data)
- ✅ Rate limiting (configurable requests/second)
- ✅ Response caching (file-based, configurable TTL)
- ✅ Automatic retry with exponential backoff
- ✅ Timeout handling
- ✅ Error handling with detailed messages

**Migration from EDGAR**:
```python
# ❌ OLD (EDGAR - still works with deprecation warning)
from edgar_analyzer.data_sources.api_source import APIDataSource

# ✅ NEW (Platform - preferred)
from extract_transform_platform.data_sources.web import APIDataSource
```

---

#### URLDataSource

**Simple HTTP GET requests with content-type detection**.
**Status**: Batch 1 complete (190 LOC platform + 29 LOC wrapper, 100% code reuse)

```python
from extract_transform_platform.data_sources.web import URLDataSource
```

**Constructor**:
```python
URLDataSource(
    url: str,
    timeout: int = 30
)
```

**Parameters**:
- `url` (str): URL to fetch (required)
- `timeout` (int, default=30): Request timeout in seconds

**Methods**:

##### read()

```python
def read() -> Union[List[Dict[str, Any]], str]:
    """
    Fetch data from URL with automatic content-type detection.

    Returns:
        Union[List[Dict[str, Any]], str]:
            - List[Dict] for JSON content
            - str for text content

    Raises:
        requests.RequestException: If request fails
        ValueError: If URL is invalid
        requests.Timeout: If request times out
    """
```

##### get_schema()

```python
def get_schema() -> Dict[str, type]:
    """
    Get schema for JSON responses (empty dict for text).

    Returns:
        Dict[str, type]: Field names mapped to types (JSON only)
    """
```

**Usage Example**:
```python
from extract_transform_platform.data_sources.web import URLDataSource

# Fetch JSON data (auto-detected)
url_source = URLDataSource(
    url="https://api.example.com/data.json"
)

data = url_source.read()  # Returns List[Dict[str, Any]]
schema = url_source.get_schema()

# Fetch plain text
text_source = URLDataSource(
    url="https://example.com/document.txt"
)

content = text_source.read()  # Returns str

# Fetch with custom timeout
url_source = URLDataSource(
    url="https://slow-api.example.com/data",
    timeout=60  # 60 seconds
)

data = url_source.read()
```

**Features**:
- ✅ Simple HTTP GET requests (no auth required)
- ✅ Automatic content-type detection (JSON, text)
- ✅ JSON parsing (returns List[Dict])
- ✅ Text content extraction (returns str)
- ✅ Error handling with detailed messages
- ✅ Timeout support

**When to Use URLDataSource vs APIDataSource**:
- **URLDataSource**: Simple GET requests, public APIs, no auth required
- **APIDataSource**: Complex requests, authentication, rate limiting, caching, retries

**Migration from EDGAR**:
```python
# ❌ OLD (EDGAR - N/A, new in Batch 1)
# URLDataSource did not exist in EDGAR

# ✅ NEW (Platform - use this)
from extract_transform_platform.data_sources.web import URLDataSource
```

---

#### JinaDataSource

**Scrape JS-heavy websites using Jina.ai API**.
**Status**: Batch 1 complete (240 LOC platform + 46 LOC wrapper, 100% code reuse + 1 bug fix)

```python
from extract_transform_platform.data_sources.web import JinaDataSource
```

**Constructor**:
```python
JinaDataSource(
    url: str,
    api_key: Optional[str] = None,
    timeout: int = 30
)
```

**Parameters**:
- `url` (str): Website URL to scrape (required)
- `api_key` (Optional[str], default=None): Jina.ai API key (optional, free tier available)
- `timeout` (int, default=30): Request timeout in seconds

**Methods**:

##### read()

```python
def read() -> Dict[str, Any]:
    """
    Scrape website with JavaScript execution and return structured data.

    Returns:
        Dict[str, Any]: Scraped content with keys:
            - 'content': Markdown-formatted main content
            - 'title': Page title
            - 'description': Page description
            - 'url': Final URL (after redirects)
            - 'publishedTime': Publication timestamp (if available)

    Raises:
        requests.RequestException: If scraping fails
        ValueError: If URL is invalid
        requests.Timeout: If request times out
    """
```

##### get_schema()

```python
def get_schema() -> Dict[str, type]:
    """
    Get schema of scraped content.

    Returns:
        Dict[str, type]: Field names mapped to types
            - 'content': str
            - 'title': str
            - 'description': str
            - 'url': str
            - 'publishedTime': str
    """
```

**Usage Example**:
```python
from extract_transform_platform.data_sources.web import JinaDataSource
import os

# With API key (recommended - higher rate limits)
jina_source = JinaDataSource(
    url="https://example.com/dynamic-content",
    api_key=os.getenv("JINA_API_KEY")
)

# Read scraped content
result = jina_source.read()
# {
#     'content': '# Page Title\n\nMain content...',
#     'title': 'Page Title',
#     'description': 'Page description',
#     'url': 'https://example.com/dynamic-content',
#     'publishedTime': '2024-01-15T10:30:00Z'
# }

# Free tier (no API key)
jina_free = JinaDataSource(
    url="https://example.com/spa-app"
    # No api_key = uses free tier (20 requests/hour)
)

data = jina_free.read()
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

**Rate Limits**:
- **Free tier** (no API key): 20 requests/hour
- **Free tier** (with API key): 200 requests/hour
- **Paid tier**: Higher limits (see Jina.ai pricing)

**Use Cases**:
- ✅ Single-page applications (React, Vue, Angular)
- ✅ Dynamic content loaded via JavaScript
- ✅ Interactive websites with AJAX
- ✅ Modern web frameworks
- ✅ Sites that don't work with traditional scrapers

**API Key Configuration**:
```bash
# Get free API key from https://jina.ai
export JINA_API_KEY="jina-xxxxxxxxxxxx"

# Or use .env file
echo "JINA_API_KEY=jina-xxxxxxxxxxxx" >> .env
```

**Migration from EDGAR**:
```python
# ❌ OLD (EDGAR - N/A, new in Batch 1)
# JinaDataSource did not exist in EDGAR

# ✅ NEW (Platform - use this)
from extract_transform_platform.data_sources.web import JinaDataSource
```

**See Also**: [Web Scraping Guide](../guides/WEB_SCRAPING.md) for detailed tutorials

---

## AI Integration

### `extract_transform_platform.ai`

AI-powered pattern detection and code generation via OpenRouter.

#### OpenRouterClient

**Client for OpenRouter API** with error handling and retry logic.

```python
from extract_transform_platform.ai import OpenRouterClient, OpenRouterConfig
```

**Constructor**:
```python
OpenRouterClient(config: OpenRouterConfig)
```

**Parameters**:
- `config` (OpenRouterConfig): OpenRouter configuration

**Methods**:

##### chat_completion()

```python
async def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Send chat completion request to OpenRouter.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use (overrides default)
        temperature: Temperature for generation (overrides default)
        max_tokens: Max tokens to generate (overrides default)

    Returns:
        Dict with 'content', 'model', 'usage' keys

    Raises:
        OpenRouterError: If API call fails
    """
```

**Usage Example**:
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
        {"role": "system", "content": "You are a data transformation expert."},
        {"role": "user", "content": "Analyze these patterns..."}
    ]
)

print(response["content"])
```

---

#### OpenRouterConfig

**Configuration for OpenRouter client**.

```python
from extract_transform_platform.ai import OpenRouterConfig

config = OpenRouterConfig(
    api_key: str,
    default_model: str = "anthropic/claude-3.5-sonnet",
    temperature: float = 0.3,
    max_tokens: int = 4000,
    site_url: Optional[str] = None,
    app_name: Optional[str] = None
)
```

**Parameters**:
- `api_key` (str): OpenRouter API key
- `default_model` (str, default="anthropic/claude-3.5-sonnet"): Default model
- `temperature` (float, default=0.3): Generation temperature (0.0-2.0)
- `max_tokens` (int, default=4000): Max tokens to generate
- `site_url` (Optional[str]): Site URL for tracking
- `app_name` (Optional[str]): App name for tracking

---

#### PromptTemplates

**Prompt templates for pattern detection**.

```python
from extract_transform_platform.ai import PromptTemplates

templates = PromptTemplates()
```

**Methods**:

##### detect_patterns()

```python
def detect_patterns(
    source_schema: Dict[str, Any],
    target_schema: Dict[str, Any],
    examples: List[Dict[str, Any]]
) -> str:
    """
    Generate prompt for pattern detection.

    Args:
        source_schema: Source data schema
        target_schema: Target data schema
        examples: List of transformation examples

    Returns:
        str: Formatted prompt for AI
    """
```

**Usage Example**:
```python
from extract_transform_platform.ai import PromptTemplates

templates = PromptTemplates()

prompt = templates.detect_patterns(
    source_schema={"employee_id": "str", "first_name": "str", "last_name": "str"},
    target_schema={"id": "str", "full_name": "str"},
    examples=[
        {
            "source": {"employee_id": "E1001", "first_name": "Alice", "last_name": "Johnson"},
            "target": {"id": "E1001", "full_name": "Alice Johnson"}
        }
    ]
)

# Use with OpenRouterClient
response = await client.chat_completion(
    messages=[{"role": "user", "content": prompt}]
)
```

---

## Schema Services (Batch 2 ✅)

### `extract_transform_platform.models.patterns`

Pattern data models for Example Parser system.

#### PatternType

**Enumeration of transformation pattern types**.

```python
from extract_transform_platform.models.patterns import PatternType

class PatternType(str, Enum):
    """Types of transformation patterns"""

    FIELD_MAPPING = "field_mapping"           # Direct field mapping
    CONCATENATION = "concatenation"           # String concatenation
    TYPE_CONVERSION = "type_conversion"       # Type conversions
    BOOLEAN_CONVERSION = "boolean_conversion" # Boolean normalization
    VALUE_MAPPING = "value_mapping"           # Discrete value mapping
    FIELD_EXTRACTION = "field_extraction"     # Substring extraction
    NESTED_ACCESS = "nested_access"           # Nested object access
    LIST_AGGREGATION = "list_aggregation"     # List operations
    CONDITIONAL = "conditional"               # Conditional logic
    DATE_PARSING = "date_parsing"             # Date/time parsing
    MATH_OPERATION = "math_operation"         # Mathematical operations
    STRING_FORMATTING = "string_formatting"   # String formatting
    DEFAULT_VALUE = "default_value"           # Default value handling
    CUSTOM = "custom"                         # Custom transformations
```

**Usage Example**:
```python
from extract_transform_platform.models.patterns import PatternType

# Check pattern type
if pattern.type == PatternType.FIELD_MAPPING:
    print("Direct field mapping pattern")
```

---

#### FieldTypeEnum

**Enumeration of field data types**.

```python
from extract_transform_platform.models.patterns import FieldTypeEnum

class FieldTypeEnum(str, Enum):
    """Field data types"""

    STRING = "string"       # String values
    INTEGER = "integer"     # Integer values
    FLOAT = "float"         # Float values
    DECIMAL = "decimal"     # Decimal values
    BOOLEAN = "boolean"     # Boolean values
    DATE = "date"           # Date values
    DATETIME = "datetime"   # DateTime values
    TIME = "time"           # Time values
    NULL = "null"           # Null values
    ARRAY = "array"         # Array/list values
    OBJECT = "object"       # Object/dict values
```

**Usage Example**:
```python
from extract_transform_platform.models.patterns import FieldTypeEnum

# Check field type
if field.type == FieldTypeEnum.INTEGER:
    print("Integer field")
```

---

#### Pattern

**Transformation pattern model**.

```python
from extract_transform_platform.models.patterns import Pattern

Pattern(
    type: PatternType,
    confidence: float,
    source_path: str,
    target_path: str,
    transformation: str,
    examples: List[Tuple[Any, Any]] = []
)
```

**Parameters**:
- `type` (PatternType): Pattern type
- `confidence` (float): Confidence score (0.0-1.0)
- `source_path` (str): Source field path (dot notation for nested)
- `target_path` (str): Target field path
- `transformation` (str): Human-readable transformation description
- `examples` (List[Tuple], default=[]): List of (input, output) value pairs

**Usage Example**:
```python
from extract_transform_platform.models.patterns import Pattern, PatternType

# Create pattern
pattern = Pattern(
    type=PatternType.FIELD_MAPPING,
    confidence=1.0,
    source_path="employee_id",
    target_path="id",
    transformation="Direct field rename",
    examples=[("E1001", "E1001"), ("E1002", "E1002")]
)

# Access properties
print(f"Type: {pattern.type}")
print(f"Confidence: {pattern.confidence}")
print(f"Source → Target: {pattern.source_path} → {pattern.target_path}")
```

---

#### SchemaField

**Schema field model**.

```python
from extract_transform_platform.models.patterns import SchemaField

SchemaField(
    name: str,
    type: FieldTypeEnum,
    required: bool = True,
    nullable: bool = False,
    path: Optional[str] = None
)
```

**Parameters**:
- `name` (str): Field name
- `type` (FieldTypeEnum): Field data type
- `required` (bool, default=True): Whether field is required
- `nullable` (bool, default=False): Whether field can be null
- `path` (Optional[str], default=None): Dot notation path (for nested fields)

**Usage Example**:
```python
from extract_transform_platform.models.patterns import SchemaField, FieldTypeEnum

# Create field
field = SchemaField(
    name="employee_id",
    type=FieldTypeEnum.STRING,
    required=True,
    nullable=False
)

# Nested field
nested_field = SchemaField(
    name="city",
    type=FieldTypeEnum.STRING,
    path="address.city",
    required=False,
    nullable=True
)
```

---

#### Schema

**Schema model for data structure**.

```python
from extract_transform_platform.models.patterns import Schema

Schema(
    fields: Dict[str, SchemaField]
)
```

**Parameters**:
- `fields` (Dict[str, SchemaField]): Mapping of field names to SchemaField objects

**Usage Example**:
```python
from extract_transform_platform.models.patterns import Schema, SchemaField, FieldTypeEnum

# Create schema
schema = Schema(
    fields={
        "id": SchemaField(name="id", type=FieldTypeEnum.STRING),
        "salary": SchemaField(name="salary", type=FieldTypeEnum.FLOAT)
    }
)

# Access fields
for field_name, field in schema.fields.items():
    print(f"{field_name}: {field.type.value}")
```

---

#### ParsedExamples

**Result model from example parsing**.

```python
from extract_transform_platform.models.patterns import ParsedExamples

ParsedExamples(
    input_schema: Schema,
    output_schema: Schema,
    patterns: List[Pattern],
    examples_count: int
)
```

**Parameters**:
- `input_schema` (Schema): Inferred input schema
- `output_schema` (Schema): Inferred output schema
- `patterns` (List[Pattern]): Detected transformation patterns
- `examples_count` (int): Number of examples analyzed

**Properties**:
- `high_confidence_patterns` - Patterns with confidence ≥0.9
- `medium_confidence_patterns` - Patterns with confidence 0.7-0.89
- `low_confidence_patterns` - Patterns with confidence <0.7

**Usage Example**:
```python
from extract_transform_platform.models.patterns import ParsedExamples

# Result from ExampleParser.parse_examples()
parsed = ParsedExamples(
    input_schema=input_schema,
    output_schema=output_schema,
    patterns=[pattern1, pattern2],
    examples_count=3
)

# Access high-confidence patterns
for pattern in parsed.high_confidence_patterns:
    print(f"{pattern.type}: {pattern.transformation}")
```

---

#### SchemaDifference

**Schema comparison difference model**.

```python
from extract_transform_platform.models.patterns import SchemaDifference

SchemaDifference(
    type: str,
    field_name: str,
    description: str,
    source_field: Optional[SchemaField] = None,
    target_field: Optional[SchemaField] = None
)
```

**Parameters**:
- `type` (str): Difference type (field_rename, type_change, added, removed)
- `field_name` (str): Field name
- `description` (str): Human-readable description
- `source_field` (Optional[SchemaField]): Source schema field (if applicable)
- `target_field` (Optional[SchemaField]): Target schema field (if applicable)

**Usage Example**:
```python
from extract_transform_platform.models.patterns import SchemaDifference

# From SchemaAnalyzer.compare_schemas()
differences = analyzer.compare_schemas(input_schema, output_schema)

for diff in differences:
    print(f"{diff.type}: {diff.description}")
```

---

### `extract_transform_platform.services.analysis`

Schema analysis and pattern extraction services.

#### SchemaAnalyzer

**Analyze and infer schemas from example data**.

```python
from extract_transform_platform.services.analysis import SchemaAnalyzer
```

**Constructor**:
```python
SchemaAnalyzer()
```

**Methods**:

##### infer_input_schema()

```python
def infer_input_schema(
    examples: List[Dict[str, Any]]
) -> Schema:
    """
    Infer input schema from examples.

    Args:
        examples: List of example dictionaries with 'input' keys

    Returns:
        Schema: Inferred input schema with field types

    Raises:
        ValueError: If examples list is empty
    """
```

##### infer_output_schema()

```python
def infer_output_schema(
    examples: List[Dict[str, Any]]
) -> Schema:
    """
    Infer output schema from examples.

    Args:
        examples: List of example dictionaries with 'output' keys

    Returns:
        Schema: Inferred output schema with field types

    Raises:
        ValueError: If examples list is empty
    """
```

##### compare_schemas()

```python
def compare_schemas(
    input_schema: Schema,
    output_schema: Schema
) -> List[SchemaDifference]:
    """
    Compare two schemas and return differences.

    Args:
        input_schema: Input data schema
        output_schema: Output data schema

    Returns:
        List[SchemaDifference]: List of schema differences

    Difference Types:
        - field_rename: Field name changed
        - type_change: Field type changed
        - added: Field added in output
        - removed: Field removed in output
    """
```

##### infer_field_type()

```python
def infer_field_type(
    value: Any
) -> FieldTypeEnum:
    """
    Infer field type from value.

    Args:
        value: Field value to analyze

    Returns:
        FieldTypeEnum: Inferred type

    Type Detection:
        - None → NULL
        - bool → BOOLEAN
        - int → INTEGER
        - float/Decimal → FLOAT/DECIMAL
        - str (date format) → DATE/DATETIME/TIME
        - str → STRING
        - list → ARRAY
        - dict → OBJECT
    """
```

**Usage Example**:
```python
from extract_transform_platform.services.analysis import SchemaAnalyzer

# Create analyzer
analyzer = SchemaAnalyzer()

# Infer schemas from examples
examples = [
    {
        "input": {"employee_id": "E1001", "salary": 95000},
        "output": {"id": "E1001", "annual_salary_usd": 95000.0}
    }
]

input_schema = analyzer.infer_input_schema(examples)
output_schema = analyzer.infer_output_schema(examples)

# Compare schemas
differences = analyzer.compare_schemas(input_schema, output_schema)
for diff in differences:
    print(f"{diff.type}: {diff.description}")
```

**Performance**: <100ms for 10 examples with 50 fields

---

#### ExampleParser

**Extract transformation patterns from input/output examples**.

```python
from extract_transform_platform.services.analysis import ExampleParser
```

**Constructor**:
```python
ExampleParser(
    schema_analyzer: SchemaAnalyzer
)
```

**Parameters**:
- `schema_analyzer` (SchemaAnalyzer): Schema analyzer instance

**Methods**:

##### parse_examples()

```python
def parse_examples(
    examples: List[ExampleConfig]
) -> ParsedExamples:
    """
    Parse examples and extract transformation patterns.

    Args:
        examples: List of ExampleConfig objects with input/output pairs

    Returns:
        ParsedExamples: Parsed result with schemas and patterns

    Raises:
        ValueError: If examples list is empty or invalid format

    Pattern Detection:
        - Analyzes input/output schemas
        - Detects 14 pattern types
        - Computes confidence scores (0.0-1.0)
        - Groups patterns by target field
    """
```

##### detect_pattern_type()

```python
def detect_pattern_type(
    source_field: SchemaField,
    target_field: SchemaField,
    examples: List[Tuple[Any, Any]]
) -> PatternType:
    """
    Detect pattern type from field comparison.

    Args:
        source_field: Source schema field
        target_field: Target schema field
        examples: List of (source_value, target_value) pairs

    Returns:
        PatternType: Detected pattern type

    Detection Logic:
        - FIELD_MAPPING: Direct field copy
        - CONCATENATION: Multiple fields combined
        - TYPE_CONVERSION: Type changed
        - BOOLEAN_CONVERSION: Yes/No → true/false
        - VALUE_MAPPING: Discrete value transformation
        - FIELD_EXTRACTION: Substring extracted
        - (and 8 more pattern types)
    """
```

##### calculate_confidence()

```python
def calculate_confidence(
    pattern: Pattern,
    examples: List[Tuple[Any, Any]]
) -> float:
    """
    Calculate confidence score for pattern.

    Args:
        pattern: Pattern to score
        examples: List of (source_value, target_value) pairs

    Returns:
        float: Confidence score (0.0-1.0)

    Scoring Factors:
        - Consistency across examples (weight: 0.6)
        - Type compatibility (weight: 0.2)
        - Pattern complexity (weight: 0.2)

    Thresholds:
        - ≥0.9: High confidence
        - 0.7-0.89: Medium confidence
        - <0.7: Low confidence
    """
```

**Usage Example**:
```python
from extract_transform_platform.services.analysis import (
    ExampleParser,
    SchemaAnalyzer
)
from edgar_analyzer.models.project_config import ExampleConfig

# Create analyzer and parser
analyzer = SchemaAnalyzer()
parser = ExampleParser(analyzer)

# Provide examples
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

# Parse examples
parsed = parser.parse_examples(examples)

# Access patterns
for pattern in parsed.high_confidence_patterns:
    print(f"{pattern.type}: {pattern.confidence:.2f}")
    print(f"  {pattern.source_path} → {pattern.target_path}")
```

**Performance**: <500ms for 10 examples with 50 fields

---

## Models

### `extract_transform_platform.models`

Data models for project configuration and transformation patterns.

#### ProjectConfig

**Project configuration model**.

```python
from extract_transform_platform.models import ProjectConfig

config = ProjectConfig(
    name: str,
    data_source: Dict[str, Any],
    examples: List[str],
    output_dir: Optional[str] = "output"
)
```

**Usage Example**:
```python
from extract_transform_platform.models import ProjectConfig

config = ProjectConfig(
    name="Employee Transform",
    data_source={
        "type": "excel",
        "config": {
            "file_path": "input/employees.xlsx",
            "sheet_name": 0,
            "header_row": 0
        }
    },
    examples=[
        "examples/row1.json",
        "examples/row2.json"
    ],
    output_dir="output"
)
```

---

#### TransformationPattern

**Transformation pattern model**.

```python
from extract_transform_platform.models import TransformationPattern

pattern = TransformationPattern(
    type: str,
    source_fields: List[str],
    target_field: str,
    operation: Optional[str] = None
)
```

**Pattern Types**:
- `"field_rename"`: Simple field renaming
- `"concatenation"`: String concatenation
- `"type_convert"`: Type conversion
- `"boolean"`: Boolean normalization
- `"value_mapping"`: Discrete value mapping
- `"field_extract"`: Substring extraction

**Usage Example**:
```python
from extract_transform_platform.models import TransformationPattern

# Field rename pattern
pattern = TransformationPattern(
    type="field_rename",
    source_fields=["employee_id"],
    target_field="id"
)

# Concatenation pattern
pattern = TransformationPattern(
    type="concatenation",
    source_fields=["first_name", "last_name"],
    target_field="full_name",
    operation="concat"
)
```

---

## Code Generation

### `extract_transform_platform.codegen`

Code generation and validation.

#### CodeGenerator

**Generate type-safe extraction code**.

```python
from extract_transform_platform.codegen import CodeGenerator

generator = CodeGenerator()
```

**Methods**:

##### generate_extractor()

```python
def generate_extractor(
    class_name: str,
    source_schema: Dict[str, type],
    target_schema: Dict[str, type],
    patterns: List[TransformationPattern]
) -> str:
    """
    Generate extractor class code.

    Returns:
        str: Generated Python code
    """
```

---

## Services

### `extract_transform_platform.services`

Shared services (caching, logging).

#### CacheService

**File-based caching service**.

```python
from extract_transform_platform.services import CacheService

cache = CacheService(cache_dir="data/cache")
```

---

## Utilities

### `extract_transform_platform.utils`

Utility functions.

#### RateLimiter

**Rate limiting for API calls**.

```python
from extract_transform_platform.utils import RateLimiter

limiter = RateLimiter(max_calls=10, period=60)
```

---

## Next Steps

- **Platform Usage Guide**: [PLATFORM_USAGE.md](../guides/PLATFORM_USAGE.md)
- **Migration Guide**: [PLATFORM_MIGRATION.md](../guides/PLATFORM_MIGRATION.md)
- **Excel Transform**: [EXCEL_FILE_TRANSFORM.md](../guides/EXCEL_FILE_TRANSFORM.md)
- **PDF Transform**: [PDF_FILE_TRANSFORM.md](../guides/PDF_FILE_TRANSFORM.md)
