"""Executive compensation vs. corporate tax analysis module."""

from edgar.analysis.analyzer import CompTaxAnalyzer
from edgar.analysis.models import BatchAnalysisSummary, CompTaxAnalysis

__all__ = [
    "CompTaxAnalyzer",
    "CompTaxAnalysis",
    "BatchAnalysisSummary",
]
