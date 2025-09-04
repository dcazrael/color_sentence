from __future__ import annotations

"""
Semantic color overrides based on German color words and common suffixes.

This module scans a transliterated text (e.g., "blaeulich") for color words,
optionally suffixed with "lich", "stichig", "farben", or "farbig".
It returns an average target RGB and an averaged mixing weight.
"""

import re
from typing import Final

from color_sentence.config.types import RGB
from color_sentence.config import overrides_config as o_cfg

__all__: list[str] = ["find_override_and_weight"]

_SUFFIX_GROUP_INDEX: Final[int] = 1


def _compile_color_patterns(stems_by_key: dict[str, list[str]]) -> list[tuple[str, re.Pattern[str]]]:
    """
    Build regex patterns for each color stem.

    The pattern shape is:  \b<stem>(farben|farbig|stichig|lich)?\w*
    """
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for color_key, stems in stems_by_key.items():
        for stem in stems:
            pattern_source: str = rf"\b{re.escape(stem)}(farben|farbig|stichig|lich)?\w*"
            compiled_pattern: re.Pattern[str] = re.compile(pattern_source, re.IGNORECASE)
            patterns.append((color_key, compiled_pattern))
    return patterns


_COLOR_PATTERNS: Final[list[tuple[str, re.Pattern[str]]]] = _compile_color_patterns(
    o_cfg.OVERRIDE_COLOR_STEMS
)


def find_override_and_weight(text_trans: str) -> tuple[RGB, float] | None:
    """
    Find color words with optional suffixes in a transliterated text and return an averaged override.

    Returns:
        (rgb_avg, weight_avg) if matches exist; otherwise None.
    """
    sum_red: float = 0.0
    sum_green: float = 0.0
    sum_blue: float = 0.0
    sum_weight: float = 0.0
    match_count: int = 0

    for color_key, pattern in _COLOR_PATTERNS:
        for match in pattern.finditer(text_trans):
            raw_suffix: str | None = match.group(_SUFFIX_GROUP_INDEX)
            suffix: str = raw_suffix.lower() if raw_suffix is not None else o_cfg.BASE_WORD_SUFFIX_KEY

            weight_for_match: float = o_cfg.OVERRIDE_SUFFIX_WEIGHTS.get(
                suffix, o_cfg.OVERRIDE_SUFFIX_WEIGHTS[o_cfg.BASE_WORD_SUFFIX_KEY]
            )

            rgb_for_match: RGB = o_cfg.OVERRIDE_COLOR_RGB[color_key]
            sum_red += float(rgb_for_match[0])
            sum_green += float(rgb_for_match[1])
            sum_blue += float(rgb_for_match[2])
            sum_weight += weight_for_match
            match_count += 1

    if match_count == 0:
        return None

    avg_red: int = int(round(sum_red / float(match_count)))
    avg_green: int = int(round(sum_green / float(match_count)))
    avg_blue: int = int(round(sum_blue / float(match_count)))
    avg_weight: float = sum_weight / float(match_count)

    base_weight: float = o_cfg.OVERRIDE_SUFFIX_WEIGHTS[o_cfg.BASE_WORD_SUFFIX_KEY]
    if avg_weight < 0.0:
        avg_weight = 0.0
    elif avg_weight > base_weight:
        avg_weight = base_weight

    rgb_avg: RGB = (avg_red, avg_green, avg_blue)
    return rgb_avg, avg_weight
