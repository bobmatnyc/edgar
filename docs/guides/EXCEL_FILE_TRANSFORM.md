# Excel File Transform Guide

Transform Excel spreadsheets into structured data using the platform's example-driven approach.

**Platform Package**: `extract_transform_platform` (NEW - Phase 2)
**Data Source**: `ExcelDataSource` (MIGRATED from `edgar_analyzer`)
**Status**: Production-ready (80% test coverage, 69 tests passing)

> **Note**: This guide uses the new `extract_transform_platform` package. For migration from `edgar_analyzer`, see [Platform Migration Guide](PLATFORM_MIGRATION.md).

---

## 📋 Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Step-by-Step Tutorial](#step-by-step-tutorial)
- [Supported Transformations](#supported-transformations)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

---

## 🎯 Overview

### What This Does

The Excel file transform capability allows you to extract and transform data from Excel spreadsheets (.xlsx, .xls) into structured JSON format without writing any code. You simply:

1. Provide your source Excel file
2. Show 2-3 examples of how rows should be transformed
3. The platform analyzes your examples and generates extraction code
4. Run the generated code on your full dataset

**Key Benefits:**
- ✅ No coding required - just configure and provide examples
- ✅ Automatic pattern detection from examples
- ✅ Type-safe transformations with validation
- ✅ Handles field renaming, concatenation, type conversions
- ✅ 70% code reuse from proven Weather API template
- ✅ Production-ready with error handling and edge cases

### How It Works

The platform uses the same **example-driven approach** proven with the Weather API template:

```
Excel File (input)
    ↓
Provide 2-3 transformation examples
    ↓
Schema Analyzer detects patterns
    ↓
AI generates extraction code
    ↓
Structured JSON (output)
```

### Import Paths

**NEW (Platform - Recommended)**:
```python
from extract_transform_platform.data_sources.file import ExcelDataSource
from extract_transform_platform.models import ProjectConfig
```

**OLD (EDGAR - Legacy)**:
```python
from edgar_analyzer.data_sources.excel_source import ExcelDataSource
from edgar_analyzer.models.project_config import ProjectConfig
```

See [Platform Migration Guide](PLATFORM_MIGRATION.md) for details.

---

**Example**: Transform HR roster

**Input** (Excel row):
```
employee_id | first_name | last_name | department  | hire_date  | salary | is_manager
E1001       | Alice      | Johnson   | Engineering | 2020-03-15 | 95000  | Yes
```

**Output** (JSON):
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

The platform automatically detects:
- Field renaming (employee_id → id)
- String concatenation (first_name + last_name → full_name)
- Type conversions (salary → float, "Yes" → true)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Excel file (.xlsx or .xls)
- At least 2-3 example rows of data

### 5-Minute Setup

#### 1. Create Project Structure

```bash
# Create new project directory
cd projects/
mkdir my_excel_project
cd my_excel_project

# Create required directories
mkdir input examples output
```

#### 2. Add Your Excel File

```bash
# Copy your Excel file to input/
cp /path/to/your/file.xlsx input/data.xlsx
```

#### 3. Create project.yaml

```yaml
name: My Excel Transformation
description: Transform Excel data into structured format
version: 1.0.0

data_source:
  type: excel
  config:
    file_path: input/data.xlsx
    sheet_name: 0        # First sheet (or use "Sheet1")
    header_row: 0        # Row 0 has column headers

examples:
  - examples/row1.json
  - examples/row2.json
  - examples/row3.json

target_schema:
  # Your desired output fields
  id: string
  name: string
  # ... add your fields
```

#### 4. Create Example Transformations

Create `examples/row1.json`:

```json
{
  "example_id": "example_1",
  "description": "First example row",
  "input": {
    "column_a": "value1",
    "column_b": "value2"
  },
  "output": {
    "field_1": "value1",
    "field_2": "value2"
  }
}
```

Repeat for 2-3 rows to show transformation patterns.

#### 5. Generate and Run

```bash
# Analyze examples and generate extraction code
python -m edgar_analyzer extract-project projects/my_excel_project/

# Run extraction on full Excel file
python -m edgar_analyzer run-extraction projects/my_excel_project/output/extract.py
```

**Done!** Your transformed data is in `output/extracted_data.json`

---

## 📖 Step-by-Step Tutorial

Follow the complete employee roster example to learn the full workflow.

### Step 1: Understand Your Source Data

Open your Excel file and identify:
- **Header row**: Which row contains column names?
- **Data rows**: Where does actual data start?
- **Column types**: What type is each column (text, number, date, boolean)?

**Example**: HR roster (input/hr_roster.xlsx)

| Column | Type | Description |
|--------|------|-------------|
| employee_id | string | Unique ID (E####) |
| first_name | string | First name |
| last_name | string | Last name |
| department | string | Department name |
| hire_date | date | Hire date (YYYY-MM-DD) |
| salary | integer | Annual salary |
| is_manager | string | "Yes" or "No" |

### Step 2: Design Your Output Schema

Decide what your transformed output should look like:

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

**Transformations needed**:
1. Rename `employee_id` → `id`
2. Concatenate `first_name + last_name` → `full_name`
3. Rename `department` → `dept`
4. Rename `hire_date` → `hired`
5. Convert `salary` (int) → `annual_salary_usd` (float)
6. Convert `is_manager` ("Yes"/"No") → `manager` (true/false)

### Step 3: Create Example Files

Create transformation examples showing input → output pairs.

**examples/alice.json** (Row 1):
```json
{
  "example_id": "hr_roster_e1001_alice",
  "description": "Engineering employee with manager status",
  "input": {
    "employee_id": "E1001",
    "first_name": "Alice",
    "last_name": "Johnson",
    "department": "Engineering",
    "hire_date": "2020-03-15",
    "salary": 95000,
    "is_manager": "Yes"
  },
  "output": {
    "id": "E1001",
    "full_name": "Alice Johnson",
    "dept": "Engineering",
    "hired": "2020-03-15",
    "annual_salary_usd": 95000.0,
    "manager": true
  }
}
```

**examples/bob.json** (Row 2):
```json
{
  "example_id": "hr_roster_e1002_bob",
  "description": "Marketing employee without manager status",
  "input": {
    "employee_id": "E1002",
    "first_name": "Bob",
    "last_name": "Smith",
    "department": "Marketing",
    "hire_date": "2019-07-22",
    "salary": 78000,
    "is_manager": "No"
  },
  "output": {
    "id": "E1002",
    "full_name": "Bob Smith",
    "dept": "Marketing",
    "hired": "2019-07-22",
    "annual_salary_usd": 78000.0,
    "manager": false
  }
}
```

**Why 2-3 examples?**
- 1 example: AI might overfit (too specific)
- 2-3 examples: AI finds patterns (just right)
- 5+ examples: Diminishing returns (more work, same accuracy)

### Step 4: Configure project.yaml

Create complete project configuration:

```yaml
name: Employee Roster Extraction
description: Transform HR roster Excel data into structured employee records
version: 1.0.0

data_source:
  type: excel
  config:
    file_path: input/hr_roster.xlsx
    sheet_name: 0        # First sheet
    header_row: 0        # Headers in row 0

examples:
  - examples/alice.json
  - examples/bob.json
  - examples/carol.json

transformations:
  # These are auto-detected from examples (documentation only)
  - type: field_rename
    description: Rename employee_id to id
  - type: concatenation
    description: Combine first_name + last_name → full_name
  - type: type_conversion
    description: Convert salary to float as annual_salary_usd
  - type: boolean_conversion
    description: Convert is_manager Yes/No to true/false

target_schema:
  id: string
  full_name: string
  dept: string
  hired: date
  annual_salary_usd: number
  manager: boolean
```

### Step 5: Analyze and Generate Code

Run the platform analyzer:

```bash
# Navigate to project root
cd /path/to/edgar

# Analyze project
python -m edgar_analyzer extract-project projects/employee_roster/

# Output:
# ✓ Loaded Excel file: 3 rows, 7 columns
# ✓ Parsed 3 examples
# ✓ Detected 6 transformation patterns
# ✓ Generated extraction code: output/employee_extractor.py
# ✓ Generated validation tests: output/test_extractor.py
```

The platform generates:
- **extractor.py**: Extraction logic with transformations
- **models.py**: Pydantic models for validation
- **test_extractor.py**: Automated tests

### Step 6: Review Generated Code

The generated `extractor.py` contains type-safe transformation logic:

```python
from pydantic import BaseModel

class Employee(BaseModel):
    id: str
    full_name: str
    dept: str
    hired: str
    annual_salary_usd: float
    manager: bool

def transform_row(row: dict) -> Employee:
    return Employee(
        id=row["employee_id"],
        full_name=f"{row['first_name']} {row['last_name']}",
        dept=row["department"],
        hired=row["hire_date"],
        annual_salary_usd=float(row["salary"]),
        manager=row["is_manager"].lower() == "yes"
    )
```

### Step 7: Run Extraction

Execute on full dataset:

```bash
# Run extraction
python -m edgar_analyzer run-extraction projects/employee_roster/output/extract.py

# View results
cat projects/employee_roster/output/extracted_data.json
```

Output:
```json
[
  {
    "id": "E1001",
    "full_name": "Alice Johnson",
    "dept": "Engineering",
    "hired": "2020-03-15",
    "annual_salary_usd": 95000.0,
    "manager": true
  },
  {
    "id": "E1002",
    "full_name": "Bob Smith",
    "dept": "Marketing",
    "hired": "2019-07-22",
    "annual_salary_usd": 78000.0,
    "manager": false
  }
]
```

### Step 8: Validate Results

Run generated tests:

```bash
# Run validation tests
pytest projects/employee_roster/output/test_extractor.py

# Output:
# test_transform_alice PASSED
# test_transform_bob PASSED
# test_transform_carol PASSED
# test_all_fields_present PASSED
# test_type_validation PASSED
# ======================== 5 passed in 0.12s ========================
```

**Success!** All transformations match examples exactly.

---

## 🔧 Supported Transformations

The platform automatically detects these transformation patterns from your examples:

### 1. Field Renaming

**Pattern**: Map input field to output field with different name

**Example**:
```json
{
  "input": {"employee_id": "E1001"},
  "output": {"id": "E1001"}
}
```

**Detection**: Schema analyzer compares input/output field names

**Use Cases**:
- Shorten verbose field names (employee_identifier → id)
- Standardize naming (dept vs department)
- Match target system schema

### 2. String Concatenation

**Pattern**: Combine multiple string fields with separator

**Example**:
```json
{
  "input": {"first_name": "Alice", "last_name": "Johnson"},
  "output": {"full_name": "Alice Johnson"}
}
```

**Detection**: Looks for output values containing multiple input values

**Use Cases**:
- Full name from first + last name
- Address from street + city + state
- Composite identifiers

### 3. Type Conversions

**Pattern**: Convert value from one type to another

**Examples**:

**String to Integer**:
```json
{
  "input": {"age": "25"},
  "output": {"age": 25}
}
```

**Integer to Float**:
```json
{
  "input": {"salary": 95000},
  "output": {"salary": 95000.0}
}
```

**String to Date**:
```json
{
  "input": {"hired": "2020-03-15"},
  "output": {"hired": "2020-03-15"}  # Preserved as ISO string
}
```

**Detection**: Schema analyzer infers types from values

**Use Cases**:
- Ensure numeric precision (int → float)
- Parse date strings
- Normalize data types

### 4. Boolean Conversions

**Pattern**: Convert text values to true/false

**Examples**:

**Yes/No → Boolean**:
```json
{
  "input": {"is_manager": "Yes"},
  "output": {"manager": true}
}
```

**True/False → Boolean**:
```json
{
  "input": {"active": "TRUE"},
  "output": {"active": true}
}
```

**1/0 → Boolean**:
```json
{
  "input": {"verified": "1"},
  "output": {"verified": true}
}
```

**Detection**: Recognizes common boolean text patterns

**Supported Patterns**:
- Yes/No, Y/N, yes/no, y/n
- True/False, TRUE/FALSE, true/false, T/F
- 1/0
- Enabled/Disabled

### 5. Value Mapping

**Pattern**: Map discrete values to new values

**Example**:
```json
{
  "input": {"status": "A"},
  "output": {"status": "Active"}
}
```

**Common Mappings**:
- Status codes: A → Active, I → Inactive
- Categories: ENG → Engineering, MKT → Marketing
- Priority levels: 1 → High, 2 → Medium, 3 → Low

### 6. Field Extraction

**Pattern**: Extract part of a value

**Example**:
```json
{
  "input": {"email": "alice@example.com"},
  "output": {"domain": "example.com"}
}
```

**Use Cases**:
- Extract domain from email
- Parse code from composite ID
- Split structured strings

---

## ✅ Best Practices

### Example Selection

1. **Choose diverse examples** (2-3 rows minimum)
   - Include different departments, statuses, edge cases
   - Show all transformation patterns
   - Cover different data types

2. **Use representative data**
   - Real data > synthetic data
   - Include edge cases (null values, special characters)
   - Show variance (different departments, dates, amounts)

3. **Keep examples simple**
   - One row per example
   - Clear transformation patterns
   - Minimal complexity

### Data Preparation

1. **Clean your Excel file**
   - Remove empty rows/columns
   - Ensure consistent headers
   - Fix formatting issues
   - Standardize date formats

2. **Define clear headers**
   - Use row 0 for headers (standard)
   - Avoid multi-row headers (Phase 1 limitation)
   - Use snake_case or camelCase consistently

3. **Check data types**
   - Dates: Use YYYY-MM-DD format
   - Booleans: Standardize (Yes/No, True/False, 1/0)
   - Numbers: Remove currency symbols and commas

### Project Organization

```
projects/my_project/
├── project.yaml          # Configuration (required)
├── input/               # Source Excel files
│   └── data.xlsx
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
   - Test with 3-5 rows first
   - Validate transformations manually
   - Then run on full dataset

2. **Use generated tests**
   - Run `pytest output/test_extractor.py`
   - Verify all examples pass
   - Check edge cases

3. **Compare outputs**
   - Spot-check random rows
   - Verify calculated fields
   - Ensure type conversions work

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: "Excel file not found"

**Error**:
```
FileNotFoundError: Excel file not found: input/data.xlsx
```

**Solution**:
1. Check file path in `project.yaml`
2. Ensure file exists in `input/` directory
3. Verify file extension (.xlsx or .xls)
4. Use absolute path if relative path fails

#### Issue: "Invalid sheet name"

**Error**:
```
ValueError: Worksheet 'Sheet2' not found
```

**Solution**:
1. Open Excel file and check sheet names
2. Use sheet index instead: `sheet_name: 0` (first sheet)
3. Verify spelling of sheet name
4. Check for hidden sheets

#### Issue: "Header row not found"

**Error**:
```
ValueError: No column headers found at row 0
```

**Solution**:
1. Verify `header_row` setting in project.yaml
2. Check if headers start at different row
3. Remove empty rows above headers
4. Ensure headers are not merged cells

#### Issue: "Type conversion failed"

**Error**:
```
ValidationError: salary: value is not a valid float
```

**Solution**:
1. Check source data for non-numeric characters
2. Remove currency symbols ($, €, etc.)
3. Remove thousand separators (commas)
4. Handle null/empty values in examples

#### Issue: "Boolean conversion failed"

**Error**:
```
ValueError: Cannot convert 'Maybe' to boolean
```

**Solution**:
1. Standardize boolean values in Excel
2. Use: Yes/No, True/False, or 1/0
3. Clean up inconsistent values
4. Add custom mapping in examples

#### Issue: "Pattern not detected"

**Problem**: AI doesn't detect expected transformation

**Solution**:
1. Add more examples (try 3-4 instead of 2)
2. Make pattern more obvious in examples
3. Ensure consistency across examples
4. Check example JSON syntax

#### Issue: "Generated code has errors"

**Error**:
```
SyntaxError: invalid syntax in extractor.py
```

**Solution**:
1. Check example JSON for syntax errors
2. Validate project.yaml structure
3. Ensure all field names are valid identifiers
4. Regenerate with corrected examples

### Excel-Specific Issues

#### Merged Cells

**Problem**: Data in merged cells appears only in first cell

**Current Limitation**: Phase 1 doesn't handle merged cells

**Workaround**:
1. Unmerge cells in Excel before processing
2. Copy merged value to all cells
3. Or wait for Phase 2 (merged cell support)

#### Date Formatting

**Problem**: Dates appear as numbers (e.g., 44582)

**Solution**:
1. Format dates as text in Excel (YYYY-MM-DD)
2. Use `parse_dates` parameter in project.yaml:
   ```yaml
   data_source:
     config:
       parse_dates:
         - hire_date
         - birth_date
   ```

#### Large Files

**Problem**: Memory error with files >10MB

**Current Limitation**: Phase 1 loads full sheet into memory

**Workaround**:
1. Use `max_rows` parameter:
   ```yaml
   data_source:
     config:
       max_rows: 1000  # Process first 1000 rows
   ```
2. Split large files into smaller chunks
3. Or wait for Phase 3 (streaming support)

---

## 📚 Examples

### Example 1: Product Catalog

**Source**: Product inventory Excel file

**Transformations**:
- Rename fields (SKU → product_id, Desc → description)
- Calculate total value (quantity × unit_price)
- Categorize (map category codes to names)

**project.yaml**:
```yaml
name: Product Catalog
data_source:
  type: excel
  config:
    file_path: input/inventory.xlsx
    sheet_name: "Products"
```

### Example 2: Sales Report

**Source**: Monthly sales Excel file

**Transformations**:
- Parse dates (convert Excel dates)
- Calculate commission (sales × 0.05)
- Region mapping (code → region name)

**project.yaml**:
```yaml
name: Sales Report
data_source:
  type: excel
  config:
    file_path: input/sales.xlsx
    parse_dates:
      - sale_date
      - ship_date
```

### Example 3: Customer List

**Source**: CRM export Excel file

**Transformations**:
- Combine name fields (first + last → full_name)
- Normalize phone numbers
- Extract email domain
- Boolean opt-in (Y/N → true/false)

**project.yaml**:
```yaml
name: Customer Database
data_source:
  type: excel
  config:
    file_path: input/customers.xlsx
    sheet_name: 0
```

---

## 🎓 Next Steps

### Learn More

- **[Technical Reference](../architecture/EXCEL_DATA_SOURCE.md)** - Implementation details
- **[Employee Roster Tutorial](../../projects/employee_roster/TUTORIAL.md)** - Complete walkthrough
- **[Schema Analyzer](../architecture/SCHEMA_ANALYZER.md)** - How pattern detection works
- **[Data Source Abstraction](../architecture/DATA_SOURCE_ABSTRACTION_LAYER.md)** - Architecture overview

### Advanced Topics

- Multi-sheet support (Phase 2)
- Merged cell handling (Phase 2)
- Formula extraction (Phase 2)
- Large file streaming (Phase 3)
- Custom transformations

### Get Help

- Check [Employee Roster POC](../../projects/employee_roster/) for working example
- Review [Weather API Template](../../projects/weather_api/) for similar patterns
- See [Troubleshooting](#troubleshooting) for common issues

---

**Built with the EDGAR Platform - Example-Driven Extract & Transform**
