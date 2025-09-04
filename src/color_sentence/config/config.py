from __future__ import annotations

"""
Core configuration for computation and TTS.

This module intentionally excludes color naming bands and semantic override
dictionaries; those live in dedicated submodules:
- color_naming_config.py
- overrides_config.py
"""

from dataclasses import dataclass
from typing import Final, Tuple
from .types import Denominator, ComputeMode, ITTS, ITTSRunner


@dataclass(frozen=True)
class LengthFloorConfig:
    """Brightness targets depending on visible text length (short = brighter)."""
    short_visible_max: int = 6
    long_visible_min: int = 30
    bright_at_short: int = 200
    bright_at_long: int = 80
    linear_step: int = 5


@dataclass(frozen=True)
class PunctuationConfig:
    """Weights translating punctuation into brightness/saturation multipliers."""
    weight_exclamation: int = 2
    weight_question: int = -1
    end_bonus: int = 1
    score_min: int = -3
    score_max: int = 3
    bright_per_score: float = 0.15
    sat_per_score: float = 0.10


@dataclass(frozen=True)
class AnchorConfig:
    """Alphabet anchor indices for R/G/B on a circular a–z (0..25) scale."""
    index_r: int = 17  # 'r'
    index_g: int = 6  # 'g'
    index_b: int = 1  # 'b'


@dataclass(frozen=True)
class GttsConfig:
    """Defaults for the gTTS synthesizer."""
    language: str = "de"
    slow: bool = False
    warmup_text: str = "Hallo."


@dataclass(frozen=True)
class GttsPlaybackConfig:
    """Minimal playback preferences per OS and WAV conversion parameters."""
    linux_primary_player: str = "ffplay"
    linux_ffmpeg: str = "ffmpeg"
    linux_aplay: str = "aplay"
    windows_primary_player: str = "ffplay"
    windows_powershell_candidates: Tuple[str, ...] = ("powershell", "powershell.exe")
    wav_codec: str = "pcm_s16le"
    wav_channels: str = "1"
    wav_rate_hz: str = "22050"


@dataclass(frozen=True)
class ComputeConfig:
    """
    Configuration controlling color computation and optional TTS behavior.
    """
    denominator: Denominator = Denominator.VISIBLE
    punctuation_mods: bool = True
    apply_length_floor: bool = True
    mode: ComputeMode = ComputeMode.FREQ

    speak_enabled: bool = False
    speak_locale: str = "de-DE"
    speak_include_hex: bool = False
    tts_backend: ITTS | None = None

    tts_async: bool = False
    tts_runner: ITTSRunner | None = None


LENGTH_FLOOR: Final[LengthFloorConfig] = LengthFloorConfig()
PUNCT: Final[PunctuationConfig] = PunctuationConfig()
ANCHOR: Final[AnchorConfig] = AnchorConfig()
GTTS: Final[GttsConfig] = GttsConfig()
GTTS_PLAYBACK: Final[GttsPlaybackConfig] = GttsPlaybackConfig()


@dataclass(frozen=True)
class ColorNameConfig:
    """
    Settings for resolving human-readable color names via Color.Pizza.
    Attributes:
        api_distance_max: Maximum allowed distance from Color.Pizza
            to accept the API's name. Larger distances fall back to
            the internal HSV heuristic.
    """
    api_distance_max: float = 20.0


COLOR_NAME: Final[ColorNameConfig] = ColorNameConfig()
