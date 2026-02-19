"""Tests for configuration loading and management."""

import os
import pytest
import tempfile
from unittest.mock import patch

from pywinauto_mcp.config import Settings


class TestSettings:
    """Test the Settings Pydantic model."""

    def test_default_values(self):
        """Verify default settings are applied correctly."""
        s = Settings()
        assert s.HOST == "0.0.0.0"
        assert s.PORT == 8000
        assert s.LOG_LEVEL == "INFO"
        assert s.DEBUG is False
        assert s.PYWINAUTO_BACKEND == "uia"
        assert s.TIMEOUT == 10.0
        assert s.RETRY_ATTEMPTS == 3
        assert s.RETRY_DELAY == 1.0
        assert s.SCREENSHOT_FORMAT == "png"
        assert s.TESSERACT_LANG == "eng"
        assert s.MCP_NAME == "pywinauto-mcp"

    def test_backend_override(self):
        """Verify PYWINAUTO_BACKEND can be overridden via env."""
        with patch.dict(os.environ, {"PYWINAUTO_BACKEND": "win32"}):
            s = Settings()
            assert s.PYWINAUTO_BACKEND == "win32"

    def test_port_override(self):
        """Verify PORT can be overridden via env."""
        with patch.dict(os.environ, {"PORT": "9000"}):
            s = Settings()
            assert s.PORT == 9000

    def test_screenshot_dir_created(self, tmp_path):
        """Verify screenshot directory is created by the validator."""
        new_dir = tmp_path / "screenshots_test"
        with patch.dict(os.environ, {"SCREENSHOT_DIR": str(new_dir)}):
            s = Settings()
            assert s.SCREENSHOT_DIR.exists()


class TestCoreConfig:
    """Test core/config.py - YAML config loading and merging."""

    def test_load_config_file_valid_yaml(self, tmp_path):
        """Load a valid YAML config file."""
        from pywinauto_mcp.core.config import load_config_file

        config_file = tmp_path / "config.yaml"
        config_file.write_text("log_level: DEBUG\nplugins:\n  ocr:\n    enabled: false\n")
        result = load_config_file(str(config_file))
        assert result["log_level"] == "DEBUG"
        assert result["plugins"]["ocr"]["enabled"] is False

    def test_load_config_file_empty_yaml(self, tmp_path):
        """Empty YAML returns empty dict."""
        from pywinauto_mcp.core.config import load_config_file

        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        result = load_config_file(str(config_file))
        assert result == {}

    def test_load_config_file_invalid_yaml(self, tmp_path):
        """Invalid YAML raises ValueError."""
        from pywinauto_mcp.core.config import load_config_file

        config_file = tmp_path / "bad.yaml"
        config_file.write_text(":\n  invalid: [yaml\n")
        with pytest.raises(ValueError, match="Invalid YAML"):
            load_config_file(str(config_file))

    def test_find_config_file_env_var(self, tmp_path):
        """find_config_file uses env var when set."""
        from pywinauto_mcp.core.config import find_config_file

        config_file = tmp_path / "config.yaml"
        config_file.write_text("log_level: DEBUG\n")
        with patch.dict(os.environ, {"PYWINAUTO_MCP_CONFIG": str(config_file)}):
            result = find_config_file()
            assert result == str(config_file)

    def test_find_config_file_missing(self):
        """find_config_file returns None when no config file exists."""
        from pywinauto_mcp.core.config import find_config_file

        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "pywinauto_mcp.core.config.DEFAULT_CONFIG_PATHS",
                ["/nonexistent/path/config.yaml"],
            ):
                result = find_config_file()
                assert result is None

    def test_get_config_defaults(self):
        """get_config returns defaults when no config file exists."""
        from pywinauto_mcp.core.config import get_config

        result = get_config(config_path="/nonexistent/config.yaml")
        assert result["log_level"] == "INFO"
        assert result["plugins"]["ocr"]["enabled"] is True

    def test_get_config_merges_file(self, tmp_path):
        """get_config merges file config with defaults."""
        from pywinauto_mcp.core.config import get_config

        config_file = tmp_path / "config.yaml"
        config_file.write_text("log_level: WARNING\ncustom_key: custom_value\n")
        result = get_config(config_path=str(config_file))
        assert result["log_level"] == "WARNING"
        assert result["custom_key"] == "custom_value"
        # Default plugin config should still be present
        assert "plugins" in result

    def test_get_config_env_override(self, tmp_path):
        """get_config applies PYWINAUTO_MCP_ env var overrides."""
        from pywinauto_mcp.core.config import get_config

        with patch.dict(os.environ, {"PYWINAUTO_MCP_LOG_LEVEL": "ERROR"}):
            result = get_config(config_path="/nonexistent/config.yaml")
            assert result["log"]["level"] == "ERROR"
