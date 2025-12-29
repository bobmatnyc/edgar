"""
LLM extraction prompt template for sct data.

This module contains the prompt template used to instruct Claude Sonnet 4.5
on how to extract structured sct data from SEC filings.

Design Decisions:
- **Explicit Examples**: Show concrete input/output pairs
- **Parsing Rules**: Clear instructions for edge cases
- **JSON Schema**: Define expected structure precisely
- **Error Prevention**: Address common LLM mistakes

Usage:
    >>> prompt = build_prompt(
    ...     section_html="<html>...</html>",
    ...     company_name="Apple Inc.",
    ...     cik="0000320193",
    ...     ticker="AAPL"
    ... )
"""

import json
from typing import Optional


def build_extraction_prompt(
    section_html: str,
    company_name: str,
    cik: str,
    ticker: Optional[str] = None,
) -> str:
    """
    Build LLM prompt for sct extraction with clear structure.

    Args:
        section_html: Extracted section HTML
        company_name: Company name
        cik: CIK number
        ticker: Stock ticker (optional)

    Returns:
        Complete prompt text
    """
    # Define JSON schema with type annotations
    schema = {
        "cik": "string (10 digits)",
        "company_name": "string",
        "executives": [
            {
                "compensation_by_year": [
                    {
                        "bonus": "integer",
                        "salary": "integer",
                        "stock_awards": "integer",
                        "total": "integer",
                        "year": "integer",
                    }
                ],
                "is_ceo": "boolean",
                "name": "string",
                "position": "string",
            }
        ],
        "ticker": "string (1-5 uppercase letters)",
    }

    schema_json = json.dumps(schema, indent=2)

    # Concrete example
    example_input = """<tr>
  <td rowspan="3"><b>Tim Cook</b><br/>CEO</td>
  <td>2024</td><td>3,000,000</td><td>58,088,946</td><td>74,609,802</td>
</tr>"""

    example_output = {
        "compensation_by_year": [
            {
                "bonus": 0,
                "salary": 3000000,
                "stock_awards": 58088946,
                "total": 74609802,
                "year": 2024,
            }
        ],
        "is_ceo": true,
        "name": "Tim Cook",
        "position": "Chief Executive Officer",
    }

    example_json = json.dumps(example_output, indent=2)

    prompt = f"""# Task: Extract Extract executive compensation data from Summary Compensation Table

## Company Information
- **Name**: {company_name}
- **CIK**: {cik}
- **Ticker**: {ticker or 'UNKNOWN'}

## Your Task
Extract executive compensation data from the Summary Compensation Table (SCT) in the HTML below.

The SCT typically contains:
- **5 Named Executive Officers (NEOs)**
- **3 fiscal years** of data per executive
- Standard compensation columns: Salary, Stock Awards, Total

## Critical Parsing Rules


### 1. Rowspan Handling (IMPORTANT!)
When you see `rowspan="3"` on a name/position cell:
- That executive name applies to the **next 3 rows**
- Each row is a different fiscal year (e.g., 2024, 2023, 2022)
- Extract all 3 years as separate entries in `compensation_by_year` array


**Examples:**

- rowspan="3" means name applies to next 3 rows

- Each row is a separate fiscal year entry



### 2. Empty Cells
- Cells containing only `&#160;`, `&nbsp;`, or whitespace = **$0**
- Missing columns (e.g., no "Bonus" column) = **default to 0**


### 3. Currency Conversion
- Convert `"3,000,000"` to integer `3000000`
- Remove commas, dollar signs, decimals
- All monetary values must be integers



## Example Extraction

**Input HTML:**
```html
{example_input}
```

**Output JSON:**
```json
{example_json}
```


**Explanation:**
- `rowspan="3"` means Tim Cook appears in next 3 rows (2024, 2023, 2022)
- Empty cells = $0 for Bonus
- Position "Chief Executive Officer" → `is_ceo: true`


## JSON Schema

Return JSON matching this structure:

```json
{schema_json}
```

## HTML Content to Extract

{section_html}

## Output Requirements

**CRITICAL**:

1. Return **ONLY** valid JSON (no markdown code fences, no explanations)

2. Extract **ALL executives** from the table (typically 5)

3. Each executive must have **1-3 years** of compensation data

4. Use proper JSON syntax: double quotes, lowercase booleans (`true`/`false`)


Extract the data now.
"""

    return prompt


# Alternative: Pre-built prompt templates for common scenarios
PROMPT_TEMPLATES = {
    "standard": build_extraction_prompt,
    # Add more variations as needed
}


def get_prompt_template(template_name: str = "standard"):
    """
    Get a specific prompt template by name.

    Args:
        template_name: Name of template to retrieve

    Returns:
        Prompt building function

    Example:
        >>> builder = get_prompt_template("standard")
        >>> prompt = builder(section_html="...", company_name="Apple Inc.", ...)
    """
    return PROMPT_TEMPLATES.get(template_name, build_extraction_prompt)
