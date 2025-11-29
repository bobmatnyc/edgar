"""
PDF Data Source

Local PDF file data source supporting:
- Table extraction from PDF pages
- Multiple extraction strategies (lines, text, mixed)
- Bounding box-based table selection
- Schema-aware parsing
- Type auto-detection via pandas
- Compatible with SchemaAnalyzer

Features:
- No caching (files are already local)
- Automatic type conversion
- NaN handling (converts to None for JSON compatibility)
- Validation of file existence and format
- Detailed error messages
- Multiple table detection strategies

Future Enhancements (Phase 2):
- Multi-page extraction
- Multi-table per page support
- OCR integration for scanned PDFs
- Advanced table structure detection
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .base import BaseDataSource

logger = logging.getLogger(__name__)


class PDFDataSource(BaseDataSource):
    """PDF file data source with table extraction and schema-aware parsing.

    Design Decision: No caching for local files
    - Files are already on disk (caching adds overhead, no benefit)
    - File changes should be reflected immediately
    - Memory usage: Don't duplicate file content in cache

    Table Extraction Strategies:
    - "lines": Use explicit lines/borders to detect tables
    - "text": Use text positioning to infer table structure
    - "mixed": Combine lines (vertical) + text (horizontal)

    Performance Analysis:
    - Time Complexity: O(r * c) where r=rows, c=columns
    - Space Complexity: O(r * c) - full table loaded into memory
    - Bottleneck: pdfplumber table extraction + pandas conversion

    Optimization Opportunities:
    - For large PDFs (>10 pages), consider page-by-page streaming
    - For multi-table pages, lazy loading per table
    - For scanned PDFs, OCR preprocessing needed

    Example:
        # Extract first table from first page
        pdf_source = PDFDataSource(Path("invoices/invoice_001.pdf"))
        data = await pdf_source.fetch()
        print(f"Found {data['row_count']} invoice items")

        # Extract with specific bounding box
        pdf_source = PDFDataSource(
            Path("invoices/invoice_002.pdf"),
            page_number=0,
            table_bbox=(50, 100, 550, 400),
            table_strategy="lines"
        )
        data = await pdf_source.fetch()
        for row in data['rows']:
            print(row['Item'], row['Amount'])

        # Extract with row limits (for large tables)
        pdf_source = PDFDataSource(
            Path("invoices/large_invoice.pdf"),
            max_rows=100
        )
        data = await pdf_source.fetch()
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
        """Initialize PDF data source.

        Args:
            file_path: Path to PDF file (.pdf)
            page_number: Page number (int) or "all" for multi-page (0-indexed)
            table_bbox: Optional bounding box (x0, top, x1, bottom) to crop page
            table_strategy: Table detection strategy ("lines", "text", "mixed")
            table_settings: Optional pdfplumber table settings dict
            skip_rows: Number of rows to skip after header
            max_rows: Maximum rows to read (for large tables)
            **kwargs: Additional arguments passed to BaseDataSource

        Design Trade-offs:
        - UTF-8 default: Covers most PDF exports
        - No caching: Files are local (cache_enabled=False)
        - No rate limiting: Local I/O (rate_limit_per_minute=9999)
        - No retries: Local files fail fast (max_retries=0)

        Error Handling:
        - FileNotFoundError: If PDF file doesn't exist
        - ValueError: If file extension not .pdf
        """
        # Override base settings for local files
        kwargs["cache_enabled"] = False  # No caching needed for local files
        kwargs["rate_limit_per_minute"] = 9999  # No rate limiting for local I/O
        kwargs["max_retries"] = 0  # No retries for local files (fail fast)

        super().__init__(**kwargs)

        self.file_path = Path(file_path)
        self.page_number = page_number
        self.table_bbox = table_bbox
        self.table_strategy = table_strategy
        self.skip_rows = skip_rows
        self.max_rows = max_rows

        # Build table settings based on strategy
        self.table_settings = self._build_table_settings(table_settings)

        # Validate file exists
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Validate file extension
        if self.file_path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Unsupported file type: {self.file_path.suffix}. " f"Expected .pdf"
            )

        logger.info(
            f"Initialized PDFDataSource for {self.file_path.name} "
            f"(page={page_number}, strategy={table_strategy})"
        )

    def _build_table_settings(self, custom_settings: Optional[Dict]) -> Dict[str, Any]:
        """Build pdfplumber table settings based on strategy.

        Args:
            custom_settings: Optional custom settings to merge with defaults

        Returns:
            Complete table settings dict for pdfplumber

        Design Decision: Strategy-based defaults
        - "lines": Best for bordered tables (invoices, reports)
        - "text": Best for borderless tables (plain text layouts)
        - "mixed": Hybrid approach for partially bordered tables
        """
        base_settings = {
            "lines": {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
            },
            "text": {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
            },
            "mixed": {
                "vertical_strategy": "lines",
                "horizontal_strategy": "text",
            },
        }

        settings = base_settings.get(self.table_strategy, base_settings["lines"])
        if custom_settings:
            settings.update(custom_settings)
        return settings

    async def fetch(self, **kwargs) -> Dict[str, Any]:
        """Read PDF file and return structured data.

        Returns:
            Dictionary with keys:
                - rows: List[Dict] - Each row as dictionary (cleaned)
                - columns: List[str] - Column names
                - page_number: int - Active page number
                - row_count: int - Number of data rows
                - source_file: str - Original file path
                - file_name: str - File name only

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If page not found or invalid parameters
            ImportError: If pdfplumber or pandas not installed
            RuntimeError: If PDF parsing fails

        Performance:
        - Time Complexity: O(r * c) where r=rows, c=columns
        - Space Complexity: O(r * c) - full data in memory
        - I/O: Single read operation via pdfplumber
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")

        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {self.file_path}")

        logger.debug(f"Reading PDF file: {self.file_path}")

        try:
            import pdfplumber
        except ImportError:
            raise ImportError(
                "pdfplumber is required for PDF files. "
                "Install with: pip install pdfplumber"
            )

        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for PDF data processing. "
                "Install with: pip install pandas"
            )

        try:
            # Open PDF with pdfplumber
            with pdfplumber.open(self.file_path) as pdf:
                # Handle page selection
                if self.page_number == "all":
                    raise NotImplementedError(
                        "Multi-page extraction not yet supported. "
                        "Please specify a single page number."
                    )

                # Validate page number
                if not isinstance(self.page_number, int):
                    raise ValueError(
                        f"page_number must be int or 'all', got {type(self.page_number)}"
                    )

                if self.page_number < 0 or self.page_number >= len(pdf.pages):
                    raise ValueError(
                        f"Page {self.page_number} out of range. "
                        f"PDF has {len(pdf.pages)} pages (0-indexed)"
                    )

                # Get target page
                page = pdf.pages[self.page_number]

                # Extract table with optional bounding box
                if self.table_bbox:
                    cropped_page = page.crop(self.table_bbox)
                    tables = cropped_page.extract_tables(self.table_settings)
                else:
                    tables = page.extract_tables(self.table_settings)

                if not tables:
                    raise ValueError(
                        f"No tables found on page {self.page_number}. "
                        f"Try different table_strategy or table_bbox."
                    )

                # Use first table (most common case)
                table = tables[0]

                # Validate table has data
                if not table or len(table) < 2:
                    raise ValueError(
                        f"Table on page {self.page_number} has insufficient data. "
                        f"Expected at least header + 1 data row."
                    )

                # Convert to pandas DataFrame
                # First row is header, rest are data rows
                df = pd.DataFrame(table[1:], columns=table[0])

                # Apply skip_rows and max_rows (same as Excel)
                if self.skip_rows:
                    df = df.iloc[self.skip_rows :]
                if self.max_rows:
                    df = df.head(self.max_rows)

                # Clean and infer types (reuse Excel logic)
                df = self._clean_and_infer_types(df)

                # Convert to list of dictionaries
                cleaned_rows = df.to_dict(orient="records")

                # Get column names
                columns = df.columns.tolist()

                logger.debug(
                    f"Parsed PDF file: {self.file_path.name} "
                    f"(page={self.page_number}, {len(cleaned_rows)} rows, "
                    f"{len(columns)} columns)"
                )

                # Return format MUST match Excel for SchemaAnalyzer compatibility
                return {
                    "rows": cleaned_rows,
                    "columns": columns,
                    "page_number": self.page_number,
                    "row_count": len(cleaned_rows),
                    "source_file": str(self.file_path),
                    "file_name": self.file_path.name,
                }

        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")
        except ValueError as e:
            # Re-raise ValueError with context
            raise
        except ImportError as e:
            # Re-raise ImportError with context
            raise
        except NotImplementedError as e:
            # Re-raise NotImplementedError (multi-page extraction)
            raise
        except Exception as e:
            logger.error(f"Error reading PDF file {self.file_path}: {e}")
            raise RuntimeError(
                f"Failed to read PDF file {self.file_path.name}: "
                f"{type(e).__name__}: {e}"
            )

    def _clean_and_infer_types(self, df: "pd.DataFrame") -> "pd.DataFrame":
        """Clean extracted data and infer types.

        REUSE pandas type inference from ExcelDataSource:
        - Convert numeric strings to numbers
        - Convert date strings to dates
        - Strip whitespace
        - Handle None/null values

        Args:
            df: Raw DataFrame from pdfplumber

        Returns:
            Cleaned DataFrame with inferred types

        Design Decision: Aggressive type inference
        - PDFs often export everything as strings
        - Pandas to_numeric/to_datetime handles conversion
        - Failed conversions keep original value (no errors)
        - Try numeric FIRST to avoid "30" becoming a timestamp

        Performance:
        - Time Complexity: O(r * c) where r=rows, c=columns
        - Space Complexity: O(r * c) - new DataFrame created
        """
        import pandas as pd

        for col in df.columns:
            # Strip whitespace from strings
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
                # Convert empty strings to None
                df[col] = df[col].replace("", None)
                df[col] = df[col].replace("nan", None)
                df[col] = df[col].replace("None", None)

            # Try numeric conversion FIRST (before datetime)
            # This prevents "30" from being interpreted as timestamp
            numeric_converted = False
            try:
                df[col] = pd.to_numeric(df[col])
                numeric_converted = True
            except (ValueError, TypeError):
                pass

            # Only try datetime if numeric conversion failed
            if not numeric_converted:
                try:
                    df[col] = pd.to_datetime(df[col])
                except (ValueError, TypeError):
                    pass

        return df

    async def validate_config(self) -> bool:
        """Validate PDF file exists and is readable.

        Returns:
            True if file exists, is readable, and has valid format
            False otherwise

        Validation Checks:
        1. File exists
        2. Is a file (not directory)
        3. Has .pdf extension
        4. Can be opened by pdfplumber
        5. Has at least one page
        6. Target page exists (if specified)

        Error Handling:
        - Logs warnings/errors but returns False (doesn't raise)
        - Useful for pre-flight checks before batch processing
        """
        try:
            # Check file exists
            if not self.file_path.exists():
                logger.warning(f"PDF file not found: {self.file_path}")
                return False

            # Check is a file
            if not self.file_path.is_file():
                logger.warning(f"Path is not a file: {self.file_path}")
                return False

            # Check extension
            if self.file_path.suffix.lower() != ".pdf":
                logger.warning(
                    f"Invalid file extension: {self.file_path.suffix} "
                    f"(expected .pdf)"
                )
                return False

            # Try to open with pdfplumber
            try:
                import pdfplumber

                with pdfplumber.open(self.file_path) as pdf:
                    # Check has pages
                    if not pdf.pages:
                        logger.warning(f"PDF file has no pages: {self.file_path}")
                        return False

                    # Check target page exists
                    if isinstance(self.page_number, int):
                        if self.page_number >= len(pdf.pages):
                            logger.warning(
                                f"Page number {self.page_number} out of range. "
                                f"File has {len(pdf.pages)} pages"
                            )
                            return False
                    elif self.page_number != "all":
                        logger.warning(
                            f"Invalid page_number type: {type(self.page_number)}"
                        )
                        return False

                logger.info(f"PDF file validation successful: {self.file_path}")
                return True

            except ImportError:
                logger.error("pdfplumber not installed")
                return False

        except PermissionError:
            logger.error(f"PDF file not readable: {self.file_path}")
            return False
        except Exception as e:
            logger.error(f"PDF file validation error: {type(e).__name__}: {e}")
            return False

    def get_cache_key(self, **kwargs) -> str:
        """Generate cache key from file path and page number.

        Design Decision: Include page number in cache key
        - Same file, different pages = different data
        - Deterministic (same inputs = same key)
        - Human-readable for debugging

        Args:
            **kwargs: Ignored (cache disabled for local files)

        Returns:
            Cache key combining file path and page identifier
        """
        page_id = (
            self.page_number
            if isinstance(self.page_number, str)
            else f"page{self.page_number}"
        )
        return f"{self.file_path.absolute()}::{page_id}"
