"""UI Element interaction portmanteau tool for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Instead of creating 15+ separate tools (one per element operation), this tool consolidates related
element interaction operations into a single interface. This design:
- Prevents tool explosion (15+ tools → 1 tool) while maintaining full functionality
- Improves discoverability by grouping related operations together
- Reduces cognitive load when working with element automation tasks
- Enables atomic batch operations across multiple element actions
- Follows FastMCP 2.13+ best practices for feature-rich MCP servers

SUPPORTED OPERATIONS:
- click: Click on a UI element
- double_click: Double-click on a UI element
- right_click: Right-click on a UI element
- hover: Hover over a UI element
- info: Get detailed information about a UI element
- text: Get text content of a UI element
- set_text: Set text content of a UI element
- rect: Get position and size of a UI element
- visible: Check if element is visible
- enabled: Check if element is enabled
- exists: Check if element exists
- wait: Wait for element to appear
- verify_text: Verify element contains expected text
- list: Get all elements in a window
"""

import ctypes
import logging
import time
from typing import Any, Literal

from pywinauto import Desktop
from pywinauto.base_wrapper import ElementNotVisible
from pywinauto.findwindows import ElementNotFoundError

try:
    from pywinauto.controls.uia_controls import ButtonWrapper, ComboBoxWrapper, EditWrapper
except ImportError:
    ButtonWrapper = EditWrapper = ComboBoxWrapper = None

import pyautogui

from pywinauto_mcp.config import settings
from pywinauto_mcp.delphi_bridge import DelphiBridge

# Import the FastMCP app instance
try:
    from pywinauto_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in portmanteau_elements")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in portmanteau_elements: {e}")
    app = None

# Lazy-initialized Delphi bridge singleton
_bridge: DelphiBridge | None = None
_bridge_attempted: bool = False


def _get_bridge() -> DelphiBridge | None:
    """Get or discover the Delphi bridge (lazy singleton)."""
    global _bridge, _bridge_attempted
    if _bridge is not None and _bridge.connected:
        return _bridge
    if _bridge_attempted:
        return _bridge
    _bridge_attempted = True
    _bridge = DelphiBridge()
    if _bridge.discover():
        logger.info(f"Delphi bridge connected at {_bridge.base_url}")
    else:
        logger.info("Delphi bridge not available, using Win32 only")
        _bridge = None
    return _bridge


def _get_desktop():
    """Get a Desktop instance with proper error handling."""
    try:
        return Desktop(backend=settings.PYWINAUTO_BACKEND)
    except Exception as e:
        logger.error(f"Failed to get Desktop instance: {e}")
        raise


def _bridge_control_to_element_info(ctrl: dict) -> dict:
    """Convert a Delphi bridge control dict to our element info format."""
    return {
        "handle": ctrl.get("handle", 0),
        "class_name": ctrl.get("className", ""),
        "automation_id": ctrl.get("name", ""),
        "text": ctrl.get("text", ""),
        "name": ctrl.get("text", ""),
        "x": ctrl.get("left", 0),
        "y": ctrl.get("top", 0),
        "width": ctrl.get("width", 0),
        "height": ctrl.get("height", 0),
        "is_visible": ctrl.get("visible", True),
        "is_enabled": ctrl.get("enabled", True),
        "parent_handle": ctrl.get("parentHandle", 0),
        "children": [_bridge_control_to_element_info(c) for c in ctrl.get("children", [])],
    }


def _bridge_find_controls(
    bridge: DelphiBridge,
    auto_id: str | None = None,
    title: str | None = None,
    *,
    active_form_only: bool = False,
) -> list[dict]:
    """Find controls via bridge, optionally restricted to the active form.

    When *active_form_only* is True, fetches the active form's control tree
    and searches within it — avoiding cross-form name collisions.
    Otherwise delegates to the global /controls endpoint.
    """
    if not active_form_only:
        params: dict[str, str] = {}
        if auto_id:
            params["name"] = auto_id
        if title:
            params["caption"] = title
        return bridge.get_controls(**params)

    # Active-form path: flatten the tree and filter locally
    tree = bridge.get_activeform_controls()
    matches: list[dict] = []

    def _walk(nodes: list[dict]) -> None:
        for node in nodes:
            match = True
            if auto_id and node.get("name", "") != auto_id:
                match = False
            if title and node.get("text", "") != title:
                match = False
            if match:
                matches.append(node)
            _walk(node.get("children", []))

    _walk(tree)
    return matches


