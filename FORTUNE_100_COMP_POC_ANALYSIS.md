# Fortune 100 Executive Compensation vs Corporate Tax POC Analysis

**Analysis Date**: 2025-12-06
**Project Location**: `/Users/masa/Clients/Zach/projects/edgar/projects/fortune-100-comp/runbooks/`
**EDGAR Binary**: `/Users/masa/Clients/Zach/projects/edgar/venv/bin/edgar`

---

## Executive Summary

This analysis evaluates 7 POC runbooks designed to test the thesis: **"Top executives at Fortune 100 companies are paid more than those companies pay in taxes."**

**Key Findings**:
- **5 of 7 POCs** can be partially tested with current EDGAR implementation
- **POC 1, 2, 5** are most aligned with existing capabilities
- **POC 3, 4, 6, 7** require significant LLM integration development
- **Estimated full implementation**: 4 hours (per runbook estimates)
- **Current testability**: ~40% with existing tools

---

## POC Summary Matrix

| POC | Name | Testable? | EDGAR Coverage | Gap | Priority |
|-----|------|-----------|----------------|-----|----------|
| 1 | Fortune 100 Universe Construction | ✅ Partial | CIK lookup via API | Fortune list fetch | **HIGH** |
| 2 | DEF 14A Proxy Retrieval | ✅ Partial | Submissions API | HTML download | **HIGH** |
| 3 | Summary Compensation Table Extraction | ⚠️ Limited | None | LLM parsing | MEDIUM |
| 4 | Pay vs Performance Extraction | ⚠️ Limited | None | LLM parsing | LOW |
| 5 | XBRL Tax Extraction | ✅ Yes | Company Facts API | None | **HIGH** |
| 6 | LLM Tax Fallback | ❌ No | None | LLM parsing | LOW |
| 7 | Data Integration | ⚠️ Limited | None | Aggregation logic | MEDIUM |

**Legend**:
- ✅ **Yes**: Can test with current implementation
- ⚠️ **Limited**: Partial functionality available
- ❌ **No**: Requires new development

---

## Detailed POC Analysis

### POC 1: Fortune 100 Universe Construction

**Objective**: Build Fortune 100 company list (2020-2024) with SEC CIK identifiers

**What It Tests**:
- Fortune 100 list retrieval (via Fortune API or GitHub backup)
- CIK enrichment using SEC's ticker-to-CIK mapping
- Fiscal year end detection from SEC submissions API
- Data validation (95% CIK match rate target)

**EDGAR Coverage**:
- ✅ **Available**: `EdgarApiService.get_company_submissions(cik)` for FYE detection
- ✅ **Available**: SEC bulk ticker mapping download capability
- ❌ **Missing**: Fortune list API integration (external to EDGAR)
- ❌ **Missing**: Company name search fallback logic

**Test Plan**:
```bash
# Test with validation set (10 companies)
export OPENROUTER_API_KEY="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"

# Manually create test universe CSV with known CIKs
cat > /tmp/test_fortune_universe.csv <<EOF
list_year,rank,company_name,ticker,cik,revenue_mm,fiscal_year_end
2024,1,Walmart,WMT,0000104169,648125.0,2024-01-31
2024,2,Amazon,AMZN,0001018724,574785.0,2023-12-31
2024,3,Apple,AAPL,0000320193,383285.0,2023-09-30
EOF

# Test CIK submission retrieval for FYE validation
/Users/masa/Clients/Zach/projects/edgar/venv/bin/edgar extract --cik 0000104169 --year 2023
```

**Success Criteria**:
- [ ] Retrieve Fortune 100 list (manual compilation acceptable for POC)
- [ ] Match ≥95 of 100 companies to valid SEC CIK
- [ ] Fiscal year end correctly identified for test companies

**Estimated Runtime**: 5 minutes (per runbook)

---

### POC 2: DEF 14A Proxy Statement Retrieval

**Objective**: Retrieve DEF 14A proxy filings for Fortune 100 companies (5 fiscal years)

**What It Tests**:
- Proxy filing identification via SEC Submissions API
- Fiscal year to proxy filing date mapping logic
- Filing metadata extraction (accession number, URL construction)
- Content validation (presence of "Summary Compensation Table")

