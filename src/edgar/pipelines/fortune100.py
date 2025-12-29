"""Fortune 100 Executive Compensation vs. Corporate Tax Analysis Pipeline.

Core pipeline logic for extracting and analyzing Fortune 100 company data.
This module is designed to be used by:
- CLI: `edgar fortune100` command
- Notebooks: Interactive exploration
- Streamlit: (future) Dashboard interface

Example:
    >>> from edgar.pipelines import Fortune100Pipeline, PipelineConfig
    >>> config = PipelineConfig(companies_range=(1, 10))
    >>> pipeline = Fortune100Pipeline(config)
    >>> result = await pipeline.run()
    >>> print(f"Success rate: {result.def14a_results.success_rate:.1%}")
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from edgar.data.fortune100 import Company, Fortune100Registry
from edgar.exporters.csv_exporter import CSVExporter
from edgar.extractors.sct import SCTExtractor
from edgar.extractors.sct.models import SCTData
from edgar.extractors.tax import TaxExtractor
from edgar.extractors.tax.models import TaxData
from edgar.services.batch_processor import BatchProcessor, BatchResult, RateLimiter
from edgar.services.sec_edgar_client import SecEdgarClient


@dataclass
class PipelineConfig:
    """Configuration for the Fortune 100 analysis pipeline.

    Attributes:
        companies_range: Tuple of (start_rank, end_rank) for companies to process.
            Default is (1, 100) for all Fortune 100.
        fiscal_year: Specific fiscal year to analyze. None for most recent.
        output_dir: Directory for output files.
        verbose: Enable verbose logging.
        max_concurrent: Maximum concurrent SEC API requests.
        skip_def14a: Skip executive compensation extraction.
        skip_10k: Skip corporate tax extraction.
        log_callback: Optional callback for log messages.
    """

    companies_range: tuple[int, int] = (1, 100)
    fiscal_year: int | None = None
    output_dir: Path = field(default_factory=lambda: Path("output/fortune100"))
    verbose: bool = False
    max_concurrent: int = 5
    skip_def14a: bool = False
    skip_10k: bool = False
    log_callback: Callable[[str], None] | None = None


@dataclass
class PipelineResult:
    """Result of a complete pipeline run.

    Attributes:
        success: Whether the pipeline completed without critical errors.
        total_duration: Total execution time in seconds.
        companies_processed: Number of companies processed.
        def14a_results: Results from DEF 14A extraction (executive compensation).
        form10k_results: Results from 10-K extraction (corporate tax).
        output_files: List of generated output files.
        errors: List of error messages.
    """

    success: bool
    total_duration: float
    companies_processed: int
    def14a_results: BatchResult[SCTData] | None
    form10k_results: BatchResult[TaxData] | None
    output_files: list[Path]
    errors: list[str]

    @property
    def def14a_success_rate(self) -> float:
        """DEF 14A extraction success rate."""
        if self.def14a_results:
            return self.def14a_results.success_rate
        return 0.0

    @property
    def form10k_success_rate(self) -> float:
        """10-K extraction success rate."""
        if self.form10k_results:
            return self.form10k_results.success_rate
        return 0.0


class Fortune100Pipeline:
    """Main pipeline orchestrator for Fortune 100 analysis.

    This class orchestrates the complete analysis workflow:
    1. Load Fortune 100 company registry
    2. Batch fetch DEF 14A filings and extract executive compensation
    3. Batch fetch 10-K filings and extract corporate tax data
    4. Export results to JSON and CSV

    Example:
        >>> config = PipelineConfig(companies_range=(1, 10), verbose=True)
        >>> pipeline = Fortune100Pipeline(config)
        >>> result = await pipeline.run()
        >>> for path in result.output_files:
        ...     print(f"Generated: {path}")
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        """Initialize the pipeline.

        Args:
            config: Pipeline configuration. Uses defaults if not provided.
        """
        self.config = config or PipelineConfig()
        self.registry = Fortune100Registry.load_default()
        self.sec_client = SecEdgarClient()
        self.rate_limiter = RateLimiter(requests_per_second=8.0)
        self.exporter = CSVExporter(output_dir=self.config.output_dir)

    async def run(self) -> PipelineResult:
        """Execute the complete pipeline.

        Returns:
            PipelineResult with extraction results and output files.
        """
        start_time = time.monotonic()
        errors: list[str] = []
        output_files: list[Path] = []

        # Phase 1: Load companies
        self._log("Phase 1: Loading Companies")
        companies = self._load_companies()
        self._log(
            f"  Loaded {len(companies)} companies "
            f"(ranks {self.config.companies_range[0]}-{self.config.companies_range[1]})"
        )

        # Phase 2: Fetch and extract DEF 14A (exec compensation)
        def14a_results = None
        if not self.config.skip_def14a:
            self._log("Phase 2: Fetching DEF 14A filings (Executive Compensation)")
            def14a_results = await self._process_def14a(companies)
            self._log(f"  Success: {def14a_results.success_count}/{len(companies)}")
            if def14a_results.failure_count > 0:
                self._log(f"  Failed: {def14a_results.failure_count} companies")
                for failed in def14a_results.failed[:3]:
                    self._log(f"    - {failed.company.name}: {failed.error}")
        else:
            self._log("Phase 2: Skipping DEF 14A extraction")

        # Phase 3: Fetch and extract 10-K (tax data)
        form10k_results = None
        if not self.config.skip_10k:
            self._log("Phase 3: Fetching 10-K filings (Corporate Tax)")
            form10k_results = await self._process_10k(companies)
            self._log(f"  Success: {form10k_results.success_count}/{len(companies)}")
            if form10k_results.failure_count > 0:
                self._log(f"  Failed: {form10k_results.failure_count} companies")
                for failed in form10k_results.failed[:3]:
                    self._log(f"    - {failed.company.name}: {failed.error}")
        else:
            self._log("Phase 3: Skipping 10-K extraction")

        # Phase 4: Export results
        self._log("Phase 4: Exporting Results")
        output_files = self._export_results(def14a_results, form10k_results)
        self._log(f"  Exported {len(output_files)} files")

        duration = time.monotonic() - start_time

        return PipelineResult(
            success=len(errors) == 0,
            total_duration=duration,
            companies_processed=len(companies),
            def14a_results=def14a_results,
            form10k_results=form10k_results,
            output_files=output_files,
            errors=errors,
        )

    def get_companies(self) -> list[Company]:
        """Get companies based on config range.

        Useful for notebooks to inspect companies before running pipeline.
        """
        return self._load_companies()

    def _load_companies(self) -> list[Company]:
        """Load companies based on config range."""
        start, end = self.config.companies_range
        return self.registry.get_by_rank_range(start, end)

    async def _process_def14a(self, companies: list[Company]) -> BatchResult[SCTData]:
        """Batch process DEF 14A filings."""
        processor: BatchProcessor[SCTData] = BatchProcessor(
            sec_client=self.sec_client,
            rate_limiter=self.rate_limiter,
            max_concurrent=self.config.max_concurrent,
        )
        return await processor.process_companies(
            companies=companies,
            extractor_factory=lambda c: SCTExtractor(company=c.name, cik=c.cik),
            form_type="DEF 14A",
            on_progress=self._progress_callback if self.config.verbose else None,
        )

    async def _process_10k(self, companies: list[Company]) -> BatchResult[TaxData]:
        """Batch process 10-K filings."""
        processor: BatchProcessor[TaxData] = BatchProcessor(
            sec_client=self.sec_client,
            rate_limiter=self.rate_limiter,
            max_concurrent=self.config.max_concurrent,
        )
        return await processor.process_companies(
            companies=companies,
            extractor_factory=lambda c: TaxExtractor(company=c.name, cik=c.cik),
            form_type="10-K",
            on_progress=self._progress_callback if self.config.verbose else None,
        )

    def _export_results(
        self,
        def14a_results: BatchResult[SCTData] | None,
        form10k_results: BatchResult[TaxData] | None,
    ) -> list[Path]:
        """Export all results to JSON and CSV."""
        output_files: list[Path] = []

        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Export DEF 14A results
        if def14a_results:
            comp_tuples = [
                (result.company, result.data)
                for result in def14a_results.successful
                if result.data is not None
            ]
            if comp_tuples:
                csv_path = self.exporter.export_compensation(
                    comp_tuples, filename="executive_compensation.csv"
                )
                output_files.append(csv_path)

            # Export JSON summary
            def14a_summary = {
                "total_companies": len(def14a_results.successful)
                + len(def14a_results.failed),
                "successful": len(def14a_results.successful),
                "failed": len(def14a_results.failed),
                "success_rate": def14a_results.success_rate,
                "total_duration": def14a_results.total_duration,
                "requests_made": def14a_results.requests_made,
                "failures": [
                    {
                        "company": f.company.name,
                        "rank": f.company.rank,
                        "error": f.error,
                    }
                    for f in def14a_results.failed
                ],
            }
            json_path = self.config.output_dir / "def14a_results.json"
            with open(json_path, "w") as f:
                json.dump(def14a_summary, f, indent=2)
            output_files.append(json_path)

        # Export 10-K results
        if form10k_results:
            tax_tuples = [
                (result.company, result.data)
                for result in form10k_results.successful
                if result.data is not None
            ]
            if tax_tuples:
                csv_path = self.exporter.export_tax(
                    tax_tuples, filename="corporate_tax.csv"
                )
                output_files.append(csv_path)

            # Export JSON summary
            form10k_summary = {
                "total_companies": len(form10k_results.successful)
                + len(form10k_results.failed),
                "successful": len(form10k_results.successful),
                "failed": len(form10k_results.failed),
                "success_rate": form10k_results.success_rate,
                "total_duration": form10k_results.total_duration,
                "requests_made": form10k_results.requests_made,
                "failures": [
                    {
                        "company": f.company.name,
                        "rank": f.company.rank,
                        "error": f.error,
                    }
                    for f in form10k_results.failed
                ],
            }
            json_path = self.config.output_dir / "10k_results.json"
            with open(json_path, "w") as f:
                json.dump(form10k_summary, f, indent=2)
            output_files.append(json_path)

        # Export combined analysis if both datasets available
        if def14a_results and form10k_results:
            comp_tuples = [
                (result.company, result.data)
                for result in def14a_results.successful
                if result.data is not None
            ]
            tax_tuples = [
                (result.company, result.data)
                for result in form10k_results.successful
                if result.data is not None
            ]
            if comp_tuples and tax_tuples:
                csv_path = self.exporter.export_combined(
                    comp_tuples, tax_tuples, filename="compensation_vs_tax.csv"
                )
                output_files.append(csv_path)

                # Create analysis summary
                analysis_summary = {
                    "timestamp": datetime.now().isoformat(),
                    "companies_analyzed": len(
                        set(c.cik for c, _ in comp_tuples)
                        & set(c.cik for c, _ in tax_tuples)
                    ),
                    "def14a_success_rate": def14a_results.success_rate,
                    "form10k_success_rate": form10k_results.success_rate,
                    "total_duration": def14a_results.total_duration
                    + form10k_results.total_duration,
                }
                json_path = self.config.output_dir / "analysis_summary.json"
                with open(json_path, "w") as f:
                    json.dump(analysis_summary, f, indent=2)
                output_files.append(json_path)

        return output_files

    def _progress_callback(self, current: int, total: int, company: str) -> None:
        """Print progress updates."""
        self._log(f"  [{current}/{total}] {company}")

    def _log(self, message: str) -> None:
        """Log message with optional callback."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"

        if self.config.log_callback:
            self.config.log_callback(full_message)
        elif self.config.verbose:
            print(full_message)
