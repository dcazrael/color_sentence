from __future__ import annotations

"""
Build short, human-friendly utterances for TTS output.
Keep this independent from the TTS backend to allow reuse in CLI/GUI.
"""

from typing import Final
from color_sentence.config.types import ComputeResult


GERMAN_OPEN_QUOTE: Final[str] = "„"
GERMAN_CLOSE_QUOTE: Final[str] = "“"
EN_OPEN_QUOTE: Final[str] = "“"
EN_CLOSE_QUOTE: Final[str] = "”"


def _quote(text: str, locale: str) -> str:
    """
    Quote text according to the locale.
    """
    if locale.lower().startswith("de"):
        return f"{GERMAN_OPEN_QUOTE}{text}{GERMAN_CLOSE_QUOTE}"
    return f"{EN_OPEN_QUOTE}{text}{EN_CLOSE_QUOTE}"


def make_tts_sentence(original: str, result: ComputeResult, *, locale: str = "de-DE", include_hex: bool = True) -> str:
    """
    Build the announcement sentence for TTS, e.g.:
    DE: Der Satz "Wie geht es dir?" hat die Farbe Cerulean (#24B1E0).
    EN: The sentence “How are you?” has the color Cerulean (#24B1E0).

    Args:
        original: The original user sentence.
        result:  The computed color result (name + hex).
        locale:  BCP-47-ish tag controlling phrasing and quotes.
        include_hex: Whether to append the hex code.

    Returns:
        A locale-appropriate sentence ready for TTS.
    """
    quoted: str = _quote(original, locale)

    if locale.lower().startswith("de"):
        if include_hex:
            return f"Der Satz {quoted} hat die Farbe {result.name} {result.hex}."
        return f"Der Satz {quoted} hat die Farbe {result.name}."
    else:
        if include_hex:
            return f"The sentence {quoted} has the color {result.name} {result.hex}."
        return f"The sentence {quoted} has the color {result.name}."