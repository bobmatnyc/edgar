"""
Example: Fetching SEC filings using the standalone edgar_api module.

This example demonstrates how to use the fetch_company_filings function
for recipe scripts without requiring DI setup.
"""

import asyncio

from edgar_analyzer.data_sources import fetch_company_filings


async def example_10k_filings():
    """Fetch 10-K annual reports for companies."""
    companies = [
        {"cik": "0000320193", "name": "Apple Inc.", "ticker": "AAPL"},
        {"cik": "0001018724", "name": "Amazon.com Inc.", "ticker": "AMZN"},
        {"cik": "0001652044", "name": "Alphabet Inc.", "ticker": "GOOGL"},
    ]

    print("Fetching 10-K filings for 2023...")
    filings = await fetch_company_filings(
        companies=companies,
        filing_type="10-K",
        year=2023,
        email="your-email@example.com",  # Required by SEC
    )

    print(f"\nResults: {len(filings)} filings")
    for filing in filings:
        print(f"\n{filing['company']}:")
        print(f"  Filing Date: {filing['filing_date']}")
        print(f"  Accession: {filing['accession_number']}")

        if filing.get("error"):
            print(f"  Error: {filing['error']}")
        else:
            html_len = len(filing.get("html", "")) if filing.get("html") else 0
            print(f"  HTML Size: {html_len:,} characters")


async def example_def14a_filings():
    """Fetch DEF 14A proxy statements for companies."""
    companies = [
        {"cik": "0000320193", "name": "Apple Inc.", "ticker": "AAPL"},
        {"cik": "0001018724", "name": "Amazon.com Inc.", "ticker": "AMZN"},
    ]

    print("\nFetching DEF 14A filings for 2023...")
    filings = await fetch_company_filings(
        companies=companies,
        filing_type="DEF 14A",
        year=2023,
        email="your-email@example.com",
    )

    print(f"\nResults: {len(filings)} filings")
    for filing in filings:
        if not filing.get("error"):
            print(f"\n{filing['company']}: {filing['filing_date']}")


async def example_error_handling():
    """Demonstrate error handling for missing filings."""
    companies = [
        {"cik": "0000320193", "name": "Apple Inc.", "ticker": "AAPL"},
        {"cik": "9999999999", "name": "Invalid Company", "ticker": "XXX"},
    ]

    print("\nFetching filings (with intentional error)...")
    filings = await fetch_company_filings(
        companies=companies,
        filing_type="10-K",
        year=2023,
        email="your-email@example.com",
    )

    # Errors are captured in the result dict, not raised
    for filing in filings:
        if filing.get("error"):
            print(f"\n{filing['company']}: ERROR - {filing['error']}")
        else:
            print(f"\n{filing['company']}: SUCCESS")


async def main():
    """Run all examples."""
    await example_10k_filings()
    await example_def14a_filings()
    await example_error_handling()


if __name__ == "__main__":
    asyncio.run(main())
