"""
Unit Tests for JinaDataSource

Comprehensive test coverage for Jina.ai data source including:
- Initialization validation (API key, base URL, rate limits)
- Successful Jina API requests (markdown and JSON responses)
- Authentication (Bearer token, free tier vs paid tier)
- Jina-specific headers and endpoint construction
- URL validation and encoding
- HTTP error handling (404, 401, 429, 500, 503)
- Network timeout handling
- Markdown content extraction and processing
- Cache integration (hits, misses, TTL)
- Configuration validation
- Cache key generation

Test Organization:
- Class per functionality group
- Descriptive test names
- Clear docstrings
- Uses AsyncMock for httpx.AsyncClient
- Async tests use @pytest.mark.asyncio

Coverage Target: 100% (62/62 statements - matching api_source and url_source achievement)
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from extract_transform_platform.data_sources.web.jina_source import JinaDataSource

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def api_key():
    """Test Jina API key."""
    return "test_jina_api_key_abc123"


@pytest.fixture
def jina_source(api_key):
    """Create JinaDataSource instance with API key (paid tier)."""
    return JinaDataSource(
        api_key=api_key,
        base_url="https://r.jina.ai",
        timeout_seconds=30.0,
        cache_enabled=True,
        cache_ttl_seconds=300,
    )


@pytest.fixture
def jina_source_free():
    """Create JinaDataSource without API key (free tier)."""
    # Ensure no API key from environment
    with patch.dict("os.environ", {}, clear=True):
        return JinaDataSource(
            timeout_seconds=10.0,
            cache_enabled=False,
        )


@pytest.fixture
def target_url():
    """Test target URL for extraction."""
    return "https://example.com/article"


@pytest.fixture
def mock_markdown_response():
    """Create mock Jina response with markdown content."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {"content-type": "text/markdown; charset=utf-8"}
    mock.text = """# Test Article Title

This is the main content extracted by Jina.ai.

## Section 1: Introduction
Some introduction text here.

## Section 2: Details
More detailed content.

### Subsection 2.1
Nested content.

## Conclusion
Final thoughts.
"""
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_json_response():
    """Create mock Jina response with JSON format."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {"content-type": "application/json"}
    mock.json.return_value = {
        "data": {
            "content": "# JSON Format Content\n\nThis is content from JSON response.",
            "title": "JSON Format Title",
            "metadata": {
                "description": "Test description",
                "images": ["https://example.com/image.jpg"],
            },
        }
    }
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_empty_markdown_response():
    """Create mock Jina response with empty markdown."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {"content-type": "text/markdown"}
    mock.text = ""
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_markdown_no_title():
    """Create mock Jina response with markdown but no title."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {"content-type": "text/markdown"}
    mock.text = """This is content without any title.

Just some paragraphs here.

