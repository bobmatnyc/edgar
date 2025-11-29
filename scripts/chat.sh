#!/usr/bin/env bash
#
# EDGAR Analyzer Chat UI Launcher
#
# This script starts the conversational CLI chatbot interface for EDGAR Analyzer.
# The chatbot provides an intelligent, self-aware interface with dynamic context
# injection, real-time code analysis, and natural language processing.
#
# Usage:
#   ./scripts/chat.sh                    # Start chat UI (default mode with web search)
#   ./scripts/chat.sh --no-web-search    # Start without web search
#   ./scripts/chat.sh --verbose          # Start with verbose output
#   ./scripts/chat.sh --traditional      # Force traditional CLI mode
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║          ${MAGENTA}EDGAR Analyzer - Chat UI${CYAN}                        ║${NC}"
echo -e "${CYAN}║          ${BLUE}Intelligent Conversational Interface${CYAN}              ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Step 1: Activate virtual environment
echo -e "${YELLOW}[1/3] Activating virtual environment...${NC}"
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
elif [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not found!${NC}"
    echo -e "${YELLOW}  Creating new virtual environment...${NC}"
    python3 -m venv "$PROJECT_ROOT/venv"
    source "$PROJECT_ROOT/venv/bin/activate"
    pip install -e ".[dev]"
    echo -e "${GREEN}✓ Virtual environment created and packages installed${NC}"
fi
echo

# Step 2: Load environment variables
echo -e "${YELLOW}[2/3] Loading environment variables...${NC}"
if [ -f "$PROJECT_ROOT/.env.local" ]; then
    # Use simple source method (Python will also load it)
    set -a
    source "$PROJECT_ROOT/.env.local"
    set +a

    echo -e "${GREEN}✓ Environment variables loaded from .env.local${NC}"

    # Verify API key is set
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo -e "${RED}✗ OPENROUTER_API_KEY not found in .env.local${NC}"
        echo -e "${YELLOW}  Chat UI requires an API key to function${NC}"
        echo -e "${YELLOW}  Please add OPENROUTER_API_KEY to .env.local${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ OPENROUTER_API_KEY found (${OPENROUTER_API_KEY:0:15}...)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env.local not found${NC}"
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo -e "${RED}✗ OPENROUTER_API_KEY not set${NC}"
        echo -e "${YELLOW}  Create .env.local with OPENROUTER_API_KEY=your_key_here${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ Using OPENROUTER_API_KEY from environment${NC}"
    fi
fi
echo

# Step 3: Start Chat UI
echo -e "${YELLOW}[3/3] Starting Chat UI...${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo

# Build command with options
CMD="python -m edgar_analyzer.main_cli"

# Parse arguments
VERBOSE=""
WEB_SEARCH="--enable-web-search"
MODE=""

for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE="--verbose"
            ;;
        --no-web-search|--disable-web-search)
            WEB_SEARCH="--disable-web-search"
            ;;
        --traditional)
            MODE="--mode traditional"
            ;;
        --chatbot)
            MODE="--mode chatbot"
            ;;
        --help|-h)
            $CMD --help
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $arg${NC}"
            echo "Usage: $0 [--verbose] [--no-web-search] [--traditional] [--chatbot]"
            exit 1
            ;;
    esac
done

# Display startup info
if [ -n "$VERBOSE" ]; then
    echo -e "${CYAN}Configuration:${NC}"
    echo -e "  Mode: ${MODE:-auto (default)}"
    echo -e "  Web Search: ${WEB_SEARCH/--enable-/enabled}"
    echo -e "  Verbose: enabled"
    echo
fi

# Run the chat UI
$CMD $VERBOSE $WEB_SEARCH $MODE

# Capture exit code
EXIT_CODE=$?

echo
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Report results
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Chat session ended successfully${NC}"
else
    echo -e "${RED}✗ Chat session ended with exit code $EXIT_CODE${NC}"
fi

echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"

exit $EXIT_CODE
