"""Command-line interface for dictk.

Each subcommand is a thin wrapper around the corresponding `dictk` API
function: it calls the array-returning API function, then writes the result
to disk. See the `dictk` package docstring for the CLI/API split.
"""

import argparse
from pathlib import Path
import sys

import numpy as np

from dictk.imaging import checkerboard, write_image
from dictk.rosta import rosta

IMAGE_FORMATS = ("tiff", "png", "jpg", "svg")


def _rosta_filename(
    width: int,
    height: int,
    dot_size: float,
    density: float,
    smoothness: float,
    image_format: str,
) -> str:
    return (
        f"rosta_{width}w_by_{height}h"
        f"_dot_{dot_size}_den_{density}_smo_{smoothness}.{image_format}"
    )


def _checkerboard_filename(
    width: int, height: int, squares_x: int, squares_y: int, image_format: str
) -> str:
    return f"checkerboard_{width}w_by_{height}h_{squares_x}x{squares_y}.{image_format}"


def _write_output(arr: np.ndarray, output: Path | None, filename: str) -> int:
    output_dir = output if output else Path.cwd()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / filename
        write_image(arr, path)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Saved image: {path}")
    return 0


def _rosta_create(args: argparse.Namespace) -> int:
    try:
        arr = rosta(
            width=args.width,
            height=args.height,
            dot_size=args.dot_size,
            density=args.density,
            smoothness=args.smoothness,
            random_seed=args.random_seed,
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    filename = _rosta_filename(
        args.width,
        args.height,
        args.dot_size,
        args.density,
        args.smoothness,
        args.format,
    )
    return _write_output(arr, args.output, filename)


def _checkerboard_create(args: argparse.Namespace) -> int:
    arr = checkerboard(
        width=args.width,
        height=args.height,
        squares_x=args.squares_x,
        squares_y=args.squares_y,
    )

    filename = _checkerboard_filename(
        args.width, args.height, args.squares_x, args.squares_y, args.format
    )
    return _write_output(arr, args.output, filename)


def build_parser() -> argparse.ArgumentParser:
    """Build the `dictk` argument parser, with one subparser per subcommand."""
    parser = argparse.ArgumentParser(
        prog="dictk", description="Digital Image Correlation Toolkit"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    rosta_parser = subparsers.add_parser(
        "rosta", help="Create a Rosta speckle pattern and save it as a TIFF image."
    )
    rosta_parser.add_argument(
        "width",
        type=int,
        nargs="?",
        default=200,
        help="Image width in pixels (int), default: %(default)s.",
    )
    rosta_parser.add_argument(
        "height",
        type=int,
        nargs="?",
        default=200,
        help="Image height in pixels (int), default: %(default)s.",
    )
    rosta_parser.add_argument(
        "--dot-size",
        "-s",
        type=float,
        default=4.0,
        help="Dot pattern size factor, 0.0 to 100.0 (float), default: %(default)s.",
    )
    rosta_parser.add_argument(
        "--density",
        "-d",
        type=float,
        default=0.32,
        help="Dot pattern density, 0.0 to 1.0 (float), default: %(default)s.",
    )
    rosta_parser.add_argument(
        "--smoothness",
        "-m",
        type=float,
        default=2.0,
        help="Smoothness factor, 0.0 to 100.0 (float), default: %(default)s.",
    )
    rosta_parser.add_argument(
        "--random-seed",
        "-r",
        type=int,
        default=42,
        help="Seed for reproducible pattern generation (int), default: %(default)s.",
    )
    rosta_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output directory (path), default: current directory.",
    )
    rosta_parser.add_argument(
        "--format",
        "-f",
        choices=IMAGE_FORMATS,
        default="tiff",
        help="Output image format (str), default: %(default)s.",
    )
    rosta_parser.set_defaults(func=_rosta_create)

    checkerboard_parser = subparsers.add_parser(
        "checkerboard",
        help="Create a checkerboard test image and save it as a TIFF image.",
    )
    checkerboard_parser.add_argument(
        "width",
        type=int,
        nargs="?",
        default=200,
        help="Image width in pixels (int), default: %(default)s.",
    )
    checkerboard_parser.add_argument(
        "height",
        type=int,
        nargs="?",
        default=200,
        help="Image height in pixels (int), default: %(default)s.",
    )
    checkerboard_parser.add_argument(
        "--squares-x",
        type=int,
        default=8,
        help="Number of checkerboard squares along the width (int), default: %(default)s.",
    )
    checkerboard_parser.add_argument(
        "--squares-y",
        type=int,
        default=8,
        help="Number of checkerboard squares along the height (int), default: %(default)s.",
    )
    checkerboard_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output directory (path), default: current directory.",
    )
    checkerboard_parser.add_argument(
        "--format",
        "-f",
        choices=IMAGE_FORMATS,
        default="tiff",
        help="Output image format (str), default: %(default)s.",
    )
    checkerboard_parser.set_defaults(func=_checkerboard_create)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the `dictk` console script; returns the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
