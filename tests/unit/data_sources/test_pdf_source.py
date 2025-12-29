"""
Unit Tests for PDFDataSource

Comprehensive test coverage for PDF file data source including:
- Initialization validation (file existence, extensions)
- Data fetching (basic reads, table extraction)
- Type handling (int, float, str, None)
- Edge cases (empty tables, missing pages, large tables)
- Schema compatibility (output format validation)
- Configuration validation
- Error handling (all error paths)

Test Organization:
- Class per functionality group
- Descriptive test names
- Clear docstrings
- Uses tmp_path for file creation (no artifacts)
- Async tests use @pytest.mark.asyncio
"""

import logging
from pathlib import Path
from typing import Any, Dict

import pytest

from extract_transform_platform.data_sources.file.pdf_source import PDFDataSource

# ============================================================================
# Test Fixtures - Create PDF files programmatically
# ============================================================================


def create_simple_pdf(file_path: Path):
    """Create simple PDF with bordered table for testing.

    Uses reportlab to create a PDF with a simple table.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    except ImportError:
        pytest.skip("reportlab not installed - required for PDF test fixtures")

    doc = SimpleDocTemplate(str(file_path), pagesize=letter)

    # Table data
    data = [
        ["Name", "Age", "City"],
        ["Alice", "30", "NYC"],
        ["Bob", "25", "LA"],
        ["Carol", "35", "Chicago"],
    ]

    # Create table with borders
    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 14),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ]
        )
    )

    doc.build([table])


def create_multi_type_pdf(file_path: Path):
    """Create PDF with multiple data types."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    except ImportError:
        pytest.skip("reportlab not installed")

    doc = SimpleDocTemplate(str(file_path), pagesize=letter)

    data = [
        ["int_col", "float_col", "str_col", "bool_col"],
        ["1", "1.5", "a", "True"],
        ["2", "2.5", "b", "False"],
        ["3", "3.5", "c", "True"],
    ]

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ]
        )
    )

    doc.build([table])


def create_empty_pdf(file_path: Path):
    """Create PDF with no tables (just text)."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        pytest.skip("reportlab not installed")

    c = canvas.Canvas(str(file_path), pagesize=letter)
    c.drawString(100, 750, "This PDF has no tables")
    c.save()


def create_large_pdf(file_path: Path):
    """Create PDF with large table (100 rows)."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    except ImportError:
        pytest.skip("reportlab not installed")

    doc = SimpleDocTemplate(str(file_path), pagesize=letter)

    data = [["id", "value", "label"]]
    for i in range(100):
        data.append([str(i), str(i * 10), f"Row_{i}"])

    table = Table(data)
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)]))

    doc.build([table])


@pytest.fixture
def simple_pdf(tmp_path):
    """Create simple PDF file for testing."""
    file_path = tmp_path / "simple.pdf"
    create_simple_pdf(file_path)
    return file_path


@pytest.fixture
def multi_type_pdf(tmp_path):
    """Create PDF with multiple data types."""
    file_path = tmp_path / "multi_type.pdf"
    create_multi_type_pdf(file_path)
    return file_path


@pytest.fixture
def empty_pdf(tmp_path):
    """Create PDF with no tables."""
    file_path = tmp_path / "empty.pdf"
    create_empty_pdf(file_path)
    return file_path


@pytest.fixture
def large_pdf(tmp_path):
    """Create PDF with large table."""
    file_path = tmp_path / "large.pdf"
    create_large_pdf(file_path)
    return file_path


# ============================================================================
# Test Initialization
# ============================================================================


