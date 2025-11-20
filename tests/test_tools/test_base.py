import asyncio
import pytest
from kortex_mcp.tools.base import (
    ToolError,
    ToolTimeout,
    ToolValidationError,
    with_timeout,
    with_error_handling,
    log_tool_execution,
    BaseTool
)

class TestToolExceptions:
    def test_tool_error_to_dict(self):
        error = ToolError("Something went wrong", details={"code": 123}, tool_name="test_tool")
        data = error.to_dict()
        assert data["error"] == "Something went wrong"
        assert data["details"] == {"code": 123}
        assert data["tool"] == "test_tool"

    def test_tool_timeout_init(self):
        error = ToolTimeout("slow_tool", 5.0)
        assert "timed out after 5.0 seconds" in error.message
        assert error.details["timeout"] == 5.0
        assert error.tool_name == "slow_tool"

    def test_tool_validation_error_init(self):
        error = ToolValidationError("valid_tool", "age", "must be positive")
        assert "Validation failed for field 'age'" in error.message
        assert error.details["field"] == "age"
        assert error.details["reason"] == "must be positive"
        assert error.tool_name == "valid_tool"

@pytest.mark.asyncio
class TestDecorators:
    async def test_with_timeout_success(self):
        @with_timeout(timeout=1.0)
        async def quick_task():
            return "done"
        
        result = await quick_task()
        assert result == "done"

    async def test_with_timeout_failure(self):
        @with_timeout(timeout=0.01)
        async def slow_task():
            await asyncio.sleep(0.1)
            return "done"
        
        with pytest.raises(ToolTimeout) as exc:
            await slow_task()
        assert exc.value.tool_name == "slow_task"

    async def test_with_error_handling_success(self):
        @with_error_handling("safe_tool")
        async def safe_task():
            return "success"
        
        result = await safe_task()
        assert result == "success"

    async def test_with_error_handling_tool_error(self):
        @with_error_handling("safe_tool")
        async def failing_task():
            raise ToolError("Expected failure")
        
        with pytest.raises(ToolError, match="Expected failure"):
            await failing_task()

    async def test_with_error_handling_generic_exception(self):
        @with_error_handling("safe_tool")
        async def crashing_task():
            raise ValueError("Crash")
        
        with pytest.raises(ToolError) as exc:
            await crashing_task()
        assert "Tool execution failed: Crash" in exc.value.message
        assert exc.value.tool_name == "safe_tool"

    async def test_log_tool_execution(self):
        @log_tool_execution
        async def logged_task(arg):
            return f"processed {arg}"
        
        result = await logged_task("data")
        assert result == "processed data"

    async def test_log_tool_execution_failure(self):
        @log_tool_execution
        async def failing_logged_task():
            raise ValueError("Log me")
        
        with pytest.raises(ValueError, match="Log me"):
            await failing_logged_task()

@pytest.mark.asyncio
class TestBaseTool:
    class ConcreteTool(BaseTool):
        async def execute(self, **kwargs):
            return kwargs.get("value", "default")

    class ValidatingTool(BaseTool):
        def validate_params(self, params):
            if "required" not in params:
                raise ToolValidationError(self.name, "required", "missing")

        async def execute(self, **kwargs):
            return "valid"

    class SlowTool(BaseTool):
        async def execute(self, **kwargs):
            await asyncio.sleep(0.1)
            return "done"

    class CrashingTool(BaseTool):
        async def execute(self, **kwargs):
            raise ValueError("Boom")

    async def test_base_tool_init(self):
        tool = self.ConcreteTool("test", "description")
        assert tool.name == "test"
        assert tool.description == "description"
        assert str(tool) == "test: description"

    async def test_run_success(self):
        tool = self.ConcreteTool("test", "desc")
        result = await tool.run(value="input")
        assert result == "input"

    async def test_run_validation_failure(self):
        tool = self.ValidatingTool("validator", "desc")
        with pytest.raises(ToolValidationError) as exc:
            await tool.run(other="param")
        assert exc.value.details["field"] == "required"

    async def test_run_timeout(self):
        tool = self.SlowTool("slow", "desc", timeout=0.01)
        with pytest.raises(ToolTimeout) as exc:
            await tool.run()
        assert exc.value.tool_name == "slow"

    async def test_run_generic_exception(self):
        tool = self.CrashingTool("crasher", "desc")
        with pytest.raises(ToolError) as exc:
            await tool.run()
        assert "Tool execution failed: Boom" in exc.value.message

    async def test_not_implemented(self):
        tool = BaseTool("abstract", "desc")
        with pytest.raises(NotImplementedError):
            await tool.execute()
