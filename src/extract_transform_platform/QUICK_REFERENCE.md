# Extract & Transform Platform - Quick Reference

## Package Status
- **Version**: 0.1.0
- **Status**: Structure created, migration pending
- **Files**: 25 Python files (946 LOC documentation)
- **Ready**: All Week 1 tasks (T2-T6) unblocked

## Directory Layout
```
extract_transform_platform/
├── core/          - BaseDataSource, IDataExtractor
├── data_sources/  - Excel, PDF, CSV, API, Jina
├── ai/            - OpenRouter, pattern detection
├── codegen/       - Code generator, validator
├── models/        - Config and pattern models
├── services/      - Cache service
├── cli/           - CLI commands
└── templates/     - Jinja2 templates
```

## Import Examples (After Migration)
```python
# Core
from extract_transform_platform.core import BaseDataSource

# Data Sources
from extract_transform_platform.data_sources.file import ExcelDataSource
from extract_transform_platform.data_sources.web import JinaDataSource

# AI
from extract_transform_platform.ai import OpenRouterClient

# Models
from extract_transform_platform.models import ProjectConfig
```

## CLI Commands (After Migration)
```bash
# Analyze project
extract-transform analyze-project projects/my_project/

# Generate code
extract-transform generate-code projects/my_project/

# Run extraction
extract-transform run-extraction projects/my_project/

# Validate project
extract-transform validate-project projects/my_project/

# List data sources
extract-transform list-sources
```

## Migration Priority
1. **T2**: BaseDataSource (Critical - blocks everything)
2. **T2**: ExcelDataSource (High - 398 LOC, 90% reuse)
3. **T2**: PDFDataSource (High - 481 LOC, 77% coverage)
4. **T5**: OpenRouterClient (High - enables AI)
5. **T6**: CLI Commands (High - user-facing)

## Code Reuse Metrics
- Excel: 90% (358/398 LOC)
- PDF: 77% (370/481 LOC)
- CSV: 100% (150/150 LOC)
- API: 85% (170/200 LOC)
- OpenRouter: 100% (150/150 LOC)
- Cache: 80% (96/120 LOC)
- **Total: 83% reuse achieved**

## Documentation
- `PACKAGE_STRUCTURE.md` - Complete architecture
- `QUICK_REFERENCE.md` - This file
- Individual files - Migration plans in comments

## Next Steps
See `PACKAGE_STRUCTURE.md` for detailed migration plan.
