# Color Sentence (Satzfarbe)

**Text → Farbe**: Diese App berechnet zu jedem Satz eine Farbe (RGB/HEX) plus einen Namen.  
Sie kombiniert Buchstabenhäufigkeit bzw. Alphabet‑Anker, semantische Farbwörter (inkl. Suffixe wie `-lich`, `-stichig`, `-farben/-farbig`), Satzzeichen‑Modifikatoren – und kann das Ergebnis per TTS ausgeben. Die GUI ist in **PySide6**, der Core ist GUI‑unabhängig (PyQt6 wäre ebenfalls möglich).

---

## Projektstruktur

```
src/color_sentence/
├─ __init__.py
├─ config/
│  ├─ config.py                 # Kernschwellen, Punctuation/Length-Floor, Anchors, TTS/Name-Config, ComputeConfig
│  ├─ types.py                  # RGB‑Alias, Enums, Protokolle (ITTS, ITTSRunner)
│  ├─ gui_config.py             # GUI‑Konstanten (Größen, Abstände, Schriftgröße, Luminanzschwelle)
│  ├─ color_naming_config.py    # HSV‑Schwellen + Hue‑Bänder (Fallback‑Namensheuristik)
│  └─ overrides_config.py       # Semantische Farbdaten (Ziel‑RGBs, Stämme, Suffix‑Gewichte)
├─ core/
│  ├─ engine.py                 # Orchestrierung: Base‑RGB → Overrides → Punctuation → Name → (optional TTS)
│  ├─ normalization.py          # Umlaute/ß‑Transliteration, sichtbare Länge, Buchstabenfilter
│  ├─ color_math.py             # clamp, rgb→hex, HSV‑Namensheuristik, Sättigung/Helligkeit
│  └─ overrides.py              # Erkennung & Gewichtung von Farbwörtern
├─ net/
│  └─ color_api.py              # Color.Pizza‑Client (httpx), akzeptiert Namen bis zu Distanz‑Schwelle
├─ tts/
│  ├─ tts_gtts.py               # gTTS‑Backend (MP3‑Cache) + schlanke Wiedergabe je OS
│  ├─ tts_runner.py             # Nicht‑blockierende Ausführung (Thread + Queue)
│  └─ utterances.py             # Formulierung der gesprochenen Sätze
├─ ui/
│  └─ gui_pyside.py             # PySide6‑GUI (Hyprland‑freundliches Layout)
└─ cli/
   └─ cli.py                    # Einfache CLI
```

Der Core hat **keine Qt‑Abhängigkeit** und kann separat verwendet werden.

---

## Voraussetzungen

- **Python 3.10+**
- **Linux** oder **Windows** (macOS lässt sich leicht ergänzen)
- Audio‑Tools (für TTS‑Wiedergabe):
  - Empfohlen: **ffplay** (Teil von `ffmpeg`)
  - Linux‑Fallback: `ffmpeg` + `aplay` (ALSA)
  - Windows‑Fallback: PowerShell MediaPlayer (vorinstalliert)

**Tipps**  
Linux: `sudo apt install ffmpeg alsa-utils`  
Windows: FFmpeg von https://ffmpeg.org/ installieren und `ffplay` in den PATH legen.

---

## Installation

### Mit uv (empfohlen)
```bash
uv venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

uv pip install -e .
```

### Mit pip
```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -e .

```

## Schnellstart

### CLI
```bash
# Beispiel (Standard: Modus freq, Satzzeichen aktiv, Length-Floor aktiv)
python -m color_sentence.ui.cli "ich bin blau!"
```

Nützliche Optionen:
```bash
# Algorithmus wählen
python -m color_sentence.ui.cli --mode freq "text"
python -m color_sentence.ui.cli --mode anchor "text"

# Satzzeichen-Mods deaktivieren
python -m color_sentence.ui.cli --no-punct "text"

# Denominator (visible|letters|rgb_hits)
python -m color_sentence.ui.cli --denom letters "text"
```

### GUI (PySide6)
```bash
python -m color_sentence.ui.gui_pyside
```
Gib einen Satz ein → **Farbe berechnen**.  
Die Box zeigt HEX, Name und RGB; die TTS spricht im Hintergrund, wenn aktiviert.

---

## Konfiguration (zur Laufzeit)

