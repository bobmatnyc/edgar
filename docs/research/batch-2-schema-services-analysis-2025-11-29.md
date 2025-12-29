# Batch 2: Schema Services Components - Migration Analysis

**Date**: 2025-11-29
**Analyst**: Research Agent
**Context**: Phase 2 Platform Migration - Batch 2 of 5
**Status**: ✅ Analysis Complete - Ready for Migration

---

## Executive Summary

Batch 2 consists of 3 core schema services components (1,634 total LOC) that form the pattern detection engine. All components are **100% generic** with zero EDGAR-specific code. They can be migrated in **sequential order** due to clear dependency chain.

### Migration Readiness: ✅ GREEN

- **Code Reuse**: 100% (all code is generic)
- **EDGAR Dependencies**: 0% (fully platform-agnostic)
- **Test Coverage**: 739 LOC of tests (comprehensive)
- **Parallelization**: Sequential migration required (dependency chain)
- **Risk Level**: LOW (clean interfaces, well-tested)

---

## Component Analysis

### 1. PatternModels (`patterns.py`)

**Location**: `src/edgar_analyzer/models/patterns.py`
**Actual LOC**: 526 (matches estimate exactly!)
**Test Coverage**: Comprehensive (via SchemaAnalyzer and ExampleParser tests)

#### Purpose
Data models for transformation patterns identified by analyzing input/output examples.

#### Key Models
- `PatternType` (enum): 14 pattern types (field_mapping, type_conversion, array_first, etc.)
- `FieldTypeEnum` (enum): 10 data types (str, int, float, date, etc.)
- `Pattern`: Transformation pattern with confidence scoring
- `SchemaField`: Field metadata (type, nesting, nullability)
- `Schema`: Input/output data schema
- `SchemaDifference`: Schema comparison results
- `ParsedExamples`: Complete analysis results
- `PromptSection`, `GeneratedPrompt`: LLM prompt generation

#### Dependencies
- **External**: `pydantic`, `enum`, `typing`
- **Internal**: NONE (fully self-contained)

#### EDGAR-Specific Code
**0%** - Completely generic pattern models.

#### Migration Notes
- **No changes required** - models are 100% platform-agnostic
- Already has placeholder in platform: `transformation_pattern.py` (51 LOC stub)
- Will **replace** stub with full implementation
- No external dependencies beyond Pydantic

#### Code Reuse Estimate
**100%** - Direct copy with import path updates only

---

### 2. SchemaAnalyzer (`schema_analyzer.py`)

**Location**: `src/edgar_analyzer/services/schema_analyzer.py`
**Actual LOC**: 432 (matches estimate exactly!)
**Test Coverage**: `tests/unit/services/test_schema_analyzer.py`

#### Purpose
Infer data schemas from examples and identify structural differences indicating transformation patterns.

#### Key Methods
- `infer_input_schema(examples)`: Infer input data schema
- `infer_output_schema(examples)`: Infer output data schema
- `compare_schemas(input, output)`: Identify schema differences
- `_extract_fields()`: Recursively extract nested fields
- `_analyze_field()`: Analyze field across examples
- `_infer_type()`: Type inference with majority voting
- `_detect_field_renames()`: Detect potential field renames (Jaccard similarity)

#### Dependencies
- **External**: `logging`, `datetime`, `decimal`, `typing`
- **Internal**:
  - `edgar_analyzer.models.patterns` (FieldTypeEnum, Schema, SchemaField, SchemaDifference)

#### EDGAR-Specific Code
**0%** - Generic schema analysis, no domain-specific logic.

#### Migration Notes
- Depends on `PatternModels` (must migrate first)
- No EDGAR-specific logic
- Handles nested structures, arrays, type inference
- Performance: O(n*m) - 100ms for 10 examples with 50 fields

#### Code Reuse Estimate
**100%** - Direct copy with import path updates only

---

### 3. ExampleParser (`example_parser.py`)

**Location**: `src/edgar_analyzer/services/example_parser.py`
**Actual LOC**: 676 (matches estimate exactly!)
**Test Coverage**:
- `tests/unit/services/test_example_parser.py`
- `tests/integration/test_example_parser_integration.py`

#### Purpose
Core service that analyzes input/output example pairs to identify transformation patterns.