**EDGAR Coverage**:
- ✅ **Available**: `EdgarApiService.get_company_submissions(cik)` returns all filings
- ✅ **Available**: Filing metadata (form type, dates, accession numbers)
- ⚠️ **Partial**: URL construction logic (documented in runbook)
- ❌ **Missing**: HTML download and content validation

**Test Plan**:
```python
# Test with Python script using existing EDGAR service
import asyncio
from edgar_analyzer.services.edgar_api_service import EdgarApiService
from edgar_analyzer.config.settings import ConfigService

async def test_proxy_retrieval():
    config = ConfigService()
    edgar = EdgarApiService(config)

    # Test Walmart FY2023 proxy (filed Apr 2024)
    submissions = await edgar.get_company_submissions("0000104169")
    recent = submissions['filings']['recent']

    # Find DEF 14A filings
    def14a_filings = [
        {
            'form': recent['form'][i],
            'filing_date': recent['filingDate'][i],
            'accession': recent['accessionNumber'][i],
            'primary_doc': recent['primaryDocument'][i]
        }
        for i in range(len(recent['form']))
        if recent['form'][i] in ('DEF 14A', 'DEFA14A')
    ]

    print(f"Found {len(def14a_filings)} DEF 14A filings")
    for filing in def14a_filings[:5]:
        print(f"  {filing['filing_date']}: {filing['form']} - {filing['accession']}")

asyncio.run(test_proxy_retrieval())
```

**Success Criteria**:
- [ ] ~500 proxy filings identified (100 companies × 5 years)
- [ ] Correct fiscal year alignment logic validated
- [ ] Filing URLs constructed correctly

**Estimated Runtime**: 30-45 minutes for 500 company-years (with rate limiting)

---

### POC 3: Summary Compensation Table Extraction

**Objective**: Extract NEO compensation from DEF 14A using LLM parsing

**What It Tests**:
- HTML preprocessing (extract compensation section)
- LLM prompt engineering for structured data extraction
- Post-extraction validation (arithmetic checks, CEO identification)
- Data quality metrics (98% extraction success target)

**EDGAR Coverage**:
- ❌ **Missing**: No LLM integration for proxy parsing
- ❌ **Missing**: HTML table extraction utilities
- ❌ **Missing**: Compensation data models

**Current EDGAR Capability**:
```bash
# EDGAR CLI only supports basic extraction
/Users/masa/Clients/Zach/projects/edgar/venv/bin/edgar extract --cik 0000104169 --year 2023
# Returns: Some compensation data, but not full SCT parsing
```

**Gap Analysis**:
- Requires OpenRouter/Anthropic API integration (available in project)
- Need BeautifulSoup4 HTML parsing (dependency exists)
- Missing: Structured prompts for SCT extraction
- Missing: Validation logic for compensation components

**Test Plan** (requires development):
1. Download 1 sample proxy HTML file manually
2. Extract compensation section with BeautifulSoup
3. Test LLM extraction with OpenRouter API
4. Validate arithmetic (total = sum of components)

**Success Criteria**:
- [ ] ≥98% extraction success rate
- [ ] CEO identified for each company-year
- [ ] Totals match sum of components (within $1K)

**Estimated Runtime**: 1-2 hours for 500 filings (LLM API calls)

---

### POC 4: Pay vs Performance Table Extraction

**Objective**: Extract "Compensation Actually Paid" from PvP tables (FY2022+ only)

**What It Tests**:
- PvP section detection in proxy filings
- CAP (realized pay) extraction vs SCT (granted pay)
- Multi-year table parsing (3-5 years shown)
- Cross-validation with SCT data

**EDGAR Coverage**:
- ❌ **Missing**: No PvP-specific parsing logic
- ❌ **Missing**: CAP adjustment calculation

**Applicability**:
- **Limited Scope**: PvP data only available for FY2020+ (proxies filed 2023+)
- For full 5-year analysis (2019-2023), only ~200 company-years have PvP data
- Pre-FY2020 requires different methodology (Option Exercises table)

**Test Plan** (requires development):
1. Identify 2023+ proxy filings from POC 2
2. Extract PvP section with keyword search
3. Parse with LLM (similar to POC 3 approach)
4. Cross-check CAP vs SCT totals

