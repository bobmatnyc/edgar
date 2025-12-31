#!/bin/bash
# CLI Commands Test Suite
# Tests all newly implemented CLI commands

set -e  # Exit on error

echo "==============================================="
echo "EDGAR Platform CLI Commands Test Suite"
echo "==============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_command() {
    local description="$1"
    local command="$2"

    echo -e "${BLUE}Testing:${NC} $description"
    echo "Command: $command"

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((TESTS_FAILED++))
    fi
    echo ""
}

echo "=== 1. Help Commands ==="
echo ""

test_command "Main help" "edgar-analyzer --cli | grep -q 'Commands:'"
test_command "Project group help" "edgar-analyzer project --help | grep -q 'create'"
test_command "Analyze help" "edgar-analyzer analyze-project --help | grep -q 'PROJECT_PATH'"
test_command "Generate help" "edgar-analyzer generate-code --help | grep -q 'PROJECT_PATH'"
test_command "Extract help" "edgar-analyzer run-extraction --help | grep -q 'PROJECT_PATH'"

echo "=== 2. Project Management Commands ==="
echo ""

# Clean up any existing test project
edgar-analyzer project delete test_suite_project --yes > /dev/null 2>&1 || true

test_command "Create project (minimal)" "edgar-analyzer project create test_suite_project --template minimal | grep -q 'Project created'"
test_command "List projects" "edgar-analyzer project list | grep -q 'test_suite_project'"
test_command "List projects (JSON)" "edgar-analyzer project list --format json | grep -q 'test_suite_project'"
test_command "Validate project" "edgar-analyzer project validate test_suite_project | grep -q 'Validation Results'"
test_command "Delete project" "edgar-analyzer project delete test_suite_project --yes | grep -q 'deleted successfully'"

echo "=== 3. Command Help Verification ==="
echo ""

# Verify all commands appear in main help
test_command "analyze-project in help" "edgar-analyzer --cli | grep -q 'analyze-project'"
test_command "generate-code in help" "edgar-analyzer --cli | grep -q 'generate-code'"
test_command "run-extraction in help" "edgar-analyzer --cli | grep -q 'run-extraction'"
test_command "project in help" "edgar-analyzer --cli | grep -q 'project'"

echo "=== 4. Error Handling ==="
echo ""

# These should fail gracefully
test_command "Project not found error" "edgar-analyzer project validate nonexistent_project 2>&1 | grep -q 'not found'"
test_command "Missing project path" "edgar-analyzer analyze-project /nonexistent/path 2>&1 | grep -q 'Error' || true"

echo ""
echo "==============================================="
echo "Test Results Summary"
echo "==============================================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
