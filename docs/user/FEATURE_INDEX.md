# EDGAR Platform - Feature Index

**Last Updated**: 2025-12-03
**Version**: 2.0

Complete index of all platform features with usage examples and workflows.

---

## Table of Contents

- [File Transform Workflows](#file-transform-workflows)
- [Report Generation](#report-generation)
- [Interactive Confidence Threshold](#interactive-confidence-threshold)
- [Supported Transformations](#supported-transformations)
- [Performance Benchmarks](#performance-benchmarks)

---

## File Transform Workflows

Transform files (Excel, PDF, DOCX, PPTX) into structured data using example-driven approach.

### Excel File Transform ✅

**Status**: Phase 1 Complete (398 LOC, 80% coverage, 35/35 validations passing)

#### Quick Start: Transform Excel → JSON

```bash
# 1. Create project with Excel source
cd projects/
mkdir my_excel_project
cd my_excel_project
mkdir input examples output

# 2. Add your Excel file
cp /path/to/your/file.xlsx input/data.xlsx

# 3. Create 2-3 transformation examples
# (See employee_roster POC for format)

# 4. Configure project.yaml
cat > project.yaml <<EOF
name: My Excel Transform
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

# 5. Run analysis and generate code
python -m edgar_analyzer analyze-project projects/my_excel_project/
python -m edgar_analyzer generate-code projects/my_excel_project/

# 6. Run extraction
python -m edgar_analyzer run-extraction projects/my_excel_project/
```

#### Example: Employee Roster POC

**Source Excel**:
```
| employee_id | first_name | last_name | department  | hire_date  | salary | is_manager |
| E1001       | Alice      | Johnson   | Engineering | 2020-03-15 | 95000  | Yes        |
```

**Transformed Output**:
```json
{
  "id": "E1001",
  "full_name": "Alice Johnson",
  "dept": "Engineering",
  "hired": "2020-03-15",
  "annual_salary_usd": 95000.0,
  "manager": true
}
```

**Automatic Transformations**:
- ✅ Field renaming (employee_id → id)
- ✅ String concatenation (first_name + last_name → full_name)
- ✅ Type conversions (int → float, "Yes" → true)
- ✅ Boolean normalization ("Yes"/"No" → true/false)

#### Key Features

1. **ExcelDataSource** - Read .xlsx/.xls files with pandas
2. **Schema-aware parsing** - Automatic type inference
3. **Pattern detection** - AI detects 6+ transformation types
4. **Code generation** - Produces type-safe extractors
5. **Validation** - Auto-generated pytest tests

#### Excel Documentation

- **[Excel File Transform Guide](EXCEL_FILE_TRANSFORM.md)** - Complete user guide
- **[ExcelDataSource Technical Reference](../architecture/EXCEL_DATA_SOURCE.md)** - Implementation details
- **[Employee Roster Tutorial](../../projects/employee_roster/TUTORIAL.md)** - Step-by-step walkthrough
- **[Employee Roster POC](../../projects/employee_roster/)** - Working proof-of-concept

---

### PDF File Transform ✅

**Status**: Phase 1 Complete (481 LOC, 77% coverage, 51 tests passing)

#### Quick Start: Transform PDF → JSON

```bash
# 1. Create project with PDF source
cd projects/
mkdir invoice_extraction
cd invoice_extraction
mkdir input examples output

# 2. Add your PDF file
cp /path/to/invoice.pdf input/invoice_001.pdf

# 3. Create 2-3 transformation examples
# (See invoice_transform POC for format)

# 4. Configure project.yaml
cat > project.yaml <<EOF
name: Invoice Extraction
data_source:
  type: pdf
  config:
    file_path: input/invoice_001.pdf
    page_number: 0
    table_strategy: lines
examples:
  - examples/row1.json
  - examples/row2.json
EOF

# 5. Run analysis and generate code
python -m edgar_analyzer analyze-project projects/invoice_extraction/
python -m edgar_analyzer generate-code projects/invoice_extraction/

# 6. Run extraction
python -m edgar_analyzer run-extraction projects/invoice_extraction/
```

#### Example: Invoice Line Items

**Source PDF Table**:
```
| Item       | Quantity | Unit Price | Total   |
| Widget A   | 2        | $15.00     | $30.00  |
| Service B  | 1        | $50.00     | $50.00  |
```

**Transformed Output**:
```json
{
  "product": "Widget A",
  "qty": 2,
  "unit_price_usd": 15.00,
  "line_total_usd": 30.00
}
```

**Automatic Transformations**:
- ✅ Field renaming (Item → product)
- ✅ Currency parsing ($15.00 → 15.00)
- ✅ Type conversions (string → int/float)
- ✅ Table extraction with multiple strategies

#### Key Features

1. **PDFDataSource** - Extract tables from PDF with pdfplumber
2. **Multiple strategies** - Lines, text, or mixed table detection
3. **Bounding box support** - Target specific page regions
4. **Schema-aware parsing** - Automatic type inference
5. **Pattern detection** - AI detects transformation patterns
6. **Code generation** - Produces type-safe extractors

#### Table Extraction Strategies

- **Lines** - For bordered tables (invoices, reports)
- **Text** - For borderless tables (plain text layouts)
- **Mixed** - Hybrid approach (partially bordered tables)

#### PDF Documentation

- **[PDF File Transform Guide](PDF_FILE_TRANSFORM.md)** - Complete user guide
- **[PDFDataSource Technical Reference](../architecture/PDF_DATA_SOURCE.md)** - Implementation details
- **[Invoice Transform POC](../../projects/invoice_transform/)** - Working proof-of-concept

---

## Report Generation

**Status**: Production-ready (97% test coverage, 135/135 tests passing)
**Ticket**: 1M-360 (IReportGenerator Multi-Format Support - FINAL)
**Package**: `extract_transform_platform.reports`

### Multi-Format Report Generation

Generate professional reports in 4 formats using unified interface:
- **Excel** (.xlsx) - Data analysis, spreadsheets, financial reports
- **PDF** (.pdf) - Print-ready documents, invoices, formal reports
- **DOCX** (.docx) - Business documents, proposals, technical docs
- **PPTX** (.pptx) - Presentations, dashboards, executive summaries

### Quick Start: Generate Your First Report

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

# Create generator via factory
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

### Generate Multiple Formats

```python
from extract_transform_platform.reports import (
    ReportGeneratorFactory,
    ExcelReportConfig,
    PDFReportConfig,
    DOCXReportConfig
)

# Excel version
excel_gen = ReportGeneratorFactory.create("excel")
excel_config = ExcelReportConfig(title="Sales Report", freeze_header=True)
excel_gen.generate(data, Path("report.xlsx"), excel_config)

# PDF version
pdf_gen = ReportGeneratorFactory.create("pdf")
pdf_config = PDFReportConfig(title="Sales Report", table_style="fancy")
pdf_gen.generate(data, Path("report.pdf"), pdf_config)

# DOCX version
docx_gen = ReportGeneratorFactory.create("docx")
docx_config = DOCXReportConfig(title="Sales Report")
docx_gen.generate(data, Path("report.docx"), docx_config)

print("✅ Generated 3 report formats!")
```

### CLI Integration (Future)

```bash
# Generate Excel report for project
edgar-analyzer project report my_project --format excel

# Generate PDF report with fancy style
edgar-analyzer project report my_project --format pdf --style fancy

# Generate batch reports (Excel + PDF + DOCX)
edgar-analyzer project report-batch my_project -f excel -f pdf -f docx
```

### Key Features

1. **Unified Interface**: Same API for all 4 formats (Protocol + ABC + Factory pattern)
2. **Type-Safe Configuration**: Pydantic models with runtime validation
3. **Professional Formatting**: Bold headers, colors, alignment, page numbers
4. **Data Source Flexibility**: DataFrame, dict, list, or custom formats
5. **Excel Features**: Freeze panes, auto-filter, custom column widths, summary sheets
6. **PDF Features**: Table styles (grid/simple/fancy), headers/footers, page numbers, orientation
7. **DOCX Features**: Heading levels, 50+ table styles, fonts, page breaks
8. **PPTX Features**: Automatic pagination, multiple slides, charts (future)

### Format Comparison

| Feature | Excel | PDF | DOCX | PPTX |
|---------|-------|-----|------|------|
| **Tables** | ✅ | ✅ | ✅ | ✅ |
| **Formatting** | ✅ | ✅ | ✅ | ✅ |
| **Charts** | 🔜 | 🔜 | 🔜 | ✅ |
| **Formulas** | 🔜 | ❌ | ❌ | ❌ |
| **Freeze Panes** | ✅ | ❌ | ❌ | ❌ |
| **Auto-Filter** | ✅ | ❌ | ❌ | ❌ |
| **Page Numbers** | ❌ | ✅ | ✅ | ✅ |
| **Headers/Footers** | ❌ | ✅ | ✅ | ✅ |

**Legend**: ✅ Supported | 🔜 Future | ❌ Not Applicable

### Documentation

- **[Report Generation Guide](REPORT_GENERATION.md)** - Complete user guide with examples
- **[Report Generator API](../api/REPORT_GENERATOR_API.md)** - Complete API reference
- **[Report Integration Guide](REPORT_INTEGRATION.md)** - Integration patterns

---

## Interactive Confidence Threshold

**Status**: Phase 1 MVP Complete (1M-362) - Production Ready ✅
**Feature**: User-prompted confidence threshold for example-driven workflows
**Test Coverage**: 43/43 tests passing (100%), zero breaking changes

### What This Does

Allows users to select minimum confidence threshold for detected transformation patterns, balancing quality (high confidence) vs coverage (more patterns).

When you provide 2-3 transformation examples, the platform automatically detects patterns and assigns confidence scores (0.0-1.0) based on consistency across examples. You can then **filter** which patterns to include in generated code.

### Quick Start

```bash
# Interactive mode (default) - prompts for threshold selection
edgar-analyzer project generate my_project

# Non-interactive mode (automation) - specify threshold
edgar-analyzer project generate my_project --confidence-threshold 0.8
```

### Interactive Flow

```
1. Pattern Detection:
   ┌─────────────────────────────────────────────┐
   │  Pattern Detection Complete                 │
   ├─────────────────────────────────────────────┤
   │  Detected 5 patterns from 3 examples:       │
   │    • 3 high confidence (≥ 0.9)    60%       │
   │    • 1 medium confidence (0.7-0.89) 20%     │
   │    • 1 low confidence (< 0.7)     20%       │
   └─────────────────────────────────────────────┘

2. Threshold Selection:
   [1] 🛡️  Conservative (0.8) - High confidence only
   [2] ⚖️  Balanced (0.7) [RECOMMENDED] - High + medium
   [3] ⚡ Aggressive (0.6) - All patterns
   [4] 🎯 Custom - Enter custom (0.0-1.0)

3. Pattern Review:
   ✅ Patterns Included (4):
      city (1.0), temperature_c (0.95),
      conditions (0.9), humidity_percent (0.8)

   ❌ Patterns Excluded (1):
      wind_direction (0.65) - Inconsistent results

4. Confirmation:
   Continue with 4 patterns? [Y/n]
```

### Threshold Presets

| Preset | Threshold | Use Case | Example |
|--------|-----------|----------|---------|
| **Conservative** | 0.8 | Production systems, critical data | Financial records, healthcare data |
| **Balanced** | 0.7 | Most use cases (recommended) | Internal tools, dashboards |
| **Aggressive** | 0.6 | Exploratory analysis, R&D | Proof-of-concepts, research |
| **Custom** | 0.0-1.0 | Advanced users, specific needs | Fine-tuned control |

### Pattern Confidence Levels

- **High (≥ 0.9)**: Pattern appears in 90%+ of examples with consistent behavior
- **Medium (0.7-0.89)**: Pattern appears in 70-89% of examples with mostly consistent behavior
- **Low (< 0.7)**: Pattern appears in <70% of examples with inconsistent behavior

### Non-Interactive Mode (CI/CD)

```bash
# Conservative threshold (production)
edgar-analyzer project generate my_project \
  --confidence-threshold 0.8 \
  --no-interactive

# Balanced threshold (staging)
edgar-analyzer project generate my_project \
  --confidence-threshold 0.7 \
  --no-interactive

# Custom threshold
edgar-analyzer project generate my_project \
  --confidence-threshold 0.75
```

### Examples

**Employee Roster** (high-quality data):
```bash
# Clean Excel data → Use Balanced (0.7)
edgar-analyzer project generate employee_roster --confidence-threshold 0.7
# Result: 7/7 patterns included (all reliable)
```

**Web Scraping** (noisy data):
```bash
# Inconsistent web content → Use Conservative (0.8)
edgar-analyzer project generate news_scraper --confidence-threshold 0.8
# Result: 4/6 patterns included (excludes unreliable author/reading_time)
```

**Legacy Data** (mixed quality):
```bash
# Mixed quality → Use Custom (0.75)
edgar-analyzer project generate legacy_migration --confidence-threshold 0.75
# Result: 7/12 patterns included (fine-tuned balance)
```

### Configuration Persistence

Optionally save threshold to project configuration:

```yaml
# projects/my_project/project.yaml
project:
  name: my_project
  confidence_threshold: 0.7  # Saved for future runs
```

**Documentation**: See [Complete Confidence Threshold Guide](CONFIDENCE_THRESHOLD.md) for detailed usage, examples, troubleshooting, and best practices.

---

## Supported Transformations

| Type | Example | Detection |
|------|---------|-----------|
| **Field Rename** | `employee_id` → `id` | Schema comparison |
| **Concatenation** | `first_name + last_name` → `full_name` | Value matching |
| **Type Convert** | `salary: 95000` (int) → `95000.0` (float) | Type change |
| **Boolean** | `"Yes"` → `true`, `"No"` → `false` | Pattern recognition |
| **Value Mapping** | `"A"` → `"Active"`, `"I"` → `"Inactive"` | Discrete mapping |
| **Field Extract** | `"alice@ex.com"` → `"ex.com"` | Substring patterns |
| **Nested Access** | `data.main.temp` → `temperature` | Path navigation |
| **List Aggregation** | `[1, 2, 3]` → `sum=6` | List operations |
| **Conditional** | `if age > 18 then "adult"` | Conditional logic |
| **Date Parsing** | `"2023-01-15"` → `datetime` | Date parsing |
| **Math Operation** | `price * quantity` → `total` | Mathematical ops |
| **String Formatting** | `"USD {:.2f}".format(val)` | String formatting |
| **Default Value** | `null` → `"Unknown"` | Default handling |
| **Custom** | User-defined transformation | Custom logic |

---

## Performance Benchmarks

### Excel File Transform

| Rows | Columns | File Size | Read Time | Memory |
|------|---------|-----------|-----------|--------|
| 100 | 7 | 15 KB | 45 ms | 3 MB |
| 1,000 | 7 | 120 KB | 180 ms | 12 MB |
| 10,000 | 7 | 1.2 MB | 950 ms | 85 MB |

**End-to-End**: <10 seconds (read → analyze → generate → validate)

### PDF File Transform

| Pages | Tables | File Size | Extract Time | Memory |
|-------|--------|-----------|--------------|--------|
| 1 | 1 | 50 KB | 120 ms | 5 MB |
| 5 | 3 | 200 KB | 450 ms | 18 MB |
| 20 | 10 | 1 MB | 2.1 s | 65 MB |

**End-to-End**: <15 seconds (extract → analyze → generate → validate)

### Report Generation

| Rows | Columns | File Size | Excel Time | PDF Time | Memory |
|------|---------|-----------|------------|----------|--------|
| 100 | 7 | 15 KB | ~50ms | ~80ms | 3 MB |
| 1,000 | 7 | 120 KB | ~200ms | ~400ms | 12 MB |
| 10,000 | 7 | 1.2 MB | ~1.5s | ~3s | 85 MB |

**Performance**: 13-312x faster than requirements (5s target)

### Pattern Detection

| Examples | Patterns | Fields | Detection Time | Memory |
|----------|----------|--------|----------------|--------|
| 3 | 5 | 10 | <100ms | 2 MB |
| 5 | 10 | 25 | <250ms | 5 MB |
| 10 | 20 | 50 | <500ms | 12 MB |

**Filtering**: <1ms for 100 patterns (50x faster than 50ms requirement)

---

## Next Steps

1. **Read Platform Overview**: [PLATFORM_OVERVIEW.md](PLATFORM_OVERVIEW.md) - Complete platform guide
2. **Check Development Guide**: [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development patterns
3. **Review API Docs**: [../api/PLATFORM_API.md](../api/PLATFORM_API.md) - Detailed API reference

---

**Last Updated**: 2025-12-03
**Contact**: See [PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md) for full project context.
