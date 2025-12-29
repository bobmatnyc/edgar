# EDGAR Analyzer - Coding Standards

**Purpose**: Define coding standards, patterns, and best practices for EDGAR Analyzer
**Scope**: Python code quality, style, testing, and documentation requirements

---

## Code Quality Standards

### Automated Code Quality

```bash
# ONE command to check code quality
make quality

# Individual quality checks
make lint          # Linting with flake8
make format        # Auto-format with black + isort
make typecheck     # Type checking with mypy
make test          # Run test suite
```

### Quality Tools

- **black**: Code formatting (line length: 88)
- **isort**: Import sorting
- **flake8**: Linting and style checking
- **mypy**: Static type checking
- **pytest**: Testing framework
- **pre-commit**: Automated quality gates

---

## Python Style Guide

### PEP 8 Compliance

**Follow PEP 8** with these modifications:
- Line length: 88 characters (black default)
- Quotes: Double quotes for strings
- Trailing commas: Required in multi-line structures

### Code Formatting

```python
# GOOD: Properly formatted
def extract_compensation(
    cik: str,
    year: int,
    filing_type: str = "DEF 14A",
) -> Optional[Dict[str, Any]]:
    """Extract executive compensation from SEC filings."""
    pass

# BAD: Poor formatting
def extract_compensation(cik,year,filing_type="DEF 14A"):
    pass
```

### Import Organization

```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Third-party imports
import pandas as pd
import requests
from pydantic import BaseModel

# Local application imports
from edgar_analyzer.models import Company
from edgar_analyzer.services import EdgarAPIService
```

### Naming Conventions

```python
# Classes: PascalCase
class BreakthroughXBRLService:
    pass

# Functions and methods: snake_case
def extract_compensation_data():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_BASE_URL = "https://data.sec.gov"

# Private methods: leading underscore
def _internal_helper():
    pass

# Protected attributes: leading underscore
self._cache = {}
```

---

## Type Hints

### Required for All Functions

```python
from typing import Optional, List, Dict, Any, Union

# Function type hints
def process_filing(
    cik: str,
    year: int,
    filing_type: str = "DEF 14A",
) -> Optional[Dict[str, Any]]:
    """Process SEC filing."""
    pass

# Class attributes
class CompanyData:
    cik: str
    name: str
    executives: List[Dict[str, Any]]

# Optional types
def get_cached_data(cik: str) -> Optional[Dict[str, Any]]:
    """Return cached data or None."""
    pass
```

### Type Aliases

```python
from typing import TypeAlias

# Define common type aliases
CIK: TypeAlias = str
FiscalYear: TypeAlias = int
CompensationData: TypeAlias = Dict[str, Any]
ExecutiveList: TypeAlias = List[Dict[str, Any]]

# Use in function signatures
def extract_data(cik: CIK, year: FiscalYear) -> CompensationData:
    pass
```

### Generic Types

```python
from typing import Generic, TypeVar

T = TypeVar("T")

class DataCache(Generic[T]):
    """Generic cache for any data type."""

    def get(self, key: str) -> Optional[T]:
        pass

    def set(self, key: str, value: T) -> None:
        pass
```

---

## Docstring Standards

### Google-Style Docstrings

```python
def extract_compensation(
    cik: str,
    year: int,
    filing_type: str = "DEF 14A",
) -> Optional[Dict[str, Any]]:
    """Extract executive compensation from SEC filings.

    Retrieves and processes executive compensation data from SEC EDGAR
    filings using XBRL concepts and proxy statement parsing.

    Args:
        cik: Company CIK identifier (e.g., "0000320193")
        year: Fiscal year for data extraction
        filing_type: SEC filing type to search (default: "DEF 14A")

    Returns:
        Dictionary containing executive compensation data with keys:
        - executives: List of executive compensation records
        - metadata: Filing metadata and source information
        - data_quality: Quality score and validation results

        Returns None if data extraction fails.

    Raises:
        EdgarAPIError: If API request fails
        ValidationError: If extracted data fails validation
        ValueError: If CIK or year format is invalid

    Example:
        >>> service = BreakthroughXBRLService()
        >>> result = service.extract_compensation("0000320193", 2023)
        >>> print(result["executives"])
        [{"name": "Tim Cook", "total_compensation": 98734394, ...}]

    Note:
        This method uses the breakthrough XBRL extraction technique
        which achieves 2x better success rate than HTML parsing.
    """
    pass
```

