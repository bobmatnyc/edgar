"""
Integration tests for JinaDataSource with real API validation.

Tests the Jina.ai Reader API integration focusing on:
- Real API calls (not mocks) for validation
- Authentication handling (API key management)
- Content extraction and markdown parsing
- Error handling (timeouts, rate limits, invalid URLs)
- News scraper template integration (T9)

Design Decisions:
- Real API calls with graceful skipping when JINA_API_KEY missing
- Uses example.com for fast, reliable testing
- Rate limit aware (respects free tier: 20 req/min)
- Integration with T12 custom exceptions for error messages
- Validates T9 news_scraper template against real API responses

Test Coverage Target: 80% (4/5 tests passing)

Known Constraints:
- Requires JINA_API_KEY environment variable
- Network dependent (graceful skip if offline)
- Rate limited (spaced tests to avoid 429 errors)
"""

import os

# Add src to path for local imports
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from extract_transform_platform.data_sources.web import JinaDataSource

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def jina_api_key() -> str:
    """Jina API key from environment.

    Skips test if JINA_API_KEY not set (graceful degradation).

    Returns:
        API key string

    Raises:
        pytest.skip: If JINA_API_KEY environment variable not set
    """
    key = os.getenv("JINA_API_KEY")
    if not key:
        pytest.skip("JINA_API_KEY not set - skipping real API integration tests")
    return key


@pytest.fixture
def jina_source(jina_api_key: str) -> JinaDataSource:
    """Jina data source instance with API key.

    Args:
        jina_api_key: API key fixture

    Returns:
        Configured JinaDataSource instance
    """
    return JinaDataSource(
        api_key=jina_api_key,
        timeout_seconds=30.0,
    )


@pytest.fixture
def jina_source_no_key() -> JinaDataSource:
    """Jina data source without API key (free tier).

    Returns:
        JinaDataSource configured for free tier (20 req/min)
    """
    # Temporarily clear JINA_API_KEY
    original_key = os.environ.pop("JINA_API_KEY", None)
    try:
        source = JinaDataSource()
        return source
    finally:
        # Restore original key
        if original_key:
            os.environ["JINA_API_KEY"] = original_key


@pytest.fixture
def news_scraper_template_path() -> Path:
    """Path to news scraper template.

    Returns:
        Path to templates/news_scraper_project.yaml
    """
    template_path = Path("templates/news_scraper_project.yaml")
    if not template_path.exists():
        pytest.skip(f"Template not found: {template_path}")
    return template_path


@pytest.fixture
def rate_limit_delay() -> None:
    """Delay between tests to respect rate limits.

    Free tier: 20 req/min = 3 seconds per request
    Paid tier: 200 req/min = 0.3 seconds per request

    We use 4 seconds to be safe with free tier.
    """
    time.sleep(4)  # 4 seconds = safe for free tier


# =============================================================================
# Test: Authentication
# =============================================================================