def _bridge_click(
    ctrl: dict,
    form_handle: int,
    button: str = "left",
    anchor: str = "center",
) -> bool:
    """Click a control found via the Delphi bridge.

    Uses physical mouse input (pyautogui) at screen coordinates.
    For windowed controls, uses GetWindowRect for exact position.
    For non-windowed controls, falls back to form client-area offset.

    *anchor* controls where within the control to click:
      center (default), left, right, top, bottom.
    Useful for clicking dropdown buttons on the right edge of combos.
    """
    try:
        import win32gui

        ctypes.windll.user32.SetForegroundWindow(form_handle)
        time.sleep(0.05)

        handle = ctrl.get("handle", 0)
        if handle:
            r = win32gui.GetWindowRect(handle)
            left, top, right, bottom = r
        else:
            client_origin = win32gui.ClientToScreen(form_handle, (0, 0))
            left = client_origin[0] + ctrl["left"]
            top = client_origin[1] + ctrl["top"]
            right = left + ctrl["width"]
            bottom = top + ctrl["height"]

        # Compute click point based on anchor
        edge_inset = 10
        if anchor == "right":
            click_x = right - edge_inset
            click_y = (top + bottom) // 2
        elif anchor == "left":
            click_x = left + edge_inset
            click_y = (top + bottom) // 2
        elif anchor == "top":
            click_x = (left + right) // 2
            click_y = top + edge_inset
        elif anchor == "bottom":
            click_x = (left + right) // 2
            click_y = bottom - edge_inset
        else:  # center
            click_x = (left + right) // 2
            click_y = (top + bottom) // 2

        logger.info(
            f"Bridge click at screen ({click_x}, {click_y}) "
            f"anchor={anchor} for '{ctrl.get('name', '')}'"
        )
        pyautogui.click(click_x, click_y, button=button)
        return True
    except Exception as e:
        logger.warning(f"Bridge coordinate click failed: {e}")
        return False



def _bridge_set_focus(ctrl: dict, form_handle: int) -> bool:
    """Set keyboard focus to a control found via the Delphi bridge.

    For windowed controls (handle != 0): uses Win32 SetFocus via
    AttachThreadInput so it works cross-process.
    For non-windowed controls: falls back to a physical click.
    """
    import win32gui
    import win32process

    # Bring the form to the foreground
    ctypes.windll.user32.SetForegroundWindow(form_handle)
    time.sleep(0.05)

    handle = ctrl.get("handle", 0)
    if handle:
        # Windowed control — attach threads and SetFocus
        try:
            current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
            target_tid = win32process.GetWindowThreadProcessId(handle)[0]
            attached = False
            if current_tid != target_tid:
                attached = bool(
                    ctypes.windll.user32.AttachThreadInput(
                        current_tid, target_tid, True
                    )
                )
            try:
                ctypes.windll.user32.SetFocus(handle)
                logger.info(
                    f"SetFocus on handle {handle} "
                    f"for '{ctrl.get('name', '')}'"
                )
                return True
            finally:
                if attached:
                    ctypes.windll.user32.AttachThreadInput(
                        current_tid, target_tid, False
                    )
        except Exception as e:
            logger.debug(f"SetFocus failed for {handle}: {e}")

    # Non-windowed — click at coordinates to focus
    try:
        client_origin = win32gui.ClientToScreen(form_handle, (0, 0))
        click_x = client_origin[0] + ctrl["left"] + ctrl["width"] // 2
        click_y = client_origin[1] + ctrl["top"] + ctrl["height"] // 2
        logger.info(
            f"Focus via click at ({click_x}, {click_y}) "
            f"for '{ctrl.get('name', '')}'"
        )
        pyautogui.click(click_x, click_y)
        return True
    except Exception as e:
        logger.warning(f"Focus via click failed: {e}")
        return False


