# Agent Memory: agentic-coder-optimizer

## Project Context

**Project**: EDGAR Analyzer - SEC filing data extraction tool
**Language**: Python 3.11+
**Type**: CLI tool for executive compensation analysis
**Architecture**: Service-oriented with dependency injection

## EDGAR Data Extraction Patterns

### XBRL Extraction Breakthrough (KEY ACHIEVEMENT)
- **Technique**: Concept-based XBRL extraction vs HTML parsing
- **Success Rate**: 2x improvement over previous methods
- **Key File**: `src/edgar_analyzer/services/breakthrough_xbrl_service.py`
- **Concepts**: `us-gaap:*Compensation*` patterns with role-based matching
- **Pattern**: Extract from XBRL facts API, match by concept names, validate roles

### Multi-Source Data Integration
- **Pattern**: Combine EDGAR API + XBRL + Fortune rankings for completeness
- **Key File**: `src/edgar_analyzer/services/multi_source_enhanced_service.py`
- **Best Practice**: Always track data source in results (data_source field)
- **Validation**: Cross-reference multiple sources for accuracy

### SEC EDGAR API Usage
- **Rate Limiting**: Required - SEC enforces rate limits
- **User Agent**: Must set custom user agent (name/email)
- **Caching**: Essential - cache in `data/cache/` directory
- **Endpoints**: Company facts, submissions, filings search
- **Key File**: `src/edgar_analyzer/services/edgar_api_service.py`

## Project Architecture Patterns

### Dependency Injection
- **Framework**: dependency-injector
- **Pattern**: Container-based service management
- **Key File**: `src/edgar_analyzer/config/container.py`
- **Usage**: `@inject` decorator with `Provide[Container.service]`

### Service Layer Organization
- **Pattern**: Service-oriented architecture
- **Location**: `src/edgar_analyzer/services/`
- **Key Services**:
  - `breakthrough_xbrl_service.py` - XBRL extraction (primary)
  - `multi_source_enhanced_service.py` - Multi-source integration
  - `edgar_api_service.py` - SEC API client
  - `report_service.py` - Report generation

### Data Validation
- **Location**: `src/edgar_analyzer/validation/`
- **Components**:
  - `data_validator.py` - Data quality checks
  - `sanity_checker.py` - Logical validation
  - `source_verifier.py` - Source tracking
- **Pattern**: Validate after extraction, before storage

## Code Quality Standards

### Testing Strategy
- **Framework**: pytest
- **Coverage Target**: 80% minimum, 90%+ for core services
- **Organization**:
  - `tests/unit/` - Fast, isolated tests
  - `tests/integration/` - External API tests
  - `tests/results/` - Test outputs
- **Pattern**: Fixtures in conftest.py, parametrize for variations

### Code Formatting
- **Tools**: black (formatter), isort (imports), flake8 (linter), mypy (types)
- **Line Length**: 88 characters (black default)
- **Commands**: `make format` (auto-fix), `make quality` (all checks)
- **Pre-commit**: Hooks installed for automatic checks

### Type Hints
- **Required**: All functions must have type hints
- **Style**: Use `typing` module (Optional, Dict, List, Any, etc.)
- **Validation**: mypy enforces type checking
- **Pattern**: Function args and return types always annotated

### Documentation
- **Docstrings**: Google-style required for all public APIs
- **Components**: Args, Returns, Raises, Example sections
- **Module Docs**: Each module has overview docstring
- **Updates**: Documentation updated with code changes

## Build and Deployment

### Makefile Commands (Single-Path Workflows)
- **ONE command to test**: `make test`
- **ONE command to check quality**: `make quality`
- **ONE command to format**: `make format`
- **ONE command to build**: `make build`
- **ONE command to extract data**: `python -m edgar_analyzer extract --cik <CIK> --year <YEAR>`
- **ONE command to generate reports**: `python create_csv_reports.py`

### Deployment Package
- **Script**: `create_deployment_package.py`
- **Output**: `edgar-analyzer-package.zip`
- **Contents**: Standalone Python package with all dependencies
- **Binary**: `edgar-analyzer` executable included

