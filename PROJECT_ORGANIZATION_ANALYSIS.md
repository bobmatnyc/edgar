# Project Organization Analysis Report

**Date**: 2025-12-31
**Project**: SEC EDGAR Executive Compensation vs Tax Expense Analysis Tool
**Analysis Type**: Comprehensive File Organization Review (DRY RUN)

---

## Executive Summary

This report analyzes the entire project structure and proposes a comprehensive reorganization plan following the standards defined in `/Users/masa/Projects/edgar/docs/reference/PROJECT_ORGANIZATION.md`.

### Key Findings

- **40 markdown files** in project root should be relocated
- **15 test/coverage files** in root should be moved to `output/`
- **1 executable script** (`edgar-analyzer`) in root should be moved to `scripts/`
- **69MB cache directories** (`.mypy_cache`) can be cleaned
- **No files older than 6 months** - all content is recent
- **No empty files** detected
- **Good separation** already exists in `docs/`, `src/`, `tests/`, `scripts/`

### Impact

- **Low Risk**: Most moves are documentation files with no code dependencies
- **High Value**: Improved discoverability and maintenance
- **Time Estimate**: 30-45 minutes for complete reorganization

---

## Current State Analysis

### Root Directory Clutter (61 files to organize)

#### Documentation Files (40 files)
All UPPERCASE `.md` files represent research, status reports, or reference documents that should be categorized and moved.

#### Test/Coverage Files (15 files)
Coverage reports, test results, and test data files that belong in `output/test-results/`.

#### Executable Scripts (1 file)
- `edgar-analyzer` - CLI entry point (should be in `scripts/`)

#### Protected Files (Correctly in Root - 9 files)
✅ These files MUST stay in root:
- `README.md`
- `CLAUDE.md`
- `Makefile`
- `pyproject.toml`
- `uv.lock`
- `.gitignore`
- `.pre-commit-config.yaml`
- `.mcp.json`
- `requirements.txt`

### Directory Status

#### ✅ Well-Organized Directories
- `src/` - Clean Python package structure
- `tests/` - Good test organization
- `scripts/` - Properly used (32 scripts)
- `docs/research/` - Good categorization with subdirectories
- `docs/user/` - Complete user documentation (23 files)
- `docs/developer/` - Clear developer docs with subdirectories

#### ⚠️ Needs Attention
- `docs/` root has some loose files
- `output/` exists but root has output files
- Cache directories need cleanup
- Missing `docs/user/guides/` and `docs/user/tutorials/` subdirectories

---

## File Categorization & Proposed Destinations

### Category 1: Research & Analysis Documents (→ `docs/research/`)

#### Phase Documentation (→ `docs/research/phases/`)
- `ALPHA_RELEASE_STATUS.md`
- `INITIALIZATION_COMPLETE.md`
- `IMPLEMENTATION_COMPLETE.md`
- `BATCH1_VERIFICATION_COMPLETE.md`

#### Feature Implementation (→ `docs/research/features/`)
- `INTERACTIVE_CHAT_MODE_BUGS.md`
- `INTERACTIVE_CHAT_MODE_TEST_EVIDENCE.md`
- `ONE_SHOT_MODE_README.md`
- `PATTERN_FILTER_DELIVERABLES.md`
- `EXTERNAL_ARTIFACTS_DELIVERABLES.md`
- `EXTERNAL_ARTIFACTS_USER_DOCS_COMPLETE.md`
- `CONFIDENCE_THRESHOLD_DOCUMENTATION_COMPLETE.md`
- `FACTORY_TEST_EXAMPLES.md`

#### Test Reports (→ `docs/research/test-reports/`)
- `COMPREHENSIVE_COVERAGE_AUDIT_DAY3.md`
- `ALPHA_TEST_SUMMARY.txt`
- `SMOKE_TEST_INDEX.md`
- `SMOKE_TEST_SUMMARY.txt`
- `TEST_ARTIFACTS_README.md`
- `test_baseline_user_testing.txt`
- `test_failures_analysis.txt`
- `test_failures_full.txt`
- `USER_TESTING_FILES.txt`

