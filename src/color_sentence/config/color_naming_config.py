from __future__ import annotations
"""
HSV thresholds and hue bands used for coarse color naming.
"""

from typing import Final, NamedTuple, Sequence


class HueBand(NamedTuple):
    """Inclusive start and exclusive end in degrees, mapped to a coarse color name."""
    start_inclusive: float
    end_exclusive: float
    name: str


HSV_BLACK_VALUE_MAX: Final[float] = 0.12
HSV_WHITE_VALUE_MIN: Final[float] = 0.92
HSV_WHITE_SAT_MAX: Final[float] = 0.15
HSV_GRAY_SAT_MAX: Final[float] = 0.12
DEGREES_FULL_CIRCLE: Final[float] = 360.0

HUE_BANDS: Final[Sequence[HueBand]] = (
    HueBand(0.0, 12.0, "red"),
    HueBand(12.0, 35.0, "orange"),
    HueBand(35.0, 55.0, "yellow"),
    HueBand(55.0, 85.0, "lime"),
    HueBand(85.0, 165.0, "green"),
    HueBand(165.0, 200.0, "cyan"),
    HueBand(200.0, 250.0, "blue"),
    HueBand(250.0, 285.0, "indigo"),
    HueBand(285.0, 320.0, "purple"),
    HueBand(320.0, 350.0, "magenta"),
)

DEFAULT_HUE_NAME: Final[str] = "pinkish"
