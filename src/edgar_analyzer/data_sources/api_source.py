"""
DEPRECATED: Backward Compatibility Wrapper for APIDataSource

This module provides backward compatibility for existing EDGAR code.
New code should import from the platform package:

    from extract_transform_platform.data_sources.web import APIDataSource

Migration Status: COMPLETE
- Platform version: src/extract_transform_platform/data_sources/web/api_source.py
- All functionality preserved (100% code reuse)
- Deprecation warnings added

Removal Timeline: After all EDGAR code migrated (estimated: 2 weeks)
"""

import warnings
from extract_transform_platform.data_sources.web.api_source import APIDataSource as _PlatformAPIDataSource


# Issue deprecation warning on import
warnings.warn(
    "edgar_analyzer.data_sources.api_source is deprecated. "
    "Use 'from extract_transform_platform.data_sources.web import APIDataSource' instead. "
    "This wrapper will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)


# Re-export platform class for backward compatibility
class APIDataSource(_PlatformAPIDataSource):
    """Backward compatibility wrapper for APIDataSource.

    DEPRECATED: Import from extract_transform_platform.data_sources.web instead.

    This wrapper will be removed after EDGAR code is fully migrated.
    """
    pass


__all__ = ["APIDataSource"]
