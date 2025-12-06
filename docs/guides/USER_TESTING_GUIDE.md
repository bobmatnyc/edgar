# User Testing Guide - Extract & Transform Platform

**Version**: 1.0 Alpha
**Target Users**: Alpha testers
**Prerequisites**: Python 3.11+, basic command-line experience
**Estimated Time**: 2-3 hours for all scenarios

---

## Welcome! 🎉

Thank you for participating in the Extract & Transform Platform alpha testing! Your feedback will help shape the future of this platform and ensure it solves real-world data extraction problems.

### What is This Platform?

The Extract & Transform Platform is a general-purpose tool for extracting and transforming data from various sources:
- **Excel files** → Structured JSON
- **PDF documents** → Extracted tables and text
- **REST APIs** → Formatted data
- **Web pages** → Scraped content

The platform uses **example-driven** approach - you provide 2-3 examples of transformations you want, and the platform generates code to apply those patterns automatically.

### What You'll Test

You'll complete 5 test scenarios:
1. **Excel Transformation** (15-20 min) - Transform employee roster
2. **PDF Extraction** (15-20 min) - Extract invoice line items
3. **Weather API** (10-15 min) - Fetch weather data
4. **Report Generation** (10 min) - Generate multi-format reports
5. **Custom Workflow** (30-45 min) - Your own data source

---

## Getting Started (5 minutes)

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourorg/edgar.git
cd edgar
```

### Step 2: Create Virtual Environment

**macOS/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**:
```bash
python -m venv venv
.\venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -e ".[dev]"
```

This will install all required packages including:
- Core platform dependencies
- Development tools (pytest, black, mypy)
- Data processing libraries (pandas, pdfplumber)
- AI integration (openrouter-py)

### Step 4: Verify Installation

```bash
python -m edgar_analyzer --help
```

**Expected Output**:
```
Usage: edgar_analyzer [OPTIONS] COMMAND [ARGS]...

EDGAR Analyzer CLI - Extract & Transform Platform

Options:
  --version  Show version
  --help     Show this message and exit

Commands:
  analyze-project    Analyze project examples
  extract           Extract EDGAR compensation data
  generate-code     Generate extractor code
  project           Project management commands
  report            Report generation commands
  run-extraction    Run data extraction
  setup             Setup and validation commands
```

If you see this, installation is successful! ✅

### Step 5: Configure Environment

```bash
# Copy environment template
cp .env.template .env.local

# Edit with your favorite editor
nano .env.local  # or vim, code, etc.
```

**Required Configuration**:
```bash
# OpenRouter API Key (required for code generation)
OPENROUTER_API_KEY=your_key_here

# Optional: OpenWeatherMap API Key (for Scenario 3)
OPENWEATHERMAP_API_KEY=your_key_here

# Optional: Jina.ai API Key (for web scraping)
JINA_API_KEY=your_key_here
```

**How to Get API Keys**:
- **OpenRouter**: https://openrouter.ai/ (Required - free tier available)
- **OpenWeatherMap**: https://openweathermap.org/api (Free tier)
- **Jina.ai**: https://jina.ai/reader (Optional)

See `test_data/instructions/api_setup.md` for detailed setup instructions.

### Step 6: Verify Configuration

```bash
python -m edgar_analyzer setup test
```

This will test your OpenRouter connection and validate configuration.

---

## Quick Start Tutorial (10 minutes)

Let's walk through a complete example together: transforming an employee roster Excel file into JSON.

### 1. Create Project Directory

```bash
cd projects/
mkdir quick_start_demo
cd quick_start_demo
mkdir input examples output
```

**Directory Structure**:
```
quick_start_demo/
├── input/          # Source data files
├── examples/       # Transformation examples
├── output/         # Generated outputs
└── project.yaml    # Configuration (we'll create this)
```

### 2. Add Sample Data

```bash
# Copy sample Excel file
cp ../../test_data/employee_roster_sample.xlsx input/roster.xlsx

