"""
Summary Compensation Table (SCT) Extractor Service.

Extracts executive compensation data from SEC DEF 14A proxy filings using
Claude Sonnet 4.5 via OpenRouter.

Process:
1. Fetch DEF 14A HTML from SEC EDGAR
2. Extract SCT section (~50-70% through document)
3. Send to Claude Sonnet 4.5 for structured extraction
4. Parse and validate response against JSON schema
5. Return structured SCTData

Design Decisions:
- **Single-Pass Extraction**: SCT section small enough for one API call (~8-15K tokens)
- **BeautifulSoup Parsing**: Extract table + context (500 chars before/after)
- **Structured JSON**: Use Sonnet's JSON mode for reliable output
- **Retry Logic**: Exponential backoff for API failures
- **Rate Limiting**: SEC EDGAR requires 0.1s minimum delay between requests

Example:
    >>> service = SCTExtractorService(openrouter_client)
    >>> result = await service.extract_sct(
    ...     filing_url="https://www.sec.gov/Archives/edgar/data/320193/...",
    ...     cik="0000320193",
    ...     company_name="Apple Inc."
    ... )
"""

import json
import re
import time
from datetime import datetime
from typing import Optional

import httpx
import structlog
from bs4 import BeautifulSoup

from edgar_analyzer.clients.openrouter_client import OpenRouterClient
from edgar_analyzer.models.sct_models import (
    CompensationYear,
    ExecutiveCompensation,
    SCTData,
    SCTExtractionResult,
)

logger = structlog.get_logger(__name__)


