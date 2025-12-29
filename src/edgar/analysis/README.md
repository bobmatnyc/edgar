# Executive Compensation vs. Corporate Tax Analysis Module

This module provides tools for analyzing the relationship between executive compensation and corporate tax payments for Fortune 100 companies.

## Overview

The `edgar.analysis` module compares:
- **Executive Compensation** (from DEF 14A proxy statements)
- **Corporate Tax Data** (from 10-K annual reports)

It generates comprehensive metrics and rankings to understand compensation-to-tax ratios across companies.

## Features

- **Single Company Analysis**: Analyze individual company metrics
- **Batch Analysis**: Compare multiple companies with rankings
- **Summary Statistics**: Aggregate metrics across all companies
- **CEO Detection**: Automatically identifies CEO and their compensation
- **Robust Handling**: Handles edge cases (missing data, zero tax, negative tax)

## Installation

The module is part of the EDGAR platform. No additional installation required.

```python
from edgar.analysis import CompTaxAnalyzer, CompTaxAnalysis, BatchAnalysisSummary
```

## Quick Start

### Single Company Analysis

```python
from edgar.analysis import CompTaxAnalyzer
from edgar.data.fortune100 import Company
from edgar.extractors.sct.models import SCTData
from edgar.extractors.tax.models import TaxData

# Initialize analyzer
analyzer = CompTaxAnalyzer()

# Prepare data (from extractors)
company = Company(rank=1, name="Test Corp", ticker="TEST", cik="0000012345", sector="Tech")
sct_data = SCTData(...)  # Executive compensation data
tax_data = TaxData(...)  # Corporate tax data

# Analyze
analysis = analyzer.analyze_single(company, sct_data, tax_data, fiscal_year=2023)

# Access results
print(f"Total Exec Compensation: ${analysis.total_exec_comp:,.0f}")
print(f"Total Tax Expense: ${analysis.total_tax_expense:,.0f}")
print(f"Comp/Tax Ratio: {analysis.comp_to_tax_ratio:.4f}")
```

### Batch Analysis with Rankings

```python
# Prepare multiple companies
results = [
    (company1, sct_data1, tax_data1),
    (company2, sct_data2, tax_data2),
    (company3, sct_data3, tax_data3),
]

# Analyze with rankings
analyses = analyzer.analyze_batch(results, fiscal_year=2023)

# Rankings are populated
for analysis in sorted(analyses, key=lambda a: a.ratio_rank):
    print(f"{analysis.company}: Ratio Rank #{analysis.ratio_rank}")
```

### Generate Summary Statistics

```python
# Generate aggregate metrics
summary = analyzer.generate_summary(analyses)

print(f"Total Companies: {summary.num_companies}")
print(f"Average Comp/Tax Ratio: {summary.avg_comp_to_tax_ratio:.4f}")
print(f"Highest Ratio Company: {summary.max_ratio_company}")
```

## Data Models

### CompTaxAnalysis

Main analysis result containing:

**Company Info:**
- `company`, `ticker`, `cik`, `rank`, `fiscal_year`

**Executive Compensation Metrics:**
- `num_executives`, `total_exec_comp`, `ceo_name`, `ceo_comp`
- `median_exec_comp`, `avg_exec_comp`

**Corporate Tax Metrics:**
- `total_tax_expense`, `current_tax`, `deferred_tax`
- `effective_tax_rate`, `cash_taxes_paid`, `pretax_income`

**Comparison Ratios:**
- `comp_to_tax_ratio` = total_exec_comp / total_tax_expense
- `ceo_to_tax_ratio` = ceo_comp / total_tax_expense
- `comp_to_pretax_ratio` = total_exec_comp / pretax_income
- `comp_to_cash_tax_ratio` = total_exec_comp / cash_taxes_paid

**Rankings** (populated in batch analysis):
- `comp_rank`, `tax_rank`, `ratio_rank`

### BatchAnalysisSummary

Aggregate statistics across all companies:

**Compensation Stats:**
- `total_exec_comp_all`, `avg_exec_comp_per_company`, `median_exec_comp_per_company`
- `max_exec_comp_company`, `max_exec_comp`

**Tax Stats:**
- `total_tax_all`, `avg_tax_per_company`, `median_tax_per_company`
- `avg_effective_rate`

**Ratio Stats:**
- `avg_comp_to_tax_ratio`, `median_comp_to_tax_ratio`
- `max_ratio_company`, `max_ratio`

## Edge Cases Handled

1. **Missing Data**: Returns zero values for missing years
2. **Zero Tax**: Avoids division by zero (returns 0.0 for ratios)
3. **Negative Tax**: Handles tax benefits correctly (allows negative ratios)
4. **Empty Datasets**: Gracefully handles empty executive/tax lists
5. **No CEO**: Returns empty string and 0.0 when CEO not found

## CEO Detection

The analyzer automatically detects CEOs using common title patterns:
- "Chief Executive Officer"
- "CEO"
- "President and CEO"
- "Chairman and CEO"
- "President & CEO"

## Testing

The module has 100% test coverage. Run tests:

```bash
uv run pytest tests/unit/test_comp_tax_analyzer.py -v
```

## Example

See `examples/comp_tax_analysis_demo.py` for a complete working example:

```bash
uv run python examples/comp_tax_analysis_demo.py
```

## Architecture

- **models.py**: Pydantic data models for analysis results
- **analyzer.py**: Core analysis logic and ranking algorithms
- **__init__.py**: Public API exports

## Dependencies

- `pydantic`: Data validation and models
- `statistics`: Statistical calculations (median, mean)
- `edgar.data.fortune100`: Company registry
- `edgar.extractors.sct`: Executive compensation data
- `edgar.extractors.tax`: Corporate tax data

## Future Enhancements

Potential improvements:
- Industry/sector comparisons
- Time-series trend analysis
- Percentile rankings
- Outlier detection
- Export to CSV/JSON
- Visualization generation

## License

Part of the EDGAR platform. See main repository for license.
