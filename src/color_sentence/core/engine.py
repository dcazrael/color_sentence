# src/color_sentence/core/engine.py
from __future__ import annotations

from typing import List, Tuple, Type

from color_sentence.config.config import (
    ANCHOR,
    COLOR_NAME,
    LENGTH_FLOOR,
    PUNCT,
    ComputeConfig,
)
from color_sentence.config.types import ComputeMode, Denominator, RGB, ComputeResult
from color_sentence.core.color_math import (
    approx_color_name,
    apply_brightness,
    apply_saturation,
    rgb_to_hex,
)
from color_sentence.core.normalization import letters_only, transliterate_de, visible_len
from color_sentence.core.overrides import find_override_and_weight
from color_sentence.tts.utterances import make_tts_sentence


def _to_byte_0_1(value: float) -> int:
    """Convert a clamped proportion in [0.0, 1.0] to an 8-bit channel [0, 255]."""
    clamped: float = 0.0 if value < 0.0 else (1.0 if value > 1.0 else value)
    scaled: float = clamped * 255.0
    channel: int = int(round(scaled))
    return channel


def _length_floor_target(visible_count: int) -> int:
    """Return the target max channel for brightness based on visible text length."""
    if visible_count <= LENGTH_FLOOR.short_visible_max:
        return LENGTH_FLOOR.bright_at_short
    if visible_count >= LENGTH_FLOOR.long_visible_min:
        return LENGTH_FLOOR.bright_at_long
    delta: int = visible_count - LENGTH_FLOOR.short_visible_max
    target: int = int(round(LENGTH_FLOOR.bright_at_short - LENGTH_FLOOR.linear_step * delta))
    return target


def _apply_length_floor(rgb: RGB, base_count: int, cfg: ComputeConfig) -> RGB:
    """Raise brightness for short inputs and cap very dark results (frequency mode)."""
    if not cfg.apply_length_floor or base_count <= 0:
        return rgb
    red: int = rgb[0]
    green: int = rgb[1]
    blue: int = rgb[2]
    current_max: int = max(red, green, blue)
    target_max: int = _length_floor_target(base_count)
    if current_max <= 0 or current_max >= target_max:
        return rgb
    factor: float = target_max / float(current_max)
    red_out: int = min(255, int(round(float(red) * factor)))
    green_out: int = min(255, int(round(float(green) * factor)))
    blue_out: int = min(255, int(round(float(blue) * factor)))
    return red_out, green_out, blue_out


def _luminance_255(rgb: RGB) -> float:
    """Return perceived luminance on a 0..255 scale (sRGB weights)."""
    red: float = float(rgb[0])
    green: float = float(rgb[1])
    blue: float = float(rgb[2])
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _punctuation_multipliers(original_text: str) -> Tuple[float, float]:
    """Compute brightness and saturation multipliers from punctuation counts."""
    count_excl: int = original_text.count("!")
    count_quest: int = original_text.count("?")
    score: int = PUNCT.weight_exclamation * count_excl + PUNCT.weight_question * count_quest

    tail: str = original_text.rstrip()
    if tail.endswith("!"):
        score += PUNCT.end_bonus
    elif tail.endswith("?"):
        score -= PUNCT.end_bonus

    if score < PUNCT.score_min:
        score = PUNCT.score_min
    elif score > PUNCT.score_max:
        score = PUNCT.score_max

    brightness_multiplier: float = 1.0 + PUNCT.bright_per_score * float(score)
    saturation_multiplier: float = 1.0 + PUNCT.sat_per_score * float(score)
    return brightness_multiplier, saturation_multiplier


