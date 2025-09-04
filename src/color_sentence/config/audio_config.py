from __future__ import annotations
"""
Selection for player under Linux and Windows as well as codec.
"""
from typing import Final

LINUX_PRIMARY_PLAYER: Final[str] = "ffplay"
LINUX_FFMPEG: Final[str] = "ffmpeg"
LINUX_APLAY: Final[str] = "aplay"

WINDOWS_PRIMARY_PLAYER: Final[str] = "ffplay"
WINDOWS_POWERSHELL_CANDIDATES: Final[tuple[str, ...]] = ("powershell", "powershell.exe")

WAV_CODEC: Final[str] = "pcm_s16le"
WAV_CHANNELS: Final[str] = "1"
WAV_RATE_HZ: Final[str] = "22050"