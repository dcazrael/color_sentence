# src/color_sentence/tts_gtts.py
from __future__ import annotations

from color_sentence.config.audio_config import LINUX_PRIMARY_PLAYER, LINUX_FFMPEG, LINUX_APLAY, WAV_CODEC, WAV_CHANNELS, \
    WAV_RATE_HZ, WINDOWS_PRIMARY_PLAYER, WINDOWS_POWERSHELL_CANDIDATES

"""
gTTS backend with a small on-disk cache.
Supported OS: Linux and Windows.

Linux playback (in order):
  1) ffplay
  2) ffmpeg -> WAV -> aplay

Windows playback (in order):
  1) ffplay
  2) PowerShell MediaPlayer (PresentationCore)
"""

from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path

import errno
import os
import platform
import shutil
import subprocess
import tempfile

from gtts import gTTS
from gtts.tts import gTTSError

from color_sentence.config import config as cfg
from color_sentence.config.types import ITTS


def _prepare_text_for_gtts(text: str) -> str:
    """
    Ensure text is acceptable for gTTS: must contain at least one alphanumeric.
    If input is only punctuation/whitespace, fall back to a short placeholder.
    """
    stripped: str = text.strip()
    has_alnum: bool = any(ch.isalnum() for ch in stripped)
    return stripped if (stripped and has_alnum) else "Hallo."


