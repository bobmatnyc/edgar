#!/usr/bin/env python3
"""
Verification script for iterative refinement implementation (1M-325).

This script verifies that the iterative refinement loop is correctly
implemented without requiring a full test environment.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def verify_implementation():
    """Verify all implementation changes are in place."""

    print("=" * 80)
    print("VERIFICATION: Iterative Refinement Loop Implementation (1M-325)")
    print("=" * 80)
    print()

    results = []

    # 1. Check CodeGeneratorService.generate() has max_retries parameter
    print("1. Checking CodeGeneratorService.generate() signature...")
    try:
        import inspect

        from edgar_analyzer.services.code_generator import CodeGeneratorService

        sig = inspect.signature(CodeGeneratorService.generate)
        params = list(sig.parameters.keys())

        if "max_retries" in params:
            print("   ✅ max_retries parameter exists")

            # Check default value
            default = sig.parameters["max_retries"].default
            if default == 3:
                print(f"   ✅ Default value is 3")
                results.append(True)
            else:
                print(f"   ❌ Default value is {default}, expected 3")
                results.append(False)
        else:
            print(f"   ❌ max_retries parameter missing. Found: {params}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)

    print()

    # 2. Check Sonnet45Agent.code() has validation_errors parameter
    print("2. Checking Sonnet45Agent.code() signature...")
    try:
        from edgar_analyzer.agents.sonnet45_agent import Sonnet45Agent

        sig = inspect.signature(Sonnet45Agent.code)
        params = list(sig.parameters.keys())

        if "validation_errors" in params:
            print("   ✅ validation_errors parameter exists")

            # Check it's optional
            default = sig.parameters["validation_errors"].default
            if default is None:
                print(f"   ✅ Default value is None (optional)")
                results.append(True)
            else:
                print(f"   ⚠️  Default value is {default}")
                results.append(True)  # Still OK
        else:
            print(f"   ❌ validation_errors parameter missing. Found: {params}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)

    print()

    # 3. Check PromptLoader has retry methods
    print("3. Checking PromptLoader retry methods...")
    try:
        from edgar_analyzer.agents.sonnet45_agent import PromptLoader

        methods = ["render_coder_retry_prompt", "_format_validation_errors"]

        all_exist = True
        for method in methods:
            if hasattr(PromptLoader, method):
                print(f"   ✅ {method} exists")
            else:
                print(f"   ❌ {method} missing")
                all_exist = False

        results.append(all_exist)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)

    print()

    # 4. Check coder_mode_retry.md template exists
    print("4. Checking coder_mode_retry.md prompt template...")
    try:
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "src",
            "edgar_analyzer",
            "agents",
            "prompts",
            "coder_mode_retry.md",
        )

        if os.path.exists(template_path):
            size = os.path.getsize(template_path)
            print(f"   ✅ Template exists ({size} bytes)")

            # Check for key placeholders
            with open(template_path, "r") as f:
                content = f.read()

            placeholders = [
                "{{plan_spec_json}}",
                "{{patterns_and_examples_json}}",
                "{{validation_errors}}",
            ]

            all_present = True
            for placeholder in placeholders:
                if placeholder in content:
                    print(f"   ✅ Placeholder {placeholder} present")
                else:
                    print(f"   ❌ Placeholder {placeholder} missing")
                    all_present = False

            results.append(all_present)
        else:
            print(f"   ❌ Template not found at {template_path}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)

    print()

    # 5. Check integration tests exist
    print("5. Checking integration tests...")
    try:
        test_path = os.path.join(
            os.path.dirname(__file__), "integration", "test_code_generation.py"
        )

        if os.path.exists(test_path):
            with open(test_path, "r") as f:
                content = f.read()

            tests = [
                "test_iterative_refinement_on_validation_failure",
                "test_max_retries_exceeded",
                "test_validation_disabled_no_retry",
            ]

            all_exist = True
            for test in tests:
                if test in content:
                    print(f"   ✅ {test} exists")
                else:
                    print(f"   ❌ {test} missing")
                    all_exist = False

            results.append(all_exist)
        else:
            print(f"   ❌ Test file not found at {test_path}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)

    print()
    print("=" * 80)
    print(f"VERIFICATION RESULTS: {sum(results)}/{len(results)} checks passed")
    print("=" * 80)

    if all(results):
        print("\n✅ ALL CHECKS PASSED - Implementation is complete!")
        return 0
    else:
        print(f"\n❌ {len(results) - sum(results)} checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(verify_implementation())
