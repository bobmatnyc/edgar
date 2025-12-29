# SCT Extraction Regression Fix Summary

## Problem
While fixing Amazon/Berkshire SCT extraction in the previous commit, Apple extraction regressed from 5 executives to 0 executives.

## Root Causes

### 1. **Table Detection Issue** (Primary Regression)
**Problem**: Strategy 1 (content-based table detection) was finding **summary tables** instead of the full Summary Compensation Table.

- Apple has a **single-executive summary table** for Tim Cook (table #123) that contains all compensation keywords (salary, stock, total, year, exec titles, dollars)
- Strategy 1 was returning this summary table BEFORE Strategy 2 (header-based) could find the real SCT table
- The real SCT table (with all 5 executives) comes much later in the document

**Fix**: Added **executive count validation** to `_is_likely_compensation_table()`:
- Now requires at least **3 executive rows** (with titles) to be considered a valid SCT table
- This filters out single-executive summary tables like Apple's Tim Cook overview
- Allows Strategy 2 to run and find the real SCT table with all executives

### 2. **Header Row Extraction Issue**
**Problem**: Amazon and Berkshire were extracting **header rows** as executives (e.g., "Name and Principal Position", "Salary").

**Fix**: Enhanced `_is_header_row()` to:
- Check **all non-empty values**, not just the first column (handles tables with empty first column like Amazon)
- Added more header keywords: "salary", "bonus", "stock", "award", "option", "non-equity", "pension", "total", "compensation"
- Added multi-column header detection: if 3+ columns look like headers, it's a header row

### 3. **Total Compensation Parsing Bug** (Data Quality Issue)
**Problem**: Apple 2024 total compensation was **$34** instead of **$74,609,802**.

**Cause**: Apple's HTML table has **empty spacing cells** between data columns:
```html
<td>2024</td>
<td>&#160;</td>  <!-- Empty nbsp cell -->
<td>3,000,000</td>
<td>&#160;</td>  <!-- Empty nbsp cell -->
...
<td><sup>(3)(4)</sup>&#160;</td>  <!-- Footnote marker -->
<td>&#160;</td>  <!-- Empty nbsp cell -->
<td>74,609,802</td>  <!-- Total -->
```

The old code filtered `if v` BEFORE cleaning, which kept nbsp cells and footnote markers, causing incorrect indexing.

**Fix**: Rewrote `_parse_compensation_row()` monetary value extraction:
- Filter out empty/whitespace-only cells **after stripping**
- Skip footnote markers like `(1)`, `(2)`, `(3)(4)`
- Convert to numbers and keep all valid values (including 0)
- This correctly identifies the 5 compensation columns for Apple's condensed format

## Test Results

### Before Fix
- ✅ Amazon: 8 executives (but 1 was header row)
- ✅ Berkshire: 9 executives (but 1 was header row)
- ❌ Apple: **0 executives** (regression!)

### After Fix
- ✅ Apple: **5 executives**, total=$74.6M ✓
- ✅ Amazon: 7 executives (header removed), total=$1.36M ✓
- ✅ Berkshire: 8 executives (header removed), total=$405K (Buffett) ✓

All 20 unit and integration tests pass, including:
- 10 unit tests (existing)
- 5 end-to-end tests (existing, now passing with correct total)
- 5 regression tests (new)

## Regression Tests Created

Created comprehensive regression test suite (`tests/integration/test_sct_extraction_regression.py`):

1. **`test_apple_extraction`**: Standard format with "Summary Compensation Table" header
2. **`test_amazon_extraction`**: Non-standard format with empty first column
3. **`test_berkshire_extraction`**: Simplified format with fewer columns
4. **`test_all_companies_no_header_rows`**: Ensures no header rows extracted as executives
5. **`test_all_companies_minimum_executives`**: Validates ≥5 executives for each company

These tests prevent future regressions when modifying the extractor.

## Key Changes

### Modified Files
- `src/edgar/extractors/sct/extractor.py`:
  - `_is_likely_compensation_table()`: Added executive count validation (requires ≥3 execs)
  - `_is_header_row()`: Enhanced header detection with more keywords and multi-column check
  - `_parse_compensation_row()`: Fixed monetary value extraction to handle empty cells and footnotes

### New Files
- `tests/integration/test_sct_extraction_regression.py`: Regression test suite for Apple/Amazon/Berkshire

## Lessons Learned

1. **Table Detection Strategy Order Matters**: Content-based detection (Strategy 1) must be **more selective** than header-based (Strategy 2) to avoid false positives
2. **Validate Table Structure**: Checking for compensation keywords isn't enough - must validate **table shape** (multiple executives)
3. **Test All Cases**: Fixing one company (Amazon) can break another (Apple) if test coverage isn't comprehensive
4. **HTML Quirks**: Different companies use different HTML structures (empty cells, footnotes, rowspans) - must handle all variants

## Verification

Run the regression tests:
```bash
uv run pytest tests/integration/test_sct_extraction_regression.py -v
```

All tests should pass with ≥5 executives for each company.
