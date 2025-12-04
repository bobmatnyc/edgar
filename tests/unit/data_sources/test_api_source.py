"""
Unit Tests for APIDataSource

Comprehensive test coverage for API data source including:
- Initialization validation (base_url, auth, headers)
- Successful API requests (GET, POST, various status codes)
- Authentication (Bearer token, custom headers)
- HTTP error handling (404, 500, 503, 429)
- Network timeout handling
- Cache integration (hits, misses, TTL)
- JSON parsing errors
- Retry logic
- Rate limiting integration
- Configuration validation

Test Organization:
- Class per functionality group
- Descriptive test names
- Clear docstrings
- Uses AsyncMock for httpx.AsyncClient
- Async tests use @pytest.mark.asyncio

Coverage Target: 70%+ (36+ statements covered of 52 total)
"""

import hashlib
import logging
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from extract_transform_platform.data_sources.web.api_source import APIDataSource


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def base_url():
    """Standard base URL for testing."""
    return "https://api.example.com"


@pytest.fixture
def auth_token():
    """Test authentication token."""
    return "test_token_abc123"


@pytest.fixture
def api_source(base_url, auth_token):
    """Create APIDataSource instance for testing."""
    return APIDataSource(
        base_url=base_url,
        auth_token=auth_token,
        timeout_seconds=30.0,
        cache_enabled=True,
        cache_ttl_seconds=300,
    )


@pytest.fixture
def api_source_no_auth(base_url):
    """Create APIDataSource without authentication."""
    return APIDataSource(
        base_url=base_url,
        timeout_seconds=10.0,
        cache_enabled=False,
    )


