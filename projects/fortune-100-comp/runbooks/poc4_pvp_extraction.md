# POC 4: Pay vs Performance Table Extraction

## Objective
Extract "Compensation Actually Paid" (CAP) from Pay vs Performance tables, available in DEF 14A filings for FY2022 onward (filed 2023+).

## Success Criteria
- [ ] Extract CAP for CEO and average for other NEOs
- [ ] Capture all years shown in PvP table (3-5 years)
- [ ] Parse financial performance metrics (TSR, net income)
- [ ] Handle the reconciliation footnotes (adjustments from SCT to CAP)

## Dependencies
- **Requires**: POC 2 output (DEF 14A HTML files)
- **Note**: Only applicable to proxies filed after December 2022

---

## Background: Pay vs Performance Disclosure

### Regulatory Basis
- **Rule**: Item 402(v) of Regulation S-K
- **Effective**: Fiscal years ending on or after December 16, 2022
- **Phase-in**: 3 years in first filing, adding 1 year each subsequent year
- **Content**: "Compensation Actually Paid" (CAP) reflects mark-to-market equity values

### What CAP Measures
CAP ≠ cash received. It's a "realizable pay" concept that adjusts SCT total for:
- Removes: Grant date fair value of equity awards
- Adds: Year-end fair value of awards granted during year
- Adds/Removes: Change in fair value of prior awards

---

## Input Requirements

**Files**:
- `def14a_filings.csv` - Filing metadata (filter: filing_date ≥ 2023-01-01)
- `filings/def14a/{cik}_{fiscal_year}_def14a.html` - Raw HTML files

---

## Expected Output

**File**: `neo_compensation_pvp.csv`

| Column | Type | Example |
|--------|------|---------|
| cik | str | 0000104169 |
| fiscal_year | int | 2023 |
| peo_name | str | C. Douglas McMillon |
| peo_sct_total | int | 27761155 |
| peo_cap | int | 32456789 |
| avg_neo_sct_total | int | 12500000 |
| avg_neo_cap | int | 14200000 |
| company_tsr_cumulative | float | 125.5 |
| peer_tsr_cumulative | float | 118.2 |
| net_income_mm | int | 15400 |
| company_selected_measure | str | Revenue Growth |
| company_selected_value | str | 7.3% |

**File**: `neo_cap_adjustments.csv` (optional detail)

| Column | Type | Example |
|--------|------|---------|
| cik | str | 0000104169 |
| fiscal_year | int | 2023 |
| executive_type | str | PEO |
| sct_total | int | 27761155 |
| less_sct_stock_awards | int | -16742845 |
| less_sct_option_awards | int | 0 |
| less_pension_change | int | 0 |
| plus_year_end_fv_current | int | 18500000 |
| plus_change_fv_prior_unvested | int | 2500000 |
| plus_change_fv_vested | int | 1200000 |
| less_fv_forfeited | int | 0 |
| plus_pension_service_cost | int | 0 |
| cap_total | int | 32457310 |

---

## Step 1: Identify PvP Section

### Detection Patterns

```python
def has_pvp_disclosure(html_content: str) -> bool:
    """
    Check if filing contains Pay vs Performance disclosure.
    """
    indicators = [
        'pay versus performance',
        'pay vs. performance',
        'pay vs performance',
        'compensation actually paid',
        'item 402(v)',
    ]
    
    content_lower = html_content.lower()
    return any(indicator in content_lower for indicator in indicators)

def extract_pvp_section(html_content: str) -> str:
    """
    Extract the Pay vs Performance section from proxy.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find PvP heading
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'b', 'strong', 'p'])
    
    for heading in headings:
        text = heading.get_text().lower()
        if 'pay versus performance' in text or 'pay vs. performance' in text:
            # Extract section until next major heading
            section_content = [str(heading)]
            
            for sibling in heading.find_next_siblings():
                # Stop at next major section
                if sibling.name in ['h1', 'h2'] and sibling.get_text().strip():
                    sibling_text = sibling.get_text().lower()
                    if not any(term in sibling_text for term in ['pay', 'performance', 'compensation']):
                        break
                
                section_content.append(str(sibling))
                
                # Also stop after getting the main content
                if len(section_content) > 50:  # Reasonable limit
                    break
            
            return '\n'.join(section_content)
    
    return ""
```

---

## Step 2: LLM Extraction

### System Prompt

