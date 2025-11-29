"""
File Data Source - Backward Compatibility Wrapper

DEPRECATED: This module is deprecated and will be removed in a future version.
Please use extract_transform_platform.data_sources.file.file_source instead.

Migration Path:
    # Old (deprecated)
    from edgar_analyzer.data_sources.file_source import FileDataSource

    # New (platform)
    from extract_transform_platform.data_sources.file import FileDataSource

This wrapper provides backward compatibility during the migration period.
"""

import warnings

from extract_transform_platform.data_sources.file.file_source import FileDataSource

# Emit deprecation warning
warnings.warn(
    "edgar_analyzer.data_sources.file_source is deprecated. "
    "Use extract_transform_platform.data_sources.file.file_source instead. "
    "This module will be removed in version 2.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["FileDataSource"]
