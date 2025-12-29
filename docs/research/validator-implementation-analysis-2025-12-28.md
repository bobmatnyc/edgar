# EDGAR Validator Implementation Analysis

**Date:** 2025-12-28
**Purpose:** Comprehensive analysis of validator implementations to guide completion of missing functionality
**Files Analyzed:** 4 validator and constraint definition files

---

## Executive Summary

The EDGAR project has established a validation framework with three specialized validators (AST, Constraint, Accuracy) that work together to ensure generated code meets quality, architecture, and functional requirements. **All three validators have complete type signatures and structure but are missing core implementation logic.** This analysis provides detailed information for completing these implementations.

### Implementation Status Overview

| Component | File | Status | Completion % | Priority |
|-----------|------|--------|--------------|----------|
| AST Validator | `ast_validator.py` | Structure validation missing | 75% | HIGH |
| Constraint Validator | `constraint_validator.py` | All 4 validation methods stubbed | 40% | HIGH |
| Accuracy Validator | `accuracy_validator.py` | Safe execution & comparison missing | 30% | MEDIUM |
| Constraints Model | `constraints.py` | Complete | 100% | N/A |

---

## 1. AST Validator (`ast_validator.py`)

### Current Implementation State

**Fully Implemented:**
- ✅ Basic syntax validation using `ast.parse()`
- ✅ Exception handling (SyntaxError → ValidationResult)
- ✅ Custom exception classes (`ValidationError`, `SyntaxValidationError`)
- ✅ `ValidationResult` dataclass with `valid`, `errors`, `warnings`
- ✅ Main entry point `validate(code: str) -> ValidationResult`

**Missing Implementation:**
- ❌ `_validate_structure()` method (lines 76-94) - Currently just `pass`

### TODO/FIXME Comments

**Line 89-93:** TODO in `_validate_structure()`:
```python
# TODO: Implement structure validation
# - Check for class definitions
# - Check for function definitions
# - Validate type hints presence
# - Check for proper docstrings
```

### Method Signatures

```python
@dataclass(frozen=True)
class ASTValidator:
    def validate(self, code: str) -> ValidationResult:
        """Main validation entry point - IMPLEMENTED"""

    def _validate_structure(
        self,
        tree: ast.AST,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate code structure - NEEDS IMPLEMENTATION"""
```

### Dependencies and Imports

```python
import ast
from dataclasses import dataclass
```

**Key Libraries:**
- `ast` - Python Abstract Syntax Tree module (standard library)
- `dataclasses` - For immutable validator class

### Implementation Requirements

The `_validate_structure()` method needs to walk the AST and check:

1. **Class Definitions Check:**
   - Ensure at least one class is defined
   - Validate class names follow PEP 8 (PascalCase)
   - Check for base class inheritance

2. **Function Definitions Check:**
   - Ensure functions exist (module-level or class methods)
   - Validate function names follow PEP 8 (snake_case)

3. **Type Hints Validation:**
   - All function parameters have type annotations
   - All functions have return type annotations
   - Check for `Any` usage (should warn if found)

4. **Docstring Presence:**
   - Module-level docstring
   - Class docstrings
   - Public method/function docstrings

**Suggested AST Visitor Pattern:**
```python
class StructureVisitor(ast.NodeVisitor):
    def visit_ClassDef(self, node): ...
    def visit_FunctionDef(self, node): ...
    def visit_AsyncFunctionDef(self, node): ...
```

---

## 2. Constraint Validator (`constraint_validator.py`)

### Current Implementation State

**Fully Implemented:**
- ✅ `__post_init__()` with default interface initialization
- ✅ Main `validate()` method structure
- ✅ AST parsing with syntax error handling
- ✅ Calls to all 4 validation sub-methods
- ✅ `ValidationResult` aggregation

**Missing Implementation:**
- ❌ `_validate_interfaces()` (line 78-86)
- ❌ `_validate_dependency_injection()` (line 88-96)
- ❌ `_validate_type_hints()` (line 98-106)
- ❌ `_validate_pydantic_usage()` (line 108-116)

### TODO/FIXME Comments

**Line 85:** `_validate_interfaces()`
```python
# TODO: Check for IDataSource and IDataExtractor implementations
```

