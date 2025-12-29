# CSV Exporters

Export EDGAR extraction results to CSV format for analysis and reporting.

## Overview

The `CSVExporter` module provides functionality to export:
- **Executive Compensation** - Summary Compensation Table (SCT) data
- **Corporate Tax** - Income tax expense and effective tax rates
- **Combined Analysis** - Executive compensation vs corporate tax metrics

## Features

- **Type-Safe**: Full type hints and Pydantic model validation
- **Flexible**: Configurable output directory and filenames
- **Comprehensive**: Exports multi-year data with proper formatting
- **Well-Tested**: 98% test coverage with comprehensive test suite

## Installation

The exporter is included in the EDGAR platform package:

```bash
uv sync
```

## Usage

### Basic Example

```python
from pathlib import Path
from edgar.exporters import CSVExporter
from edgar.data.fortune100 import Company
from edgar.extractors.sct.models import SCTData
from edgar.extractors.tax.models import TaxData

# Initialize exporter
exporter = CSVExporter(output_dir=Path("output"))

# Export executive compensation
comp_results: list[tuple[Company, SCTData]] = [...]
comp_path = exporter.export_compensation(comp_results)
print(f"Exported to: {comp_path}")

# Export corporate tax data
tax_results: list[tuple[Company, TaxData]] = [...]
tax_path = exporter.export_tax(tax_results)
print(f"Exported to: {tax_path}")

# Export combined analysis
combined_path = exporter.export_combined(comp_results, tax_results)
print(f"Exported to: {combined_path}")
```

### Custom Filenames

```python
exporter = CSVExporter(output_dir=Path("reports"))

# Use custom filenames
exporter.export_compensation(results, filename="2024_exec_comp.csv")
exporter.export_tax(results, filename="2024_corp_tax.csv")
exporter.export_combined(
    comp_results,
    tax_results,
    filename="2024_analysis.csv"
)
```

## CSV Schemas

### Executive Compensation (`executive_compensation.csv`)

| Column | Type | Description |
|--------|------|-------------|
| rank | int | Fortune 100 rank |
| company | str | Company name |
| ticker | str | Stock ticker symbol |
| cik | str | SEC CIK number (10-digit) |
| fiscal_year | int | Fiscal year |
| executive_name | str | Executive name |
| title | str | Executive title/position |
| salary | float | Base salary (USD) |
| bonus | float | Discretionary bonus (USD) |
| stock_awards | float | Stock awards grant date value (USD) |
| option_awards | float | Option awards value (USD) |
| non_equity_incentive | float | Non-equity incentive compensation (USD) |
| pension_change | float | Change in pension value (USD) |
| other_comp | float | All other compensation (USD) |
| total_comp | float | Total compensation (USD) |

**Example:**
```csv
rank,company,ticker,cik,fiscal_year,executive_name,title,salary,bonus,stock_awards,option_awards,non_equity_incentive,pension_change,other_comp,total_comp
3,Apple Inc.,AAPL,0000320193,2024,Timothy D. Cook,CEO,"3,000,000.00",0.00,"58,128,634.00",0.00,"12,000,000.00",0.00,"1,523,232.00","74,651,866.00"
```

### Corporate Tax (`corporate_tax.csv`)

| Column | Type | Description |
|--------|------|-------------|
| rank | int | Fortune 100 rank |
| company | str | Company name |
| ticker | str | Stock ticker symbol |
| cik | str | SEC CIK number (10-digit) |
| fiscal_year | int | Fiscal year |
| current_federal | float | Current federal income tax (USD) |
| current_state | float | Current state income tax (USD) |
| current_foreign | float | Current foreign income tax (USD) |
| total_current | float | Total current tax expense (USD) |
| deferred_federal | float | Deferred federal income tax (USD) |
| deferred_state | float | Deferred state income tax (USD) |
| deferred_foreign | float | Deferred foreign income tax (USD) |
| total_deferred | float | Total deferred tax expense (USD) |
| total_tax_expense | float | Total income tax expense (USD) |
| pretax_income | float | Pre-tax income (USD) |
| effective_tax_rate | str | Effective tax rate (percentage) |
| cash_taxes_paid | float | Cash taxes paid (USD) |

**Example:**
```csv
rank,company,ticker,cik,fiscal_year,current_federal,current_state,current_foreign,total_current,deferred_federal,deferred_state,deferred_foreign,total_deferred,total_tax_expense,pretax_income,effective_tax_rate,cash_taxes_paid
3,Apple Inc.,AAPL,0000320193,2024,"12,500,000,000.00","1,200,000,000.00","8,000,000,000.00","21,700,000,000.00","-500,000,000.00","-50,000,000.00","200,000,000.00","-350,000,000.00","21,350,000,000.00","100,000,000,000.00",21.35%,"20,000,000,000.00"
```

