# EDGAR Analyzer - Claude Code Agent Guide

**Project Type**: Python CLI tool for SEC EDGAR data analysis
**Focus**: Executive compensation extraction from SEC filings
**Agent Role**: Optimize EDGAR data workflows and Python codebase maintenance

---

## Quick Navigation

- [Project Overview](#project-overview)
- [Priority Workflows](#priority-workflows-)
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

## Documentation Index

### User Guides
- **[Quick Start](docs/guides/QUICK_START.md)** - 5-minute setup
- **[CLI Usage](docs/guides/CLI_USAGE.md)** - Complete CLI reference
- **[Data Interpretation](docs/USER_GUIDE_DATA_INTERPRETATION.md)** - Understanding results

### Technical Documentation
- **[Architecture Overview](docs/architecture/PROJECT_STRUCTURE.md)** - Codebase structure
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
│   ├── integration/             # Integration tests
│   └── results/                 # Test results
├── docs/                         # Documentation
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

# ONE command to run tests
pytest tests/

# ONE command to check code quality
make quality

# ONE command to build package
python create_deployment_package.py

# ONE command to view docs
open docs/README.md
```

---

**Agent Role**: Optimize EDGAR data extraction workflows, maintain code quality, enhance documentation, and improve data processing efficiency.

**Success Criteria**:
- ✅ XBRL extraction success rate > 90%
- ✅ Data source tracking 100% accurate
- ✅ All tests passing
- ✅ Code quality standards met
- ✅ Documentation up-to-date

**Contact**: See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for full project context.