Die zentrale Laufzeit‑Config ist `ComputeConfig` (in `config/config.py`). Wichtige Felder:

- `mode`: `freq` (Buchstabenhäufigkeit) oder `anchor` (Alphabet‑Anker)  
- `denominator`: `visible` | `letters` | `rgb_hits`  
- `punctuation_mods`: `True/False` (Einfluss von `!`/`?`)  
- `apply_length_floor`: `True/False` (kurze Texte heller, lange gedämpfter)  
- `speak_enabled`, `tts_backend`, `tts_async`, `tts_runner` (TTS steuern)  
- `speak_locale`, `speak_include_hex` (Form der TTS‑Äußerung)  

Beispiel:
```python
from dataclasses import replace
from color_sentence.config.config import ComputeConfig
from color_sentence.config.types import ComputeMode, Denominator

cfg = ComputeConfig()
cfg = replace(cfg, mode=ComputeMode.ANCHOR, denominator=Denominator.LETTERS)
```

### Farbnamensauflösung
- **Color.Pizza API** (in `net/color_api.py`) liefert Namen mit Distanzmaß.  
- Akzeptanzschwelle: `COLOR_NAME.api_distance_max` (in `config/config.py`).  
- Ist die Distanz zu groß oder die API nicht erreichbar, wird auf die **interne HSV‑Heuristik** (in `core/color_math.py`) zurückgegriffen.

### Semantische Overrides
- Daten: `config/overrides_config.py` (Ziel‑RGBs, Stämme, Suffix‑Gewichte).  
- Erkennung/Mischung: `core/overrides.py` (liefert `(rgb, weight)`).

### Satzzeichen & Length‑Floor
- Schwellen/Werte: `LENGTH_FLOOR`, `PUNCT` in `config/config.py`.  
- Anwendung: in `core/engine.py`, ohne Magic Numbers im Code.

---

## TTS

- Backend: **gTTS** (`tts/tts_gtts.py`) mit kleinem MP3‑Cache.  
- Nicht‑blockierend via `tts_runner.py` (Thread + Queue).  
- Wiedergabe:
  - Linux: bevorzugt `ffplay`; Fallback `ffmpeg` → WAV → `aplay`
  - Windows: bevorzugt `ffplay`; Fallback PowerShell MediaPlayer

Aktivieren (z.B. in der GUI‑Initialisierung):
```python
from dataclasses import replace
from color_sentence.config.config import ComputeConfig
from color_sentence.tts.tts_gtts import GttsSynthesizer
from color_sentence.tts.tts_runner import TtsRunner
from color_sentence.core.engine import prepare_engine

backend = GttsSynthesizer()
runner = TtsRunner(backend=backend)

cfg = ComputeConfig()
cfg = replace(cfg, speak_enabled=True, tts_backend=backend, tts_async=True, tts_runner=runner)
prepare_engine(cfg)  # wärmt TTS vor
```

---

## Entwicklung

### Beispiel `pyproject.toml` (Ausschnitt)
```toml
[project]
name = "color-sentence"
version = "0.1.0"
requires-python = ">=3.10"
readme = "README.md"
dependencies = []

[project.optional-dependencies]
gui = ["PySide6>=6.7"]
tts = ["gTTS>=2.5"]
net = ["httpx>=0.27"]

[project.scripts]
color-sentence = "color_sentence.ui.cli:main"
color-sentence-gui = "color_sentence.ui.gui_pyside:run"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.mypy]
python_version = "3.10"
strict = true

[tool.ruff]
line-length = 100
```

### Tests ausführen
```bash
pytest -q
```

---

## Troubleshooting

- **Kein/seltsamer Farbname**: Color.Pizza liefert Namen mit Distanz; ist die Distanz > Schwelle oder die API down, nutzt die App die HSV‑Heuristik. Passe `COLOR_NAME.api_distance_max` an.
- **Keine Audioausgabe**: Prüfe, ob `ffplay` (oder `ffmpeg` + `aplay`) verfügbar ist. Unter Windows muss PowerShell im PATH sein. Lautstärke/Systemaudio prüfen.
- **Erster TTS‑Call stockt**: `prepare_engine(cfg)` beim Start aufrufen (wärmt TTS auf).

---

## Lizenz
MIT (oder anpassen).
