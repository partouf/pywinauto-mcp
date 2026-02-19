"""Basic smoke tests for pywinauto-mcp."""

import importlib


def test_config_loads():
    """Verify the config module can be imported and settings instantiated."""
    from pywinauto_mcp.config import Settings

    s = Settings()
    assert s.PYWINAUTO_BACKEND in ("uia", "win32")
    assert s.TIMEOUT > 0


def test_app_module_importable():
    """Verify the app module can be imported."""
    mod = importlib.import_module("pywinauto_mcp.app")
    assert hasattr(mod, "app")


def test_main_module_importable():
    """Verify the main module can be imported."""
    mod = importlib.import_module("pywinauto_mcp.main")
    assert hasattr(mod, "main")