More content follows.
"""
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_response_404():
    """Create mock HTTP 404 response (target URL not found)."""
    mock = MagicMock()
    mock.status_code = 404
    mock.text = "Not Found"
    mock.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            message="Not Found",
            request=MagicMock(),
            response=mock,
        )
    )
    return mock


@pytest.fixture
def mock_response_401():
    """Create mock HTTP 401 response (invalid API key)."""
    mock = MagicMock()
    mock.status_code = 401
    mock.text = "Unauthorized"
    mock.json.return_value = {
        "error": "Unauthorized",
        "message": "Invalid API key",
    }
    mock.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            message="Unauthorized",
            request=MagicMock(),
            response=mock,
        )
    )
    return mock


@pytest.fixture
def mock_response_429():
    """Create mock HTTP 429 response (rate limit exceeded)."""
    mock = MagicMock()
    mock.status_code = 429
    mock.text = "Too Many Requests"
    mock.json.return_value = {
        "error": "Rate limit exceeded",
        "message": "Please slow down your requests",
    }
    mock.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            message="Too Many Requests",
            request=MagicMock(),
            response=mock,
        )
    )
    return mock


@pytest.fixture
def mock_response_500():
    """Create mock HTTP 500 response (Jina API error)."""
    mock = MagicMock()
    mock.status_code = 500
    mock.text = "Internal Server Error"
    mock.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            message="Internal Server Error",
            request=MagicMock(),
            response=mock,
        )
    )
    return mock


@pytest.fixture
def mock_response_503():
    """Create mock HTTP 503 response (service unavailable)."""
    mock = MagicMock()
    mock.status_code = 503
    mock.text = "Service Unavailable"
    mock.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            message="Service Unavailable",
            request=MagicMock(),
            response=mock,
        )
    )
    return mock


# ============================================================================
# Initialization Tests
# ============================================================================


class TestJinaDataSourceInitialization:
    """Tests for JinaDataSource initialization."""

    def test_initialization_with_api_key(self, api_key):
        """Test initialization with API key (paid tier)."""
        jina = JinaDataSource(api_key=api_key)

        assert jina.api_key == api_key
        assert jina.base_url == "https://r.jina.ai"
        assert jina.timeout_seconds == 30.0
        # Paid tier gets 200 req/min
        assert jina.rate_limit_per_minute == 200

    def test_initialization_without_api_key(self):
        """Test initialization without API key (free tier)."""
        # Ensure no API key from environment
        with patch.dict("os.environ", {}, clear=True):
            jina = JinaDataSource()

            assert jina.api_key is None
            assert jina.base_url == "https://r.jina.ai"
            assert jina.timeout_seconds == 30.0
            # Free tier gets 20 req/min
            assert jina.rate_limit_per_minute == 20

    def test_initialization_with_env_api_key(self):
        """Test initialization with API key from environment."""
        with patch.dict("os.environ", {"JINA_API_KEY": "env_api_key_xyz"}):
            jina = JinaDataSource()

            assert jina.api_key == "env_api_key_xyz"
            assert jina.rate_limit_per_minute == 200  # Paid tier

    def test_initialization_with_custom_base_url(self, api_key):
        """Test initialization with custom base URL."""
        custom_url = "https://custom.jina.ai"
        jina = JinaDataSource(api_key=api_key, base_url=custom_url)

        assert jina.base_url == custom_url

    def test_initialization_with_trailing_slash_base_url(self, api_key):
        """Test base URL trailing slash is removed."""
        jina = JinaDataSource(api_key=api_key, base_url="https://r.jina.ai/")

        assert jina.base_url == "https://r.jina.ai"

    def test_initialization_with_custom_timeout(self, api_key):
        """Test initialization with custom timeout."""
        jina = JinaDataSource(api_key=api_key, timeout_seconds=60.0)

        assert jina.timeout_seconds == 60.0

    def test_initialization_with_custom_rate_limit(self, api_key):
        """Test initialization with explicit rate limit override."""
        jina = JinaDataSource(api_key=api_key, rate_limit_per_minute=100)

        assert jina.rate_limit_per_minute == 100

    def test_initialization_with_cache_ttl(self, api_key):
        """Test initialization with custom cache TTL."""
        jina = JinaDataSource(api_key=api_key, cache_ttl_seconds=1800)

        assert jina.cache_ttl_seconds == 1800

    def test_default_cache_ttl_is_one_hour(self, api_key):
        """Test default cache TTL is 1 hour (3600 seconds)."""
        jina = JinaDataSource(api_key=api_key)

        assert jina.cache_ttl_seconds == 3600


# ============================================================================
# Successful Fetch Tests
# ============================================================================


class TestSuccessfulJinaFetches:
    """Tests for successful Jina API content extraction."""

    @pytest.mark.asyncio
    async def test_fetch_markdown_response(
        self, jina_source, target_url, mock_markdown_response
    ):
        """Test successful fetch with markdown response."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            result = await jina_source.fetch(url=target_url)

            assert result is not None
            assert "content" in result
            assert "title" in result
            assert "url" in result
            assert "extracted_at" in result
            assert "metadata" in result

            # Verify content extraction
            assert "Test Article Title" in result["content"]
            assert "Section 1: Introduction" in result["content"]

            # Verify title extraction from first heading
            assert result["title"] == "Test Article Title"

            # Verify URL preserved
            assert result["url"] == target_url

            # Verify metadata
            assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_fetch_json_response(
        self, jina_source, target_url, mock_json_response
    ):
        """Test successful fetch with JSON response format."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_json_response

            result = await jina_source.fetch(url=target_url)

            assert result is not None
            assert (
                result["content"]
                == "# JSON Format Content\n\nThis is content from JSON response."
            )
            assert result["title"] == "JSON Format Title"
            assert result["url"] == target_url
            assert result["metadata"]["description"] == "Test description"
            assert "image.jpg" in result["metadata"]["images"][0]

    @pytest.mark.asyncio
    async def test_fetch_markdown_without_title(
        self, jina_source, target_url, mock_markdown_no_title
    ):
        """Test fetch with markdown that has no title heading."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_no_title

            result = await jina_source.fetch(url=target_url)

            assert result is not None
            assert result["title"] == ""  # No title found
            assert "Just some paragraphs here" in result["content"]

    @pytest.mark.asyncio
    async def test_fetch_empty_content(
        self, jina_source, target_url, mock_empty_markdown_response
    ):
        """Test fetch with empty markdown response."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_empty_markdown_response

            result = await jina_source.fetch(url=target_url)

            assert result is not None
            assert result["content"] == ""
            assert result["title"] == ""

    @pytest.mark.asyncio
    async def test_jina_endpoint_construction(
        self, jina_source, target_url, mock_markdown_response
    ):
        """Test Jina API endpoint is constructed correctly."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            await jina_source.fetch(url=target_url)

            # Verify Jina endpoint called
            call_args = mock_get.call_args
            called_url = call_args[0][0]
            assert called_url == f"https://r.jina.ai/{target_url}"

    @pytest.mark.asyncio
    async def test_extracted_at_timestamp_format(
        self, jina_source, target_url, mock_markdown_response
    ):
        """Test extracted_at timestamp is ISO format."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            result = await jina_source.fetch(url=target_url)

            # Should be ISO format datetime
            timestamp = result["extracted_at"]
            assert "T" in timestamp  # ISO format includes T separator
            # Should be parseable
            datetime.fromisoformat(timestamp)


# ============================================================================
# Authentication Tests
# ============================================================================


class TestJinaAuthentication:
    """Tests for Jina API authentication."""

    @pytest.mark.asyncio
    async def test_fetch_with_api_key_header(
        self, jina_source, target_url, mock_markdown_response
    ):
        """Test fetch includes Bearer token in Authorization header."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            await jina_source.fetch(url=target_url)

            # Verify Authorization header
            call_args = mock_get.call_args
            headers = call_args[1]["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer test_jina_api_key_abc123"

    @pytest.mark.asyncio
    async def test_fetch_without_api_key_no_auth_header(
        self, jina_source_free, target_url, mock_markdown_response
    ):
        """Test fetch without API key has no Authorization header."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            await jina_source_free.fetch(url=target_url)

            # Verify no Authorization header
            call_args = mock_get.call_args
            headers = call_args[1].get("headers", {})
            assert "Authorization" not in headers

    @pytest.mark.asyncio
    async def test_invalid_api_key_401_error(
        self, jina_source, target_url, mock_response_401
    ):
        """Test 401 Unauthorized with invalid API key."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_401

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await jina_source.fetch(url=target_url)

            assert exc_info.value.response.status_code == 401


# ============================================================================
# URL Validation Tests
# ============================================================================


class TestURLValidation:
    """Tests for target URL validation."""

    @pytest.mark.asyncio
    async def test_invalid_url_missing_protocol(self, jina_source):
        """Test fetch rejects URL without protocol."""
        with pytest.raises(ValueError, match="Invalid URL.*must start with http"):
            await jina_source.fetch(url="example.com/article")

    @pytest.mark.asyncio
    async def test_invalid_url_wrong_protocol(self, jina_source):
        """Test fetch rejects URL with wrong protocol."""
        with pytest.raises(ValueError, match="Invalid URL.*must start with http"):
            await jina_source.fetch(url="ftp://example.com/file")

    @pytest.mark.asyncio
    async def test_valid_http_url(self, jina_source, mock_markdown_response):
        """Test fetch accepts http:// URL."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            result = await jina_source.fetch(url="http://example.com")

            assert result is not None

    @pytest.mark.asyncio
    async def test_valid_https_url(self, jina_source, mock_markdown_response):
        """Test fetch accepts https:// URL."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            result = await jina_source.fetch(url="https://example.com")

            assert result is not None

    @pytest.mark.asyncio
    async def test_url_with_query_parameters(self, jina_source, mock_markdown_response):
        """Test fetch handles URL with query parameters."""
        url = "https://example.com/search?q=test&page=1"

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            result = await jina_source.fetch(url=url)

            assert result is not None
            # Verify full URL passed to Jina
            called_url = mock_get.call_args[0][0]
            assert url in called_url

    @pytest.mark.asyncio
    async def test_url_with_fragment(self, jina_source, mock_markdown_response):
        """Test fetch handles URL with fragment identifier."""
        url = "https://example.com/page#section-2"

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            result = await jina_source.fetch(url=url)

            assert result is not None


# ============================================================================
# HTTP Error Handling Tests
# ============================================================================


class TestHTTPErrorHandling:
    """Tests for HTTP error responses."""

    @pytest.mark.asyncio
    async def test_404_target_not_found(
        self, jina_source, target_url, mock_response_404
    ):
        """Test 404 Not Found (target URL invalid)."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_404

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await jina_source.fetch(url=target_url)

            assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    async def test_429_rate_limit_exceeded(
        self, jina_source, target_url, mock_response_429
    ):
        """Test 429 Too Many Requests (rate limit exceeded)."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_429

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await jina_source.fetch(url=target_url)

            assert exc_info.value.response.status_code == 429

    @pytest.mark.asyncio
    async def test_500_jina_api_error(self, jina_source, target_url, mock_response_500):
        """Test 500 Internal Server Error (Jina API failure)."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_500

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await jina_source.fetch(url=target_url)

            assert exc_info.value.response.status_code == 500

    @pytest.mark.asyncio
    async def test_503_service_unavailable(
        self, jina_source, target_url, mock_response_503
    ):
        """Test 503 Service Unavailable (Jina down)."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_503

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await jina_source.fetch(url=target_url)

            assert exc_info.value.response.status_code == 503


# ============================================================================
# Network Error Tests
# ============================================================================


class TestNetworkErrors:
    """Tests for network-level errors."""

    @pytest.mark.asyncio
    async def test_connection_timeout(self, jina_source, target_url):
        """Test connection timeout error."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectTimeout("Connection timeout")

            with pytest.raises(httpx.ConnectTimeout):
                await jina_source.fetch(url=target_url)

    @pytest.mark.asyncio
    async def test_read_timeout(self, jina_source, target_url):
        """Test read timeout error."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ReadTimeout("Read timeout")

            with pytest.raises(httpx.ReadTimeout):
                await jina_source.fetch(url=target_url)

    @pytest.mark.asyncio
    async def test_connection_error(self, jina_source, target_url):
        """Test connection error."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(httpx.ConnectError):
                await jina_source.fetch(url=target_url)

    @pytest.mark.asyncio
    async def test_network_error(self, jina_source, target_url):
        """Test generic network error."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.NetworkError("Network error")

            with pytest.raises(httpx.NetworkError):
                await jina_source.fetch(url=target_url)


# ============================================================================
# Cache Integration Tests
# ============================================================================


class TestCacheIntegration:
    """Tests for caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_content(
        self, jina_source, target_url, mock_markdown_response
    ):
        """Test cache hit returns cached content without API call."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            # First call - cache miss
            result1 = await jina_source.fetch(url=target_url)

            # Second call - cache hit
            result2 = await jina_source.fetch(url=target_url)

            # Results should be identical
            assert result1 == result2

            # API should only be called once
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_miss_calls_api(self, jina_source, mock_markdown_response):
        """Test cache miss for different URLs calls API."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            # Different URLs
            await jina_source.fetch(url="https://example.com/page1")
            await jina_source.fetch(url="https://example.com/page2")

            # API should be called twice (different cache keys)
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_disabled_always_calls_api(
        self, jina_source_free, target_url, mock_markdown_response
    ):
        """Test with cache disabled, API is called every time."""
        # jina_source_free has cache_enabled=False
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            # Multiple calls to same URL
            await jina_source_free.fetch(url=target_url)
            await jina_source_free.fetch(url=target_url)

            # API should be called twice (no caching)
            assert mock_get.call_count == 2


# ============================================================================
# Cache Key Generation Tests
# ============================================================================


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_cache_key_generation(self, jina_source, target_url):
        """Test cache key is MD5 hash of URL."""
        cache_key = jina_source.get_cache_key(url=target_url)

        expected_key = hashlib.md5(target_url.encode()).hexdigest()
        assert cache_key == expected_key

    def test_cache_key_is_consistent(self, jina_source, target_url):
        """Test cache key is consistent for same URL."""
        key1 = jina_source.get_cache_key(url=target_url)
        key2 = jina_source.get_cache_key(url=target_url)

        assert key1 == key2

    def test_cache_key_different_for_different_urls(self, jina_source):
        """Test different URLs produce different cache keys."""
        key1 = jina_source.get_cache_key(url="https://example.com/page1")
        key2 = jina_source.get_cache_key(url="https://example.com/page2")

        assert key1 != key2

    def test_cache_key_is_32_chars(self, jina_source, target_url):
        """Test cache key is 32 characters (MD5 hex digest)."""
        cache_key = jina_source.get_cache_key(url=target_url)

        assert len(cache_key) == 32

    def test_cache_key_ignores_kwargs(self, jina_source, target_url):
        """Test cache key generation ignores extra kwargs."""
        key1 = jina_source.get_cache_key(url=target_url)
        key2 = jina_source.get_cache_key(url=target_url, extra="ignored")

        assert key1 == key2


# ============================================================================
# Configuration Validation Tests
# ============================================================================


class TestConfigurationValidation:
    """Tests for configuration validation."""

    @pytest.mark.asyncio
    async def test_validate_config_success(self, jina_source, mock_markdown_response):
        """Test validate_config succeeds with valid configuration."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_markdown_response

            is_valid = await jina_source.validate_config()

            assert is_valid is True

            # Verify example.com was used for validation
            called_url = mock_get.call_args[0][0]
            assert "example.com" in called_url

    @pytest.mark.asyncio
    async def test_validate_config_failure_no_content(
        self, jina_source, mock_empty_markdown_response
    ):
        """Test validate_config fails when response has no content."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_empty_markdown_response

            is_valid = await jina_source.validate_config()

            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_failure_network_error(self, jina_source):
        """Test validate_config fails on network error."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.NetworkError("Network error")

            is_valid = await jina_source.validate_config()

            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_failure_401_error(
        self, jina_source, mock_response_401
    ):
        """Test validate_config fails on 401 Unauthorized."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response_401

            is_valid = await jina_source.validate_config()

            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_config_failure_timeout(self, jina_source):
        """Test validate_config fails on timeout."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ReadTimeout("Timeout")

            is_valid = await jina_source.validate_config()

            assert is_valid is False


# ============================================================================
# Markdown Processing Tests
# ============================================================================


class TestMarkdownProcessing:
    """Tests for markdown content processing."""

    @pytest.mark.asyncio
    async def test_title_extraction_from_h1(self, jina_source, target_url):
        """Test title is extracted from first H1 heading."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/markdown"}
        mock_response.text = "# Main Title\n\nContent here.\n\n## Section"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await jina_source.fetch(url=target_url)

            assert result["title"] == "Main Title"

    @pytest.mark.asyncio
    async def test_title_extraction_skips_h2(self, jina_source, target_url):
        """Test title extraction skips H2 if no H1 present."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/markdown"}
        mock_response.text = "## Section Title\n\nContent here."
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await jina_source.fetch(url=target_url)

            # Should not extract from H2
            assert result["title"] == ""

    @pytest.mark.asyncio
    async def test_title_strips_hash_and_whitespace(self, jina_source, target_url):
        """Test title extraction removes # and whitespace."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/markdown"}
        mock_response.text = "#   Title With Spaces   \n\nContent."
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await jina_source.fetch(url=target_url)

            assert result["title"] == "Title With Spaces"

    @pytest.mark.asyncio
    async def test_large_markdown_content(self, jina_source, target_url):
        """Test handling of large markdown response."""
        # Generate large content
        large_content = "# Large Document\n\n" + "\n\n".join(
            [f"## Section {i}\n\nContent for section {i}." for i in range(100)]
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/markdown"}
        mock_response.text = large_content
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await jina_source.fetch(url=target_url)

            assert len(result["content"]) > 1000
            assert "Section 99" in result["content"]


# ============================================================================
# Timeout Configuration Tests
# ============================================================================


class TestTimeoutConfiguration:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_timeout_passed_to_client(
        self, jina_source, target_url, mock_markdown_response
    ):
        """Test timeout is passed to httpx client."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_markdown_response)
            mock_client_class.return_value = mock_client

            await jina_source.fetch(url=target_url)

            # Verify timeout passed to AsyncClient
            mock_client_class.assert_called_once_with(timeout=30.0)
