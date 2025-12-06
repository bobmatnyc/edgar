# POC 2: DEF 14A Proxy Statement Retrieval

## Objective
Reliably retrieve DEF 14A (definitive proxy statement) filings for Fortune 100 companies across 5 fiscal years.

## Success Criteria
- [ ] Retrieve correct proxy filing for each company-year combination
- [ ] Handle fiscal year ≠ calendar year alignment
- [ ] Identify and flag amended filings (DEFA14A)
- [ ] Extract raw HTML/text suitable for LLM parsing

## Dependencies
- **Requires**: POC 1 output (`fortune100_universe.csv`)

---

## Input Requirements

**File**: `fortune100_universe.csv` from POC 1

Required columns:
- `cik`: SEC Central Index Key
- `list_year`: Fortune list year (maps to fiscal year)
- `fiscal_year_end`: Company's FYE date

---

## Expected Output

**File**: `def14a_filings.csv`

| Column | Type | Example |
|--------|------|---------|
| cik | str | 0000104169 |
| company_name | str | Walmart |
| fiscal_year | int | 2023 |
| filing_date | date | 2024-04-18 |
| accession_number | str | 0001193125-24-123456 |
| filing_url | str | https://www.sec.gov/Archives/... |
| file_size_kb | int | 2450 |
| is_amended | bool | False |

**Directory**: `filings/def14a/`
- Raw HTML files: `{cik}_{fiscal_year}_def14a.html`

---

## Step 1: Identify Target Filings

### Fiscal Year to Proxy Mapping Logic

```python
def get_proxy_date_range(fiscal_year: int, fye_month: int) -> tuple[str, str]:
    """
    Determine the date range to search for proxy statements.
    
    Proxy statements are typically filed 30-120 days after fiscal year end,
    before the annual shareholder meeting.
    
    Args:
        fiscal_year: The fiscal year of compensation data
        fye_month: Month of fiscal year end (1-12)
    
    Returns:
        (start_date, end_date) in YYYY-MM-DD format
    """
    from datetime import date, timedelta
    
    # Fiscal year end date
    if fye_month == 12:
        fye = date(fiscal_year, 12, 31)
    else:
        # Non-calendar FY: ends in following calendar year
        fye = date(fiscal_year + 1, fye_month, 28)  # Approximate
    
    # Search window: 30-150 days after FYE
    start = fye + timedelta(days=30)
    end = fye + timedelta(days=150)
    
    return start.isoformat(), end.isoformat()

# Examples:
# Walmart FY2023 (ends Jan 2024) → search Feb-Jun 2024
# Apple FY2023 (ends Sep 2023) → search Oct 2023-Feb 2024
# Amazon FY2023 (ends Dec 2023) → search Jan-May 2024
```

---

## Step 2: Retrieve Filing Index

### Method A: SEC Submissions API (Recommended)

```python
import requests
import time

def get_def14a_filings(cik: str, start_date: str, end_date: str) -> list[dict]:
    """
    Get DEF 14A filings for a company within date range.
    
    Returns list of filing metadata dicts.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {'User-Agent': 'ResearchProject/1.0 (contact@email.com)'}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    filings = []
    recent = data['filings']['recent']
    
    for i, form in enumerate(recent['form']):
        if form in ('DEF 14A', 'DEFA14A'):
            filing_date = recent['filingDate'][i]
            
            if start_date <= filing_date <= end_date:
                filings.append({
                    'accession_number': recent['accessionNumber'][i],
                    'filing_date': filing_date,
                    'form': form,
                    'primary_document': recent['primaryDocument'][i],
                    'file_number': recent['fileNumber'][i],
                })
    
    return filings
```

### Method B: EDGAR Full-Text Search (Backup)

```python
def search_def14a_edgar(cik: str, start_date: str, end_date: str) -> list[dict]:
    """
    Search EDGAR for DEF 14A using full-text search API.
    """
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        'q': f'formType:"DEF 14A"',
        'dateRange': 'custom',
        'startdt': start_date,
        'enddt': end_date,
        'ciks': cik.lstrip('0'),  # EFTS uses non-padded CIK
        'from': 0,
        'size': 10
    }
    headers = {'User-Agent': 'ResearchProject/1.0 (contact@email.com)'}
    
    response = requests.get(url, params=params, headers=headers)
    return response.json().get('hits', {}).get('hits', [])
```

---

## Step 3: Download Filing Content

### Construct Filing URL

```python
def get_filing_url(cik: str, accession: str, primary_doc: str) -> str:
    """
    Construct the URL to the primary document.
    
    EDGAR URL format:
    https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{primary_doc}
    """
    accession_clean = accession.replace('-', '')
    cik_clean = cik.lstrip('0')
    
    return f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{primary_doc}"
```

### Download and Save

```python
def download_filing(url: str, output_path: str) -> int:
    """
    Download filing HTML and save to disk.
    Returns file size in KB.
    """
    headers = {'User-Agent': 'ResearchProject/1.0 (contact@email.com)'}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    return len(response.content) // 1024
```

