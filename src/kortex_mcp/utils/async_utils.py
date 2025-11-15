"""Async utilities for Kortex MCP Server.

This module provides async helpers, timeout decorators, and utilities
for non-blocking operations.
"""

import asyncio
import functools
from typing import TypeVar, Callable, Any, Coroutine, Optional
from datetime import datetime


T = TypeVar("T")


def async_timeout(seconds: float):
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
    default: Optional[T] = None
) -> Optional[T]:
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
    
    return await asyncio.gather(*[bounded_coro(coro) for coro in coroutines])


class AsyncTimer:
    """Context manager for timing async operations.

    Example:
        >>> async with AsyncTimer() as timer:
        ...     await some_operation()
        >>> print(f"Operation took {timer.elapsed:.2f} seconds")
    """

    def __init__(self) -> None:
        """Initialize the timer."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

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
    last_exception: Optional[Exception] = None
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
