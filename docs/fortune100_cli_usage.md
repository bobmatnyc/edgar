# Fortune 100 CLI Commands - Usage Guide

## Overview

The Fortune 100 CLI commands provide a streamlined interface for extracting executive compensation (SCT) and tax expense data from SEC EDGAR filings for Fortune 100 companies.

## Architecture

```
Fortune 100 CLI Commands
├── fortune100 extract         # Full pipeline (SCT + Tax)
├── fortune100 extract-sct     # SCT only (DEF 14A)
├── fortune100 extract-tax     # Tax only (10-K)
└── fortune100 list            # List companies
```

**Integration:**
- **Adapter Layer**: `src/edgar_analyzer/extractors/fortune100/`
  - `SCTAdapter`: Wraps SCTExtractor for Meta-Extractor
  - `TaxAdapter`: Wraps TaxExtractor for Meta-Extractor
- **CLI Layer**: `src/edgar_analyzer/cli/commands/fortune100.py`
- **Registry**: `src/edgar_analyzer/extractors/registry.json`

## Installation

The commands are automatically registered when you import the main CLI:

```python
from edgar_analyzer.cli.main import cli
```

Or via command line:
```bash
python -m edgar_analyzer.cli.main fortune100 --help
```

## Available Commands

### 1. `fortune100 extract` - Full Pipeline

Extract both SCT (executive compensation) and Tax data for Fortune 100 companies.

**Usage:**
```bash
edgar fortune100 extract --rank-start 1 --rank-end 10 --output results/
```

**Options:**
- `--rank-start, -s`: Starting rank (default: 1)
- `--rank-end, -e`: Ending rank (default: 100)
- `--sector`: Filter by sector (e.g., Technology, Healthcare)
- `--output, -o`: Output directory (default: `output/fortune100`)
- `--format, -f`: Output format - `json`, `csv`, or `both` (default: json)
- `--max-concurrent`: Max concurrent workers (default: 5)
- `--verbose, -v`: Verbose output

**Example:**
```bash
# Extract top 10 companies with JSON output
edgar fortune100 extract --rank-start 1 --rank-end 10 --format json

# Extract Technology sector only
edgar fortune100 extract --sector Technology --output tech_results/

# Extract with verbose logging
edgar fortune100 extract -s 1 -e 5 -v
```

### 2. `fortune100 extract-sct` - SCT Only

Extract Summary Compensation Table data from DEF 14A proxy statements.

**Usage:**
```bash
edgar fortune100 extract-sct --rank-start 1 --rank-end 5 --format json
```

**Options:**
- Same as `extract` command

**Example:**
```bash
# Extract SCT data for top 5 companies
edgar fortune100 extract-sct --rank-start 1 --rank-end 5

# Extract Healthcare sector SCT data
edgar fortune100 extract-sct --sector Healthcare --output sct_healthcare/
```

### 3. `fortune100 extract-tax` - Tax Only

Extract Tax Expense data from 10-K annual reports.

**Usage:**
```bash
edgar fortune100 extract-tax --rank-start 1 --rank-end 10 --output results/
```

**Options:**
- Same as `extract` command

**Example:**
```bash
# Extract tax data for top 10 companies
edgar fortune100 extract-tax --rank-start 1 --rank-end 10

# Extract Financial sector tax data
edgar fortune100 extract-tax --sector Financial --format csv
```

### 4. `fortune100 list` - List Companies

List Fortune 100 companies with optional filtering.

**Usage:**
```bash
edgar fortune100 list --sector Technology
```

**Options:**
- `--rank-start, -s`: Start rank
- `--rank-end, -e`: End rank
- `--sector`: Filter by sector
- `--format, -f`: Output format - `table` or `json` (default: table)

**Example:**
```bash
# List all companies in table format
edgar fortune100 list

# List top 10 companies
edgar fortune100 list --rank-start 1 --rank-end 10

# List Technology sector as JSON
edgar fortune100 list --sector Technology --format json

# List Healthcare sector
edgar fortune100 list --sector Healthcare
```

**Output (Table Format):**
```
Fortune 100 Companies (10 total)
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Rank ┃ Company                       ┃ Ticker ┃ CIK        ┃ Sector     ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│    1 │ Walmart Inc.                  │ WMT    │ 0000104169 │ Retail     │
│    2 │ Amazon.com, Inc.              │ AMZN   │ 0001018724 │ Technology │
│    3 │ Apple Inc.                    │ AAPL   │ 0000320193 │ Technology │
...
└──────┴───────────────────────────────┴────────┴────────────┴────────────┘

By Sector:
  Energy: 1
  Financial: 1
  Healthcare: 4
  Retail: 1
  Technology: 3
```