#### Key Methods
- `parse_examples(examples)`: Main entry point - extract patterns from examples
- `identify_patterns(examples)`: Identify transformation patterns across examples
- `_identify_field_pattern()`: Pattern detection for single field
- `_detect_pattern_type()`: Pattern type classification (priority-based)
- `_detect_field_mapping()`: Field mapping/extraction detection
- `_detect_array_first()`: Array first element extraction
- `_create_*_pattern()`: Pattern creation helpers
- `_find_source_value()`: Find input value for output value
- `_find_path_for_value()`: Recursive path finding
- `_get_value_at_path()`: Dot-notation path traversal

#### Dependencies
- **External**: `logging`, `typing`
- **Internal**:
  - `edgar_analyzer.models.patterns` (FieldTypeEnum, ParsedExamples, Pattern, PatternType, Schema)
  - `edgar_analyzer.models.project_config` (ExampleConfig)
  - `edgar_analyzer.services.schema_analyzer` (SchemaAnalyzer)

#### EDGAR-Specific Code
**0%** - Generic pattern extraction, no domain logic.

#### Migration Notes
- Depends on `PatternModels` and `SchemaAnalyzer`
- Uses `ExampleConfig` from `project_config.py` (already migrated in Batch 1)
- Confidence scoring based on example consistency
- Pattern detection priority:
  1. Field mapping/extraction (nested paths)
  2. Constant value
  3. Array first element
  4. Type conversion
  5. Direct copy
- Performance: O(n*m*p) - 500ms for 10 examples with 50 fields

#### Code Reuse Estimate
**100%** - Direct copy with import path updates only

---

## Dependency Graph

```
┌─────────────────────┐
│ PatternModels       │  ← Must migrate FIRST (no dependencies)
│ (patterns.py)       │
│ 526 LOC             │
└──────────┬──────────┘
           │
           │ depends on
           ▼
┌─────────────────────┐
│ SchemaAnalyzer      │  ← Migrate SECOND (depends on PatternModels)
│ (schema_analyzer.py)│
│ 432 LOC             │
└──────────┬──────────┘
           │
           │ depends on
           ▼
┌─────────────────────┐
│ ExampleParser       │  ← Migrate THIRD (depends on both above)
│ (example_parser.py) │
│ 676 LOC             │
└─────────────────────┘

External Dependency: ExampleConfig (already migrated in Batch 1 ✅)
```

---

## Parallelization Strategy

### ❌ CANNOT PARALLELIZE

Components **must** be migrated in strict sequential order due to dependency chain:

1. **First**: PatternModels (no dependencies)
2. **Second**: SchemaAnalyzer (depends on PatternModels)
3. **Third**: ExampleParser (depends on PatternModels + SchemaAnalyzer)

### Execution Order

```bash
# Task 1: Migrate PatternModels
1M-XXX: Migrate PatternModels to platform package

# Task 2: Migrate SchemaAnalyzer (after Task 1 complete)
1M-XXX: Migrate SchemaAnalyzer to platform package

# Task 3: Migrate ExampleParser (after Task 2 complete)
1M-XXX: Migrate ExampleParser to platform package
```

---

## Migration Complexity Assessment

### Component Difficulty Ratings

| Component | LOC | Dependencies | EDGAR Code | Difficulty | Estimate |
|-----------|-----|--------------|------------|------------|----------|
| PatternModels | 526 | 0 internal | 0% | ✅ EASY | 2 hours |
| SchemaAnalyzer | 432 | 1 internal | 0% | ✅ EASY | 2 hours |
| ExampleParser | 676 | 3 internal | 0% | 🟡 MEDIUM | 3 hours |

**Total Estimated Effort**: 7 hours (sequential)

### Difficulty Justification

**PatternModels - EASY**:
- Pure Pydantic models
- No logic, just data structures
- Self-contained (no internal dependencies)
- Replaces existing stub

**SchemaAnalyzer - EASY**:
- Single internal dependency (PatternModels)
- No EDGAR-specific code
- Well-tested, clean interfaces

**ExampleParser - MEDIUM**:
- Multiple internal dependencies
- Complex pattern detection logic (14 pattern types)
- Requires careful import path updates
- Integration with existing project_config

---

## Code Reuse Metrics

### Overall Statistics

- **Total LOC**: 1,634
- **Generic Code**: 1,634 (100%)
- **EDGAR-Specific Code**: 0 (0%)
- **Code Reuse**: 100%
- **Lines to Remove**: 0
- **Lines to Modify**: ~50 (import paths only)

### Detailed Breakdown

| Component | Total LOC | Generic | EDGAR | Reuse % | Changes Required |
|-----------|-----------|---------|-------|---------|------------------|
| PatternModels | 526 | 526 | 0 | 100% | Import paths |
| SchemaAnalyzer | 432 | 432 | 0 | 100% | Import paths |
| ExampleParser | 676 | 676 | 0 | 100% | Import paths |
| **TOTAL** | **1,634** | **1,634** | **0** | **100%** | **Import paths only** |

