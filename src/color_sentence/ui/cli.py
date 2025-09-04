from __future__ import annotations

from color_sentence.config.config import ComputeConfig
from color_sentence.tts.tts_gtts import GttsSynthesizer

"""
Command-line interface for computing a color from input text.
"""

import argparse

from color_sentence.core.engine import compute_color, prepare_engine
from color_sentence.config.types import Denominator, ComputeMode, ComputeResult

DEFAULT_CONFIG: ComputeConfig = ComputeConfig()


def build_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the CLI.

    Returns:
        A fully configured ArgumentParser instance.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Compute a representative color from a sentence."
    )

    denominator_choices: list[str] = [d.value for d in Denominator]
    mode_choices: list[str] = [m.value for m in ComputeMode]

    parser.add_argument("text", help="Input sentence to analyze.")
    parser.add_argument(
        "--denom",
        choices=denominator_choices,
        default=DEFAULT_CONFIG.denominator.value,
        help="Normalization base for frequency mode.",
    )
    parser.add_argument(
        "--no-punct",
        action="store_true",
        help="Disable punctuation-based brightness/saturation modulation.",
    )
    parser.add_argument(
        "--no-floor",
        action="store_true",
        help="Disable the length-based brightness floor (frequency mode only).",
    )
    parser.add_argument(
        "--mode",
        choices=mode_choices,
        default=ComputeMode.FREQ.value,
        help="Computation mode: 'freq' (letter frequency) or 'anchor' (alphabet anchors).",
    )
    return parser


def main() -> None:
    """
    Parse arguments, compute the color, and print RGB/HEX/Name.
    """
    parser: argparse.ArgumentParser = build_parser()
    args: argparse.Namespace = parser.parse_args()

    config = ComputeConfig(
        speak_enabled=bool(getattr(args, "speak", True)),
        tts_backend=GttsSynthesizer(),
    )
    prepare_engine(config)

    result: ComputeResult = compute_color(args.text, config)
    output: str = f"RGB: {result.rgb}  HEX: {result.hex}  NAME: {result.name}"
    print(output)


if __name__ == "__main__":  # pragma: no cover
    main()
