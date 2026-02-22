# PyWinAuto MCP - Portmanteau Edition

**Version 0.4.0** | **10 Tools** | **FastMCP 2.13.1** | **Delphi Bridge**

A FastMCP 2.13.1 compliant server for Windows UI automation using PyWinAuto. Features 10 tools consolidating 60+ operations, with Delphi bridge integration for full VCL control access.

## What's New

### Delphi Bridge Integration
The `automation_elements` tool and the new `delphi_activeform` tool integrate with
[DelphiUITestExposer](https://github.com/user/DelphiUITestExposer) — an HTTP server
you embed in your Delphi application. The bridge exposes **all** VCL controls including
non-windowed ones (TSpeedButton, TcxButton, TLabel, etc.) that the Win32 API cannot see.

Each Delphi component's `Name` property is mapped to `automation_id`, making it the
preferred selector for Delphi apps.

### Tools

| Tool | Operations | Description |
|------|------------|-------------|
| `automation_windows` | 11 | Window management (list, find, maximize, minimize, etc.) |
| `automation_elements` | 14 | UI element interaction (click, hover, text, etc.) with Delphi bridge |
| `automation_mouse` | 9 | Mouse control (move, click, scroll, drag) |
| `automation_keyboard` | 4 | Keyboard input (type, press, hotkey) |
| `automation_visual` | 4 | Visual operations (screenshot, OCR, find image) |
| `automation_face` | 5 | Face recognition (add, recognize, list, delete) |
| `automation_system` | 7 | System utilities (health, help, clipboard, processes) |
| `get_desktop_state` | 1 | Comprehensive desktop UI element discovery |
| `delphi_activeform` | 1 | List interactive controls on the active Delphi form (bridge) |
| `automation_batch` | 3 | Batch execute multiple operations in one call (bridge) |

## 🏆 Features

### 🔍 Window Management (`automation_windows`)
```python
# List all windows
automation_windows("list")

# Find window by title
automation_windows("find", title="Notepad", partial=True)

# Maximize, minimize, restore
automation_windows("maximize", handle=12345)
automation_windows("minimize", handle=12345)
automation_windows("restore", handle=12345)

# Position and size
automation_windows("position", handle=12345, x=100, y=100, width=800, height=600)
```

### Delphi Active Form (`delphi_activeform`)

Lists interactive controls on the currently focused Delphi form. No window handle needed.
Returns a compact flat list with `automation_id`, `class_name`, `text`. Filters out labels,
layout containers, and inner parts of composite controls by default to keep output small.

Also detects native Win32 dialogs (MessageBox, TaskDialog, Open/Save) that the bridge
cannot see, and reports them with their child controls (buttons, inputs, combos).

```python
# See what's on the active form — discover automation_id values
delphi_activeform()

# Include read-only labels
delphi_activeform(include_labels=True)

# Include layout containers (TPanel, TScrollBox, etc.)
delphi_activeform(include_containers=True)

# Include hidden controls
delphi_activeform(include_hidden=True)
```

### Element Interaction (`automation_elements`)

Elements can be targeted by `auto_id`, `title`, `class_name`, `control_type`, or `control_id`.
Use `window_title` or `window_handle` to specify the parent window.

For Delphi apps with the bridge, `auto_id` maps to the Delphi component Name — this is
the preferred selector. `active_form_only` defaults to `True` to avoid name collisions
across forms.

- **click**: Uses physical mouse input at screen coordinates (pyautogui). Supports `anchor`
  parameter (`center`, `right`, `left`, `top`, `bottom`) to click specific edges of a control.
- **set_text**: Click-to-focus + keyboard input (`Ctrl+A`, `Delete`, type)
- **rect**: Returns screen coordinates of a control (bridge-first, UIA fallback)

```python
# Delphi app workflow: use auto_id (Delphi component Name)
automation_elements("list", window_title="Login")
automation_elements("set_text", auto_id="TE_Username", text="admin")
automation_elements("set_text", auto_id="TE_Password", text="secret")
automation_elements("click", auto_id="Btn_Login")

# Click a dropdown button on the right edge of a combo
automation_elements("click", auto_id="edType", anchor="right")

# Get screen coordinates of a control
automation_elements("rect", auto_id="edReferentie")

# Target by caption text
automation_elements("click", window_title="Login", title="Login")

# Click by coordinates (relative to window)
automation_elements("right_click", window_handle=12345, x=100, y=200)

# Wait and verify
automation_elements("wait", window_handle=12345, title="Status", timeout=10.0)
automation_elements("verify_text", window_handle=12345, title="Status", expected_text="Ready")

# List all elements (for discovery when selectors are unknown)
automation_elements("list", window_handle=12345, max_depth=3)
```

### Batch Operations (`automation_batch`)

Execute multiple element operations in one call. Reduces round-trips for form-filling
and multi-step workflows. Steps execute sequentially; stops on first error.

```python
# Fill a login form in one call
automation_batch(steps=[
    {"op": "set_text", "id": "TE_Username", "text": "admin"},
    {"op": "set_text", "id": "TE_Password", "text": "secret"},
    {"op": "click", "id": "Btn_Login"},
])

# Click a dropdown button on the right edge
automation_batch(steps=[
    {"op": "click", "id": "edType", "anchor": "right"},
    {"op": "wait", "wait": 0.5},
])

# With explicit window context
automation_batch(
    window_title="Login",
    steps=[
        {"op": "set_text", "id": "edName", "text": "John"},
        {"op": "click", "id": "btnSave", "wait": 1.0},
    ],
)
```

### 🖱️ Mouse Control (`automation_mouse`)
```python
# Position and movement
automation_mouse("position")
automation_mouse("move", x=500, y=300)
automation_mouse("move_relative", x=10, y=-5)

# Clicking
automation_mouse("click", x=500, y=300)
automation_mouse("double_click", x=500, y=300)
automation_mouse("right_click")

# Scrolling and dragging
automation_mouse("scroll", amount=3)
automation_mouse("drag", x=100, y=100, target_x=500, target_y=300)
```

### ⌨️ Keyboard Input (`automation_keyboard`)
```python
# Type text
automation_keyboard("type", text="Hello World!")

# Press keys
automation_keyboard("press", key="enter")
automation_keyboard("hotkey", keys=["ctrl", "c"])
automation_keyboard("hotkey", keys=["ctrl", "shift", "s"])
```

### 📸 Visual Intelligence (`automation_visual`)
```python
# Screenshots
automation_visual("screenshot")
automation_visual("screenshot", window_handle=12345, return_base64=True)

# OCR text extraction
automation_visual("extract_text", image_path="screen.png")

# Find image on screen
automation_visual("find_image", template_path="button.png", threshold=0.8)
```

### 🔒 Face Recognition (`automation_face`)
```python
# Add and recognize faces
automation_face("add", name="John Doe", image_path="john.jpg")
automation_face("recognize", image_path="unknown.jpg")

# List and manage
automation_face("list")
automation_face("delete", name="John Doe")

# Webcam capture
automation_face("capture", camera_index=0)
```

### ⚙️ System Utilities (`automation_system`)
```python
# Health and help
automation_system("health")
automation_system("help")

# Wait operations
automation_system("wait", seconds=2.5)
automation_system("wait_for_window", title="Notepad", timeout=10.0)

# Clipboard
automation_system("clipboard_get")
automation_system("clipboard_set", text="Copied!")

# Process list
automation_system("process_list")
```

### 📊 Desktop State Capture
```python
# Basic UI discovery
get_desktop_state()

# With visual annotations
get_desktop_state(use_vision=True)

# With OCR text extraction
get_desktop_state(use_ocr=True)

# Full analysis
get_desktop_state(use_vision=True, use_ocr=True, max_depth=15)
```

## 🛠 Installation

### Prerequisites
- Windows 10/11
- Python 3.10+
- Microsoft UI Automation (UIA) support

### Install from source

```powershell
# Clone the repository
git clone https://github.com/sandraschi/pywinauto-mcp.git
cd pywinauto-mcp

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install core package
pip install -e .

# Install with face recognition
pip install -e ".[face]"

# Install with all dependencies (including dev tools)
pip install -e ".[all]"
```

### Install Tesseract OCR (for OCR features)
Download and install Tesseract from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

## 🚀 Quick Start

### Start the MCP Server

```powershell
# Direct run
python -m pywinauto_mcp

# Or using the entry point
pywinauto-mcp
```

### Claude Desktop Configuration

Add to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pywinauto": {
      "command": "python",
      "args": ["-m", "pywinauto_mcp"],
      "cwd": "D:\\Dev\\repos\\pywinauto-mcp"
    }
  }
}
```

## 🔧 Configuration

Create a `.env` file in the project root:

```ini
# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# PyWinAuto Settings
PYWINAUTO_BACKEND=win32  # "win32" (native Win32 API) or "uia" (UI Automation/COM)
TIMEOUT=10.0
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0