**Line 95:** `_validate_dependency_injection()`
```python
# TODO: Check for frozen dataclasses, injected dependencies
```

**Line 105:** `_validate_type_hints()`
```python
# TODO: Check all functions have type hints
```

**Line 115:** `_validate_pydantic_usage()`
```python
# TODO: Check for BaseModel inheritance, Field usage
```

### Method Signatures

```python
@dataclass(frozen=True)
class ConstraintValidator:
    required_interfaces: list[str] = None  # Defaults to ["IDataSource", "IDataExtractor"]

    def __post_init__(self) -> None:
        """Initialize defaults - IMPLEMENTED"""

    def validate(
        self,
        code: str,
        constraints: dict[str, Any],
    ) -> ValidationResult:
        """Main validation - IMPLEMENTED (structure only)"""

    def _validate_interfaces(
        self, tree: ast.AST, errors: list[str], warnings: list[str]
    ) -> None:
        """NEEDS IMPLEMENTATION"""

    def _validate_dependency_injection(
        self, tree: ast.AST, errors: list[str], warnings: list[str]
    ) -> None:
        """NEEDS IMPLEMENTATION"""

    def _validate_type_hints(
        self, tree: ast.AST, errors: list[str], warnings: list[str]
    ) -> None:
        """NEEDS IMPLEMENTATION"""

    def _validate_pydantic_usage(
        self, tree: ast.AST, errors: list[str], warnings: list[str]
    ) -> None:
        """NEEDS IMPLEMENTATION"""
```

### Dependencies and Imports

```python
import ast
from dataclasses import dataclass
from typing import Any

from edgar.validators.ast_validator import ValidationResult
```

**Key Dependencies:**
- `ast` - For AST traversal
- `ValidationResult` - Shared result type from `ast_validator`

### Implementation Requirements

#### 2.1 `_validate_interfaces()`

**Purpose:** Ensure generated code implements required interfaces (IDataSource, IDataExtractor)

**Detection Strategy:**
1. Find all `ClassDef` nodes in AST
2. For each class, check `bases` attribute for interface names
3. If interface found, verify required methods exist:
   - `IDataSource`: `async def fetch(self) -> dict[str, Any]`
   - `IDataExtractor`: `def extract(self, raw_data: dict[str, Any]) -> BaseModel`

**Error Conditions:**
- No class implements required interface → Error: "Missing implementation of {interface}"
- Interface implemented but missing required method → Error: "{interface}.{method} not found"
- Method signature mismatch → Warning: "{method} signature differs from interface"

**Reference:** See `/Users/masa/Projects/edgar/src/edgar/models/constraints.py` lines 111-120 for interface definitions

#### 2.2 `_validate_dependency_injection()`

**Purpose:** Ensure dependency injection pattern is followed

**Detection Strategy:**
1. Find all `ClassDef` nodes
2. Check for `@dataclass(frozen=True)` decorator
3. Validate `__init__` or `__post_init__` accepts dependencies
4. Check for hardcoded configuration (string literals for URLs, API keys, etc.)

**Error Conditions:**
- Dataclass not frozen → Error: "Class {name} should use frozen=True for immutability"
- Hardcoded configuration found → Error: "Hardcoded config detected: {value}"
- Global variables used → Error: "Global variable {name} violates DI pattern"

**Pattern Reference:** `constraints.py` lines 123-130 (Dependency Injection pattern)

#### 2.3 `_validate_type_hints()`

**Purpose:** Ensure comprehensive type hint coverage

**Detection Strategy:**
1. Visit all `FunctionDef` and `AsyncFunctionDef` nodes
2. Check `args.args` for parameter annotations
3. Check `returns` attribute for return type annotation
4. Scan for `Any` type usage

**Error Conditions:**
- Function parameter without type hint → Error: "{function}.{param} missing type hint"
- Function without return type → Error: "{function} missing return type annotation"
- `Any` type used → Warning: "Avoid Any type in {location}" (if `forbid_any_type` is True)

**Configuration:** `constraints.py` lines 79-85 defines type safety settings

#### 2.4 `_validate_pydantic_usage()`

**Purpose:** Ensure Pydantic models are used correctly

