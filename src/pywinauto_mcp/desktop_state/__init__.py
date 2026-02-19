"""Desktop State Capture Module.

Provides comprehensive UI element discovery, visual annotations, and OCR capabilities
for Windows desktop automation.
"""

from .annotator import ScreenshotAnnotator
from .capture import DesktopStateCapture
from .formatter import DesktopStateFormatter
from .ocr import OCRExtractor
from .walker import UIElementWalker

__all__ = [
    "UIElementWalker",
    "ScreenshotAnnotator",
    "OCRExtractor",
    "DesktopStateFormatter",
    "DesktopStateCapture",
]
