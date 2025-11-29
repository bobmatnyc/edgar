#!/bin/bash
#
# Run all auto-compaction QA tests
#
# Usage: ./RUN_ALL_TESTS.sh
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "AUTO-COMPACTION QA TEST SUITE"
echo "============================================================"
echo ""
echo "Project: $PROJECT_ROOT"
echo "Test Directory: $SCRIPT_DIR"
echo ""

# Activate virtual environment
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo "❌ Virtual environment not found at $PROJECT_ROOT/venv"
    exit 1
fi

echo ""
echo "============================================================"
echo "TEST 1: Original Unit Tests"
echo "============================================================"
python "$PROJECT_ROOT/test_auto_compaction.py"

echo ""
echo "============================================================"
echo "TEST 2: Compaction Metrics"
echo "============================================================"
python "$SCRIPT_DIR/test_compaction_metrics.py"

echo ""
echo "============================================================"
echo "TEST 3: Context Preservation"
echo "============================================================"
python "$SCRIPT_DIR/test_context_preservation.py"

echo ""
echo "============================================================"
echo "TEST 4: Error Handling"
echo "============================================================"
python "$SCRIPT_DIR/test_error_handling.py"

echo ""
echo "============================================================"
echo "TEST 5: Performance"
echo "============================================================"
python "$SCRIPT_DIR/test_performance.py"

echo ""
echo "============================================================"
echo "TEST 6: Manual Integration Test"
echo "============================================================"
python "$SCRIPT_DIR/manual_test_compaction.py"

echo ""
echo "============================================================"
echo "ALL TESTS COMPLETE"
echo "============================================================"
echo ""
echo "✅ Test suite execution finished"
echo ""
echo "Review the full QA report at:"
echo "  $PROJECT_ROOT/QA_REPORT_AUTO_COMPACTION.md"
echo ""
echo "Review the quick summary at:"
echo "  $PROJECT_ROOT/QA_SUMMARY.md"
echo ""
