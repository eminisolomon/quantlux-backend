"""Rate limiting for API calls."""

import asyncio
import time

from app.utils.logger import logger


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, calls_per_second: float = 10.0):
        """Initialize rate limiter."""
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait_if_needed(self):
        """Wait if needed to respect rate limit."""
        now = time.time()
        elapsed = now - self.last_call

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limit: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self.last_call = time.time()

    async def await_if_needed(self):
        """Async version of wait_if_needed."""
        now = time.time()
        elapsed = now - self.last_call

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limit: awaiting {sleep_time:.3f}s")
            await asyncio.sleep(sleep_time)

        self.last_call = time.time()
