from __future__ import annotations

"""
Text normalization utilities.

- `transliterate_de`: replace German umlauts/ß with ASCII equivalents.
- `visible_len`: count non-whitespace characters.
- `letters_only`: extract ASCII letters A–Z as a list of single-character strings.
"""

import re
from typing import Final


__all__ = [
    "transliterate_de",
    "visible_len",
    "letters_only",
]


# Precompiled pattern for ASCII letters
ASCII_LETTERS_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z]")


def transliterate_de(text: str) -> str:
    """
    Replace German umlauts/ß with ASCII equivalents (ä→ae, ö→oe, ü→ue, ß→ss).

    Args:
        text: Arbitrary input string.

    Returns:
        A new string with German-specific characters transliterated to ASCII.
    """
    mapping: dict[str, str] = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
    }

    output_chars: list[str] = []
    for ch in text:
        replacement: str = mapping.get(ch, ch)
        output_chars.append(replacement)

    result: str = "".join(output_chars)
    return result


def visible_len(text: str) -> int:
    """
    Count all non-whitespace characters in the given text.

    Args:
        text: Arbitrary input string.

    Returns:
        Number of characters for which `str.isspace()` is False.
    """
    count: int = 0
    for ch in text:
        is_space: bool = ch.isspace()
        if not is_space:
            count += 1
    return count


def letters_only(text: str) -> list[str]:
    """
    Return a list of ASCII letters (A–Z/a–z) found in the input text.

    Args:
        text: Arbitrary input string.

    Returns:
        List of single-character strings containing only ASCII letters.
    """
    matches: list[str] = ASCII_LETTERS_PATTERN.findall(text)
    return matches
