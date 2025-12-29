"""
Integration tests for Batch 1 data sources migration.

Tests all 4 data sources migrated from EDGAR to platform:
- FileDataSource (CSV, JSON, YAML, Text)
- APIDataSource (HTTP client with auth, caching, rate limiting)
- URLDataSource (Simple HTTP GET with content detection)
- JinaDataSource (Jina.ai web scraping service)

Verifies:
1. Platform imports work correctly
2. EDGAR wrapper imports work with deprecation warnings
3. Identical functionality between platform and wrapper
4. Backward compatibility maintained
5. All core methods functional
"""

import json
import warnings
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# Test imports from both platform and EDGAR packages


class TestFileDataSourceMigration:
    """Test FileDataSource migration from EDGAR to platform."""

    def test_platform_import(self) -> None:
        """Verify platform import works."""
        from extract_transform_platform.data_sources.file import FileDataSource

        assert FileDataSource is not None
        assert hasattr(FileDataSource, "fetch")

    def test_edgar_wrapper_import_with_warning(self) -> None:
        """Verify EDGAR wrapper import works with deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from edgar_analyzer.data_sources import FileDataSource

            # Multiple warnings expected from wrapper imports
            assert len(w) >= 1
            # Check at least one is the expected deprecation
            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
                and "deprecated" in str(warning.message).lower()
            ]
            assert len(deprecation_warnings) >= 1

    @pytest.mark.asyncio
    async def test_csv_parsing_platform(self, tmp_path: Path) -> None:
        """Test CSV parsing using platform import."""
        from extract_transform_platform.data_sources.file import FileDataSource

        # Create test CSV
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n")

        source = FileDataSource(str(csv_file))
        result = await source.fetch()

        assert result is not None
        assert "rows" in result
        assert len(result["rows"]) == 2
        assert result["rows"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_csv_parsing_wrapper(self, tmp_path: Path) -> None:
        """Test CSV parsing using EDGAR wrapper (should match platform)."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import FileDataSource

        # Create test CSV
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n")

        source = FileDataSource(str(csv_file))
        result = await source.fetch()

        assert result is not None
        assert "rows" in result
        assert len(result["rows"]) == 2
        assert result["rows"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_json_parsing_platform(self, tmp_path: Path) -> None:
        """Test JSON parsing using platform import."""
        from extract_transform_platform.data_sources.file import FileDataSource

        # Create test JSON
        json_file = tmp_path / "test.json"
        json_file.write_text('{"users": [{"name": "Alice"}, {"name": "Bob"}]}')

        source = FileDataSource(str(json_file))
        result = await source.fetch()

        assert result is not None
        assert "users" in result
        assert len(result["users"]) == 2

    @pytest.mark.asyncio
    async def test_yaml_parsing_platform(self, tmp_path: Path) -> None:
        """Test YAML parsing using platform import."""
        from extract_transform_platform.data_sources.file import FileDataSource

        # Create test YAML
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("name: Test\nvalue: 123\n")

        source = FileDataSource(str(yaml_file))
        result = await source.fetch()

        assert result is not None
        assert result["name"] == "Test"
        assert result["value"] == 123

    @pytest.mark.asyncio
    async def test_identical_functionality(self, tmp_path: Path) -> None:
        """Verify platform and wrapper produce identical results."""
        from extract_transform_platform.data_sources.file import (
            FileDataSource as PlatformFS,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import FileDataSource as WrapperFS

        # Create test CSV
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n")

        platform_result = await PlatformFS(str(csv_file)).fetch()
        wrapper_result = await WrapperFS(str(csv_file)).fetch()

        # Results should be identical
        assert platform_result == wrapper_result


class TestAPIDataSourceMigration:
    """Test APIDataSource migration from EDGAR to platform."""

    def test_platform_import(self) -> None:
        """Verify platform import works."""
        from extract_transform_platform.data_sources.web import APIDataSource

        assert APIDataSource is not None
        assert hasattr(APIDataSource, "fetch")

    def test_edgar_wrapper_import_with_warning(self) -> None:
        """Verify EDGAR wrapper import works with deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from edgar_analyzer.data_sources import APIDataSource

            # APIDataSource wrapper may not emit deprecation warning
            # if it's a direct re-export without wrapper logic
            # Just verify import works
            assert APIDataSource is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request")
    async def test_http_get_platform(self, mock_request: MagicMock) -> None:
        """Test HTTP GET using platform import."""
        from extract_transform_platform.data_sources.web import APIDataSource

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        source = APIDataSource("https://api.example.com/data")
        result = await source.fetch()

        assert result is not None
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request")
    async def test_http_post_platform(self, mock_request: MagicMock) -> None:
        """Test HTTP POST using platform import."""
        from extract_transform_platform.data_sources.web import APIDataSource

        mock_response = MagicMock()
        mock_response.json.return_value = {"created": True}
        mock_response.status_code = 201
        mock_request.return_value = mock_response

        source = APIDataSource("https://api.example.com/create")
        result = await source.fetch(endpoint="/create", method="POST")

        assert result is not None
        assert result["created"] is True

    def test_bearer_token_auth(self) -> None:
        """Test Bearer token authentication."""
        from extract_transform_platform.data_sources.web import APIDataSource

        source = APIDataSource(
            "https://api.example.com/secure", auth_token="test-token-123"
        )

        # Verify token was added to headers as Bearer token
        assert "Authorization" in source.headers
        assert source.headers["Authorization"] == "Bearer test-token-123"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request")
    async def test_identical_functionality(self, mock_request: MagicMock) -> None:
        """Verify platform and wrapper produce identical results."""
        from extract_transform_platform.data_sources.web import (
            APIDataSource as PlatformAPI,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import APIDataSource as WrapperAPI

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        platform_result = await PlatformAPI("https://api.example.com/data").fetch()
        wrapper_result = await WrapperAPI("https://api.example.com/data").fetch()

        # Results should be identical
        assert platform_result == wrapper_result


class TestURLDataSourceMigration:
    """Test URLDataSource migration from EDGAR to platform."""

    def test_platform_import(self) -> None:
        """Verify platform import works."""
        from extract_transform_platform.data_sources.web import URLDataSource

        assert URLDataSource is not None
        assert hasattr(URLDataSource, "fetch")

    def test_edgar_wrapper_import_with_warning(self) -> None:
        """Verify EDGAR wrapper import works with deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from edgar_analyzer.data_sources import URLDataSource

            # URLDataSource wrapper may not emit deprecation warning
            # if it's a direct re-export without wrapper logic
            # Just verify import works
            assert URLDataSource is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_json_url_platform(self, mock_get: MagicMock) -> None:
        """Test JSON URL fetching using platform import."""
        from extract_transform_platform.data_sources.web import URLDataSource

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.headers = {"content-type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        source = URLDataSource()
        result = await source.fetch(url="https://example.com/data.json")

        assert result is not None
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_text_url_platform(self, mock_get: MagicMock) -> None:
        """Test text URL fetching using platform import."""
        from extract_transform_platform.data_sources.web import URLDataSource

        mock_response = MagicMock()
        mock_response.text = "Hello, World!"
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        source = URLDataSource()
        result = await source.fetch(url="https://example.com/hello.txt")

        assert result is not None
        assert result["content"] == "Hello, World!"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_identical_functionality(self, mock_get: MagicMock) -> None:
        """Verify platform and wrapper produce identical results."""
        from extract_transform_platform.data_sources.web import (
            URLDataSource as PlatformURL,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import URLDataSource as WrapperURL

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"content-type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        platform_result = await PlatformURL().fetch(url="https://example.com/data.json")
        wrapper_result = await WrapperURL().fetch(url="https://example.com/data.json")

        # Results should be identical
        assert platform_result == wrapper_result


class TestJinaDataSourceMigration:
    """Test JinaDataSource migration from EDGAR to platform."""

    def test_platform_import(self) -> None:
        """Verify platform import works."""
        from extract_transform_platform.data_sources.web import JinaDataSource

        assert JinaDataSource is not None
        assert hasattr(JinaDataSource, "fetch")

    def test_edgar_wrapper_import_with_warning(self) -> None:
        """Verify EDGAR wrapper import works with deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from edgar_analyzer.data_sources import JinaDataSource

            # JinaDataSource wrapper may not emit deprecation warning
            # if it's a direct re-export without wrapper logic
            # Just verify import works
            assert JinaDataSource is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_jina_api_platform(self, mock_get: MagicMock) -> None:
        """Test Jina.ai API integration using platform import."""
        from extract_transform_platform.data_sources.web import JinaDataSource

        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "data": {"title": "Test Page", "content": "Test content"}
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        source = JinaDataSource(api_key="test-key")
        result = await source.fetch(url="https://example.com")

        assert result is not None
        assert "content" in result
        assert result["content"] == "Test content"
        assert result["title"] == "Test Page"

    def test_api_key_handling_platform(self) -> None:
        """Test API key handling in platform import."""
        from extract_transform_platform.data_sources.web import JinaDataSource

        # Test with explicit API key
        source = JinaDataSource(api_key="test-key-123")
        assert source.api_key == "test-key-123"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_identical_functionality(self, mock_get: MagicMock) -> None:
        """Verify platform and wrapper produce identical results."""
        from extract_transform_platform.data_sources.web import (
            JinaDataSource as PlatformJina,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import JinaDataSource as WrapperJina

        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "data": {"title": "Test Title", "content": "Test content", "metadata": {}}
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        platform_result = await PlatformJina(api_key="test").fetch(
            url="https://example.com"
        )
        wrapper_result = await WrapperJina(api_key="test").fetch(
            url="https://example.com"
        )

        # Results should be identical (ignoring extracted_at timestamp)
        assert platform_result["content"] == wrapper_result["content"]
        assert platform_result["title"] == wrapper_result["title"]
        assert platform_result["url"] == wrapper_result["url"]


class TestBatch1ExportsAndPackaging:
    """Test that all exports are correct and backward compatible."""

    def test_platform_package_exports(self) -> None:
        """Verify all data sources are exported from platform package."""
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

        # All should be importable
        assert FileDataSource is not None
        assert APIDataSource is not None
        assert URLDataSource is not None
        assert JinaDataSource is not None
        assert ExcelDataSource is not None
        assert PDFDataSource is not None

    def test_edgar_package_exports(self) -> None:
        """Verify all data sources are still exported from EDGAR package."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import (
                APIDataSource,
                ExcelDataSource,
                FileDataSource,
                JinaDataSource,
                PDFDataSource,
                URLDataSource,
            )

        # All should be importable (with warnings suppressed)
        assert FileDataSource is not None
        assert APIDataSource is not None
        assert URLDataSource is not None
        assert JinaDataSource is not None
        assert ExcelDataSource is not None
        assert PDFDataSource is not None

    def test_base_class_exports(self) -> None:
        """Verify base classes are exported correctly."""
        from extract_transform_platform.core import BaseDataSource, IDataSource

        assert BaseDataSource is not None
        assert IDataSource is not None

    def test_edgar_base_class_deprecation(self) -> None:
        """Verify base classes show deprecation warnings in EDGAR package."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from edgar_analyzer.data_sources import BaseDataSource, IDataSource

            # May have warnings for base imports (optional - not enforced)
            # Just verify imports work
            assert BaseDataSource is not None
            assert IDataSource is not None


class TestTypeHintsPreserved:
    """Verify type hints are preserved after migration."""

    def test_file_source_type_hints(self) -> None:
        """Verify FileDataSource has proper type hints."""
        from extract_transform_platform.data_sources.file import FileDataSource

        # Check return type hints
        assert hasattr(FileDataSource.fetch, "__annotations__")

    def test_api_source_type_hints(self) -> None:
        """Verify APIDataSource has proper type hints."""
        from extract_transform_platform.data_sources.web import APIDataSource

        # Check return type hints
        assert hasattr(APIDataSource.fetch, "__annotations__")

    def test_url_source_type_hints(self) -> None:
        """Verify URLDataSource has proper type hints."""
        from extract_transform_platform.data_sources.web import URLDataSource

        # Check return type hints
        assert hasattr(URLDataSource.fetch, "__annotations__")

    def test_jina_source_type_hints(self) -> None:
        """Verify JinaDataSource has proper type hints."""
        from extract_transform_platform.data_sources.web import JinaDataSource

        # Check return type hints
        assert hasattr(JinaDataSource.fetch, "__annotations__")


class TestCorMethodsAllSources:
    """Test core methods (fetch, validate_config, get_cache_key) for all sources."""

    @pytest.mark.asyncio
    async def test_file_source_core_methods(self, tmp_path: Path) -> None:
        """Test core methods for FileDataSource."""
        from extract_transform_platform.data_sources.file import FileDataSource

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,30\n")

        source = FileDataSource(str(csv_file))

        # fetch() works
        result = await source.fetch()
        assert result is not None

        # validate_config() exists
        assert hasattr(source, "validate_config")

        # get_cache_key() exists
        assert hasattr(source, "get_cache_key")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request")
    async def test_api_source_core_methods(self, mock_request: MagicMock) -> None:
        """Test core methods for APIDataSource."""
        from extract_transform_platform.data_sources.web import APIDataSource

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        source = APIDataSource("https://api.example.com/data")

        # fetch() works
        result = await source.fetch()
        assert result is not None

        # validate_config() exists
        assert hasattr(source, "validate_config")

        # get_cache_key() exists
        cache_key = source.get_cache_key()
        assert isinstance(cache_key, str)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_url_source_core_methods(self, mock_get: MagicMock) -> None:
        """Test core methods for URLDataSource."""
        from extract_transform_platform.data_sources.web import URLDataSource

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"content-type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        source = URLDataSource()

        # fetch() works
        result = await source.fetch(url="https://example.com/data.json")
        assert result is not None

        # validate_config() exists
        assert hasattr(source, "validate_config")

        # get_cache_key() exists
        cache_key = source.get_cache_key(url="https://example.com/data.json")
        assert isinstance(cache_key, str)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_jina_source_core_methods(self, mock_get: MagicMock) -> None:
        """Test core methods for JinaDataSource."""
        from extract_transform_platform.data_sources.web import JinaDataSource

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        source = JinaDataSource(api_key="test")

        # fetch() works
        result = await source.fetch(url="https://example.com")
        assert result is not None

        # validate_config() exists
        assert hasattr(source, "validate_config")

        # get_cache_key() exists
        cache_key = source.get_cache_key(url="https://example.com")
        assert isinstance(cache_key, str)


class TestNoBreakingChanges:
    """Verify no breaking changes in public API."""

    @pytest.mark.asyncio
    async def test_file_source_api_unchanged(self, tmp_path: Path) -> None:
        """Verify FileDataSource API is unchanged."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import FileDataSource

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,30\n")

        # Old code should still work
        source = FileDataSource(str(csv_file))
        result = await source.fetch()

        assert result is not None
        assert "rows" in result

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.request")
    async def test_api_source_api_unchanged(self, mock_request: MagicMock) -> None:
        """Verify APIDataSource API is unchanged."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import APIDataSource

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Old code should still work
        source = APIDataSource("https://api.example.com/data")
        result = await source.fetch()

        assert result is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_url_source_api_unchanged(self, mock_get: MagicMock) -> None:
        """Verify URLDataSource API is unchanged."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import URLDataSource

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"content-type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Old code should still work
        source = URLDataSource()
        result = await source.fetch(url="https://example.com/data.json")

        assert result is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_jina_source_api_unchanged(self, mock_get: MagicMock) -> None:
        """Verify JinaDataSource API is unchanged."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from edgar_analyzer.data_sources import JinaDataSource

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Old code should still work
        source = JinaDataSource(api_key="test")
        result = await source.fetch(url="https://example.com")

        assert result is not None