# Verify file copied
ls -lh input/
```

**Expected**: You should see `roster.xlsx` (~15 KB)

### 3. View Sample Data

Open `input/roster.xlsx` in Excel or run:

```bash
# View first 5 rows (requires pandas)
python -c "import pandas as pd; print(pd.read_excel('input/roster.xlsx').head())"
```

**Excel Structure**:
| employee_id | first_name | last_name | department  | hire_date  | salary | is_manager |
|-------------|------------|-----------|-------------|------------|--------|------------|
| E1001       | Alice      | Johnson   | Engineering | 2020-03-15 | 95000  | Yes        |
| E1002       | Bob        | Smith     | Sales       | 2021-06-20 | 75000  | No         |

### 4. Create Transformation Examples

Create `examples/row1.json`:

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

Create `examples/row2.json`:

```json
{
  "input": {
    "employee_id": "E1002",
    "first_name": "Bob",
    "last_name": "Smith",
    "department": "Sales",
    "hire_date": "2021-06-20",
    "salary": 75000,
    "is_manager": "No"
  },
  "output": {
    "id": "E1002",
    "full_name": "Bob Smith",
    "dept": "Sales",
    "hired": "2021-06-20",
    "annual_salary_usd": 75000.0,
    "manager": false
  }
}
```

**Transformation Patterns Shown**:
- ✅ Field rename: `employee_id` → `id`
- ✅ Concatenation: `first_name + last_name` → `full_name`
- ✅ Field rename: `department` → `dept`
- ✅ Field rename: `hire_date` → `hired`
- ✅ Type conversion: `salary` (int) → `annual_salary_usd` (float)
- ✅ Boolean conversion: `is_manager` ("Yes"/"No") → `manager` (true/false)

### 5. Configure Project

Create `project.yaml`:

```yaml
name: Quick Start Employee Roster
description: Transform employee roster Excel to JSON
version: 1.0.0

data_source:
  type: excel
  config:
    file_path: input/roster.xlsx
    sheet_name: 0           # First sheet (0-indexed)
    header_row: 0           # First row is header

examples:
  - examples/row1.json
  - examples/row2.json

output:
  format: json
  directory: output/

validation:
  required_fields:
    - id
    - full_name
    - dept
  field_types:
    annual_salary_usd: float
    manager: boolean
```

### 6. Analyze Project

```bash
# Go back to project root
cd ../..

# Analyze transformation patterns
python -m edgar_analyzer analyze-project projects/quick_start_demo/
```

**Expected Output**:
```
Analyzing project: Quick Start Employee Roster
✓ Loading configuration
✓ Validating examples
✓ Analyzing transformation patterns

Detected Patterns:
  • Field Rename (confidence: 1.0)
    - employee_id → id
    - department → dept
    - hire_date → hired
  • String Concatenation (confidence: 1.0)
    - first_name + last_name → full_name
  • Type Conversion (confidence: 1.0)
    - salary (int) → annual_salary_usd (float)
  • Boolean Conversion (confidence: 1.0)
    - is_manager ("Yes"/"No") → manager (true/false)

Analysis complete! ✓
```

### 7. Generate Extractor Code

```bash
python -m edgar_analyzer generate-code projects/quick_start_demo/
```

**What Happens**:
1. Platform sends patterns to AI (Sonnet 4.5 via OpenRouter)
2. AI generates type-safe Python extractor code
3. Code is validated and saved to `output/extractor.py`

**Expected Output**:
```
Generating extractor code for: Quick Start Employee Roster
✓ Preparing transformation patterns
✓ Sending to AI for code generation
✓ Validating generated code
✓ Saving extractor to output/extractor.py

Code generation complete! ✓
Generated: output/extractor.py (234 lines)
```

### 8. Review Generated Code

```bash
head -50 projects/quick_start_demo/output/extractor.py
```

**Generated Code Structure**:
```python
from extract_transform_platform.core import IDataExtractor
from typing import Dict, Optional, Any, List

