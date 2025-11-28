# Constraint Enforcer - Quick Reference

**One-page guide for validating AI-generated code**

---

## Quick Start

```python
from edgar_analyzer.services.constraint_enforcer import ConstraintEnforcer

enforcer = ConstraintEnforcer()
result = enforcer.validate_code(your_code)

if not result.valid:
    for violation in result.violations:
        print(violation)
```

---

## Common Violations & Fixes

### ❌ MISSING_INTERFACE
```python
# Bad
class WeatherExtractor:
    pass

# Good
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    pass
```

### ❌ MISSING_DECORATOR
```python
# Bad
class WeatherExtractor(IDataExtractor):
    def __init__(self, client):
        self.client = client

# Good
from dependency_injector.wiring import inject

class WeatherExtractor(IDataExtractor):
    @inject
    def __init__(self, client):
        self.client = client
```

### ❌ MISSING_TYPE_HINT / MISSING_RETURN_TYPE
```python
# Bad
def extract(self, params):
    return {}

# Good
from typing import Dict, Any

def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
    return {}
```

### ❌ FORBIDDEN_IMPORT
```python
# Bad
import os
files = os.listdir("/tmp")

# Good
from pathlib import Path
files = [f.name for f in Path("/tmp").iterdir()]
```

### ❌ HIGH_COMPLEXITY
```python
# Bad - Complexity: 11
def process(x):
    if x > 0:
        if x > 10:
            if x > 20:
                # ... 8 more nested ifs

# Good - Complexity: 3
def process(x):
    if x <= 0:
        return 0
    return self._calculate_tier(x)
```

### ❌ PRINT_STATEMENT
```python
# Bad
def fetch(url):
    print(f"Fetching {url}")
    return requests.get(url)

# Good
from logging import getLogger
logger = getLogger(__name__)

def fetch(url):
    logger.info(f"Fetching {url}")
    return requests.get(url)
```

### ❌ DANGEROUS_FUNCTION
```python
# Bad
result = eval(user_input)

# Good
import json
result = json.loads(user_input)
```

### ❌ SQL_INJECTION_RISK
```python
# Bad
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# Good
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

### ❌ HARDCODED_CREDENTIAL
```python
# Bad
api_key = "sk_live_12345"

# Good
import os
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY not set")
```

---

## Constraint Rules

| Constraint | Limit | Configurable |
|------------|-------|--------------|
| Cyclomatic Complexity | 10 | Yes |
| Method Lines | 50 | Yes |
| Class Lines | 300 | Yes |
| Type Hints | Required | Yes |
| Docstrings | Required | Yes |
| Print Statements | Forbidden | Yes |

---

## Configuration

**Default config**: `src/edgar_analyzer/config/constraints.yaml`

```python
from edgar_analyzer.models.validation import ConstraintConfig

# Custom config
config = ConstraintConfig(
    max_complexity=15,           # More permissive
    allow_print_statements=True,  # For debugging
    enforce_type_hints=False,     # Legacy code
)

enforcer = ConstraintEnforcer(config=config)
```

---

## Violation Severity

| Level | Meaning | Action |
|-------|---------|--------|
| **ERROR** | Must fix | Blocks acceptance |
| **WARNING** | Should fix | Non-blocking |
| **INFO** | Best practice | Informational |

---

## Perfect Extractor Template

```python
"""
Module description.

Detailed extractor documentation.
"""

from logging import getLogger
from typing import Dict, Any, Optional
from dependency_injector.wiring import inject

from edgar_analyzer.interfaces.data_extractor import IDataExtractor


logger = getLogger(__name__)


class MyExtractor(IDataExtractor):
    """
    Extract data from source.

    Detailed class documentation.
    """

    @inject
    def __init__(self, client: HTTPClient, config: Dict[str, Any]):
        """
        Initialize extractor.

        Args:
            client: HTTP client for API requests
            config: Configuration dictionary
        """
        self.client = client
        self.config = config
        logger.info("MyExtractor initialized")

    def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data.

        Args:
            params: Extraction parameters

        Returns:
            Extracted data dictionary

        Raises:
            ValueError: If params invalid
            APIError: If API request fails
        """
        logger.info(f"Extracting data: {params}")

        try:
            data = self._fetch_data(params)
            logger.debug(f"Received data: {data}")
            return self._transform(data)
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            raise

    def _fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from API.

        Args:
            params: Request parameters

        Returns:
            Raw API response
        """
        # Implementation
        return {}

    def _transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw data.

        Args:
            data: Raw data

        Returns:
            Transformed data
        """
        # Implementation
        return data
```

---

## CLI Usage

**Run demo**:
```bash
python3 test_constraint_enforcer_demo.py
```

**Validate file**:
```python
enforcer = ConstraintEnforcer()
result = enforcer.validate_file("path/to/extractor.py")
```

**Validate multiple files**:
```python
from pathlib import Path

for file_path in Path("extractors").glob("*.py"):
    result = enforcer.validate_file(str(file_path))
    if not result.valid:
        print(f"❌ {file_path}: {result.errors_count} errors")
```

---

## Performance

- **Typical validation**: 0.88ms
- **Target**: <100ms
- **Actual speedup**: 113x faster than target ✅

---

## Testing

**Run all tests**:
```bash
pytest tests/unit/services/test_constraint_enforcer.py -v
pytest tests/integration/test_constraint_enforcement.py -v
```

**Run demo**:
```bash
python3 test_constraint_enforcer_demo.py
```

---

## Documentation

- **Full docs**: `docs/CONSTRAINT_ENFORCEMENT.md`
- **Validator guide**: `src/edgar_analyzer/validators/README.md`
- **Implementation**: `CONSTRAINT_ENFORCER_IMPLEMENTATION.md`

---

## Forbidden Imports

❌ **Never import these**:
- `os` - Use `pathlib.Path` instead
- `subprocess` - Security risk
- `eval` / `exec` / `compile` - Arbitrary code execution
- `__import__` - Dynamic imports

---

## Best Practices

✅ **Always**:
- Implement `IDataExtractor`
- Use `@inject` on `__init__`
- Add type hints to all methods
- Use structured logging (`logger.*`)
- Write docstrings
- Handle errors with try/except
- Log errors before raising

❌ **Never**:
- Import forbidden modules
- Use `print()` in production
- Hardcode credentials
- Use f-strings in SQL queries
- Write methods > 50 lines
- Nest > 10 conditionals

---

## Quick Checklist

Before submitting generated code:

- [ ] Implements `IDataExtractor`
- [ ] Has `@inject` on `__init__`
- [ ] All methods have type hints
- [ ] All methods have docstrings
- [ ] No forbidden imports
- [ ] No `print()` statements
- [ ] No hardcoded credentials
- [ ] Complexity < 10
- [ ] Methods < 50 lines
- [ ] Classes < 300 lines
- [ ] Uses structured logging
- [ ] Logs API calls
- [ ] Logs errors

---

**See full documentation**: `docs/CONSTRAINT_ENFORCEMENT.md`
