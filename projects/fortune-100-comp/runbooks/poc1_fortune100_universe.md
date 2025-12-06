# POC 1: Fortune 100 Universe Construction

## Objective
Build a reliable mapping of Fortune 100 companies by year (2020-2024), enriched with SEC CIK identifiers.

## Success Criteria
- [ ] Retrieve Fortune 100 list for each year (2020-2024)
- [ ] Match ≥95 of 100 companies to valid SEC CIK
- [ ] Handle ticker changes, M&A, and name variations
- [ ] Output validated CSV with all required fields

---

## Input Requirements
- None (fetches from public sources)

## Expected Output

**File**: `fortune100_universe.csv`

| Column | Type | Example |
|--------|------|---------|
| list_year | int | 2024 |
| rank | int | 1 |
| company_name | str | Walmart |
| ticker | str | WMT |
| cik | str | 0000104169 |
| revenue_mm | float | 648125.0 |
| fiscal_year_end | str | 2024-01-31 |

---

## Step 1: Fetch Fortune 100 Lists

### Option A: Fortune API (Preferred)

```python
import requests
import time

def fetch_fortune_list(year: int) -> list[dict]:
    """
    Fetch Fortune 500 list for a given year.
    Fortune 100 = first 100 entries.
    
    Note: List IDs change by year - may need to discover dynamically.
    """
    # Known list IDs (verify these are current)
    list_ids = {
        2024: 2564929,  # Verify this
        2023: 2345678,  # Placeholder - need to verify
        # etc.
    }
    
    base_url = "https://fortune.com/api/v2/list"
    url = f"{base_url}/{list_ids[year]}/expand/item/ranking/asc/0/100"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Research Project)',
        'Accept': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()['items'][:100]
```

### Option B: GitHub Historical Data (Backup)

```bash
# Clone historical Fortune 500 data
git clone https://github.com/cmusam/fortune500.git

# Files are in CSV format by year
ls fortune500/csv/
# fortune500_2020.csv, fortune500_2021.csv, etc.
```

### Option C: Manual Compilation (Fallback)

If APIs fail, compile from:
- Wikipedia: "Fortune 500" article has annual lists
- Fortune.com archive pages
- Kaggle datasets

---

## Step 2: CIK Enrichment

### Primary Method: SEC Bulk Mapping

```python
import requests

def get_cik_ticker_map() -> dict[str, str]:
    """
    Download SEC's official ticker-to-CIK mapping.
    Returns dict mapping ticker -> CIK (zero-padded).
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {'User-Agent': 'ResearchProject/1.0 (contact@email.com)'}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    # Format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc"}, ...}
    return {
        entry['ticker']: str(entry['cik_str']).zfill(10)
        for entry in data.values()
    }
```

### Fallback: EDGAR Company Search

```python
def lookup_cik_by_name(company_name: str) -> str:
    """
    Search EDGAR for CIK by company name.
    Use when ticker lookup fails (M&A, name changes).
    """
    url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        'company': company_name,
        'CIK': '',
        'type': '10-K',
        'owner': 'include',
        'count': '10',
        'action': 'getcompany',
        'output': 'atom'
    }
    headers = {'User-Agent': 'ResearchProject/1.0 (contact@email.com)'}
    
    response = requests.get(url, params=params, headers=headers)
    # Parse XML response to extract CIK
    # ...
```

---

## Step 3: Validate and Enrich

### Fiscal Year End Detection

```python
def get_fiscal_year_end(cik: str) -> str:
    """
    Get company's fiscal year end from SEC submissions.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {'User-Agent': 'ResearchProject/1.0 (contact@email.com)'}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    # fiscalYearEnd is in MMDD format
    fye = data.get('fiscalYearEnd', '1231')  # Default Dec 31
    return f"{fye[:2]}-{fye[2:]}"  # "12-31"
```

---

## Test Cases

### Validation Set (10 Companies)

| Company | Ticker | Expected CIK | FYE | Notes |
|---------|--------|--------------|-----|-------|
| Walmart | WMT | 0000104169 | 01-31 | Non-calendar FY |
| Amazon | AMZN | 0001018724 | 12-31 | |
| Apple | AAPL | 0000320193 | 09-30 | Non-calendar FY |
| UnitedHealth | UNH | 0000731766 | 12-31 | |
| Berkshire Hathaway | BRK.A | 0001067983 | 12-31 | Class A shares |
| McKesson | MCK | 0000927653 | 03-31 | Non-calendar FY |
| ExxonMobil | XOM | 0000034088 | 12-31 | |
| CVS Health | CVS | 0000064803 | 12-31 | |
| Costco | COST | 0000909832 | 09-01 | Non-calendar FY |
| Alphabet | GOOGL | 0001652044 | 12-31 | |

### Expected Issues to Handle

| Issue | Example | Resolution |
|-------|---------|------------|
| Multi-class tickers | BRK.A vs BRK.B | Use primary class (A) |
| Ticker changes | FB → META (2022) | Map historical ticker to current CIK |
| M&A | Raytheon + UTC → RTX | Track both pre/post merger |
| Spinoffs | IBM → IBM + KD (Kyndryl) | Include both if Fortune 100 |
| Private companies | Cargill, Koch | Exclude (no SEC filings) |

---

## Validation Checks

```python
def validate_universe(df: pd.DataFrame) -> dict:
    """
    Run validation checks on Fortune 100 universe.
    """
    results = {
        'total_rows': len(df),
        'unique_companies_per_year': df.groupby('list_year')['cik'].nunique().to_dict(),
        'missing_ciks': df[df['cik'].isna()]['company_name'].tolist(),
        'duplicate_ciks': df[df.duplicated(['list_year', 'cik'], keep=False)].to_dict('records'),
    }
    
    # Each year should have exactly 100 companies
    for year, count in results['unique_companies_per_year'].items():
        if count != 100:
            results[f'year_{year}_warning'] = f"Expected 100, got {count}"
    
    return results
```

---

## Output Validation

Run these checks before proceeding to POC 2:

```bash
# Check row counts
wc -l fortune100_universe.csv
# Expected: 501 (header + 100 companies × 5 years)

# Check for missing CIKs
grep ",," fortune100_universe.csv | wc -l
# Expected: 0 (or only known private companies)

# Verify CIK format (10 digits, zero-padded)
cut -d',' -f5 fortune100_universe.csv | grep -v "^[0-9]\{10\}$" | head
# Expected: only header row
```

---

## Known Exceptions

These Fortune 100 companies may not have SEC filings:

| Company | Reason | Action |
|---------|--------|--------|
| Cargill | Private | Exclude |
| Koch Industries | Private | Exclude |
| Publix | Private (employee-owned) | Exclude |
| State Farm | Mutual company | Exclude |

Document exclusions in output notes.

---

## Estimated Runtime
- Fortune list fetch: ~5 seconds per year
- CIK bulk download: ~2 seconds
- CIK validation per company: ~0.5 seconds (rate-limited)
- **Total**: ~5 minutes for all 5 years
