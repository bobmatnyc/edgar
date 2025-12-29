"""Parallel processing service for performance optimization."""

import asyncio
from typing import Any, Callable, List, Optional, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class ParallelProcessingService:
    """Service for parallel processing with rate limiting and error handling."""

    def __init__(self, max_concurrent: int = 10, rate_limit_delay: float = 0.1):
        """Initialize parallel processing service."""
        self.max_concurrent = max_concurrent
        self.rate_limit_delay = rate_limit_delay
        self.semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(
            "Parallel processing service initialized",
            max_concurrent=max_concurrent,
            rate_limit_delay=rate_limit_delay
        )

    async def process_batch(
        self,
        items: List[T],
        processor: Callable[[T], Any],
        batch_size: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[R]:
        """Process items in parallel batches with rate limiting."""
        if not items:
            return []

        batch_size = batch_size or self.max_concurrent
        results = []
        total_items = len(items)

        logger.info("Starting batch processing", total_items=total_items, batch_size=batch_size)

        # Process items in batches
        for i in range(0, total_items, batch_size):
            batch = items[i:i + batch_size]
            batch_results = await self._process_batch_concurrent(batch, processor)
            results.extend(batch_results)

            # Progress callback
            if progress_callback:
                progress_callback(min(i + batch_size, total_items), total_items)

            # Rate limiting between batches
            if i + batch_size < total_items:
                await asyncio.sleep(self.rate_limit_delay)

        logger.info("Batch processing completed", total_items=total_items, results=len(results))
        return results

    async def _process_batch_concurrent(
        self, batch: List[T], processor: Callable[[T], Any]
    ) -> List[R]:
        """Process a single batch concurrently."""
        tasks = [self._process_item_with_semaphore(item, processor) for item in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    "Item processing failed",
                    item=str(batch[i]),
                    error=str(result)
                )
            elif result is not None:
                valid_results.append(result)

        return valid_results

    async def _process_item_with_semaphore(
        self, item: T, processor: Callable[[T], Any]
    ) -> Optional[R]:
        """Process single item with semaphore for rate limiting."""
        async with self.semaphore:
            try:
                # Add small delay for rate limiting
                await asyncio.sleep(self.rate_limit_delay)

                # Process the item
                if asyncio.iscoroutinefunction(processor):
                    result = await processor(item)
                else:
                    result = processor(item)

                return result

            except Exception as e:
                logger.error("Failed to process item", item=str(item), error=str(e))
                raise

    async def process_companies_parallel(
        self,
        company_ciks: List[str],
        analysis_function: Callable[[str], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """Process companies in parallel with optimized batching."""
        logger.info("Starting parallel company processing", companies=len(company_ciks))

        # Optimize batch size based on number of companies
        if len(company_ciks) <= 10:
            batch_size = len(company_ciks)  # Process all at once for small sets
        elif len(company_ciks) <= 50:
            batch_size = 10  # Medium batches
        else:
            batch_size = 20  # Larger batches for big datasets

        results = await self.process_batch(
            company_ciks,
            analysis_function,
            batch_size=batch_size,
            progress_callback=progress_callback
        )

        logger.info(
            "Parallel company processing completed",
            total_companies=len(company_ciks),
            successful_results=len(results)
        )

        return results

    async def process_multi_year_parallel(
        self,
        company_cik: str,
        years: List[int],
        year_processor: Callable[[str, int], Any]
    ) -> List[Any]:
        """Process multiple years for a company in parallel."""
        logger.info("Starting multi-year parallel processing", cik=company_cik, years=len(years))

        # Create tasks for each year
        async def process_year(year: int):
            return await year_processor(company_cik, year)

        # Process years concurrently with rate limiting
        results = await self.process_batch(
            years,
            lambda year: process_year(year),
            batch_size=3  # Limit concurrent years to avoid overwhelming API
        )

        logger.info(
            "Multi-year parallel processing completed",
            cik=company_cik,
            years=len(years),
            results=len(results)
        )

        return results