### Combined Analysis (`compensation_vs_tax.csv`)

| Column | Type | Description |
|--------|------|-------------|
| rank | int | Fortune 100 rank |
| company | str | Company name |
| ticker | str | Stock ticker symbol |
| cik | str | SEC CIK number (10-digit) |
| fiscal_year | int | Fiscal year |
| num_executives | int | Number of named executives |
| total_exec_comp | float | Total executive compensation (USD) |
| ceo_name | str | CEO name |
| ceo_comp | float | CEO total compensation (USD) |
| median_exec_comp | float | Median executive compensation (USD) |
| total_tax_expense | float | Total income tax expense (USD) |
| effective_tax_rate | str | Effective tax rate (percentage) |
| cash_taxes_paid | float | Cash taxes paid (USD) |
| comp_to_tax_ratio | float | Total exec comp / total tax expense |
| ceo_to_tax_ratio | float | CEO comp / total tax expense |

**Example:**
```csv
rank,company,ticker,cik,fiscal_year,num_executives,total_exec_comp,ceo_name,ceo_comp,median_exec_comp,total_tax_expense,effective_tax_rate,cash_taxes_paid,comp_to_tax_ratio,ceo_to_tax_ratio
3,Apple Inc.,AAPL,0000320193,2024,2,"101,151,866.00",Timothy D. Cook,"74,651,866.00","50,575,933.00","21,350,000,000.00",21.35%,"20,000,000,000.00",0.004738,0.003497
```

## Advanced Usage

### Multi-Year Analysis

The exporter automatically handles multi-year data:

```python
# Export data spanning multiple fiscal years
comp_results = [
    (company, sct_data_with_2023_and_2024)
]

# Generates one row per executive per year
exporter.export_compensation(comp_results)
```

### Batch Processing

Export data for multiple companies:

```python
from edgar.data.fortune100 import Fortune100Registry

registry = Fortune100Registry.load_default()
companies = registry.get_by_rank_range(1, 10)  # Top 10

results = []
for company in companies:
    sct_data = extract_compensation(company)
    results.append((company, sct_data))

exporter.export_compensation(results, filename="fortune_top10.csv")
```

### Ratio Analysis

The combined export calculates key metrics:

```python
# Generates compensation-to-tax ratios for analysis
combined_path = exporter.export_combined(comp_results, tax_results)

# Load into pandas for further analysis
import pandas as pd
df = pd.read_csv(combined_path)
print(df[['company', 'comp_to_tax_ratio', 'ceo_to_tax_ratio']])
```

## Implementation Details

### Data Flow

1. **Input**: Lists of `(Company, SCTData)` and `(Company, TaxData)` tuples
2. **Processing**: Extract, format, and join data by CIK and fiscal year
3. **Output**: CSV files with proper formatting and headers

### Formatting

- **Currency**: Comma-separated with 2 decimal places (`1,234,567.89`)
- **Percentages**: Two decimal places with % sign (`21.35%`)
- **Ratios**: Six decimal places (`0.004738`)

### CEO Identification

The combined export identifies CEOs by searching for:
- "CEO" in title (case-insensitive)
- "Chief Executive" in title

## Testing

Run the test suite:

```bash
# All tests
uv run pytest tests/unit/test_csv_exporter.py -v

# With coverage
uv run pytest tests/unit/test_csv_exporter.py --cov=src/edgar/exporters --cov-report=term-missing
```

Current coverage: **98%**

## Demonstration

Run the demo script:

```bash
uv run python examples/demo_csv_export.py
```

This generates sample CSV files in the `demo_output/` directory.

## Architecture

```
edgar/exporters/
├── __init__.py          # Public API exports
├── csv_exporter.py      # CSVExporter implementation
└── README.md            # This file
```

### Key Components

- **CSVExporter**: Main class with three export methods
  - `export_compensation()`: Executive compensation CSV
  - `export_tax()`: Corporate tax CSV
  - `export_combined()`: Combined analysis CSV

- **Helper Methods**:
  - `_ensure_output_dir()`: Create output directory
  - `_format_currency()`: Format currency values
  - `_format_percent()`: Format percentage values

## Error Handling

The exporter handles:
- **Missing data**: Skips rows with incomplete data
- **Year mismatches**: Only exports matching fiscal years in combined analysis
- **Empty results**: Creates CSV with header only

## Performance

- **Memory efficient**: Streaming CSV writes
- **Fast**: Direct iteration without intermediate storage
- **Scalable**: Handles Fortune 100 dataset with ease

## Future Enhancements

Potential additions:
- JSON export format
- Excel (XLSX) export
- Custom column selection
- Filtering by date range or company
- Aggregate statistics

## License

Part of the EDGAR platform project.
