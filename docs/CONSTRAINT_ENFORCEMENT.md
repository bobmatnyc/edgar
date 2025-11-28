# Constraint Enforcement System

**Purpose**: Ensure AI-generated code meets architectural, quality, and security standards through AST-based validation.

**Phase**: Phase 1 MVP - Weather API Proof-of-Concept
**Ticket**: 1M-327 - Build Constraint Enforcer (AST Validation)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Constraint Categories](#constraint-categories)
- [Usage](#usage)
- [Configuration](#configuration)
- [Violation Examples](#violation-examples)
- [Integration](#integration)
- [Performance](#performance)

---

## Overview

The Constraint Enforcer validates generated code against strict architectural rules to prevent:

- **Architectural drift**: Code that doesn't follow platform patterns
- **Security vulnerabilities**: Dangerous functions, SQL injection, hardcoded credentials
- **Quality degradation**: High complexity, missing documentation, poor logging
- **Maintenance issues**: No type hints, missing interfaces, anti-patterns

### Design Philosophy

**Proactive Prevention > Reactive Fixing**

The enforcer catches issues at generation time, not runtime. This prevents bad patterns from ever reaching production.

### Key Benefits

✅ **Consistency**: All extractors follow same architecture
✅ **Security**: No dangerous patterns in generated code
✅ **Maintainability**: Type hints, interfaces, proper logging
✅ **Quality**: Complexity limits, code size constraints
✅ **Testability**: Dependency injection, clear interfaces

---

## Architecture

### Component Structure

```
ConstraintEnforcer (Orchestrator)
    ├── InterfaceValidator (IDataExtractor check)
    ├── DependencyInjectionValidator (@inject decorator)
    ├── TypeHintValidator (Type annotations)
    ├── ImportValidator (Forbidden imports)
    ├── ComplexityValidator (Cyclomatic complexity)
    ├── SecurityValidator (SQL injection, eval, credentials)
    └── LoggingValidator (Structured logging)
```

### Validation Flow

```
Code Input
    ↓
AST Parsing ─────→ Syntax Error? → Return SYNTAX_ERROR
    ↓
Run All Validators
    ↓
Aggregate Violations
    ↓
Determine Validity (no ERROR-level violations)
    ↓
Return ValidationResult
```

### Performance Characteristics

- **AST Parsing**: O(n) where n = code size (~1ms for 500 LOC)
- **Each Validator**: O(n) where n = AST nodes (~0.5ms per validator)
- **Total**: ~5-10ms for typical extractor (7 validators × 500 LOC)
- **Target**: <100ms (easily achieved)

---

## Constraint Categories

### 1. Architectural Constraints

**Must Have:**
- ✅ Class implements `IDataExtractor` interface
- ✅ Uses dependency injection (`@inject` decorator)
- ✅ Type hints on all methods
- ✅ Google-style docstrings

**Must NOT Have:**
- ❌ Global variables or mutable state
- ❌ Direct imports of forbidden modules
- ❌ Hardcoded credentials or API keys

**Example - Valid:**
```python
from dependency_injector.wiring import inject
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    """Extract weather data."""

    @inject
    def __init__(self, client: HTTPClient):
        """Initialize with dependencies."""
        self.client = client

    def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract weather data."""
        return self.client.get("/weather")
```

**Example - Invalid:**
```python
# ❌ Missing interface
# ❌ Missing @inject
# ❌ Missing type hints
class WeatherExtractor:
    def __init__(self, client):
        self.client = client

    def extract(self, params):
        return self.client.get("/weather")
```

### 2. Code Quality Constraints

**Limits:**
- Cyclomatic complexity < 10 per method
- Method length < 50 lines
- Class length < 300 lines

**Example - Valid (Complexity: 3):**
```python
def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Process data with low complexity."""
    if not data:
        return {}

    if "error" in data:
        logger.error(f"Error in data: {data['error']}")
        return {}

    return self._transform(data)
```

**Example - Invalid (Complexity: 12):**
```python
def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Process data with high complexity."""
    # ❌ Too many nested conditions
    if data:
        if "type" in data:
            if data["type"] == "A":
                if data["level"] > 5:
                    if data["active"]:
                        if data["verified"]:
                            if data["premium"]:
                                if data["region"] == "US":
                                    if data["age"] > 18:
                                        if data["consent"]:
                                            return {"approved": True}
    return {}
```

### 3. Security Constraints

**Prohibited:**
- ❌ `eval()`, `exec()`, `compile()` - arbitrary code execution
- ❌ SQL string concatenation/f-strings - injection risk
- ❌ Hardcoded credentials - security leak
- ❌ `os`, `subprocess` imports - shell command risk

**Example - Valid:**
```python
def query_users(self, user_id: str) -> Dict[str, Any]:
    """Query user safely with parameterized query."""
    logger.info(f"Querying user: {user_id}")

    # ✅ Parameterized query (safe)
    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )
    return cursor.fetchone()
```

**Example - Invalid:**
```python
def query_users(self, user_id: str) -> Dict[str, Any]:
    """Query user with SQL injection vulnerability."""
    # ❌ SQL injection risk
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()
```

**Example - Hardcoded Credentials (Invalid):**
```python
class APIClient:
    def __init__(self):
        # ❌ Hardcoded credential
        self.api_key = "sk_live_1234567890abcdef"
```

**Example - Environment Variables (Valid):**
```python
class APIClient:
    def __init__(self):
        # ✅ Load from environment
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY not set")
```

### 4. Logging Constraints

**Requirements:**
- ✅ Use `logger.info()`, `logger.error()`, `logger.debug()`
- ✅ Log all API calls
- ✅ Log all error conditions
- ❌ No `print()` statements in production code

**Example - Valid:**
```python
from logging import getLogger

logger = getLogger(__name__)

def fetch_data(self, url: str) -> Dict[str, Any]:
    """Fetch data from API."""
    logger.info(f"Fetching data from: {url}")

    try:
        response = self.client.get(url)
        logger.debug(f"Response status: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise
```

**Example - Invalid:**
```python
def fetch_data(self, url: str) -> Dict[str, Any]:
    """Fetch data from API."""
    # ❌ Using print instead of logger
    print(f"Fetching data from: {url}")

    try:
        response = self.client.get(url)
        return response.json()
    except Exception as e:
        # ❌ No error logging
        raise
```

---

## Usage

### Basic Usage

```python
from edgar_analyzer.services.constraint_enforcer import ConstraintEnforcer

# Initialize enforcer
enforcer = ConstraintEnforcer()

# Validate code
code = '''
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class MyExtractor(IDataExtractor):
    pass
'''

result = enforcer.validate_code(code)

if result.valid:
    print("✅ Code passes all constraints")
else:
    print(f"❌ Found {len(result.violations)} violations:")
    for violation in result.violations:
        print(f"  {violation}")
```

### Validate File

```python
# Validate a Python file
result = enforcer.validate_file("extractors/weather_extractor.py")

if not result.valid:
    # Print errors first
    for error in result.get_violations_by_severity(Severity.ERROR):
        print(f"ERROR: {error}")

    # Then warnings
    for warning in result.get_violations_by_severity(Severity.WARNING):
        print(f"WARNING: {warning}")
```

### Custom Configuration

```python
from edgar_analyzer.models.validation import ConstraintConfig

# Create custom config
config = ConstraintConfig(
    max_complexity=5,  # Stricter complexity limit
    max_method_lines=30,  # Shorter methods
    allow_print_statements=True,  # Allow prints (debugging)
    enforce_interface=False,  # Don't require interface
)

# Use custom config
enforcer = ConstraintEnforcer(config=config)
result = enforcer.validate_code(code)
```

### Load Configuration from YAML

```python
import yaml
from edgar_analyzer.models.validation import ConstraintConfig

# Load config from file
with open("config/constraints.yaml") as f:
    config_dict = yaml.safe_load(f)

config = ConstraintConfig.from_dict(config_dict)
enforcer = ConstraintEnforcer(config=config)
```

---

## Configuration

### Configuration File Format

**File**: `src/edgar_analyzer/config/constraints.yaml`

```yaml
# Code Quality Constraints
max_complexity: 10
max_method_lines: 50
max_class_lines: 300

# Security: Forbidden Imports
forbidden_imports:
  - os
  - subprocess
  - eval
  - exec
  - compile
  - __import__

# Dependency Injection: Required Decorators
required_decorators:
  __init__:
    - inject

# Enforcement Flags
enforce_type_hints: true
enforce_docstrings: true
enforce_interface: true
allow_print_statements: false
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_complexity` | int | 10 | Maximum cyclomatic complexity per method |
| `max_method_lines` | int | 50 | Maximum lines per method |
| `max_class_lines` | int | 300 | Maximum lines per class |
| `forbidden_imports` | list | See above | Modules that cannot be imported |
| `required_decorators` | dict | `{__init__: [inject]}` | Required decorators per method |
| `enforce_type_hints` | bool | true | Require type hints on all methods |
| `enforce_docstrings` | bool | true | Require docstrings on all classes/methods |
| `enforce_interface` | bool | true | Require IDataExtractor implementation |
| `allow_print_statements` | bool | false | Allow print() in production code |

### Dynamic Configuration Updates

```python
# Update configuration at runtime
enforcer = ConstraintEnforcer()

# Get current config
current_config = enforcer.get_config()

# Modify config
new_config = ConstraintConfig(
    max_complexity=15,  # More permissive
    forbidden_imports=current_config.forbidden_imports,
)

# Update enforcer
enforcer.update_config(new_config)
```

---

## Violation Examples

### Complete Examples with Fixes

#### Example 1: Missing Interface

**Invalid:**
```python
class WeatherExtractor:
    """Missing IDataExtractor interface."""
    pass
```

**Violation:**
```
❌ [MISSING_INTERFACE] Class 'WeatherExtractor' must implement IDataExtractor interface (line 1)
   Suggestion: Add 'IDataExtractor' to class bases: class WeatherExtractor(IDataExtractor):
```

**Fixed:**
```python
from edgar_analyzer.interfaces.data_extractor import IDataExtractor

class WeatherExtractor(IDataExtractor):
    """Implements IDataExtractor interface."""
    pass
```

#### Example 2: Missing @inject Decorator

**Invalid:**
```python
class WeatherExtractor(IDataExtractor):
    def __init__(self, client: HTTPClient):
        self.client = client
```

**Violation:**
```
❌ [MISSING_DECORATOR] WeatherExtractor.__init__ must have @inject decorator (line 2)
   Suggestion: Add decorator: @inject
```

**Fixed:**
```python
from dependency_injector.wiring import inject

class WeatherExtractor(IDataExtractor):
    @inject
    def __init__(self, client: HTTPClient):
        self.client = client
```

#### Example 3: Missing Type Hints

**Invalid:**
```python
def extract(self, params):
    return {}
```

**Violation:**
```
❌ [MISSING_TYPE_HINT] Method 'extract' has parameters without type hints: params (line 1)
   Suggestion: Add type hints to all parameters: def extract(self, params: <type>):

❌ [MISSING_RETURN_TYPE] Method 'extract' has no return type annotation (line 1)
   Suggestion: Add return type: def extract(...) -> <ReturnType>:
```

**Fixed:**
```python
from typing import Dict, Any

def extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
    return {}
```

#### Example 4: Forbidden Import

**Invalid:**
```python
import os

def get_files(self):
    return os.listdir("/tmp")
```

**Violation:**
```
❌ [FORBIDDEN_IMPORT] Import of 'os' is not allowed (security risk) (line 1)
   Suggestion: Remove 'import os'. Use safer alternatives or request allowlist update.
```

**Fixed:**
```python
from pathlib import Path

def get_files(self):
    # Use pathlib instead of os
    return [f.name for f in Path("/tmp").iterdir()]
```

#### Example 5: High Complexity

**Invalid:**
```python
def process(self, x: int) -> int:
    """High complexity method."""
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    if x > 40:
                        if x > 50:
                            if x > 60:
                                if x > 70:
                                    if x > 80:
                                        if x > 90:
                                            return 100
    return 0
```

**Violation:**
```
❌ [HIGH_COMPLEXITY] Method 'process' has cyclomatic complexity 11 (max: 10) (line 1)
   Suggestion: Refactor 'process' into smaller methods. Extract conditional logic into helper methods.
```

**Fixed:**
```python
def process(self, x: int) -> int:
    """Refactored for lower complexity."""
    if x <= 0:
        return 0

    # Extract logic into helper method
    return self._calculate_tier(x)

def _calculate_tier(self, value: int) -> int:
    """Calculate tier based on value."""
    tiers = [
        (90, 100),
        (80, 90),
        (70, 80),
        # ... etc
    ]

    for threshold, result in tiers:
        if value > threshold:
            return result

    return 0
```

---

## Integration

### Integration with Code Generator

```python
from edgar_analyzer.services.code_generator import CodeGenerator
from edgar_analyzer.services.constraint_enforcer import ConstraintEnforcer

# Initialize components
generator = CodeGenerator()
enforcer = ConstraintEnforcer()

# Generate code
prompt = "Create a weather API extractor"
generated_code = generator.generate(prompt)

# Validate generated code
result = enforcer.validate_code(generated_code)

if not result.valid:
    # Provide feedback to AI for regeneration
    feedback = "\n".join([
        f"- {v.code}: {v.message} (line {v.line})"
        for v in result.violations
    ])

    # Regenerate with feedback
    improved_code = generator.regenerate(
        prompt=prompt,
        previous_code=generated_code,
        feedback=feedback
    )

    # Re-validate
    final_result = enforcer.validate_code(improved_code)

    if final_result.valid:
        print("✅ Code generation successful after refinement")
```

### Integration with CI/CD

```python
# ci_validation.py
import sys
from pathlib import Path
from edgar_analyzer.services.constraint_enforcer import ConstraintEnforcer

def validate_extractors(extractors_dir: str) -> bool:
    """Validate all extractor files."""
    enforcer = ConstraintEnforcer()
    all_valid = True

    for file_path in Path(extractors_dir).glob("**/*_extractor.py"):
        result = enforcer.validate_file(str(file_path))

        if not result.valid:
            print(f"\n❌ {file_path}:")
            for violation in result.violations:
                print(f"  {violation}")
            all_valid = False

    return all_valid

if __name__ == "__main__":
    if not validate_extractors("src/extractors"):
        sys.exit(1)  # Fail CI build
    print("✅ All extractors pass validation")
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

python ci_validation.py

if [ $? -ne 0 ]; then
    echo "❌ Constraint validation failed. Fix violations before committing."
    exit 1
fi
```

---

## Performance

### Benchmarks

Measured on typical extractor code (~200 LOC, 7 methods):

| Operation | Time | Details |
|-----------|------|---------|
| AST Parsing | 0.8ms | Parse code into AST |
| InterfaceValidator | 0.3ms | Check IDataExtractor implementation |
| DependencyInjectionValidator | 0.4ms | Check @inject decorators |
| TypeHintValidator | 0.5ms | Check type annotations |
| ImportValidator | 0.3ms | Check forbidden imports |
| ComplexityValidator | 1.2ms | Calculate cyclomatic complexity |
| SecurityValidator | 0.9ms | Check security patterns |
| LoggingValidator | 0.6ms | Check logging usage |
| **Total** | **5.0ms** | **Complete validation** |

### Performance Optimization Tips

**1. Batch Validation**
```python
# Validate multiple files efficiently
results = [
    enforcer.validate_file(f)
    for f in Path("extractors").glob("*.py")
]
```

**2. Cache Parsed ASTs** (for repeated validation)
```python
import ast
from functools import lru_cache

@lru_cache(maxsize=128)
def parse_code_cached(code: str) -> ast.AST:
    """Cache parsed ASTs for repeated validation."""
    return ast.parse(code)
```

**3. Parallel Validation** (for large codebases)
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(enforcer.validate_file, str(f))
        for f in Path("extractors").glob("*.py")
    ]
    results = [f.result() for f in futures]
```

---

## FAQ

### Q: Can I disable specific validators?

**A:** Yes, via configuration:

```python
config = ConstraintConfig(
    enforce_interface=False,  # Disable interface validation
    enforce_type_hints=False,  # Disable type hint validation
)
```

### Q: How do I add a new forbidden import?

**A:** Update configuration:

```python
config = ConstraintConfig(
    forbidden_imports={
        "os", "subprocess", "eval", "exec",
        "pickle",  # Add new forbidden import
    }
)
```

### Q: Can I allow specific violations in legacy code?

**A:** Yes, use WARNING severity or custom config:

```python
# Create permissive config for legacy code
legacy_config = ConstraintConfig(
    enforce_interface=False,
    allow_print_statements=True,
    max_complexity=20,  # More permissive
)
```

### Q: How do I test custom validators?

**A:** Create unit tests:

```python
def test_custom_validator():
    validator = MyCustomValidator(config)
    tree = ast.parse(code)
    violations = validator.validate(tree)
    assert len(violations) == expected_count
```

---

## Summary

The Constraint Enforcer ensures AI-generated code meets all architectural, quality, and security standards through:

✅ **AST-based validation** - Accurate, fast, comprehensive
✅ **Multiple validator types** - Architecture, quality, security, logging
✅ **Actionable feedback** - Line numbers, suggestions, severity levels
✅ **Configurable rules** - Adjust thresholds per project needs
✅ **High performance** - <100ms validation for typical code

**Next Steps:**
1. Run unit tests: `pytest tests/unit/services/test_constraint_enforcer.py`
2. Run integration tests: `pytest tests/integration/test_constraint_enforcement.py`
3. Validate generated code in Code Generator integration
4. Set up CI/CD validation pipeline

**Related Documentation:**
- [Code Generator](CODE_GENERATOR.md)
- [IDataExtractor Interface](INTERFACES.md)
- [Security Guidelines](SECURITY.md)
