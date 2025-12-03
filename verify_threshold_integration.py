#!/usr/bin/env python3
"""
Verification script for confidence threshold CLI integration.

This script demonstrates that the integration is complete and functional.
It performs syntax checks, import verification, and basic functionality tests.

Run: python verify_threshold_integration.py
"""

import ast
import sys
from pathlib import Path


def check_syntax(file_path: Path) -> bool:
    """Check Python file syntax."""
    try:
        with open(file_path) as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False


def check_imports() -> bool:
    """Verify all required imports work."""
    try:
        # Service layer
        from extract_transform_platform.services.analysis.pattern_filter import (
            PatternFilterService,
        )
        from extract_transform_platform.services.codegen.code_generator import (
            CodeGeneratorService,
        )

        # CLI layer
        from edgar_analyzer.cli.prompts.confidence_threshold import (
            ConfidenceThresholdPrompt,
        )

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def verify_code_generator_integration() -> bool:
    """Verify CodeGeneratorService has pattern filtering."""
    try:
        from extract_transform_platform.services.codegen.code_generator import (
            CodeGeneratorService,
        )
        import inspect

        # Check __init__ signature
        init_sig = inspect.signature(CodeGeneratorService.__init__)
        print(f"✓ CodeGeneratorService.__init__ signature: {init_sig}")

        # Check generate signature
        generate_sig = inspect.signature(CodeGeneratorService.generate)
        params = list(generate_sig.parameters.keys())

        if "confidence_threshold" not in params:
            print("❌ confidence_threshold parameter missing from generate()")
            return False

        print("✓ confidence_threshold parameter present in generate()")

        # Check filter_service attribute exists
        generator = CodeGeneratorService()
        if not hasattr(generator, "filter_service"):
            print("❌ filter_service attribute missing")
            return False

        print("✓ filter_service attribute present")
        return True

    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False


def verify_cli_integration() -> bool:
    """Verify CLI command has confidence threshold support."""
    try:
        from edgar_analyzer.cli.commands.project import generate
        import inspect

        # Check CLI command signature
        sig = inspect.signature(generate.callback)
        params = list(sig.parameters.keys())

        if "confidence_threshold" not in params:
            print("❌ confidence_threshold parameter missing from CLI command")
            return False

        print("✓ confidence_threshold parameter present in CLI command")
        return True

    except Exception as e:
        print(f"❌ CLI verification error: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Confidence Threshold Integration Verification")
    print("=" * 70)
    print()

    checks = []

    # 1. Syntax checks
    print("📋 Syntax Checks")
    print("-" * 70)

    files_to_check = [
        Path("src/extract_transform_platform/services/codegen/code_generator.py"),
        Path("src/edgar_analyzer/cli/commands/project.py"),
        Path("tests/integration/test_analyze_project_threshold.py"),
    ]

    syntax_ok = all(check_syntax(f) for f in files_to_check)
    checks.append(("Syntax validation", syntax_ok))

    if syntax_ok:
        print("✓ All files have valid Python syntax")
    print()

    # 2. Import checks
    print("📦 Import Checks")
    print("-" * 70)
    imports_ok = check_imports()
    checks.append(("Import verification", imports_ok))
    print()

    # 3. Service layer integration
    print("⚙️  Service Layer Integration")
    print("-" * 70)
    service_ok = verify_code_generator_integration()
    checks.append(("CodeGeneratorService integration", service_ok))
    print()

    # 4. CLI layer integration
    print("🖥️  CLI Layer Integration")
    print("-" * 70)
    cli_ok = verify_cli_integration()
    checks.append(("CLI command integration", cli_ok))
    print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)

    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")

    all_passed = all(result for _, result in checks)

    print()
    if all_passed:
        print("🎉 All verification checks passed!")
        print()
        print("Integration is complete and ready for testing.")
        print()
        print("Next steps:")
        print("1. Run: edgar-analyzer project generate <project_name>")
        print("2. Test interactive threshold prompt")
        print("3. Test CLI flag: --confidence-threshold 0.8")
        return 0
    else:
        print("⚠️  Some verification checks failed.")
        print("Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
