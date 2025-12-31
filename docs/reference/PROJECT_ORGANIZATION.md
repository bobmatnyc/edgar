# Project Organization Standard

**Version**: 1.0
**Last Updated**: 2025-12-31
**Project**: SEC EDGAR Executive Compensation vs Tax Expense Analysis Tool

## Overview

This document defines the organizational standard for the EDGAR project. It establishes:
- Canonical directory structure and file placement rules
- Naming conventions for different file types
- Protected files that must remain in specific locations
- Maintenance procedures for keeping the project organized

All project contributors should follow these standards to maintain consistency and discoverability.

## Directory Structure

```
edgar/
├── README.md                    # Project overview and quick start
├── CLAUDE.md                    # AI assistant instructions
├── Makefile                     # Build and development commands
├── pyproject.toml              # Python project configuration
├── uv.lock                     # Dependency lock file
├── .pre-commit-config.yaml     # Git hooks configuration
├── .mcp.json                   # MCP server configuration
│
├── src/                        # Source code (Python packages)
│   └── edgar_analyzer/         # Main package
│
├── tests/                      # All test files
│   ├── unit/                   # Unit tests (mirrors src/ structure)
│   ├── integration/            # Integration tests
│   └── manual/                 # Manual test scripts and procedures
│
├── scripts/                    # Utility and automation scripts
│   ├── verification/           # Verification and validation scripts
│   └── dev/                    # Development helper scripts
│
├── docs/                       # All documentation
│   ├── reference/              # Reference documentation
│   │   └── PROJECT_ORGANIZATION.md  # This file
│   ├── research/               # Research and analysis documents
│   │   ├── phases/             # Phase-based development docs
│   │   ├── features/           # Feature implementation notes
│   │   ├── bug-fixes/          # Bug fix documentation
│   │   ├── test-reports/       # Test analysis and reports
│   │   └── tickets/            # Ticket/issue documentation
│   ├── developer/              # Developer documentation
│   │   ├── api/                # API documentation
│   │   └── architecture/       # Architecture decisions
│   ├── user/                   # User-facing documentation
│   │   ├── guides/             # How-to guides
│   │   └── tutorials/          # Step-by-step tutorials
│   ├── ops/                    # Operations documentation
│   └── archive/                # Archived/superseded docs
│
├── output/                     # Generated outputs (gitignored)
│   ├── test-results/           # Test execution results
│   ├── reports/                # Generated reports
│   └── data/                   # Downloaded/processed data
│
└── .claude-mpm/                # Claude MPM configuration
    └── skills/                 # Project-specific skills
```

## File Placement Rules

### Research & Analysis Documents

| File Type | Location | Example |
|-----------|----------|---------|
| Phase development docs | `docs/research/phases/` | `phase-1-data-collection.md` |
| Feature implementation notes | `docs/research/features/` | `recipe-model-design.md` |
| Bug fix analysis | `docs/research/bug-fixes/` | `fix-cli-validation-error.md` |
| Test reports | `docs/research/test-reports/` | `unit-test-coverage-2025-12.md` |
| Ticket documentation | `docs/research/tickets/` | `issue-123-analysis.md` |

**Rule**: All exploratory work, design discussions, and implementation research goes in `docs/research/` with appropriate subdirectory.

### Developer Documentation

| File Type | Location | Example |
|-----------|----------|---------|
| API documentation | `docs/developer/api/` | `edgar-analyzer-api.md` |
| Architecture decisions | `docs/developer/architecture/` | `adr-001-recipe-model.md` |
| Development guides | `docs/developer/` | `contributing.md`, `setup.md` |

**Rule**: Technical documentation for developers goes in `docs/developer/`.

### User Documentation

| File Type | Location | Example |
|-----------|----------|---------|
| User guides | `docs/user/guides/` | `analyzing-compensation.md` |
| Tutorials | `docs/user/tutorials/` | `getting-started.md` |
| CLI reference | `docs/user/` | `cli-reference.md` |

**Rule**: End-user facing documentation goes in `docs/user/`.

### Scripts

| File Type | Location | Example |
|-----------|----------|---------|
| Python utility scripts | `scripts/` | `analyze_filings.py` |
| Shell verification scripts | `scripts/verification/` | `verify_data_quality.sh` |
| Development helpers | `scripts/dev/` | `setup_dev_env.sh` |

**Rule**: ALL executable scripts go in `scripts/`. NO scripts in project root.

### Tests

| File Type | Location | Example |
|-----------|----------|---------|
| Unit tests | `tests/unit/` | `test_analyzer.py` |
| Integration tests | `tests/integration/` | `test_edgar_api.py` |
| Manual test procedures | `tests/manual/` | `manual-recipe-test.md` |