**Detection Strategy:**
1. Find classes inheriting from `BaseModel`
2. Check for `Field(...)` usage in class attributes
3. Verify field descriptions are provided
4. Check for custom validators (`@field_validator`, `@model_validator`)

**Error Conditions:**
- Data class not using Pydantic → Error: "Use Pydantic BaseModel for data structures"
- Field without description → Warning: "Field {name} missing description"
- Missing field validation → Info: "Consider adding validators for {field}"

**Pattern Reference:** `constraints.py` lines 132-138 (Pydantic Validation pattern)

---

## 3. Accuracy Validator (`accuracy_validator.py`)

### Current Implementation State

**Fully Implemented:**
- ✅ Parameter validation (examples vs expected_outputs count)
- ✅ Basic validation structure
- ✅ Error/warning list initialization
- ✅ `ValidationResult` return

**Missing Implementation:**
- ❌ Safe code execution environment
- ❌ Output comparison logic
- ❌ Runtime error handling
- ❌ Data type/structure validation

### TODO/FIXME Comments

**Line 54-58:** Main `validate()` method:
```python
# TODO: Implement safe code execution and validation
# - Execute code in restricted environment
# - Compare outputs with expected results
# - Check for runtime errors
# - Validate data types and structure
```

**Line 83:** `_execute_code_safely()`:
```python
# TODO: Implement safe code execution
raise NotImplementedError("Safe code execution not yet implemented")
```

**Line 100:** `_compare_outputs()`:
```python
# TODO: Implement deep output comparison
return []
```

### Method Signatures

```python
@dataclass(frozen=True)
class AccuracyValidator:
    safe_mode: bool = True
    timeout: float = 5.0

    def validate(
        self,
        code: str,
        examples: list[dict[str, Any]],
        expected_outputs: list[dict[str, Any]],
    ) -> ValidationResult:
        """Main validation - PARTIALLY IMPLEMENTED"""

    def _execute_code_safely(
        self,
        code: str,
        example_input: dict[str, Any],
    ) -> dict[str, Any]:
        """NEEDS IMPLEMENTATION - Currently raises NotImplementedError"""

    def _compare_outputs(
        self,
        actual: dict[str, Any],
        expected: dict[str, Any],
    ) -> list[str]:
        """NEEDS IMPLEMENTATION - Currently returns []"""
```

### Dependencies and Imports

```python
from dataclasses import dataclass
from typing import Any

from edgar.validators.ast_validator import ValidationResult
```

**Missing Imports Needed:**
- `subprocess` or `multiprocessing` - For isolated execution
- `signal` - For timeout handling
- `json` or `deepdiff` - For output comparison
- `RestrictedPython` library (optional) - For safe execution

### Implementation Requirements

#### 3.1 Safe Code Execution (`_execute_code_safely()`)

**Challenge:** Execute untrusted generated code safely without compromising system

**Recommended Approach:**

**Option 1: RestrictedPython (Recommended)**
```python
from RestrictedPython import compile_restricted, safe_globals

def _execute_code_safely(self, code: str, example_input: dict[str, Any]) -> dict[str, Any]:
    # Compile with restrictions
    byte_code = compile_restricted(code, '<string>', 'exec')

    # Create safe execution environment
    safe_env = {
        '__builtins__': safe_globals,
        'example_input': example_input,
    }

    # Execute with timeout
    exec(byte_code, safe_env)

    return safe_env.get('result', {})
```

**Option 2: Subprocess Isolation**
```python
import subprocess
import json

def _execute_code_safely(self, code: str, example_input: dict[str, Any]) -> dict[str, Any]:
    # Write code to temp file
    # Execute in subprocess with timeout
    result = subprocess.run(
        ['python', '-c', code],
        input=json.dumps(example_input),
        capture_output=True,
        timeout=self.timeout,
    )
    return json.loads(result.stdout)
```

**Security Requirements:**
- Restrict file system access
- Block network access
- Limit memory usage
- Enforce timeout (`self.timeout` seconds)
- Prevent dangerous imports (`os`, `sys`, `subprocess`, etc.)

