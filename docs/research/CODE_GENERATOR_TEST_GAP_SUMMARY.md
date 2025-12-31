# Code Generator Test Gap Analysis - Executive Summary

**Date**: 2025-12-03
**Target**: Increase code_generator.py coverage from 67% to 80%+

---

## Quick Facts

- **Current Coverage**: 67% (143/214 statements)
- **Target Coverage**: 80%+ (171+ statements)
- **Gap**: 28+ statements
- **Tests Needed**: 10-15 tests
- **Expected Final Coverage**: 85-90%

---

## Key Findings

### What's Currently Tested (67%)
✅ Progress tracking (GenerationProgress, 7 steps, callbacks)
✅ Rollback mechanism (delete on failure)
✅ Dry-run mode (write_files=False)
✅ Optional steps (validation/file writing skip)

### What's Missing (33%)
❌ **CodeValidator** (0% coverage) - All validation methods untested
❌ **CodeWriter** (20% coverage) - Backup mechanism, __init__.py generation
❌ **generate_from_parsed()** (0% coverage) - Alternative entry point

---

## Recommended Test Plan (15 tests)

### Priority 1: CodeValidator (5 tests, +16% coverage)
1. Valid code passes all checks
2. Syntax errors detected
3. Missing type hints reported
4. Missing IDataExtractor interface detected
5. Missing tests detected

### Priority 2: CodeWriter (4 tests, +10% coverage)
1. Creates directory structure
2. Backs up existing files with timestamp
3. Returns file paths dictionary
4. Generates __init__.py correctly

### Priority 3: generate_from_parsed() (3 tests, +7% coverage)
1. With validation enabled
2. Validation failure raises exception
3. Without file writing (dry-run)

### Priority 4: Edge Cases (3 tests, +3% coverage)
1. Empty examples list handling
2. Parser exceptions propagated
3. Error tracking in context

---

## Implementation Strategy

### Week 1: Core Tests (9 tests → 80%+ coverage)
- Create `test_code_validator.py` (5 tests)
- Create `test_code_writer.py` (4 tests)
- Run coverage: 67% → 93%

### Week 2: Alternative Paths (6 tests → 85-90% coverage)
- Create `test_code_generator_main.py` (6 tests)
- Run full suite verification
- Document remaining gaps

---

## Expected Coverage Improvement

| Phase | Tests Added | Coverage | Gain |
|-------|-------------|----------|------|
| Current | 7 (progress) | 67% | - |
| +CodeValidator | 5 | 83% | +16% |
| +CodeWriter | 4 | 93% | +10% |
| +Alternative Paths | 3 | 85-90% | +7% |
| +Edge Cases | 3 | 85-90% | +3% |
| **TOTAL** | **15** | **85-90%** | **+18-23%** |

---

## Quick Start

### 1. Read Full Analysis
📄 `docs/research/code-generator-test-gap-analysis-2025-12-03.md`

### 2. Create Test Files
```bash
touch tests/unit/services/codegen/test_code_validator.py
touch tests/unit/services/codegen/test_code_writer.py
touch tests/unit/services/codegen/test_code_generator_main.py
```

### 3. Verify Current Coverage
```bash
pytest tests/unit/services/test_code_generator*.py \
  --cov=src/extract_transform_platform/services/codegen/code_generator \
  --cov-report=term-missing
```

---

## Success Criteria

✅ Reach 80%+ statement coverage (171+/214 statements)
✅ All tests run in <5 seconds (unit test speed)
✅ No external dependencies (mock Sonnet45Agent, ExampleParser)
✅ Proper isolation (tmp_path for file operations)

---

## Full Documentation

See `docs/research/code-generator-test-gap-analysis-2025-12-03.md` for:
- Detailed implementation analysis
- Complete test scenarios with code examples
- Fixture requirements
- Mocking patterns
- Coverage improvement estimates
- Risk assessment

---

**Next Action**: Review full analysis, then implement Priority 1 tests (CodeValidator)
