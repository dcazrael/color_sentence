# tests/conftest.py
from __future__ import annotations
import sys
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[1]
SRC: Path = ROOT / "src"
sys.path.insert(0, str(SRC))
