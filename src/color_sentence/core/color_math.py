from __future__ import annotations

from color_sentence.config.color_naming_config import DEGREES_FULL_CIRCLE, HSV_BLACK_VALUE_MAX, HSV_WHITE_VALUE_MIN, \
    HSV_WHITE_SAT_MAX, HSV_GRAY_SAT_MAX, HUE_BANDS, DEFAULT_HUE_NAME

"""
Utility functions for RGB channel clamping, hex conversion, coarse color naming, and
simple saturation/brightness adjustments.
"""

import colorsys
from typing import Final

from color_sentence.config.types import RGB

__all__ = [
    "clamp_byte",
    "rgb_to_hex",
    "approx_color_name",
    "apply_saturation",
    "apply_brightness",
]

MIN_BYTE: Final[int] = 0
MAX_BYTE: Final[int] = 255


def clamp_byte(value: int) -> int:
    """
    Clamp an integer to the valid 8-bit color channel range [0, 255].
    """
    clamped: int = value
    if clamped < MIN_BYTE:
        clamped = MIN_BYTE
    elif clamped > MAX_BYTE:
        clamped = MAX_BYTE
    return clamped


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    """
    Convert three 8-bit channels into a #RRGGBB hex string.
    """
    hex_string: str = f"#{red:02X}{green:02X}{blue:02X}"
    return hex_string


def approx_color_name(red: int, green: int, blue: int) -> str:
    """
    Return a coarse color name derived from RGB via HSV thresholds.
    """
    red_norm: float = red / float(MAX_BYTE)
    green_norm: float = green / float(MAX_BYTE)
    blue_norm: float = blue / float(MAX_BYTE)

    hue_fraction: float
    saturation: float
    value: float
    hue_fraction, saturation, value = colorsys.rgb_to_hsv(red_norm, green_norm, blue_norm)
    hue_degrees: float = hue_fraction * DEGREES_FULL_CIRCLE

    if value < HSV_BLACK_VALUE_MAX:
        return "black"
    if value > HSV_WHITE_VALUE_MIN and saturation < HSV_WHITE_SAT_MAX:
        return "white"
    if saturation < HSV_GRAY_SAT_MAX:
        return "gray"

    for band in HUE_BANDS:
        if band.start_inclusive <= hue_degrees < band.end_exclusive:
            return band.name

    return DEFAULT_HUE_NAME


def apply_saturation(rgb: RGB, saturation_multiplier: float) -> RGB:
    """
    Scale saturation by moving each channel away from or towards the mean.
    """
    red_in: int = rgb[0]
    green_in: int = rgb[1]
    blue_in: int = rgb[2]

    mean_value: float = (red_in + green_in + blue_in) / 3.0

    def adjust(channel: int) -> int:
        adjusted_float: float = mean_value + (channel - mean_value) * saturation_multiplier
        adjusted_int: int = int(round(adjusted_float))
        return clamp_byte(adjusted_int)

    red_out: int = adjust(red_in)
    green_out: int = adjust(green_in)
    blue_out: int = adjust(blue_in)
    return red_out, green_out, blue_out


def apply_brightness(rgb: RGB, brightness_multiplier: float) -> RGB:
    """
    Scale brightness by multiplying each channel with a common factor.
    """
    red_in: int = rgb[0]
    green_in: int = rgb[1]
    blue_in: int = rgb[2]

    def adjust(channel: int) -> int:
        adjusted_float: float = channel * brightness_multiplier
        adjusted_int: int = int(round(adjusted_float))
        return clamp_byte(adjusted_int)

    red_out: int = adjust(red_in)
    green_out: int = adjust(green_in)
    blue_out: int = adjust(blue_in)
    return red_out, green_out, blue_out
