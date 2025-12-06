# POC 7: Data Integration & Final Comparison

## Objective
Join compensation and tax datasets, calculate comparison metrics, and produce the final analysis dataset for the thesis: "Top executives are paid more than their companies pay in taxes."

## Success Criteria
- [ ] Successfully join ≥95% of company-year records
- [ ] Handle fiscal year alignment correctly
- [ ] Calculate both granted and realized pay comparisons
- [ ] Produce publication-ready comparison table

## Dependencies
- **Requires**: POC 1 (`fortune100_universe.csv`)
- **Requires**: POC 3 (`neo_compensation_sct.csv`)
- **Requires**: POC 4 (`neo_compensation_pvp.csv`)
- **Requires**: POC 5 + POC 6 merged (`cash_taxes_combined.csv`)

---

## Input Files Summary

| File | Source | Key Columns |
|------|--------|-------------|
| `fortune100_universe.csv` | POC 1 | cik, list_year, company_name, rank |
| `neo_compensation_sct.csv` | POC 3 | cik, fiscal_year, executive_name, is_ceo, sct_total |
| `neo_compensation_pvp.csv` | POC 4 | cik, fiscal_year, peo_compensation_actually_paid |
| `cash_taxes_combined.csv` | POC 5+6 | cik, fiscal_year, cash_taxes_paid |

---

## Expected Output

### Primary Output: `exec_comp_vs_taxes.csv`

| Column | Type | Description |
|--------|------|-------------|
| fortune_year | int | Fortune 100 list year |
| fortune_rank | int | Rank (1-100) |
| cik | str | SEC CIK |
| company_name | str | Company name |
| ticker | str | Stock ticker |
| fiscal_year | int | Fiscal year of data |
| ceo_name | str | CEO name |
| ceo_granted_pay | int | CEO SCT Total |
| ceo_realized_pay | int | CEO CAP (if available) |
| total_neo_granted_pay | int | Sum of all NEO SCT totals |
| total_neo_realized_pay | int | Sum of all NEO CAP |
| neo_count | int | Number of NEOs |
| cash_taxes_paid | int | Company cash taxes |
| ceo_granted_exceeds_tax | bool | CEO granted > taxes |
| ceo_realized_exceeds_tax | bool | CEO realized > taxes |
| all_neo_exceeds_tax | bool | Total NEO granted > taxes |
| ceo_to_tax_ratio | float | CEO granted / taxes |
| neo_to_tax_ratio | float | Total NEO / taxes |

### Summary Output: `thesis_summary.csv`

| Column | Type | Description |
|--------|------|-------------|
| fiscal_year | int | Year |
| companies_analyzed | int | Count of companies |
| ceo_exceeds_count | int | Companies where CEO > taxes |
| ceo_exceeds_pct | float | Percentage |
| all_neo_exceeds_count | int | Companies where all NEO > taxes |
| all_neo_exceeds_pct | float | Percentage |
| median_ceo_pay | int | Median CEO pay |
| median_taxes | int | Median cash taxes |
| total_ceo_pay | int | Sum of CEO pay |
| total_taxes | int | Sum of cash taxes |

---

## Step 1: Aggregate Compensation Data

### CEO Pay Aggregation

```python
import pandas as pd

def aggregate_ceo_pay(sct_df: pd.DataFrame, pvp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate CEO compensation by company-year.
    
    Handles cases with multiple CEOs (mid-year transitions).
    """
    # Filter to CEOs only
    ceo_sct = sct_df[sct_df['is_ceo']].copy()
    
    # Aggregate by cik + fiscal_year (sum if multiple CEOs)
    ceo_agg = ceo_sct.groupby(['cik', 'fiscal_year']).agg({
        'executive_name': lambda x: ' / '.join(x),  # Combine names if multiple
        'sct_total': 'sum',
        'sct_salary': 'sum',
        'sct_stock_awards': 'sum',
        'sct_option_awards': 'sum',
    }).reset_index()
    
    ceo_agg.columns = [
        'cik', 'fiscal_year', 'ceo_name', 
        'ceo_granted_pay', 'ceo_salary', 'ceo_stock', 'ceo_options'
    ]
    
    # Merge PvP data for realized pay
    if pvp_df is not None and len(pvp_df) > 0:
        pvp_ceo = pvp_df[['cik', 'fiscal_year', 'peo_compensation_actually_paid']].copy()
        pvp_ceo.columns = ['cik', 'fiscal_year', 'ceo_realized_pay']
        
        ceo_agg = ceo_agg.merge(pvp_ceo, on=['cik', 'fiscal_year'], how='left')
    else:
        ceo_agg['ceo_realized_pay'] = None
    
    return ceo_agg
```

