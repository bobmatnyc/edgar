# POC 5: Cash Taxes Paid - XBRL Extraction

## Objective
Extract corporate cash taxes paid from 10-K filings using the SEC XBRL API, which provides structured financial data.

## Success Criteria
- [ ] Retrieve cash taxes paid for ≥90% of company-years via XBRL
- [ ] Correctly identify net vs gross tax amounts
- [ ] Handle fiscal year alignment
- [ ] Flag refund years (negative values)

## Dependencies
- **Requires**: POC 1 output (`fortune100_universe.csv`)

---

## Background: Cash Taxes Paid Disclosure

### Disclosure Location
Cash taxes paid is a **supplemental disclosure** in the Statement of Cash Flows, required by ASC 230. It appears:
1. **On the face** of the cash flow statement (supplemental section)
2. **In footnotes** to the cash flow statement
3. **In the income tax footnote** (sometimes)

### XBRL Elements

| Element | Description | Preference |
|---------|-------------|------------|
| `IncomeTaxesPaidNet` | Cash taxes paid, net of refunds | **Preferred** |
| `IncomeTaxesPaid` | Cash taxes paid (gross) | Secondary |
| `IncomeTaxesReceived` | Tax refunds received | Use if only gross available |

### Starting 2025: Enhanced Disclosure
ASU 2023-09 requires disaggregation by jurisdiction (federal, state, foreign) starting FY2025. This POC focuses on aggregate amounts for 2020-2024.

---

## Input Requirements

**File**: `fortune100_universe.csv` from POC 1

Required columns:
- `cik`: SEC Central Index Key (zero-padded)
- `list_year`: Fortune list year
- `fiscal_year_end`: Company's FYE

---

## Expected Output

**File**: `cash_taxes_paid.csv`

| Column | Type | Example |
|--------|------|---------|
| cik | str | 0000104169 |
| company_name | str | Walmart |
| fiscal_year | int | 2023 |
| fiscal_period_end | date | 2024-01-31 |
| cash_taxes_paid | int | 5123000000 |
| is_net_of_refunds | bool | True |
| xbrl_element_used | str | IncomeTaxesPaidNet |
| filing_accession | str | 0000104169-24-000012 |
| filing_date | date | 2024-03-15 |

---

## Step 1: Retrieve XBRL Company Facts

### SEC Company Facts API

```python
import requests
import time

def get_xbrl_facts(cik: str) -> dict:
    """
    Retrieve all XBRL facts for a company from SEC API.
    
    Returns structured data with all reported XBRL elements.
    """
    cik_padded = cik.zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
    
    headers = {
        'User-Agent': 'ResearchProject/1.0 (contact@youremail.com)',
        'Accept': 'application/json'
    }
    
    # Rate limit: max 10 requests/second
    time.sleep(0.1)
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()
```

### API Response Structure

```json
{
  "cik": 104169,
  "entityName": "WALMART INC",
  "facts": {
    "us-gaap": {
      "IncomeTaxesPaidNet": {
        "label": "Income Taxes Paid, Net",
        "description": "...",
        "units": {
          "USD": [
            {
              "end": "2024-01-31",
              "val": 5123000000,
              "accn": "0000104169-24-000012",
              "fy": 2024,
              "fp": "FY",
              "form": "10-K",
              "filed": "2024-03-15",
              "frame": "CY2023"
            },
            // ... more periods
          ]
        }
      },
      // ... other elements
    }
  }
}
```

---

## Step 2: Extract Tax Data

### Extraction Logic

```python
def extract_cash_taxes(xbrl_facts: dict, target_years: list[int]) -> list[dict]:
    """
    Extract cash taxes paid for target fiscal years.
    
    Prioritizes IncomeTaxesPaidNet, falls back to IncomeTaxesPaid.
    """
    results = []
    us_gaap = xbrl_facts.get('facts', {}).get('us-gaap', {})
    
    # Priority order of elements
    tax_elements = [
        ('IncomeTaxesPaidNet', True),   # Net of refunds (preferred)
        ('IncomeTaxesPaid', False),      # Gross (fallback)
    ]
    
    # Track which years we've found
    found_years = set()
    
    for element_name, is_net in tax_elements:
        if element_name not in us_gaap:
            continue
            
        element_data = us_gaap[element_name]
        usd_data = element_data.get('units', {}).get('USD', [])
        
        for entry in usd_data:
            # Only want annual 10-K filings
            if entry.get('form') != '10-K' or entry.get('fp') != 'FY':
                continue
                
            fy = entry.get('fy')
            
            # Skip if year not in target range or already found
            if fy not in target_years or fy in found_years:
                continue
            
            found_years.add(fy)
            
            results.append({
                'fiscal_year': fy,
                'fiscal_period_end': entry.get('end'),
                'cash_taxes_paid': entry.get('val'),
                'is_net_of_refunds': is_net,
                'xbrl_element_used': element_name,
                'filing_accession': entry.get('accn'),
                'filing_date': entry.get('filed'),
                'frame': entry.get('frame'),
            })
    
    return results
```

