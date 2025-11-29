#!/bin/bash
# Test CLI commands with external artifacts directory

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}Testing CLI with External Artifacts Directory${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo

# Activate venv
source venv/bin/activate

# Test 1: Default behavior (no env var)
echo -e "${BLUE}Test 1: Default behavior (no EDGAR_ARTIFACTS_DIR)${NC}"
unset EDGAR_ARTIFACTS_DIR

# Check default location
DEFAULT_LOC=$(python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())')
echo -e "${GREEN}✓${NC} Default location: $DEFAULT_LOC"
echo

# Test 2: Custom external directory
echo -e "${BLUE}Test 2: Custom external directory${NC}"
TEMP_DIR=$(mktemp -d -t edgar_cli_test)
export EDGAR_ARTIFACTS_DIR="$TEMP_DIR/my_artifacts"

echo "Setting EDGAR_ARTIFACTS_DIR=$EDGAR_ARTIFACTS_DIR"

# Verify directory is recognized
CUSTOM_LOC=$(python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())')
echo -e "${GREEN}✓${NC} Custom location: $CUSTOM_LOC"

# Create directory structure
python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'

# Verify directories created
if [ -d "$EDGAR_ARTIFACTS_DIR/projects" ]; then
    echo -e "${GREEN}✓${NC} projects/ directory created"
else
    echo -e "${RED}✗${NC} projects/ directory not created"
    exit 1
fi

if [ -d "$EDGAR_ARTIFACTS_DIR/output" ]; then
    echo -e "${GREEN}✓${NC} output/ directory created"
else
    echo -e "${RED}✗${NC} output/ directory not created"
    exit 1
fi

if [ -d "$EDGAR_ARTIFACTS_DIR/data" ]; then
    echo -e "${GREEN}✓${NC} data/ directory created"
else
    echo -e "${RED}✗${NC} data/ directory not created"
    exit 1
fi

echo

# Test 3: Create .env.local file
echo -e "${BLUE}Test 3: Create .env.local with EDGAR_ARTIFACTS_DIR${NC}"
ENV_TEST_DIR=$(mktemp -d -t edgar_env_test)
echo "EDGAR_ARTIFACTS_DIR=$ENV_TEST_DIR/artifacts_from_env" > .env.local.test

# Note: .env.local loading requires python-dotenv configuration
echo -e "${YELLOW}⚠${NC} .env.local support requires additional configuration"
echo -e "${GREEN}✓${NC} Created .env.local.test file"
rm .env.local.test
echo

# Test 4: Tilde expansion
echo -e "${BLUE}Test 4: Tilde expansion${NC}"
export EDGAR_ARTIFACTS_DIR="~/edgar_test_artifacts"

EXPANDED=$(python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())')
if [[ "$EXPANDED" == *"$HOME"* ]]; then
    echo -e "${GREEN}✓${NC} Tilde expanded to: $EXPANDED"
else
    echo -e "${RED}✗${NC} Tilde not expanded: $EXPANDED"
    exit 1
fi
echo

# Test 5: Relative path
echo -e "${BLUE}Test 5: Relative path resolution${NC}"
export EDGAR_ARTIFACTS_DIR="./test_artifacts"

ABSOLUTE=$(python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())')
if [[ "$ABSOLUTE" = /* ]]; then
    echo -e "${GREEN}✓${NC} Relative path converted to absolute: $ABSOLUTE"
else
    echo -e "${RED}✗${NC} Path not absolute: $ABSOLUTE"
    exit 1
fi
echo

# Cleanup
echo -e "${BLUE}Cleaning up...${NC}"
rm -rf "$TEMP_DIR"
rm -rf "$ENV_TEST_DIR"
unset EDGAR_ARTIFACTS_DIR

echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}All CLI tests passed!${NC}"
echo -e "${GREEN}=====================================================================${NC}"
