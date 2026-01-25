# PRD - PyWinAuto MCP: Portmanteau Edition

## 1. Overview
PyWinAuto MCP is a high-performance Model Context Protocol (MCP) server for Windows UI automation. It leverages the `pywinauto` library to provide agentic AI assistants with the capability to interact with Windows applications through a consolidated and efficient toolset.

## 2. Goals
- **Tool Efficiency**: Consolidate 60+ legacy tools into 8 comprehensive "Portmanteau" tools to avoid "tool explosion" and improve model performance.
- **SOTA Alignment**: Adhere to January 2026 State-of-the-Art (SOTA) standards for MCP development, including FastMCP 2.13+ compliance.
- **Security**: Integrate biometric-grade security features like face recognition for controlled automation environments.
- **Maintainability**: Ensure 100% docstring compliance (Ruff D-rules) and clean architectural separation.

## 3. Key Features
- **Portmanteau Tools**:
    - `automation_windows`: Lifecycle and window state management.
    - `automation_elements`: Deep UI tree interaction and verification.
    - `automation_mouse`: Precision coordinate-based control.
    - `automation_keyboard`: Sophisticated text and hotkey input.
    - `automation_visual`: OCR and template matching for non-standard UI.
    - `automation_face`: Identity-based security gating.
    - `automation_system`: Health, help, and environment utilities.
    - `get_desktop_state`: Full UI element discovery for grounding.
- **FastMCP Integration**: Native support for sampling, tool registration, and conversational error handling.
- **Environment Grounding**: Automatic state capture for visual-to-element mapping.

## 4. Technical Standards (SOTA 2026)
- **Documentation**: Google-style docstrings with strict adherence to PEP 257 (verified via Ruff).
- **Communication**: Zero-friction industrial technical tone for peer-to-peer AI collaboration.
- **Tool Patterns**: Portmanteau logic consolidation for token efficiency and reduced cognitive load.
- **Validation**: Empirical verification for all UI state changes before returning success.

## 5. Success Metrics
- **Pass Rate**: >98% success on standard UI automation tasks.
- **Latency**: <500ms overhead for tool execution (excluding PyWinAuto wait times).
- **Compliance**: 100% match with SOTA 2026 audit checklists.