### Handling Edge Cases

```python
def handle_missing_data(cik: str, missing_years: list[int], xbrl_facts: dict) -> list[dict]:
    """
    Handle cases where primary tax elements are missing.
    
    Some companies may use different element names or report in footnotes only.
    """
    results = []
    us_gaap = xbrl_facts.get('facts', {}).get('us-gaap', {})
    
    # Alternative elements to check
    alternatives = [
        'PaymentsForIncomeTaxes',
        'IncomeTaxesPaidNetClassifiedAsOperating',
        'CashPaidForIncomeTaxes',
    ]
    
    for element_name in alternatives:
        if element_name in us_gaap:
            # Extract similar to primary logic
            pass
    
    # If still missing, flag for LLM fallback (POC 6)
    for year in missing_years:
        if year not in [r['fiscal_year'] for r in results]:
            results.append({
                'fiscal_year': year,
                'cash_taxes_paid': None,
                'extraction_status': 'XBRL_MISSING',
                'fallback_required': True,
            })
    
    return results
```

---

## Step 3: Fiscal Year Alignment

### Understanding Fiscal Years

```python
def get_fiscal_year(period_end: str, fye_month: int) -> int:
    """
    Determine the fiscal year for a period end date.
    
    Convention: FY is named for the calendar year in which it ends.
    
    Examples:
    - Walmart FYE Jan 31, 2024 → FY2024 (or FY2023 in some systems)
    - Apple FYE Sep 30, 2023 → FY2023
    - Amazon FYE Dec 31, 2023 → FY2023
    """
    from datetime import datetime
    
    end_date = datetime.fromisoformat(period_end)
    
    # The XBRL 'fy' field typically gives us the correct fiscal year
    # but we should validate it matches our expectations
    
    return end_date.year
```

### Alignment Table

| Company | FYE | SEC 'fy' for Jan 2024 filing | Our FY Label |
|---------|-----|------------------------------|--------------|
| Walmart | Jan 31 | 2024 | FY2023 |
| Apple | Sep 30 | 2023 | FY2023 |
| Amazon | Dec 31 | 2023 | FY2023 |
| Costco | Sep (varies) | 2023 | FY2023 |

**Important**: Match fiscal years consistently between tax and compensation data. The SEC's `fy` field is usually reliable.

---

## Step 4: Validation

### Sanity Checks

```python
def validate_tax_data(record: dict, company_revenue: float) -> list[str]:
    """
    Validate extracted tax data for reasonableness.
    """
    warnings = []
    
    taxes = record.get('cash_taxes_paid')
    
    if taxes is None:
        warnings.append("Missing cash taxes paid data")
        return warnings
    
    # Check for reasonable range
    if company_revenue > 0:
        effective_rate = taxes / company_revenue
        
        if effective_rate > 0.15:
            warnings.append(f"Tax/revenue ratio {effective_rate:.1%} seems high")
        
        if effective_rate < 0:
            warnings.append(f"Net tax refund: {taxes:,}")
    
    # Flag large absolute values for verification
    if abs(taxes) > 20_000_000_000:  # > $20B
        warnings.append(f"Very large tax amount: ${taxes:,.0f}")
    
    # Flag zero taxes for large companies
    if taxes == 0:
        warnings.append("Zero cash taxes paid - verify")
    
    return warnings
```

### Cross-Check with Income Tax Provision

