# EDGAR Platform - Claude Code Agent Guide

**Project Type**: General-purpose, example-driven data extraction & transformation platform
**Original Focus**: SEC EDGAR executive compensation (transforming into generic platform)
**Agent Role**: Build general-purpose platform that works from examples (70% code reuse from EDGAR)

**Linear Project**: [EDGAR → General-Purpose Extract & Transform Platform](https://linear.app/1m-hyperdev/project/edgar-%E2%86%92-general-purpose-extract-and-transform-platform-e4cb3518b13e/issues)
**Epic ID**: `edgar-e4cb3518b13e` / `4a248615-f1dd-4669-9f61-edec2d2355ac`

---

## Platform Vision (Phase 2 GO Decision Approved ✅)

Transform EDGAR into a **general-purpose platform** supporting 4 major work paths:
- **a) Project-based workflows** (external artifacts directory)
- **b) File transformation** (Excel, PDF, DOCX, PPTX → structured data)
- **c) Web scraping/research** (JS-heavy sites with Jina.ai)
- **d) Interactive workflows** (example-driven, user-prompted confidence threshold)

**Status**: Phase 1 MVP validated (92% confidence GO decision), Phase 2 approved
**Timeline**: 6 weeks total (currently in Phase 2: Core Platform Architecture)

---

## Quick Navigation

