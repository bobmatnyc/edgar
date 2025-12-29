# EDGAR Analyzer - Project Structure

**Purpose**: Complete overview of project organization and codebase structure
**Target**: Developers and AI agents understanding the project layout

---

## Codebase Statistics

### Overall Metrics
- **Total Python Files**: 47
- **Total Lines of Code**: 12,478
- **Total Functions**: 217
- **Total Classes**: 61
- **Test Files**: 50+
- **Documentation Files**: 20+

### Module Distribution
| Module | Lines | Functions | Classes | Purpose |
|--------|-------|-----------|---------|---------|
| **services/** | 7,618 | 112 | 33 | Business logic & APIs |
| **validation/** | 1,431 | 26 | 5 | Data validation |
| **cli/** | 1,378 | 27 | 1 | CLI interface |
| **models/** | 490 | 24 | 11 | Data models |
| **patterns/** | 369 | 5 | 1 | Code patterns |
| **extractors/** | 257 | 6 | 1 | Data extractors |
| **config/** | 220 | 7 | 7 | Configuration |
| **utils/** | 213 | 3 | 1 | Utilities |
| **controllers/** | 187 | 1 | 1 | Controllers |

---

## Directory Tree

```
edgar/
├── .claude/                     # Claude Code agent configurations
│   └── agents/                  # Agent definition files
│       ├── agentic-coder-optimizer.md
│       ├── python_engineer.md
│       └── [30+ other agents]
│
├── .claude-mpm/                 # Claude MPM configuration
│   ├── config/                  # MPM configuration files
│   │   └── project.json
│   ├── memories/                # Agent memory system
│   │   └── agentic-coder-optimizer_memories.md
│   └── logs/                    # MPM logs (gitignored)
│
├── src/                         # Source code
│   ├── edgar_analyzer/          # Main application package
│   │   ├── __init__.py
│   │   ├── __main__.py          # Entry point: python -m edgar_analyzer
│   │   ├── main_cli.py          # CLI entry point
│   │   │
│   │   ├── services/            # Business logic services (7,618 LOC)
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py                      # Service interfaces
│   │   │   ├── breakthrough_xbrl_service.py       # XBRL extraction ⭐
│   │   │   ├── multi_source_enhanced_service.py   # Multi-source integration
│   │   │   ├── edgar_api_service.py               # SEC EDGAR API client
│   │   │   ├── data_extraction_service.py         # Data extraction orchestration
│   │   │   ├── enhanced_data_extraction_service.py
│   │   │   ├── xbrl_enhanced_extraction_service.py
│   │   │   ├── report_service.py                  # Report generation
│   │   │   ├── enhanced_report_service.py
│   │   │   ├── checkpoint_report_service.py
│   │   │   ├── cache_service.py                   # Caching
│   │   │   ├── company_service.py                 # Company data
│   │   │   ├── parallel_processing_service.py     # Parallel processing
│   │   │   ├── checkpoint_extraction_service.py   # Checkpointing
│   │   │   ├── auto_resume_service.py             # Auto-resume
│   │   │   ├── historical_analysis_service.py     # Historical analysis
│   │   │   ├── validation_service.py              # Data validation
│   │   │   ├── llm_service.py                     # LLM integration
│   │   │   ├── openrouter_service.py              # OpenRouter API
│   │   │   ├── fmp_api_service.py                 # Financial Modeling Prep API
│   │   │   ├── agentic_control_service.py         # Agentic control
│   │   │   ├── qa_controller.py                   # Quality assurance
│   │   │   ├── sample_report_generator.py         # Sample reports
│   │   │   ├── enhanced_table_parser.py           # Table parsing
│   │   │   └── model_config.py                    # Model configuration
│   │   │
│   │   ├── models/              # Data models (490 LOC)
│   │   │   ├── __init__.py
│   │   │   ├── company.py                         # Company data model
│   │   │   └── intermediate_data.py               # Processing models
│   │   │
│   │   ├── cli/                 # CLI interface (1,378 LOC)
│   │   │   ├── __init__.py
│   │   │   └── main.py                            # Click-based CLI
│   │   │
│   │   ├── config/              # Configuration (220 LOC)
│   │   │   ├── __init__.py
│   │   │   ├── container.py                       # DI container
│   │   │   └── settings.py                        # Settings management
│   │   │
│   │   ├── validation/          # Data validation (1,431 LOC)
│   │   │   ├── __init__.py
│   │   │   ├── data_validator.py                  # Data quality checks
│   │   │   ├── quality_reporter.py                # Quality reporting
│   │   │   ├── sanity_checker.py                  # Sanity checks
│   │   │   └── source_verifier.py                 # Source verification
│   │   │
│   │   ├── utils/               # Utilities (213 LOC)
│   │   │   ├── __init__.py
│   │   │   └── fortune500_builder.py              # Fortune 500 data builder
│   │   │
│   │   ├── extractors/          # Data extractors (257 LOC)
│   │   │   ├── __init__.py
│   │   │   └── adaptive_compensation_extractor.py # Adaptive extraction
│   │   │
│   │   ├── patterns/            # Code patterns (369 LOC)
│   │   │   ├── __init__.py
│   │   │   └── self_improving_code.py             # Self-improving pattern
│   │   │
│   │   └── controllers/         # Controllers (187 LOC)
│   │       ├── __init__.py
│   │       └── self_improving_extraction_controller.py
│   │
│   ├── cli_chatbot/             # Conversational interface
│   │   ├── __init__.py
│   │   ├── README.md
│   │   ├── core/                # Core chatbot logic
│   │   │   ├── __init__.py
│   │   │   ├── controller.py
│   │   │   ├── context_injector.py
│   │   │   ├── interfaces.py
│   │   │   └── scripting_engine.py
│   │   └── fallback/            # Traditional CLI fallback
│   │       ├── __init__.py
│   │       └── traditional_cli.py
│   │
│   └── self_improving_code/     # Self-improving system
│       ├── __init__.py
│       ├── README.md
│       ├── core/                # Core self-improvement logic
│       │   ├── __init__.py
│       │   ├── controller.py
│       │   └── interfaces.py
│       ├── llm/                 # LLM integration
│       │   ├── __init__.py
│       │   ├── engineer.py
│       │   └── supervisor.py
│       ├── safety/              # Safety mechanisms
│       │   ├── __init__.py
│       │   └── git_manager.py
│       └── examples/            # Usage examples
│           ├── __init__.py
│           └── edgar_extraction.py
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── README.md
│   │
│   ├── unit/                    # Unit tests
│   │   └── __init__.py
│   │
│   ├── integration/             # Integration tests
│   │   └── __init__.py
│   │
│   ├── results/                 # Test results (gitignored)
│   │   ├── breakthrough_xbrl_test_*.json
│   │   ├── fortune_100_*.json
│   │   └── COMPREHENSIVE_QA_SUMMARY.md
│   │
│   ├── output/                  # Test outputs
│   │   ├── checkpoint_analysis_*.json
│   │   └── quality_test_*.json
│   │
│   ├── scripts/                 # Utility scripts
│   │   ├── quality/
│   │   │   └── enforce_code_standards.py
│   │   └── setup/
│   │       └── install_pre_commit_hooks.py
│   │
│   └── [50+ test files]
│       ├── test_*.py            # Various test modules
│       ├── run_*.py             # Test runners
│       ├── debug_*.py           # Debug utilities
│       └── analyze_*.py         # Analysis scripts
│
├── docs/                        # Documentation
│   ├── README.md                # Documentation hub
│   │
│   ├── guides/                  # User guides
│   │   ├── QUICK_START.md
│   │   ├── CLI_USAGE.md
│   │   ├── CODE_GOVERNANCE.md
│   │   ├── API_KEY_SECURITY.md
│   │   ├── SECURITY.md
│   │   └── WEB_SEARCH_CAPABILITIES.md
│   │
│   ├── architecture/            # Architecture documentation
│   │   ├── PROJECT_STRUCTURE.md
│   │   ├── SELF_IMPROVING_CODE_PATTERN.md
│   │   ├── OPENROUTER_ARCHITECTURE.md
│   │   └── FEASIBILITY_ANALYSIS.md
│   │
│   ├── api/                     # API documentation
│   │   └── OPENROUTER_SERVICE.md
│   │
│   ├── SYSTEM_READY_SUMMARY.md
│   ├── DATA_DICTIONARY.md
│   ├── METHODOLOGY_AND_DATA_SOURCES.md
│   ├── BREAKTHROUGH_XBRL_EXECUTIVE_COMPENSATION.md
│   ├── RESEARCH_BREAKTHROUGH_SUMMARY.md
│   ├── EXECUTIVE_COMPENSATION_DATA_SOURCES.md
│   ├── EXECUTIVE_COMPENSATION_ACTION_PLAN.md
│   └── USER_GUIDE_DATA_INTERPRETATION.md
│
├── data/                        # Data files
│   ├── companies/               # Company lists
│   │   ├── fortune_500_complete.json
│   │   └── fortune_500_sample.json
│   │
│   ├── cache/                   # API cache (gitignored)
│   │   ├── facts_*.json
│   │   └── submissions_*.json
│   │
│   └── checkpoints/             # Analysis checkpoints
│       └── analysis_fortune500_*.json
│
├── output/                      # Generated reports (gitignored)
│   └── [Generated CSV and Excel files]
│
├── logs/                        # Application logs (gitignored)
│   └── edgar_analyzer.log
│
├── results/                     # Analysis results
│   └── top_100_enhanced_results_*.json
│
├── edgar-analyzer-package/      # Deployment package
│   ├── README.md
│   ├── QUICK_START.md
│   ├── pyproject.toml
│   └── src/edgar_analyzer/      # Packaged source
│
├── venv/                        # Virtual environment (gitignored)
│
├── Configuration Files
│   ├── .env.template            # Environment template (tracked)
│   ├── .env.local               # Local config (gitignored)
│   ├── .gitignore               # Git ignore rules
│   ├── pyproject.toml           # Python project config
│   ├── requirements.txt         # Python dependencies
│   ├── Makefile                 # Build automation ⭐
│   └── .pre-commit-config.yaml  # Pre-commit hooks
│
├── Launcher Scripts
│   ├── edgar_cli.sh             # Unix launcher
│   ├── edgar-analyzer.bat       # Windows launcher (batch)
│   └── edgar-analyzer           # Binary executable
│
├── Utility Scripts
│   ├── setup_edgar_cli.py       # Automated setup
│   ├── create_csv_reports.py   # CSV report generation
│   ├── create_report_spreadsheet.py  # Excel generation
│   └── create_deployment_package.py  # Package builder
│
└── Documentation Files
    ├── README.md                # Main project README
    ├── CLAUDE.md                # Claude Code agent guide ⭐
    ├── DEVELOPER.md             # Developer guide ⭐
    ├── CODE.md                  # Coding standards ⭐
    ├── STRUCTURE.md             # This file ⭐
    ├── PROJECT_OVERVIEW.md      # Project overview
    ├── DATA_SOURCES.md          # Data source tracking
    ├── LICENSE                  # MIT License
    └── CHANGELOG.md             # Version history
```

---

## Key Components

### Core Services (src/edgar_analyzer/services/)

#### 1. XBRL Extraction (⭐ Breakthrough)
**File**: `breakthrough_xbrl_service.py`
- **Achievement**: 2x better success rate
- **Method**: Concept-based XBRL extraction
- **Concepts**: `us-gaap:*Compensation*` patterns
- **Features**: Multi-year support, role matching

#### 2. Multi-Source Integration
**File**: `multi_source_enhanced_service.py`
- **Sources**: EDGAR, XBRL, Fortune rankings
- **Tracking**: Data source attribution
- **Validation**: Cross-source verification

#### 3. SEC EDGAR API
**File**: `edgar_api_service.py`
- **Endpoints**: Company facts, submissions, filings
- **Features**: Rate limiting, caching, error handling
- **Requirements**: User agent, rate limiting

#### 4. Data Extraction
**Files**: `data_extraction_service.py`, `enhanced_data_extraction_service.py`
- **Orchestration**: Coordinate extraction workflow
- **Strategies**: Multiple extraction approaches
- **Fallbacks**: Graceful degradation

#### 5. Report Generation
**Files**: `report_service.py`, `enhanced_report_service.py`
- **Formats**: CSV, Excel (XLSX)
- **Features**: Multiple output formats
- **Quality**: Data validation before output

### Data Models (src/edgar_analyzer/models/)

#### Company Model
**File**: `company.py`
- **Fields**: CIK, name, ticker, industry
- **Validation**: Pydantic-based
- **Usage**: Throughout application

#### Intermediate Data
**File**: `intermediate_data.py`
- **Purpose**: Processing state management
- **Pattern**: Immutable structures
- **Usage**: Service layer communication

### Configuration (src/edgar_analyzer/config/)

#### Dependency Injection
**File**: `container.py`
- **Framework**: dependency-injector
- **Pattern**: Container-based service management
- **Usage**: `@inject` decorator

#### Settings Management
**File**: `settings.py`
- **Source**: Environment variables, .env files
- **Framework**: Pydantic settings
- **Validation**: Type-safe configuration

### CLI Interface (src/edgar_analyzer/cli/)

#### Click-based CLI
**File**: `main.py`
- **Framework**: Click
- **Commands**: extract, test, analyze
- **Features**: Command groups, options, help

### Validation (src/edgar_analyzer/validation/)

#### Data Validator
**File**: `data_validator.py`
- **Checks**: Completeness, accuracy, consistency
- **Pattern**: Rule-based validation
- **Output**: Validation reports

#### Sanity Checker
**File**: `sanity_checker.py`
- **Checks**: Range validation, logical consistency
- **Pattern**: Heuristic-based checks

#### Source Verifier
**File**: `source_verifier.py`
- **Purpose**: Data source tracking and verification
- **Pattern**: Source attribution validation

---

## Data Flow

### Analysis Workflow

```
1. User Input (CIK, Year)
        ↓
2. Company Service
   - Retrieve company data
   - Validate CIK
        ↓
3. EDGAR API Service
   - Fetch company facts
   - Cache response
        ↓
4. XBRL Extraction Service ⭐
   - Extract compensation concepts
   - Match executive roles
   - Validate data
        ↓
5. Multi-Source Enhancement
   - Integrate Fortune rankings
   - Cross-reference data
   - Track sources
        ↓
6. Data Validation
   - Quality checks
   - Sanity validation
   - Source verification
        ↓
7. Report Generation
   - Format data
   - Generate CSV/Excel
   - Output results
        ↓
8. Result Storage
   - Save to output/
   - Update checkpoints
   - Cache for reuse
```

### Service Dependencies

```
CLI Layer
    ↓
Controllers
    ↓
Service Orchestrators
    ├─→ XBRL Service
    ├─→ EDGAR API Service
    ├─→ Multi-Source Service
    ├─→ Validation Service
    └─→ Report Service
        ↓
Data Models
    ↓
External APIs
    ├─→ SEC EDGAR
    ├─→ XBRL Data
    └─→ Fortune Rankings
```

---

## File Naming Conventions

### Python Modules
- **Services**: `*_service.py`
- **Models**: `*.py` (singular nouns)
- **Tests**: `test_*.py`
- **Utilities**: `*_utils.py` or descriptive names
- **Scripts**: Descriptive names (`create_*.py`, `run_*.py`)

### Documentation
- **Guides**: `UPPER_CASE.md`
- **READMEs**: `README.md`
- **Architecture**: `PROJECT_*.md`, `*_ARCHITECTURE.md`

### Data Files
- **JSON**: `*.json`
- **Cache**: `facts_*.json`, `submissions_*.json`
- **Checkpoints**: `analysis_*_*.json`

### Configuration
- **Templates**: `*.template`
- **Local**: `*.local` (gitignored)
- **Environment**: `.env*`

---

## Import Patterns

### Absolute Imports
```python
# Services
from edgar_analyzer.services import BreakthroughXBRLService
from edgar_analyzer.services import EdgarAPIService

# Models
from edgar_analyzer.models import Company

# Configuration
from edgar_analyzer.config.container import Container
```

### Relative Imports (within package)
```python
# Within services package
from .interfaces import DataExtractor
from .cache_service import CacheService
```

### Type Imports
```python
from typing import Optional, Dict, Any, List
from pathlib import Path
```

---

## Testing Structure

### Test Organization
```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_services.py
│   ├── test_models.py
│   └── test_validators.py
│
├── integration/             # External API tests
│   ├── test_edgar_api.py
│   ├── test_xbrl_extraction.py
│   └── test_report_generation.py
│
└── results/                 # Test outputs (gitignored)
    └── *_results_*.json
```

### Test Naming
- **Files**: `test_*.py`
- **Classes**: `Test*`
- **Functions**: `test_*`
- **Pattern**: `test_<function>_<scenario>`

---

## Build Artifacts

### Generated Files (gitignored)
- `build/` - Build artifacts
- `dist/` - Distribution packages
- `*.egg-info/` - Package metadata
- `__pycache__/` - Python bytecode
- `.pytest_cache/` - Pytest cache
- `.mypy_cache/` - Mypy cache
- `htmlcov/` - Coverage reports

### Output Directories (gitignored)
- `output/` - Generated reports
- `logs/` - Application logs
- `data/cache/` - API response cache
- `tests/results/` - Test results

### Tracked Outputs
- `results/` - Analysis results (some tracked)
- `data/checkpoints/` - Analysis checkpoints
- `edgar-analyzer-package/` - Deployment package

---

## Configuration Files

### Python Configuration
- **pyproject.toml** - Main Python project configuration
  - Dependencies
  - Build settings
  - Tool configuration (black, isort, mypy, pytest)
  - Project metadata

### Build Tools
- **Makefile** - Build automation and workflows
  - Single-path commands
  - Development workflows
  - Quality checks
  - Testing commands

### Version Control
- **.gitignore** - Git ignore patterns
  - Secrets and API keys
  - Build artifacts
  - Virtual environments
  - Cache and logs
  - Claude MPM sensitive directories

### Environment
- **.env.template** - Environment variable template
- **.env.local** - Local configuration (gitignored)

---

## Documentation Organization

### Primary Docs (Root Level)
- **README.md** - Project overview and quick start
- **CLAUDE.md** - Claude Code agent guide
- **DEVELOPER.md** - Developer technical guide
- **CODE.md** - Coding standards
- **STRUCTURE.md** - This file
- **PROJECT_OVERVIEW.md** - Complete project context

### Technical Docs (docs/)
- **guides/** - User and developer guides
- **architecture/** - System architecture
- **api/** - API reference
- **Research docs** - Breakthrough documentation

### Component Docs
- **src/.../README.md** - Component-specific docs
- **tests/README.md** - Test documentation

---

## Dependency Graph

### External Dependencies
```
Production:
├── click              # CLI framework
├── requests           # HTTP client
├── pandas             # Data manipulation
├── openpyxl           # Excel support
├── beautifulsoup4     # HTML parsing
├── lxml               # XML parsing
├── pydantic           # Data validation
├── dependency-injector # DI framework
├── rich               # Terminal formatting
├── python-dotenv      # Environment variables
└── structlog          # Structured logging

Development:
├── pytest             # Testing framework
├── pytest-cov         # Coverage reporting
├── pytest-mock        # Mocking support
├── black              # Code formatting
├── isort              # Import sorting
├── flake8             # Linting
├── mypy               # Type checking
└── pre-commit         # Git hooks
```

### Internal Dependencies
```
CLI → Controllers → Services → Models → External APIs
```

---

## Key Patterns

### Service Pattern
- Services in `services/` directory
- Interface-based design
- Dependency injection
- Single responsibility

### Repository Pattern
- Data access abstraction
- Caching layer
- Error handling
- Rate limiting

### Strategy Pattern
- Multiple extraction strategies
- Pluggable algorithms
- Fallback mechanisms

### Factory Pattern
- Service creation
- Model instantiation
- Configuration management

---

## Growth Areas

### Current Limitations
- Not all companies have XBRL data
- Proxy HTML parsing is fragile
- Limited historical data coverage
- API rate limiting constraints

### Future Enhancements
- Additional data sources
- Improved HTML parsing
- Real-time data updates
- Enhanced visualization
- Web interface

---

## Quick Navigation

### For New Developers
1. Start with [README.md](README.md)
2. Read [DEVELOPER.md](DEVELOPER.md)
3. Review [CODE.md](CODE.md)
4. Explore `src/edgar_analyzer/services/`

### For AI Agents
1. Read [CLAUDE.md](CLAUDE.md)
2. Check [.claude-mpm/memories/](/.claude-mpm/memories/)
3. Review service layer code
4. Check test examples

### For Understanding Architecture
1. [docs/architecture/](docs/architecture/)
2. Service dependency graph
3. Data flow diagrams
4. This document

---

**Project Structure Version**: 1.0
**Last Updated**: 2025-11-28
**Total Documentation**: 25+ markdown files
**Total Code**: 12,478 lines across 47 files
