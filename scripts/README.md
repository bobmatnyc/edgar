# EDGAR Scripts

Utility scripts for testing, validation, and ad-hoc operations.

## Directory Structure

```
scripts/
├── e2e_edgar_extraction.py      # E2E extraction test
├── analyze_patterns.py          # Pattern analysis utility
├── fetch_apple_def14a.py        # Fetch sample filing
├── refine_extractors.py         # Self-refinement CLI
├── adhoc/                       # Ad-hoc scripts (not production)
│   └── fortune100_analysis.py   # Original pipeline script
└── debug/                       # Debugging utilities
    └── debug_table_detection.py # Table detection debugger
```

## Production Commands

For production use, prefer the CLI commands over scripts:

```bash
# Fortune 100 Analysis (recommended)
edgar fortune100 -c 1-100 -v

# E2E Test (recommended)
edgar e2e-test

# Interactive Exploration (recommended)
jupyter notebook notebooks/
```

## Scripts

### E2E Extraction Test
**File**: `e2e_edgar_extraction.py`

End-to-end test of the complete EDGAR extraction pipeline.

```bash
python scripts/e2e_edgar_extraction.py -v
```

### Pattern Analysis
**File**: `analyze_patterns.py`

Analyze transformation patterns from SEC filings.

```bash
python scripts/analyze_patterns.py
```

### Self-Refinement
**File**: `refine_extractors.py`

Analyze extraction failures and suggest improvements.

```bash
# Analyze recent failures
python scripts/refine_extractors.py --analyze

# Apply suggested fixes
python scripts/refine_extractors.py --apply
```

## Ad-Hoc Scripts

Scripts in `adhoc/` are for one-off operations and experimentation.
They are **not part of the production pipeline**.

```bash
# Legacy Fortune 100 script (use CLI instead)
python scripts/adhoc/fortune100_analysis.py --companies 1-10
```

## Debug Scripts

Scripts in `debug/` are for troubleshooting extraction issues.

```bash
# Debug table detection
python scripts/debug/debug_table_detection.py
```

## Development

### Adding New Scripts

For **production features**, add to `src/edgar/` and expose via CLI.

For **ad-hoc tasks**, add to `scripts/adhoc/`.

For **debugging**, add to `scripts/debug/`.

### Script Template

```python
#!/usr/bin/env python3
"""Brief description."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar.services import YourService

def main() -> None:
    # Your logic here
    pass

if __name__ == "__main__":
    main()
```

## Related Documentation

- [CLI Usage](../README.md)
- [Jupyter Notebooks](../notebooks/)
- [Pipeline Module](../src/edgar/pipelines/)
