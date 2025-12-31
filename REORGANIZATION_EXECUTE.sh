#!/bin/bash
# Project Organization Execution Script
# Based on: PROJECT_ORGANIZATION_ANALYSIS.md
# Date: 2025-12-31
#
# SAFETY: This script is in DRY RUN mode by default
# To execute: ./REORGANIZATION_EXECUTE.sh --execute
#
# IMPORTANT: Review PROJECT_ORGANIZATION_ANALYSIS.md before running!

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Mode flag
DRY_RUN=true
if [[ "${1:-}" == "--execute" ]]; then
    DRY_RUN=false
fi

# Logging function
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Git mv wrapper
git_mv() {
    local src="$1"
    local dest="$2"

    if [ ! -f "$src" ] && [ ! -d "$src" ]; then
        log_warn "Source not found: $src (skipping)"
        return 0
    fi

    if $DRY_RUN; then
        echo "DRY RUN: git mv $src $dest"
    else
        log_info "Moving: $src -> $dest"
        git mv "$src" "$dest"
    fi
}

# Create directory if it doesn't exist
ensure_dir() {
    local dir="$1"

    if [ ! -d "$dir" ]; then
        if $DRY_RUN; then
            echo "DRY RUN: mkdir -p $dir"
        else
            log_info "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    fi
}