### Total NEO Aggregation

```python
def aggregate_all_neo_pay(sct_df: pd.DataFrame, pvp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate total NEO compensation (CEO + other NEOs) by company-year.
    """
    # Sum all NEOs
    neo_agg = sct_df.groupby(['cik', 'fiscal_year']).agg({
        'sct_total': 'sum',
        'executive_name': 'count',  # Count of NEOs
    }).reset_index()
    
    neo_agg.columns = ['cik', 'fiscal_year', 'total_neo_granted_pay', 'neo_count']
    
    # Add realized pay from PvP if available
    if pvp_df is not None and len(pvp_df) > 0:
        # PvP has CEO CAP + avg other NEO CAP
        # Need to calculate total: CEO CAP + (avg other NEO CAP × count of other NEOs)
        pvp_totals = pvp_df.copy()
        
        # Get NEO count from SCT
        neo_counts = sct_df.groupby(['cik', 'fiscal_year']).size().reset_index(name='count')
        pvp_totals = pvp_totals.merge(neo_counts, on=['cik', 'fiscal_year'], how='left')
        
        # Calculate: CEO CAP + avg_other_NEO_CAP × (neo_count - 1)
        pvp_totals['total_neo_realized_pay'] = (
            pvp_totals['peo_compensation_actually_paid'] + 
            pvp_totals['avg_neo_comp_actually_paid'] * (pvp_totals['count'] - 1)
        )
        
        neo_agg = neo_agg.merge(
            pvp_totals[['cik', 'fiscal_year', 'total_neo_realized_pay']],
            on=['cik', 'fiscal_year'],
            how='left'
        )
    else:
        neo_agg['total_neo_realized_pay'] = None
    
    return neo_agg
```

---

## Step 2: Join with Tax Data

### Primary Join

```python
def join_comp_and_taxes(
    ceo_df: pd.DataFrame,
    neo_df: pd.DataFrame,
    tax_df: pd.DataFrame,
    universe_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Join compensation and tax data with Fortune 100 universe.
    """
    # Start with universe
    result = universe_df.copy()
    
    # Join CEO comp
    result = result.merge(
        ceo_df,
        left_on=['cik', 'list_year'],  # Fortune list year = fiscal year covered
        right_on=['cik', 'fiscal_year'],
        how='left'
    )
    
    # Join total NEO comp
    result = result.merge(
        neo_df[['cik', 'fiscal_year', 'total_neo_granted_pay', 'total_neo_realized_pay', 'neo_count']],
        on=['cik', 'fiscal_year'],
        how='left'
    )
    
    # Join tax data
    result = result.merge(
        tax_df[['cik', 'fiscal_year', 'cash_taxes_paid']],
        on=['cik', 'fiscal_year'],
        how='left'
    )
    
    return result
```

### Fiscal Year Alignment Logic

```python
def align_fiscal_years(universe_df: pd.DataFrame) -> pd.DataFrame:
    """
    Map Fortune list year to fiscal year for compensation and tax data.
    
    Fortune 100 list is published in June based on prior fiscal year data.
    Example: 2024 Fortune 100 = companies ranked by FY2023 revenue
    
    For compensation analysis:
    - 2024 list → FY2023 comp data (from 2024 proxy)
    - 2023 list → FY2022 comp data (from 2023 proxy)
    """
    df = universe_df.copy()
    
    # Fortune list year - 1 = fiscal year of data
    df['fiscal_year'] = df['list_year'] - 1
    
    return df
```

**Note**: Verify this alignment logic. Some analyses may want:
- List year = fiscal year being compared
- List year - 1 = fiscal year of underlying data

Document the choice clearly for reproducibility.

---

## Step 3: Calculate Comparison Metrics

### Core Comparison Logic

