# tests/test_engine.py
from __future__ import annotations
from dataclasses import replace

from color_sentence import compute_color, ComputeConfig, ComputeMode, Denominator


def _luminance(rgb: tuple[int, int, int]) -> float:
    """Relative Luminanz (sRGB-gewichtet), 0..255-Skala."""
    r, g, b = rgb
    return 0.2126 * float(r) + 0.7152 * float(g) + 0.0722 * float(b)


def test_freq_basic_blue_override_word() -> None:
    """Satz mit 'blau' sollte Blau-Anteil dominieren (Frequenz + Override)."""
    cfg = ComputeConfig(
        mode=ComputeMode.FREQ,
        punctuation_mods=False,
        apply_length_floor=False,
    )
    res = compute_color("ich bin blau", cfg)
    r, g, b = res.rgb
    assert b >= r and b >= g


def test_suffix_weight_strength() -> None:
    """'blau' (70%) sollte stärker Richtung Blau gehen als 'blaeulich' (35%)."""
    cfg = ComputeConfig(
        mode=ComputeMode.FREQ,
        punctuation_mods=False,
        apply_length_floor=False,
    )
    res_base = compute_color("blau", cfg)
    res_lich = compute_color("blaeulich", cfg)
    # Blau-Kanal sollte bei vollem Wort höher sein
    assert res_base.rgb[2] > res_lich.rgb[2]


def test_transliteration_umlaut() -> None:
    """'bläulich' muss wie 'blaeulich' wirken (Umlaute-Transliteration)."""
    cfg = ComputeConfig(
        mode=ComputeMode.FREQ,
        punctuation_mods=False,
        apply_length_floor=False,
    )
    res_umlaut = compute_color("bläulich", cfg)
    res_ascii = compute_color("blaeulich", cfg)
    # Gleiche Tendenz und sehr ähnliche Werte
    assert res_umlaut.rgb[2] >= res_umlaut.rgb[0]  # blau dominiert
    # Differenz darf existieren (z. B. durch Längenunterschiede), aber nicht riesig
    diff = sum(abs(a - b) for a, b in zip(res_umlaut.rgb, res_ascii.rgb))
    assert diff < 40


def test_punctuation_brightness_exclamations() -> None:
    """'!' sollte heller/satter machen als ohne Satzzeichen."""
    cfg = ComputeConfig(
        mode=ComputeMode.FREQ,
        punctuation_mods=True,
        apply_length_floor=False,
    )
    res_plain = compute_color("blau", replace(cfg, punctuation_mods=False))
    res_exc = compute_color("blau!!!", cfg)

    assert _luminance(res_exc.rgb) > _luminance(res_plain.rgb)


def test_punctuation_brightness_questions() -> None:
    """'??' sollte abdunkeln gegenüber ohne Satzzeichen."""
    cfg = ComputeConfig(
        mode=ComputeMode.FREQ,
        punctuation_mods=True,
        apply_length_floor=False,
    )
    res_plain = compute_color("blau", replace(cfg, punctuation_mods=False))
    res_q = compute_color("blau??", cfg)

    assert _luminance(res_q.rgb) <= _luminance(res_plain.rgb)


def test_length_floor_short_vs_long() -> None:
    """
    Kurzer Text 'rg' wird aufgehellt, langer Text mit gleicher r/g-Verteilung bleibt
    näher an 128/128 (ohne Floor wäre identisch).
    """
    base_cfg = ComputeConfig(
        mode=ComputeMode.FREQ,
        punctuation_mods=False,
        apply_length_floor=True,
    )
    # gleicher Buchstabenmix, aber unterschiedlich lange Eingaben
    res_short = compute_color("rg", base_cfg)              # sehr kurz -> hell
    res_long = compute_color("rg " * 20, base_cfg)         # viele sichtbare Zeichen -> gedämpfter

    assert max(res_short.rgb) > max(res_long.rgb)


def test_denominator_visible_vs_letters() -> None:
    """
    Bei 'r--' ist die Basis für VISIBLE größer (inkl. '-'), daher ist Rot-Kanal
    kleiner als bei LETTERS (nur 'r').
    """
    txt = "r--"
    res_visible = compute_color(
        txt,
        ComputeConfig(
            mode=ComputeMode.FREQ,
            denominator=Denominator.VISIBLE,
            punctuation_mods=False,
            apply_length_floor=False,
        ),
    )
    res_letters = compute_color(
        txt,
        ComputeConfig(
            mode=ComputeMode.FREQ,
            denominator=Denominator.LETTERS,
            punctuation_mods=False,
            apply_length_floor=False,
        ),
    )
    assert res_visible.rgb[0] < res_letters.rgb[0]  # Rot kleiner bei größerem Nenner


def test_anchor_mode_prefers_blue_for_a() -> None:
    """
    Anker-Modus: 'a' liegt näher bei 'b' (Index 1) → Blau sollte dominieren.
    """
    cfg = ComputeConfig(
        mode=ComputeMode.ANCHOR,
        punctuation_mods=False,
        apply_length_floor=False,
    )
    res = compute_color("aaa", cfg)
    r, g, b = res.rgb
    assert b >= r and b >= g


def test_anchor_mode_prefers_red_for_t() -> None:
    """Anker-Modus: 't' (Index 19) liegt näher an 'r' (17) → Rot dominiert."""
    cfg = ComputeConfig(
        mode=ComputeMode.ANCHOR,
        punctuation_mods=False,
        apply_length_floor=False,
    )
    res = compute_color("tttt", cfg)
    r, g, b = res.rgb
    assert r >= g and r >= b


def test_color_name_nonempty() -> None:
    """
    Namensauflösung: Unabhängig von der Web-API sollte immer ein nicht-leerer Name
    zurückkommen (Web → Color.Pizza, sonst HSV-Heuristik).
    """
    cfg = ComputeConfig(
        mode=ComputeMode.FREQ,
        punctuation_mods=False,
        apply_length_floor=False,
    )
    res = compute_color("gruen", cfg)
    assert isinstance(res.name, str) and len(res.name.strip()) > 0
