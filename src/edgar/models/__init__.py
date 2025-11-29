"""Data models for EDGAR platform.

This module contains data models for:
- Extraction strategies
- Architecture constraints
- Validation results
"""

from edgar.models.extraction_strategy import ExtractionStrategy
from edgar.models.constraints import ArchitectureConstraints

__all__ = [
    "ExtractionStrategy",
    "ArchitectureConstraints",
]
