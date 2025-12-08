# EDGAR Executive Compensation Extraction Template

Extract executive compensation data from SEC EDGAR proxy filings (DEF 14A) using AI-powered pattern detection.

## Overview

This template provides a pre-configured project for extracting structured executive compensation data from SEC EDGAR filings. It uses the platform's AI capabilities to:

1. Access SEC EDGAR API and filing documents
2. Parse Summary Compensation Tables from proxy statements
3. Extract executive names, titles, and compensation components
4. Transform data into structured JSON/CSV/Excel formats
5. Validate totals and business logic

## Features

- **Automated SEC EDGAR Access**: Respects rate limits and user-agent requirements
- **AI-Powered Extraction**: Uses Sonnet 4.5 for intelligent table parsing
- **Multi-Year Support**: Extracts 3 years of compensation history
- **Comprehensive Validation**: Ensures data integrity and business logic
- **Multiple Output Formats**: JSON, CSV, and Excel
- **Caching**: Reduces API calls and speeds up re-runs
- **Checkpointing**: Resume after failures

## Prerequisites

### 1. Environment Variables

Add to `.env.local`:

```bash
# SEC EDGAR requires User-Agent identification
SEC_EDGAR_USER_AGENT="YourName YourEmail@example.com"

# OpenRouter API for AI extraction (Sonnet 4.5)
OPENROUTER_API_KEY="your_openrouter_api_key"
```

### 2. Install Platform

```bash
# Clone repository
git clone https://github.com/your-org/edgar.git
cd edgar

# Install dependencies
pip install -e ".[dev]"

# Verify installation
edgar --version
```

## Quick Start

### Method 1: Use Template Directly

```bash
# Copy template to your workspace
cp -r templates/edgar_executive_comp ~/my_projects/edgar_comp

# Navigate to project
cd ~/my_projects/edgar_comp

# Analyze project (detect patterns from examples)
edgar analyze-project .

# View detected patterns
edgar patterns .

# Generate extraction code
edgar generate-code .

# Run extraction for a company
edgar run-extraction . --cik 0000320193 --fiscal-year 2024
```

### Method 2: Create Project from Template

```bash
# Create new project using template
edgar project create my_comp_extraction --template edgar_executive_comp

# Navigate to project
cd projects/my_comp_extraction

# Customize project.yaml if needed
vim project.yaml

# Run analysis
edgar analyze-project .
```

### Method 3: Interactive Chat Mode

```bash
# Start chat mode with project loaded
edgar chat --project templates/edgar_executive_comp

# Interactive commands:
edgar> analyze
edgar> patterns
edgar> generate
edgar> extract --cik 0000320193
edgar> confidence 0.90
```

## Data Schema

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cik` | string | Yes | 10-digit CIK (zero-padded) |
| `fiscal_year` | integer | Yes | Fiscal year to extract |
| `company_name` | string | No | Company name (auto-detected) |
| `ticker` | string | No | Stock ticker (auto-detected) |

### Output Schema

```json
{
  "company_name": "Apple Inc.",
  "ticker": "AAPL",
  "cik": "0000320193",
  "filing_date": "2024-01-10",
  "fiscal_years": [2024, 2023, 2022],
  "executives": [
    {
      "name": "Timothy D. Cook",
      "position": "Chief Executive Officer",
      "is_ceo": true,
      "is_cfo": false,
      "compensation_by_year": [
        {
          "year": 2024,
          "salary": 3000000,
          "bonus": 0,
          "stock_awards": 58088946,
          "option_awards": 0,
          "non_equity_incentive": 12000000,
          "change_in_pension": 0,
          "all_other_compensation": 1520856,
          "total": 74609802
        }
      ]
    }
  ]
}
```

### Compensation Components

| Field | Description |
|-------|-------------|
| `salary` | Base salary |
| `bonus` | Cash bonus |
| `stock_awards` | Fair value of stock awards (FASB ASC 718) |
| `option_awards` | Fair value of option awards |
| `non_equity_incentive` | Performance-based cash incentives |
| `change_in_pension` | Change in pension value and deferred compensation |
| `all_other_compensation` | Perquisites, security costs, etc. |
| `total` | Sum of all components |

## Usage Examples

### Extract Single Company

```bash
# Apple Inc. for fiscal year 2024
edgar run-extraction . \
  --cik 0000320193 \
  --fiscal-year 2024

# Output: output/executive_comp_0000320193_2024.json
```

### Extract Multiple Companies

Create `companies.txt`:
```
0000320193,2024  # Apple
0000789019,2023  # Microsoft
0000066740,2023  # Walmart
0000019617,2023  # JPMorgan Chase
0001018724,2023  # Amazon
```

Run batch extraction:
```bash
edgar run-extraction . --companies-file companies.txt
```

### Customize Extraction

Edit `project.yaml` to modify:
- Output formats (JSON, CSV, Excel)
- Validation rules
- Confidence thresholds
- Caching behavior
- Rate limits

## Configuration

### Rate Limits

SEC EDGAR enforces 10 requests/second. Template defaults to 5 req/sec:

```yaml
rate_limit:
  requests_per_second: 5  # Conservative (SEC allows 10)
  burst_size: 3
