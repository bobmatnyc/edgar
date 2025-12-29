# Fortune 100 Analysis Pipeline

## Overview

The Fortune 100 Analysis Pipeline orchestrates batch extraction and analysis of executive compensation (DEF 14A) and corporate tax data (10-K) for Fortune 100 companies.

## Architecture

### Components

```
Fortune100Pipeline
├── Fortune100Registry - Load Fortune 100 company data
├── SecEdgarClient - SEC EDGAR API client
├── BatchProcessor - Rate-limited batch processing
├── SCTExtractor - Summary Compensation Table extraction
├── TaxExtractor - Corporate tax data extraction
└── CSVExporter - CSV export functionality
```

### Execution Flow

```
Phase 1: Load Companies
  └── Fortune100Registry.get_by_rank_range(start, end)

Phase 2: DEF 14A Extraction (Executive Compensation)
  └── BatchProcessor.process_companies()
      ├── RateLimiter.acquire() - 8 req/sec
      ├── SecEdgarClient.get_latest_filing("DEF 14A")
      ├── SecEdgarClient.fetch_filing_html()
      └── SCTExtractor.extract()

Phase 3: 10-K Extraction (Corporate Tax)
  └── BatchProcessor.process_companies()
      ├── RateLimiter.acquire() - 8 req/sec
      ├── SecEdgarClient.get_latest_filing("10-K")
      ├── SecEdgarClient.fetch_filing_html()
      └── TaxExtractor.extract()

Phase 4: Export Results
  └── CSVExporter
      ├── export_compensation() - Executive compensation CSV
      ├── export_tax() - Corporate tax CSV
      └── export_combined() - Comparison analysis CSV
```

## Usage

### Command Line

```bash
# Full pipeline (all 100 companies)
python scripts/fortune100_analysis.py

# Top 10 companies only (for testing)
python scripts/fortune100_analysis.py --companies 1-10

# Specific fiscal year
python scripts/fortune100_analysis.py --year 2024

# Verbose output (show progress)
python scripts/fortune100_analysis.py -v

# Custom output directory
python scripts/fortune100_analysis.py --output ./analysis_results

# Skip phases (for incremental runs)
python scripts/fortune100_analysis.py --skip-def14a  # Only fetch tax data
python scripts/fortune100_analysis.py --skip-10k     # Only fetch compensation

# Combined options
python scripts/fortune100_analysis.py -c 1-20 -y 2024 -v -o ./output/top20
```

### Via CLI

```bash
# Using edgar CLI
edgar fortune100 -c 1-10 -v
```

### Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--companies` | `-c` | `1-100` | Company rank range (e.g., `1-10`) |
| `--year` | `-y` | Most recent | Specific fiscal year |
| `--output` | `-o` | `output/fortune100` | Output directory |
| `--verbose` | `-v` | `False` | Enable verbose output |
| `--concurrent` | - | `5` | Max concurrent requests |
| `--skip-def14a` | - | `False` | Skip DEF 14A extraction |
| `--skip-10k` | - | `False` | Skip 10-K extraction |

## Output Files

### Directory Structure

```
output/fortune100/
├── executive_compensation.csv   # One row per executive per year
├── corporate_tax.csv             # One row per company per year
├── compensation_vs_tax.csv       # Combined analysis
├── def14a_results.json           # DEF 14A extraction summary
├── 10k_results.json              # 10-K extraction summary
└── analysis_summary.json         # Overall analysis metrics
```

### CSV Schemas

#### executive_compensation.csv

| Column | Type | Description |
|--------|------|-------------|
| `rank` | int | Fortune 100 rank |
| `company` | string | Company name |
| `ticker` | string | Stock ticker symbol |
| `cik` | string | SEC CIK (10-digit) |
| `fiscal_year` | int | Fiscal year |
| `executive_name` | string | Executive full name |
| `title` | string | Executive title |
| `salary` | float | Base salary |
| `bonus` | float | Cash bonus |
| `stock_awards` | float | Stock awards value |
| `option_awards` | float | Option awards value |
| `non_equity_incentive` | float | Non-equity incentive |
| `pension_change` | float | Pension value change |
| `other_comp` | float | Other compensation |
| `total_comp` | float | Total compensation |

#### corporate_tax.csv

| Column | Type | Description |
|--------|------|-------------|
| `rank` | int | Fortune 100 rank |
| `company` | string | Company name |
| `ticker` | string | Stock ticker symbol |
| `cik` | string | SEC CIK (10-digit) |
| `fiscal_year` | int | Fiscal year |
| `current_federal` | float | Current federal tax |
| `current_state` | float | Current state tax |
| `current_foreign` | float | Current foreign tax |
| `total_current` | float | Total current tax |
| `deferred_federal` | float | Deferred federal tax |
| `deferred_state` | float | Deferred state tax |
| `deferred_foreign` | float | Deferred foreign tax |
| `total_deferred` | float | Total deferred tax |
| `total_tax_expense` | float | Total tax expense |
| `pretax_income` | float | Pretax income |
| `effective_tax_rate` | float | Effective tax rate (%) |
| `cash_taxes_paid` | float | Cash taxes paid |

#### compensation_vs_tax.csv