def _compute_rgb_freq(text_trans: str, denominator: Denominator) -> Tuple[RGB, int]:
    """Compute base RGB via r/g/b letter frequencies. Returns (rgb, base_count)."""
    letters: List[str]
    base_count: int

    if denominator is Denominator.VISIBLE:
        base_count = visible_len(text_trans)
        letters = letters_only(text_trans)
    elif denominator is Denominator.LETTERS:
        letters = letters_only(text_trans)
        base_count = len(letters)
    else:
        letters = letters_only(text_trans)
        hits: int = sum(1 for ch in letters if ch in "rRgGbB")
        base_count = max(1, hits)

    red_count: int = sum(1 for ch in letters if ch in "rR")
    green_count: int = sum(1 for ch in letters if ch in "gG")
    blue_count: int = sum(1 for ch in letters if ch in "bB")

    red: int = _to_byte_0_1((red_count / base_count) if base_count > 0 else 0.0)
    green: int = _to_byte_0_1((green_count / base_count) if base_count > 0 else 0.0)
    blue: int = _to_byte_0_1((blue_count / base_count) if base_count > 0 else 0.0)
    return (red, green, blue), base_count


def _letter_index(letter: str) -> int | None:
    """Map 'a'..'z' (case-insensitive) to 0..25; return None for non-letters."""
    lower: str = letter.lower()
    if "a" <= lower <= "z":
        return ord(lower) - ord("a")
    return None


def _nearest_anchor_keys(alpha_index: int) -> list[str]:
    """Return anchor key(s) among {'R','G','B'} with minimal circular distance."""
    distances: dict[str, int] = {}
    for key, idx in (("R", ANCHOR.index_r), ("G", ANCHOR.index_g), ("B", ANCHOR.index_b)):
        forward: int = (alpha_index - idx) % 26
        backward: int = (idx - alpha_index) % 26
        distance: int = forward if forward < backward else backward
        distances[key] = distance

    best_distance: int = min(distances.values())
    winners: list[str] = [k for k, d in distances.items() if d == best_distance]
    return winners


def _compute_rgb_anchor(text_trans: str) -> RGB:
    """Compute base RGB via nearest R/G/B anchors on a mod-26 circle, scaled to max 255."""
    counts: dict[str, float] = {"R": 0.0, "G": 0.0, "B": 0.0}
    for ch in text_trans:
        idx_opt: int | None = _letter_index(ch)
        if idx_opt is None:
            continue
        winners: list[str] = _nearest_anchor_keys(idx_opt)
        share: float = 1.0 / float(len(winners))
        for key in winners:
            counts[key] += share

    red_sum: float = counts["R"]
    green_sum: float = counts["G"]
    blue_sum: float = counts["B"]
    maximum: float = max(red_sum, green_sum, blue_sum)
    if maximum == 0.0:
        return 0, 0, 0

    scale: float = 255.0 / maximum
    red: int = int(round(red_sum * scale))
    green: int = int(round(green_sum * scale))
    blue: int = int(round(blue_sum * scale))
    return red, green, blue


def _blend_override(rgb: RGB, text_trans: str) -> RGB:
    """Blend semantic override color into the base RGB if present."""
    found = find_override_and_weight(text_trans)
    if found is None:
        return rgb
    override_rgb: RGB = found[0]
    weight: float = found[1]
    red: int = int(round((1.0 - weight) * float(rgb[0]) + weight * float(override_rgb[0])))
    green: int = int(round((1.0 - weight) * float(rgb[1]) + weight * float(override_rgb[1])))
    blue: int = int(round((1.0 - weight) * float(rgb[2]) + weight * float(override_rgb[2])))
    return red, green, blue


def _apply_punctuation(rgb: RGB, original_text: str, cfg: ComputeConfig) -> RGB:
    """Apply punctuation-based brightness/saturation; enforce monotone luminance."""
    if not cfg.punctuation_mods:
        return rgb

    base_luminance: float = _luminance_255(rgb)

    multipliers: Tuple[float, float] = _punctuation_multipliers(original_text)
    brightness_multiplier: float = multipliers[0]
    saturation_multiplier: float = multipliers[1]

    after_sat: RGB = apply_saturation(rgb, saturation_multiplier)
    after_bright: RGB = apply_brightness(after_sat, brightness_multiplier)

    new_luminance: float = _luminance_255(after_bright)

    # If we intended to darken but luminance increased, scale back to baseline.
    if brightness_multiplier < 1.0 and new_luminance > base_luminance and new_luminance > 0.0:
        scale_down: float = base_luminance / new_luminance
        return apply_brightness(after_bright, scale_down)

    # If we intended to brighten but luminance decreased, scale up to baseline.
    if brightness_multiplier > 1.0 and base_luminance > new_luminance > 0.0:
        scale_up: float = base_luminance / new_luminance
        return apply_brightness(after_bright, scale_up)

    return after_bright


