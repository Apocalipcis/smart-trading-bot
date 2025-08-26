"""
Rate limiting and retry logic for API requests with idempotency support.
"""
import asyncio
import time
import uuid
from typing import Any, Callable, Dict, Optional, TypeVar
from dataclasses import dataclass
from enum import Enum

import httpx


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class IdempotencyError(Exception):
    """Raised when idempotency key conflicts occur."""
    pass


class RequestType(Enum):
    """Types of API requests for rate limiting."""
    REST = "rest"
    WEBSOCKET = "websocket"
    ORDER = "order"
    MARKET_DATA = "market_data"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: int = 10
    burst_size: int = 20
    retry_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter_factor: float = 0.1


class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, rate: int, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity  # maximum tokens
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from the bucket."""
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_refill
            new_tokens = time_passed * self.rate
            
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def wait_for_tokens(self, tokens: int = 1) -> None:
        """Wait until enough tokens are available."""
        while not await self.acquire(tokens):
            await asyncio.sleep(1.0 / self.rate)


class IdempotencyStore:
    """Store for tracking idempotency keys."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.store: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()
    
    async def add_key(self, key: str, response_data: Dict[str, Any]) -> None:
        """Add an idempotency key with response data."""
        async with self._lock:
            self.store[key] = {
                'response': response_data,
                'timestamp': time.time()
            }
    
    async def get_response(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response for an idempotency key."""
        async with self._lock:
            if key in self.store:
                entry = self.store[key]
                if time.time() - entry['timestamp'] < self.ttl_seconds:
                    return entry['response']
                else:
                    del self.store[key]
            return None
    
    async def cleanup_expired(self) -> None:
        """Clean up expired idempotency keys."""
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.store.items()
                if current_time - entry['timestamp'] > self.ttl_seconds
            ]
            for key in expired_keys:
                del self.store[key]


class RateLimiter:
    """Main rate limiter with retry logic and idempotency support."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.buckets: Dict[RequestType, TokenBucket] = {
            RequestType.REST: TokenBucket(config.requests_per_second, config.burst_size),
            RequestType.WEBSOCKET: TokenBucket(config.requests_per_second * 2, config.burst_size * 2),
            RequestType.ORDER: TokenBucket(config.requests_per_second // 2, config.burst_size // 2),
            RequestType.MARKET_DATA: TokenBucket(config.requests_per_second * 3, config.burst_size * 3)
        }
        self.idempotency_store = IdempotencyStore()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the rate limiter cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self) -> None:
        """Stop the rate limiter cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired idempotency keys."""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                await self.idempotency_store.cleanup_expired()
            except asyncio.CancelledError:
                break
    
    def _generate_idempotency_key(self) -> str:
        """Generate a unique idempotency key."""
        return str(uuid.uuid4())
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = min(
            self.config.base_delay * (2 ** attempt),
            self.config.max_delay
        )
        
        # Add jitter to prevent thundering herd
        jitter = delay * self.config.jitter_factor * (2 * time.time() % 1 - 1)
        return max(0.1, delay + jitter)
    
    async def execute_with_retry(
        self,
        func: Callable,
        request_type: RequestType = RequestType.REST,
        idempotency_key: Optional[str] = None,
        *args,
        **kwargs
    ) -> Any:
        """Execute a function with rate limiting and retry logic."""
        # Check idempotency first
        if idempotency_key:
            cached_response = await self.idempotency_store.get_response(idempotency_key)
            if cached_response:
                return cached_response
        
        # Wait for rate limit
        bucket = self.buckets[request_type]
        await bucket.wait_for_tokens()
        
        # Execute with retries
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                result = await func(*args, **kwargs)
                
                # Store successful response for idempotency
                if idempotency_key:
                    await self.idempotency_store.add_key(idempotency_key, result)
                
                return result
                
            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                
                # Don't retry on client errors (4xx)
                if isinstance(e, httpx.HTTPStatusError) and 400 <= e.response.status_code < 500:
                    break
                
                if attempt < self.config.retry_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    break
        
        raise RetryExhaustedError(f"All retry attempts exhausted. Last error: {last_exception}")
    
    async def execute_order_request(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute an order request with order-specific rate limiting."""
        return await self.execute_with_retry(
            func, RequestType.ORDER, *args, **kwargs
        )
    
    async def execute_market_data_request(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute a market data request with market data rate limiting."""
        return await self.execute_with_retry(
            func, RequestType.MARKET_DATA, *args, **kwargs
        )


# Type variable for generic function types
T = TypeVar('T')


async def with_rate_limit(
    rate_limiter: RateLimiter,
    request_type: RequestType,
    func: Callable[..., T],
    *args,
    **kwargs
) -> T:
    """Decorator-style function execution with rate limiting."""
    return await rate_limiter.execute_with_retry(func, request_type, *args, **kwargs)