#### Bug Fixes (→ `docs/research/bug-fixes/`)
- `VERIFY_BUG3_README.md`

#### Tickets (→ `docs/research/tickets/`)
- `WORKFLOWS_NEEDING_TICKETS.md`
- `IMPLEMENTATION_1M-325_ITERATIVE_REFINEMENT.md`

#### Migration Documentation (→ `docs/developer/migration/`)
- `MIGRATION_T2_BASE_DATA_SOURCE.md`
- `CHANGELOG_LOGGING_ENV.md`
- `LOGGING_AND_ENV_SETUP.md`

#### POCs & Spikes (→ `docs/research/`)
- `POC_2_PROXY_FILING_IDENTIFICATION.md`

### Category 2: Developer Documentation (→ `docs/developer/`)

#### Architecture & Technical Docs (→ `docs/developer/`)
- `DEVELOPER.md` → `docs/developer/DEVELOPER_GUIDE.md`
- `CODE.md` → `docs/developer/CODE_STANDARDS.md`
- `STRUCTURE.md` → `docs/developer/PROJECT_STRUCTURE.md`

#### Reference Documentation (→ `docs/reference/`)
- `DATA_SOURCES.md`
- `CLI_COMMANDS_REFERENCE.md`
- `QUICK_REFERENCE_DATA_SOURCES.md`

### Category 3: User Documentation (→ `docs/user/`)

#### User Guides (→ `docs/user/guides/`)
- `QUICKSTART_SETUP.md` → `docs/user/guides/quick-start.md`
- `SETUP_QUICK_START.md` → (consolidate with above)
- `SETUP_COMMAND_DEMO.md` → `docs/user/guides/setup-demo.md`
- `SETUP_DEMO.md` → (consolidate with above)
- `TESTING_QUICK_START.md` → `docs/user/guides/testing-guide.md`

#### Platform Documentation (→ `docs/user/`)
- `PROJECT_OVERVIEW.md` → `docs/user/PLATFORM_OVERVIEW.md`
- `README_BINARY.md` → `docs/user/BINARY_DISTRIBUTION.md`

### Category 4: Implementation Status (→ `docs/research/implementation/`)

Note: `docs/implementation/` already exists but is separate from `docs/research/`. Consider consolidating.

- `DOCUMENTATION_STATUS.md`
- `EDGAR_PROJECT_WORKFLOW_VERIFICATION.md`

### Category 5: Feature-Specific (→ `docs/research/features/`)

- `SCRIPTING_ENGINE_FILE_OPERATIONS.md`
- `SCRIPTING_ENGINE_INTEGRATION.md`

### Category 6: Test Results & Coverage (→ `output/test-results/`)

#### Coverage Data
- `coverage.json` (549K)
- `coverage_validator.json` (547K)
- `coverage_snapshot_20251205.json` (549K)
- `coverage_output.txt`
- `coverage_run_output.txt`

#### Test Results
- `test_50_companies_results.json`
- `smoke_test_results.json`
- `INTERACTIVE_CHAT_QA_REPORT.json`

### Category 7: Executable Scripts (→ `scripts/`)

- `edgar-analyzer` → `scripts/edgar_analyzer_cli` (or keep as symlink)
- `edgar-analyzer.bat` → `scripts/edgar_analyzer_cli.bat`

### Category 8: Generated Build Artifacts (→ Archive or Delete)

- `edgar-analyzer-package/` → Consider moving to `output/packages/` or archive
- `edgar-analyzer-package.zip` → Move to `output/packages/`

### Category 9: Cache/Generated Directories (→ Clean/Gitignore)

- `__pycache__/` (8.0K) - Should be in `.gitignore`
- `.mypy_cache/` (69MB) - Should be in `.gitignore`
- `.ruff_cache/` (64K) - Should be in `.gitignore`
- `htmlcov/` (380K) - Should be in `.gitignore` or `output/`
- `output/` (740K) - Keep but organize contents

---

## Consolidation Opportunities

### Duplicate/Similar Files to Merge

