"""
DEPRECATED: URLDataSource has been migrated to extract_transform_platform

This module provides backward compatibility for existing EDGAR code.
New code should import from:
    from extract_transform_platform.data_sources import URLDataSource

Migration Path:
1. Update imports to use platform package
2. Remove this wrapper once all references updated
3. Archive or delete this file

Status: Deprecated (2025-11-29)
Removal Target: End of Phase 2 migration
"""

import warnings

from extract_transform_platform.data_sources.web import URLDataSource

# Issue deprecation warning when imported
warnings.warn(
    "edgar_analyzer.data_sources.url_source is deprecated. "
    "Use extract_transform_platform.data_sources.URLDataSource instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["URLDataSource"]
