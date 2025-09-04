from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

import httpx


BASE_URL: Final[str] = "https://api.color.pizza/v1"
REQUEST_TIMEOUT_SECONDS: Final[float] = 3.0
HEADER_USER_AGENT: Final[str] = "color_sentence/0.1 (+https://example.invalid)"


@dataclass(frozen=True)
class ColorNameInfo:
    """Color name lookup result from Color.Pizza."""
    requested_hex: str
    display_name: str
    matched_hex: str
    distance: float
    exact_match: bool


def _normalize_hex(hex_code: str) -> str:
    """Normalize to '#RRGGBB' uppercase; raise ValueError on invalid input."""
    raw: str = hex_code.strip()
    cleaned: str = raw[1:] if raw.startswith("#") else raw
    cleaned = cleaned.strip()
    if len(cleaned) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in cleaned):
        raise ValueError(f"Invalid hex color: {hex_code!r} (expected 6 hex digits)")
    return f"#{cleaned.upper()}"


def _extract_first_name(payload: dict) -> Optional[ColorNameInfo]:
    """Extract the first color entry into a structured result."""
    colors = payload.get("colors")
    if not isinstance(colors, list) or not colors:
        return None

    first = colors[0]
    name_val = first.get("name")
    hex_val = first.get("hex")
    distance_val = first.get("distance")
    requested_val = first.get("requestedHex", "")

    if not isinstance(name_val, str) or not isinstance(hex_val, str):
        return None

    display_name: str = name_val.strip()
    matched_hex_norm: str = _normalize_hex(hex_val)
    requested_hex_norm: str = _normalize_hex(f"#{requested_val}" if not str(requested_val).startswith("#") else requested_val)

    # Color.Pizza defines distance≈0 for exact name hits; also guard via hex equality.
    distance_num: float = float(distance_val) if isinstance(distance_val, (int, float)) else 0.0
    exact: bool = (distance_num == 0.0) or (matched_hex_norm == requested_hex_norm)

    return ColorNameInfo(
        requested_hex=requested_hex_norm,
        display_name=display_name,
        matched_hex=matched_hex_norm,
        distance=distance_num,
        exact_match=exact,
    )


def get_color_name_from_hex(hex_code: str, *, timeout_seconds: float = REQUEST_TIMEOUT_SECONDS) -> ColorNameInfo:
    """
    Resolve a human-friendly color name for a hex via Color.Pizza.

    Args:
        hex_code: '#RRGGBB' or 'RRGGBB'.
        timeout_seconds: HTTP timeout in seconds.

    Returns:
        ColorNameInfo with name, matched hex, distance, exact flag.

    Raises:
        ValueError: Invalid hex input or unusable response structure.
        httpx.HTTPError: Network/HTTP errors.
        RuntimeError: Missing name in a syntactically valid response.
    """
    normalized_hex: str = _normalize_hex(hex_code)
    params = {
        "values": normalized_hex.lstrip("#"),
        "goodnamesonly": "true",
        "noduplicates": "true",
    }
    headers = {"User-Agent": HEADER_USER_AGENT}

    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=timeout_seconds) as client:
        resp: httpx.Response = client.get("/", params=params)
        resp.raise_for_status()
        payload: dict = resp.json()

    info = _extract_first_name(payload)
    if info is None:
        raise RuntimeError("Color.Pizza response did not include a usable color name.")
    return info