1. **Setup Guides** (4 files → 1-2 files)
   - `QUICKSTART_SETUP.md`
   - `SETUP_QUICK_START.md`
   - `SETUP_COMMAND_DEMO.md`
   - `SETUP_DEMO.md`

   **Recommendation**: Consolidate into `docs/user/guides/setup-guide.md` with sections for quick start, demo, and commands.

2. **Data Source Documentation** (2 files → 1 file)
   - `DATA_SOURCES.md`
   - `QUICK_REFERENCE_DATA_SOURCES.md`

   **Recommendation**: Merge into `docs/reference/data-sources.md` with quick reference section.

3. **Coverage Files** (3 identical coverage.json files)
   - `coverage.json`
   - `coverage_validator.json`
   - `coverage_snapshot_20251205.json`

   **Recommendation**: Keep only latest in `output/test-results/`, archive dated snapshots.

---

## Pruning Candidates

### Files to Archive (Not Delete)

**Rationale**: Files are recent (< 3 days old), but may be superseded by reorganization or documentation consolidation.

Archive location: `docs/archive/2025-12-31/`

#### Status/Completion Files
- `IMPLEMENTATION_COMPLETE.md` - If implementation phase is truly complete
- `INITIALIZATION_COMPLETE.md` - If initialization is superseded
- `DOCUMENTATION_STATUS.md` - If status is now tracked elsewhere

#### Duplicate Test Artifacts
- `coverage_validator.json` - Keep latest only
- `coverage_snapshot_20251205.json` - Archive dated snapshot

### Directories to Clean

1. **`.mypy_cache/` (69MB)** - Safe to delete, will regenerate
2. **`.ruff_cache/` (64K)** - Safe to delete, will regenerate
3. **`__pycache__/` in root (8.0K)** - Should not exist in root, delete
4. **`htmlcov/` (380K)** - Move to `output/test-results/htmlcov/`

---

## Reorganization Plan (DRY RUN)

### Phase 1: Prepare Structure (Create Missing Directories)

```bash
# Create missing subdirectories
mkdir -p docs/user/guides
mkdir -p docs/user/tutorials
mkdir -p docs/research/implementation
mkdir -p output/test-results
mkdir -p output/packages
mkdir -p docs/archive/2025-12-31
```

### Phase 2: Move Research Documents

```bash
# Phase documentation
git mv ALPHA_RELEASE_STATUS.md docs/research/phases/
git mv INITIALIZATION_COMPLETE.md docs/research/phases/
git mv IMPLEMENTATION_COMPLETE.md docs/research/phases/
git mv BATCH1_VERIFICATION_COMPLETE.md docs/research/phases/

# Feature implementation
git mv INTERACTIVE_CHAT_MODE_BUGS.md docs/research/features/
git mv INTERACTIVE_CHAT_MODE_TEST_EVIDENCE.md docs/research/features/
git mv ONE_SHOT_MODE_README.md docs/research/features/
git mv PATTERN_FILTER_DELIVERABLES.md docs/research/features/
git mv EXTERNAL_ARTIFACTS_DELIVERABLES.md docs/research/features/
git mv EXTERNAL_ARTIFACTS_USER_DOCS_COMPLETE.md docs/research/features/
git mv CONFIDENCE_THRESHOLD_DOCUMENTATION_COMPLETE.md docs/research/features/
git mv FACTORY_TEST_EXAMPLES.md docs/research/features/
git mv SCRIPTING_ENGINE_FILE_OPERATIONS.md docs/research/features/
git mv SCRIPTING_ENGINE_INTEGRATION.md docs/research/features/

# Test reports
git mv COMPREHENSIVE_COVERAGE_AUDIT_DAY3.md docs/research/test-reports/
git mv ALPHA_TEST_SUMMARY.txt docs/research/test-reports/
git mv SMOKE_TEST_INDEX.md docs/research/test-reports/
git mv SMOKE_TEST_SUMMARY.txt docs/research/test-reports/
git mv TEST_ARTIFACTS_README.md docs/research/test-reports/
git mv test_baseline_user_testing.txt docs/research/test-reports/
git mv test_failures_analysis.txt docs/research/test-reports/
git mv test_failures_full.txt docs/research/test-reports/
git mv USER_TESTING_FILES.txt docs/research/test-reports/

# Bug fixes
git mv VERIFY_BUG3_README.md docs/research/bug-fixes/

# Tickets
git mv WORKFLOWS_NEEDING_TICKETS.md docs/research/tickets/
git mv IMPLEMENTATION_1M-325_ITERATIVE_REFINEMENT.md docs/research/tickets/

# POCs
git mv POC_2_PROXY_FILING_IDENTIFICATION.md docs/research/
```