class TestPDFDataSourceInitialization:
    """Tests for PDFDataSource initialization and validation."""

    def test_valid_pdf_file(self, simple_pdf):
        """Test initialization with valid .pdf file."""
        source = PDFDataSource(simple_pdf)

        assert source.file_path == simple_pdf
        assert source.page_number == 0
        assert source.table_strategy == "lines"
        assert source.skip_rows is None
        assert source.max_rows is None
        assert source.table_bbox is None

    def test_file_not_found(self, tmp_path):
        """Test FileNotFoundError for missing file."""
        nonexistent = tmp_path / "nonexistent.pdf"

        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            PDFDataSource(nonexistent)

    def test_unsupported_file_type_docx(self, tmp_path):
        """Test ValueError for .docx file."""
        test_file = tmp_path / "test.docx"
        test_file.touch()

        with pytest.raises(ValueError, match="Unsupported file type.*Expected .pdf"):
            PDFDataSource(test_file)

    def test_unsupported_file_type_txt(self, tmp_path):
        """Test ValueError for .txt file."""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        with pytest.raises(ValueError, match="Unsupported file type.*Expected .pdf"):
            PDFDataSource(test_file)

    def test_page_number_as_integer(self, simple_pdf):
        """Test initialization with page number as integer."""
        source = PDFDataSource(simple_pdf, page_number=0)
        assert source.page_number == 0

    def test_page_number_as_all_string(self, simple_pdf):
        """Test initialization with page_number='all'."""
        source = PDFDataSource(simple_pdf, page_number="all")
        assert source.page_number == "all"

    def test_custom_table_strategy(self, simple_pdf):
        """Test initialization with custom table strategy."""
        source = PDFDataSource(simple_pdf, table_strategy="text")
        assert source.table_strategy == "text"

    def test_table_bbox_parameter(self, simple_pdf):
        """Test initialization with table bounding box."""
        bbox = (50, 100, 550, 400)
        source = PDFDataSource(simple_pdf, table_bbox=bbox)
        assert source.table_bbox == bbox

    def test_max_rows_parameter(self, simple_pdf):
        """Test initialization with max_rows parameter."""
        source = PDFDataSource(simple_pdf, max_rows=10)
        assert source.max_rows == 10

    def test_skip_rows_parameter(self, simple_pdf):
        """Test initialization with skip_rows parameter."""
        source = PDFDataSource(simple_pdf, skip_rows=2)
        assert source.skip_rows == 2

    def test_cache_disabled_for_local_files(self, simple_pdf):
        """Test that caching is disabled for local files."""
        source = PDFDataSource(simple_pdf)
        assert source.cache_enabled is False

    def test_no_rate_limiting_for_local_files(self, simple_pdf):
        """Test that rate limiting is disabled for local files."""
        source = PDFDataSource(simple_pdf)
        assert source.rate_limit_per_minute == 9999

    def test_no_retries_for_local_files(self, simple_pdf):
        """Test that retries are disabled for local files (fail fast)."""
        source = PDFDataSource(simple_pdf)
        assert source.max_retries == 0


# ============================================================================
# Test Table Settings Builder
# ============================================================================


class TestPDFDataSourceTableSettings:
    """Tests for table settings builder."""

    def test_lines_strategy_settings(self, simple_pdf):
        """Test lines strategy generates correct settings."""
        source = PDFDataSource(simple_pdf, table_strategy="lines")
        assert source.table_settings["vertical_strategy"] == "lines"
        assert source.table_settings["horizontal_strategy"] == "lines"

    def test_text_strategy_settings(self, simple_pdf):
        """Test text strategy generates correct settings."""
        source = PDFDataSource(simple_pdf, table_strategy="text")
        assert source.table_settings["vertical_strategy"] == "text"
        assert source.table_settings["horizontal_strategy"] == "text"

    def test_mixed_strategy_settings(self, simple_pdf):
        """Test mixed strategy generates correct settings."""
        source = PDFDataSource(simple_pdf, table_strategy="mixed")
        assert source.table_settings["vertical_strategy"] == "lines"
        assert source.table_settings["horizontal_strategy"] == "text"

    def test_custom_settings_override(self, simple_pdf):
        """Test custom settings merge with defaults."""
        custom = {"snap_tolerance": 5}
        source = PDFDataSource(simple_pdf, table_settings=custom)
        assert "snap_tolerance" in source.table_settings
        assert source.table_settings["snap_tolerance"] == 5


# ============================================================================
# Test Data Fetching
# ============================================================================


