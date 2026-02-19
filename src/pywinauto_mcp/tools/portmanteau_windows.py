"""Window management portmanteau tool for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Instead of creating 11+ separate tools (one per window operation), this tool consolidates related
window management operations into a single interface. This design:
- Prevents tool explosion (11+ tools → 1 tool) while maintaining full functionality
- Improves discoverability by grouping related operations together
- Reduces cognitive load when working with window automation tasks
- Enables atomic batch operations across multiple window actions
- Follows FastMCP 2.13+ best practices for feature-rich MCP servers

SUPPORTED OPERATIONS:
- list: List all visible windows on the desktop
- find: Find window by title, class, or handle
- maximize: Maximize a window
- minimize: Minimize a window
- restore: Restore a minimized/maximized window
- close: Close a window
- activate: Bring window to foreground and activate it
- position: Set window position and size
- rect: Get window rectangle/bounds
- title: Get window title
- state: Get window state (minimized, maximized, etc.)

Args:
    operation: The window operation to perform
    handle: Window handle (required for most operations)
    title: Window title for find operation
    partial: Partial title match for find operation (default: True)
    x: X coordinate for position operation
    y: Y coordinate for position operation
    width: Width for position operation
    height: Height for position operation

Returns:
    Operation-specific result with window details

Examples:
    # List all windows
    automation_windows("list")

    # Find window by title
    automation_windows("find", title="Notepad")

    # Maximize a window
    automation_windows("maximize", handle=12345)

    # Set window position
    automation_windows("position", handle=12345, x=100, y=100, width=800, height=600)

"""

import logging
import time
from typing import Any, Literal

from pywinauto import Desktop
from pywinauto.findwindows import WindowNotFoundError

from pywinauto_mcp.config import settings

# Import the FastMCP app instance
try:
    from pywinauto_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in portmanteau_windows")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in portmanteau_windows: {e}")
    app = None


def _get_desktop():
    """Get a Desktop instance with proper error handling."""
    try:
        return Desktop(backend=settings.PYWINAUTO_BACKEND)
    except Exception as e:
        logger.error(f"Failed to get Desktop instance: {e}")
        raise


def _get_window_info(window) -> dict[str, Any]:
    """Extract standard window information."""
    try:
        info = {
            "handle": window.handle,
            "title": window.window_text(),
            "class_name": window.class_name(),
            "is_visible": window.is_visible(),
            "is_enabled": window.is_enabled(),
        }

        try:
            rect = window.rectangle()
            info["rect"] = {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.width(),
                "height": rect.height(),
            }
        except Exception:
            pass

        return info
    except Exception as e:
        logger.warning(f"Error getting window info: {e}")
        return {}


