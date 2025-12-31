"""Test script for SCT and Tax validators.

This script demonstrates the validators with various scenarios:
- Valid records (all fields present)
- Partial records (missing optional fields)
- Invalid records (missing required fields)
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edgar_analyzer.validators import validate_sct_data, validate_tax_data


def test_sct_validator():
    """Test SCT validator with various scenarios."""
    print("=" * 80)
    print("Testing SCT Validator")
    print("=" * 80)

    sct_test_data = [
        # Valid record - all fields present
        {
            "company": "Apple Inc.",
            "cik": "0000320193",
            "filing_date": "2024-01-15",
            "executives": [
                {
                    "name": "Tim Cook",
                    "title": "CEO",
                    "compensation": [
                        {
                            "year": 2023,
                            "salary": 3000000.0,
                            "total": 63209845.0,
                        }
                    ],
                },
                {
                    "name": "Luca Maestri",
                    "title": "CFO",
                    "compensation": [
                        {
                            "year": 2023,
                            "salary": 1000000.0,
                            "total": 26509671.0,
                        }
                    ],
                },
            ],
        },
        # Partial record - missing filing_date, empty compensation
        {
            "company": "Microsoft Corp",
            "cik": "0000789019",
            "executives": [
                {
                    "name": "Satya Nadella",
                    "title": "CEO",
                    "compensation": [],  # Empty compensation
                }
            ],
        },
        # Partial record - no executives
        {
            "company": "Test Corp",
            "cik": "0001234567",
            "filing_date": "2024-01-15",
            "executives": [],
        },
        # Partial record - missing executive name
        {
            "company": "Example Inc",
            "cik": "0009999999",
            "executives": [
                {
                    "title": "CEO",  # Missing name
                    "compensation": [{"year": 2023, "total": 1000000.0}],
                }
            ],
        },
        # Invalid record - missing both company and cik
        {
            "filing_date": "2024-01-15",
            "executives": [],
        },
    ]

    result = validate_sct_data(sct_test_data)

    print("\nValidation Results:")
    print(f"  Total records: {result['stats']['total_records']}")
    print(f"  Valid records: {result['stats']['valid_records']}")
    print(f"  Partial records: {result['stats']['partial_records']}")
    print(f"  Invalid records: {result['stats']['invalid_records']}")
    print(f"  Total executives: {result['stats']['total_executives']}")
    print(f"  Total compensation years: {result['stats']['total_compensation_years']}")
    print(f"\nValidation errors: {len(result['validation_errors'])}")

    print("\nError Details:")
    for error in result["validation_errors"]:
        severity = error["severity"]
        company = error.get("company", "Unknown")
        cik = error.get("cik", "Unknown")
        errors = error.get("errors", [])
        print(f"  [{severity.upper()}] {company} ({cik}):")
        for err in errors:
            print(f"    - {err}")

    print(f"\nValidated data count: {len(result['validated_data'])}")
    print()


def test_tax_validator():
    """Test Tax validator with various scenarios."""
    print("=" * 80)
    print("Testing Tax Validator")
    print("=" * 80)

    tax_test_data = [
        # Valid record - all fields present
        {
            "company": "Apple Inc.",
            "cik": "0000320193",
            "filing_date": "2024-02-15",
            "fiscal_year_end": "2023-09-30",
            "tax_years": [
                {
                    "year": 2023,
                    "current_federal": 10500000000.0,
                    "current_state": 1200000000.0,
                    "current_foreign": 5800000000.0,
                    "total_tax_expense": 15500000000.0,
                    "effective_tax_rate": 0.145,
                },
                {
                    "year": 2022,
                    "total_tax_expense": 14527000000.0,
                    "effective_tax_rate": 0.152,
                },
            ],
        },
        # Partial record - missing fiscal_year_end, missing year in tax_years
        {
            "company": "Microsoft Corp",
            "cik": "0000789019",
            "filing_date": "2024-02-20",
            "tax_years": [
                {
                    # Missing year field
                    "total_tax_expense": 18294000000.0,
                }
            ],
        },
        # Partial record - no tax years
        {
            "company": "Test Corp",
            "cik": "0001234567",
            "filing_date": "2024-01-15",
            "tax_years": [],
        },
        # Partial record - missing total_tax_expense
        {
            "company": "Example Inc",
            "cik": "0009999999",
            "tax_years": [
                {
                    "year": 2023,
                    # Missing total_tax_expense
                }
            ],
        },
        # Invalid record - missing both company and cik
        {
            "filing_date": "2024-01-15",
            "tax_years": [],
        },
    ]

    result = validate_tax_data(tax_test_data)

    print("\nValidation Results:")
    print(f"  Total records: {result['stats']['total_records']}")
    print(f"  Valid records: {result['stats']['valid_records']}")
    print(f"  Partial records: {result['stats']['partial_records']}")
    print(f"  Invalid records: {result['stats']['invalid_records']}")
    print(f"  Total tax years: {result['stats']['total_tax_years']}")
    print(f"  Total tax expense sum: ${result['stats']['total_tax_expense_sum']:,.0f}")
    print(f"\nValidation errors: {len(result['validation_errors'])}")

    print("\nError Details:")
    for error in result["validation_errors"]:
        severity = error["severity"]
        company = error.get("company", "Unknown")
        cik = error.get("cik", "Unknown")
        errors = error.get("errors", [])
        print(f"  [{severity.upper()}] {company} ({cik}):")
        for err in errors:
            print(f"    - {err}")

    print(f"\nValidated data count: {len(result['validated_data'])}")
    print()


if __name__ == "__main__":
    test_sct_validator()
    test_tax_validator()
    print("=" * 80)
    print("✅ All validator tests completed!")
    print("=" * 80)
