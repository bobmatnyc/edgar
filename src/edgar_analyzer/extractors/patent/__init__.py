"""
Patent Extractor Package.

This package contains the patent data extractor and related models.

Main Components:
- PatentExtractor: Service for extracting patent data from SEC filings
- ExtractedData: Pydantic model for structured patent data
- ExtractedDataExtractionResult: Result wrapper with success/error status

Example:
    >>> from edgar_analyzer.clients.openrouter_client import OpenRouterClient
    >>> from .patent_extractor import PatentExtractor
    >>>
    >>> openrouter = OpenRouterClient(api_key="sk-or-v1-...")
    >>> extractor = PatentExtractor(openrouter)
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

from .extractor import PatentExtractor
from .models import (
    ExtractedData,
    ExtractedDataExtractionResult,
)

__all__ = [
    "PatentExtractor",
    "ExtractedData",
    "ExtractedDataExtractionResult",
    "ExtractedData",
]

__version__ = "1.0.0"
__author__ = "EDGAR Analyzer Team"
__description__ = "Extract patent filing information from Google Patents API responses"