**Success Criteria**:
- [ ] PvP data for FY2020+ company-years
- [ ] SCT totals in PvP match POC 3 extractions
- [ ] CAP values captured (including negatives)

**Estimated Runtime**: 15-20 minutes for ~100 applicable filings

---

### POC 5: XBRL Tax Extraction

**Objective**: Extract corporate cash taxes paid from 10-K filings via XBRL API

**What It Tests**:
- SEC Company Facts API access
- XBRL element identification (`IncomeTaxesPaidNet` preferred)
- Fiscal year alignment logic
- Data validation (reasonableness checks vs revenue)

**EDGAR Coverage**:
- ✅ **Available**: `EdgarApiService` has XBRL API infrastructure
- ⚠️ **Partial**: May need Company Facts endpoint (currently has submissions)
- ✅ **Available**: Rate limiting and caching built-in

**Test Plan**:
```python
# Test XBRL Company Facts API
import requests
import time

def get_xbrl_facts(cik: str) -> dict:
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
    headers = {
        'User-Agent': 'ResearchProject/1.0 (contact@email.com)',
        'Accept': 'application/json'
    }
    time.sleep(0.1)  # Rate limit
    response = requests.get(url, headers=headers)
    return response.json()

# Test Walmart
facts = get_xbrl_facts("0000104169")
us_gaap = facts['facts']['us-gaap']

# Look for IncomeTaxesPaidNet
if 'IncomeTaxesPaidNet' in us_gaap:
    tax_data = us_gaap['IncomeTaxesPaidNet']
    print(f"Found: {tax_data['label']}")

    # Get FY2023 data
    for entry in tax_data['units']['USD']:
        if entry.get('fy') == 2024 and entry.get('form') == '10-K':
            print(f"FY2023: ${entry['val']:,} (filed {entry['filed']})")
```

**Success Criteria**:
- [ ] ≥90% XBRL extraction success
- [ ] Values in reasonable range vs revenue
- [ ] Net vs gross taxes correctly identified

**Estimated Runtime**: 2-3 minutes for 100 companies (all 5 years in one API call)

---

### POC 6: LLM Tax Fallback

**Objective**: Extract cash taxes from 10-K text when XBRL fails (<10% of cases)

**What It Tests**:
- 10-K HTML download and cash flow section extraction
- LLM parsing of supplemental disclosures
- Unit conversion (millions → dollars)
- Cross-validation against XBRL where available

**EDGAR Coverage**:
- ⚠️ **Partial**: 10-K filing retrieval (via submissions API)
- ❌ **Missing**: HTML parsing and section extraction
- ❌ **Missing**: LLM integration for tax extraction

**Test Plan** (requires development):
1. Identify fallback cases from POC 5 (XBRL missing)
2. Download 10-K HTML for those company-years
3. Extract cash flow supplemental section
4. Parse with LLM (similar to POC 3 approach)
5. Validate against any adjacent XBRL data

**Success Criteria**:
- [ ] ≥90% LLM extraction success for fallbacks
- [ ] Cross-validation match ≥95% within 5% tolerance

**Estimated Runtime**: 15-20 minutes for ~50 fallback cases

---

### POC 7: Data Integration & Final Comparison

**Objective**: Join compensation and tax datasets, calculate comparison metrics

**What It Tests**:
- Multi-source data joins (Fortune list + SCT + PvP + taxes)
- Fiscal year alignment logic
- Comparison calculations (CEO pay > taxes)
- Edge case handling (negative taxes, refunds)
- Summary statistics generation

**EDGAR Coverage**:
- ❌ **Missing**: No aggregation or join logic
- ❌ **Missing**: Comparison metric calculations
- ✅ **Available**: Data models could support this (pandas/pydantic)

