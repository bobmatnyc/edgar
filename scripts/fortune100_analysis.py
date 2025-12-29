#!/usr/bin/env python3
"""Fortune 100 Executive Compensation vs. Corporate Tax Analysis Pipeline.

This script orchestrates the complete analysis workflow:
1. Load Fortune 100 company registry
2. Batch fetch DEF 14A filings and extract executive compensation
3. Batch fetch 10-K filings and extract corporate tax data
4. Export results to JSON and CSV for analysis

Usage:
    python scripts/fortune100_analysis.py                    # Full pipeline
    python scripts/fortune100_analysis.py --companies 1-10   # Top 10 only
    python scripts/fortune100_analysis.py --year 2024        # Specific year
    python scripts/fortune100_analysis.py -v                 # Verbose output
"""

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar.data.fortune100 import Fortune100Registry, Company
from edgar.services.sec_edgar_client import SecEdgarClient
from edgar.services.batch_processor import BatchProcessor, BatchResult, RateLimiter
from edgar.extractors.sct import SCTExtractor
from edgar.extractors.sct.models import SCTData
from edgar.extractors.tax import TaxExtractor
from edgar.extractors.tax.models import TaxData
from edgar.exporters.csv_exporter import CSVExporter


@dataclass
class PipelineConfig:
    """Configuration for the analysis pipeline."""

    companies_range: tuple[int, int] = (1, 100)  # Default: all Fortune 100
    fiscal_year: int | None = None  # Default: most recent
    output_dir: Path = Path("output/fortune100")
    verbose: bool = False
    max_concurrent: int = 5
    skip_def14a: bool = False  # Skip executive compensation
    skip_10k: bool = False  # Skip tax data


@dataclass
class PipelineResult:
    """Result of the complete pipeline run."""

    success: bool
    total_duration: float
    companies_processed: int
    def14a_results: BatchResult[SCTData] | None
    form10k_results: BatchResult[TaxData] | None
    output_files: list[Path]
    errors: list[str]


