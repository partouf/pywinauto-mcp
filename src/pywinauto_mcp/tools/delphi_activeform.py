"""Delphi active form tool — lists controls on the currently active form.

Uses the DelphiUITestExposer bridge's /activeform/controls endpoint to return
ALL controls (including non-windowed VCL controls) on whichever form currently
has focus. No window handle needed.

Also detects native Win32 dialogs (MessageBox/TaskDialog) that the bridge
cannot see, and reports them with their button labels.
"""

import ctypes
import logging
import time
from typing import Any

import win32gui
import win32process

# Import the FastMCP app instance
try:
    from pywinauto_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in delphi_activeform")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in delphi_activeform: {e}")
    app = None

# Re-use the bridge singleton from portmanteau_elements
from pywinauto_mcp.tools.portmanteau_elements import (  # noqa: E402
    _get_bridge,
)

# Classes that are internal child parts of composite controls — never useful
_INNER_CLASSES = frozenset({
    "TcxCustomDropDownInnerEdit",
    "TDBrosGridFieldEditor",
    "TcxCustomRadioGroupButton",
})

# Read-only label classes
_LABEL_CLASSES = frozenset({
    "TLabel",
    "TcxLabel",
})

# Pure layout/container classes (no interaction value)
_CONTAINER_CLASSES = frozenset({
    "TPanel",
    "TcxScrollBox",
    "TShape",
    "TPageControl",
    "TScrollBox",
})


def _flatten_controls(
    nodes: list[dict],
    *,
    include_hidden: bool = False,
    include_labels: bool = False,
    include_containers: bool = False,
) -> list[dict]:
    """Flatten a nested control tree into a compact list.

    Only includes fields useful for targeting: automation_id, class_name, text.
    Applies aggressive filtering by default to keep output small:
    - Skips controls with no automation_id (untargetable)
    - Skips inner child parts of composite controls
    - Skips read-only labels (unless *include_labels*)
    - Skips layout containers (unless *include_containers*)
    - Skips invisible controls (unless *include_hidden*)
    """
    result: list[dict] = []

    def _walk(items: list[dict]) -> None:
        for node in items:
            children = node.get("children", [])
            visible = node.get("visible", True)
            if not visible and not include_hidden:
                _walk(children)
                continue

            name = node.get("name", "")
            cls = node.get("className", "")

            # Always skip inner parts of composite controls
            if cls in _INNER_CLASSES:
                continue

            # Must have an automation_id to be targetable
            if name:
                skip = False
                if cls in _LABEL_CLASSES and not include_labels:
                    skip = True
                if cls in _CONTAINER_CLASSES and not include_containers:
                    skip = True

                if not skip:
                    text = node.get("text", "")
                    entry: dict[str, Any] = {
                        "automation_id": name,
                        "class_name": cls,
                    }
                    if text and text != name:
                        entry["text"] = text[:80]
                    if not visible:
                        entry["visible"] = False
                    if not node.get("enabled", True):
                        entry["enabled"] = False
                    result.append(entry)

            _walk(children)

    _walk(items=nodes)
    return result


# Child control classes worth reporting in native dialogs
_DIALOG_CHILD_CLASSES = frozenset({
    "Button",       # OK, Cancel, Yes, No, Save, Open, Browse...
    "Edit",         # Filename input, search box
    "ComboBox",     # File type filter, encoding selector
    "ComboBoxEx32", # Extended combo (filename in Open/Save)
    "Static",       # Message text, labels
    "CheckBox",     # Options like "Read-only"
})


