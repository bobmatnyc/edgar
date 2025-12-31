# EDGAR Platform - Claude Code Agent Guide

**Project Type**: General-purpose, example-driven data extraction & transformation platform
**Linear Project**: [EDGAR → General-Purpose Platform](https://linear.app/1m-hyperdev/project/edgar-%E2%86%92-general-purpose-extract-and-transform-platform-e4cb3518b13e/issues)
**Epic ID**: `edgar-e4cb3518b13e` / `4a248615-f1dd-4669-9f61-edec2d2355ac`

---

## Platform Vision & Status

Transform EDGAR into a **general-purpose platform** supporting 4 work paths:
- **a) Project-based workflows** (external artifacts directory)
- **b) File transformation** (Excel, PDF, DOCX, PPTX → structured data)
- **c) Web scraping** (JS-heavy sites with Jina.ai)
- **d) Interactive workflows** (example-driven, user-prompted confidence threshold)

**Current Status**: Phase 2 Complete ✅ (95.6% test pass, 565/591 tests)
**Code Reuse**: 83% from EDGAR (exceeds 70% target)
**Next Phase**: Phase 3 - Polish & Testing (2 weeks)

---

## Quick Start Commands

```bash
# Interactive Chat Mode ✨ (NEW - Phase 3 - DEFAULT)
edgar                                        # Start chat mode (new default!)
edgar --project projects/weather_test/       # Chat with project loaded
edgar --resume last                          # Resume last session
edgar chat --list-sessions                   # List all sessions

# EDGAR Data Extraction
edgar extract --cik 0000320193 --year 2023

# File Transform (Excel/PDF)
edgar analyze-project projects/employee_roster/
edgar generate-code projects/employee_roster/
edgar run-extraction projects/employee_roster/

# Project Management (T7+T8 Complete)
edgar project create my_project --template weather
edgar project list --format table
edgar project validate my_project

# Quality & Testing
make test          # Run all tests (565/591 passing)
make quality       # Run linters, type checks
make build         # Create deployment package

# External Artifacts Setup
export EDGAR_ARTIFACTS_DIR=~/edgar_projects  # Add to ~/.bashrc

# Legacy Command (backward compatibility)
edgar-analyzer chat --project projects/weather_test/  # Still works!
```

---

## Interactive Chat Mode ✨ (Phase 3 - DEFAULT)

**Auggie-style REPL for iterative extraction workflows!**

**Now the default when running `edgar` with no arguments!**

```bash
# Just type 'edgar' to start!
edgar

# Or with options
edgar --project projects/weather_test/

edgar> analyze
✅ Analysis complete

edgar> What patterns did you detect?
→ Interpreted as: patterns
┌──────────────────┬────────────┬──────────────────┐
│ Type             │ Confidence │ Source → Target  │
├──────────────────┼────────────┼──────────────────┤
│ FIELD_MAPPING    │ 100.0%     │ temp → temperature│
│ TYPE_CONVERSION  │ 95.0%      │ timestamp → date │
└──────────────────┴────────────┴──────────────────┘

edgar> confidence 0.85
✅ Confidence threshold: 70.0% → 85.0%

edgar> generate
✅ Code generation complete!
```

**Features**:
- 🗣️ **Natural language understanding** - Ask questions naturally
- 🔄 **Session save/restore** - Resume work seamlessly
- 🎨 **Rich terminal UI** - Beautiful tables and progress indicators
- ⚡ **Tab completion & history** - Efficient command entry
- 🎯 **Confidence threshold tuning** - Adjust pattern sensitivity interactively

**Quick Commands**:
```bash
# Start fresh session (new default!)
edgar
edgar chat

# With project loaded
edgar --project <path>
edgar chat --project <path>

# Resume last session
edgar --resume last
edgar chat --resume last

# List saved sessions
edgar chat --list-sessions
```

**Available Commands** (in session):
- `analyze` - Detect transformation patterns
- `patterns` - Show detected patterns
- `generate` - Generate extraction code
- `validate` - Validate code quality
- `extract` - Run extraction
- `confidence <0.0-1.0>` - Set threshold
- `save [name]` - Save session
- `resume [name]` - Restore session
- `help` - Show all commands

