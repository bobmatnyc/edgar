# EDGAR Analyzer - Developer Guide

**Target Audience**: Developers contributing to the EDGAR Analyzer project
**Focus**: Technical architecture, development workflow, and coding standards

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Code Organization](#code-organization)
- [Coding Standards](#coding-standards)
- [Testing Strategy](#testing-strategy)
- [Debugging Guide](#debugging-guide)
- [Contributing Workflow](#contributing-workflow)

---

## Quick Start

### 5-Minute Developer Setup

```bash
# 1. Clone and enter project
git clone <repository-url>
cd edgar

# 2. Complete automated setup
make setup

# 3. Activate virtual environment
source venv/bin/activate

# 4. Configure API keys
cp .env.template .env.local
# Edit .env.local with your keys

# 5. Run tests to verify
make test

# 6. Start development
make dev
```

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Interface Layer                   │
│  ┌─────────────────┐        ┌─────────────────────┐    │
│  │ Conversational  │        │  Traditional CLI    │    │
│  │    Interface    │        │   (Click-based)     │    │
│  └────────┬────────┘        └──────────┬──────────┘    │
└───────────┼────────────────────────────┼────────────────┘
            │                            │
┌───────────┴────────────────────────────┴────────────────┐
│              Service Layer (Business Logic)              │
│  ┌──────────────────┐  ┌─────────────────────────┐     │
│  │ XBRL Extraction  │  │ Multi-Source Enhanced   │     │
│  │   (Breakthrough) │  │        Service          │     │
│  └──────┬───────────┘  └──────────┬──────────────┘     │
│         │                          │                     │
│  ┌──────┴────────────┐  ┌─────────┴──────────────┐    │
│  │  EDGAR API        │  │  Data Extraction       │    │
│  │    Service        │  │     Service            │    │
│  └──────┬────────────┘  └──────────┬─────────────┘    │
└─────────┼───────────────────────────┼──────────────────┘
          │                           │
┌─────────┴───────────────────────────┴──────────────────┐
│              Data Layer & External APIs                  │
│  ┌─────────────┐  ┌──────────┐  ┌─────────────────┐   │
│  │ SEC EDGAR   │  │   XBRL   │  │   File Cache    │   │
│  │     API     │  │   Data   │  │   (data/cache)  │   │
│  └─────────────┘  └──────────┘  └─────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Services Layer (`src/edgar_analyzer/services/`)

**BreakthroughXBRLService** - XBRL data extraction
- **Responsibility**: Extract executive compensation from XBRL filings
- **Key Achievement**: 2x success rate improvement
- **Pattern**: Concept-based extraction with role matching
- **File**: `breakthrough_xbrl_service.py`

**MultiSourceEnhancedService** - Multi-source data integration
- **Responsibility**: Combine data from EDGAR, XBRL, and Fortune rankings
- **Pattern**: Source tracking and validation
- **File**: `multi_source_enhanced_service.py`

**EdgarAPIService** - SEC EDGAR API interface
- **Responsibility**: HTTP client for SEC EDGAR API
- **Features**: Rate limiting, caching, error handling
- **File**: `edgar_api_service.py`

**DataExtractionService** - Core data extraction logic
- **Responsibility**: Orchestrate data extraction workflow
- **Pattern**: Strategy pattern for different extraction methods
- **File**: `data_extraction_service.py`

**ReportService** - Report generation
- **Responsibility**: Generate CSV and Excel reports
- **File**: `report_service.py`

#### 2. Models Layer (`src/edgar_analyzer/models/`)

**Company** - Company data model
- **Fields**: CIK, name, ticker, industry, etc.
- **Validation**: Pydantic-based validation
- **File**: `company.py`

**IntermediateData** - Processing data models
- **Purpose**: Hold intermediate processing state
- **Pattern**: Immutable data structures
- **File**: `intermediate_data.py`

#### 3. Configuration Layer (`src/edgar_analyzer/config/`)

**Container** - Dependency injection container
- **Pattern**: Dependency injector framework
- **Purpose**: Manage service dependencies
- **File**: `container.py`

**Settings** - Application configuration
- **Source**: Environment variables, .env files
- **Pattern**: Pydantic settings management
- **File**: `settings.py`

#### 4. CLI Layer (`src/edgar_analyzer/cli/`)

**Main CLI** - Click-based command interface
- **Commands**: extract, test, analyze
- **Pattern**: Click command groups
- **File**: `main.py`

#### 5. Validation Layer (`src/edgar_analyzer/validation/`)

**DataValidator** - Data quality validation
- **Checks**: Completeness, accuracy, consistency
- **File**: `data_validator.py`

**SanityChecker** - Sanity checks for extracted data
- **Checks**: Range validation, logical consistency
- **File**: `sanity_checker.py`

**SourceVerifier** - Data source verification
- **Purpose**: Track and verify data sources
- **File**: `source_verifier.py`

---

## Development Setup

### Prerequisites

- **Python 3.11+** (3.13 recommended)
- **pip** (latest version)
- **git** (for version control)
- **make** (for build automation)

### Environment Setup

```bash
# 1. Create virtual environment
make venv

# 2. Activate virtual environment
source venv/bin/activate  # Unix/macOS
.\venv\Scripts\activate   # Windows

# 3. Install dependencies
make install

# 4. Install pre-commit hooks
make pre-commit

# 5. Configure environment
cp .env.template .env.local
# Edit .env.local with your API keys
```

### Required API Keys

```bash
# .env.local
OPENROUTER_API_KEY=your_openrouter_api_key_here
SEC_EDGAR_USER_AGENT=YourName/YourEmail
LOG_LEVEL=DEBUG  # For development
```

### Verify Installation

```bash
# Run test suite
make test

# Check code quality
make quality

# Start application
make dev
```

---

## Code Organization

### Directory Structure

```
edgar/
├── src/edgar_analyzer/          # Main application code
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # Entry point (python -m edgar_analyzer)
│   ├── main_cli.py              # CLI entry point
│   │
│   ├── services/                # Business logic services
│   │   ├── breakthrough_xbrl_service.py      # XBRL extraction (KEY)
│   │   ├── multi_source_enhanced_service.py  # Multi-source integration
│   │   ├── edgar_api_service.py              # SEC EDGAR API
│   │   ├── data_extraction_service.py        # Data extraction
│   │   ├── report_service.py                 # Report generation
│   │   ├── cache_service.py                  # Caching
│   │   └── interfaces.py                     # Service interfaces
│   │
│   ├── models/                  # Data models
│   │   ├── company.py           # Company data
│   │   └── intermediate_data.py # Processing models
│   │
│   ├── cli/                     # CLI interface
│   │   ├── __init__.py
│   │   └── main.py              # Click commands
│   │
│   ├── config/                  # Configuration
│   │   ├── container.py         # DI container
│   │   └── settings.py          # Settings management
│   │
│   ├── validation/              # Data validation
│   │   ├── data_validator.py
│   │   ├── sanity_checker.py
│   │   └── source_verifier.py
│   │
│   ├── utils/                   # Utilities
│   │   └── fortune500_builder.py
│   │
│   ├── extractors/              # Data extractors
│   │   └── adaptive_compensation_extractor.py
│   │
│   └── controllers/             # Controllers
│       └── self_improving_extraction_controller.py
│
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── results/                 # Test results
│   └── README.md                # Test documentation
│
├── docs/                        # Documentation
│   ├── guides/                  # User guides
│   ├── architecture/            # Architecture docs
│   └── api/                     # API documentation
│
├── data/                        # Data files
│   ├── companies/               # Company lists
│   ├── cache/                   # API cache (gitignored)
│   └── checkpoints/             # Analysis checkpoints
│
└── output/                      # Generated reports
```

### Module Dependencies

```
CLI Layer
    ↓
Service Layer
    ↓
Models Layer
    ↓
External APIs (SEC EDGAR, etc.)
```

**Dependency Rules**:
- CLI layer imports from Service layer
- Service layer imports from Models layer
- Models layer has no internal dependencies
- Cross-service dependencies via dependency injection

---

## Coding Standards

### Python Style Guide

**Follow PEP 8** with these tools:
- **black**: Code formatting (88 char line length)
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### Code Formatting

```bash
# Auto-format code
make format

# Check formatting
black --check src/ tests/
isort --check src/ tests/

# Lint code
make lint
```

### Type Hints

**Required for all functions**:

```python
from typing import Optional, List, Dict, Any

def extract_compensation(
    cik: str,
    year: int,
    filing_type: str = "DEF 14A"
) -> Optional[Dict[str, Any]]:
    """Extract executive compensation data.

    Args:
        cik: Company CIK identifier
        year: Fiscal year
        filing_type: SEC filing type (default: DEF 14A)

    Returns:
        Compensation data dictionary or None if not found

    Raises:
        EdgarAPIError: If API call fails
        ValidationError: If data validation fails
    """
    pass
```

### Docstring Standards

**Use Google-style docstrings**:

```python
def process_xbrl_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process XBRL data to extract executive compensation.

    Extracts compensation information from XBRL concepts using
    concept-based matching and role identification.

    Args:
        data: Raw XBRL data dictionary

    Returns:
        List of executive compensation records

    Raises:
        ValueError: If data format is invalid

    Example:
        >>> data = load_xbrl_data("0000320193")
        >>> executives = process_xbrl_data(data)
        >>> print(len(executives))
        5
    """
    pass
```

### Error Handling

```python
# Use specific exceptions
from edgar_analyzer.exceptions import (
    EdgarAPIError,
    ValidationError,
    DataNotFoundError
)

# Pattern: Try-except with logging
import logging
logger = logging.getLogger(__name__)

def fetch_data(cik: str) -> Optional[Dict[str, Any]]:
    try:
        response = api_service.get_company_facts(cik)
        return response.json()
    except EdgarAPIError as e:
        logger.error(f"Failed to fetch data for {cik}: {e}")
        return None
    except ValidationError as e:
        logger.warning(f"Validation failed for {cik}: {e}")
        return None
```

### Dependency Injection

```python
# Use dependency injector
from dependency_injector.wiring import inject, Provide
from edgar_analyzer.config.container import Container

@inject
def process_company(
    cik: str,
    edgar_service: EdgarAPIService = Provide[Container.edgar_api_service],
    xbrl_service: BreakthroughXBRLService = Provide[Container.xbrl_service]
) -> Dict[str, Any]:
    """Process company using injected services."""
    facts = edgar_service.get_company_facts(cik)
    compensation = xbrl_service.extract_compensation(facts)
    return compensation
```

### Logging

```python
import logging
import structlog

# Use structured logging
logger = structlog.get_logger(__name__)

def process_filing(cik: str, year: int) -> None:
    logger.info("processing_filing", cik=cik, year=year)

    try:
        result = extract_data(cik, year)
        logger.info("filing_processed", cik=cik, year=year,
                   executives_found=len(result))
    except Exception as e:
        logger.error("filing_processing_failed", cik=cik, year=year,
                    error=str(e))
        raise
```

---

## Testing Strategy

### Test Organization

```
tests/
├── unit/                        # Unit tests (fast, isolated)
│   ├── test_services.py
│   ├── test_models.py
│   └── test_validators.py
│
├── integration/                 # Integration tests (slower, external deps)
│   ├── test_edgar_api.py
│   ├── test_xbrl_extraction.py
│   └── test_report_generation.py
│
└── results/                     # Test outputs
```

### Testing Commands

```bash
# Run all tests
make test

# Run specific test suites
make test-unit
make test-integration

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/unit/test_services.py

# Run specific test function
pytest tests/unit/test_services.py::test_xbrl_extraction -v
```

### Unit Test Pattern

```python
import pytest
from edgar_analyzer.services import BreakthroughXBRLService

class TestBreakthroughXBRLService:
    """Test XBRL extraction service."""

    @pytest.fixture
    def xbrl_service(self):
        """Create XBRL service instance."""
        return BreakthroughXBRLService()

    @pytest.fixture
    def sample_xbrl_data(self):
        """Load sample XBRL data."""
        return {
            "facts": {
                "us-gaap": {
                    "ExecutiveCompensation": [
                        {"value": 1000000, "fy": 2023}
                    ]
                }
            }
        }

    def test_extract_compensation_success(self, xbrl_service, sample_xbrl_data):
        """Test successful compensation extraction."""
        result = xbrl_service.extract_compensation(sample_xbrl_data)

        assert result is not None
        assert "executives" in result
        assert len(result["executives"]) > 0

    def test_extract_compensation_missing_data(self, xbrl_service):
        """Test extraction with missing data."""
        result = xbrl_service.extract_compensation({})

        assert result is not None
        assert result["executives"] == []
```

### Integration Test Pattern

```python
import pytest
from edgar_analyzer.services import EdgarAPIService

class TestEdgarAPIIntegration:
    """Integration tests for EDGAR API."""

    @pytest.fixture
    def edgar_service(self):
        """Create EDGAR API service."""
        return EdgarAPIService()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_fetch_company_facts(self, edgar_service):
        """Test fetching company facts from EDGAR API."""
        # Use Apple Inc. as test case
        cik = "0000320193"

        result = edgar_service.get_company_facts(cik)

        assert result is not None
        assert "cik" in result
        assert "entityName" in result
        assert result["cik"] == "320193"  # CIK without leading zeros
```

### Test Fixtures

```python
# conftest.py - Shared fixtures
import pytest
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_companies():
    """Return list of sample companies for testing."""
    return [
        {"cik": "0000320193", "name": "Apple Inc."},
        {"cik": "0000789019", "name": "Microsoft Corporation"}
    ]

@pytest.fixture
def mock_edgar_api(mocker):
    """Mock EDGAR API service."""
    return mocker.patch("edgar_analyzer.services.EdgarAPIService")
```

### Coverage Requirements

- **Minimum**: 80% overall coverage
- **Target**: 90%+ for core services
- **Critical**: 100% for data validation

```bash
# Generate coverage report
make test-coverage

# View HTML report
open htmlcov/index.html
```

---

## Debugging Guide

### Enable Debug Logging

```bash
# Set log level in environment
export LOG_LEVEL=DEBUG

# Or in .env.local
LOG_LEVEL=DEBUG
```

### Debug Specific Components

```python
# In code - set specific logger level
import logging
logging.getLogger("edgar_analyzer.services.xbrl").setLevel(logging.DEBUG)
```

### Debugging Tools

#### 1. Python Debugger (pdb)

```python
# Insert breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

#### 2. IPython Debugging

```bash
# Install ipython
pip install ipython

# Use ipdb for better debugging
pip install ipdb
```

```python
# In code
import ipdb; ipdb.set_trace()
```

#### 3. VSCode Debugging

`.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Python: EDGAR Analyzer",
            "type": "python",
            "request": "launch",
            "module": "edgar_analyzer",
            "console": "integratedTerminal"
        }
    ]
}
```

### Common Debugging Scenarios

#### XBRL Extraction Issues

```bash
# Run debug script
python tests/debug_xbrl_concepts.py

# Check specific company
python tests/debug_xbrl_concepts.py --cik 0000320193
```

#### API Rate Limiting

```bash
# Check rate limit status
python tests/debug_proxy_content.py

# Add delay between requests
export EDGAR_RATE_LIMIT_DELAY=0.5
```

#### Data Validation Failures

```bash
# Run comprehensive QA
python tests/run_comprehensive_qa.py

# Check specific company validation
python tests/verify_fixed_sources.py
```

---

## Contributing Workflow

### Development Process

1. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make Changes**
```bash
# Edit code
vim src/edgar_analyzer/services/new_service.py

# Run tests continuously
pytest tests/ --watch
```

3. **Quality Checks**
```bash
# Format code
make format

# Run all quality checks
make quality
```

4. **Commit Changes**
```bash
git add .
git commit -m "feat: Add new XBRL extraction feature"
```

5. **Push and Create PR**
```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(xbrl): Add multi-year compensation extraction

Implement support for extracting compensation data across
multiple fiscal years in a single API call.

Closes #123
```

### Code Review Checklist

- [ ] Code follows style guide (black, isort, flake8)
- [ ] Type hints added for all functions
- [ ] Docstrings added/updated
- [ ] Unit tests added/updated
- [ ] Integration tests added if needed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] All tests passing
- [ ] Coverage maintained/improved

### Pre-commit Hooks

The project uses pre-commit hooks to enforce quality:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
```

---

## Performance Optimization

### Caching Strategy

```python
from edgar_analyzer.services import CacheService

# Use cache for expensive API calls
@cache_service.cached(ttl=3600)
def fetch_company_facts(cik: str) -> Dict[str, Any]:
    return edgar_api.get_company_facts(cik)
```

### Batch Processing

```python
from edgar_analyzer.services import ParallelProcessingService

# Process multiple companies in parallel
companies = ["0000320193", "0000789019", "0000018230"]
results = parallel_service.process_batch(companies, max_workers=5)
```

### Rate Limiting

```python
import time
from functools import wraps

def rate_limit(calls_per_second: float = 10.0):
    """Decorator to rate limit function calls."""
    min_interval = 1.0 / calls_per_second

    def decorator(func):
        last_called = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result

        return wrapper
    return decorator
```

---

## Additional Resources

### Documentation
- [Architecture Overview](docs/architecture/PROJECT_STRUCTURE.md)
- [API Reference](docs/api/)
- [User Guide](docs/guides/QUICK_START.md)

### External Resources
- [SEC EDGAR API Documentation](https://www.sec.gov/edgar/sec-api-documentation)
- [XBRL Standards](https://www.xbrl.org/)
- [Python Dependency Injector](https://python-dependency-injector.ets-labs.org/)

### Getting Help
- Check [Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md)
- Review [FAQ](docs/guides/FAQ.md)
- Open an issue on GitHub

---

**Happy Coding!** Build amazing features and maintain high code quality. 🚀
