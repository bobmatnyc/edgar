# Extractor Code Templates

This directory contains Jinja2 templates for generating domain-specific data extractors.

## Overview

The Meta-Extractor system uses these templates to generate complete, production-ready extractor implementations from domain-specific configuration. The templates are parameterized to support any extraction domain (compensation tables, financial statements, regulatory disclosures, etc.).

## Template Architecture

```
templates/extractors/
├── base_extractor.py.j2    # Main extractor class (~200 LOC)
├── data_models.py.j2        # Pydantic models (~100 LOC)
├── prompt_template.j2       # LLM prompts (~100 LOC)
├── test_extractor.py.j2     # pytest tests (~150 LOC)
└── __init__.py.j2           # Package initialization
```

## Template Variables Reference

### base_extractor.py.j2

**Required Variables:**
- `extractor_name` (str): Class name (e.g., "SCTExtractor", "BalanceSheetExtractor")
- `extractor_description` (str): Brief description for docstring
- `domain` (str): Domain slug for logging/file naming (e.g., "sct", "balance_sheet")
- `data_model_import` (str): Import statement for Pydantic model
- `data_model_class` (str): Name of main data model class
- `result_class` (str): Name of result wrapper class

**Configuration Variables:**
- `rate_limit_delay` (float): SEC EDGAR rate limit delay in seconds (default: 0.15)
- `context_chars` (int): Characters before/after table for context (default: 1000)
- `max_html_size` (int): Maximum HTML size to send to LLM (default: 100000)

**Pattern Analysis Variables (from PatternAnalysis):**
- `heading_patterns` (list[str]): Regex patterns for section headings
- `table_validation_rules` (dict): Table validation configuration
  - `required_columns` (list[str]): Column keywords that must be present
  - `reject_patterns` (list[str]): Patterns indicating wrong table type

**LLM Configuration:**
- `llm_temperature` (float): Temperature for extraction (default: 0.1)
- `llm_max_tokens` (int): Max tokens to generate (default: 8000)
- `system_prompt` (str): System prompt for LLM

**Example:**
```python
{
    "extractor_name": "SCTExtractor",
    "extractor_description": "Summary Compensation Table extractor",
    "domain": "sct",
    "data_model_import": "from ..models.sct_models import SCTData",
    "data_model_class": "SCTData",
    "result_class": "SCTExtractionResult",

    "rate_limit_delay": 0.15,
    "context_chars": 1000,
    "max_html_size": 100000,

    "heading_patterns": [
        r"Summary Compensation Table",
        r"SUMMARY COMPENSATION TABLE"
    ],
    "table_validation_rules": {
        "required_columns": ["name", "year", "salary"],
        "reject_patterns": ["grant date", "fees earned"]
    },

    "llm_temperature": 0.1,
    "llm_max_tokens": 8000,
    "system_prompt": "You are an expert at extracting structured data from SEC filings."
}
```

### data_models.py.j2

**Required Variables:**
- `domain` (str): Domain slug for module naming
- `models` (list[dict]): List of Pydantic model definitions

**Model Structure:**
```python
{
    "name": "ExecutiveCompensation",
    "description": "Named Executive Officer compensation data",
    "fields": [
        {
            "name": "name",
            "type": "str",
            "description": "Executive full name",
            "required": True,
            "default": None
        },
        {
            "name": "salary",
            "type": "int",
            "description": "Base salary ($)",
            "required": False,
            "default": 0,
            "ge": 0  # Pydantic constraint
        }
    ],
    "validators": [
        {
            "name": "validate_total",
            "field": "total",
            "code": "# Custom validation logic"
        }
    ],
    "is_main_model": False  # Set True for top-level model
}
```

### prompt_template.j2

**Required Variables:**
- `domain` (str): Domain slug
- `task_description` (str): What data to extract
- `parsing_rules` (list[str]): List of parsing rules/guidelines
- `example_input` (str): Example HTML/text input
- `example_output` (dict): Example JSON output
- `json_schema` (dict): Expected JSON structure

