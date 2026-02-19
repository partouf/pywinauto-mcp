# PyWinAuto MCP - Portmanteau Edition

**Version 0.3.1** | **8 Comprehensive Portmanteau Tools** | **FastMCP 2.13.1** | **SOTA 2026 Compliant**

A sophisticated, FastMCP 2.13.1 compliant server for Windows UI automation using PyWinAuto. Features 8 comprehensive portmanteau tools consolidating 60+ operations, face recognition security, and professional packaging.

## 🚀 What's New in v0.3.0 - Portmanteau Edition

### Tool Consolidation
Previous versions had 60+ individual tools scattered across multiple files with duplicates. The Portmanteau Edition consolidates everything into **8 comprehensive tools**:

| Tool | Operations | Description |
|------|------------|-------------|
| `automation_windows` | 11 | Window management (list, find, maximize, minimize, etc.) |
| `automation_elements` | 14 | UI element interaction (click, hover, text, etc.) |
| `automation_mouse` | 9 | Mouse control (move, click, scroll, drag) |
| `automation_keyboard` | 4 | Keyboard input (type, press, hotkey) |
| `automation_visual` | 4 | Visual operations (screenshot, OCR, find image) |
| `automation_face` | 5 | Face recognition (add, recognize, list, delete) |
| `automation_system` | 7 | System utilities (health, help, clipboard, processes) |
| `get_desktop_state` | 1 | Comprehensive desktop UI element discovery |

### Benefits
- **Reduced tool explosion**: 60+ tools → 8 tools
- **No duplicates**: Each operation defined once
- **Better discoverability**: Related operations grouped together
- **FastMCP 2.13.1 compliant**: Latest features and security fixes
- **SOTA 2026 Standard**: 100% docstring compliance (Ruff D-rules) and industrial technical documentation

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

### 🎯 Element Interaction (`automation_elements`)

Elements can be targeted by `title`, `auto_id`, `class_name`, `control_type`, or `control_id`. Selectors can be combined for precision.

```python
# Target elements directly by title (recommended for fewer round-trips)
automation_elements("set_text", window_handle=12345, title="Username", text="admin")
automation_elements("set_text", window_handle=12345, title="Password", text="secret")
automation_elements("click", window_handle=12345, title="Login")

# Target by automation id
automation_elements("click", window_handle=12345, auto_id="btnSubmit")

# Target by control_id (classic approach)
automation_elements("click", window_handle=12345, control_id="btnOK")

# Combine selectors for precision
automation_elements("set_text", window_handle=12345, title="Name", control_type="Edit", text="Hello!")

# Click by coordinates (relative to window)
automation_elements("right_click", window_handle=12345, x=100, y=200)

# Wait and verify
automation_elements("wait", window_handle=12345, title="Status", timeout=10.0)
automation_elements("verify_text", window_handle=12345, title="Status", expected_text="Ready")

# List all elements (for discovery when selectors are unknown)
automation_elements("list", window_handle=12345, max_depth=3)
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
PYWINAUTO_BACKEND=uia  # "uia" (UI Automation/COM) or "win32" (native Win32 API)
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
└── tools/
    ├── __init__.py           # Tool registration
    ├── portmanteau_windows.py    # Window management
    ├── portmanteau_elements.py   # UI elements
    ├── portmanteau_mouse.py      # Mouse control
    ├── portmanteau_keyboard.py   # Keyboard input
    ├── portmanteau_visual.py     # Visual/OCR
    ├── portmanteau_face.py       # Face recognition
    ├── portmanteau_system.py     # System utilities
    ├── desktop_state.py          # Desktop state (standalone)
    └── archived/                 # Legacy tools (preserved)
```

### Why Portmanteau?

1. **Prevents tool explosion**: Instead of 60+ tools, 8 comprehensive tools
2. **Better discoverability**: Related operations grouped logically
3. **Reduced cognitive load**: Fewer tools to remember
4. **Consistent interface**: Each tool follows the same pattern
5. **Easier maintenance**: Changes in one place affect all operations

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PyWinAuto](https://pywinauto.github.io/) for Windows automation
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server framework
- [Advanced Memory MCP](https://github.com/sandraschi/advanced-memory-mcp) for portmanteau pattern inspiration
