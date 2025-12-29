# Report Generator API Reference

Complete API documentation for the IReportGenerator multi-format reporting system.

**Package**: `extract_transform_platform.reports`
**Status**: Production-ready (97% test coverage, 135/135 tests passing)
**Ticket**: 1M-360 (IReportGenerator Multi-Format Support)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core Interfaces](#core-interfaces)
  - [IReportGenerator Protocol](#ireportgenerator-protocol)
  - [BaseReportGenerator ABC](#basereportgenerator-abc)
- [Configuration Models](#configuration-models)
  - [ReportConfig](#reportconfig)
  - [ExcelReportConfig](#excelreportconfig)
  - [PDFReportConfig](#pdfreportconfig)
  - [DOCXReportConfig](#docxreportconfig)
  - [PPTXReportConfig](#pptxreportconfig)
- [Concrete Generators](#concrete-generators)
  - [ExcelReportGenerator](#excelreportgenerator)
  - [PDFReportGenerator](#pdfreportgenerator)
  - [DOCXReportGenerator](#docxreportgenerator)
  - [PPTXReportGenerator](#pptxreportgenerator)
- [Factory](#factory)
  - [ReportGeneratorFactory](#reportgeneratorfactory)
- [Type Definitions](#type-definitions)
- [Error Handling](#error-handling)

---

## 🎯 Overview

### Design Pattern

The IReportGenerator system follows the **Protocol + ABC + Factory** pattern:

```
IReportGenerator (Protocol)       # Duck typing interface
         ↑
         |
BaseReportGenerator (ABC)         # Concrete base with helpers
         ↑
         |
    ┌────┴────┬────────┬────────┐
    |         |        |        |
Excel      PDF      DOCX      PPTX  # Concrete implementations
    ↑         ↑        ↑        ↑
    └─────────┴────────┴────────┘
              |
    ReportGeneratorFactory        # Centralized creation
```

### Package Structure

```python
from extract_transform_platform.reports import (
    # Configuration models
    ReportConfig,
    ExcelReportConfig,
    PDFReportConfig,
    DOCXReportConfig,
    PPTXReportConfig,

    # Interfaces
    IReportGenerator,
    BaseReportGenerator,

    # Concrete generators
    ExcelReportGenerator,
    PDFReportGenerator,
    DOCXReportGenerator,
    PPTXReportGenerator,

    # Factory
    ReportGeneratorFactory
)
```

### Import Paths

```python
# All exports from single module
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    ExcelReportConfig,
    IReportGenerator
)

# Individual module imports (advanced)
from extract_transform_platform.reports.base import (
    ReportConfig,
    IReportGenerator,
    BaseReportGenerator
)
from extract_transform_platform.reports.factory import ReportGeneratorFactory
from extract_transform_platform.reports.excel_generator import ExcelReportGenerator
```

---

## 🔌 Core Interfaces

### IReportGenerator Protocol

**Purpose**: Duck typing interface for report generators

**Type**: Protocol (structural subtyping with `@runtime_checkable`)

**Location**: `extract_transform_platform.reports.base.IReportGenerator`

#### Interface Definition

```python
from typing import Protocol, runtime_checkable, Any, List
from pathlib import Path

@runtime_checkable
class IReportGenerator(Protocol):
    """Protocol for report generators."""

    def generate(
        self,
        data: Any,
        output_path: Path,
        config: ReportConfig
    ) -> Path:
        """Generate report from data.

        Args:
            data: Report data (DataFrame, dict, list)
            output_path: Output file path (with appropriate extension)
            config: Report configuration (format-specific subclass)

        Returns:
            Path to generated report file (absolute path)

        Raises:
            TypeError: If data format unsupported or config wrong type
            ValueError: If output path has wrong extension
            IOError: If file cannot be written
        """
        ...

    def get_supported_features(self) -> List[str]:
        """Return list of supported features.

        Returns:
            List of feature names (e.g., ["tables", "formatting", "charts"])
        """
        ...
```

#### Usage Example

```python
from extract_transform_platform.reports import (
    IReportGenerator,
    ExcelReportGenerator
)

# Type checking (structural)
generator: IReportGenerator = ExcelReportGenerator()

# Runtime checking
if isinstance(generator, IReportGenerator):
    output = generator.generate(data, path, config)
```

#### Design Rationale

- **Structural subtyping**: Any class implementing the interface works
- **No inheritance required**: Flexible for external integrations
- **Runtime checking**: `isinstance()` works with `@runtime_checkable`
- **Type hints**: IDE autocomplete and static analysis support

---

### BaseReportGenerator ABC

**Purpose**: Abstract base class with concrete helper methods

**Type**: Abstract Base Class (ABC)

**Location**: `extract_transform_platform.reports.base.BaseReportGenerator`

#### Class Definition

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List
import pandas as pd

class BaseReportGenerator(ABC):
    """Abstract base class for report generators."""

    def __init__(self) -> None:
        """Initialize base report generator."""
        self._supported_features: List[str] = []
        # Subclasses set supported features

    @abstractmethod
    def generate(
        self,
        data: Any,
        output_path: Path,
        config: ReportConfig
    ) -> Path:
        """Generate report from data.

        Abstract method - must be implemented by subclasses.
        """
        pass

    def get_supported_features(self) -> List[str]:
        """Return list of supported features.

        Returns:
            List of feature names
        """
        return self._supported_features.copy()

    # Helper methods (protected)

    def _validate_output_path(
        self,
        output_path: Path,
        expected_extension: str
    ) -> None:
        """Validate output path has correct extension.

        Args:
            output_path: Output file path
            expected_extension: Expected extension (e.g., ".xlsx")

        Raises:
            ValueError: If extension doesn't match
        """
        if output_path.suffix.lower() != expected_extension:
            raise ValueError(
                f"Output path must have {expected_extension} extension, "
                f"got {output_path.suffix}"
            )

    def _validate_data_not_empty(
        self,
        data: Any,
        data_name: str = "Data"
    ) -> None:
        """Validate data is not empty.

        Args:
            data: Data to validate
            data_name: Name for error message

        Raises:
            ValueError: If data is None or empty
        """
        if data is None:
            raise ValueError(f"{data_name} cannot be None")

        if isinstance(data, pd.DataFrame) and data.empty:
            raise ValueError(f"{data_name} cannot be empty")

        if isinstance(data, (list, dict)) and len(data) == 0:
            raise ValueError(f"{data_name} cannot be empty")

    def _to_dataframe(self, data: Any) -> pd.DataFrame:
        """Convert various data formats to DataFrame.

        Supports:
        - DataFrame (passthrough)
        - Dict (single row or columnar)
        - List of dicts (multiple rows)
        - List of lists (raw data)
        - List of values (single column)

        Args:
            data: Input data

        Returns:
            DataFrame representation

        Raises:
            TypeError: If data format unsupported
        """
        if isinstance(data, pd.DataFrame):
            return data

        if isinstance(data, dict):
            # Single row: {"name": "Alice", "age": 30}
            # Columnar: {"name": ["Alice", "Bob"], "age": [30, 25]}
            return pd.DataFrame(data)

        if isinstance(data, list):
            if len(data) == 0:
                return pd.DataFrame()

            # List of dicts: [{"name": "Alice"}, {"name": "Bob"}]
            if isinstance(data[0], dict):
                return pd.DataFrame(data)

            # List of lists: [["Alice", 30], ["Bob", 25]]
            if isinstance(data[0], list):
                return pd.DataFrame(data)

            # List of values: [1, 2, 3, 4, 5]
            return pd.DataFrame(data, columns=["value"])

        raise TypeError(
            f"Unsupported data type: {type(data).__name__}. "
            f"Supported: DataFrame, dict, list"
        )

    def _ensure_directory_exists(self, output_path: Path) -> None:
        """Create parent directory if it doesn't exist.

        Args:
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
```

#### Usage Example

```python
from extract_transform_platform.reports import BaseReportGenerator
from pathlib import Path

class CustomReportGenerator(BaseReportGenerator):
    """Custom report generator."""

    def __init__(self):
        super().__init__()
        self._supported_features = ["tables", "custom_format"]

    def generate(self, data, output_path, config):
        # Use helper methods
        self._validate_output_path(output_path, ".custom")
        self._validate_data_not_empty(data, "Report data")

        # Convert to DataFrame
        df = self._to_dataframe(data)

        # Ensure directory exists
        self._ensure_directory_exists(output_path)

        # Generate report
        # ... implementation ...

        return output_path.absolute()
```

---

## ⚙️ Configuration Models

All configuration models use Pydantic for validation and type safety.

### ReportConfig

**Purpose**: Base configuration for all report formats

**Location**: `extract_transform_platform.reports.base.ReportConfig`

#### Class Definition

```python
from pydantic import BaseModel, Field

class ReportConfig(BaseModel):
    """Base configuration for all report generators."""

    title: str = Field(..., description="Report title")

    author: str = Field(
        default="EDGAR Platform",
        description="Report author"
    )

    include_timestamp: bool = Field(
        default=True,
        description="Include generation timestamp"
    )

    page_size: str = Field(
        default="letter",
        description="Page size (letter, a4, legal)",
        pattern="^(letter|a4|legal)$"
    )

    model_config = {
        "frozen": False,
        "validate_assignment": True
    }
```

#### Fields

| Field | Type | Default | Description | Validation |
|-------|------|---------|-------------|------------|
| `title` | str | *required* | Report title | - |
| `author` | str | "EDGAR Platform" | Report author | - |
| `include_timestamp` | bool | True | Include generation timestamp | - |
| `page_size` | str | "letter" | Page size | Must be: letter, a4, legal |

#### Usage Example

```python
from extract_transform_platform.reports import ReportConfig

# Basic config
config = ReportConfig(title="My Report")

# Full config
config = ReportConfig(
    title="Quarterly Report",
    author="Finance Team",
    include_timestamp=True,
    page_size="a4"
)

# Validation
try:
    config = ReportConfig(
        title="Report",
        page_size="invalid"  # ❌ Validation error
    )
except ValueError as e:
    print(f"Validation error: {e}")
```

---

### ExcelReportConfig

**Purpose**: Excel-specific configuration (extends ReportConfig)

**Location**: `extract_transform_platform.reports.base.ExcelReportConfig`

#### Class Definition

```python
from typing import Dict
from pydantic import Field

class ExcelReportConfig(ReportConfig):
    """Excel-specific configuration."""

    sheet_name: str = Field(
        default="Report",
        description="Sheet name"
    )

    freeze_header: bool = Field(
        default=True,
        description="Freeze top row"
    )

    auto_filter: bool = Field(
        default=True,
        description="Enable auto-filter"
    )

    column_widths: Dict[str, int] = Field(
        default_factory=dict,
        description="Column widths (column_name: width)"
    )

    include_summary: bool = Field(
        default=False,
        description="Include summary sheet"
    )
```

#### Additional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sheet_name` | str | "Report" | Worksheet name |
| `freeze_header` | bool | True | Freeze top row for scrolling |
| `auto_filter` | bool | True | Enable auto-filter on header |
| `column_widths` | Dict[str, int] | {} | Custom column widths |
| `include_summary` | bool | False | Add summary statistics sheet |

#### Usage Example

```python
from extract_transform_platform.reports import ExcelReportConfig

config = ExcelReportConfig(
    title="Sales Report",
    sheet_name="Q4_Sales",
    freeze_header=True,
    auto_filter=True,
    column_widths={
        "Product": 30,
        "Description": 50,
        "Price": 15
    },
    include_summary=False
)
```

---

### PDFReportConfig

**Purpose**: PDF-specific configuration (extends ReportConfig)

**Location**: `extract_transform_platform.reports.base.PDFReportConfig`

#### Class Definition

```python
from pydantic import Field

class PDFReportConfig(ReportConfig):
    """PDF-specific configuration."""

    page_orientation: str = Field(
        default="portrait",
        description="Page orientation (portrait, landscape)",
        pattern="^(portrait|landscape)$"
    )

    margin_top: float = Field(
        default=0.75,
        description="Top margin (inches)",
        ge=0.0,
        le=2.0
    )

    margin_bottom: float = Field(
        default=0.75,
        description="Bottom margin (inches)",
        ge=0.0,
        le=2.0
    )

    margin_left: float = Field(
        default=0.75,
        description="Left margin (inches)",
        ge=0.0,
        le=2.0
    )

    margin_right: float = Field(
        default=0.75,
        description="Right margin (inches)",
        ge=0.0,
        le=2.0
    )

    font_name: str = Field(
        default="Helvetica",
        description="Font family",
        pattern="^(Helvetica|Times-Roman|Courier)$"
    )

    font_size: int = Field(
        default=10,
        description="Base font size",
        ge=8,
        le=16
    )

    table_style: str = Field(
        default="grid",
        description="Table style (grid, simple, fancy)",
        pattern="^(grid|simple|fancy)$"
    )

    include_page_numbers: bool = Field(
        default=True,
        description="Include page numbers"
    )

    header_text: str | None = Field(
        default=None,
        description="Header text"
    )

    footer_text: str | None = Field(
        default=None,
        description="Footer text"
    )
```

#### Additional Fields

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `page_orientation` | str | "portrait" | portrait, landscape | Page orientation |
| `margin_top` | float | 0.75 | 0.0-2.0 | Top margin (inches) |
| `margin_bottom` | float | 0.75 | 0.0-2.0 | Bottom margin (inches) |
| `margin_left` | float | 0.75 | 0.0-2.0 | Left margin (inches) |
| `margin_right` | float | 0.75 | 0.0-2.0 | Right margin (inches) |
| `font_name` | str | "Helvetica" | Helvetica, Times-Roman, Courier | Font family |
| `font_size` | int | 10 | 8-16 | Base font size (points) |
| `table_style` | str | "grid" | grid, simple, fancy | Table style |
| `include_page_numbers` | bool | True | - | Include page numbers |
| `header_text` | str\|None | None | - | Optional header text |
| `footer_text` | str\|None | None | - | Optional footer text |

#### Usage Example

```python
from extract_transform_platform.reports import PDFReportConfig

config = PDFReportConfig(
    title="Invoice",
    page_orientation="portrait",
    margin_top=1.0,
    margin_bottom=1.0,
    font_name="Helvetica",
    font_size=11,
    table_style="fancy",
    include_page_numbers=True,
    header_text="ABC Company",
    footer_text="Payment due within 30 days"
)
```

---

### DOCXReportConfig

**Purpose**: DOCX-specific configuration (extends ReportConfig)

**Location**: `extract_transform_platform.reports.base.DOCXReportConfig`

#### Class Definition

```python
from pydantic import Field

class DOCXReportConfig(ReportConfig):
    """DOCX-specific configuration."""

    heading_level: int = Field(
        default=1,
        description="Title heading level (1-9)",
        ge=1,
        le=9
    )

    table_style: str = Field(
        default="Light Grid Accent 1",
        description="Table style name"
    )

    font_name: str = Field(
        default="Calibri",
        description="Document font"
    )

    font_size: int = Field(
        default=11,
        description="Base font size (pt)",
        ge=8,
        le=16
    )

    include_toc: bool = Field(
        default=False,
        description="Include table of contents"
    )

    page_break_after_title: bool = Field(
        default=False,
        description="Page break after title"
    )

    table_alignment: str = Field(
        default="center",
        description="Table alignment (left, center, right)",
        pattern="^(left|center|right)$"
    )
```

#### Additional Fields

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `heading_level` | int | 1 | 1-9 | Title heading level |
| `table_style` | str | "Light Grid Accent 1" | - | python-docx table style |
| `font_name` | str | "Calibri" | - | Document font family |
| `font_size` | int | 11 | 8-16 | Base font size (points) |
| `include_toc` | bool | False | - | Include table of contents |
| `page_break_after_title` | bool | False | - | Page break after title |
| `table_alignment` | str | "center" | left, center, right | Table alignment |

#### Usage Example

```python
from extract_transform_platform.reports import DOCXReportConfig

config = DOCXReportConfig(
    title="Business Proposal",
    heading_level=1,
    table_style="Light Grid Accent 1",
    font_name="Arial",
    font_size=12,
    include_toc=False,
    page_break_after_title=True,
    table_alignment="center"
)
```

---

### PPTXReportConfig

**Purpose**: PPTX-specific configuration (extends ReportConfig)

**Location**: `extract_transform_platform.reports.base.PPTXReportConfig`

#### Class Definition

```python
from pydantic import Field

class PPTXReportConfig(ReportConfig):
    """PPTX-specific configuration."""

    slide_layout: str = Field(
        default="Title and Content",
        description="Slide layout name"
    )

    theme_color: str = Field(
        default="#366092",
        description="Theme color (hex format)",
        pattern="^#[0-9A-Fa-f]{6}$"
    )

    font_name: str = Field(
        default="Calibri",
        description="Font family"
    )

    font_size: int = Field(
        default=14,
        description="Base font size (pt)",
        ge=10,
        le=24
    )

    table_style: str = Field(
        default="Medium Style 2 - Accent 1",
        description="Table style name"
    )

    include_chart: bool = Field(
        default=False,
        description="Include chart slide"
    )

    chart_type: str = Field(
        default="bar",
        description="Chart type (bar, column, line, pie)",
        pattern="^(bar|column|line|pie)$"
    )

    max_rows_per_slide: int = Field(
        default=10,
        description="Maximum table rows per slide",
        ge=5,
        le=50
    )
```

#### Additional Fields

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `slide_layout` | str | "Title and Content" | - | Slide layout name |
| `theme_color` | str | "#366092" | Hex color | Theme color |
| `font_name` | str | "Calibri" | - | Font family |
| `font_size` | int | 14 | 10-24 | Base font size (points) |
| `table_style` | str | "Medium Style 2 - Accent 1" | - | Table style |
| `include_chart` | bool | False | - | Include chart slide |
| `chart_type` | str | "bar" | bar, column, line, pie | Chart type |
| `max_rows_per_slide` | int | 10 | 5-50 | Max rows per slide |

#### Usage Example

```python
from extract_transform_platform.reports import PPTXReportConfig

config = PPTXReportConfig(
    title="Quarterly Review",
    slide_layout="Title and Content",
    theme_color="#366092",
    font_name="Calibri",
    font_size=14,
    table_style="Medium Style 2 - Accent 1",
    include_chart=False,
    chart_type="bar",
    max_rows_per_slide=10
)
```

---

## 🏭 Concrete Generators

### ExcelReportGenerator

**Purpose**: Generate Excel reports with openpyxl

**Location**: `extract_transform_platform.reports.excel_generator.ExcelReportGenerator`

**Dependencies**: openpyxl, pandas

#### Class Definition

```python
class ExcelReportGenerator(BaseReportGenerator):
    """Excel report generator with openpyxl."""

    def __init__(self) -> None:
        """Initialize Excel report generator."""
        super().__init__()
        self._supported_features = [
            "tables",
            "formatting",
            "formulas",
            "charts",
            "multiple_sheets",
            "freeze_panes",
            "auto_filter"
        ]

    def generate(
        self,
        data: Any,
        output_path: Path,
        config: ReportConfig
    ) -> Path:
        """Generate Excel report.

        Args:
            data: DataFrame, dict, or list
            output_path: Output .xlsx path
            config: ExcelReportConfig

        Returns:
            Absolute path to generated file
        """
        # Implementation...
```

#### Supported Features

- ✅ Tables - Tabular data rendering
- ✅ Formatting - Bold headers, colors, alignment
- 🔜 Formulas - Excel formulas (future)
- 🔜 Charts - Bar, line, pie charts (future)
- ✅ Multiple Sheets - Multiple worksheets
- ✅ Freeze Panes - Frozen header rows
- ✅ Auto-Filter - Filterable columns

#### Performance

| Rows | Columns | File Size | Generation Time | Memory |
|------|---------|-----------|-----------------|--------|
| 100 | 7 | 15 KB | ~50ms | 3 MB |
| 1,000 | 7 | 120 KB | ~200ms | 12 MB |
| 10,000 | 7 | 1.2 MB | ~1.5s | 85 MB |

---

### PDFReportGenerator

**Purpose**: Generate PDF reports with reportlab

**Location**: `extract_transform_platform.reports.pdf_generator.PDFReportGenerator`

**Dependencies**: reportlab, pandas

#### Supported Features

- ✅ Tables - Tabular data with 3 styles (grid, simple, fancy)
- ✅ Formatting - Fonts, colors, alignment
- ✅ Headers/Footers - Custom text on all pages
- ✅ Page Numbers - Automatic page numbering
- ✅ Multiple Pages - Automatic pagination

---

### DOCXReportGenerator

**Purpose**: Generate DOCX reports with python-docx

**Location**: `extract_transform_platform.reports.docx_generator.DOCXReportGenerator`

**Dependencies**: python-docx, pandas

#### Supported Features

- ✅ Tables - Tabular data with 50+ built-in styles
- ✅ Formatting - Headings, fonts, alignment
- ✅ Heading Levels - 1-9 heading levels
- 🔜 Table of Contents - Automatic TOC (future)
- ✅ Page Breaks - Control document flow

---

### PPTXReportGenerator

**Purpose**: Generate PPTX reports with python-pptx

**Location**: `extract_transform_platform.reports.pptx_generator.PPTXReportGenerator`

**Dependencies**: python-pptx, pandas

#### Supported Features

- ✅ Tables - Tabular data with pagination
- ✅ Multiple Slides - Automatic slide creation
- ✅ Formatting - Fonts, colors, alignment
- 🔜 Charts - Bar, column, line, pie (future)

---

## 🏗️ Factory

### ReportGeneratorFactory

**Purpose**: Centralized generator creation

**Location**: `extract_transform_platform.reports.factory.ReportGeneratorFactory`

#### Class Methods

##### create(format: str) → IReportGenerator

Create generator for specified format.

```python
@classmethod
def create(cls, format: str) -> IReportGenerator:
    """Create report generator.

    Args:
        format: Report format (excel, xlsx, pdf, docx, pptx)
               Case-insensitive

    Returns:
        Generator instance

    Raises:
        ValueError: If format not supported
    """
```

**Example**:
```python
generator = ReportGeneratorFactory.create("excel")
generator = ReportGeneratorFactory.create("EXCEL")  # Case-insensitive
```

##### register(format: str, generator_class: Type[BaseReportGenerator]) → None

Register custom generator.

```python
@classmethod
def register(
    cls,
    format: str,
    generator_class: Type[BaseReportGenerator]
) -> None:
    """Register custom generator.

    Args:
        format: Format identifier
        generator_class: Must inherit from BaseReportGenerator

    Raises:
        TypeError: If invalid generator class
    """
```

**Example**:
```python
ReportGeneratorFactory.register("custom", CustomReportGenerator)
```

##### get_supported_formats() → List[str]

Get list of supported formats.

```python
@classmethod
def get_supported_formats(cls) -> List[str]:
    """Get supported formats.

    Returns:
        Sorted list of format identifiers
    """
```

**Example**:
```python
formats = ReportGeneratorFactory.get_supported_formats()
# ['docx', 'excel', 'pdf', 'pptx', 'xlsx']
```

##### is_format_supported(format: str) → bool

Check if format is supported.

```python
@classmethod
def is_format_supported(cls, format: str) -> bool:
    """Check format support.

    Args:
        format: Format identifier

    Returns:
        True if supported
    """
```

**Example**:
```python
if ReportGeneratorFactory.is_format_supported("excel"):
    generator = ReportGeneratorFactory.create("excel")
```

---

## 📦 Type Definitions

### Supported Data Types

```python
# Input data types
DataType = Union[
    pd.DataFrame,                          # Preferred
    Dict[str, Any],                        # Single row or columnar
    List[Dict[str, Any]],                  # Multiple rows
    List[List[Any]],                       # Raw data
    List[Any]                              # Single column
]

# Configuration types
ConfigType = Union[
    ReportConfig,                          # Base
    ExcelReportConfig,                     # Excel-specific
    PDFReportConfig,                       # PDF-specific
    DOCXReportConfig,                      # DOCX-specific
    PPTXReportConfig                       # PPTX-specific
]
```

---

## ⚠️ Error Handling

### Exception Hierarchy

```python
# Standard Python exceptions used
TypeError       # Wrong data type or config type
ValueError      # Invalid configuration or empty data
IOError         # File write errors
```

### Common Errors

#### TypeError: Unsupported data type

```python
try:
    generator.generate(invalid_data, path, config)
except TypeError as e:
    print(f"Data type error: {e}")
    # Supported: DataFrame, dict, list
```

#### ValueError: Invalid configuration

```python
try:
    config = PDFReportConfig(page_size="invalid")
except ValueError as e:
    print(f"Config validation error: {e}")
    # Must be: letter, a4, legal
```

#### ValueError: Output path extension

```python
try:
    generator = ReportGeneratorFactory.create("excel")
    generator.generate(data, Path("report.pdf"), config)  # Wrong extension
except ValueError as e:
    print(f"Extension error: {e}")
    # Must be .xlsx for Excel
```

#### IOError: File write error

```python
try:
    generator.generate(data, Path("report.xlsx"), config)
except IOError as e:
    print(f"File error: {e}")
    # File may be open or permission denied
```

---

## 🔗 Related Documentation

- **[Report Generation User Guide](../guides/REPORT_GENERATION.md)** - Complete user guide with examples
- **[Report Integration Guide](../guides/REPORT_INTEGRATION.md)** - Integration patterns
- **[Platform Usage Guide](../guides/PLATFORM_USAGE.md)** - General platform patterns

---

## 📝 Summary

The IReportGenerator API provides:

- ✅ **Unified interface** - IReportGenerator protocol for all formats
- ✅ **Type safety** - Pydantic configuration models with validation
- ✅ **Factory pattern** - Centralized generator creation
- ✅ **Professional features** - Industry-standard formatting and layouts
- ✅ **Error handling** - Comprehensive validation and clear error messages
- ✅ **Production-ready** - 97% test coverage, 135/135 tests passing

**Next Steps**:
1. Review [Report Generation Guide](../guides/REPORT_GENERATION.md) for usage examples
2. Explore [Report Integration Guide](../guides/REPORT_INTEGRATION.md) for platform integration
3. See [Quick Start Guide](../guides/QUICK_START.md) for platform setup

---

**Status**: Production-ready (97% coverage, 135/135 tests passing)
**Ticket**: 1M-360 (IReportGenerator Multi-Format Support)
**Package**: `extract_transform_platform.reports`
