# Pattern Detection Guide

**Platform**: `extract_transform_platform`
**Component**: Example Parser & Schema Analyzer
**Status**: Batch 2 Complete (60/60 tests passing)

## Table of Contents

- [Overview](#overview)
- [How Pattern Detection Works](#how-pattern-detection-works)
- [Pattern Types](#pattern-types)
- [Confidence Scoring](#confidence-scoring)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Overview

The Pattern Detection system analyzes input/output example pairs to automatically identify transformation patterns. This **example-driven approach** eliminates the need for manual transformation logic - you simply provide 2-3 examples, and the platform infers the transformation rules.

### Key Features

- **14 Pattern Types**: Covers common data transformations
- **Automatic Detection**: AI-powered pattern recognition
- **Confidence Scoring**: 0.0-1.0 confidence for each pattern
- **Schema-Aware**: Understands field types and structures
- **Nested Support**: Handles nested objects and arrays

### Components

| Component | Purpose | LOC |
|-----------|---------|-----|
| **PatternModels** | Pattern data structures | 530 LOC |
| **SchemaAnalyzer** | Schema inference & comparison | 436 LOC |
| **ExampleParser** | Pattern extraction from examples | 679 LOC |

---

## How Pattern Detection Works

### Step 1: Provide Examples

```python
from edgar_analyzer.models.project_config import ExampleConfig

examples = [
    ExampleConfig(
        input={"employee_id": "E1001", "first_name": "Alice", "last_name": "Johnson"},
        output={"id": "E1001", "full_name": "Alice Johnson"}
    ),
    ExampleConfig(
        input={"employee_id": "E1002", "first_name": "Bob", "last_name": "Smith"},
        output={"id": "E1002", "full_name": "Bob Smith"}
    )
]
```

### Step 2: Analyze Schemas

```python
from extract_transform_platform.services.analysis import SchemaAnalyzer

analyzer = SchemaAnalyzer()

# Infer input schema
input_schema = analyzer.infer_input_schema(examples)
# Fields: employee_id (STRING), first_name (STRING), last_name (STRING)

# Infer output schema
output_schema = analyzer.infer_output_schema(examples)
# Fields: id (STRING), full_name (STRING)

# Compare schemas
differences = analyzer.compare_schemas(input_schema, output_schema)
# Differences:
#   - Field rename: employee_id → id
#   - Field removed: first_name, last_name
#   - Field added: full_name
```

### Step 3: Extract Patterns

```python
from extract_transform_platform.services.analysis import ExampleParser

parser = ExampleParser(analyzer)
parsed = parser.parse_examples(examples)

# Detected patterns:
# 1. FIELD_MAPPING: employee_id → id (confidence: 1.0)
# 2. CONCATENATION: first_name + last_name → full_name (confidence: 1.0)
```

### Step 4: Generate Code

Patterns are passed to AI (Sonnet 4.5) for code generation:

```python
# Generated transformation code (simplified)
def transform(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": input_data["employee_id"],  # FIELD_MAPPING
        "full_name": f"{input_data['first_name']} {input_data['last_name']}"  # CONCATENATION
    }
```

---

## Pattern Types

### 1. FIELD_MAPPING

**Description**: Direct field mapping (rename or copy).

**Example**:
```python
# Input
{"employee_id": "E1001"}

# Output
{"id": "E1001"}

# Pattern
Pattern(
    type=PatternType.FIELD_MAPPING,
    source_path="employee_id",
    target_path="id",
    transformation="Direct field rename"
)
```

**Use Cases**:
- Field renaming
- Field copying
- Simple field transformations

**Detection**: Source value equals target value (exact match).

---

### 2. CONCATENATION

**Description**: Combine multiple fields into a single field.

**Example**:
```python
# Input
{"first_name": "Alice", "last_name": "Johnson"}

# Output
{"full_name": "Alice Johnson"}

# Pattern
Pattern(
    type=PatternType.CONCATENATION,
    source_path="first_name + last_name",
    target_path="full_name",
    transformation="Concatenate with space separator"
)
```

**Use Cases**:
- Full name from first + last
- Address from street + city + state
- Composite keys

**Detection**: Target value is concatenation of multiple source values.

---

### 3. TYPE_CONVERSION

**Description**: Convert field type (int ↔ float ↔ str ↔ bool).

**Example**:
```python
# Input
{"salary": 95000}  # int

# Output
{"annual_salary_usd": 95000.0}  # float

# Pattern
Pattern(
    type=PatternType.TYPE_CONVERSION,
    source_path="salary",
    target_path="annual_salary_usd",
    transformation="int → float"
)
```

**Use Cases**:
- int → float (precision requirements)
- str → int (parsing numbers)
- bool → str (display values)
- float → int (rounding)

**Detection**: Source and target types differ, but values are equivalent.

---

### 4. BOOLEAN_CONVERSION

**Description**: Normalize boolean representations.

**Example**:
```python
# Input
{"is_manager": "Yes"}

# Output
{"manager": true}

# Pattern
Pattern(
    type=PatternType.BOOLEAN_CONVERSION,
    source_path="is_manager",
    target_path="manager",
    transformation="'Yes'/'No' → true/false"
)
```

**Common Mappings**:
- `"Yes"/"No"` → `true/false`
- `"Y"/"N"` → `true/false`
- `"1"/"0"` → `true/false`
- `"True"/"False"` → `true/false`

**Detection**: Source is string boolean representation, target is boolean.

---

### 5. VALUE_MAPPING

**Description**: Map discrete values to other values.

**Example**:
```python
# Input
{"status_code": "A"}

# Output
{"status": "Active"}

# Pattern
Pattern(
    type=PatternType.VALUE_MAPPING,
    source_path="status_code",
    target_path="status",
    transformation="'A' → 'Active', 'I' → 'Inactive', 'P' → 'Pending'"
)
```

**Use Cases**:
- Status code expansions
- Category mappings
- Enumeration conversions

**Detection**: Discrete set of source values maps to discrete set of target values.

---

### 6. FIELD_EXTRACTION

**Description**: Extract substring or component from field.

**Example**:
```python
# Input
{"email": "alice@example.com"}

# Output
{"domain": "example.com"}

# Pattern
Pattern(
    type=PatternType.FIELD_EXTRACTION,
    source_path="email",
    target_path="domain",
    transformation="Extract domain from email"
)
```

**Use Cases**:
- Domain from email
- Area code from phone number
- Path component from URL
- First/last character extraction

**Detection**: Target value is substring of source value.

---

### 7. NESTED_ACCESS

**Description**: Access nested object field.

**Example**:
```python
# Input
{"address": {"city": "London", "country": "UK"}}

# Output
{"city": "London"}

# Pattern
Pattern(
    type=PatternType.NESTED_ACCESS,
    source_path="address.city",
    target_path="city",
    transformation="Extract nested field address.city"
)
```

**Use Cases**:
- Flatten nested structures
- Extract specific nested values
- Simplify complex objects

**Detection**: Source path contains dot notation, target is direct field.

---

### 8. LIST_AGGREGATION

**Description**: Aggregate list/array values.

**Example**:
```python
# Input
{"scores": [85, 90, 88]}

# Output
{"average_score": 87.67}

# Pattern
Pattern(
    type=PatternType.LIST_AGGREGATION,
    source_path="scores",
    target_path="average_score",
    transformation="Average of list values"
)
```

**Operations**:
- `sum()` - Sum of values
- `avg()` - Average of values
- `min()` - Minimum value
- `max()` - Maximum value
- `count()` - Number of items
- `join()` - Join strings

**Detection**: Source is array, target is scalar derived from array.

---

### 9. CONDITIONAL

**Description**: Conditional logic (if/else).

**Example**:
```python
# Input
{"age": 25}

# Output
{"adult": true}

# Pattern
Pattern(
    type=PatternType.CONDITIONAL,
    source_path="age",
    target_path="adult",
    transformation="age >= 18 → true, else false"
)
```

**Use Cases**:
- Age → adult/minor
- Temperature → hot/cold/warm
- Score → pass/fail
- Value → category

**Detection**: Target value depends on condition applied to source value.

---

### 10. DATE_PARSING

**Description**: Parse date/time from string.

**Example**:
```python
# Input
{"hire_date_str": "2020-03-15"}

# Output
{"hire_date": datetime(2020, 3, 15)}

# Pattern
Pattern(
    type=PatternType.DATE_PARSING,
    source_path="hire_date_str",
    target_path="hire_date",
    transformation="Parse ISO date string"
)
```

**Formats Supported**:
- ISO 8601: `2020-03-15T10:30:00Z`
- US format: `03/15/2020`
- EU format: `15.03.2020`
- Custom formats

**Detection**: Source is string matching date pattern, target is date/datetime.

---

### 11. MATH_OPERATION

**Description**: Mathematical operations.

**Example**:
```python
# Input
{"quantity": 10, "unit_price": 15.00}

# Output
{"total": 150.00}

# Pattern
Pattern(
    type=PatternType.MATH_OPERATION,
    source_path="quantity * unit_price",
    target_path="total",
    transformation="Multiplication"
)
```

**Operations**:
- `+` Addition
- `-` Subtraction
- `*` Multiplication
- `/` Division
- `%` Modulo
- `**` Exponentiation

**Detection**: Target value is mathematical result of source values.

---

### 12. STRING_FORMATTING

**Description**: Format strings with templates.

**Example**:
```python
# Input
{"first_name": "Alice", "last_name": "Johnson"}

# Output
{"display_name": "Johnson, Alice"}

# Pattern
Pattern(
    type=PatternType.STRING_FORMATTING,
    source_path="last_name + first_name",
    target_path="display_name",
    transformation="Format as 'Last, First'"
)
```

**Use Cases**:
- Name formatting
- Date formatting
- Number formatting
- Template filling

**Detection**: Target is formatted combination of source values.

---

### 13. DEFAULT_VALUE

**Description**: Use default value if field is null/missing.

**Example**:
```python
# Input
{"optional_field": None}

# Output
{"required_field": "N/A"}

# Pattern
Pattern(
    type=PatternType.DEFAULT_VALUE,
    source_path="optional_field",
    target_path="required_field",
    transformation="Use 'N/A' if null"
)
```

**Use Cases**:
- Handle missing data
- Provide fallback values
- Ensure required fields

**Detection**: Target has consistent value when source is null.

---

### 14. CUSTOM

**Description**: Custom transformation logic (catchall).

**Example**:
```python
# Input
{"complex_input": "ABC-123-XYZ"}

# Output
{"complex_output": "123"}

# Pattern
Pattern(
    type=PatternType.CUSTOM,
    source_path="complex_input",
    target_path="complex_output",
    transformation="Extract middle segment"
)
```

**Use Cases**:
- Complex transformations not fitting other patterns
- Domain-specific logic
- Multi-step transformations

**Detection**: Transformation doesn't match any other pattern type.

---

## Confidence Scoring

### Scoring Algorithm

```python
def calculate_confidence(pattern: Pattern, examples: List[Tuple]) -> float:
    """
    Confidence = (consistency * 0.6) + (type_compatibility * 0.2) + (complexity * 0.2)
    """

    # Consistency: Do all examples show the same pattern?
    consistency = count_matching_examples / total_examples

    # Type Compatibility: Do source/target types make sense?
    type_compatibility = 1.0 if types_compatible else 0.5

    # Complexity: Simpler patterns = higher confidence
    complexity = 1.0 / (pattern_complexity_score + 1)

    confidence = (consistency * 0.6) + (type_compatibility * 0.2) + (complexity * 0.2)
    return confidence
```

### Confidence Thresholds

| Range | Level | Meaning | Recommendation |
|-------|-------|---------|----------------|
| **≥0.9** | High | Pattern appears consistently in all examples | Use for code generation |
| **0.7-0.89** | Medium | Pattern appears in most examples | Review before using |
| **<0.7** | Low | Pattern is inconsistent or complex | Provide more examples |

### Example Confidence Scores

```python
# High confidence (1.0)
Pattern(
    type=PatternType.FIELD_MAPPING,
    confidence=1.0,  # All examples match, simple pattern
    source_path="employee_id",
    target_path="id"
)

# Medium confidence (0.8)
Pattern(
    type=PatternType.VALUE_MAPPING,
    confidence=0.8,  # 4/5 examples match, moderate complexity
    source_path="status_code",
    target_path="status"
)

# Low confidence (0.6)
Pattern(
    type=PatternType.CUSTOM,
    confidence=0.6,  # 3/5 examples match, high complexity
    source_path="complex_field",
    target_path="result"
)
```

---

## Best Practices

### 1. Provide Sufficient Examples

✅ **Good**: 2-3 representative examples
```python
examples = [
    # Example 1: Normal case
    ExampleConfig(input={"status": "A"}, output={"status_name": "Active"}),
    # Example 2: Another normal case
    ExampleConfig(input={"status": "I"}, output={"status_name": "Inactive"}),
    # Example 3: Edge case
    ExampleConfig(input={"status": "P"}, output={"status_name": "Pending"})
]
```

❌ **Bad**: Only 1 example
```python
examples = [
    ExampleConfig(input={"status": "A"}, output={"status_name": "Active"})
]
# Not enough data to infer pattern
```

### 2. Cover Edge Cases

✅ **Good**: Include null, empty, special values
```python
examples = [
    ExampleConfig(input={"name": "Alice"}, output={"display": "Alice"}),
    ExampleConfig(input={"name": ""}, output={"display": "N/A"}),  # Empty string
    ExampleConfig(input={"name": None}, output={"display": "N/A"})  # Null value
]
```

❌ **Bad**: Only happy path
```python
examples = [
    ExampleConfig(input={"name": "Alice"}, output={"display": "Alice"}),
    ExampleConfig(input={"name": "Bob"}, output={"display": "Bob"})
]
# Doesn't handle edge cases
```

### 3. Be Consistent

✅ **Good**: Same transformation in all examples
```python
examples = [
    ExampleConfig(input={"temp_f": 32}, output={"temp_c": 0.0}),
    ExampleConfig(input={"temp_f": 212}, output={"temp_c": 100.0}),
    ExampleConfig(input={"temp_f": 68}, output={"temp_c": 20.0})
]
# Clear pattern: (F - 32) * 5/9
```

❌ **Bad**: Inconsistent transformations
```python
examples = [
    ExampleConfig(input={"temp_f": 32}, output={"temp_c": 0.0}),
    ExampleConfig(input={"temp_f": 212}, output={"temp_c": "100"}),  # Wrong type
    ExampleConfig(input={"temp_f": 68}, output={"temp_c": 25.0})  # Wrong value
]
# Inconsistent pattern
```

### 4. Use Descriptive Field Names

✅ **Good**: Clear, descriptive names
```python
ExampleConfig(
    input={"employee_id": "E1001", "first_name": "Alice"},
    output={"id": "E1001", "full_name": "Alice Johnson"}
)
```

❌ **Bad**: Ambiguous names
```python
ExampleConfig(
    input={"a": "E1001", "b": "Alice"},
    output={"c": "E1001", "d": "Alice Johnson"}
)
```

---

## Examples

### Example 1: Employee Data Transform

**Source**:
```json
{
  "employee_id": "E1001",
  "first_name": "Alice",
  "last_name": "Johnson",
  "salary": 95000,
  "is_manager": "Yes",
  "hire_date": "2020-03-15"
}
```

**Target**:
```json
{
  "id": "E1001",
  "full_name": "Alice Johnson",
  "annual_salary_usd": 95000.0,
  "manager": true,
  "hired": "2020-03-15"
}
```

**Detected Patterns**:
1. **FIELD_MAPPING**: `employee_id` → `id` (confidence: 1.0)
2. **CONCATENATION**: `first_name + last_name` → `full_name` (confidence: 1.0)
3. **TYPE_CONVERSION**: `salary` (int) → `annual_salary_usd` (float) (confidence: 1.0)
4. **BOOLEAN_CONVERSION**: `is_manager` ("Yes") → `manager` (true) (confidence: 1.0)
5. **FIELD_MAPPING**: `hire_date` → `hired` (confidence: 1.0)

---

### Example 2: Weather API Transform

**Source**:
```json
{
  "name": "London",
  "main": {
    "temp": 15.5,
    "humidity": 72
  },
  "weather": [
    {"description": "partly cloudy"}
  ]
}
```

**Target**:
```json
{
  "city": "London",
  "temperature_c": 15.5,
  "humidity_pct": 72,
  "conditions": "partly cloudy"
}
```

**Detected Patterns**:
1. **FIELD_MAPPING**: `name` → `city` (confidence: 1.0)
2. **NESTED_ACCESS**: `main.temp` → `temperature_c` (confidence: 1.0)
3. **NESTED_ACCESS**: `main.humidity` → `humidity_pct` (confidence: 1.0)
4. **FIELD_EXTRACTION**: `weather[0].description` → `conditions` (confidence: 0.9)

---

### Example 3: Invoice Line Items

**Source**:
```json
{
  "Item": "Widget A",
  "Quantity": "2",
  "Unit Price": "$15.00",
  "Total": "$30.00"
}
```

**Target**:
```json
{
  "product": "Widget A",
  "qty": 2,
  "unit_price_usd": 15.00,
  "line_total_usd": 30.00
}
```

**Detected Patterns**:
1. **FIELD_MAPPING**: `Item` → `product` (confidence: 1.0)
2. **TYPE_CONVERSION**: `Quantity` (str) → `qty` (int) (confidence: 1.0)
3. **FIELD_EXTRACTION + TYPE_CONVERSION**: `Unit Price` ("$15.00") → `unit_price_usd` (15.00) (confidence: 0.9)
4. **FIELD_EXTRACTION + TYPE_CONVERSION**: `Total` ("$30.00") → `line_total_usd` (30.00) (confidence: 0.9)

---

## Next Steps

### Learn More

1. **Platform Usage Guide**: End-to-end examples
   - [Platform Usage Guide](PLATFORM_USAGE.md)

2. **Platform API Reference**: Detailed API documentation
   - [Platform API Reference](../api/PLATFORM_API.md)

3. **Schema Services**: Deep dive into components
   - [CLAUDE.md - Batch 2 Schema Services](../../CLAUDE.md#batch-2-schema-services-complete-)

### Try It Yourself

```bash
# Create example project
mkdir -p projects/my_transform/{input,examples,output}

# Add your source data
cp ~/Downloads/data.xlsx projects/my_transform/input/

# Create 2-3 transformation examples
# (See employee_roster POC for format)

# Run analysis and pattern detection
python -m edgar_analyzer analyze-project projects/my_transform/

# Review detected patterns
cat projects/my_transform/analysis_report.json

# Generate transformation code
python -m edgar_analyzer generate-code projects/my_transform/

# Run transformation
python -m edgar_analyzer run-extraction projects/my_transform/
```

---

## Summary

**Pattern Detection System**:
- ✅ 14 transformation pattern types
- ✅ Automatic pattern recognition from examples
- ✅ Confidence scoring (0.0-1.0)
- ✅ Schema-aware analysis
- ✅ Nested structure support

**Performance**:
- Schema Analysis: <100ms for 10 examples with 50 fields
- Pattern Detection: <500ms for 10 examples with 50 fields
- End-to-End: <10 seconds (read → analyze → generate → validate)

**Best Practices**:
1. Provide 2-3 representative examples
2. Cover edge cases (null, empty, special values)
3. Be consistent across examples
4. Use descriptive field names

**Need Help?** See [Platform Usage Guide](PLATFORM_USAGE.md) or [Platform API Reference](../api/PLATFORM_API.md)
