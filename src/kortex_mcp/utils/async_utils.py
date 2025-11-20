"""Async utilities for Kortex MCP Server.

This module provides async helpers, timeout decorators, and utilities
for non-blocking operations.
"""

import asyncio
import functools
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def async_timeout(seconds: float) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """Decorator to add timeout to async functions.

    Args:
        seconds: Timeout in seconds

    Returns:
        Decorated async function with timeout

    Raises:
        asyncio.TimeoutError: If function execution exceeds timeout

    Example:
        >>> @async_timeout(5.0)
        ... async def slow_operation():
        ...     await asyncio.sleep(10)
        >>> await slow_operation()  # Raises TimeoutError after 5 seconds
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
        return wrapper
    return decorator


async def run_with_timeout(
    coro: Coroutine[Any, Any, T],
    timeout: float,
    default: T | None = None
) -> T | None:
    """Run a coroutine with a timeout, returning default on timeout.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        default: Value to return on timeout (default: None)

    Returns:
        Result of coroutine or default value if timeout occurs

    Example:
        >>> result = await run_with_timeout(
        ...     fetch_data(),
        ...     timeout=5.0,
        ...     default=[]
        ... )
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return default


async def gather_with_limit(
    *coroutines: Coroutine[Any, Any, T],
    limit: int = 10
) -> list[T]:
    """Execute multiple coroutines with a concurrency limit.

    Args:
        *coroutines: Coroutines to execute
        limit: Maximum number of concurrent executions

    Returns:
        List of results from all coroutines

    Example:
        >>> results = await gather_with_limit(
        ...     fetch_page(1),
        ...     fetch_page(2),
        ...     fetch_page(3),
        ...     limit=2
        ... )
    """
    semaphore = asyncio.Semaphore(limit)

    async def bounded_coro(coro: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(bounded_coro(c) for c in coroutines))


def monitor_performance(
    operation_name: str,
    threshold_ms: float = 100.0
) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """Decorator to monitor performance of async operations.

    Logs a warning if the operation takes longer than the threshold.

    Args:
        operation_name: Name of the operation for logging
        threshold_ms: Threshold in milliseconds (default: 100.0)

    Returns:
        Decorated async function

    Example:
        >>> @monitor_performance("database_query", threshold_ms=50)
        ... async def query_db():
        ...     ...
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"Performance warning: {operation_name} took {duration_ms:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(
                        f"Performance: {operation_name} took {duration_ms:.2f}ms"
                    )
        return wrapper
    return decorator


class PerformanceMonitor:
    """Simple performance monitor to track operation timings."""
    _timings: dict[str, list[float]] = {}

    @classmethod
    def record(cls, operation: str, duration: float) -> None:
        """Record execution time for an operation.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        if operation not in cls._timings:
            cls._timings[operation] = []
        cls._timings[operation].append(duration)

    @classmethod
    def get_stats(cls, operation: str) -> dict[str, float] | None:
        """Get statistics for an operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Dictionary with count, avg, min, max, last stats, or None if no data
        """
        if operation not in cls._timings or not cls._timings[operation]:
            return None
        times = cls._timings[operation]
        return {
            "count": len(times),
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "last": times[-1]
        }
        
    @classmethod
    def reset(cls) -> None:
        """Reset all timings."""
        cls._timings = {}


def measure_time(operation_name: str | None = None) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """Decorator to measure execution time of async functions.
    
    Args:
        operation_name: Optional name for the operation. Defaults to function name.
        
    Returns:
        Decorated async function that records timing
        
    Example:
        >>> @measure_time("database_query")
        ... async def query_db():
        ...     await asyncio.sleep(0.1)
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                name = operation_name or func.__name__
                PerformanceMonitor.record(name, duration)
                logger.debug(f"Operation '{name}' took {duration:.4f}s")
        return wrapper
    return decorator


def async_lru_cache(maxsize: int = 128) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """LRU cache decorator for async functions.
    
    Args:
        maxsize: Maximum number of items to cache
        
    Returns:
        Decorated async function with caching
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        cache: dict[str, T] = {}
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create a key from args and kwargs
            # Note: This is a simple implementation and requires args/kwargs to be stringifiable/hashable
            key = str(args) + str(sorted(kwargs.items()))
            
            if key in cache:
                return cache[key]
                
            result = await func(*args, **kwargs)
            
            if len(cache) >= maxsize:
                # Remove oldest item (first inserted)
                # In Python 3.7+, dicts preserve insertion order
                cache.pop(next(iter(cache)))
                
            cache[key] = result
            return result
        return wrapper
    return decorator


class AsyncTimer:
    """Context manager for timing async operations.

    Example:
        >>> async with AsyncTimer() as timer:
        ...     await some_operation()
        >>> print(f"Operation took {timer.elapsed:.2f} seconds")
    """

    def __init__(self) -> None:
        """Initialize the timer."""
        self.start_time: float | None = None
        self.end_time: float | None = None

    async def __aenter__(self) -> "AsyncTimer":
        """Start the timer."""
        self.start_time = asyncio.get_event_loop().time()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Stop the timer."""
        self.end_time = asyncio.get_event_loop().time()

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds.

        Returns:
            Elapsed time in seconds

        Raises:
            RuntimeError: If timer was not started
        """
        if self.start_time is None:
            raise RuntimeError("Timer was not started")

        end = self.end_time if self.end_time is not None else asyncio.get_event_loop().time()
        return end - self.start_time


async def retry_async(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    **kwargs: Any
) -> T:
    """Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        *args: Positional arguments for func
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        **kwargs: Keyword arguments for func

    Returns:
        Result from successful function call

    Raises:
        Exception: The last exception if all retries fail

    Example:
        >>> result = await retry_async(
        ...     unstable_operation,
        ...     arg1, arg2,
        ...     max_retries=5,
        ...     delay=0.5
        ... )
    """
    last_exception: Exception | None = None
    current_delay = delay

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                break

    if last_exception:
        raise last_exception
    raise RuntimeError("Retry failed with no exception")


async def run_periodic(
    func: Callable[..., Coroutine[Any, Any, None]],
    interval: float,
    *args: Any,
    **kwargs: Any
) -> None:
    """Run an async function periodically.

    Args:
        func: Async function to run periodically
        interval: Interval between executions in seconds
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Example:
        >>> async def health_check():
        ...     print("Checking health...")
        >>> # Run in background task
        >>> task = asyncio.create_task(run_periodic(health_check, 60.0))
    """
    while True:
        try:
            await func(*args, **kwargs)
        except Exception:
            # Log error but continue running
            pass
        await asyncio.sleep(interval)