@dataclass
class GttsSynthesizer(ITTS):
    """
    Google Text-to-Speech with per-text MP3 caching.
    Minimal OS strategies; no macOS branch by design.
    """
    language: str = cfg.GTTS.language
    slow: bool = cfg.GTTS.slow
    cache_dir: Path | None = None
    _ready: bool = False

    def warmup(self) -> None:
        """
        Ensure cache dir exists and playback path is primed using a tiny sample.
        """
        if self._ready:
            return

        cache_root: Path = self._resolve_cache_dir()
        cache_root.mkdir(parents=True, exist_ok=True)

        warm_text: str = cfg.GTTS.warmup_text
        sample_path: Path = self._cached_mp3_for_text(warm_text)
        if not sample_path.exists():
            self._synthesize_to(sample_path, warm_text)

        self._play_mp3(sample_path)
        self._ready = True

    def speak(self, text: str) -> None:
        """
        Synthesize (or reuse cached) MP3 and play it.
        """
        if not self._ready:
            self.warmup()

        mp3_path: Path = self._cached_mp3_for_text(text)
        if not mp3_path.exists():
            self._synthesize_to(mp3_path, text)

        self._play_mp3(mp3_path)

    def _resolve_cache_dir(self) -> Path:
        """
        Resolve cache dir according to OS conventions.
        """
        if self.cache_dir is not None:
            return self.cache_dir

        system_name: str = platform.system().lower()
        base_dir: Path

        if system_name.startswith("windows"):
            local: str | None = os.environ.get("LOCALAPPDATA")
            base_dir = Path(local) if local is not None else Path.home() / "AppData" / "Local"
            return base_dir / "color_sentence" / "gtts-cache" / self.language

        # Linux & Unix-like
        xdg: str | None = os.environ.get("XDG_CACHE_HOME")
        base_dir = Path(xdg) if xdg is not None else Path.home() / ".cache"
        return base_dir / "color_sentence" / "gtts-cache" / self.language

    def _cached_mp3_for_text(self, text: str) -> Path:
        """
        Build a stable cache filename for (language, slow, text).
        """
        cache_root: Path = self._resolve_cache_dir()
        key: str = f"{self.language}|{self.slow}|{text}"
        digest: str = sha1(key.encode("utf-8")).hexdigest()
        filename: str = f"{'slow' if self.slow else 'fast'}_{digest}.mp3"
        return cache_root / filename

    def _synthesize_to(self, target_mp3: Path, text: str) -> None:
        """
        Synthesize MP3 to a temp file in the *target directory* (same filesystem),
        then atomically replace the final file. Fallback to shutil.move if needed.
        """
        safe_text: str = _prepare_text_for_gtts(text)

        target_dir: Path = target_mp3.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        # Temp-Datei im *Zielordner* erzeugen → kein Cross-Device-Problem
        tmp_handle = tempfile.NamedTemporaryFile(
            prefix="gtts_", suffix=".mp3", dir=str(target_dir), delete=False
        )
        tmp_path: Path = Path(tmp_handle.name)
        tmp_handle.close()

        try:
            engine = gTTS(text=safe_text, lang=self.language, slow=self.slow)  # type: ignore[name-defined]
            engine.save(str(tmp_path))
            try:
                tmp_path.replace(target_mp3)
            except OSError:
                shutil.move(str(tmp_path), str(target_mp3))
        except gTTSError as exc:  # type: ignore[name-defined]
            raise RuntimeError(f"gTTS network error: {exc}") from exc
        except OSError as exc:
            raise RuntimeError(f"File I/O during synthesis failed: {exc}") from exc
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except FileNotFoundError:
                pass
            except PermissionError:
                pass

    def _play_mp3(self, mp3_path: Path) -> None:
        """
        Dispatch to platform playback.
        """
        system_name: str = platform.system().lower()
        if system_name.startswith("linux"):
            self._play_linux(mp3_path)
            return
        if system_name.startswith("windows"):
            self._play_windows(mp3_path)
            return
        raise RuntimeError(f"Unsupported OS for playback: {system_name!r}")

    def _play_linux(self, mp3_path: Path) -> None:
        """
        ffplay if available; otherwise ffmpeg->WAV->aplay.
        """
        ffplay_bin: str | None = shutil.which(LINUX_PRIMARY_PLAYER)
        if ffplay_bin is not None:
            args: list[str] = [ffplay_bin, "-nodisp", "-autoexit", "-loglevel", "quiet", str(mp3_path)]
            _run_checked(args)
            return

        ffmpeg_bin: str | None = shutil.which(LINUX_FFMPEG)
        aplay_bin: str | None = shutil.which(LINUX_APLAY)
        if ffmpeg_bin is None or aplay_bin is None:
            raise RuntimeError("Linux playback unavailable. Install 'ffplay' or both 'ffmpeg' and 'aplay'.")

        wav_path: Path = self._mp3_to_wav(mp3_path, ffmpeg_bin)
        try:
            args_play: list[str] = [aplay_bin, "-q", str(wav_path)]
            _run_checked(args_play)
        finally:
            _safe_unlink(wav_path)

    @staticmethod
    def _mp3_to_wav(mp3_path: Path, ffmpeg_bin: str) -> Path:
        """
        Convert MP3 to a temporary WAV (mono 22.05kHz) compatible with aplay.
        """
        tmp = tempfile.NamedTemporaryFile(prefix="gtts_", suffix=".wav", delete=False)
        wav_path: Path = Path(tmp.name)
        tmp.close()

        cmd: list[str] = [
            ffmpeg_bin,
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(mp3_path),
            "-acodec",
            WAV_CODEC,
            "-ac",
            WAV_CHANNELS,
            "-ar",
            WAV_RATE_HZ,
            str(wav_path),
        ]
        _run_checked(cmd)
        return wav_path

    @staticmethod
    def _play_windows(mp3_path: Path) -> None:
        """
        ffplay if available; otherwise PowerShell MediaPlayer.
        """
        ffplay_bin: str | None = shutil.which(WINDOWS_PRIMARY_PLAYER)
        if ffplay_bin is not None:
            args: list[str] = [ffplay_bin, "-nodisp", "-autoexit", "-loglevel", "quiet", str(mp3_path)]
            _run_checked(args)
            return

        powershell_bin: str | None = _first_available(WINDOWS_POWERSHELL_CANDIDATES)
        if powershell_bin is None:
            raise RuntimeError("PowerShell not found on PATH; cannot play MP3 on Windows.")

        uri_str: str = mp3_path.resolve().as_uri()
        ps_script: str = rf"""
Add-Type -AssemblyName PresentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Open([Uri] '{uri_str}')
$player.Volume = 1.0
$player.Play()
while (-not $player.NaturalDuration.HasTimeSpan) {{ Start-Sleep -Milliseconds 50 }}
while ($player.Position -lt $player.NaturalDuration.TimeSpan) {{ Start-Sleep -Milliseconds 100 }}
"""
        args_ps: list[str] = [powershell_bin, "-NoProfile", "-Command", ps_script]
        _run_checked(args_ps)


def _first_available(candidates: tuple[str, ...]) -> str | None:
    """
    Return first executable from PATH among candidates.
    """
    for name in candidates:
        resolved: str | None = shutil.which(name)
        if resolved is not None:
            return resolved
    return None


def _run_checked(cmd: list[str]) -> None:
    """
    Run a subprocess; raise descriptive RuntimeError on known failures.
    """
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        program: str = cmd[0] if len(cmd) > 0 else "<unknown>"
        raise RuntimeError(f"Executable not found: {program!r}") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Command failed: {cmd!r} (exit {exc.returncode})") from exc


def _safe_unlink(path: Path) -> None:
    """
    Best-effort file deletion with narrow exception handling.
    """
    try:
        path.unlink(missing_ok=True)
    except FileNotFoundError:
        return
    except PermissionError:
        return
    except OSError as exc:
        if exc.errno in (errno.ENOENT, errno.EACCES):
            return
        raise
