"""
LLM extraction prompt template for patent data.

This module contains the prompt template used to instruct Claude Sonnet 4.5
on how to extract structured patent data from SEC filings.

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
    Build LLM prompt for patent extraction with clear structure.

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
        "abstract": "str",
        "assignee": "str",
        "claims_count": "int",
        "filing_date": "str",
        "grant_date": "str",
        "patent_number": "str",
        "status": "str",
        "title": "str",
    }

    schema_json = json.dumps(schema, indent=2)

    # Concrete example
    example_input = """<html>...</html>"""

    example_output = {
        "abstract": "example_value",
        "assignee": "example_value",
        "claims_count": "example_value",
        "filing_date": "example_value",
        "grant_date": "example_value",
        "patent_number": "example_value",
        "status": "example_value",
        "title": "example_value",
    }

    example_json = json.dumps(example_output, indent=2)

    prompt = f"""# Task: Extract Extract patent filing information from Google Patents API responses

## Company Information
- **Name**: {company_name}
- **CIK**: {cik}
- **Ticker**: {ticker or 'UNKNOWN'}

## Your Task
Extract patent data from the provided HTML.

## Critical Parsing Rules


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
See patterns detected during analysis.

## JSON Schema

Return JSON matching this structure:

```json
{schema_json}
```

## HTML Content to Extract

{section_html}

## Output Requirements

**CRITICAL**:
1. Return ONLY valid JSON (no markdown code fences)
2. Extract ALL relevant data from the input
3. Use proper JSON syntax: double quotes, lowercase booleans

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
