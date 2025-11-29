# Employee Roster Extraction - Proof of Concept

This project demonstrates end-to-end Excel file transformation using the EDGAR platform's example-driven approach.

## Overview

Transforms HR roster data from Excel format into structured employee records with:
- Field renaming (employee_id → id, department → dept)
- String concatenation (first_name + last_name → full_name)
- Type conversions (salary → float, is_manager → boolean)
- Date preservation (hire_date → hired)

## Source Data

**File**: `input/hr_roster.xlsx`

| Column | Type | Description |
|--------|------|-------------|
| employee_id | string | Unique employee identifier (E####) |
| first_name | string | Employee first name |
| last_name | string | Employee last name |
| department | string | Department name |
| hire_date | date | Date of hire (YYYY-MM-DD) |
| salary | integer | Annual salary in USD |
| is_manager | string | Manager status (Yes/No) |

## Transformations

1. **Field Rename**: `employee_id` → `id`
2. **String Concatenation**: `first_name` + `last_name` → `full_name`
3. **Field Rename**: `department` → `dept`
4. **Field Rename**: `hire_date` → `hired`
5. **Type Conversion**: `salary` (int) → `annual_salary_usd` (float)
6. **Boolean Conversion**: `is_manager` (Yes/No) → `manager` (true/false)

## Example Outputs

### Alice Johnson (E1001)
```json
{
  "id": "E1001",
  "full_name": "Alice Johnson",
  "dept": "Engineering",
  "hired": "2020-03-15",
  "annual_salary_usd": 95000.0,
  "manager": true
}
```

### Bob Smith (E1002)
```json
{
  "id": "E1002",
  "full_name": "Bob Smith",
  "dept": "Marketing",
  "hired": "2019-07-22",
  "annual_salary_usd": 78000.0,
  "manager": false
}
```

### Carol Davis (E1003)
```json
{
  "id": "E1003",
  "full_name": "Carol Davis",
  "dept": "Engineering",
  "hired": "2021-01-10",
  "annual_salary_usd": 85000.0,
  "manager": true
}
```

## Usage

```bash
# Analyze examples and generate extraction code
python -m edgar_analyzer extract-project projects/employee_roster/

# Run extraction on Excel file
python -m edgar_analyzer run-extraction projects/employee_roster/output/extract.py
```

## Success Criteria

- ✅ ExcelDataSource reads hr_roster.xlsx successfully
- ✅ Schema analyzer infers correct transformations from examples
- ✅ Generated code produces correct output for all 3 employees
- ✅ All transformations match example outputs exactly

## Project Structure

```
projects/employee_roster/
├── project.yaml          # Project configuration
├── input/
│   └── hr_roster.xlsx   # Source Excel file (3 employees)
├── examples/
│   ├── alice.json       # Example: E1001 transformation
│   ├── bob.json         # Example: E1002 transformation
│   └── carol.json       # Example: E1003 transformation
├── output/
│   └── (generated code) # Auto-generated extraction code
└── README.md            # This file
```

## Notes

- This POC demonstrates Phase 2 File Transform work path
- Uses example-driven approach (same pattern as Weather API)
- Validates ExcelDataSource integration with schema analyzer
- Proves general-purpose platform viability

## Transformation Details

### Field Renaming
- **employee_id → id**: Shorter, more generic identifier
- **department → dept**: Abbreviated field name
- **hire_date → hired**: Simplified field name

### String Concatenation
- **first_name + last_name → full_name**: Combines two fields with space separator
- Example: "Alice" + "Johnson" → "Alice Johnson"

### Type Conversions
- **salary (int) → annual_salary_usd (float)**: Explicit type and currency
- Example: 95000 → 95000.0

### Boolean Conversion
- **is_manager (Yes/No) → manager (true/false)**: Standard boolean representation
- Mapping: "Yes" → true, "No" → false

## Data Quality

All source data is clean and well-formed:
- No missing values
- Consistent date format (YYYY-MM-DD)
- Valid employee IDs (E####)
- Boolean values are consistent (Yes/No)

## Future Enhancements

Potential extensions for this POC:
- Handle missing values (null/empty fields)
- Date format conversions
- Validation rules (salary > 0, valid departments)
- Computed fields (tenure calculation)
- Aggregations (department summaries)
