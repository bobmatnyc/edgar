"""
Models Module

Pydantic models for project configuration and data structures.

Components:
- project_config: Project configuration model
- transformation_pattern: Transformation pattern models
- patterns: Pattern models for schema analysis and transformation

Status: Week 1, Phase 1 - New implementations
"""

# Pattern models (T3 - Extract Schema Analyzer)
from extract_transform_platform.models.patterns import (
    Pattern,
    PatternType,
    FieldTypeEnum,
    SchemaField,
    Schema,
    SchemaDifference,
    ParsedExamples,
    PromptSection,
    GeneratedPrompt,
)

# TODO: from extract_transform_platform.models.project_config import ProjectConfig
# TODO: from extract_transform_platform.models.transformation_pattern import TransformationPattern

__all__ = [
    # Pattern models
    "Pattern",
    "PatternType",
    "FieldTypeEnum",
    "SchemaField",
    "Schema",
    "SchemaDifference",
    "ParsedExamples",
    "PromptSection",
    "GeneratedPrompt",
    # Project models (TODO)
    "ProjectConfig",
    "TransformationPattern",
]
