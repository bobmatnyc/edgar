# POC 6: Cash Taxes Paid - LLM Fallback Extraction

## Objective
Extract cash taxes paid from 10-K filings using LLM-based parsing when XBRL extraction (POC 5) fails or returns incomplete data.

## Success Criteria
- [ ] Successfully extract tax data for ≥90% of fallback cases
- [ ] Identify correct line item in cash flow supplemental disclosure
- [ ] Handle various formatting styles and units
- [ ] Cross-validate against any available XBRL data

## Dependencies
- **Requires**: POC 5 output (`xbrl_fallback_required.csv`)
- **Requires**: POC 1 output (`fortune100_universe.csv`)

---

## When to Use This POC

Run this POC for company-years flagged in POC 5:
- `extraction_status = 'XBRL_MISSING'`
- `fallback_required = True`

Common reasons for XBRL gaps:
1. Older filings (pre-2020 may have incomplete XBRL)
2. Non-standard element usage
3. Data only in footnotes, not tagged
4. Filing amendments not fully tagged

---

## Input Requirements

**File**: `xbrl_fallback_required.csv` from POC 5

| Column | Type |
|--------|------|
| cik | str |
| company_name | str |
| fiscal_year | int |
| fallback_required | bool |

---

## Expected Output

**File**: `cash_taxes_llm.csv`

| Column | Type | Example |
|--------|------|---------|
| cik | str | 0000104169 |
| company_name | str | Walmart |
| fiscal_year | int | 2020 |
| cash_taxes_paid | int | 4850000000 |
| is_net_of_refunds | bool | True |
| source_location | str | Cash Flow Supplemental |
| unit_reported | str | millions |
| extraction_confidence | float | 0.92 |
| raw_text_extracted | str | "$4,850 million" |

---

## Step 1: Retrieve 10-K Filings

### Find Filing for Fiscal Year

```python
import requests

def get_10k_filing(cik: str, fiscal_year: int) -> dict:
    """
    Get 10-K filing metadata for a specific fiscal year.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    headers = {'User-Agent': 'ResearchProject/1.0 (contact@email.com)'}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    recent = data['filings']['recent']
    
    for i, form in enumerate(recent['form']):
        if form == '10-K':
            # Check if this is for our target fiscal year
            # The 'fy' field may not be in submissions API, 
            # so we check filing date vs FYE
            filing_date = recent['filingDate'][i]
            
            # 10-K typically filed within 60-90 days of FYE
            # For calendar year companies, FY2023 10-K filed in Feb-Mar 2024
            if is_matching_fiscal_year(filing_date, fiscal_year, data.get('fiscalYearEnd')):
                return {
                    'accession_number': recent['accessionNumber'][i],
                    'filing_date': filing_date,
                    'primary_document': recent['primaryDocument'][i],
                }
    
    return None
```

### Download 10-K Content

```python
def download_10k(cik: str, accession: str, primary_doc: str) -> str:
    """
    Download 10-K filing HTML content.
    """
    accession_clean = accession.replace('-', '')
    cik_clean = cik.lstrip('0')
    
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{primary_doc}"
    
    headers = {'User-Agent': 'ResearchProject/1.0 (contact@email.com)'}
    response = requests.get(url, headers=headers)
    
    return response.text
```

---

## Step 2: Extract Relevant Sections

### Locate Cash Flow Statement

```python
from bs4 import BeautifulSoup

def extract_cash_flow_section(html_content: str) -> str:
    """
    Extract the Statement of Cash Flows and supplemental disclosures.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Search patterns for cash flow statement
    patterns = [
        'statement of cash flows',
        'statements of cash flows',
        'consolidated statement of cash flows',
        'consolidated statements of cash flows',
    ]
    
    # Find section headers
    for pattern in patterns:
        elements = soup.find_all(
            ['h1', 'h2', 'h3', 'h4', 'b', 'strong', 'p'],
            string=lambda t: t and pattern in t.lower() if t else False
        )
        
        if elements:
            # Extract the section (tables and text until next major heading)
            return extract_section_content(elements[0])
    
    # Fallback: search for supplemental disclosure directly
    supp_patterns = [
        'supplemental cash flow',
        'supplemental disclosure',
        'cash paid for income taxes',
        'income taxes paid',
    ]
    
    for pattern in supp_patterns:
        elements = soup.find_all(
            text=lambda t: t and pattern in t.lower() if t else False
        )
        if elements:
            # Get surrounding context
            for elem in elements[:3]:  # Check first 3 matches
                parent = elem.parent
                # Get parent table or section
                table = parent.find_parent('table')
                if table:
                    return str(table)
    
    return ""

def extract_section_content(heading_element, max_length: int = 50000) -> str:
    """
    Extract content following a heading until next major section.
    """
    content = [str(heading_element)]
    
    for sibling in heading_element.find_next_siblings():
        content.append(str(sibling))
        
        # Stop at next major heading
        if sibling.name in ['h1', 'h2'] and len(''.join(content)) > 5000:
            break
        
        # Stop if we've collected enough
        if len(''.join(content)) > max_length:
            break
    
    return '\n'.join(content)
```

