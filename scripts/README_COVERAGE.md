# Coverage Analysis Tools

Quick reference for coverage analysis tools and workflows.

## Quick Commands

```bash
# Run full coverage report
pytest --cov=src/extract_transform_platform \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-report=json

# View HTML report
open htmlcov/index.html

# Quick summary (terminal)
python3 scripts/coverage_summary.py

# Category detail
python3 scripts/coverage_summary.py --category Services
python3 scripts/coverage_summary.py --category "Data Sources"

# JSON output
python3 scripts/coverage_summary.py --format json
```

## Coverage Snapshots

Coverage snapshots are saved with date stamps for historical tracking:

```bash
# Save snapshot
cp coverage.json coverage_snapshot_$(date +%Y%m%d).json

# List snapshots
ls -lah coverage_snapshot_*.json

# Compare snapshots
python3 -c "
import json
with open('coverage_snapshot_20251205.json') as f:
    old = json.load(f)['totals']['percent_covered']
with open('coverage.json') as f:
    new = json.load(f)['totals']['percent_covered']
print(f'Coverage change: {old:.1f}% → {new:.1f}% ({new-old:+.1f} pts)')
"
```

## Analysis Documents

**Phase 3 Week 2 Coverage Gap Analysis**:
- File: `PHASE3_WEEK2_COVERAGE_GAP_ANALYSIS.md`
- Date: 2025-12-05
- Coverage baseline: 32.0%
- Target: 75-80%
- Revised realistic goal: 60-65%

**Coverage Categories**:
| Category | Coverage | Priority |
|----------|----------|----------|
| CodeGen | 76.0% | ✅ Near target |
| Models | 79.7% | ✅ Near target |
| AI/ML | 27.6% | 🔴 Critical |
| Services | 9.0% | 🔴 Critical |
| Data Sources | 0.0% | 🔴 Critical |
| Reports | 0.0% | 🔴 Blocked |

## Workflow

**Daily Coverage Tracking**:

```bash
# 1. Run tests
pytest --cov=src/extract_transform_platform --cov-report=json -q

# 2. Save snapshot
cp coverage.json coverage_snapshot_$(date +%Y%m%d).json

# 3. Check summary
python3 scripts/coverage_summary.py

# 4. Update work plan
# Edit PHASE3_WEEK2_COVERAGE_GAP_ANALYSIS.md with actuals
```

**Before Committing**:

```bash
# 1. Run full test suite
make test

# 2. Check coverage
python3 scripts/coverage_summary.py

# 3. Verify targets met
# Services: 70%+
# Models: 80%+
# Overall: 60%+
```

## Troubleshooting

**Issue: Reports module import errors**
```bash
# Install missing dependencies
uv pip install python-docx python-pptx

# Or use python3 -m pip
python3 -m pip install python-docx python-pptx --user
```

**Issue: Coverage.json outdated**
```bash
# Clean cache and rerun
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
pytest --cov=src/extract_transform_platform --cov-report=json --cache-clear
```

**Issue: Tests hanging**
```bash
# Run with timeout
pytest --timeout=300 --cov=src/extract_transform_platform --cov-report=json
```

## Coverage Targets (Phase 3)

**Realistic Goals**:
- Overall platform: 60-65%
- Services module: >50%
- CodeGen module: >90%
- Models module: >80%
- Critical modules: >70%

**Stretch Goals**:
- Overall platform: 70%+
- All modules: >60%
- Critical modules: >80%

## References

- **Gap Analysis**: `/Users/masa/Clients/Zach/projects/edgar/PHASE3_WEEK2_COVERAGE_GAP_ANALYSIS.md`
- **Coverage Snapshots**: `/Users/masa/Clients/Zach/projects/edgar/coverage_snapshot_*.json`
- **HTML Reports**: `/Users/masa/Clients/Zach/projects/edgar/htmlcov/index.html`
- **Summary Script**: `/Users/masa/Clients/Zach/projects/edgar/scripts/coverage_summary.py`
