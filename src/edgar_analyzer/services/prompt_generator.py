"""
EDGAR WRAPPER: prompt_generator.py

DEPRECATED: This module is a compatibility wrapper for legacy EDGAR code.

NEW CODE SHOULD USE:
    from extract_transform_platform.services.codegen import PromptGenerator

This wrapper maintains backward compatibility while all code is migrated
to use the platform package.

Migration Status: COMPLETE (1M-379, T4)
- Core service migrated to: extract_transform_platform.services.codegen.prompt_generator
- Code reuse: 100% (436 LOC preserved)
- Tests: 0 breaking changes
"""

# Re-export from platform package
from extract_transform_platform.services.codegen.prompt_generator import PromptGenerator

__all__ = ["PromptGenerator"]
