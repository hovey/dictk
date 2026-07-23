from pathlib import Path

import numpy as np
import pytest

from dictk.imaging import (
    astronaut,
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
    arr = checkerboard(width=40, height=40, count_x=4, count_y=4)
    # Adjacent rectangles along a row must differ.
    rect_width = 40 // 4
    first_rect = arr[0, 0]
    second_rect = arr[0, rect_width]
    assert first_rect != second_rect


@pytest.mark.parametrize("count_x", [0, -1])
def test_checkerboard_invalid_count_x_raises(count_x):
    with pytest.raises(ValueError):
        checkerboard(width=40, height=40, count_x=count_x)


@pytest.mark.parametrize("count_y", [0, -1])
def test_checkerboard_invalid_count_y_raises(count_y):
    with pytest.raises(ValueError):
        checkerboard(width=40, height=40, count_y=count_y)


def test_astronaut_default_shape_and_dtype():
    arr = astronaut()
    assert arr.shape == (512, 512)
    assert arr.dtype == np.uint8


def test_astronaut_is_grayscale():
    arr = astronaut()
    assert arr.ndim == 2


def test_astronaut_resizes():
    arr = astronaut(width=40, height=20)
    assert arr.shape == (20, 40)
    assert arr.dtype == np.uint8


@pytest.mark.parametrize("width", [0, -1])
def test_astronaut_invalid_width_raises(width):
    with pytest.raises(ValueError):
        astronaut(width=width, height=40)


@pytest.mark.parametrize("height", [0, -1])
def test_astronaut_invalid_height_raises(height):
    with pytest.raises(ValueError):
        astronaut(width=40, height=height)


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
