# 📋 Changelog

All notable changes to PyWinAuto MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Delphi Bridge Integration**: New `delphi_bridge.py` client for communicating with DelphiUITestExposer HTTP servers embedded in Delphi applications. Discovers the bridge by scanning listening TCP ports and probing for the `/forms` endpoint. Auto-reconnects when the app restarts on a different port.
- **`delphi_activeform` tool**: Standalone tool that lists interactive controls on the currently active Delphi form via the bridge's `/activeform/controls` endpoint. No window handle needed — just call `delphi_activeform()`. Returns a compact flat list filtered to actionable controls only. Supports `include_labels`, `include_containers`, `include_hidden` flags. Also detects native Win32 dialogs (MessageBox, TaskDialog, Open/Save) that the bridge cannot see.
- **`automation_batch` tool**: Execute multiple element operations (click, set_text, wait) in one call. Reduces round-trips for form-filling workflows. Stops on first error with detailed failure info.
- **`anchor` parameter for clicks**: `_bridge_click`, `automation_elements("click")`, and `automation_batch` click steps support `anchor` (center, right, left, top, bottom) to click specific edges of a control — e.g. dropdown buttons on combo fields.
- **Bridge-first `rect` operation**: `automation_elements("rect")` tries the Delphi bridge first (using `GetWindowRect` for exact screen coordinates), falling back to UIA. UIA cannot see many VCL controls like `TDBrosGridFieldEditor`.
- **Native Win32 dialog detection**: `delphi_activeform` scans for `#32770` dialogs (MessageBox, TaskDialog, Open/Save) owned by the same process. Reports their child controls (buttons, edits, combos, static text) so agents can dismiss blocking popups.
- **Delphi component Name as `automation_id`**: The bridge maps each Delphi control's `Name` property (e.g. `TE_Username`, `Btn_Login`) to `automation_id` in element results, making it the preferred selector for Delphi apps.
- **Bridge-first element operations**: `automation_elements` operations (`list`, `click`, `set_text`, `rect`) try the Delphi bridge first, seeing all controls including non-windowed VCL controls (TSpeedButton, TcxButton, TLabel, etc.) that Win32 API cannot enumerate.
- **`active_form_only` parameter**: Defaults to `True` in both `automation_elements` and `automation_batch`. Restricts bridge lookups to the currently active form, avoiding name collisions when the same `auto_id` exists on multiple forms.
- **`window_title` parameter**: `automation_elements` now accepts `window_title` as an alternative to `window_handle`, skipping the window discovery step.
- **Smart output filtering in `delphi_activeform`**: Skips non-interactive controls by default — inner composite parts (TcxCustomDropDownInnerEdit, TDBrosGridFieldEditor), labels (TLabel, TcxLabel), layout containers (TPanel, TScrollBox), and controls without an `automation_id`. Reduces output from ~130K to ~30K chars.

### Fixed
- **`basic_tools` import error**: Fixed startup error `cannot import name 'basic_tools' from 'pywinauto_mcp.tools'` — the stale import in `main.py` now correctly imports the tools package.
- **Backend not passed to `Application().start()`**: `portmanteau_system.py` now passes `settings.PYWINAUTO_BACKEND` when starting applications.
- **Bridge click not working**: `_bridge_click` now uses physical mouse input (pyautogui) instead of Win32 message-based clicks which Delphi/DevExpress controls ignore. Uses `GetWindowRect` for windowed controls to get exact screen coordinates regardless of nesting depth.
- **Bridge set_text not working**: All `set_text` paths now use click-to-focus + keyboard input (`Ctrl+A`, `Delete`, type). `WM_SETTEXT` was removed entirely — it updates the Win32 buffer but doesn't notify VCL/DevExpress, causing broken internal state. Win32 `SetFocus` API was also replaced with physical click because `SetForegroundWindow` on MDI parents overrides `SetFocus` calls.
- **Bridge auto-reconnect**: `DelphiBridge._get()` detects connection failures and automatically re-discovers the bridge on a new port when the app restarts.
- **Ruff D203/D213 warnings**: Added explicit ignores in `pyproject.toml` for incompatible docstring rules.

### Removed
- **UIA multiprocessing fallback**: Removed dead `_uia_find_and_click()` function from `portmanteau_elements.py` — fully superseded by the Delphi bridge.
- **`WM_SETTEXT` code path**: Removed entirely from `portmanteau_elements.py` — all text input now uses keyboard.

## [0.3.1] - 2026-01-25

### Fixed
- **Docstring Refactoring**: Fixed missing blank lines after sections (D413) across all 8 portmanteau tools.
- **SOTA 2026 Alignment**: Standardized documentation to Jan 2026 industrial SOTA patterns.

### Added
- **Formal PRD**: Created `docs/PRD.md` to define project requirements and technical standards.
- **Improved Grounding**: Enhanced tool documentation for better AI agent navigation.

## [0.3.0] - 2025-10-08

### Added
- Comprehensive DXT manifest with 22+ automation tools
- Extensive prompt templates for conversational AI interaction
- GitHub Actions CI/CD pipeline with automated testing
- Issue and pull request templates for better contributions
- Contributing guidelines and development documentation

### Changed
- Reorganized repository structure with dedicated `dxt/` directory
- Updated pywin32 dependency to version 311
- Enhanced package metadata and descriptions

## [0.2.0] - 2025-01-23

### Added
- **Complete DXT Package**: Comprehensive Windows UI automation with face recognition
- **22 Automation Tools**: Window management, element interaction, OCR, mouse/keyboard control
- **Dual Interface Architecture**: MCP tools + REST API with feature parity
- **Face Recognition Security**: Webcam authentication and intruder detection
- **OCR Integration**: Text extraction from windows and images
- **Advanced Element Interaction**: Click, type, hover, and drag operations

### Changed
- Major architecture overhaul with modular plugin system
- Enhanced error handling and retry mechanisms
- Improved configuration management

## [0.1.0] - 2025-07-30

### Added
- Initial PyWinAuto MCP server implementation
- Basic window management tools
- Face recognition API endpoints
- Security monitoring features
- DXT packaging support

### Changed
- Initial release with core automation functionality

---

## 📊 Version Information

- **Current Version**: 0.4.0-dev
- **Python Support**: 3.10, 3.11, 3.12
- **Platform**: Windows 10/11
- **License**: MIT

## 🔄 Release Process

Releases are automated through GitHub Actions:
1. Push to `master` branch triggers CI
2. Tests run on Windows with multiple Python versions
3. DXT package is built and uploaded as artifact
4. Release creation triggers final package distribution

## 🤝 Contributing to Changelog

When contributing to this project, please:
- Add entries to the "Unreleased" section above
- Use present tense for changes ("Add feature" not "Added feature")
- Group changes under appropriate headings (Added, Changed, Fixed, etc.)
- Reference issue numbers when applicable

---

*For more detailed information about each release, see the [GitHub Releases](https://github.com/yourusername/pywinauto-mcp/releases) page.*
