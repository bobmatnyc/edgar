# Data Validators for Recipe System

This directory contains data validators for validating extraction results from the recipe system.

## Available Validators

### SCT Validator (`sct_validator.py`)

Validates Summary Compensation Table extraction results.

**Usage:**
```python
from edgar_analyzer.validators import validate_sct_data

result = validate_sct_data(sct_data)
print(result["stats"])
```

**Input Format:**
```python
sct_data = [
    {
        "company": "Apple Inc.",
        "cik": "0000320193",
        "filing_date": "2024-01-15",
        "executives": [
            {
                "name": "Tim Cook",
                "title": "CEO",
                "compensation": [
                    {"year": 2023, "total": 63209845.0, ...}
                ]
            }
        ]
    }
]
```

**Validation Rules:**
- ✅ Must have `company` and `cik` fields (both required)
- ✅ `executives` list should have at least 1 entry
- ✅ Each executive should have `name` and `compensation` list
- ⚠️ Warnings logged for missing fields, but partial data included

**Return Value:**
```python
{
    "validated_data": [...],  # List of valid records (includes partial)
    "validation_errors": [
        {
            "record_index": 0,
            "company": "Apple Inc.",
            "cik": "0000320193",
            "errors": ["Missing field: ..."],
            "severity": "warning" | "error"
        }
    ],
    "stats": {
        "total_records": 10,
        "valid_records": 8,
        "partial_records": 1,
        "invalid_records": 1,
        "total_executives": 50,
        "total_compensation_years": 150
    }
}
```

### Tax Validator (`tax_validator.py`)

Validates income tax extraction results.

**Usage:**
```python
from edgar_analyzer.validators import validate_tax_data

result = validate_tax_data(tax_data)
print(result["stats"])
```

**Input Format:**
```python
tax_data = [
    {
        "company": "Apple Inc.",
        "cik": "0000320193",
        "filing_date": "2024-02-15",
        "fiscal_year_end": "2023-09-30",
        "tax_years": [
            {
                "year": 2023,
                "current_federal": 10500000000.0,
                "total_tax_expense": 15500000000.0,
                ...
            }
        ]
    }
]
```

**Validation Rules:**
- ✅ Must have `company` and `cik` fields (both required)
- ✅ `tax_years` list should have at least 1 entry
- ✅ Each tax year should have `year` and `total_tax_expense`
- ⚠️ Warnings logged for missing fields, but partial data included

**Return Value:**
```python
{
    "validated_data": [...],  # List of valid records (includes partial)
    "validation_errors": [
        {
            "record_index": 0,
            "company": "Apple Inc.",
            "cik": "0000320193",
            "errors": ["Missing field: ..."],
            "severity": "warning" | "error"
        }
    ],
    "stats": {
        "total_records": 10,
        "valid_records": 8,
        "partial_records": 1,
        "invalid_records": 1,
        "total_tax_years": 30,
        "total_tax_expense_sum": 450000000000.0
    }
}
```

## Design Principles

### Lenient Validation
Both validators follow a **lenient validation** approach:
- Include data even if partially valid
- Flag issues in `validation_errors` list
- Only exclude records with severe errors (missing both company AND cik)

### Error Severity Levels
- **`valid`**: No issues, all required fields present
- **`partial`**: Some warnings, but data is usable (included in output)
- **`invalid`**: Severe errors, data excluded from output

### Logging
All validators use `structlog` for structured logging:
- `INFO`: Overall validation start/complete
- `WARNING`: Partial records with issues
- No logging suppression (follows project logging config)

## Integration with Recipe System

Validators are designed to be used in recipe steps:

```yaml
steps:
  - name: extract_sct
    type: extractor
    extractor:
      extractor: SCTAdapter
      filing_type: "DEF 14A"
    inputs:
      filings: $steps.fetch_filings.filings
    outputs:
      - sct_data

  - name: validate_sct
    type: python
    inputs:
      sct_data: $steps.extract_sct.sct_data
    outputs:
      - validated_data
      - validation_errors
      - stats
    function: |
      from edgar_analyzer.validators import validate_sct_data
      return validate_sct_data(inputs["sct_data"])
```

## Testing

Run the validators with test data:

```python
from edgar_analyzer.validators import validate_sct_data, validate_tax_data

# Test with sample data
sct_result = validate_sct_data([
    {
        "company": "Apple Inc.",
        "cik": "0000320193",
        "executives": [{"name": "Tim Cook", "compensation": []}]
    }
])

print(f"Valid records: {sct_result['stats']['valid_records']}")
```

## Code Validators vs Data Validators

This directory contains two types of validators:

1. **Code Validators** (existing): Validate generated Python code
   - `ComplexityValidator`, `TypeHintValidator`, etc.
   - Check code against architectural constraints

2. **Data Validators** (new): Validate extracted data
   - `validate_sct_data`, `validate_tax_data`
   - Validate recipe extraction results

Both serve the quality assurance goals of the project but at different levels.
