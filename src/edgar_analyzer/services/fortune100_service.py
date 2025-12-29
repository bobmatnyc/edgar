"""
Fortune 100 Service - Orchestrates Fortune 100 data extraction pipeline.

This service coordinates the extraction of SCT (Summary Compensation Table) and
Tax data from Fortune 100 companies, using BatchProcessor for rate-limited SEC
API calls and Meta-Extractor adapters for data extraction.

Architecture:
- Service Layer: Orchestrates batch processing for Fortune 100 companies
- Adapter Layer: SCTAdapter, TaxAdapter bridge Fortune 100 extractors
- Batch Layer: BatchProcessor handles rate limiting and concurrency
- Data Layer: Fortune100Registry provides company lookup

Pipeline Flow:
1. Load Fortune 100 company registry (rank, name, CIK, sector)
2. Create extraction tasks for each company (SCT + Tax)
3. Process tasks with rate limiting (8 req/sec SEC compliance)
4. Consolidate results into JSON + CSV formats
5. Handle partial failures gracefully

Example Usage:
    >>> from edgar_analyzer.config.settings import ConfigService
    >>> from edgar_analyzer.services.edgar_api_service import EdgarApiService
    >>> config = ConfigService()
    >>> edgar_api = EdgarApiService(config=config)
    >>> service = Fortune100Service(edgar_api=edgar_api)
    >>> result = await service.extract_all(
    ...     form_type="DEF 14A",
    ...     output_dir=Path("output/"),
    ...     on_progress=lambda c, t, n: print(f"{c}/{t} - {n}")
    ... )
    >>> print(f"Success: {result.success_count}/{result.total_count}")
"""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog

from edgar_analyzer.extractors.fortune100.models import SCTData, TaxData
from edgar_analyzer.extractors.fortune100.sct_adapter import SCTAdapter
from edgar_analyzer.extractors.fortune100.tax_adapter import TaxAdapter
from edgar_analyzer.services.batch_processor import (
    BatchProcessor,
    BatchResult,
    CompanyTask,
    ExtractionResult,
)
from edgar_analyzer.services.interfaces import IEdgarApiService

logger = structlog.get_logger(__name__)


@dataclass
class Fortune100ExtractionResult:
    """
    Consolidated result from Fortune 100 extraction pipeline.

    Attributes:
        sct_results: SCT extraction results (successful + failed)
        tax_results: Tax extraction results (successful + failed)
        total_duration: Total pipeline duration in seconds
        output_files: List of generated output file paths
    """

    sct_results: Optional[BatchResult[SCTData]] = None
    tax_results: Optional[BatchResult[TaxData]] = None
    total_duration: float = 0.0
    output_files: list[Path] = None

    def __post_init__(self) -> None:
        if self.output_files is None:
            self.output_files = []

    @property
    def total_count(self) -> int:
        """Total number of companies processed."""
        count = 0
        if self.sct_results:
            count += len(self.sct_results.successful) + len(self.sct_results.failed)
        if self.tax_results:
            count += len(self.tax_results.successful) + len(self.tax_results.failed)
        return count

    @property
    def success_count(self) -> int:
        """Total number of successful extractions."""
        count = 0
        if self.sct_results:
            count += self.sct_results.success_count
        if self.tax_results:
            count += self.tax_results.success_count
        return count

    @property
    def failure_count(self) -> int:
        """Total number of failed extractions."""
        count = 0
        if self.sct_results:
            count += self.sct_results.failure_count
        if self.tax_results:
            count += self.tax_results.failure_count
        return count