def _get_element_info(element) -> dict[str, Any]:
    """Extract relevant information from a UI element."""
    info = {}
    try:
        info = {
            "class_name": element.class_name(),
            "text": element.window_text(),
            "control_id": element.control_id() if hasattr(element, "control_id") else None,
            "process_id": element.process_id(),
            "is_visible": element.is_visible(),
            "is_enabled": element.is_enabled(),
            "handle": element.handle,
        }

        if hasattr(element, "automation_id"):
            info["automation_id"] = element.automation_id()

        if hasattr(element, "element_info"):
            info["name"] = element.element_info.name
            info["control_type"] = str(element.element_info.control_type)

        try:
            rect = element.rectangle()
            info["rect"] = {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.width(),
                "height": rect.height(),
            }
            info["x"] = rect.left
            info["y"] = rect.top
            info["width"] = rect.width()
            info["height"] = rect.height()
        except Exception as e:
            logger.debug(f"Could not get rectangle for element: {e}")  # Changed bare except

        # Element type detection
        if ButtonWrapper and isinstance(element, ButtonWrapper):
            info["element_type"] = "button"
        elif EditWrapper and isinstance(element, EditWrapper):
            info["element_type"] = "edit"
            try:
                info["is_readonly"] = element.is_read_only()
            except Exception as e:  # Changed bare except
                logger.debug(f"Could not get is_read_only for edit element: {e}")
        elif ComboBoxWrapper and isinstance(element, ComboBoxWrapper):
            info["element_type"] = "combobox"
            try:
                info["items"] = element.item_texts()
                info["selected_index"] = element.selected_index()
                info["selected_text"] = element.selected_text()
            except Exception as e:  # Changed bare except
                logger.debug(f"Could not get combobox info: {e}")

    except Exception as e:
        logger.warning(f"Error getting element info: {e}")

    return info


def _find_element(
    window, control_id=None, auto_id=None, title=None, class_name=None, control_type=None
):
    """Find a child element using any combination of available selectors.

    Builds a selector dict from whichever parameters are provided and passes
    them to pywinauto's child_window().  Returns (element, selector_desc) where
    selector_desc is a human-readable string describing the criteria used.
    Raises ValueError when no selector is given.
    """
    kwargs = {}
    parts = []
    if control_id is not None:
        kwargs["control_id"] = control_id
        parts.append(f"control_id='{control_id}'")
    if auto_id is not None:
        kwargs["auto_id"] = auto_id
        parts.append(f"auto_id='{auto_id}'")
    if title is not None:
        kwargs["title"] = title
        parts.append(f"title='{title}'")
    if class_name is not None:
        kwargs["class_name"] = class_name
        parts.append(f"class_name='{class_name}'")
    if control_type is not None:
        kwargs["control_type"] = control_type
        parts.append(f"control_type='{control_type}'")
    if not kwargs:
        raise ValueError(
            "At least one selector (control_id, auto_id, title,"
            " class_name, control_type) is required"
        )
    return window.child_window(**kwargs), ", ".join(parts)


