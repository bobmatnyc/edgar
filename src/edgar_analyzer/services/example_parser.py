"""
DEPRECATED: Example Parser service (backward compatibility wrapper)

This module is deprecated and will be removed in a future version.
Use extract_transform_platform.services.analysis.example_parser instead.

Migration Note:
    Old: from edgar_analyzer.services.example_parser import ExampleParser
    New: from extract_transform_platform.services.analysis import ExampleParser

Deprecation Timeline:
    - Added: 2025-11-29 (Phase 2 - T3 Extract Schema Analyzer)
    - Removal: TBD (after Phase 3 completion)
"""

import warnings
from typing import Any

# Import platform version
from extract_transform_platform.services.analysis.example_parser import (
    ExampleParser as _PlatformExampleParser,
)

warnings.warn(
    "edgar_analyzer.services.example_parser is deprecated. "
    "Use extract_transform_platform.services.analysis.example_parser instead. "
    "This compatibility wrapper will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


class ExampleParser(_PlatformExampleParser):
    """
    DEPRECATED: Use extract_transform_platform.services.analysis.ExampleParser

    This is a backward compatibility wrapper that delegates to the platform
    version. All functionality has been migrated to the generic platform.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with deprecation warning."""
        super().__init__(*args, **kwargs)


# Export for backward compatibility
__all__ = ["ExampleParser"]
