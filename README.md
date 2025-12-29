# EDGAR Platform

**E**xample-**D**riven **G**eneration with **A**I **R**easoning

AI-powered data extraction platform for SEC filings with self-refining extractors. Generates production-ready Python code from examples using Claude Sonnet 4.5.

## Features

- **SEC EDGAR Integration**: Extract data from DEF 14A (proxy statements) and 10-K (annual reports)
- **Fortune 100 Analysis**: Batch processing with rate limiting for all Fortune 100 companies
- **Executive Compensation**: Extract Summary Compensation Table (SCT) data
- **Corporate Tax**: Extract income tax expense and effective tax rates
- **Self-Refining**: Automatic analysis of extraction failures with pattern-based improvements
- **Type-Safe**: Pydantic models with full type hints and validation

## Quick Start

### 1. Setup

```bash
cd /Users/masa/Projects/edgar
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure API Key

Create `.env` file:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
EDGAR_MODEL=anthropic/claude-sonnet-4
```

### 3. Run Tests

```bash
pytest                           # All tests
pytest tests/unit/               # Unit tests only
pytest tests/integration/        # Integration tests
```

### 4. Run Fortune 100 Analysis

```bash
# Full Fortune 100 pipeline (100 companies)
python scripts/fortune100_analysis.py --companies 1-100 -v

# Quick test with top 10
python scripts/fortune100_analysis.py --companies 1-10 -v
```

**Output Files** (`output/fortune100/`):
- `executive_compensation.csv` - Individual executive compensation records
- `corporate_tax.csv` - Corporate tax expense by fiscal year
- `compensation_vs_tax.csv` - Combined analysis with ratios

## Pipeline Success Rates

| Extraction Type | Success Rate |
|-----------------|--------------|
| DEF 14A (Executive Comp) | 88% |
| 10-K (Corporate Tax) | 81% |
| Combined (Both) | 79% |

## Project Structure

```
edgar/
├── src/edgar/
│   ├── extractors/
│   │   ├── sct/              # Summary Compensation Table extractor
│   │   └── tax/              # Income Tax extractor
│   ├── services/
│   │   ├── sec_edgar_client.py   # SEC EDGAR API client
│   │   ├── batch_processor.py    # Rate-limited batch processing
│   │   └── pattern_analyzer.py   # Transformation pattern detection
│   ├── data/
│   │   └── fortune100.py         # Fortune 100 company registry
│   ├── exporters/
│   │   └── csv_exporter.py       # CSV export utilities
│   ├── analysis/
│   │   └── analyzer.py           # Comp vs. Tax analysis
│   └── refinement/
│       └── refiner.py            # Self-refinement engine
├── scripts/
│   ├── fortune100_analysis.py    # Main pipeline script
│   └── refine_extractors.py      # Self-refinement CLI
└── tests/
    ├── unit/
    └── integration/
```

## Self-Refinement

EDGAR automatically analyzes extraction failures and improves its extractors:

```bash
# Analyze recent failures
python scripts/refine_extractors.py --analyze

# Apply suggested improvements
python scripts/refine_extractors.py --apply
```

The self-refinement cycle:
1. **Run Pipeline** → Identify failures
2. **Analyze Patterns** → Detect common issues
3. **Apply Fixes** → Update extractors
4. **Verify** → Run regression tests
5. **Iterate** → Continuous improvement

## Development

### Code Quality

```bash
mypy src/                    # Type checking
ruff check src/              # Linting
black src/                   # Formatting
pytest --cov=edgar           # Coverage
```

### Requirements

- Python 3.11+
- OpenRouter API Key (for Claude Sonnet access)
- See `pyproject.toml` for dependencies

## License

MIT License - See LICENSE file for details
