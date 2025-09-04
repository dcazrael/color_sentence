from __future__ import annotations
"""
Static data for semantic color overrides:
- canonical color RGB targets
- transliterated stems per color
- suffix weights
"""

from typing import Final
from .types import RGB

OVERRIDE_COLOR_RGB: Final[dict[str, RGB]] = {
    "rot": (255, 0, 0),
    "gruen": (0, 255, 0),
    "blau": (0, 0, 255),
    "gelb": (255, 255, 0),
    "orange": (255, 165, 0),
    "lila": (180, 0, 255),
    "violett": (148, 0, 211),
    "magenta": (255, 0, 255),
    "pink": (255, 105, 180),
    "tuerkis": (64, 224, 208),
    "cyan": (0, 255, 255),
    "braun": (150, 75, 0),
    "grau": (128, 128, 128),
    "weiss": (255, 255, 255),
    "schwarz": (0, 0, 0),
    # Metals / earth tones
    "gold": (212, 175, 55),
    "silber": (192, 192, 192),
    "bronze": (205, 127, 50),
    "kupfer": (184, 115, 51),
    "messing": (181, 166, 66),
    # Additional shades
    "beige": (245, 245, 220),
    "oliv": (128, 128, 0),
    "mint": (170, 255, 195),
    "khaki": (195, 176, 145),
}

OVERRIDE_COLOR_STEMS: Final[dict[str, list[str]]] = {
    "rot": ["rot", "roet"],
    "gruen": ["gruen"],
    "blau": ["blau", "blaeu"],
    "gelb": ["gelb"],
    "braun": ["braun", "braeun"],
    "orange": ["orange"],
    "lila": ["lila"],
    "violett": ["violett"],
    "magenta": ["magenta"],
    "pink": ["pink"],
    "tuerkis": ["tuerkis"],
    "cyan": ["cyan"],
    "grau": ["grau"],
    "weiss": ["weiss"],
    "schwarz": ["schwarz"],
    # Metals / earth tones
    "gold": ["gold"],
    "silber": ["silber", "silbern"],
    "bronze": ["bronze", "bronzen"],
    "kupfer": ["kupfer"],
    "messing": ["messing"],
    # Additional shades
    "beige": ["beige"],
    "oliv": ["oliv"],
    "mint": ["mint"],
    "khaki": ["khaki"],
}

OVERRIDE_SUFFIX_WEIGHTS: Final[dict[str, float]] = {
    "": 0.70,        # base word
    "farben": 0.60,
    "farbig": 0.60,
    "stichig": 0.50,
    "lich": 0.35,
}

BASE_WORD_SUFFIX_KEY: Final[str] = ""
