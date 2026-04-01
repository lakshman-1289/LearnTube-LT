import asyncio
import time
import random
import logging
import os
from typing import Callable, Any, Dict, List, Optional

from aiohttp import ClientError

from course_generator.src.core.token_utils import count_tokens

logger = logging.getLogger("groq_requester")
logger.setLevel(logging.INFO)


class RateLimiter:
    """Simple in-process rate limiter that ensures a minimum interval between requests.

    Usage:
        async with rate_limiter:
            # safe to make request
    """

    def __init__(self, min_interval_seconds: float = 2.5):
        self.min_interval = float(min_interval_seconds)
        self._lock = asyncio.Lock()
        self._last_time = 0.0

    async def __aenter__(self):
        await self._lock.acquire()
        now = time.time()
        elapsed = now - self._last_time
        wait = self.min_interval - elapsed
        if wait > 0:
            logger.debug(f"RateLimiter sleeping {wait:.2f}s to respect min interval")
            await asyncio.sleep(wait)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._last_time = time.time()
        self._lock.release()


async def retry_with_backoff(
    func: Callable[[], Any],
    is_retryable: Callable[[Exception], bool],
    max_retries: int = 5,
    initial_delay: float = 5.0,
    max_delay: float = 120.0,
    jitter_range: tuple = (1.0, 3.0),
) -> Any:
    """
    Run async func with exponential backoff and jitter for retryable errors.

    - initial_delay: first delay in seconds
    - doubles each retry up to max_delay
    - adds random jitter in +/- jitter_range
    """
    attempt = 0
    delay = initial_delay

    while True:
        try:
            attempt += 1
            logger.debug(f"Attempt {attempt}: calling function")
            return await func()

        except Exception as e:
            retryable = is_retryable(e)
            if not retryable or attempt >= max_retries:
                logger.info(f"Not retrying (attempt {attempt}). Error: {e}")
                raise

            # compute jittered delay
            jitter = random.uniform(jitter_range[0], jitter_range[1])
            sleep_time = min(max_delay, delay) + jitter
            logger.info(f"Retryable error on attempt {attempt}: {e}; sleeping {sleep_time:.1f}s before retry")
            await asyncio.sleep(sleep_time)
            delay = min(max_delay, delay * 2)

