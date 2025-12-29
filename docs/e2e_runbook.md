# E2E Runbook Documentation

## Overview

The End-to-End (E2E) runbook script validates the complete EDGAR extraction pipeline from data acquisition through validation. It executes all phases in sequence and reports success/failure with detailed metrics.

## Pipeline Phases

### Phase 1: Data Acquisition
**Purpose**: Fetch SEC filing from EDGAR database

**Steps**:
1. Connect to SEC EDGAR API
2. Retrieve latest DEF 14A filing for Apple Inc. (CIK: 0000320193)
3. Download HTML content
4. Save raw HTML to `data/e2e_test/apple_def14a_raw.html`
5. Create ground truth validation rules

**Output**:
- `data/e2e_test/apple_def14a_raw.html` - Raw filing HTML
- `data/e2e_test/apple_sct_ground_truth.json` - Validation rules

**Success Criteria**:
- HTML downloaded successfully (>100KB)
- Filing date present and valid
- Ground truth file created

### Phase 2: Pattern Analysis
**Purpose**: Detect transformation patterns in filing structure

**Steps**:
1. Load raw HTML from Phase 1
2. Run PatternAnalyzer to detect compensation table patterns
3. Calculate overall confidence score
4. Save pattern analysis results

**Output**:
- `data/e2e_test/pattern_analysis.json` - Detected patterns and confidence

**Success Criteria**:
- At least 3 patterns detected
- Overall confidence ≥ 85%
- Input/output schemas generated

### Phase 3: Extractor Verification
**Purpose**: Verify SCT extractor module is available

**Steps**:
1. Import SCTExtractor module
2. Instantiate extractor with test configuration
3. Verify no import or initialization errors

**Success Criteria**:
- SCTExtractor module imports successfully
- Extractor instantiates without errors

### Phase 4: Extraction Execution
**Purpose**: Run extraction and validate results against ground truth

**Steps**:
1. Load raw HTML from Phase 1
2. Run SCTExtractor to extract compensation data
3. Validate against ground truth rules:
   - Minimum 5 executives extracted
   - CEO (Tim Cook) present in results
   - CEO total compensation ≥ $60M
4. Save extracted data

**Output**:
- `output/e2e_test/apple_sct_extracted.json` - Extracted compensation data
- `output/e2e_test/e2e_runbook_result.json` - Full runbook results

**Success Criteria**:
- At least 5 executives extracted
- CEO found with name containing "Cook"
- CEO total compensation ≥ $60,000,000
- All validation rules passed

## Usage

### Run Full E2E Test

```bash
cd /Users/masa/Projects/edgar
python3 scripts/e2e_edgar_extraction.py
```

**Expected Output**:
```
============================================================
EDGAR E2E Extraction Test
============================================================

Phase 1: Data Acquisition
  → PASSED: Downloaded 1,234,567 bytes, filing date 2024-01-05 (2.3s)

Phase 2: Pattern Analysis
  → PASSED: 5 patterns, 92.0% confidence (1.1s)

Phase 3: Extractor Verification
  → PASSED: SCTExtractor ready (0.1s)

Phase 4: Extraction Execution
  → PASSED: 7 executives, CEO total $63,209,845 (0.8s)

============================================================
SUMMARY
============================================================
  ✅ Phase 1: Data Acquisition - PASSED
  ✅ Phase 2: Pattern Analysis - PASSED
  ✅ Phase 3: Extractor Verification - PASSED
  ✅ Phase 4: Extraction Execution - PASSED

Total Duration: 4.3s
Overall Status: ✅ PASSED
============================================================
```

### Verbose Mode

Show detailed progress within each phase:

```bash
python3 scripts/e2e_edgar_extraction.py --verbose
```

**Additional Output**:
- API request details
- Pattern detection progress
- Extractor initialization logs
- Validation check details

### Run Specific Phase

Run only a single phase for debugging:

```bash
# Run only Phase 2 (requires Phase 1 data to exist)
python3 scripts/e2e_edgar_extraction.py --phase 2

# Run only Phase 4 (requires Phase 1 data to exist)
python3 scripts/e2e_edgar_extraction.py --phase 4
```

**Note**: Phases 2 and 4 depend on Phase 1 data. Run Phase 1 first if data doesn't exist.

## CLI Integration

The runbook can also be executed via the EDGAR CLI:

```bash
# Install CLI entry point (one-time setup)
pip install -e .

# Run E2E test via CLI
edgar e2e-test
edgar e2e-test -v
edgar e2e-test --phase 2
```

## Output Files

### Data Directory (`data/e2e_test/`)

