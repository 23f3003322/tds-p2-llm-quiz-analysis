"""
Rate Limiter
Implements token bucket rate limiting
"""

import asyncio
import time
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter
    Ensures API calls respect rate limits
    """
    
    def __init__(
        self,
        calls: Optional[int] = None,
        period: float = 60.0
    ):
        """
        Initialize rate limiter
        
        Args:
            calls: Maximum calls per period (None = no limit)
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.tokens = calls if calls else float('inf')
        self.max_tokens = calls if calls else float('inf')
        self.last_update = time.time()
        self._lock = asyncio.Lock()
        
        if calls:
            logger.debug(f"Rate limiter: {calls} calls per {period}s")
    
    async def acquire(self):
        """
        Acquire a token (wait if necessary)
        """
        if self.calls is None:
            return  # No rate limiting
        
        async with self._lock:
            # Refill tokens based on time passed
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(
                self.max_tokens,
                self.tokens + (time_passed * self.max_tokens / self.period)
            )
            self.last_update = now
            
            # Wait if no tokens available
            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (self.period / self.max_tokens)
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 1
            
            # Consume token
            self.tokens -= 1
