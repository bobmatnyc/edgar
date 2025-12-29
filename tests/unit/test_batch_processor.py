"""Unit tests for batch processor module.

Tests cover:
- Rate limiter token bucket behavior
- Batch processing with mock client
- Error handling and retries
- Progress callbacks
- Concurrent processing
"""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from edgar.data.fortune100 import Company
from edgar.services.batch_processor import (
    BatchProcessor,
    BatchResult,
    ExtractionResult,
    RateLimiter,
)
from edgar.services.sec_edgar_client import SecEdgarClient


class ExtractionTestData(BaseModel):
    """Test Pydantic model for extraction results."""

    value: str


class MockExtractor:
    """Mock extractor for testing."""

    def __init__(self, company: str):
        self.company = company

    def extract(self, raw_data: dict[str, Any]) -> ExtractionTestData:
        """Extract test data."""
        return ExtractionTestData(value=f"Extracted: {self.company}")


# Rate Limiter Tests


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initializes with correct values."""
        limiter = RateLimiter(requests_per_second=10.0)
        assert limiter.requests_per_second == 10.0
        assert limiter._tokens == 10.0

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_immediate_request(self):
        """Test rate limiter allows immediate request when tokens available."""
        limiter = RateLimiter(requests_per_second=10.0)
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        # Should be nearly instant (< 10ms)
        assert elapsed < 0.01

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_rate(self):
        """Test rate limiter enforces request rate."""
        limiter = RateLimiter(requests_per_second=10.0)

        # Consume all tokens
        for _ in range(10):
            await limiter.acquire()

        # Next request should wait
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should wait approximately 1/10 second (0.1s)
        assert 0.08 < elapsed < 0.15

    @pytest.mark.asyncio
    async def test_rate_limiter_token_replenishment(self):
        """Test rate limiter replenishes tokens over time."""
        limiter = RateLimiter(requests_per_second=10.0)

        # Consume all tokens
        for _ in range(10):
            await limiter.acquire()

        # Wait for replenishment (0.5 seconds = 5 tokens)
        await asyncio.sleep(0.5)

        # Should be able to acquire 5 tokens without waiting
        start = time.monotonic()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should be nearly instant
        assert elapsed < 0.05

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent_requests(self):
        """Test rate limiter handles concurrent requests correctly."""
        limiter = RateLimiter(requests_per_second=5.0)

        # Launch 10 concurrent requests
        start = time.monotonic()
        tasks = [limiter.acquire() for _ in range(10)]
        await asyncio.gather(*tasks)
        elapsed = time.monotonic() - start

        # First 5 requests are immediate (from initial bucket)
        # Next 5 requests need to wait: (5 requests - 0 tokens) / 5 req/sec = 1 second minimum
        # Allow tolerance for async overhead and scheduling
        assert elapsed >= 0.8  # At least 0.8 seconds for the waiting requests


# ExtractionResult Tests


class TestExtractionResult:
    """Test suite for ExtractionResult class."""

    def test_extraction_result_success(self):
        """Test successful extraction result."""
        company = Company(rank=1, name="Test Corp", ticker="TEST", cik="0000000001", sector="Tech")
        data = ExtractionTestData(value="test")
        result = ExtractionResult(
            company=company,
            form_type="10-K",
            filing_date="2024-01-01",
            data=data,
            error=None,
            extraction_time=1.5,
        )

        assert result.success is True
        assert result.data == data
        assert result.error is None

    def test_extraction_result_failure(self):
        """Test failed extraction result."""
        company = Company(rank=1, name="Test Corp", ticker="TEST", cik="0000000001", sector="Tech")
        result = ExtractionResult(
            company=company,
            form_type="10-K",
            filing_date="2024-01-01",
            data=None,
            error="Failed to parse",
            extraction_time=1.0,
        )

        assert result.success is False
        assert result.data is None
        assert result.error == "Failed to parse"


# BatchResult Tests


class TestBatchResult:
    """Test suite for BatchResult class."""

    def test_batch_result_metrics(self):
        """Test batch result calculates metrics correctly."""
        company = Company(rank=1, name="Test Corp", ticker="TEST", cik="0000000001", sector="Tech")

        successful = [
            ExtractionResult(
                company=company,
                form_type="10-K",
                filing_date="2024-01-01",
                data=ExtractionTestData(value="test1"),
                error=None,
                extraction_time=1.0,
            ),
            ExtractionResult(
                company=company,
                form_type="10-K",
                filing_date="2024-01-01",
                data=ExtractionTestData(value="test2"),
                error=None,
                extraction_time=1.0,
            ),
        ]

        failed = [
            ExtractionResult(
                company=company,
                form_type="10-K",
                filing_date="2024-01-01",
                data=None,
                error="Failed",
                extraction_time=0.5,
            )
        ]

        result = BatchResult(
            successful=successful,
            failed=failed,
            total_duration=10.0,
            requests_made=3,
        )

        assert result.success_count == 2
        assert result.failure_count == 1
        assert result.success_rate == pytest.approx(2 / 3)

    def test_batch_result_empty(self):
        """Test batch result with no results."""
        result = BatchResult(successful=[], failed=[], total_duration=0.0, requests_made=0)

        assert result.success_count == 0
        assert result.failure_count == 0
        assert result.success_rate == 0.0


# BatchProcessor Tests


@pytest.fixture
def mock_sec_client():
    """Create mock SEC EDGAR client."""
    client = AsyncMock(spec=SecEdgarClient)
    client.get_latest_filing.return_value = {
        "cik": "0000000001",
        "accession_number": "0000000001-24-000001",
        "filing_date": "2024-01-01",
        "form_type": "10-K",
        "primary_document": "test.html",
        "url": "https://www.sec.gov/test",
    }
    client.fetch_filing_html.return_value = "<html>Test filing</html>"
    return client


@pytest.fixture
def test_companies():
    """Create test companies."""
    return [
        Company(
            rank=1,
            name="Company A",
            ticker="TSTA",
            cik="0000000001",
            sector="Technology",
        ),
        Company(
            rank=2,
            name="Company B",
            ticker="TSTB",
            cik="0000000002",
            sector="Finance",
        ),
        Company(
            rank=3,
            name="Company C",
            ticker="TSTC",
            cik="0000000003",
            sector="Healthcare",
        ),
    ]


class TestBatchProcessor:
    """Test suite for BatchProcessor class."""

    @pytest.mark.asyncio
    async def test_batch_processor_success(self, mock_sec_client, test_companies):
        """Test successful batch processing."""
        processor = BatchProcessor(
            sec_client=mock_sec_client,
            rate_limiter=RateLimiter(requests_per_second=100.0),  # Fast for testing
            max_concurrent=3,
            max_retries=1,
        )

        result = await processor.process_companies(
            companies=test_companies,
            extractor_factory=lambda c: MockExtractor(c.name),
            form_type="10-K",
        )

        assert result.success_count == 3
        assert result.failure_count == 0
        assert result.requests_made == 3
        assert all(r.data is not None for r in result.successful)

    @pytest.mark.asyncio
    async def test_batch_processor_with_failures(self, mock_sec_client, test_companies):
        """Test batch processing with some failures."""

        # Make second company fail
        async def failing_get_filing(cik, form_type):
            if cik == "0000000002":
                raise ValueError("Filing not found")
            return {
                "cik": cik,
                "accession_number": f"{cik}-24-000001",
                "filing_date": "2024-01-01",
                "form_type": form_type,
                "primary_document": "test.html",
                "url": "https://www.sec.gov/test",
            }

        mock_sec_client.get_latest_filing.side_effect = failing_get_filing
        mock_sec_client.fetch_filing_html.return_value = "<html>Test</html>"

        processor = BatchProcessor(
            sec_client=mock_sec_client,
            rate_limiter=RateLimiter(requests_per_second=100.0),
            max_concurrent=3,
            max_retries=1,
        )

        result = await processor.process_companies(
            companies=test_companies,
            extractor_factory=lambda c: MockExtractor(c.name),
            form_type="10-K",
        )

        assert result.success_count == 2
        assert result.failure_count == 1
        assert result.failed[0].company.cik == "0000000002"

    @pytest.mark.asyncio
    async def test_batch_processor_progress_callback(self, mock_sec_client, test_companies):
        """Test progress callback is called correctly."""
        progress_calls = []

        def on_progress(current: int, total: int, company_name: str):
            progress_calls.append((current, total, company_name))

        processor = BatchProcessor(
            sec_client=mock_sec_client,
            rate_limiter=RateLimiter(requests_per_second=100.0),
            max_concurrent=3,
            max_retries=1,
        )

        await processor.process_companies(
            companies=test_companies,
            extractor_factory=lambda c: MockExtractor(c.name),
            form_type="10-K",
            on_progress=on_progress,
        )

        # Should have 3 progress calls
        assert len(progress_calls) == 3
        # All should have total=3
        assert all(total == 3 for _, total, _ in progress_calls)
        # Current should be 1, 2, 3 (in some order due to concurrency)
        current_values = {current for current, _, _ in progress_calls}
        assert current_values == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_batch_processor_error_callback(self, mock_sec_client, test_companies):
        """Test error callback is called for failures."""
        errors = []

        def on_error(company: Company, exception: Exception):
            errors.append((company.name, str(exception)))

        # Make all companies fail
        mock_sec_client.get_latest_filing.side_effect = ValueError("Test error")

        processor = BatchProcessor(
            sec_client=mock_sec_client,
            rate_limiter=RateLimiter(requests_per_second=100.0),
            max_concurrent=3,
            max_retries=1,
        )

        await processor.process_companies(
            companies=test_companies,
            extractor_factory=lambda c: MockExtractor(c.name),
            form_type="10-K",
            on_error=on_error,
        )

        # Should have error callback for each company
        assert len(errors) == 3
        company_names = {name for name, _ in errors}
        assert company_names == {"Company A", "Company B", "Company C"}

    @pytest.mark.asyncio
    async def test_batch_processor_retry_logic(self, mock_sec_client, test_companies):
        """Test retry logic with exponential backoff."""
        call_count = 0

        async def failing_then_success(cik, form_type):
            nonlocal call_count
            call_count += 1
            # Fail first 2 attempts, succeed on 3rd
            if call_count < 3:
                raise ValueError("Temporary failure")
            return {
                "cik": cik,
                "accession_number": f"{cik}-24-000001",
                "filing_date": "2024-01-01",
                "form_type": form_type,
                "primary_document": "test.html",
                "url": "https://www.sec.gov/test",
            }

        mock_sec_client.get_latest_filing.side_effect = failing_then_success
        mock_sec_client.fetch_filing_html.return_value = "<html>Test</html>"

        processor = BatchProcessor(
            sec_client=mock_sec_client,
            rate_limiter=RateLimiter(requests_per_second=100.0),
            max_concurrent=1,  # Process one at a time
            max_retries=3,
        )

        start = time.monotonic()
        result = await processor.process_companies(
            companies=[test_companies[0]],  # Process only first company
            extractor_factory=lambda c: MockExtractor(c.name),
            form_type="10-K",
        )
        elapsed = time.monotonic() - start

        # Should succeed after retries
        assert result.success_count == 1

        # Should have made 3 attempts
        assert call_count == 3

        # Should have exponential backoff: 2s + 4s = 6s total wait time
        # Allow some tolerance
        assert elapsed >= 6.0

    @pytest.mark.asyncio
    async def test_batch_processor_concurrency_limit(self, mock_sec_client, test_companies):
        """Test concurrency limit is enforced."""
        active_requests = 0
        max_concurrent_seen = 0

        async def track_concurrency(url):
            nonlocal active_requests, max_concurrent_seen
            active_requests += 1
            max_concurrent_seen = max(max_concurrent_seen, active_requests)
            await asyncio.sleep(0.1)  # Simulate some work
            active_requests -= 1
            return "<html>Test</html>"

        mock_sec_client.fetch_filing_html.side_effect = track_concurrency

        processor = BatchProcessor(
            sec_client=mock_sec_client,
            rate_limiter=RateLimiter(requests_per_second=100.0),
            max_concurrent=2,  # Limit to 2 concurrent
            max_retries=1,
        )

        await processor.process_companies(
            companies=test_companies,
            extractor_factory=lambda c: MockExtractor(c.name),
            form_type="10-K",
        )

        # Max concurrent should not exceed limit
        assert max_concurrent_seen <= 2

    @pytest.mark.asyncio
    async def test_batch_processor_rate_limiting_integration(self, mock_sec_client, test_companies):
        """Test rate limiting is applied during batch processing."""
        processor = BatchProcessor(
            sec_client=mock_sec_client,
            rate_limiter=RateLimiter(requests_per_second=2.0),  # 2 req/sec
            max_concurrent=3,
            max_retries=1,
        )

        start = time.monotonic()
        result = await processor.process_companies(
            companies=test_companies,  # 3 companies
            extractor_factory=lambda c: MockExtractor(c.name),
            form_type="10-K",
        )
        elapsed = time.monotonic() - start

        # With 2 req/sec rate limit:
        # - First 2 requests use initial tokens (immediate)
        # - Third request waits for token: (1 token needed) / (2 req/sec) = 0.5 seconds
        # Allow tolerance for async overhead
        assert elapsed >= 0.4
        assert result.success_count == 3
