# src/satzfarbe/types.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeAlias

RGB: TypeAlias = tuple[int, int, int]
"""RGB tuple with 8-bit channels (red, green, blue)."""


class ITTS(Protocol):
    """Interface for a pluggable text-to-speech backend."""
    def warmup(self) -> None:
        """Prepare the backend for low-latency first use."""
        ...
    def speak(self, text: str) -> None:
        """Speak the given text synchronously (may block)."""
        ...


class ITTSRunner(Protocol):
    """Interface for a non-blocking TTS runner that executes TTS in the background."""
    def ensure_started(self) -> None:
        """Start the underlying worker if not already running."""
        ...
    def enqueue(self, text: str) -> None:
        """Queue a sentence for speaking without blocking the caller."""
        ...
    def shutdown(self) -> None:
        """Stop the worker gracefully."""
        ...


class Denominator(Enum):
    """Base set used to normalize R/G/B letter counts."""
    VISIBLE = "visible"     # all non-whitespace characters
    LETTERS = "letters"     # letters A–Z only
    RGB_HITS = "rgb_hits"   # only occurrences of r/R, g/G, b/B


class ComputeMode(Enum):
    """Algorithm used to derive the base RGB values from text."""
    FREQ = "freq"           # frequency counting of r/g/b letters
    ANCHOR = "anchor"       # nearest-letter anchor mapping on a mod-26 circle


@dataclass(frozen=True)
class ComputeResult:
    """Final color result for a given input text."""
    rgb: RGB
    hex: str
    name: str
