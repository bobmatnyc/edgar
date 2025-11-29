"""
PDF Data Source - Backward Compatibility Wrapper

DEPRECATED: This module is maintained for backward compatibility only.

New code should import from:
    from extract_transform_platform.data_sources.file import PDFDataSource

This wrapper will be removed in a future version after migration is complete.

Migration Status:
- PDFDataSource: ✅ Migrated to extract_transform_platform (481 LOC)
- Test Coverage: 77% (51 tests passing)
- Code Reuse: 100% from EDGAR (proven pattern)
"""

import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

# Import from platform (canonical source)
from extract_transform_platform.data_sources.file.pdf_source import (
    PDFDataSource as _PlatformPDFDataSource,
)


# Re-export with deprecation warning
class PDFDataSource(_PlatformPDFDataSource):
    """PDF file data source - backward compatibility wrapper.

    DEPRECATED: Import from extract_transform_platform.data_sources.file.PDFDataSource

    This wrapper maintains backward compatibility for existing EDGAR code.
    All functionality has been migrated to the platform.

    Example (OLD - deprecated):
        from edgar_analyzer.data_sources.pdf_source import PDFDataSource

    Example (NEW - preferred):
        from extract_transform_platform.data_sources.file import PDFDataSource
    """

    def __init__(
        self,
        file_path: Path,
        page_number: Union[int, str] = 0,
        table_bbox: Optional[Tuple[float, float, float, float]] = None,
        table_strategy: str = "lines",
        table_settings: Optional[Dict[str, Any]] = None,
        skip_rows: Optional[int] = None,
        max_rows: Optional[int] = None,
        **kwargs,
    ):
        """Initialize PDF data source with deprecation warning.

        See extract_transform_platform.data_sources.file.PDFDataSource for documentation.
        """
        warnings.warn(
            "edgar_analyzer.data_sources.pdf_source.PDFDataSource is deprecated. "
            "Import from extract_transform_platform.data_sources.file.PDFDataSource instead. "
            "This wrapper will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )

        super().__init__(
            file_path=file_path,
            page_number=page_number,
            table_bbox=table_bbox,
            table_strategy=table_strategy,
            table_settings=table_settings,
            skip_rows=skip_rows,
            max_rows=max_rows,
            **kwargs,
        )


# Maintain module-level exports for backward compatibility
__all__ = ["PDFDataSource"]