**Example:**
```python
{
    "domain": "sct",
    "task_description": "Extract executive compensation data from Summary Compensation Table",
    "parsing_rules": [
        "Convert currency strings to integers (remove $, commas)",
        "Empty cells (&#160;) should be 0",
        "Rowspan handling: name applies to next N rows"
    ],
    "example_input": "<tr><td>Tim Cook</td><td>3,000,000</td></tr>",
    "example_output": {"name": "Tim Cook", "salary": 3000000},
    "json_schema": {
        "executives": [
            {
                "name": "string",
                "salary": "integer"
            }
        ]
    }
}
```

### test_extractor.py.j2

**Required Variables:**
- `extractor_name` (str): Name of extractor class
- `domain` (str): Domain slug
- `test_fixtures` (list[dict]): Test data fixtures
- `expected_outputs` (list[dict]): Expected extraction results

**Test Fixture Structure:**
```python
{
    "name": "test_apple_sct_extraction",
    "fixture_data": {
        "filing_url": "https://www.sec.gov/...",
        "cik": "0000320193",
        "company_name": "Apple Inc.",
        "ticker": "AAPL"
    },
    "expected": {
        "success": True,
        "executives_count": 5,
        "fiscal_years": [2024, 2023, 2022]
    }
}
```

## Usage Example

### 1. Render Templates with Jinja2

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Setup Jinja2 environment
template_dir = Path("templates/extractors")
env = Environment(loader=FileSystemLoader(str(template_dir)))

# Load template
template = env.get_template("base_extractor.py.j2")

# Render with variables
output = template.render(
    extractor_name="SCTExtractor",
    domain="sct",
    heading_patterns=[r"Summary Compensation Table"],
    # ... other variables
)

# Write generated code
output_file = Path(f"src/generated/extractors/{domain}_extractor.py")
output_file.write_text(output)
```

### 2. Generated Code Structure

```
src/generated/extractors/
├── __init__.py              # Package initialization
├── sct_extractor.py         # Main extractor class
├── sct_models.py            # Pydantic models
├── sct_prompts.py           # LLM prompt templates
└── tests/
    └── test_sct_extractor.py
```

### 3. Integration with Meta-Extractor

The Meta-Extractor will:
1. Analyze example filings to extract patterns
2. Build template variables from pattern analysis
3. Render all templates with domain-specific values
4. Write generated code to output directory
5. Run tests to validate generated extractors

## Template Design Principles

### 1. Generic Infrastructure (65%)
Templates handle common extraction logic:
- SEC EDGAR rate limiting
- HTML fetching with User-Agent
- Retry logic with exponential backoff
- Logging with structlog
- Error handling and result wrapping

### 2. Domain-Specific Parameterization (35%)
Variables control domain-specific behavior:
- Heading search patterns
- Table validation logic
- Context extraction parameters
- Prompt building

### 3. Code Quality Standards
Generated code must:
- Pass black/isort/mypy linters
- Follow PEP 8 style guide
- Include comprehensive docstrings
- Have 80%+ test coverage

## Maintenance

### Adding New Template Variables
1. Update template files with new Jinja2 tags
2. Document variable in this README
3. Update example configurations
4. Test rendering with new variables

### Template Testing
```bash
# Test template rendering
python tests/test_template_rendering.py

# Validate generated code
black --check templates/extractors/*.j2.output
mypy templates/extractors/*.j2.output
```

## Reference Implementation

The SCT extractor (`src/edgar_analyzer/services/sct_extractor_service.py`) is the reference implementation that informed these templates. Use it as a guide for:
- Code structure and organization
- Error handling patterns
- Logging best practices
- HTML parsing strategies
- LLM prompt engineering

## Version History

- **v1.0.0** (2025-12-07): Initial template infrastructure for Meta-Extractor POC Phase 1
  - base_extractor.py.j2
  - data_models.py.j2
  - prompt_template.j2
  - test_extractor.py.j2
  - __init__.py.j2
