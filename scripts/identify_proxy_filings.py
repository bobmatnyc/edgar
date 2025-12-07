#!/usr/bin/env python3
"""
Identify and locate DEF 14A (proxy statement) filings for Fortune 100 companies.

This script:
1. Loads Fortune 100 2024 dataset
2. For each company with a CIK, queries SEC EDGAR submissions API
3. Finds the most recent DEF 14A or DEF 14A/A filing
4. Extracts filing metadata (date, accession number, document URL)
5. Outputs JSON file with proxy filing metadata

POC 2: Proxy Filing Identification
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ]
)
logger = structlog.get_logger(__name__)


class ProxyFilingIdentifier:
    """Identifies DEF 14A proxy filings for Fortune 100 companies."""

    def __init__(
        self,
        user_agent: str = "ProxyFilingIdentifier/1.0 (edgar-analyzer-poc)",
        rate_limit_delay: float = 0.11,  # 10 requests/second = 0.1s, use 0.11 to be safe
    ):
        """Initialize the proxy filing identifier.

        Args:
            user_agent: User agent string for SEC EDGAR API
            rate_limit_delay: Delay between requests in seconds (SEC allows 10/sec)
        """
        self.user_agent = user_agent
        self.rate_limit_delay = rate_limit_delay
        self.base_url = "https://data.sec.gov"
        self._last_request_time = 0.0
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper headers."""
        if self._session is None or self._session.closed:
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov",
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._session

    async def _rate_limit(self) -> None:
        """Enforce SEC EDGAR rate limiting (10 requests/second)."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)

        self._last_request_time = time.time()

    async def _fetch_submissions(self, cik: str) -> Optional[Dict]:
        """Fetch company submissions from SEC EDGAR API.

        Args:
            cik: 10-digit zero-padded CIK number

        Returns:
            Submissions data dict or None if request fails
        """
        await self._rate_limit()

        url = f"{self.base_url}/submissions/CIK{cik}.json"
        session = await self._get_session()

        try:
            logger.debug("Fetching submissions", cik=cik, url=url)
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                logger.info("Submissions fetched", cik=cik, status=response.status)
                return data

        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning("Company not found", cik=cik, status=404)
            else:
                logger.error("API request failed", cik=cik, status=e.status, error=str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error fetching submissions", cik=cik, error=str(e))
            return None

    def _find_latest_proxy_filing(self, submissions: Dict) -> Optional[Dict]:
        """Find the most recent DEF 14A filing from submissions data.

        Args:
            submissions: Company submissions data from SEC EDGAR

        Returns:
            Filing metadata dict or None if no proxy filing found
        """
        # Check recent filings first
        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])

        # Find first DEF 14A or DEF 14A/A
        for i, form in enumerate(forms):
            if form in ("DEF 14A", "DEF 14A/A"):
                return {
                    "filing_type": form,
                    "filing_date": filing_dates[i],
                    "accession_number": accession_numbers[i],
                    "primary_document": primary_documents[i],
                }

        # If not found in recent, check older filings (files array)
        files = submissions.get("filings", {}).get("files", [])
        for file_info in files:
            file_name = file_info.get("name", "")
            # The files array contains references to additional filing data
            # For now, we'll just return None if not found in recent
            # Full implementation would fetch these additional files
            pass

        return None

    def _build_filing_url(self, cik: str, accession_number: str, primary_document: str) -> str:
        """Build the SEC EDGAR filing URL.

        Args:
            cik: 10-digit zero-padded CIK
            accession_number: Filing accession number (with dashes)
            primary_document: Primary document filename

        Returns:
            Full URL to the filing document
        """
        # Remove dashes from accession number for URL path
        accession_no_dashes = accession_number.replace("-", "")
        # Remove leading zeros from CIK for URL (SEC uses non-padded CIK in URLs)
        cik_unpadded = str(int(cik))

        return (
            f"https://www.sec.gov/Archives/edgar/data/{cik_unpadded}/"
            f"{accession_no_dashes}/{primary_document}"
        )

    async def identify_proxy_filing(
        self, cik: str, company_name: str, ticker: Optional[str]
    ) -> Optional[Dict]:
        """Identify the most recent proxy filing for a company.

        Args:
            cik: 10-digit zero-padded CIK number
            company_name: Company name
            ticker: Stock ticker symbol (may be None for private companies)

        Returns:
            Filing metadata dict or None if no filing found
        """
        logger.info("Processing company", company=company_name, cik=cik, ticker=ticker)

        # Fetch submissions
        submissions = await self._fetch_submissions(cik)
        if not submissions:
            logger.warning("No submissions data", company=company_name)
            return None

        # Find latest proxy filing
        filing_info = self._find_latest_proxy_filing(submissions)
        if not filing_info:
            logger.warning("No proxy filing found", company=company_name)
            return None

        # Build complete metadata
        filing_url = self._build_filing_url(
            cik, filing_info["accession_number"], filing_info["primary_document"]
        )

        result = {
            "cik": cik,
            "company_name": company_name,
            "ticker": ticker,
            "filing_type": filing_info["filing_type"],
            "filing_date": filing_info["filing_date"],
            "accession_number": filing_info["accession_number"],
            "primary_document": filing_info["primary_document"],
            "filing_url": filing_url,
        }

        logger.info(
            "Proxy filing found",
            company=company_name,
            filing_date=filing_info["filing_date"],
            filing_type=filing_info["filing_type"],
        )
        return result

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("HTTP session closed")


async def main():
    """Main execution function."""
    # File paths
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "companies" / "fortune_100_2024.json"
    output_file = project_root / "data" / "filings" / "fortune_100_proxy_filings_2024.json"

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting proxy filing identification", input_file=str(input_file))

    # Load Fortune 100 data
    with open(input_file, "r") as f:
        fortune_data = json.load(f)

    companies = fortune_data["companies"]
    total_companies = len(companies)
    logger.info("Loaded company data", total_companies=total_companies)

    # Initialize identifier
    identifier = ProxyFilingIdentifier()

    # Process each company
    filings = []
    companies_without_cik = []
    companies_without_filing = []

    try:
        for i, company in enumerate(companies, 1):
            company_name = company["name"]
            cik = company.get("cik")
            ticker = company.get("ticker")

            logger.info(
                "Processing",
                progress=f"{i}/{total_companies}",
                company=company_name,
                cik=cik,
            )

            # Skip companies without CIK
            if not cik:
                logger.warning("No CIK available", company=company_name)
                companies_without_cik.append(company_name)
                continue

            # Identify proxy filing
            filing_info = await identifier.identify_proxy_filing(cik, company_name, ticker)

            if filing_info:
                filings.append(filing_info)
            else:
                companies_without_filing.append(company_name)

            # Progress indicator every 10 companies
            if i % 10 == 0:
                logger.info(
                    "Progress update",
                    processed=i,
                    total=total_companies,
                    filings_found=len(filings),
                )

    finally:
        await identifier.close()

    # Prepare output
    output_data = {
        "metadata": {
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
            "total_companies": total_companies,
            "companies_with_ciks": total_companies - len(companies_without_cik),
            "companies_without_ciks": len(companies_without_cik),
            "filings_found": len(filings),
            "companies_without_filings": len(companies_without_filing),
        },
        "filings": filings,
        "companies_without_cik": companies_without_cik,
        "companies_without_filing": companies_without_filing,
    }

    # Write output
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(
        "Proxy filing identification complete",
        output_file=str(output_file),
        filings_found=len(filings),
        companies_without_cik=len(companies_without_cik),
        companies_without_filing=len(companies_without_filing),
    )

    # Print summary
    print("\n" + "=" * 80)
    print("PROXY FILING IDENTIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total Companies:              {total_companies}")
    print(f"Companies with CIKs:          {total_companies - len(companies_without_cik)}")
    print(f"Companies without CIKs:       {len(companies_without_cik)}")
    print(f"Proxy Filings Found:          {len(filings)}")
    print(f"Companies without Filings:    {len(companies_without_filing)}")
    print(f"\nOutput File: {output_file}")
    print("=" * 80)

    if companies_without_cik:
        print("\nCompanies without CIK:")
        for company in companies_without_cik:
            print(f"  - {company}")

    if companies_without_filing:
        print("\nCompanies without proxy filings:")
        for company in companies_without_filing:
            print(f"  - {company}")

    # Show sample of first 10 filings
    if filings:
        print("\n" + "=" * 80)
        print("SAMPLE FILINGS (First 10):")
        print("=" * 80)
        for filing in filings[:10]:
            print(f"\n{filing['company_name']} ({filing['ticker']})")
            print(f"  Filing Type:      {filing['filing_type']}")
            print(f"  Filing Date:      {filing['filing_date']}")
            print(f"  Accession Number: {filing['accession_number']}")
            print(f"  URL:              {filing['filing_url']}")


if __name__ == "__main__":
    asyncio.run(main())