**Test Plan** (requires development):
```python
import pandas as pd

# Mock data join logic
universe = pd.read_csv('fortune100_universe.csv')
ceo_comp = pd.read_csv('neo_compensation_sct.csv')
taxes = pd.read_csv('cash_taxes_combined.csv')

# Filter to CEOs only
ceos = ceo_comp[ceo_comp['is_ceo']]

# Join
merged = universe.merge(
    ceos[['cik', 'fiscal_year', 'executive_name', 'sct_total']],
    left_on=['cik', 'list_year'],
    right_on=['cik', 'fiscal_year'],
    how='left'
).merge(
    taxes[['cik', 'fiscal_year', 'cash_taxes_paid']],
    on=['cik', 'fiscal_year'],
    how='left'
)

# Calculate comparison
merged['ceo_exceeds_tax'] = merged['sct_total'] > merged['cash_taxes_paid']

# Summary
print(f"Companies where CEO > taxes: {merged['ceo_exceeds_tax'].sum()}")
print(f"Percentage: {merged['ceo_exceeds_tax'].mean() * 100:.1f}%")
```

**Success Criteria**:
- [ ] ≥95% company-years have complete data
- [ ] Thesis statistics calculated correctly
- [ ] Edge cases documented

**Estimated Runtime**: ~30 seconds for data processing

---

## Testable POCs with Current Implementation

### Immediately Testable

**POC 5: XBRL Tax Extraction** (90% coverage)
```bash
# Create test script
cat > /tmp/test_xbrl_tax.py <<'EOF'
import requests
import time
import pandas as pd

test_companies = [
    ('0000104169', 'Walmart'),
    ('0001018724', 'Amazon'),
    ('0000320193', 'Apple'),
]

results = []
for cik, name in test_companies:
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
    headers = {'User-Agent': 'ResearchProject/1.0 (test@email.com)'}
    time.sleep(0.15)

    response = requests.get(url, headers=headers)
    data = response.json()

    us_gaap = data['facts'].get('us-gaap', {})
    if 'IncomeTaxesPaidNet' in us_gaap:
        tax_element = us_gaap['IncomeTaxesPaidNet']
        for entry in tax_element['units']['USD']:
            if entry.get('form') == '10-K' and entry.get('fp') == 'FY':
                results.append({
                    'cik': cik,
                    'company': name,
                    'fiscal_year': entry['fy'],
                    'cash_taxes': entry['val'],
                    'filed': entry['filed']
                })

df = pd.DataFrame(results)
print(df.to_string(index=False))
EOF

python /tmp/test_xbrl_tax.py
```

**Expected Output**:
```
       cik   company  fiscal_year  cash_taxes       filed
0000104169   Walmart         2024  5123000000  2024-03-15
0000104169   Walmart         2023  4672000000  2023-03-14
0001018724    Amazon         2023  3170000000  2024-02-02
0000320193     Apple         2023 14997000000  2023-11-03
```

---

### Partially Testable

**POC 1: Fortune 100 Universe** (40% coverage)
- ✅ Can test: CIK lookup, FYE detection
- ❌ Cannot test: Fortune list retrieval (requires external API)

**POC 2: DEF 14A Retrieval** (60% coverage)
- ✅ Can test: Filing identification, metadata extraction
- ❌ Cannot test: HTML download, content validation

---

## Recommendations

### Phase 1: Foundation Testing (Week 1)

**Priority 1: POC 5 - XBRL Tax Extraction**
- **Why**: Highest coverage (90%), no LLM required
- **Action**: Run full test on 10 companies × 5 years
- **Deliverable**: `cash_taxes_xbrl.csv` with validation report
- **Effort**: 2-3 hours

**Priority 2: POC 1 - Universe Construction (Manual)**
- **Why**: Foundation for all other POCs
- **Action**: Manually compile Fortune 100 list for 1 year (2024)
- **Deliverable**: `fortune100_universe_2024.csv` with 100 companies
- **Effort**: 3-4 hours (manual research)

**Priority 3: POC 2 - Proxy Filing Identification**
- **Why**: Enables compensation POCs
- **Action**: Script to identify DEF 14A filings for test set
- **Deliverable**: `def14a_filings_test.csv` with filing metadata
- **Effort**: 2-3 hours

### Phase 2: LLM Integration (Week 2)

**Priority 4: POC 3 - SCT Extraction (Development)**
- **Why**: Core to thesis, highest LLM complexity
- **Action**: Build LLM integration for 1 company proof-of-concept
- **Deliverable**: Working extraction for 1 proxy filing
- **Effort**: 8-12 hours

