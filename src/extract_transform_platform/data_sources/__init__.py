"""
Data Sources Module

Provides data source implementations for various formats and protocols.

Submodules:
- file: File-based data sources (Excel, PDF, CSV, JSON, YAML, DOCX)
- web: Web-based data sources (URL, API, Jina.ai)

Status: Week 1-2, Phase 1 - Migration from edgar_analyzer.data_sources

Code Reuse Metrics:
- Excel: 90% from EDGAR (398 LOC, 80% coverage)
- PDF: 77% coverage (481 LOC, 51 tests)
- File: 100% from EDGAR (286 LOC, CSV/JSON/YAML/TXT support)
- URL: 100% from EDGAR (190 LOC, simple HTTP/HTTPS)
- API: 85% from EDGAR APIDataSource
"""

from extract_transform_platform.data_sources.file import (
    ExcelDataSource,
    FileDataSource,
    PDFDataSource,
)
from extract_transform_platform.data_sources.web import (
    APIDataSource,
    JinaDataSource,
    URLDataSource,
)

__all__ = [
    # File sources
    "ExcelDataSource",
    "FileDataSource",
    "PDFDataSource",
    # "CSVDataSource",  # Covered by FileDataSource
    # "DOCXDataSource",
    # Web sources
    "URLDataSource",
    "APIDataSource",
    "JinaDataSource",
]