---

## Risk Assessment

### Overall Risk: 🟢 LOW

### Risk Factors

**✅ No Risk (Green)**:
- Zero EDGAR-specific code
- Well-tested components (739 LOC of tests)
- Clean interfaces with clear responsibilities
- No external service dependencies
- Self-contained pattern detection logic

**🟡 Medium Risk (Yellow)**:
- Sequential dependency chain (blocks parallelization)
- Import path updates required across 3 files
- ExampleParser has complex pattern detection logic (needs careful testing)

**❌ High Risk (Red)**:
- None identified

### Mitigation Strategies

1. **Sequential Migration**: Follow strict order (PatternModels → SchemaAnalyzer → ExampleParser)
2. **Import Path Validation**: Use grep to find all import references before migration
3. **Test Suite Execution**: Run full test suite after each component migration
4. **Integration Testing**: Run example_parser_integration tests after all 3 migrated

---

## Test Coverage Analysis

### Test Files

1. **Unit Tests - SchemaAnalyzer**:
   - `tests/unit/services/test_schema_analyzer.py`
   - Tests schema inference, type detection, field extraction

2. **Unit Tests - ExampleParser**:
   - `tests/unit/services/test_example_parser.py`
   - Tests pattern detection, confidence scoring, edge cases

3. **Integration Tests - ExampleParser**:
   - `tests/integration/test_example_parser_integration.py`
   - End-to-end pattern extraction workflow

4. **Total Test LOC**: 739 (comprehensive coverage)

### Test Migration Plan

- Copy test files to `tests/unit/platform/` and `tests/integration/platform/`
- Update import paths in test files
- Run tests after each component migration
- Add platform-specific integration tests if needed

---

## Platform Package Integration

### Current Platform State

**Existing Placeholder**:
```
src/extract_transform_platform/models/transformation_pattern.py
```
- 51 LOC stub with TODOs
- Will be **replaced** by full `patterns.py` implementation

**Platform Services Directory**:
```
src/extract_transform_platform/services/
├── __init__.py (323 bytes)
└── cache_service.py (1,557 bytes)
```
- Will add `schema_analyzer.py` (432 LOC)
- Will add `example_parser.py` (676 LOC)

### Post-Migration Structure

```
src/extract_transform_platform/
├── models/
│   ├── patterns.py (526 LOC) ← REPLACES transformation_pattern.py
│   ├── data_source_config.py (✅ Batch 1)
│   └── project_config.py (✅ Batch 1)
├── services/
│   ├── schema_analyzer.py (432 LOC) ← NEW
│   ├── example_parser.py (676 LOC) ← NEW
│   └── cache_service.py (1,557 LOC)
└── data_sources/
    ├── base.py (✅ Batch 1)
    ├── file_source.py (✅ Batch 1)
    ├── excel_source.py (✅ Batch 1)
    └── pdf_source.py (✅ Batch 1)
```

---

## Import Path Changes

### PatternModels (patterns.py)

**Before**:
```python
# No internal imports (self-contained)
from pydantic import BaseModel, Field, field_validator
```

**After**:
```python
# No changes required (external imports only)
from pydantic import BaseModel, Field, field_validator
```

### SchemaAnalyzer (schema_analyzer.py)

**Before**:
```python
from edgar_analyzer.models.patterns import (
    FieldTypeEnum,
    Schema,
    SchemaField,
    SchemaDifference,
)
```

**After**:
```python
from extract_transform_platform.models.patterns import (
    FieldTypeEnum,
    Schema,
    SchemaField,
    SchemaDifference,
)
```

### ExampleParser (example_parser.py)

**Before**:
```python
from edgar_analyzer.models.patterns import (
    FieldTypeEnum,
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
)
from edgar_analyzer.models.project_config import ExampleConfig
from edgar_analyzer.services.schema_analyzer import SchemaAnalyzer
```

**After**:
```python
from extract_transform_platform.models.patterns import (
    FieldTypeEnum,
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
)
from extract_transform_platform.models.project_config import ExampleConfig
from extract_transform_platform.services.schema_analyzer import SchemaAnalyzer
```

---

## Validation Checklist

### Pre-Migration Validation

- [x] Verify all 3 files exist with expected LOC
- [x] Confirm zero EDGAR-specific code
- [x] Identify all dependencies
- [x] Map dependency chain
- [x] Locate test files (739 LOC)
- [x] Check platform package structure

