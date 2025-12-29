"""
Fortune 100 Data Models - Re-exports for Meta-Extractor compatibility.

This module re-exports the Pydantic models from Fortune 100 extractors
(src/edgar/extractors/{sct,tax}/models.py) to provide a unified import path
for Meta-Extractor adapters.

Re-export Strategy:
- SCT Models: CompensationYear, ExecutiveCompensation, SCTData
- Tax Models: TaxYear, TaxData

Design Decision: Re-export vs Duplication
- **Re-export**: Single source of truth, no model duplication
- **Import Path**: edgar_analyzer.extractors.fortune100.models
- **Compatibility**: Models remain unchanged (proven Fortune 100 extractors)

Example Usage:
    >>> from edgar_analyzer.extractors.fortune100.models import SCTData, TaxData
    >>> sct_data = SCTData(company="Apple Inc.", cik="0000320193", ...)
    >>> tax_data = TaxData(company="Apple Inc.", fiscal_year_end="2023-09-30", ...)
"""

# Re-export SCT models
from edgar.extractors.sct.models import (
    CompensationYear,
    ExecutiveCompensation,
    SCTData,
)

# Re-export Tax models
from edgar.extractors.tax.models import TaxData, TaxYear

__all__ = [
    # SCT models
    "CompensationYear",
    "ExecutiveCompensation",
    "SCTData",
    # Tax models
    "TaxYear",
    "TaxData",
]
