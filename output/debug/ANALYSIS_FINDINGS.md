# EDGAR Extractor Pattern Analysis

## Executive Summary

Analysis of failed extractions revealed that **Berkshire Hathaway uses a simplified compensation table** with only 3 columns instead of the standard 8 columns used by most companies. The current extractor requires at least 5 monetary values and fails when encountering this simplified format.

---

## DEF 14A (Summary Compensation Table) Findings

### Failed Companies
1. **Amazon.com Inc.** (CIK: 0001018724)
2. **Berkshire Hathaway Inc.** (CIK: 0001067983) ⚠️ **Root Cause Identified**
3. **Exxon Mobil Corporation** (CIK: 0000034088)

### Root Cause: Berkshire Hathaway Simplified Table

**Berkshire's Table Structure:**
```
| Name and Principal Position | Year | Salary | Bonus | All Other Compensation | Total Compensation |
```

**Standard Table Structure (Apple, Microsoft, etc.):**
```
| Name | Year | Salary | Bonus | Stock | Options | Non-Equity | Pension | Other | Total |
```

**Key Difference:**
- **Berkshire**: 4 monetary columns (Salary, Bonus, Other, Total)
- **Standard**: 8 monetary columns (Salary, Bonus, Stock, Options, Non-Equity, Pension, Other, Total)

**Current Extractor Logic:**
```python
if len(monetary_values) >= 8:
    # Full table with all columns
    ...
elif len(monetary_values) >= 5:
    # Condensed table (Apple style)
    ...
else:
    # Not enough data - FAILS HERE for Berkshire
    return None
```

**Berkshire's Data:**
- Warren Buffett 2024: `[100000, 0, 305111, 405111]` → 4 values
- This fails the `>= 5` check!

---

## Solution for SCT Extractor

### Add Support for 3-Column Simplified Table

```python
def _parse_compensation_row(self, values: list[str]) -> CompensationYear | None:
    """Parse a row of compensation data."""
    # Find year...
    monetary_values = [self._to_number(v) for v in values_after_year if v]

    try:
        if len(monetary_values) >= 8:
            # Full table: Salary, Bonus, Stock, Options, Non-Equity, Pension, Other, Total
            ...
        elif len(monetary_values) >= 5:
            # Condensed table (Apple): Salary, Stock, Non-Equity, Other, Total
            ...
        elif len(monetary_values) >= 4:
            # ✅ NEW: Simplified table (Berkshire): Salary, Bonus, Other, Total
            return CompensationYear(
                year=year,
                salary=monetary_values[0],
                bonus=monetary_values[1],
                other_compensation=monetary_values[2],
                total=monetary_values[3],
                stock_awards=0.0,
                option_awards=0.0,
                non_equity_incentive=0.0,
                pension_change=0.0,
            )
        else:
            return None
    except (IndexError, ValueError):
        return None
```

---

## 10-K (Income Tax) Findings

### Analysis Results

**Apple Inc. (CIK: 0000320193):**
- ✅ Tax table found: Table #19 contains provision for income taxes
- Structure: Simple summary table with years and tax rates
- **Pattern**: Year-based summary, NOT detailed breakdown by federal/state/foreign

**Microsoft Corporation (CIK: 0000789019):**
- ⚠️ Tax keywords found but in wrong tables (incorporation state, business description)
- Need better filtering to find actual tax provision tables

**Alphabet Inc. (CIK: 0001652044):**
- Similar to Apple - summary tables instead of detailed breakdowns

### Root Cause: Tax Table Detection

The current extractor looks for tables with:
```python
location_indicators = ["federal", "state", "foreign"]
timing_indicators = ["current", "deferred"]
has_location = any(indicator in text for indicator in location_indicators)
has_timing = any(indicator in text for indicator in timing_indicators)
return has_location and has_timing
```

**Problem**: Some companies use **simplified tax tables** without detailed current/deferred breakdowns!

**Example - Apple's Table:**
```
|  | 2025 |  | 2024 |  | 2023 |
| Provision for income taxes | $ 20,719 | $ 29,749 | $ 16,741 |
| Effective tax rate | 15.6% | 24.1% | 14.7% |
| Statutory federal income tax rate | 21% | 21% | 21% |
```

**No "federal", "state", "foreign", "current", or "deferred" keywords!**

---

## Solution for Tax Extractor

### Update `_looks_like_tax_table` to Support Simplified Tables

```python
def _looks_like_tax_table(self, table: Tag) -> bool:
    """Check if table looks like an income tax expense table."""
    text = table.get_text().lower()

    # Pattern 1: Detailed table (current implementation)
    location_indicators = ["federal", "state", "foreign"]
    timing_indicators = ["current", "deferred"]
    has_location = any(indicator in text for indicator in location_indicators)
    has_timing = any(indicator in text for indicator in timing_indicators)

    if has_location and has_timing:
        return True

    # ✅ NEW Pattern 2: Simplified summary table
    # Look for "provision for income taxes" or "income tax expense" WITH years
    has_provision = "provision for income tax" in text or "income tax expense" in text
    has_years = bool(re.search(r'20[12][0-9]', text))  # Years like 2020-2029

    if has_provision and has_years:
        return True

    return False
```

### Add Fallback Extraction for Simplified Tables

```python
def _extract_tax_years(self, table: Tag) -> list[TaxYear]:
    """Extract tax year data from income tax expense table."""
    # Try detailed extraction first (current implementation)
    detailed_results = self._extract_detailed_tax_years(table)

    if detailed_results:
        return detailed_results

    # ✅ NEW: Fallback to simplified extraction
    return self._extract_simplified_tax_years(table)

def _extract_simplified_tax_years(self, table: Tag) -> list[TaxYear]:
    """Extract from simplified tax summary tables (Apple, Alphabet style)."""
    # Look for row with "provision for income tax" or "income tax expense"
    # Extract total tax expense for each year
    # Create TaxYear with total_tax_expense only (other fields = 0.0)
    ...
```

---

## Action Items

### High Priority
1. ✅ **SCT Extractor**: Add `len(monetary_values) >= 4` case for Berkshire-style simplified tables
2. ✅ **Tax Extractor**: Update `_looks_like_tax_table` to detect simplified summary tables
3. ✅ **Tax Extractor**: Add `_extract_simplified_tax_years` fallback method

### Testing
4. Re-run extraction on failed companies to verify fixes
5. Ensure no regressions on previously working companies (Apple, Microsoft)

---

## Expected Improvements

### DEF 14A (SCT)
- **Before**: 3 failures (Amazon, Berkshire, Exxon)
- **After**: 0-1 failures (Berkshire fixed, Amazon/Exxon may have other issues)

### 10-K (Tax)
- **Before**: ~40% returning $0 (simplified tables not detected)
- **After**: <10% failures (only companies with truly unusual formats)

---

## Implementation Priority

1. **Start with SCT** - simpler fix, clear root cause
2. **Then Tax** - more complex, requires fallback extraction logic
3. **Verify both** - re-run pipeline on failed companies
