# EDGAR Scripts

Utility scripts for testing, validation, and automation.

## Available Scripts

### E2E Extraction Test
**File**: `e2e_edgar_extraction.py`

End-to-end test of the complete EDGAR extraction pipeline.

**Usage**:
```bash
# Run full test
python3 scripts/e2e_edgar_extraction.py

# Verbose output
python3 scripts/e2e_edgar_extraction.py -v

# Run specific phase only
python3 scripts/e2e_edgar_extraction.py --phase 1  # Data acquisition
python3 scripts/e2e_edgar_extraction.py --phase 2  # Pattern analysis
python3 scripts/e2e_edgar_extraction.py --phase 3  # Extractor verification
python3 scripts/e2e_edgar_extraction.py --phase 4  # Extraction execution
```

**Via CLI**:
```bash
edgar e2e-test
edgar e2e-test -v
edgar e2e-test --phase 2
```

**Pipeline Phases**:
1. **Data Acquisition**: Fetch SEC filing from EDGAR
2. **Pattern Analysis**: Detect transformation patterns
3. **Extractor Verification**: Verify code generation
4. **Extraction Execution**: Run extractor and validate

**Output Files**:
- `data/e2e_test/apple_def14a_raw.html` - Raw filing HTML
- `data/e2e_test/apple_sct_ground_truth.json` - Validation rules
- `data/e2e_test/pattern_analysis.json` - Pattern detection results
- `output/e2e_test/apple_sct_extracted.json` - Extracted compensation data
- `output/e2e_test/e2e_runbook_result.json` - Test execution summary

**Exit Codes**:
- `0` - All phases passed
- `1` - One or more phases failed

**Documentation**:
- [E2E Runbook Guide](../docs/e2e_runbook.md) - Comprehensive documentation
- [E2E Quick Start](../docs/e2e_quick_start.md) - Quick reference

## Future Scripts

Planned utility scripts for common tasks:

- `validate_filing.py` - Validate specific SEC filing
- `benchmark_extractors.py` - Performance benchmarking
- `generate_extractor.py` - Interactive extractor generation
- `analyze_patterns.py` - Standalone pattern analysis tool

## Development

### Adding New Scripts

1. **Create script** in `scripts/` directory
2. **Add shebang**: `#!/usr/bin/env python3`
3. **Make executable**: `chmod +x scripts/your_script.py`
4. **Add CLI entry** (optional) in `src/edgar/cli.py`
5. **Document** in this README

### Script Template

```python
#!/usr/bin/env python3
"""Brief description of script purpose.

Detailed description of what the script does and when to use it.

Usage:
    python scripts/your_script.py [options]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar.services import YourService


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Your script description",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Your script logic here

    sys.exit(0)


if __name__ == "__main__":
    main()
```

## Testing

All scripts should have corresponding test files in `tests/`:

```bash
# Test E2E runbook
pytest tests/test_e2e_runbook.py -v
```

## CI/CD Integration

Scripts can be integrated into GitHub Actions workflows:

```yaml
- name: Run E2E test
  run: python3 scripts/e2e_edgar_extraction.py -v

- name: Upload results
  uses: actions/upload-artifact@v3
  with:
    name: e2e-results
    path: output/e2e_test/
```

## Related Documentation

- [E2E Runbook Guide](../docs/e2e_runbook.md)
- [E2E Quick Start](../docs/e2e_quick_start.md)
- [Phase 5 Completion Summary](../docs/phase5_completion.md)
