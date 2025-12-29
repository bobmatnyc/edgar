"""
SCT Extractor Package.

This package contains the Summary Compensation Table (SCT) data extractor.

Main Components:
- SCTExtractor: Service for extracting SCT data from SEC DEF 14A filings
- SCTData: Pydantic model for structured SCT data
- SCTExtractionResult: Result wrapper with success/error status

Example:
    >>> from edgar_analyzer.clients.openrouter_client import OpenRouterClient
    >>> from edgar_analyzer.extractors.sct import SCTExtractor
    >>>
    >>> openrouter = OpenRouterClient(api_key="sk-or-v1-...")
    >>> extractor = SCTExtractor(openrouter)
    >>> result = await extractor.extract(
    ...     filing_url="https://www.sec.gov/Archives/edgar/data/...",
    ...     cik="0000320193",
    ...     company_name="Apple Inc."
    ... )
    >>> if result.success:
    ...     print(f"Extraction successful: {result.data}")
"""

from edgar_analyzer.extractors.sct.extractor import SCTExtractor
from edgar_analyzer.extractors.sct.models import (
    CompensationYear,
    ExecutiveCompensation,
    SCTData,
    SCTExtractionResult,
)

__all__ = [
    "SCTExtractor",
    "SCTData",
    "SCTExtractionResult",
    "CompensationYear",
    "ExecutiveCompensation",
]

__version__ = "1.0.0"
__author__ = "EDGAR Analyzer Team"
__description__ = "Summary Compensation Table extractor"
