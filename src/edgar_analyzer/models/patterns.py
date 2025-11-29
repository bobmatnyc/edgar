"""
Pattern models for Example Parser system - DEPRECATED.

⚠️  DEPRECATION NOTICE ⚠️
This module has been migrated to the generic extract_transform_platform package.
Please update your imports:

    OLD: from edgar_analyzer.models.patterns import Pattern
    NEW: from extract_transform_platform.models.patterns import Pattern

This compatibility wrapper will be removed in a future release.

Migration: T3 - Extract Schema Analyzer (1M-378)
Date: 2025-11-29
"""

import warnings

# Import all models from platform package
from extract_transform_platform.models.patterns import (
    # Enumerations
    PatternType,
    FieldTypeEnum,
    # Pattern models
    Pattern,
    SchemaField,
    Schema,
    SchemaDifference,
    ParsedExamples,
    # Prompt generation models
    PromptSection,
    GeneratedPrompt,
)

# Issue deprecation warning
warnings.warn(
    "edgar_analyzer.models.patterns is deprecated. "
    "Use extract_transform_platform.models.patterns instead. "
    "This compatibility wrapper will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all models for backward compatibility
__all__ = [
    # Enumerations
    "PatternType",
    "FieldTypeEnum",
    # Pattern models
    "Pattern",
    "SchemaField",
    "Schema",
    "SchemaDifference",
    "ParsedExamples",
    # Prompt generation models
    "PromptSection",
    "GeneratedPrompt",
]