class TestPDFDataSourceFetch:
    """Tests for PDFDataSource.fetch() method."""

    @pytest.mark.asyncio
    async def test_basic_fetch(self, simple_pdf):
        """Test basic PDF table reading."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        # Validate structure (MUST match Excel format)
        assert "rows" in result
        assert "columns" in result
        assert "row_count" in result
        assert "page_number" in result
        assert "source_file" in result
        assert "file_name" in result

        # Validate types
        assert isinstance(result["rows"], list)
        assert isinstance(result["columns"], list)
        assert isinstance(result["row_count"], int)
        assert isinstance(result["page_number"], int)
        assert isinstance(result["source_file"], str)
        assert isinstance(result["file_name"], str)

    @pytest.mark.asyncio
    async def test_row_data_structure(self, simple_pdf):
        """Test row data is list of dictionaries."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        # Each row should be a dictionary
        for row in result["rows"]:
            assert isinstance(row, dict)

        # Check row count
        assert len(result["rows"]) == 3

    @pytest.mark.asyncio
    async def test_column_names_extraction(self, simple_pdf):
        """Test column names are extracted correctly."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        assert result["columns"] == ["Name", "Age", "City"]

    @pytest.mark.asyncio
    async def test_row_count_accuracy(self, simple_pdf):
        """Test row count matches actual data rows."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        assert result["row_count"] == 3
        assert result["row_count"] == len(result["rows"])

    @pytest.mark.asyncio
    async def test_page_number_metadata(self, simple_pdf):
        """Test page number included in metadata."""
        source = PDFDataSource(simple_pdf, page_number=0)
        result = await source.fetch()

        assert result["page_number"] == 0

    @pytest.mark.asyncio
    async def test_source_file_metadata(self, simple_pdf):
        """Test source file path included in metadata."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        assert result["source_file"] == str(simple_pdf)
        assert result["file_name"] == simple_pdf.name

    @pytest.mark.asyncio
    async def test_specific_row_values(self, simple_pdf):
        """Test specific row values are read correctly."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        # First row (type inference: Age becomes int)
        assert result["rows"][0]["Name"] == "Alice"
        assert result["rows"][0]["Age"] == 30  # Should be int
        assert result["rows"][0]["City"] == "NYC"

        # Second row
        assert result["rows"][1]["Name"] == "Bob"
        assert result["rows"][1]["Age"] == 25
        assert result["rows"][1]["City"] == "LA"


# ============================================================================
# Test Type Preservation
# ============================================================================


