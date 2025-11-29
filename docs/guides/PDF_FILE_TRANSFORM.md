# PDF File Transform Guide

Transform PDF documents with structured tables into structured data using the EDGAR platform's example-driven approach.

---

## 📋 Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Step-by-Step Tutorial](#step-by-step-tutorial)
- [Configuration Reference](#configuration-reference)
- [Table Extraction Strategies](#table-extraction-strategies)
- [Bounding Box Selection](#bounding-box-selection)
- [Transformation Patterns](#transformation-patterns)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)
- [Next Steps](#next-steps)

---

## 🎯 Overview

### What This Does

The PDF file transform capability allows you to extract and transform data from PDF documents containing structured tables into JSON format without writing any code. You simply:

1. Provide your source PDF file with table data
2. Show 2-3 examples of how rows should be transformed
3. The platform analyzes your examples and generates extraction code
4. Run the generated code on your full dataset

**Key Benefits:**
- ✅ No coding required - just configure and provide examples
- ✅ Automatic table detection and extraction
- ✅ Multiple extraction strategies (bordered tables, borderless tables)
- ✅ Bounding box support for multi-section documents
- ✅ Type-safe transformations with validation
- ✅ Handles field renaming, type conversions, calculations
- ✅ 90% code reuse from proven Excel template
- ✅ Production-ready with error handling and edge cases

**Common Use Cases:**
- **Invoice extraction** - Line items, totals, vendor information
- **Financial reports** - Balance sheets, income statements, cash flow
- **Form data** - Application forms, survey results, questionnaires
- **Receipts and statements** - Purchase receipts, bank statements
- **Product catalogs** - Inventory lists, price sheets, specifications
- **Scientific data** - Lab results, experimental data, measurements

### How It Works

The platform uses the same **example-driven approach** proven with the Weather API and Excel templates:

```
PDF File (input)
    ↓
Provide 2-3 transformation examples
    ↓
Schema Analyzer detects patterns
    ↓
AI generates extraction code
    ↓
Structured JSON (output)
```

**Example**: Transform invoice line items

**Input** (PDF table row):
```
Item          | Quantity | Unit Price | Total
Widget A      | 2        | $15.00     | $30.00
```

**Output** (JSON):
```json
{
  "product": "Widget A",
  "qty": 2,
  "unit_price_usd": 15.00,
  "line_total_usd": 30.00
}
```

The platform automatically detects:
- Field renaming (Item → product, Quantity → qty)
- Currency parsing ($15.00 → 15.00)
- Type conversions (string → float)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- PDF file with structured table data
- pdfplumber library installed (`pip install pdfplumber`)
- At least 2-3 example rows of data

### 5-Minute Setup

#### 1. Create Project Structure

```bash
# Create new project directory
cd projects/
mkdir invoice_extraction
cd invoice_extraction

# Create required directories
mkdir input examples output
```

#### 2. Add Your PDF File

```bash
# Copy your PDF file to input/
cp /path/to/your/invoice.pdf input/invoice_001.pdf
```

#### 3. Create project.yaml

```yaml
name: Invoice Line Item Extraction
description: Transform PDF invoice line items into structured format
version: 1.0.0

data_source:
  type: pdf
  config:
    file_path: input/invoice_001.pdf
    page_number: 0          # First page (0-indexed)
    table_strategy: lines   # Use line borders to detect table

examples:
  - examples/row1.json
  - examples/row2.json
  - examples/row3.json

target_schema:
  # Your desired output fields
  product: string
  qty: integer
  unit_price_usd: number
  line_total_usd: number
```

#### 4. Create Example Transformations

Create `examples/row1.json`:

```json
{
  "example_id": "invoice_line_1",
  "description": "First line item from invoice",
  "input": {
    "Item": "Widget A",
    "Quantity": "2",
    "Unit Price": "$15.00",
    "Total": "$30.00"
  },
  "output": {
    "product": "Widget A",
    "qty": 2,
    "unit_price_usd": 15.00,
    "line_total_usd": 30.00
  }
}
```

Repeat for 2-3 rows to show transformation patterns.

#### 5. Generate and Run

```bash
# Analyze examples and generate extraction code
python -m edgar_analyzer extract-project projects/invoice_extraction/

# Run extraction on full PDF
python -m edgar_analyzer run-extraction projects/invoice_extraction/output/extract.py
```

**Done!** Your transformed data is in `output/extracted_data.json`

---

## 📋 Prerequisites

### Required Software

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **pdfplumber Library**
   ```bash
   pip install pdfplumber
   ```

   *Note*: pdfplumber requires Pillow (PIL) which is installed automatically

3. **pandas Library** (usually already installed)
   ```bash
   pip install pandas
   ```

### PDF Requirements

Your PDF file should have:

1. **Structured table data** - Data organized in rows and columns
2. **Consistent formatting** - Table structure is the same throughout
3. **Text-based content** - Not scanned images (OCR needed for scans)
4. **Clear table boundaries** - Either visible borders or consistent spacing

**✅ Supported PDF Types:**
- Invoices with line item tables
- Financial reports with data tables
- Form data with structured fields
- Database or Excel exports saved as PDF
- Computer-generated PDFs with table structures

**❌ Currently Not Supported:**
- Scanned documents (images) without OCR
- Hand-written forms
- PDFs with only unstructured text
- PDFs with heavily nested or merged cells
- Multi-page table extraction (Phase 1 limitation)

### Knowledge Requirements

- Basic understanding of JSON format
- Familiarity with your source data structure
- Ability to identify transformation patterns

---

## 📖 Step-by-Step Tutorial

Follow the complete invoice extraction example to learn the full workflow.

### Step 1: Understand Your Source Data

Open your PDF file and identify:
- **Table location**: Which page contains the table?
- **Table structure**: Does it have visible borders or rely on spacing?
- **Column headers**: What are the column names?
- **Data types**: What type is each column (text, number, currency, date)?
- **Table boundaries**: Does the table have surrounding text or multiple sections?

**Example**: Invoice with line items (input/invoice_001.pdf)

| Column | Type | Description |
|--------|------|-------------|
| Item | string | Product name or description |
| Quantity | integer | Number of units |
| Unit Price | currency | Price per unit (with $ symbol) |
| Total | currency | Line total (Quantity × Unit Price) |

**Visual Analysis**:
- Page: 0 (first page)
- Table strategy: "lines" (has visible borders)
- Header row: First row of table
- Data rows: 5 line items
- Bounding box: Not needed (table is main content)

### Step 2: Choose Table Extraction Strategy

PDF tables can be structured in different ways. Choose the right strategy:

#### Lines Strategy (Recommended for Invoices)
**Use when**: Table has visible borders/lines
**Best for**: Invoices, reports, formal documents
**Setting**: `table_strategy: lines`

```yaml
data_source:
  config:
    table_strategy: lines  # Use line borders
```

#### Text Strategy (For Borderless Tables)
**Use when**: Table has no borders, relies on spacing
**Best for**: Plain text reports, simple layouts
**Setting**: `table_strategy: text`

```yaml
data_source:
  config:
    table_strategy: text  # Use text positioning
```

#### Mixed Strategy (Hybrid)
**Use when**: Table has some borders but not all
**Best for**: Complex layouts, partially bordered tables
**Setting**: `table_strategy: mixed`

```yaml
data_source:
  config:
    table_strategy: mixed  # Vertical lines + text spacing
```

**For our invoice example**, we'll use `lines` strategy since invoices typically have clear borders.

### Step 3: Design Your Output Schema

Decide what your transformed output should look like:

```json
{
  "product": "Widget A",
  "qty": 2,
  "unit_price_usd": 15.00,
  "line_total_usd": 30.00
}
```

**Transformations needed**:
1. Rename `Item` → `product`
2. Rename `Quantity` → `qty` (convert to integer)
3. Parse `Unit Price` ("$15.00") → `unit_price_usd` (15.00)
4. Parse `Total` ("$30.00") → `line_total_usd` (30.00)

**Currency Parsing Pattern**:
- Remove "$" symbol
- Convert to float
- Store as numeric value

### Step 4: Create Example Files

Create transformation examples showing input → output pairs.

**examples/widget_a.json** (Row 1):
```json
{
  "example_id": "invoice_001_widget_a",
  "description": "Widget A line item with currency parsing",
  "input": {
    "Item": "Widget A",
    "Quantity": "2",
    "Unit Price": "$15.00",
    "Total": "$30.00"
  },
  "output": {
    "product": "Widget A",
    "qty": 2,
    "unit_price_usd": 15.00,
    "line_total_usd": 30.00
  }
}
```

**examples/service_b.json** (Row 2):
```json
{
  "example_id": "invoice_001_service_b",
  "description": "Service B with different quantity and pricing",
  "input": {
    "Item": "Service B",
    "Quantity": "1",
    "Unit Price": "$50.00",
    "Total": "$50.00"
  },
  "output": {
    "product": "Service B",
    "qty": 1,
    "unit_price_usd": 50.00,
    "line_total_usd": 50.00
  }
}
```

**examples/widget_c.json** (Row 3):
```json
{
  "example_id": "invoice_001_widget_c",
  "description": "Widget C with fractional quantity",
  "input": {
    "Item": "Widget C",
    "Quantity": "3",
    "Unit Price": "$8.50",
    "Total": "$25.50"
  },
  "output": {
    "product": "Widget C",
    "qty": 3,
    "unit_price_usd": 8.50,
    "line_total_usd": 25.50
  }
}
```

**Why 2-3 examples?**
- 1 example: AI might overfit (too specific to that row)
- 2-3 examples: AI finds patterns (optimal balance)
- 5+ examples: Diminishing returns (more work, same accuracy)

**Example Selection Tips**:
- Choose rows with different values (variety)
- Include edge cases (decimals, large numbers)
- Show all transformation patterns you need
- Use real data from your PDF

### Step 5: Configure project.yaml

Create complete project configuration:

```yaml
name: Invoice Line Item Extraction
description: Transform invoice PDF line items into structured JSON
version: 1.0.0

data_source:
  type: pdf
  config:
    file_path: input/invoice_001.pdf
    page_number: 0        # First page (0-indexed)
    table_strategy: lines # Use line borders to detect table
    # Optional: Use bounding box if table is in specific area
    # table_bbox: [50, 100, 550, 400]  # [x0, top, x1, bottom]

examples:
  - examples/widget_a.json
  - examples/service_b.json
  - examples/widget_c.json

transformations:
  # These are auto-detected from examples (documentation only)
  - type: field_rename
    description: Rename Item to product
  - type: field_rename
    description: Rename Quantity to qty
  - type: currency_parsing
    description: Parse Unit Price ($15.00 → 15.00)
  - type: currency_parsing
    description: Parse Total ($30.00 → 30.00)
  - type: type_conversion
    description: Convert qty to integer

target_schema:
  product: string
  qty: integer
  unit_price_usd: number
  line_total_usd: number
```

### Step 6: Analyze and Generate Code

Run the platform analyzer:

```bash
# Navigate to project root
cd /path/to/edgar

# Analyze project
python -m edgar_analyzer extract-project projects/invoice_extraction/

# Output:
# ✓ Loaded PDF file: page 0, 5 rows, 4 columns
# ✓ Parsed 3 examples
# ✓ Detected 5 transformation patterns
# ✓ Generated extraction code: output/invoice_extractor.py
# ✓ Generated validation tests: output/test_extractor.py
```

The platform generates:
- **extractor.py**: Extraction logic with transformations
- **models.py**: Pydantic models for validation
- **test_extractor.py**: Automated tests

### Step 7: Review Generated Code

The generated `extractor.py` contains type-safe transformation logic:

```python
from pydantic import BaseModel
from typing import Optional

class InvoiceLineItem(BaseModel):
    product: str
    qty: int
    unit_price_usd: float
    line_total_usd: float

def parse_currency(value: str) -> float:
    """Parse currency string to float (e.g., '$15.00' → 15.00)"""
    if value is None:
        return 0.0
    return float(value.replace('$', '').replace(',', '').strip())

def transform_row(row: dict) -> InvoiceLineItem:
    return InvoiceLineItem(
        product=row["Item"],
        qty=int(row["Quantity"]),
        unit_price_usd=parse_currency(row["Unit Price"]),
        line_total_usd=parse_currency(row["Total"])
    )
```

**Generated Code Features**:
- Type-safe with Pydantic models
- Currency parsing helper function
- Error handling for None/null values
- Validation ensures data quality

### Step 8: Run Extraction

Execute on full PDF:

```bash
# Run extraction
python -m edgar_analyzer run-extraction projects/invoice_extraction/output/extract.py

# View results
cat projects/invoice_extraction/output/extracted_data.json
```

Output:
```json
[
  {
    "product": "Widget A",
    "qty": 2,
    "unit_price_usd": 15.00,
    "line_total_usd": 30.00
  },
  {
    "product": "Service B",
    "qty": 1,
    "unit_price_usd": 50.00,
    "line_total_usd": 50.00
  },
  {
    "product": "Widget C",
    "qty": 3,
    "unit_price_usd": 8.50,
    "line_total_usd": 25.50
  }
]
```

### Step 9: Validate Results

Run generated tests:

```bash
# Run validation tests
pytest projects/invoice_extraction/output/test_extractor.py

# Output:
# test_transform_widget_a PASSED
# test_transform_service_b PASSED
# test_transform_widget_c PASSED
# test_all_fields_present PASSED
# test_type_validation PASSED
# test_currency_parsing PASSED
# ======================== 6 passed in 0.14s ========================
```

**Success!** All transformations match examples exactly.

### Step 10: Verify Manually

Spot-check random rows:

```python
# Load extracted data
import json

with open('output/extracted_data.json') as f:
    data = json.load(f)

# Check first item
print(f"Product: {data[0]['product']}")
print(f"Quantity: {data[0]['qty']}")
print(f"Unit Price: ${data[0]['unit_price_usd']:.2f}")
print(f"Line Total: ${data[0]['line_total_usd']:.2f}")

# Verify calculation
calculated_total = data[0]['qty'] * data[0]['unit_price_usd']
assert data[0]['line_total_usd'] == calculated_total, "Total mismatch!"
```

---

## 🔧 Configuration Reference

### data_source.type: pdf

Required data source type for PDF files.

```yaml
data_source:
  type: pdf
  config:
    # ... PDF-specific configuration
```

### file_path

**Type**: String (path to file)
**Required**: Yes
**Description**: Path to PDF file relative to project root

**Examples**:
```yaml
file_path: input/invoice.pdf              # Simple path
file_path: input/invoices/2024/jan.pdf    # Nested directory
file_path: /absolute/path/to/file.pdf     # Absolute path
```

### page_number

**Type**: Integer or "all"
**Default**: 0 (first page)
**Description**: Which page to extract from (0-indexed)

**Examples**:
```yaml
page_number: 0      # First page (default)
page_number: 1      # Second page
page_number: 2      # Third page
page_number: "all"  # All pages (Phase 2 - not yet implemented)
```

**Note**: PDF pages are 0-indexed (first page = 0, second page = 1, etc.)

### table_strategy

**Type**: String
**Options**: "lines", "text", "mixed"
**Default**: "lines"
**Description**: How to detect table structure

**Options Explained**:

#### "lines" - Line-Based Detection
Use when table has visible borders/lines.

```yaml
table_strategy: lines
```

**Best for**:
- Invoices with bordered tables
- Financial reports with grid lines
- Formal documents with table borders
- Any PDF with visible cell boundaries

**How it works**: Uses vertical and horizontal lines to determine cell boundaries.

#### "text" - Text-Based Detection
Use when table has no borders, relies on spacing.

```yaml
table_strategy: text
```

**Best for**:
- Plain text reports
- Borderless tables
- Simple layouts with consistent spacing
- Text-only PDFs

**How it works**: Uses text positioning and whitespace to infer table structure.

#### "mixed" - Hybrid Detection
Use when table has partial borders.

```yaml
table_strategy: mixed
```

**Best for**:
- Tables with only vertical lines
- Tables with only horizontal lines
- Complex layouts with mixed formatting
- When "lines" or "text" alone don't work

**How it works**: Uses vertical lines + horizontal text positioning.

### table_bbox

**Type**: Array of 4 numbers [x0, top, x1, bottom]
**Optional**: Yes (default: extract entire page)
**Description**: Bounding box to crop page before extraction

**Format**: `[x0, top, x1, bottom]` in PDF coordinate system
- `x0`: Left boundary (in points)
- `top`: Top boundary (in points)
- `x1`: Right boundary (in points)
- `bottom`: Bottom boundary (in points)

**Examples**:
```yaml
# Extract only line items section (exclude header and footer)
table_bbox: [50, 100, 550, 400]

# Extract left half of page
table_bbox: [0, 0, 300, 792]

# Extract right half of page
table_bbox: [300, 0, 612, 792]
```

**When to use**:
- PDF has multiple sections (header, table, footer)
- You only want specific table, not all tables on page
- Table is in specific region of page
- Need to exclude surrounding text or images

**Finding coordinates**:
```python
# Use pdfplumber to explore coordinates
import pdfplumber

with pdfplumber.open("invoice.pdf") as pdf:
    page = pdf.pages[0]
    print(f"Page size: {page.width} × {page.height}")
    # Standard Letter: 612 × 792 points
```

### table_settings

**Type**: Dictionary
**Optional**: Yes (uses strategy defaults)
**Description**: Advanced pdfplumber table settings

**Advanced Settings**:
```yaml
table_settings:
  snap_tolerance: 3           # Snap lines within 3 points
  join_tolerance: 3           # Join line segments within 3 points
  edge_min_length: 3          # Minimum line length to consider
  min_words_vertical: 3       # Minimum words for vertical alignment
  min_words_horizontal: 1     # Minimum words for horizontal alignment
  text_tolerance: 3           # Text positioning tolerance
  intersection_tolerance: 3   # Line intersection tolerance
```

**When to use**:
- Default extraction doesn't work well
- Need fine-tuning for complex tables
- Dealing with slight alignment issues
- Optimizing for specific PDF format

**Most users don't need this** - stick with strategy defaults.

### skip_rows

**Type**: Integer
**Optional**: Yes
**Description**: Number of rows to skip after header

**Examples**:
```yaml
skip_rows: 1    # Skip first data row (maybe subtotal row)
skip_rows: 2    # Skip first two data rows
```

**Use when**:
- Table has summary rows after header
- Need to skip certain rows
- Table has formatting rows to ignore

### max_rows

**Type**: Integer
**Optional**: Yes
**Description**: Maximum number of data rows to extract

**Examples**:
```yaml
max_rows: 10    # Extract first 10 rows only
max_rows: 100   # Extract first 100 rows
```

**Use when**:
- Testing with small subset of data
- Table is very large (performance)
- Only need top N rows
- Incremental processing

---

## 📊 Table Extraction Strategies

Choosing the right extraction strategy is critical for success.

### Strategy Decision Tree

```
Does your table have visible borders?
│
├─ YES → Use "lines" strategy
│         (Most invoices, reports)
│
└─ NO → Does it have consistent spacing?
         │
         ├─ YES → Use "text" strategy
         │         (Plain text reports)
         │
         └─ NO → Use "mixed" strategy
                   (Partially bordered tables)
```

### Lines Strategy (Bordered Tables)

**Best for**: PDFs with clear table borders

**Visual Example**:
```
┌────────────┬──────────┬────────────┬────────────┐
│ Item       │ Quantity │ Unit Price │ Total      │
├────────────┼──────────┼────────────┼────────────┤
│ Widget A   │ 2        │ $15.00     │ $30.00     │
├────────────┼──────────┼────────────┼────────────┤
│ Service B  │ 1        │ $50.00     │ $50.00     │
└────────────┴──────────┴────────────┴────────────┘
```

**Configuration**:
```yaml
data_source:
  config:
    table_strategy: lines
```

**Advantages**:
- Most accurate for bordered tables
- Handles complex cell structures
- Works with merged cells (limited)
- Reliable cell boundary detection

**Limitations**:
- Requires visible lines/borders
- Doesn't work well with borderless tables
- May over-detect non-table lines

### Text Strategy (Borderless Tables)

**Best for**: PDFs with consistent spacing, no borders

**Visual Example**:
```
Item          Quantity    Unit Price    Total
Widget A      2           $15.00        $30.00
Service B     1           $50.00        $50.00
Widget C      3           $8.50         $25.50
```

**Configuration**:
```yaml
data_source:
  config:
    table_strategy: text
```

**Advantages**:
- Works without visible borders
- Good for plain text layouts
- Handles variable-width columns
- Lightweight processing

**Limitations**:
- Requires consistent alignment
- Sensitive to spacing variations
- May misalign with poor formatting
- Doesn't handle merged cells well

### Mixed Strategy (Hybrid)

**Best for**: Tables with partial borders or mixed formatting

**Visual Example**:
```
Item       │ Quantity │ Unit Price │ Total
──────────────────────────────────────────
Widget A   │ 2        │ $15.00     │ $30.00
Service B  │ 1        │ $50.00     │ $50.00
Widget C   │ 3        │ $8.50      │ $25.50
```

**Configuration**:
```yaml
data_source:
  config:
    table_strategy: mixed
```

**Advantages**:
- Combines strengths of both strategies
- Works with partially bordered tables
- More flexible than pure strategies
- Good fallback when others fail

**Limitations**:
- More complex processing
- May still fail on unusual layouts
- Requires experimentation

### Strategy Comparison Table

| Feature | Lines | Text | Mixed |
|---------|-------|------|-------|
| Bordered tables | ✅ Excellent | ❌ Poor | ✅ Good |
| Borderless tables | ❌ Poor | ✅ Excellent | ✅ Good |
| Partial borders | ⚠️ Variable | ⚠️ Variable | ✅ Good |
| Processing speed | Fast | Faster | Medium |
| Accuracy | High | Medium | Medium-High |
| Configuration complexity | Simple | Simple | Medium |

### Testing Strategies

If unsure which strategy to use, test all three:

```bash
# Test with lines strategy
python test_extraction.py --strategy lines

# Test with text strategy
python test_extraction.py --strategy text

# Test with mixed strategy
python test_extraction.py --strategy mixed

# Compare results and choose best one
```

---

## 📍 Bounding Box Selection

Bounding boxes let you extract specific table regions from complex PDFs.

### What is a Bounding Box?

A rectangular region defined by four coordinates:

```
(x0, top) ──────────────────┐
│                           │
│   Table Area              │
│   (extracted)             │
│                           │
└────────────────── (x1, bottom)
```

**Format**: `[x0, top, x1, bottom]`
- `x0`: Left edge (in points from left)
- `top`: Top edge (in points from top)
- `x1`: Right edge (in points from left)
- `bottom`: Bottom edge (in points from top)

### PDF Coordinate System

PDFs use **points** as units (1 inch = 72 points)

**Standard Letter page**: 612 × 792 points (8.5" × 11")

```
(0, 0) ─────────────────────────── (612, 0)
│                                      │
│                                      │
│        Page Content                  │
│                                      │
│                                      │
(0, 792) ──────────────────────── (612, 792)
```

### When to Use Bounding Boxes

✅ **Use bounding boxes when**:
- PDF has multiple tables on one page
- Table is surrounded by non-table content
- Need to exclude header/footer sections
- Want specific region, not entire page
- Dealing with complex multi-section documents

❌ **Don't use bounding boxes when**:
- Table is the only content on page
- Simple invoices with one table
- Table boundaries are clear with strategy alone

### Example: Invoice with Header and Footer

**Scenario**: Invoice PDF with:
- Header (company info, invoice number) - top 100 points
- Line items table - middle section
- Footer (totals, terms) - bottom 100 points

**Goal**: Extract only line items, exclude header/footer

**Configuration**:
```yaml
data_source:
  config:
    file_path: input/invoice.pdf
    page_number: 0
    table_strategy: lines
    table_bbox: [50, 100, 550, 650]  # Exclude header (0-100) and footer (650-792)
```

**Result**: Only line items extracted, header/footer ignored

### Finding Bounding Box Coordinates

#### Method 1: pdfplumber Interactive

```python
import pdfplumber

with pdfplumber.open("invoice.pdf") as pdf:
    page = pdf.pages[0]

    # Print page dimensions
    print(f"Page size: {page.width} × {page.height}")

    # Extract all tables to see boundaries
    tables = page.extract_tables()
    for i, table in enumerate(tables):
        print(f"Table {i}: {len(table)} rows, {len(table[0])} columns")

    # Inspect page layout
    print(page.chars[0])  # First character properties
    print(page.lines[0])  # First line properties
```

#### Method 2: PDF Viewer with Coordinates

Some PDF viewers show cursor coordinates:
- Adobe Acrobat Pro (show coordinates in status bar)
- PDF-XChange Editor (coordinate display)
- Online tools like pdf-coordinates.com

#### Method 3: Trial and Error

Start with estimated values and refine:

```yaml
# Initial guess (middle of page)
table_bbox: [50, 100, 550, 650]

# Too much header? Increase top
table_bbox: [50, 150, 550, 650]

# Too much footer? Decrease bottom
table_bbox: [50, 100, 550, 600]

# Table too narrow? Adjust left/right
table_bbox: [25, 100, 575, 600]
```

### Common Bounding Box Patterns

#### Full Page (Default)
```yaml
# No bounding box = extract entire page
table_bbox: null
```

#### Exclude Header (100 points)
```yaml
table_bbox: [0, 100, 612, 792]  # Start at y=100
```

#### Exclude Footer (100 points)
```yaml
table_bbox: [0, 0, 612, 692]  # End at y=692 (792-100)
```

#### Exclude Header and Footer
```yaml
table_bbox: [0, 100, 612, 692]  # Middle section only
```

#### Left Half of Page
```yaml
table_bbox: [0, 0, 306, 792]  # x0=0 to x1=306 (612/2)
```

#### Right Half of Page
```yaml
table_bbox: [306, 0, 612, 792]  # x0=306 to x1=612
```

#### Center Region (80% of page)
```yaml
table_bbox: [61, 79, 551, 713]  # 10% margin on all sides
```

### Debugging Bounding Boxes

If extraction fails with bounding box:

1. **Check coordinates are in correct order**
   ```yaml
   # ✅ Correct: x0 < x1, top < bottom
   table_bbox: [50, 100, 550, 650]

   # ❌ Wrong: backwards coordinates
   table_bbox: [550, 650, 50, 100]
   ```

2. **Verify coordinates within page bounds**
   ```python
   # Check page size first
   page.width  # e.g., 612
   page.height  # e.g., 792

   # Ensure: 0 ≤ x0 < x1 ≤ width
   #         0 ≤ top < bottom ≤ height
   ```

3. **Visualize bounding box**
   ```python
   # Crop and preview
   cropped = page.crop([50, 100, 550, 650])
   im = cropped.to_image()
   im.show()  # Visual confirmation
   ```

4. **Test without bounding box first**
   ```yaml
   # Remove bounding box temporarily
   table_bbox: null

   # See what gets extracted
   # Then add bounding box to refine
   ```

---

## 🔄 Transformation Patterns

The platform automatically detects these transformation patterns from your examples:

### 1. Field Renaming

**Pattern**: Map input field to output field with different name

**Example**:
```json
{
  "input": {"Item": "Widget A"},
  "output": {"product": "Widget A"}
}
```

**Detection**: Schema analyzer compares input/output field names

**Use Cases**:
- Shorten verbose names (Item Description → product)
- Standardize naming (Qty vs Quantity → qty)
- Match target system schema

### 2. Currency Parsing

**Pattern**: Remove currency symbols and convert to number

**Examples**:

**Dollar Sign**:
```json
{
  "input": {"Unit Price": "$15.00"},
  "output": {"unit_price_usd": 15.00}
}
```

**With Commas**:
```json
{
  "input": {"Total": "$1,500.00"},
  "output": {"total_usd": 1500.00}
}
```

**Detection**: AI detects currency symbols ($, €, £) and number patterns

**Supported Formats**:
- $15.00 → 15.00
- $1,500.00 → 1500.00
- €99.99 → 99.99
- £50.00 → 50.00
- ¥1000 → 1000.00

### 3. Type Conversions

**Pattern**: Convert value from one type to another

**String to Integer**:
```json
{
  "input": {"Quantity": "2"},
  "output": {"qty": 2}
}
```

**String to Float**:
```json
{
  "input": {"Rate": "8.5"},
  "output": {"rate": 8.5}
}
```

**String to Date**:
```json
{
  "input": {"Date": "2024-01-15"},
  "output": {"date": "2024-01-15"}  # Validated as ISO date
}
```

### 4. Whitespace Normalization

**Pattern**: Strip leading/trailing whitespace

**Example**:
```json
{
  "input": {"Item": "  Widget A  "},
  "output": {"product": "Widget A"}
}
```

**Automatic**: Applied to all string fields by default

### 5. Null/Empty Handling

**Pattern**: Handle missing or empty values

**Examples**:

**Empty String to None**:
```json
{
  "input": {"Notes": ""},
  "output": {"notes": null}
}
```

**"N/A" to None**:
```json
{
  "input": {"Reference": "N/A"},
  "output": {"reference": null}
}
```

### 6. Calculated Fields

**Pattern**: Derive new values from existing fields

**Example**:
```json
{
  "input": {
    "Quantity": "2",
    "Unit Price": "$15.00"
  },
  "output": {
    "qty": 2,
    "unit_price_usd": 15.00,
    "line_total_usd": 30.00  // qty × unit_price_usd
  }
}
```

**Advanced**: Requires explicit example showing calculation

### 7. String Concatenation

**Pattern**: Combine multiple fields into one

**Example**:
```json
{
  "input": {
    "First Name": "John",
    "Last Name": "Doe"
  },
  "output": {
    "full_name": "John Doe"
  }
}
```

### 8. Field Extraction

**Pattern**: Extract part of a value

**Example**:
```json
{
  "input": {"SKU": "WID-12345-A"},
  "output": {"product_id": "12345"}
}
```

**Pattern Detection**: AI looks for substring relationships

---

## ✅ Best Practices

### Example Selection

1. **Choose diverse examples** (2-3 rows minimum)
   - Include different product types, values, edge cases
   - Show all transformation patterns
   - Cover different data types (text, numbers, currency)

2. **Use representative data**
   - Real data from actual PDF > synthetic data
   - Include edge cases (high values, decimals, zeros)
   - Show variance (different product names, quantities)

3. **Keep examples simple**
   - One row per example
   - Clear transformation patterns
   - Minimal complexity

### PDF Preparation

1. **Verify PDF is text-based, not scanned**
   - Test: Can you select/copy text in PDF viewer?
   - ✅ Text-based: Use as-is
   - ❌ Scanned: Need OCR first (tesseract, Adobe Acrobat)

2. **Check table structure**
   - Consistent column alignment
   - Clear header row
   - No heavily merged cells
   - Standard row-column layout

3. **Test extraction first**
   ```python
   import pdfplumber

   with pdfplumber.open("invoice.pdf") as pdf:
       page = pdf.pages[0]
       tables = page.extract_tables()
       print(f"Found {len(tables)} tables")
       if tables:
           print(f"First table: {len(tables[0])} rows")
   ```

### Strategy Selection

1. **Start with "lines" strategy** (most common)
2. **If that fails, try "text" strategy**
3. **Use "mixed" as fallback**
4. **Document which strategy works** for your PDF type

### Project Organization

```
projects/my_pdf_project/
├── project.yaml          # Configuration (required)
├── input/               # Source PDF files
│   └── data.pdf
├── examples/            # Transformation examples (2-3 required)
│   ├── example1.json
│   ├── example2.json
│   └── example3.json
├── output/              # Generated code and results
│   ├── extractor.py
│   ├── models.py
│   ├── test_extractor.py
│   └── extracted_data.json
└── README.md           # Project documentation
```

### Validation Tips

1. **Start small**
   - Test with single page first
   - Validate transformations manually
   - Then scale to multiple pages (Phase 2)

2. **Use generated tests**
   ```bash
   pytest output/test_extractor.py -v
   ```

3. **Spot-check results**
   - Verify first/last rows
   - Check calculated fields
   - Ensure type conversions work

4. **Compare with source**
   - Open PDF and output side-by-side
   - Verify row counts match
   - Check edge cases manually

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: "No tables found on page"

**Error**:
```
ValueError: No tables found on page 0. Try different table_strategy or table_bbox.
```

**Causes**:
- Wrong table_strategy for PDF format
- Table outside default extraction area
- PDF has no structured table

**Solutions**:
1. **Try different strategy**
   ```yaml
   table_strategy: text    # Instead of lines
   ```

2. **Use bounding box**
   ```yaml
   table_bbox: [50, 100, 550, 650]  # Specific region
   ```

3. **Check if PDF has tables**
   ```python
   import pdfplumber
   with pdfplumber.open("file.pdf") as pdf:
       tables = pdf.pages[0].extract_tables()
       print(f"Found: {len(tables)} tables")
   ```

#### Issue: "Page X out of range"

**Error**:
```
ValueError: Page 2 out of range. PDF has 1 pages (0-indexed)
```

**Cause**: page_number exceeds PDF page count

**Solutions**:
1. **Check page count**
   ```python
   import pdfplumber
   with pdfplumber.open("file.pdf") as pdf:
       print(f"Total pages: {len(pdf.pages)}")
   ```

2. **Use correct page index** (0-indexed!)
   ```yaml
   page_number: 0  # First page
   ```

#### Issue: "Table has insufficient data"

**Error**:
```
ValueError: Table on page 0 has insufficient data. Expected at least header + 1 data row.
```

**Cause**: Extracted table is empty or has only header

**Solutions**:
1. **Adjust bounding box** (may be too restrictive)
2. **Try different strategy**
3. **Check if table actually has data**

#### Issue: Wrong data extracted

**Problem**: Extraction works but gets wrong columns or values

**Solutions**:
1. **Use bounding box** to isolate table
   ```yaml
   table_bbox: [50, 100, 550, 650]
   ```

2. **Adjust table_strategy**
   ```yaml
   table_strategy: mixed  # Hybrid approach
   ```

3. **Fine-tune table_settings**
   ```yaml
   table_settings:
     snap_tolerance: 5
     join_tolerance: 5
   ```

#### Issue: Currency parsing fails

**Problem**: Currency values not converting correctly

**Examples**:
- "$1,500.00" → NaN
- "€99.99" → string instead of number

**Solutions**:
1. **Check currency format in examples**
   ```json
   {
     "input": {"Total": "$1,500.00"},
     "output": {"total": 1500.00}  // Correct: number
   }
   ```

2. **Handle multiple currency formats**
   ```python
   def parse_currency(value: str) -> float:
       # Remove $, €, £, ¥ and commas
       cleaned = value.replace('$', '').replace('€', '').replace('£', '')
       cleaned = cleaned.replace('¥', '').replace(',', '').strip()
       return float(cleaned)
   ```

#### Issue: Type inference issues

**Problem**: Columns have wrong types (string instead of number)

**Cause**: PDF extracts everything as strings, type inference fails

**Solutions**:
1. **Show explicit type conversion in examples**
   ```json
   {
     "input": {"Quantity": "2"},      // String
     "output": {"qty": 2}              // Integer
   }
   ```

2. **Use Pydantic type validation**
   ```python
   class Item(BaseModel):
       qty: int  # Forces integer conversion
   ```

#### Issue: pdfplumber not installed

**Error**:
```
ImportError: pdfplumber is required for PDF files.
Install with: pip install pdfplumber
```

**Solution**:
```bash
pip install pdfplumber
```

#### Issue: Scanned PDF (image-based)

**Problem**: PDF is scanned image, no extractable text

**Check**:
```python
import pdfplumber
with pdfplumber.open("scanned.pdf") as pdf:
    text = pdf.pages[0].extract_text()
    print(f"Extracted text: {text}")
    # If empty or gibberish → scanned PDF
```

**Solution**:
1. **Use OCR preprocessing**
   ```bash
   # Option 1: Adobe Acrobat (commercial)
   # File → Export To → Text (OCR)

   # Option 2: tesseract (free)
   pip install pdf2image pytesseract
   ```

2. **OCR conversion script**
   ```python
   from pdf2image import convert_from_path
   import pytesseract

   # Convert PDF to images
   images = convert_from_path('scanned.pdf')

   # OCR each page
   for i, image in enumerate(images):
       text = pytesseract.image_to_string(image)
       print(f"Page {i}: {text}")
   ```

#### Issue: Multi-page extraction not working

**Error**:
```
NotImplementedError: Multi-page extraction not yet supported.
Please specify a single page number.
```

**Cause**: Phase 1 limitation - single page only

**Workarounds**:
1. **Extract pages separately**
   ```yaml
   # Create separate projects for each page
   page_number: 0  # Project 1
   page_number: 1  # Project 2
   ```

2. **Wait for Phase 2** (multi-page support coming soon)

---

## 📚 Examples

### Example 1: Simple Invoice

**Source**: Invoice with line items (invoice_001.pdf)

**Transformations**:
- Rename fields (Item → product, Quantity → qty)
- Parse currency ($15.00 → 15.00)
- Convert quantity to integer

**project.yaml**:
```yaml
name: Simple Invoice Extraction
description: Extract line items from standard invoice
version: 1.0.0

data_source:
  type: pdf
  config:
    file_path: input/invoice_001.pdf
    page_number: 0
    table_strategy: lines

examples:
  - examples/item1.json
  - examples/item2.json
  - examples/item3.json

target_schema:
  product: string
  qty: integer
  unit_price_usd: number
  line_total_usd: number
```

**Example transformation** (examples/item1.json):
```json
{
  "example_id": "invoice_001_item_1",
  "description": "First line item",
  "input": {
    "Item": "Widget A",
    "Quantity": "2",
    "Unit Price": "$15.00",
    "Total": "$30.00"
  },
  "output": {
    "product": "Widget A",
    "qty": 2,
    "unit_price_usd": 15.00,
    "line_total_usd": 30.00
  }
}
```

### Example 2: Financial Report

**Source**: Balance sheet with multiple sections

**Transformations**:
- Extract specific section with bounding box
- Parse large numbers with commas
- Handle positive/negative values

**project.yaml**:
```yaml
name: Balance Sheet Assets
description: Extract assets section from balance sheet
version: 1.0.0

data_source:
  type: pdf
  config:
    file_path: input/balance_sheet_2024.pdf
    page_number: 0
    table_strategy: lines
    table_bbox: [50, 150, 550, 400]  # Assets section only

examples:
  - examples/cash.json
  - examples/receivables.json
  - examples/inventory.json

target_schema:
  account: string
  amount_usd: number
  category: string
```

**Example transformation**:
```json
{
  "example_id": "balance_sheet_cash",
  "input": {
    "Account": "Cash and Cash Equivalents",
    "Amount": "$1,500,000",
    "Category": "Current Assets"
  },
  "output": {
    "account": "Cash and Cash Equivalents",
    "amount_usd": 1500000.00,
    "category": "Current Assets"
  }
}
```

### Example 3: Product Catalog

**Source**: Product specifications from PDF catalog

**Transformations**:
- Extract product details
- Parse dimensional data
- Convert units

**project.yaml**:
```yaml
name: Product Catalog Extraction
description: Extract product specifications from catalog
version: 1.0.0

data_source:
  type: pdf
  config:
    file_path: input/catalog_2024.pdf
    page_number: 2
    table_strategy: text  # Borderless table

examples:
  - examples/product_a.json
  - examples/product_b.json

target_schema:
  sku: string
  name: string
  dimensions_inches: string
  weight_lbs: number
  price_usd: number
```

### Example 4: Survey Results

**Source**: Survey response table

**Transformations**:
- Extract respondent data
- Parse rating scales
- Handle optional fields

**project.yaml**:
```yaml
name: Survey Results
description: Extract survey responses from PDF
version: 1.0.0

data_source:
  type: pdf
  config:
    file_path: input/survey_results.pdf
    page_number: 0
    table_strategy: mixed

examples:
  - examples/respondent_1.json
  - examples/respondent_2.json

target_schema:
  respondent_id: string
  question_1_rating: integer
  question_2_rating: integer
  comments: string
```

---

## 🎓 Next Steps

### Learn More

- **[Technical Reference](../architecture/PDF_DATA_SOURCE.md)** - Implementation details
- **[Invoice POC](../../projects/invoice_transform/)** - Complete walkthrough
- **[Schema Analyzer](../architecture/SCHEMA_ANALYZER.md)** - How pattern detection works
- **[Data Source Abstraction](../architecture/DATA_SOURCE_ABSTRACTION_LAYER.md)** - Architecture overview
- **[Excel File Transform](EXCEL_FILE_TRANSFORM.md)** - Similar patterns for Excel

### Advanced Topics

- Multi-page extraction (Phase 2)
- OCR integration for scanned PDFs (Phase 2)
- Complex table structures (nested tables, merged cells)
- Custom transformation functions
- Batch processing multiple PDFs
- Performance optimization for large PDFs

### Phase 2 Features (Coming Soon)

- **Multi-page extraction** - Extract from all pages in one operation
- **Multi-table per page** - Handle multiple tables on single page
- **OCR preprocessing** - Built-in OCR for scanned documents
- **Advanced table detection** - Better handling of complex layouts
- **Streaming extraction** - Process very large PDFs efficiently
- **Form field extraction** - Extract from PDF forms, not just tables

### Get Help

- Check [Invoice Transform POC](../../projects/invoice_transform/) for working example
- Review [Excel File Transform](EXCEL_FILE_TRANSFORM.md) for similar patterns
- See [Troubleshooting](#troubleshooting) for common issues
- Refer to [Configuration Reference](#configuration-reference) for all options

---

## 🔗 Related Documentation

- **[PDF Data Source (Technical)](../architecture/PDF_DATA_SOURCE.md)** - Developer reference
- **[Excel File Transform](EXCEL_FILE_TRANSFORM.md)** - Similar file-based workflow
- **[Schema Analyzer](../architecture/SCHEMA_ANALYZER.md)** - Pattern detection engine
- **[Base Data Source](../architecture/BASE_DATA_SOURCE.md)** - Architecture foundation
- **[Phase 2 Planning](../../docs/planning/PHASE_2_CORE_ARCHITECTURE.md)** - Upcoming features

---

**Built with the EDGAR Platform - Example-Driven Extract & Transform**
