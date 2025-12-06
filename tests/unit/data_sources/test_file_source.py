"""
Unit Tests for FileDataSource

Comprehensive test coverage for local file data source including:
- Initialization validation (file existence, encoding)
- Format parsing (JSON, YAML, CSV, text, unknown extensions)
- Error handling (file not found, malformed files, directory paths)
- Edge cases (empty files, large files, encoding issues)
- Configuration validation (validate_config, cache_key)

Test Organization:
- Class per functionality group (5 classes)
- Descriptive test names following pytest conventions
- Clear docstrings with coverage notes
- Uses tmp_path for file creation (no artifacts)
- Async tests use @pytest.mark.asyncio

Target Coverage: 70%+ (17 unit tests)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

import pytest

from extract_transform_platform.data_sources.file.file_source import FileDataSource


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def simple_json_file(tmp_path):
    """Create simple JSON file for testing."""
    file_path = tmp_path / "test.json"
    data = {"name": "Alice", "age": 30, "city": "NYC"}
    file_path.write_text(json.dumps(data))
    return file_path


@pytest.fixture
def simple_csv_file(tmp_path):
    """Create simple CSV file for testing."""
    file_path = tmp_path / "test.csv"
    file_path.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA\n")
    return file_path


@pytest.fixture
def simple_yaml_file(tmp_path):
    """Create simple YAML file for testing."""
    file_path = tmp_path / "test.yaml"
    file_path.write_text("name: Alice\nage: 30\ncity: NYC\n")
    return file_path


@pytest.fixture
def simple_text_file(tmp_path):
    """Create simple text file for testing."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello World\nLine 2\nLine 3\n")
    return file_path


@pytest.fixture
def mock_json_data():
    """Mock JSON data for testing."""
    return {"name": "Alice", "age": 30, "city": "NYC"}


@pytest.fixture
def mock_csv_content():
    """Mock CSV content for testing."""
    return "name,age,city\nAlice,30,NYC\nBob,25,LA"


# ============================================================================
# Test Initialization
# ============================================================================


class TestFileDataSourceInitialization:
    """Tests for FileDataSource initialization and validation."""

    def test_init_with_valid_file_path(self, simple_json_file):
        """Test initialization with valid file path.

        Coverage: Lines 62-90 (__init__ method)
        """
        source = FileDataSource(simple_json_file)

        assert source.file_path == simple_json_file
        assert source.encoding == "utf-8"
        assert source.cache_enabled is False
        assert source.rate_limit_per_minute == 9999
        assert source.max_retries == 0

    def test_init_with_encoding(self, simple_json_file):
        """Test initialization with custom encoding parameter.

        Coverage: Lines 62-90 (encoding parameter)
        """
        source = FileDataSource(simple_json_file, encoding="latin-1")

        assert source.file_path == simple_json_file
        assert source.encoding == "latin-1"

    def test_init_without_cache(self, simple_json_file):
        """Test initialization disables cache for local files.

        Coverage: Lines 80-84 (kwargs overrides)
        """
        source = FileDataSource(simple_json_file)

        # Local files should never use cache
        assert source.cache_enabled is False
        # No rate limiting for local I/O
        assert source.rate_limit_per_minute == 9999
        # No retries for local files (fail fast)
        assert source.max_retries == 0


# ============================================================================
# Test Format Parsing
# ============================================================================


