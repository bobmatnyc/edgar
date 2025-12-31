"""
Standalone SEC EDGAR API client for recipe system.

This module provides a simple, DI-free interface for fetching company filings
from the SEC EDGAR database. It's designed for use in recipe scripts that don't
require the full service-oriented architecture.

Rate limiting: 8 requests/second (SEC allows 10/sec, we use 8 for safety)
User-Agent: Required by SEC, includes email for compliance
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)

# SEC API Configuration
SEC_BASE_URL = "https://data.sec.gov"
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
RATE_LIMIT_DELAY = 0.125  # 8 requests/second (1/8 = 0.125)
REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
USER_AGENT = "EdgarAnalyzer/0.2.2 (contact@example.com)"


class SecRateLimiter:
    """Simple rate limiter for SEC API requests."""

    def __init__(self, delay: float = RATE_LIMIT_DELAY):
        """Initialize rate limiter.

        Args:
            delay: Minimum delay between requests in seconds
        """
        self._delay = delay
        self._last_request_time = 0.0

    async def wait(self) -> None:
        """Wait if necessary to enforce rate limit."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._delay:
            sleep_time = self._delay - time_since_last
            await asyncio.sleep(sleep_time)

        self._last_request_time = time.time()


async def fetch_company_filings(
    companies: list[dict[str, Any]],
    filing_type: str,
    year: int = 2023,
    email: str = "contact@example.com",
) -> list[dict[str, Any]]:
    """
    Fetch SEC filings for a list of companies.

    Args:
        companies: List of company dicts with 'cik', 'name', 'ticker'
        filing_type: Filing type to fetch ("DEF 14A" or "10-K")
        year: Target fiscal year
        email: Contact email for SEC User-Agent (required)

    Returns:
        List of filing dicts with:
        - cik: Company CIK
        - company: Company name
        - filing_type: Filing type
        - filing_date: Filing date (YYYY-MM-DD)
        - accession_number: SEC accession number
        - html: Filing HTML content (or error message)
        - error: Error message if fetch failed (optional)

    Example:
        companies = [
            {"cik": "0000320193", "name": "Apple Inc.", "ticker": "AAPL"},
            {"cik": "0001018724", "name": "Amazon.com Inc.", "ticker": "AMZN"},
        ]
        filings = await fetch_company_filings(companies, "10-K", 2023)
    """
    rate_limiter = SecRateLimiter()
    user_agent = f"EdgarAnalyzer/0.2.2 ({email})"

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
        },
    ) as client:
        tasks = [
            _fetch_company_filing(client, rate_limiter, company, filing_type, year)
            for company in companies
        ]
        filings = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to error dicts
    results = []
    for i, filing in enumerate(filings):
        if isinstance(filing, Exception):
            company = companies[i]
            logger.error(
                "Failed to fetch filing for company",
                cik=company.get("cik"),
                company=company.get("name"),
                error=str(filing),
            )
            results.append(
                {
                    "cik": company.get("cik", "unknown"),
                    "company": company.get("name", "unknown"),
                    "filing_type": filing_type,
                    "filing_date": None,
                    "accession_number": None,
                    "html": None,
                    "error": str(filing),
                }
            )
        else:
            results.append(filing)

    success_count = sum(1 for r in results if not r.get("error"))
    logger.info(
        "Filing fetch complete",
        total=len(companies),
        success=success_count,
        failed=len(companies) - success_count,
        filing_type=filing_type,
        year=year,
    )

    return results


async def _fetch_company_filing(
    client: httpx.AsyncClient,
    rate_limiter: SecRateLimiter,
    company: dict[str, Any],
    filing_type: str,
    year: int,
) -> dict[str, Any]:
    """Fetch a single company's filing.

    Args:
        client: HTTP client
        rate_limiter: Rate limiter instance
        company: Company dict with 'cik', 'name', 'ticker'
        filing_type: Filing type to fetch
        year: Target fiscal year

    Returns:
        Filing dict with metadata and HTML content
    """
    cik = company.get("cik", "")
    company_name = company.get("name", "Unknown")

    # Format CIK with leading zeros (10 digits)
    cik_formatted = str(cik).zfill(10)

    logger.info(
        "Fetching filing",
        cik=cik_formatted,
        company=company_name,
        filing_type=filing_type,
        year=year,
    )

    try:
        # Step 1: Get company submissions metadata
        submissions = await _get_company_submissions(
            client, rate_limiter, cik_formatted
        )

        # Step 2: Find most recent filing of requested type for target year
        filing_metadata = _find_filing(submissions, filing_type, year)

        if not filing_metadata:
            logger.warning(
                "No filing found for company",
                cik=cik_formatted,
                company=company_name,
                filing_type=filing_type,
                year=year,
            )
            return {
                "cik": cik_formatted,
                "company": company_name,
                "filing_type": filing_type,
                "filing_date": None,
                "accession_number": None,
                "html": None,
                "error": f"No {filing_type} filing found for {year}",
            }

        # Step 3: Fetch filing HTML content
        html_content = await _get_filing_content(
            client,
            rate_limiter,
            cik_formatted,
            filing_metadata["accession_number"],
        )

        logger.info(
            "Successfully fetched filing",
            cik=cik_formatted,
            company=company_name,
            filing_type=filing_type,
            filing_date=filing_metadata["filing_date"],
        )

        return {
            "cik": cik_formatted,
            "company": company_name,
            "filing_type": filing_type,
            "filing_date": filing_metadata["filing_date"],
            "accession_number": filing_metadata["accession_number"],
            "html": html_content,
        }

    except Exception as e:
        logger.error(
            "Error fetching filing",
            cik=cik_formatted,
            company=company_name,
            error=str(e),
        )
        raise