```

### Caching

Reduce API calls by enabling caching:

```yaml
cache:
  enabled: true
  ttl: 86400  # 24 hours
  max_size_mb: 100
  cache_dir: "data/cache/edgar"
```

### Validation

Customize validation rules:

```yaml
validation:
  constraints:
    salary:
      min: 0
      max: 100000000  # $100M max
  custom_validators:
    - name: "total_equals_sum"
      expression: "total == salary + bonus + ..."
```

## Examples Corpus

Included examples (for pattern detection):

1. **Apple Inc. (0000320193)** - Technology, stock-heavy
2. **Microsoft Corp. (0000789019)** - Technology, performance awards

**Add More Examples**: See `examples/README.md` for instructions on adding examples from other companies and industries.

## Output Formats

### JSON (Structured)
```bash
output/executive_comp_0000320193_2024.json
```
Full nested structure with all metadata.

### CSV (Flat)
```bash
output/executive_comp_0000320193_2024.csv
```
Flattened for Excel analysis (one row per executive-year).

### Excel (Formatted)
```bash
output/executive_comp_0000320193_2024.xlsx
```
Formatted spreadsheet with frozen headers.

## Validation

Validate extracted data:

```bash
# Validate structure and business logic
edgar validate . \
  --output output/executive_comp_0000320193_2024.json

# Check validation rules
edgar validate . --check-totals --check-required-fields
```

## Troubleshooting

### Issue: SEC User-Agent Required

**Error**: `403 Forbidden` or rate limit errors

**Solution**:
```bash
# Add to .env.local
SEC_EDGAR_USER_AGENT="John Doe jdoe@example.com"
```

### Issue: CIK Not Found

**Error**: `Company not found`

**Solution**:
```bash
# Ensure CIK is 10-digit zero-padded
edgar run-extraction . --cik 0000320193  # ✅ Correct
edgar run-extraction . --cik 320193      # ❌ Wrong
```

### Issue: No Compensation Data

**Error**: `No Summary Compensation Table found`

**Solution**:
- Verify DEF 14A filing exists for that year
- Check filing date (filings typically 3-4 months after fiscal year end)
- Try previous fiscal year

### Issue: Low Confidence Scores

**Error**: Extracted data has confidence < 85%

**Solution**:
```bash
# Add more examples for your industry
cp examples/apple_2024.json examples/your_company_2024.json
# Edit with real data

# Re-analyze with more examples
edgar analyze-project .

# Adjust confidence threshold
edgar chat --confidence 0.80
```

## Advanced Usage

### Custom Transformations

Add custom patterns to `project.yaml`:

```yaml
patterns:
  - type: CUSTOM
    description: "Convert thousands to actual values"
    expression: "value * 1000"
```

### Parallel Extraction

**WARNING**: SEC rate limits are strict. Use carefully.

```yaml
runtime:
  parallel: true
  max_workers: 3  # Max 3 concurrent (5 req/sec ÷ 3 = 1.67 req/sec each)
```

### Resume After Failure

Checkpointing is enabled by default:

```bash
# Extraction failed after 5 companies
edgar run-extraction . --companies-file companies.txt

# Resume from checkpoint
edgar run-extraction . --resume
```

## Data Sources

This template uses:

1. **SEC EDGAR Company Facts API**
   - URL: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
   - Rate Limit: 10 req/sec
   - Format: JSON

2. **SEC EDGAR Filing Documents**
   - URL: `https://www.sec.gov/cgi-bin/browse-edgar`
   - Form Type: DEF 14A (Proxy Statement)
   - Format: HTML

## Resources

- [SEC EDGAR Search](https://www.sec.gov/edgar/search/)
- [DEF 14A Filing Guide](https://www.sec.gov/files/form-def14a.pdf)
- [Executive Compensation Disclosure Rules](https://www.sec.gov/divisions/corpfin/guidance/execcomp.htm)
- [Platform Documentation](../../docs/README.md)
- [Pattern Detection Guide](../../docs/guides/PATTERN_DETECTION.md)

## Support

For issues or questions:

1. **Check logs**: `logs/edgar_analyzer.log`
2. **Validate environment**: `edgar project validate .`
3. **Review examples**: `examples/README.md`
4. **Platform docs**: `docs/README.md`

## License

Same as parent project (see root LICENSE file).

## Version

Template Version: 1.0.0
Platform Version: 0.1.3+
Last Updated: 2025-12-08
