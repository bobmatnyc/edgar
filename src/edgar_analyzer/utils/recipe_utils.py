"""
Recipe utility functions for combining and writing extraction results.

This module provides utilities for the recipe system to combine SCT and Tax
extraction results and write them to various output formats.

Key Features:
- Combine SCT and Tax results by CIK
- Write results to JSON and CSV formats
- Handle both BatchResult and list of dicts
- Calculate summary statistics

Example Usage:
    >>> from edgar_analyzer.utils.recipe_utils import combine_company_results, write_results
    >>> combined = combine_company_results(sct_results, tax_results)
    >>> paths = write_results(combined, "output", format="both")
    >>> print(f"Wrote {paths['json']} and {paths['csv']}")
"""

import csv
from pathlib import Path
from typing import Any, Union

import structlog

from edgar_analyzer.services.batch_processor import BatchResult

logger = structlog.get_logger(__name__)

# Type alias for input results
ResultsInput = Union[list[dict[str, Any]], BatchResult[Any]]


def _normalize_results(results: ResultsInput, data_type: str) -> list[dict[str, Any]]:
    """
    Convert BatchResult or list to list of dicts with extracted data.

    Args:
        results: Either BatchResult or list of dicts
        data_type: Type identifier for logging ("sct" or "tax")

    Returns:
        List of dicts with format:
            {
                "cik": "0000320193",
                "company": "Apple Inc.",
                "data": {...}  # model_dump() output or None if failed
            }

    Example:
        >>> batch_result = BatchResult(successful=[...], failed=[...], ...)
        >>> normalized = _normalize_results(batch_result, "sct")
        >>> assert all("cik" in item for item in normalized)
    """
    normalized: list[dict[str, Any]] = []

    logger.debug(
        "normalize_results_input",
        data_type=data_type,
        results_type=type(results).__name__,
        is_list=isinstance(results, list),
        is_batch=isinstance(results, BatchResult),
    )

    if isinstance(results, BatchResult):
        # Process successful extractions
        for extraction in results.successful:
            if extraction.data is not None:
                # Pydantic model - use model_dump()
                data_dict = extraction.data.model_dump()
                normalized.append(
                    {
                        "cik": extraction.cik,
                        "company": extraction.company_name,
                        "data": data_dict,
                    }
                )
                logger.debug(
                    "Normalized successful extraction",
                    data_type=data_type,
                    cik=extraction.cik,
                    company=extraction.company_name,
                )

        # Process failed extractions (include with data=None)
        for extraction in results.failed:
            normalized.append(
                {
                    "cik": extraction.cik,
                    "company": extraction.company_name,
                    "data": None,
                }
            )
            logger.debug(
                "Normalized failed extraction",
                data_type=data_type,
                cik=extraction.cik,
                company=extraction.company_name,
                error=extraction.error,
            )

    else:
        # List of dicts from validator - convert to expected format
        # Validator format: {"company": "...", "cik": "...", "executives": [...]}
        # Expected format: {"cik": "...", "company": "...", "data": {...}}
        logger.debug(
            "Converting list results",
            data_type=data_type,
            count=len(results) if isinstance(results, list) else "N/A",
        )

        for idx, item in enumerate(results):
            if isinstance(item, dict):
                # Extract cik and company, rest is data
                cik = item.get("cik", "")
                company = item.get("company", "")

                # Build data dict (exclude cik and company from data)
                data = {k: v for k, v in item.items() if k not in ("cik", "company")}

                normalized.append(
                    {
                        "cik": cik,
                        "company": company,
                        "data": data if data else None,
                    }
                )
                logger.debug(
                    "Normalized list item",
                    data_type=data_type,
                    idx=idx,
                    cik=cik,
                    company=company,
                    data_keys=list(data.keys()) if data else [],
                )
            else:
                logger.warning(
                    "Unexpected item type in results list",
                    data_type=data_type,
                    idx=idx,
                    item_type=type(item).__name__,
                    item_repr=repr(item)[:200],
                )

    return normalized


