"""Tests for desktop_state/walker.py - element filtering and type classification."""

import pytest

from pywinauto_mcp.desktop_state.walker import UIElementWalker


class TestInteractiveTypes:
    """Test INTERACTIVE_TYPES classification."""

    def test_button_is_interactive(self):
        assert "Button" in UIElementWalker.INTERACTIVE_TYPES

    def test_edit_is_interactive(self):
        assert "Edit" in UIElementWalker.INTERACTIVE_TYPES

    def test_combobox_is_interactive(self):
        assert "ComboBox" in UIElementWalker.INTERACTIVE_TYPES

    def test_checkbox_is_interactive(self):
        assert "CheckBox" in UIElementWalker.INTERACTIVE_TYPES

    def test_hyperlink_is_interactive(self):
        assert "Hyperlink" in UIElementWalker.INTERACTIVE_TYPES

    def test_text_is_not_interactive(self):
        assert "Text" not in UIElementWalker.INTERACTIVE_TYPES


class TestInformativeTypes:
    """Test INFORMATIVE_TYPES classification."""

    def test_text_is_informative(self):
        assert "Text" in UIElementWalker.INFORMATIVE_TYPES

    def test_statusbar_is_informative(self):
        assert "StatusBar" in UIElementWalker.INFORMATIVE_TYPES

    def test_button_is_not_informative(self):
        assert "Button" not in UIElementWalker.INFORMATIVE_TYPES


class TestShouldInclude:
    """Test the _should_include filtering logic."""

    def setup_method(self):
        self.walker = UIElementWalker()

    def _make_element(self, elem_type="Button", visible=True, width=100, height=30):
        return {
            "type": elem_type,
            "name": "Test",
            "app": "TestApp",
            "bounds": {"x": 10, "y": 20, "width": width, "height": height},
            "is_visible": visible,
            "is_enabled": True,
        }

    def test_visible_button_included(self):
        """Visible interactive element is included."""
        elem = self._make_element("Button")
        assert self.walker._should_include(elem) is True

    def test_visible_text_included(self):
        """Visible informative element is included."""
        elem = self._make_element("Text")
        assert self.walker._should_include(elem) is True

    def test_invisible_excluded(self):
        """Invisible element is excluded."""
        elem = self._make_element(visible=False)
        assert self.walker._should_include(elem) is False

    def test_zero_width_excluded(self):
        """Element with zero width is excluded."""
        elem = self._make_element(width=0)
        assert self.walker._should_include(elem) is False

    def test_zero_height_excluded(self):
        """Element with zero height is excluded."""
        elem = self._make_element(height=0)
        assert self.walker._should_include(elem) is False

    def test_negative_width_excluded(self):
        """Element with negative width is excluded."""
        elem = self._make_element(width=-10)
        assert self.walker._should_include(elem) is False

    def test_unknown_type_excluded(self):
        """Element with unknown type is excluded."""
        elem = self._make_element("UnknownType")
        assert self.walker._should_include(elem) is False

    def test_pane_excluded(self):
        """Pane type is neither interactive nor informative."""
        elem = self._make_element("Pane")
        assert self.walker._should_include(elem) is False

    def test_slider_included(self):
        """Slider is interactive."""
        elem = self._make_element("Slider")
        assert self.walker._should_include(elem) is True

    def test_titlebar_included(self):
        """TitleBar is informative."""
        elem = self._make_element("TitleBar")
        assert self.walker._should_include(elem) is True


class TestWalkerInit:
    """Test walker initialization."""

    def test_default_max_depth(self):
        walker = UIElementWalker()
        assert walker.max_depth == 10

    def test_custom_max_depth(self):
        walker = UIElementWalker(max_depth=5)
        assert walker.max_depth == 5

    def test_default_timeout(self):
        walker = UIElementWalker()
        assert walker.element_timeout == 0.5

    def test_custom_timeout(self):
        walker = UIElementWalker(element_timeout=1.0)
        assert walker.element_timeout == 1.0

    def test_elements_start_empty(self):
        walker = UIElementWalker()
        assert walker.elements == []
