"""
Backward Compatibility Wrapper - DEPRECATED

This module is DEPRECATED and maintained only for backward compatibility.
All code has been migrated to extract_transform_platform.utils.rate_limiter

Please update imports to:
    from extract_transform_platform.utils import RateLimiter

Migration Status: Complete (T2) - This is now a thin wrapper
Code Reuse: 100% (imports from platform)

History:
- Original: 84 LOC (RateLimiter implementation)
- Migrated: extract_transform_platform.utils.rate_limiter (100% generic)
- Current: 20 LOC (backward compatibility wrapper)
- Net LOC Impact: -64 lines (removed duplicates)
"""

import warnings
from extract_transform_platform.utils.rate_limiter import RateLimiter

# Emit deprecation warning on import
warnings.warn(
    "edgar_analyzer.utils.rate_limiter is deprecated. "
    "Import from extract_transform_platform.utils instead:\n"
    "  from extract_transform_platform.utils import RateLimiter",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['RateLimiter']