def combine_company_results(
    sct_results: ResultsInput, tax_results: ResultsInput
) -> dict[str, Any]:
    """
    Combine SCT and Tax extraction results by company CIK.

    Merges results from two data sources (SCT from DEF 14A, Tax from 10-K)
    using CIK as the join key. Handles partial results where one or both
    extractions may have failed.

    Args:
        sct_results: SCT extraction results (BatchResult or list of dicts)
        tax_results: Tax extraction results (BatchResult or list of dicts)

    Returns:
        Combined results dictionary with structure:
        {
            "companies": [
                {
                    "cik": "0000320193",
                    "name": "Apple Inc.",
                    "sct_data": {...} | None,
                    "tax_data": {...} | None
                }
            ],
            "summary": {
                "total_companies": 100,
                "sct_success": 95,
                "tax_success": 92,
                "both_success": 90
            }
        }

    Example:
        >>> sct_batch = BatchResult(successful=[...], failed=[...], ...)
        >>> tax_batch = BatchResult(successful=[...], failed=[...], ...)
        >>> combined = combine_company_results(sct_batch, tax_batch)
        >>> print(f"Both succeeded: {combined['summary']['both_success']}")
    """
    logger.info("Combining SCT and Tax results")

    # Normalize both result sets
    sct_normalized = _normalize_results(sct_results, "sct")
    tax_normalized = _normalize_results(tax_results, "tax")

    # Build lookup maps by CIK
    sct_by_cik: dict[str, dict[str, Any]] = {
        item["cik"]: item for item in sct_normalized
    }
    tax_by_cik: dict[str, dict[str, Any]] = {
        item["cik"]: item for item in tax_normalized
    }

    # Get all unique CIKs from both sources
    all_ciks = set(sct_by_cik.keys()) | set(tax_by_cik.keys())

    # Combine results
    companies: list[dict[str, Any]] = []
    sct_success_count = 0
    tax_success_count = 0
    both_success_count = 0

    for cik in sorted(all_ciks):  # Sort for deterministic output
        sct_item = sct_by_cik.get(cik)
        tax_item = tax_by_cik.get(cik)

        # Get company name (prefer SCT, fallback to Tax)
        company_name = ""
        if sct_item:
            company_name = sct_item["company"]
        elif tax_item:
            company_name = tax_item["company"]

        # Extract data (None if failed or missing)
        sct_data = sct_item["data"] if sct_item else None
        tax_data = tax_item["data"] if tax_item else None

        # Track success counts
        if sct_data is not None:
            sct_success_count += 1
        if tax_data is not None:
            tax_success_count += 1
        if sct_data is not None and tax_data is not None:
            both_success_count += 1

        companies.append(
            {
                "cik": cik,
                "name": company_name,
                "sct_data": sct_data,
                "tax_data": tax_data,
            }
        )

    # Build summary statistics
    summary = {
        "total_companies": len(companies),
        "sct_success": sct_success_count,
        "tax_success": tax_success_count,
        "both_success": both_success_count,
    }

    logger.info(
        "Results combined",
        total_companies=summary["total_companies"],
        sct_success=summary["sct_success"],
        tax_success=summary["tax_success"],
        both_success=summary["both_success"],
    )

    return {
        "companies": companies,
        "summary": summary,
    }


def _write_combined_csv(results: dict[str, Any], csv_path: Path) -> None:
    """
    Write combined results to CSV file.

    Creates a CSV with columns for both SCT and Tax data, with one row per company.
    Uses latest year data for multi-year fields.

    Args:
        results: Combined results from combine_company_results
        csv_path: Path to write CSV file

    CSV Columns:
        - CIK, Company, Year
        - Total Exec Comp, CEO Comp, Num Executives
        - Total Tax Expense, Effective Tax Rate
        - Exec/Tax Ratio

    Example:
        >>> combined = combine_company_results(sct_results, tax_results)
        >>> _write_combined_csv(combined, Path("output/results.csv"))
    """
    logger.info("Writing CSV file", path=str(csv_path))

    # Ensure output directory exists
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "CIK",
            "Company",
            "Year",
            "Total_Exec_Comp",
            "CEO_Comp",
            "Num_Executives",
            "Total_Tax_Expense",
            "Effective_Tax_Rate",
            "Exec_Tax_Ratio",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for company in results["companies"]:
            cik = company["cik"]
            name = company["name"]
            sct_data = company["sct_data"]
            tax_data = company["tax_data"]

            # Extract SCT data (latest year)
            total_exec_comp = 0.0
            ceo_comp = 0.0
            num_executives = 0
            year = ""

            if sct_data:
                executives = sct_data.get("executives", [])
                num_executives = len(executives)

                # Calculate total compensation (latest year for each exec)
                for exec_data in executives:
                    comp_years = exec_data.get("compensation", [])
                    if comp_years:
                        latest = comp_years[0]  # First entry is latest
                        total_exec_comp += latest.get("total", 0.0)

                        # Identify CEO (typically first executive or title contains "CEO")
                        if not year:
                            year = str(latest.get("year", ""))

                # CEO is typically first executive in SCT
                if executives:
                    ceo_exec = executives[0]
                    ceo_comp_years = ceo_exec.get("compensation", [])
                    if ceo_comp_years:
                        ceo_comp = ceo_comp_years[0].get("total", 0.0)

            # Extract Tax data (latest year)
            total_tax_expense = 0.0
            effective_tax_rate = 0.0

            if tax_data:
                tax_years = tax_data.get("tax_years", [])
                if tax_years:
                    latest_tax = tax_years[0]  # First entry is latest
                    total_tax_expense = latest_tax.get("total_tax_expense", 0.0)
                    effective_tax_rate = latest_tax.get("effective_tax_rate", 0.0)
                    if not year:
                        year = str(latest_tax.get("year", ""))

            # Calculate Exec/Tax Ratio
            exec_tax_ratio = 0.0
            if total_tax_expense > 0:
                exec_tax_ratio = total_exec_comp / total_tax_expense

            # Write row
            writer.writerow(
                {
                    "CIK": cik,
                    "Company": name,
                    "Year": year,
                    "Total_Exec_Comp": f"{total_exec_comp:.2f}",
                    "CEO_Comp": f"{ceo_comp:.2f}",
                    "Num_Executives": num_executives,
                    "Total_Tax_Expense": f"{total_tax_expense:.2f}",
                    "Effective_Tax_Rate": f"{effective_tax_rate:.4f}",
                    "Exec_Tax_Ratio": f"{exec_tax_ratio:.4f}",
                }
            )

    logger.info("CSV file written", path=str(csv_path), rows=len(results["companies"]))