class TestFileDataSourceFormatParsing:
    """Tests for format detection and parsing for all supported types."""

    @pytest.mark.asyncio
    async def test_fetch_json_format(self, simple_json_file, mock_json_data):
        """Test successful JSON file parsing.

        Coverage: Lines 92-141 (fetch + format detection), 142-160 (_parse_json)
        """
        source = FileDataSource(simple_json_file)
        result = await source.fetch()

        # Verify JSON data is returned directly
        assert result == mock_json_data
        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_fetch_yaml_format(self, simple_yaml_file):
        """Test successful YAML file parsing.

        Coverage: Lines 92-141 (fetch + format detection), 162-189 (_parse_yaml)
        """
        source = FileDataSource(simple_yaml_file)
        result = await source.fetch()

        # Verify YAML data is parsed correctly
        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_fetch_csv_format(self, simple_csv_file):
        """Test successful CSV file parsing.

        Coverage: Lines 92-141 (fetch + format detection), 190-229 (_parse_csv)
        """
        source = FileDataSource(simple_csv_file)
        result = await source.fetch()

        # Verify CSV structure matches expected format
        assert "rows" in result
        assert "row_count" in result
        assert "columns" in result
        assert "file_path" in result

        # Verify data content
        assert result["row_count"] == 2
        assert result["columns"] == ["name", "age", "city"]
        assert len(result["rows"]) == 2
        assert result["rows"][0]["name"] == "Alice"
        assert result["rows"][1]["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_fetch_text_format(self, simple_text_file):
        """Test plain text file parsing.

        Coverage: Lines 92-141 (fetch + format detection), 231-248 (_parse_text)
        """
        source = FileDataSource(simple_text_file)
        result = await source.fetch()

        # Verify text file structure
        assert "content" in result
        assert "file_path" in result
        assert "file_name" in result
        assert "file_size" in result
        assert "line_count" in result

        # Verify content
        assert result["content"] == "Hello World\nLine 2\nLine 3\n"
        assert result["file_name"] == "test.txt"
        assert result["line_count"] == 4  # 3 lines + final newline
        assert result["file_size"] > 0

    @pytest.mark.asyncio
    async def test_fetch_unknown_extension(self, tmp_path):
        """Test text fallback for unknown file extension.

        Coverage: Lines 139-140 (else branch → _parse_text)
        """
        # Create file with unknown extension
        unknown_file = tmp_path / "README.md"
        unknown_file.write_text("# Markdown Content\n\nSome text here.\n")

        source = FileDataSource(unknown_file)
        result = await source.fetch()

        # Should fall back to text parsing
        assert "content" in result
        assert result["content"] == "# Markdown Content\n\nSome text here.\n"
        assert result["file_name"] == "README.md"


# ============================================================================
# Test Error Handling
# ============================================================================


class TestFileDataSourceErrorHandling:
    """Tests for error handling for all failure scenarios."""

    @pytest.mark.asyncio
    async def test_fetch_file_not_found(self, tmp_path):
        """Test FileNotFoundError when file doesn't exist.

        Coverage: Lines 113-114 (fetch → FileNotFoundError)
        """
        nonexistent = tmp_path / "nonexistent.json"
        source = FileDataSource(nonexistent)

        with pytest.raises(FileNotFoundError, match="File not found"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_fetch_path_is_directory(self, tmp_path):
        """Test ValueError when path is directory not file.

        Coverage: Lines 116-117 (fetch → is_file() → ValueError)
        """
        # tmp_path is a directory
        source = FileDataSource(tmp_path)

        with pytest.raises(ValueError, match="Path is not a file"):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_fetch_malformed_json(self, tmp_path):
        """Test json.JSONDecodeError for invalid JSON.

        Coverage: Lines 154-160 (_parse_json → JSONDecodeError)
        """
        malformed_json = tmp_path / "bad.json"
        malformed_json.write_text("{invalid json content")

        source = FileDataSource(malformed_json)

        with pytest.raises(json.JSONDecodeError):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_fetch_malformed_yaml(self, tmp_path):
        """Test yaml.YAMLError for invalid YAML.

        Coverage: Lines 182-188 (_parse_yaml → YAMLError)
        """
        malformed_yaml = tmp_path / "bad.yaml"
        malformed_yaml.write_text("key: [unclosed list\n  - item")

        source = FileDataSource(malformed_yaml)

        # Should raise yaml.YAMLError (or Exception if yaml not specific)
        with pytest.raises(Exception):
            await source.fetch()


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestFileDataSourceEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_fetch_empty_file(self, tmp_path):
        """Test handling empty text file gracefully.

        Coverage: Lines 231-248 (_parse_text with empty content)
        """
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        source = FileDataSource(empty_file)
        result = await source.fetch()

        # Should handle empty file
        assert result["content"] == ""
        assert result["line_count"] == 1  # Empty file has 1 line
        assert result["file_size"] == 0

    @pytest.mark.asyncio
    async def test_fetch_encoding_error(self, tmp_path):
        """Test handling encoding issues (UTF-8 vs Latin-1).

        Coverage: Lines 122 (read_text with encoding)
        """
        # Create file with Latin-1 encoding
        latin1_file = tmp_path / "latin1.txt"
        latin1_file.write_bytes(b"Caf\xe9")  # Latin-1 encoded "Café"

        # Should fail with default UTF-8 encoding
        source_utf8 = FileDataSource(latin1_file)
        with pytest.raises(UnicodeDecodeError):
            await source_utf8.fetch()

        # Should succeed with correct encoding
        source_latin1 = FileDataSource(latin1_file, encoding="latin-1")
        result = await source_latin1.fetch()
        assert "Café" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_large_file(self, tmp_path):
        """Test handling large file (>1MB).

        Coverage: Lines 92-141 (fetch with large content)
        Performance: Verify file reading doesn't timeout
        """
        large_file = tmp_path / "large.txt"
        # Create 1MB file (1024 * 1024 characters)
        large_content = "x" * (1024 * 1024)
        large_file.write_text(large_content)

        source = FileDataSource(large_file)
        result = await source.fetch()

        # Should successfully read large file
        assert result["file_size"] == 1024 * 1024
        assert len(result["content"]) == 1024 * 1024
        assert result["content"] == large_content


# ============================================================================
# Test Configuration
# ============================================================================


class TestFileDataSourceConfiguration:
    """Tests for configuration validation and cache key generation."""

    @pytest.mark.asyncio
    async def test_validate_config_valid(self, simple_json_file):
        """Test validate_config returns True for valid file.

        Coverage: Lines 250-267 (validate_config → True path)
        """
        source = FileDataSource(simple_json_file)
        is_valid = await source.validate_config()

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_config_missing_file_path(self, tmp_path):
        """Test validate_config returns False for missing file.

        Coverage: Lines 250-274 (validate_config → False path)
        """
        nonexistent = tmp_path / "missing.json"
        source = FileDataSource(nonexistent)

        is_valid = await source.validate_config()

        assert is_valid is False

    def test_get_cache_key(self, simple_json_file):
        """Test cache key generation from file path.

        Coverage: Lines 276-290 (get_cache_key)
        """
        source = FileDataSource(simple_json_file)
        cache_key = source.get_cache_key()

        # Cache key should be absolute file path
        assert cache_key == str(simple_json_file.absolute())

    def test_get_cache_key_deterministic(self, simple_json_file):
        """Test cache key is deterministic (same file = same key).

        Coverage: Lines 276-290 (get_cache_key consistency)
        """
        source1 = FileDataSource(simple_json_file)
        source2 = FileDataSource(simple_json_file)

        assert source1.get_cache_key() == source2.get_cache_key()

    @pytest.mark.asyncio
    async def test_validate_config_path_is_directory(self, tmp_path):
        """Test validate_config returns False for directory path.

        Coverage: Lines 258-265 (validate_config → is_file check)
        """
        # tmp_path is a directory
        source = FileDataSource(tmp_path)

        is_valid = await source.validate_config()

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_permission_error(self, simple_json_file, monkeypatch):
        """Test validate_config returns False on PermissionError.

        Coverage: Lines 269-271 (validate_config → PermissionError handler)
        """
        source = FileDataSource(simple_json_file)

        # Mock read_bytes to raise PermissionError
        def mock_read_bytes():
            raise PermissionError("Access denied")

        monkeypatch.setattr(Path, "read_bytes", lambda self: mock_read_bytes())

        is_valid = await source.validate_config()

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_generic_exception(self, simple_json_file, monkeypatch):
        """Test validate_config returns False on unexpected exception.

        Coverage: Lines 272-274 (validate_config → Exception handler)
        """
        source = FileDataSource(simple_json_file)

        # Mock exists to raise unexpected exception
        def mock_exists():
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(Path, "exists", lambda self: mock_exists())

        is_valid = await source.validate_config()

        assert is_valid is False


# ============================================================================
# Test Logging (Optional - for completeness)
# ============================================================================


class TestFileDataSourceLogging:
    """Tests for logging behavior (optional coverage boost)."""

    def test_logging_on_initialization(self, simple_json_file, caplog):
        """Test that initialization logs info message.

        Coverage: Line 90 (logger.info)
        """
        with caplog.at_level(logging.INFO):
            source = FileDataSource(simple_json_file)

        assert any(
            "Initialized FileDataSource" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logging_on_fetch(self, simple_json_file, caplog):
        """Test that fetch logs debug messages.

        Coverage: Lines 119-128 (logger.debug)
        """
        source = FileDataSource(simple_json_file)

        with caplog.at_level(logging.DEBUG):
            await source.fetch()

        assert any("Reading file" in record.message for record in caplog.records)
        assert any("bytes from" in record.message for record in caplog.records)
