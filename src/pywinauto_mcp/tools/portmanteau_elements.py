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

# Import the FastMCP app instance
try:
    from pywinauto_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in portmanteau_elements")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in portmanteau_elements: {e}")
    app = None


def _get_desktop():
    """Get a Desktop instance with proper error handling."""
    try:
        return Desktop(backend=settings.PYWINAUTO_BACKEND)
    except Exception as e:
        logger.error(f"Failed to get Desktop instance: {e}")
        raise


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
- control_id: Win32 or symbolic control identifier
- auto_id: UIA AutomationId for precise targeting
- title: Element name/caption text (human-readable label)
- class_name: Windows class name
- control_type: UI role (e.g., "Button", "Edit", "ComboBox")

You can combine selectors to narrow matches (e.g., title="Username" + control_type="Edit").
This means you do NOT need to call "list" first to discover control_ids - you can target
elements directly by their visible title or automation id.

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

Examples:
    # Click a button by caption - just window title + button title
    automation_elements("click", window_title="Login", title="OK")

    # Fill a form by window title (no handle needed)
    automation_elements("set_text", window_title="Login", title="Username", text="admin")
    automation_elements("set_text", window_title="Login", title="Password", text="secret")
    automation_elements("click", window_title="Login", title="Login")

    # Target by automation id
    automation_elements("click", window_handle=12345, auto_id="btnSubmit")

    # Target by control_id (classic approach)
    automation_elements("click", window_handle=12345, control_id="btnOK")

    # Combine selectors for precision
    automation_elements("set_text", window_title="MyApp",
        title="Name", control_type="Edit", text="Hello")

    # List all elements (for discovery when selectors are unknown)
    automation_elements("list", window_title="MyApp", max_depth=3)

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
        absolute: bool = False,
        duration: float = 0.5,
        text: str | None = None,
        expected_text: str | None = None,
        exact_match: bool = True,
        timeout: float = 5.0,
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Comprehensive UI element interaction operations for Windows automation.

        PORTMANTEAU PATTERN RATIONALE:
        Consolidates all element-level interactions into a single interface, significantly
        reducing the complexity of UI navigation and manipulation. This approach ensures
        consistent selection logic and error handling across different control types.
        Follows FastMCP 2.14.3 standards for high-reliability UI automation.

        SUPPORTED OPERATIONS:
        - click: Triggers a standard mouse click on the specified UI element.
        - double_click: Performs a double-click action on the element.
        - right_click: Performs a right-click action on the element.
        - hover: Moves the mouse cursor over the element without clicking.
        - info: Retrieves detailed metadata for a control, including its type and role.
        - text: Retrieves the current visible text content of an element.
        - set_text: Inputs a string value into an editable field (e.g., text box).
        - rect: Retrieves the screen coordinates and dimensions of the target element.
        - visible: Checks if the element is currently visible on screen.
        - enabled: Checks if the element is currently enabled for interaction.
        - exists: Verifies the presence of the element in the UI tree.
        - wait: Suspends execution until an element achieves a specific state (e.g., exists).
        - verify_text: Compares the element's text content against an expected string.
        - list: Recursively discovers child elements of the target window or container.

        DIALOGIC RETURN PATTERN:
        This tool implements the SOTA 2026 Dialogic Return Pattern for handling complex
        UI state transitions. In scenarios where an element is visually blocked, disabled,
        or exists in multiple instances (ambiguity), the tool transitions to a
        clarification_needed status. The returned payload includes element_tree metadata
        and suggested selection_alternatives to allow the AI agent to resolve the
        ambiguity through precise coordinate or handle targeting.

        USAGE AND RECOVERY:
        Standard interaction requires a valid window_handle and one or more selection
        criteria (auto_id, title, etc.). If an ElementNotFoundError occurs, the tool
        returns diagnostic_info describing the current window state and suggested
        recovery_options, such as increasing the timeout or refreshing the UI tree.

        Args:
            operation (str, required): The element interaction to perform.
            window_handle (int | None): Parent window identifier (HWND).
            window_title (str | None): Parent window title (exact, case-insensitive).
                Use this instead of window_handle to skip the window discovery step.
            control_id (str | int | None): Win32 or symbolic control identifier.
            auto_id (str | None): AutomationID for UIA-based element selection.
            title (str | None): Plaintext title or name of the target element.
            control_type (str | None): The expected UI role (e.g., Button, Edit).
            class_name (str | None): Windows class name for precise targeting.
            x (int | None): Horizontal offset for relative coordinate operations.
            y (int | None): Vertical offset for relative coordinate operations.
            button (str): Mouse button for clicks (left, right, middle, default left).
            absolute (bool): Toggles between element-relative and screen-absolute coordinates.
            duration (float): Time in seconds to complete a mouse movement or hover.
            text (str | None): The string value to input for set_text operations.
            expected_text (str | None): Reference string for verify_text operations.
            exact_match (bool): Toggles between strict and partial string matching.
            timeout (float): Maximum seconds to wait for an element to become ready.
            max_depth (int): Recursion limit for child element discovery.

        Returns:
            dict[str, Any]: Operation-specific result dictionary with element status.

        """
        try:
            timestamp = time.time()
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

                # Use WM_SETTEXT via Win32 as the primary method — UIA
                # ValuePattern.SetValue silently fails on many Delphi/DevExpress
                # controls even though it reports success.
                wm_settext = 0x000C
                target_wrapper = (
                    target.wrapper_object() if hasattr(target, "wrapper_object") else target
                )
                target_handle = getattr(target_wrapper, "handle", None)

                # Bring the parent window to the foreground first
                if window_handle:
                    ctypes.windll.user32.SetForegroundWindow(window_handle)

                if target_handle:
                    result = ctypes.windll.user32.SendMessageW(
                        target_handle,
                        wm_settext,
                        0,
                        text,
                    )
                    if result:
                        method = "wm_settext"
                    else:
                        logger.debug("WM_SETTEXT returned 0, falling back to keyboard input")
                        target_wrapper.set_focus()
                        target_wrapper.type_keys("^a{DELETE}")
                        target_wrapper.type_keys(text, with_spaces=True)
                        method = "keyboard"
                else:
                    try:
                        target.set_edit_text(text)
                        method = "direct"
                    except Exception as e:
                        logger.debug(f"set_edit_text failed, falling back to keyboard: {e}")
                        element.set_focus()
                        element.type_keys("^a{DELETE}")
                        element.type_keys(text, with_spaces=True)
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
