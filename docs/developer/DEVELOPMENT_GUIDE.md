# EDGAR Platform - Development Guide

**Last Updated**: 2025-12-03
**Version**: 2.0

Complete guide for development patterns, best practices, and troubleshooting.

---

## Table of Contents

- [Code Style Standards](#code-style-standards)
- [Testing Patterns](#testing-patterns)
- [Dependency Injection](#dependency-injection)
- [Error Handling](#error-handling)
- [Development Patterns](#development-patterns)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)
- [Key Learnings & Patterns](#key-learnings--patterns)
- [Memory Categories for Agent Learning](#memory-categories-for-agent-learning)

---

## Code Style Standards

```bash
# Format code (auto-fix)
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run all checks
make quality  # Runs black, isort, flake8, mypy
```

### Standards

- **Line Length**: 88 characters (black default)
- **Import Order**: stdlib → third-party → local (isort)
- **Type Hints**: Required for all functions
- **Docstrings**: Google-style for all public APIs
- **Naming**: snake_case for functions/variables, PascalCase for classes

### Example

```python
from typing import Dict, Optional, Any
from pathlib import Path
import pandas as pd

from extract_transform_platform.core import BaseDataSource


class ExcelDataSource(BaseDataSource):
    """Read and parse Excel spreadsheets (.xlsx, .xls).

    Args:
        file_path: Path to Excel file
        sheet_name: Sheet name or index (default: 0)
        header_row: Row number for headers (default: 0)

    Returns:
        Parsed data as list of dictionaries

    Example:
        >>> source = ExcelDataSource("data.xlsx", sheet_name="Sheet1")
        >>> data = source.read()
    """

    def __init__(
        self,
        file_path: Path,
        sheet_name: int | str = 0,
        header_row: int = 0
    ) -> None:
        self.file_path = Path(file_path)
        self.sheet_name = sheet_name
        self.header_row = header_row

    def read(self) -> list[Dict[str, Any]]:
        """Read Excel file and return parsed data."""
        df = pd.read_excel(
            self.file_path,
            sheet_name=self.sheet_name,
            header=self.header_row
        )
        return df.to_dict(orient="records")
```

---

## Testing Patterns

### Unit Test Pattern

```python
import pytest
from edgar_analyzer.services import BreakthroughXBRLService


def test_xbrl_extraction():
    """Test XBRL extraction for Apple Inc."""
    service = BreakthroughXBRLService()
    result = service.extract_compensation(cik="0000320193", year=2023)

    assert result is not None
    assert "executives" in result
    assert len(result["executives"]) > 0


def test_xbrl_extraction_missing_data():
    """Test graceful handling of missing XBRL data."""
    service = BreakthroughXBRLService()
    result = service.extract_compensation(cik="0000000000", year=2023)

    assert result is None or result["executives"] == []
```

### Integration Test Pattern

```python
import pytest
from pathlib import Path
from extract_transform_platform.data_sources.file import ExcelDataSource


@pytest.fixture
def sample_excel(tmp_path):
    """Create sample Excel file for testing."""
    import pandas as pd

    df = pd.DataFrame({
        "employee_id": ["E1001", "E1002"],
        "first_name": ["Alice", "Bob"],
        "last_name": ["Johnson", "Smith"]
    })

    file_path = tmp_path / "sample.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


def test_excel_data_source_integration(sample_excel):
    """Test ExcelDataSource with real Excel file."""
    source = ExcelDataSource(sample_excel, sheet_name=0)
    data = source.read()

    assert len(data) == 2
    assert data[0]["employee_id"] == "E1001"
    assert data[0]["first_name"] == "Alice"
```

### Test Organization

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_schema_analyzer.py
│   ├── test_example_parser.py
│   └── test_pattern_models.py
├── integration/             # Integration tests (external dependencies)
│   ├── test_batch1_datasources.py
│   ├── test_excel_integration.py
│   └── test_api_integration.py
└── e2e/                     # End-to-end tests (complete workflows)
    ├── test_weather_api_e2e.py
    └── test_employee_roster_e2e.py
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Specific test file
pytest tests/unit/test_schema_analyzer.py

# Specific test function
pytest tests/unit/test_schema_analyzer.py::test_infer_input_schema

# With coverage
pytest --cov=src tests/

# With verbose output
pytest -vv tests/
```

---

## Dependency Injection

The platform uses `dependency-injector` for service management.

### Container Setup

```python
from dependency_injector import containers, providers
from edgar_analyzer.services import (
    EdgarAPIService,
    BreakthroughXBRLService,
    CacheService
)


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""

    # Configuration
    config = providers.Configuration()

    # Services
    cache_service = providers.Singleton(
        CacheService,
        cache_dir=config.cache_dir
    )

    edgar_api_service = providers.Singleton(
        EdgarAPIService,
        cache_service=cache_service,
        user_agent=config.sec_edgar_user_agent
    )

    xbrl_service = providers.Factory(
        BreakthroughXBRLService,
        edgar_api=edgar_api_service
    )
```

### Using Dependency Injection

```python
from edgar_analyzer.config.container import Container


# Initialize container
container = Container()
container.config.cache_dir.from_env("CACHE_DIR", default="data/cache")
container.config.sec_edgar_user_agent.from_env("SEC_EDGAR_USER_AGENT")

# Wire modules
container.wire(modules=[__name__])

# Inject services
xbrl_service = container.xbrl_service()
result = xbrl_service.extract_compensation(cik="0000320193", year=2023)
```

### Injectable Services

```python
from dependency_injector.wiring import inject, Provide
from edgar_analyzer.config.container import Container
from edgar_analyzer.services import BreakthroughXBRLService


@inject
def analyze_company(
    cik: str,
    year: int,
    xbrl_service: BreakthroughXBRLService = Provide[Container.xbrl_service]
) -> dict:
    """Analyze company with injected XBRL service."""
    return xbrl_service.extract_compensation(cik=cik, year=year)
```

---

## Error Handling

### Standard Error Handling Pattern

```python
from edgar_analyzer.exceptions import EdgarAPIError, ValidationError
import logging

logger = logging.getLogger(__name__)


def extract_data(cik: str) -> dict | None:
    """Extract data with comprehensive error handling."""
    try:
        result = service.extract_data(cik)
        return result

    except EdgarAPIError as e:
        logger.error(f"API error for CIK {cik}: {e}")
        return None

    except ValidationError as e:
        logger.warning(f"Validation error for CIK {cik}: {e}")
        return default_value

    except Exception as e:
        logger.exception(f"Unexpected error for CIK {cik}: {e}")
        raise
```

### Custom Exceptions (T12 - 1M-454)

```python
from extract_transform_platform.exceptions import (
    ProjectNotFoundError,
    ProjectValidationError,
    DataSourceError,
    PatternDetectionError,
    CodeGenerationError
)


# ProjectNotFoundError - 400-800% clearer than generic errors
try:
    project = manager.get_project("nonexistent")
except ProjectNotFoundError as e:
    print(f"❌ {e}")
    print(f"💡 Tip: {e.suggestion}")
    # Output: ❌ Project 'nonexistent' not found
    # Output: 💡 Tip: Run 'edgar-analyzer project list' to see available projects


# ProjectValidationError - Actionable guidance
try:
    project = manager.validate_project("invalid")
except ProjectValidationError as e:
    print(f"❌ {e}")
    print(f"💡 Fix: {e.suggestion}")
    # Output: ❌ Project configuration invalid: missing required field 'name'
    # Output: 💡 Fix: Add 'name' field to project.yaml
```

---

## Development Patterns

### Protocol + ABC + Factory Pattern

**Used for**: BaseDataSource, IReportGenerator, IDataExtractor

```python
from typing import Protocol, runtime_checkable
from abc import ABC, abstractmethod


# 1. Protocol (duck typing interface)
@runtime_checkable
class IReportGenerator(Protocol):
    """Protocol for report generators."""

    def generate(self, data: Any, output_path: Path, config: ReportConfig) -> Path:
        ...


# 2. Abstract Base Class (common functionality)
class BaseReportGenerator(ABC):
    """Abstract base class with helpers."""

    @abstractmethod
    def generate(self, data: Any, output_path: Path, config: ReportConfig) -> Path:
        pass

    def _validate_output_path(self, output_path: Path, extension: str):
        """Common validation logic."""
        if not output_path.suffix == extension:
            raise ValueError(f"Output path must have {extension} extension")


# 3. Factory (centralized creation)
class ReportGeneratorFactory:
    """Factory for creating report generators."""

    _generators: Dict[str, Type[BaseReportGenerator]] = {
        "excel": ExcelReportGenerator,
        "pdf": PDFReportGenerator,
    }

    @classmethod
    def create(cls, format: str) -> IReportGenerator:
        """Create report generator for specified format."""
        return cls._generators[format.lower()]()
```

### Pydantic Configuration Models

```python
from pydantic import BaseModel, Field, field_validator


class ExcelReportConfig(BaseModel):
    """Excel-specific configuration."""

    title: str = Field(..., description="Report title")
    author: str = Field(default="EDGAR Platform", description="Report author")
    sheet_name: str = Field(default="Report", min_length=1, max_length=31)
    freeze_header: bool = Field(default=True)
    auto_filter: bool = Field(default=True)

    @field_validator("sheet_name")
    @classmethod
    def validate_sheet_name(cls, v: str) -> str:
        """Validate Excel sheet name constraints."""
        invalid_chars = ['\\', '/', '*', '?', ':', '[', ']']
        if any(c in v for c in invalid_chars):
            raise ValueError(f"Sheet name contains invalid characters: {invalid_chars}")
        return v
```

### Async/Await Patterns

```python
import asyncio
from typing import List
from extract_transform_platform.services.project_manager import ProjectManager


async def batch_create_projects(project_names: List[str]) -> List[dict]:
    """Create multiple projects concurrently."""
    manager = ProjectManager()

    tasks = [
        manager.create_project(name, template="weather")
        for name in project_names
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
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

#### Platform Import Errors

```bash
# Problem: Cannot import from extract_transform_platform
# Solution: Use platform imports
# ❌ from edgar_analyzer.data_sources.base import BaseDataSource
# ✅ from extract_transform_platform.core import BaseDataSource
```

#### Large Dataset Performance

```bash
# Problem: Slow processing for large datasets
# Solution: Use external artifacts directory
export EDGAR_ARTIFACTS_DIR=~/edgar_projects
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

### Excel File Transform

- **Pattern**: Example-driven transformation (same as Weather API)
- **Schema Detection**: Automatic pattern recognition from 2-3 examples
- **Type Safety**: Pydantic models + pandas type inference
- **Code Reuse**: 70% from FileDataSource (CSV pattern)
- **Files**: `src/extract_transform_platform/data_sources/file/excel_source.py`
- **POC**: `projects/employee_roster/` (35/35 validations passing)

**Transformations Supported**:
- Field renaming (employee_id → id)
- String concatenation (first_name + last_name → full_name)
- Type conversions (int → float, string → date)
- Boolean normalization ("Yes"/"No" → true/false)
- Value mapping (discrete value transformations)
- Field extraction (substring patterns)

### PDF File Transform

- **Pattern**: Table extraction strategies (lines/text/mixed)
- **Bounding Box Support**: Target specific page regions
- **Currency Parsing**: Automatic $ removal and float conversion
- **Files**: `src/extract_transform_platform/data_sources/file/pdf_source.py`
- **POC**: `projects/invoice_transform/` (working proof-of-concept)

### Report Generation

- **Pattern**: Protocol + ABC + Factory (same as BaseDataSource)
- **Code Reuse**: 95% code reduction (200+ lines → 5 lines for legacy migration)
- **Performance**: 13-312x faster than requirements
- **Multiple Formats**: Excel, PDF, DOCX, PPTX with unified interface
- **Files**: `src/extract_transform_platform/reports/`

---

## Memory Categories for Agent Learning

**EDGAR Extraction Patterns**: XBRL extraction techniques, concept mapping, success rates

**Data Source Integration**: Multi-source patterns, validation methods, tracking

**Excel File Transform**: Example-driven approach, schema detection, transformation patterns, pandas usage

**PDF File Transform**: Table extraction strategies (lines/text/mixed), bounding boxes, pdfplumber usage, currency parsing

**Report Generation**: Multi-format output, unified interface, Protocol + ABC + Factory pattern

**Code Quality**: Testing patterns, type checking, formatting standards, dependency injection

**Performance**: Caching strategies, batch processing, rate limiting, external artifacts

**Common Issues**: Known bugs, workarounds, debugging techniques, import errors

**Platform Migration**: EDGAR → platform import paths, backward compatibility patterns

---

## Best Practices

### File Transform Workflows

1. **Start with examples** - Provide 2-3 input/output transformation examples
2. **Let AI detect patterns** - SchemaAnalyzer + ExampleParser handle schema inference
3. **Select confidence threshold** - Use interactive prompt or --confidence-threshold flag
4. **Generate code** - Sonnet 4.5 creates type-safe extractors
5. **Validate output** - Auto-generated pytest tests verify correctness

### Code Quality

1. **Run tests before committing** - Use `make test`
2. **Format code automatically** - Use `black` and `isort`
3. **Type hints required** - Use mypy for type checking
4. **Document complex logic** - Clear docstrings and comments
5. **Follow platform patterns** - Protocol + ABC + Factory, Pydantic models

### Platform Development

1. **Use platform imports** - Prefer `extract_transform_platform.*` over `edgar_analyzer.*`
2. **Follow Protocol + ABC + Factory pattern** - BaseDataSource precedent
3. **Pydantic models for config** - Type-safe configuration
4. **Comprehensive testing** - 80%+ coverage target
5. **Custom exceptions** - Actionable error messages (T12 pattern)

### Performance Optimization

1. **Use caching** - Cache API responses in `data/cache/`
2. **Batch operations** - Process multiple records in parallel
3. **External artifacts** - Use `EDGAR_ARTIFACTS_DIR` for large datasets
4. **Monitor rate limits** - Respect API rate limits (SEC EDGAR, OpenRouter)
5. **Async/await** - Use for I/O-bound operations

### EDGAR Data Extraction

1. **Always use XBRL service first** - Breakthrough service has 2x success rate
2. **Check cache before API calls** - Respect SEC rate limits
3. **Validate data sources** - Track where data comes from
4. **Handle missing data gracefully** - Not all companies have complete data

### File Organization

1. **Keep tests with code** - Tests in `tests/` mirror `src/`
2. **Results in dedicated directory** - Use `tests/results/` for outputs
3. **Documentation in docs/** - Organized by category (guides, api, architecture)
4. **Cache in data/cache/** - Temporary API data
5. **External artifacts** - Use `EDGAR_ARTIFACTS_DIR` for production data

---

## Next Steps

1. **Read Platform Overview**: [PLATFORM_OVERVIEW.md](PLATFORM_OVERVIEW.md) - Complete platform guide
2. **Browse Feature Index**: [FEATURE_INDEX.md](FEATURE_INDEX.md) - All features with examples
3. **Review API Docs**: [../api/PLATFORM_API.md](../api/PLATFORM_API.md) - Detailed API reference
4. **Check Code Governance**: [CODE_GOVERNANCE.md](CODE_GOVERNANCE.md) - Development standards

---

**Last Updated**: 2025-12-03
**Contact**: See [PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md) for full project context.
