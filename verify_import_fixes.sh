#!/bin/bash
# Verification script for import error fixes

echo "===== Import Error Fixes Verification ====="
echo ""

echo "1. Testing FilteredParsedExamples import..."
pytest tests/unit/services/test_pattern_filter.py::TestPatternFilterService::test_filter_threshold_07_balanced -v --tb=short 2>&1 | grep -E "PASSED|FAILED"
echo ""

echo "2. Testing GenerationProgress import..."
pytest tests/unit/services/test_code_generator_progress.py::TestGenerationProgress::test_creation_with_valid_status -v --tb=short 2>&1 | grep -E "PASSED|FAILED"
echo ""

echo "3. Testing setup command exports..."
pytest tests/unit/cli/test_setup_command.py::TestSetupTestCommand::test_openrouter_success -v --tb=short 2>&1 | grep -E "PASSED|FAILED"
echo ""

echo "4. Test collection summary..."
pytest tests/ --co -q 2>&1 | grep "collected"
echo ""

echo "===== Verification Complete ====="