**Natural Language Examples**:
- "What patterns did you detect?"
- "Show me the examples"
- "Generate the code"
- "Set confidence to 0.85"

See [Interactive Chat Mode Guide](docs/guides/INTERACTIVE_CHAT_MODE.md) for complete documentation.

---

## Code Architecture

### Platform Package Structure (Preferred)

```
src/extract_transform_platform/
├── core/                        # BaseDataSource, IDataExtractor
├── data_sources/
│   ├── file/                    # ExcelDataSource, PDFDataSource, CSVDataSource
│   └── web/                     # APIDataSource, JinaDataSource
├── ai/                          # OpenRouterClient, PromptTemplates
├── models/                      # PatternModels (14 types), ProjectConfig
├── services/
│   ├── analysis/                # SchemaAnalyzer, ExampleParser
│   ├── project_manager/         # ProjectManager (T7 - 622 LOC, 95% coverage)
│   └── cache_service.py
└── codegen/                     # Code generator, validator
```

**Import Paths** (Platform - Preferred):
```python
from extract_transform_platform.core import IDataExtractor, BaseDataSource
from extract_transform_platform.data_sources.file import ExcelDataSource, PDFDataSource
from extract_transform_platform.data_sources.web import APIDataSource, JinaDataSource
from extract_transform_platform.ai import OpenRouterClient
from extract_transform_platform.models.patterns import Pattern, PatternType
from extract_transform_platform.services.analysis import SchemaAnalyzer, ExampleParser
from extract_transform_platform.services.project_manager import ProjectManager
```

**Legacy EDGAR Paths** (Deprecated but functional):
```python
from edgar_analyzer.data_sources.excel_source import ExcelDataSource  # OLD
from edgar_analyzer.services.openrouter_client import OpenRouterClient  # OLD
```

---

## Platform Components (Phase 2 Complete)

### Batch 1: Data Sources ✅ (T2 - 1M-377)
- **ExcelDataSource** (398 LOC, 80% coverage) - .xlsx/.xls with pandas
- **PDFDataSource** (481 LOC, 77% coverage) - Tables with pdfplumber (lines/text/mixed)
- **APIDataSource** (242 LOC) - Generic REST API client
- **JinaDataSource** (245 LOC) - Web scraping for JS-heavy sites
- **FileDataSource** (290 LOC) - CSV/JSON/YAML

### Batch 2: Schema Services ✅ (T3 - 1M-378)
- **PatternModels** (530 LOC) - 14 transformation pattern types
- **SchemaAnalyzer** (436 LOC) - Schema inference & comparison (<100ms for 10 examples)
- **ExampleParser** (679 LOC) - Pattern extraction from 2-3 examples

### Batch 3: Platform Services ✅
- **ProjectManager** (T7 - 622 LOC) - CRUD operations, YAML config, caching
- **CLI Integration** (T8 - 240 LOC) - Refactored to use ProjectManager service
- **OpenRouter Client** (T5) - 100% platform code, Sonnet 4.5 integration
- **IDataExtractor Interface** (T6) - Abstract interface for generated extractors

### Batch 4: Meta-Extractor System ✅ (Phase 4 Complete)
- **MetaExtractor** (629 LOC) - End-to-end orchestrator for extractor generation
- **ExtractorSynthesizer** (790 LOC) - Pattern analysis & code generation from examples
- **ExtractorRegistry** (509 LOC) - Dynamic loading & versioning of extractors
- **SelfImprovementLoop** (787 LOC) - Iterative refinement based on test failures
- **FailureAnalyzer** (739 LOC) - Failure categorization & improvement suggestions
- **Patent Extractor** (POC) - Production-ready extractor for USPTO patent data

---

## Meta-Extractor: Auto-Generate Custom Extractors ✨

**Create production-ready extractors from 2-3 examples in <5 seconds!**

### Quick Start