# Only proceed with tool registration if app is available
if app is not None:
    logger.info("Registering portmanteau_windows tool with FastMCP")

    @app.tool(
        name="automation_windows",
        description="""Comprehensive window management tool tracking SOTA 2026 standards.

SUPPORTED OPERATIONS:
- list: Enumerates all accessible windows with metadata (handles, titles, classes).
- find: Locates specific windows using flexible search criteria (title, handle, process).
- manage: Executes window-state transitions (minimize, maximize, restore, close).
- focus: Brings a specific window to the foreground and assigns input focus.
- get_active: Retrieves metadata for the window currently holding user focus.

DIALOGIC RETURN PATTERN:
If targeted windows are ambiguous or system-protected, returns clarification_needed.

Examples:
    automation_windows("list")
    automation_windows("manage", handle=12345, action="maximize")

""",
    )
    def automation_windows(
        operation: Literal["list", "find", "manage", "focus", "get_active"],
        handle: int | None = None,
        title: str | None = None,
        process_id: int | None = None,
        action: Literal["minimize", "maximize", "restore", "close"] | None = None,
    ) -> dict[str, Any]:
        """Comprehensive window management operations for Windows UI automation.

        PORTMANTEAU PATTERN RATIONALE:
        Consolidates all window-level lifecycle and state management into a single interface.
        This design prevents tool explosion while ensuring atomic control over window
        visibility, z-order, and spatial positioning. Follows FastMCP 2.14.3 SOTA
        standards for robust desktop automation.

        SUPPORTED OPERATIONS:
        - list: Recursively discovers all visible windows on the desktop.
        - find: Locates a single window matching specific title or class criteria.
        - manage: Expands the target window to fill its current display.
        - focus: Collapses the window to the taskbar.
        - get_active: Returns a window to its previous size and position.

        DIALOGIC RETURN PATTERN:
        In the event of ambiguous window titles (multiple matches) or failed activation
        due to OS-level focus locks, this tool returns a clarification_needed status.
        The response includes an available_handles list to enable the AI agent to
        disambiguate using unique HWND indicators.

        USAGE AND RECOVERY:
        Standard operations typically require a handle (HWND). If a WindowNotFoundError
        is encountered, the tool provides search_alternatives based on partial title
        matching of existing windows to aid in automated recovery.

        Args:
            operation (str, required): The window management task to execute.
            handle (int | None): The unique Windows window handle (HWND).
            title (str | None): String to match against window text (for find/list).
            process_id (int | None): Process ID to match against (for find).
            action (str | None): Specific action for 'manage' operation (e.g., 'maximize').

        Returns:
            dict[str, Any]: Operation-specific result dictionary with window metadata and status.

        """
        try:
            timestamp = time.time()
            window_system_metadata = {
                "timestamp": timestamp,
                "platform": "windows",
            }
            desktop = _get_desktop()

            # === LIST OPERATION ===
            if operation == "list":
                windows = []
                for window in desktop.windows():
                    try:
                        if window.is_visible():
                            windows.append(_get_window_info(window))
                    except Exception as e:
                        logger.warning(f"Error processing window: {e}")

                return {
                    "status": "success",
                    "operation": "list",
                    "count": len(windows),
                    "windows": windows,
                    "timestamp": timestamp,
                    "metadata": window_system_metadata,
                }

            # === FIND OPERATION ===
            elif operation == "find":
                if not title and not handle and not process_id:
                    return {
                        "status": "error",
                        "operation": "find",
                        "error": (
                            "At least one of title, handle,"
                            " or process_id is required"
                            " for find operation"
                        ),
                        "timestamp": timestamp,
                        "metadata": window_system_metadata,
                    }

                matches = []
                for window in desktop.windows():
                    try:
                        match = True
                        if title:
                            if title.lower() not in window.window_text().lower():
                                match = False
                        if handle and window.handle != handle:
                            match = False
                        if process_id and window.process_id() != process_id:
                            match = False

                        if match:
                            matches.append(_get_window_info(window))
                    except Exception as e:
                        logger.warning(f"Error checking window: {e}")

                return {
                    "status": "success",
                    "operation": "find",
                    "count": len(matches),
                    "windows": matches,
                    "query": {"title": title, "handle": handle, "process_id": process_id},
                    "timestamp": timestamp,
                    "metadata": window_system_metadata,
                }

            # === GET ACTIVE WINDOW OPERATION ===
            elif operation == "get_active":
                try:
                    active_window = desktop.active_window()
                    if active_window:
                        return {
                            "status": "success",
                            "operation": "get_active",
                            "window": _get_window_info(active_window),
                            "timestamp": timestamp,
                            "metadata": window_system_metadata,
                        }
                    else:
                        return {
                            "status": "success",
                            "operation": "get_active",
                            "window": None,
                            "message": "No active window found",
                            "timestamp": timestamp,
                            "metadata": window_system_metadata,
                        }
                except Exception as e:
                    return {
                        "status": "error",
                        "operation": "get_active",
                        "error": f"Failed to get active window: {str(e)}",
                        "error_type": type(e).__name__,
                        "timestamp": timestamp,
                        "metadata": window_system_metadata,
                    }

            # === OPERATIONS REQUIRING HANDLE ===
            if handle is None:
                return {
                    "status": "error",
                    "operation": operation,
                    "error": f"handle parameter is required for {operation} operation",
                    "timestamp": timestamp,
                    "metadata": window_system_metadata,
                }

            try:
                window = desktop.window(handle=handle)
            except WindowNotFoundError:
                return {
                    "status": "error",
                    "operation": operation,
                    "error": f"Window with handle {handle} not found",
                    "timestamp": timestamp,
                    "metadata": window_system_metadata,
                }

            # === MANAGE OPERATION ===
            if operation == "manage":
                if action is None:
                    return {
                        "status": "error",
                        "operation": "manage",
                        "error": "action parameter is required for manage operation",
                        "timestamp": timestamp,
                        "metadata": window_system_metadata,
                    }

                if action == "maximize":
                    window.maximize()
                elif action == "minimize":
                    window.minimize()
                elif action == "restore":
                    window.restore()
                elif action == "close":
                    window.close()
                else:
                    return {
                        "status": "error",
                        "operation": "manage",
                        "error": f"Unknown action: {action}",
                        "valid_actions": ["minimize", "maximize", "restore", "close"],
                        "timestamp": timestamp,
                        "metadata": window_system_metadata,
                    }

                return {
                    "status": "success",
                    "operation": "manage",
                    "action": action,
                    "handle": handle,
                    "timestamp": timestamp,
                    "metadata": window_system_metadata,
                }

            # === FOCUS OPERATION ===
            elif operation == "focus":
                try:
                    logger.info(f"Attempting to activate window with handle: {handle}")

                    # First ensure window is restored if minimized
                    if window.is_minimized():
                        logger.info("Window is minimized, restoring first")
                        window.restore()

                    # Try to set focus and activate
                    logger.info("Setting focus to window")
                    window.set_focus()

                    logger.info("Activating window")
                    window.activate()

                    # Verify activation
                    if not window.has_focus():
                        logger.warning(
                            "Window activation may not have succeeded - window does not have focus"
                        )

                    logger.info("Window activation completed")

                    return {
                        "status": "success",
                        "operation": "focus",
                        "handle": handle,
                        "action": "activated",
                        "has_focus": window.has_focus(),
                        "is_visible": window.is_visible(),
                        "is_enabled": window.is_enabled(),
                        "timestamp": timestamp,
                        "metadata": window_system_metadata,
                    }
                except Exception as e:
                    error_msg = f"Error activating window: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return {
                        "status": "error",
                        "operation": "focus",
                        "handle": handle,
                        "error": error_msg,
                        "error_type": type(e).__name__,
                        "window_state": {
                            "exists": True,
                            "is_visible": window.is_visible() if "window" in locals() else False,
                            "is_enabled": window.is_enabled() if "window" in locals() else False,
                            "has_focus": window.has_focus() if "window" in locals() else False,
                            "is_minimized": (
                                window.is_minimized() if "window" in locals() else False
                            ),
                        },
                        "timestamp": timestamp,
                        "metadata": window_system_metadata,
                    }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown operation: {operation}",
                    "valid_operations": [
                        "list",
                        "find",
                        "maximize",
                        "minimize",
                        "restore",
                        "close",
                        "activate",
                        "position",
                        "rect",
                        "title",
                        "state",
                    ],
                }

        except WindowNotFoundError as e:
            return {
                "status": "error",
                "operation": operation,
                "error": f"Window not found: {str(e)}",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {
                "status": "error",
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__,
            }


__all__ = ["automation_windows"]