**Rule**: ALL tests go in `tests/`. Test structure mirrors `src/` structure.

### Output Files

| File Type | Location | Example |
|-----------|----------|---------|
| Test execution results | `output/test-results/` | `pytest-2025-12-31.xml` |
| Generated reports | `output/reports/` | `compensation-analysis.pdf` |
| Downloaded data | `output/data/` | `edgar-filings-2024.json` |

**Rule**: ALL generated/downloaded files go in `output/`. This directory is gitignored.

## Naming Conventions

### Markdown Documents

- **Format**: `kebab-case.md`
- **Examples**:
  - `recipe-model-design.md`
  - `phase-1-implementation.md`
  - `api-documentation.md`

### Python Scripts

- **Format**: `snake_case.py`
- **Examples**:
  - `analyze_compensation.py`
  - `download_filings.py`
  - `verify_data.py`

### Shell Scripts

- **Format**: `snake_case.sh`
- **Examples**:
  - `verify_installation.sh`
  - `setup_environment.sh`

### Test Files

- **Format**: `test_*.py` (pytest convention)
- **Examples**:
  - `test_analyzer.py`
  - `test_recipe_model.py`

### Configuration Files

- **Format**: Project-specific conventions
- **Examples**:
  - `.yaml` for YAML files
  - `.toml` for TOML files
  - `.json` for JSON files

## Protected Files

The following files MUST remain in the project root and NEVER be moved:

### Essential Configuration
- `README.md` - Project overview
- `CLAUDE.md` - AI assistant instructions
- `pyproject.toml` - Python project config
- `uv.lock` - Dependency lock file
- `Makefile` - Build automation
- `.gitignore` - Git ignore rules
- `.pre-commit-config.yaml` - Pre-commit hooks
- `.mcp.json` - MCP configuration

### License & Legal
- `LICENSE` (if present)
- `CONTRIBUTING.md` (if present)

### Python Package Files
- `setup.py` (if present)
- `setup.cfg` (if present)
- `requirements.txt` (if present)

**Rationale**: These files are expected in the root by tools, package managers, and standard conventions. Moving them breaks builds, deployments, and developer expectations.

## Organization Principles

### 1. Separation of Concerns
- **Source code** (`src/`): Production code only
- **Tests** (`tests/`): All testing code
- **Scripts** (`scripts/`): Automation and utilities
- **Docs** (`docs/`): All documentation
- **Output** (`output/`): Generated artifacts (gitignored)

### 2. Discoverability
- Use descriptive directory names
- Group related files together
- Follow Python/ecosystem conventions
- Document exceptions to standards

### 3. Scalability
- Subdirectories for categories with 5+ files
- Archive old/superseded documentation
- Clean up temporary files regularly

### 4. Convention Adherence
- Follow Python package structure standards
- Respect pytest test discovery patterns
- Use standard configuration file locations

## Maintenance Procedures

### Regular Maintenance

**Monthly Review**:
1. Check for misplaced files in project root
2. Archive superseded documentation to `docs/archive/`
3. Clean up `output/` directory
4. Update this document if patterns change

### When Adding New Files

1. **Determine file purpose**: Is it source code, test, script, or documentation?
2. **Consult placement rules**: Use the tables above to find correct location
3. **Follow naming conventions**: Match the established patterns
4. **Update documentation**: If adding new category, document it here

### Reorganization Process

If major reorganization is needed:

1. **Document the change**: Update this file first
2. **Create backup**: `tar -czf backup_$(date +%Y%m%d).tar.gz .`
3. **Use git mv**: Preserve git history with `git mv old/path new/path`
4. **Update imports**: Fix Python import statements
5. **Update CLAUDE.md**: Reflect structure changes in AI instructions
6. **Test thoroughly**: Ensure nothing breaks

## Exceptions

Exceptions to these rules should be:
- **Documented**: Note the exception and rationale
- **Rare**: Most files should follow standard patterns
- **Justified**: Technical or ecosystem requirements

Current exceptions:
- None documented

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-31 | Initial organization standard |

## References

- Python Package Structure: [Python Packaging Guide](https://packaging.python.org/)
- Pytest Conventions: [Pytest Documentation](https://docs.pytest.org/)
- Project README: `/Users/masa/Projects/edgar/README.md`
- Claude Instructions: `/Users/masa/Projects/edgar/CLAUDE.md`

---

**Questions or Suggestions?**
If you find files that don't fit these categories or need clarification on placement, update this document or raise an issue for discussion.
