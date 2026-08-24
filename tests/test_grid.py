import numpy as np
import pytest

from dictk.correlation import WindowingMethod
from dictk.grid import Executor, elements, generate, locate, locate_subpixel
from dictk.image import PixelCoordinate, stretch, translate
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


def test_elements_requires_keyword_arguments():
    with pytest.raises(TypeError):
        elements(3, 4)


def test_elements_count_matches_multi_point_motion_grid():
    # Multi-Point Motion and Simple Stretch's own 3x4 point grid: 2x3
    # unit cells = 6 elements.
    els = elements(count_x=3, count_y=4)
    assert len(els) == 6


def test_elements_corner_order_of_a_single_cell():
    # A 2x2 point grid is exactly 1 element: points 0,1,2,3 at row-major
    # indices (top_left=0, top_right=1, bottom_right=3, bottom_left=2).
    els = elements(count_x=2, count_y=2)
    assert els == [(0, 1, 3, 2)]


def test_elements_row_major_order():
    # A 3x3 point grid is 2x2 = 4 elements. Row 0 of elements first (both
    # cells sharing point-grid row 0-1), then row 1 (point-grid rows 1-2).
    els = elements(count_x=3, count_y=3)
    assert els == [
        (0, 1, 4, 3),
        (1, 2, 5, 4),
        (3, 4, 7, 6),
        (4, 5, 8, 7),
    ]


def test_elements_indices_match_generate_points():
    # A live cross-check: elements()'s indices, applied to generate()'s
    # own output, must recover a geometrically sane quad (top_left/
    # top_right share a y, top_left/bottom_left share an x).
    points = generate(
        origin=PixelCoordinate(x=0, y=0),
        count_x=3,
        count_y=3,
        spacing_x=1,
        spacing_y=1,
    )
    top_left, top_right, bottom_right, bottom_left = elements(count_x=3, count_y=3)[0]
    assert points[top_left].y == points[top_right].y
    assert points[top_left].x == points[bottom_left].x
    assert points[bottom_right].y == points[bottom_left].y
    assert points[bottom_right].x == points[top_right].x
    assert points[top_left].y < points[bottom_left].y


@pytest.mark.parametrize("count_x", [0, 1, -1])
def test_elements_invalid_count_x_raises(count_x):
    with pytest.raises(ValueError):
        elements(count_x=count_x, count_y=2)


@pytest.mark.parametrize("count_y", [0, 1, -1])
def test_elements_invalid_count_y_raises(count_y):
    with pytest.raises(ValueError):
        elements(count_x=2, count_y=count_y)


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


def test_locate_windowing_none_matches_default():
    """windowing=None is identical to omitting the argument entirely."""
    ref, cur = _reference_and_current(dx=-6, dy=8)
    points = generate(
        origin=PixelCoordinate(x=40, y=40),
        count_x=3,
        count_y=3,
        spacing_x=20,
        spacing_y=20,
    )
    kwargs = dict(
        reference_image=ref,
        current_image=cur,
        reference_points=points,
        kernel_margin_width=15,
        kernel_margin_height=15,
        search_margin_width=30,
        search_margin_height=30,
    )
    assert locate(**kwargs) == locate(**kwargs, windowing=None)


@pytest.mark.parametrize("method", [WindowingMethod.HANN, WindowingMethod.HAMMING])
def test_locate_windowing_still_recovers_known_translation(method):
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
        windowing=method,
    )
    for p0, p1 in zip(points, found):
        assert (p1.x - p0.x, p1.y - p0.y) == (-6, 8)


def test_locate_max_workers_none_matches_default():
    """max_workers=None is identical to omitting the argument entirely."""
    ref, cur = _reference_and_current(dx=-6, dy=8)
    points = generate(
        origin=PixelCoordinate(x=40, y=40),
        count_x=3,
        count_y=3,
        spacing_x=20,
        spacing_y=20,
    )
    kwargs = dict(
        reference_image=ref,
        current_image=cur,
        reference_points=points,
        kernel_margin_width=15,
        kernel_margin_height=15,
        search_margin_width=30,
        search_margin_height=30,
    )
    assert locate(**kwargs) == locate(**kwargs, max_workers=None)


@pytest.mark.parametrize("executor", [Executor.THREAD, Executor.PROCESS])
@pytest.mark.parametrize("max_workers", [1, 2, 4])
def test_locate_max_workers_matches_sequential(max_workers, executor):
    """Concurrent results match the sequential path exactly, same order,
    same values -- for both pool types, and even at max_workers=1."""
    ref, cur = _reference_and_current(dx=-6, dy=8)
    points = generate(
        origin=PixelCoordinate(x=40, y=40),
        count_x=3,
        count_y=3,
        spacing_x=20,
        spacing_y=20,
    )
    kwargs = dict(
        reference_image=ref,
        current_image=cur,
        reference_points=points,
        kernel_margin_width=15,
        kernel_margin_height=15,
        search_margin_width=30,
        search_margin_height=30,
    )
    sequential = locate(**kwargs)
    concurrent = locate(**kwargs, max_workers=max_workers, executor=executor)
    assert concurrent == sequential