**Error Handling:**
- `TimeoutError` → Error: "Code execution exceeded {timeout}s"
- `MemoryError` → Error: "Code execution exceeded memory limit"
- `ImportError` → Error: "Restricted import: {module}"
- General exceptions → Error: "Runtime error: {exception}"

#### 3.2 Output Comparison (`_compare_outputs()`)

**Purpose:** Deep comparison of actual vs expected outputs

**Recommended Libraries:**
- `deepdiff` - Comprehensive deep comparison
- Built-in `json` - For serialization comparison
- `pytest.approx` - For floating-point comparison

**Implementation Strategy:**

```python
from deepdiff import DeepDiff

def _compare_outputs(
    self,
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> list[str]:
    differences = []

    # Use DeepDiff for comprehensive comparison
    diff = DeepDiff(expected, actual, ignore_order=True)

    if diff:
        # Type changes
        if 'type_changes' in diff:
            differences.append(f"Type mismatch: {diff['type_changes']}")

        # Value changes
        if 'values_changed' in diff:
            differences.append(f"Value mismatch: {diff['values_changed']}")

        # Missing/added items
        if 'dictionary_item_removed' in diff:
            differences.append(f"Missing keys: {diff['dictionary_item_removed']}")
        if 'dictionary_item_added' in diff:
            differences.append(f"Extra keys: {diff['dictionary_item_added']}")

    return differences
```

**Comparison Checks:**
1. **Data Types:** Ensure types match (int vs float, str vs bytes, etc.)
2. **Structure:** Dictionary keys, list lengths, nested structure
3. **Values:** Exact value comparison (with tolerance for floats)
4. **Order:** List order matters unless explicitly ignored
5. **Null Handling:** None vs missing key distinction

**Special Cases:**
- Floating point comparison: Use tolerance (e.g., `abs(a - b) < 1e-9`)
- Date/time: Parse and compare as datetime objects
- UUIDs/timestamps: May need to ignore or use patterns
- Large datasets: Consider sampling or summary comparison

#### 3.3 Main Validation Loop

The main `validate()` method needs to iterate through examples:

```python
def validate(
    self,
    code: str,
    examples: list[dict[str, Any]],
    expected_outputs: list[dict[str, Any]],
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    # Existing count check...

    for idx, (example, expected) in enumerate(zip(examples, expected_outputs)):
        try:
            # Execute code with example
            actual = self._execute_code_safely(code, example)

            # Compare outputs
            diffs = self._compare_outputs(actual, expected)
            if diffs:
                errors.append(f"Example {idx + 1} failed: {', '.join(diffs)}")

        except TimeoutError:
            errors.append(f"Example {idx + 1} timed out after {self.timeout}s")
        except Exception as e:
            errors.append(f"Example {idx + 1} runtime error: {str(e)}")

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
```

---

## 4. Constraints Model (`constraints.py`)

### Current Implementation State

**Status:** ✅ **COMPLETE** - No implementation needed

This file defines Pydantic models used by the validators. All models are fully implemented:

- `InterfaceRequirement` - Defines required interfaces
- `DesignPattern` - Design pattern specifications
- `CodeQualityRule` - Quality rules with severity levels
- `ArchitectureConstraints` - Main constraints model with defaults

### Key Features

**Default Constraints Available:**
```python
ArchitectureConstraints.default()
```

Returns constraints with:
- **Interfaces:** `IDataSource`, `IDataExtractor`
- **Design Patterns:** Dependency Injection, Pydantic Validation
- **Type Safety:** All type hints required, forbid `Any` type
- **Code Quality:** PEP 8, docstring coverage, max function length
- **Forbidden Patterns:** Global vars, hardcoded config, bare except, mutable defaults

### Usage in Validators

Validators should use this model to get constraint requirements:

```python
from edgar.models.constraints import ArchitectureConstraints

constraints = ArchitectureConstraints.default()

# Access interface requirements
for interface in constraints.interfaces:
    print(f"Check for {interface.name}: {interface.methods}")

# Access type safety settings
if constraints.type_safety["require_type_hints"]:
    # Validate type hints
    pass
```

---

## 5. Implementation Priorities and Dependencies

### High Priority (Must Complete First)

1. **AST Validator Structure Validation** (`ast_validator.py`)
   - Required by: Constraint Validator
   - Complexity: Medium
   - Estimated Effort: 4-6 hours
   - Dependencies: None (only uses `ast` stdlib)

