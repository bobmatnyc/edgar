# Excel File Transform Work Path - Technical Analysis

**Research Date**: 2025-11-29
**Ticket**: 1M-319 - Phase 2 Core Platform Architecture
**Epic**: EDGAR → General-Purpose Extract & Transform Platform (edgar-e4cb3518b13e)
**Work Path**: File Transform (Priority: Excel → PDF → DOCX → PPTX)
**Researcher**: Claude Code Research Agent

---

## Executive Summary

Comprehensive analysis of the EDGAR codebase reveals **excellent foundation for Excel file parsing** with 70%+ code reuse potential. The platform already has:

- ✅ **pandas & openpyxl dependencies** (installed and actively used)
- ✅ **Schema analyzer** (adaptable to tabular data)
- ✅ **Example-driven approach** (proven with Weather API)
- ✅ **Data source abstraction layer** (FileDataSource supports CSV, extensible to Excel)
- ✅ **Project structure pattern** (`projects/{project_name}/` established)

**Key Recommendation**: Build `ExcelDataSource` as extension of existing `FileDataSource` with schema-aware parsing, enabling example-driven transformation similar to Weather API template.

**Timeline**: 2-3 days implementation for MVP proof-of-concept
**Risk Level**: LOW - All infrastructure exists, minimal new code required

---

## Table of Contents