def write_results(
    results: dict[str, Any],
    output_dir: Union[str, Path],
    format: str = "json",
    prefix: str = "",
) -> dict[str, Path]:
    """
    Write combined results to files in specified format(s).

    Args:
        results: Combined results from combine_company_results
        output_dir: Output directory path
        format: Output format - "json", "csv", or "both"
        prefix: Optional filename prefix (e.g., "fortune100_")

    Returns:
        Dictionary mapping format to file path:
        {
            "json": Path("output/results.json"),
            "csv": Path("output/combined.csv")
        }

    Raises:
        ValueError: If format is not "json", "csv", or "both"

    Example:
        >>> combined = combine_company_results(sct_results, tax_results)
        >>> paths = write_results(combined, "output", format="both", prefix="f100_")
        >>> print(f"JSON: {paths['json']}")
        >>> print(f"CSV: {paths['csv']}")
    """
    # Validate format
    if format not in ("json", "csv", "both"):
        raise ValueError(f"Invalid format: {format}. Must be 'json', 'csv', or 'both'")

    # Convert output_dir to Path
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    written_files: dict[str, Path] = {}

    logger.info(
        "Writing results",
        output_dir=str(output_path),
        format=format,
        prefix=prefix,
    )

    # Write JSON
    if format in ("json", "both"):
        import json

        json_filename = f"{prefix}results.json" if prefix else "results.json"
        json_path = output_path / json_filename

        with json_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        written_files["json"] = json_path
        logger.info("JSON file written", path=str(json_path))

    # Write CSV
    if format in ("csv", "both"):
        csv_filename = f"{prefix}combined.csv" if prefix else "combined.csv"
        csv_path = output_path / csv_filename

        _write_combined_csv(results, csv_path)
        written_files["csv"] = csv_path

    logger.info(
        "Results written successfully",
        files=list(written_files.keys()),
        output_dir=str(output_path),
    )

    return written_files


def write_validation_results(
    validated_data: list[dict[str, Any]],
    validation_errors: list[dict[str, Any]],
    stats: dict[str, Any],
    output_dir: Union[str, Path],
    format: str = "json",
    prefix: str = "",
) -> dict[str, Path]:
    """
    Write validation results to JSON file.

    This is a helper for sub-recipe steps that need to write intermediate
    validation results before combining.

    Args:
        validated_data: List of validated records
        validation_errors: List of validation errors
        stats: Validation statistics
        output_dir: Output directory path
        format: Output format (only "json" supported for validation results)
        prefix: Optional filename prefix

    Returns:
        Dictionary mapping format to file path

    Example:
        >>> paths = write_validation_results(
        ...     validated_data=[...],
        ...     validation_errors=[...],
        ...     stats={...},
        ...     output_dir="output/sct",
        ...     prefix="sct_"
        ... )
    """
    import json

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Combine into single dict for output
    result = {
        "validated_data": validated_data,
        "validation_errors": validation_errors,
        "stats": stats,
    }

    # Write JSON
    filename = f"{prefix}results.json" if prefix else "validation_results.json"
    json_path = output_path / filename

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info("Validation results written", path=str(json_path))

    return {"json": json_path}


# Alias for backward compatibility
write_sct_validation_results = write_validation_results
write_tax_validation_results = write_validation_results


__all__ = [
    "combine_company_results",
    "write_results",
    "write_validation_results",
    "write_sct_validation_results",
    "write_tax_validation_results",
]