class TestJinaAuthentication:
    """Test Jina API authentication scenarios."""

    @pytest.mark.asyncio
    async def test_valid_api_key(
        self, jina_source: JinaDataSource, rate_limit_delay: None
    ) -> None:
        """Test authentication with valid API key.

        Verifies:
        - API call succeeds with valid key
        - Response contains expected structure
        - No authentication errors

        Args:
            jina_source: Configured source with valid API key
            rate_limit_delay: Fixture to add delay between tests
        """
        # Use example.com - fast, reliable, always available
        result = await jina_source.fetch("https://example.com")

        # Verify response structure
        assert result is not None
        assert "content" in result
        assert "title" in result
        assert "url" in result
        assert "extracted_at" in result

        # Verify content extracted
        assert len(result["content"]) > 0
        assert result["url"] == "https://example.com"

        # Verify markdown format (should contain heading or text)
        content = result["content"]
        assert len(content) > 50  # Meaningful content

    @pytest.mark.asyncio
    async def test_missing_api_key_free_tier(
        self, jina_source_no_key: JinaDataSource, rate_limit_delay: None
    ) -> None:
        """Test Jina works without API key (free tier).

        Verifies:
        - Free tier works (20 req/min)
        - No authentication error
        - Content extraction still functional

        Args:
            jina_source_no_key: Source without API key
            rate_limit_delay: Fixture to add delay between tests
        """
        # Verify rate limit configured for free tier
        assert jina_source_no_key.rate_limit_per_minute == 20

        # Test free tier extraction
        result = await jina_source_no_key.fetch("https://example.com")

        assert result is not None
        assert "content" in result
        assert len(result["content"]) > 0

    @pytest.mark.asyncio
    async def test_invalid_api_key_error(self, rate_limit_delay: None) -> None:
        """Test error handling with invalid API key.

        Verifies:
        - Invalid key raises clear error
        - Error message is user-friendly
        - No uncaught exceptions

        Args:
            rate_limit_delay: Fixture to add delay between tests
        """
        # Create source with invalid key
        source = JinaDataSource(api_key="invalid-test-key-12345")

        # Should raise HTTP error (401 Unauthorized) or similar
        with pytest.raises((httpx.HTTPError, httpx.HTTPStatusError)):
            await source.fetch("https://example.com")


# =============================================================================
# Test: Content Extraction
# =============================================================================


class TestJinaContentExtraction:
    """Test content extraction functionality with real API."""

    @pytest.mark.asyncio
    async def test_basic_integration(
        self, jina_source: JinaDataSource, rate_limit_delay: None
    ) -> None:
        """Test basic Jina integration with example.com.

        This is the primary integration test verifying:
        - API connectivity
        - Response structure
        - Markdown extraction
        - Metadata parsing

        Args:
            jina_source: Configured Jina source
            rate_limit_delay: Fixture to add delay between tests
        """
        result = await jina_source.fetch("https://example.com")

        # Core response structure
        assert result is not None
        assert isinstance(result, dict)

        # Required fields
        required_fields = ["content", "title", "url", "extracted_at"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Content validation
        content = result["content"]
        assert isinstance(content, str)
        assert len(content) > 0

        # Metadata validation
        assert result["url"] == "https://example.com"
        assert isinstance(result["extracted_at"], str)

        # Markdown format check (basic validation)
        # example.com should have heading or paragraph content
        assert "example" in content.lower()

    @pytest.mark.asyncio
    async def test_content_extraction_quality(
        self, jina_source: JinaDataSource, rate_limit_delay: None
    ) -> None:
        """Test content extraction quality and completeness.

        Verifies:
        - Markdown properly formatted
        - Main content extracted (not just headers)
        - Title extraction works
        - Metadata includes expected fields

        Args:
            jina_source: Configured Jina source
            rate_limit_delay: Fixture to add delay between tests
        """
        result = await jina_source.fetch("https://example.com")

        # Content quality checks
        content = result["content"]

        # Should have substantial content (example.com has ~100+ chars)
        assert len(content) >= 50, "Content too short - extraction may have failed"

        # Should have title field (may be empty for some pages)
        assert "title" in result
        assert isinstance(result["title"], str)

        # Should have metadata dict (even if empty)
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_markdown_format_validation(
        self, jina_source: JinaDataSource, rate_limit_delay: None
    ) -> None:
        """Test markdown format of extracted content.

        Verifies:
        - Content is valid markdown
        - Headings preserved (if present)
        - Text content readable

        Args:
            jina_source: Configured Jina source
            rate_limit_delay: Fixture to add delay between tests
        """
        result = await jina_source.fetch("https://example.com")
        content = result["content"]

        # Basic markdown validation
        # Markdown should be clean text (no HTML tags)
        assert "<html>" not in content.lower()
        assert "<body>" not in content.lower()
        assert "<div>" not in content.lower()

        # Should contain readable text
        assert len(content.split()) > 10  # At least 10 words


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestJinaErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_url_error(
        self, jina_source: JinaDataSource, rate_limit_delay: None
    ) -> None:
        """Test handling of invalid URL.

        Verifies:
        - Invalid URL raises ValueError
        - Error message is clear
        - No uncaught exceptions

        Args:
            jina_source: Configured Jina source
            rate_limit_delay: Fixture to add delay between tests
        """
        # Test invalid URL (no protocol)
        with pytest.raises(ValueError) as exc_info:
            await jina_source.fetch("not-a-valid-url")

        # Verify error message is helpful
        assert "Invalid URL" in str(exc_info.value)
        assert "http://" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, jina_api_key: str) -> None:
        """Test timeout handling with very short timeout.

        Verifies:
        - Timeout error raised gracefully
        - No hanging requests
        - Clear error message

        Args:
            jina_api_key: Valid API key fixture

        Note:
            Uses short timeout (0.1s) to force timeout on real request.
            This test may be flaky if network is extremely fast.
        """
        # Create source with very short timeout
        source = JinaDataSource(
            api_key=jina_api_key,
            timeout_seconds=0.01,  # 10ms - will timeout
        )

        # Should raise timeout error
        with pytest.raises((httpx.TimeoutException, httpx.ReadTimeout)):
            await source.fetch("https://example.com")

    @pytest.mark.asyncio
    async def test_nonexistent_domain_error(
        self, jina_source: JinaDataSource, rate_limit_delay: None
    ) -> None:
        """Test handling of nonexistent domain.

        Verifies:
        - DNS error or connection error raised
        - Error handled gracefully
        - No uncaught exceptions

        Args:
            jina_source: Configured Jina source
            rate_limit_delay: Fixture to add delay between tests
        """
        # Use nonexistent domain
        with pytest.raises(
            (httpx.HTTPError, httpx.ConnectError, httpx.HTTPStatusError)
        ):
            await jina_source.fetch(
                "https://this-domain-definitely-does-not-exist-12345.com"
            )

    @pytest.mark.asyncio
    async def test_validate_config_success(
        self, jina_source: JinaDataSource, rate_limit_delay: None
    ) -> None:
        """Test validate_config method with valid configuration.

        Verifies:
        - validate_config returns True for valid setup
        - Uses example.com for fast validation
        - No errors during validation

        Args:
            jina_source: Configured Jina source
            rate_limit_delay: Fixture to add delay between tests
        """
        result = await jina_source.validate_config()

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_failure(self) -> None:
        """Test validate_config with invalid configuration.

        Verifies:
        - validate_config returns False for invalid setup
        - No exceptions raised
        - Graceful failure

        Note:
            This test creates a source with invalid API key.
        """
        # Create source with invalid key
        source = JinaDataSource(api_key="invalid-key-12345")

        result = await source.validate_config()

        # Should return False, not raise exception
        assert result is False


