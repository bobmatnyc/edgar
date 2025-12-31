"""SCT Data Validator for Recipe System.

Validates Summary Compensation Table extraction results with lenient rules.
Flags issues but includes partial data to maximize data availability.

Validation Rules:
- Must have `company` and `cik` fields
- `executives` list should have at least 1 entry
- Each executive should have `name` and `compensation` list
- Warnings logged for missing fields, but partial data included

Design:
- Lenient validation (include data even if partially valid)
- Structured error reporting with validation_errors list
- Summary statistics for monitoring data quality
"""

import structlog

logger = structlog.get_logger(__name__)


def validate_sct_data(sct_data: list[dict]) -> dict:
    """Validate SCT extraction results.

    Args:
        sct_data: List of SCT extraction results from ExtractorHandler.
                  Expected structure (from SCTData model):
                  [
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
                                          ...
                                      }
                                  ]
                              }
                          ]
                      }
                  ]

    Returns:
        Dict with:
        - validated_data: List of valid SCT records (includes partial data)
        - validation_errors: List of validation errors with context
        - stats: Summary statistics
            - total_records: Total input records
            - valid_records: Records passing all checks
            - partial_records: Records with warnings but included
            - invalid_records: Records excluded (severe errors)
            - total_executives: Total executives across all records
            - total_compensation_years: Total compensation years extracted

    Example:
        >>> result = validate_sct_data(sct_data)
        >>> print(result["stats"]["valid_records"])
        8
        >>> for error in result["validation_errors"]:
        ...     print(f"{error['company']}: {error['error']}")
    """
    validated_data: list[dict] = []
    validation_errors: list[dict] = []

    total_records = len(sct_data)
    valid_records = 0
    partial_records = 0
    invalid_records = 0
    total_executives = 0
    total_compensation_years = 0

    logger.info("validating_sct_data", total_records=total_records)

    for idx, record in enumerate(sct_data):
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
                "sct_record_invalid",
                record_index=idx,
                errors=record_errors,
            )
            continue  # Skip this record

        # Executives validation
        executives = record.get("executives", [])

        if not executives:
            record_errors.append("No executives found in record")
            severity = "partial"
        elif not isinstance(executives, list):
            record_errors.append(f"executives field is not a list: {type(executives)}")
            severity = "partial"
        else:
            # Validate each executive
            for exec_idx, executive in enumerate(executives):
                exec_name = executive.get("name", "")
                compensation = executive.get("compensation", [])

                if not exec_name:
                    record_errors.append(f"Executive {exec_idx} missing name field")
                    severity = "partial"

                if not compensation:
                    record_errors.append(
                        f"Executive '{exec_name or exec_idx}' has no compensation data"
                    )
                    severity = "partial"
                elif not isinstance(compensation, list):
                    record_errors.append(
                        f"Executive '{exec_name or exec_idx}' compensation is not a list"
                    )
                    severity = "partial"
                else:
                    # Count compensation years
                    total_compensation_years += len(compensation)

            # Count executives (even if partial)
            total_executives += len(executives)

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
                    "sct_record_partial",
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
        "total_executives": total_executives,
        "total_compensation_years": total_compensation_years,
    }

    logger.info(
        "sct_validation_complete",
        stats=stats,
        error_count=len(validation_errors),
    )

    return {
        "validated_data": validated_data,
        "validation_errors": validation_errors,
        "stats": stats,
    }
