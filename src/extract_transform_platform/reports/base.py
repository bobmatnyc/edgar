"""
Module: extract_transform_platform.reports.base

Purpose: Base classes and interfaces for report generation.

Contains:
- ReportConfig: Base configuration for all report generators (Pydantic)
- ExcelReportConfig: Excel-specific configuration (Pydantic)
- IReportGenerator: Protocol defining report generator interface
- BaseReportGenerator: Abstract base class with common functionality

Design Pattern: Protocol + ABC + Factory (following BaseDataSource precedent)
- IReportGenerator (Protocol): Duck typing interface for flexibility
- BaseReportGenerator (ABC): Concrete base with shared logic
- Factory pattern in factory.py for format selection

Status: Phase 1 - Core Interface + Excel Support (1M-360)

Code Reuse: Pattern migrated from BaseDataSource (100% proven pattern)
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Protocol, runtime_checkable

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Configuration Models
# ============================================================================


class ReportConfig(BaseModel):
    """Base configuration for all report generators.

    This is the parent class for all format-specific configurations.
    Provides common settings shared across all report formats.

    Design Decision: Pydantic models for type safety
    - Runtime validation of configuration values
    - JSON serialization for config files
    - Clear error messages for invalid configs
    - IDE autocomplete support

    Attributes:
        title: Report title (displayed in header/metadata)
        author: Report author (default: "EDGAR Platform")
        include_timestamp: Include generation timestamp in report
        page_size: Page size for paginated formats (letter, A4, legal)
    """

    title: str = Field(..., description="Report title")
    author: str = Field(default="EDGAR Platform", description="Report author")
    include_timestamp: bool = Field(
        default=True, description="Include generation timestamp"
    )
    page_size: str = Field(
        default="letter",
        description="Page size (letter, A4, legal)",
        pattern="^(letter|a4|legal)$",
    )

    model_config = {
        "frozen": False,  # Allow modification after creation
        "validate_assignment": True,  # Validate on assignment
    }


class ExcelReportConfig(ReportConfig):
    """Excel-specific configuration.

    Extends ReportConfig with Excel-specific settings for workbook,
    worksheet, and formatting options.

    Design Decision: Excel-specific features
    - Freeze header row for easier navigation
    - Auto-filter for data analysis
    - Custom column widths for readability
    - Sheet naming for organization

    Attributes:
        sheet_name: Worksheet name (default: "Report")
        freeze_header: Freeze top row for scrolling
        auto_filter: Enable auto-filter on header row
        column_widths: Custom column widths (column_name: width_in_chars)
        include_summary: Include summary statistics sheet
    """

    sheet_name: str = Field(default="Report", description="Sheet name")
    freeze_header: bool = Field(default=True, description="Freeze top row")
    auto_filter: bool = Field(default=True, description="Enable auto-filter")
    column_widths: Dict[str, int] = Field(
        default_factory=dict, description="Column widths (column_name: width)"
    )
    include_summary: bool = Field(default=False, description="Include summary sheet")


class PDFReportConfig(ReportConfig):
    """PDF-specific configuration.

    Extends ReportConfig with PDF-specific settings for page layout,
    margins, fonts, and table styling using reportlab.

    Design Decision: PDF-specific features
    - Page orientation for different report layouts
    - Custom margins for professional appearance
    - Font customization for branding
    - Table styles (grid, simple, fancy) for different aesthetics
    - Headers/footers for document context
    - Page numbers for navigation

    Attributes:
        page_orientation: Page orientation (portrait, landscape)
        margin_top: Top margin in inches (default: 0.75)
        margin_bottom: Bottom margin in inches (default: 0.75)
        margin_left: Left margin in inches (default: 0.75)
        margin_right: Right margin in inches (default: 0.75)
        font_name: Font family (Helvetica, Times-Roman, Courier)
        font_size: Base font size in points (default: 10)
        table_style: Table style (grid, simple, fancy)
        include_page_numbers: Include page numbers in footer
        header_text: Optional header text (appears on all pages)
        footer_text: Optional footer text (appears on all pages)
    """

    page_orientation: str = Field(
        default="portrait",
        description="Page orientation (portrait, landscape)",
        pattern="^(portrait|landscape)$",
    )
    margin_top: float = Field(
        default=0.75, description="Top margin (inches)", ge=0.0, le=2.0
    )
    margin_bottom: float = Field(
        default=0.75, description="Bottom margin (inches)", ge=0.0, le=2.0
    )
    margin_left: float = Field(
        default=0.75, description="Left margin (inches)", ge=0.0, le=2.0
    )
    margin_right: float = Field(
        default=0.75, description="Right margin (inches)", ge=0.0, le=2.0
    )
    font_name: str = Field(
        default="Helvetica",
        description="Font family",
        pattern="^(Helvetica|Times-Roman|Courier)$",
    )
    font_size: int = Field(default=10, description="Base font size", ge=8, le=16)
    table_style: str = Field(
        default="grid",
        description="Table style (grid, simple, fancy)",
        pattern="^(grid|simple|fancy)$",
    )
    include_page_numbers: bool = Field(default=True, description="Include page numbers")
    header_text: str | None = Field(default=None, description="Header text")
    footer_text: str | None = Field(default=None, description="Footer text")


class DOCXReportConfig(ReportConfig):
    """DOCX-specific configuration.

    Extends ReportConfig with DOCX-specific settings for document structure,
    table styling, and formatting using python-docx.

    Design Decision: DOCX-specific features
    - Heading levels for document structure (1-9)
    - Table styles from python-docx built-ins
    - Custom fonts for branding
    - Table alignment for professional appearance
    - Table of contents for navigation
    - Page breaks for document organization

    Attributes:
        heading_level: Title heading level (default: 1, range: 1-9)
        table_style: Table style name from python-docx (default: "Light Grid Accent 1")
        font_name: Document font (default: "Calibri")
        font_size: Base font size in points (default: 11)
        include_toc: Include table of contents (default: False)
        page_break_after_title: Page break after title (default: False)
        table_alignment: Table alignment - left, center, right (default: "center")
    """

    heading_level: int = Field(
        default=1, description="Title heading level (1-9)", ge=1, le=9
    )
    table_style: str = Field(
        default="Light Grid Accent 1", description="Table style name"
    )
    font_name: str = Field(default="Calibri", description="Document font")
    font_size: int = Field(default=11, description="Base font size (pt)", ge=8, le=16)
    include_toc: bool = Field(default=False, description="Include table of contents")
    page_break_after_title: bool = Field(
        default=False, description="Page break after title"
    )
    table_alignment: str = Field(
        default="center",
        description="Table alignment (left, center, right)",
        pattern="^(left|center|right)$",
    )


class PPTXReportConfig(ReportConfig):
    """PPTX-specific configuration.

    Extends ReportConfig with PPTX-specific settings for slide layout,
    tables, charts, and styling using python-pptx.

    Design Decision: PPTX-specific features
    - Slide layouts for professional presentations
    - Theme colors for branding consistency
    - Custom fonts for readability
    - Table styling with headers
    - Chart types for data visualization (bar, column, line, pie)
    - Multi-slide pagination for large datasets

    Attributes:
        slide_layout: Slide layout name (default: "Title and Content")
        theme_color: Theme color in hex format (default: "#366092")
        font_name: Font family (default: "Calibri")
        font_size: Base font size in points (default: 14)
        table_style: Table style name (default: "Medium Style 2 - Accent 1")
        include_chart: Include chart slide (default: False)
        chart_type: Chart type - bar, column, line, pie (default: "bar")
        max_rows_per_slide: Maximum table rows per slide (default: 10)
    """

    slide_layout: str = Field(
        default="Title and Content", description="Slide layout name"
    )
    theme_color: str = Field(
        default="#366092",
        description="Theme color (hex format)",
        pattern="^#[0-9A-Fa-f]{6}$",
    )
    font_name: str = Field(default="Calibri", description="Font family")
    font_size: int = Field(default=14, description="Base font size (pt)", ge=10, le=24)
    table_style: str = Field(
        default="Medium Style 2 - Accent 1", description="Table style name"
    )
    include_chart: bool = Field(default=False, description="Include chart slide")
    chart_type: str = Field(
        default="bar",
        description="Chart type (bar, column, line, pie)",
        pattern="^(bar|column|line|pie)$",
    )
    max_rows_per_slide: int = Field(
        default=10, description="Maximum table rows per slide", ge=5, le=50
    )


# ============================================================================
# Protocol Interface (Duck Typing)
# ============================================================================


@runtime_checkable
class IReportGenerator(Protocol):
    """Protocol for report generators - duck typing interface.

    This is a structural type (Protocol) allowing any class that implements
    these methods to be used as a report generator, regardless of inheritance.

    Design Decision: Protocol over pure ABC
    - Allows duck typing (structural subtyping)
    - No inheritance required
    - More flexible for external integrations
    - Can check compliance with isinstance() at runtime

    Usage Pattern:
        >>> generator = ExcelReportGenerator()
        >>> if isinstance(generator, IReportGenerator):
        ...     output_path = generator.generate(data, path, config)

    Performance:
    - isinstance() check: O(1) with @runtime_checkable
    - No runtime overhead for method calls (pure duck typing)
    """

    def generate(self, data: Any, output_path: Path, config: ReportConfig) -> Path:
        """Generate report from data.

        Args:
            data: Report data (DataFrame, dict, list, or custom type)
            output_path: Output file path (with appropriate extension)
            config: Report configuration (format-specific subclass)

        Returns:
            Path to generated report file

        Raises:
            TypeError: If data format is unsupported
            ValueError: If output path has wrong extension
            IOError: If file cannot be written

        Design Notes:
        - Accept multiple data formats (DataFrame, dict, list)
        - Validate output path extension matches generator format
        - Create parent directories if they don't exist
        - Return absolute path for clarity
        """
        ...

    def get_supported_features(self) -> List[str]:
        """Return list of supported features.

        Features may include:
        - "tables": Tabular data rendering
        - "formatting": Cell/text formatting (bold, colors, etc.)
        - "formulas": Computed fields
        - "charts": Data visualization
        - "multiple_sheets": Multiple sheets/pages
        - "freeze_panes": Frozen header rows/columns
        - "auto_filter": Filterable columns
        - "images": Embedded images
        - "hyperlinks": Clickable links

        Returns:
            List of feature names supported by this generator

        Design Notes:
        - Used for capability detection by clients
        - Features are strings for easy extension
        - Future: Consider feature flags enum for type safety
        """
        ...


# ============================================================================
# Abstract Base Class (Concrete Implementation Base)
# ============================================================================


class BaseReportGenerator(ABC):
    """Abstract base class for report generators.

    Provides common functionality for all report generators:
    - Feature tracking
    - Output path validation
    - Directory creation
    - Logging

    Design Decision: ABC with concrete helper methods
    - Subclasses must implement abstract methods (generate)
    - Subclasses can use concrete helper methods (_validate_output_path)
    - Reduces code duplication across generators
    - Enforces consistent error handling

    Code Reuse: Pattern from BaseDataSource
    - Similar structure: Protocol + ABC + concrete helpers
    - Cache/retry logic not needed (local file operations)
    - Focus on validation and error handling

    Performance Analysis:
    - Time Complexity: O(1) for validation, O(n) for generation (n = data size)
    - Space Complexity: O(m) where m = output file size
    - No caching needed (reports are typically one-time operations)
    """

    def __init__(self) -> None:
        """Initialize base report generator.

        Subclasses should call super().__init__() and set _supported_features.
        """
        self._supported_features: List[str] = []
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def generate(self, data: Any, output_path: Path, config: ReportConfig) -> Path:
        """Generate report - must be implemented by subclasses.

        This is the core method that each generator must implement.
        Implementation should:
        1. Validate input data format
        2. Validate output path extension
        3. Convert data to generator-specific format if needed
        4. Apply configuration settings
        5. Write report to output_path
        6. Return absolute path to generated file

        Args:
            data: Report data
            output_path: Output file path
            config: Report configuration

        Returns:
            Path to generated report

        Raises:
            NotImplementedError: If called on base class
        """
        pass

    def get_supported_features(self) -> List[str]:
        """Return supported features.

        Concrete implementation that subclasses can override if needed.

        Returns:
            Copy of supported features list (defensive copy)

        Design Decision: Return copy, not reference
        - Prevents external modification of internal list
        - Follows immutability principle
        - Small performance cost for safety
        """
        return self._supported_features.copy()

    def _validate_output_path(self, output_path: Path, extension: str) -> None:
        """Validate output path has correct extension.

        Helper method for subclasses to validate file extensions.

        Args:
            output_path: Output file path to validate
            extension: Expected extension (e.g., ".xlsx", ".pdf")

        Raises:
            ValueError: If extension doesn't match

        Side Effects:
        - Creates parent directories if they don't exist

        Design Decision: Fail early on validation
        - Better to fail before processing data
        - Clear error messages for users
        - Automatic directory creation for convenience
        """
        if output_path.suffix.lower() != extension.lower():
            raise ValueError(
                f"Output path must have {extension} extension, "
                f"got {output_path.suffix}"
            )

        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Validated output path: {output_path}")

    def _validate_data_not_empty(self, data: Any, data_type_name: str = "data") -> None:
        """Validate that data is not None or empty.

        Helper method for subclasses to validate data presence.

        Args:
            data: Data to validate
            data_type_name: Name of data type for error messages

        Raises:
            ValueError: If data is None or empty

        Design Decision: Explicit validation over silent failures
        - Better to fail with clear error than produce empty reports
        - Helps catch bugs early in pipeline
        """
        if data is None:
            raise ValueError(f"{data_type_name} cannot be None")

        # Check for empty containers
        if hasattr(data, "__len__") and len(data) == 0:
            raise ValueError(f"{data_type_name} cannot be empty")

        logger.debug(f"Validated {data_type_name} is not empty")
