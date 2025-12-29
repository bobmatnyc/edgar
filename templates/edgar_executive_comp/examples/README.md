# EDGAR Executive Compensation Examples

This directory contains example input/output pairs that teach the platform how to extract and transform executive compensation data from SEC EDGAR proxy filings.

## Example Files

### Included Examples

1. **apple_2024.json** - Apple Inc. (Technology)
   - High stock-based compensation
   - Multiple fiscal years per executive
   - CEO with significant security costs

2. **microsoft_2023.json** - Microsoft Corporation (Technology)
   - Performance stock awards
   - Multiple executives with complete compensation breakdown

## Example Structure

Each example file contains:

```json
{
  "description": "Brief description of the example",
  "input": {
    "cik": "10-digit CIK",
    "company_name": "Company Name",
    "ticker": "TICKER",
    "fiscal_year": 2024,
    "filing_url": "URL to DEF 14A filing",
    "filing_date": "YYYY-MM-DD"
  },
  "output": {
    "company_name": "Company Name",
    "ticker": "TICKER",
    "cik": "0000123456",
    "filing_date": "YYYY-MM-DD",
    "fiscal_years": [2024, 2023, 2022],
    "executives": [
      {
        "name": "Executive Name",
        "position": "Title",
        "is_ceo": true/false,
        "is_cfo": true/false,
        "compensation_by_year": [
          {
            "year": 2024,
            "salary": 0,
            "bonus": 0,
            "stock_awards": 0,
            "option_awards": 0,
            "non_equity_incentive": 0,
            "change_in_pension": 0,
            "all_other_compensation": 0,
            "total": 0
          }
        ]
      }
    ]
  }
}
```

## How to Add More Examples

### 1. Identify a Company

Choose a company with public executive compensation data:
- Must have filed DEF 14A (proxy statement)
- Data available on SEC EDGAR: https://www.sec.gov/edgar/search/

### 2. Find the Filing

1. Go to https://www.sec.gov/edgar/search/
2. Search by company name or CIK
3. Filter by form type: "DEF 14A"
4. Find the Summary Compensation Table (usually Section titled "Executive Compensation")

### 3. Extract the Data

From the Summary Compensation Table, extract:
- Executive names and titles
- For each fiscal year:
  - Salary
  - Bonus
  - Stock Awards
  - Option Awards
  - Non-Equity Incentive Plan Compensation
  - Change in Pension Value
  - All Other Compensation
  - Total Compensation

### 4. Create Example File

Create `{company}_{year}.json` following the structure above:

```bash
# Template
cp apple_2024.json your_company_2024.json

# Edit the file with your data
vim your_company_2024.json
```

### 5. Validate the Example

Run validation to ensure correct structure:

```bash
python -m edgar_analyzer validate-example \
  examples/your_company_2024.json
```

## Data Sources

Examples should be based on real SEC EDGAR filings:
- **DEF 14A** - Proxy Statement (contains Summary Compensation Table)
- **XBRL data** - Structured financial data (if available)

## Quality Guidelines

### Good Examples
✅ Real data from SEC filings
✅ Multiple executives (5+ preferred)
✅ Multiple fiscal years (3 years ideal)
✅ Complete compensation breakdown
✅ CEO and CFO identified
✅ Footnotes included when relevant

### Avoid
❌ Incomplete compensation data
❌ Made-up or synthetic data
❌ Missing executive roles
❌ Inconsistent fiscal years
❌ Total doesn't equal sum of components

## Example Diversity

Aim for diversity across:
- **Industries**: Technology, Finance, Retail, Healthcare, Energy
- **Compensation Structures**:
  - Stock-heavy (Tech companies)
  - Bonus-heavy (Financial services)
  - Balanced (Traditional companies)
- **Company Sizes**: Large cap, mid cap, small cap
- **Fiscal Year Ends**: Different fiscal calendars

## Minimum Requirements

For effective pattern detection, you need:
- **At least 2 examples** (minimum for pattern detection)
- **Recommended 5+ examples** (better pattern learning)
- **10+ examples** (optimal for complex transformations)

## Testing Your Examples

After adding examples, test the extraction:

```bash
# Analyze patterns
python -m edgar_analyzer analyze-project edgar_executive_comp

# View detected patterns
python -m edgar_analyzer patterns edgar_executive_comp

# Generate extraction code
python -m edgar_analyzer generate-code edgar_executive_comp

# Test extraction
python -m edgar_analyzer run-extraction edgar_executive_comp \
  --cik 0000320193 --fiscal-year 2024
```

## Common Issues

### Issue: Total doesn't match sum
**Solution**: Recalculate. Total = Salary + Bonus + Stock + Options + Non-Equity + Pension Change + Other

### Issue: CIK not zero-padded
**Solution**: Ensure CIK is exactly 10 digits (e.g., "0000320193" not "320193")

### Issue: Missing fiscal years
**Solution**: Include at least 3 fiscal years for each top executive

### Issue: Unclear executive roles
**Solution**: Set `is_ceo` and `is_cfo` flags correctly based on title

## Resources

- [SEC EDGAR Search](https://www.sec.gov/edgar/search/)
- [DEF 14A Filing Guide](https://www.sec.gov/files/form-def14a.pdf)
- [Summary Compensation Table Requirements](https://www.sec.gov/divisions/corpfin/guidance/execcomp.htm)
- [Platform Pattern Detection Guide](../../../docs/guides/PATTERN_DETECTION.md)

## Support

For questions or issues with examples:
1. Check the [Platform Documentation](../../../docs/README.md)
2. Review existing examples for reference
3. Validate your example structure before adding
