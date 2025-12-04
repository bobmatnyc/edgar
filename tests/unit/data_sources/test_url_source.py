"""
Unit Tests for URLDataSource

Comprehensive test coverage for URL data source including:
- Initialization validation (timeout configuration)
- Successful URL fetches (JSON, text, various content types)
- URL validation (http/https protocol enforcement)
- HTTP error handling (404, 500, 403, 503)
- Network timeout handling
- Cache integration (hits, misses, TTL)
- JSON parsing errors (invalid JSON with JSON content-type)
- Content-type detection and handling
- Cache key generation (MD5 hashing)
- Configuration validation (always valid)

Test Organization:
- Class per functionality group
- Descriptive test names
- Clear docstrings
- Uses AsyncMock for httpx.AsyncClient
- Async tests use @pytest.mark.asyncio

Coverage Target: 70%+ (aim for 100% like api_source.py)
File Under Test: src/extract_transform_platform/data_sources/web/url_source.py (39 statements)
"""

import hashlib
import logging
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from extract_transform_platform.data_sources.web.url_source import URLDataSource


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def url_source():
    """Create URLDataSource instance with default settings."""
    return URLDataSource()


@pytest.fixture
def url_source_custom():
    """Create URLDataSource instance with custom timeout."""
    return URLDataSource(timeout_seconds=10.0)


@pytest.fixture
def url_source_with_cache():
    """Create URLDataSource instance with caching enabled."""
    return URLDataSource(cache_enabled=True, cache_ttl_seconds=300)


@pytest.fixture
def url_source_no_cache():
    """Create URLDataSource instance with caching disabled."""
    return URLDataSource(cache_enabled=False)


@pytest.fixture
def mock_json_response():
    """Mock HTTP response with JSON content."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {"content-type": "application/json; charset=utf-8"}
    mock.content = b'{"result": "success", "data": [1, 2, 3]}'
    mock.json.return_value = {"result": "success", "data": [1, 2, 3]}
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_text_response():
    """Mock HTTP response with plain text content."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {"content-type": "text/plain; charset=utf-8"}
    mock.content = b"This is plain text content"
    mock.text = "This is plain text content"
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_html_response():
    """Mock HTTP response with HTML content."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {"content-type": "text/html; charset=utf-8"}
    mock.content = b"<html><body><h1>Test Page</h1></body></html>"
    mock.text = "<html><body><h1>Test Page</h1></body></html>"
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_invalid_json_response():
    """Mock HTTP response with JSON content-type but invalid JSON."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {"content-type": "application/json"}
    mock.content = b"Not valid JSON content"
    mock.text = "Not valid JSON content"
    mock.json.side_effect = ValueError("Invalid JSON")
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_no_content_type_response():
    """Mock HTTP response with no content-type header."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {}  # No content-type header
    mock.content = b"Some content"
    mock.text = "Some content"
    mock.raise_for_status = MagicMock()
    return mock


# ============================================================================
# Test Class: Initialization
# ============================================================================


class TestURLDataSourceInitialization:
    """Tests for URLDataSource initialization and configuration."""

    def test_default_initialization(self, url_source):
        """Test URLDataSource initializes with default settings."""
        assert url_source is not None
        assert url_source.timeout_seconds == 30.0
        assert url_source.cache_enabled is True
        assert url_source.cache_ttl_seconds == 3600

    def test_custom_timeout(self, url_source_custom):
        """Test URLDataSource initializes with custom timeout."""
        assert url_source_custom.timeout_seconds == 10.0

    def test_cache_enabled_configuration(self, url_source_with_cache):
        """Test URLDataSource with cache enabled."""
        assert url_source_with_cache.cache_enabled is True
        assert url_source_with_cache.cache_ttl_seconds == 300

    def test_cache_disabled_configuration(self, url_source_no_cache):
        """Test URLDataSource with cache disabled."""
        assert url_source_no_cache.cache_enabled is False

    def test_inherits_from_base_data_source(self, url_source):
        """Test URLDataSource inherits from BaseDataSource."""
        from extract_transform_platform.core.base import BaseDataSource

        assert isinstance(url_source, BaseDataSource)


# ============================================================================
# Test Class: Successful URL Fetches
# ============================================================================


class TestSuccessfulURLFetches:
    """Tests for successful URL fetch operations."""

    @pytest.mark.asyncio
    async def test_fetch_json_success(self, url_source, mock_json_response):
        """Test successful fetch of JSON content."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_json_response

            result = await url_source.fetch(url="https://api.example.com/data")

            assert result is not None
            assert result["result"] == "success"
            assert result["data"] == [1, 2, 3]
            mock_get.assert_called_once_with("https://api.example.com/data")

    @pytest.mark.asyncio
    async def test_fetch_text_success(self, url_source, mock_text_response):
        """Test successful fetch of plain text content."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_text_response

            result = await url_source.fetch(url="https://example.com/robots.txt")

            assert result is not None
            assert result["content"] == "This is plain text content"
            assert result["url"] == "https://example.com/robots.txt"
            assert result["content_type"] == "text/plain; charset=utf-8"
            assert result["status_code"] == 200
            assert result["content_length"] == len(b"This is plain text content")

    @pytest.mark.asyncio
    async def test_fetch_html_success(self, url_source, mock_html_response):
        """Test successful fetch of HTML content."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_html_response

            result = await url_source.fetch(url="https://example.com/index.html")

            assert result is not None
            assert result["content"] == "<html><body><h1>Test Page</h1></body></html>"
            assert result["url"] == "https://example.com/index.html"
            assert result["content_type"] == "text/html; charset=utf-8"

    @pytest.mark.asyncio
    async def test_fetch_http_url(self, url_source, mock_text_response):
        """Test fetch with http:// URL (not just https://)."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_text_response

            result = await url_source.fetch(url="http://example.com/data")

            assert result is not None
            assert result["url"] == "http://example.com/data"

    @pytest.mark.asyncio
    async def test_fetch_no_content_type_header(
        self, url_source, mock_no_content_type_response
    ):
        """Test fetch when response has no content-type header."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_no_content_type_response

            result = await url_source.fetch(url="https://example.com/data")

            assert result is not None
            assert result["content"] == "Some content"
            assert result["content_type"] == ""  # Empty string when no header