```
You are an expert SEC filing analyst specializing in executive compensation disclosures.

Your task is to extract Pay Versus Performance table data from DEF 14A proxy statements filed under Item 402(v) of Regulation S-K.

KEY CONCEPTS:
- PEO = Principal Executive Officer (CEO)
- NEO = Named Executive Officer (other executives)
- SCT = Summary Compensation Table (granted pay)
- CAP = Compensation Actually Paid (realized/realizable pay)
- TSR = Total Shareholder Return (cumulative, indexed to 100)

EXTRACTION RULES:
1. Extract ALL fiscal years shown in the table (typically 3-5 years)
2. Convert dollar amounts to integers (remove $ and commas)
3. TSR values are typically indexed (100 = starting value) or percentages
4. Net income may be in millions - note and preserve the unit
5. If multiple PEOs in a year, extract each separately
6. For "Compensation Actually Paid", this is the KEY METRIC - extract carefully
7. Negative CAP values are valid (stock price declines)

OUTPUT FORMAT:
Return a JSON array with one object per fiscal year shown.
```

### User Prompt Template

```python
def build_pvp_extraction_prompt(company_name: str, pvp_section: str) -> str:
    return f"""
Extract the Pay Versus Performance table data for {company_name}.

DOCUMENT SECTION:
{pvp_section}

Return a JSON array with this structure:
[
  {{
    "fiscal_year": 2023,
    "peo_name": "CEO Full Name",
    "peo_sct_total": 27761155,
    "peo_compensation_actually_paid": 32456789,
    "avg_other_neo_sct_total": 12500000,
    "avg_other_neo_cap": 14200000,
    "company_tsr": 125.5,
    "peer_group_tsr": 118.2,
    "net_income": 15400000000,
    "net_income_unit": "dollars",
    "company_selected_measure_name": "Revenue Growth",
    "company_selected_measure_value": "7.3%"
  }},
  ...
]

CRITICAL: "peo_compensation_actually_paid" is the key metric - this represents what the CEO actually received/realized.

Extract ALL years shown in the table. Return ONLY valid JSON, no explanation.
"""
```

---

## Step 3: Extract Adjustment Footnotes (Optional)

### Adjustment Detail Prompt

```python
def build_adjustment_extraction_prompt(company_name: str, footnote_section: str) -> str:
    return f"""
Extract the reconciliation adjustments that convert Summary Compensation Table total to Compensation Actually Paid for {company_name}.

DOCUMENT SECTION:
{footnote_section}

The footnotes typically show a table or list with adjustments like:
- Less: Stock Awards (grant date fair value from SCT)
- Less: Option Awards (grant date fair value from SCT)
- Less: Change in Pension Value
- Plus: Fair Value at Year-End of Awards Granted During Year
- Plus: Change in Fair Value of Prior Year Awards Unvested at Year-End
- Plus: Change in Fair Value of Awards Vesting During Year
- Less: Fair Value of Awards Forfeited
- Plus: Pension Service Cost

Return a JSON array with adjustments for each executive/year:
[
  {{
    "fiscal_year": 2023,
    "executive_type": "PEO",
    "adjustments": {{
      "sct_total": 27761155,
      "less_stock_awards": -16742845,
      "less_option_awards": 0,
      "less_pension_change": 0,
      "plus_year_end_fv_current_grants": 18500000,
      "plus_change_fv_prior_unvested": 2500000,
      "plus_change_fv_vested": 1200000,
      "less_fv_forfeited": 0,
      "plus_pension_service_cost": 0,
      "calculated_cap": 32458310
    }}
  }}
]
"""
```

---

## Step 4: Validation

### Cross-Check with SCT Data

```python
def validate_pvp_against_sct(pvp_record: dict, sct_records: list[dict]) -> list[str]:
    """
    Validate PvP data against previously extracted SCT data.
    """
    warnings = []
    
    # Find matching SCT record
    sct_match = next(
        (r for r in sct_records 
         if r['fiscal_year'] == pvp_record['fiscal_year'] and r['is_ceo']),
        None
    )
    
    if sct_match:
        # SCT totals should match
        if abs(sct_match['total'] - pvp_record['peo_sct_total']) > 1000:
            warnings.append(
                f"SCT total mismatch: POC3 extracted {sct_match['total']}, "
                f"PvP shows {pvp_record['peo_sct_total']}"
            )
    else:
        warnings.append(f"No matching SCT record for CEO in FY{pvp_record['fiscal_year']}")
    
    return warnings
```

