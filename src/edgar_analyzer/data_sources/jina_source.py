"""
DEPRECATED: Jina.ai Data Source (EDGAR compatibility wrapper)

This module is deprecated and maintained only for backward compatibility.
New code should use: extract_transform_platform.data_sources.web.JinaDataSource

Migration Guide:
    # OLD (EDGAR-specific)
    from edgar_analyzer.data_sources import JinaDataSource

    # NEW (Platform-generic)
    from extract_transform_platform.data_sources import JinaDataSource

Status: DEPRECATED - Use platform version
Removal: Planned for Phase 3 (after EDGAR migration complete)
"""

import warnings

# Import from platform version
from extract_transform_platform.data_sources.web.jina_source import JinaDataSource as _PlatformJinaDataSource


class JinaDataSource(_PlatformJinaDataSource):
    """DEPRECATED: Backward compatibility wrapper for JinaDataSource.

    This class is deprecated. Use extract_transform_platform.data_sources.JinaDataSource instead.

    All functionality has been migrated to the platform package.
    This wrapper exists only for backward compatibility with existing EDGAR code.
    """

    def __init__(self, *args, **kwargs):
        """Initialize JinaDataSource with deprecation warning."""
        warnings.warn(
            "edgar_analyzer.data_sources.JinaDataSource is deprecated. "
            "Use extract_transform_platform.data_sources.JinaDataSource instead. "
            "This compatibility wrapper will be removed in Phase 3.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


# Re-export for backward compatibility
__all__ = ["JinaDataSource"]