class TestPDFDataSourceTypePreservation:
    """Tests for data type preservation and inference."""

    @pytest.mark.asyncio
    async def test_integer_inference(self, multi_type_pdf):
        """Test integer columns are inferred correctly."""
        source = PDFDataSource(multi_type_pdf)
        result = await source.fetch()

        for row in result["rows"]:
            assert isinstance(row["int_col"], int)

    @pytest.mark.asyncio
    async def test_float_inference(self, multi_type_pdf):
        """Test float columns are inferred correctly."""
        source = PDFDataSource(multi_type_pdf)
        result = await source.fetch()

        for row in result["rows"]:
            assert isinstance(row["float_col"], float)

    @pytest.mark.asyncio
    async def test_string_preservation(self, multi_type_pdf):
        """Test string columns remain strings."""
        source = PDFDataSource(multi_type_pdf)
        result = await source.fetch()

        for row in result["rows"]:
            assert isinstance(row["str_col"], str)

    @pytest.mark.asyncio
    async def test_whitespace_stripping(self, simple_pdf):
        """Test whitespace is stripped from strings."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        # All string values should have no leading/trailing whitespace
        for row in result["rows"]:
            for value in row.values():
                if isinstance(value, str):
                    assert value == value.strip()


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestPDFDataSourceEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_pdf_no_tables(self, empty_pdf):
        """Test error when PDF has no tables."""
        source = PDFDataSource(empty_pdf)

        with pytest.raises(ValueError, match="No tables found"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_max_rows_limit(self, large_pdf):
        """Test max_rows parameter limits rows read."""
        source = PDFDataSource(large_pdf, max_rows=10)
        result = await source.fetch()

        # Should only read first 10 rows
        assert len(result["rows"]) == 10
        assert result["row_count"] == 10

        # Verify row values
        assert result["rows"][0]["id"] == 0
        assert result["rows"][9]["id"] == 9

    @pytest.mark.asyncio
    async def test_invalid_page_number_too_high(self, simple_pdf):
        """Test error for page number out of range."""
        source = PDFDataSource(simple_pdf, page_number=99)

        with pytest.raises(ValueError, match="out of range"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_page_number_all_not_implemented(self, simple_pdf):
        """Test NotImplementedError for page_number='all'."""
        source = PDFDataSource(simple_pdf, page_number="all")

        with pytest.raises(NotImplementedError, match="Multi-page extraction"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_file_deleted_after_init(self, simple_pdf):
        """Test error when file is deleted after initialization."""
        source = PDFDataSource(simple_pdf)

        # Delete the file
        simple_pdf.unlink()

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_file_is_directory_not_file(self, tmp_path):
        """Test error when path is directory not file."""
        fake_file = tmp_path / "fake.pdf"
        fake_file.mkdir()

        source = PDFDataSource(fake_file)

        with pytest.raises(ValueError, match="Path is not a file"):
            await source.fetch()


# ============================================================================
# Test Schema Compatibility
# ============================================================================


class TestPDFDataSourceSchemaCompatibility:
    """Tests for SchemaAnalyzer compatibility (MUST match Excel format)."""

    @pytest.mark.asyncio
    async def test_output_format_matches_excel_structure(self, simple_pdf):
        """Test output format matches Excel structure exactly."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        # Validate format matches expected structure
        assert isinstance(result, dict)
        assert isinstance(result["rows"], list)
        assert all(isinstance(row, dict) for row in result["rows"])
        assert isinstance(result["columns"], list)
        assert isinstance(result["row_count"], int)

    @pytest.mark.asyncio
    async def test_json_serializable_output(self, multi_type_pdf):
        """Test output is JSON serializable."""
        import json

        source = PDFDataSource(multi_type_pdf)
        result = await source.fetch()

        # Should be serializable
        json_str = json.dumps(result, default=str)
        assert json_str is not None

    @pytest.mark.asyncio
    async def test_no_none_in_column_names(self, simple_pdf):
        """Test column names contain no None values."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        assert all(col is not None for col in result["columns"])

    @pytest.mark.asyncio
    async def test_column_names_are_strings(self, simple_pdf):
        """Test all column names are strings."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        assert all(isinstance(col, str) for col in result["columns"])

    @pytest.mark.asyncio
    async def test_metadata_fields_present(self, simple_pdf):
        """Test all required metadata fields are present."""
        source = PDFDataSource(simple_pdf)
        result = await source.fetch()

        # Same fields as Excel (page_number instead of sheet_name)
        required_fields = [
            "rows",
            "columns",
            "row_count",
            "page_number",
            "source_file",
            "file_name",
        ]
        for field in required_fields:
            assert field in result


# ============================================================================
# Test Configuration Methods
# ============================================================================


