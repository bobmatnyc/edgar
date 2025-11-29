#!/usr/bin/env bash
#
# Weather Data Extractor Test Script
#
# This script activates the virtual environment, loads environment variables,
# and runs the weather extractor tests.
#
# Usage:
#   ./scripts/test_weather.sh              # Run all weather tests
#   ./scripts/test_weather.sh --template   # Run only template validation tests
#   ./scripts/test_weather.sh --generation # Run only code generation tests
#   ./scripts/test_weather.sh --generate   # Generate weather extractor (no tests)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Weather Data Extractor Test Runner${NC}"
echo -e "${BLUE}======================================${NC}"
echo

# Step 1: Activate virtual environment
echo -e "${YELLOW}[1/4] Activating virtual environment...${NC}"
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
elif [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not found!${NC}"
    echo -e "${YELLOW}  Run: python3 -m venv venv && source venv/bin/activate && pip install -e '.[dev]'${NC}"
    exit 1
fi
echo

# Step 2: Load environment variables
echo -e "${YELLOW}[2/4] Loading environment variables...${NC}"
if [ -f "$PROJECT_ROOT/.env.local" ]; then
    # Export variables, ignoring comments and empty lines
    set -a
    source <(grep -v '^#' "$PROJECT_ROOT/.env.local" | grep -v '^$' | sed 's/\r$//')
    set +a
    echo -e "${GREEN}✓ Environment variables loaded from .env.local${NC}"

    # Verify API key is set
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo -e "${YELLOW}⚠ OPENROUTER_API_KEY not found in .env.local${NC}"
        echo -e "${YELLOW}  Code generation tests will be skipped${NC}"
    else
        echo -e "${GREEN}✓ OPENROUTER_API_KEY found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env.local not found${NC}"
    echo -e "${YELLOW}  Using environment variables only${NC}"
fi
echo

# Step 3: Determine which tests to run
echo -e "${YELLOW}[3/4] Preparing test execution...${NC}"

TEMPLATE_TESTS="$PROJECT_ROOT/tests/integration/test_weather_project_template.py"
GENERATION_TESTS="$PROJECT_ROOT/tests/integration/test_weather_api_generation.py"
GENERATE_SCRIPT="$PROJECT_ROOT/scripts/generate_weather_extractor.py"

case "${1:-all}" in
    --template)
        echo -e "${BLUE}Running template validation tests only${NC}"
        TEST_TARGET="$TEMPLATE_TESTS"
        ;;
    --generation)
        echo -e "${BLUE}Running code generation tests only${NC}"
        TEST_TARGET="$GENERATION_TESTS"
        ;;
    --generate)
        echo -e "${BLUE}Generating weather extractor (no tests)${NC}"
        TEST_TARGET=""
        RUN_GENERATOR=true
        ;;
    all|--all)
        echo -e "${BLUE}Running all weather tests${NC}"
        TEST_TARGET="$TEMPLATE_TESTS $GENERATION_TESTS"
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo "Usage: $0 [--template|--generation|--generate|--all]"
        exit 1
        ;;
esac
echo

# Step 4: Run tests or generator
echo -e "${YELLOW}[4/4] Executing...${NC}"
echo

if [ "$RUN_GENERATOR" = true ]; then
    # Run weather extractor generator
    python "$GENERATE_SCRIPT"
    EXIT_CODE=$?
else
    # Run pytest with verbose output
    pytest $TEST_TARGET \
        -v \
        --tb=short \
        --no-cov \
        -W ignore::DeprecationWarning \
        --color=yes
    EXIT_CODE=$?
fi

echo
echo -e "${BLUE}======================================${NC}"

# Report results
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed successfully!${NC}"
else
    echo -e "${RED}✗ Tests failed with exit code $EXIT_CODE${NC}"
fi

echo -e "${BLUE}======================================${NC}"

exit $EXIT_CODE
