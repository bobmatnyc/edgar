# Fortune 100 Executive Comp vs. Corporate Tax Analysis
## POC Runbook Index

### Project Thesis
> "Top executives at Fortune 100 companies are paid more than those companies pay in taxes."

### Analysis Period
- **Fortune Lists**: 2020-2024
- **Fiscal Years**: 2019-2023 (data underlying each list)
- **Compensation Types**: Both "granted" (SCT) and "realized" (CAP) pay
- **Tax Measure**: Cash taxes paid (net of refunds)

---

## POC Execution Order

```
┌─────────────────────────────────────────────────────────────────┐
│                         POC 1                                   │
│              Fortune 100 Universe Construction                  │
│     (Company lists, CIKs, fiscal year ends)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│        POC 2            │   │        POC 5            │
│   DEF 14A Retrieval     │   │  XBRL Tax Extraction    │
│   (Proxy statements)    │   │  (Cash taxes paid)      │
└───────────┬─────────────┘   └───────────┬─────────────┘
            │                             │
     ┌──────┴──────┐                      ▼
     ▼             ▼              ┌───────────────┐
┌─────────┐   ┌─────────┐         │    POC 6      │
│  POC 3  │   │  POC 4  │         │  LLM Tax      │
│   SCT   │   │   PvP   │         │  Fallback     │
│Extract  │   │ Extract │         └───────┬───────┘
└────┬────┘   └────┬────┘                 │
     │             │                      │
     └──────┬──────┘                      │
            │                             │
            └─────────────┬───────────────┘
                          ▼
              ┌─────────────────────────┐
              │        POC 7            │
              │  Data Integration &     │
              │  Final Comparison       │
              └─────────────────────────┘
```

---

## POC Summary Table

| POC | Name | Input | Output | Est. Time |
|-----|------|-------|--------|-----------|
| 1 | Universe Construction | External APIs | `fortune100_universe.csv` | 5 min |
| 2 | DEF 14A Retrieval | POC 1 | `def14a_filings.csv` + HTML files | 45 min |
| 3 | SCT Extraction | POC 2 | `neo_compensation_sct.csv` | 2 hrs |
| 4 | PvP Extraction | POC 2 | `neo_compensation_pvp.csv` | 20 min |
| 5 | XBRL Tax Extraction | POC 1 | `cash_taxes_xbrl.csv` | 3 min |
| 6 | LLM Tax Fallback | POC 5 failures | `cash_taxes_llm.csv` | 20 min |
| 7 | Integration | POC 3,4,5,6 | `exec_comp_vs_taxes.csv` | 1 min |

**Total estimated time**: ~4 hours (mostly LLM processing in POC 3)

---

## File Manifest

### Intermediate Files

| File | Created By | Used By | Description |
|------|------------|---------|-------------|
| `fortune100_universe.csv` | POC 1 | POC 2,5,7 | Company list with CIKs |
| `def14a_filings.csv` | POC 2 | POC 3,4 | Proxy filing metadata |
| `filings/def14a/*.html` | POC 2 | POC 3,4 | Raw proxy HTML |
| `neo_compensation_sct.csv` | POC 3 | POC 7 | Summary Comp Table data |
| `neo_compensation_pvp.csv` | POC 4 | POC 7 | Pay vs Performance data |
| `cash_taxes_xbrl.csv` | POC 5 | POC 6,7 | XBRL-extracted tax data |
| `xbrl_fallback_required.csv` | POC 5 | POC 6 | XBRL extraction failures |
| `cash_taxes_llm.csv` | POC 6 | POC 7 | LLM-extracted tax data |

### Final Outputs

| File | Description |
|------|-------------|
| `exec_comp_vs_taxes.csv` | Full detail comparison dataset |
| `thesis_summary.csv` | Year-by-year summary statistics |
| `thesis_headline.json` | Key statistics for reporting |
| `data_quality_report.json` | Validation and coverage metrics |

---

## Validation Checkpoints

### After POC 1
- [ ] 100 companies per list year (or documented exceptions)
- [ ] ≥95% CIK match rate
- [ ] Fiscal year ends correctly identified

### After POC 2
- [ ] ~500 proxy filings retrieved
- [ ] All files contain "Summary Compensation Table"
- [ ] 2023+ files contain "Pay Versus Performance"

### After POC 3
- [ ] ≥98% extraction success rate
- [ ] CEO identified for each company-year
- [ ] Totals match sum of components (within $1K)

### After POC 4
- [ ] PvP data for FY2020+ company-years
- [ ] SCT totals in PvP match POC 3 extractions
- [ ] CAP values captured (including negatives)

### After POC 5
- [ ] ≥90% XBRL extraction success
- [ ] Values in reasonable range vs. company revenue
- [ ] Net vs. gross taxes correctly identified

### After POC 6
- [ ] ≥90% LLM extraction success for fallbacks
- [ ] Values cross-validated against available XBRL
- [ ] Clear documentation of remaining gaps

### After POC 7
- [ ] ≥95% company-years have complete data
- [ ] Thesis statistics calculated correctly
- [ ] Edge cases (refunds, zero taxes) documented

---

## Quick Start: Minimal Test Run

For initial validation, run each POC on a subset of 10 companies:

```python
TEST_CIKS = [
    '0000104169',  # Walmart
    '0001018724',  # Amazon
    '0000320193',  # Apple
    '0000789019',  # Microsoft
    '0001652044',  # Alphabet
    '0000019617',  # JPMorgan
    '0000034088',  # ExxonMobil
    '0000064803',  # CVS Health
    '0000731766',  # UnitedHealth
    '0000909832',  # Costco
]

TEST_YEARS = [2023]  # Single year first
```

**Expected runtime for test subset**: ~30 minutes total

---

## Common Issues & Resolutions

| Issue | POC | Resolution |
|-------|-----|------------|
| Rate limiting by SEC | 2,5 | Add delays, respect 10 req/sec |
| LLM parsing errors | 3,4,6 | Retry with cleaner input or manual review |
| Fiscal year mismatch | 7 | Verify alignment logic, check FYE |
| Missing CIK | 1 | Use company name search fallback |
| Private company | 1 | Exclude (document in notes) |
| CEO mid-year change | 3 | Sum both CEOs' compensation |
| Negative taxes | 5,6,7 | Valid - company received refund |

---

## API Rate Limits

| API | Limit | POC |
|-----|-------|-----|
| SEC EDGAR | 10 req/sec | 1,2,5,6 |
| Fortune API | Unknown (be respectful) | 1 |
| Anthropic Claude | Varies by tier | 3,4,6 |

---

## Token Budget Estimate (LLM Costs)

| POC | Calls | Tokens/Call | Total Tokens |
|-----|-------|-------------|--------------|
| 3 | ~500 | ~8,000 | ~4M |
| 4 | ~100 | ~6,000 | ~600K |
| 6 | ~50 | ~5,000 | ~250K |
| **Total** | | | **~5M tokens** |

At Claude 3.5 Sonnet pricing (~$3/M input, $15/M output), estimate ~$30-50 total.

---

## Notes for Publication

When presenting results, document:

1. **Methodology choices**
   - Granted vs. realized pay (and why both matter)
   - Cash taxes vs. provision (and why cash is more meaningful)
   - Fortune 100 scope (and excluded private companies)

2. **Limitations**
   - 5-year window may not capture full cycles
   - PvP data only available for recent years
   - Stock comp valuation is complex

3. **Edge cases**
   - Refund years inflate "exceeds" count
   - CEO transitions affect year-over-year comparisons
   - Fiscal year differences require careful alignment
