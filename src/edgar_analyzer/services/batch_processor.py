"""
Batch processing infrastructure for SEC EDGAR API - Meta-Extractor Architecture.

This module provides rate-limited batch processing for Fortune 100 companies,
ensuring compliance with SEC EDGAR Fair Access Policy (max 10 requests/second).

Migrated from src/edgar/services/batch_processor.py and adapted to Meta-Extractor
service patterns with dependency injection and async-first design.

Design Decisions:
- Token Bucket Rate Limiter: Smooth request distribution (8 req/sec vs 10 max)
- Conservative Limit: Safety margin for network latency and SEC compliance
- Async Architecture: Non-blocking I/O for concurrent processing
- Service Pattern: Constructor injection for testability and modularity

Performance:
- Rate: 8 requests/sec (480/min, 28,800/hour)
- Fortune 100 processing: ~12.5 seconds for all companies
- Concurrent workers: 5 default (tunable based on API behavior)

Trade-offs:
- Token bucket vs fixed window: Better handling of burst requests
- Async locks: Thread-safe but adds minimal overhead (~1ms per request)
- Conservative rate: Prevents SEC rate limit violations vs maximum throughput
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

import structlog
from pydantic import BaseModel

from edgar_analyzer.extractors.fortune100.models import SCTData, TaxData
from edgar_analyzer.services.interfaces import IEdgarApiService

logger = structlog.get_logger(__name__)

# Type variable for extracted data (SCTData, TaxData, or custom models)
T = TypeVar("T", bound=BaseModel)


@dataclass
class RateLimiter:
    """
    Token bucket rate limiter for SEC EDGAR API.

    SEC EDGAR Fair Access Policy:
    - Max 10 requests per second
    - Recommend spacing bulk requests
    - User-Agent header required

    Implementation:
    - Token bucket algorithm for smooth request distribution
    - Conservative 8 req/sec limit (20% safety margin)
    - Async lock for thread-safety
    - Automatic token replenishment based on elapsed time

    Attributes:
        requests_per_second: Maximum requests per second (default: 8.0)

    Example:
        >>> limiter = RateLimiter(requests_per_second=8.0)
        >>> await limiter.acquire()  # Blocks if insufficient tokens
    """

    requests_per_second: float = 8.0  # Conservative limit below SEC max
    _tokens: float = field(default=0.0, init=False)
    _last_update: float = field(default_factory=time.monotonic, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        """Initialize token bucket to full capacity."""
        self._tokens = self.requests_per_second
        logger.debug(
            "RateLimiter initialized",
            requests_per_second=self.requests_per_second,
        )

    async def acquire(self) -> None:
        """
        Wait until a request slot is available.

        Uses token bucket algorithm to maintain smooth request rate.
        Blocks if insufficient tokens, then waits for replenishment.

        Time Complexity: O(1)
        Space Complexity: O(1)

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
                logger.debug(
                    "Rate limit reached, waiting",
                    wait_time=wait_time,
                    tokens=self._tokens,
                )
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
    """
    Result of a single company extraction.

    Captures both successful extractions and failures with error details
    for partial result handling and debugging.

    Attributes:
        company_name: Company name that was processed
        cik: SEC CIK number
        form_type: SEC form type requested (e.g., "DEF 14A", "10-K")
        filing_date: Filing date from SEC metadata
        data: Extracted data (None if failed)
        error: Error message (None if successful)
        extraction_time: Time taken in seconds

    Example:
        >>> result = ExtractionResult(
        ...     company_name="Apple Inc.",
        ...     cik="0000320193",
        ...     form_type="DEF 14A",
        ...     filing_date="2024-01-15",
        ...     data=sct_data,
        ...     error=None,
        ...     extraction_time=2.5
        ... )
        >>> assert result.success
    """

    company_name: str
    cik: str
    form_type: str
    filing_date: str
    data: Optional[T]
    error: Optional[str] = None
    extraction_time: float = 0.0

    @property
    def success(self) -> bool:
        """
        Check if extraction was successful.

        Returns:
            True if data was extracted without errors
        """
        return self.data is not None and self.error is None