# ============================================================================
# Test Class: URL Validation
# ============================================================================


class TestURLValidation:
    """Tests for URL format validation."""

    @pytest.mark.asyncio
    async def test_invalid_url_no_protocol(self, url_source):
        """Test fetch with URL missing protocol raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URL.*must start with http"):
            await url_source.fetch(url="example.com")

    @pytest.mark.asyncio
    async def test_invalid_url_ftp_protocol(self, url_source):
        """Test fetch with FTP protocol raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URL.*must start with http"):
            await url_source.fetch(url="ftp://example.com/file.txt")

    @pytest.mark.asyncio
    async def test_invalid_url_empty_string(self, url_source):
        """Test fetch with empty URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URL.*must start with http"):
            await url_source.fetch(url="")

    @pytest.mark.asyncio
    async def test_invalid_url_file_protocol(self, url_source):
        """Test fetch with file:// protocol raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URL.*must start with http"):
            await url_source.fetch(url="file:///etc/passwd")

    @pytest.mark.asyncio
    async def test_invalid_url_malformed_protocol(self, url_source):
        """Test fetch with malformed protocol raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URL.*must start with http"):
            await url_source.fetch(url="://missing-scheme")


# ============================================================================
# Test Class: HTTP Error Handling
# ============================================================================


class TestHTTPErrorHandling:
    """Tests for HTTP error response handling."""

    @pytest.mark.asyncio
    async def test_http_404_not_found(self, url_source):
        """Test 404 Not Found error raises HTTPStatusError."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="Not Found",
                request=MagicMock(),
                response=mock_response,
            )
            mock_get.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await url_source.fetch(url="https://example.com/nonexistent")

    @pytest.mark.asyncio
    async def test_http_500_server_error(self, url_source):
        """Test 500 Internal Server Error raises HTTPStatusError."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="Internal Server Error",
                request=MagicMock(),
                response=mock_response,
            )
            mock_get.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await url_source.fetch(url="https://example.com/error")

    @pytest.mark.asyncio
    async def test_http_403_forbidden(self, url_source):
        """Test 403 Forbidden error raises HTTPStatusError."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="Forbidden",
                request=MagicMock(),
                response=mock_response,
            )
            mock_get.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await url_source.fetch(url="https://example.com/forbidden")

    @pytest.mark.asyncio
    async def test_http_503_service_unavailable(self, url_source):
        """Test 503 Service Unavailable error raises HTTPStatusError."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="Service Unavailable",
                request=MagicMock(),
                response=mock_response,
            )
            mock_get.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await url_source.fetch(url="https://example.com/unavailable")


# ============================================================================
# Test Class: Network Issues
# ============================================================================


class TestNetworkIssues:
    """Tests for network-level error handling."""

    @pytest.mark.asyncio
    async def test_timeout_error(self, url_source):
        """Test request timeout raises TimeoutException."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(httpx.TimeoutException):
                await url_source.fetch(url="https://example.com/slow")

    @pytest.mark.asyncio
    async def test_connect_timeout(self, url_source):
        """Test connection timeout raises ConnectTimeout."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectTimeout("Connection timeout")

            with pytest.raises(httpx.ConnectTimeout):
                await url_source.fetch(url="https://example.com/unreachable")

    @pytest.mark.asyncio
    async def test_network_error(self, url_source):
        """Test network error raises NetworkError."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.NetworkError("Network unreachable")

            with pytest.raises(httpx.NetworkError):
                await url_source.fetch(url="https://example.com/network-fail")