### Environment Configuration
- **Template**: `.env.template` (tracked in git)
- **Local**: `.env.local` (gitignored, contains secrets)
- **Required**: `OPENROUTER_API_KEY`, `SEC_EDGAR_USER_AGENT`
- **Pattern**: Copy template, fill in secrets locally

## Performance Optimization

### Caching Strategy
- **Location**: `data/cache/` directory (gitignored)
- **Service**: `CacheService` in `src/edgar_analyzer/services/cache_service.py`
- **Pattern**: Cache expensive API calls, TTL-based invalidation
- **Files**: `facts_*.json`, `submissions_*.json`

### Batch Processing
- **Service**: `ParallelProcessingService`
- **Pattern**: ThreadPoolExecutor for concurrent requests
- **Limit**: Respect SEC rate limits (max 10 req/sec)
- **Usage**: Fortune 100/500 bulk analysis

### Checkpoint System
- **Location**: `data/checkpoints/` directory
- **Purpose**: Resume interrupted analysis runs
- **Pattern**: Save intermediate results, resume from last checkpoint
- **Files**: `analysis_fortune500_*.json`

## Common Issues and Solutions

### API Rate Limiting
- **Problem**: SEC EDGAR rate limits exceeded
- **Solution**: Add delay between requests, use caching
- **Environment**: `EDGAR_RATE_LIMIT_DELAY=0.5`

### Missing XBRL Data
- **Problem**: Not all companies have XBRL compensation data
- **Solution**: Graceful fallback to HTML parsing or mark as unavailable
- **Pattern**: Try XBRL first, fallback to proxy parsing

### Data Validation Failures
- **Problem**: Extracted data fails validation
- **Solution**: Use `run_comprehensive_qa.py` to identify issues
- **Pattern**: Log validation errors, continue processing other companies

### Import Errors
- **Problem**: Module not found errors
- **Solution**: Install in editable mode: `pip install -e ".[dev]"`
- **Reason**: Development dependencies need editable install

## Documentation Structure

### Primary Documentation
- **CLAUDE.md** - Agent-focused quick reference (NEW)
- **README.md** - Project overview and quick start
- **DEVELOPER.md** - Technical architecture and dev guide (NEW)
- **CODE.md** - Coding standards and patterns (NEW)
- **PROJECT_OVERVIEW.md** - Complete project structure

### Technical Docs
- **docs/architecture/** - System architecture documentation
- **docs/guides/** - User and developer guides
- **docs/api/** - API reference documentation
- **DATA_DICTIONARY.md** - Data field definitions

### Research Documentation
- **BREAKTHROUGH_XBRL_EXECUTIVE_COMPENSATION.md** - Major achievement
- **RESEARCH_BREAKTHROUGH_SUMMARY.md** - Research findings
- **METHODOLOGY_AND_DATA_SOURCES.md** - Analysis methodology

## Key Learnings

### What Works Well
- XBRL concept-based extraction (2x better than HTML parsing)
- Multi-source data integration with source tracking
- Dependency injection for testability
- Comprehensive caching for API rate limits
- Structured logging with context

### Areas for Improvement
- Not all companies have XBRL compensation data
- Proxy statement HTML parsing is fragile
- Some data validation rules too strict
- Need better error messages for end users

### Development Workflow
- Always run `make quality` before committing
- Use `make test` to verify changes
- Keep API keys in `.env.local` only
- Update documentation with code changes
- Use dependency injection for testability

## Agent-Specific Notes

### When Analyzing Code
- Focus on `src/edgar_analyzer/services/` for business logic
- Check `breakthrough_xbrl_service.py` for extraction techniques
- Review `tests/` for usage examples and patterns

### When Adding Features
- Follow service-oriented pattern
- Add to appropriate service in `services/`
- Include unit tests in `tests/unit/`
- Update relevant documentation
- Run `make quality` to verify standards

### When Debugging
- Enable DEBUG logging: `export LOG_LEVEL=DEBUG`
- Check cache in `data/cache/` for API responses
- Use debug scripts in `tests/debug_*.py`
- Review test results in `tests/results/`

### When Optimizing
- Profile with caching enabled
- Check batch processing opportunities
- Review rate limiting configuration
- Consider parallel processing for bulk operations

---

**Last Updated**: 2025-11-28
**Memory Version**: 1.0
