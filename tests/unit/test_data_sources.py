"""
Unit Tests for Data Source Abstraction Layer

Tests all data sources with mocked HTTP and file I/O:
- BaseDataSource: Caching, rate limiting, retry logic
- APIDataSource: REST API calls with auth
- JinaDataSource: Web content extraction
- FileDataSource: Local file reading
- URLDataSource: Simple HTTP fetching
- RateLimiter: Token bucket rate limiting
"""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from edgar_analyzer.data_sources import (
    APIDataSource,
    BaseDataSource,
    FileDataSource,
    IDataSource,
    JinaDataSource,
    URLDataSource,
)
from edgar_analyzer.utils.rate_limiter import RateLimiter

# ============================================================================
# Test RateLimiter
# ============================================================================


class TestRateLimiter:
    """Test rate limiter functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """Test that requests within limit are allowed immediately."""
        limiter = RateLimiter(requests_per_minute=60)

        # Should allow 60 requests without delay
        start = datetime.now()
        for _ in range(60):
            await limiter.acquire()
        elapsed = (datetime.now() - start).total_seconds()

        # Should complete almost instantly (<0.1s)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_when_limit_exceeded(self):
        """Test that requests are blocked when limit is exceeded."""
        limiter = RateLimiter(requests_per_minute=5)

        # Quickly make 5 requests
        for _ in range(5):
            await limiter.acquire()

        # 6th request should block
        start = datetime.now()
        await limiter.acquire()
        elapsed = (datetime.now() - start).total_seconds()

        # Should have waited (at least some delay)
        # Note: Test is time-sensitive, using generous threshold
        assert elapsed > 0.01  # At least 10ms delay

    @pytest.mark.asyncio
    async def test_rate_limiter_usage_tracking(self):
        """Test that rate limiter correctly tracks usage."""
        limiter = RateLimiter(requests_per_minute=10)

        assert limiter.get_current_usage() == 0

        await limiter.acquire()
        assert limiter.get_current_usage() == 1

        await limiter.acquire()
        await limiter.acquire()
        assert limiter.get_current_usage() == 3

    def test_rate_limiter_reset(self):
        """Test that reset clears all tracked requests."""
        limiter = RateLimiter(requests_per_minute=10)
        limiter.requests.extend([datetime.now()] * 5)

        assert limiter.get_current_usage() == 5

        limiter.reset()
        assert limiter.get_current_usage() == 0

    def test_rate_limiter_validates_positive_limit(self):
        """Test that rate limiter rejects invalid limits."""
        with pytest.raises(ValueError, match="must be positive"):
            RateLimiter(requests_per_minute=0)

        with pytest.raises(ValueError, match="must be positive"):
            RateLimiter(requests_per_minute=-1)


# ============================================================================
# Test BaseDataSource
# ============================================================================


class MockDataSource(BaseDataSource):
    """Concrete implementation of BaseDataSource for testing."""

    async def fetch(self, **kwargs) -> Dict[str, Any]:
        return {"data": "test"}

    async def validate_config(self) -> bool:
        return True

    def get_cache_key(self, **kwargs) -> str:
        return "test_key"


class TestBaseDataSource:
    """Test base data source functionality."""

    def test_initialization_with_defaults(self):
        """Test that base data source initializes with default settings."""
        source = MockDataSource()

        assert source.cache_enabled is True
        assert source.cache_ttl_seconds == 3600
        assert source.rate_limit_per_minute == 60
        assert source.max_retries == 3
        assert source.retry_backoff_factor == 2.0

    def test_initialization_with_custom_settings(self):
        """Test custom initialization settings."""
        source = MockDataSource(
            cache_enabled=False,
            cache_ttl_seconds=7200,
            rate_limit_per_minute=120,
            max_retries=5,
            retry_backoff_factor=3.0,
        )

        assert source.cache_enabled is False
        assert source.cache_ttl_seconds == 7200
        assert source.rate_limit_per_minute == 120
        assert source.max_retries == 5
        assert source.retry_backoff_factor == 3.0

    @pytest.mark.asyncio
    async def test_fetch_with_cache_hit(self):
        """Test that cached data is returned without calling fetch function."""
        source = MockDataSource(cache_enabled=True)

        fetch_fn = AsyncMock(return_value={"data": "fresh"})

        # First call - cache miss
        result1 = await source.fetch_with_cache("test_key", fetch_fn)
        assert result1 == {"data": "fresh"}
        assert fetch_fn.call_count == 1

        # Second call - cache hit
        result2 = await source.fetch_with_cache("test_key", fetch_fn)
        assert result2 == {"data": "fresh"}
        assert fetch_fn.call_count == 1  # Not called again

    @pytest.mark.asyncio
    async def test_fetch_with_cache_expiry(self):
        """Test that expired cache entries are refetched."""
        source = MockDataSource(cache_enabled=True, cache_ttl_seconds=1)

        fetch_fn = AsyncMock(return_value={"data": "fresh"})

        # First call
        await source.fetch_with_cache("test_key", fetch_fn)
        assert fetch_fn.call_count == 1

        # Wait for cache to expire
        await asyncio.sleep(1.1)

        # Second call - cache expired
        await source.fetch_with_cache("test_key", fetch_fn)
        assert fetch_fn.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_with_cache_disabled(self):
        """Test that fetch is always called when cache is disabled."""
        source = MockDataSource(cache_enabled=False)

        fetch_fn = AsyncMock(return_value={"data": "fresh"})

        # Multiple calls
        await source.fetch_with_cache("test_key", fetch_fn)
        await source.fetch_with_cache("test_key", fetch_fn)
        await source.fetch_with_cache("test_key", fetch_fn)

        # Each call should trigger fetch
        assert fetch_fn.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_logic_success_on_first_attempt(self):
        """Test successful fetch on first attempt."""
        source = MockDataSource(max_retries=3)

        fetch_fn = AsyncMock(return_value={"data": "success"})

        result = await source._retry_fetch(fetch_fn)

        assert result == {"data": "success"}
        assert fetch_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_logic_success_on_retry(self):
        """Test successful fetch after retries."""
        source = MockDataSource(max_retries=3, retry_backoff_factor=2.0)

        # Fail first 2 attempts, succeed on 3rd
        fetch_fn = AsyncMock(
            side_effect=[
                Exception("Network error"),
                Exception("Timeout"),
                {"data": "success"},
            ]
        )

        result = await source._retry_fetch(fetch_fn)

        assert result == {"data": "success"}
        assert fetch_fn.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_logic_all_attempts_fail(self):
        """Test that exception is raised after all retries exhausted."""
        source = MockDataSource(max_retries=2, retry_backoff_factor=2.0)

        fetch_fn = AsyncMock(side_effect=Exception("Persistent error"))

        with pytest.raises(Exception, match="Persistent error"):
            await source._retry_fetch(fetch_fn)

        # Should try: initial + 2 retries = 3 total
        assert fetch_fn.call_count == 3

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        source = MockDataSource(cache_enabled=True)

        # Add cache entries
        source._cache["key1"] = ({"data": "1"}, datetime.now())
        source._cache["key2"] = ({"data": "2"}, datetime.now())

        assert len(source._cache) == 2

        cleared = source.clear_cache()

        assert cleared == 2
        assert len(source._cache) == 0

    def test_get_cache_stats_empty(self):
        """Test cache stats for empty cache."""
        source = MockDataSource(cache_enabled=True)

        stats = source.get_cache_stats()

        assert stats["enabled"] is True
        assert stats["size"] == 0
        assert stats["ttl_seconds"] == 3600

    def test_get_cache_stats_with_data(self):
        """Test cache stats with cached data."""
        source = MockDataSource(cache_enabled=True, cache_ttl_seconds=7200)

        # Add cache entries with different ages
        now = datetime.now()
        source._cache["key1"] = ({"data": "1"}, now - timedelta(seconds=100))
        source._cache["key2"] = ({"data": "2"}, now - timedelta(seconds=50))
        source._cache["key3"] = ({"data": "3"}, now - timedelta(seconds=10))

        stats = source.get_cache_stats()

        assert stats["enabled"] is True
        assert stats["size"] == 3
        assert stats["ttl_seconds"] == 7200
        assert 90 < stats["oldest_age_seconds"] < 110  # ~100s
        assert 0 < stats["newest_age_seconds"] < 20  # ~10s


# ============================================================================
# Test APIDataSource
# ============================================================================


class TestAPIDataSource:
    """Test API data source functionality."""

    @pytest.mark.asyncio
    async def test_api_fetch_success(self):
        """Test successful API fetch."""
        api = APIDataSource(
            base_url="https://api.example.com",
            rate_limit_per_minute=9999,  # No rate limiting for tests
        )

        mock_response = Mock()
        mock_response.json.return_value = {"result": "success"}
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            result = await api.fetch(
                endpoint="users/123", params={"include": "profile"}
            )

            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_api_fetch_with_auth_token(self):
        """Test API fetch with bearer token authentication."""
        api = APIDataSource(
            base_url="https://api.example.com",
            auth_token="test_token_12345",
            rate_limit_per_minute=9999,
        )

        assert api.headers["Authorization"] == "Bearer test_token_12345"

    @pytest.mark.asyncio
    async def test_api_fetch_builds_correct_url(self):
        """Test that API URLs are built correctly."""
        api = APIDataSource(
            base_url="https://api.example.com",
            rate_limit_per_minute=9999,
        )

        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.status_code = 200
        mock_response.content = b"{}"
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_request = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.request = mock_request

            await api.fetch(endpoint="/users/123")

            # Verify URL construction
            call_args = mock_request.call_args
            assert call_args[1]["url"] == "https://api.example.com/users/123"

    @pytest.mark.asyncio
    async def test_api_validate_config_success(self):
        """Test successful API configuration validation."""
        api = APIDataSource(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            is_valid = await api.validate_config()

            assert is_valid is True

    @pytest.mark.asyncio
    async def test_api_validate_config_failure(self):
        """Test API validation failure on server error."""
        api = APIDataSource(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            is_valid = await api.validate_config()

            assert is_valid is False

    def test_api_get_cache_key_deterministic(self):
        """Test that cache keys are deterministic for same inputs."""
        api = APIDataSource(base_url="https://api.example.com")

        key1 = api.get_cache_key(endpoint="users", params={"id": 1, "name": "alice"})
        key2 = api.get_cache_key(endpoint="users", params={"name": "alice", "id": 1})

        # Same params in different order should produce same key
        assert key1 == key2

    def test_api_get_cache_key_different_params(self):
        """Test that different params produce different cache keys."""
        api = APIDataSource(base_url="https://api.example.com")

        key1 = api.get_cache_key(endpoint="users", params={"id": 1})
        key2 = api.get_cache_key(endpoint="users", params={"id": 2})

        assert key1 != key2


# ============================================================================
# Test JinaDataSource
# ============================================================================


class TestJinaDataSource:
    """Test Jina data source functionality."""

    def test_jina_initialization_free_tier(self):
        """Test Jina initialization without API key (free tier)."""
        jina = JinaDataSource()

        assert jina.rate_limit_per_minute == 20  # Free tier limit
        assert jina.api_key is None

    def test_jina_initialization_paid_tier(self):
        """Test Jina initialization with API key (paid tier)."""
        jina = JinaDataSource(api_key="jina_test_key_12345")

        assert jina.rate_limit_per_minute == 200  # Paid tier limit
        assert jina.api_key == "jina_test_key_12345"

    @pytest.mark.asyncio
    async def test_jina_fetch_markdown_response(self):
        """Test Jina fetch with markdown response."""
        jina = JinaDataSource(rate_limit_per_minute=9999)

        mock_response = Mock()
        mock_response.headers = {"content-type": "text/markdown"}
        mock_response.text = "# Example Page\n\nThis is example content."
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await jina.fetch("https://example.com")

            assert result["content"] == "# Example Page\n\nThis is example content."
            assert result["title"] == "Example Page"
            assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_jina_fetch_json_response(self):
        """Test Jina fetch with JSON response format."""
        jina = JinaDataSource(rate_limit_per_minute=9999)

        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "data": {
                "content": "# Test\n\nContent",
                "title": "Test Page",
                "metadata": {"author": "John"},
            }
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await jina.fetch("https://example.com")

            assert result["content"] == "# Test\n\nContent"
            assert result["title"] == "Test Page"
            assert result["metadata"] == {"author": "John"}

    @pytest.mark.asyncio
    async def test_jina_fetch_invalid_url(self):
        """Test Jina fetch with invalid URL."""
        jina = JinaDataSource()

        with pytest.raises(ValueError, match="Invalid URL"):
            await jina.fetch("not-a-url")

        with pytest.raises(ValueError, match="Invalid URL"):
            await jina.fetch("ftp://example.com")

    def test_jina_get_cache_key(self):
        """Test Jina cache key generation."""
        jina = JinaDataSource()

        key1 = jina.get_cache_key(url="https://example.com")
        key2 = jina.get_cache_key(url="https://example.com")
        key3 = jina.get_cache_key(url="https://different.com")

        # Same URL should produce same key
        assert key1 == key2

        # Different URL should produce different key
        assert key1 != key3


# ============================================================================
# Test FileDataSource
# ============================================================================


class TestFileDataSource:
    """Test file data source functionality."""

    def test_file_initialization_disables_cache(self):
        """Test that file source disables caching by default."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test": "data"}')
            file_path = Path(f.name)

        try:
            file_source = FileDataSource(file_path)

            assert file_source.cache_enabled is False
            assert file_source.max_retries == 0

        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_file_fetch_json(self):
        """Test fetching JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "Alice", "age": 30}, f)
            file_path = Path(f.name)

        try:
            file_source = FileDataSource(file_path)
            result = await file_source.fetch()

            assert result == {"name": "Alice", "age": 30}

        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_file_fetch_yaml(self):
        """Test fetching YAML file."""
        pytest.importorskip("yaml")  # Skip if PyYAML not installed

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("name: Bob\nage: 25\n")
            file_path = Path(f.name)

        try:
            file_source = FileDataSource(file_path)
            result = await file_source.fetch()

            assert result == {"name": "Bob", "age": 25}

        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_file_fetch_text(self):
        """Test fetching text file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!\nThis is a test.")
            file_path = Path(f.name)

        try:
            file_source = FileDataSource(file_path)
            result = await file_source.fetch()

            assert result["content"] == "Hello, World!\nThis is a test."
            assert result["file_name"] == file_path.name
            assert result["line_count"] == 2

        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_file_fetch_not_found(self):
        """Test fetching non-existent file."""
        file_source = FileDataSource(Path("/non/existent/file.json"))

        with pytest.raises(FileNotFoundError):
            await file_source.fetch()

    @pytest.mark.asyncio
    async def test_file_validate_config_exists(self):
        """Test file validation for existing file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            file_path = Path(f.name)

        try:
            file_source = FileDataSource(file_path)
            is_valid = await file_source.validate_config()

            assert is_valid is True

        finally:
            file_path.unlink()

    @pytest.mark.asyncio
    async def test_file_validate_config_not_found(self):
        """Test file validation for non-existent file."""
        file_source = FileDataSource(Path("/non/existent/file.json"))
        is_valid = await file_source.validate_config()

        assert is_valid is False


# ============================================================================
# Test URLDataSource
# ============================================================================


class TestURLDataSource:
    """Test URL data source functionality."""

    @pytest.mark.asyncio
    async def test_url_fetch_json(self):
        """Test fetching JSON from URL."""
        url_source = URLDataSource(rate_limit_per_minute=9999)

        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"status": "ok"}
        mock_response.status_code = 200
        mock_response.content = b'{"status": "ok"}'
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await url_source.fetch("https://api.example.com/status")

            assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_url_fetch_text(self):
        """Test fetching plain text from URL."""
        url_source = URLDataSource(rate_limit_per_minute=9999)

        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "Plain text content"
        mock_response.status_code = 200
        mock_response.content = b"Plain text content"
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await url_source.fetch("https://example.com/robots.txt")

            assert result["content"] == "Plain text content"
            assert result["url"] == "https://example.com/robots.txt"
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_url_fetch_invalid_url(self):
        """Test URL fetch with invalid URL."""
        url_source = URLDataSource()

        with pytest.raises(ValueError, match="Invalid URL"):
            await url_source.fetch("not-a-url")

        with pytest.raises(ValueError, match="Invalid URL"):
            await url_source.fetch("ftp://example.com")

    @pytest.mark.asyncio
    async def test_url_validate_config(self):
        """Test URL validation always returns True."""
        url_source = URLDataSource()

        is_valid = await url_source.validate_config()

        assert is_valid is True

    def test_url_get_cache_key(self):
        """Test URL cache key generation."""
        url_source = URLDataSource()

        key1 = url_source.get_cache_key(url="https://example.com")
        key2 = url_source.get_cache_key(url="https://example.com")
        key3 = url_source.get_cache_key(url="https://different.com")

        # Same URL should produce same key
        assert key1 == key2

        # Different URL should produce different key
        assert key1 != key3