### Phase 3: Move Developer Documentation

```bash
# Developer docs
git mv DEVELOPER.md docs/developer/DEVELOPER_GUIDE.md
git mv CODE.md docs/developer/CODE_STANDARDS.md
git mv STRUCTURE.md docs/developer/PROJECT_STRUCTURE.md

# Migration docs
git mv MIGRATION_T2_BASE_DATA_SOURCE.md docs/developer/migration/
git mv CHANGELOG_LOGGING_ENV.md docs/developer/migration/
git mv LOGGING_AND_ENV_SETUP.md docs/developer/migration/

# Reference docs
git mv DATA_SOURCES.md docs/reference/
git mv CLI_COMMANDS_REFERENCE.md docs/reference/
git mv QUICK_REFERENCE_DATA_SOURCES.md docs/reference/
```

### Phase 4: Move User Documentation

```bash
# User guides
git mv QUICKSTART_SETUP.md docs/user/guides/quick-start.md
git mv SETUP_COMMAND_DEMO.md docs/user/guides/setup-demo.md
git mv TESTING_QUICK_START.md docs/user/guides/testing-guide.md

# Platform docs
git mv PROJECT_OVERVIEW.md docs/user/PLATFORM_OVERVIEW.md
git mv README_BINARY.md docs/user/BINARY_DISTRIBUTION.md

# Note: SETUP_QUICK_START.md and SETUP_DEMO.md to be consolidated manually before moving
```

### Phase 5: Move Implementation Status

```bash
git mv DOCUMENTATION_STATUS.md docs/research/implementation/
git mv EDGAR_PROJECT_WORKFLOW_VERIFICATION.md docs/research/implementation/
```

### Phase 6: Move Test Results & Coverage

```bash
# Coverage files
git mv coverage.json output/test-results/
git mv coverage_output.txt output/test-results/
git mv coverage_run_output.txt output/test-results/

# Test results
git mv test_50_companies_results.json output/test-results/
git mv smoke_test_results.json output/test-results/
git mv INTERACTIVE_CHAT_QA_REPORT.json output/test-results/

# Archive dated snapshots
git mv coverage_validator.json docs/archive/2025-12-31/
git mv coverage_snapshot_20251205.json docs/archive/2025-12-31/
```

### Phase 7: Move Scripts & Build Artifacts

```bash
# Scripts (if needed - may be better as symlink)
git mv edgar-analyzer.bat scripts/

# Build artifacts
git mv edgar-analyzer-package.zip output/packages/
# Note: edgar-analyzer-package/ directory may need manual review before moving
```

### Phase 8: Clean Cache Directories

```bash
# Safe to delete (will regenerate)
rm -rf .mypy_cache
rm -rf .ruff_cache
rm -rf __pycache__

# Move htmlcov to output
mv htmlcov output/test-results/
```

### Phase 9: Update .gitignore

Ensure these patterns are in `.gitignore`:
```
# Python
__pycache__/
*.py[cod]
.mypy_cache/
.ruff_cache/

# Coverage
htmlcov/
.coverage
coverage.json

# Output
output/
```

---

## File Consolidation Plan

### 1. Setup Documentation Consolidation

**Target**: `docs/user/guides/setup-guide.md`

Merge these files:
- `QUICKSTART_SETUP.md` (focus on quick install)
- `SETUP_QUICK_START.md` (likely duplicate)
- `SETUP_COMMAND_DEMO.md` (demo section)
- `SETUP_DEMO.md` (likely duplicate)