class TestPDFDataSourceConfiguration:
    """Tests for configuration validation and cache key generation."""

    @pytest.mark.asyncio
    async def test_validate_config_valid_file(self, simple_pdf):
        """Test validate_config returns True for valid file."""
        source = PDFDataSource(simple_pdf)
        is_valid = await source.validate_config()

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_config_missing_file(self, tmp_path):
        """Test validate_config returns False for missing file."""
        test_file = tmp_path / "temp.pdf"
        create_simple_pdf(test_file)

        source = PDFDataSource(test_file)

        # Delete file
        test_file.unlink()

        # Should return False (not raise)
        is_valid = await source.validate_config()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_invalid_page_number(self, simple_pdf):
        """Test validate_config returns False for out of range page."""
        source = PDFDataSource(simple_pdf, page_number=99)

        is_valid = await source.validate_config()
        assert is_valid is False

    def test_get_cache_key_with_integer_page(self, simple_pdf):
        """Test cache key generation with integer page number."""
        source = PDFDataSource(simple_pdf, page_number=0)
        cache_key = source.get_cache_key()

        assert isinstance(cache_key, str)
        assert str(simple_pdf.absolute()) in cache_key
        assert "page0" in cache_key

    def test_get_cache_key_with_all_string(self, simple_pdf):
        """Test cache key generation with page_number='all'."""
        source = PDFDataSource(simple_pdf, page_number="all")
        cache_key = source.get_cache_key()

        assert isinstance(cache_key, str)
        assert str(simple_pdf.absolute()) in cache_key
        assert "all" in cache_key

    def test_get_cache_key_deterministic(self, simple_pdf):
        """Test cache key is deterministic (same inputs = same key)."""
        source1 = PDFDataSource(simple_pdf, page_number=0)
        source2 = PDFDataSource(simple_pdf, page_number=0)

        assert source1.get_cache_key() == source2.get_cache_key()

    @pytest.mark.asyncio
    async def test_validate_config_not_a_file(self, tmp_path):
        """Test validate_config returns False for directory."""
        # Create a directory with .pdf name
        fake_file = tmp_path / "fake.pdf"
        fake_file.mkdir()

        source = PDFDataSource(fake_file)

        is_valid = await source.validate_config()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_wrong_extension(self, tmp_path):
        """Test validate_config returns False for wrong extension."""
        # Create file with wrong extension but pass validation at init
        test_file = tmp_path / "test.pdf"
        test_file.touch()

        source = PDFDataSource(test_file)

        # Manually change the file extension after init
        import shutil

        new_path = tmp_path / "test.txt"
        shutil.move(test_file, new_path)
        source.file_path = new_path

        is_valid = await source.validate_config()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_empty_pdf_no_pages(self, tmp_path, monkeypatch):
        """Test validate_config returns False for PDF with no pages."""
        test_file = tmp_path / "empty.pdf"
        create_empty_pdf(test_file)

        source = PDFDataSource(test_file)

        # Mock pdfplumber to return PDF with no pages
        import pdfplumber

        class MockPDF:
            pages = []

        class MockPDFContext:
            def __enter__(self):
                return MockPDF()

            def __exit__(self, *args):
                pass

        def mock_open(*args, **kwargs):
            return MockPDFContext()

        monkeypatch.setattr(pdfplumber, "open", mock_open)

        is_valid = await source.validate_config()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_invalid_page_type(self, simple_pdf):
        """Test validate_config returns False for invalid page_number type."""
        # Create source with invalid page_number (not int or "all")
        source = PDFDataSource(simple_pdf, page_number=0)
        source.page_number = 1.5  # Invalid type (float)

        is_valid = await source.validate_config()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_pdfplumber_not_installed(
        self, simple_pdf, monkeypatch
    ):
        """Test validate_config returns False if pdfplumber not available."""
        source = PDFDataSource(simple_pdf)

        # Mock pdfplumber import failure
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pdfplumber":
                raise ImportError("pdfplumber not installed")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        is_valid = await source.validate_config()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_permission_error(self, tmp_path, monkeypatch):
        """Test validate_config returns False on PermissionError."""
        test_file = tmp_path / "test.pdf"
        create_simple_pdf(test_file)

        source = PDFDataSource(test_file)

        # Mock to raise PermissionError
        from pathlib import Path

        def mock_exists(self):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(Path, "exists", mock_exists)

        is_valid = await source.validate_config()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_unexpected_exception(self, simple_pdf, monkeypatch):
        """Test validate_config returns False on unexpected exception."""
        source = PDFDataSource(simple_pdf)

        # Mock to raise unexpected exception
        from pathlib import Path

        def mock_exists(self):
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(Path, "exists", mock_exists)

        is_valid = await source.validate_config()
        assert is_valid is False


# ============================================================================
# Test Error Handling
# ============================================================================


class TestPDFDataSourceErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_pdfplumber_not_installed_error(self, simple_pdf, monkeypatch):
        """Test ImportError if pdfplumber not available."""
        import sys

        source = PDFDataSource(simple_pdf)

        # Mock pdfplumber import failure
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pdfplumber":
                raise ImportError("pdfplumber not installed")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with pytest.raises(ImportError, match="pdfplumber is required"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_pandas_not_installed_error(self, simple_pdf, monkeypatch):
        """Test ImportError if pandas not available."""
        import sys

        source = PDFDataSource(simple_pdf)

        # Mock pandas import failure
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pandas":
                raise ImportError("pandas not installed")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with pytest.raises(ImportError, match="pandas is required"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_invalid_page_number_type(self, simple_pdf, monkeypatch):
        """Test ValueError for invalid page_number type."""
        import pdfplumber

        source = PDFDataSource(simple_pdf, page_number="invalid")

        with pytest.raises(ValueError, match="page_number must be int or 'all'"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_negative_page_number(self, simple_pdf):
        """Test ValueError for negative page number."""
        source = PDFDataSource(simple_pdf, page_number=-1)

        with pytest.raises(ValueError, match="out of range"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_table_with_insufficient_data(self, tmp_path):
        """Test ValueError when table has only header (no data rows)."""
        # Create PDF with only header row
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        except ImportError:
            pytest.skip("reportlab not installed")

        file_path = tmp_path / "header_only.pdf"
        doc = SimpleDocTemplate(str(file_path), pagesize=letter)

        # Only header, no data rows
        data = [["Name", "Age", "City"]]

        table = Table(data)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)]))
        doc.build([table])

        source = PDFDataSource(file_path)

        with pytest.raises(ValueError, match="insufficient data"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_runtime_error_on_pdf_parsing_failure(self, tmp_path, monkeypatch):
        """Test RuntimeError when PDF parsing fails unexpectedly."""
        # Create a valid PDF first
        file_path = tmp_path / "valid.pdf"
        create_simple_pdf(file_path)

        source = PDFDataSource(file_path)

        # Mock pdfplumber to raise unexpected exception
        import pdfplumber

        def mock_open(*args, **kwargs):
            raise Exception("Unexpected PDF parsing error")

        monkeypatch.setattr(pdfplumber, "open", mock_open)

        with pytest.raises(RuntimeError, match="Failed to read PDF file"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_skip_rows_functionality(self, large_pdf):
        """Test skip_rows parameter skips rows correctly."""
        source = PDFDataSource(large_pdf, skip_rows=5)
        result = await source.fetch()

        # Should skip first 5 data rows (after header)
        # First row should be row 5 (id=5)
        assert result["rows"][0]["id"] == 5

    @pytest.mark.asyncio
    async def test_table_bbox_cropping(self, tmp_path):
        """Test table_bbox parameter crops page correctly."""
        # Create PDF with table
        file_path = tmp_path / "bbox_test.pdf"
        create_simple_pdf(file_path)

        # Create source with bounding box
        # Note: bbox values are illustrative
        bbox = (0, 0, 612, 792)  # Full page dimensions
        source = PDFDataSource(file_path, table_bbox=bbox)

        result = await source.fetch()

        # Should still read the table (within bounds)
        assert result["row_count"] > 0

    def test_logging_on_initialization(self, simple_pdf, caplog):
        """Test that initialization logs info message."""
        with caplog.at_level(logging.INFO):
            source = PDFDataSource(simple_pdf)

        assert any(
            "Initialized PDFDataSource" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logging_on_fetch(self, simple_pdf, caplog):
        """Test that fetch logs debug message."""
        source = PDFDataSource(simple_pdf)

        with caplog.at_level(logging.DEBUG):
            await source.fetch()

        assert any("Reading PDF file" in record.message for record in caplog.records)
        assert any("Parsed PDF file" in record.message for record in caplog.records)


# ============================================================================
# Test Integration Scenarios
# ============================================================================


class TestPDFDataSourceIntegration:
    """Integration tests for real-world scenarios."""

    @pytest.mark.asyncio
    async def test_read_then_validate(self, simple_pdf):
        """Test reading file then validating configuration."""
        source = PDFDataSource(simple_pdf)

        # Read file
        result = await source.fetch()
        assert result["row_count"] > 0

        # Validate config
        is_valid = await source.validate_config()
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_multiple_fetches_same_source(self, simple_pdf):
        """Test fetching multiple times from same source."""
        source = PDFDataSource(simple_pdf)

        # First fetch
        result1 = await source.fetch()

        # Second fetch (no caching, should re-read)
        result2 = await source.fetch()

        # Results should be identical
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_different_sources_same_file(self, simple_pdf):
        """Test multiple sources reading same file."""
        source1 = PDFDataSource(simple_pdf)
        source2 = PDFDataSource(simple_pdf)

        result1 = await source1.fetch()
        result2 = await source2.fetch()

        # Should get same data
        assert result1 == result2
