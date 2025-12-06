"""
EDGAR WRAPPER: validation.py

DEPRECATED: This module is a compatibility wrapper for legacy EDGAR code.

NEW CODE SHOULD USE:
    from extract_transform_platform.models.validation import ValidationResult

This wrapper maintains backward compatibility while all code is migrated
to use the platform package.

Migration Status: COMPLETE (1M-378, T3)
- Core models migrated to: extract_transform_platform.models.validation
- Code reuse: 100% (178 LOC preserved)
- Tests: 0 breaking changes
"""

# Re-export all models from platform package
from extract_transform_platform.models.validation import (
    ConstraintConfig,
    Severity,
    ValidationResult,
    Violation,
)

__all__ = [
    "Severity",
    "Violation",
    "ValidationResult",
    "ConstraintConfig",
]