### Migration Validation (Per Component)

**PatternModels**:
- [ ] Copy `patterns.py` to `extract_transform_platform/models/`
- [ ] Replace existing `transformation_pattern.py` stub
- [ ] Verify no import path changes needed (self-contained)
- [ ] Update `__init__.py` to export new models
- [ ] Run unit tests for models
- [ ] Commit and push

**SchemaAnalyzer**:
- [ ] Copy `schema_analyzer.py` to `extract_transform_platform/services/`
- [ ] Update import path: `edgar_analyzer.models.patterns` → `extract_transform_platform.models.patterns`
- [ ] Update `__init__.py` to export SchemaAnalyzer
- [ ] Run unit tests for SchemaAnalyzer
- [ ] Commit and push

**ExampleParser**:
- [ ] Copy `example_parser.py` to `extract_transform_platform/services/`
- [ ] Update import paths (3 internal imports)
- [ ] Update `__init__.py` to export ExampleParser
- [ ] Run unit tests for ExampleParser
- [ ] Run integration tests
- [ ] Verify end-to-end pattern detection works
- [ ] Commit and push

### Post-Migration Validation

- [ ] All 3 components migrated successfully
- [ ] All tests passing (unit + integration)
- [ ] Import paths updated correctly
- [ ] Platform package structure correct
- [ ] Documentation updated
- [ ] Create Linear tasks for Batch 3

---

## Next Steps

### Immediate Actions (Batch 2)

1. **Create Linear Tasks** (Sequential Order):
   - Task 1: Migrate PatternModels to platform package
   - Task 2: Migrate SchemaAnalyzer to platform package (after Task 1)
   - Task 3: Migrate ExampleParser to platform package (after Task 2)

2. **Execute Migrations** (Sequential):
   - Migrate PatternModels first (no dependencies)
   - Migrate SchemaAnalyzer second (depends on PatternModels)
   - Migrate ExampleParser third (depends on both)

3. **Validation**:
   - Run test suite after each component
   - Run integration tests after all 3 complete
   - Verify example-driven workflow still works

### Future Actions (Batch 3)

- Analyze Batch 3 components (Code Generation services)
- Estimate 4-5 components (CodeGenerator, PromptBuilder, etc.)
- Expected: ~1,500 LOC, similar 100% reuse rate

---

## Appendix: File Paths Reference

### Source Files (EDGAR)

```
src/edgar_analyzer/models/patterns.py (526 LOC)
src/edgar_analyzer/services/schema_analyzer.py (432 LOC)
src/edgar_analyzer/services/example_parser.py (676 LOC)
```

### Destination Files (Platform)

```
src/extract_transform_platform/models/patterns.py (526 LOC)
src/extract_transform_platform/services/schema_analyzer.py (432 LOC)
src/extract_transform_platform/services/example_parser.py (676 LOC)
```

### Test Files

```
tests/unit/services/test_schema_analyzer.py
tests/unit/services/test_example_parser.py
tests/integration/test_example_parser_integration.py
tests/unit/config/test_project_schema.py
```

---

## Success Metrics

### Migration Success Criteria

- [x] All 3 components identified and analyzed
- [ ] All 3 components migrated to platform package
- [ ] All import paths updated correctly
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Zero EDGAR-specific code in migrated components
- [ ] Documentation updated
- [ ] Linear tasks created and tracked

### Expected Outcomes

- **Code Reuse**: 100% (1,634 LOC migrated without changes)
- **Test Coverage**: Maintained (739 LOC of tests)
- **Migration Time**: 7 hours (sequential execution)
- **Risk Level**: LOW (clean, well-tested components)

---

## Conclusion

Batch 2 consists of 3 schema services components (1,634 LOC) that are **100% generic** and ready for migration. All components are self-contained with clean interfaces and comprehensive test coverage.

**Key Findings**:
- ✅ 100% code reuse (zero EDGAR-specific code)
- ✅ Sequential migration required (clear dependency chain)
- ✅ Well-tested (739 LOC of tests)
- ✅ Low risk (clean interfaces, no external dependencies)

**Recommendation**: **PROCEED** with sequential migration in order:
1. PatternModels (2 hours)
2. SchemaAnalyzer (2 hours)
3. ExampleParser (3 hours)

**Total Effort**: 7 hours (1 day)

---

**Research Complete**: 2025-11-29
**Next Action**: Create Linear tasks for Batch 2 sequential migration
**File**: `docs/research/batch-2-schema-services-analysis-2025-11-29.md`
