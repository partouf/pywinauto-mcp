"""Batch tool — execute multiple element operations in one call.

Reduces round-trips for common workflows like filling forms.
Each step is executed sequentially; stops on first error.
"""

import ctypes
import logging
import time
from typing import Any

import pyautogui

# Import the FastMCP app instance
try:
    from pywinauto_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in automation_batch")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in automation_batch: {e}")
    app = None

from pywinauto_mcp.tools.portmanteau_elements import (  # noqa: E402
    _bridge_click,
    _bridge_find_controls,
    _get_bridge,
)


def _resolve_window_handle(window_title: str | None) -> int | None:
    """Resolve a window title to a handle, or return foreground window."""
    if window_title:
        from pywinauto import Desktop

        from pywinauto_mcp.config import settings

        desktop = Desktop(backend=settings.PYWINAUTO_BACKEND)
        for w in desktop.windows():
            try:
                if w.window_text().lower() == window_title.lower():
                    return w.handle
            except Exception:
                continue
    return ctypes.windll.user32.GetForegroundWindow()


if app is not None:
    logger.info("Registering automation_batch tool with FastMCP")

    @app.tool(
        name="automation_batch",
        description="""Execute multiple element operations in one call.

Reduces round-trips for form-filling and multi-step workflows.
Steps execute sequentially; stops on first error.

Each step is a dict with:
- op: "click", "set_text", or "wait"
- id: automation_id (component Name) for click/set_text
- title: caption text (alternative to id)
- text: value to type (for set_text)
- anchor: where to click within the control (default "center").
  Values: "center", "right", "left", "top", "bottom".
  Use "right" to click dropdown buttons on combo/edit controls.
- wait: seconds to pause after this step (default 0.1)

All steps share the same window context (window_title param)
and use active_form_only=True by default.

Examples:
    automation_batch(steps=[
        {"op": "set_text", "id": "TE_Username", "text": "admin"},
        {"op": "set_text", "id": "TE_Password", "text": "secret"},
        {"op": "click", "id": "Btn_Login"},
    ])

    # Click a dropdown button on the right edge of a combo
    automation_batch(steps=[
        {"op": "click", "id": "edType", "anchor": "right"},
    ])
""",
    )
    def automation_batch(
        steps: list[dict[str, Any]],
        window_title: str | None = None,
        active_form_only: bool = True,
    ) -> dict[str, Any]:
        """Execute a batch of element operations sequentially.

        Args:
            steps: List of operation dicts (op, id, title, text, wait).
            window_title: Parent window title. If omitted, uses
                the foreground window.
            active_form_only: Restrict bridge lookups to active form.

        """
        timestamp = time.time()
        bridge = _get_bridge()
        if bridge is None:
            return {
                "status": "error",
                "error": "Bridge not available.",
            }

        form_handle = _resolve_window_handle(window_title)
        if not form_handle:
            return {
                "status": "error",
                "error": f"Window '{window_title}' not found.",
            }

        results: list[dict[str, Any]] = []

        def _fail(step_index: int, step_dict: dict, error: str):
            return {
                "status": "error",
                "failed_step": step_index,
                "failed_command": step_dict,
                "error": error,
                "completed": results,
            }

        for i, step in enumerate(steps):
            op = step.get("op", "")
            auto_id = step.get("id")
            title = step.get("title")
            text = step.get("text")
            anchor = step.get("anchor", "center")
            wait = step.get("wait", 0.1)

            if not op:
                return _fail(i, step, "Missing 'op' in step")

            try:
                if op == "wait":
                    delay = step.get("wait", step.get("text", 0.5))
                    time.sleep(float(delay))
                    results.append({"op": "wait", "ok": True})
                    continue

                if not auto_id and not title:
                    return _fail(i, step, "Step needs 'id' or 'title'")

                ctrls = _bridge_find_controls(
                    bridge, auto_id, title,
                    active_form_only=active_form_only,
                )
                if not ctrls:
                    return _fail(
                        i, step,
                        f"Control not found: {auto_id or title}",
                    )

                ctrl = ctrls[0]

                if op == "click":
                    if _bridge_click(ctrl, form_handle, anchor=anchor):
                        results.append({
                            "op": "click",
                            "id": ctrl.get("name", ""),
                            "ok": True,
                        })
                    else:
                        return _fail(i, step, "Click failed")

                elif op == "set_text":
                    if text is None:
                        return _fail(
                            i, step, "Missing 'text' for set_text",
                        )
                    # Click to focus — goes through VCL's full
                    # focus pipeline unlike SetFocus API
                    if _bridge_click(ctrl, form_handle):
                        time.sleep(0.15)
                        pyautogui.hotkey("ctrl", "a")
                        pyautogui.press("delete")
                        if text.isascii():
                            pyautogui.typewrite(text, interval=0.02)
                        else:
                            pyautogui.write(text)
                        results.append({
                            "op": "set_text",
                            "id": ctrl.get("name", ""),
                            "ok": True,
                        })
                    else:
                        return _fail(i, step, "Click-to-focus failed")

                else:
                    return _fail(i, step, f"Unknown op: {op}")

            except Exception as e:
                return _fail(i, step, str(e))

            if wait:
                time.sleep(float(wait))

        return {
            "status": "success",
            "steps_completed": len(results),
            "results": results,
            "timestamp": timestamp,
        }


__all__ = ["automation_batch"]