```bash
# Create examples (input/output pairs)
mkdir -p examples/my_domain/
cat > examples/my_domain/example1.json <<EOF
{
  "input": {"html": "<table>...</table>", "url": "https://..."},
  "output": {"records": [...], "count": 1}
}
EOF

# Generate extractor automatically
edgar extractors create my_extractor \
  --examples examples/my_domain/ \
  --description "Extract data from HTML tables"

# Output:
# ✅ Extractor created successfully!
#    Domain: my_domain
#    Confidence: 94.2%
#    Files: 4
#    Time: 3.42s
#    Registered as: my_extractor
```

### CLI Commands

```bash
# Create extractor from examples
edgar extractors create <name> --examples <dir> [OPTIONS]

# List registered extractors
edgar extractors list [--domain <domain>] [--min-confidence <0.0-1.0>]

# Show extractor details
edgar extractors info <name>

# Validate extractor
edgar extractors validate <name>
```

### Usage Example

```python
from edgar_analyzer.extractors.registry import ExtractorRegistry
from edgar_analyzer.services.openrouter_client import OpenRouterClient

# Load extractor dynamically
registry = ExtractorRegistry()
ExtractorClass = registry.get("my_extractor")

# Initialize with OpenRouter client
openrouter = OpenRouterClient()
extractor = ExtractorClass(openrouter_client=openrouter)

# Extract data
input_data = {"html": "<html>...</html>", "url": "https://example.com"}
result = extractor.extract(input_data)
print(result)  # {"records": [...], "count": 1}
```

### Key Features

1. **Automatic Pattern Detection** - Analyzes examples to detect 14 transformation types
2. **Code Generation** - Renders Jinja2 templates for complete extractor packages
3. **Validation** - Ensures generated code meets quality standards
4. **Registry** - Dynamic loading and versioning
5. **Self-Improvement** - Iteratively refines based on test failures (Phase 4)

### Generated Files

```
src/edgar_analyzer/extractors/my_domain/
├── __init__.py            # Package initialization
├── extractor.py           # Main extractor class (~200 LOC)
├── models.py              # Pydantic models (~80 LOC)
├── prompts.py             # LLM system prompts (~50 LOC)
└── test_my_extractor.py   # Unit tests (~150 LOC)
```

### Confidence Scores

| Score | Meaning | Action |
|-------|---------|--------|
| 0.95-1.00 | Excellent | ✅ Production ready |
| 0.85-0.94 | Good | ✅ Safe to use |
| 0.70-0.84 | Fair | ⚠️ Review code |
| <0.70 | Poor | ❌ Improve examples |

### Key Files

```
src/edgar_analyzer/extractors/
├── meta_extractor.py       # Orchestrator (629 LOC)
├── synthesizer.py          # Pattern analysis (790 LOC)
├── registry.py             # Dynamic loading (509 LOC)
├── self_improvement.py     # Iterative refinement (787 LOC)
├── failure_analyzer.py     # Failure analysis (739 LOC)
├── templates/              # Jinja2 code templates
│   ├── extractor.py.j2
│   ├── models.py.j2
│   ├── prompts.py.j2
│   └── test_extractor.py.j2
└── patent/                 # Example: Patent extractor (POC)
    ├── extractor.py
    ├── models.py
    └── prompts.py
```

### Documentation

- **[User Guide](docs/user/META_EXTRACTOR_USER_GUIDE.md)** - Complete usage guide with examples
- **[API Reference](docs/developer/api/META_EXTRACTOR_API.md)** - Detailed API documentation
- **[Architecture](docs/developer/architecture/META_EXTRACTOR_ARCHITECTURE.md)** - System design & diagrams
- **[Troubleshooting](docs/user/META_EXTRACTOR_TROUBLESHOOTING.md)** - Common issues & solutions

---

## File Transform Workflows

### Excel → JSON Transform

**Setup** (5 steps):
```bash
cd projects/ && mkdir my_excel_project && cd my_excel_project
mkdir input examples output
cp /path/to/file.xlsx input/data.xlsx
# Create 2-3 examples (see employee_roster POC)
cat > project.yaml <<EOF
name: My Excel Transform
data_source:
  type: excel
  config:
    file_path: input/data.xlsx
    sheet_name: 0
examples: [examples/row1.json, examples/row2.json]
EOF
python -m edgar_analyzer analyze-project .
python -m edgar_analyzer generate-code .
python -m edgar_analyzer run-extraction .
```