1. [Current State Assessment](#1-current-state-assessment)
2. [Excel Capabilities Analysis](#2-excel-capabilities-analysis)
3. [Schema Analyzer Compatibility](#3-schema-analyzer-compatibility)
4. [Example-Driven Approach](#4-example-driven-approach)
5. [Technical Architecture](#5-technical-architecture)
6. [Proof-of-Concept Specification](#6-proof-of-concept-specification)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Risk Analysis](#8-risk-analysis)

---

## 1. Current State Assessment

### 1.1 Existing Excel Dependencies

**From `pyproject.toml`**:
```toml
dependencies = [
    "pandas>=2.0.0",      # ✅ Excel reading/writing
    "openpyxl>=3.1.0",    # ✅ Excel file manipulation
    ...
]
```

**Status**: ✅ Both libraries installed and actively used

### 1.2 Current Excel Usage

**File**: `src/edgar_analyzer/services/report_service.py`
```python
# Lines 8-12: Excel writing with openpyxl
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

# Lines 74-110: Excel export functionality
async def export_to_excel(self, report: AnalysisReport, filepath: str) -> None:
    """Export report to Excel file."""
    df = self._create_report_dataframe(report)
    wb = Workbook()
    # ... styling and formatting
```

**Usage Pattern**:
- DataFrame creation from structured data
- Excel workbook generation with styling
- Column auto-sizing and formatting
- Multiple services use pandas DataFrames (9 files, 29 occurrences)

**Insight**: Platform already has sophisticated Excel **writing** capabilities. Need to add Excel **reading** with schema inference.

### 1.3 Data Source Abstraction Layer

**File**: `src/edgar_analyzer/data_sources/file_source.py`

**Current Support**:
- ✅ JSON files (`.json`)
- ✅ YAML files (`.yml`, `.yaml`)
- ✅ CSV files (`.csv`) - uses pandas
- ✅ Text files (`.txt`, others)

**CSV Parsing Pattern** (lines 186-225):
```python
def _parse_csv(self, content: str) -> Dict[str, Any]:
    """Parse CSV file content using pandas."""
    import pandas as pd
    df = pd.read_csv(io.StringIO(content))
    rows = df.to_dict(orient="records")

    return {
        "rows": rows,
        "row_count": len(rows),
        "columns": list(df.columns),
        "file_path": str(self.file_path),
    }
```

**Insight**: Existing `_parse_csv()` provides blueprint for `_parse_excel()` - similar structure expected.

---

## 2. Excel Capabilities Analysis

### 2.1 Pandas Excel Reading

**Available Methods**:
```python
import pandas as pd

# Single sheet
df = pd.read_excel("file.xlsx", sheet_name="Sheet1")

# All sheets
sheets = pd.read_excel("file.xlsx", sheet_name=None)  # Returns dict

# Specific range
df = pd.read_excel("file.xlsx", usecols="A:D", nrows=100)

# Header detection
df = pd.read_excel("file.xlsx", header=0)  # Auto-detect headers
```

**Features**:
- Auto-detects data types (int, float, datetime, string)
- Handles merged cells (with limitations)
- Supports multi-index headers
- Built-in null handling
- Date parsing with `parse_dates` parameter

### 2.2 OpenpyxI Direct Access

**For advanced scenarios**:
```python
from openpyxl import load_workbook

wb = load_workbook("file.xlsx", data_only=True)
ws = wb["Sheet1"]

# Cell-level access
value = ws["A1"].value
formula = ws["A1"].formula
style = ws["A1"].font.bold

# Merged cells detection
merged_ranges = ws.merged_cells.ranges
```

**Use Cases**:
- Complex formatting detection
- Formula extraction
- Merged cell handling
- Sheet structure analysis

### 2.3 Comparison: Pandas vs. OpenpyxI

| Feature | Pandas | OpenpyxI | Recommendation |
|---------|--------|----------|----------------|
| **Read speed** | Fast | Moderate | Pandas for data |
| **Data types** | Auto-detect | Manual | Pandas |
| **Formatting** | Limited | Full access | OpenpyxI for styles |
| **Large files** | Memory-intensive | Streaming mode | OpenpyxI for >50MB |
| **Schema inference** | Built-in | Manual | Pandas |
| **Multi-sheet** | Simple API | Manual iteration | Pandas |

**Recommendation**:
- **Phase 1 MVP**: Use pandas for data extraction (simple, fast, type-aware)
- **Phase 2 Enhancement**: Add openpyxl for formatting/structure detection

---

## 3. Schema Analyzer Compatibility

### 3.1 Current Schema Analyzer Design

**File**: `src/edgar_analyzer/services/schema_analyzer.py`

**Core Method**:
```python
def infer_schema(self, examples: List[Dict[str, Any]], is_input: bool = True) -> Schema:
    """Infer schema from a list of example dictionaries."""
    # Extract all fields from all examples
    all_fields: Dict[str, List[Any]] = {}
    for example in examples:
        self._extract_fields(example, "", all_fields)  # Recursive extraction

    # Build schema fields
    fields: List[SchemaField] = []
    for path, values in all_fields.items():
        field = self._analyze_field(path, values, len(examples))
        fields.append(field)
```

**Key Capabilities**:
- ✅ **Nested structure support** (dot notation: `main.temp`)
- ✅ **Array handling** (`weather[0].description`)
- ✅ **Type inference** (11 types: str, int, float, date, datetime, bool, etc.)
- ✅ **Null tracking** (nullable field detection)
- ✅ **Sample values** (up to 3 representative values)
- ✅ **Field rename detection** (Jaccard similarity ≥50%)

### 3.2 Excel → Schema Mapping

**Excel Structure**:
```
| Column A  | Column B      | Column C        |
|-----------|---------------|-----------------|
| Name      | Age           | Registration    |
|-----------|---------------|-----------------|
| Alice     | 25            | 2023-01-15      |
| Bob       | 32            | 2023-02-20      |
```

**Converted to Dict** (via pandas):
```python
[
    {"Name": "Alice", "Age": 25, "Registration": "2023-01-15"},
    {"Name": "Bob", "Age": 32, "Registration": "2023-02-20"}
]
```

**Schema Inference Result**:
```python
Schema(
    fields=[
        SchemaField(path="Name", field_type=FieldTypeEnum.STRING, required=True),
        SchemaField(path="Age", field_type=FieldTypeEnum.INTEGER, required=True),
        SchemaField(path="Registration", field_type=FieldTypeEnum.DATE, required=True)
    ],
    is_nested=False,
    has_arrays=False
)
```

**Insight**: Schema analyzer already works with flat dictionaries - **Excel rows convert perfectly**.

### 3.3 Nested Excel Structures

**Excel with hierarchical headers**:
```
|           | Contact Info            |
| Name      | Email         | Phone   |
|-----------|---------------|---------|
| Alice     | a@ex.com      | 555-01  |
```

**Pandas handling**:
```python
# Multi-index columns
df = pd.read_excel("file.xlsx", header=[0, 1])

# Flatten to dot notation
df.columns = ['_'.join(col).strip() for col in df.columns.values]
# Result: ["Name", "Contact Info_Email", "Contact Info_Phone"]
```

**Schema analyzer compatibility**: ✅ Works with flattened column names

### 3.4 Recommended Enhancements

**For Excel-specific features**:

1. **Column Mapping Detection**:
```python
# Detect if Excel column names match expected schema
def detect_column_mapping(excel_df: pd.DataFrame, target_schema: Schema) -> Dict[str, str]:
    """Map Excel columns to schema fields using fuzzy matching."""
    # e.g., "emp_name" → "employee_name" (80% similarity)
```

2. **Data Type Hints**:
```python
# Use Excel number formats as type hints
# Currency format ($1,234.56) → Decimal
# Date format (MM/DD/YYYY) → Date
# Percentage format (45.2%) → Float
```

3. **Range Detection**:
```python
# Auto-detect data region (skip headers, footers)
def detect_data_range(ws: Worksheet) -> Tuple[int, int, int, int]:
    """Returns (start_row, start_col, end_row, end_col)"""
```

**Priority**: Phase 2 (MVP uses basic pandas schema inference)

---

## 4. Example-Driven Approach

### 4.1 Weather API Template Analysis

**File**: `projects/weather_api/project.yaml`

**Structure**:
```yaml
project:
  name: weather_api_extractor
  description: Extract current weather data from OpenWeatherMap API

data_sources:
  - type: api
    endpoint: https://api.openweathermap.org/data/2.5/weather
    auth:
      type: api_key
      key: ${OPENWEATHER_API_KEY}

examples:
  - input:
      coord: {lon: -0.1257, lat: 51.5085}
      weather: [{id: 500, main: "Rain", description: "light rain"}]
      main: {temp: 15.5, feels_like: 14.2, humidity: 72}
    output:
      city: London
      temperature_c: 15.5
      humidity_percent: 72
      conditions: light rain
    description: "Rainy temperate climate - demonstrates nested field extraction"
```

**Key Pattern**: Input/output pairs teach AI how to transform data

### 4.2 Excel Example Structure

**Proposed `project.yaml` for Excel**:
```yaml
project:
  name: employee_roster_extractor
  description: Extract employee data from HR Excel spreadsheets

data_sources:
  - type: excel
    file_path: examples/hr_roster.xlsx
    sheet_name: "Employees"  # Optional, defaults to first sheet
    header_row: 0            # Row index for headers
    data_start_row: 1        # First row of actual data

    # Advanced options (Phase 2)
    skip_empty_rows: true
    detect_merged_cells: false
    date_columns: ["hire_date", "birth_date"]

examples:
  # Example 1: Input is Excel row, output is structured JSON
  - input:
      # Raw Excel row data (as pandas would read it)
      employee_id: "E1001"
      first_name: "Alice"
      last_name: "Johnson"
      department: "Engineering"
      hire_date: "2020-03-15"
      salary: 95000
      is_manager: "Yes"
    output:
      # Transformed output
      id: "E1001"
      full_name: "Alice Johnson"
      dept: "Engineering"
      hired: "2020-03-15"
      annual_salary_usd: 95000.0
      manager: true
    description: "Engineering employee - demonstrates name concatenation and boolean conversion"

  # Example 2: Different department
  - input:
      employee_id: "M2005"
      first_name: "Bob"
      last_name: "Smith"
      department: "Marketing"
      hire_date: "2019-07-22"
      salary: 78000
      is_manager: "No"
    output:
      id: "M2005"
      full_name: "Bob Smith"
      dept: "Marketing"
      hired: "2019-07-22"
      annual_salary_usd: 78000.0
      manager: false
    description: "Marketing employee - demonstrates consistent transformation"

validation:
  required_fields:
    - id
    - full_name
    - dept

  field_types:
    id: str
    full_name: str
    dept: str
    hired: str  # ISO date format
    annual_salary_usd: float
    manager: bool
```

### 4.3 Example Storage Pattern

**Directory Structure**:
```
projects/employee_roster/
├── project.yaml              # Project configuration
├── examples/
│   ├── hr_roster.xlsx        # Source Excel file
│   ├── example_1.json        # Individual example (optional)
│   └── example_2.json        # Individual example (optional)
├── generated/
│   └── employee_roster_extractor/
│       ├── extractor.py      # Generated extractor code
│       ├── models.py         # Pydantic models
│       └── test_extractor.py # Generated tests
└── README.md                 # Project documentation
```

**Pattern**: Same as Weather API (`projects/weather_api/` structure)

### 4.4 Example ID Pattern

**From Weather API** (`projects/weather_api/examples/london.json`):
```json
{
  "example_id": "example_1",
  "input": { ... },
  "output": { ... },
  "description": "Rainy temperate climate - demonstrates nested field extraction"
}
```

**For Excel**:
```json
{
  "example_id": "row_1_alice_johnson",
  "input": {
    "employee_id": "E1001",
    "first_name": "Alice",
    ...
  },
  "output": {
    "id": "E1001",
    "full_name": "Alice Johnson",
    ...
  },
  "description": "Engineering employee with manager status"
}
```

**Pattern**: `{source}_{identifier}_{human_readable}` (e.g., `row_1_alice_johnson`)

---

## 5. Technical Architecture

### 5.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interaction                        │
│  edgar-cli create-project employee_roster --source excel   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                   Project Manager                           │
│  - Creates projects/{name}/ directory                       │
│  - Generates project.yaml template                          │
│  - Validates configuration                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                  ExcelDataSource                            │
│  File: src/edgar_analyzer/data_sources/excel_source.py     │
│                                                             │
│  Methods:                                                   │
│  - fetch() → List[Dict[str, Any]]                          │
│  - parse_sheet(sheet_name) → DataFrame                     │
│  - infer_header_row() → int                                │
│  - detect_data_region() → Tuple[int, int]                  │
│                                                             │
│  Dependencies:                                              │
│  - pandas.read_excel()                                      │
│  - openpyxl (via pandas engine)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                  SchemaAnalyzer                             │
│  File: src/edgar_analyzer/services/schema_analyzer.py      │
│                                                             │
│  Methods:                                                   │
│  - infer_schema(examples: List[Dict]) → Schema             │
│  - compare_schemas(input, output) → List[SchemaDifference] │
│                                                             │
│  Input: List[Dict] from Excel rows                         │
│  Output: Schema with field types, nullability, nesting     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                  ExampleParser                              │
│  File: src/edgar_analyzer/services/example_parser.py       │
│                                                             │
│  Methods:                                                   │
│  - parse_examples(examples) → ParsedExamples               │
│  - identify_patterns(examples) → List[Pattern]             │
│                                                             │
│  Detects:                                                   │
│  - Field mappings (employee_id → id)                       │
│  - String concatenation (first_name + last_name)           │
│  - Type conversions ("Yes" → true)                         │
│  - Calculations (optional)                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                  PromptGenerator                            │
│  File: src/edgar_analyzer/services/prompt_generator.py     │
│                                                             │
│  Generates Sonnet 4.5 prompts including:                   │
│  - Input/output schemas                                     │
│  - Transformation patterns                                  │
│  - Example pairs                                            │
│  - Validation rules                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                  CodeGenerator                              │
│  File: src/edgar_analyzer/services/code_generator.py       │
│                                                             │
│  Uses Sonnet 4.5 via OpenRouter to generate:              │
│  - extractor.py (extraction logic)                         │
│  - models.py (Pydantic models)                             │
│  - test_extractor.py (validation tests)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                  Generated Code                             │
│  Directory: projects/{name}/generated/{name}_extractor/    │
│                                                             │
│  Files:                                                     │
│  - extractor.py                                             │
│  - models.py                                                │
│  - test_extractor.py                                        │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 ExcelDataSource Design

**File**: `src/edgar_analyzer/data_sources/excel_source.py` (NEW)

```python
"""
Excel Data Source

Extends FileDataSource to support Excel files (.xlsx, .xls) with:
- Multi-sheet support
- Header detection
- Type inference
- Schema-aware parsing
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from .base import BaseDataSource

logger = logging.getLogger(__name__)


class ExcelDataSource(BaseDataSource):
    """Excel file data source with schema-aware parsing.

    Features:
    - Single or multi-sheet reading
    - Auto-header detection
    - Type inference (int, float, datetime, bool, str)
    - Null handling
    - Memory-efficient chunked reading (for large files)

    Example:
        # Single sheet
        excel = ExcelDataSource(
            file_path=Path("data/employees.xlsx"),
            sheet_name="Employees"
        )
        data = await excel.fetch()
        rows = data['rows']  # List[Dict[str, Any]]

        # All sheets
        excel = ExcelDataSource(
            file_path=Path("data/workbook.xlsx"),
            sheet_name=None  # Read all sheets
        )
        data = await excel.fetch()
        for sheet_name, rows in data['sheets'].items():
            print(f"{sheet_name}: {len(rows)} rows")
    """

    def __init__(
        self,
        file_path: Path,
        sheet_name: Optional[Union[str, int, List[str]]] = 0,
        header_row: int = 0,
        data_start_row: Optional[int] = None,
        usecols: Optional[str] = None,
        dtype: Optional[Dict[str, type]] = None,
        parse_dates: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize Excel data source.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name, index, or None for all sheets
            header_row: Row index for column headers (0-indexed)
            data_start_row: First row of actual data (defaults to header_row + 1)
            usecols: Column range to read (e.g., "A:E" or "A,C,E:G")
            dtype: Dict of column names to data types
            parse_dates: List of column names to parse as dates
            **kwargs: Additional arguments passed to BaseDataSource
        """
        # No caching for local files
        kwargs["cache_enabled"] = False
        kwargs["rate_limit_per_minute"] = 9999
        kwargs["max_retries"] = 0

        super().__init__(**kwargs)

        self.file_path = Path(file_path)
        self.sheet_name = sheet_name
        self.header_row = header_row
        self.data_start_row = data_start_row or (header_row + 1)
        self.usecols = usecols
        self.dtype = dtype
        self.parse_dates = parse_dates or []

        logger.info(f"Initialized ExcelDataSource for {self.file_path}")

    async def fetch(self, **kwargs) -> Dict[str, Any]:
        """Read and parse Excel file.

        Returns:
            Dictionary containing:
            - rows: List[Dict] (single sheet mode)
            - sheets: Dict[str, List[Dict]] (multi-sheet mode)
            - metadata: File info, column types, etc.
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")

        logger.debug(f"Reading Excel file: {self.file_path}")

        # Read Excel file
        if self.sheet_name is None:
            # Multi-sheet mode
            return await self._fetch_all_sheets()
        else:
            # Single sheet mode
            return await self._fetch_single_sheet()

    async def _fetch_single_sheet(self) -> Dict[str, Any]:
        """Fetch data from single sheet."""
        df = pd.read_excel(
            self.file_path,
            sheet_name=self.sheet_name,
            header=self.header_row,
            skiprows=None if self.data_start_row == self.header_row + 1 else range(self.header_row + 1, self.data_start_row),
            usecols=self.usecols,
            dtype=self.dtype,
            parse_dates=self.parse_dates,
            engine="openpyxl"
        )

        # Convert to list of dicts
        rows = df.to_dict(orient="records")

        # Infer types from DataFrame
        column_types = {col: str(dtype) for col, dtype in df.dtypes.items()}

        logger.debug(
            f"Parsed Excel sheet: {self.sheet_name} "
            f"({len(rows)} rows, {len(df.columns)} columns)"
        )

        return {
            "rows": rows,
            "row_count": len(rows),
            "columns": list(df.columns),
            "column_types": column_types,
            "sheet_name": self.sheet_name,
            "file_path": str(self.file_path),
        }

    async def _fetch_all_sheets(self) -> Dict[str, Any]:
        """Fetch data from all sheets."""
        # Read all sheets as dict
        sheet_dict = pd.read_excel(
            self.file_path,
            sheet_name=None,  # Read all sheets
            header=self.header_row,
            engine="openpyxl"
        )

        # Convert each sheet to list of dicts
        sheets = {}
        total_rows = 0

        for sheet_name, df in sheet_dict.items():
            rows = df.to_dict(orient="records")
            sheets[sheet_name] = {
                "rows": rows,
                "row_count": len(rows),
                "columns": list(df.columns),
                "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            total_rows += len(rows)

        logger.debug(
            f"Parsed Excel workbook: {len(sheets)} sheets, {total_rows} total rows"
        )

        return {
            "sheets": sheets,
            "sheet_count": len(sheets),
            "sheet_names": list(sheets.keys()),
            "total_rows": total_rows,
            "file_path": str(self.file_path),
        }

    async def validate_config(self) -> bool:
        """Validate Excel file exists and is readable."""
        if not self.file_path.exists():
            logger.error(f"Excel file not found: {self.file_path}")
            return False

        if self.file_path.suffix.lower() not in [".xlsx", ".xls"]:
            logger.error(f"Invalid Excel file extension: {self.file_path.suffix}")
            return False

        # Test read
        try:
            pd.read_excel(self.file_path, sheet_name=self.sheet_name, nrows=0, engine="openpyxl")
            logger.debug(f"Excel file validation passed: {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Excel file validation failed: {e}")
            return False

    def get_cache_key(self, **kwargs) -> str:
        """Generate cache key (not used for local files)."""
        return f"excel:{self.file_path}:{self.sheet_name}"
```

**LOC Estimate**: ~250 lines (including docstrings)

### 5.3 Integration with Existing Services

**No changes required**:
- ✅ SchemaAnalyzer: Works with `List[Dict]` - Excel rows fit perfectly
- ✅ ExampleParser: Agnostic to data source
- ✅ PromptGenerator: Uses ParsedExamples (format-independent)
- ✅ CodeGenerator: Uses prompts (no knowledge of Excel)

**Minor enhancement** (optional, Phase 2):
- `FileDataSource._parse_excel()` method to handle `.xlsx` extension
- Register `ExcelDataSource` in data source factory

### 5.4 Dependency Injection Container

**File**: `src/edgar_analyzer/config/container.py`

**Add Excel data source provider**:
```python
from edgar_analyzer.data_sources.excel_source import ExcelDataSource

class Container(containers.DeclarativeContainer):
    # ... existing providers ...

    excel_data_source = providers.Factory(
        ExcelDataSource,
        # Configuration from project.yaml
    )
```

---

## 6. Proof-of-Concept Specification

### 6.1 Minimum Viable Feature Set

**Goal**: Demonstrate Excel → JSON transformation using example-driven approach

**Features**:
1. ✅ Read single-sheet Excel file
2. ✅ Infer schema from Excel columns
3. ✅ Transform rows using 2-3 examples
4. ✅ Generate extractor code with Sonnet 4.5
5. ✅ Validate output against examples

**Out of Scope (Phase 1)**:
- ❌ Multi-sheet support (Phase 2)
- ❌ Merged cell handling (Phase 2)
- ❌ Formula extraction (Phase 2)
- ❌ Complex formatting detection (Phase 2)
- ❌ Large file streaming (Phase 2, if needed)

### 6.2 Test Excel File Structure

**File**: `projects/employee_roster/examples/hr_roster.xlsx`

**Sheet 1: "Employees"**
```
| employee_id | first_name | last_name | department  | hire_date  | salary | is_manager |
|-------------|------------|-----------|-------------|------------|--------|------------|
| E1001       | Alice      | Johnson   | Engineering | 2020-03-15 | 95000  | Yes        |
| E1002       | Bob        | Smith     | Marketing   | 2019-07-22 | 78000  | No         |
| M2005       | Carol      | Davis     | Engineering | 2021-01-10 | 105000 | Yes        |
| S3010       | David      | Wilson    | Sales       | 2022-05-18 | 82000  | No         |
```

**Characteristics**:
- **Simple structure**: Flat table, no nesting
- **Data types**: String, int, float, date, boolean (as text)
- **Transformations**: String concat, boolean conversion, field rename
- **Size**: 4 rows (minimal for pattern detection)

### 6.3 Expected Transformations

**Pattern 1: Field Mapping**
```python
employee_id → id  # Direct copy
department → dept  # Field rename
hire_date → hired  # Field rename
salary → annual_salary_usd  # Field rename + type ensure (float)
```

**Pattern 2: String Concatenation**
```python
first_name + " " + last_name → full_name
# "Alice" + " " + "Johnson" → "Alice Johnson"
```

**Pattern 3: Boolean Conversion**
```python
is_manager ("Yes" | "No") → manager (True | False)
# "Yes" → True
# "No" → False
```

### 6.4 Success Criteria

**Functional**:
1. ✅ ExcelDataSource reads `hr_roster.xlsx` successfully
2. ✅ Returns 4 rows as `List[Dict[str, Any]]`
3. ✅ SchemaAnalyzer infers correct types (str, int, date)
4. ✅ ExampleParser detects 3 transformation patterns
5. ✅ Generated `extractor.py` produces correct output for all 4 rows
6. ✅ Generated tests pass (100% pass rate)

**Non-Functional**:
1. ✅ Reads Excel file in <100ms
2. ✅ Schema inference in <50ms
3. ✅ Code generation in <5 seconds (Sonnet 4.5 API call)
4. ✅ Total end-to-end time: <10 seconds

**Quality**:
1. ✅ Generated code passes mypy type checking
2. ✅ Generated code passes black formatting
3. ✅ Generated tests have 100% coverage
4. ✅ No manual code edits required

### 6.5 File Paths and Organization

**Project Directory**:
```
projects/employee_roster/
├── project.yaml                      # Configuration (NEW)
├── examples/
│   ├── hr_roster.xlsx                # Source Excel (NEW)
│   ├── example_1.json                # Generated from row 1
│   └── example_2.json                # Generated from row 2
├── generated/
│   └── employee_roster_extractor/
│       ├── extractor.py              # Generated by Sonnet 4.5
│       ├── models.py                 # Generated Pydantic models
│       └── test_extractor.py         # Generated tests
└── README.md                         # Auto-generated docs
```

**External Artifacts Directory** (Phase 2):
```
{EXTERNAL_ARTIFACTS_DIR}/
└── employee_roster/
    ├── hr_roster.xlsx                # Original Excel file
    └── output/
        └── employees.json            # Extracted data
```

**Note**: Phase 1 MVP uses `projects/` directory. Phase 2 moves artifacts external.

---

## 7. Implementation Roadmap

### 7.1 Phase 1: Basic Excel Parsing (MVP)

**Duration**: 2 days
**Goal**: Prove Excel → JSON transformation works

**Tasks**:
1. **Create ExcelDataSource** (4 hours)
   - Implement `excel_source.py`
   - Add to data sources package
   - Write unit tests

2. **Test Schema Analyzer with Excel** (2 hours)
   - Create test Excel files
   - Verify type inference
   - Validate pattern detection

3. **Update Project Templates** (2 hours)
   - Add Excel data source type to `project.yaml` schema
   - Create Excel project template
   - Update validation rules

4. **Proof-of-Concept Project** (8 hours)
   - Create `employee_roster` project
   - Write 3 example transformations
   - Generate extractor code
   - Validate output

5. **Documentation** (2 hours)
   - Update `DATA_SOURCE_ABSTRACTION_LAYER.md`
   - Create Excel-specific guide
   - Add to Phase 2 completion report

**Deliverables**:
- ✅ `ExcelDataSource` class (250 LOC)
- ✅ Unit tests (200 LOC)
- ✅ Working employee_roster PoC
- ✅ Documentation updates

### 7.2 Phase 2: Multi-Sheet Support

**Duration**: 1 day
**Goal**: Handle workbooks with multiple sheets

**Tasks**:
1. **Multi-Sheet Fetching** (2 hours)
   - Implement `fetch_all_sheets()`
   - Return dict of sheets
   - Update schema analyzer for multi-schema

2. **Sheet Selection** (2 hours)
   - Add sheet_name parameter to project.yaml
   - Support sheet index or name
   - Handle missing sheets gracefully

3. **Cross-Sheet Examples** (4 hours)
   - Support examples from different sheets
   - Update example parser for multi-source
   - Test with multi-sheet workbook

**Deliverables**:
- ✅ Multi-sheet support in ExcelDataSource
- ✅ Updated project.yaml schema
- ✅ Multi-sheet PoC project

### 7.3 Phase 3: Advanced Excel Features

**Duration**: 2 days
**Goal**: Handle complex Excel structures

**Tasks**:
1. **Merged Cell Handling** (4 hours)
   - Use openpyxl to detect merged ranges
   - Unmerge or propagate values
   - Update schema analyzer

2. **Header Detection** (3 hours)
   - Auto-detect header row
   - Support multi-row headers
   - Flatten to dot notation

3. **Formula Extraction** (4 hours)
   - Read formula strings (openpyxl)
   - Store in metadata
   - Optional: evaluate formulas

4. **Large File Optimization** (5 hours)
   - Implement chunked reading
   - Memory profiling
   - Streaming mode for >50MB files

**Deliverables**:
- ✅ Advanced ExcelDataSource features
- ✅ Performance benchmarks
- ✅ Updated documentation

### 7.4 Total Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Basic Excel | 2 days | None (ready now) |
| Phase 2: Multi-Sheet | 1 day | Phase 1 complete |
| Phase 3: Advanced | 2 days | Phase 2 complete |
| **Total** | **5 days** | Sequential |

**Critical Path**: Phase 1 → Phase 2 → Phase 3
**Parallel Opportunities**: Documentation can be written alongside development

---

## 8. Risk Analysis

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Pandas type inference failures** | Medium | Low | Provide dtype hints in project.yaml |
| **Openpyxl compatibility issues** | Low | Medium | Already used in codebase (report_service.py) |
| **Large file memory issues** | Medium | Medium | Implement chunked reading in Phase 3 |
| **Schema analyzer edge cases** | Low | Low | Existing unit tests cover most scenarios |
| **Merged cell confusion** | Medium | Low | Phase 3 feature, not MVP blocker |

**Overall Risk**: **LOW** - All dependencies proven, minimal new code

### 8.2 Integration Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **DI container conflicts** | Low | Low | Follow existing data source pattern |
| **Project YAML schema changes** | Low | Medium | Version schema, provide migration |
| **Breaking existing CSV support** | Very Low | High | ExcelDataSource is separate class |
| **Performance regression** | Low | Low | Add benchmarks, monitor CI |

**Overall Risk**: **LOW** - Non-breaking additive changes

### 8.3 User Experience Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Confusing multi-sheet UX** | Medium | Medium | Clear documentation, examples |
| **Unexpected type conversions** | Medium | Low | Show type inference in debug mode |
| **Complex Excel not supported** | High | Low | Document limitations, Phase 3 roadmap |
| **Error messages unclear** | Medium | Low | Add detailed logging, helpful errors |

**Overall Risk**: **MEDIUM** - Requires good documentation and examples

### 8.4 Timeline Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Phase 1 takes longer than 2 days** | Low | Low | 70% code reuse, proven patterns |
| **Sonnet 4.5 API issues** | Low | Medium | Already integrated, fallback to local testing |
| **Testing reveals gaps** | Medium | Low | Iterative testing, early validation |
| **Documentation takes longer** | Low | Low | Templates exist, copy from Weather API |

**Overall Risk**: **LOW** - Conservative estimates with buffer

---

## 9. Recommendations

### 9.1 Immediate Actions (Next 48 Hours)

1. **Create ExcelDataSource** (Day 1)
   - Copy `file_source.py` as template
   - Implement `_parse_excel()` method
   - Add to `__init__.py` exports

2. **Validate with Test File** (Day 1)
   - Create simple test Excel (3 columns, 5 rows)
   - Write unit test for fetch()
   - Verify schema inference

3. **Build Employee Roster PoC** (Day 2)
   - Create project structure
   - Write 3 examples
   - Generate code with Sonnet 4.5
   - Run tests, validate output

### 9.2 Medium-Term Actions (Next 2 Weeks)

1. **Implement Multi-Sheet Support** (Week 1)
   - Handle `sheet_name=None` case
   - Update project.yaml schema
   - Create multi-sheet example

2. **Documentation & Examples** (Week 1-2)
   - Write Excel-specific guide
   - Create 3 example projects
   - Update Phase 2 completion report

3. **Advanced Features** (Week 2)
   - Merged cell handling
   - Header auto-detection
   - Performance optimization

### 9.3 Best Practices

**For MVP**:
- ✅ Keep it simple: Single sheet, flat structure
- ✅ Use pandas defaults: Auto type inference
- ✅ Leverage existing code: 70% reuse target
- ✅ Document limitations: Set expectations

**For Production**:
- ✅ Add comprehensive error handling
- ✅ Validate Excel structure before parsing
- ✅ Provide helpful error messages
- ✅ Include debugging tools (show inferred types)

---

## 10. Conclusion

The EDGAR platform has **exceptional foundation for Excel parsing**:

✅ **Dependencies Ready**: pandas and openpyxl installed and battle-tested
✅ **Pattern Proven**: CSV parsing provides blueprint for Excel
✅ **Schema Analyzer Compatible**: Works perfectly with tabular data
✅ **Example-Driven Works**: Weather API demonstrates pattern
✅ **Infrastructure Exists**: Data source abstraction, DI container, code generation

**Implementation Complexity**: **LOW**
**Code Reuse**: **70%+**
**Timeline**: **2 days for MVP**, 5 days for full feature set
**Risk**: **LOW** - Proven patterns, minimal new code

**Recommendation**: **PROCEED with Phase 1 implementation immediately**

The Excel file transform work path is the **ideal starting point** for Phase 2 implementation:
- Lowest risk (all dependencies exist)
- Highest code reuse (70%+)
- Clear success criteria (employee roster PoC)
- Direct user value (Excel is most common format)

---

## Appendix A: Code Samples

### A.1 Complete ExcelDataSource Implementation

See Section 5.2 for full implementation (~250 LOC)

### A.2 Example Project Configuration

See Section 4.2 for complete `project.yaml` example

### A.3 Generated Extractor (Expected)

```python
"""
Employee Roster Extractor
Auto-generated by EDGAR Platform

This extractor transforms HR roster Excel data into structured JSON.
"""

from typing import List
from pydantic import BaseModel


class Employee(BaseModel):
    """Employee record model."""
    id: str
    full_name: str
    dept: str
    hired: str  # ISO date format
    annual_salary_usd: float
    manager: bool


def extract_employee(row: dict) -> Employee:
    """Transform Excel row to Employee model."""
    return Employee(
        id=row["employee_id"],
        full_name=f"{row['first_name']} {row['last_name']}",
        dept=row["department"],
        hired=row["hire_date"],
        annual_salary_usd=float(row["salary"]),
        manager=row["is_manager"].lower() == "yes"
    )


def extract_all_employees(rows: List[dict]) -> List[Employee]:
    """Transform all Excel rows to Employee models."""
    return [extract_employee(row) for row in rows]
```

**LOC**: ~40 lines (generated by Sonnet 4.5)

---

## Appendix B: Testing Strategy

### B.1 Unit Tests

```python
"""Test ExcelDataSource"""

import pytest
from pathlib import Path
from edgar_analyzer.data_sources import ExcelDataSource


@pytest.fixture
def sample_excel(tmp_path):
    """Create sample Excel file for testing."""
    import pandas as pd

    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Carol"],
        "age": [25, 32, 28],
        "hired": ["2020-01-15", "2019-06-22", "2021-03-10"]
    })

    excel_path = tmp_path / "test.xlsx"
    df.to_excel(excel_path, index=False)
    return excel_path


async def test_fetch_single_sheet(sample_excel):
    """Test fetching single Excel sheet."""
    source = ExcelDataSource(file_path=sample_excel, sheet_name=0)
    data = await source.fetch()

    assert "rows" in data
    assert data["row_count"] == 3
    assert len(data["columns"]) == 3
    assert data["rows"][0]["name"] == "Alice"


async def test_type_inference(sample_excel):
    """Test automatic type inference."""
    source = ExcelDataSource(file_path=sample_excel, sheet_name=0)
    data = await source.fetch()

    # Check inferred types
    assert isinstance(data["rows"][0]["name"], str)
    assert isinstance(data["rows"][0]["age"], int)
    # Date should be detected as string or datetime
    assert "hired" in data["column_types"]


async def test_missing_file():
    """Test error handling for missing file."""
    source = ExcelDataSource(file_path=Path("nonexistent.xlsx"))

    with pytest.raises(FileNotFoundError):
        await source.fetch()
```

### B.2 Integration Tests

```python
"""Test Excel → Schema → Patterns → Code Generation"""

async def test_end_to_end_excel_extraction():
    """Test complete Excel extraction pipeline."""
    # 1. Load Excel
    excel = ExcelDataSource(file_path=Path("tests/data/employees.xlsx"))
    data = await excel.fetch()

    # 2. Infer schema
    analyzer = SchemaAnalyzer()
    schema = analyzer.infer_schema(data["rows"], is_input=True)

    assert len(schema.fields) == 7  # All columns detected
    assert schema.get_field("employee_id").field_type == FieldTypeEnum.STRING
    assert schema.get_field("salary").field_type == FieldTypeEnum.INTEGER

    # 3. Parse examples
    parser = ExampleParser(analyzer)
    examples = [
        ExampleConfig(input=data["rows"][0], output=transform_row(data["rows"][0])),
        ExampleConfig(input=data["rows"][1], output=transform_row(data["rows"][1]))
    ]
    parsed = parser.parse_examples(examples)

    assert len(parsed.patterns) >= 3  # At least 3 patterns detected
    assert len(parsed.high_confidence_patterns) >= 2
```

---

## Appendix C: Performance Benchmarks

### C.1 Expected Performance

| Operation | Time (ms) | Memory (MB) | Notes |
|-----------|-----------|-------------|-------|
| Read 100 rows | <50 | <5 | Single sheet, simple types |
| Read 1,000 rows | <200 | <20 | Single sheet |
| Read 10,000 rows | <1,000 | <100 | Chunked reading recommended |
| Schema inference (100 rows) | <30 | <2 | All columns analyzed |
| Pattern detection (10 examples) | <100 | <5 | Pattern complexity varies |
| Code generation | <5,000 | <50 | Sonnet 4.5 API call |

**Total End-to-End** (100 rows, 3 examples): **<6 seconds**

### C.2 Optimization Opportunities

**Phase 3**:
1. **Lazy loading**: Read only necessary columns
2. **Chunked iteration**: Process large files in chunks
3. **Type hints**: Skip inference when types provided
4. **Parallel sheet reading**: Read multiple sheets concurrently

---

**Research Complete**: 2025-11-29
**Next Action**: Create ticket for ExcelDataSource implementation
**Estimated Effort**: 2 days (MVP), 5 days (full features)
**Code Reuse**: 70%+ from existing services