- [Project Overview](#project-overview)
- [Priority Workflows](#priority-workflows-)
- [Excel File Transform (NEW)](#excel-file-transform-new-)
- [Documentation Index](#documentation-index)
- [Code Architecture](#code-architecture)
- [Development Patterns](#development-patterns)
- [Common Tasks](#common-tasks)

---

## Project Overview

### What This Does
Extracts executive compensation data from SEC EDGAR filings using:
- **XBRL data extraction** (2x better success rate)
- **Multi-source data integration** (Fortune rankings + EDGAR)
- **CSV and spreadsheet report generation**
- **Self-improving code patterns with LLM integration**

### Key Capabilities
- Fortune 500 company analysis
- Historical compensation tracking
- XBRL-enhanced extraction (breakthrough achievement)
- Data source validation and verification
- Automated report generation

### Tech Stack
- **Language**: Python 3.11+
- **Key Libraries**: Click, Pandas, BeautifulSoup4, Pydantic, Dependency Injector
- **Data Sources**: SEC EDGAR API, XBRL filings, Fortune rankings
- **Tools**: pytest, black, isort, mypy, pre-commit

---

## Priority Workflows 🔴🟡🟢⚪

### 🔴 CRITICAL - Run These First

#### Extract EDGAR Data
```bash
# Single command to run analysis
python -m edgar_analyzer extract --cik 0000320193 --year 2023

# Using the CLI launcher
./edgar_cli.sh
```

#### Run Tests
```bash
# All tests
make test

# Specific test suites
pytest tests/unit/
pytest tests/integration/
```

#### Generate Reports
```bash
# CSV reports
python create_csv_reports.py

# Excel spreadsheet
python create_report_spreadsheet.py
```

### 🟡 IMPORTANT - Daily Operations

#### Build Deployment Package
```bash
# Create distribution package
make build

# Alternative: direct script
python create_deployment_package.py
```

#### Code Quality Checks
```bash
# Run all quality checks
make quality

# Individual checks
make lint
make format
make typecheck
```

#### View Documentation
```bash
# Open documentation hub
open docs/README.md

# Quick start guide
open docs/guides/QUICK_START.md
```

### 🟢 USEFUL - Enhancement Tasks

#### Run Fortune 100 Analysis
```bash
# Complete Fortune 100 with real data
python tests/run_complete_fortune_100_with_real_data.py

# Enhanced top 100 analysis
python tests/run_top_100_enhanced.py
```

#### Validate Data Quality
```bash
# Comprehensive QA
python tests/run_comprehensive_qa.py

# Fast QA cleanup
python tests/run_fast_qa_cleanup.py
```

#### Test XBRL Extraction
```bash
# Breakthrough XBRL service test
python tests/test_breakthrough_xbrl_service.py

# XBRL executive compensation
python tests/test_xbrl_executive_compensation.py
```

### ⚪ REFERENCE - Background Info

#### Project Documentation
- [Complete Documentation Hub](docs/README.md)
- [Quick Start Guide](docs/guides/QUICK_START.md)
- [CLI Usage Guide](docs/guides/CLI_USAGE.md)
- [Data Dictionary](docs/DATA_DICTIONARY.md)
- [Methodology & Data Sources](docs/METHODOLOGY_AND_DATA_SOURCES.md)

---

## Excel File Transform (NEW) 🆕

**Status**: ✅ Phase 1 Complete (398 LOC, 80% coverage, 35/35 validations passing)

### Quick Start: Transform Excel → JSON

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

### Example: Employee Roster POC

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

### Key Features

1. **ExcelDataSource** - Read .xlsx/.xls files with pandas
2. **Schema-aware parsing** - Automatic type inference
3. **Pattern detection** - AI detects 6+ transformation types
4. **Code generation** - Produces type-safe extractors
5. **Validation** - Auto-generated pytest tests

### Documentation

- **[Excel File Transform Guide](docs/guides/EXCEL_FILE_TRANSFORM.md)** - Complete user guide
- **[ExcelDataSource Technical Reference](docs/architecture/EXCEL_DATA_SOURCE.md)** - Implementation details
- **[Employee Roster Tutorial](projects/employee_roster/TUTORIAL.md)** - Step-by-step walkthrough
- **[Employee Roster POC](projects/employee_roster/)** - Working proof-of-concept

### Supported Transformations

| Type | Example | Detection |
|------|---------|-----------|
| **Field Rename** | `employee_id` → `id` | Schema comparison |
| **Concatenation** | `first_name + last_name` → `full_name` | Value matching |
| **Type Convert** | `salary: 95000` (int) → `95000.0` (float) | Type change |
| **Boolean** | `"Yes"` → `true`, `"No"` → `false` | Pattern recognition |
| **Value Mapping** | `"A"` → `"Active"`, `"I"` → `"Inactive"` | Discrete mapping |
| **Field Extract** | `"alice@ex.com"` → `"ex.com"` | Substring patterns |

### Performance

| Rows | Columns | File Size | Read Time | Memory |
|------|---------|-----------|-----------|--------|
| 100 | 7 | 15 KB | 45 ms | 3 MB |
| 1,000 | 7 | 120 KB | 180 ms | 12 MB |
| 10,000 | 7 | 1.2 MB | 950 ms | 85 MB |

**End-to-End**: <10 seconds (read → analyze → generate → validate)

---

## Documentation Index

### User Guides
- **[Quick Start](docs/guides/QUICK_START.md)** - 5-minute setup
- **[CLI Usage](docs/guides/CLI_USAGE.md)** - Complete CLI reference
- **[Excel File Transform](docs/guides/EXCEL_FILE_TRANSFORM.md)** - Excel → JSON transformation (NEW 🆕)
- **[Data Interpretation](docs/USER_GUIDE_DATA_INTERPRETATION.md)** - Understanding results

### Technical Documentation
- **[Architecture Overview](docs/architecture/PROJECT_STRUCTURE.md)** - Codebase structure
- **[ExcelDataSource Reference](docs/architecture/EXCEL_DATA_SOURCE.md)** - Excel parsing implementation (NEW 🆕)
- **[Self-Improving Pattern](docs/architecture/SELF_IMPROVING_CODE_PATTERN.md)** - LLM enhancement
- **[OpenRouter Architecture](docs/architecture/OPENROUTER_ARCHITECTURE.md)** - API design
- **[Feasibility Analysis](docs/architecture/FEASIBILITY_ANALYSIS.md)** - Technical analysis

### Developer Guides
- **[Code Governance](docs/guides/CODE_GOVERNANCE.md)** - Development standards
- **[API Key Security](docs/guides/API_KEY_SECURITY.md)** - Secret management
- **[Security Guidelines](docs/guides/SECURITY.md)** - Security best practices

### Research & Achievements
- **[XBRL Breakthrough](docs/BREAKTHROUGH_XBRL_EXECUTIVE_COMPENSATION.md)** - 2x success rate
- **[Research Summary](docs/RESEARCH_BREAKTHROUGH_SUMMARY.md)** - Major findings
- **[Data Sources](docs/EXECUTIVE_COMPENSATION_DATA_SOURCES.md)** - Source analysis
- **[Action Plan](docs/EXECUTIVE_COMPENSATION_ACTION_PLAN.md)** - Implementation roadmap

### Data References
- **[Data Dictionary](docs/DATA_DICTIONARY.md)** - Field definitions
- **[Data Sources](DATA_SOURCES.md)** - Source tracking
- **[Methodology](docs/METHODOLOGY_AND_DATA_SOURCES.md)** - Analysis methodology

---

## Code Architecture

### Project Structure
```
edgar/
├── src/
│   ├── edgar_analyzer/          # Main application
│   │   ├── services/            # Core business logic
│   │   │   ├── breakthrough_xbrl_service.py    # XBRL extraction (KEY)
│   │   │   ├── multi_source_enhanced_service.py # Multi-source integration
│   │   │   ├── edgar_api_service.py            # SEC EDGAR API
│   │   │   ├── data_extraction_service.py      # Data extraction
│   │   │   └── report_service.py               # Report generation
│   │   ├── data_sources/        # Data source abstraction (NEW 🆕)
│   │   │   ├── base.py          # BaseDataSource abstract class
│   │   │   ├── excel_source.py  # Excel file source (398 LOC)
│   │   │   ├── file_source.py   # CSV/JSON/YAML file source
│   │   │   └── api_source.py    # REST API source
│   │   ├── models/              # Data models
│   │   │   ├── company.py       # Company data structures
│   │   │   └── intermediate_data.py # Processing models
│   │   ├── cli/                 # CLI interface
│   │   ├── config/              # Configuration & DI
│   │   ├── validation/          # Data validation
│   │   └── utils/               # Utilities
│   ├── cli_chatbot/             # Conversational interface
│   └── self_improving_code/     # LLM enhancement system
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   │   └── data_sources/        # Data source tests (69 tests, 80% coverage)
│   ├── integration/             # Integration tests
│   └── results/                 # Test results
├── docs/                         # Documentation
│   ├── guides/                  # User guides
│   │   └── EXCEL_FILE_TRANSFORM.md  # Excel transform guide (NEW 🆕)
│   └── architecture/            # Technical docs
│       └── EXCEL_DATA_SOURCE.md     # ExcelDataSource reference (NEW 🆕)
├── projects/                     # Transformation projects (NEW 🆕)
│   ├── employee_roster/         # Employee roster POC (35/35 validations)
│   │   ├── input/               # Source Excel files
│   │   ├── examples/            # Transformation examples
│   │   ├── output/              # Generated code
│   │   └── TUTORIAL.md          # Step-by-step tutorial (NEW 🆕)
│   └── weather_api/             # Weather API POC (proven template)
├── data/                         # Data files
│   ├── companies/               # Company lists
│   ├── cache/                   # API cache
│   └── checkpoints/             # Analysis checkpoints
└── output/                       # Generated reports
```

### Key Components

#### 1. XBRL Extraction Service (BREAKTHROUGH)
**File**: `src/edgar_analyzer/services/breakthrough_xbrl_service.py`
- **Achievement**: 2x better success rate vs previous methods
- **Function**: Extract executive compensation from XBRL filings
- **Key Features**:
  - Concept-based data extraction
  - Multi-year support
  - Role-based executive matching
  - Data validation

#### 2. Multi-Source Enhanced Service
**File**: `src/edgar_analyzer/services/multi_source_enhanced_service.py`
- **Function**: Integrate data from multiple sources
- **Sources**: EDGAR, Fortune rankings, XBRL data
- **Features**: Source tracking, data verification, quality scoring

#### 3. EDGAR API Service
**File**: `src/edgar_analyzer/services/edgar_api_service.py`
- **Function**: Interface with SEC EDGAR API
- **Features**: Rate limiting, caching, error handling
- **Endpoints**: Company submissions, facts API, filings search

#### 4. Report Generation
**Files**:
- `src/edgar_analyzer/services/report_service.py`
- `create_csv_reports.py`
- `create_report_spreadsheet.py`
- **Function**: Generate CSV and Excel reports
- **Formats**: Multiple output formats, data visualization

#### 5. ExcelDataSource (NEW - Phase 2) 🆕
**File**: `src/edgar_analyzer/data_sources/excel_source.py`
- **Achievement**: 70% code reuse from FileDataSource pattern
- **Function**: Read and parse Excel spreadsheets (.xlsx, .xls)
- **Key Features**:
  - Schema-aware parsing with pandas
  - Automatic type inference (int, float, date, string, boolean)
  - Compatible with SchemaAnalyzer for pattern detection
  - No caching (local files - no network overhead)
  - NaN handling (converts to None for JSON compatibility)
- **Performance**: <50ms for 100 rows, <1s for 10k rows
- **Test Coverage**: 80% (69 tests, all passing)
- **POC**: Employee roster (35/35 validations passing)

---

## Development Patterns

### Code Style Standards
```bash
# Format code (auto-fix)
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Testing Patterns
```python
# Unit test pattern
import pytest
from edgar_analyzer.services import BreakthroughXBRLService

def test_xbrl_extraction():
    service = BreakthroughXBRLService()
    result = service.extract_compensation(cik="0000320193", year=2023)
    assert result is not None
    assert "executives" in result
```

### Dependency Injection
```python
# Using dependency-injector
from edgar_analyzer.config.container import Container

container = Container()
container.wire(modules=[__name__])

# Inject services
service = container.edgar_api_service()
```

### Error Handling
```python
# Standard error handling pattern
try:
    result = service.extract_data(cik)
except EdgarAPIError as e:
    logger.error(f"API error: {e}")
    return None
except ValidationError as e:
    logger.warning(f"Validation error: {e}")
    return default_value
```

---

## Common Tasks

### Add New Company Analysis
```bash
# 1. Add company to data file
vim data/companies/fortune_500_complete.json

# 2. Run extraction
python -m edgar_analyzer extract --cik <CIK> --year 2023

# 3. Verify results
ls -la output/
```

### Debug Extraction Issues
```bash
# 1. Enable debug logging
export LOG_LEVEL=DEBUG

# 2. Run with specific company
python tests/debug_xbrl_concepts.py

# 3. Check logs
tail -f logs/edgar_analyzer.log
```

### Update Documentation
```bash
# 1. Edit relevant doc
vim docs/guides/QUICK_START.md

# 2. Validate links
grep -r "](.*\.md)" docs/

# 3. Preview changes
open docs/README.md
```

### Run Quality Checks
```bash
# Before commit - run all checks
black --check src/ tests/
isort --check src/ tests/
flake8 src/ tests/
mypy src/
pytest tests/

# Auto-fix issues
black src/ tests/
isort src/ tests/
```

### Create Deployment Package
```bash
# 1. Build package
python create_deployment_package.py

# 2. Verify package
unzip -l edgar-analyzer-package.zip

# 3. Test package
cd edgar-analyzer-package/
python -m edgar_analyzer --help
```

---

## Agent Best Practices

### EDGAR Data Extraction
1. **Always use XBRL service first** - Breakthrough service has 2x success rate
2. **Check cache before API calls** - Respect SEC rate limits
3. **Validate data sources** - Track where data comes from
4. **Handle missing data gracefully** - Not all companies have complete data

### Code Quality
1. **Run tests before committing** - Use `pytest tests/`
2. **Format code automatically** - Use `black` and `isort`
3. **Type hints required** - Use mypy for type checking
4. **Document complex logic** - Clear docstrings and comments

### File Organization
1. **Keep tests with code** - Tests in `tests/` mirror `src/`
2. **Results in dedicated directory** - Use `tests/results/` for outputs
3. **Documentation in docs/** - Organized by category
4. **Cache in data/cache/** - Temporary API data

### Performance Optimization
1. **Use caching** - Cache API responses in `data/cache/`
2. **Batch operations** - Process multiple companies in parallel
3. **Checkpoint analysis** - Save intermediate results
4. **Monitor rate limits** - SEC EDGAR has rate limiting

---

## Environment Setup

### Required Environment Variables
```bash
# .env.local (gitignored)
OPENROUTER_API_KEY=your_api_key_here
SEC_EDGAR_USER_AGENT=YourName/YourEmail
LOG_LEVEL=INFO
```

### Virtual Environment
```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate  # Unix
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"
```

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Key Learnings & Patterns

### XBRL Extraction Breakthrough
- **Pattern**: Concept-based extraction > HTML parsing
- **Success Rate**: 2x improvement over previous methods
- **Key Concepts**: `us-gaap:*Compensation*`, role-based matching
- **File**: `src/edgar_analyzer/services/breakthrough_xbrl_service.py`

### Multi-Source Data Integration
- **Pattern**: Combine EDGAR + Fortune + XBRL for completeness
- **Tracking**: Always record data source in results
- **Validation**: Cross-reference multiple sources
- **File**: `src/edgar_analyzer/services/multi_source_enhanced_service.py`

### Self-Improving Code
- **Pattern**: LLM supervisor + engineer for code enhancement
- **Safety**: Git checkpoints before modifications
- **Validation**: AST-based script validation
- **Files**: `src/self_improving_code/`

### Report Generation
- **Pattern**: CSV for data, Excel for presentation
- **Multiple formats**: Support various output needs
- **Validation**: Data quality checks before output
- **Files**: `create_csv_reports.py`, `create_report_spreadsheet.py`

### Excel File Transform (NEW - Phase 2) 🆕
- **Pattern**: Example-driven transformation (same as Weather API)
- **Schema Detection**: Automatic pattern recognition from 2-3 examples
- **Type Safety**: Pydantic models + pandas type inference
- **Code Reuse**: 70% from FileDataSource (CSV pattern)
- **Files**: `src/edgar_analyzer/data_sources/excel_source.py`
- **POC**: `projects/employee_roster/` (35/35 validations passing)
- **Transformations Supported**:
  - Field renaming (employee_id → id)
  - String concatenation (first_name + last_name → full_name)
  - Type conversions (int → float, string → date)
  - Boolean normalization ("Yes"/"No" → true/false)
  - Value mapping (discrete value transformations)
  - Field extraction (substring patterns)

---

## Troubleshooting

### Common Issues

#### API Rate Limiting
```bash
# Problem: Too many API calls
# Solution: Use cache, add delays
export EDGAR_RATE_LIMIT_DELAY=0.5
```

#### Missing XBRL Data
```bash
# Problem: XBRL extraction fails
# Solution: Check filing type, year availability
python tests/debug_xbrl_concepts.py
```

#### Data Validation Errors
```bash
# Problem: Data fails validation
# Solution: Run QA checks
python tests/run_comprehensive_qa.py
```

#### Import Errors
```bash
# Problem: Module not found
# Solution: Install in editable mode
pip install -e ".[dev]"
```

---

## Memory Categories for Agent Learning

**EDGAR Extraction Patterns**: XBRL extraction techniques, concept mapping, success rates
**Data Source Integration**: Multi-source patterns, validation methods, tracking
**Excel File Transform (NEW)**: Example-driven approach, schema detection, transformation patterns, pandas usage
**Report Generation**: Output formats, data presentation, quality standards
**Code Quality**: Testing patterns, type checking, formatting standards
**Performance**: Caching strategies, batch processing, rate limiting
**Common Issues**: Known bugs, workarounds, debugging techniques

---

## Quick Reference Commands

```bash
# ONE command to run analysis
python -m edgar_analyzer extract --cik 0000320193 --year 2023

# ONE command to generate reports
python create_csv_reports.py

# ONE command to transform Excel file (NEW 🆕)
python -m edgar_analyzer analyze-project projects/employee_roster/

# ONE command to run tests
pytest tests/

# ONE command to check code quality
make quality

# ONE command to build package
python create_deployment_package.py

# ONE command to view docs
open docs/README.md

# ONE command to view Excel tutorial (NEW 🆕)
open projects/employee_roster/TUTORIAL.md
```

---

**Agent Role**: Build general-purpose extract & transform platform from EDGAR foundation (70% code reuse), focusing on example-driven workflows and multi-format support.

**Success Criteria (Platform Transformation)**:
- ✅ Phase 1 MVP validated (92% confidence)
- ✅ All 4 work paths functional (project-based, file transform, web scraping, interactive)
- ✅ Excel/PDF/DOCX/PPTX support implemented
- ✅ External artifacts directory configured
- ✅ JS-heavy web scraping with Jina.ai
- ✅ User-prompted confidence threshold
- ✅ All tests passing
- ✅ Code quality standards met

**User Preferences (Confirmed 2025-11-28)**:
1. Office format priority: Excel → PDF → DOCX → PPTX
2. Artifact storage: External directory (outside repo)
3. Web scraping: JS-heavy sites (Jina.ai key provided, no auth yet)
4. Example collection: Exemplar-based with data types
5. Confidence threshold: User choice (prompted)
6. Project workflow: Sequential (one project at a time)

**Linear Project**: [View all issues](https://linear.app/1m-hyperdev/project/edgar-%E2%86%92-general-purpose-extract-and-transform-platform-e4cb3518b13e/issues)

**Contact**: See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for full project context.