2. **Constraint Validator - Type Hints** (`constraint_validator.py`)
   - Required by: Code generation validation pipeline
   - Complexity: Medium
   - Estimated Effort: 3-4 hours
   - Dependencies: AST Validator

3. **Constraint Validator - Interfaces** (`constraint_validator.py`)
   - Required by: Architecture enforcement
   - Complexity: Medium
   - Estimated Effort: 4-5 hours
   - Dependencies: AST Validator, Constraints Model

### Medium Priority

4. **Constraint Validator - Dependency Injection** (`constraint_validator.py`)
   - Complexity: High (pattern detection is complex)
   - Estimated Effort: 6-8 hours
   - Dependencies: AST Validator

5. **Constraint Validator - Pydantic Usage** (`constraint_validator.py`)
   - Complexity: Medium
   - Estimated Effort: 3-4 hours
   - Dependencies: AST Validator

### Lower Priority (Can Be Iterative)

6. **Accuracy Validator - Safe Execution** (`accuracy_validator.py`)
   - Complexity: High (security implications)
   - Estimated Effort: 8-10 hours
   - Dependencies: May need external library (RestrictedPython)
   - Note: Consider using subprocess isolation first, then enhance

7. **Accuracy Validator - Output Comparison** (`accuracy_validator.py`)
   - Complexity: Medium
   - Estimated Effort: 4-5 hours
   - Dependencies: Consider `deepdiff` library

---

## 6. Testing Recommendations

### Test Data Requirements

**For AST Validator:**
```python
# Valid code with all requirements
valid_code = """
class DataSource(IDataSource):
    '''Fetches data.'''
    async def fetch(self) -> dict[str, Any]:
        ...
"""

# Invalid code - missing type hints
invalid_code = """
def process(data):  # Missing type hints
    return data
"""
```

**For Constraint Validator:**
```python
# Code following DI pattern
di_code = """
@dataclass(frozen=True)
class Service:
    config: Config  # Injected dependency
"""

# Code violating DI pattern
non_di_code = """
class Service:
    API_KEY = "hardcoded-key-123"  # Violation!
"""
```

**For Accuracy Validator:**
```python
examples = [
    {"company_id": "AAPL", "year": 2023},
    {"company_id": "MSFT", "year": 2023},
]

expected_outputs = [
    {"revenue": 383285000000, "net_income": 96995000000},
    {"revenue": 211915000000, "net_income": 72361000000},
]
```

### Test Coverage Goals

- **Unit Tests:** Each validation method independently
- **Integration Tests:** Full validator pipeline
- **Edge Cases:** Empty code, syntax errors, partial implementations
- **Performance Tests:** Large AST trees, timeout handling

---

## 7. External Dependencies to Consider

### Required Libraries

| Library | Purpose | Priority | Installation |
|---------|---------|----------|--------------|
| `deepdiff` | Output comparison | HIGH | `pip install deepdiff` |
| `RestrictedPython` | Safe code execution | MEDIUM | `pip install RestrictedPython` |

### Standard Library Usage

All current validators only use Python stdlib:
- `ast` - AST parsing and traversal
- `dataclasses` - Immutable validator classes
- `typing` - Type hints

**Recommendation:** Keep stdlib-only where possible to minimize dependencies.

---

## 8. Architecture Patterns to Follow

### Visitor Pattern for AST Traversal

```python
class TypeHintVisitor(ast.NodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_FunctionDef(self, node):
        # Check type hints
        for arg in node.args.args:
            if arg.annotation is None:
                self.errors.append(f"Missing type hint: {arg.arg}")

        if node.returns is None:
            self.errors.append(f"Missing return type: {node.name}")

        self.generic_visit(node)
```

### Error Accumulation Pattern

All validators follow this pattern:
```python
errors: list[str] = []
warnings: list[str] = []

# Run multiple checks, accumulating errors
self._check_one(tree, errors, warnings)
self._check_two(tree, errors, warnings)

# Return aggregated result
return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
```

### Frozen Dataclass Pattern