---

## Step 4: Validate Retrieved Filings

### Content Validation

```python
def validate_def14a_content(html_content: str) -> dict:
    """
    Validate that the filing contains expected compensation tables.
    """
    checks = {
        'has_summary_comp_table': False,
        'has_executive_comp_section': False,
        'has_pay_vs_perf': False,  # Only 2023+
        'estimated_table_count': 0,
    }
    
    content_lower = html_content.lower()
    
    # Check for Summary Compensation Table
    if 'summary compensation table' in content_lower:
        checks['has_summary_comp_table'] = True
    
    # Check for executive compensation section
    if any(phrase in content_lower for phrase in [
        'executive compensation',
        'compensation discussion',
        'compensation of named executive'
    ]):
        checks['has_executive_comp_section'] = True
    
    # Check for Pay vs Performance (2023+ only)
    if 'pay versus performance' in content_lower or 'compensation actually paid' in content_lower:
        checks['has_pay_vs_perf'] = True
    
    # Estimate table count
    checks['estimated_table_count'] = content_lower.count('<table')
    
    return checks
```

---

## Test Cases

### Validation Set (10 Companies)

Test retrieval for FY2023 (proxies filed in 2024):

| Company | CIK | Expected Filing Date | FYE | Notes |
|---------|-----|---------------------|-----|-------|
| Walmart | 0000104169 | Apr 2024 | Jan 31 | Non-calendar FY |
| Amazon | 0001018724 | Apr 2024 | Dec 31 | Calendar FY |
| Apple | 0000320193 | Jan 2024 | Sep 30 | Non-calendar FY |
| Microsoft | 0000789019 | Oct 2024 | Jun 30 | Non-calendar FY |
| Alphabet | 0001652044 | Apr 2024 | Dec 31 | Calendar FY |
| JPMorgan | 0000019617 | Apr 2024 | Dec 31 | Calendar FY |
| ExxonMobil | 0000034088 | Apr 2024 | Dec 31 | Calendar FY |
| CVS Health | 0000064803 | Mar 2024 | Dec 31 | Calendar FY |
| UnitedHealth | 0000731766 | Apr 2024 | Dec 31 | Calendar FY |
| Costco | 0000909832 | Dec 2023 | Sep 3 | Non-calendar FY |

### Content Validation Checks

For each retrieved filing, verify:
1. File size > 100 KB (proxies are substantial documents)
2. Contains "Summary Compensation Table" phrase
3. Contains NEO names (should match company's known executives)
4. For FY2022+: Contains "Pay Versus Performance" section

---

## Expected Issues and Handling

| Issue | Detection | Resolution |
|-------|-----------|------------|
| Multiple DEF 14A filings | Count > 1 in date range | Take most recent (or largest file) |
| DEFA14A amendments | Form type = DEFA14A | Flag; may need original + amendment |
| Filing covers multiple years | Check table content | Extract all years present |
| Proxy combined with 10-K | Document type check | Parse compensation sections only |
| HTML vs XBRL rendering | File extension check | Use HTML version for LLM parsing |
| Large file size (>10 MB) | Size check | May need chunking for LLM |

---

## Rate Limiting

```python
import time

SEC_RATE_LIMIT = 10  # requests per second max

def rate_limited_request(url: str, headers: dict) -> requests.Response:
    """Make a rate-limited request to SEC."""
    time.sleep(1 / SEC_RATE_LIMIT)  # 100ms between requests
    return requests.get(url, headers=headers)
```

---

## Output Validation

```bash
# Check filing index completeness
wc -l def14a_filings.csv
# Expected: ~500 rows (100 companies × 5 years, minus exceptions)

# Check for missing filings
grep "filing_url,," def14a_filings.csv | wc -l
# Expected: 0

# Check downloaded file sizes
du -sh filings/def14a/
# Expected: 500-2000 MB total

# Verify content presence
grep -l "Summary Compensation Table" filings/def14a/*.html | wc -l
# Expected: ~500 (should match filing count)

# Check Pay vs Performance (2023+ filings only)
grep -l "Pay Versus Performance" filings/def14a/*_2023_*.html | wc -l
# Expected: ~100 (FY2022 and FY2023 data)
```

---

## Edge Cases Log

Create a log file for manual review:

**File**: `def14a_exceptions.csv`

| cik | fiscal_year | issue_type | notes | resolution |
|-----|-------------|------------|-------|------------|
| ... | ... | multiple_filings | 2 DEF14A found | Used later filing |
| ... | ... | no_filing_found | No proxy in window | Extended search range |
| ... | ... | content_validation_failed | No SCT found | Manual review needed |

---

## Estimated Runtime

- Filing index retrieval: ~0.5 seconds per company-year
- File download: ~1-3 seconds per filing (varies by size)
- Content validation: ~0.1 seconds per file
- **Total**: ~30-45 minutes for 500 company-years (with rate limiting)
