import numpy as np
import pytest

from dictk.grid import generate, locate
from dictk.image import PixelCoordinate, translate
from dictk.rosta import rosta


def test_generate_row_major_order():
    pts = generate(
        origin=PixelCoordinate(x=10, y=20),
        count_x=3,
        count_y=2,
        spacing_x=5,
        spacing_y=7,
    )
    assert pts == [
        PixelCoordinate(x=10, y=20),
        PixelCoordinate(x=15, y=20),
        PixelCoordinate(x=20, y=20),
        PixelCoordinate(x=10, y=27),
        PixelCoordinate(x=15, y=27),
        PixelCoordinate(x=20, y=27),
    ]


def test_generate_independent_counts():
    pts = generate(
        origin=PixelCoordinate(x=0, y=0),
        count_x=4,
        count_y=1,
        spacing_x=1,
        spacing_y=1,
    )
    assert len(pts) == 4


def test_generate_independent_spacing():
    pts = generate(
        origin=PixelCoordinate(x=0, y=0),
        count_x=2,
        count_y=2,
        spacing_x=3,
        spacing_y=9,
    )
    assert pts[1].x - pts[0].x == 3
    assert pts[2].y - pts[0].y == 9


def test_generate_requires_keyword_arguments():
    with pytest.raises(TypeError):
        generate(PixelCoordinate(x=0, y=0), 2, 2, 1, 1)


@pytest.mark.parametrize("count_x", [0, -1])
def test_generate_invalid_count_x_raises(count_x):
    with pytest.raises(ValueError):
        generate(
            origin=PixelCoordinate(x=0, y=0),
            count_x=count_x,
            count_y=2,
            spacing_x=1,
            spacing_y=1,
        )


@pytest.mark.parametrize("count_y", [0, -1])
def test_generate_invalid_count_y_raises(count_y):
    with pytest.raises(ValueError):
        generate(
            origin=PixelCoordinate(x=0, y=0),
            count_x=2,
            count_y=count_y,
            spacing_x=1,
            spacing_y=1,
        )


def _reference_and_current(dx: float, dy: float):
    reference_image = rosta(width=150, height=150, density=0.4)
    current_image = translate(arr=reference_image, dx=dx, dy=dy)
    return reference_image, current_image


def test_locate_batch_recovers_known_translation():
    ref, cur = _reference_and_current(dx=-6, dy=8)
    points = generate(
        origin=PixelCoordinate(x=40, y=40),
        count_x=3,
        count_y=3,
        spacing_x=20,
        spacing_y=20,
    )
    found = locate(
        reference_image=ref,
        current_image=cur,
        reference_points=points,
        kernel_margin_width=15,
        kernel_margin_height=15,
        search_margin_width=30,
        search_margin_height=30,
    )
    assert len(found) == len(points)
    for p0, p1 in zip(points, found):
        assert (p1.x - p0.x, p1.y - p0.y) == (-6, 8)


def test_locate_explicit_search_centers():
    ref, cur = _reference_and_current(dx=-6, dy=8)
    points = generate(
        origin=PixelCoordinate(x=40, y=40),
        count_x=2,
        count_y=2,
        spacing_x=20,
        spacing_y=20,
    )
    # Slightly imperfect guesses -- only need to place the true position
    # within the search area, same as the single-point case.
    rough_guesses = [PixelCoordinate(x=p.x - 3, y=p.y + 2) for p in points]
    found = locate(
        reference_image=ref,
        current_image=cur,
        reference_points=points,
        search_centers=rough_guesses,
        kernel_margin_width=15,
        kernel_margin_height=15,
        search_margin_width=30,
        search_margin_height=30,
    )
    for p0, p1 in zip(points, found):
        assert (p1.x - p0.x, p1.y - p0.y) == (-6, 8)


def test_locate_mismatched_search_centers_length_raises():
    ref, cur = _reference_and_current(dx=0, dy=0)
    points = generate(
        origin=PixelCoordinate(x=40, y=40),
        count_x=2,
        count_y=2,
        spacing_x=20,
        spacing_y=20,
    )
    with pytest.raises(ValueError):
        locate(
            reference_image=ref,
            current_image=cur,
            reference_points=points,
            search_centers=points[:2],
            kernel_margin_width=15,
            kernel_margin_height=15,
            search_margin_width=30,
            search_margin_height=30,
        )


def test_locate_empty_points_returns_empty_list():
    ref, cur = _reference_and_current(dx=0, dy=0)
    found = locate(
        reference_image=ref,
        current_image=cur,
        reference_points=[],
        kernel_margin_width=15,
        kernel_margin_height=15,
        search_margin_width=30,
        search_margin_height=30,
    )
    assert found == []


def test_locate_requires_keyword_arguments():
    arr = np.zeros((50, 50), dtype=np.uint8)
    points = [PixelCoordinate(x=25, y=25)]
    with pytest.raises(TypeError):
        locate(arr, arr, points, None, 10, 10, 20, 20)