if app is not None:
    logger.info("Registering portmanteau_elements tool with FastMCP")

    @app.tool(
        name="automation_elements",
        description="""Comprehensive UI element interaction tool for Windows automation.

WINDOW SELECTION:
Specify the parent window using EITHER:
- window_handle: Direct HWND integer (precise, no lookup needed)
- window_title: Window title text (exact match, case-insensitive)

Using window_title lets you skip the window discovery step entirely.

ELEMENT SELECTION:
Elements can be targeted using any combination of these selectors:
- auto_id: Delphi component Name (e.g., "TE_Username", "Btn_Login") — PREFERRED for Delphi apps.
  Use "list" to discover available automation_id values.
- title: Element caption/text (human-readable label)
- control_id: Win32 or symbolic control identifier
- class_name: Windows/VCL class name (e.g., "TcxTextEdit", "TButton")
- control_type: UI role (e.g., "Button", "Edit", "ComboBox")

You can combine selectors to narrow matches (e.g., auto_id="TE_Username").
The Delphi bridge discovers ALL controls including non-windowed ones (TSpeedButton,
TcxButton, etc.) that Win32 API cannot see.

SUPPORTED OPERATIONS:
- click: Click on element (by selector or coordinates)
- double_click: Double-click on element
- right_click: Right-click on element
- hover: Hover over element for specified duration
- info: Get detailed element information
- text: Get element text content
- set_text: Input a string value into an editable field
- rect: Get element position and size
- visible: Check if element is visible
- enabled: Check if element is enabled
- exists: Check if element exists (with timeout)
- wait: Wait for element to appear (with timeout)
- verify_text: Verify element contains expected text
- list: Get all elements in window (with depth control)

ACTIVE FORM SCOPE:
active_form_only defaults to True — bridge lookups are restricted to the
currently active form to avoid cross-form name collisions. Set False only
when you need to target a control on a non-active form.

Examples:
    # List elements to discover automation_id values
    automation_elements("list", window_title="Login")

    # Fill a Delphi form (active_form_only=True is the default)
    automation_elements("set_text", auto_id="TE_Username", text="admin")
    automation_elements("set_text", auto_id="TE_Password", text="secret")
    automation_elements("click", auto_id="Btn_Login")

    # Click by caption text
    automation_elements("click", window_title="Login", title="Login")

    # List all elements (for discovery when selectors are unknown)
    automation_elements("list", window_title="MyApp")

""",
    )
    def automation_elements(
        operation: Literal[
            "click",
            "double_click",
            "right_click",
            "hover",
            "info",
            "text",
            "set_text",
            "rect",
            "visible",
            "enabled",
            "exists",
            "wait",
            "verify_text",
            "list",
        ],
        window_handle: int | None = None,
        window_title: str | None = None,
        control_id: str | int | None = None,
        auto_id: str | None = None,
        title: str | None = None,
        control_type: str | None = None,
        class_name: str | None = None,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
        anchor: str = "center",
        absolute: bool = False,
        duration: float = 0.5,
        text: str | None = None,
        expected_text: str | None = None,
        exact_match: bool = True,
        timeout: float = 5.0,
        max_depth: int = 3,
        active_form_only: bool = True,
    ) -> dict[str, Any]:
        """Comprehensive UI element interaction operations for Windows automation.

        Args:
            operation (str, required): The element interaction to perform.
            window_handle (int | None): Parent window identifier (HWND).
            window_title (str | None): Parent window title (exact, case-insensitive).
                Use this instead of window_handle to skip the window discovery step.
            control_id (str | int | None): Win32 or symbolic control identifier.
            auto_id (str | None): AutomationID / Delphi component Name.
            title (str | None): Plaintext title or name of the target element.
            control_type (str | None): The expected UI role (e.g., Button, Edit).
            class_name (str | None): Windows class name for precise targeting.
            x (int | None): Horizontal offset for relative coordinate operations.
            y (int | None): Vertical offset for relative coordinate operations.
            button (str): Mouse button for clicks (left, right, middle, default left).
            anchor (str): Where to click within the control: center (default),
                right, left, top, bottom. Use "right" for dropdown buttons.
            absolute (bool): Toggles between element-relative and screen-absolute coordinates.
            duration (float): Time in seconds to complete a mouse movement or hover.
            text (str | None): The string value to input for set_text operations.
            expected_text (str | None): Reference string for verify_text operations.
            exact_match (bool): Toggles between strict and partial string matching.
            timeout (float): Maximum seconds to wait for an element to become ready.
            max_depth (int): Recursion limit for child element discovery.
            active_form_only (bool): Restrict Delphi bridge lookups to the
                currently active form. Default True to avoid cross-form name
                collisions. Set False to search all forms.

        Returns:
            dict[str, Any]: Operation-specific result dictionary with element status.

        """
        try:
            timestamp = time.time()
            logger.info(
                f"automation_elements('{operation}', "
                f"window_handle={window_handle}, window_title={window_title}, "
                f"control_id={control_id}, auto_id={auto_id}, title={title}, "
                f"class_name={class_name}, control_type={control_type})"
            )
            desktop = _get_desktop()

            # === RESOLVE WINDOW: by handle or by title ===
            if window_handle is None and window_title is not None:
                for w in desktop.windows():
                    try:
                        if w.window_text().lower() == window_title.lower():
                            window_handle = w.handle
                            break
                    except Exception:
                        continue
                if window_handle is None:
                    return {
                        "status": "error",
                        "operation": operation,
                        "error": f"No window found with title '{window_title}'",
                    }

            # === LIST OPERATION (doesn't require control_id) ===
            if operation == "list":
                if window_handle is None:
                    return {
                        "status": "error",
                        "operation": "list",
                        "error": "window_handle or window_title parameter is required",
                    }

                # Prefer Delphi bridge — sees all controls including non-windowed
                bridge = _get_bridge()
                if bridge is not None:
                    try:
                        raw = bridge.get_form_controls(window_handle)
                        elements = [_bridge_control_to_element_info(c) for c in raw]
                        return {
                            "status": "success",
                            "operation": "list",
                            "source": "delphi_bridge",
                            "window_handle": window_handle,
                            "element_count": len(elements),
                            "elements": elements,
                            "timestamp": timestamp,
                        }
                    except Exception as e:
                        logger.debug(f"Bridge list failed, falling back to Win32: {e}")

                # Fallback: Win32 enumeration
                window = desktop.window(handle=window_handle)
                if not window.exists():
                    return {
                        "status": "error",
                        "operation": "list",
                        "error": f"Window with handle {window_handle} not found",
                    }

                def get_children_recursive(elem, depth=0):
                    if depth > max_depth:
                        return []

                    elements = []
                    try:
                        for child in elem.children():
                            elem_info = _get_element_info(child)
                            elem_info["children"] = get_children_recursive(child, depth + 1)
                            elements.append(elem_info)
                    except Exception as e:
                        logger.warning(f"Error getting children: {e}")

                    return elements

                elements = get_children_recursive(window)
                return {
                    "status": "success",
                    "operation": "list",
                    "source": "win32",
                    "window_handle": window_handle,
                    "element_count": len(elements),
                    "elements": elements,
                    "max_depth": max_depth,
                    "timestamp": timestamp,
                }

            # === VALIDATION FOR OPERATIONS REQUIRING WINDOW ===
            if window_handle is None:
                return {
                    "status": "error",
                    "operation": operation,
                    "error": "window_handle or window_title parameter is required",
                }

            window = desktop.window(handle=window_handle)

            # === OPERATIONS WITH CONTROL_ID OR COORDINATES ===

            # === CLICK OPERATION ===
            if operation == "click":
                # Try Delphi bridge first for auto_id or title
                bridge = _get_bridge()
                if bridge is not None and (auto_id or title):
                    try:
                        results = _bridge_find_controls(
                            bridge, auto_id, title,
                            active_form_only=active_form_only,
                        )
                        if results:
                            ctrl = results[0]
                            if _bridge_click(
                                ctrl, window_handle, button,
                                anchor=anchor,
                            ):
                                return {
                                    "status": "success",
                                    "operation": "click",
                                    "source": "delphi_bridge",
                                    "automation_id": ctrl.get("name", ""),
                                    "text": ctrl.get("text", ""),
                                    "button": button,
                                    "anchor": anchor,
                                    "timestamp": timestamp,
                                }
                    except Exception as e:
                        logger.debug(f"Bridge click failed: {e}")

                has_selector = any(
                    v is not None for v in [control_id, auto_id, title, class_name, control_type]
                )
                if has_selector:
                    element, desc = _find_element(
                        window, control_id, auto_id, title, class_name, control_type
                    )
                    if not element.exists():
                        return {
                            "status": "error",
                            "operation": "click",
                            "error": f"Element with {desc} not found",
                        }
                    element.click(button=button)
                    return {
                        "status": "success",
                        "operation": "click",
                        "selector": desc,
                        "button": button,
                        "timestamp": timestamp,
                    }
                elif x is not None and y is not None:
                    if absolute:
                        pyautogui.click(x, y, button=button)
                    else:
                        rect = window.rectangle()
                        pyautogui.click(rect.left + x, rect.top + y, button=button)
                    return {
                        "status": "success",
                        "operation": "click",
                        "x": x,
                        "y": y,
                        "absolute": absolute,
                        "button": button,
                        "timestamp": timestamp,
                    }
                else:
                    return {
                        "status": "error",
                        "operation": "click",
                        "error": "A selector (control_id/auto_id/title/class_name/control_type)"
                        " or both x and y must be provided",
                    }

            # === DOUBLE_CLICK OPERATION ===
            elif operation == "double_click":
                has_selector = any(
                    v is not None for v in [control_id, auto_id, title, class_name, control_type]
                )
                if has_selector:
                    element, desc = _find_element(
                        window, control_id, auto_id, title, class_name, control_type
                    )
                    if not element.exists():
                        return {
                            "status": "error",
                            "operation": "double_click",
                            "error": f"Element with {desc} not found",
                        }
                    element.double_click(button=button)
                    return {
                        "status": "success",
                        "operation": "double_click",
                        "selector": desc,
                        "button": button,
                        "timestamp": timestamp,
                    }
                elif x is not None and y is not None:
                    if absolute:
                        pyautogui.doubleClick(x, y, button=button)
                    else:
                        rect = window.rectangle()
                        pyautogui.doubleClick(rect.left + x, rect.top + y, button=button)
                    return {
                        "status": "success",
                        "operation": "double_click",
                        "x": x,
                        "y": y,
                        "absolute": absolute,
                        "button": button,
                        "timestamp": timestamp,
                    }
                else:
                    return {
                        "status": "error",
                        "operation": "double_click",
                        "error": "A selector (control_id/auto_id/title/class_name/control_type)"
                        " or both x and y must be provided",
                    }

            # === RIGHT_CLICK OPERATION ===
            elif operation == "right_click":
                has_selector = any(
                    v is not None for v in [control_id, auto_id, title, class_name, control_type]
                )
                if has_selector:
                    element, desc = _find_element(
                        window, control_id, auto_id, title, class_name, control_type
                    )
                    if not element.exists():
                        return {
                            "status": "error",
                            "operation": "right_click",
                            "error": f"Element with {desc} not found",
                        }
                    element.click(button="right")
                    return {
                        "status": "success",
                        "operation": "right_click",
                        "selector": desc,
                        "timestamp": timestamp,
                    }
                elif x is not None and y is not None:
                    if absolute:
                        pyautogui.rightClick(x, y)
                    else:
                        rect = window.rectangle()
                        pyautogui.rightClick(rect.left + x, rect.top + y)
                    return {
                        "status": "success",
                        "operation": "right_click",
                        "x": x,
                        "y": y,
                        "absolute": absolute,
                        "timestamp": timestamp,
                    }
                else:
                    return {
                        "status": "error",
                        "operation": "right_click",
                        "error": "A selector (control_id/auto_id/title/class_name/control_type)"
                        " or both x and y must be provided",
                    }

            # === HOVER OPERATION ===
            elif operation == "hover":
                has_selector = any(
                    v is not None for v in [control_id, auto_id, title, class_name, control_type]
                )
                if has_selector:
                    element, desc = _find_element(
                        window, control_id, auto_id, title, class_name, control_type
                    )
                    if not element.exists():
                        return {
                            "status": "error",
                            "operation": "hover",
                            "error": f"Element with {desc} not found",
                        }
                    rect = element.rectangle()
                    center_x = rect.left + (rect.width() // 2)
                    center_y = rect.top + (rect.height() // 2)
                    pyautogui.moveTo(center_x, center_y, duration=0.3)
                    time.sleep(duration)
                    return {
                        "status": "success",
                        "operation": "hover",
                        "selector": desc,
                        "position": (center_x, center_y),
                        "duration": duration,
                        "timestamp": timestamp,
                    }
                elif x is not None and y is not None:
                    if not absolute:
                        rect = window.rectangle()
                        x = rect.left + x
                        y = rect.top + y
                    pyautogui.moveTo(x, y, duration=0.3)
                    time.sleep(duration)
                    return {
                        "status": "success",
                        "operation": "hover",
                        "position": (x, y),
                        "duration": duration,
                        "timestamp": timestamp,
                    }
                else:
                    return {
                        "status": "error",
                        "operation": "hover",
                        "error": "A selector (control_id/auto_id/title/class_name/control_type)"
                        " or both x and y must be provided",
                    }

            # === OPERATIONS REQUIRING AN ELEMENT SELECTOR ===
            has_selector = any(
                v is not None for v in [control_id, auto_id, title, class_name, control_type]
            )
            if not has_selector:
                return {
                    "status": "error",
                    "operation": operation,
                    "error": (
                        f"At least one selector (control_id, auto_id, title,"
                        f" class_name, control_type) is required for {operation}"
                    ),
                }

            element, selector_desc = _find_element(
                window, control_id, auto_id, title, class_name, control_type
            )

            # === INFO OPERATION ===
            if operation == "info":
                if not element.exists():
                    return {
                        "status": "error",
                        "operation": "info",
                        "error": f"Element with {selector_desc} not found",
                    }
                info = _get_element_info(element)
                info["status"] = "success"
                info["operation"] = "info"
                info["timestamp"] = timestamp
                return info

            # === TEXT OPERATION ===
            elif operation == "text":
                if not element.exists():
                    return {
                        "status": "error",
                        "operation": "text",
                        "error": f"Element with {selector_desc} not found",
                    }
                return {
                    "status": "success",
                    "operation": "text",
                    "selector": selector_desc,
                    "text": element.window_text(),
                    "timestamp": timestamp,
                }

            # === SET_TEXT OPERATION ===
            elif operation == "set_text":
                if text is None:
                    return {
                        "status": "error",
                        "operation": "set_text",
                        "error": "text parameter is required for set_text operation",
                    }

                # Try Delphi bridge first for auto_id or title
                bridge = _get_bridge()
                if bridge is not None and (auto_id or title):
                    try:
                        results = _bridge_find_controls(
                            bridge, auto_id, title,
                            active_form_only=active_form_only,
                        )
                        if results:
                            ctrl = results[0]
                            # Click the control to focus it — physical
                            # click goes through VCL's full focus pipeline
                            # which SetFocus alone does not.
                            if _bridge_click(ctrl, window_handle):
                                time.sleep(0.15)
                                pyautogui.hotkey("ctrl", "a")
                                pyautogui.press("delete")
                                if text.isascii():
                                    pyautogui.typewrite(
                                        text, interval=0.02
                                    )
                                else:
                                    pyautogui.write(text)
                                return {
                                    "status": "success",
                                    "operation": "set_text",
                                    "source": "delphi_bridge",
                                    "automation_id": ctrl.get("name", ""),
                                    "text_set": text,
                                    "method": "keyboard",
                                    "timestamp": timestamp,
                                }
                    except Exception as e:
                        logger.debug(f"Bridge set_text failed: {e}")

                if not element.exists():
                    return {
                        "status": "error",
                        "operation": "set_text",
                        "error": f"Element with {selector_desc} not found",
                    }

                # Resolve the target: if the element is a container (Pane),
                # look for an Edit-type child to type into (common with
                # DevExpress/VCL composite controls like TcxTextEdit).
                target = element
                try:
                    wrapper = element.wrapper_object()
                    ct = str(getattr(wrapper.element_info, "control_type", ""))
                    if ct in ("Pane", "Group", "Custom"):
                        for child in wrapper.children():
                            child_ct = str(getattr(child.element_info, "control_type", ""))
                            if child_ct == "Edit":
                                target = child
                                logger.debug(f"set_text: using inner Edit child of {ct} element")
                                break
                except Exception as e:
                    logger.debug(
                        f"set_text: could not inspect children, using element directly: {e}"
                    )

                # Always use focus + keyboard input. WM_SETTEXT and UIA
                # ValuePattern update the Win32 buffer but don't notify
                # VCL/DevExpress, causing broken internal state.
                if window_handle:
                    ctypes.windll.user32.SetForegroundWindow(window_handle)
                    time.sleep(0.05)

                target_wrapper = (
                    target.wrapper_object() if hasattr(target, "wrapper_object") else target
                )
                try:
                    target_wrapper.set_focus()
                except Exception:
                    element.set_focus()
                time.sleep(0.1)
                pyautogui.hotkey("ctrl", "a")
                pyautogui.press("delete")
                if text.isascii():
                    pyautogui.typewrite(text, interval=0.02)
                else:
                    pyautogui.write(text)
                method = "keyboard"

                return {
                    "status": "success",
                    "operation": "set_text",
                    "selector": selector_desc,
                    "text_set": text,
                    "method": method,
                    "timestamp": timestamp,
                }

            # === RECT OPERATION ===
            elif operation == "rect":
                # Try Delphi bridge first — UIA can't see many VCL controls
                bridge = _get_bridge()
                if bridge is not None and (auto_id or title):
                    try:
                        results = _bridge_find_controls(
                            bridge, auto_id, title,
                            active_form_only=active_form_only,
                        )
                        if results:
                            ctrl = results[0]
                            handle = ctrl.get("handle", 0)
                            if handle:
                                import win32gui

                                r = win32gui.GetWindowRect(handle)
                                return {
                                    "status": "success",
                                    "operation": "rect",
                                    "source": "delphi_bridge",
                                    "automation_id": ctrl.get("name", ""),
                                    "left": r[0],
                                    "top": r[1],
                                    "right": r[2],
                                    "bottom": r[3],
                                    "width": r[2] - r[0],
                                    "height": r[3] - r[1],
                                    "timestamp": timestamp,
                                }
                    except Exception as e:
                        logger.debug(f"Bridge rect failed: {e}")

                if not element.exists():
                    return {
                        "status": "error",
                        "operation": "rect",
                        "error": f"Element with {selector_desc} not found",
                    }
                rect = element.rectangle()
                return {
                    "status": "success",
                    "operation": "rect",
                    "selector": selector_desc,
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                    "width": rect.width(),
                    "height": rect.height(),
                    "timestamp": timestamp,
                }

            # === VISIBLE OPERATION ===
            elif operation == "visible":
                if not element.exists():
                    return {
                        "status": "error",
                        "operation": "visible",
                        "error": f"Element with {selector_desc} not found",
                    }
                return {
                    "status": "success",
                    "operation": "visible",
                    "selector": selector_desc,
                    "is_visible": element.is_visible(),
                    "timestamp": timestamp,
                }

            # === ENABLED OPERATION ===
            elif operation == "enabled":
                if not element.exists():
                    return {
                        "status": "error",
                        "operation": "enabled",
                        "error": f"Element with {selector_desc} not found",
                    }
                return {
                    "status": "success",
                    "operation": "enabled",
                    "selector": selector_desc,
                    "is_enabled": element.is_enabled(),
                    "timestamp": timestamp,
                }

            # === EXISTS OPERATION ===
            elif operation == "exists":
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if element.exists():
                        return {
                            "status": "success",
                            "operation": "exists",
                            "selector": selector_desc,
                            "exists": True,
                            "wait_time": time.time() - start_time,
                            "timestamp": timestamp,
                        }
                    time.sleep(0.1)

                return {
                    "status": "success",
                    "operation": "exists",
                    "selector": selector_desc,
                    "exists": False,
                    "timeout": timeout,
                    "timestamp": timestamp,
                }

            # === WAIT OPERATION ===
            elif operation == "wait":
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if element.exists():
                        return {
                            "status": "success",
                            "operation": "wait",
                            "selector": selector_desc,
                            "found": True,
                            "wait_time": time.time() - start_time,
                            "element": _get_element_info(element),
                            "timestamp": timestamp,
                        }
                    time.sleep(0.1)

                return {
                    "status": "error",
                    "operation": "wait",
                    "selector": selector_desc,
                    "error": f"Element not found within {timeout} seconds",
                }

            # === VERIFY_TEXT OPERATION ===
            elif operation == "verify_text":
                if expected_text is None:
                    return {
                        "status": "error",
                        "operation": "verify_text",
                        "error": "expected_text parameter is required",
                    }
                if not element.exists():
                    return {
                        "status": "error",
                        "operation": "verify_text",
                        "error": f"Element with {selector_desc} not found",
                    }

                actual_text = element.window_text()
                if exact_match:
                    matches = actual_text == expected_text
                else:
                    matches = expected_text.lower() in actual_text.lower()

                return {
                    "status": "success" if matches else "failure",
                    "operation": "verify_text",
                    "selector": selector_desc,
                    "expected_text": expected_text,
                    "actual_text": actual_text,
                    "exact_match": exact_match,
                    "match_found": matches,
                    "timestamp": timestamp,
                }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown operation: {operation}",
                    "valid_operations": [
                        "click",
                        "double_click",
                        "right_click",
                        "hover",
                        "info",
                        "text",
                        "set_text",
                        "rect",
                        "visible",
                        "enabled",
                        "exists",
                        "wait",
                        "verify_text",
                        "list",
                    ],
                }

        except ElementNotFoundError as e:
            return {
                "status": "error",
                "operation": operation,
                "error": f"Element not found: {str(e)}",
                "error_type": "ElementNotFoundError",
            }
        except ElementNotVisible as e:
            return {
                "status": "error",
                "operation": operation,
                "error": f"Element not visible: {str(e)}",
                "error_type": "ElementNotVisible",
            }
        except Exception as e:
            return {
                "status": "error",
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__,
            }


__all__ = ["automation_elements"]
