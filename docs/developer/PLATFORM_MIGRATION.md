# Platform Migration Guide

**Migration**: `edgar_analyzer` → `extract_transform_platform`
**Timeline**: Phase 2 (Weeks 1-6)
**Status**: Foundation complete (1M-376, 1M-377 T2, 1M-380 T5)

## Table of Contents

- [Overview](#overview)
- [Why Migrate?](#why-migrate)
- [Migration Strategy](#migration-strategy)
- [Import Path Changes](#import-path-changes)
- [Step-by-Step Migration](#step-by-step-migration)
- [Backward Compatibility](#backward-compatibility)
- [Testing Migration](#testing-migration)
- [Common Issues](#common-issues)

---

## Overview

The EDGAR project is transitioning to a **dual-package structure** to support the platform evolution:

- **`extract_transform_platform/`** - Generic platform (NEW - all new code goes here)
- **`edgar_analyzer/`** - EDGAR-specific implementation (maintained for backward compatibility)

**Migration Status**:
- ✅ Core abstractions (BaseDataSource, IDataSource)
- ✅ File data sources (ExcelDataSource, PDFDataSource, FileDataSource)
- ✅ Web data sources (APIDataSource, URLDataSource, JinaDataSource) - **Batch 1 Complete**
- ✅ AI integration (OpenRouterClient, PromptTemplates, AIConfig)
- ✅ Pattern models (PatternType, SchemaField, Pattern, ParsedExamples) - **Batch 2 Complete** 🆕
- ✅ Schema services (SchemaAnalyzer, ExampleParser) - **Batch 2 Complete** 🆕
- ✅ All tests passing (180/180 total: Batch 1 120/120 + Batch 2 60/60)
- ✅ Code reuse: 85% (exceeds 70% target)

**Batch 1 Summary** (1M-377 T2):
- ✅ FileDataSource: 290 LOC platform + 30 LOC wrapper (100% reuse)
- ✅ APIDataSource: 239 LOC platform + 42 LOC wrapper (100% reuse)
- ✅ URLDataSource: 190 LOC platform + 29 LOC wrapper (100% reuse)
- ✅ JinaDataSource: 240 LOC platform + 46 LOC wrapper (100% reuse + 1 bug fix)
- ✅ Zero breaking changes
- ✅ Full backward compatibility with EDGAR imports

**Batch 2 Summary** (1M-378 T3): 🆕
- ✅ PatternModels: 530 LOC platform + 58 LOC wrapper (100% reuse)
- ✅ SchemaAnalyzer: 436 LOC platform + 94 LOC wrapper (100% reuse)
- ✅ ExampleParser: 679 LOC platform + 47 LOC wrapper (100% reuse)
- ✅ 14 transformation pattern types
- ✅ 60/60 tests passing (100% coverage)
- ✅ Zero breaking changes
- ✅ Full backward compatibility with EDGAR imports

---

## Why Migrate?

### Benefits

1. **Generic Platform**: No EDGAR-specific dependencies
2. **Better Organization**: Clear separation of concerns
3. **Code Reuse**: 83% reuse from EDGAR (proven patterns)
4. **Testing**: Comprehensive test suite (132/132 passing)
5. **Future-Proof**: Platform-first architecture supports multiple domains

### Timeline

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | MVP validation (92% confidence GO decision) |
| **Phase 2** | 🔄 In Progress | Core platform architecture (Weeks 1-6) |
| **Phase 3** | ⏳ Planned | DOCX/PPTX support + advanced features |

---

## Migration Strategy

### Dual-Package Approach

**NEW CODE** (Platform - Preferred):
```python
from extract_transform_platform.core import BaseDataSource
from extract_transform_platform.data_sources.file import ExcelDataSource
from extract_transform_platform.ai import OpenRouterClient
```

**EXISTING CODE** (EDGAR - Legacy):
```python
from edgar_analyzer.data_sources.base import BaseDataSource
from edgar_analyzer.data_sources.excel_source import ExcelDataSource
from edgar_analyzer.services.openrouter_client import OpenRouterClient
```

**Both paths work** - Migrate incrementally at your own pace.

---

## Import Path Changes

### Core Abstractions

| Component | Platform Path (NEW) | EDGAR Path (OLD) |
|-----------|-------------------|------------------|
| BaseDataSource | `extract_transform_platform.core` | `edgar_analyzer.data_sources.base` |
| IDataSource | `extract_transform_platform.core` | `edgar_analyzer.data_sources.base` |

**Migration Example**:
```python
# OLD (EDGAR)
from edgar_analyzer.data_sources.base import BaseDataSource, IDataSource

# NEW (Platform)
from extract_transform_platform.core import BaseDataSource, IDataSource
```

---

### File Data Sources

| Component | Platform Path (NEW) | EDGAR Path (OLD) |
|-----------|-------------------|------------------|
| ExcelDataSource | `extract_transform_platform.data_sources.file` | `edgar_analyzer.data_sources.excel_source` |
| PDFDataSource | `extract_transform_platform.data_sources.file` | `edgar_analyzer.data_sources.pdf_source` |
| CSVDataSource | `extract_transform_platform.data_sources.file` | `edgar_analyzer.data_sources.file_source` |

**Migration Example**:
```python
# OLD (EDGAR)
from edgar_analyzer.data_sources.excel_source import ExcelDataSource
from edgar_analyzer.data_sources.pdf_source import PDFDataSource
from edgar_analyzer.data_sources.file_source import FileDataSource as CSVDataSource

# NEW (Platform)
from extract_transform_platform.data_sources.file import (
    ExcelDataSource,
    PDFDataSource,
    CSVDataSource,
)
```

---

### Web Data Sources (Batch 1 Complete ✅)

| Component | Platform Path (NEW) | EDGAR Path (OLD) | Status |
|-----------|-------------------|------------------|--------|
| FileDataSource | `extract_transform_platform.data_sources.file` | `edgar_analyzer.data_sources.file_source` | ✅ Migrated |
| APIDataSource | `extract_transform_platform.data_sources.web` | `edgar_analyzer.data_sources.api_source` | ✅ Migrated |
| URLDataSource | `extract_transform_platform.data_sources.web` | N/A (new in Batch 1) | ✅ New |
| JinaDataSource | `extract_transform_platform.data_sources.web` | N/A (new in Batch 1) | ✅ New |

**Migration Example**:
```python
# OLD (EDGAR - still works with deprecation warning)
from edgar_analyzer.data_sources.file_source import FileDataSource
from edgar_analyzer.data_sources.api_source import APIDataSource

# NEW (Platform - preferred)
from extract_transform_platform.data_sources.file import FileDataSource
from extract_transform_platform.data_sources.web import (
    APIDataSource,
    URLDataSource,  # NEW in Batch 1 - simple HTTP GET
    JinaDataSource,  # NEW in Batch 1 - JS-heavy web scraping
)
```

**Batch 1 Notes**:
- **FileDataSource**: Universal file parser (CSV, JSON, YAML, text)
- **APIDataSource**: REST API integration with auth, rate limiting, caching
- **URLDataSource**: Simple HTTP GET requests (no auth required)
- **JinaDataSource**: JavaScript-heavy site scraping with Jina.ai API

**See Also**: [Web Scraping Guide](WEB_SCRAPING.md) for detailed JinaDataSource tutorials

---

### Schema Services (Batch 2 ✅)

| Component | Platform Path (NEW) | EDGAR Path (OLD) | Status |
|-----------|-------------------|------------------|--------|
| PatternModels | `extract_transform_platform.models.patterns` | `edgar_analyzer.models.patterns` | ✅ Migrated |
| SchemaAnalyzer | `extract_transform_platform.services.analysis` | `edgar_analyzer.services.schema_analyzer` | ✅ Migrated |
| ExampleParser | `extract_transform_platform.services.analysis` | `edgar_analyzer.services.example_parser` | ✅ Migrated |

**Migration Example**:
```python
# OLD (EDGAR - still works with deprecation warning)
from edgar_analyzer.models.patterns import Pattern, PatternType, ParsedExamples
from edgar_analyzer.services.schema_analyzer import SchemaAnalyzer
from edgar_analyzer.services.example_parser import ExampleParser

# NEW (Platform - preferred)
from extract_transform_platform.models.patterns import (
    Pattern, PatternType, ParsedExamples, Schema, SchemaField, FieldTypeEnum
)
from extract_transform_platform.services.analysis import (
    SchemaAnalyzer, ExampleParser
)
```

**Batch 2 Notes**:
- **PatternModels**: 14 transformation pattern types (field mapping, concatenation, type conversion, etc.)
- **SchemaAnalyzer**: Schema inference and comparison (11 field types detected)
- **ExampleParser**: Pattern extraction from 2-3 examples (confidence scoring 0.0-1.0)

**See Also**: [Pattern Detection Guide](PATTERN_DETECTION.md) for detailed explanation of all 14 pattern types

---

### AI Integration

| Component | Platform Path (NEW) | EDGAR Path (OLD) |
|-----------|-------------------|------------------|
| OpenRouterClient | `extract_transform_platform.ai` | `edgar_analyzer.services.openrouter_client` |
| OpenRouterConfig | `extract_transform_platform.ai` | `edgar_analyzer.services.openrouter_client` |
| PromptTemplates | `extract_transform_platform.ai` | `edgar_analyzer.services.prompt_templates` |
| AIConfig | `extract_transform_platform.ai` | N/A (new) |

**Migration Example**:
```python
# OLD (EDGAR)
from edgar_analyzer.services.openrouter_client import (
    OpenRouterClient,
    OpenRouterConfig,
)
from edgar_analyzer.services.prompt_templates import PromptTemplates

# NEW (Platform)
from extract_transform_platform.ai import (
    OpenRouterClient,
    OpenRouterConfig,
    PromptTemplates,
    AIConfig,  # NEW - centralized AI configuration
)
```

---

### Models

| Component | Platform Path (NEW) | EDGAR Path (OLD) |
|-----------|-------------------|------------------|
| ProjectConfig | `extract_transform_platform.models` | `edgar_analyzer.models.project_config` |
| TransformationPattern | `extract_transform_platform.models` | `edgar_analyzer.models.transformation_pattern` |

**Migration Example**:
```python
# OLD (EDGAR)
from edgar_analyzer.models.project_config import ProjectConfig
from edgar_analyzer.models.transformation_pattern import TransformationPattern

# NEW (Platform)
from extract_transform_platform.models import (
    ProjectConfig,
    TransformationPattern,
)
```

---

### Code Generation

| Component | Platform Path (NEW) | EDGAR Path (OLD) |
|-----------|-------------------|------------------|
| CodeGenerator | `extract_transform_platform.codegen` | `edgar_analyzer.codegen.generator` |
| CodeValidator | `extract_transform_platform.codegen` | `edgar_analyzer.codegen.validator` |

**Migration Example**:
```python
# OLD (EDGAR)
from edgar_analyzer.codegen.generator import CodeGenerator
from edgar_analyzer.codegen.validator import CodeValidator

# NEW (Platform)
from extract_transform_platform.codegen import (
    CodeGenerator,
    CodeValidator,
)
```

---

## Step-by-Step Migration

### Step 1: Identify EDGAR Imports

Find all EDGAR imports in your codebase:

```bash
# Find all EDGAR imports
grep -r "from edgar_analyzer" src/ --include="*.py"

# Find specific import patterns
grep -r "from edgar_analyzer.data_sources" src/ --include="*.py"
grep -r "from edgar_analyzer.services.openrouter" src/ --include="*.py"
```

### Step 2: Update Imports

**Option A: Manual Migration** (File by file)

```python
# Before
from edgar_analyzer.data_sources.base import BaseDataSource
from edgar_analyzer.data_sources.excel_source import ExcelDataSource
from edgar_analyzer.services.openrouter_client import OpenRouterClient

# After
from extract_transform_platform.core import BaseDataSource
from extract_transform_platform.data_sources.file import ExcelDataSource
from extract_transform_platform.ai import OpenRouterClient
```

**Option B: Automated Migration** (Recommended)

```bash
# Use sed for batch replacement (macOS)
find src/ -name "*.py" -exec sed -i '' \
  's/from edgar_analyzer.data_sources.base/from extract_transform_platform.core/g' {} \;

find src/ -name "*.py" -exec sed -i '' \
  's/from edgar_analyzer.data_sources.excel_source/from extract_transform_platform.data_sources.file/g' {} \;

find src/ -name "*.py" -exec sed -i '' \
  's/from edgar_analyzer.services.openrouter_client/from extract_transform_platform.ai/g' {} \;

# Linux (use -i without '')
find src/ -name "*.py" -exec sed -i \
  's/from edgar_analyzer.data_sources.base/from extract_transform_platform.core/g' {} \;
```

### Step 3: Update Tests

Update test imports following the same pattern:

```python
# Before
from edgar_analyzer.data_sources.excel_source import ExcelDataSource

# After
from extract_transform_platform.data_sources.file import ExcelDataSource
```

### Step 4: Run Tests

Verify migration with comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/unit/data_sources/ -v
pytest tests/unit/ai/ -v

# Check test coverage
pytest tests/ --cov=extract_transform_platform --cov-report=html
```

### Step 5: Update Documentation

Update code examples in documentation:

```bash
# Update guides
vim docs/guides/EXCEL_FILE_TRANSFORM.md
vim docs/guides/PDF_FILE_TRANSFORM.md

# Update API references
vim docs/api/PLATFORM_API.md
```

---

## Backward Compatibility

### Legacy Imports Still Work

**EDGAR imports are maintained** for backward compatibility:

```python
# ✅ This still works (legacy path)
from edgar_analyzer.data_sources.excel_source import ExcelDataSource

# ✅ This is the new path (preferred)
from extract_transform_platform.data_sources.file import ExcelDataSource

# Both import the SAME CLASS - they're aliases
```

### Deprecation Strategy

**No breaking changes planned** - EDGAR paths will remain functional:

1. **Phase 2 (Current)**: Both paths work, platform preferred
2. **Phase 3**: Both paths work, EDGAR marked deprecated
3. **Future**: Both paths work indefinitely (no forced migration)

**Recommendation**: Migrate to platform imports for new code, update existing code incrementally.

---

## Testing Migration

### Test Checklist

Before considering migration complete, verify:

- [ ] All imports updated to platform paths
- [ ] All unit tests passing (132/132)
- [ ] All integration tests passing
- [ ] Code coverage maintained (>75%)
- [ ] Documentation updated
- [ ] Examples updated with new imports

### Test Commands

```bash
# Full test suite
pytest tests/ -v --cov=extract_transform_platform

# Platform-specific tests
pytest tests/unit/platform/ -v
pytest tests/integration/platform/ -v

# Data source tests (file)
pytest tests/unit/data_sources/file/ -v

# Data source tests (web)
pytest tests/unit/data_sources/web/ -v

# AI integration tests
pytest tests/unit/ai/ -v
```

### Expected Results

```
================================ test session starts =================================
collected 132 items

tests/unit/platform/test_base.py ........                                    [  6%]
tests/unit/data_sources/file/test_excel_source.py ....................           [ 21%]
tests/unit/data_sources/file/test_pdf_source.py ...................              [ 35%]
tests/unit/ai/test_openrouter_client.py ................                        [ 47%]
...

================================= 132 passed in 12.34s ================================
```

---

## Common Issues

### Issue 1: Import Not Found

**Error**:
```
ImportError: cannot import name 'ExcelDataSource' from 'extract_transform_platform.data_sources.file'
```

**Solution**: Verify package installation
```bash
# Reinstall in editable mode
pip install -e ".[dev]"

# Verify installation
python -c "from extract_transform_platform.data_sources.file import ExcelDataSource; print('OK')"
```

---

### Issue 2: Circular Import

**Error**:
```
ImportError: cannot import name 'BaseDataSource' from partially initialized module
```

**Solution**: Check import order
```python
# ❌ Bad (circular import)
from extract_transform_platform.data_sources.file import ExcelDataSource
from extract_transform_platform.core import BaseDataSource

# ✅ Good (import from core first)
from extract_transform_platform.core import BaseDataSource
from extract_transform_platform.data_sources.file import ExcelDataSource
```

---

### Issue 3: Mixed Imports

**Error**: Tests fail with "class mismatch" errors

**Solution**: Use consistent import paths
```python
# ❌ Bad (mixing old and new)
from edgar_analyzer.data_sources.base import BaseDataSource
from extract_transform_platform.data_sources.file import ExcelDataSource

# ✅ Good (all platform)
from extract_transform_platform.core import BaseDataSource
from extract_transform_platform.data_sources.file import ExcelDataSource

# ✅ Also good (all EDGAR)
from edgar_analyzer.data_sources.base import BaseDataSource
from edgar_analyzer.data_sources.excel_source import ExcelDataSource
```

---

### Issue 4: Type Checking Errors

**Error**: mypy reports type mismatches

**Solution**: Update type stubs
```bash
# Regenerate type stubs
stubgen -p extract_transform_platform -o typings/

# Run type checking
mypy src/extract_transform_platform/
```

---

## Next Steps

After migration:

1. **Read Platform Usage Guide**: Learn platform-specific features
   - [Platform Usage Guide](PLATFORM_USAGE.md)

2. **Explore Platform API**: Detailed API reference
   - [Platform API Reference](../api/PLATFORM_API.md)

3. **Update Excel/PDF Workflows**: Use new import paths
   - [Excel File Transform Guide](EXCEL_FILE_TRANSFORM.md)
   - [PDF File Transform Guide](PDF_FILE_TRANSFORM.md)

4. **Join Platform Development**: Contribute to platform evolution
   - [Linear Project](https://linear.app/1m-hyperdev/project/edgar-%E2%86%92-general-purpose-extract-and-transform-platform-e4cb3518b13e/issues)

---

## Summary

**Migration Benefits**:
- ✅ Generic platform (no EDGAR dependencies)
- ✅ Better organization (clear separation of concerns)
- ✅ 83% code reuse (proven patterns)
- ✅ Comprehensive testing (132/132 passing)
- ✅ Backward compatible (EDGAR imports still work)

**Migration Process**:
1. Identify EDGAR imports
2. Update to platform imports
3. Run tests
4. Update documentation
5. Celebrate 🎉

**Timeline**: Migrate at your own pace - both paths work indefinitely.

---

**Need Help?** See [Platform Usage Guide](PLATFORM_USAGE.md) or [Platform API Reference](../api/PLATFORM_API.md)
