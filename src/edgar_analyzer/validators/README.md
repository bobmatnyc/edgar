# Constraint Validators

This directory contains individual validators for the Constraint Enforcer system.

## Overview

Each validator checks a specific aspect of code quality, security, or architecture:

| Validator | Purpose | Violation Codes |
|-----------|---------|-----------------|
| **InterfaceValidator** | Ensures classes implement IDataExtractor | `MISSING_INTERFACE` |
| **DependencyInjectionValidator** | Checks for @inject decorator | `MISSING_DECORATOR` |
| **TypeHintValidator** | Validates type annotations | `MISSING_TYPE_HINT`, `MISSING_RETURN_TYPE` |
| **ImportValidator** | Blocks forbidden imports | `FORBIDDEN_IMPORT` |
| **ComplexityValidator** | Measures cyclomatic complexity | `HIGH_COMPLEXITY`, `METHOD_TOO_LONG`, `CLASS_TOO_LONG` |
| **SecurityValidator** | Detects security anti-patterns | `DANGEROUS_FUNCTION`, `SQL_INJECTION_RISK`, `HARDCODED_CREDENTIAL` |
| **LoggingValidator** | Enforces structured logging | `PRINT_STATEMENT`, `MISSING_API_LOGGING`, `MISSING_ERROR_LOGGING` |

## Validator Architecture

All validators follow the same pattern:

```python
class ValidatorName:
    """Validator description."""

    def __init__(self, config: ConstraintConfig):
        """Initialize with configuration."""
        self.config = config

    def validate(self, tree: ast.AST) -> List[Violation]:
        """
        Validate code against constraints.

        Args:
            tree: AST of code to validate

        Returns:
            List of violations (empty if valid)
        """
        violations = []
        # Validation logic here
        return violations
```

## Adding a New Validator

1. Create new file: `new_validator.py`
2. Implement validator class following pattern above
3. Add to `__init__.py` exports
4. Update `ConstraintEnforcer` to include new validator
5. Add tests in `tests/unit/validators/`
6. Update documentation

Example:
```python
# new_validator.py
from typing import List
import ast
from edgar_analyzer.models.validation import Violation, Severity, ConstraintConfig


class NewValidator:
    """Validates some new constraint."""

    def __init__(self, config: ConstraintConfig):
        self.config = config

    def validate(self, tree: ast.AST) -> List[Violation]:
        violations = []
        # Your validation logic
        return violations
```

## Performance Considerations

- Each validator performs O(n) walk over AST
- Average validation time: ~0.5ms per validator
- Total for 7 validators: ~5ms on typical code
- Target: <100ms for complete validation

## Testing

Run validator tests:
```bash
pytest tests/unit/validators/ -v
```

Test individual validator:
```bash
pytest tests/unit/validators/test_interface_validator.py -v
```

## Configuration

Validators use `ConstraintConfig` for configuration:

```python
from edgar_analyzer.models.validation import ConstraintConfig

config = ConstraintConfig(
    max_complexity=10,
    forbidden_imports={"os", "subprocess"},
    enforce_type_hints=True,
)
```

See `src/edgar_analyzer/config/constraints.yaml` for full configuration options.

## Validator Details

### InterfaceValidator

**Purpose**: Ensure extractor classes implement `IDataExtractor` interface

**Checks**:
- Classes ending in "Extractor" must inherit from `IDataExtractor`

**Example Violation**:
```python
class WeatherExtractor:  # ❌ Missing IDataExtractor
    pass
```

**Fix**:
```python
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):  # ✅ Implements interface
    pass
```

### DependencyInjectionValidator

**Purpose**: Enforce dependency injection pattern

**Checks**:
- `__init__` methods must have `@inject` decorator

**Example Violation**:
```python
class WeatherExtractor(IDataExtractor):
    def __init__(self, client):  # ❌ Missing @inject
        self.client = client
```

**Fix**:
```python
from dependency_injector.wiring import inject

class WeatherExtractor(IDataExtractor):
    @inject  # ✅ Has @inject decorator
    def __init__(self, client):
        self.client = client
```

### TypeHintValidator

**Purpose**: Require type annotations for maintainability

**Checks**:
- All method parameters have type hints
- All methods have return type annotations

**Example Violation**:
```python
def extract(self, params):  # ❌ No type hints
    return {}
```

**Fix**:
```python
from typing import Dict, Any

def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:  # ✅ Type hints
    return {}
```

### ImportValidator

**Purpose**: Prevent security vulnerabilities

**Checks**:
- No imports of forbidden modules (os, subprocess, eval, exec, etc.)

**Example Violation**:
```python
import os  # ❌ Forbidden import
```

**Fix**:
```python
from pathlib import Path  # ✅ Use safer alternative
```

### ComplexityValidator

**Purpose**: Maintain code simplicity and readability

**Checks**:
- Cyclomatic complexity < 10 per method
- Method length < 50 lines
- Class length < 300 lines

**Example Violation**:
```python
def complex_method(x):
    if x > 0:
        if x > 10:
            if x > 20:
                # ... many nested conditions
                # ❌ Complexity > 10
```

**Fix**:
```python
def simple_method(x):
    if x <= 0:
        return 0

    # ✅ Extract logic to helpers
    return self._calculate_tier(x)

def _calculate_tier(self, value):
    # Simpler logic
    pass
```

### SecurityValidator

**Purpose**: Detect security vulnerabilities

**Checks**:
- No `eval()`, `exec()`, `compile()`
- No SQL injection patterns (f-strings in queries)
- No hardcoded credentials

**Example Violations**:
```python
# ❌ Dangerous function
result = eval(user_input)

# ❌ SQL injection
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# ❌ Hardcoded credential
api_key = "sk_live_12345"
```

**Fixes**:
```python
# ✅ No eval - use json.loads or ast.literal_eval
result = json.loads(user_input)

# ✅ Parameterized query
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))

# ✅ Load from environment
api_key = os.getenv("API_KEY")
```

### LoggingValidator

**Purpose**: Enforce production-ready logging

**Checks**:
- No `print()` statements
- API calls should be logged
- Error handling should be logged

**Example Violation**:
```python
def fetch_data(self, url):
    print("Fetching data")  # ❌ Print statement
    data = requests.get(url)  # ❌ No API logging
    return data
```

**Fix**:
```python
from logging import getLogger

logger = getLogger(__name__)

def fetch_data(self, url):
    logger.info(f"Fetching data from: {url}")  # ✅ Structured logging
    try:
        data = requests.get(url)
        logger.debug(f"Received: {data}")
        return data
    except Exception as e:
        logger.error(f"Error fetching data: {e}")  # ✅ Error logging
        raise
```

## See Also

- [Constraint Enforcement Documentation](../../../../docs/CONSTRAINT_ENFORCEMENT.md)
- [ConstraintEnforcer Service](../services/constraint_enforcer.py)
- [Validation Models](../models/validation.py)