# Main execution
main() {
    log_info "Project Organization Script"
    log_info "Mode: $(if $DRY_RUN; then echo 'DRY RUN'; else echo 'EXECUTE'; fi)"
    echo ""

    if $DRY_RUN; then
        log_warn "This is a DRY RUN. No files will be moved."
        log_warn "Review output, then run with: $0 --execute"
        echo ""
    else
        log_warn "EXECUTING file reorganization!"
        read -p "Have you created a backup? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_error "Backup not confirmed. Exiting."
            exit 1
        fi
    fi

    # Phase 1: Create directory structure
    log_info "=== Phase 1: Creating Directory Structure ==="
    ensure_dir "docs/user/guides"
    ensure_dir "docs/user/tutorials"
    ensure_dir "docs/research/implementation"
    ensure_dir "output/test-results"
    ensure_dir "output/packages"
    ensure_dir "docs/archive/2025-12-31"
    echo ""

    # Phase 2: Move Research Documents
    log_info "=== Phase 2: Moving Research Documents ==="

    # Phase documentation
    git_mv "ALPHA_RELEASE_STATUS.md" "docs/research/phases/"
    git_mv "INITIALIZATION_COMPLETE.md" "docs/research/phases/"
    git_mv "IMPLEMENTATION_COMPLETE.md" "docs/research/phases/"
    git_mv "BATCH1_VERIFICATION_COMPLETE.md" "docs/research/phases/"

    # Feature implementation
    git_mv "INTERACTIVE_CHAT_MODE_BUGS.md" "docs/research/features/"
    git_mv "INTERACTIVE_CHAT_MODE_TEST_EVIDENCE.md" "docs/research/features/"
    git_mv "ONE_SHOT_MODE_README.md" "docs/research/features/"
    git_mv "PATTERN_FILTER_DELIVERABLES.md" "docs/research/features/"
    git_mv "EXTERNAL_ARTIFACTS_DELIVERABLES.md" "docs/research/features/"
    git_mv "EXTERNAL_ARTIFACTS_USER_DOCS_COMPLETE.md" "docs/research/features/"
    git_mv "CONFIDENCE_THRESHOLD_DOCUMENTATION_COMPLETE.md" "docs/research/features/"
    git_mv "FACTORY_TEST_EXAMPLES.md" "docs/research/features/"
    git_mv "SCRIPTING_ENGINE_FILE_OPERATIONS.md" "docs/research/features/"
    git_mv "SCRIPTING_ENGINE_INTEGRATION.md" "docs/research/features/"

    # Test reports
    git_mv "COMPREHENSIVE_COVERAGE_AUDIT_DAY3.md" "docs/research/test-reports/"
    git_mv "ALPHA_TEST_SUMMARY.txt" "docs/research/test-reports/"
    git_mv "SMOKE_TEST_INDEX.md" "docs/research/test-reports/"
    git_mv "SMOKE_TEST_SUMMARY.txt" "docs/research/test-reports/"
    git_mv "TEST_ARTIFACTS_README.md" "docs/research/test-reports/"
    git_mv "test_baseline_user_testing.txt" "docs/research/test-reports/"
    git_mv "test_failures_analysis.txt" "docs/research/test-reports/"
    git_mv "test_failures_full.txt" "docs/research/test-reports/"
    git_mv "USER_TESTING_FILES.txt" "docs/research/test-reports/"

    # Bug fixes
    git_mv "VERIFY_BUG3_README.md" "docs/research/bug-fixes/"

    # Tickets
    git_mv "WORKFLOWS_NEEDING_TICKETS.md" "docs/research/tickets/"
    git_mv "IMPLEMENTATION_1M-325_ITERATIVE_REFINEMENT.md" "docs/research/tickets/"

    # POCs
    git_mv "POC_2_PROXY_FILING_IDENTIFICATION.md" "docs/research/"
    echo ""

    # Phase 3: Move Developer Documentation
    log_info "=== Phase 3: Moving Developer Documentation ==="

    git_mv "DEVELOPER.md" "docs/developer/DEVELOPER_GUIDE.md"
    git_mv "CODE.md" "docs/developer/CODE_STANDARDS.md"
    git_mv "STRUCTURE.md" "docs/developer/PROJECT_STRUCTURE.md"

    # Migration docs
    git_mv "MIGRATION_T2_BASE_DATA_SOURCE.md" "docs/developer/migration/"
    git_mv "CHANGELOG_LOGGING_ENV.md" "docs/developer/migration/"
    git_mv "LOGGING_AND_ENV_SETUP.md" "docs/developer/migration/"

    # Reference docs
    git_mv "DATA_SOURCES.md" "docs/reference/"
    git_mv "CLI_COMMANDS_REFERENCE.md" "docs/reference/"
    git_mv "QUICK_REFERENCE_DATA_SOURCES.md" "docs/reference/"
    echo ""

    # Phase 4: Move User Documentation
    log_info "=== Phase 4: Moving User Documentation ==="

    git_mv "QUICKSTART_SETUP.md" "docs/user/guides/quick-start.md"
    git_mv "SETUP_COMMAND_DEMO.md" "docs/user/guides/setup-demo.md"
    git_mv "TESTING_QUICK_START.md" "docs/user/guides/testing-guide.md"

    git_mv "PROJECT_OVERVIEW.md" "docs/user/PLATFORM_OVERVIEW.md"
    git_mv "README_BINARY.md" "docs/user/BINARY_DISTRIBUTION.md"

    log_warn "Manual consolidation needed for: SETUP_QUICK_START.md, SETUP_DEMO.md"
    echo ""

    # Phase 5: Move Implementation Status
    log_info "=== Phase 5: Moving Implementation Status ==="

    git_mv "DOCUMENTATION_STATUS.md" "docs/research/implementation/"
    git_mv "EDGAR_PROJECT_WORKFLOW_VERIFICATION.md" "docs/research/implementation/"
    echo ""

    # Phase 6: Move Test Results & Coverage
    log_info "=== Phase 6: Moving Test Results & Coverage ==="

    git_mv "coverage.json" "output/test-results/"
    git_mv "coverage_output.txt" "output/test-results/"
    git_mv "coverage_run_output.txt" "output/test-results/"

    git_mv "test_50_companies_results.json" "output/test-results/"
    git_mv "smoke_test_results.json" "output/test-results/"
    git_mv "INTERACTIVE_CHAT_QA_REPORT.json" "output/test-results/"

    git_mv "coverage_validator.json" "docs/archive/2025-12-31/"
    git_mv "coverage_snapshot_20251205.json" "docs/archive/2025-12-31/"
    echo ""

    # Phase 7: Move Scripts & Build Artifacts
    log_info "=== Phase 7: Moving Scripts & Build Artifacts ==="

    git_mv "edgar-analyzer.bat" "scripts/"

    if [ -f "edgar-analyzer-package.zip" ]; then
        git_mv "edgar-analyzer-package.zip" "output/packages/"
    fi

    log_warn "Review edgar-analyzer executable before moving (may need symlink)"
    log_warn "Review edgar-analyzer-package/ directory before moving"
    echo ""

    # Phase 8: Clean Cache Directories
    log_info "=== Phase 8: Cleaning Cache Directories ==="

    if $DRY_RUN; then
        echo "DRY RUN: rm -rf .mypy_cache .ruff_cache __pycache__"
        echo "DRY RUN: mv htmlcov output/test-results/"
    else
        log_info "Removing cache directories..."
        rm -rf .mypy_cache .ruff_cache __pycache__

        if [ -d "htmlcov" ]; then
            log_info "Moving htmlcov to output/test-results/"
            mv htmlcov output/test-results/
        fi
    fi
    echo ""

    # Summary
    log_info "=== Reorganization Complete ==="
    if $DRY_RUN; then
        log_warn "This was a DRY RUN. Review the proposed changes above."
        log_warn "To execute: $0 --execute"
    else
        log_info "Files have been reorganized successfully!"
        log_info "Next steps:"
        echo "  1. Review changes: git status"
        echo "  2. Update documentation links"
        echo "  3. Run tests: make test"
        echo "  4. Consolidate duplicate files manually"
        echo "  5. Update .gitignore if needed"
        echo "  6. Commit: git commit -m 'chore: reorganize project per PROJECT_ORGANIZATION.md'"
    fi
}

# Run main
main