@pytest.mark.parametrize("max_workers", [0, -1])
def test_locate_max_workers_invalid_raises(max_workers):
    arr = np.zeros((50, 50), dtype=np.uint8)
    points = [PixelCoordinate(x=25, y=25)]
    with pytest.raises(ValueError):
        locate(
            reference_image=arr,
            current_image=arr,
            reference_points=points,
            kernel_margin_width=10,
            kernel_margin_height=10,
            search_margin_width=20,
            search_margin_height=20,
            max_workers=max_workers,
        )


def test_locate_subpixel_requires_keyword_arguments():
    arr = np.zeros((50, 50), dtype=np.uint8)
    points = [PixelCoordinate(x=25, y=25)]
    with pytest.raises(TypeError):
        locate_subpixel(arr, arr, points, None, 10, 10, 20, 20)


def test_locate_subpixel_batch_matches_locate_for_integer_displacement():
    # atol matches translation.locate_subpixel's own regression anchor --
    # translate() bilinear-interpolates even integer dx/dy, so a small
    # residual error is expected here, not a bug.
    ref, cur = _reference_and_current(dx=-6, dy=8)
    points = generate(
        origin=PixelCoordinate(x=40, y=40),
        count_x=3,
        count_y=3,
        spacing_x=20,
        spacing_y=20,
    )
    found = locate_subpixel(
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
        assert np.isclose(p1.x - p0.x, -6, atol=0.05)
        assert np.isclose(p1.y - p0.y, 8, atol=0.05)


def test_locate_subpixel_empty_points_returns_empty_list():
    ref, cur = _reference_and_current(dx=0, dy=0)
    found = locate_subpixel(
        reference_image=ref,
        current_image=cur,
        reference_points=[],
        kernel_margin_width=15,
        kernel_margin_height=15,
        search_margin_width=30,
        search_margin_height=30,
    )
    assert found == []


def test_locate_subpixel_mismatched_search_centers_length_raises():
    ref, cur = _reference_and_current(dx=0, dy=0)
    points = generate(
        origin=PixelCoordinate(x=40, y=40),
        count_x=2,
        count_y=2,
        spacing_x=20,
        spacing_y=20,
    )
    with pytest.raises(ValueError):
        locate_subpixel(
            reference_image=ref,
            current_image=cur,
            reference_points=points,
            search_centers=points[:2],
            kernel_margin_width=15,
            kernel_margin_height=15,
            search_margin_width=30,
            search_margin_height=30,
        )


@pytest.mark.parametrize("executor", [Executor.THREAD, Executor.PROCESS])
@pytest.mark.parametrize("max_workers", [1, 2, 4])
def test_locate_subpixel_max_workers_matches_sequential(max_workers, executor):
    ref, cur = _reference_and_current(dx=-6, dy=8)
    points = generate(
        origin=PixelCoordinate(x=40, y=40),
        count_x=3,
        count_y=3,
        spacing_x=20,
        spacing_y=20,
    )
    kwargs = dict(
        reference_image=ref,
        current_image=cur,
        reference_points=points,
        kernel_margin_width=15,
        kernel_margin_height=15,
        search_margin_width=30,
        search_margin_height=30,
    )
    sequential = locate_subpixel(**kwargs)
    concurrent = locate_subpixel(**kwargs, max_workers=max_workers, executor=executor)
    assert concurrent == sequential


@pytest.mark.parametrize("max_workers", [0, -1])
def test_locate_subpixel_max_workers_invalid_raises(max_workers):
    arr = np.zeros((50, 50), dtype=np.uint8)
    points = [PixelCoordinate(x=25, y=25)]
    with pytest.raises(ValueError):
        locate_subpixel(
            reference_image=arr,
            current_image=arr,
            reference_points=points,
            kernel_margin_width=10,
            kernel_margin_height=10,
            search_margin_width=20,
            search_margin_height=20,
            max_workers=max_workers,
        )


def test_locate_subpixel_recovers_true_fractional_target_more_closely_than_locate():
    """Same reasoning as translation.locate_subpixel's own regression
    anchor, at batch scale: a uniaxial stretch's true targets are
    generally fractional, and locate_subpixel() should land closer to
    them than locate()'s own truncated results, on average."""
    reference_image = rosta(width=200, height=200, density=0.4)
    factor_x = 1.02
    current_image = stretch(arr=reference_image, factor_x=factor_x)
    points = generate(
        origin=PixelCoordinate(x=18, y=16),
        count_x=10,
        count_y=10,
        spacing_x=5,
        spacing_y=5,
    )
    kwargs = dict(
        reference_image=reference_image,
        current_image=current_image,
        reference_points=points,
        kernel_margin_width=20,
        kernel_margin_height=20,
        search_margin_width=48,
        search_margin_height=52,
    )
    integer_found = locate(**kwargs)
    subpixel_found = locate_subpixel(**kwargs)
    true_x = [p.x * factor_x for p in points]
    integer_error = np.mean([abs(f.x - tx) for f, tx in zip(integer_found, true_x)])
    subpixel_error = np.mean([abs(f.x - tx) for f, tx in zip(subpixel_found, true_x)])
    assert subpixel_error < integer_error
