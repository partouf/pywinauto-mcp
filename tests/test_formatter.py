"""Tests for desktop_state/formatter.py - element formatting and reporting."""

import pytest

from pywinauto_mcp.desktop_state.formatter import DesktopStateFormatter


def _make_interactive(elem_id=0, elem_type="Button", name="OK", app="TestApp"):
    return {
        "id": elem_id,
        "type": elem_type,
        "name": name,
        "app": app,
        "bounds": {"x": 10, "y": 20, "width": 100, "height": 30},
        "is_visible": True,
        "is_enabled": True,
    }


def _make_informative(elem_id=0, elem_type="Text", name="Label", app="TestApp"):
    return {
        "id": elem_id,
        "type": elem_type,
        "name": name,
        "app": app,
        "bounds": {"x": 50, "y": 60, "width": 200, "height": 20},
        "is_visible": True,
        "is_enabled": True,
    }


class TestIsInteractive:
    """Test _is_interactive classification."""

    def setup_method(self):
        self.formatter = DesktopStateFormatter()

    def test_button_interactive(self):
        elem = _make_interactive(elem_type="Button")
        assert self.formatter._is_interactive(elem) is True

    def test_edit_interactive(self):
        elem = _make_interactive(elem_type="Edit")
        assert self.formatter._is_interactive(elem) is True

    def test_text_not_interactive(self):
        elem = _make_informative(elem_type="Text")
        assert self.formatter._is_interactive(elem) is False

    def test_checkbox_interactive(self):
        elem = _make_interactive(elem_type="CheckBox")
        assert self.formatter._is_interactive(elem) is True


class TestIsInformative:
    """Test _is_informative classification."""

    def setup_method(self):
        self.formatter = DesktopStateFormatter()

    def test_text_informative(self):
        elem = _make_informative(elem_type="Text")
        assert self.formatter._is_informative(elem) is True

    def test_statusbar_informative(self):
        elem = _make_informative(elem_type="StatusBar")
        assert self.formatter._is_informative(elem) is True

    def test_button_not_informative(self):
        elem = _make_interactive(elem_type="Button")
        assert self.formatter._is_informative(elem) is False


class TestBuildTextReport:
    """Test _build_text_report formatting."""

    def setup_method(self):
        self.formatter = DesktopStateFormatter()

    def test_interactive_section_header(self):
        report = self.formatter._build_text_report([], [])
        assert "Interactive Elements:" in report

    def test_informative_section_header(self):
        report = self.formatter._build_text_report([], [])
        assert "Informative Elements:" in report

    def test_interactive_element_in_report(self):
        btn = _make_interactive(elem_id=0, name="Submit", app="MyApp")
        report = self.formatter._build_text_report([btn], [])
        assert "[0]" in report
        assert "Button" in report
        assert "Submit" in report
        assert "MyApp" in report

    def test_informative_element_in_report(self):
        label = _make_informative(name="Status: Ready", app="MyApp")
        report = self.formatter._build_text_report([], [label])
        assert "Status: Ready" in report
        assert "MyApp" in report

    def test_coordinates_in_report(self):
        btn = _make_interactive(elem_id=1)
        report = self.formatter._build_text_report([btn], [])
        assert "(10,20)" in report

    def test_missing_name_uses_ocr_text(self):
        """When 'name' key is absent, ocr_text is used as fallback."""
        btn = _make_interactive()
        del btn["name"]
        btn["ocr_text"] = "OCR Result"
        report = self.formatter._build_text_report([btn], [])
        assert "OCR Result" in report

    def test_empty_informative_skipped(self):
        """Informative elements with no name are not included."""
        label = _make_informative(name="")
        report = self.formatter._build_text_report([], [label])
        lines = report.strip().split("\n")
        # Only headers and separator lines, no actual element lines
        informative_section = report.split("Informative Elements:")[1]
        assert informative_section.strip().startswith("-")


class TestFormat:
    """Test the format() method."""

    def setup_method(self):
        self.formatter = DesktopStateFormatter()

    def test_format_empty_elements(self):
        result = self.formatter.format([])
        assert result["element_count"] == 0
        assert result["interactive_elements"] == []
        assert result["informative_elements"] == []
        assert "text" in result

    def test_format_separates_types(self):
        elements = [
            _make_interactive(elem_id=0, elem_type="Button"),
            _make_informative(elem_id=1, elem_type="Text"),
        ]
        result = self.formatter.format(elements)
        assert result["element_count"] == 2
        assert len(result["interactive_elements"]) == 1
        assert len(result["informative_elements"]) == 1
        assert result["interactive_elements"][0]["type"] == "Button"
        assert result["informative_elements"][0]["type"] == "Text"

    def test_format_no_screenshot(self):
        result = self.formatter.format([])
        assert "screenshot_base64" not in result

    def test_format_mixed_elements(self):
        """Pane elements are neither interactive nor informative."""
        elements = [
            _make_interactive(elem_type="Button"),
            _make_informative(elem_type="Text"),
            {
                "type": "Pane",
                "name": "Container",
                "app": "App",
                "bounds": {"x": 0, "y": 0, "width": 100, "height": 100},
                "is_visible": True,
                "is_enabled": True,
            },
        ]
        result = self.formatter.format(elements)
        assert result["element_count"] == 3
        # Pane is neither interactive nor informative
        assert len(result["interactive_elements"]) == 1
        assert len(result["informative_elements"]) == 1