**Automatic Transformations**:
| Type | Example |
|------|---------|
| Field Rename | `employee_id` → `id` |
| Concatenation | `first_name + last_name` → `full_name` |
| Type Conversion | `95000` (int) → `95000.0` (float) |
| Boolean Normalization | `"Yes"` → `true`, `"No"` → `false` |
| Currency Parsing | `"$15.00"` → `15.0` |
| Value Mapping | `"A"` → `"Active"` |

### PDF → JSON Transform

**Table Extraction Strategies**:
- **Lines** - Bordered tables (invoices, reports)
- **Text** - Borderless tables (plain text)
- **Mixed** - Hybrid approach (partial borders)

**Setup** (same 5-step pattern as Excel, change type to `pdf`):
```yaml
data_source:
  type: pdf
  config:
    file_path: input/invoice.pdf
    page_number: 0
    table_strategy: lines  # or text, mixed
```

---

## Project Templates

**Available Templates**:
1. **Weather API** - REST API extraction (OpenWeatherMap, 468 LOC)
2. **News Scraper** - Web scraping (Jina.ai, 263 LOC)
3. **Minimal** - Bare-bones starter (144 LOC)

**Quick Start**:
```bash
cp templates/news_scraper_project.yaml projects/my_news/project.yaml
# Customize: name, data source, examples
python -m edgar_analyzer project create my_news --template news_scraper
```

---

## External Artifacts Directory

**Benefits**: Clean repo, unlimited storage, easy backup, shared access

**Setup**:
```bash
export EDGAR_ARTIFACTS_DIR=~/edgar_projects  # Add to ~/.bashrc
source ~/.bashrc
python -m edgar_analyzer project create test --template weather
# Project created at: ~/edgar_projects/projects/test/
```

**Structure**:
```
$EDGAR_ARTIFACTS_DIR/
├── output/       # Reports (Excel, JSON, CSV)
├── projects/     # User workspaces
├── data/         # cache/, checkpoints/, backups/
└── logs/
```

---

## Development Patterns

### Code Quality Standards
```bash
black src/ tests/          # Format code
isort src/ tests/          # Sort imports
flake8 src/ tests/         # Lint code
mypy src/                  # Type checking
pytest tests/              # Run tests
```

### Testing Pattern
```python
import pytest
from extract_transform_platform.data_sources.file import ExcelDataSource

def test_excel_read():
    source = ExcelDataSource(file_path="test.xlsx", sheet_name=0)
    data = source.read()
    assert data is not None
```

### Dependency Injection
```python
from edgar_analyzer.config.container import Container

container = Container()
container.wire(modules=[__name__])
service = container.edgar_api_service()
```

---

## EDGAR-Specific Features (Legacy)

### Key Components
1. **XBRL Extraction** - `breakthrough_xbrl_service.py` (2x success rate)
2. **Multi-Source Integration** - EDGAR + Fortune + XBRL
3. **Report Generation** - CSV/Excel outputs

### Tech Stack
- **Python 3.11+** | **Click, Pandas, Pydantic, BeautifulSoup4**
- **Data Sources**: SEC EDGAR API, XBRL filings, Fortune rankings
- **Tools**: pytest, black, isort, mypy, pre-commit

---

## Documentation Index

**User Guides**:
- [Quick Start](docs/guides/QUICK_START.md) | [CLI Usage](docs/guides/CLI_USAGE.md)
- [Excel Transform](docs/guides/EXCEL_FILE_TRANSFORM.md) | [PDF Transform](docs/guides/PDF_FILE_TRANSFORM.md)
- [External Artifacts](docs/guides/EXTERNAL_ARTIFACTS.md)

**Technical Docs**:
- [Architecture](docs/architecture/PROJECT_STRUCTURE.md) | [Platform API](docs/api/PLATFORM_API.md)
- [ExcelDataSource](docs/architecture/EXCEL_DATA_SOURCE.md) | [PDFDataSource](docs/architecture/PDF_DATA_SOURCE.md)
- [ProjectManager API](docs/api/PROJECT_MANAGER_API.md)