```python
def compare_to_provision(xbrl_facts: dict, fiscal_year: int) -> dict:
    """
    Compare cash taxes to income tax provision for reasonableness.
    
    Cash taxes can differ significantly from provision due to:
    - Timing differences (deferred taxes)
    - Refunds from prior years
    - Estimated payment timing
    """
    us_gaap = xbrl_facts.get('facts', {}).get('us-gaap', {})
    
    # Income tax expense elements
    provision_elements = [
        'IncomeTaxExpenseBenefit',
        'IncomeTaxExpenseContinuingOperations',
    ]
    
    cash_taxes = None
    provision = None
    
    # Extract both for comparison
    # ... (similar extraction logic)
    
    if cash_taxes and provision:
        ratio = cash_taxes / provision if provision != 0 else None
        return {
            'cash_taxes': cash_taxes,
            'provision': provision,
            'ratio': ratio,
            'significant_difference': abs(ratio - 1) > 0.5 if ratio else True
        }
    
    return {}
```

---

## Test Cases

### Validation Set (10 Companies)

| Company | CIK | FY2023 Expected Taxes | Notes |
|---------|-----|----------------------|-------|
| Walmart | 0000104169 | ~$5-6B | Large retailer |
| Apple | 0000320193 | ~$15-18B | High-margin tech |
| Amazon | 0001018724 | ~$3-5B | Historically low |
| ExxonMobil | 0000034088 | ~$10-15B | Oil & gas profits |
| Berkshire | 0001067983 | ~$8-12B | Conglomerate |
| JPMorgan | 0000019617 | ~$10-12B | Financial services |
| Alphabet | 0001652044 | ~$12-15B | Tech giant |
| Microsoft | 0000789019 | ~$15-20B | High-margin software |
| UnitedHealth | 0000731766 | ~$4-6B | Healthcare |
| CVS Health | 0000064803 | ~$2-4B | Pharmacy/insurance |

### Edge Cases

| Scenario | Example | Expected Behavior |
|----------|---------|-------------------|
| Net refund year | Company with NOL carryback | Negative value |
| Missing XBRL element | Older filings | Flag for POC 6 fallback |
| Restated financials | Amended 10-K/A | Use most recent filing |
| Unusual FYE | 52/53 week year | Handle date variance |

---

## Batch Processing Script

```python
def process_all_companies(universe_df: pd.DataFrame, target_years: list[int]) -> pd.DataFrame:
    """
    Process all Fortune 100 companies for tax data.
    """
    all_results = []
    
    for _, row in universe_df.iterrows():
        cik = row['cik']
        company_name = row['company_name']
        
        try:
            # Get XBRL facts
            facts = get_xbrl_facts(cik)
            
            # Extract tax data
            tax_records = extract_cash_taxes(facts, target_years)
            
            # Add company info
            for record in tax_records:
                record['cik'] = cik
                record['company_name'] = company_name
                all_results.append(record)
            
            # Check for missing years
            found_years = {r['fiscal_year'] for r in tax_records}
            missing = set(target_years) - found_years
            
            if missing:
                fallback_records = handle_missing_data(cik, list(missing), facts)
                for record in fallback_records:
                    record['cik'] = cik
                    record['company_name'] = company_name
                    all_results.append(record)
                    
        except Exception as e:
            # Log error and continue
            all_results.append({
                'cik': cik,
                'company_name': company_name,
                'extraction_status': f'ERROR: {str(e)}',
                'fallback_required': True,
            })
    
    return pd.DataFrame(all_results)
```

---

## Output Validation

```bash
# Check completeness
wc -l cash_taxes_paid.csv
# Expected: ~500 rows (100 companies × 5 years)

# Check for missing data
grep "fallback_required" cash_taxes_paid.csv | wc -l
# Target: <50 (should get >90% via XBRL)

# Check for negative values (refunds)
awk -F',' '$5 < 0' cash_taxes_paid.csv | wc -l
# Note count - valid but interesting

# Verify range of values
awk -F',' 'NR>1 {print $5}' cash_taxes_paid.csv | sort -n | head -10
awk -F',' 'NR>1 {print $5}' cash_taxes_paid.csv | sort -n | tail -10
```

---

## Output Files

1. **`cash_taxes_paid.csv`** - Primary output with all tax data
2. **`xbrl_extraction_log.csv`** - Extraction metadata and errors
3. **`xbrl_fallback_required.csv`** - Companies/years needing POC 6 fallback

---

## Estimated Runtime

- API call per company: ~0.5 seconds (with rate limiting)
- Data processing: ~0.1 seconds per company
- **Total for 100 companies**: ~2-3 minutes
- **Total for all 5 years**: ~2-3 minutes (single API call returns all years)