class Fortune100Service:
    """
    Fortune 100 extraction pipeline orchestration service.

    Coordinates extraction of SCT and Tax data from Fortune 100 companies
    with rate limiting, progress tracking, and consolidated output.

    Features:
    - Batch processing with SEC rate limiting (8 req/sec)
    - Concurrent extraction (configurable max_concurrent)
    - Progress callbacks for CLI/UI integration
    - JSON + CSV export formats
    - Partial result handling (some failures OK)
    - Rank-based filtering (e.g., top 10, 11-50, etc.)

    Attributes:
        edgar_api: SEC EDGAR API service
        batch_processor_sct: Batch processor for SCT extraction
        batch_processor_tax: Batch processor for Tax extraction

    Example:
        >>> service = Fortune100Service(edgar_api=edgar_api)
        >>> result = await service.extract_sct_data(
        ...     rank_start=1,
        ...     rank_end=10,
        ...     output_dir=Path("output/")
        ... )
        >>> print(f"Extracted {result.success_count} companies")
    """

    def __init__(
        self,
        edgar_api: IEdgarApiService,
        max_concurrent: int = 5,
        max_retries: int = 3,
    ):
        """
        Initialize Fortune 100 service.

        Args:
            edgar_api: SEC EDGAR API service for fetching filings
            max_concurrent: Maximum concurrent requests (default: 5)
            max_retries: Maximum retry attempts per request (default: 3)
        """
        self.edgar_api = edgar_api

        # Create batch processors for SCT and Tax extraction
        self.batch_processor_sct = BatchProcessor[SCTData](
            edgar_api=edgar_api,
            max_concurrent=max_concurrent,
            max_retries=max_retries,
        )

        self.batch_processor_tax = BatchProcessor[TaxData](
            edgar_api=edgar_api,
            max_concurrent=max_concurrent,
            max_retries=max_retries,
        )

        logger.info(
            "Fortune100Service initialized",
            max_concurrent=max_concurrent,
            max_retries=max_retries,
        )

    async def extract_sct_data(
        self,
        companies: list[Dict[str, Any]],
        output_dir: Optional[Path] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None,
    ) -> BatchResult[SCTData]:
        """
        Extract Summary Compensation Table (SCT) data from companies.

        Args:
            companies: List of company dicts with 'name', 'cik', 'rank'
            output_dir: Output directory for JSON/CSV files (optional)
            on_progress: Progress callback(current, total, company_name)
            on_error: Error callback(company_name, exception)

        Returns:
            BatchResult with SCT extraction results

        Example:
            >>> companies = [
            ...     {"name": "Apple Inc.", "cik": "0000320193", "rank": 3}
            ... ]
            >>> result = await service.extract_sct_data(
            ...     companies,
            ...     output_dir=Path("output/")
            ... )
        """
        logger.info(
            "Starting SCT extraction",
            company_count=len(companies),
        )

        # Create extraction tasks
        tasks = [
            CompanyTask(
                company_name=company["name"],
                cik=company["cik"],
                form_type="DEF 14A",
                extractor_factory=lambda c=company: SCTAdapter(
                    company=c["name"], cik=c["cik"]
                ),
            )
            for company in companies
        ]

        # Process batch
        result = await self.batch_processor_sct.process_batch(
            tasks=tasks,
            on_progress=on_progress,
            on_error=on_error,
        )

        # Export results if output directory provided
        if output_dir:
            await self._export_sct_results(result, output_dir)

        logger.info(
            "SCT extraction completed",
            successful=result.success_count,
            failed=result.failure_count,
            success_rate=f"{result.success_rate * 100:.1f}%",
        )

        return result

    async def extract_tax_data(
        self,
        companies: list[Dict[str, Any]],
        output_dir: Optional[Path] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None,
    ) -> BatchResult[TaxData]:
        """
        Extract Tax data from companies.

        Args:
            companies: List of company dicts with 'name', 'cik', 'rank'
            output_dir: Output directory for JSON/CSV files (optional)
            on_progress: Progress callback(current, total, company_name)
            on_error: Error callback(company_name, exception)

        Returns:
            BatchResult with Tax extraction results

        Example:
            >>> companies = [
            ...     {"name": "Apple Inc.", "cik": "0000320193", "rank": 3}
            ... ]
            >>> result = await service.extract_tax_data(
            ...     companies,
            ...     output_dir=Path("output/")
            ... )
        """
        logger.info(
            "Starting Tax extraction",
            company_count=len(companies),
        )

        # Create extraction tasks
        tasks = [
            CompanyTask(
                company_name=company["name"],
                cik=company["cik"],
                form_type="10-K",
                extractor_factory=lambda c=company: TaxAdapter(
                    company=c["name"], cik=c["cik"]
                ),
            )
            for company in companies
        ]

        # Process batch
        result = await self.batch_processor_tax.process_batch(
            tasks=tasks,
            on_progress=on_progress,
            on_error=on_error,
        )

        # Export results if output directory provided
        if output_dir:
            await self._export_tax_results(result, output_dir)

        logger.info(
            "Tax extraction completed",
            successful=result.success_count,
            failed=result.failure_count,
            success_rate=f"{result.success_rate * 100:.1f}%",
        )

        return result

    async def extract_all(
        self,
        companies: list[Dict[str, Any]],
        extract_sct: bool = True,
        extract_tax: bool = True,
        output_dir: Optional[Path] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None,
    ) -> Fortune100ExtractionResult:
        """
        Extract both SCT and Tax data from companies.

        Args:
            companies: List of company dicts with 'name', 'cik', 'rank'
            extract_sct: Extract SCT data (default: True)
            extract_tax: Extract Tax data (default: True)
            output_dir: Output directory for JSON/CSV files (optional)
            on_progress: Progress callback(current, total, company_name)
            on_error: Error callback(company_name, exception)

        Returns:
            Fortune100ExtractionResult with consolidated results

        Example:
            >>> companies = load_fortune100_companies()
            >>> result = await service.extract_all(
            ...     companies,
            ...     output_dir=Path("output/fortune100/")
            ... )
            >>> print(f"Total: {result.total_count}")
            >>> print(f"Success: {result.success_count}")
            >>> print(f"Failed: {result.failure_count}")
        """
        import time

        start_time = time.monotonic()

        logger.info(
            "Starting Fortune 100 extraction pipeline",
            company_count=len(companies),
            extract_sct=extract_sct,
            extract_tax=extract_tax,
        )

        sct_results = None
        tax_results = None
        output_files = []

        # Extract SCT data
        if extract_sct:
            sct_results = await self.extract_sct_data(
                companies=companies,
                output_dir=output_dir,
                on_progress=on_progress,
                on_error=on_error,
            )

        # Extract Tax data
        if extract_tax:
            tax_results = await self.extract_tax_data(
                companies=companies,
                output_dir=output_dir,
                on_progress=on_progress,
                on_error=on_error,
            )

        total_duration = time.monotonic() - start_time

        result = Fortune100ExtractionResult(
            sct_results=sct_results,
            tax_results=tax_results,
            total_duration=total_duration,
            output_files=output_files,
        )

        logger.info(
            "Fortune 100 extraction pipeline completed",
            total_duration=f"{total_duration:.2f}s",
            total_count=result.total_count,
            success_count=result.success_count,
            failure_count=result.failure_count,
        )

        return result

    async def _export_sct_results(
        self, result: BatchResult[SCTData], output_dir: Path
    ) -> None:
        """
        Export SCT results to JSON and CSV files.

        Args:
            result: SCT batch result
            output_dir: Output directory path
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export JSON
        json_path = output_dir / "sct_data.json"
        json_data = [r.data.model_dump() for r in result.successful if r.data]

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        logger.info("Exported SCT JSON", path=str(json_path), count=len(json_data))

        # Export CSV (flattened)
        csv_path = output_dir / "sct_data.csv"
        self._export_sct_csv(result.successful, csv_path)

        logger.info("Exported SCT CSV", path=str(csv_path))

    async def _export_tax_results(
        self, result: BatchResult[TaxData], output_dir: Path
    ) -> None:
        """
        Export Tax results to JSON and CSV files.

        Args:
            result: Tax batch result
            output_dir: Output directory path
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export JSON
        json_path = output_dir / "tax_data.json"
        json_data = [r.data.model_dump() for r in result.successful if r.data]

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        logger.info("Exported Tax JSON", path=str(json_path), count=len(json_data))

        # Export CSV (flattened)
        csv_path = output_dir / "tax_data.csv"
        self._export_tax_csv(result.successful, csv_path)

        logger.info("Exported Tax CSV", path=str(csv_path))

    def _export_sct_csv(
        self, results: List[ExtractionResult[SCTData]], csv_path: Path
    ) -> None:
        """
        Export SCT data to CSV format (flattened for analysis).

        Args:
            results: List of successful SCT extraction results
            csv_path: Output CSV file path
        """
        if not results:
            return

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Company",
                    "CIK",
                    "Filing Date",
                    "Executive Name",
                    "Title",
                    "Year",
                    "Salary",
                    "Bonus",
                    "Stock Awards",
                    "Option Awards",
                    "Non-Equity Incentive",
                    "Pension Change",
                    "Other Compensation",
                    "Total Compensation",
                ]
            )

            # Write data rows (one row per executive per year)
            for result in results:
                if not result.data:
                    continue

                data = result.data
                for exec in data.executives:
                    for comp in exec.compensation:
                        writer.writerow(
                            [
                                data.company,
                                data.cik,
                                data.filing_date,
                                exec.name,
                                exec.title,
                                comp.year,
                                comp.salary,
                                comp.bonus,
                                comp.stock_awards,
                                comp.option_awards,
                                comp.non_equity_incentive,
                                comp.pension_change,
                                comp.other_compensation,
                                comp.total,
                            ]
                        )

    def _export_tax_csv(
        self, results: List[ExtractionResult[TaxData]], csv_path: Path
    ) -> None:
        """
        Export Tax data to CSV format (flattened for analysis).

        Args:
            results: List of successful Tax extraction results
            csv_path: Output CSV file path
        """
        if not results:
            return

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Company",
                    "CIK",
                    "Fiscal Year End",
                    "Year",
                    "Income Before Tax",
                    "Tax Expense",
                    "Effective Tax Rate",
                    "Deferred Tax Assets",
                    "Deferred Tax Liabilities",
                ]
            )

            # Write data rows (one row per year)
            for result in results:
                if not result.data:
                    continue

                data = result.data
                for tax_year in data.tax_years:
                    writer.writerow(
                        [
                            data.company,
                            data.cik,
                            data.fiscal_year_end,
                            tax_year.year,
                            tax_year.income_before_tax,
                            tax_year.tax_expense,
                            tax_year.effective_tax_rate,
                            tax_year.deferred_tax_assets,
                            tax_year.deferred_tax_liabilities,
                        ]
                    )