@dataclass
class BatchResult(Generic[T]):
    """
    Result of batch processing run.

    Aggregates all successful and failed extractions with metrics
    for analysis and reporting.

    Attributes:
        successful: List of successful extractions
        failed: List of failed extractions
        total_duration: Total batch processing time in seconds
        requests_made: Total number of API requests made

    Example:
        >>> result = BatchResult(
        ...     successful=[result1, result2],
        ...     failed=[result3],
        ...     total_duration=15.2,
        ...     requests_made=100
        ... )
        >>> print(f"Success rate: {result.success_rate:.1%}")
        Success rate: 66.7%
    """

    successful: list[ExtractionResult[T]]
    failed: list[ExtractionResult[T]]
    total_duration: float
    requests_made: int

    @property
    def success_rate(self) -> float:
        """
        Calculate success rate as percentage.

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
class CompanyTask:
    """
    Company extraction task definition.

    Encapsulates all information needed to extract data for a company.

    Attributes:
        company_name: Company name
        cik: SEC CIK number
        form_type: SEC form type to fetch
        extractor_factory: Function to create extractor instance
    """

    company_name: str
    cik: str
    form_type: str
    extractor_factory: Callable[[], Any]  # Returns IDataExtractor


class BatchProcessor(Generic[T]):
    """
    Batch processor for Fortune 100 SEC filings with rate limiting.

    Features:
    - Rate-limited requests (SEC compliant 8 req/sec)
    - Concurrent processing with semaphore
    - Progress callbacks for CLI updates
    - Error handling with partial results
    - Retry with exponential backoff (3 attempts)
    - Individual failure isolation (one failure doesn't stop batch)

    Attributes:
        edgar_api: SEC EDGAR API service for fetching filings
        rate_limiter: Rate limiter instance (default: 8 req/sec)
        max_concurrent: Maximum concurrent requests (default: 5)
        max_retries: Maximum retry attempts per request (default: 3)

    Example:
        >>> from edgar_analyzer.services.edgar_api_service import EdgarApiService
        >>> from edgar_analyzer.config.settings import ConfigService
        >>> config = ConfigService()
        >>> edgar_api = EdgarApiService(config=config)
        >>> processor = BatchProcessor[SCTData](
        ...     edgar_api=edgar_api,
        ...     max_concurrent=5
        ... )
        >>> tasks = [...]  # List of CompanyTask
        >>> result = await processor.process_batch(tasks)
        >>> print(f"Success: {result.success_count}/{len(tasks)}")
    """

    def __init__(
        self,
        edgar_api: IEdgarApiService,
        rate_limiter: Optional[RateLimiter] = None,
        max_concurrent: int = 5,
        max_retries: int = 3,
    ):
        """
        Initialize batch processor.

        Args:
            edgar_api: SEC EDGAR API service for fetching filings
            rate_limiter: Custom rate limiter (default: 8 req/sec)
            max_concurrent: Maximum concurrent requests (default: 5)
            max_retries: Maximum retry attempts per request (default: 3)
        """
        self.edgar_api = edgar_api
        self.rate_limiter = rate_limiter or RateLimiter()
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries

        logger.info(
            "BatchProcessor initialized",
            max_concurrent=max_concurrent,
            max_retries=max_retries,
            rate_limit=self.rate_limiter.requests_per_second,
        )

    async def process_batch(
        self,
        tasks: list[CompanyTask],
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None,
    ) -> BatchResult[T]:
        """
        Process multiple companies with rate limiting.

        Fetches SEC filings and runs extraction for each company, with:
        - Rate limiting to comply with SEC API limits (8 req/sec)
        - Concurrent processing for performance (bounded by semaphore)
        - Progress tracking via callbacks
        - Error isolation (individual failures don't stop batch)

        Args:
            tasks: List of company extraction tasks
            on_progress: Callback(current, total, company_name) for progress updates
            on_error: Callback(company_name, exception) for error handling

        Returns:
            BatchResult with successful and failed extractions

        Example:
            >>> tasks = [
            ...     CompanyTask(
            ...         company_name="Apple Inc.",
            ...         cik="0000320193",
            ...         form_type="DEF 14A",
            ...         extractor_factory=lambda: SCTAdapter(...)
            ...     )
            ... ]
            >>> result = await processor.process_batch(
            ...     tasks,
            ...     on_progress=lambda c, t, n: print(f"{c}/{t} - {n}")
            ... )
            >>> print(f"Success: {result.success_count}/{len(tasks)}")
        """
        start_time = time.monotonic()
        successful: list[ExtractionResult[T]] = []
        failed: list[ExtractionResult[T]] = []
        total = len(tasks)
        requests_made = 0

        logger.info("Starting batch processing", total_tasks=total)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_with_semaphore(
            idx: int, task: CompanyTask
        ) -> ExtractionResult[T]:
            """Process single company with semaphore and rate limiting."""
            async with semaphore:
                # Acquire rate limit token before request
                await self.rate_limiter.acquire()

                # Process with retry logic
                result = await self._process_single(task)

                # Call progress callback if provided
                if on_progress:
                    on_progress(idx + 1, total, task.company_name)

                return result

        # Process all companies concurrently (bounded by semaphore)
        tasks_list = [
            process_with_semaphore(i, task) for i, task in enumerate(tasks)
        ]
        results = await asyncio.gather(*tasks_list, return_exceptions=True)

        # Separate successful and failed results
        for i, result_item in enumerate(results):
            if isinstance(result_item, Exception):
                # Gather raised an exception (shouldn't happen with our error handling)
                task = tasks[i]
                if on_error:
                    on_error(task.company_name, result_item)

                failed.append(
                    ExtractionResult(
                        company_name=task.company_name,
                        cik=task.cik,
                        form_type=task.form_type,
                        filing_date="",
                        data=None,
                        error=str(result_item),
                        extraction_time=0.0,
                    )
                )
            else:
                # Type-safe cast to ExtractionResult
                result = result_item  # Already ExtractionResult[T]
                if result.success:
                    successful.append(result)
                    requests_made += 1
                else:
                    failed.append(result)
                    requests_made += 1
                    if on_error and result.error:
                        on_error(result.company_name, Exception(result.error))

        total_duration = time.monotonic() - start_time

        logger.info(
            "Batch processing completed",
            successful=len(successful),
            failed=len(failed),
            total_duration=f"{total_duration:.2f}s",
            requests_made=requests_made,
            success_rate=f"{(len(successful) / total * 100) if total > 0 else 0:.1f}%",
        )

        return BatchResult(
            successful=successful,
            failed=failed,
            total_duration=total_duration,
            requests_made=requests_made,
        )

    async def _process_single(self, task: CompanyTask) -> ExtractionResult[T]:
        """
        Process a single company with retry logic.

        Implements exponential backoff retry for transient failures
        (network errors, SEC API temporary issues).

        Args:
            task: Company extraction task

        Returns:
            ExtractionResult with success or failure details

        Retry Strategy:
        - Attempt 1: Immediate
        - Attempt 2: 2 second delay
        - Attempt 3: 4 second delay
        - Attempt 4: 8 second delay (if max_retries=3)
        """
        last_error: Optional[str] = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Processing company",
                    company=task.company_name,
                    cik=task.cik,
                    attempt=attempt + 1,
                )

                # Attempt fetch and extraction
                result = await self._fetch_and_extract(task)
                return result

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Extraction attempt failed",
                    company=task.company_name,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=last_error,
                )

                # If we have retries left, wait with exponential backoff
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    delay = 2 ** (attempt + 1)
                    await asyncio.sleep(delay)

        # All retries exhausted - return failure
        logger.error(
            "All retry attempts exhausted",
            company=task.company_name,
            error=last_error,
        )

        return ExtractionResult(
            company_name=task.company_name,
            cik=task.cik,
            form_type=task.form_type,
            filing_date="",
            data=None,
            error=last_error or "Unknown error",
            extraction_time=0.0,
        )

    async def _fetch_and_extract(self, task: CompanyTask) -> ExtractionResult[T]:
        """
        Fetch filing and run extraction.

        Args:
            task: Company extraction task

        Returns:
            ExtractionResult with extracted data

        Raises:
            Exception: If fetch or extraction fails

        Note:
            This method uses the legacy SEC client approach.
            TODO: Migrate to use EdgarApiService once get_filing_content is implemented.
        """
        start_time = time.monotonic()

        # TODO: Replace with EdgarApiService.get_filing_content when available
        # For now, we rely on the extractor having access to fetch logic
        # This will be refactored once EdgarApiService.get_filing_content is complete

        # Create extractor instance
        extractor = task.extractor_factory()

        # Call extractor (adapters handle the async/sync bridge)
        result_dict = await extractor.extract(
            filing_type=task.form_type,
            html="",  # Placeholder - extractor will fetch
            company=task.company_name,
            cik=task.cik,
        )

        if result_dict is None:
            raise ValueError("Extraction returned None")

        # Convert dict to typed model (adapters return dict)
        # We need to reconstruct the Pydantic model from dict
        # This assumes T is a Pydantic model with model_validate
        typed_data: T = type(self).__orig_bases__[0].__args__[0].model_validate(
            result_dict
        )

        extraction_time = time.monotonic() - start_time

        logger.info(
            "Extraction successful",
            company=task.company_name,
            extraction_time=f"{extraction_time:.2f}s",
        )

        return ExtractionResult(
            company_name=task.company_name,
            cik=task.cik,
            form_type=task.form_type,
            filing_date=result_dict.get("filing_date", ""),
            data=typed_data,
            error=None,
            extraction_time=extraction_time,
        )
