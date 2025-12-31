# EDGAR Data Sources for Executive Compensation vs Tax Expense Analysis

## Verified XBRL Tags for Tax Expense Data

### Primary Tax Expense Tags (✅ Confirmed Working)
- **`us-gaap:IncomeTaxExpenseBenefit`** - Total income tax expense/benefit
  - Most comprehensive tag for tax expense data
  - Available in 10-K and 10-Q filings
  - Tested successfully with Apple Inc. (CIK: 0000320193)

### Secondary Tax Expense Tags
- **`us-gaap:CurrentIncomeTaxExpenseBenefit`** - Current period tax expense
- **`us-gaap:DeferredIncomeTaxExpenseBenefit`** - Deferred tax expense
- **`us-gaap:IncomeTaxesPaid`** - Cash payments for income taxes
- **`us-gaap:FederalIncomeTaxExpenseBenefit`** - Federal tax expense only
- **`us-gaap:StateAndLocalIncomeTaxExpenseBenefit`** - State/local tax expense

## Executive Compensation Data Sources

### Primary Sources
1. **DEF 14A (Proxy Statements)**
   - Summary Compensation Table
   - Most reliable source for executive compensation
   - Filed annually before shareholder meetings
   - Contains detailed breakdown by executive

2. **Form 10-K (Annual Reports)**
   - Executive compensation disclosures
   - May have less detail than proxy statements
   - More readily available in XBRL format

3. **Form 8-K (Current Reports)**
   - Changes in executive compensation
   - New executive appointments
   - Compensation plan modifications

### XBRL Tags for Executive Compensation
- **`us-gaap:CompensationCostsShareBasedPayments`** - Stock-based compensation
- **`us-gaap:EmployeeBenefitsAndShareBasedCompensation`** - Total employee compensation
- Custom company-specific tags may be required for detailed executive data

## Filing Types and Frequencies

### Annual Filings
- **10-K**: Annual report with comprehensive financial data
- **DEF 14A**: Proxy statement with executive compensation details
- **Frequency**: Once per year

### Quarterly Filings
- **10-Q**: Quarterly report with updated financial data
- **Frequency**: 3 times per year (Q1, Q2, Q3)

## Data Extraction Strategy

### Tax Expense Data
1. **Primary Source**: 10-K annual filings for comprehensive annual tax expense
2. **Secondary Source**: 10-Q quarterly filings for interim data
3. **XBRL Path**: `facts.us-gaap.IncomeTaxExpenseBenefit.units.USD`
4. **Filter Criteria**: `form == '10-K'` and `fy == target_year`

### Executive Compensation Data
1. **Primary Source**: DEF 14A proxy statements
2. **Secondary Source**: 10-K executive compensation sections
3. **Extraction Method**: Text parsing of HTML/XML content
4. **Key Tables**: Summary Compensation Table, Grants of Plan-Based Awards

## Fortune 500 Company Identification

### Data Sources for Company Lists
1. **Fortune Magazine**: Official Fortune 500 list (annual)
2. **S&P 500**: Market cap-based list of large companies
3. **SEC Company Database**: All public companies with CIK numbers

### CIK Number Sources
- **SEC CIK Lookup**: https://www.sec.gov/search-filings/cik-lookup
- **Company Submissions API**: https://data.sec.gov/submissions/CIK{cik}.json
- **Bulk Data**: https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip

## API Endpoints and Rate Limits

### SEC EDGAR API Endpoints
- **Company Submissions**: `https://data.sec.gov/submissions/CIK{cik}.json`
- **Company Facts**: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
- **Frames**: `https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json`

### Rate Limits
- **Maximum**: 10 requests per second
- **Recommended**: 0.1 second delay between requests
- **Headers Required**: User-Agent with contact information

## Data Quality Considerations

### High Quality Data ✅
- Tax expense data in XBRL format (standardized)
- Large company filings (better compliance)
- Recent filings (2020+) have better XBRL coverage

### Potential Issues ⚠️
- Executive compensation may require text parsing
- Some companies use custom XBRL taxonomies
- Historical data may have incomplete XBRL tagging
- Timing differences between compensation and tax reporting periods

## Testing Results

### Successful API Tests ✅
- **Apple Inc. (CIK: 0000320193)**
  - Tax Expense 2025: $20,719,000,000
  - API response time: < 2 seconds
  - Data format: Clean XBRL structure

### Next Steps for Validation
1. Test additional Fortune 500 companies
2. Validate executive compensation data extraction
3. Build comprehensive company CIK database
4. Implement error handling for missing data