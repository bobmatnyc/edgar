"""
Extract patent filing information from Google Patents API responses.

Extracts patent data from SEC filings using Claude Sonnet 4.5 via OpenRouter.

Process:
1. Fetch filing HTML from SEC EDGAR
2. Extract patent section using pattern matching
3. Send to Claude Sonnet 4.5 for structured extraction
4. Parse and validate response against JSON schema
5. Return structured ExtractedData

Design Decisions:
- **Single-Pass Extraction**: Section small enough for one API call
- **BeautifulSoup Parsing**: Extract table + context
- **Structured JSON**: Use Sonnet's JSON mode for reliable output
- **Retry Logic**: Exponential backoff for API failures
- **Rate Limiting**: SEC EDGAR requires 0.1s minimum delay between requests

Example:
    >>> service = PatentExtractor(openrouter_client)
    >>> result = await service.extract(
    ...     filing_url="https://www.sec.gov/Archives/edgar/data/...",
    ...     cik="0000320193",
    ...     company_name="Apple Inc."
    ... )
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import structlog
from bs4 import BeautifulSoup

from edgar_analyzer.clients.openrouter_client import OpenRouterClient
from extract_transform_platform.core.base import IDataExtractor

from .models import ExtractedData, ExtractedDataExtractionResult

logger = structlog.get_logger(__name__)


class PatentExtractor(IDataExtractor):
    """
    Service for extracting patent data from SEC filings.

    Uses Claude Sonnet 4.5 via OpenRouter to extract structured data
    from HTML filings.

    Design Pattern: Service-oriented architecture with dependency injection
    for testability (OpenRouterClient injected, not instantiated).

    Example:
        >>> from edgar_analyzer.clients.openrouter_client import OpenRouterClient
        >>> openrouter = OpenRouterClient(api_key="...")
        >>> service = PatentExtractor(openrouter)
        >>> result = await service.extract(
        ...     filing_url="https://...",
        ...     cik="0000320193",
        ...     company_name="Apple Inc."
        ... )
    """

    # SEC EDGAR rate limiting (required: 10 requests/second max)
    SEC_RATE_LIMIT_DELAY = 0.15  # seconds (conservative: ~6.6 req/sec)

    # HTML section extraction parameters
    CONTEXT_CHARS = 1000  # Characters before/after table to include
    MAX_HTML_SIZE = 100000  # Max HTML size to send to LLM

    def __init__(
        self,
        openrouter_client: OpenRouterClient,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize patent extractor.

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
            "PatentExtractor initialized",
            user_agent=self.user_agent,
            model=self.openrouter.model,
        )

    async def extract(
        self,
        filing_url: str,
        cik: str,
        company_name: str,
        ticker: Optional[str] = None,
    ) -> ExtractedDataExtractionResult:
        """
        Extract patent data from SEC filing.

        Args:
            filing_url: SEC EDGAR URL for filing
            cik: Company CIK (10 digits)
            company_name: Company legal name
            ticker: Stock ticker symbol (optional)

        Returns:
            ExtractedDataExtractionResult with success status and data/error

        Example:
            >>> result = await service.extract(
            ...     filing_url="https://www.sec.gov/Archives/edgar/data/320193/...",
            ...     cik="0000320193",
            ...     company_name="Apple Inc.",
            ...     ticker="AAPL"
            ... )
            >>> if result.success:
            ...     print(f"Extraction successful")
        """
        start_time = time.time()

        try:
            logger.info(
                "Starting patent extraction",
                cik=cik,
                company_name=company_name,
                filing_url=filing_url,
            )

            # Step 1: Fetch filing HTML
            html_content = self._fetch_filing_html(filing_url)
            logger.debug("Fetched filing HTML", size_bytes=len(html_content))

            # Step 2: Extract patent section
            section_html = self._extract_section(html_content)
            logger.debug("Extracted patent section", size_bytes=len(section_html))

            # DEBUG: Save extracted HTML for analysis
            debug_dir = Path(__file__).parent.parent.parent / "output" / "patent_debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / f"{cik}_patent_section.html"
            with open(debug_file, "w") as f:
                f.write(section_html)
            logger.debug(f"Saved patent HTML to {debug_file}")

            # Step 3: Build LLM prompt
            prompt = self._build_extraction_prompt(
                section_html=section_html,
                company_name=company_name,
                cik=cik,
                ticker=ticker,
            )

            # Step 4: Call Claude Sonnet for extraction with retry logic
            max_extraction_attempts = 2
            data = None

            for attempt in range(max_extraction_attempts):
                logger.debug(
                    "Calling OpenRouter for extraction",
                    attempt=attempt + 1,
                    max_attempts=max_extraction_attempts,
                )
                response_json = await self.openrouter.chat_completion_json(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert at extracting structured data from SEC filings. Extract patent filing information from Google Patents API responses. Extract data following the provided schema exactly.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=8000,
                )

                # Step 5: Parse and validate response
                try:
                    data = self._parse_response(
                        response_json=response_json,
                        filing_url=filing_url,
                    )

                    # Validate minimum data requirements
                    if not self._validate_extraction(data):
                        logger.warning(
                            "Validation failed, retrying with enhanced prompt",
                            attempt=attempt + 1,
                            max_attempts=max_extraction_attempts,
                        )

                        if attempt < max_extraction_attempts - 1:
                            # Add explicit instruction for retry
                            prompt += (
                                "\n\n**CRITICAL**: Please review the data carefully "
                                "and ensure all required fields are extracted."
                            )
                            continue
                        else:
                            raise ValueError(
                                "Failed to extract valid data after all retry attempts."
                            )

                    # Success!
                    break

                except Exception as e:
                    logger.error(
                        "Parsing failed",
                        error=str(e),
                        attempt=attempt + 1,
                        max_attempts=max_extraction_attempts,
                    )
                    if attempt < max_extraction_attempts - 1:
                        continue
                    raise

            extraction_time = time.time() - start_time
            logger.info(
                "patent extraction successful",
                cik=cik,
                extraction_time_seconds=extraction_time,
            )

            return ExtractedDataExtractionResult(
                success=True,
                data=data,
                extraction_time_seconds=extraction_time,
                model_used=self.openrouter.model,
            )

        except Exception as e:
            extraction_time = time.time() - start_time
            logger.error(
                "patent extraction failed",
                cik=cik,
                company_name=company_name,
                error=str(e),
                error_type=type(e).__name__,
                extraction_time_seconds=extraction_time,
            )

            return ExtractedDataExtractionResult(
                success=False,
                error_message=f"{type(e).__name__}: {str(e)}",
                extraction_time_seconds=extraction_time,
                model_used=self.openrouter.model,
            )

    def _fetch_filing_html(self, url: str) -> str:
        """
        Fetch filing HTML from SEC EDGAR with rate limiting.

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

    def _is_valid_table(self, table) -> bool:
        """
        Validate that table has expected patent structure.

        Args:
            table: BeautifulSoup table element

        Returns:
            True if table appears to be correct type, False otherwise
        """
        # Get first 5 rows for header detection
        rows = table.find_all("tr", limit=5)
        if not rows:
            return False

        header_text = " ".join(row.get_text() for row in rows).lower()

        # Required columns

        # Check all required columns present
        required_columns_present = all([])

        # Reject tables with wrong indicators
        reject_indicators = []
        is_wrong_table = any(
            indicator in header_text for indicator in reject_indicators
        )

        logger.debug(
            "Table validation",
            required_columns_present=required_columns_present,
            is_wrong_table=is_wrong_table,
            header_preview=header_text[:200],
        )

        return required_columns_present and not is_wrong_table

    def _extract_table_with_context(
        self, table, chars_before: int = 1000, chars_after: int = 1000
    ) -> str:
        """
        Extract table HTML with surrounding context using BeautifulSoup navigation.

        Args:
            table: BeautifulSoup table element
            chars_before: Characters of context before table
            chars_after: Characters of context after table

        Returns:
            HTML string with table and surrounding context
        """
        elements = []
        char_count = 0

        # Collect previous siblings for context
        current = table.previous_sibling
        while current and char_count < chars_before:
            elem_str = str(current)
            elements.insert(0, elem_str)
            char_count += len(elem_str)
            current = current.previous_sibling

        # Add the table itself
        elements.append(str(table))

        # Collect next siblings for footnotes
        char_count = 0
        current = table.next_sibling
        while current and char_count < chars_after:
            elem_str = str(current)
            elements.append(elem_str)
            char_count += len(elem_str)
            current = current.next_sibling

        return "\n".join(elements)

    def _extract_section(self, html: str) -> str:
        """
        Extract patent section from full filing HTML.

        Strategy:
        1. Search for section heading using patterns
        2. Find valid table near heading
        3. Extract table + context using BeautifulSoup navigation
        4. Validate content contains expected terms
        5. Limit to MAX_HTML_SIZE to fit in LLM context

        Args:
            html: Full filing HTML content

        Returns:
            Extracted section HTML

        Raises:
            ValueError: If section not found or validation fails
        """
        soup = BeautifulSoup(html, "html.parser")

        # Search patterns for section heading
        patterns = [
            r"Summary.*Table",
            r"Executive Compensation",
        ]

        # Collect ALL heading matches
        all_heading_matches = []

        for pattern in patterns:
            # Search in text nodes
            for element in soup.find_all(string=re.compile(pattern, re.IGNORECASE)):
                parent = element.parent
                if parent.name in [
                    "p",
                    "span",
                    "b",
                    "strong",
                    "h1",
                    "h2",
                    "h3",
                    "td",
                    "th",
                ]:
                    all_heading_matches.append((parent, element.strip(), pattern))
                    logger.debug(
                        f"Collected heading match: {element.strip()[:80]}",
                        pattern=pattern,
                    )

        if not all_heading_matches:
            raise ValueError(
                "Could not find patent section. " f"Searched for patterns: {patterns}"
            )

        logger.info(
            f"Found {len(all_heading_matches)} heading matches, validating tables..."
        )

        # Try each heading match
        section_table = None
        section_element = None
        heading_text = None

        for match_idx, (parent, text, pattern) in enumerate(all_heading_matches):
            logger.debug(
                f"Trying heading match {match_idx + 1}/{len(all_heading_matches)}: {text[:80]}",
                pattern=pattern,
            )

            # Find tables after this heading
            tables = parent.find_all_next("table", limit=10)

            # Check each table for valid structure
            for table_idx, table in enumerate(tables):
                if self._is_valid_table(table):
                    # SUCCESS! Found valid table
                    section_table = table
                    section_element = parent
                    heading_text = text
                    logger.info(
                        f"Found valid table at heading match {match_idx + 1}/{len(all_heading_matches)}, "
                        f"table {table_idx + 1}/{len(tables)}",
                        heading_preview=heading_text[:80],
                        pattern=pattern,
                    )
                    break
                else:
                    logger.debug(
                        f"Table {table_idx + 1} rejected by validation",
                        heading_preview=text[:60],
                    )

            # If we found a valid table, stop searching
            if section_table:
                break

        if not section_table:
            raise ValueError(
                f"No valid patent table found after trying all {len(all_heading_matches)} heading matches."
            )

        # Extract table with context
        section_html = self._extract_table_with_context(
            section_table,
            chars_before=self.CONTEXT_CHARS,
            chars_after=self.CONTEXT_CHARS,
        )

        # Check minimum size
        if len(section_html) < 2000:
            logger.warning(
                "Extracted section suspiciously small", size=len(section_html)
            )

        # Limit size
        if len(section_html) > self.MAX_HTML_SIZE:
            logger.warning(
                "Section HTML exceeds max size, truncating",
                original_size=len(section_html),
                max_size=self.MAX_HTML_SIZE,
            )
            section_html = section_html[: self.MAX_HTML_SIZE]

        return section_html

    def _build_extraction_prompt(
        self,
        section_html: str,
        company_name: str,
        cik: str,
        ticker: Optional[str] = None,
    ) -> str:
        """
        Build LLM prompt for patent extraction.

        Args:
            section_html: Extracted section HTML
            company_name: Company name
            cik: CIK number
            ticker: Stock ticker (optional)

        Returns:
            Complete prompt text
        """
        # This will be customized by prompt_template.j2
        # For now, basic structure
        prompt = f"""# Task: Extract patent Data

## Company Information
- **Name**: {company_name}
- **CIK**: {cik}
- **Ticker**: {ticker or 'UNKNOWN'}

## Your Task
Extract structured data from the patent section in the HTML below.

## HTML Content to Extract

{section_html}

## Output Requirements

**CRITICAL**:
1. Return **ONLY** valid JSON (no markdown code fences, no explanations)
2. Extract **ALL** relevant data from the section
3. Use proper JSON syntax: double quotes, lowercase booleans (`true`/`false`)

Extract the data now.
"""
        return prompt

    def _validate_extraction(self, data: ExtractedData) -> bool:
        """
        Validate extracted data meets minimum requirements.

        Args:
            data: Extracted data object

        Returns:
            True if validation passes, False otherwise
        """
        # Basic validation - override in specific implementations
        return data is not None

    def _parse_response(
        self,
        response_json: str,
        filing_url: str,
    ) -> ExtractedData:
        """
        Parse and validate LLM response.

        Args:
            response_json: JSON response from LLM
            filing_url: Filing URL for metadata

        Returns:
            Validated ExtractedData object

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            pydantic.ValidationError: If response doesn't match schema
        """
        # Parse JSON - strip markdown code fences if present
        try:
            content = response_json.strip()

            # Strip markdown code fences
            if content.startswith("```"):
                first_newline = content.find("\n")
                if first_newline > 0:
                    content = content[first_newline + 1 :]

            # Find the last closing brace
            last_brace = content.rfind("}")
            if last_brace > 0:
                content = content[: last_brace + 1]

            content = content.strip()

            data_dict = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON response",
                error=str(e),
                raw_response=response_json[:500],
            )
            raise ValueError(f"Invalid JSON response: {str(e)}")

        # Add filing URL if not present
        if "filing_url" not in data_dict:
            data_dict["filing_url"] = filing_url

        # Validate with Pydantic
        data = ExtractedData(**data_dict)

        logger.debug(
            "Parsed and validated patent data",
        )

        return data
