"""
Excel Data Source

Local Excel file (.xlsx, .xls) data source supporting:
- Single sheet reading
- Schema-aware parsing
- Type auto-detection via pandas
- Header row specification
- Compatible with SchemaAnalyzer

Features:
- No caching (files are already local)
- Automatic type conversion
- NaN handling (converts to None for JSON compatibility)
- Validation of file existence and format
- Detailed error messages

Future Enhancements (Phase 2):
- Multi-sheet support
- Merged cell handling
- Formula extraction
- Large file streaming
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import BaseDataSource

logger = logging.getLogger(__name__)


class ExcelDataSource(BaseDataSource):
    """Excel file data source with schema-aware parsing.

    Design Decision: No caching for local files
    - Files are already on disk (caching adds overhead, no benefit)
    - File changes should be reflected immediately
    - Memory usage: Don't duplicate file content in cache

    Supported Formats:
    - .xlsx: Excel 2007+ format (via openpyxl)
    - .xls: Legacy Excel format (via openpyxl)

    Performance Analysis:
    - Time Complexity: O(r * c) where r=rows, c=columns
    - Space Complexity: O(r * c) - full sheet loaded into memory
    - Bottleneck: pandas read_excel() loads entire sheet

    Optimization Opportunities:
    - For large files (>10k rows), consider chunked reading
    - For multi-sheet files, lazy loading per sheet
    - For streaming, use pandas chunksize parameter

    Example:
        # Read first sheet (default)
        excel_source = ExcelDataSource(Path("data/employees.xlsx"))
        data = await excel_source.fetch()
        print(f"Found {data['row_count']} employees")

        # Read specific sheet with custom header
        excel_source = ExcelDataSource(
            Path("data/report.xlsx"),
            sheet_name="Q1 Results",
            header_row=2
        )
        data = await excel_source.fetch()
        for row in data['rows']:
            print(row['Revenue'])

        # Read with row limits (for large files)
        excel_source = ExcelDataSource(
            Path("data/large.xlsx"),
            max_rows=1000
        )
        data = await excel_source.fetch()
    """

    def __init__(
        self,
        file_path: Path,
        sheet_name: Union[str, int] = 0,
        header_row: int = 0,
        skip_rows: Optional[int] = None,
        max_rows: Optional[int] = None,
        encoding: str = "utf-8",
        **kwargs,
    ):
        """Initialize Excel data source.

        Args:
            file_path: Path to Excel file (.xlsx or .xls)
            sheet_name: Sheet name (str) or index (int), default 0 (first sheet)
            header_row: Row number to use as column headers (0-indexed)
            skip_rows: Number of rows to skip after header
            max_rows: Maximum rows to read (for large files)
            encoding: File encoding (default: utf-8)
            **kwargs: Additional arguments passed to BaseDataSource

        Design Trade-offs:
        - UTF-8 default: Covers most Excel exports
        - No caching: Files are local (cache_enabled=False)
        - No rate limiting: Local I/O (rate_limit_per_minute=9999)
        - No retries: Local files fail fast (max_retries=0)

        Error Handling:
        - FileNotFoundError: If Excel file doesn't exist
        - ValueError: If file extension not .xlsx or .xls
        """
        # Override base settings for local files
        kwargs["cache_enabled"] = False  # No caching needed for local files
        kwargs["rate_limit_per_minute"] = 9999  # No rate limiting for local I/O
        kwargs["max_retries"] = 0  # No retries for local files (fail fast)

        super().__init__(**kwargs)

        self.file_path = Path(file_path)
        self.sheet_name = sheet_name
        self.header_row = header_row
        self.skip_rows = skip_rows
        self.max_rows = max_rows
        self.encoding = encoding

        # Validate file exists
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        # Validate file extension
        if self.file_path.suffix.lower() not in [".xlsx", ".xls"]:
            raise ValueError(
                f"Unsupported file type: {self.file_path.suffix}. "
                f"Expected .xlsx or .xls"
            )

        logger.info(
            f"Initialized ExcelDataSource for {self.file_path.name} "
            f"(sheet={sheet_name}, header_row={header_row})"
        )

    async def fetch(self, **kwargs) -> Dict[str, Any]:
        """Read Excel file and return structured data.

        Returns:
            Dictionary with keys:
                - rows: List[Dict] - Each row as dictionary (cleaned)
                - columns: List[str] - Column names
                - sheet_name: str - Active sheet name
                - row_count: int - Number of data rows
                - source_file: str - Original file path
                - file_name: str - File name only

        Raises:
            FileNotFoundError: If Excel file doesn't exist
            ValueError: If sheet not found or invalid parameters
            ImportError: If pandas or openpyxl not installed
            RuntimeError: If Excel parsing fails

        Performance:
        - Time Complexity: O(r * c) where r=rows, c=columns
        - Space Complexity: O(r * c) - full data in memory
        - I/O: Single read operation via pandas
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")

        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {self.file_path}")

        logger.debug(f"Reading Excel file: {self.file_path}")

        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for Excel files. "
                "Install with: pip install pandas openpyxl"
            )

        try:
            # Read Excel file with pandas
            df = pd.read_excel(
                self.file_path,
                sheet_name=self.sheet_name,
                header=self.header_row,
                skiprows=self.skip_rows,
                nrows=self.max_rows,
                engine="openpyxl",  # Use openpyxl for .xlsx
            )

            # Convert DataFrame to list of dictionaries
            raw_rows = df.to_dict(orient="records")

            # Clean data (handle NaN, etc.)
            cleaned_rows = self._clean_data(raw_rows)

            # Get column names
            columns = df.columns.tolist()

            # Determine actual sheet name for metadata
            active_sheet = self._get_active_sheet_name()

            logger.debug(
                f"Parsed Excel file: {self.file_path.name} "
                f"(sheet={active_sheet}, {len(cleaned_rows)} rows, "
                f"{len(columns)} columns)"
            )

            return {
                "rows": cleaned_rows,
                "columns": columns,
                "sheet_name": active_sheet,
                "row_count": len(cleaned_rows),
                "source_file": str(self.file_path),
                "file_name": self.file_path.name,
            }

        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")
        except ValueError as e:
            if "Worksheet" in str(e):
                raise ValueError(
                    f"Sheet '{self.sheet_name}' not found in {self.file_path.name}"
                )
            raise
        except Exception as e:
            logger.error(f"Error reading Excel file {self.file_path}: {e}")
            raise RuntimeError(
                f"Failed to read Excel file {self.file_path.name}: "
                f"{type(e).__name__}: {e}"
            )

    def _clean_data(self, rows: List[Dict]) -> List[Dict]:
        """Clean Excel data (handle NaN, empty cells, etc.).

        Args:
            rows: Raw rows from pandas (may contain NaN values)

        Returns:
            Cleaned rows with None instead of NaN for JSON compatibility

        Design Decision: Convert NaN to None
        - JSON doesn't support NaN (would fail serialization)
        - None is more Pythonic than NaN
        - Easier to check: `if value is None` vs `if pd.isna(value)`

        Performance:
        - Time Complexity: O(r * c) where r=rows, c=columns
        - Space Complexity: O(r * c) - new list created
        - Alternative: In-place modification (saves space but mutates input)
        """
        try:
            import pandas as pd
        except ImportError:
            # If pandas not available, return as-is
            return rows

        cleaned = []
        for row in rows:
            cleaned_row = {}
            for key, value in row.items():
                # Replace pandas NaN with None for JSON compatibility
                if pd.isna(value):
                    cleaned_row[key] = None
                else:
                    cleaned_row[key] = value
            cleaned.append(cleaned_row)

        return cleaned

    def _get_active_sheet_name(self) -> str:
        """Get the actual sheet name (resolve index to name if needed).

        Returns:
            Sheet name as string

        Design Decision: Lazy sheet name resolution
        - Only resolve when needed (avoid extra file read)
        - Index-based selection common, but name useful for debugging
        - Use pandas ExcelFile for efficient sheet list access
        """
        if isinstance(self.sheet_name, str):
            # Already have sheet name
            return self.sheet_name

        # Sheet name is an index, need to resolve to name
        try:
            import pandas as pd

            with pd.ExcelFile(self.file_path, engine="openpyxl") as xls:
                if self.sheet_name < len(xls.sheet_names):
                    return xls.sheet_names[self.sheet_name]
                else:
                    # Index out of range, return as string
                    return f"Sheet{self.sheet_name}"

        except Exception:
            # Fallback if resolution fails
            return f"Sheet{self.sheet_name}"

    async def validate_config(self) -> bool:
        """Validate Excel file exists and is readable.

        Returns:
            True if file exists, is readable, and has valid format
            False otherwise

        Validation Checks:
        1. File exists
        2. Is a file (not directory)
        3. Has .xlsx or .xls extension
        4. Can be opened by pandas/openpyxl
        5. Has at least one sheet
        6. Target sheet exists (if specified)

        Error Handling:
        - Logs warnings/errors but returns False (doesn't raise)
        - Useful for pre-flight checks before batch processing
        """
        try:
            # Check file exists
            if not self.file_path.exists():
                logger.warning(f"Excel file not found: {self.file_path}")
                return False

            # Check is a file
            if not self.file_path.is_file():
                logger.warning(f"Path is not a file: {self.file_path}")
                return False

            # Check extension
            if self.file_path.suffix.lower() not in [".xlsx", ".xls"]:
                logger.warning(
                    f"Invalid file extension: {self.file_path.suffix} "
                    f"(expected .xlsx or .xls)"
                )
                return False

            # Try to open with pandas
            try:
                import pandas as pd

                with pd.ExcelFile(self.file_path, engine="openpyxl") as xls:
                    # Check has sheets
                    if not xls.sheet_names:
                        logger.warning(f"Excel file has no sheets: {self.file_path}")
                        return False

                    # Check target sheet exists
                    if isinstance(self.sheet_name, str):
                        if self.sheet_name not in xls.sheet_names:
                            logger.warning(
                                f"Sheet '{self.sheet_name}' not found in "
                                f"{self.file_path.name}. Available: {xls.sheet_names}"
                            )
                            return False
                    elif isinstance(self.sheet_name, int):
                        if self.sheet_name >= len(xls.sheet_names):
                            logger.warning(
                                f"Sheet index {self.sheet_name} out of range. "
                                f"File has {len(xls.sheet_names)} sheets"
                            )
                            return False

                logger.info(f"Excel file validation successful: {self.file_path}")
                return True

            except ImportError:
                logger.error("pandas or openpyxl not installed")
                return False

        except PermissionError:
            logger.error(f"Excel file not readable: {self.file_path}")
            return False
        except Exception as e:
            logger.error(f"Excel file validation error: {type(e).__name__}: {e}")
            return False

    def get_cache_key(self, **kwargs) -> str:
        """Generate cache key from file path and sheet name.

        Design Decision: Include sheet name in cache key
        - Same file, different sheets = different data
        - Deterministic (same inputs = same key)
        - Human-readable for debugging

        Args:
            **kwargs: Ignored (cache disabled for local files)

        Returns:
            Cache key combining file path and sheet identifier
        """
        sheet_id = (
            self.sheet_name
            if isinstance(self.sheet_name, str)
            else f"idx{self.sheet_name}"
        )
        return f"{self.file_path.absolute()}::{sheet_id}"
