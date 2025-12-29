# Test Data - Extract & Transform Platform Alpha Testing

**Version**: 1.0 Alpha
**Purpose**: Sample data and examples for alpha testers
**Status**: Ready for alpha testing

---

## Overview

This directory contains all sample data, transformation examples, and instructions needed for alpha testing the Extract & Transform Platform.

---

## Directory Structure

```
test_data/
├── README.md                       # This file
├── employee_roster_sample.xlsx     # Excel sample (10 employee records) [TO BE CREATED]
├── invoice_sample.pdf              # PDF invoice sample [TO BE CREATED]
├── examples/                       # Pre-built transformation examples
│   ├── employee_roster/            # Excel transformation examples ✅
│   │   ├── row1.json
│   │   ├── row2.json
│   │   └── row3.json
│   └── invoice/                    # PDF extraction examples ✅
│       ├── line1.json
│       ├── line2.json
│       └── line3.json
└── instructions/                   # Setup and reference guides ✅
    ├── api_setup.md                # API key setup instructions
    └── quick_reference.md          # Common commands cheat sheet
```

---

## Sample Data Files

### Employee Roster Sample (Excel)

**File**: `employee_roster_sample.xlsx`
**Status**: TO BE CREATED (placeholder - use projects/employee_roster/input/ for now)
**Format**: Excel spreadsheet (.xlsx)
**Records**: 10 employee records
**Use Case**: Test Excel → JSON transformation (Scenario 1)

**Fields**:
- `employee_id` (string) - Employee ID (E1001, E1002, etc.)
- `first_name` (string) - First name
- `last_name` (string) - Last name
- `department` (string) - Department name
- `hire_date` (date) - Hire date (YYYY-MM-DD)
- `salary` (integer) - Annual salary
- `is_manager` (string) - "Yes" or "No"

**Transformation Patterns**:
- Field rename: `employee_id` → `id`
- Concatenation: `first_name + last_name` → `full_name`
- Type conversion: `salary` (int) → `annual_salary_usd` (float)
- Boolean: `is_manager` ("Yes"/"No") → `manager` (true/false)

**Temporary Workaround**: Use `projects/employee_roster/input/employee_roster.xlsx`

---

### Invoice Sample (PDF)

**File**: `invoice_sample.pdf`
**Status**: TO BE CREATED (placeholder - use projects/invoice_transform/input/ for now)
**Format**: PDF document with table
**Use Case**: Test PDF → JSON extraction (Scenario 2)