## Output Format

### JSON Output (`--format json`)

```json
[
  {
    "company": {
      "rank": 1,
      "name": "Walmart Inc.",
      "ticker": "WMT",
      "cik": "0000104169",
      "sector": "Retail"
    },
    "sct_data": {
      "company": "Walmart Inc.",
      "cik": "0000104169",
      "executives": [
        {
          "name": "Doug McMillon",
          "title": "President and CEO",
          "compensation": [
            {
              "year": 2023,
              "salary": 1400000,
              "bonus": 2300000,
              "stock_awards": 17500000,
              ...
            }
          ]
        }
      ]
    },
    "tax_data": {
      "company": "Walmart Inc.",
      "fiscal_year_end": "2024-01-31",
      "tax_years": [
        {
          "year": 2023,
          "total_tax_expense": 6900000000,
          ...
        }
      ]
    }
  }
]
```

### CSV Output (`--format csv`)

Flattened CSV format with one row per company (not yet implemented).

## Registry Integration

The Fortune 100 adapters are registered in the Meta-Extractor registry:

```json
{
  "extractors": {
    "sct_fortune100_adapter": {
      "class_path": "edgar_analyzer.extractors.fortune100.sct_adapter.SCTAdapter",
      "confidence": 0.95,
      "description": "Fortune 100 Summary Compensation Table Adapter",
      "domain": "sct",
      "tags": ["fortune100", "adapter", "sct", "def14a", "compensation"]
    },
    "tax_fortune100_adapter": {
      "class_path": "edgar_analyzer.extractors.fortune100.tax_adapter.TaxAdapter",
      "confidence": 0.95,
      "description": "Fortune 100 Tax Expense Adapter",
      "domain": "tax",
      "tags": ["fortune100", "adapter", "tax", "10-k", "income-tax"]
    }
  }
}
```

## Progress Display

The CLI uses `rich` library for beautiful progress displays:

```
Fortune 100 Full Pipeline
  Ranks: 1-10
  Sector: All
  Output: output/fortune100
  Format: json
  Workers: 5

Processing companies...
⠋ Processing Apple Inc. (#3) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 30% • 0:00:15 • 0:00:35

Full Pipeline Summary:
  Total: 10
  Successful: 8
  Failed: 2
  Success Rate: 80.0%
```

## Error Handling

- **Graceful Failures**: If extraction fails for a company, it's logged and the pipeline continues
- **Verbose Mode**: Use `-v` flag to see detailed error messages
- **Logging**: All errors are logged to `logs/fortune100.log`

## Sectors Available

Current hardcoded sectors (to be replaced with database):
- Technology
- Healthcare
- Retail
- Energy
- Financial

## Limitations & TODOs

1. **Data Fetching**: Currently returns `None` (TODO: integrate EDGAR fetching)
2. **CSV Export**: Not yet implemented
3. **Concurrent Processing**: Max workers option present but not fully utilized
4. **Company List**: Hardcoded top 10 (TODO: load from database)
5. **Filing Retrieval**: Need to add SEC EDGAR API integration

## Development Notes

### Adding More Companies

Update `FORTUNE_100_COMPANIES` list in `fortune100.py`:

```python
FORTUNE_100_COMPANIES = [
    {"rank": 1, "name": "Walmart Inc.", "ticker": "WMT", "cik": "0000104169", "sector": "Retail"},
    # Add more...
]
```

### Extending Functionality

To add new commands:

```python
@fortune100_cli.command(name="analyze")
@click.option("--company", required=True)
def analyze_company(company: str):
    """Analyze a specific company."""
    # Implementation...
```

## Testing

Test individual commands:

```python
from edgar_analyzer.cli.commands.fortune100 import list_companies
import click

ctx = click.Context(list_companies)
ctx.invoke(list_companies, rank_start=1, rank_end=10, sector=None, format='table')
```

## See Also

- [Meta-Extractor Documentation](./meta_extractor.md)
- [Fortune 100 Adapter Layer](../src/edgar_analyzer/extractors/fortune100/README.md)
- [Extractor Registry](../src/edgar_analyzer/extractors/registry.json)