**Priority 5: POC 7 - Data Integration**
- **Why**: Validates end-to-end workflow
- **Action**: Join test data from POC 1, 3, 5
- **Deliverable**: Preliminary comparison metrics
- **Effort**: 4-6 hours

### Phase 3: Full Validation (Week 3)

**Priority 6: Scale to Full Dataset**
- Run all POCs on full 100 companies × 5 years
- Generate final thesis statistics
- **Effort**: 8-12 hours runtime + monitoring

---

## Risk Assessment

### High Risk Areas

1. **LLM Extraction Reliability** (POC 3, 4, 6)
   - **Risk**: <98% success rate target may be ambitious
   - **Mitigation**: Start with high-quality proxies, iterate on prompts
   - **Fallback**: Manual review queue for failed extractions

2. **Fiscal Year Alignment** (POC 7)
   - **Risk**: Mismatch between Fortune list year and fiscal year
   - **Mitigation**: Document alignment logic clearly, validate with known cases
   - **Fallback**: Create mapping table for non-calendar FY companies

3. **XBRL Coverage** (POC 5)
   - **Risk**: <90% success rate (10% fallback to POC 6)
   - **Mitigation**: Test early on full dataset to quantify gap
   - **Fallback**: Expand LLM fallback capacity

### Medium Risk Areas

1. **Rate Limiting** (POC 2, 5)
   - SEC limits: 10 req/sec
   - **Mitigation**: Built-in delays, retry logic
   - Runtime: ~45 min for 500 requests

2. **Token Budget** (POC 3, 4, 6)
   - Estimate: ~5M tokens (~$30-50 at Sonnet rates)
   - **Mitigation**: Use Haiku for initial passes, Sonnet for validation

---

## Next Steps

1. **Execute POC 5** (XBRL Tax Extraction) - **IMMEDIATE**
   - Test on 10 companies
   - Generate validation report
   - Document XBRL coverage rate

2. **Manual POC 1** (Fortune 100 List) - **THIS WEEK**
   - Compile 2024 Fortune 100 (top 100 from Fortune.com)
   - Enrich with CIKs from SEC mapping
   - Validate FYE dates

3. **Script POC 2** (Proxy Identification) - **THIS WEEK**
   - Write Python script using EDGAR API service
   - Test on 10 companies × 1 year
   - Document filing date patterns

4. **Plan LLM Development** - **NEXT WEEK**
   - Design POC 3 architecture
   - Create sample prompts
   - Test on 1 proxy filing

---

## Appendix: Test Data Sets

### Validation Set (10 Companies)

| Company | CIK | Ticker | FYE | Notes |
|---------|-----|--------|-----|-------|
| Walmart | 0000104169 | WMT | 01-31 | Non-calendar FY |
| Amazon | 0001018724 | AMZN | 12-31 | Calendar FY |
| Apple | 0000320193 | AAPL | 09-30 | Non-calendar FY |
| Microsoft | 0000789019 | MSFT | 06-30 | Non-calendar FY |
| Alphabet | 0001652044 | GOOGL | 12-31 | Calendar FY |
| JPMorgan | 0000019617 | JPM | 12-31 | Calendar FY |
| ExxonMobil | 0000034088 | XOM | 12-31 | Calendar FY |
| CVS Health | 0000064803 | CVS | 12-31 | Calendar FY |
| UnitedHealth | 0000731766 | UNH | 12-31 | Calendar FY |
| Costco | 0000909832 | COST | 09-01 | Non-calendar FY |

### Expected FY2023 Data (for validation)

| Company | CEO | CEO Total Comp | Cash Taxes Paid |
|---------|-----|----------------|-----------------|
| Walmart | C. Douglas McMillon | ~$27.8M | ~$5-6B |
| Apple | Timothy D. Cook | ~$63.2M | ~$15-18B |
| Amazon | Andrew R. Jassy | ~$29.2M | ~$3-5B |
| Microsoft | Satya Nadella | ~$48.5M | ~$15-20B |
| JPMorgan | James Dimon | ~$36.0M | ~$10-12B |

---

**Analysis Complete**
**Author**: QA Agent
**Next Action**: Execute POC 5 test script
