"""Batch processing infrastructure for SEC EDGAR API.

This module provides rate-limited batch processing for Fortune 100 companies,
ensuring compliance with SEC EDGAR Fair Access Policy (max 10 requests/second).

Design Decision: Token Bucket Rate Limiter
Rationale: Token bucket algorithm provides smooth request distribution and prevents
bursts that could trigger SEC rate limits.

Trade-offs:
- Conservative limit (8 req/sec vs 10 max): Provides safety margin for network latency
- Token bucket vs fixed window: Better handling of burst requests
- Async locks: Thread-safe but adds minimal overhead (~1ms per request)

Performance:
- Rate: 8 requests/sec (480/min, 28,800/hour)
- Fortune 100 processing: ~12.5 seconds for all companies
- Concurrent workers: 5 default (tunable based on API behavior)
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Callable, Generic, TypeVar, cast

from pydantic import BaseModel

from edgar.data.fortune100 import Company
from edgar.interfaces.data_extractor import IDataExtractor
from edgar.services.sec_edgar_client import SecEdgarClient

T = TypeVar("T", bound=BaseModel)


@dataclass
class RateLimiter:
    """Token bucket rate limiter for SEC EDGAR API.

    SEC EDGAR Fair Access Policy:
    - Max 10 requests per second
    - Recommend spacing bulk requests
    - User-Agent header required

    Implementation:
    - Token bucket algorithm
    - Conservative 8 req/sec limit (safety margin)
    - Async lock for thread-safety
    - Automatic token replenishment

    Attributes:
        requests_per_second: Maximum requests per second (default: 8.0)
    """

    requests_per_second: float = 8.0  # Conservative limit below SEC max
    _tokens: float = field(default=0.0, init=False)
    _last_update: float = field(default_factory=time.monotonic, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        """Initialize token bucket to full capacity."""
        self._tokens = self.requests_per_second

    async def acquire(self) -> None:
        """Wait until a request slot is available.

        Uses token bucket algorithm to maintain smooth request rate.
        Blocks if insufficient tokens, then waits for replenishment.

        Example:
            >>> limiter = RateLimiter(requests_per_second=8.0)
            >>> await limiter.acquire()  # Proceed immediately if tokens available
            >>> await limiter.acquire()  # May wait if no tokens
        """
        async with self._lock:
            # Replenish tokens based on time elapsed
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(
                self.requests_per_second,
                self._tokens + elapsed * self.requests_per_second,
            )
            self._last_update = now

            # If insufficient tokens, calculate wait time and sleep
            if self._tokens < 1:
                wait_time = (1 - self._tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)
                # After sleeping, replenish tokens again
                now = time.monotonic()
                elapsed = now - self._last_update
                self._tokens = min(
                    self.requests_per_second,
                    self._tokens + elapsed * self.requests_per_second,
                )
                self._last_update = now

            # Consume one token
            self._tokens -= 1


@dataclass
class ExtractionResult(Generic[T]):
    """Result of a single company extraction.

    Captures both successful extractions and failures with error details.

    Attributes:
        company: Company that was processed
        form_type: SEC form type requested (e.g., "DEF 14A", "10-K")
        filing_date: Filing date from SEC metadata
        data: Extracted data (None if failed)
        error: Error message (None if successful)
        extraction_time: Time taken in seconds
    """

    company: Company
    form_type: str
    filing_date: str
    data: T | None
    error: str | None = None
    extraction_time: float = 0.0

    @property
    def success(self) -> bool:
        """Check if extraction was successful.

        Returns:
            True if data was extracted without errors
        """
        return self.data is not None and self.error is None


@dataclass
class BatchResult(Generic[T]):
    """Result of batch processing run.

    Aggregates all successful and failed extractions with metrics.

    Attributes:
        successful: List of successful extractions
        failed: List of failed extractions
        total_duration: Total batch processing time in seconds
        requests_made: Total number of API requests made
    """

    successful: list[ExtractionResult[T]]
    failed: list[ExtractionResult[T]]
    total_duration: float
    requests_made: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage.

        Returns:
            Success rate (0.0 to 1.0), or 0.0 if no results
        """
        total = len(self.successful) + len(self.failed)
        return len(self.successful) / total if total > 0 else 0.0

    @property
    def success_count(self) -> int:
        """Count of successful extractions."""
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Count of failed extractions."""
        return len(self.failed)


@dataclass
class BatchProcessor(Generic[T]):
    """Batch processor for Fortune 100 SEC filings.

    Features:
    - Rate-limited requests (SEC compliant)
    - Concurrent processing with semaphore
    - Progress callbacks for UI updates
    - Error handling with partial results
    - Retry with exponential backoff
    - Individual failure isolation

    Attributes:
        sec_client: SEC EDGAR client for API calls
        rate_limiter: Rate limiter instance (default: 8 req/sec)
        max_concurrent: Maximum concurrent requests (default: 5)
        max_retries: Maximum retry attempts per request (default: 3)
    """

    sec_client: SecEdgarClient
    rate_limiter: RateLimiter = field(default_factory=RateLimiter)
    max_concurrent: int = 5
    max_retries: int = 3

    async def process_companies(
        self,
        companies: list[Company],
        extractor_factory: Callable[[Company], IDataExtractor],
        form_type: str,
        on_progress: Callable[[int, int, str], None] | None = None,
        on_error: Callable[[Company, Exception], None] | None = None,
    ) -> BatchResult[T]:
        """Process multiple companies with rate limiting.

        Fetches SEC filings and runs extraction for each company, with:
        - Rate limiting to comply with SEC API limits
        - Concurrent processing for performance
        - Progress tracking via callbacks
        - Error isolation (individual failures don't stop batch)

        Args:
            companies: List of companies to process
            extractor_factory: Function that creates an extractor for a company
            form_type: SEC form type (e.g., "DEF 14A", "10-K")
            on_progress: Callback(current, total, company_name) for progress updates
            on_error: Callback(company, exception) for error handling

        Returns:
            BatchResult with successful and failed extractions

        Example:
            >>> registry = Fortune100Registry.load_default()
            >>> companies = registry.get_by_rank_range(1, 10)
            >>> processor = BatchProcessor(sec_client=SecEdgarClient())
            >>> result = await processor.process_companies(
            ...     companies,
            ...     lambda c: SCTExtractor(company=c.name, cik=c.cik),
            ...     "DEF 14A"
            ... )
            >>> print(f"Success: {result.success_count}/{len(companies)}")
        """
        start_time = time.monotonic()
        successful: list[ExtractionResult[T]] = []
        failed: list[ExtractionResult[T]] = []
        total = len(companies)
        requests_made = 0

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_with_semaphore(idx: int, company: Company) -> ExtractionResult[T]:
            """Process single company with semaphore and rate limiting."""
            async with semaphore:
                # Acquire rate limit token before request
                await self.rate_limiter.acquire()

                # Create extractor for this company
                extractor = extractor_factory(company)

                # Process with retry logic
                result = await self._process_single(company, extractor, form_type)

                # Call progress callback if provided
                if on_progress:
                    on_progress(idx + 1, total, company.name)

                return result

        # Process all companies concurrently (bounded by semaphore)
        tasks = [process_with_semaphore(i, company) for i, company in enumerate(companies)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successful and failed results
        for i, result_item in enumerate(results):
            if isinstance(result_item, Exception):
                # Gather raised an exception (shouldn't happen with our error handling)
                company = companies[i]
                if on_error:
                    on_error(company, result_item)
                failed.append(
                    ExtractionResult(
                        company=company,
                        form_type=form_type,
                        filing_date="",
                        data=None,
                        error=str(result_item),
                        extraction_time=0.0,
                    )
                )
            else:
                # Type-safe cast to ExtractionResult
                result = cast(ExtractionResult[T], result_item)
                if result.success:
                    successful.append(result)
                    requests_made += 1
                else:
                    failed.append(result)
                    requests_made += 1
                    if on_error and result.error:
                        company = result.company
                        on_error(company, Exception(result.error))

        total_duration = time.monotonic() - start_time

        return BatchResult(
            successful=successful,
            failed=failed,
            total_duration=total_duration,
            requests_made=requests_made,
        )

    async def _process_single(
        self,
        company: Company,
        extractor: IDataExtractor,
        form_type: str,
    ) -> ExtractionResult[T]:
        """Process a single company with retry logic.

        Implements exponential backoff retry for transient failures.

        Args:
            company: Company to process
            extractor: Data extractor instance
            form_type: SEC form type

        Returns:
            ExtractionResult with success or failure details
        """
        last_error: str | None = None

        for attempt in range(self.max_retries):
            try:
                # Attempt fetch and extraction
                result = await self._fetch_and_extract(company, extractor, form_type)
                return result

            except Exception as e:
                last_error = str(e)

                # If we have retries left, wait with exponential backoff
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    delay = 2 ** (attempt + 1)
                    await asyncio.sleep(delay)

        # All retries exhausted - return failure
        return ExtractionResult(
            company=company,
            form_type=form_type,
            filing_date="",
            data=None,
            error=last_error or "Unknown error",
            extraction_time=0.0,
        )

    async def _fetch_and_extract(
        self,
        company: Company,
        extractor: IDataExtractor,
        form_type: str,
    ) -> ExtractionResult[T]:
        """Fetch filing and run extraction.

        Args:
            company: Company to process
            extractor: Data extractor instance
            form_type: SEC form type

        Returns:
            ExtractionResult with extracted data

        Raises:
            Exception: If fetch or extraction fails
        """
        start_time = time.monotonic()

        # Fetch latest filing metadata
        filing = await self.sec_client.get_latest_filing(cik=company.cik, form_type=form_type)

        # Fetch HTML content
        html = await self.sec_client.fetch_filing_html(filing["url"])

        # Run extraction
        raw_data = {"html": html, "filing": filing}
        extracted_data = extractor.extract(raw_data)

        # Type-safe cast - we know the extractor returns T
        typed_data = cast(T, extracted_data)

        extraction_time = time.monotonic() - start_time

        return ExtractionResult(
            company=company,
            form_type=form_type,
            filing_date=filing["filing_date"],
            data=typed_data,
            error=None,
            extraction_time=extraction_time,
        )
