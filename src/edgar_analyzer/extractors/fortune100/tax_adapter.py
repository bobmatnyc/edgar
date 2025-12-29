"""
TaxAdapter - Adapter to integrate Fortune 100 TaxExtractor with Meta-Extractor.

This adapter wraps the Fortune 100 TaxExtractor (from src/edgar/extractors/tax/)
to be compatible with the Meta-Extractor registry using IDataExtractor interface.

Architecture:
- Fortune 100 TaxExtractor: extract(raw_data: dict) -> TaxData
- Meta-Extractor IDataExtractor: extract(**kwargs) -> Optional[Dict[str, Any]]

Mapping Strategy:
- Input: Accept filing_type, html, company, cik as kwargs
- Wrap TaxExtractor.extract() call
- Convert TaxData Pydantic model -> dict output
- Handle filing type validation (10-K)

Example Usage:
    >>> adapter = TaxAdapter(company="Apple Inc.", cik="0000320193")
    >>> result = await adapter.extract(
    ...     filing_type="10-K",
    ...     html="<html>...</html>"
    ... )
    >>> print(result["company"])  # "Apple Inc."
    >>> print(result["tax_years"][0]["total_tax_expense"])  # 14527000000.0
"""

from typing import Any, Dict, Optional

import structlog

from extract_transform_platform.core.base import IDataExtractor
from edgar.extractors.tax.extractor import TaxExtractor
from edgar.extractors.tax.models import TaxData

logger = structlog.get_logger(__name__)


class TaxAdapter(IDataExtractor):
    """
    Adapter for Fortune 100 TaxExtractor to work with Meta-Extractor registry.

    This adapter bridges the Fortune 100 extractor (synchronous, Pydantic models)
    with the Meta-Extractor interface (async, dict-based).

    Attributes:
        company: Company name for extracted data
        cik: SEC CIK number
        _extractor: Wrapped TaxExtractor instance

    Design Decisions:
    - **Async Interface**: IDataExtractor requires async, though TaxExtractor is sync
    - **Dict Output**: Meta-Extractor expects dict (JSON-serializable), not Pydantic
    - **Filing Type**: Only accepts 10-K (annual reports with tax data)
    - **Error Handling**: Wraps ValueError from TaxExtractor, logs errors

    Performance:
    - Time Complexity: O(n) where n = number of table rows (HTML parsing)
    - Space Complexity: O(m) where m = number of tax years (typically 3-5)
    - No caching (handled by BaseDataSource if needed)
    """

    def __init__(self, company: str = "Unknown", cik: str = ""):
        """
        Initialize TaxAdapter.

        Args:
            company: Company name for extracted data
            cik: SEC CIK number
        """
        self.company = company
        self.cik = cik
        self._extractor = TaxExtractor(company=company, cik=cik)

        logger.info(
            "Initialized TaxAdapter",
            company=company,
            cik=cik,
        )

    async def extract(self, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Extract income tax data from 10-K filing.

        Args:
            **kwargs: Extractor-specific parameters
                Required:
                - filing_type: Must be "10-K"
                - html: HTML content of the filing
                Optional:
                - company: Override company name (uses init value if not provided)
                - cik: Override CIK (uses init value if not provided)
                - filing_date: Filing date (YYYY-MM-DD)
                - fiscal_year_end: Fiscal year end date

        Returns:
            Dictionary with extracted tax data:
            {
                "company": "Apple Inc.",
                "cik": "0000320193",
                "filing_date": "2024-02-15",
                "fiscal_year_end": "2023-09-30",
                "tax_years": [
                    {
                        "year": 2023,
                        "current_federal": 10500000000.0,
                        "current_state": 1200000000.0,
                        "current_foreign": 5800000000.0,
                        "deferred_federal": -1500000000.0,
                        "deferred_state": -100000000.0,
                        "deferred_foreign": -400000000.0,
                        "total_current": 17500000000.0,
                        "total_deferred": -2000000000.0,
                        "total_tax_expense": 15500000000.0,
                        "effective_tax_rate": 0.145
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
            "Starting tax extraction",
            filing_type=filing_type,
            company=company,
            cik=cik,
            html_length=len(html) if html else 0,
        )

        # Validate filing type
        if filing_type != "10-K":
            logger.warning(
                "Invalid filing type for tax extraction",
                filing_type=filing_type,
                expected="10-K",
            )
            return None

        # Validate required parameters
        if not html:
            logger.error("Missing required parameter: html")
            raise ValueError("Parameter 'html' is required for tax extraction")

        # Prepare raw_data for Fortune 100 extractor
        raw_data: Dict[str, Any] = {
            "html": html,
            "filing": {
                "filing_date": kwargs.get("filing_date", ""),
                "fiscal_year_end": kwargs.get("fiscal_year_end", ""),
            },
        }

        try:
            # Call Fortune 100 extractor (sync)
            result: TaxData = self._extractor.extract(raw_data)

            # Convert Pydantic model to dict for Meta-Extractor
            result_dict = result.model_dump()

            logger.info(
                "Tax extraction successful",
                company=result.company,
                tax_years_count=len(result.tax_years),
                latest_tax_expense=result.latest_tax_expense,
            )

            return result_dict

        except ValueError as e:
            logger.error(
                "Tax extraction failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Return None for graceful failure (Meta-Extractor pattern)
            return None

        except Exception as e:
            logger.error(
                "Unexpected error during tax extraction",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Re-raise unexpected errors for debugging
            raise
