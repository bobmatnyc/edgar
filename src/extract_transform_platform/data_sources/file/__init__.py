"""
File Data Sources

Data source implementations for file-based formats.

Supported Formats:
- Excel (.xlsx, .xls) - MIGRATED ✅ (90% reuse, 398 LOC)
- PDF (.pdf) - MIGRATED ✅ (77% coverage, 481 LOC)
- File (CSV, JSON, YAML, TXT) - MIGRATED ✅ (100% reuse, 286 LOC)
- DOCX (.docx) - Phase 3 planned (research complete)

Status: Week 1-2, Phase 1 - Migration in progress
"""

from extract_transform_platform.data_sources.file.excel_source import ExcelDataSource
from extract_transform_platform.data_sources.file.file_source import FileDataSource
from extract_transform_platform.data_sources.file.pdf_source import PDFDataSource

# TODO: from extract_transform_platform.data_sources.file.csv_source import CSVDataSource
# TODO: from extract_transform_platform.data_sources.file.docx_source import DOCXDataSource

__all__ = [
    "ExcelDataSource",
    "FileDataSource",
    "PDFDataSource",
    # "CSVDataSource",
    # "DOCXDataSource",
]
