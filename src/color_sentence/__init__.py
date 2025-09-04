# src/color_sentence/__init__.py
from __future__ import annotations
from .core.engine import compute_color, prepare_engine
from .config.config import ComputeConfig
from .config.types import ComputeMode, Denominator, ComputeResult, RGB

__all__ = [
    "compute_color",
    "prepare_engine",
    "ComputeConfig",
    "ComputeMode",
    "Denominator",
    "ComputeResult",
    "RGB",
]
