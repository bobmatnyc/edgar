"""Tax Data Validator for Recipe System.

Validates income tax extraction results with lenient rules.
Flags issues but includes partial data to maximize data availability.

Validation Rules:
- Must have `company` and `cik` fields
- `tax_years` list should have at least 1 entry
- Each tax year should have `year` and `total_tax_expense`
- Warnings logged for missing fields, but partial data included

Design:
- Lenient validation (include data even if partially valid)
- Structured error reporting with validation_errors list
- Summary statistics for monitoring data quality
"""

import structlog

logger = structlog.get_logger(__name__)


def validate_tax_data(tax_data: list[dict]) -> dict:
    """Validate Tax extraction results.

    Args:
        tax_data: List of Tax extraction results from ExtractorHandler.
                  Expected structure (from TaxData model):
                  [
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
                                  ...
                              }
                          ]
                      }
                  ]

    Returns:
        Dict with:
        - validated_data: List of valid tax records (includes partial data)
        - validation_errors: List of validation errors with context
        - stats: Summary statistics
            - total_records: Total input records
            - valid_records: Records passing all checks
            - partial_records: Records with warnings but included
            - invalid_records: Records excluded (severe errors)
            - total_tax_years: Total tax years across all records
            - total_tax_expense_sum: Sum of all total_tax_expense values

    Example:
        >>> result = validate_tax_data(tax_data)
        >>> print(result["stats"]["valid_records"])
        8
        >>> for error in result["validation_errors"]:
        ...     print(f"{error['company']}: {error['error']}")
    """
    validated_data: list[dict] = []
    validation_errors: list[dict] = []

    total_records = len(tax_data)
    valid_records = 0
    partial_records = 0
    invalid_records = 0
    total_tax_years = 0
    total_tax_expense_sum = 0.0

    logger.info("validating_tax_data", total_records=total_records)

    for idx, record in enumerate(tax_data):
        record_errors: list[str] = []
        severity = "valid"  # valid, partial, invalid

        # Required fields validation
        company = record.get("company", "")
        cik = record.get("cik", "")

        if not company:
            record_errors.append("Missing required field: company")
            severity = "partial"

        if not cik:
            record_errors.append("Missing required field: cik")
            severity = "partial"

        # If both company and cik are missing, mark as invalid
        if not company and not cik:
            severity = "invalid"
            invalid_records += 1
            validation_errors.append(
                {
                    "record_index": idx,
                    "company": company or "Unknown",
                    "cik": cik or "Unknown",
                    "errors": record_errors,
                    "severity": "error",
                }
            )
            logger.warning(
                "tax_record_invalid",
                record_index=idx,
                errors=record_errors,
            )
            continue  # Skip this record

        # Tax years validation
        tax_years = record.get("tax_years", [])

        if not tax_years:
            record_errors.append("No tax years found in record")
            severity = "partial"
        elif not isinstance(tax_years, list):
            record_errors.append(f"tax_years field is not a list: {type(tax_years)}")
            severity = "partial"
        else:
            # Validate each tax year
            for year_idx, tax_year in enumerate(tax_years):
                year = tax_year.get("year")
                total_tax_expense = tax_year.get("total_tax_expense")

                if year is None:
                    record_errors.append(f"Tax year {year_idx} missing year field")
                    severity = "partial"

                if total_tax_expense is None:
                    record_errors.append(
                        f"Tax year {year or year_idx} missing total_tax_expense field"
                    )
                    severity = "partial"
                else:
                    # Accumulate total tax expense
                    try:
                        total_tax_expense_sum += float(total_tax_expense)
                    except (ValueError, TypeError):
                        record_errors.append(
                            f"Tax year {year or year_idx} has invalid total_tax_expense: {total_tax_expense}"
                        )
                        severity = "partial"

            # Count tax years (even if partial)
            total_tax_years += len(tax_years)

        # Record the validation result
        if record_errors:
            validation_errors.append(
                {
                    "record_index": idx,
                    "company": company,
                    "cik": cik,
                    "errors": record_errors,
                    "severity": "warning" if severity == "partial" else "error",
                }
            )

        # Include record in validated data (lenient approach)
        if severity != "invalid":
            validated_data.append(record)

            if severity == "valid":
                valid_records += 1
            elif severity == "partial":
                partial_records += 1
                logger.warning(
                    "tax_record_partial",
                    company=company,
                    cik=cik,
                    errors=record_errors,
                )

    # Summary statistics
    stats = {
        "total_records": total_records,
        "valid_records": valid_records,
        "partial_records": partial_records,
        "invalid_records": invalid_records,
        "total_tax_years": total_tax_years,
        "total_tax_expense_sum": total_tax_expense_sum,
    }

    logger.info(
        "tax_validation_complete",
        stats=stats,
        error_count=len(validation_errors),
    )

    return {
        "validated_data": validated_data,
        "validation_errors": validation_errors,
        "stats": stats,
    }
