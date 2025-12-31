#!/bin/bash
# P0 Bug Fixes Verification Script
# Tests both critical bugs are fixed

set -e  # Exit on error

echo "========================================"
echo "P0 Bug Fixes Verification"
echo "========================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Cleanup previous test projects
echo "🧹 Cleaning up previous test projects..."
rm -rf projects/verify_*
echo ""

# ============================================
# BUG #1: Template System Verification
# ============================================
echo "========================================"
echo "BUG #1: Template System"
echo "========================================"
echo ""

echo "Test 1.1: Weather template..."
python -m edgar_analyzer project create verify_weather --template weather > /dev/null 2>&1
if grep -q "openweathermap_current" projects/verify_weather/project.yaml; then
    echo "✅ Weather template loaded correctly"
else
    echo "❌ FAILED: Weather template not loaded"
    exit 1
fi
echo ""

echo "Test 1.2: News scraper template..."
python -m edgar_analyzer project create verify_news --template news_scraper > /dev/null 2>&1
if grep -q "jina_reader" projects/verify_news/project.yaml; then
    echo "✅ News scraper template loaded correctly"
else
    echo "❌ FAILED: News scraper template not loaded"
    exit 1
fi
echo ""

echo "Test 1.3: Minimal template..."
python -m edgar_analyzer project create verify_minimal --template minimal > /dev/null 2>&1
if grep -q "Minimal project template" projects/verify_minimal/project.yaml; then
    echo "✅ Minimal template loaded correctly"
else
    echo "❌ FAILED: Minimal template not loaded"
    exit 1
fi
echo ""

echo "Test 1.4: Invalid template error handling..."
if python -m edgar_analyzer project create verify_invalid --template nonexistent 2>&1 | grep -q "not one of"; then
    echo "✅ Invalid template error handled correctly"
else
    echo "❌ FAILED: Invalid template error not handled"
    exit 1
fi
echo ""

# ============================================
# BUG #2: Type Conversion Verification
# ============================================
echo "========================================"
echo "BUG #2: Type Conversion in analyze-project"
echo "========================================"
echo ""

echo "Test 2.1: analyze-project with weather_test..."
if python -m edgar_analyzer analyze-project projects/weather_test/ 2>&1 | grep -q "Analysis complete"; then
    echo "✅ analyze-project completed successfully"
else
    echo "❌ FAILED: analyze-project failed"
    exit 1
fi
echo ""

echo "Test 2.2: Exit code verification..."
python -m edgar_analyzer analyze-project projects/weather_test/ > /dev/null 2>&1
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Exit code is 0 (success)"
else
    echo "❌ FAILED: Exit code is $EXIT_CODE (expected 0)"
    exit 1
fi
echo ""

echo "Test 2.3: analysis_results.json created..."
if [ -f "projects/weather_test/analysis_results.json" ]; then
    echo "✅ analysis_results.json exists"
else
    echo "❌ FAILED: analysis_results.json not created"
    exit 1
fi
echo ""

echo "Test 2.4: Correct schema field names..."
if grep -q "input_schema" projects/weather_test/analysis_results.json && grep -q "output_schema" projects/weather_test/analysis_results.json; then
    echo "✅ Schema fields correctly named (input_schema, output_schema)"
else
    echo "❌ FAILED: Incorrect schema field names"
    exit 1
fi
echo ""

# ============================================
# Cleanup
# ============================================
echo "========================================"
echo "Cleanup"
echo "========================================"
echo ""

echo "🧹 Removing test projects..."
rm -rf projects/verify_*
echo ""

# ============================================
# Summary
# ============================================
echo "========================================"
echo "✅ ALL TESTS PASSED!"
echo "========================================"
echo ""
echo "Both P0 bugs are fixed:"
echo "  ✅ Bug #1: Template system fully implemented"
echo "  ✅ Bug #2: Type conversion in analyze-project fixed"
echo ""
echo "Platform workflow is unblocked!"
echo ""