All validators are immutable:
```python
@dataclass(frozen=True)
class Validator:
    config: Config  # Injected at construction

    def validate(self, code: str) -> ValidationResult:
        # Pure function - no state mutation
        ...
```

---

## 9. Integration Points

### How Validators Work Together

```
Generated Code (str)
    ↓
1. ASTValidator.validate(code)
    ├─ Syntax check
    └─ Structure validation
    ↓
2. ConstraintValidator.validate(code, constraints)
    ├─ Interface implementation
    ├─ Dependency injection
    ├─ Type hints
    └─ Pydantic usage
    ↓
3. AccuracyValidator.validate(code, examples, expected)
    ├─ Safe execution
    └─ Output comparison
    ↓
ValidationResult (aggregated)
```

### Calling Convention

```python
from edgar.validators.ast_validator import ASTValidator
from edgar.validators.constraint_validator import ConstraintValidator
from edgar.validators.accuracy_validator import AccuracyValidator
from edgar.models.constraints import ArchitectureConstraints

# Step 1: Syntax validation
ast_validator = ASTValidator()
ast_result = ast_validator.validate(generated_code)

if not ast_result.valid:
    return ast_result  # Fail fast on syntax errors

# Step 2: Architecture constraints
constraints = ArchitectureConstraints.default()
constraint_validator = ConstraintValidator()
constraint_result = constraint_validator.validate(generated_code, constraints.dict())

# Step 3: Accuracy validation (if examples available)
accuracy_validator = AccuracyValidator(safe_mode=True, timeout=5.0)
accuracy_result = accuracy_validator.validate(
    generated_code,
    examples,
    expected_outputs,
)

# Aggregate results
all_errors = ast_result.errors + constraint_result.errors + accuracy_result.errors
all_warnings = ast_result.warnings + constraint_result.warnings + accuracy_result.warnings

final_result = ValidationResult(
    valid=len(all_errors) == 0,
    errors=all_errors,
    warnings=all_warnings,
)
```

---

## 10. Next Steps for Implementation

### Recommended Implementation Order

1. **Phase 1: AST Foundation (Week 1)**
   - Implement `ASTValidator._validate_structure()`
   - Write unit tests for AST validation
   - Test with sample generated code

2. **Phase 2: Constraint Validation (Week 2)**
   - Implement `ConstraintValidator._validate_type_hints()` (easiest)
   - Implement `ConstraintValidator._validate_interfaces()`
   - Implement `ConstraintValidator._validate_pydantic_usage()`
   - Implement `ConstraintValidator._validate_dependency_injection()` (most complex)
   - Write comprehensive tests

3. **Phase 3: Accuracy Validation (Week 3)**
   - Start with basic subprocess execution (safer)
   - Implement `AccuracyValidator._execute_code_safely()`
   - Implement `AccuracyValidator._compare_outputs()`
   - Add timeout and error handling
   - Consider RestrictedPython migration later

4. **Phase 4: Integration Testing (Week 4)**
   - Test full validation pipeline
   - Performance optimization
   - Security review of safe execution
   - Documentation updates

### Quick Wins

Start with these for immediate value:
1. AST structure validation (enables basic checks)
2. Type hint validation (high value, medium complexity)
3. Interface validation (core architecture requirement)

### Deferred Enhancements

Can be added later without blocking core functionality:
- Advanced pattern detection (e.g., detecting specific code smells)
- Performance profiling of generated code
- Security vulnerability scanning
- Complexity metrics (cyclomatic complexity, etc.)

---

## Conclusion

The EDGAR validation framework has a solid architectural foundation with clear separation of concerns:
- **AST Validator**: Syntax and structure
- **Constraint Validator**: Architecture patterns and type safety
- **Accuracy Validator**: Functional correctness

All validators follow consistent patterns (frozen dataclasses, error accumulation, ValidationResult), making implementation straightforward once you understand the AST traversal patterns.

**Total Estimated Effort:** 30-40 hours across all validators

**Blockers:** None - all dependencies are available (mostly stdlib)

**Risk Areas:**
- Safe code execution security (Accuracy Validator)
- Complex pattern detection (Dependency Injection validation)

**Recommendation:** Implement in phases, starting with AST and Constraint validators to get immediate value, then iterate on Accuracy validation with enhanced security.
