"""
Schema analysis service for Example Parser.

DEPRECATION WARNING: This module has been migrated to the generic platform.
Use: from extract_transform_platform.services.analysis import SchemaAnalyzer

This backward compatibility wrapper will be maintained during Phase 2 migration.

Original Documentation:
-----------------------
This service infers data schemas from example input/output pairs and identifies
structural differences that indicate transformation patterns.

Design Decisions:
- **Type Inference**: Analyze actual values to determine types (not declarations)
- **Null Handling**: Track nullability separately from type
- **Nested Structure Support**: Handle arbitrarily nested dicts and lists
- **Path-Based Addressing**: Use dot notation for nested fields (e.g., "main.temp")

Performance:
- Time Complexity: O(n * m) where n=examples, m=fields per example
- Space Complexity: O(f) where f=total unique fields across examples
- Typical Performance: <100ms for 10 examples with 50 fields each

Migration Status:
    Migrated to: extract_transform_platform.services.analysis.schema_analyzer
    Migration Ticket: 1M-378 (T3 - Extract Schema Analyzer)
    Migration Date: 2025-11-29
    Deprecation Notice: Phase 2, Batch 2 of 3
"""

import warnings

# Import from platform - this is now the canonical implementation
from extract_transform_platform.services.analysis.schema_analyzer import (
    SchemaAnalyzer as _PlatformSchemaAnalyzer,
)

# Show deprecation warning on import
warnings.warn(
    "edgar_analyzer.services.schema_analyzer is deprecated. "
    "Use extract_transform_platform.services.analysis.SchemaAnalyzer instead. "
    "This wrapper will be removed in Phase 3.",
    DeprecationWarning,
    stacklevel=2,
)


class SchemaAnalyzer(_PlatformSchemaAnalyzer):
    """Backward compatibility wrapper for SchemaAnalyzer.

    DEPRECATED: Use extract_transform_platform.services.analysis.SchemaAnalyzer instead.

    This wrapper inherits all functionality from the platform implementation.
    No additional code needed - all methods are inherited from the parent class.

    Example:
        >>> # OLD (deprecated)
        >>> from edgar_analyzer.services.schema_analyzer import SchemaAnalyzer
        >>>
        >>> # NEW (preferred)
        >>> from extract_transform_platform.services.analysis import SchemaAnalyzer
    """
    pass


# For backward compatibility, re-export pattern models
from edgar_analyzer.models.patterns import (  # noqa: E402
    FieldTypeEnum,
    Schema,
    SchemaField,
    SchemaDifference,
)

__all__ = [
    "SchemaAnalyzer",
    "FieldTypeEnum",
    "Schema",
    "SchemaField",
    "SchemaDifference",
]


# ORIGINAL IMPLEMENTATION MOVED TO PLATFORM
# ==========================================
# The complete implementation has been migrated to:
# extract_transform_platform.services.analysis.schema_analyzer
#
# Original file: 432 LOC
# Platform file: 432 LOC (100% preserved)
# EDGAR-specific code: 0% (fully generic)
#
# This wrapper maintains backward compatibility during Phase 2 migration.
# The wrapper will be removed in Phase 3.
