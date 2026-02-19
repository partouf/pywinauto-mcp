"""Tests for core/decorators.py - tool and stateful decorators."""

import pytest

from pywinauto_mcp.core.decorators import stateful, tool


class TestToolDecorator:
    """Test the @tool decorator factory."""

    def test_sets_tool_metadata(self):
        """Decorator sets _is_tool and metadata attributes."""

        @tool(name="my_tool", description="test desc", category="testing")
        def my_func():
            pass

        assert my_func._is_tool is True
        assert my_func._tool_name == "my_tool"
        assert my_func._tool_description == "test desc"
        assert my_func._tool_category == "testing"

    def test_name_defaults_to_function_name(self):
        """Tool name defaults to the decorated function name."""

        @tool()
        def auto_named():
            pass

        assert auto_named._tool_name == "auto_named"

    def test_description_defaults_to_docstring(self):
        """Description falls back to docstring when not provided."""

        @tool()
        def documented():
            """This is the docstring."""

        assert documented._tool_description == "This is the docstring."

    def test_description_defaults_to_empty(self):
        """Description is empty string when no desc or docstring."""

        @tool()
        def no_doc():
            pass

        assert no_doc._tool_description == ""

    def test_default_category(self):
        """Category defaults to 'general'."""

        @tool()
        def func():
            pass

        assert func._tool_category == "general"

    def test_input_output_models(self):
        """input_model and output_model are stored."""

        @tool(input_model="InputModel", output_model="OutputModel")
        def func():
            pass

        assert func._input_model == "InputModel"
        assert func._output_model == "OutputModel"


class TestStatefulDecorator:
    """Test the @stateful decorator factory."""

    def test_marks_as_stateful(self):
        """Decorator sets _requires_state to True."""

        @stateful()
        def my_func():
            pass

        assert my_func._requires_state is True

    def test_marks_as_stateless(self):
        """Decorator can set _requires_state to False."""

        @stateful(requires_state=False)
        def my_func():
            pass

        assert my_func._requires_state is False

    def test_function_still_callable(self):
        """Decorated function still returns its result."""

        @stateful()
        def add(a, b):
            return a + b

        assert add(1, 2) == 3
