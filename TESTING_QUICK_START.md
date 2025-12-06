# Testing Quick Start - Week 1 Implementation

**Goal**: Achieve 70%+ coverage on top 10 priority modules
**Timeframe**: Days 3-4 (2 days)
**Total Tests**: 101 tests

---

## 📋 Day 3: Quick Wins (6 modules, 69 tests)

### Morning Session (4 hours)

**1. Pattern Filter Tests** (90 min, 12 tests)
```bash
# File: tests/unit/services/test_pattern_filter.py
pytest tests/unit/services/test_pattern_filter.py -v
```

**Key Tests**:
- Threshold validation (0.0, 1.0, invalid)
- Pattern splitting by confidence
- Warning generation (0 excluded, >3 excluded, field mappings)
- Preset thresholds
- Confidence summary formatting

**Fixtures Needed**:
- `sample_parsed_examples` with known confidence values

---

**2. Report Factory Tests** (90 min, 14 tests)
```bash
# File: tests/unit/reports/test_factory.py
pytest tests/unit/reports/test_factory.py -v
```

**Key Tests**:
- Format creation (excel, xlsx, pdf, docx, pptx)
- Case-insensitive format handling
- Unsupported format error
- Custom generator registration
- Format support checks

**No complex fixtures needed** (simple factory logic)

---

**3. Exception Tests** (30 min, 3 tests)
```bash
# File: tests/unit/services/test_codegen_exceptions.py
pytest tests/unit/services/test_codegen_exceptions.py -v
```

**Key Tests**:
- Exception class initialization
- Error message formatting
- Inheritance chain validation

**No fixtures needed** (exception classes)

---

### Afternoon Session (4 hours)

**4. Report Base Tests** (120 min, 18 tests)
```bash
# File: tests/unit/reports/test_base.py
pytest tests/unit/reports/test_base.py -v
```

**Key Tests**:
- Pydantic config validation (all 4 config types)
- Invalid field values (margins, font, theme color)
- Default values
- Path validation (extension, directory creation)
- Data validation (None, empty)

**Fixtures Needed**:
- `tmp_path` (pytest built-in)

---

**5. API Source Tests** (120 min, 15 tests)
```bash
# File: tests/unit/data_sources/test_api_source.py
pytest tests/unit/data_sources/test_api_source.py -v
```

**Key Tests**:
- Initialization (auth token, headers)
- HTTP GET success/failure (mock httpx)
- Query parameters
- HTTP errors (404, 500)
- Timeout handling
- Cache behavior

**Fixtures Needed**:
- `httpx_mock` (pytest-httpx)

**Mocking Pattern**:
```python
@pytest.mark.asyncio
async def test_fetch_success(httpx_mock):
    httpx_mock.add_response(json={"data": "test"})
    api = APIDataSource(base_url="https://api.test.com")
    result = await api.fetch("endpoint")
    assert result == {"data": "test"}
```

---

### Evening Session (1 hour)

**6. URL Source Tests** (60 min, 7 tests)
```bash
# File: tests/unit/data_sources/test_url_source.py
pytest tests/unit/data_sources/test_url_source.py -v
```

**Key Tests**:
- Initialization
- HTML content fetching
- Invalid URL handling
- HTTP timeout/errors
- Configuration validation

**Similar to API Source** (simpler, no auth)

---

## 📋 Day 4: File Sources (4 modules, 32 tests)

### Morning Session (3 hours)

**7. Jina Source Tests** (120 min, 12 tests)
```bash
# File: tests/unit/data_sources/test_jina_source.py
pytest tests/unit/data_sources/test_jina_source.py -v
```

**Key Tests**:
- Rate limit auto-config (free vs paid)
- Markdown response parsing
- JSON response parsing
- Title extraction from markdown
- Invalid URL handling
- Timeout/error handling

**Fixtures Needed**:
- Sample markdown content with heading
- Sample Jina JSON response

---

**8. Constraint Enforcer Tests** (60 min, 4 tests)
```bash
# File: tests/unit/services/test_constraint_enforcer.py
pytest tests/unit/services/test_constraint_enforcer.py -v
```

**Key Tests**:
- Valid constraint enforcement
- Invalid constraints
- Edge cases
- Error messages

---

### Afternoon Session (3 hours)

**9. Excel Source Tests** (90 min, 8 tests)
```bash
# File: tests/unit/data_sources/test_excel_source.py
pytest tests/unit/data_sources/test_excel_source.py -v
```

**Key Tests**:
- .xlsx and .xls file handling
- Sheet name selection
- Invalid file path
- Corrupted file handling
- Cache key generation

