"""Tests for tools/utils.py - decorators, response models, and helpers."""

import pytest

from pywinauto_mcp.tools.utils import (
    ErrorResponse,
    SuccessResponse,
    handle_errors,
    log_execution,
    register_tool,
    timer,
)


class TestErrorResponse:
    """Test the ErrorResponse Pydantic model."""

    def test_required_fields(self):
        """ErrorResponse requires error and error_type."""
        resp = ErrorResponse(error="Something broke", error_type="ValueError")
        assert resp.success is False
        assert resp.error == "Something broke"
        assert resp.error_type == "ValueError"
        assert resp.timestamp  # Auto-generated

    def test_success_is_false(self):
        """success field is always False."""
        resp = ErrorResponse(error="x", error_type="y")
        assert resp.success is False


class TestSuccessResponse:
    """Test the SuccessResponse Pydantic model."""

    def test_default_data(self):
        """SuccessResponse defaults to empty data dict."""
        resp = SuccessResponse()
        assert resp.success is True
        assert resp.data == {}
        assert resp.timestamp

    def test_custom_data(self):
        """SuccessResponse accepts custom data."""
        resp = SuccessResponse(data={"key": "value"})
        assert resp.data == {"key": "value"}


class TestHandleErrors:
    """Test the handle_errors decorator."""

    def test_wraps_successful_result(self):
        """Successful function result is wrapped in SuccessResponse."""

        @handle_errors
        def good_func():
            return 42

        result = good_func()
        assert result["success"] is True
        assert result["data"]["result"] == 42

    def test_passes_through_dict_with_success_key(self):
        """Dict with 'success' key is returned as-is."""

        @handle_errors
        def already_formatted():
            return {"success": True, "custom": "data"}

        result = already_formatted()
        assert result == {"success": True, "custom": "data"}

    def test_catches_exception(self):
        """Exceptions are caught and returned as ErrorResponse."""

        @handle_errors
        def bad_func():
            raise ValueError("test error")

        result = bad_func()
        assert result["success"] is False
        assert result["error"] == "test error"
        assert result["error_type"] == "ValueError"

    def test_catches_runtime_error(self):
        """RuntimeError is caught with correct type."""

        @handle_errors
        def fails():
            raise RuntimeError("runtime fail")

        result = fails()
        assert result["error_type"] == "RuntimeError"
        assert "runtime fail" in result["error"]

    def test_preserves_function_name(self):
        """Decorated function preserves original name."""

        @handle_errors
        def my_func():
            pass

        assert my_func.__name__ == "my_func"


class TestLogExecution:
    """Test the log_execution decorator."""

    def test_returns_result(self):
        """Decorated function returns its result."""

        @log_execution
        def add(a, b):
            return a + b

        assert add(1, 2) == 3

    def test_reraises_exceptions(self):
        """Exceptions are re-raised after logging."""

        @log_execution
        def fails():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            fails()

    def test_preserves_function_name(self):
        """Decorated function preserves original name."""

        @log_execution
        def my_func():
            pass

        assert my_func.__name__ == "my_func"


class TestRegisterTool:
    """Test the register_tool decorator factory."""

    def test_sets_metadata(self):
        """register_tool attaches metadata to function."""

        @register_tool(name="my_tool", description="Does things", category="test")
        def my_func():
            return "result"

        assert my_func._is_tool is True
        assert my_func._tool_name == "my_tool"
        assert my_func._tool_description == "Does things"
        assert my_func._tool_category == "test"

    def test_default_name_from_function(self):
        """Tool name defaults to function name."""

        @register_tool()
        def some_function():
            pass

        assert some_function._tool_name == "some_function"

    def test_wraps_with_error_handling(self):
        """Registered tool gets handle_errors wrapping."""

        @register_tool(name="failing_tool")
        def fail():
            raise ValueError("intentional")

        result = fail()
        assert result["success"] is False
        assert result["error_type"] == "ValueError"


class TestTimer:
    """Test the timer context manager."""

    def test_timer_runs_block(self):
        """Timer context manager lets the block execute."""
        executed = False
        with timer("test operation"):
            executed = True
        assert executed

    def test_timer_handles_exception(self):
        """Timer logs even when block raises."""
        with pytest.raises(ValueError):
            with timer("failing operation"):
                raise ValueError("test")