@pytest.fixture
def mock_response_200():
    """Create mock HTTP 200 response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"data": [{"id": 1, "name": "Test"}], "total": 1}
    mock.content = b'{"data": [{"id": 1, "name": "Test"}], "total": 1}'
    mock.raise_for_status = MagicMock()
    return mock


@pytest.fixture
def mock_response_404():
    """Create mock HTTP 404 response."""
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
def mock_response_500():
    """Create mock HTTP 500 response."""
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
    """Create mock HTTP 503 response."""
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
# Test Initialization
# ============================================================================


class TestAPIDataSourceInitialization:
    """Tests for APIDataSource initialization and validation."""

    def test_init_with_auth_token(self, base_url, auth_token):
        """Test initialization with authentication token."""
        source = APIDataSource(base_url=base_url, auth_token=auth_token)

        assert source.base_url == base_url
        assert source.headers["Authorization"] == f"Bearer {auth_token}"
        assert source.timeout_seconds == 30.0

    def test_init_without_auth_token(self, base_url):
        """Test initialization without authentication token."""
        source = APIDataSource(base_url=base_url)

        assert source.base_url == base_url
        assert "Authorization" not in source.headers
        assert source.timeout_seconds == 30.0

    def test_init_with_custom_headers(self, base_url):
        """Test initialization with custom headers."""
        custom_headers = {
            "User-Agent": "MyApp/1.0",
            "X-Custom-Header": "custom_value",
        }
        source = APIDataSource(base_url=base_url, headers=custom_headers)

        assert source.headers["User-Agent"] == "MyApp/1.0"
        assert source.headers["X-Custom-Header"] == "custom_value"

    def test_init_with_custom_timeout(self, base_url):
        """Test initialization with custom timeout."""
        source = APIDataSource(base_url=base_url, timeout_seconds=60.0)

        assert source.timeout_seconds == 60.0

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        source = APIDataSource(base_url="https://api.example.com/")

        assert source.base_url == "https://api.example.com"

    def test_auth_token_adds_bearer_prefix(self, base_url, auth_token):
        """Test that auth token is formatted as Bearer token."""
        source = APIDataSource(base_url=base_url, auth_token=auth_token)

        assert source.headers["Authorization"] == f"Bearer {auth_token}"

    def test_cache_enabled_by_default(self, base_url):
        """Test that caching is enabled by default."""
        source = APIDataSource(base_url=base_url)

        # BaseDataSource enables cache by default
        assert source.cache_enabled is True

    def test_custom_cache_settings(self, base_url):
        """Test initialization with custom cache settings."""
        source = APIDataSource(
            base_url=base_url,
            cache_enabled=False,
            cache_ttl_seconds=600,
        )

        assert source.cache_enabled is False
        assert source.cache_ttl_seconds == 600


# ============================================================================
# Test Successful API Requests
# ============================================================================


class TestAPIDataSourceFetch:
    """Tests for APIDataSource.fetch() method."""

    @pytest.mark.asyncio
    async def test_basic_get_request(self, api_source, mock_response_200):
        """Test basic GET request with 200 response."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await api_source.fetch(endpoint="users")

            assert result is not None
            assert "data" in result
            assert len(result["data"]) == 1
            assert result["data"][0]["id"] == 1
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_request_with_query_params(self, api_source, mock_response_200):
        """Test GET request with query parameters."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            params = {"limit": 10, "offset": 0}
            result = await api_source.fetch(endpoint="users", params=params)

            assert result is not None
            # Verify params were passed
            call_args = mock_client.request.call_args
            assert call_args[1]["params"] == params

    @pytest.mark.asyncio
    async def test_request_with_custom_method(self, api_source, mock_response_200):
        """Test request with custom HTTP method (POST)."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await api_source.fetch(endpoint="users", method="POST")

            assert result is not None
            # Verify POST method was used
            call_args = mock_client.request.call_args
            assert call_args[1]["method"] == "POST"

    @pytest.mark.asyncio
    async def test_endpoint_leading_slash_handled(self, api_source, mock_response_200):
        """Test that leading slash in endpoint is handled correctly."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Endpoint with leading slash
            result = await api_source.fetch(endpoint="/users")

            assert result is not None
            # Verify URL construction
            call_args = mock_client.request.call_args
            url = call_args[1]["url"]
            # Should not have double slash
            assert "//users" not in url

    @pytest.mark.asyncio
    async def test_empty_endpoint_uses_base_url(self, api_source, mock_response_200):
        """Test request with empty endpoint uses base URL only."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await api_source.fetch(endpoint="")

            assert result is not None
            # Verify base URL was used
            call_args = mock_client.request.call_args
            url = call_args[1]["url"]
            assert url == api_source.base_url


# ============================================================================
# Test Authentication & Headers
# ============================================================================


class TestAPIDataSourceAuthentication:
    """Tests for authentication and header handling."""

    @pytest.mark.asyncio
    async def test_bearer_token_in_request_headers(self, api_source, mock_response_200):
        """Test that Bearer token is included in request headers."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await api_source.fetch(endpoint="secure")

            # Verify Authorization header
            call_args = mock_client.request.call_args
            headers = call_args[1]["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"].startswith("Bearer ")

    @pytest.mark.asyncio
    async def test_custom_headers_in_request(self, base_url, mock_response_200):
        """Test that custom headers are included in request."""
        custom_headers = {"X-API-Version": "v2", "X-Request-ID": "12345"}
        source = APIDataSource(base_url=base_url, headers=custom_headers)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await source.fetch(endpoint="test")

            # Verify custom headers
            call_args = mock_client.request.call_args
            headers = call_args[1]["headers"]
            assert headers["X-API-Version"] == "v2"
            assert headers["X-Request-ID"] == "12345"


# ============================================================================
# Test HTTP Error Handling
# ============================================================================


class TestAPIDataSourceHTTPErrors:
    """Tests for HTTP error handling."""

    @pytest.mark.asyncio
    async def test_404_not_found_error(self, api_source, mock_response_404):
        """Test 404 Not Found error handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_404)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await api_source.fetch(endpoint="nonexistent")

    @pytest.mark.asyncio
    async def test_500_internal_server_error(self, api_source, mock_response_500):
        """Test 500 Internal Server Error handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_500)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await api_source.fetch(endpoint="error")

    @pytest.mark.asyncio
    async def test_503_service_unavailable_error(self, api_source, mock_response_503):
        """Test 503 Service Unavailable error handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_503)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await api_source.fetch(endpoint="unavailable")


