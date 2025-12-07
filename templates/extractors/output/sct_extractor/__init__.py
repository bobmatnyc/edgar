"""
Sct Extractor Package.

This package contains the sct data extractor and related models.

Main Components:
- SCTExtractor: Service for extracting sct data from SEC filings
- SCTData: Pydantic model for structured sct data
- SCTExtractionResult: Result wrapper with success/error status

Example:
    >>> from edgar_analyzer.clients.openrouter_client import OpenRouterClient
    >>> from .sct_extractor import SCTExtractor
    >>>
    >>> openrouter = OpenRouterClient(api_key="sk-or-v1-...")
    >>> extractor = SCTExtractor(openrouter)
    >>> result = await extractor.extract(
    ...     filing_url="https://www.sec.gov/Archives/edgar/data/...",
    ...     cik="0000320193",
    ...     company_name="Apple Inc.",
    ...     ticker="AAPL"
    ... )
    >>> if result.success:
    ...     print(f"Extraction successful")
    ...     print(result.data)
"""

from .sct_extractor import SCTExtractor
from .sct_models import (
    SCTData,
    SCTExtractionResult,
    CompensationYear,
    ExecutiveCompensation,
    SCTData,
)

__all__ = [
    "SCTExtractor",
    "SCTData",
    "SCTExtractionResult",
    "CompensationYear",
    "ExecutiveCompensation",
    "SCTData",
]

__version__ = "1.0.0"
__author__ = "EDGAR Analyzer Team"
__description__ = "Summary Compensation Table extractor"
