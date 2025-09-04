from __future__ import annotations

"""
UI layout and style constants for the PySide6 GUI.
All pixel-based values and thresholds live here to avoid magic numbers in code.
"""

from typing import Final

WINDOW_MIN_WIDTH: Final[int] = 900
FONT_POINT_SIZE: Final[int] = 18

PADDING_PX: Final[int] = 20
SPACING_PX: Final[int] = 20

INPUT_MIN_HEIGHT: Final[int] = 80
BUTTON_SIZE_PX: Final[int] = 80

COLOR_BOX_MIN_W: Final[int] = 200
COLOR_BOX_MIN_H: Final[int] = 100

# If computed luminance (0–255 scale) exceeds this value, use dark text on the color box.
LUMINANCE_DARK_TEXT_THRESHOLD: Final[float] = 160.0