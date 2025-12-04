"""
Models Module

Pydantic models for project configuration and data structures.

Components:
- project_config: Project configuration model (MIGRATED ✅)
- transformation_pattern: Transformation pattern models
- patterns: Pattern models for schema analysis and transformation (MIGRATED ✅)
- plan: Code generation plan models (MIGRATED ✅)
- validation: Constraint validation models (MIGRATED ✅)

Status: Week 1, Phase 1 - T3 Complete
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
    FilteredParsedExamples,
    PromptSection,
    GeneratedPrompt,
)

# Project configuration models (T3 - Migrated from EDGAR)
from extract_transform_platform.models.project_config import (
    ProjectConfig,
    ProjectMetadata,
    DataSourceConfig,
    DataSourceType,
    AuthConfig,
    AuthType,
    CacheConfig,
    RateLimitConfig,
    ExampleConfig,
    ValidationConfig,
    FieldConstraint,
    FieldType,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    RuntimeConfig,
    ErrorStrategy,
)

# Plan models (T3 - Migrated from EDGAR)
from extract_transform_platform.models.plan import (
    MethodSpec,
    ClassSpec,
    PlanSpec,
    GeneratedCode,
    GenerationContext,
    CodeValidationResult,
    GenerationProgress,
)

# Validation models (T3 - Migrated from EDGAR)
from extract_transform_platform.models.validation import (
    Severity,
    Violation,
    ValidationResult,
    ConstraintConfig,
)

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
    "FilteredParsedExamples",
    "PromptSection",
    "GeneratedPrompt",
    # Project configuration models
    "ProjectConfig",
    "ProjectMetadata",
    "DataSourceConfig",
    "DataSourceType",
    "AuthConfig",
    "AuthType",
    "CacheConfig",
    "RateLimitConfig",
    "ExampleConfig",
    "ValidationConfig",
    "FieldConstraint",
    "FieldType",
    "OutputConfig",
    "OutputDestinationConfig",
    "OutputFormat",
    "RuntimeConfig",
    "ErrorStrategy",
    # Plan models
    "MethodSpec",
    "ClassSpec",
    "PlanSpec",
    "GeneratedCode",
    "GenerationContext",
    "CodeValidationResult",
    "GenerationProgress",
    # Validation models
    "Severity",
    "Violation",
    "ValidationResult",
    "ConstraintConfig",
    # Transformation patterns (TODO)
    "TransformationPattern",
]
