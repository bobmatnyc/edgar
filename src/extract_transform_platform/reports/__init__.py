"""
Package: extract_transform_platform.reports

Purpose: Multi-format report generation with Protocol + ABC + Factory pattern.

Public API:
- ReportConfig, ExcelReportConfig, PDFReportConfig, DOCXReportConfig, PPTXReportConfig: Configuration models (Pydantic)
- IReportGenerator: Protocol interface (duck typing)
- BaseReportGenerator: Abstract base class (concrete helpers)
- ExcelReportGenerator: Excel report generator (openpyxl)
- PDFReportGenerator: PDF report generator (reportlab)
- DOCXReportGenerator: DOCX report generator (python-docx)
- PPTXReportGenerator: PPTX report generator (python-pptx)
- ReportGeneratorFactory: Factory for format selection

Status: Phase 3B - Core Interface + Excel + PDF + DOCX + PPTX Support (1M-360 FINAL)

Usage Example:
    >>> from extract_transform_platform.reports import (
    ...     ReportGeneratorFactory,
    ...     ExcelReportConfig,
    ...     PDFReportConfig,
    ...     DOCXReportConfig
    ... )
    >>>
    >>> # Create Excel generator via factory
    >>> generator = ReportGeneratorFactory.create("excel")
    >>> config = ExcelReportConfig(
    ...     title="Sales Report Q4",
    ...     freeze_header=True,
    ...     auto_filter=True
    ... )
    >>> output = generator.generate(data, Path("report.xlsx"), config)
    >>>
    >>> # Create PDF generator via factory
    >>> pdf_generator = ReportGeneratorFactory.create("pdf")
    >>> pdf_config = PDFReportConfig(
    ...     title="Sales Report Q4",
    ...     table_style="grid",
    ...     include_page_numbers=True
    ... )
    >>> pdf_output = pdf_generator.generate(data, Path("report.pdf"), pdf_config)
    >>>
    >>> # Create DOCX generator via factory
    >>> docx_generator = ReportGeneratorFactory.create("docx")
    >>> docx_config = DOCXReportConfig(
    ...     title="Sales Report Q4",
    ...     table_style="Light Grid Accent 1",
    ...     table_alignment="center"
    ... )
    >>> docx_output = docx_generator.generate(data, Path("report.docx"), docx_config)

Design Pattern: Protocol + ABC + Factory (following BaseDataSource precedent)
- IReportGenerator (Protocol): Duck typing interface
- BaseReportGenerator (ABC): Concrete base with helpers
- ReportGeneratorFactory: Centralized format selection
"""

# Interfaces
# Configuration models
from .base import (
    BaseReportGenerator,
    DOCXReportConfig,
    ExcelReportConfig,
    IReportGenerator,
    PDFReportConfig,
    PPTXReportConfig,
    ReportConfig,
)

# Generators
from .docx_generator import DOCXReportGenerator
from .excel_generator import ExcelReportGenerator

# Factory
from .factory import ReportGeneratorFactory
from .pdf_generator import PDFReportGenerator
from .pptx_generator import PPTXReportGenerator

__all__ = [
    # Configuration
    "ReportConfig",
    "ExcelReportConfig",
    "PDFReportConfig",
    "DOCXReportConfig",
    "PPTXReportConfig",
    # Interfaces
    "IReportGenerator",
    "BaseReportGenerator",
    # Generators
    "ExcelReportGenerator",
    "PDFReportGenerator",
    "DOCXReportGenerator",
    "PPTXReportGenerator",
    # Factory
    "ReportGeneratorFactory",
]

__version__ = "0.1.0"