# ============================================================================
# Test Class: JSON Parsing
# ============================================================================


class TestJSONParsing:
    """Tests for JSON content parsing."""

    @pytest.mark.asyncio
    async def test_invalid_json_fallback_to_text(
        self, url_source, mock_invalid_json_response
    ):
        """Test invalid JSON with JSON content-type falls back to text."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_invalid_json_response

            result = await url_source.fetch(url="https://example.com/bad-json")

            # Should fallback to text response format
            assert result is not None
            assert result["content"] == "Not valid JSON content"
            assert result["url"] == "https://example.com/bad-json"
            assert "content_type" in result

    @pytest.mark.asyncio
    async def test_json_with_various_content_types(self, url_source):
        """Test JSON detection with various content-type variations."""
        test_cases = [
            "application/json",
            "application/json; charset=utf-8",
            "application/json;charset=UTF-8",
            "APPLICATION/JSON",  # Case insensitive
        ]

        for content_type in test_cases:
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.headers = {"content-type": content_type}
                mock_response.content = b'{"test": true}'
                mock_response.json.return_value = {"test": True}
                mock_response.raise_for_status = MagicMock()
                mock_get.return_value = mock_response

                result = await url_source.fetch(url="https://example.com/json")

                assert result == {"test": True}


# ============================================================================
# Test Class: Cache Integration
# ============================================================================


class TestCacheIntegration:
    """Tests for caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_hit(self, url_source_with_cache, mock_json_response):
        """Test cache hit returns cached data without new request."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_json_response

            # First fetch - cache miss
            result1 = await url_source_with_cache.fetch(
                url="https://example.com/data"
            )
            assert mock_get.call_count == 1

            # Second fetch - cache hit
            result2 = await url_source_with_cache.fetch(
                url="https://example.com/data"
            )
            assert mock_get.call_count == 1  # No new request
            assert result1 == result2

    @pytest.mark.asyncio
    async def test_cache_miss(self, url_source_with_cache, mock_json_response):
        """Test cache miss makes new request."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_json_response

            result = await url_source_with_cache.fetch(
                url="https://example.com/data"
            )

            assert result is not None
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_disabled(self, url_source_no_cache, mock_json_response):
        """Test disabled cache always makes new requests."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_json_response

            # First fetch
            await url_source_no_cache.fetch(url="https://example.com/data")
            assert mock_get.call_count == 1

            # Second fetch - should make new request (cache disabled)
            await url_source_no_cache.fetch(url="https://example.com/data")
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_different_urls(
        self, url_source_with_cache, mock_json_response, mock_text_response
    ):
        """Test different URLs don't share cache."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            # First URL returns JSON
            mock_get.return_value = mock_json_response
            result1 = await url_source_with_cache.fetch(
                url="https://example.com/data1"
            )

            # Second URL returns text
            mock_get.return_value = mock_text_response
            result2 = await url_source_with_cache.fetch(
                url="https://example.com/data2"
            )

            assert mock_get.call_count == 2
            assert result1 != result2


# ============================================================================
# Test Class: Cache Key Generation
# ============================================================================


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_cache_key_generation(self, url_source):
        """Test cache key is MD5 hash of URL."""
        url = "https://example.com/data"
        cache_key = url_source.get_cache_key(url=url)

        expected_key = hashlib.md5(url.encode()).hexdigest()
        assert cache_key == expected_key

    def test_cache_key_deterministic(self, url_source):
        """Test cache key is deterministic for same URL."""
        url = "https://example.com/data"
        key1 = url_source.get_cache_key(url=url)
        key2 = url_source.get_cache_key(url=url)

        assert key1 == key2

    def test_cache_key_different_urls(self, url_source):
        """Test different URLs generate different cache keys."""
        key1 = url_source.get_cache_key(url="https://example.com/data1")
        key2 = url_source.get_cache_key(url="https://example.com/data2")

        assert key1 != key2

    def test_cache_key_with_query_params(self, url_source):
        """Test cache keys differ for URLs with different query params."""
        key1 = url_source.get_cache_key(url="https://example.com/api?q=test1")
        key2 = url_source.get_cache_key(url="https://example.com/api?q=test2")

        assert key1 != key2


# ============================================================================
# Test Class: Configuration Validation
# ============================================================================


class TestConfigurationValidation:
    """Tests for validate_config method."""

    @pytest.mark.asyncio
    async def test_validate_config_always_true(self, url_source):
        """Test validate_config always returns True."""
        result = await url_source.validate_config()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_with_custom_timeout(self, url_source_custom):
        """Test validate_config returns True for custom configured instance."""
        result = await url_source_custom.validate_config()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_with_cache_disabled(self, url_source_no_cache):
        """Test validate_config returns True even with cache disabled."""
        result = await url_source_no_cache.validate_config()
        assert result is True
