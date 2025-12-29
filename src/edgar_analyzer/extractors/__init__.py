"""
Extractor registry and dynamically loaded extractors.

This package contains:
- ExtractorRegistry: Central registry for managing extractors
- ExtractorSynthesizer: LLM-powered pattern analysis and code generation
- MetaExtractor: End-to-end orchestrator for creating extractors
- SelfImprovementLoop: Iterative refinement based on test failures (Phase 4)
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

Example (SelfImprovementLoop):
    >>> from edgar_analyzer.extractors import SelfImprovementLoop, TestCase
    >>> loop = SelfImprovementLoop(meta_extractor, max_iterations=5)
    >>> result = await loop.run(
    ...     extractor_name="sct_extractor",
    ...     test_cases=[TestCase(input={...}, expected_output={...})],
    ...     target_accuracy=0.90
    ... )
    >>> print(f"Final accuracy: {result.final_accuracy}")
"""

from edgar_analyzer.extractors.meta_extractor import (
    CreateResult,
    DeploymentResult,
    MetaExtractor,
    ValidationResult,
)
from edgar_analyzer.extractors.registry import ExtractorMetadata, ExtractorRegistry
from edgar_analyzer.extractors.self_improvement import (
    DeploymentResult as SelfImprovementDeploymentResult,
)
from edgar_analyzer.extractors.self_improvement import (
    EvaluationResult,
    FailureAnalysis,
    FailureType,
    ImprovementResult,
    IterationHistory,
    SelfImprovementLoop,
    TestCase,
)
from edgar_analyzer.extractors.synthesizer import (
    ExtractorSynthesizer,
    GeneratedExtractor,
    PatternAnalysis,
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
    # SelfImprovementLoop (Phase 4)
    "SelfImprovementLoop",
    "TestCase",
    "FailureAnalysis",
    "FailureType",
    "EvaluationResult",
    "ImprovementResult",
    "IterationHistory",
    "SelfImprovementDeploymentResult",
]
