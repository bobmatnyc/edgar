"""
Excel Data Source (Backward Compatibility Wrapper)

DEPRECATED: This module is a backward compatibility wrapper.
New code should import from: extract_transform_platform.data_sources.file.excel_source

Migration Status: COMPLETE ✅
- ExcelDataSource migrated to extract_transform_platform
- 100% generic implementation (no EDGAR dependencies)
- All existing EDGAR code continues to work via this wrapper
- No functional changes - pure import re-export

Original Implementation: 398 LOC, 80% test coverage, 35/35 validations
Migrated: 2024-11-29
Code Reuse: 90% (only import path changed)
"""

import warnings
from extract_transform_platform.data_sources.file.excel_source import (
    ExcelDataSource as _PlatformExcelDataSource,
)

# Issue deprecation warning on first import
warnings.warn(
    "edgar_analyzer.data_sources.excel_source is deprecated. "
    "Import from extract_transform_platform.data_sources.file.excel_source instead. "
    "This wrapper will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export ExcelDataSource for backward compatibility
ExcelDataSource = _PlatformExcelDataSource

__all__ = ["ExcelDataSource"]