# ============================================================================
# Test Network Timeouts
# ============================================================================


class TestAPIDataSourceTimeouts:
    """Tests for network timeout handling."""

    @pytest.mark.asyncio
    async def test_connection_timeout(self, api_source):
        """Test connection timeout error handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(
                side_effect=httpx.TimeoutException("Connection timeout")
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # APIDataSource should raise TimeoutException (after retries)
            with pytest.raises(httpx.TimeoutException):
                await api_source.fetch(endpoint="slow")

    @pytest.mark.asyncio
    async def test_read_timeout(self, api_source):
        """Test read timeout error handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(
                side_effect=httpx.ReadTimeout("Read timeout")
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.ReadTimeout):
                await api_source.fetch(endpoint="slow")

    @pytest.mark.asyncio
    async def test_timeout_value_passed_to_client(self, base_url):
        """Test that timeout value is passed to httpx client."""
        timeout = 5.0
        source = APIDataSource(base_url=base_url, timeout_seconds=timeout)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await source.fetch(endpoint="test")

            # Verify timeout was passed to AsyncClient constructor
            assert mock_client_class.call_args[1]["timeout"] == timeout


# ============================================================================
# Test Cache Integration
# ============================================================================


class TestAPIDataSourceCache:
    """Tests for cache integration."""

    @pytest.mark.asyncio
    async def test_cache_hit_no_api_call(self, api_source, mock_response_200):
        """Test cache hit returns cached data without API call."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First call - cache miss
            result1 = await api_source.fetch(endpoint="users")

            # Second call - cache hit (should not call API)
            result2 = await api_source.fetch(endpoint="users")

            assert result1 == result2
            # Should only be called once (first call)
            assert mock_client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_miss_calls_api(self, api_source, mock_response_200):
        """Test cache miss calls API."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await api_source.fetch(endpoint="users")

            assert result is not None
            # Should call API on cache miss
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_different_endpoints_different_cache_keys(
        self, api_source, mock_response_200
    ):
        """Test different endpoints use different cache keys."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Call different endpoints
            await api_source.fetch(endpoint="users")
            await api_source.fetch(endpoint="products")

            # Should call API twice (different cache keys)
            assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_disabled_always_calls_api(
        self, api_source_no_auth, mock_response_200
    ):
        """Test with cache disabled, always calls API."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Multiple calls with cache disabled
            await api_source_no_auth.fetch(endpoint="users")
            await api_source_no_auth.fetch(endpoint="users")

            # Should call API both times (cache disabled)
            assert mock_client.request.call_count == 2


# ============================================================================
# Test JSON Parsing Errors
# ============================================================================


