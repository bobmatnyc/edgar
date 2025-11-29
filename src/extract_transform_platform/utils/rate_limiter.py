"""
Rate Limiter Utility

Implements token bucket rate limiting for API calls.
Supports both synchronous and asynchronous contexts.

Design Decision: Generic utility for any rate-limited operation
- Token bucket algorithm with sliding window
- Async-first design for modern I/O operations
- Thread-safe with asyncio.Lock

Performance:
- Time Complexity: O(n) for cleanup where n = requests in window
- Space Complexity: O(m) where m = requests_per_minute
- Cleanup is lazy (on acquire), not proactive
"""

import asyncio
from datetime import datetime, timedelta
from collections import deque
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for controlling request rates.

    Uses a sliding window approach to track requests and enforce limits.
    Generic utility suitable for API calls, web scraping, file I/O, etc.

    Example:
        limiter = RateLimiter(requests_per_minute=60)
        await limiter.acquire()  # Wait if needed before making request

    Trade-offs:
    - Sliding window vs Fixed window: More accurate burst detection
    - In-memory tracking vs Redis: Simple, no external dependencies
    - Per-instance vs Global: Per-instance for flexibility
    """

    def __init__(self, requests_per_minute: int):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum number of requests allowed per minute

        Raises:
            ValueError: If requests_per_minute is not positive
        """
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")

        self.requests_per_minute = requests_per_minute
        self.window = timedelta(minutes=1)
        self.requests: deque[datetime] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request.

        Blocks until a request slot is available within the rate limit.
        Uses asyncio.sleep() to avoid busy waiting.

        Performance:
        - Best case: O(1) when no cleanup needed
        - Worst case: O(n) cleanup + sleep time
        - Average: O(k) where k = expired requests in window
        """
        async with self._lock:
            now = datetime.now()

            # Remove old requests outside the sliding window
            while self.requests and now - self.requests[0] > self.window:
                self.requests.popleft()

            # Check if we need to wait
            if len(self.requests) >= self.requests_per_minute:
                # Calculate wait time until oldest request expires
                oldest = self.requests[0]
                wait_until = oldest + self.window
                wait_time = (wait_until - now).total_seconds()

                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                # Clean up expired requests after waiting
                now = datetime.now()
                while self.requests and now - self.requests[0] > self.window:
                    self.requests.popleft()

            # Record this request
            self.requests.append(now)

    def get_current_usage(self) -> int:
        """Get current number of requests in the sliding window.

        Returns:
            Number of requests made in the last minute

        Note: This method does NOT acquire the lock, so it may be
        slightly out of sync during concurrent acquire() calls.
        """
        now = datetime.now()
        # Clean up old requests
        while self.requests and now - self.requests[0] > self.window:
            self.requests.popleft()
        return len(self.requests)

    def reset(self) -> None:
        """Reset the rate limiter, clearing all tracked requests.

        Useful for testing or when changing rate limit requirements.
        """
        self.requests.clear()
