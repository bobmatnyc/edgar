"""
Fortune 100 Adapter Layer - Integration with Meta-Extractor.

This package provides adapters to integrate Fortune 100 extractors
(SCTExtractor, TaxExtractor) with the Meta-Extractor registry.

Adapters:
- SCTAdapter: Wraps SCTExtractor for DEF 14A filings (proxy statements)
- TaxAdapter: Wraps TaxExtractor for 10-K filings (annual reports)

Architecture:
    Fortune 100 Extractors          Adapter Layer           Meta-Extractor
    =====================          ==============          ==============
    SCTExtractor                →  SCTAdapter          →   Registry
    TaxExtractor                →  TaxAdapter          →   Registry

    Interface: extract(dict) → Model   → IDataExtractor.extract(**kwargs) → dict

Registration Example:
    >>> from edgar_analyzer.extractors.registry import ExtractorRegistry
    >>> from edgar_analyzer.extractors.fortune100 import SCTAdapter
    >>>
    >>> registry = ExtractorRegistry()
    >>> registry.register(
    ...     name="sct_fortune100",
    ...     class_path="edgar_analyzer.extractors.fortune100.sct_adapter.SCTAdapter",
    ...     version="1.0.0",
    ...     description="Fortune 100 Summary Compensation Table Extractor",
    ...     domain="sct",
    ...     tags=["fortune100", "compensation", "def14a"]
    ... )

Usage Example:
    >>> adapter = SCTAdapter(company="Apple Inc.", cik="0000320193")
    >>> result = await adapter.extract(
    ...     filing_type="DEF 14A",
    ...     html="<html>...</html>"
    ... )
    >>> print(result["executives"][0]["name"])  # "Tim Cook"
"""

from edgar_analyzer.extractors.fortune100.sct_adapter import SCTAdapter
from edgar_analyzer.extractors.fortune100.tax_adapter import TaxAdapter
from edgar_analyzer.extractors.fortune100.models import (
    CompensationYear,
    ExecutiveCompensation,
    SCTData,
    TaxYear,
    TaxData,
)

__all__ = [
    # Adapters
    "SCTAdapter",
    "TaxAdapter",
    # Models (re-exported from Fortune 100)
    "CompensationYear",
    "ExecutiveCompensation",
    "SCTData",
    "TaxYear",
    "TaxData",
]
