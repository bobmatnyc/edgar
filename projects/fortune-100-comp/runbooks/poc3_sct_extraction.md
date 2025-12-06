# POC 3: Summary Compensation Table Extraction

## Objective
Extract Named Executive Officer compensation data from DEF 14A Summary Compensation Tables using LLM-based parsing.

## Success Criteria
- [ ] Extract all NEOs (typically 5-7 per company per year)
- [ ] Parse all compensation components with <1% error rate
- [ ] Handle multi-year tables (most show 3 years)
- [ ] Validate totals match sum of components

## Dependencies
- **Requires**: POC 2 output (`def14a_filings.csv` + downloaded HTML files)

---

## Input Requirements

**Files**:
- `def14a_filings.csv` - Filing metadata
- `filings/def14a/{cik}_{fiscal_year}_def14a.html` - Raw HTML files

---

## Expected Output

**File**: `neo_compensation_sct.csv`

| Column | Type | Example |
|--------|------|---------|
| cik | str | 0000104169 |
| fiscal_year | int | 2023 |
| executive_name | str | C. Douglas McMillon |
| executive_title | str | President and CEO |
| is_ceo | bool | True |
| is_cfo | bool | False |
| salary | int | 1425000 |
| bonus | int | 0 |
| stock_awards | int | 16742845 |
| option_awards | int | 0 |
| non_equity_incentive | int | 9063576 |
| pension_change | int | 0 |
| other_comp | int | 529734 |
| total | int | 27761155 |
| calculated_total | int | 27761155 |
| total_diff | int | 0 |
| extraction_confidence | float | 0.95 |

---

## Step 1: Preprocess HTML

### Extract Compensation Section

```python
from bs4 import BeautifulSoup
import re

def extract_compensation_section(html_content: str) -> str:
    """
    Extract the executive compensation section from full proxy.
    Reduces token count for LLM processing.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find Summary Compensation Table by heading or caption
    markers = [
        'summary compensation table',
        'executive compensation',
        'compensation of named executive officers',
    ]
    
    # Strategy 1: Find by heading
    for marker in markers:
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'b', 'strong'])
        for heading in headings:
            if marker in heading.get_text().lower():
                # Get the next table after this heading
                section = extract_section_after(heading, max_tables=3)
                if section:
                    return section
    
    # Strategy 2: Find table with "Salary" and "Stock Awards" columns
    tables = soup.find_all('table')
    for table in tables:
        text = table.get_text().lower()
        if 'salary' in text and 'stock awards' in text and 'total' in text:
            return str(table)
    
    return html_content  # Fallback: return full content

def extract_section_after(element, max_tables: int = 3) -> str:
    """
    Extract content from element until we've captured max_tables.
    """
    content = []
    tables_found = 0
    
    for sibling in element.find_next_siblings():
        content.append(str(sibling))
        if sibling.name == 'table':
            tables_found += 1
            if tables_found >= max_tables:
                break
    
    return '\n'.join(content)
```

### Convert Table to Markdown (Optional)

```python
import pandas as pd

def html_table_to_markdown(html_table: str) -> str:
    """
    Convert HTML table to markdown for cleaner LLM input.
    Preserves structure while reducing tokens.
    """
    try:
        dfs = pd.read_html(html_table)
        if dfs:
            return dfs[0].to_markdown(index=False)
    except:
        pass
    return html_table
```

---

## Step 2: LLM Extraction

### System Prompt

```
You are an expert SEC filing analyst specializing in executive compensation disclosures.

Your task is to extract data from Summary Compensation Tables in DEF 14A proxy statements.

EXTRACTION RULES:
1. Extract ALL Named Executive Officers shown in the table
2. Extract ALL years shown (usually 3 fiscal years)
3. Convert all dollar amounts to integers (no commas, no $ signs)
4. Replace dashes, blanks, "—", "N/A", or empty cells with 0
5. If a value shows "(123,456)" with parentheses, it's negative: -123456
6. Identify the CEO (Principal Executive Officer) and CFO (Principal Financial Officer)

COLUMN MAPPING:
- "Salary" → salary
- "Bonus" → bonus  
- "Stock Awards" → stock_awards
- "Option Awards" → option_awards
- "Non-Equity Incentive Plan Compensation" → non_equity_incentive
- "Change in Pension Value and Nonqualified Deferred Compensation Earnings" → pension_change
- "All Other Compensation" → other_comp
- "Total" → total

OUTPUT FORMAT:
Return a JSON array of objects, one per executive per year.
```

### User Prompt Template

```python
def build_extraction_prompt(company_name: str, html_section: str) -> str:
    return f"""
Extract the Summary Compensation Table data for {company_name}.

DOCUMENT SECTION:
{html_section}

Return a JSON array with this structure:
[
  {{
    "fiscal_year": 2023,
    "executive_name": "Full Name",
    "executive_title": "Title as shown",
    "is_ceo": true,
    "is_cfo": false,
    "salary": 1500000,
    "bonus": 0,
    "stock_awards": 12000000,
    "option_awards": 0,
    "non_equity_incentive": 3500000,
    "pension_change": 0,
    "other_comp": 250000,
    "total": 17250000
  }},
  ...
]

Extract ALL executives and ALL years shown. Return ONLY valid JSON, no explanation.
"""
```

### LLM Call Pattern

```python
def extract_sct_with_llm(html_section: str, company_name: str, model: str = "claude-3-5-sonnet") -> list[dict]:
    """
    Call LLM to extract Summary Compensation Table data.
    
    Returns list of compensation records.
    """
    import anthropic
    
    client = anthropic.Anthropic()
    
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_extraction_prompt(company_name, html_section)}
        ]
    )
    
    # Parse JSON response
    response_text = message.content[0].text
    
    # Handle potential markdown code blocks
    if '```json' in response_text:
        response_text = response_text.split('```json')[1].split('```')[0]
    elif '```' in response_text:
        response_text = response_text.split('```')[1].split('```')[0]
    
    return json.loads(response_text)