### Module Docstrings

```python
"""XBRL Executive Compensation Extraction Service.

This module provides the breakthrough XBRL extraction service that
achieves 2x better success rates compared to traditional HTML parsing
methods.

Key Features:
    - Concept-based XBRL data extraction
    - Multi-year compensation analysis
    - Role-based executive matching
    - Comprehensive data validation

Classes:
    BreakthroughXBRLService: Main XBRL extraction service

Example:
    >>> from edgar_analyzer.services import BreakthroughXBRLService
    >>> service = BreakthroughXBRLService()
    >>> result = service.extract_compensation("0000320193", 2023)
"""
```

### Class Docstrings

```python
class BreakthroughXBRLService:
    """XBRL-based executive compensation extraction service.

    Extracts executive compensation data from SEC EDGAR XBRL filings
    using concept-based matching and role identification.

    This service achieves 2x better success rates compared to HTML
    parsing by leveraging structured XBRL data directly.

    Attributes:
        edgar_api: EDGAR API service for data retrieval
        cache: Cache service for API response caching
        validator: Data validator for quality checks

    Example:
        >>> service = BreakthroughXBRLService()
        >>> result = service.extract_compensation("0000320193", 2023)
        >>> print(len(result["executives"]))
        5
    """
```

---

## Error Handling

### Exception Hierarchy

```python
# Base exception
class EdgarAnalyzerError(Exception):
    """Base exception for EDGAR Analyzer."""
    pass

# Specific exceptions
class EdgarAPIError(EdgarAnalyzerError):
    """EDGAR API request failed."""
    pass

class ValidationError(EdgarAnalyzerError):
    """Data validation failed."""
    pass

class DataNotFoundError(EdgarAnalyzerError):
    """Required data not found."""
    pass
```

### Error Handling Pattern

```python
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def fetch_company_data(cik: str) -> Optional[Dict[str, Any]]:
    """Fetch company data with proper error handling."""
    try:
        # Attempt data retrieval
        response = edgar_api.get_company_facts(cik)
        data = response.json()

        # Validate data
        if not is_valid_data(data):
            raise ValidationError(f"Invalid data for CIK {cik}")

        return data

    except EdgarAPIError as e:
        # Log API errors and return None
        logger.error(f"API error for CIK {cik}: {e}")
        return None

    except ValidationError as e:
        # Log validation errors and return None
        logger.warning(f"Validation failed for CIK {cik}: {e}")
        return None

    except Exception as e:
        # Log unexpected errors and re-raise
        logger.exception(f"Unexpected error for CIK {cik}")
        raise EdgarAnalyzerError(f"Failed to fetch data for {cik}") from e
```

### Context Managers

```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def api_rate_limiter(delay: float = 0.1) -> Iterator[None]:
    """Context manager for API rate limiting."""
    import time

    yield

    time.sleep(delay)

# Usage
with api_rate_limiter(delay=0.5):
    data = edgar_api.get_company_facts(cik)
```

---

## Logging Standards

### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

