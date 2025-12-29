"""Self-refinement module for EDGAR extractors.

This module provides automatic analysis and improvement of extraction failures.
"""

from edgar.refinement.refiner import (
    ExtractionFailure,
    ExtractorRefiner,
    RefinementSuggestion,
)

__all__ = ["ExtractorRefiner", "ExtractionFailure", "RefinementSuggestion"]