def _detect_native_dialogs() -> list[dict[str, Any]]:
    """Find native Win32 dialogs (#32770) owned by the foreground app.

    These are MessageBox, TaskDialog, Open/Save dialogs, etc. that the
    Delphi bridge cannot see. Returns a list of dicts with handle, title,
    child controls (buttons, inputs, combos, static text), and rect.
    """
    fg = ctypes.windll.user32.GetForegroundWindow()
    if not fg:
        return []

    _, fg_pid = win32process.GetWindowThreadProcessId(fg)

    dialogs: list[dict[str, Any]] = []

    def _enum_callback(hwnd: int, _: Any) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        if win32gui.GetClassName(hwnd) != "#32770":
            return True
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid != fg_pid:
            return True

        controls: list[dict[str, Any]] = []

        def _enum_children(child: int, __: Any) -> bool:
            cls = win32gui.GetClassName(child)
            if cls not in _DIALOG_CHILD_CLASSES:
                return True
            if not win32gui.IsWindowVisible(child):
                return True
            txt = win32gui.GetWindowText(child)
            entry: dict[str, Any] = {
                "class": cls,
                "handle": child,
            }
            if txt:
                entry["text"] = txt[:120]
            ctrl_id = win32gui.GetDlgCtrlID(child)
            if ctrl_id:
                entry["id"] = ctrl_id
            controls.append(entry)
            return True

        win32gui.EnumChildWindows(hwnd, _enum_children, None)

        rect = win32gui.GetWindowRect(hwnd)
        dialogs.append({
            "handle": hwnd,
            "title": win32gui.GetWindowText(hwnd),
            "class": "#32770",
            "controls": controls,
            "rect": {
                "left": rect[0], "top": rect[1],
                "right": rect[2], "bottom": rect[3],
            },
        })
        return True

    win32gui.EnumWindows(_enum_callback, None)
    return dialogs


if app is not None:
    logger.info("Registering delphi_activeform tool with FastMCP")

    @app.tool(
        name="delphi_activeform",
        description="""List interactive controls on the active Delphi form.

Requires the DelphiUITestExposer bridge. No window handle needed.

Returns ONLY actionable controls by default (buttons, inputs, grids,
tabs, checkboxes, radio groups). Filters out labels, layout containers,
and inner parts of composite controls to keep output compact.

Also detects native Win32 dialogs (MessageBox/TaskDialog) that the
bridge cannot see. If present, they appear in "native_dialogs" with
button handles — dismiss them first before interacting with VCL controls.

Each entry has:
- automation_id: Delphi component Name (use with auto_id= in other tools)
- class_name: VCL class (e.g. "TcxTextEdit", "TButton")
- text: Caption (only if different from automation_id)

Options to include more:
- include_labels=True: Add TLabel/TcxLabel (read-only text)
- include_containers=True: Add TPanel/TScrollBox etc.
- include_hidden=True: Add invisible controls

Examples:
    delphi_activeform()
    delphi_activeform(include_labels=True)
""",
    )
    def delphi_activeform(
        include_hidden: bool = False,
        include_labels: bool = False,
        include_containers: bool = False,
    ) -> dict[str, Any]:
        """List controls on the currently active Delphi form.

        Args:
            include_hidden: Include invisible controls.
            include_labels: Include read-only labels (TLabel, TcxLabel).
            include_containers: Include layout containers (TPanel, etc.).

        """
        timestamp = time.time()
        bridge = _get_bridge()
        if bridge is None:
            return {
                "status": "error",
                "error": "Delphi bridge not available. "
                "Ensure the target app has DelphiUITestExposer enabled.",
            }

        try:
            # Check for native Win32 dialogs first — they block the VCL UI
            native_dialogs = _detect_native_dialogs()

            raw = bridge.get_activeform_controls()
            controls = _flatten_controls(
                raw,
                include_hidden=include_hidden,
                include_labels=include_labels,
                include_containers=include_containers,
            )
            result: dict[str, Any] = {
                "status": "success",
                "count": len(controls),
                "controls": controls,
                "timestamp": timestamp,
            }
            if native_dialogs:
                result["native_dialogs"] = native_dialogs
                result["warning"] = (
                    "Native Win32 dialog(s) detected — these block the "
                    "Delphi UI. Dismiss them first using automation_elements "
                    "click with the button handle, or automation_mouse click."
                )
            return result
        except Exception as e:
            return {
                "status": "error",
                "error": f"Bridge request failed: {e}",
            }


__all__ = ["delphi_activeform"]
