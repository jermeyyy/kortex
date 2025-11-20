import asyncio
import pytest
from kortex_mcp.utils.async_utils import async_timeout, run_with_timeout, gather_with_limit

class TestAsyncUtils:
    @pytest.mark.asyncio
    async def test_async_timeout_success(self):
        @async_timeout(1.0)
        async def quick_task():
            return "done"
        
        result = await quick_task()
        assert result == "done"

    @pytest.mark.asyncio
    async def test_async_timeout_fails(self):
        @async_timeout(0.1)
        async def slow_task():
            await asyncio.sleep(0.2)
            return "done"
        
        with pytest.raises(asyncio.TimeoutError):
            await slow_task()

    @pytest.mark.asyncio
    async def test_run_with_timeout_success(self):
        async def quick_task():
            return "done"
        
        result = await run_with_timeout(quick_task(), timeout=1.0)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_run_with_timeout_fails_returns_default(self):
        async def slow_task():
            await asyncio.sleep(0.2)
            return "done"
        
        result = await run_with_timeout(slow_task(), timeout=0.1, default="timeout")
        assert result == "timeout"

    @pytest.mark.asyncio
    async def test_gather_with_limit(self):
        async def task(i):
            await asyncio.sleep(0.01)
            return i
        
        tasks = [task(i) for i in range(5)]
        results = await gather_with_limit(*tasks, limit=2)
        assert sorted(results) == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_monitor_performance(self):
        from kortex_mcp.utils.async_utils import monitor_performance
        
        @monitor_performance(operation_name="test_op", threshold_ms=0)
        async def monitored_task():
            await asyncio.sleep(0.01)
            return "done"
        
        result = await monitored_task()
        assert result == "done"

    @pytest.mark.asyncio
    async def test_async_timer(self):
        from kortex_mcp.utils.async_utils import AsyncTimer
        
        async with AsyncTimer() as timer:
            await asyncio.sleep(0.01)
            assert timer.elapsed >= 0.01
        
        assert timer.elapsed >= 0.01

    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        from kortex_mcp.utils.async_utils import retry_async
        
        count = 0
        async def flaky_task():
            nonlocal count
            count += 1
            if count < 2:
                raise ValueError("Fail")
            return "success"
        
        result = await retry_async(flaky_task, max_retries=3, delay=0.01)
        assert result == "success"
        assert count == 2

    @pytest.mark.asyncio
    async def test_retry_async_failure(self):
        from kortex_mcp.utils.async_utils import retry_async
        
        async def failing_task():
            raise ValueError("Always fail")
        
        with pytest.raises(ValueError, match="Always fail"):
            await retry_async(failing_task, max_retries=2, delay=0.01)

    @pytest.mark.asyncio
    async def test_run_periodic(self):
        from kortex_mcp.utils.async_utils import run_periodic
        
        count = 0
        async def periodic_task():
            nonlocal count
            count += 1
            if count >= 3:
                raise asyncio.CancelledError() # Stop the loop
        
        try:
            await asyncio.wait_for(
                run_periodic(periodic_task, interval=0.01),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            pass
        except asyncio.CancelledError:
            pass
            
        assert count >= 3