def process_company(cik: str, year: int) -> Dict[str, Any]:
    """Process company with structured logging."""
    logger.info("processing_company", cik=cik, year=year)

    try:
        result = extract_data(cik, year)

        logger.info(
            "company_processed",
            cik=cik,
            year=year,
            executives_found=len(result.get("executives", [])),
            data_quality=result.get("quality_score"),
        )

        return result

    except Exception as e:
        logger.error(
            "company_processing_failed",
            cik=cik,
            year=year,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
```

### Log Levels

```python
# DEBUG: Detailed diagnostic information
logger.debug("cache_hit", cik=cik, cache_key=cache_key)

# INFO: General informational messages
logger.info("extraction_started", cik=cik, year=year)

# WARNING: Warning messages for recoverable issues
logger.warning("data_incomplete", cik=cik, missing_fields=["salary"])

# ERROR: Error messages for failures
logger.error("api_request_failed", cik=cik, status_code=500)

# CRITICAL: Critical errors requiring immediate attention
logger.critical("service_unavailable", service="edgar_api")
```

---

## Testing Standards

### Test Organization

```python
# tests/unit/test_xbrl_service.py
import pytest
from edgar_analyzer.services import BreakthroughXBRLService

class TestBreakthroughXBRLService:
    """Unit tests for XBRL extraction service."""

    @pytest.fixture
    def xbrl_service(self):
        """Create XBRL service instance."""
        return BreakthroughXBRLService()

    @pytest.fixture
    def sample_xbrl_data(self):
        """Load sample XBRL data for testing."""
        return {
            "facts": {
                "us-gaap": {
                    "ExecutiveCompensation": [
                        {
                            "value": 1000000,
                            "fy": 2023,
                            "label": "CEO Total Compensation",
                        }
                    ]
                }
            }
        }

    def test_extract_compensation_success(
        self, xbrl_service, sample_xbrl_data
    ):
        """Test successful compensation extraction."""
        result = xbrl_service.extract_compensation(sample_xbrl_data)

        assert result is not None
        assert "executives" in result
        assert len(result["executives"]) > 0
        assert result["data_quality"]["success"] is True

    def test_extract_compensation_missing_data(self, xbrl_service):
        """Test extraction with missing XBRL data."""
        result = xbrl_service.extract_compensation({})

        assert result is not None
        assert result["executives"] == []
        assert result["data_quality"]["success"] is False
```

### Test Naming Convention

```python
# Pattern: test_<function>_<scenario>

def test_extract_compensation_success():
    """Test successful case."""
    pass

def test_extract_compensation_missing_data():
    """Test error case."""
    pass

def test_extract_compensation_invalid_format():
    """Test validation case."""
    pass

def test_extract_compensation_with_cache():
    """Test caching behavior."""
    pass
```

### Test Coverage Requirements

```python
# Aim for high coverage on critical code
# tests/conftest.py
def pytest_configure(config):
    """Configure pytest with coverage requirements."""
    config.option.cov_fail_under = 80  # Minimum 80% coverage
```

---

## Dependency Injection

### Container Configuration

```python
# config/container.py
from dependency_injector import containers, providers
from edgar_analyzer.services import (
    EdgarAPIService,
    BreakthroughXBRLService,
    CacheService,
)

class Container(containers.DeclarativeContainer):
    """Dependency injection container."""

    config = providers.Configuration()

    # Services
    cache_service = providers.Singleton(CacheService)

    edgar_api_service = providers.Singleton(
        EdgarAPIService,
        cache=cache_service,
    )

    xbrl_service = providers.Factory(
        BreakthroughXBRLService,
        edgar_api=edgar_api_service,
        cache=cache_service,
    )
```

### Service Injection

```python
from dependency_injector.wiring import inject, Provide
from edgar_analyzer.config.container import Container

@inject
def process_company(
    cik: str,
    edgar_service: EdgarAPIService = Provide[Container.edgar_api_service],
    xbrl_service: BreakthroughXBRLService = Provide[Container.xbrl_service],
) -> Dict[str, Any]:
    """Process company with dependency injection."""
    facts = edgar_service.get_company_facts(cik)
    compensation = xbrl_service.extract_compensation(facts)
    return compensation
```

---

## Code Patterns

### Factory Pattern

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class DataExtractor(ABC):
    """Abstract base class for data extractors."""

    @abstractmethod
    def extract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from source."""
        pass

class XBRLExtractor(DataExtractor):
    """XBRL data extractor."""

    def extract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract from XBRL data."""
        return self._extract_xbrl_concepts(data)

class HTMLExtractor(DataExtractor):
    """HTML data extractor."""

    def extract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract from HTML data."""
        return self._parse_html_tables(data)

class ExtractorFactory:
    """Factory for creating extractors."""

    @staticmethod
    def create(extractor_type: str) -> DataExtractor:
        """Create extractor by type."""
        if extractor_type == "xbrl":
            return XBRLExtractor()
        elif extractor_type == "html":
            return HTMLExtractor()
        else:
            raise ValueError(f"Unknown extractor type: {extractor_type}")
```

### Strategy Pattern

```python
from typing import Protocol, Dict, Any

class ExtractionStrategy(Protocol):
    """Protocol for extraction strategies."""

    def extract(self, filing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract compensation data."""
        ...

class XBRLStrategy:
    """XBRL extraction strategy."""

    def extract(self, filing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract using XBRL concepts."""
        pass

class ProxyStrategy:
    """Proxy statement extraction strategy."""

    def extract(self, filing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract from proxy tables."""
        pass

class CompensationExtractor:
    """Extractor using configurable strategy."""

    def __init__(self, strategy: ExtractionStrategy):
        self.strategy = strategy

    def extract(self, filing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract using current strategy."""
        return self.strategy.extract(filing_data)
```

---

## Performance Optimization

### Caching

```python
from functools import lru_cache
from typing import Dict, Any

# Method-level caching
@lru_cache(maxsize=128)
def parse_cik(cik: str) -> str:
    """Parse and normalize CIK."""
    return cik.lstrip("0")

# Service-level caching
class CacheService:
    """Cache service for API responses."""

    def __init__(self, ttl: int = 3600):
        self._cache: Dict[str, Any] = {}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set cache value."""
        self._cache[key] = value
```

### Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Any

def process_batch(
    items: List[Any],
    processor: Callable[[Any], Any],
    max_workers: int = 5,
) -> List[Any]:
    """Process items in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(processor, items))
    return results

# Usage
companies = ["0000320193", "0000789019", "0000018230"]
results = process_batch(
    companies,
    lambda cik: extract_compensation(cik, 2023),
    max_workers=3,
)
```

---

## Documentation Standards

### README Requirements

Every package should have a README:

```markdown
# Package Name

Brief description of package purpose.

## Features

- Feature 1
- Feature 2

## Usage

```python
from package import Module

result = Module.function()
```

## API Reference

See [API.md](API.md) for detailed API documentation.
```

### API Documentation

Document all public APIs:

```python
def extract_compensation(cik: str, year: int) -> Dict[str, Any]:
    """Extract executive compensation data.

    Public API for extracting compensation from SEC filings.

    Args:
        cik: Company CIK identifier
        year: Fiscal year

    Returns:
        Compensation data dictionary

    Raises:
        EdgarAPIError: If API call fails
        ValidationError: If data validation fails

    Example:
        >>> result = extract_compensation("0000320193", 2023)
        >>> print(result["executives"])
        [...]
    """
```

---

## Code Review Checklist

### Before Submitting

- [ ] Code formatted with black
- [ ] Imports sorted with isort
- [ ] No linting errors (flake8)
- [ ] Type hints for all functions
- [ ] Docstrings for all public APIs
- [ ] Unit tests added/updated
- [ ] Integration tests if needed
- [ ] Coverage maintained (>80%)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Pre-commit hooks pass

### Review Guidelines

**Code Quality**:
- Clear, readable code
- Appropriate abstractions
- No code duplication
- Proper error handling

**Testing**:
- Adequate test coverage
- Edge cases tested
- Integration points tested

**Documentation**:
- Clear docstrings
- Updated README
- API documentation current

---

## Quick Reference

```bash
# Format code
make format

# Check quality
make quality

# Run tests
make test

# Type check
make typecheck

# Full workflow
make workflow
```

---

**Maintain high code quality standards for sustainable, maintainable codebase!** ✅