async def _get_company_submissions(
    client: httpx.AsyncClient,
    rate_limiter: SecRateLimiter,
    cik: str,
) -> dict[str, Any]:
    """Fetch company submissions metadata from SEC.

    Args:
        client: HTTP client
        rate_limiter: Rate limiter instance
        cik: Company CIK (10 digits, zero-padded)

    Returns:
        Submissions metadata dict
    """
    await rate_limiter.wait()

    url = f"{SEC_BASE_URL}/submissions/CIK{cik}.json"

    for attempt in range(MAX_RETRIES):
        try:
            logger.debug("Fetching submissions", url=url, attempt=attempt + 1)
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"CIK not found: {cik}")
            logger.warning(
                "HTTP error fetching submissions",
                url=url,
                status=e.response.status_code,
                attempt=attempt + 1,
            )
            if attempt == MAX_RETRIES - 1:
                raise
            await asyncio.sleep(2**attempt)  # Exponential backoff

        except httpx.RequestError as e:
            logger.warning(
                "Request error fetching submissions",
                url=url,
                error=str(e),
                attempt=attempt + 1,
            )
            if attempt == MAX_RETRIES - 1:
                raise
            await asyncio.sleep(2**attempt)

    raise Exception(f"Failed to fetch submissions after {MAX_RETRIES} attempts")


def _find_filing(
    submissions: dict[str, Any],
    filing_type: str,
    year: int,
) -> Optional[dict[str, str]]:
    """Find most recent filing of specified type for target year.

    Args:
        submissions: Company submissions metadata
        filing_type: Filing type (e.g., "DEF 14A", "10-K")
        year: Target fiscal year

    Returns:
        Filing metadata dict with 'accession_number' and 'filing_date',
        or None if not found
    """
    recent_filings = submissions.get("filings", {}).get("recent", {})

    forms = recent_filings.get("form", [])
    filing_dates = recent_filings.get("filingDate", [])
    accession_numbers = recent_filings.get("accessionNumber", [])

    # Find all filings matching type and year
    matches = []
    for i, form in enumerate(forms):
        if form == filing_type:
            filing_date_str = filing_dates[i]
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")

            if filing_date.year == year:
                matches.append(
                    {
                        "accession_number": accession_numbers[i],
                        "filing_date": filing_date_str,
                        "date_obj": filing_date,
                    }
                )

    if not matches:
        return None

    # Return most recent filing
    matches.sort(key=lambda x: x["date_obj"], reverse=True)
    result = matches[0]

    # Remove date_obj before returning (not JSON serializable)
    return {
        "accession_number": result["accession_number"],
        "filing_date": result["filing_date"],
    }


async def _get_filing_content(
    client: httpx.AsyncClient,
    rate_limiter: SecRateLimiter,
    cik: str,
    accession_number: str,
) -> str:
    """Fetch filing HTML content from SEC Archives.

    Args:
        client: HTTP client
        rate_limiter: Rate limiter instance
        cik: Company CIK (10 digits, zero-padded)
        accession_number: SEC accession number (e.g., "0001193125-23-123456")

    Returns:
        Filing HTML content
    """
    await rate_limiter.wait()

    # Remove dashes from accession number for URL path
    accession_no_dashes = accession_number.replace("-", "")

    # Try common primary document filenames
    # Most common patterns: .htm, .html, with various prefixes
    filenames = [
        f"{accession_number}.txt",  # Full text submission
        f"{accession_number}-index.htm",  # Index page
        "primary_doc.htm",  # Common primary document name
        f"d{accession_no_dashes}.htm",  # Pattern: d + accession
        f"a{accession_no_dashes}.htm",  # Pattern: a + accession
    ]

    # Remove leading zeros from CIK for archive URL
    cik_no_leading_zeros = str(int(cik))

    # Try each filename until we find one that works
    for filename in filenames:
        url = f"{SEC_ARCHIVES_URL}/{cik_no_leading_zeros}/{accession_no_dashes}/{filename}"

        try:
            logger.debug("Attempting to fetch filing content", url=url)
            response = await client.get(url)
            response.raise_for_status()

            logger.debug(
                "Successfully fetched filing content",
                url=url,
                size=len(response.text),
            )
            return response.text

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Try next filename
                continue
            logger.warning(
                "HTTP error fetching filing content",
                url=url,
                status=e.response.status_code,
            )
            continue

        except httpx.RequestError as e:
            logger.warning(
                "Request error fetching filing content",
                url=url,
                error=str(e),
            )
            continue

    # If we get here, none of the filenames worked
    # Fall back to fetching the index page to find the primary document
    logger.warning(
        "Could not find filing content with common filenames, "
        "falling back to index parsing",
        cik=cik,
        accession_number=accession_number,
    )

    # Return a placeholder error message
    return f"<!-- Error: Could not locate primary document for accession {accession_number} -->"
