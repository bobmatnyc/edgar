"""
SCTAdapter - Adapter to integrate Fortune 100 SCTExtractor with Meta-Extractor.

This adapter wraps the Fortune 100 SCTExtractor (from src/edgar/extractors/sct/)
to be compatible with the Meta-Extractor registry using IDataExtractor interface.

Architecture:
- Fortune 100 SCTExtractor: extract(raw_data: dict) -> SCTData
- Meta-Extractor IDataExtractor: extract(**kwargs) -> Optional[Dict[str, Any]]

Mapping Strategy:
- Input: Accept filing_type, html, company, cik as kwargs
- Wrap SCTExtractor.extract() call
- Convert SCTData Pydantic model -> dict output
- Handle filing type validation (DEF 14A)

Example Usage:
    >>> adapter = SCTAdapter(company="Apple Inc.", cik="0000320193")
    >>> result = await adapter.extract(
    ...     filing_type="DEF 14A",
    ...     html="<html>...</html>"
    ... )
    >>> print(result["company"])  # "Apple Inc."
    >>> print(result["executives"][0]["name"])  # "Tim Cook"
"""

from typing import Any, Dict, Optional

import structlog

from extract_transform_platform.core.base import IDataExtractor
from edgar.extractors.sct.extractor import SCTExtractor
from edgar.extractors.sct.models import SCTData

logger = structlog.get_logger(__name__)


class SCTAdapter(IDataExtractor):
    """
    Adapter for Fortune 100 SCTExtractor to work with Meta-Extractor registry.

    This adapter bridges the Fortune 100 extractor (synchronous, Pydantic models)
    with the Meta-Extractor interface (async, dict-based).

    Attributes:
        company: Company name for extracted data
        cik: SEC CIK number
        _extractor: Wrapped SCTExtractor instance

    Design Decisions:
    - **Async Interface**: IDataExtractor requires async, though SCTExtractor is sync
    - **Dict Output**: Meta-Extractor expects dict (JSON-serializable), not Pydantic
    - **Filing Type**: Only accepts DEF 14A (proxy statements with SCT data)
    - **Error Handling**: Wraps ValueError from SCTExtractor, logs errors

    Performance:
    - Time Complexity: O(n) where n = number of table rows (HTML parsing)
    - Space Complexity: O(m) where m = number of executives * years
    - No caching (handled by BaseDataSource if needed)
    """

    def __init__(self, company: str = "Unknown", cik: str = ""):
        """
        Initialize SCTAdapter.

        Args:
            company: Company name for extracted data
            cik: SEC CIK number
        """
        self.company = company
        self.cik = cik
        self._extractor = SCTExtractor(company=company, cik=cik)

        logger.info(
            "Initialized SCTAdapter",
            company=company,
            cik=cik,
        )

    async def extract(self, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Extract Summary Compensation Table data from DEF 14A filing.

        Args:
            **kwargs: Extractor-specific parameters
                Required:
                - filing_type: Must be "DEF 14A"
                - html: HTML content of the filing
                Optional:
                - company: Override company name (uses init value if not provided)
                - cik: Override CIK (uses init value if not provided)

        Returns:
            Dictionary with extracted SCT data:
            {
                "company": "Apple Inc.",
                "cik": "0000320193",
                "filing_date": "2024-01-15",
                "executives": [
                    {
                        "name": "Tim Cook",
                        "title": "Chief Executive Officer",
                        "compensation": [
                            {
                                "year": 2023,
                                "salary": 3000000.0,
                                "bonus": 0.0,
                                "stock_awards": 47700000.0,
                                ...
                            }
                        ]
                    }
                ]
            }
            None if extraction fails or filing type is invalid.

        Raises:
            ValueError: If required parameters missing or invalid filing type
        """
        # Extract parameters
        filing_type = kwargs.get("filing_type", "")
        html = kwargs.get("html", "")
        company = kwargs.get("company", self.company)
        cik = kwargs.get("cik", self.cik)

        logger.debug(
            "Starting SCT extraction",
            filing_type=filing_type,
            company=company,
            cik=cik,
            html_length=len(html) if html else 0,
        )

        # Validate filing type
        if filing_type != "DEF 14A":
            logger.warning(
                "Invalid filing type for SCT extraction",
                filing_type=filing_type,
                expected="DEF 14A",
            )
            return None

        # Validate required parameters
        if not html:
            logger.error("Missing required parameter: html")
            raise ValueError("Parameter 'html' is required for SCT extraction")

        # Prepare raw_data for Fortune 100 extractor
        raw_data: Dict[str, Any] = {
            "html": html,
            "filing": {
                "filing_date": kwargs.get("filing_date", ""),
            },
        }

        try:
            # Call Fortune 100 extractor (sync)
            result: SCTData = self._extractor.extract(raw_data)

            # Convert Pydantic model to dict for Meta-Extractor
            result_dict = result.model_dump()

            logger.info(
                "SCT extraction successful",
                company=result.company,
                executives_count=len(result.executives),
            )

            return result_dict

        except ValueError as e:
            logger.error(
                "SCT extraction failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Return None for graceful failure (Meta-Extractor pattern)
            return None

        except Exception as e:
            logger.error(
                "Unexpected error during SCT extraction",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Re-raise unexpected errors for debugging
            raise