```

---

## Step 3: Post-Extraction Validation

### Arithmetic Validation

```python
def validate_sct_record(record: dict) -> dict:
    """
    Validate a single SCT record and add calculated fields.
    """
    # Calculate expected total
    calculated = (
        record['salary'] +
        record['bonus'] +
        record['stock_awards'] +
        record['option_awards'] +
        record['non_equity_incentive'] +
        record['pension_change'] +
        record['other_comp']
    )
    
    record['calculated_total'] = calculated
    record['total_diff'] = abs(record['total'] - calculated)
    
    # Flag if difference exceeds threshold (allow for rounding)
    if record['total_diff'] > 1000:
        record['validation_warning'] = f"Total mismatch: reported {record['total']} vs calculated {calculated}"
    
    return record
```

### Cross-Reference Validation

```python
def validate_ceo_presence(records: list[dict], fiscal_year: int) -> bool:
    """
    Verify at least one CEO is present for the fiscal year.
    """
    ceos = [r for r in records if r['fiscal_year'] == fiscal_year and r['is_ceo']]
    return len(ceos) >= 1

def validate_reasonable_ranges(record: dict) -> list[str]:
    """
    Check for unreasonable values that may indicate extraction errors.
    """
    warnings = []
    
    # CEO salary typically $1M-$2M for Fortune 100
    if record['is_ceo'] and record['salary'] < 500000:
        warnings.append(f"CEO salary {record['salary']} seems low")
    
    # Total comp typically $5M-$100M for Fortune 100 CEO
    if record['is_ceo'] and record['total'] < 1000000:
        warnings.append(f"CEO total {record['total']} seems low for Fortune 100")
    
    if record['total'] > 500000000:
        warnings.append(f"Total {record['total']} exceeds $500M - verify")
    
    # Negative values only valid for pension_change
    for field in ['salary', 'bonus', 'stock_awards', 'option_awards', 
                  'non_equity_incentive', 'other_comp']:
        if record[field] < 0:
            warnings.append(f"{field} is negative: {record[field]}")
    
    return warnings
```

---

## Test Cases

### Manual Verification Set

Extract and manually verify against source filing:

| Company | CIK | FY | CEO Name | CEO Total (Expected) |
|---------|-----|-----|----------|---------------------|
| Walmart | 0000104169 | 2023 | C. Douglas McMillon | ~$27.7M |
| Apple | 0000320193 | 2023 | Timothy D. Cook | ~$63.2M |
| Amazon | 0001018724 | 2023 | Andrew R. Jassy | ~$29.2M |
| JPMorgan | 0000019617 | 2023 | James Dimon | ~$36.0M |
| Microsoft | 0000789019 | 2023 | Satya Nadella | ~$48.5M |

### Automated Checks

```python
def run_extraction_tests(sample_filings: list[str]) -> dict:
    """
    Run automated extraction tests on sample filings.
    """
    results = {
        'total_filings': len(sample_filings),
        'successful_extractions': 0,
        'failed_extractions': 0,
        'total_records': 0,
        'records_with_warnings': 0,
        'arithmetic_failures': 0,
    }
    
    for filing in sample_filings:
        try:
            records = extract_sct_with_llm(filing['html'], filing['company'])
            results['successful_extractions'] += 1
            results['total_records'] += len(records)
            
            for record in records:
                validated = validate_sct_record(record)
                if validated.get('validation_warning'):
                    results['records_with_warnings'] += 1
                if validated['total_diff'] > 1000:
                    results['arithmetic_failures'] += 1
                    
        except Exception as e:
            results['failed_extractions'] += 1
            
    return results
```

---

## Expected Extraction Challenges

| Challenge | Example | Mitigation |
|-----------|---------|------------|
| Split columns | "Non-Equity\nIncentive Plan\nCompensation" | LLM handles line breaks |
| Footnote markers | "1,234,567(1)" | Strip footnote refs before parsing |
| Multiple tables | SCT + SCT footnotes | Extract main table only |
| Year range varies | Some show 2 years, some 3 | Handle variable year count |
| Name variations | "Mr. Smith" vs "John Smith" | Normalize names |
| Role changes | CFO promoted to CEO mid-year | May appear twice |
| Departed executives | Former CEO with partial year | Include with flag |

---

## Token Budget Estimation

| Component | Estimated Tokens |
|-----------|-----------------|
| System prompt | ~500 |
| Extracted HTML section | ~3,000-10,000 |
| Response | ~1,000-2,000 |
| **Per extraction** | ~5,000-12,000 |
| **500 filings total** | ~2.5M-6M tokens |

Consider using `claude-3-haiku` for initial extraction with `claude-3-5-sonnet` for validation failures.

---

## Output Files

1. **`neo_compensation_sct.csv`** - Primary output with all extracted records
2. **`sct_extraction_log.csv`** - Extraction metadata (success/fail, token usage, timing)
3. **`sct_validation_warnings.csv`** - Records flagged for manual review

---

## Quality Metrics

Target metrics for POC success:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Extraction success rate | ≥98% | Filings with ≥1 record extracted |
| Arithmetic accuracy | ≥95% | Records where total_diff ≤ $1000 |
| CEO identification | 100% | At least 1 CEO per company-year |
| Record completeness | ≥99% | Records with all fields populated |

---

## Estimated Runtime

- HTML preprocessing: ~0.5 seconds per file
- LLM extraction: ~3-5 seconds per file (API call)
- Validation: ~0.1 seconds per record
- **Total for 500 filings**: ~1-2 hours