```python
def calculate_comparisons(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate comparison metrics between compensation and taxes.
    """
    result = df.copy()
    
    # Boolean comparisons (granted pay)
    result['ceo_granted_exceeds_tax'] = result['ceo_granted_pay'] > result['cash_taxes_paid']
    result['all_neo_exceeds_tax'] = result['total_neo_granted_pay'] > result['cash_taxes_paid']
    
    # Boolean comparisons (realized pay) - only where available
    result['ceo_realized_exceeds_tax'] = (
        result['ceo_realized_pay'].notna() & 
        (result['ceo_realized_pay'] > result['cash_taxes_paid'])
    )
    
    # Ratios (handle division by zero and negative taxes)
    result['ceo_to_tax_ratio'] = result.apply(
        lambda r: calculate_ratio(r['ceo_granted_pay'], r['cash_taxes_paid']),
        axis=1
    )
    
    result['neo_to_tax_ratio'] = result.apply(
        lambda r: calculate_ratio(r['total_neo_granted_pay'], r['cash_taxes_paid']),
        axis=1
    )
    
    return result

def calculate_ratio(comp: float, taxes: float) -> float:
    """
    Calculate comp/tax ratio with edge case handling.
    """
    if pd.isna(comp) or pd.isna(taxes):
        return None
    
    if taxes == 0:
        return float('inf') if comp > 0 else 0
    
    if taxes < 0:
        # Negative taxes = net refund
        # Comp > 0 and taxes < 0 means comp definitely exceeds taxes
        return float('inf')
    
    return comp / taxes
```

---

## Step 4: Handle Edge Cases

### Negative Tax Handling

```python
def flag_special_cases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag records with special circumstances for analysis.
    """
    result = df.copy()
    
    # Net refund years
    result['tax_refund_year'] = result['cash_taxes_paid'] < 0
    
    # Zero tax years (but positive comp)
    result['zero_tax_year'] = (result['cash_taxes_paid'] == 0) & (result['ceo_granted_pay'] > 0)
    
    # Missing data flags
    result['missing_comp'] = result['ceo_granted_pay'].isna()
    result['missing_tax'] = result['cash_taxes_paid'].isna()
    
    # CEO transition year
    result['multi_ceo'] = result['ceo_name'].str.contains('/', na=False)
    
    return result
```

### Thesis Counting Logic

```python
def count_thesis_support(df: pd.DataFrame) -> dict:
    """
    Count companies supporting the thesis by various definitions.
    """
    # Exclude incomplete records
    complete = df[
        df['ceo_granted_pay'].notna() & 
        df['cash_taxes_paid'].notna()
    ].copy()
    
    # Definition 1: CEO granted > taxes
    ceo_granted = (complete['ceo_granted_pay'] > complete['cash_taxes_paid']).sum()
    
    # Definition 2: CEO realized > taxes (where available)
    realized_available = complete[complete['ceo_realized_pay'].notna()]
    ceo_realized = (realized_available['ceo_realized_pay'] > realized_available['cash_taxes_paid']).sum()
    
    # Definition 3: Total NEO granted > taxes
    neo_granted = (complete['total_neo_granted_pay'] > complete['cash_taxes_paid']).sum()
    
    # Definition 4: CEO > taxes, excluding refund years
    positive_tax = complete[complete['cash_taxes_paid'] > 0]
    ceo_vs_positive_tax = (positive_tax['ceo_granted_pay'] > positive_tax['cash_taxes_paid']).sum()
    
    return {
        'total_complete_records': len(complete),
        'ceo_granted_exceeds_count': ceo_granted,
        'ceo_granted_exceeds_pct': ceo_granted / len(complete) * 100,
        'ceo_realized_exceeds_count': ceo_realized,
        'ceo_realized_exceeds_pct': ceo_realized / len(realized_available) * 100 if len(realized_available) > 0 else None,
        'neo_granted_exceeds_count': neo_granted,
        'neo_granted_exceeds_pct': neo_granted / len(complete) * 100,
        'ceo_vs_positive_tax_count': ceo_vs_positive_tax,
        'ceo_vs_positive_tax_pct': ceo_vs_positive_tax / len(positive_tax) * 100 if len(positive_tax) > 0 else None,
    }
```

---

## Step 5: Generate Summary Statistics

### By Year Summary

```python
def generate_yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate summary statistics by fiscal year.
    """
    yearly = df.groupby('fiscal_year').apply(
        lambda g: pd.Series({
            'companies_analyzed': len(g[g['ceo_granted_pay'].notna() & g['cash_taxes_paid'].notna()]),
            'ceo_exceeds_count': (g['ceo_granted_exceeds_tax'] == True).sum(),
            'all_neo_exceeds_count': (g['all_neo_exceeds_tax'] == True).sum(),
            'median_ceo_pay': g['ceo_granted_pay'].median(),
            'median_taxes': g['cash_taxes_paid'].median(),
            'mean_ceo_pay': g['ceo_granted_pay'].mean(),
            'mean_taxes': g['cash_taxes_paid'].mean(),
            'total_ceo_pay': g['ceo_granted_pay'].sum(),
            'total_taxes': g['cash_taxes_paid'].sum(),
            'refund_years': (g['cash_taxes_paid'] < 0).sum(),
        })
    ).reset_index()
    
    # Calculate percentages
    yearly['ceo_exceeds_pct'] = yearly['ceo_exceeds_count'] / yearly['companies_analyzed'] * 100
    yearly['all_neo_exceeds_pct'] = yearly['all_neo_exceeds_count'] / yearly['companies_analyzed'] * 100
    
    return yearly
```

