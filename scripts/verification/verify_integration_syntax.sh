#!/bin/bash

# Syntax-only verification (doesn't require runtime dependencies)

echo "======================================================================"
echo "Confidence Threshold Integration - Syntax Verification"
echo "======================================================================"
echo ""

# Activate venv
source .venv/bin/activate

echo "📋 Checking Python syntax..."
echo "----------------------------------------------------------------------"

files=(
    "src/extract_transform_platform/services/codegen/code_generator.py"
    "src/edgar_analyzer/cli/commands/project.py"
    "tests/integration/test_analyze_project_threshold.py"
)

all_ok=true

for file in "${files[@]}"; do
    if python -m py_compile "$file" 2>/dev/null; then
        echo "✓ $file"
    else
        echo "❌ $file"
        all_ok=false
    fi
done

echo ""
echo "======================================================================"
echo "Summary"
echo "======================================================================"

if [ "$all_ok" = true ]; then
    echo "✅ All files have valid Python syntax"
    echo ""
    echo "Integration is syntactically correct and ready for testing."
    echo ""
    echo "Next steps:"
    echo "1. Install runtime dependencies: pip install -r requirements.txt"
    echo "2. Run: edgar-analyzer project generate <project_name>"
    echo "3. Test interactive threshold prompt"
    echo "4. Test CLI flag: --confidence-threshold 0.8"
    exit 0
else
    echo "❌ Some syntax errors found"
    exit 1
fi