### Reasonableness Checks

```python
def validate_cap_reasonableness(record: dict) -> list[str]:
    """
    Check that CAP values are reasonable relative to SCT.
    """
    warnings = []
    
    sct = record['peo_sct_total']
    cap = record['peo_compensation_actually_paid']
    
    if sct > 0:
        ratio = cap / sct
        
        # CAP typically 0.5x to 3x SCT, but can be negative
        if ratio > 5:
            warnings.append(f"CAP/SCT ratio {ratio:.1f} is unusually high")
        if ratio < -2:
            warnings.append(f"CAP/SCT ratio {ratio:.1f} suggests major equity losses")
    
    # Negative CAP is valid but should be flagged for awareness
    if cap < 0:
        warnings.append(f"Negative CAP ({cap:,}) - stock price likely declined significantly")
    
    return warnings
```

---

## Test Cases

### Manual Verification Set

| Company | CIK | FY | CEO SCT Total | CEO CAP | Note |
|---------|-----|-----|---------------|---------|------|
| Walmart | 0000104169 | 2023 | ~$27.8M | Verify | |
| Apple | 0000320193 | 2023 | ~$63.2M | Verify | High stock awards |
| JPMorgan | 0000019617 | 2023 | ~$36.0M | Verify | |
| ExxonMobil | 0000034088 | 2023 | ~$35.0M | Verify | |
| Amazon | 0001018724 | 2022 | ~$6.1M | Verify | First year with 10-year grants |

### Edge Cases to Test

| Scenario | Company/Example | Expected Handling |
|----------|-----------------|-------------------|
| Multiple PEOs | CEO transition | Separate rows per PEO |
| Negative CAP | 2022 tech companies | Valid; capture as negative |
| Missing CSM | Some early filings | Use null/empty |
| Non-calendar FY | Apple, Walmart | Match to correct fiscal year |

---

## Applicability Matrix

| Fortune Year | Fiscal Years Available in PvP | Notes |
|--------------|------------------------------|-------|
| 2024 list | FY2023, FY2022, FY2021 | Full phase-in |
| 2023 list | FY2022, FY2021, FY2020 | First filing year |
| 2022 list | N/A | PvP not yet required |
| 2021 list | N/A | PvP not yet required |
| 2020 list | N/A | PvP not yet required |

**Key insight**: For the full 5-year analysis (2020-2024), PvP/CAP data is only available for FY2020+ from 2023+ filings. For FY2019 and earlier, must rely on Option Exercises + Stock Vested table (see POC 5).

---

## Output Validation

```bash
# Check PvP extraction count (should be ~200 company-years)
wc -l neo_compensation_pvp.csv
# Expected: ~200-300 rows (100 companies × 2-3 applicable years)

# Verify no missing CAP values
grep ",," neo_compensation_pvp.csv | grep "peo_compensation_actually_paid" | wc -l
# Expected: 0

# Check for negative CAP values (valid but notable)
awk -F',' '$5 < 0' neo_compensation_pvp.csv | wc -l
# Shows count of negative CAP records (especially 2022)

# Cross-reference with SCT data
# Should join cleanly on (cik, fiscal_year)
```

---

## Integration with POC 3

```python
def merge_sct_and_pvp(sct_df: pd.DataFrame, pvp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge Summary Compensation Table and Pay vs Performance data.
    
    For years with both:
    - Use SCT for component breakdown
    - Use PvP for "Compensation Actually Paid"
    
    For years without PvP (pre-FY2020):
    - Use SCT only
    - Calculate proxy for "realized" using Option Exercises table
    """
    # Filter SCT to CEOs only for comparison
    sct_ceos = sct_df[sct_df['is_ceo']].copy()
    
    # Merge on CIK + fiscal year
    merged = sct_ceos.merge(
        pvp_df[['cik', 'fiscal_year', 'peo_compensation_actually_paid', 'peo_sct_total']],
        on=['cik', 'fiscal_year'],
        how='left',
        suffixes=('_sct', '_pvp')
    )
    
    # Add realized pay column (CAP if available, else null)
    merged['realized_pay'] = merged['peo_compensation_actually_paid']
    
    return merged
```

---

## Estimated Runtime

- PvP section detection: ~0.1 seconds per file
- LLM extraction: ~2-3 seconds per file
- Validation: ~0.1 seconds per record
- **Total for ~100 applicable filings**: ~15-20 minutes
