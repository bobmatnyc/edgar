"""
Services Module

Shared services for the extract & transform platform.

Components:
- cache_service: Response caching and cache management
- analysis: Schema inference, pattern detection, code generation

Status: Week 1, Phase 1 - Migration from edgar_analyzer
Phase 2 Additions: Schema analysis services (T3 - Extract Schema Analyzer)
"""

# TODO: from extract_transform_platform.services.cache_service import CacheService
from extract_transform_platform.services.analysis import ExampleParser, SchemaAnalyzer

__all__ = [
    "CacheService",
    "ExampleParser",
    "SchemaAnalyzer",
]
