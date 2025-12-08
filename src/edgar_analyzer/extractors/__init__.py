"""
Extractor registry and dynamically loaded extractors.

This package contains:
- ExtractorRegistry: Central registry for managing extractors
- Generated extractors organized by domain (sct/, 10k/, etc.)

Example:
    >>> from edgar_analyzer.extractors import ExtractorRegistry
    >>> registry = ExtractorRegistry()
    >>> extractor_class = registry.get("sct_extractor")
    >>> extractor = extractor_class(openrouter_client)
"""

from edgar_analyzer.extractors.registry import ExtractorMetadata, ExtractorRegistry

__all__ = ["ExtractorRegistry", "ExtractorMetadata"]