**Fixtures Needed**:
- `tests/fixtures/sample.xlsx` (small Excel file)
- Mock `pandas.read_excel`

**Sample Fixture**:
```python
@pytest.fixture
def sample_excel(tmp_path):
    excel_path = tmp_path / "sample.xlsx"
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    df.to_excel(excel_path, index=False)
    return excel_path
```

---

**10. PDF Source Tests** (90 min, 8 tests)
```bash
# File: tests/unit/data_sources/test_pdf_source.py
pytest tests/unit/data_sources/test_pdf_source.py -v
```

**Key Tests**:
- PDF file parsing
- Table extraction
- Page range specification
- Invalid/corrupted file handling
- Cache key generation

**Fixtures Needed**:
- `tests/fixtures/sample.pdf` (simple PDF with table)
- Mock `pdfplumber.open`

---

## 🛠️ Testing Tools & Setup

### Required Packages

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-httpx pytest-timeout
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/extract_transform_platform --cov-report=html --cov-report=term

# Run specific module
pytest tests/unit/services/test_pattern_filter.py -v

# Run with debug output
pytest -s -v

# Run only failed tests
pytest --lf
```

### Coverage Thresholds

```bash
# Fail if coverage < 70%
pytest --cov --cov-fail-under=70
```

---

## 📁 Test File Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── sample.xlsx               # Excel test data
│   ├── sample.pdf                # PDF test data
│   └── sample_patterns.json      # Pattern test data
├── unit/
│   ├── services/
│   │   ├── test_pattern_filter.py
│   │   ├── test_constraint_enforcer.py
│   │   └── test_codegen_exceptions.py
│   ├── reports/
│   │   ├── test_factory.py
│   │   └── test_base.py
│   └── data_sources/
│       ├── test_api_source.py
│       ├── test_url_source.py
│       ├── test_jina_source.py
│       ├── test_excel_source.py
│       └── test_pdf_source.py
```

---

## 🔧 Common Test Patterns

### Async Tests (httpx mocking)

```python
import pytest
from pytest_httpx import HTTPXMock

@pytest.mark.asyncio
async def test_api_fetch(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"key": "value"})
    
    api = APIDataSource(base_url="https://test.com")
    result = await api.fetch("endpoint")
    
    assert result["key"] == "value"
```

### Pydantic Validation Tests

```python
import pytest
from pydantic import ValidationError

def test_invalid_config():
    with pytest.raises(ValidationError) as exc_info:
        ReportConfig(title="Test", page_size="invalid")
    
    assert "page_size" in str(exc_info.value)
```

### Filesystem Tests

```python
def test_file_operation(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    result = my_function(test_file)
    
    assert result == "expected"
```

### Exception Tests

```python
def test_exception_raised():
    with pytest.raises(ValueError, match="must be in"):
        filter_service.filter_patterns(parsed, threshold=1.5)
```

---

## ✅ Success Checklist

### Day 3 End-of-Day
- [ ] 69 tests passing
- [ ] Coverage >70% for: pattern_filter, factory, base, api_source, url_source, exceptions
- [ ] All tests run in <10 seconds
- [ ] No test warnings

### Day 4 End-of-Day
- [ ] 32 additional tests passing (101 total)
- [ ] Coverage >70% for: jina_source, excel_source, pdf_source, constraint_enforcer
- [ ] Test fixtures documented
- [ ] CI/CD integration tested

### Day 5 Verification
- [ ] Full coverage report generated
- [ ] Platform coverage >60%
- [ ] All tests pass in <30 seconds
- [ ] Test documentation updated

---

## 🚨 Common Issues & Solutions

### Issue: `pytest-asyncio` warnings
```bash
# Add to pytest.ini or pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Issue: Import errors
```bash
# Ensure src is in PYTHONPATH
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Or use editable install
pip install -e .
```

### Issue: Mock not resetting between tests
```python
# Use pytest-mock's mocker fixture (auto-resets)
def test_with_mock(mocker):
    mock_func = mocker.patch('module.function')
    # Test code
```

### Issue: Slow tests
```bash
# Run with timeout
pytest --timeout=10

# Profile slow tests
pytest --durations=10
```

---

## 📚 References

- Full Analysis: `docs/research/platform-coverage-gaps-analysis-2025-12-03.md`
- Summary: `PLATFORM_COVERAGE_GAPS_SUMMARY.md`
- Pytest Docs: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- pytest-httpx: https://colin-b.github.io/pytest_httpx/

---

**Last Updated**: 2025-12-03
**Time Budget**: Day 3 (9h) + Day 4 (6h) = 15 hours
**Expected Outcome**: 70%+ coverage on top 10 modules
