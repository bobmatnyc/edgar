"""
EDGAR WRAPPER: project_config.py

DEPRECATED: This module is a compatibility wrapper for legacy EDGAR code.

NEW CODE SHOULD USE:
    from extract_transform_platform.models.project_config import ProjectConfig

This wrapper maintains backward compatibility while all code is migrated
to use the platform package.

Migration Status: COMPLETE (1M-378, T3)
- Core models migrated to: extract_transform_platform.models.project_config
- Code reuse: 100% (805 LOC preserved)
- Tests: 0 breaking changes
"""

# Re-export all models from platform package
from extract_transform_platform.models.project_config import (  # Enumerations; Authentication; Caching; Rate Limiting; Data Sources; Examples; Validation; Output; Runtime; Project Metadata; Root Config; Schema Version
    SCHEMA_VERSION,
    SUPPORTED_OUTPUT_FORMATS,
    SUPPORTED_SOURCE_TYPES,
    AuthConfig,
    AuthType,
    CacheConfig,
    DataSourceConfig,
    DataSourceType,
    ErrorStrategy,
    ExampleConfig,
    FieldConstraint,
    FieldType,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    ProjectConfig,
    ProjectMetadata,
    RateLimitConfig,
    RuntimeConfig,
    ValidationConfig,
)

__all__ = [
    # Enumerations
    "DataSourceType",
    "AuthType",
    "OutputFormat",
    "ErrorStrategy",
    "FieldType",
    # Authentication
    "AuthConfig",
    # Caching
    "CacheConfig",
    # Rate Limiting
    "RateLimitConfig",
    # Data Sources
    "DataSourceConfig",
    # Examples
    "ExampleConfig",
    # Validation
    "FieldConstraint",
    "ValidationConfig",
    # Output
    "OutputDestinationConfig",
    "OutputConfig",
    # Runtime
    "RuntimeConfig",
    # Project Metadata
    "ProjectMetadata",
    # Root Config
    "ProjectConfig",
    # Schema Version
    "SCHEMA_VERSION",
    "SUPPORTED_SOURCE_TYPES",
    "SUPPORTED_OUTPUT_FORMATS",
]
