"""Batch processing demonstration for Fortune 100 companies.

This example shows how to use the BatchProcessor to efficiently process
multiple companies while respecting SEC EDGAR API rate limits.

Usage:
    uv run python examples/batch_processing_demo.py
"""

import asyncio
from typing import Any

from edgar.data.fortune100 import Fortune100Registry
from edgar.extractors.sct.extractor import SCTExtractor
from edgar.services.batch_processor import BatchProcessor
from edgar.services.sec_edgar_client import SecEdgarClient


async def main() -> None:
    """Run batch processing demo."""
    print("=" * 80)
    print("EDGAR Batch Processor Demo")
    print("=" * 80)
    print()

    # Load Fortune 100 registry
    print("Loading Fortune 100 companies...")
    registry = Fortune100Registry.load_default()

    # Select companies to process (top 5 for demo)
    companies = registry.get_by_rank_range(1, 5)
    print(f"Selected {len(companies)} companies for processing:")
    for company in companies:
        print(f"  {company.rank}. {company.name} ({company.ticker})")
    print()

    # Create SEC EDGAR client
    sec_client = SecEdgarClient()

    # Create batch processor with rate limiting
    processor = BatchProcessor(
        sec_client=sec_client,
        max_concurrent=3,  # Process 3 companies at a time
        max_retries=2,  # Retry failed requests twice
    )

    # Progress callback
    def on_progress(current: int, total: int, company_name: str) -> None:
        percent = (current / total) * 100
        print(f"Progress: [{current}/{total}] ({percent:.0f}%) - Processing {company_name}")

    # Error callback
    def on_error(company: Any, exception: Exception) -> None:
        print(f"❌ Error processing {company.name}: {exception}")

    # Process companies
    print("Starting batch processing...")
    print(f"Rate limit: {processor.rate_limiter.requests_per_second} requests/second")
    print(f"Max concurrent: {processor.max_concurrent}")
    print()

    result = await processor.process_companies(
        companies=companies,
        extractor_factory=lambda c: SCTExtractor(company=c.name, cik=c.cik),
        form_type="DEF 14A",
        on_progress=on_progress,
        on_error=on_error,
    )

    # Print results
    print()
    print("=" * 80)
    print("Batch Processing Results")
    print("=" * 80)
    print(f"Total Companies: {len(companies)}")
    print(f"Successful: {result.success_count}")
    print(f"Failed: {result.failure_count}")
    print(f"Success Rate: {result.success_rate:.1%}")
    print(f"Total Duration: {result.total_duration:.2f} seconds")
    print(f"Requests Made: {result.requests_made}")
    print(f"Average Time per Company: {result.total_duration / len(companies):.2f}s")
    print()

    # Show successful extractions
    if result.successful:
        print("Successful Extractions:")
        for extraction in result.successful:
            print(f"\n  Company: {extraction.company.name}")
            print(f"  Form Type: {extraction.form_type}")
            print(f"  Filing Date: {extraction.filing_date}")
            print(f"  Extraction Time: {extraction.extraction_time:.2f}s")
            if extraction.data:
                print(f"  Executives Found: {len(extraction.data.executives)}")
                for exec_data in extraction.data.executives[:3]:  # Show first 3
                    print(f"    - {exec_data.name} ({exec_data.title})")
                    if exec_data.compensation:
                        latest = exec_data.compensation[0]
                        print(f"      {latest.year}: ${latest.total:,.0f} total compensation")

    # Show failed extractions
    if result.failed:
        print("\nFailed Extractions:")
        for extraction in result.failed:
            print(f"  - {extraction.company.name}: {extraction.error}")

    print()
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
