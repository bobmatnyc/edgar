# Fortune 100 Pipeline Re-run Results

## Execution Summary
- **Duration**: 13.8s
- **Companies Tested**: 10 (Ranks 1-10)
- **Date**: 2025-12-29

## Success Rates Comparison

### DEF 14A (Executive Compensation)
- **Current Run**: 7/10 (70.0%)
- **Previous Run**: 7/10 (70.0%)
- **Status**: ✅ SAME (as expected)

**Failed Companies** (same as before):
1. Amazon.com Inc. - Summary Compensation Table not found
2. Berkshire Hathaway Inc. - Summary Compensation Table not found
3. Exxon Mobil Corp. - Summary Compensation Table not found

### 10-K (Corporate Tax)
- **Current Run**: 10/10 (100.0%)
- **Previous Run**: 10/10 (100.0%)
- **Status**: ✅ SAME (maintained perfect rate)

## Tax Extraction Quality

### ✅ IMPROVEMENT VERIFIED: Total Tax Expense Extracted

**Apple Inc. (AAPL)**:
- FY 2025: $20,719M (previously $0)
- FY 2024: $29,749M (previously $0)
- FY 2023: $16,741M (previously $0)

**Alphabet Inc. (GOOGL)**:
- FY 2024: $19,697M (previously $0)
- FY 2023: $11,922M (previously $0)

**Other Companies with Tax Data**:
- Berkshire Hathaway: $20,815M (FY 2024), $23,019M (FY 2023)
- Walmart: $3,367M (FY 2024), $3,478M (FY 2023)
- CVS Health: $476M (FY 2024), $1,658M (FY 2023)
- McKesson: $878M (FY 2025), $629M (FY 2024)
- Cencora: $484,702M (FY 2025) - ⚠️ Unusually high, needs verification

## Issues Still Present

### ❌ Component Tax Fields Still Zero
All companies show $0 for:
- current_federal, current_state, current_foreign
- deferred_federal, deferred_state, deferred_foreign
- pretax_income
- cash_taxes_paid

**Example** (Apple FY 2025):
- total_tax_expense: $20,719M ✅
- current_federal: $0 ❌
- current_state: $0 ❌
- current_foreign: $0 ❌
- pretax_income: $0 ❌

### ⚠️ Data Quality Concern
**Cencora Inc. (COR)**: 
- FY 2025: $484,702M total tax (seems anomalously high)
- FY 2024: $428,260M total tax
- Needs manual verification - possible extraction error

## Verification Status

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| DEF 14A Success Rate | 70% | 70% | ✅ |
| 10-K Success Rate | 100% | 100% | ✅ |
| Apple Tax (FY 2025) | ~$20B | $20.7B | ✅ |
| Alphabet Tax (FY 2024) | ~$19B | $19.7B | ✅ |
| Component Tax Fields | Non-zero | All $0 | ❌ |

## Conclusion

**Improvements Verified**:
1. ✅ Total tax expense now extracted correctly ($20.7B for Apple vs previous $0)
2. ✅ Alphabet tax data extracted ($19.7B)
3. ✅ Success rates maintained at expected levels

**Remaining Work**:
1. ❌ Component tax fields (federal/state/foreign, current/deferred) still not extracted
2. ❌ Pretax income not extracted
3. ❌ Cash taxes paid not extracted
4. ⚠️ Need to verify Cencora's unusually high tax amounts