| Column | Type | Description |
|--------|------|-------------|
| `rank` | int | Fortune 100 rank |
| `company` | string | Company name |
| `ticker` | string | Stock ticker symbol |
| `cik` | string | SEC CIK (10-digit) |
| `fiscal_year` | int | Fiscal year |
| `num_executives` | int | Number of executives |
| `total_exec_comp` | float | Total executive compensation |
| `ceo_name` | string | CEO name |
| `ceo_comp` | float | CEO compensation |
| `median_exec_comp` | float | Median executive compensation |
| `total_tax_expense` | float | Total tax expense |
| `effective_tax_rate` | float | Effective tax rate (%) |
| `cash_taxes_paid` | float | Cash taxes paid |
| `comp_to_tax_ratio` | float | Total comp / tax expense |
| `ceo_to_tax_ratio` | float | CEO comp / tax expense |

### JSON Summaries

#### def14a_results.json

```json
{
  "total_companies": 10,
  "successful": 8,
  "failed": 2,
  "success_rate": 0.8,
  "total_duration": 45.2,
  "requests_made": 10,
  "failures": [
    {
      "company": "Company A",
      "rank": 5,
      "error": "No DEF 14A filing found"
    }
  ]
}
```

#### analysis_summary.json

```json
{
  "timestamp": "2024-12-28T23:15:00",
  "companies_analyzed": 8,
  "def14a_success_rate": 0.8,
  "form10k_success_rate": 0.9,
  "total_duration": 90.5
}
```

## Performance

### Rate Limiting

- **SEC EDGAR Policy**: Max 10 requests/second
- **Pipeline Setting**: 8 requests/second (conservative)
- **Concurrent Requests**: 5 (configurable via `--concurrent`)

### Estimated Duration

| Companies | Est. Duration | Requests |
|-----------|---------------|----------|
| 10 | ~3-5 sec | 20 (10 DEF 14A + 10 10-K) |
| 50 | ~12-15 sec | 100 |
| 100 | ~25-30 sec | 200 |

*Assumes successful requests with no retries*

### Retry Logic

- **Max Retries**: 3 attempts per request
- **Backoff**: Exponential (2s, 4s, 8s)
- **Error Isolation**: Individual failures don't stop batch

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "No DEF 14A filing found" | Company hasn't filed proxy yet | Wait for filing or use --year |
| "No 10-K filing found" | Company hasn't filed annual report | Wait for filing or use --year |
| "Rate limit exceeded" | Too many requests | Pipeline handles automatically |
| "Connection timeout" | Network issues | Automatic retry with backoff |

### Partial Results

The pipeline continues on individual failures:
- Successful extractions are exported to CSV
- Failed extractions are logged in JSON summaries
- Exit code is 0 if any extractions succeed

## Examples

### Test Run (Top 10)

```bash
python scripts/fortune100_analysis.py -c 1-10 -v
```

Output:
```
============================================================
Fortune 100 Executive Compensation vs. Corporate Tax Analysis
============================================================
Companies: Ranks 1-10
Output: output/fortune100

[23:15:00] Phase 1: Loading Companies
[23:15:00]   Loaded 10 companies (ranks 1-10)
[23:15:00] Phase 2: Fetching DEF 14A filings (Executive Compensation)
[23:15:00]   [1/10] Walmart Inc.
[23:15:01]   [2/10] Amazon.com Inc.
...
[23:15:05]   Success: 8/10
[23:15:05]   Failed: 2 companies
[23:15:05]     - Company A: No DEF 14A filing found
[23:15:05] Phase 3: Fetching 10-K filings (Corporate Tax)
...
[23:15:10]   Success: 9/10
[23:15:10] Phase 4: Exporting Results
[23:15:10]   Exported 6 files

============================================================
RESULTS
============================================================
Status: SUCCESS
Duration: 15.2s
Companies: 10
DEF 14A: 8 succeeded, 2 failed (80.0% success rate)
10-K: 9 succeeded, 1 failed (90.0% success rate)

Output Files (6):
  - output/fortune100/executive_compensation.csv
  - output/fortune100/def14a_results.json
  - output/fortune100/corporate_tax.csv
  - output/fortune100/10k_results.json
  - output/fortune100/compensation_vs_tax.csv
  - output/fortune100/analysis_summary.json
```

### Incremental Runs

If DEF 14A extraction already complete:

```bash
# Only extract tax data
python scripts/fortune100_analysis.py --skip-def14a
```

## Troubleshooting

### Script Not Found

```bash
# Ensure you're in project root
cd /Users/masa/Projects/edgar

# Run with python3
python3 scripts/fortune100_analysis.py --help
```

### Import Errors

```bash
# Verify src/ is in PYTHONPATH
export PYTHONPATH=/Users/masa/Projects/edgar/src:$PYTHONPATH
```

### Permission Denied

```bash
# Make script executable
chmod +x scripts/fortune100_analysis.py

# Run directly
./scripts/fortune100_analysis.py --help
```

## Development

### Adding New Extractors

1. Create extractor class implementing `IDataExtractor`
2. Update `_process_*` methods in `Fortune100Pipeline`
3. Add export logic in `_export_results`

### Customizing Rate Limits

```python
# In Fortune100Pipeline.__init__
self.rate_limiter = RateLimiter(requests_per_second=10.0)  # Max SEC limit
```

### Adding Progress Callbacks

```python
def custom_progress(current: int, total: int, company: str) -> None:
    print(f"Processing {company}... ({current}/{total})")

pipeline = Fortune100Pipeline(config)
# Progress callback used if config.verbose = True
```

## Related Documentation

- [SEC EDGAR Client](../src/edgar/services/sec_edgar_client.py)
- [Batch Processor](../src/edgar/services/batch_processor.py)
- [SCT Extractor](../src/edgar/extractors/sct/extractor.py)
- [Tax Extractor](../src/edgar/extractors/tax/extractor.py)
- [CSV Exporter](../src/edgar/exporters/csv_exporter.py)
