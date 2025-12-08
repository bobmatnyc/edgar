"""
Extractor registry and dynamically loaded extractors.

This package contains:
- ExtractorRegistry: Central registry for managing extractors
- ExtractorSynthesizer: LLM-powered pattern analysis and code generation
- MetaExtractor: End-to-end orchestrator for creating extractors
- Generated extractors organized by domain (sct/, 10k/, etc.)

Example (Registry):
    >>> from edgar_analyzer.extractors import ExtractorRegistry
    >>> registry = ExtractorRegistry()
    >>> extractor_class = registry.get("sct_extractor")
    >>> extractor = extractor_class(openrouter_client)

Example (MetaExtractor):
    >>> from edgar_analyzer.extractors import MetaExtractor
    >>> from pathlib import Path
    >>> meta = MetaExtractor()
    >>> result = meta.create(
    ...     name="sct_extractor",
    ...     examples_dir=Path("examples/sct/"),
    ...     description="Extract Summary Compensation Tables"
    ... )
    >>> print(result.status)  # "success"
"""

from edgar_analyzer.extractors.registry import ExtractorMetadata, ExtractorRegistry
from edgar_analyzer.extractors.synthesizer import (
    ExtractorSynthesizer,
    GeneratedExtractor,
    PatternAnalysis,
)
from edgar_analyzer.extractors.meta_extractor import (
    CreateResult,
    DeploymentResult,
    MetaExtractor,
    ValidationResult,
)

__all__ = [
    # Registry
    "ExtractorRegistry",
    "ExtractorMetadata",
    # Synthesizer
    "ExtractorSynthesizer",
    "PatternAnalysis",
    "GeneratedExtractor",
    # MetaExtractor
    "MetaExtractor",
    "CreateResult",
    "ValidationResult",
    "DeploymentResult",
]
