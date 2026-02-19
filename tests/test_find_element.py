"""Tests for _find_element selector logic in portmanteau_elements.py."""

import pytest
from unittest.mock import MagicMock

from pywinauto_mcp.tools.portmanteau_elements import _find_element


class TestFindElement:
    """Test the _find_element helper function."""

    def setup_method(self):
        self.window = MagicMock()
        self.window.child_window.return_value = MagicMock(name="found_element")

    def test_single_control_id(self):
        """Find by control_id only."""
        elem, desc = _find_element(self.window, control_id=123)
        self.window.child_window.assert_called_once_with(control_id=123)
        assert "control_id='123'" in desc

    def test_single_auto_id(self):
        """Find by auto_id only."""
        elem, desc = _find_element(self.window, auto_id="txtUsername")
        self.window.child_window.assert_called_once_with(auto_id="txtUsername")
        assert "auto_id='txtUsername'" in desc

    def test_single_title(self):
        """Find by title only."""
        elem, desc = _find_element(self.window, title="Login")
        self.window.child_window.assert_called_once_with(title="Login")
        assert "title='Login'" in desc

    def test_single_class_name(self):
        """Find by class_name only."""
        elem, desc = _find_element(self.window, class_name="TcxTextEdit")
        self.window.child_window.assert_called_once_with(class_name="TcxTextEdit")
        assert "class_name='TcxTextEdit'" in desc

    def test_single_control_type(self):
        """Find by control_type only."""
        elem, desc = _find_element(self.window, control_type="Edit")
        self.window.child_window.assert_called_once_with(control_type="Edit")
        assert "control_type='Edit'" in desc

    def test_multiple_selectors(self):
        """Find using multiple selectors at once."""
        elem, desc = _find_element(self.window, class_name="TcxTextEdit", control_type="Pane")
        self.window.child_window.assert_called_once_with(
            class_name="TcxTextEdit", control_type="Pane"
        )
        assert "class_name='TcxTextEdit'" in desc
        assert "control_type='Pane'" in desc

    def test_all_selectors(self):
        """Find using all selectors together."""
        elem, desc = _find_element(
            self.window,
            control_id=1,
            auto_id="aid",
            title="t",
            class_name="cls",
            control_type="ct",
        )
        self.window.child_window.assert_called_once_with(
            control_id=1, auto_id="aid", title="t", class_name="cls", control_type="ct"
        )
        assert "control_id='1'" in desc
        assert "auto_id='aid'" in desc
        assert "title='t'" in desc
        assert "class_name='cls'" in desc
        assert "control_type='ct'" in desc

    def test_no_selectors_raises(self):
        """Raises ValueError when no selectors are provided."""
        with pytest.raises(ValueError, match="At least one selector"):
            _find_element(self.window)

    def test_all_none_raises(self):
        """Raises ValueError when all selectors are None."""
        with pytest.raises(ValueError):
            _find_element(self.window, None, None, None, None, None)

    def test_returns_element_from_child_window(self):
        """Returned element is the result of child_window()."""
        expected = MagicMock(name="target_element")
        self.window.child_window.return_value = expected
        elem, desc = _find_element(self.window, title="Test")
        assert elem is expected

    def test_desc_is_comma_separated(self):
        """Description string is comma-separated for multiple selectors."""
        _, desc = _find_element(self.window, title="T", class_name="C")
        assert ", " in desc
        parts = desc.split(", ")
        assert len(parts) == 2