class EmployeeRosterExtractor(IDataExtractor):
    """Extract and transform employee roster data."""

    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract all employee records with transformations.

        Args:
            file_path: Path to Excel file

        Returns:
            List of transformed employee records
        """
        # Read Excel file
        df = pd.read_excel(file_path, sheet_name=0, header=0)

        results = []
        for _, row in df.iterrows():
            # Apply transformations
            record = self._transform_record(row)
            results.append(record)

        return results

    def _transform_record(self, row: pd.Series) -> Dict[str, Any]:
        """Transform single employee record."""
        return {
            "id": row["employee_id"],
            "full_name": f"{row['first_name']} {row['last_name']}",
            "dept": row["department"],
            "hired": str(row["hire_date"]),
            "annual_salary_usd": float(row["salary"]),
            "manager": row["is_manager"] == "Yes"
        }
```

The AI-generated code is:
- ✅ Type-safe (full type hints)
- ✅ Follows platform conventions
- ✅ Implements IDataExtractor interface
- ✅ Handles transformations correctly

### 9. Run Extraction

```bash
python -m edgar_analyzer run-extraction projects/quick_start_demo/
```

**Expected Output**:
```
Running extraction for: Quick Start Employee Roster
✓ Loading extractor from output/extractor.py
✓ Initializing EmployeeRosterExtractor
✓ Reading source data from input/roster.xlsx
✓ Extracting 10 records
✓ Applying transformations
✓ Validating output
✓ Saving to output/extracted_data.json

Extraction complete! ✓
Processed: 10 records
Output: output/extracted_data.json
```

### 10. Verify Results

```bash
cat projects/quick_start_demo/output/extracted_data.json | head -20
```

**Expected Output**:
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
    "dept": "Sales",
    "hired": "2021-06-20",
    "annual_salary_usd": 75000.0,
    "manager": false
  },
  ...
]
```

### 🎉 Success!

You've completed a full end-to-end workflow:
1. ✅ Created project with sample data
2. ✅ Defined transformation examples
3. ✅ Analyzed patterns automatically
4. ✅ Generated extractor code via AI
5. ✅ Ran extraction and got results

**Time**: ~10 minutes (after setup)

---

## Platform Workflows

Now that you've completed the tutorial, let's explore the platform in more detail.

### Workflow Overview

```
┌─────────────────┐
│  1. Setup       │  Create project, add source data
│  Project        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Provide     │  Create 2-3 transformation examples
│  Examples       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. Analyze     │  Platform detects patterns
│  Patterns       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. Generate    │  AI creates extractor code
│  Code           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. Run         │  Execute extraction
│  Extraction     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  6. Generate    │  Create reports (Excel, PDF, etc.)
│  Reports        │
└─────────────────┘
```

### Commands Reference

#### Project Management

```bash
# Create new project
python -m edgar_analyzer project create <name> [--template weather|news_scraper|minimal]

# List all projects
python -m edgar_analyzer project list

# Validate project configuration
python -m edgar_analyzer project validate <name>

# Delete project
python -m edgar_analyzer project delete <name> [--force]
```

#### Analysis and Code Generation

```bash
# Analyze transformation patterns
python -m edgar_analyzer analyze-project <project_path>

# Generate extractor code
python -m edgar_analyzer generate-code <project_path>

# Run extraction
python -m edgar_analyzer run-extraction <project_path>
```

#### Report Generation

```bash
# Generate Excel report
python -m edgar_analyzer report generate \
  --project <project_path> \
  --format excel \
  --output reports/output.xlsx

# Generate PDF report
python -m edgar_analyzer report generate \
  --project <project_path> \
  --format pdf \
  --output reports/output.pdf

# Generate all formats
python -m edgar_analyzer report generate \
  --project <project_path> \
  --format all \
  --output reports/
```

#### Setup and Validation

```bash
# Test OpenRouter connection
python -m edgar_analyzer setup test

# Validate API keys
python -m edgar_analyzer setup validate-keys

# Show configuration
python -m edgar_analyzer setup show-config
```

---

## Test Scenario Details

### Scenario 1: Excel File Transformation

**See**: [USER_TESTING_PLAN.md - Scenario 1](../USER_TESTING_PLAN.md#scenario-1-excel-file-transformation)

**Sample Data**: `test_data/employee_roster_sample.xlsx`

**Examples**: `test_data/examples/employee_roster/`

**Expected Duration**: 15-20 minutes

**Key Learnings**:
- How to configure Excel data source
- Creating transformation examples
- Pattern detection and confidence scores
- Handling type conversions

---

### Scenario 2: PDF Invoice Extraction

**See**: [USER_TESTING_PLAN.md - Scenario 2](../USER_TESTING_PLAN.md#scenario-2-pdf-invoice-extraction)

**Sample Data**: `test_data/invoice_sample.pdf`

**Examples**: `test_data/examples/invoice/`

**Expected Duration**: 15-20 minutes

**Key Learnings**:
- PDF table extraction strategies
- Currency parsing
- Handling different table layouts
- Page-specific extraction

**Table Strategies**:
- `lines` - For bordered tables (recommended for invoices)
- `text` - For borderless tables (plain text layouts)
- `mixed` - Hybrid approach (partially bordered tables)

---

### Scenario 3: Weather API Integration

**See**: [USER_TESTING_PLAN.md - Scenario 3](../USER_TESTING_PLAN.md#scenario-3-weather-api-integration)

**Template**: `templates/weather_project.yaml`

**API**: OpenWeatherMap (free tier)

**Expected Duration**: 10-15 minutes

**Key Learnings**:
- Using project templates
- Configuring API authentication
- Rate limiting and caching
- Real-time data extraction

**Setup OpenWeatherMap API**:
1. Visit https://openweathermap.org/api
2. Click "Sign Up" (free tier)
3. Verify email
4. Go to API Keys section
5. Copy your API key
6. Add to `.env.local`: `OPENWEATHERMAP_API_KEY=your_key`

---

### Scenario 4: Report Generation

**See**: [USER_TESTING_PLAN.md - Scenario 4](../USER_TESTING_PLAN.md#scenario-4-report-generation)

**Prerequisites**: Completed Scenario 1, 2, or 3

**Expected Duration**: 10 minutes

**Key Learnings**:
- Multi-format report generation
- Report templates and styling
- Data validation before reporting
- Output file management

**Supported Formats**:
- **Excel** (.xlsx) - Spreadsheet with formatting
- **PDF** (.pdf) - Professional document
- **DOCX** (.docx) - Microsoft Word document
- **PPTX** (.pptx) - PowerPoint presentation

---

### Scenario 5: Custom Workflow

**See**: [USER_TESTING_PLAN.md - Scenario 5](../USER_TESTING_PLAN.md#scenario-5-end-to-end-custom-workflow)

**Your Data**: Bring your own Excel, PDF, or API

**Expected Duration**: 30-45 minutes

**Key Learnings**:
- Complete workflow independence
- Handling edge cases
- Debugging and troubleshooting
- Real-world use case validation

**Tips for Success**:
- Start with small dataset (10-20 records)
- Provide 3 examples (not just 2)
- Test with edge cases (nulls, special characters)
- Review generated code before running

---

## Troubleshooting Guide

### Common Errors and Solutions

#### Error: "OpenRouter API key not found"

**Problem**: Missing or incorrect API key in `.env.local`

**Solution**:
```bash
# Check if .env.local exists
ls -la .env.local

# Add API key
echo "OPENROUTER_API_KEY=your_key_here" >> .env.local

# Verify
python -m edgar_analyzer setup test
```

---

#### Error: "Pattern detection failed"

**Problem**: AI couldn't identify clear transformation patterns from examples

**Solution**:
1. Add a 3rd example to clarify patterns
2. Ensure examples show consistent transformations
3. Check input/output field names match exactly
4. Review example JSON for syntax errors

```bash
# Validate example JSON
python -c "import json; json.load(open('examples/row1.json'))"
```

---

#### Error: "Table not detected in PDF"

**Problem**: PDF table extraction strategy doesn't match document structure

**Solution**:
Try different table strategies in `project.yaml`:

```yaml
data_source:
  type: pdf
  config:
    table_strategy: lines  # Change to 'text' or 'mixed'
```

**Table Strategy Guide**:
- **lines**: Bordered tables (most invoices, reports)
- **text**: Plain text tables (no borders)
- **mixed**: Partially bordered tables

---

#### Error: "Code generation timeout"

**Problem**: OpenRouter API taking too long or quota exceeded

**Solution**:
1. Check OpenRouter dashboard for quota limits
2. Wait 1 minute and retry
3. Simplify transformation patterns
4. Reduce number of examples

```bash
# Check API status
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models
```

---

#### Error: "Extraction failed: No module named 'pandas'"

**Problem**: Missing dependencies

**Solution**:
```bash
# Reinstall with dev dependencies
pip install -e ".[dev]"

# Verify pandas installed
python -c "import pandas; print(pandas.__version__)"
```

---

#### Error: "Permission denied" writing to output/

**Problem**: Insufficient file system permissions

**Solution**:
```bash
# Check permissions
ls -la projects/my_project/

# Fix permissions
chmod -R u+w projects/my_project/output/

# Or use sudo (not recommended)
sudo python -m edgar_analyzer run-extraction projects/my_project/
```

---

### Where to Find Logs

**Application Logs**:
```bash
# View recent logs
tail -50 logs/edgar_analyzer.log

# Follow logs in real-time
tail -f logs/edgar_analyzer.log

# Search for errors
grep -i error logs/edgar_analyzer.log
```

**Test Logs**:
```bash
# View test output
cat tests/results/latest_test_run.log
```

---

### How to Report Bugs

**GitHub Issues**: Preferred for public bugs

1. Go to: https://github.com/yourorg/edgar/issues
2. Click "New Issue"
3. Choose "Bug Report" template
4. Add "alpha-tester" label
5. Include:
   - Operating system and Python version
   - Complete error message
   - Steps to reproduce
   - Relevant configuration files
   - Log files (sanitize sensitive data!)

**Email**: For private or sensitive issues

Send to: edgar-support@example.com

Include:
- Subject: `[Alpha Testing] Your Issue Title`
- Description of problem
- Steps to reproduce
- Attachments: logs, config files, screenshots

---

### Getting Help

**Slack**: #edgar-alpha-testing (fastest response)
- Tag @dev-team for urgent issues
- Share screenshots and errors
- Learn from other testers

**Documentation**:
- [Platform Usage Guide](./PLATFORM_USAGE.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
- [Quick Start](./QUICK_START.md)

**Office Hours** (Optional):
- Daily 2-3 PM EST during alpha testing week
- Video call link: [to be provided]

---

## Tips for Effective Testing

### Before You Start

1. **Read Documentation** - Skim the Quick Start and Platform Usage guides
2. **Set Up Environment** - Complete all setup steps before testing
3. **Allocate Time** - Block 2-3 hours for uninterrupted testing
4. **Take Notes** - Document issues as you encounter them

### During Testing

1. **Think Out Loud** - If doing screen share, narrate your thoughts
2. **Try to Break It** - Test edge cases and unusual inputs
3. **Compare Expectations** - Note when behavior differs from expectations
4. **Ask Questions** - No question is too basic or silly

### After Testing

1. **Complete Feedback Form** - Provide detailed, honest feedback
2. **Share Examples** - Provide sample data if you encountered issues
3. **Suggest Improvements** - What would make this more useful for you?
4. **Follow Up** - Available for optional interview if requested

---

## Feedback Form

See `docs/USER_FEEDBACK_TEMPLATE.md` for complete feedback form.

**Quick Feedback Checklist**:

**Ratings** (1-5 scale):
- [ ] Ease of use
- [ ] Documentation quality
- [ ] Error message clarity
- [ ] Performance
- [ ] Overall satisfaction

**Yes/No Questions**:
- [ ] Did you complete all scenarios?
- [ ] Did you encounter any blockers?
- [ ] Would you recommend this platform?
- [ ] Does this solve a real problem for you?

**Open Feedback**:
- What worked well?
- What was confusing or frustrating?
- What features are missing?
- What would you use this for?

---

## Next Steps After Testing

1. **Complete Feedback Form** - Submit within 24 hours of testing
2. **Optional Interview** - Schedule 15-minute follow-up call
3. **Stay Engaged** - Join #edgar-alpha-testing Slack for updates
4. **Beta Access** - Get early access to beta release

---

## Appendix

### Keyboard Shortcuts

**CLI Navigation**:
- `Ctrl+C` - Cancel current command
- `Ctrl+Z` - Suspend current command
- `Ctrl+R` - Search command history
- `↑ / ↓` - Navigate command history

**Editor Shortcuts** (nano):
- `Ctrl+O` - Save file
- `Ctrl+X` - Exit
- `Ctrl+K` - Cut line
- `Ctrl+U` - Paste line

### Quick Reference Card

```bash
# PROJECT SETUP
edgar_analyzer project create <name>
cd projects/<name>
mkdir input examples output

# CONFIGURE
nano project.yaml
nano examples/row1.json

# RUN WORKFLOW
edgar_analyzer analyze-project .
edgar_analyzer generate-code .
edgar_analyzer run-extraction .

# GENERATE REPORTS
edgar_analyzer report generate --format excel
edgar_analyzer report generate --format pdf

# VALIDATE
edgar_analyzer project validate <name>
edgar_analyzer setup test
```

### Sample Data Locations

```
test_data/
├── employee_roster_sample.xlsx     # Excel sample
├── invoice_sample.pdf              # PDF sample
├── examples/
│   ├── employee_roster/            # Excel examples
│   └── invoice/                    # PDF examples
└── instructions/
    ├── api_setup.md                # API key setup
    └── quick_reference.md          # Command cheat sheet
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-04
**Maintained By**: Platform Development Team
**Questions?** Slack: #edgar-alpha-testing | Email: edgar-support@example.com