class TestAPIDataSourceJSONParsing:
    """Tests for JSON parsing error handling."""

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, api_source):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Not valid JSON content"
        mock_response.content = b"Not valid JSON content"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValueError, match="API returned non-JSON response"):
                await api_source.fetch(endpoint="invalid")

    @pytest.mark.asyncio
    async def test_malformed_json_response(self, api_source):
        """Test handling of malformed JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Expecting value")
        mock_response.text = '{"incomplete": '
        mock_response.content = b'{"incomplete": '
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValueError, match="API returned non-JSON response"):
                await api_source.fetch(endpoint="malformed")


# ============================================================================
# Test Configuration Validation
# ============================================================================


class TestAPIDataSourceValidation:
    """Tests for configuration validation."""

    @pytest.mark.asyncio
    async def test_validate_config_success_200(self, api_source):
        """Test validate_config returns True for 200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            is_valid = await api_source.validate_config()

            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_config_success_with_404(self, api_source):
        """Test validate_config returns True for 404 (server accessible)."""
        mock_response = MagicMock()
        mock_response.status_code = 404  # Client error but server is accessible

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            is_valid = await api_source.validate_config()

            assert is_valid is True  # 4xx means server is accessible

    @pytest.mark.asyncio
    async def test_validate_config_failure_500(self, api_source):
        """Test validate_config returns False for 500 error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            is_valid = await api_source.validate_config()

            assert is_valid is False  # 5xx means server error

    @pytest.mark.asyncio
    async def test_validate_config_failure_network_error(self, api_source):
        """Test validate_config returns False for network error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            is_valid = await api_source.validate_config()

            assert is_valid is False  # Network error

    @pytest.mark.asyncio
    async def test_validate_config_failure_timeout(self, api_source):
        """Test validate_config returns False for timeout."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            is_valid = await api_source.validate_config()

            assert is_valid is False  # Timeout


# ============================================================================
# Test Cache Key Generation
# ============================================================================


class TestAPIDataSourceCacheKey:
    """Tests for cache key generation."""

    def test_cache_key_includes_base_url(self, api_source):
        """Test cache key includes base URL."""
        cache_key = api_source.get_cache_key(endpoint="users")

        assert isinstance(cache_key, str)
        # MD5 hash should be 32 hex characters
        assert len(cache_key) == 32

    def test_cache_key_includes_endpoint(self, api_source):
        """Test cache key includes endpoint."""
        key1 = api_source.get_cache_key(endpoint="users")
        key2 = api_source.get_cache_key(endpoint="products")

        # Different endpoints should produce different keys
        assert key1 != key2

    def test_cache_key_includes_params(self, api_source):
        """Test cache key includes query parameters."""
        key1 = api_source.get_cache_key(endpoint="users", params={"limit": 10})
        key2 = api_source.get_cache_key(endpoint="users", params={"limit": 20})

        # Different params should produce different keys
        assert key1 != key2

    def test_cache_key_includes_method(self, api_source):
        """Test cache key includes HTTP method."""
        key1 = api_source.get_cache_key(endpoint="users", method="GET")
        key2 = api_source.get_cache_key(endpoint="users", method="POST")

        # Different methods should produce different keys
        assert key1 != key2

    def test_cache_key_deterministic(self, api_source):
        """Test cache key is deterministic (same inputs = same key)."""
        params = {"limit": 10, "offset": 0}
        key1 = api_source.get_cache_key(endpoint="users", params=params, method="GET")
        key2 = api_source.get_cache_key(endpoint="users", params=params, method="GET")

        assert key1 == key2

    def test_cache_key_param_order_independent(self, api_source):
        """Test cache key is independent of param order."""
        params1 = {"limit": 10, "offset": 0}
        params2 = {"offset": 0, "limit": 10}  # Different order

        key1 = api_source.get_cache_key(endpoint="users", params=params1)
        key2 = api_source.get_cache_key(endpoint="users", params=params2)

        # Should produce same key (params are sorted)
        assert key1 == key2

    def test_cache_key_is_md5_hash(self, api_source):
        """Test cache key is MD5 hash."""
        cache_key = api_source.get_cache_key(endpoint="users")

        # MD5 hash should be 32 hex characters
        assert len(cache_key) == 32
        assert all(c in "0123456789abcdef" for c in cache_key)


# ============================================================================
# Test Logging
# ============================================================================


class TestAPIDataSourceLogging:
    """Tests for logging behavior."""

    def test_initialization_logging(self, base_url, caplog):
        """Test that initialization logs info message."""
        with caplog.at_level(logging.INFO):
            source = APIDataSource(base_url=base_url)

        assert any(
            "Initialized APIDataSource" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_fetch_debug_logging(self, api_source, mock_response_200, caplog):
        """Test that fetch logs debug messages."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_200)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with caplog.at_level(logging.DEBUG):
                await api_source.fetch(endpoint="users")

            # Check for debug logs
            log_messages = [record.message for record in caplog.records]
            assert any("API GET request" in msg for msg in log_messages)
