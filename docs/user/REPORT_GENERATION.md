# Report Generation Guide

Generate professional reports in multiple formats (Excel, PDF, DOCX, PPTX) using the platform's IReportGenerator system.

**Platform Package**: `extract_transform_platform.reports`
**Status**: Production-ready (97% test coverage, 135/135 tests passing)
**Ticket**: 1M-360 (IReportGenerator Multi-Format Support)

> **Note**: This is the unified multi-format reporting system. All 4 formats follow the same interface and patterns.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start-5-minutes)
- [Supported Formats](#supported-formats)
- [Configuration Reference](#configuration-reference)
- [Format-Specific Guides](#format-specific-guides)
  - [Excel Reports](#excel-reports)
  - [PDF Reports](#pdf-reports)
  - [DOCX Reports](#docx-reports)
  - [PPTX Reports](#pptx-reports)
- [Advanced Usage](#advanced-usage)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## 🎯 Overview

### What Is IReportGenerator?

The IReportGenerator system is a unified interface for generating professional reports in multiple formats. It provides:

- ✅ **Single interface** - Same API for all 4 formats
- ✅ **Type-safe configuration** - Pydantic models with validation
- ✅ **Factory pattern** - Easy format selection
- ✅ **Professional formatting** - Headers, footers, styling, charts
- ✅ **Data source flexibility** - DataFrames, dicts, lists
- ✅ **Production-ready** - 97% test coverage, comprehensive error handling

### Supported Formats

| Format | Extension | Use Case | Features |
|--------|-----------|----------|----------|
| **Excel** | `.xlsx` | Data analysis, spreadsheets | Tables, formulas, charts, freeze panes, auto-filter |
| **PDF** | `.pdf` | Print-ready documents | Tables, headers/footers, page numbers, orientation |
| **DOCX** | `.docx` | Business documents | Headings, table styles, fonts, page breaks |
| **PPTX** | `.pptx` | Presentations | Slides, charts, pagination, themes |

### When to Use Each Format

- **Excel**: Financial reports, data exports, analysis with formulas
- **PDF**: Formal reports, invoices, print documents, archival
- **DOCX**: Business proposals, technical documentation, contracts
- **PPTX**: Executive summaries, sales presentations, dashboards

### Key Features

1. **Protocol + ABC + Factory Pattern**: Same proven pattern as BaseDataSource
2. **Type-Safe Configuration**: Pydantic models with runtime validation
3. **Professional Formatting**: Industry-standard styles and layouts
4. **Flexible Data Sources**: DataFrame, dict, list, or custom formats
5. **Error Handling**: Comprehensive validation and clear error messages
6. **Performance**: Optimized for datasets up to 10,000+ rows

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
# Core dependencies (included in platform)
pip install openpyxl reportlab python-docx python-pptx pandas
```

### Step 2: Generate Your First Report

```python
from pathlib import Path
import pandas as pd
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    ExcelReportConfig
)

# Prepare data
data = pd.DataFrame({
    "Product": ["Widget A", "Widget B", "Widget C"],
    "Sales": [1500, 2300, 1800],
    "Revenue": [45000, 69000, 54000]
})

# Create generator
generator = ReportGeneratorFactory.create("excel")

# Configure report
config = ExcelReportConfig(
    title="Sales Report Q4 2024",
    freeze_header=True,
    auto_filter=True
)

# Generate report
output = generator.generate(data, Path("sales_report.xlsx"), config)
print(f"✅ Report generated: {output}")
```

**Output**: Professional Excel file with formatted headers, frozen top row, and auto-filter enabled.

### Step 3: Try Other Formats

```python
# PDF Report
from extract_transform_platform.reports import PDFReportConfig

pdf_generator = ReportGeneratorFactory.create("pdf")
pdf_config = PDFReportConfig(
    title="Sales Report Q4 2024",
    table_style="fancy",
    include_page_numbers=True
)
pdf_generator.generate(data, Path("sales_report.pdf"), pdf_config)

# DOCX Report
from extract_transform_platform.reports import DOCXReportConfig

docx_generator = ReportGeneratorFactory.create("docx")
docx_config = DOCXReportConfig(
    title="Sales Report Q4 2024",
    table_style="Light Grid Accent 1"
)
docx_generator.generate(data, Path("sales_report.docx"), docx_config)
```

---

## 📊 Supported Formats

### Format Comparison

| Feature | Excel | PDF | DOCX | PPTX |
|---------|-------|-----|------|------|
| **Tables** | ✅ | ✅ | ✅ | ✅ |
| **Formatting** | ✅ | ✅ | ✅ | ✅ |
| **Charts** | 🔜 | 🔜 | 🔜 | ✅ |
| **Formulas** | 🔜 | ❌ | ❌ | ❌ |
| **Multiple Pages** | ✅ | ✅ | ✅ | ✅ |
| **Freeze Panes** | ✅ | ❌ | ❌ | ❌ |
| **Auto-Filter** | ✅ | ❌ | ❌ | ❌ |
| **Page Numbers** | ❌ | ✅ | ✅ | ✅ |
| **Headers/Footers** | ❌ | ✅ | ✅ | ✅ |

**Legend**: ✅ Supported | 🔜 Future | ❌ Not Applicable

### Format Selection Strategy

```python
from extract_transform_platform.reports import ReportGeneratorFactory

# List all supported formats
formats = ReportGeneratorFactory.get_supported_formats()
print(formats)  # ['docx', 'excel', 'pdf', 'pptx', 'xlsx']

# Check if format is supported
if ReportGeneratorFactory.is_format_supported("excel"):
    generator = ReportGeneratorFactory.create("excel")
```

---

## ⚙️ Configuration Reference

### Base Configuration (ReportConfig)

All format-specific configs inherit from `ReportConfig`:

```python
from extract_transform_platform.reports import ReportConfig

config = ReportConfig(
    title="My Report",                    # Report title (required)
    author="EDGAR Platform",              # Report author (default: "EDGAR Platform")
    include_timestamp=True,               # Include generation timestamp (default: True)
    page_size="letter"                    # Page size: letter, a4, legal (default: "letter")
)
```

**Fields**:
- `title` (str, required): Report title displayed in header/metadata
- `author` (str, default="EDGAR Platform"): Report author name
- `include_timestamp` (bool, default=True): Include generation timestamp
- `page_size` (str, default="letter"): Page size - `letter`, `a4`, `legal`

### ExcelReportConfig

```python
from extract_transform_platform.reports import ExcelReportConfig

config = ExcelReportConfig(
    # Base config
    title="Sales Report",
    author="Finance Team",

    # Excel-specific
    sheet_name="Report",                  # Worksheet name (default: "Report")
    freeze_header=True,                   # Freeze top row (default: True)
    auto_filter=True,                     # Enable auto-filter (default: True)
    column_widths={"Product": 20, "Sales": 15},  # Custom column widths
    include_summary=False                 # Include summary sheet (default: False)
)
```

**Excel-Specific Fields**:
- `sheet_name` (str, default="Report"): Worksheet name
- `freeze_header` (bool, default=True): Freeze top row for scrolling
- `auto_filter` (bool, default=True): Enable auto-filter on header row
- `column_widths` (Dict[str, int], optional): Custom column widths in characters
- `include_summary` (bool, default=False): Add summary statistics sheet

### PDFReportConfig

```python
from extract_transform_platform.reports import PDFReportConfig

config = PDFReportConfig(
    # Base config
    title="Invoice",
    page_size="letter",

    # PDF-specific
    page_orientation="portrait",          # portrait or landscape (default: "portrait")
    margin_top=0.75,                      # Top margin in inches (default: 0.75)
    margin_bottom=0.75,                   # Bottom margin in inches (default: 0.75)
    margin_left=0.75,                     # Left margin in inches (default: 0.75)
    margin_right=0.75,                    # Right margin in inches (default: 0.75)
    font_name="Helvetica",                # Font: Helvetica, Times-Roman, Courier
    font_size=10,                         # Font size in points (8-16, default: 10)
    table_style="grid",                   # Table style: grid, simple, fancy
    include_page_numbers=True,            # Include page numbers (default: True)
    header_text="Confidential",           # Optional header text
    footer_text="© 2024 Company"          # Optional footer text
)
```

**PDF-Specific Fields**:
- `page_orientation` (str, default="portrait"): `portrait` or `landscape`
- `margin_top/bottom/left/right` (float, 0.0-2.0, default=0.75): Margins in inches
- `font_name` (str, default="Helvetica"): `Helvetica`, `Times-Roman`, `Courier`
- `font_size` (int, 8-16, default=10): Base font size in points
- `table_style` (str, default="grid"): `grid`, `simple`, `fancy`
- `include_page_numbers` (bool, default=True): Include page numbers in footer
- `header_text` (str, optional): Header text on all pages
- `footer_text` (str, optional): Footer text on all pages

### DOCXReportConfig

```python
from extract_transform_platform.reports import DOCXReportConfig

config = DOCXReportConfig(
    # Base config
    title="Business Proposal",

    # DOCX-specific
    heading_level=1,                      # Title heading level 1-9 (default: 1)
    table_style="Light Grid Accent 1",    # python-docx table style
    font_name="Calibri",                  # Document font (default: "Calibri")
    font_size=11,                         # Font size 8-16 pt (default: 11)
    include_toc=False,                    # Include table of contents (default: False)
    page_break_after_title=False,         # Page break after title (default: False)
    table_alignment="center"              # Table alignment: left, center, right
)
```

**DOCX-Specific Fields**:
- `heading_level` (int, 1-9, default=1): Title heading level
- `table_style` (str, default="Light Grid Accent 1"): python-docx table style name
- `font_name` (str, default="Calibri"): Document font family
- `font_size` (int, 8-16, default=11): Base font size in points
- `include_toc` (bool, default=False): Include table of contents
- `page_break_after_title` (bool, default=False): Page break after title
- `table_alignment` (str, default="center"): `left`, `center`, `right`

### PPTXReportConfig

```python
from extract_transform_platform.reports import PPTXReportConfig

config = PPTXReportConfig(
    # Base config
    title="Executive Summary",

    # PPTX-specific
    layout_name="Title Slide",            # Slide layout (default: "Title Slide")
    rows_per_slide=10,                    # Rows per slide (default: 10)
    include_charts=False,                 # Include charts (default: False)
    chart_type="bar"                      # Chart type: bar, line, pie (default: "bar")
)
```

**PPTX-Specific Fields**:
- `layout_name` (str, default="Title Slide"): Slide layout name
- `rows_per_slide` (int, default=10): Maximum rows per slide for tables
- `include_charts` (bool, default=False): Include data visualization charts
- `chart_type` (str, default="bar"): `bar`, `line`, `pie`

---

## 📝 Format-Specific Guides

### Excel Reports

**Use Case**: Data analysis, financial reports, spreadsheets

#### Basic Excel Report

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    ExcelReportConfig
)
import pandas as pd
from pathlib import Path

# Prepare data
data = pd.DataFrame({
    "Employee": ["Alice", "Bob", "Charlie"],
    "Department": ["Engineering", "Sales", "Marketing"],
    "Salary": [95000, 85000, 78000]
})

# Create generator
generator = ReportGeneratorFactory.create("excel")

# Configure
config = ExcelReportConfig(
    title="Employee Salaries",
    sheet_name="Employees",
    freeze_header=True,
    auto_filter=True
)

# Generate
output = generator.generate(data, Path("employees.xlsx"), config)
```

#### Advanced Excel Features

**Custom Column Widths**:
```python
config = ExcelReportConfig(
    title="Sales Report",
    column_widths={
        "Product": 30,      # 30 characters wide
        "Description": 50,  # 50 characters wide
        "Price": 15         # 15 characters wide
    }
)
```

**Summary Sheet** (future):
```python
config = ExcelReportConfig(
    title="Financial Report",
    include_summary=True  # Adds summary sheet with statistics
)
```

**Multiple Data Sources**:
```python
# From dict
data = {"name": ["Alice", "Bob"], "age": [30, 25]}
generator.generate(data, Path("report.xlsx"), config)

# From list of dicts
data = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
]
generator.generate(data, Path("report.xlsx"), config)
```

#### Excel Features

- ✅ **Freeze Panes**: Top row stays visible when scrolling
- ✅ **Auto-Filter**: Click dropdown arrows to filter columns
- ✅ **Custom Column Widths**: Set width per column
- ✅ **Professional Formatting**: Bold headers, alignment
- 🔜 **Summary Sheet**: Automatic statistics (future)
- 🔜 **Charts**: Bar, line, pie charts (future)

---

### PDF Reports

**Use Case**: Print-ready documents, invoices, formal reports

#### Basic PDF Report

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    PDFReportConfig
)
import pandas as pd
from pathlib import Path

# Prepare data
data = pd.DataFrame({
    "Item": ["Widget A", "Widget B", "Widget C"],
    "Quantity": [2, 1, 5],
    "Price": [15.00, 50.00, 10.00],
    "Total": [30.00, 50.00, 50.00]
})

# Create generator
generator = ReportGeneratorFactory.create("pdf")

# Configure
config = PDFReportConfig(
    title="Invoice #12345",
    table_style="fancy",
    include_page_numbers=True,
    header_text="ABC Company",
    footer_text="Thank you for your business!"
)

# Generate
output = generator.generate(data, Path("invoice.pdf"), config)
```

#### Advanced PDF Features

**Landscape Orientation**:
```python
config = PDFReportConfig(
    title="Wide Report",
    page_orientation="landscape"  # For tables with many columns
)
```

**Custom Margins**:
```python
config = PDFReportConfig(
    title="Compact Report",
    margin_top=0.5,      # Narrow margins
    margin_bottom=0.5,
    margin_left=0.5,
    margin_right=0.5
)
```

**Table Styles**:
```python
# Grid style (default) - Full borders
config = PDFReportConfig(title="Report", table_style="grid")

# Simple style - Minimal borders
config = PDFReportConfig(title="Report", table_style="simple")

# Fancy style - Colored headers, alternating rows
config = PDFReportConfig(title="Report", table_style="fancy")
```

**Headers and Footers**:
```python
config = PDFReportConfig(
    title="Financial Report",
    header_text="Confidential - Internal Use Only",
    footer_text="© 2024 Company Name. All rights reserved.",
    include_page_numbers=True  # Page numbers in footer
)
```

#### PDF Features

- ✅ **Professional Layout**: Industry-standard margins and spacing
- ✅ **Table Styles**: Grid, simple, fancy
- ✅ **Headers/Footers**: Custom text on all pages
- ✅ **Page Numbers**: Automatic page numbering
- ✅ **Orientation**: Portrait or landscape
- ✅ **Font Customization**: Helvetica, Times-Roman, Courier

---

### DOCX Reports

**Use Case**: Business documents, proposals, technical documentation

#### Basic DOCX Report

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    DOCXReportConfig
)
import pandas as pd
from pathlib import Path

# Prepare data
data = pd.DataFrame({
    "Task": ["Design", "Development", "Testing", "Deployment"],
    "Owner": ["Alice", "Bob", "Charlie", "Dave"],
    "Status": ["Complete", "In Progress", "Pending", "Pending"]
})

# Create generator
generator = ReportGeneratorFactory.create("docx")

# Configure
config = DOCXReportConfig(
    title="Project Status Report",
    table_style="Light Grid Accent 1",
    table_alignment="center"
)

# Generate
output = generator.generate(data, Path("status.docx"), config)
```

#### Advanced DOCX Features

**Heading Levels**:
```python
config = DOCXReportConfig(
    title="Technical Documentation",
    heading_level=2  # Use Heading 2 for title
)
```

**Page Breaks**:
```python
config = DOCXReportConfig(
    title="Executive Summary",
    page_break_after_title=True  # Title on separate page
)
```

**Table Styles** (python-docx built-in):
```python
# Professional styles
config = DOCXReportConfig(
    title="Report",
    table_style="Light Grid Accent 1"  # Blue headers
)

# Alternative styles
config = DOCXReportConfig(
    title="Report",
    table_style="Medium Grid 3 Accent 1"  # Bordered cells
)
```

**Font Customization**:
```python
config = DOCXReportConfig(
    title="Business Proposal",
    font_name="Arial",
    font_size=12  # Larger text for readability
)
```

#### DOCX Features

- ✅ **Heading Styles**: Professional document structure
- ✅ **Table Styles**: 50+ built-in python-docx styles
- ✅ **Font Customization**: Any system font
- ✅ **Table Alignment**: Left, center, right
- 🔜 **Table of Contents**: Automatic TOC generation (future)
- ✅ **Page Breaks**: Control document flow

---

### PPTX Reports

**Use Case**: Presentations, executive dashboards, sales decks

#### Basic PPTX Report

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    PPTXReportConfig
)
import pandas as pd
from pathlib import Path

# Prepare data
data = pd.DataFrame({
    "Quarter": ["Q1", "Q2", "Q3", "Q4"],
    "Revenue": [125000, 138000, 142000, 156000],
    "Profit": [32000, 35000, 38000, 42000]
})

# Create generator
generator = ReportGeneratorFactory.create("pptx")

# Configure
config = PPTXReportConfig(
    title="Quarterly Performance",
    rows_per_slide=5,
    include_charts=False  # Future: True for charts
)

# Generate
output = generator.generate(data, Path("performance.pptx"), config)
```

#### Advanced PPTX Features

**Pagination**:
```python
# Large dataset - split across multiple slides
config = PPTXReportConfig(
    title="Full Dataset",
    rows_per_slide=10  # 10 rows per slide
)
```

**Charts** (future):
```python
config = PPTXReportConfig(
    title="Sales Dashboard",
    include_charts=True,
    chart_type="bar"  # bar, line, or pie
)
```

**Custom Layouts**:
```python
config = PPTXReportConfig(
    title="Executive Summary",
    layout_name="Title Slide"  # Use specific slide layout
)
```

#### PPTX Features

- ✅ **Automatic Pagination**: Split large tables across slides
- ✅ **Title Slide**: Professional presentation start
- ✅ **Table Formatting**: Clean, readable tables
- 🔜 **Charts**: Bar, line, pie charts (future)
- ✅ **Multiple Slides**: Automatic slide creation

---

## 🔧 Advanced Usage

### Factory Pattern

The factory pattern centralizes generator creation:

```python
from extract_transform_platform.reports import ReportGeneratorFactory

# Create by format
excel_gen = ReportGeneratorFactory.create("excel")
pdf_gen = ReportGeneratorFactory.create("pdf")

# Format aliases work too
xlsx_gen = ReportGeneratorFactory.create("xlsx")  # Same as "excel"

# Check support
if ReportGeneratorFactory.is_format_supported("excel"):
    generator = ReportGeneratorFactory.create("excel")

# List all formats
formats = ReportGeneratorFactory.get_supported_formats()
print(formats)  # ['docx', 'excel', 'pdf', 'pptx', 'xlsx']
```

### Custom Generators

Register custom report generators:

```python
from extract_transform_platform.reports import (
    BaseReportGenerator,
    ReportGeneratorFactory,
    ReportConfig
)
from pathlib import Path
from typing import Any

class CustomReportGenerator(BaseReportGenerator):
    """Custom report generator."""

    def generate(self, data: Any, output_path: Path, config: ReportConfig) -> Path:
        """Generate custom report."""
        # Validate inputs
        self._validate_output_path(output_path, ".custom")
        self._validate_data_not_empty(data, "Custom data")

        # Convert to DataFrame
        df = self._to_dataframe(data)

        # Generate custom report
        # ... implementation ...

        return output_path.absolute()

# Register custom generator
ReportGeneratorFactory.register("custom", CustomReportGenerator)

# Use custom generator
generator = ReportGeneratorFactory.create("custom")
```

### Error Handling

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    ExcelReportConfig
)
from pathlib import Path

try:
    # Create generator
    generator = ReportGeneratorFactory.create("excel")

    # Configure
    config = ExcelReportConfig(title="Report")

    # Generate
    output = generator.generate(data, Path("report.xlsx"), config)
    print(f"✅ Report generated: {output}")

except ValueError as e:
    # Invalid format or configuration
    print(f"❌ Configuration error: {e}")

except TypeError as e:
    # Wrong config type or data format
    print(f"❌ Type error: {e}")

except IOError as e:
    # File write error
    print(f"❌ File error: {e}")
```

### Data Source Conversions

The platform automatically converts various data formats:

```python
# DataFrame (preferred)
import pandas as pd
data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

# Dict (single row)
data = {"name": "Alice", "age": 30}

# Dict (columnar)
data = {"name": ["Alice", "Bob"], "age": [30, 25]}

# List of dicts (multiple rows)
data = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
]

# List of lists (no column names)
data = [["Alice", 30], ["Bob", 25]]

# List of values (single column)
data = [1, 2, 3, 4, 5]

# All formats work with any generator
generator.generate(data, Path("report.xlsx"), config)
```

### Multi-Format Workflow

Generate the same report in multiple formats:

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    ExcelReportConfig,
    PDFReportConfig,
    DOCXReportConfig
)
import pandas as pd
from pathlib import Path

# Prepare data once
data = pd.DataFrame({
    "Product": ["Widget A", "Widget B"],
    "Sales": [1500, 2300]
})

# Generate Excel version
excel_gen = ReportGeneratorFactory.create("excel")
excel_config = ExcelReportConfig(title="Sales Report", freeze_header=True)
excel_gen.generate(data, Path("report.xlsx"), excel_config)

# Generate PDF version
pdf_gen = ReportGeneratorFactory.create("pdf")
pdf_config = PDFReportConfig(title="Sales Report", table_style="fancy")
pdf_gen.generate(data, Path("report.pdf"), pdf_config)

# Generate DOCX version
docx_gen = ReportGeneratorFactory.create("docx")
docx_config = DOCXReportConfig(title="Sales Report")
docx_gen.generate(data, Path("report.docx"), docx_config)

print("✅ Generated 3 report formats!")
```

---

## 📚 Examples

### Example 1: Financial Report (Excel)

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    ExcelReportConfig
)
import pandas as pd
from pathlib import Path

# Financial data
data = pd.DataFrame({
    "Account": ["Revenue", "Cost of Goods Sold", "Gross Profit", "Operating Expenses"],
    "Q1": [500000, 300000, 200000, 100000],
    "Q2": [550000, 320000, 230000, 110000],
    "Q3": [580000, 340000, 240000, 115000],
    "Q4": [620000, 360000, 260000, 120000]
})

# Create generator
generator = ReportGeneratorFactory.create("excel")

# Configure
config = ExcelReportConfig(
    title="Financial Report 2024",
    author="Finance Department",
    sheet_name="Income Statement",
    freeze_header=True,
    auto_filter=True,
    column_widths={"Account": 25}  # Wide account column
)

# Generate
output = generator.generate(data, Path("financial_report.xlsx"), config)
print(f"✅ Financial report: {output}")
```

### Example 2: Invoice (PDF)

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    PDFReportConfig
)
import pandas as pd
from pathlib import Path

# Invoice line items
data = pd.DataFrame({
    "Description": ["Consulting Services", "Software License", "Support (1 year)"],
    "Quantity": [40, 1, 1],
    "Unit Price": [150.00, 2500.00, 1200.00],
    "Total": [6000.00, 2500.00, 1200.00]
})

# Create generator
generator = ReportGeneratorFactory.create("pdf")

# Configure
config = PDFReportConfig(
    title="Invoice #INV-2024-001",
    author="ABC Company",
    table_style="fancy",
    include_page_numbers=True,
    header_text="ABC Company - 123 Main St, City, State",
    footer_text="Payment due within 30 days. Thank you for your business!"
)

# Generate
output = generator.generate(data, Path("invoice_001.pdf"), config)
print(f"✅ Invoice: {output}")
```

### Example 3: Project Status (DOCX)

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    DOCXReportConfig
)
import pandas as pd
from pathlib import Path

# Project tasks
data = pd.DataFrame({
    "Task": ["Requirements", "Design", "Development", "Testing", "Deployment"],
    "Owner": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "Status": ["Complete", "Complete", "In Progress", "Pending", "Pending"],
    "Due Date": ["2024-01-15", "2024-02-01", "2024-03-15", "2024-04-01", "2024-04-15"]
})

# Create generator
generator = ReportGeneratorFactory.create("docx")

# Configure
config = DOCXReportConfig(
    title="Project Status Report - Q1 2024",
    author="Project Manager",
    heading_level=1,
    table_style="Light Grid Accent 1",
    table_alignment="center",
    font_name="Calibri",
    font_size=11
)

# Generate
output = generator.generate(data, Path("project_status.docx"), config)
print(f"✅ Project status: {output}")
```

### Example 4: Sales Dashboard (PPTX)

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    PPTXReportConfig
)
import pandas as pd
from pathlib import Path

# Quarterly sales
data = pd.DataFrame({
    "Quarter": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
    "Revenue": [1250000, 1380000, 1420000, 1560000],
    "Units Sold": [5200, 5600, 5800, 6300],
    "Avg Price": [240, 246, 245, 248]
})

# Create generator
generator = ReportGeneratorFactory.create("pptx")

# Configure
config = PPTXReportConfig(
    title="2024 Sales Performance",
    author="Sales Team",
    layout_name="Title Slide",
    rows_per_slide=10
)

# Generate
output = generator.generate(data, Path("sales_dashboard.pptx"), config)
print(f"✅ Sales dashboard: {output}")
```

---

## 🐛 Troubleshooting

### Common Errors

#### ValueError: Unsupported report format

**Error**:
```
ValueError: Unsupported report format: 'xls'. Supported formats: docx, excel, pdf, pptx, xlsx
```

**Solution**:
```python
# Use supported formats only
generator = ReportGeneratorFactory.create("excel")  # ✅
generator = ReportGeneratorFactory.create("xls")    # ❌
```

#### ValueError: Output path must have .xlsx extension

**Error**:
```
ValueError: Output path must have .xlsx extension, got .xls
```

**Solution**:
```python
# Use correct extension for each format
generator.generate(data, Path("report.xlsx"), config)  # ✅ Excel
generator.generate(data, Path("report.pdf"), config)   # ✅ PDF
generator.generate(data, Path("report.xls"), config)   # ❌ Wrong extension
```

#### TypeError: ExcelReportGenerator requires ExcelReportConfig

**Error**:
```
TypeError: ExcelReportGenerator requires ExcelReportConfig, got PDFReportConfig
```

**Solution**:
```python
# Match config type to generator format
from extract_transform_platform.reports import ExcelReportConfig

excel_gen = ReportGeneratorFactory.create("excel")
config = ExcelReportConfig(title="Report")  # ✅ Match
excel_gen.generate(data, Path("report.xlsx"), config)
```

#### ValueError: Report data cannot be empty

**Error**:
```
ValueError: Report data cannot be empty
```

**Solution**:
```python
# Ensure data is not empty
if data is None or (isinstance(data, pd.DataFrame) and data.empty):
    print("❌ No data to report")
else:
    generator.generate(data, Path("report.xlsx"), config)
```

#### IOError: Permission denied

**Error**:
```
IOError: [Errno 13] Permission denied: 'report.xlsx'
```

**Solution**:
```python
# Close file if open in Excel/viewer
# Or use different filename
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output = Path(f"report_{timestamp}.xlsx")
generator.generate(data, output, config)
```

### Performance Issues

#### Large Dataset (10,000+ rows)

**Problem**: Report generation takes >5 seconds

**Solutions**:
```python
# 1. Use Excel instead of PDF (PDF is slower for large tables)
generator = ReportGeneratorFactory.create("excel")

# 2. Disable summary sheet (reduces processing)
config = ExcelReportConfig(
    title="Large Report",
    include_summary=False  # Skip statistics
)

# 3. Consider pagination for PPTX
config = PPTXReportConfig(
    title="Large Dataset",
    rows_per_slide=20  # Split into manageable slides
)
```

#### Memory Usage

**Problem**: High memory usage with large reports

**Solution**:
```python
# Process in chunks for very large datasets
import pandas as pd

chunk_size = 1000
for i, chunk in enumerate(pd.read_csv("large_data.csv", chunksize=chunk_size)):
    config = ExcelReportConfig(
        title=f"Report Part {i+1}",
        sheet_name=f"Data_{i+1}"
    )
    generator.generate(chunk, Path(f"report_part_{i+1}.xlsx"), config)
```

---

## ✅ Best Practices

### 1. Choose the Right Format

```python
# Financial analysis → Excel
# Enables formulas, charts, pivot tables
generator = ReportGeneratorFactory.create("excel")

# Print documents → PDF
# Fixed layout, professional appearance
generator = ReportGeneratorFactory.create("pdf")

# Business documents → DOCX
# Editable, collaborative, corporate templates
generator = ReportGeneratorFactory.create("docx")

# Presentations → PPTX
# Visual, concise, executive-friendly
generator = ReportGeneratorFactory.create("pptx")
```

### 2. Use Descriptive Titles

```python
# ❌ Vague
config = ExcelReportConfig(title="Report")

# ✅ Descriptive
config = ExcelReportConfig(title="Q4 2024 Sales Report - North America Region")
```

### 3. Configure Appropriately

```python
# Excel: Enable productivity features
config = ExcelReportConfig(
    title="Sales Analysis",
    freeze_header=True,   # ✅ Easier navigation
    auto_filter=True,     # ✅ Enable filtering
    column_widths={...}   # ✅ Readable columns
)

# PDF: Professional appearance
config = PDFReportConfig(
    title="Invoice",
    table_style="fancy",        # ✅ Professional look
    include_page_numbers=True,  # ✅ Easy reference
    header_text="Company Name"  # ✅ Branding
)
```

### 4. Handle Errors Gracefully

```python
from pathlib import Path

def generate_report_safe(data, format="excel"):
    """Generate report with error handling."""
    try:
        generator = ReportGeneratorFactory.create(format)
        config = ExcelReportConfig(title="Report")
        output = generator.generate(data, Path(f"report.{format}"), config)
        return output
    except ValueError as e:
        print(f"❌ Invalid configuration: {e}")
        return None
    except IOError as e:
        print(f"❌ File error: {e}")
        return None
```

### 5. Validate Data Before Generation

```python
import pandas as pd

def validate_and_generate(data):
    """Validate data before generating report."""
    # Check if data is empty
    if data is None or (isinstance(data, pd.DataFrame) and data.empty):
        print("❌ No data to report")
        return None

    # Check if DataFrame has columns
    if isinstance(data, pd.DataFrame) and len(data.columns) == 0:
        print("❌ DataFrame has no columns")
        return None

    # Generate report
    generator = ReportGeneratorFactory.create("excel")
    config = ExcelReportConfig(title="Validated Report")
    return generator.generate(data, Path("report.xlsx"), config)
```

### 6. Use Type Hints

```python
from pathlib import Path
from typing import Any
import pandas as pd
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    ExcelReportConfig,
    IReportGenerator
)

def create_report(
    data: pd.DataFrame,
    title: str,
    output_path: Path,
    format: str = "excel"
) -> Path:
    """Generate report with type safety.

    Args:
        data: Report data as DataFrame
        title: Report title
        output_path: Output file path
        format: Report format (excel, pdf, docx, pptx)

    Returns:
        Path to generated report
    """
    generator: IReportGenerator = ReportGeneratorFactory.create(format)
    config = ExcelReportConfig(title=title)
    return generator.generate(data, output_path, config)
```

### 7. Multi-Format Strategy

```python
def generate_all_formats(data: pd.DataFrame, base_name: str) -> dict:
    """Generate report in all formats.

    Args:
        data: Report data
        base_name: Base filename (without extension)

    Returns:
        Dict of format -> output path
    """
    from extract_transform_platform.reports import (
        ReportGeneratorFactory,
        ExcelReportConfig,
        PDFReportConfig,
        DOCXReportConfig,
        PPTXReportConfig
    )

    outputs = {}

    # Excel
    excel_gen = ReportGeneratorFactory.create("excel")
    excel_config = ExcelReportConfig(title=base_name)
    outputs["excel"] = excel_gen.generate(
        data, Path(f"{base_name}.xlsx"), excel_config
    )

    # PDF
    pdf_gen = ReportGeneratorFactory.create("pdf")
    pdf_config = PDFReportConfig(title=base_name)
    outputs["pdf"] = pdf_gen.generate(
        data, Path(f"{base_name}.pdf"), pdf_config
    )

    # DOCX
    docx_gen = ReportGeneratorFactory.create("docx")
    docx_config = DOCXReportConfig(title=base_name)
    outputs["docx"] = docx_gen.generate(
        data, Path(f"{base_name}.docx"), docx_config
    )

    # PPTX
    pptx_gen = ReportGeneratorFactory.create("pptx")
    pptx_config = PPTXReportConfig(title=base_name)
    outputs["pptx"] = pptx_gen.generate(
        data, Path(f"{base_name}.pptx"), pptx_config
    )

    return outputs
```

---

## 🔗 Related Documentation

- **[Report Generator API Reference](../api/REPORT_GENERATOR_API.md)** - Complete API documentation
- **[Report Integration Guide](REPORT_INTEGRATION.md)** - Integration with platform components
- **[Quick Start Guide](QUICK_START.md)** - Platform setup and basics
- **[Platform Usage Guide](PLATFORM_USAGE.md)** - General platform patterns

---

## 📝 Summary

The IReportGenerator system provides a unified, type-safe interface for generating professional reports in 4 formats:

- ✅ **Excel**: Data analysis, spreadsheets, financial reports
- ✅ **PDF**: Print-ready documents, invoices, formal reports
- ✅ **DOCX**: Business documents, proposals, technical docs
- ✅ **PPTX**: Presentations, dashboards, executive summaries

**Key Benefits**:
- Single interface for all formats
- Type-safe Pydantic configuration
- Professional formatting built-in
- 97% test coverage, production-ready
- Flexible data sources (DataFrame, dict, list)

**Next Steps**:
1. Try the [Quick Start](#quick-start-5-minutes) example
2. Explore [format-specific guides](#format-specific-guides)
3. Review [API reference](../api/REPORT_GENERATOR_API.md) for details
4. See [integration guide](REPORT_INTEGRATION.md) for platform integration

---

**Status**: Production-ready (97% coverage, 135/135 tests passing)
**Ticket**: 1M-360 (IReportGenerator Multi-Format Support)
**Package**: `extract_transform_platform.reports`