**New Structure**:
```markdown
# Setup Guide

## Quick Start (5 minutes)
[Content from QUICKSTART_SETUP.md]

## Detailed Setup
[Additional setup steps]

## Demo Mode
[Content from SETUP_COMMAND_DEMO.md]

## Troubleshooting
[Common setup issues]
```

### 2. Data Sources Consolidation

**Target**: `docs/reference/data-sources.md`

Merge:
- `DATA_SOURCES.md` (full documentation)
- `QUICK_REFERENCE_DATA_SOURCES.md` (quick reference table)

**New Structure**:
```markdown
# Data Sources Reference

## Quick Reference
[Table from QUICK_REFERENCE_DATA_SOURCES.md]

## Detailed Documentation
[Full content from DATA_SOURCES.md]
```

---

## Post-Reorganization Tasks

### 1. Update CLAUDE.md

Update the project structure reference in CLAUDE.md to reflect new organization.

### 2. Update README.md

Update any references to moved files in the main README.

### 3. Update Internal Documentation Links

Search for references to moved files:
```bash
grep -r "DEVELOPER.md" docs/
grep -r "DATA_SOURCES.md" docs/
grep -r "PROJECT_OVERVIEW.md" docs/
```

Update links to use new paths.

### 4. Test Build & Documentation

```bash
make test
make quality
# Test any documentation build process
```

### 5. Update PROJECT_ORGANIZATION.md

Document any new categories or exceptions discovered during reorganization.

---

## Risk Assessment

### Low Risk Moves (Safe - No Code Dependencies)
- All markdown documentation files
- Test result files (JSON, TXT)
- Coverage reports

### Medium Risk Moves (Check for References)
- `DEVELOPER.md` - May be referenced in documentation
- `DATA_SOURCES.md` - May be referenced in code comments or docs
- `PROJECT_OVERVIEW.md` - May be linked from README

### High Risk Moves (Requires Validation)
- `edgar-analyzer` executable - Entry point, may have deployment dependencies
- `edgar-analyzer-package/` - Build artifact, check CI/CD dependencies

### No Risk (Regenerates Automatically)
- Cache directories (`.mypy_cache`, `.ruff_cache`, `__pycache__`)
- `htmlcov/` directory

---

## Execution Checklist

Before executing reorganization:

- [ ] Create backup: `tar -czf edgar-backup-2025-12-31.tar.gz .`
- [ ] Create all target directories (Phase 1)
- [ ] Verify git status is clean
- [ ] Run tests to establish baseline: `make test`
- [ ] Review each git mv command before execution
- [ ] Execute moves in phases (Phase 2-8)
- [ ] Update documentation links (Post-reorganization tasks)
- [ ] Run tests after reorganization: `make test`
- [ ] Update .gitignore if needed
- [ ] Commit with message: `chore: reorganize project structure per PROJECT_ORGANIZATION.md`
- [ ] Update PROJECT_ORGANIZATION.md with lessons learned

---

## Statistics Summary

### Files to Move
- **Research docs**: 28 files
- **Developer docs**: 9 files
- **User docs**: 7 files
- **Test results**: 9 files
- **Scripts**: 1-2 files
- **Total**: ~54 files

### Consolidation Opportunities
- **Setup guides**: 4 → 1 file
- **Data sources**: 2 → 1 file
- **Coverage files**: 3 → 1 file (+ 2 archived)
- **Total reduction**: ~8 files

### Cleanup Targets
- **Cache directories**: 69MB to reclaim
- **Duplicate files**: ~1.5MB to archive
- **Build artifacts**: Consider archiving

### Expected Outcome
- **Root directory**: 61 files → ~9 files (85% reduction)
- **Improved navigation**: Clear categorization
- **Better maintenance**: Aligned with PROJECT_ORGANIZATION.md standards
- **Git history**: Preserved with git mv

---

## Questions & Decisions Needed

1. **edgar-analyzer executable**: Keep in root as symlink or move to scripts/?
   - Recommendation: Create `bin/edgar-analyzer` symlink to `scripts/edgar_analyzer_cli`