---

## Step 3: LLM Extraction

### System Prompt

```
You are an expert SEC filing analyst specializing in financial statement analysis.

Your task is to extract the "cash taxes paid" (also called "income taxes paid") from the Statement of Cash Flows in a 10-K annual report.

SEARCH LOCATIONS (in order of reliability):
1. Supplemental Cash Flow Information section
2. Footnotes to the Statement of Cash Flows
3. Income Tax footnote (if not found elsewhere)

LOOK FOR PHRASES LIKE:
- "Cash paid for income taxes"
- "Income taxes paid"
- "Income taxes paid, net"
- "Income taxes paid, net of refunds"
- "Supplemental disclosure: Income taxes"

EXTRACTION RULES:
1. Extract the dollar amount for the fiscal year
2. Note whether it's "net of refunds" or gross
3. Convert to actual dollars (if in millions, multiply by 1,000,000)
4. Negative values indicate net refund received
5. If multiple years shown, extract the most recent fiscal year

OUTPUT FORMAT:
Return a JSON object with the extracted data and metadata.
```

### User Prompt Template

```python
def build_tax_extraction_prompt(company_name: str, fiscal_year: int, section: str) -> str:
    return f"""
Extract the cash taxes paid for {company_name} for fiscal year {fiscal_year}.

DOCUMENT SECTION:
{section}

Return a JSON object with this structure:
{{
  "fiscal_year": {fiscal_year},
  "cash_taxes_paid": 4850000000,
  "is_net_of_refunds": true,
  "unit_as_reported": "millions",
  "raw_text": "Income taxes paid, net $4,850",
  "source_location": "Supplemental Cash Flow Information",
  "confidence": 0.95,
  "notes": "Any relevant notes about the extraction"
}}

If the data cannot be found, return:
{{
  "fiscal_year": {fiscal_year},
  "cash_taxes_paid": null,
  "source_location": null,
  "confidence": 0.0,
  "notes": "Reason for failure"
}}

Return ONLY valid JSON, no explanation.
"""
```

---

## Step 4: Unit Conversion

### Handling Different Units

```python
def normalize_tax_amount(raw_value: str, unit: str) -> int:
    """
    Convert reported value to actual dollars.
    """
    # Clean the raw value
    cleaned = raw_value.replace('$', '').replace(',', '').replace(' ', '')
    
    # Handle parentheses for negative
    if '(' in cleaned and ')' in cleaned:
        cleaned = '-' + cleaned.replace('(', '').replace(')', '')
    
    # Parse number
    try:
        value = float(cleaned)
    except ValueError:
        return None
    
    # Apply unit multiplier
    unit_lower = unit.lower() if unit else ''
    
    if 'million' in unit_lower:
        return int(value * 1_000_000)
    elif 'billion' in unit_lower:
        return int(value * 1_000_000_000)
    elif 'thousand' in unit_lower:
        return int(value * 1_000)
    else:
        return int(value)
```

### Common Unit Patterns

| Pattern in Filing | Unit | Multiplier |
|-------------------|------|------------|
| "(in millions)" | millions | × 1,000,000 |
| "($ in millions)" | millions | × 1,000,000 |
| "(amounts in thousands)" | thousands | × 1,000 |
| No indication, large company | millions | × 1,000,000 (assume) |
| No indication, values > 100,000 | dollars | × 1 |

---

## Step 5: Validation

### Cross-Check Logic

```python
def validate_llm_extraction(llm_result: dict, xbrl_data: dict = None) -> dict:
    """
    Validate LLM-extracted tax data.
    """
    validations = {
        'is_valid': True,
        'warnings': [],
        'confidence_adjusted': llm_result.get('confidence', 0)
    }
    
    taxes = llm_result.get('cash_taxes_paid')
    
    if taxes is None:
        validations['is_valid'] = False
        validations['warnings'].append("No value extracted")
        return validations
    
    # Check against XBRL if available (from other years or adjacent filings)
    if xbrl_data:
        xbrl_taxes = xbrl_data.get('cash_taxes_paid')
        if xbrl_taxes:
            ratio = taxes / xbrl_taxes if xbrl_taxes != 0 else None
            if ratio and (ratio < 0.3 or ratio > 3):
                validations['warnings'].append(
                    f"Significant deviation from XBRL: LLM={taxes:,}, XBRL={xbrl_taxes:,}"
                )
                validations['confidence_adjusted'] *= 0.7
    
    # Reasonableness checks
    if taxes > 50_000_000_000:  # > $50B
        validations['warnings'].append(f"Unusually high: ${taxes:,.0f}")
    
    if taxes == 0:
        validations['warnings'].append("Zero taxes - may be valid but verify")
    
    # Check for common extraction errors
    if taxes > 0 and taxes < 10000 and llm_result.get('unit_as_reported') in [None, 'dollars']:
        validations['warnings'].append("Value seems low - check unit conversion")
        validations['confidence_adjusted'] *= 0.5
    
    return validations
```

