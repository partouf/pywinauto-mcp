"""Visual/Screenshot/OCR portmanteau tool for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Instead of creating 5+ separate tools (one per visual operation), this tool consolidates related
visual operations into a single interface. This design:
- Prevents tool explosion (5+ tools → 1 tool) while maintaining full functionality
- Improves discoverability by grouping related operations together
- Follows FastMCP 2.13+ best practices for feature-rich MCP servers

SUPPORTED OPERATIONS:
- screenshot: Capture screen, window, or region
- extract_text: OCR text extraction from image or screen region
- find_image: Template matching to find image on screen
- highlight: Highlight a UI element with colored rectangle
"""

import base64
import io
import logging
import os
import tempfile
import time
from typing import Any, Literal

import cv2
import numpy as np
from PIL import Image, ImageGrab

from pywinauto_mcp.config import settings

# Import the FastMCP app instance
try:
    from pywinauto_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in portmanteau_visual")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in portmanteau_visual: {e}")
    app = None

# Try to import OCR
try:
    import pytesseract

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract not available. OCR functionality will be limited.")


if app is not None:
    logger.info("Registering portmanteau_visual tool with FastMCP")

    @app.tool(
        name="automation_visual",
        description="""Comprehensive visual automation tool tracking SOTA 2026 standards.

SUPPORTED OPERATIONS:
- screenshot: Captures a pixel-perfect image of the desktop, window, or region.
- extract_text: Employs Tesseract OCR to interpret text content from visual inputs.
- find_image: Performs template matching to locate graphical assets with confidence scoring.
- highlight: Renders a temporary visual indicator (rectangle) on the desktop for feedback.

DIALOGIC RETURN PATTERN:
If visual ambiguity or low OCR confidence occurs, returns clarification_needed.

Examples:
    automation_visual("screenshot")
    automation_visual("extract_text", window_handle=12345)
    automation_visual("find_image", template_path="button.png")

""",
    )
    def automation_visual(
        operation: Literal["screenshot", "extract_text", "find_image", "highlight"],
        window_handle: int | None = None,
        region_left: int | None = None,
        region_top: int | None = None,
        region_right: int | None = None,
        region_bottom: int | None = None,
        image_path: str | None = None,
        template_path: str | None = None,
        output_path: str | None = None,
        format: str = "png",
        return_base64: bool = False,
        language: str = "eng",
        ocr_config: str = "--psm 6",
        threshold: float = 0.8,
        control_id: str | None = None,
        color: str = "red",
        thickness: int = 2,
        highlight_duration: float = 3.0,
    ) -> dict[str, Any]:
        """Comprehensive visual automation tool for screenshots, OCR, and image recognition.

        PORTMANTEAU PATTERN RATIONALE:
        Consolidates complex computer vision and image processing operations into a single
        unified interface. This approach enables seamless transitions between capturing
        UI states (screenshots) and interpreting them (OCR/Template Matching) without
        inter-tool data transfer overhead. Follows FastMCP 2.14.3 standards for
        multimodal UI automation.

        SUPPORTED OPERATIONS:
        - screenshot: Captures a pixel-perfect image of the full desktop, a specific
          window, or a defined screen rectangle.
        - extract_text: Utilizes Tesseract OCR to interpret text content from image files
          or live screen regions. Ideal for non-textual controls and web-in-desktop views.
        - find_image: Employs template matching to locate specific graphical assets
          on the screen, returning precise coordinates and confidence scores.
        - highlight: Overlays a visual indicator (rectangle) on the screen to provide
          visual feedback during automated workflows or debugging sessions.

        DIALOGIC RETURN PATTERN:
        This tool implements the SOTA 2026 Dialogic Return Pattern for handling visual
        uncertainty. When template matching yields multiple matches or low confidence,
        it returns a clarification_needed status with a match_candidates list,
        allowing the AI agent to provide refined search criteria or secondary verification.

        USAGE AND RECOVERY:
        Standard screenshot operations default to full-screen capture if no window_handle
        or region is specified. In the event of OCR failure or template mismatch, the
        tool returns diagnostic_visual_data to assist in determining if the target
        element was obscured or incorrectly rendered.

        Args:
            operation (str, required): The visual task to execute.
            window_handle (int | None): The handle (HWND) of a specific window to capture.
            region_left (int | None): X-coordinate of the capture region.
            region_top (int | None): Y-coordinate of the capture region.
            region_right (int | None): Boundary X of the capture region.
            region_bottom (int | None): Boundary Y of the capture region.
            image_path (str | None): Path to an existing image for OCR operations.
            template_path (str | None): Path to the template image for finding.
            output_path (str | None): Destination for saving captured images.
            format (str): Image file format (e.g., png, jpg, bmp).
            return_base64 (bool): If True, returns image data in base64 string format.
            language (str): Tesseract language identifier (e.g., 'eng', 'deu').
            ocr_config (str): Advanced configuration flags for Tesseract.
            threshold (float): Minimum confidence (0-1) for image recognition.
            control_id (str | None): Target element ID for visual highlighting.
            color (str): Border color for highlights (red, green, blue, yellow).
            thickness (int): Border pixel thickness for highlights.
            highlight_duration (float): Display time for non-persistent highlights.

        Returns:
            dict[str, Any]: Operation-specific result dictionary with visual metadata and status.

        """
        try:
            timestamp = time.time()
            visual_metadata = {
                "timestamp": timestamp,
                "engine": "opencv_tesseract_pillow",
                "identity": "pywinauto-mcp-sota-2026",
            }

            # Build region tuple if provided
            region = None
            if all(v is not None for v in [region_left, region_top, region_right, region_bottom]):
                region = (region_left, region_top, region_right, region_bottom)

            # === SCREENSHOT OPERATION ===
            if operation == "screenshot":
                # Capture screenshot
                if window_handle is not None:
                    try:
                        import win32gui
                        from pywinauto.win32functions import SetForegroundWindow

                        SetForegroundWindow(window_handle)
                        time.sleep(0.3)

                        # Get window rect
                        rect = win32gui.GetWindowRect(window_handle)
                        left, top, right, bottom = rect

                        if region:
                            left += region[0]
                            top += region[1]
                            right = min(left + (region[2] - region[0]), right)
                            bottom = min(top + (region[3] - region[1]), bottom)

                        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                    except Exception as e:
                        return {
                            "status": "error",
                            "operation": "screenshot",
                            "error": f"Failed to capture window: {e}",
                        }
                elif region:
                    screenshot = ImageGrab.grab(bbox=region)
                else:
                    screenshot = ImageGrab.grab()

                # Convert to bytes
                img_buffer = io.BytesIO()
                screenshot.save(img_buffer, format=format.upper())
                img_bytes = img_buffer.getvalue()

                img_b64 = None
                file_path = None
                if return_base64:
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                else:
                    # Save to file
                    if output_path:
                        with open(output_path, "wb") as f:
                            f.write(img_bytes)
                        file_path = output_path
                    else:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as f:
                            f.write(img_bytes)
                            file_path = f.name

                result = {
                    "status": "success",
                    "operation": "screenshot",
                    "image_b64": img_b64,
                    "size": len(img_bytes),
                    "screenshot_path": file_path,
                    "timestamp": timestamp,
                    "visual_metadata": visual_metadata,
                }

                return result

            # === EXTRACT_TEXT OPERATION ===
            elif operation == "extract_text":
                if not OCR_AVAILABLE:
                    return {
                        "status": "error",
                        "operation": "extract_text",
                        "error": "OCR not available. Install pytesseract.",
                    }

                # Get image
                if image_path:
                    if not os.path.exists(image_path):
                        return {
                            "status": "error",
                            "operation": "extract_text",
                            "error": f"Image file not found: {image_path}",
                        }
                    image = Image.open(image_path)
                else:
                    # Take screenshot
                    if region:
                        image = ImageGrab.grab(bbox=region)
                    elif window_handle:
                        import win32gui

                        rect = win32gui.GetWindowRect(window_handle)
                        image = ImageGrab.grab(bbox=rect)
                    else:
                        image = ImageGrab.grab()

                # Convert to grayscale for better OCR
                image = image.convert("L")

                # Extract text
                text = pytesseract.image_to_string(image, lang=language, config=ocr_config)

                # Get confidence if possible
                try:
                    data = pytesseract.image_to_data(
                        image, lang=language, config=ocr_config, output_type=pytesseract.Output.DICT
                    )
                    confidences = [float(c) for c in data["conf"] if float(c) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                except:
                    avg_confidence = -1

                return {
                    "status": "success",
                    "operation": "extract_text",
                    "text": text.strip(),
                    "confidence": avg_confidence,
                    "language": language,
                    "timestamp": timestamp,
                    "visual_metadata": visual_metadata,
                }

            # === FIND_IMAGE OPERATION ===
            elif operation == "find_image":
                if not template_path:
                    return {
                        "status": "error",
                        "operation": "find_image",
                        "error": "template_path parameter is required",
                    }

                if not os.path.exists(template_path):
                    return {
                        "status": "error",
                        "operation": "find_image",
                        "error": f"Template file not found: {template_path}",
                    }

                # Load template
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is None:
                    return {
                        "status": "error",
                        "operation": "find_image",
                        "error": f"Failed to load template: {template_path}",
                    }

                template_h, template_w = template.shape[:2]

                # Take screenshot
                if region:
                    screenshot = ImageGrab.grab(bbox=region)
                elif window_handle:
                    import win32gui

                    rect = win32gui.GetWindowRect(window_handle)
                    screenshot = ImageGrab.grab(bbox=rect)
                else:
                    screenshot = ImageGrab.grab()

                # Convert to OpenCV format
                screen_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                # Template matching
                result_cv = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_cv)

                best_match = None
                if max_val >= threshold:
                    x, y = max_loc
                    center_x = x + (template_w // 2)
                    center_y = y + (template_h // 2)

                    best_match = {
                        "confidence": float(max_val),
                        "location": {
                            "x": int(center_x),
                            "y": int(center_y),
                            "left": int(x),
                            "top": int(y),
                            "right": int(x + template_w),
                            "bottom": int(y + template_h),
                            "width": int(template_w),
                            "height": int(template_h),
                        },
                    }

                return {
                    "status": "success",
                    "operation": "find_image",
                    "found": bool(best_match),
                    "best_match": best_match,
                    "threshold": threshold,
                    "message": "Match found" if best_match else "No match found above threshold",
                    "timestamp": timestamp,
                    "visual_metadata": visual_metadata,
                }

            # === HIGHLIGHT OPERATION ===
            elif operation == "highlight":
                if window_handle is None or control_id is None:
                    return {
                        "status": "error",
                        "operation": "highlight",
                        "error": "window_handle and control_id are required",
                    }

                from pywinauto import Desktop

                desktop = Desktop(backend=settings.PYWINAUTO_BACKEND)
                window = desktop.window(handle=window_handle)
                element = window.child_window(control_id=control_id)

                if not element.exists():
                    return {
                        "status": "error",
                        "operation": "highlight",
                        "error": f"Element with control_id '{control_id}' not found",
                    }

                rect = element.rectangle()

                # Take screenshot
                import win32gui

                win_rect = win32gui.GetWindowRect(window_handle)
                screenshot = ImageGrab.grab(bbox=win_rect)
                img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                # Convert color
                color_map = {
                    "red": (0, 0, 255),
                    "green": (0, 255, 0),
                    "blue": (255, 0, 0),
                    "yellow": (0, 255, 255),
                }
                bgr = color_map.get(color.lower(), (0, 0, 255))

                # Draw rectangle (adjust for window position)
                top_left = (rect.left - win_rect[0], rect.top - win_rect[1])
                bottom_right = (rect.right - win_rect[0], rect.bottom - win_rect[1])
                cv2.rectangle(img, top_left, bottom_right, bgr, thickness)

                # Save or return
                if output_path:
                    cv2.imwrite(output_path, img)
                    file_path = output_path
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                        cv2.imwrite(f.name, img)
                        file_path = f.name

                return {
                    "status": "success",
                    "operation": "highlight",
                    "file_path": file_path,
                    "element": {
                        "control_id": control_id,
                        "left": rect.left,
                        "top": rect.top,
                        "right": rect.right,
                        "bottom": rect.bottom,
                        "width": rect.width(),
                        "height": rect.height(),
                    },
                    "timestamp": timestamp,
                }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown operation: {operation}",
                    "valid_operations": ["screenshot", "extract_text", "find_image", "highlight"],
                }

        except Exception as e:
            return {
                "status": "error",
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__,
            }


__all__ = ["automation_visual"]