2. **edgar-analyzer-package/**: Archive, move to output, or delete?
   - Recommendation: Move to `output/packages/edgar-analyzer-package/`

3. **Consolidation**: Merge duplicates now or in separate phase?
   - Recommendation: Separate phase after reorganization for better tracking

4. **docs/implementation/** vs **docs/research/implementation/**: Consolidate?
   - Recommendation: Review both, consolidate if overlapping

---

## Appendix: Full File Inventory

### Root Directory Files (Before Reorganization)

**Markdown Files (40)**:
ALPHA_RELEASE_STATUS.md, BATCH1_VERIFICATION_COMPLETE.md, CHANGELOG_LOGGING_ENV.md, CLAUDE.md ✅, CLI_COMMANDS_REFERENCE.md, CODE.md, COMPREHENSIVE_COVERAGE_AUDIT_DAY3.md, CONFIDENCE_THRESHOLD_DOCUMENTATION_COMPLETE.md, DATA_SOURCES.md, DEVELOPER.md, DOCUMENTATION_STATUS.md, EDGAR_PROJECT_WORKFLOW_VERIFICATION.md, EXTERNAL_ARTIFACTS_DELIVERABLES.md, EXTERNAL_ARTIFACTS_USER_DOCS_COMPLETE.md, FACTORY_TEST_EXAMPLES.md, IMPLEMENTATION_1M-325_ITERATIVE_REFINEMENT.md, IMPLEMENTATION_COMPLETE.md, INITIALIZATION_COMPLETE.md, INTERACTIVE_CHAT_MODE_BUGS.md, INTERACTIVE_CHAT_MODE_TEST_EVIDENCE.md, LOGGING_AND_ENV_SETUP.md, MIGRATION_T2_BASE_DATA_SOURCE.md, ONE_SHOT_MODE_README.md, PATTERN_FILTER_DELIVERABLES.md, POC_2_PROXY_FILING_IDENTIFICATION.md, PROJECT_OVERVIEW.md, QUICK_REFERENCE_DATA_SOURCES.md, QUICKSTART_SETUP.md, README.md ✅, README_BINARY.md, SCRIPTING_ENGINE_FILE_OPERATIONS.md, SCRIPTING_ENGINE_INTEGRATION.md, SETUP_COMMAND_DEMO.md, SETUP_DEMO.md, SETUP_QUICK_START.md, SMOKE_TEST_INDEX.md, STRUCTURE.md, TEST_ARTIFACTS_README.md, TESTING_QUICK_START.md, VERIFY_BUG3_README.md, WORKFLOWS_NEEDING_TICKETS.md

**JSON Files (6)**:
coverage.json, coverage_validator.json, coverage_snapshot_20251205.json, INTERACTIVE_CHAT_QA_REPORT.json, test_50_companies_results.json, smoke_test_results.json

**Text Files (6)**:
ALPHA_TEST_SUMMARY.txt, coverage_output.txt, coverage_run_output.txt, SMOKE_TEST_SUMMARY.txt, test_baseline_user_testing.txt, test_failures_analysis.txt, test_failures_full.txt, USER_TESTING_FILES.txt

**Executables (1)**:
edgar-analyzer, edgar-analyzer.bat

**Protected (9)**:
README.md, CLAUDE.md, Makefile, pyproject.toml, uv.lock, .gitignore, .pre-commit-config.yaml, .mcp.json, requirements.txt

---

## Conclusion

This reorganization plan will significantly improve project organization by:

1. **Reducing root clutter** from 61 files to ~9 essential files
2. **Improving discoverability** through logical categorization
3. **Following standards** defined in PROJECT_ORGANIZATION.md
4. **Preserving git history** using git mv commands
5. **Consolidating duplicates** where appropriate
6. **Cleaning up** generated files and caches

The reorganization is low-risk and can be executed in phases. All moves preserve git history and maintain project functionality.

**Recommendation**: Execute this plan in a feature branch, test thoroughly, then merge to main.

