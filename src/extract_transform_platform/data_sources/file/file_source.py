"""
File Data Source

Local file system data source supporting:
- JSON files
- YAML files
- CSV files (via pandas)
- Plain text files

Features:
- Automatic format detection from extension
- No caching (files are already local)
- Validation of file existence and readability

Status: MIGRATED from edgar_analyzer (100% generic, no dependencies)
Code Reuse: 100% from EDGAR FileDataSource (proven pattern)
Validation: All CSV, JSON, YAML, text parsing preserved
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from extract_transform_platform.core.base import BaseDataSource

logger = logging.getLogger(__name__)


class FileDataSource(BaseDataSource):
    """Local file data source with automatic format detection.

    Design Decision: No caching for local files
    - Files are already on disk (caching adds overhead, no benefit)
    - File changes should be reflected immediately
    - Memory usage: Don't duplicate file content in cache

    Supported Formats:
    - .json: JSON parsing
    - .yaml, .yml: YAML parsing
    - .csv: CSV parsing (returns list of dicts)
    - .txt, other: Plain text content

    Example:
        # JSON file
        file_source = FileDataSource(Path("data/config.json"))
        config = await file_source.fetch()
        print(config['database']['host'])

        # CSV file
        csv_source = FileDataSource(Path("data/companies.csv"))
        rows = await csv_source.fetch()
        for row in rows:
            print(row['company_name'])

        # Text file
        text_source = FileDataSource(Path("README.md"))
        content = await text_source.fetch()
        print(content['content'])
    """

    def __init__(
        self,
        file_path: Path,
        encoding: str = "utf-8",
        **kwargs,
    ):
        """Initialize file data source.

        Args:
            file_path: Path to file
            encoding: File encoding (default: utf-8)
            **kwargs: Additional arguments passed to BaseDataSource

        Design Trade-offs:
        - UTF-8 default: Covers 99% of text files
        - No caching: Files are local (cache_enabled=False)
        - No rate limiting: Local I/O (rate_limit_per_minute=9999)
        """
        # Override base settings for local files
        kwargs["cache_enabled"] = False  # No caching needed for local files
        kwargs["rate_limit_per_minute"] = 9999  # No rate limiting for local I/O
        kwargs["max_retries"] = 0  # No retries for local files (fail fast)

        super().__init__(**kwargs)

        self.file_path = Path(file_path)
        self.encoding = encoding

        logger.info(f"Initialized FileDataSource for {self.file_path}")

    async def fetch(self, **kwargs) -> Dict[str, Any]:
        """Read and parse file.

        Returns:
            Dictionary containing parsed data or file content

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file isn't readable
            json.JSONDecodeError: If JSON parsing fails
            ValueError: If file format is unsupported

        Performance:
        - Time Complexity: O(n) where n = file size
        - Space Complexity: O(n) - full file loaded into memory
        - I/O: Single read operation (no streaming)

        Optimization Opportunity:
        - For large files (>100MB), consider streaming or chunked reading
        - For CSV files, could return pandas DataFrame for better memory efficiency
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {self.file_path}")

        logger.debug(f"Reading file: {self.file_path}")

        # Read file content
        content = self.file_path.read_text(encoding=self.encoding)
        file_size = self.file_path.stat().st_size

        logger.debug(
            f"Read {file_size} bytes from {self.file_path.name} "
            f"({len(content)} characters)"
        )

        # Auto-detect format and parse
        suffix = self.file_path.suffix.lower()

        if suffix == ".json":
            return self._parse_json(content)
        elif suffix in [".yml", ".yaml"]:
            return self._parse_yaml(content)
        elif suffix == ".csv":
            return self._parse_csv(content)
        else:
            return self._parse_text(content)

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON file content.

        Args:
            content: Raw file content

        Returns:
            Parsed JSON as dictionary

        Raises:
            json.JSONDecodeError: If JSON is malformed
        """
        try:
            data = json.loads(content)
            logger.debug(f"Parsed JSON file: {self.file_path.name}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.file_path}: {e}")
            raise

    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """Parse YAML file content.

        Args:
            content: Raw file content

        Returns:
            Parsed YAML as dictionary

        Raises:
            ImportError: If PyYAML not installed
            yaml.YAMLError: If YAML is malformed
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML files. Install with: pip install pyyaml"
            )

        try:
            data = yaml.safe_load(content)
            logger.debug(f"Parsed YAML file: {self.file_path.name}")
            return data
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {self.file_path}: {e}")
            raise

    def _parse_csv(self, content: str) -> Dict[str, Any]:
        """Parse CSV file content.

        Args:
            content: Raw file content

        Returns:
            Dictionary with 'rows' key containing list of row dicts

        Raises:
            ImportError: If pandas not installed
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for CSV files. Install with: pip install pandas"
            )

        try:
            # Use pandas for robust CSV parsing
            import io

            df = pd.read_csv(io.StringIO(content))
            rows = df.to_dict(orient="records")

            logger.debug(
                f"Parsed CSV file: {self.file_path.name} ({len(rows)} rows, "
                f"{len(df.columns)} columns)"
            )

            return {
                "rows": rows,
                "row_count": len(rows),
                "columns": list(df.columns),
                "file_path": str(self.file_path),
            }
        except Exception as e:
            logger.error(f"Error parsing CSV {self.file_path}: {e}")
            raise

    def _parse_text(self, content: str) -> Dict[str, Any]:
        """Parse plain text file.

        Args:
            content: Raw file content

        Returns:
            Dictionary with 'content' and metadata
        """
        logger.debug(f"Read text file: {self.file_path.name}")

        return {
            "content": content,
            "file_path": str(self.file_path),
            "file_name": self.file_path.name,
            "file_size": self.file_path.stat().st_size,
            "line_count": content.count("\n") + 1,
        }

    async def validate_config(self) -> bool:
        """Validate file exists and is readable.

        Returns:
            True if file exists and is readable
            False otherwise
        """
        try:
            is_valid = self.file_path.exists() and self.file_path.is_file()

            if is_valid:
                # Try to read to ensure readability
                _ = self.file_path.read_bytes()
                logger.info(f"File validation successful: {self.file_path}")
            else:
                logger.warning(f"File validation failed: {self.file_path} not found")

            return is_valid

        except PermissionError:
            logger.error(f"File not readable: {self.file_path}")
            return False
        except Exception as e:
            logger.error(f"File validation error: {type(e).__name__}: {e}")
            return False

    def get_cache_key(self, **kwargs) -> str:
        """Generate cache key from file path.

        Design Decision: File path as cache key
        - Unique per file
        - Deterministic
        - Human-readable (for debugging)

        Args:
            **kwargs: Ignored

        Returns:
            Absolute file path as string
        """
        return str(self.file_path.absolute())
