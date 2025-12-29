"""
Tests for SCTExtractor.

Test Coverage:
- Extraction success scenarios
- Error handling (network, parsing, validation)
- Rate limiting behavior
- HTML section detection
- LLM response parsing

Design Decisions:
- **Mock External Calls**: Don't hit real SEC EDGAR or OpenRouter APIs in tests
- **Fixture-Based**: Use pytest fixtures for test data
- **Comprehensive Coverage**: Test happy path + edge cases + error conditions
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from edgar_analyzer.clients.openrouter_client import OpenRouterClient
from ..models.sct_models import (
    SCTData,
    SCTExtractionResult,
    ExecutiveCompensation,
    CompensationYear,
)
from ..sct_extractor import SCTExtractor


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_openrouter():
    """Mock OpenRouter client for testing."""
    client = MagicMock(spec=OpenRouterClient)
    client.model = "anthropic/claude-sonnet-4.5"
    client.chat_completion_json = AsyncMock()
    return client


@pytest.fixture
def extractor(mock_openrouter):
    """Create extractor instance with mocked dependencies."""
    return SCTExtractor(
        openrouter_client=mock_openrouter, user_agent="TestAgent test@example.com"
    )


@pytest.fixture
def sample_sct_html_data():
    """Sample SCT HTML for testing"""
    return {
        "html": "\u003ctable\u003e\u003ctr\u003e\u003cth\u003eName\u003c/th\u003e\u003cth\u003eYear\u003c/th\u003e\u003cth\u003eSalary\u003c/th\u003e\u003c/tr\u003e\u003c/table\u003e"
    }


# ============================================================================
# EXTRACTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_extraction_success(extractor, mock_openrouter):
    """Test successful extraction with valid data"""

    # Mock LLM responses

    mock_openrouter.chat_completion_json.return_value = '{"company_name": "Apple Inc.", "ticker": "AAPL", "cik": "0000320193", "executives": []}'

    # Execute (default pattern)
    result = await extractor.extract(
        filing_url="https://www.sec.gov/test",
        cik="0000320193",
        company_name="Apple Inc.",
        ticker="AAPL",
    )

    # Default assertions
    assert result.success is True

    assert result.data is not None
    assert result.error_message is None


# ============================================================================
# HTML PARSING TESTS
# ============================================================================


def test_is_valid_table_success(extractor):
    """Test table validation with correct structure."""
    from bs4 import BeautifulSoup

    html = """
    <table>
        <tr>
            
            <th>name</th>
            
            <th>year</th>
            
            <th>salary</th>
            
        </tr>
        <tr>
            
            <td>Sample data</td>
            
            <td>Sample data</td>
            
            <td>Sample data</td>
            
        </tr>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    assert extractor._is_valid_table(table) is True


def test_is_valid_table_rejection(extractor):
    """Test table validation rejects wrong table types."""
    from bs4 import BeautifulSoup

    # Table with reject patterns
    html = """
    <table>
        <tr>
            
            <th>grant date</th>
            
            <th>fees earned</th>
            
        </tr>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    assert extractor._is_valid_table(table) is False


def test_extract_table_with_context(extractor):
    """Test context extraction around table."""
    from bs4 import BeautifulSoup

    html = """
    <p>Context before table</p>
    <table>
        <tr><td>Table data</td></tr>
    </table>
    <p>Context after table (footnotes)</p>
    """

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    result = extractor._extract_table_with_context(
        table, chars_before=100, chars_after=100
    )

    assert "Context before" in result
    assert "Table data" in result
    assert "Context after" in result


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_rate_limiting(extractor):
    """Test SEC EDGAR rate limiting behavior."""
    import time

    with patch("httpx.Client") as mock_client:
        mock_response = MagicMock()
        mock_response.text = "<html>test</html>"
        mock_response.raise_for_status = MagicMock()
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        # First request
        start = time.time()
        extractor._fetch_filing_html("https://test.com/filing1")
        first_duration = time.time() - start

        # Second request (should be delayed)
        start = time.time()
        extractor._fetch_filing_html("https://test.com/filing2")
        second_duration = time.time() - start

        # Second request should include rate limit delay
        assert second_duration >= extractor.SEC_RATE_LIMIT_DELAY


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_extraction_network_error(extractor, mock_openrouter):
    """Test extraction handles network errors gracefully."""
    with patch.object(extractor, "_fetch_filing_html") as mock_fetch:
        mock_fetch.side_effect = Exception("Network timeout")

        result = await extractor.extract(
            filing_url="https://test.com/filing",
            cik="0000000000",
            company_name="Test Corp",
        )

        assert result.success is False
        assert "Network timeout" in result.error_message


@pytest.mark.asyncio
async def test_extraction_invalid_json_response(extractor, mock_openrouter):
    """Test extraction handles invalid JSON from LLM."""
    with (
        patch.object(extractor, "_fetch_filing_html") as mock_fetch,
        patch.object(extractor, "_extract_section") as mock_extract,
    ):

        mock_fetch.return_value = "<html>test</html>"
        mock_extract.return_value = "<table>data</table>"
        mock_openrouter.chat_completion_json.return_value = "not valid json"

        result = await extractor.extract(
            filing_url="https://test.com/filing",
            cik="0000000000",
            company_name="Test Corp",
        )

        assert result.success is False
        assert "Invalid JSON" in result.error_message


@pytest.mark.asyncio
async def test_extraction_validation_failure_retry(extractor, mock_openrouter):
    """Test extraction retries on validation failure."""
    with (
        patch.object(extractor, "_fetch_filing_html") as mock_fetch,
        patch.object(extractor, "_extract_section") as mock_extract,
        patch.object(extractor, "_validate_extraction") as mock_validate,
    ):

        mock_fetch.return_value = "<html>test</html>"
        mock_extract.return_value = "<table>data</table>"

        # First call fails validation, second succeeds
        mock_validate.side_effect = [False, True]

        # Mock LLM to return valid JSON
        mock_openrouter.chat_completion_json.return_value = json.dumps(
            {
                "company_name": "Test Corp",
                # ... other required fields
            }
        )

        result = await extractor.extract(
            filing_url="https://test.com/filing",
            cik="0000000000",
            company_name="Test Corp",
        )

        # Should have retried (2 calls)
        assert mock_openrouter.chat_completion_json.call_count == 2


# ============================================================================
# INTEGRATION TESTS (Optional - mark as slow)
# ============================================================================


# ============================================================================
# UTILITY TESTS
# ============================================================================


def test_parse_response_strips_markdown_fences(extractor):
    """Test that markdown code fences are stripped from LLM response."""
    json_with_fences = """```json
    {
        "company_name": "Test Corp",
        "cik": "0000000000"
    }
    ```"""

    # This should not raise an error
    result = extractor._parse_response(
        response_json=json_with_fences, filing_url="https://test.com"
    )

    assert result is not None