class SCTExtractorService:
    """
    Service for extracting Summary Compensation Tables from DEF 14A filings.

    Uses Claude Sonnet 4.5 via OpenRouter to extract structured executive
    compensation data from HTML proxy filings.

    Design Pattern: Service-oriented architecture with dependency injection
    for testability (OpenRouterClient injected, not instantiated).

    Example:
        >>> from edgar_analyzer.clients.openrouter_client import OpenRouterClient
        >>> openrouter = OpenRouterClient(api_key="...")
        >>> service = SCTExtractorService(openrouter)
        >>> result = await service.extract_sct(
        ...     filing_url="https://...",
        ...     cik="0000320193",
        ...     company_name="Apple Inc."
        ... )
    """

    # SEC EDGAR rate limiting (required: 10 requests/second max)
    SEC_RATE_LIMIT_DELAY = 0.15  # seconds (conservative: ~6.6 req/sec)

    # HTML section extraction parameters
    SCT_CONTEXT_CHARS = 1000  # Characters before/after table to include
    MAX_HTML_SIZE = 100_000  # Max HTML size to send to LLM (~50KB typical)

    def __init__(
        self,
        openrouter_client: OpenRouterClient,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize SCT extractor.

        Args:
            openrouter_client: OpenRouter API client instance
            user_agent: User agent for SEC EDGAR requests (required by SEC)

        Note:
            SEC requires user agent format: "CompanyName Contact@email.com"
        """
        self.openrouter = openrouter_client
        self.user_agent = user_agent or "EDGARAnalyzer research@example.com"

        # Rate limiting state
        self._last_request_time = 0.0

        logger.info(
            "SCTExtractorService initialized",
            user_agent=self.user_agent,
            model=self.openrouter.model,
        )

    async def extract_sct(
        self,
        filing_url: str,
        cik: str,
        company_name: str,
        ticker: Optional[str] = None,
    ) -> SCTExtractionResult:
        """
        Extract Summary Compensation Table from DEF 14A filing.

        Args:
            filing_url: SEC EDGAR URL for DEF 14A filing
            cik: Company CIK (10 digits)
            company_name: Company legal name
            ticker: Stock ticker symbol (optional)

        Returns:
            SCTExtractionResult with success status and data/error

        Example:
            >>> result = await service.extract_sct(
            ...     filing_url="https://www.sec.gov/Archives/edgar/data/320193/...",
            ...     cik="0000320193",
            ...     company_name="Apple Inc.",
            ...     ticker="AAPL"
            ... )
            >>> if result.success:
            ...     print(f"Extracted {len(result.data.executives)} executives")
        """
        start_time = time.time()

        try:
            logger.info(
                "Starting SCT extraction",
                cik=cik,
                company_name=company_name,
                filing_url=filing_url,
            )

            # Step 1: Fetch DEF 14A HTML
            html_content = self._fetch_filing_html(filing_url)
            logger.debug("Fetched filing HTML", size_bytes=len(html_content))

            # Step 2: Extract SCT section
            sct_html = self._extract_sct_section(html_content)
            logger.debug("Extracted SCT section", size_bytes=len(sct_html))

            # Step 3: Build LLM prompt
            prompt = self._build_extraction_prompt(
                sct_html=sct_html,
                company_name=company_name,
                cik=cik,
                ticker=ticker,
            )

            # Step 4: Call Claude Sonnet for extraction
            logger.debug("Calling OpenRouter for extraction")
            response_json = await self.openrouter.chat_completion_json(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured data from SEC filings. "
                        "Extract executive compensation data following the provided schema exactly.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=8000,
            )

            # Step 5: Parse and validate response
            sct_data = self._parse_response(
                response_json=response_json,
                filing_url=filing_url,
            )

            extraction_time = time.time() - start_time
            logger.info(
                "SCT extraction successful",
                cik=cik,
                executives_count=len(sct_data.executives),
                extraction_time_seconds=extraction_time,
            )

            return SCTExtractionResult(
                success=True,
                data=sct_data,
                extraction_time_seconds=extraction_time,
                model_used=self.openrouter.model,
            )

        except Exception as e:
            extraction_time = time.time() - start_time
            logger.error(
                "SCT extraction failed",
                cik=cik,
                company_name=company_name,
                error=str(e),
                error_type=type(e).__name__,
                extraction_time_seconds=extraction_time,
            )

            return SCTExtractionResult(
                success=False,
                error_message=f"{type(e).__name__}: {str(e)}",
                extraction_time_seconds=extraction_time,
                model_used=self.openrouter.model,
            )

    def _fetch_filing_html(self, url: str) -> str:
        """
        Fetch DEF 14A HTML from SEC EDGAR with rate limiting.

        Args:
            url: SEC EDGAR filing URL

        Returns:
            HTML content as string

        Raises:
            httpx.HTTPError: If request fails
        """
        # Rate limiting (SEC requires max 10 requests/second)
        time_since_last = time.time() - self._last_request_time
        if time_since_last < self.SEC_RATE_LIMIT_DELAY:
            sleep_time = self.SEC_RATE_LIMIT_DELAY - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml",
        }

        logger.debug("Fetching filing HTML", url=url)

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()

        self._last_request_time = time.time()

        return response.text

    def _extract_sct_section(self, html: str) -> str:
        """
        Extract SCT section from full DEF 14A HTML.

        Strategy:
        1. Search for "Summary Compensation Table" heading
        2. Extract table + context (1000 chars before/after)
        3. Limit to MAX_HTML_SIZE to fit in LLM context

        Args:
            html: Full DEF 14A HTML content

        Returns:
            Extracted SCT section HTML

        Raises:
            ValueError: If SCT section not found
        """
        soup = BeautifulSoup(html, "html.parser")

        # Search patterns for SCT heading
        patterns = [
            r"Summary Compensation Table",
            r"SUMMARY COMPENSATION TABLE",
            r"Executive Compensation Tables",
            r"EXECUTIVE COMPENSATION",
        ]

        # Find SCT heading
        sct_element = None
        for pattern in patterns:
            # Search in text nodes
            for element in soup.find_all(string=re.compile(pattern, re.IGNORECASE)):
                parent = element.parent
                if parent.name in ["p", "span", "b", "strong", "h1", "h2", "h3"]:
                    sct_element = parent
                    logger.debug(f"Found SCT heading with pattern: {pattern}")
                    break
            if sct_element:
                break

        if not sct_element:
            raise ValueError(
                "Could not find Summary Compensation Table section. "
                f"Searched for patterns: {patterns}"
            )

        # Find the table following the heading
        # Look for next <table> tag within 5000 chars
        table = None
        current = sct_element
        for _ in range(100):  # Limit iterations to prevent infinite loop
            current = current.find_next()
            if not current:
                break
            if current.name == "table":
                table = current
                break

        if not table:
            raise ValueError(
                "Could not find table element after SCT heading. "
                "Table may be in image format or use non-standard structure."
            )

        # Extract HTML around the table
        # Get position in original HTML
        table_html = str(table)
        table_start = html.find(str(table)[:100])  # Find by first 100 chars

        if table_start == -1:
            # Fallback: just use table HTML
            sct_html = table_html
        else:
            # Extract with context
            context_start = max(0, table_start - self.SCT_CONTEXT_CHARS)
            context_end = min(
                len(html),
                table_start + len(table_html) + self.SCT_CONTEXT_CHARS,
            )
            sct_html = html[context_start:context_end]

        # Limit size
        if len(sct_html) > self.MAX_HTML_SIZE:
            logger.warning(
                "SCT HTML exceeds max size, truncating",
                original_size=len(sct_html),
                max_size=self.MAX_HTML_SIZE,
            )
            sct_html = sct_html[: self.MAX_HTML_SIZE]

        return sct_html

    def _build_extraction_prompt(
        self,
        sct_html: str,
        company_name: str,
        cik: str,
        ticker: Optional[str] = None,
    ) -> str:
        """
        Build LLM prompt for SCT extraction.

        Args:
            sct_html: Extracted SCT section HTML
            company_name: Company name
            cik: CIK number
            ticker: Stock ticker (optional)

        Returns:
            Complete prompt text
        """
        # Load JSON schema
        schema = {
            "company_name": company_name,
            "ticker": ticker or "UNKNOWN",
            "cik": cik,
            "filing_date": "YYYY-MM-DD",
            "fiscal_years": [2024, 2023, 2022],
            "executives": [
                {
                    "name": "Executive Full Name",
                    "position": "Title/Position",
                    "is_ceo": True,
                    "is_cfo": False,
                    "compensation_by_year": [
                        {
                            "year": 2024,
                            "salary": 3000000,
                            "bonus": 0,
                            "stock_awards": 58088946,
                            "option_awards": 0,
                            "non_equity_incentive": 12000000,
                            "change_in_pension": 0,
                            "all_other_compensation": 1520856,
                            "total": 74609802,
                            "footnotes": ["3", "4"],
                        }
                    ],
                }
            ],
            "footnotes": {
                "3": "Footnote description",
                "4": "Another footnote",
            },
            "extraction_metadata": {
                "extraction_date": datetime.utcnow().isoformat() + "Z",
                "model": self.openrouter.model,
                "confidence": 0.95,
            },
        }

        prompt = f"""# Task: Extract Summary Compensation Table from DEF 14A Proxy Filing

## Company Information
- Name: {company_name}
- CIK: {cik}
- Ticker: {ticker or 'UNKNOWN'}

## Instructions
Extract executive compensation data from the Summary Compensation Table (SCT) below.

### Data Requirements
1. **Executive Names**: Extract full name exactly as shown
2. **Position**: Extract complete title (may include line breaks)
3. **Fiscal Years**: Identify years covered (typically 3: 2024, 2023, 2022)
4. **Compensation Components**: Extract all monetary values as integers (remove commas, no decimals)
   - Salary: Base salary
   - Bonus: Annual bonus (may be blank/0)
   - Stock Awards: Fair value of stock grants
   - Option Awards: Fair value of option grants (may be blank/0)
   - Non-Equity Incentive: Performance-based cash compensation
   - Change in Pension: Pension value changes (may be blank/0)
   - All Other Compensation: Perks, benefits, 401k matching
   - Total: Sum of all components
5. **CEO/CFO Flags**: Identify Principal Executive Officer (CEO) and Principal Financial Officer (CFO)
6. **Footnotes**: Extract footnote reference IDs (e.g., superscripts like <sup>(3)</sup>)
7. **Multi-Year Data**: Handle rowspan cells - associate executive name with all fiscal years

### HTML Parsing Rules
- Skip spacer cells (cells with only &nbsp; or &#160;)
- Extract numeric values only (remove "$", ",", and whitespace)
- Handle nested tables (find the data table with compensation values)
- Decode HTML entities (&#160; → space, &#8212; → dash)
- Join multi-line positions with space or newline

### Output Format
Return valid JSON matching this structure:

```json
{schema}
```

## HTML Content to Extract

{sct_html}

## Critical Validation
- Verify: Total = Salary + Bonus + Stock Awards + Option Awards + Non-Equity Incentive + Change in Pension + All Other Compensation
- Each executive should have 1-3 years of data (3 typical)
- Typically 5 Named Executive Officers (may vary)
- All monetary values must be integers (no decimals, no commas)

Extract the data now, returning ONLY valid JSON.
"""

        return prompt

    def _parse_response(
        self,
        response_json: str,
        filing_url: str,
    ) -> SCTData:
        """
        Parse and validate LLM response.

        Args:
            response_json: JSON response from LLM
            filing_url: Filing URL for metadata

        Returns:
            Validated SCTData object

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            pydantic.ValidationError: If response doesn't match schema
        """
        # Parse JSON - strip markdown code fences if present
        try:
            content = response_json.strip()
            # Strip markdown code fences (Claude often wraps JSON in ```json ... ```)
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data_dict = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), raw_response=response_json[:200])
            raise ValueError(f"Invalid JSON response: {str(e)}")

        # Add filing URL if not present
        if "filing_url" not in data_dict:
            data_dict["filing_url"] = filing_url

        # Validate with Pydantic
        sct_data = SCTData(**data_dict)

        logger.debug(
            "Parsed and validated SCT data",
            executives_count=len(sct_data.executives),
            fiscal_years=sct_data.fiscal_years,
        )

        return sct_data
