from pathlib import Path

import numpy as np
import pytest

from dictk.imaging import (
    checkerboard,
    combine_images,
    describe_image,
    read_image,
    rgba_to_gray,
    write_image,
)


def test_checkerboard_shape_and_dtype():
    arr = checkerboard(width=40, height=20)
    assert arr.shape == (20, 40)
    assert arr.dtype == np.uint8


def test_checkerboard_only_black_or_white():
    arr = checkerboard(width=40, height=20)
    assert set(np.unique(arr)).issubset({0, 255})


def test_checkerboard_alternates():
    arr = checkerboard(width=40, height=40, squares_x=4, squares_y=4)
    # Adjacent squares along a row must differ.
    square_width = 40 // 4
    first_square = arr[0, 0]
    second_square = arr[0, square_width]
    assert first_square != second_square


def test_rgba_to_gray_passthrough_for_2d():
    arr = np.arange(9).reshape(3, 3)
    result = rgba_to_gray(arr)
    assert np.array_equal(result, arr)


def test_rgba_to_gray_averages_rgb():
    arr = np.zeros((2, 2, 3), dtype=np.uint8)
    arr[..., 0] = 30
    arr[..., 1] = 60
    arr[..., 2] = 90
    result = rgba_to_gray(arr)
    assert result.shape == (2, 2)
    assert np.all(result == 60)


def test_rgba_to_gray_invalid_shape_raises():
    with pytest.raises(ValueError):
        rgba_to_gray(np.zeros((2, 2, 5)))


def test_combine_images_shape_and_dtype():
    a = np.full((10, 10), 100, dtype=np.uint8)
    b = np.full((10, 10), 200, dtype=np.uint8)
    combined = combine_images(a, b)
    assert combined.shape == (10, 10)
    assert combined.dtype == np.uint8
    assert combined.max() <= 255


def test_combine_images_normalizes_to_max_255():
    a = np.full((4, 4), 10, dtype=np.uint8)
    b = np.full((4, 4), 10, dtype=np.uint8)
    combined = combine_images(a, b)
    # Uniform input -> uniform output, scaled to the max value of 255.
    assert np.all(combined == 255)


def test_combine_images_shape_mismatch_raises():
    a = np.zeros((10, 10), dtype=np.uint8)
    b = np.zeros((5, 5), dtype=np.uint8)
    with pytest.raises(ValueError):
        combine_images(a, b)


def test_describe_image_grayscale():
    arr = np.zeros((10, 20), dtype=np.uint8)
    description = describe_image(arr)
    assert "Shape: (10, 20)" in description
    assert "grayscale" in description


def test_describe_image_rgb():
    arr = np.zeros((10, 20, 3), dtype=np.uint8)
    description = describe_image(arr)
    assert "RGB" in description


def test_describe_image_rgba():
    arr = np.zeros((10, 20, 4), dtype=np.uint8)
    description = describe_image(arr)
    assert "RGBA" in description


@pytest.mark.parametrize("suffix", ["tiff", "png", "jpg"])
def test_write_image_raster_formats_round_trip(tmp_path: Path, suffix: str):
    arr = checkerboard(width=16, height=8)
    path = tmp_path / f"out.{suffix}"
    write_image(arr, path)

    assert path.exists()
    round_tripped = read_image(path)
    assert round_tripped.shape == arr.shape


def test_write_image_svg_produces_embedded_png(tmp_path: Path):
    arr = checkerboard(width=16, height=8)
    path = tmp_path / "out.svg"
    write_image(arr, path)

    content = path.read_text()
    assert content.startswith("<?xml")
    assert "<svg" in content
    assert 'width="16" height="8"' in content
    assert "data:image/png;base64," in content
    assert content.rstrip().endswith("</svg>")
