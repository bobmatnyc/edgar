"""
Backward Compatibility Wrapper - DEPRECATED

This module is DEPRECATED and maintained only for backward compatibility.
All code has been migrated to extract_transform_platform.core.base

Please update imports to:
    from extract_transform_platform.core import BaseDataSource, IDataSource

Migration Status: Complete (T2) - This is now a thin wrapper
Code Reuse: 100% (imports from platform)

History:
- Original: 295 LOC (BaseDataSource + IDataSource)
- Migrated: extract_transform_platform.core.base (100% generic)
- Current: 30 LOC (backward compatibility wrapper)
- Net LOC Impact: -265 lines (removed duplicates)
"""

import warnings
from extract_transform_platform.core.base import BaseDataSource, IDataSource

# Emit deprecation warning on import
warnings.warn(
    "edgar_analyzer.data_sources.base is deprecated. "
    "Import from extract_transform_platform.core instead:\n"
    "  from extract_transform_platform.core import BaseDataSource, IDataSource",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['BaseDataSource', 'IDataSource']

# Legacy logger for any existing code that references it
import logging
logger = logging.getLogger(__name__)