### Overall Summary

```python
def generate_overall_summary(df: pd.DataFrame) -> dict:
    """
    Generate overall thesis summary statistics.
    """
    complete = df[df['ceo_granted_pay'].notna() & df['cash_taxes_paid'].notna()]
    
    return {
        'analysis_period': f"FY{complete['fiscal_year'].min()}-{complete['fiscal_year'].max()}",
        'total_company_years': len(complete),
        'unique_companies': complete['cik'].nunique(),
        
        # Headline statistics
        'ceo_exceeds_tax_count': (complete['ceo_granted_exceeds_tax']).sum(),
        'ceo_exceeds_tax_pct': (complete['ceo_granted_exceeds_tax']).mean() * 100,
        
        # Financial totals
        'total_ceo_compensation': complete['ceo_granted_pay'].sum(),
        'total_corporate_taxes': complete['cash_taxes_paid'].sum(),
        'aggregate_ratio': complete['ceo_granted_pay'].sum() / complete['cash_taxes_paid'].sum(),
        
        # Distribution
        'median_ceo_pay': complete['ceo_granted_pay'].median(),
        'median_taxes': complete['cash_taxes_paid'].median(),
        'median_ratio': complete['ceo_to_tax_ratio'].median(),
    }
```

---

## Step 6: Validation

### Data Quality Checks

```python
def validate_final_dataset(df: pd.DataFrame) -> dict:
    """
    Run validation checks on final merged dataset.
    """
    issues = []
    
    # Check for expected record count
    expected_rows = 100 * 5  # 100 companies × 5 years
    if len(df) < expected_rows * 0.9:
        issues.append(f"Low record count: {len(df)} vs expected ~{expected_rows}")
    
    # Check for missing data
    missing_comp = df['ceo_granted_pay'].isna().sum()
    missing_tax = df['cash_taxes_paid'].isna().sum()
    
    if missing_comp > 25:  # > 5%
        issues.append(f"High missing comp: {missing_comp} records")
    
    if missing_tax > 25:
        issues.append(f"High missing tax: {missing_tax} records")
    
    # Check for data quality issues
    suspicious_ratios = df[df['ceo_to_tax_ratio'] > 100]
    if len(suspicious_ratios) > 10:
        issues.append(f"Many extreme ratios (>100x): {len(suspicious_ratios)} records")
    
    # Cross-check totals
    ceo_total = df['ceo_granted_pay'].sum()
    tax_total = df['cash_taxes_paid'].sum()
    
    return {
        'record_count': len(df),
        'complete_records': len(df[df['ceo_granted_pay'].notna() & df['cash_taxes_paid'].notna()]),
        'missing_comp': missing_comp,
        'missing_tax': missing_tax,
        'issues': issues,
        'ceo_total': ceo_total,
        'tax_total': tax_total,
    }
```

---

## Output Files

1. **`exec_comp_vs_taxes.csv`** - Full detail dataset
2. **`thesis_summary.csv`** - Year-by-year summary
3. **`thesis_headline.json`** - Key statistics for reporting
4. **`integration_validation.json`** - Data quality report

---

## Sample Output Format

### Headline Statistics (JSON)

```json
{
  "analysis_period": "FY2020-FY2024",
  "total_company_years": 487,
  "headline": "In X% of Fortune 100 company-years, the CEO was paid more than the company paid in federal income taxes",
  "ceo_exceeds_tax_count": 145,
  "ceo_exceeds_tax_pct": 29.8,
  "total_ceo_compensation_billions": 24.5,
  "total_corporate_taxes_billions": 285.3,
  "methodology_notes": [
    "CEO compensation uses Summary Compensation Table 'total' column (granted pay)",
    "Corporate taxes uses cash taxes paid from Statement of Cash Flows",
    "5-year period: fiscal years 2020-2024",
    "Fortune 100 membership tracked annually"
  ]
}
```

---

## Estimated Runtime

- Data loading: ~5 seconds
- Aggregation: ~10 seconds
- Joins: ~5 seconds
- Calculations: ~5 seconds
- Validation: ~5 seconds
- **Total**: ~30 seconds