# Face Recognition Settings
FACE_RECOGNITION_TOLERANCE=0.6
FACE_RECOGNITION_MODEL=hog

# Screenshot Settings
SCREENSHOT_DIR=./screenshots
SCREENSHOT_FORMAT=png
```

## 📚 Architecture

### Portmanteau Pattern

The Portmanteau Edition follows FastMCP 2.13+ best practices:

```
pywinauto_mcp/
├── app.py                    # FastMCP app instance
├── main.py                   # Entry point
├── config.py                 # Settings (backend, timeouts)
├── delphi_bridge.py          # DelphiUITestExposer HTTP client
└── tools/
    ├── __init__.py           # Tool registration
    ├── portmanteau_windows.py    # Window management
    ├── portmanteau_elements.py   # UI elements + Delphi bridge
    ├── portmanteau_mouse.py      # Mouse control
    ├── portmanteau_keyboard.py   # Keyboard input
    ├── portmanteau_visual.py     # Visual/OCR
    ├── portmanteau_face.py       # Face recognition
    ├── portmanteau_system.py     # System utilities
    ├── desktop_state.py          # Desktop state (standalone)
    ├── delphi_activeform.py      # Active Delphi form (bridge)
    └── automation_batch.py       # Batch operations (bridge)
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PyWinAuto](https://pywinauto.github.io/) for Windows automation
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server framework
- [Advanced Memory MCP](https://github.com/sandraschi/advanced-memory-mcp) for portmanteau pattern inspiration
