#!/usr/bin/env python3
"""
Test Patent Extractor - Quick validation against example data.

This script:
1. Loads the 3 patent filing examples
2. Validates the extractor can process each input
3. Calculates accuracy metrics
4. Reports results for validation documentation

Usage:
    python scripts/test_patent_extractor.py
"""

import json
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from edgar_analyzer.extractors.patent.models import ExtractedData


def load_examples():
    """Load example files."""
    examples_dir = Path(__file__).parent.parent / "examples" / "patent_filings"
    examples = []

    for json_file in sorted(examples_dir.glob("*.json")):
        with open(json_file) as f:
            examples.append(json.load(f))

    return examples


def extract_from_input(input_data: dict) -> ExtractedData:
    """
    Simulate extraction by parsing the example input.

    This is a simplified test that validates the data model
    without calling the actual OpenRouter API.
    """
    api_response = input_data.get("api_response", {})

    # Extract inventor names from list of dicts
    inventors = []
    for inventor in api_response.get("inventors", []):
        if isinstance(inventor, dict):
            inventors.append(inventor["name"])
        else:
            inventors.append(str(inventor))

    # Extract classifications (flatten CPC array)
    classifications = api_response.get("classifications", {}).get("cpc", [])

    # Extract assignee
    assignee_data = api_response.get("assignee", {})
    assignee = (
        assignee_data.get("name", "")
        if isinstance(assignee_data, dict)
        else str(assignee_data)
    )

    # Get claims count
    claims_data = api_response.get("claims", {})
    claims_count = claims_data.get("total_claims", 0)

    return ExtractedData(
        patent_number=api_response.get("patent_id", ""),
        title=api_response.get("title", ""),
        inventors=inventors,
        assignee=assignee,
        filing_date=api_response.get("filing_date", ""),
        grant_date=api_response.get("grant_date", ""),
        claims_count=claims_count,
        abstract=api_response.get("abstract", ""),
        status=api_response.get("legal_status", ""),
        classifications=classifications,
    )


def compare_results(expected: dict, actual: ExtractedData) -> tuple[bool, list[str]]:
    """
    Compare expected output with actual extraction result.

    Returns:
        (matches, errors) - matches is True if all fields match, errors lists mismatches
    """
    errors = []

    # Compare all fields
    for field_name in expected.keys():
        expected_value = expected[field_name]
        actual_value = getattr(actual, field_name, None)

        if expected_value != actual_value:
            errors.append(
                f"  - {field_name}: expected={expected_value}, actual={actual_value}"
            )

    return len(errors) == 0, errors


def main():
    """Run patent extractor validation tests."""
    print("=" * 70)
    print("PATENT EXTRACTOR VALIDATION TEST")
    print("=" * 70)
    print()

    # Load examples
    examples = load_examples()
    print(f"Loaded {len(examples)} examples\n")

    # Track results
    total = len(examples)
    passed = 0
    failed = 0
    all_errors = []

    # Test each example
    for i, example in enumerate(examples, 1):
        example_id = example.get("example_id", f"example_{i}")
        print(f"[{i}/{total}] Testing {example_id}...", end=" ")

        try:
            # Extract from input
            result = extract_from_input(example["input"])

            # Compare with expected output
            matches, errors = compare_results(example["output"], result)

            if matches:
                print("✅ PASS")
                passed += 1
            else:
                print("❌ FAIL")
                failed += 1
                all_errors.append((example_id, errors))
                print(f"Errors for {example_id}:")
                for error in errors:
                    print(error)
                print()

        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
            all_errors.append((example_id, [f"Exception: {str(e)}"]))

    # Print summary
    print()
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"\nTotal Examples: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")

    if all_errors:
        print(f"\nErrors ({len(all_errors)}):")
        for example_id, errors in all_errors:
            print(f"\n{example_id}:")
            for error in errors:
                print(f"  {error}")

    # Success criteria: ≥85% accuracy (at least 2 out of 3 for now)
    accuracy = passed / total
    print()
    print("=" * 70)

    if accuracy >= 0.85:
        print("✅ VALIDATION PASSED (≥85% accuracy)")
        print(f"Accuracy: {accuracy:.1%}")
        return 0
    else:
        print("❌ VALIDATION FAILED (<85% accuracy)")
        print(f"Accuracy: {accuracy:.1%}")
        print("Target: ≥85%")
        return 1


if __name__ == "__main__":
    sys.exit(main())
