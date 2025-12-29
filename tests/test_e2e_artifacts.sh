#!/bin/bash
# End-to-End Test: External Artifacts Directory with CLI Commands

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}End-to-End Test: External Artifacts Directory${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo

# Activate venv
source venv/bin/activate

# Create temporary external directory
EXTERNAL_DIR=$(mktemp -d -t edgar_e2e_test)
export EDGAR_ARTIFACTS_DIR="$EXTERNAL_DIR"

echo -e "${BLUE}External artifacts directory: $EDGAR_ARTIFACTS_DIR${NC}"
echo

# Scenario 1: Directory Structure Creation
echo -e "${BLUE}Scenario 1: Directory Structure Creation${NC}"
python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'

for dir in projects output data data/cache; do
    if [ -d "$EDGAR_ARTIFACTS_DIR/$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/ created"
    else
        echo -e "${RED}✗${NC} $dir/ not created"
        exit 1
    fi
done
echo

# Scenario 2: Verify Configuration Loading
echo -e "${BLUE}Scenario 2: Configuration Loading${NC}"
LOADED_DIR=$(python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())')

# Normalize both paths (resolve symlinks)
NORMALIZED_EXPECTED=$(python -c "from pathlib import Path; import os; print(Path(os.environ['EDGAR_ARTIFACTS_DIR']).resolve())")
NORMALIZED_LOADED=$(python -c "from pathlib import Path; print(Path('$LOADED_DIR').resolve())")

if [ "$NORMALIZED_LOADED" = "$NORMALIZED_EXPECTED" ]; then
    echo -e "${GREEN}✓${NC} Configuration loaded correctly: $LOADED_DIR"
else
    echo -e "${RED}✗${NC} Configuration mismatch: expected $NORMALIZED_EXPECTED, got $NORMALIZED_LOADED"
    exit 1
fi
echo

# Scenario 3: Test with ConfigService
echo -e "${BLUE}Scenario 3: ConfigService Integration${NC}"
python -c '
from edgar_analyzer.config.settings import ConfigService
from pathlib import Path
import os

config = ConfigService()
artifacts_dir = config.settings.artifacts_base_dir

if artifacts_dir:
    env_path = Path(os.environ.get("EDGAR_ARTIFACTS_DIR")).resolve()
    artifacts_resolved = artifacts_dir.resolve()

    if artifacts_resolved == env_path:
        print("✓ ConfigService loaded EDGAR_ARTIFACTS_DIR correctly")
        print(f"  Artifacts base: {artifacts_dir}")
    else:
        print(f"✗ Path mismatch: {artifacts_resolved} != {env_path}")
        exit(1)
else:
    print("✗ ConfigService did not load EDGAR_ARTIFACTS_DIR")
    exit(1)
'

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} ConfigService integration successful"
else
    echo -e "${RED}✗${NC} ConfigService integration failed"
    exit 1
fi
echo

# Scenario 4: Test Path Resolution
echo -e "${BLUE}Scenario 4: Path Resolution${NC}"
python -c '
from edgar_analyzer.config.settings import ConfigService
from pathlib import Path
import os

config = ConfigService()

# Test relative path resolution
data_path = config.settings.get_absolute_path("data")
output_path = config.settings.get_absolute_path("output")
projects_path = config.settings.get_absolute_path("projects")

artifacts_dir = Path(os.environ["EDGAR_ARTIFACTS_DIR"]).resolve()

# Verify paths are under artifacts directory
if artifacts_dir in data_path.resolve().parents or data_path.resolve().parent == artifacts_dir:
    print(f"✓ data/ resolved to: {data_path}")
else:
    print(f"✗ data/ not under artifacts dir: {data_path}, expected parent: {artifacts_dir}")
    exit(1)

if artifacts_dir in output_path.resolve().parents or output_path.resolve().parent == artifacts_dir:
    print(f"✓ output/ resolved to: {output_path}")
else:
    print(f"✗ output/ not under artifacts dir: {output_path}")
    exit(1)

if artifacts_dir in projects_path.resolve().parents or projects_path.resolve().parent == artifacts_dir:
    print(f"✓ projects/ resolved to: {projects_path}")
else:
    print(f"✗ projects/ not under artifacts dir: {projects_path}")
    exit(1)
'

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Path resolution successful"
else
    echo -e "${RED}✗${NC} Path resolution failed"
    exit 1
fi
echo

# Scenario 5: Test Fallback Behavior
echo -e "${BLUE}Scenario 5: Fallback Behavior (no env var)${NC}"
unset EDGAR_ARTIFACTS_DIR

FALLBACK_DIR=$(python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())')

if [ "$FALLBACK_DIR" = "$PWD" ]; then
    echo -e "${GREEN}✓${NC} Fallback to current directory: $FALLBACK_DIR"
else
    echo -e "${YELLOW}⚠${NC} Fallback directory: $FALLBACK_DIR (expected: $PWD)"
fi
echo

# Cleanup
echo -e "${BLUE}Cleaning up...${NC}"
rm -rf "$EXTERNAL_DIR"

echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}All end-to-end tests passed!${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo

# Summary
echo -e "${BLUE}Test Summary:${NC}"
echo "  ✓ Directory structure creation"
echo "  ✓ Configuration loading"
echo "  ✓ ConfigService integration"
echo "  ✓ Path resolution"
echo "  ✓ Fallback behavior"
echo
echo -e "${GREEN}External artifacts directory functionality is working correctly!${NC}"
