# E2E Runbook Quick Start

## Installation

```bash
cd /Users/masa/Projects/edgar
pip install -e .
```

## Basic Usage

### Run Full Test
```bash
python3 scripts/e2e_edgar_extraction.py
```

### Verbose Output
```bash
python3 scripts/e2e_edgar_extraction.py -v
```

### Run Single Phase
```bash
python3 scripts/e2e_edgar_extraction.py --phase 1  # Data acquisition
python3 scripts/e2e_edgar_extraction.py --phase 2  # Pattern analysis
python3 scripts/e2e_edgar_extraction.py --phase 3  # Extractor verification
python3 scripts/e2e_edgar_extraction.py --phase 4  # Extraction execution
```

### Via CLI
```bash
edgar e2e-test           # Full test
edgar e2e-test -v        # Verbose
edgar e2e-test --phase 2 # Single phase
```

## Quick Checks

### Check Results
```bash
# View runbook summary
cat output/e2e_test/e2e_runbook_result.json | python3 -m json.tool

# View extracted data
cat output/e2e_test/apple_sct_extracted.json | python3 -m json.tool

# View pattern analysis
cat data/e2e_test/pattern_analysis.json | python3 -m json.tool
```

### Verify Success
```bash
python3 scripts/e2e_edgar_extraction.py && echo "SUCCESS" || echo "FAILED"
```

## Expected Output

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

## Common Issues

### Phase 1: Connection Error
**Issue**: `FAILED: HTTPError: 429 Too Many Requests`

**Solution**: Wait 10 seconds and retry

### Phase 2: Low Confidence
**Issue**: `FAILED: Confidence 78.0% < 85% threshold`

**Solution**: Check `data/e2e_test/pattern_analysis.json` for details

### Phase 2/4: Missing Data
**Issue**: `FAILED: Phase 1 data not found`

**Solution**: Run Phase 1 first:
```bash
python3 scripts/e2e_edgar_extraction.py --phase 1
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run E2E test
  run: python3 scripts/e2e_edgar_extraction.py -v
```

### Exit Code Usage
```bash
python3 scripts/e2e_edgar_extraction.py
if [ $? -eq 0 ]; then
    echo "Test passed"
else
    echo "Test failed"
    exit 1
fi
```

## File Locations

**Data**:
- `data/e2e_test/apple_def14a_raw.html` - Raw filing
- `data/e2e_test/apple_sct_ground_truth.json` - Validation rules
- `data/e2e_test/pattern_analysis.json` - Pattern results

**Output**:
- `output/e2e_test/apple_sct_extracted.json` - Extracted data
- `output/e2e_test/e2e_runbook_result.json` - Runbook results

## Testing

Run unit tests:
```bash
pytest tests/test_e2e_runbook.py -v
```

## Documentation

Full documentation: [docs/e2e_runbook.md](./e2e_runbook.md)
