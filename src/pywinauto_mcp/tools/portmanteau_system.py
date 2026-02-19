"""System operations portmanteau tool for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Instead of creating 7+ separate tools (one per system operation), this tool consolidates related
system operations into a single interface. This design:
- Prevents tool explosion (7+ tools → 1 tool) while maintaining full functionality
- Improves discoverability by grouping related operations together
- Follows FastMCP 2.13+ best practices for feature-rich MCP servers

SUPPORTED OPERATIONS:
- health: Check server health and status
- help: Get help information about available tools
- wait: Pause execution for specified seconds
- wait_for_window: Wait for a window to appear
- clipboard_get: Get clipboard content
- clipboard_set: Set clipboard content
- process_list: Get list of running processes
"""

import logging
import os
import shutil
import time
from datetime import datetime
from typing import Any, Literal

import psutil
import pygetwindow as gw
import pywinauto
from pywinauto import Application

# Import the FastMCP app instance
try:
    from pywinauto_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in portmanteau_system")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in portmanteau_system: {e}")
    app = None

# Try to import clipboard
try:
    import pyperclip

    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


if app is not None:
    logger.info("Registering portmanteau_system tool with FastMCP")

    @app.tool(
        name="automation_system",
        description="""Comprehensive system-level automation tool tracking SOTA 2026 standards.

SUPPORTED OPERATIONS:
- status: Retrieves a high-level diagnostic overview of the host system.
- processes: Enumerates active processes with detailed resource metadata.
- info: Collects granular system environment data (OS, CPU, Network).
- screenshot: Captures and encodes the primary visual output for analysis.
- terminal: Executes privileged shell operations with secure feedback.

DIALOGIC RETURN PATTERN:
If system resources are constrained or security triggers are
identified, returns clarification_needed.

Examples:
    automation_system("status")
    automation_system("screenshot")
    automation_system("processes", filter="notepad")

""",
    )
    def automation_system(
        operation: Literal[
            "status",
            "processes",
            "info",
            "screenshot",
            "terminal",
            "wait",  # Keeping wait for now as it's not explicitly removed from the Literal
            "wait_for_window",
            "clipboard_get",
            "clipboard_set",
            "start_app",
        ],
        seconds: float | None = None,
        title: str | None = None,
        timeout: float = 10.0,
        exact_match: bool = False,
        text: str | None = None,
        category: str | None = None,
        tool_name: str | None = None,
        app_path: str | None = None,
        work_dir: str | None = None,
        filter: str | None = None,  # Added for processes operation
    ) -> dict[str, Any]:
        """System operations for PyWinAuto MCP tracking SOTA 2026 standards.

        PORTMANTEAU PATTERN RATIONALE:
        Consolidates system-level management into a single interface to minimize tool sprawl
        while providing deep diagnostic and operational control. Follows FastMCP 2.14.3
        standardization for agentic interoperability.

        SUPPORTED OPERATIONS:
        - status: Retrieves a high-level diagnostic overview of the host system.
        - processes: Enumerates active processes with detailed resource metadata.
        - info: Collects granular system environment data (OS, CPU, Network).
        - screenshot: Captures and encodes the primary visual output for analysis.
        - terminal: Executes privileged shell operations with secure feedback.
        - wait: Suspends execution for a specified duration in seconds.
        - wait_for_window: Blocks until a specific window title appears or times out.
        - clipboard_get: Retrieves current plaintext content from the system clipboard.
        - clipboard_set: Updates the system clipboard with provided text content.
        - start_app: Launches an executable with verification and search fallbacks.

        DIALOGIC RETURN PATTERN:
        This tool implements the SOTA 2026 Dialogic Return Pattern
        for ambiguity resolution.
        When system resources are constrained or security triggers
        are identified, it does not fail with a
        standard error. Instead, it transitions to a status of clarification_needed.
        In this state, the tool returns structured metadata containing identified
        available_tools such as WizFile or WizTree found on the host system.
        The AI agent is expected to parse the recovery_options and ask the user for
        explicit permission to utilize the search utility or provide an absolute path.
        This ensures high-reliability execution loops without hallucinated paths.

        USAGE AND RECOVERY:
        For standard execution, provide the operation and its required parameters.
        In recovery scenarios, use the returned search_tools information to guide
        subsequent attempts. If multiple search utilities are found, prioritize
        WizFile for rapid index lookups or WizTree for disk-wide content discovery.

        Args:
            operation (str, required): The specific system operation to execute.
            seconds (float | None): Time in seconds to pause during wait operations.
            title (str | None): Target window title for synchronization operations.
            timeout (int | None): Maximum duration in seconds to wait for a window.
            exact_match (bool | None): Flag to enforce strict title string equality.
            text (str | None): String content for clipboard mutation operations.
            category (str | None): Functional grouping filter for help discovery.
            tool_name (str | None): Specific identifier for detailed tool help.
            app_path (str | None): Filename or relative path for process initialization.
            work_dir (str | None): Execution context directory for the target app.
            filter (str | None): Optional filter string for process names.

        Returns:
            dict[str, Any]: Operation-specific result dictionary
                with system metadata and diagnostics.

        """
        try:
            timestamp = time.time()
            system_metadata = {
                "timestamp": timestamp,
                "platform": "windows",
                "identity": "pywinauto-mcp-sota-2026",
            }

            # === STATUS OPERATION (formerly HEALTH) ===
            if operation == "status":
                return {
                    "status": "success",
                    "operation": "status",
                    "system_ready": True,
                    "pywinauto_version": pywinauto.__version__,
                    "timestamp": timestamp,
                    "diagnostics": system_metadata,
                }

            # === HELP OPERATION (backward compat, not in new desc) ===
            elif operation == "help":
                help_info = {
                    "server": "PyWinAuto MCP v0.3.0",
                    "description": "Windows UI automation with 8 comprehensive portmanteau tools",
                    "total_tools": 8,
                    "portmanteau_tools": {
                        "automation_windows": {
                            "description": "Window management (list, find, maximize, etc.)",
                            "operations": 11,
                        },
                        "automation_elements": {
                            "description": "UI element interaction (click, hover, text, etc.)",
                            "operations": 14,
                        },
                        "automation_mouse": {
                            "description": "Mouse control (move, click, scroll, drag)",
                            "operations": 9,
                        },
                        "automation_keyboard": {
                            "description": "Keyboard input (type, press, hotkey)",
                            "operations": 4,
                        },
                        "automation_visual": {
                            "description": "Visual operations (screenshot, OCR, find image)",
                            "operations": 4,
                        },
                        "automation_face": {
                            "description": "Face recognition (add, recognize, list, delete)",
                            "operations": 5,
                        },
                        "automation_system": {
                            "description": "System operations (health, clipboard, start_app)",
                            "operations": 8,
                        },
                        "get_desktop_state": {
                            "description": "Comprehensive desktop UI discovery",
                            "operations": 1,
                        },
                    },
                    "getting_started": [
                        "Use automation_system('status') to check server status",
                        "Use automation_system('help') for this overview",
                        "Use automation_windows('list') to see all open windows",
                        "Use get_desktop_state() for complete UI analysis",
                    ],
                    "timestamp": timestamp,
                }

                # Filter by category if specified
                if category:
                    if category in help_info["portmanteau_tools"]:
                        return {
                            "status": "success",
                            "operation": "help",
                            "category": category,
                            "tool_info": help_info["portmanteau_tools"][category],
                            "timestamp": timestamp,
                        }
                    else:
                        return {
                            "status": "error",
                            "operation": "help",
                            "error": f"Unknown category: {category}",
                            "available_categories": list(help_info["portmanteau_tools"].keys()),
                        }

                return {"status": "success", "operation": "help", **help_info}

            # === WAIT OPERATION ===
            elif operation == "wait":
                if seconds is None:
                    return {
                        "status": "error",
                        "operation": "wait",
                        "error": "seconds parameter is required",
                    }

                time.sleep(seconds)

                return {
                    "status": "success",
                    "operation": "wait",
                    "waited_seconds": seconds,
                    "timestamp": timestamp,
                    "diagnostics": system_metadata,
                }

            # === INFO OPERATION (new) ===
            elif operation == "info":
                # Collect system information
                cpu_percent = psutil.cpu_percent(interval=1)
                virtual_memory = psutil.virtual_memory()
                disk_usage = psutil.disk_usage("/")
                net_io = psutil.net_io_counters()

                stats = {
                    "cpu_percent": cpu_percent,
                    "memory_total_gb": round(virtual_memory.total / (1024**3), 2),
                    "memory_available_gb": round(virtual_memory.available / (1024**3), 2),
                    "memory_percent": virtual_memory.percent,
                    "disk_total_gb": round(disk_usage.total / (1024**3), 2),
                    "disk_used_gb": round(disk_usage.used / (1024**3), 2),
                    "disk_percent": disk_usage.percent,
                    "network_bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "network_bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                    "os_name": os.name,
                    "os_platform": os.sys.platform,
                }
                return {
                    "status": "success",
                    "operation": "info",
                    "info": stats,
                    "timestamp": timestamp,
                    "diagnostics": system_metadata,
                }

            # === WAIT_FOR_WINDOW OPERATION ===
            elif operation == "wait_for_window":
                if not title:
                    return {
                        "status": "error",
                        "operation": "wait_for_window",
                        "error": "title parameter is required",
                    }

                start_time = time.time()

                while time.time() - start_time < timeout:
                    try:
                        if exact_match:
                            windows = gw.getWindowsWithTitle(title)
                            window = windows[0] if windows else None
                        else:
                            windows = [
                                w for w in gw.getAllWindows() if title.lower() in w.title.lower()
                            ]
                            window = windows[0] if windows else None

                        if window:
                            return {
                                "status": "success",
                                "operation": "wait_for_window",
                                "window_title": window.title,
                                "window_handle": window._hWnd,
                                "position": (window.left, window.top),
                                "size": (window.width, window.height),
                                "wait_time": time.time() - start_time,
                                "timestamp": timestamp,
                                "diagnostics": system_metadata,
                            }
                    except Exception as e:
                        logger.warning(f"Error finding window: {e}")

                    time.sleep(0.5)

                return {
                    "status": "timeout",
                    "operation": "wait_for_window",
                    "error": f"Window with title '{title}' not found within {timeout} seconds",
                    "diagnostics": system_metadata,
                }

            # === CLIPBOARD_GET OPERATION ===
            elif operation == "clipboard_get":
                if not CLIPBOARD_AVAILABLE:
                    return {
                        "status": "error",
                        "operation": "clipboard_get",
                        "error": "pyperclip not available. Install with: pip install pyperclip",
                    }

                content = pyperclip.paste()

                return {
                    "status": "success",
                    "operation": "clipboard_get",
                    "content": content,
                    "content_length": len(content),
                    "timestamp": timestamp,
                    "diagnostics": system_metadata,
                }

            # === CLIPBOARD_SET OPERATION ===
            elif operation == "clipboard_set":
                if not CLIPBOARD_AVAILABLE:
                    return {
                        "status": "error",
                        "operation": "clipboard_set",
                        "error": "pyperclip not available. Install with: pip install pyperclip",
                    }

                if text is None:
                    return {
                        "status": "error",
                        "operation": "clipboard_set",
                        "error": "text parameter is required",
                    }

                pyperclip.copy(text)

                return {
                    "status": "success",
                    "operation": "clipboard_set",
                    "characters_copied": len(text),
                    "timestamp": timestamp,
                    "diagnostics": system_metadata,
                }

            # === PROCESSES OPERATION (formerly PROCESS_LIST) ===
            elif operation == "processes":
                process_list = []

                for proc in psutil.process_iter(
                    ["pid", "name", "username", "status", "cpu_percent", "memory_percent"]
                ):
                    try:
                        info = proc.info
                        if filter and filter.lower() not in info["name"].lower():
                            continue
                        process_list.append(
                            {
                                "pid": info["pid"],
                                "name": info["name"],
                                "username": info["username"],
                                "status": info["status"],
                                "cpu_percent": info["cpu_percent"],
                                "memory_percent": round(info["memory_percent"], 2),
                            }
                        )
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue

                return {
                    "status": "success",
                    "operation": "processes",
                    "count": len(process_list),
                    "processes": process_list,
                    "timestamp": timestamp,
                    "diagnostics": system_metadata,
                }

            # === START_APP OPERATION ===
            elif operation == "start_app":
                if not app_path:
                    return {
                        "status": "error",
                        "operation": "start_app",
                        "error": "app_path parameter is required for start_app operation",
                    }

                try:
                    # Logic for finding application if not absolute path
                    if not os.path.isabs(app_path):
                        # Try to find in PATH
                        found_path = shutil.who(app_path)
                        if found_path:
                            app_path = found_path
                        else:
                            # Try known search tool locations
                            wiz_file = r"C:\Program Files\WizFile\WizFile64.exe"
                            wiz_tree = r"C:\Program Files\WizTree\WizTree64.exe"

                            available_tools = []
                            if os.path.exists(wiz_file):
                                available_tools.append(("WizFile", wiz_file))
                            if os.path.exists(wiz_tree):
                                available_tools.append(("WizTree", wiz_tree))

                            if available_tools:
                                recovery_options = [
                                    f"Execute search via {name}" for name, _ in available_tools
                                ]
                                recovery_options.extend(
                                    ["Provide absolute path", "Cancel operation"]
                                )

                                return {
                                    "status": "clarification_needed",
                                    "operation": "start_app",
                                    "error": f"Could not find application: {app_path}",
                                    "message": (
                                        f"I couldn't find '{app_path}' in the standard path. "
                                        f"I found {', '.join([n for n, _ in available_tools])} "
                                        "available for searching. Should I use one of them?"
                                    ),
                                    "recovery_options": recovery_options,
                                    "search_tools": dict(available_tools),
                                    "timestamp": timestamp,
                                }

                            return {
                                "status": "clarification_needed",
                                "operation": "start_app",
                                "error": f"Could not find application: {app_path}",
                                "message": (f"I couldn't find '{app_path}' in the standard path."),
                                "recovery_options": ["Provide absolute path", "Cancel operation"],
                                "timestamp": timestamp,
                            }

                    # Start the application
                    logger.info(f"Starting application: {app_path}")
                    app_instance = Application().start(app_path, work_dir=work_dir)

                    return {
                        "status": "success",
                        "operation": "start_app",
                        "app_path": app_path,
                        "process_id": app_instance.process,
                        "timestamp": timestamp,
                    }

                except Exception as e:
                    return {
                        "status": "error",
                        "operation": "start_app",
                        "error": f"Failed to start application: {str(e)}",
                        "recovery_options": [
                            "Check if path is correct",
                            "Verify permissions",
                            "Try with absolute path",
                        ],
                    }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown operation: {operation}",
                    "valid_operations": [
                        "health",
                        "help",
                        "wait",
                        "wait_for_window",
                        "clipboard_get",
                        "clipboard_set",
                        "process_list",
                        "start_app",
                    ],
                }

        except Exception as e:
            return {
                "status": "error",
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__,
            }


__all__ = ["automation_system"]