**Structure**:
- Invoice header (Invoice #, Date, Customer)
- Line items table (4 rows)
  - Item name
  - Quantity
  - Unit Price ($XX.XX format)
  - Total ($XX.XX format)

**Transformation Patterns**:
- Field rename: `Item` → `product`
- Type conversion: `Quantity` (string) → `qty` (int)
- Currency parsing: `$15.00` → `15.00` (float)
- Field rename: `Unit Price` → `unit_price_usd`

**Temporary Workaround**: Use `projects/invoice_transform/input/` (if available)

---

## Transformation Examples

### Employee Roster Examples

**Location**: `examples/employee_roster/`

**Files**:
- `row1.json` - Alice Johnson (Engineering, Manager)
- `row2.json` - Bob Smith (Sales, Not Manager)
- `row3.json` - Carol Williams (Marketing, Manager)

**Usage**:
```bash
# Copy to your project
cp test_data/examples/employee_roster/*.json projects/my_project/examples/
```

**Pattern Demonstrated**:
```json
{
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

---

### Invoice Examples

**Location**: `examples/invoice/`

**Files**:
- `line1.json` - Widget A ($15.00 × 2 = $30.00)
- `line2.json` - Service B ($50.00 × 1 = $50.00)
- `line3.json` - Product C ($8.50 × 5 = $42.50)

**Usage**:
```bash
# Copy to your project
cp test_data/examples/invoice/*.json projects/my_project/examples/
```

**Pattern Demonstrated**:
```json
{
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

---

## Instructions

### API Setup

**File**: `instructions/api_setup.md`
**Purpose**: Step-by-step guide for obtaining API keys

**Covers**:
- ✅ OpenRouter API (Required) - AI code generation
- ✅ OpenWeatherMap API (Optional) - Weather data
- ✅ Jina.ai API (Optional) - Web scraping

**Quick Start**:
```bash
# Read the guide
cat test_data/instructions/api_setup.md | less

# Or open in browser
open test_data/instructions/api_setup.md
```

---

### Quick Reference

**File**: `instructions/quick_reference.md`
**Purpose**: Common commands and troubleshooting cheat sheet

**Covers**:
- ✅ Essential commands
- ✅ File structure reference
- ✅ Configuration examples
- ✅ Common error solutions
- ✅ Keyboard shortcuts

**Quick Start**:
```bash
# Print cheat sheet
cat test_data/instructions/quick_reference.md

# Search for specific command
grep -A 5 "edgar_analyzer" test_data/instructions/quick_reference.md
```

---

## Usage in Test Scenarios

### Scenario 1: Excel Transformation

**Sample Data**: `employee_roster_sample.xlsx` (or use `projects/employee_roster/input/`)
**Examples**: `examples/employee_roster/row*.json`

```bash
# Setup
mkdir projects/my_excel_test
cd projects/my_excel_test
mkdir input examples output

# Copy sample data (temporary workaround)
cp ../employee_roster/input/employee_roster.xlsx input/roster.xlsx

# Copy examples
cp ../../test_data/examples/employee_roster/*.json examples/

# Continue with scenario...
```

---

### Scenario 2: PDF Extraction

**Sample Data**: `invoice_sample.pdf` (or use `projects/invoice_transform/input/`)
**Examples**: `examples/invoice/line*.json`

```bash
# Setup
mkdir projects/invoice_test
cd projects/invoice_test
mkdir input examples output

# Copy sample data (temporary workaround)
cp ../invoice_transform/input/*.pdf input/invoice_001.pdf

# Copy examples
cp ../../test_data/examples/invoice/*.json examples/

# Continue with scenario...
```

---

### Scenario 3: Weather API

**Sample Data**: N/A (uses live API)
**Template**: Use `--template weather` to create pre-configured project

```bash
# Create from template
edgar_analyzer project create weather_test --template weather

# Configure API key (see api_setup.md)
nano .env.local

# Run extraction
edgar_analyzer run-extraction projects/weather_test/
```

---

## File Format Specifications

### Example JSON Format

All transformation examples follow this structure:

```json
{
  "input": {
    "source_field_1": "source_value_1",
    "source_field_2": "source_value_2"
  },
  "output": {
    "target_field_1": "transformed_value_1",
    "target_field_2": "transformed_value_2"
  }
}
```

**Rules**:
- `input` - Exact fields from source data (Excel columns, PDF table headers, API response)
- `output` - Desired target schema with transformations applied
- Field names must match exactly (case-sensitive)
- Values show expected transformations (type changes, concatenation, etc.)

---

## Known Limitations

### Sample Data Status

**⚠️ Note**: As of 2025-12-04, the following files are placeholders:
- `employee_roster_sample.xlsx` - Use `projects/employee_roster/input/` instead
- `invoice_sample.pdf` - Use `projects/invoice_transform/input/` instead

These will be created and added before alpha testing begins.

**Current Workaround**:
1. Use existing project directories for sample data
2. Examples in `examples/` directory are complete and ready to use
3. All instructions and documentation are complete

---

## Adding Your Own Data

### Custom Excel File

```bash
# 1. Create project
mkdir projects/my_custom_project
cd projects/my_custom_project
mkdir input examples output

# 2. Add your Excel file
cp /path/to/your/file.xlsx input/data.xlsx

# 3. Create examples (use test_data examples as templates)
cp ../../test_data/examples/employee_roster/row1.json examples/
# Edit examples/row1.json with your data

# 4. Configure project.yaml
nano project.yaml
```

### Custom PDF File

```bash
# 1. Create project
mkdir projects/my_pdf_project
cd projects/my_pdf_project
mkdir input examples output

# 2. Add your PDF
cp /path/to/your/invoice.pdf input/document.pdf

# 3. Create examples (use test_data examples as templates)
cp ../../test_data/examples/invoice/line1.json examples/
# Edit examples/line1.json with your data

# 4. Configure project.yaml with PDF settings
nano project.yaml
```

---

## Support

### Questions About Test Data?

**Slack**: #edgar-alpha-testing
**Email**: edgar-support@example.com
**Documentation**: See User Testing Guide in `docs/guides/USER_TESTING_GUIDE.md`

### Reporting Issues

If you find issues with sample data or examples:
1. Post in #edgar-alpha-testing Slack channel
2. Or create GitHub issue with "test-data" label
3. Include description of issue and expected behavior

---

## Checklist for Testers

Before starting testing scenarios:

- [ ] Read `instructions/api_setup.md`
- [ ] Obtain OpenRouter API key (required)
- [ ] Obtain OpenWeatherMap API key (optional, for Scenario 3)
- [ ] Configure `.env.local` with API keys
- [ ] Read `instructions/quick_reference.md`
- [ ] Verify sample data access (or use project directories as workaround)
- [ ] Test installation: `edgar_analyzer setup test`

**Ready to Start?** → See `docs/guides/USER_TESTING_GUIDE.md` for step-by-step scenarios!

---

**Directory Version**: 1.0
**Last Updated**: 2025-12-04
**Maintained By**: Platform Development Team
**Status**: Ready for alpha testing (with noted workarounds)