**Migration Guides**:
- [Platform Migration](docs/guides/PLATFORM_MIGRATION.md)
- [Pattern Detection](docs/guides/PATTERN_DETECTION.md)

---

## Pattern Types (14 Supported)

`FIELD_MAPPING`, `CONCATENATION`, `TYPE_CONVERSION`, `BOOLEAN_CONVERSION`, `VALUE_MAPPING`, `FIELD_EXTRACTION`, `NESTED_ACCESS`, `LIST_AGGREGATION`, `CONDITIONAL`, `DATE_PARSING`, `MATH_OPERATION`, `STRING_FORMATTING`, `DEFAULT_VALUE`, `CUSTOM`

---

## Performance Benchmarks

| Rows | Columns | File Size | Read Time | Memory |
|------|---------|-----------|-----------|--------|
| 100 | 7 | 15 KB | 45 ms | 3 MB |
| 1,000 | 7 | 120 KB | 180 ms | 12 MB |
| 10,000 | 7 | 1.2 MB | 950 ms | 85 MB |

**End-to-End**: <10 seconds (read → analyze → generate → validate)

---

## Environment Setup

```bash
# .env.local (gitignored)
OPENROUTER_API_KEY=your_api_key_here
SEC_EDGAR_USER_AGENT=YourName/YourEmail
LOG_LEVEL=INFO
EDGAR_ARTIFACTS_DIR=~/edgar_projects  # Optional

# Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

---

## Common Tasks

**Add New Company Analysis**:
```bash
vim data/companies/fortune_500_complete.json
python -m edgar_analyzer extract --cik <CIK> --year 2023
ls -la output/
```

**Debug Extraction**:
```bash
export LOG_LEVEL=DEBUG
python tests/debug_xbrl_concepts.py
tail -f logs/edgar_analyzer.log
```

**Update Documentation**:
```bash
vim docs/guides/QUICK_START.md
grep -r "](.*\.md)" docs/  # Validate links
open docs/README.md
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **API Rate Limiting** | `export EDGAR_RATE_LIMIT_DELAY=0.5` |
| **XBRL Extraction Fails** | `python tests/debug_xbrl_concepts.py` |
| **Data Validation Errors** | `python tests/run_comprehensive_qa.py` |
| **Import Errors** | `pip install -e ".[dev]"` |

---

## Agent Best Practices

### Code Quality
1. Run tests before committing (`pytest tests/`)
2. Format code automatically (`black`, `isort`)
3. Type hints required (`mypy` for type checking)
4. Document complex logic (clear docstrings)

### File Organization
1. Tests in `tests/` mirror `src/`
2. Results in `tests/results/`
3. Documentation in `docs/` by category
4. Cache in `data/cache/`

### Performance
1. Use caching for API responses
2. Batch operations for parallel processing
3. Checkpoint analysis for intermediate results
4. Monitor rate limits (SEC EDGAR)

---

## Success Criteria (Platform Transformation)

- ✅ Phase 1 MVP validated (92% confidence)
- ✅ Phase 2 Complete (All 16 tickets delivered)
- ✅ All 4 work paths functional
- ✅ Excel/PDF/DOCX/PPTX support
- ✅ External artifacts directory
- ✅ JS-heavy web scraping (Jina.ai)
- ✅ 95.6% test pass rate (565/591 tests)
- ✅ 80%+ coverage achieved
- ✅ Code quality standards met

**User Preferences (2025-11-28)**:
1. Office format priority: Excel → PDF → DOCX → PPTX
2. Artifact storage: External directory
3. Web scraping: Jina.ai (key provided)
4. Example collection: Exemplar-based with data types
5. Confidence threshold: User-prompted
6. Project workflow: Sequential (one at a time)

---

**Linear Project**: [View all issues](https://linear.app/1m-hyperdev/project/edgar-%E2%86%92-general-purpose-extract-and-transform-platform-e4cb3518b13e/issues)
**Contact**: See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for full context.
