"""
Analysis services for the Extract & Transform Platform.

This package provides schema inference, pattern detection, and code generation
services for the example-driven transformation system.

Migration Note:
    Extracted from edgar_analyzer.services (Phase 2 - T3 batch)
    No EDGAR-specific code - generic analysis for all data sources.
"""

from extract_transform_platform.services.analysis.example_parser import (
    ExampleParser,
)
from extract_transform_platform.services.analysis.schema_analyzer import (
    SchemaAnalyzer,
)

__all__ = [
    "ExampleParser",
    "SchemaAnalyzer",
]