---

## Test Cases

### Manual Verification Set

| Company | CIK | FY | Expected Location | Expected Format |
|---------|-----|-----|-------------------|-----------------|
| General Electric | 0000040545 | 2020 | Supplemental CF | Millions |
| Ford Motor | 0000037996 | 2020 | Supplemental CF | Millions |
| General Motors | 0001467858 | 2020 | Supplemental CF | Millions |
| AT&T | 0000732717 | 2020 | Supplemental CF | Millions |
| Verizon | 0000732712 | 2020 | Supplemental CF | Millions |

### Edge Cases

| Scenario | Example | Expected Handling |
|----------|---------|-------------------|
| Net refund | NOL carryback | Negative value or explicit "(refund)" |
| Combined disclosure | "Interest and taxes paid: $X" | Extract taxes component if split shown |
| Fiscal year != calendar | Apple, Walmart | Match to correct period |
| Restated figures | Amended 10-K | Use restated value |
| Discontinued operations | Segment sold | Use continuing operations if split |

---

## Fallback Chain

If LLM extraction from cash flow statement fails:

1. **Try income tax footnote**
   - Search for "Note X: Income Taxes"
   - Look for "taxes paid" or "cash taxes" disclosure

2. **Try MD&A section**
   - Sometimes discusses cash tax obligations
   - Less reliable but may provide estimates

3. **Flag for manual review**
   - Output to `manual_review_required.csv`
   - Include available context for human review

```python
def fallback_extraction_chain(cik: str, fiscal_year: int, html_content: str) -> dict:
    """
    Attempt extraction using fallback chain.
    """
    # Attempt 1: Cash flow supplemental
    cf_section = extract_cash_flow_section(html_content)
    if cf_section:
        result = extract_with_llm(cf_section, 'cash_flow')
        if result.get('cash_taxes_paid') is not None:
            return result
    
    # Attempt 2: Income tax footnote
    tax_footnote = extract_tax_footnote(html_content)
    if tax_footnote:
        result = extract_with_llm(tax_footnote, 'tax_footnote')
        if result.get('cash_taxes_paid') is not None:
            result['source_location'] = 'Income Tax Footnote'
            result['confidence'] *= 0.8  # Lower confidence
            return result
    
    # Attempt 3: Flag for manual review
    return {
        'fiscal_year': fiscal_year,
        'cash_taxes_paid': None,
        'extraction_status': 'MANUAL_REVIEW_REQUIRED',
        'attempted_sources': ['cash_flow', 'tax_footnote'],
    }
```

---

## Output Files

1. **`cash_taxes_llm.csv`** - Successfully extracted via LLM
2. **`cash_taxes_validation.csv`** - Validation results and confidence scores
3. **`manual_review_required.csv`** - Cases requiring human review

---

## Merge with POC 5 Output

```python
def merge_tax_data(xbrl_df: pd.DataFrame, llm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge XBRL and LLM tax extraction results.
    
    Priority: XBRL > LLM (XBRL is machine-reported, more reliable)
    """
    # Start with XBRL data
    merged = xbrl_df[xbrl_df['fallback_required'] != True].copy()
    merged['extraction_method'] = 'xbrl'
    
    # Add LLM-extracted data for fallback cases
    llm_valid = llm_df[llm_df['cash_taxes_paid'].notna()].copy()
    llm_valid['extraction_method'] = 'llm'
    
    # Combine
    result = pd.concat([merged, llm_valid], ignore_index=True)
    
    # Sort by cik and fiscal year
    result = result.sort_values(['cik', 'fiscal_year'])
    
    return result
```

---

## Quality Metrics

| Metric | Target |
|--------|--------|
| LLM extraction success rate | ≥90% of fallback cases |
| Confidence score average | ≥0.85 |
| Manual review rate | ≤10% of fallback cases |
| Cross-validation match (where XBRL available) | ≥95% within 5% tolerance |

---

## Estimated Runtime

- 10-K download: ~1-2 seconds per filing
- Section extraction: ~0.5 seconds per filing
- LLM extraction: ~3-5 seconds per filing
- Validation: ~0.1 seconds per record
- **Total for ~50 fallback cases**: ~15-20 minutes
