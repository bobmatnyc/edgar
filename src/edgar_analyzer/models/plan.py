"""
EDGAR WRAPPER: plan.py

DEPRECATED: This module is a compatibility wrapper for legacy EDGAR code.

NEW CODE SHOULD USE:
    from extract_transform_platform.models.plan import PlanSpec, GeneratedCode

This wrapper maintains backward compatibility while all code is migrated
to use the platform package.

Migration Status: COMPLETE (1M-378, T3)
- Core models migrated to: extract_transform_platform.models.plan
- Code reuse: 100% (456 LOC preserved)
- Tests: 0 breaking changes
"""

# Re-export all models from platform package
from extract_transform_platform.models.plan import (  # PM Mode Outputs; Coder Mode Outputs; Generation Context; Validation Results
    ClassSpec,
    CodeValidationResult,
    GeneratedCode,
    GenerationContext,
    MethodSpec,
    PlanSpec,
)

__all__ = [
    # PM Mode Outputs
    "MethodSpec",
    "ClassSpec",
    "PlanSpec",
    # Coder Mode Outputs
    "GeneratedCode",
    # Generation Context
    "GenerationContext",
    # Validation Results
    "CodeValidationResult",
]