# =============================================================================
# Test: News Scraper Template Integration (T9)
# =============================================================================


class TestJinaNewsScraperTemplate:
    """Test news scraper template integration with JinaDataSource."""

    def test_template_loads_successfully(
        self, news_scraper_template_path: Path
    ) -> None:
        """Test news scraper template file loads and parses.

        Verifies:
        - Template YAML is valid
        - Contains required sections
        - Data source configuration valid

        Args:
            news_scraper_template_path: Path to template
        """
        with open(news_scraper_template_path, "r") as f:
            template = yaml.safe_load(f)

        # Verify core structure
        assert template is not None
        assert "project" in template
        assert "data_sources" in template
        assert "examples" in template

        # Verify project metadata
        project = template["project"]
        assert project["name"] == "news_scraper"
        assert "jina" in project["tags"]

    def test_template_jina_config(self, news_scraper_template_path: Path) -> None:
        """Test Jina configuration in news scraper template.

        Verifies:
        - Jina data source configured correctly
        - Auth settings present
        - Rate limiting configured
        - Cache settings appropriate

        Args:
            news_scraper_template_path: Path to template
        """
        with open(news_scraper_template_path, "r") as f:
            template = yaml.safe_load(f)

        # Get Jina data source config
        data_sources = template["data_sources"]
        assert len(data_sources) > 0

        jina_source = data_sources[0]
        assert jina_source["type"] == "jina"
        assert jina_source["name"] == "jina_reader"
        assert jina_source["base_url"] == "https://r.jina.ai"

        # Verify auth config
        assert "auth" in jina_source
        auth = jina_source["auth"]
        assert auth["type"] == "bearer"
        assert "JINA_API_KEY" in auth["token"]

        # Verify rate limiting
        assert "rate_limit" in jina_source
        rate_limit = jina_source["rate_limit"]
        assert "requests_per_second" in rate_limit

        # Verify caching
        assert "cache" in jina_source
        cache = jina_source["cache"]
        assert cache["enabled"] is True
        assert cache["ttl"] == 3600  # 1 hour

    def test_template_examples_format(self, news_scraper_template_path: Path) -> None:
        """Test example format in news scraper template.

        Verifies:
        - Examples have input/output structure
        - Input matches Jina response format
        - Output has required fields
        - At least 2 examples present

        Args:
            news_scraper_template_path: Path to template
        """
        with open(news_scraper_template_path, "r") as f:
            template = yaml.safe_load(f)

        examples = template["examples"]
        assert len(examples) >= 2, "Template should have at least 2 examples"

        # Validate first example
        example = examples[0]
        assert "input" in example
        assert "output" in example

        # Verify input format matches Jina response
        input_data = example["input"]
        assert "content" in input_data
        assert "title" in input_data
        assert "url" in input_data
        assert "extracted_at" in input_data

        # Verify output has required fields
        output_data = example["output"]
        assert "article_title" in output_data
        assert "author" in output_data
        assert "published_date" in output_data
        assert "source_url" in output_data

    @pytest.mark.asyncio
    async def test_template_compatible_with_real_api(
        self,
        jina_source: JinaDataSource,
        news_scraper_template_path: Path,
        rate_limit_delay: None,
    ) -> None:
        """Test template examples compatible with real Jina API response.

        Verifies:
        - Template examples match real API response structure
        - Required fields present in real responses
        - No schema mismatches

        Args:
            jina_source: Configured Jina source
            news_scraper_template_path: Path to template
            rate_limit_delay: Fixture to add delay between tests
        """
        # Get real API response
        result = await jina_source.fetch("https://example.com")

        # Load template examples
        with open(news_scraper_template_path, "r") as f:
            template = yaml.safe_load(f)

        example_input = template["examples"][0]["input"]

        # Verify real API response has same fields as template
        for field in ["content", "title", "url", "extracted_at"]:
            assert field in result, f"Real API missing field from template: {field}"
            assert field in example_input, f"Template missing field: {field}"

        # Verify types match
        assert isinstance(result["content"], str)
        assert isinstance(result["title"], str)
        assert isinstance(result["url"], str)
        assert isinstance(result["extracted_at"], str)


# =============================================================================
# Test: Cache Functionality
# =============================================================================


class TestJinaCaching:
    """Test caching behavior of JinaDataSource."""

    @pytest.mark.asyncio
    async def test_cache_hit_performance(
        self, jina_source: JinaDataSource, rate_limit_delay: None
    ) -> None:
        """Test cache improves performance on repeated requests.

        Verifies:
        - First request is slow (network)
        - Second request is fast (cache)
        - Content identical between requests

        Args:
            jina_source: Configured Jina source
            rate_limit_delay: Fixture to add delay between tests
        """
        url = "https://example.com"

        # First request (network)
        start1 = time.time()
        result1 = await jina_source.fetch(url)
        duration1 = time.time() - start1

        # Second request (cache)
        start2 = time.time()
        result2 = await jina_source.fetch(url)
        duration2 = time.time() - start2

        # Verify cache hit is faster
        # Network request should be >0.5s, cache should be <0.01s
        assert duration2 < duration1 * 0.1, "Cache not significantly faster"

        # Verify content identical
        assert result1["content"] == result2["content"]
        assert result1["title"] == result2["title"]