class Fortune100Pipeline:
    """Main pipeline orchestrator for Fortune 100 analysis."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.registry = Fortune100Registry.load_default()
        self.sec_client = SecEdgarClient()
        self.rate_limiter = RateLimiter(requests_per_second=8.0)
        self.exporter = CSVExporter(output_dir=config.output_dir)

    async def run(self) -> PipelineResult:
        """Execute the complete pipeline."""
        start_time = time.monotonic()
        errors: list[str] = []
        output_files: list[Path] = []

        # Phase 1: Load companies
        self._log("Phase 1: Loading Companies")
        companies = self._load_companies()
        self._log(f"  Loaded {len(companies)} companies (ranks {self.config.companies_range[0]}-{self.config.companies_range[1]})")

        # Phase 2: Fetch and extract DEF 14A (exec compensation)
        def14a_results = None
        if not self.config.skip_def14a:
            self._log("Phase 2: Fetching DEF 14A filings (Executive Compensation)")
            def14a_results = await self._process_def14a(companies)
            self._log(f"  Success: {def14a_results.success_count}/{len(companies)}")
            if def14a_results.failure_count > 0:
                self._log(f"  Failed: {def14a_results.failure_count} companies")
                for failed in def14a_results.failed[:3]:  # Show first 3 failures
                    self._log(f"    - {failed.company.name}: {failed.error}")
        else:
            self._log("Phase 2: Skipping DEF 14A extraction (--skip-def14a)")

        # Phase 3: Fetch and extract 10-K (tax data)
        form10k_results = None
        if not self.config.skip_10k:
            self._log("Phase 3: Fetching 10-K filings (Corporate Tax)")
            form10k_results = await self._process_10k(companies)
            self._log(f"  Success: {form10k_results.success_count}/{len(companies)}")
            if form10k_results.failure_count > 0:
                self._log(f"  Failed: {form10k_results.failure_count} companies")
                for failed in form10k_results.failed[:3]:  # Show first 3 failures
                    self._log(f"    - {failed.company.name}: {failed.error}")
        else:
            self._log("Phase 3: Skipping 10-K extraction (--skip-10k)")

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
            # Export CSV
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
                "total_companies": len(def14a_results.successful) + len(def14a_results.failed),
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
            # Export CSV
            tax_tuples = [
                (result.company, result.data)
                for result in form10k_results.successful
                if result.data is not None
            ]
            if tax_tuples:
                csv_path = self.exporter.export_tax(tax_tuples, filename="corporate_tax.csv")
                output_files.append(csv_path)

            # Export JSON summary
            form10k_summary = {
                "total_companies": len(form10k_results.successful) + len(form10k_results.failed),
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
                        set(c.cik for c, _ in comp_tuples) & set(c.cik for c, _ in tax_tuples)
                    ),
                    "def14a_success_rate": def14a_results.success_rate,
                    "form10k_success_rate": form10k_results.success_rate,
                    "total_duration": def14a_results.total_duration + form10k_results.total_duration,
                }
                json_path = self.config.output_dir / "analysis_summary.json"
                with open(json_path, "w") as f:
                    json.dump(analysis_summary, f, indent=2)
                output_files.append(json_path)

        return output_files

    def _progress_callback(self, current: int, total: int, company: str) -> None:
        """Print progress updates."""
        print(f"  [{current}/{total}] {company}")

    def _log(self, message: str) -> None:
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")


def parse_args() -> PipelineConfig:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fortune 100 Executive Compensation vs. Corporate Tax Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline (all 100 companies)
  python scripts/fortune100_analysis.py

  # Top 10 companies only (for testing)
  python scripts/fortune100_analysis.py --companies 1-10

  # Specific fiscal year
  python scripts/fortune100_analysis.py --year 2024

  # Verbose output
  python scripts/fortune100_analysis.py -v

  # Custom output directory
  python scripts/fortune100_analysis.py --output ./analysis_results

  # Combined options
  python scripts/fortune100_analysis.py -c 1-20 -y 2024 -v -o ./output/top20
        """,
    )
    parser.add_argument(
        "--companies",
        "-c",
        type=str,
        default="1-100",
        help="Company rank range, e.g., '1-10' for top 10 (default: 1-100)",
    )
    parser.add_argument(
        "--year",
        "-y",
        type=int,
        default=None,
        help="Specific fiscal year to analyze (default: most recent)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("output/fortune100"),
        help="Output directory (default: output/fortune100)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=5,
        help="Max concurrent requests (default: 5)",
    )
    parser.add_argument(
        "--skip-def14a",
        action="store_true",
        help="Skip DEF 14A (executive compensation) extraction",
    )
    parser.add_argument(
        "--skip-10k",
        action="store_true",
        help="Skip 10-K (corporate tax) extraction",
    )

    args = parser.parse_args()

    # Parse company range
    try:
        start, end = map(int, args.companies.split("-"))
        if not (1 <= start <= 100 and 1 <= end <= 100):
            parser.error("Company ranks must be between 1 and 100")
        if start > end:
            parser.error(f"Start rank {start} must be <= end rank {end}")
    except ValueError:
        parser.error(f"Invalid company range format: {args.companies} (expected 'start-end')")

    return PipelineConfig(
        companies_range=(start, end),
        fiscal_year=args.year,
        output_dir=args.output,
        verbose=args.verbose,
        max_concurrent=args.concurrent,
        skip_def14a=args.skip_def14a,
        skip_10k=args.skip_10k,
    )


async def main() -> int:
    """Main entry point."""
    config = parse_args()
    pipeline = Fortune100Pipeline(config)

    print("=" * 60)
    print("Fortune 100 Executive Compensation vs. Corporate Tax Analysis")
    print("=" * 60)
    print(f"Companies: Ranks {config.companies_range[0]}-{config.companies_range[1]}")
    print(f"Output: {config.output_dir}")
    if config.fiscal_year:
        print(f"Fiscal Year: {config.fiscal_year}")
    print()

    result = await pipeline.run()

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Duration: {result.total_duration:.1f}s")
    print(f"Companies: {result.companies_processed}")

    if result.def14a_results:
        print(
            f"DEF 14A: {result.def14a_results.success_count} succeeded, "
            f"{result.def14a_results.failure_count} failed "
            f"({result.def14a_results.success_rate:.1%} success rate)"
        )

    if result.form10k_results:
        print(
            f"10-K: {result.form10k_results.success_count} succeeded, "
            f"{result.form10k_results.failure_count} failed "
            f"({result.form10k_results.success_rate:.1%} success rate)"
        )

    print(f"\nOutput Files ({len(result.output_files)}):")
    for path in result.output_files:
        print(f"  - {path}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