def _resolve_display_name(hex_code: str, rgb: RGB) -> str:
    """Resolve a human-readable name using Color.Pizza with a distance cap; fall back to HSV heuristic."""
    try:
        from color_sentence.net.color_api import (  # type: ignore[reportGeneralTypeIssues]
            ColorNameInfo,
            get_color_name_from_hex as pizza_lookup,
        )
    except ImportError:
        pizza_lookup = None  # type: ignore[assignment]
        ColorNameInfo = None

    api_errors: Tuple[Type[BaseException], ...] = (ValueError, RuntimeError)
    try:
        import httpx  # type: ignore[import-not-found]
        api_errors = api_errors + (httpx.HTTPError,)  # type: ignore[attr-defined]
    except ImportError:
        pass

    if pizza_lookup is None:
        return approx_color_name(rgb[0], rgb[1], rgb[2])

    try:
        info: ColorNameInfo = pizza_lookup(hex_code)  # type: ignore[operator]
        if info.distance <= COLOR_NAME.api_distance_max:
            return info.display_name
        return approx_color_name(rgb[0], rgb[1], rgb[2])
    except api_errors:  # type: ignore[misc]
        return approx_color_name(rgb[0], rgb[1], rgb[2])


def _maybe_speak(original_text: str, result: ComputeResult, cfg: ComputeConfig) -> None:
    """Trigger TTS synchronously or via runner if enabled; ignore runtime TTS errors."""
    if not cfg.speak_enabled or cfg.tts_backend is None:
        return
    sentence: str = make_tts_sentence(
        original_text,
        result,
        locale=cfg.speak_locale,
        include_hex=cfg.speak_include_hex,
    )
    if cfg.tts_async and cfg.tts_runner is not None:
        try:
            cfg.tts_runner.enqueue(sentence)
        except RuntimeError:
            return
        return
    try:
        cfg.tts_backend.speak(sentence)
    except RuntimeError:
        return


def compute_color(text: str, cfg: ComputeConfig = ComputeConfig()) -> ComputeResult:
    """
    Compute the color for a text:
    1) normalize text
    2) derive base RGB (freq or anchor)
    3) apply length floor (freq mode)
    4) blend semantic overrides
    5) apply punctuation modifiers
    6) resolve display name
    7) optionally speak
    """
    original_text: str = text
    text_trans: str = transliterate_de(text)

    base_rgb: RGB
    base_count: int

    if cfg.mode is ComputeMode.FREQ:
        freq_result: Tuple[RGB, int] = _compute_rgb_freq(text_trans, cfg.denominator)
        base_rgb = freq_result[0]
        base_count = freq_result[1]
        base_rgb = _apply_length_floor(base_rgb, base_count, cfg)
    else:
        base_rgb = _compute_rgb_anchor(text_trans)

    with_override: RGB = _blend_override(base_rgb, text_trans)
    with_punct: RGB = _apply_punctuation(with_override, original_text, cfg)

    hex_code: str = rgb_to_hex(with_punct[0], with_punct[1], with_punct[2])
    display_name: str = _resolve_display_name(hex_code, with_punct)

    result: ComputeResult = ComputeResult(rgb=with_punct, hex=hex_code, name=display_name)
    _maybe_speak(original_text, result, cfg)
    return result


def prepare_engine(cfg: ComputeConfig) -> None:
    """Warm up TTS backend or start the async runner to avoid first-use latency."""
    if not cfg.speak_enabled:
        return
    if cfg.tts_async and cfg.tts_runner is not None:
        cfg.tts_runner.ensure_started()
        return
    if cfg.tts_backend is not None:
        try:
            cfg.tts_backend.warmup()
        except RuntimeError:
            return