| File | Description | Phase |
|------|-------------|-------|
| `apple_def14a_raw.html` | Raw SEC filing HTML | 1 |
| `apple_sct_ground_truth.json` | Validation rules and expected values | 1 |
| `pattern_analysis.json` | Detected patterns and confidence scores | 2 |

### Output Directory (`output/e2e_test/`)

| File | Description | Phase |
|------|-------------|-------|
| `apple_sct_extracted.json` | Extracted compensation data | 4 |
| `e2e_runbook_result.json` | Full runbook execution results | All |

### Result Schema

**e2e_runbook_result.json**:
```json
{
  "success": true,
  "total_duration": 4.3,
  "timestamp": "2025-01-15T10:30:45.123456",
  "phases": [
    {
      "phase": 1,
      "name": "Data Acquisition",
      "status": "PASSED",
      "duration": 2.3,
      "message": "Downloaded 1,234,567 bytes, filing date 2024-01-05"
    },
    ...
  ]
}
```

## Exit Codes

- **0**: All phases passed successfully
- **1**: One or more phases failed

Use exit codes in CI/CD pipelines:

```bash
python3 scripts/e2e_edgar_extraction.py
if [ $? -eq 0 ]; then
    echo "E2E test passed"
else
    echo "E2E test failed"
    exit 1
fi
```

## Troubleshooting

### Phase 1 Failures

**Problem**: Connection timeout or rate limiting
```
FAILED: HTTPError: 429 Too Many Requests
```

**Solution**: Wait 10 seconds and retry. SEC rate limits: max 10 requests/second.

**Problem**: Filing not found
```
FAILED: No DEF 14A filings found for CIK 0000320193
```

**Solution**: Check if company has recent DEF 14A filings. Try different filing type.

### Phase 2 Failures

**Problem**: Low confidence score
```
FAILED: Confidence 78.0% < 85% threshold
```

**Solution**: This indicates pattern detection uncertainty. Inspect `pattern_analysis.json` for details. May need to improve PatternAnalyzer heuristics.

**Problem**: Phase 1 data not found
```
FAILED: Phase 1 data not found. Run Phase 1 first.
```

**Solution**: Run Phase 1 to download filing data:
```bash
python3 scripts/e2e_edgar_extraction.py --phase 1
```

### Phase 3 Failures

**Problem**: Import error
```
FAILED: Import error: No module named 'edgar.extractors.sct'
```

**Solution**: Ensure extractors module exists:
```bash
ls src/edgar/extractors/sct.py
```

### Phase 4 Failures

**Problem**: Insufficient executives
```
FAILED: Only 3 executives (need 5)
```

**Solution**: Check if extractor is finding all table rows. Inspect HTML structure in `apple_def14a_raw.html`.

**Problem**: CEO not found
```
FAILED: CEO not found (expected 'Cook')
```

**Solution**: Verify CEO name in ground truth matches actual data. Check `apple_sct_extracted.json` for extracted names.

**Problem**: CEO compensation too low
```
FAILED: CEO total $45,000,000 < $60,000,000
```

**Solution**: This may indicate extraction logic error or outdated ground truth. Verify expected values.

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: E2E EDGAR Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Run E2E test
        run: |
          python3 scripts/e2e_edgar_extraction.py -v

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-results
          path: output/e2e_test/
```

## Performance Benchmarks

Expected phase durations (Apple DEF 14A, ~1.2MB HTML):

| Phase | Typical Duration | Notes |
|-------|------------------|-------|
| 1. Data Acquisition | 2-5s | Depends on SEC API response time |
| 2. Pattern Analysis | 1-2s | BeautifulSoup parsing + heuristics |
| 3. Extractor Verification | <0.2s | Import and instantiation only |
| 4. Extraction Execution | 0.5-1.5s | Parsing + validation |
| **Total** | **4-9s** | Full pipeline |

## Future Enhancements

Potential improvements to the E2E runbook:

1. **Multi-Company Testing**: Test against multiple companies (tech, finance, healthcare)
2. **Historical Validation**: Compare extractions across multiple years
3. **Parallel Execution**: Run phases concurrently where possible
4. **Detailed Diffing**: Show exact differences between extracted and expected values
5. **Performance Profiling**: Add cProfile integration for bottleneck detection
6. **Retry Logic**: Automatic retry with exponential backoff for Phase 1 network errors
7. **Slack/Email Notifications**: Alert on failures in production environments
8. **Metrics Export**: Export timing/success metrics to Prometheus/Grafana

## Related Documentation

- [Pattern Analyzer](../src/edgar/services/pattern_analyzer.py) - Phase 2 implementation
- [SCT Extractor](../src/edgar/extractors/sct.py) - Phase 4 extractor logic
- [SEC EDGAR Client](../src/edgar/services/sec_edgar_client.py) - Phase 1 API client
