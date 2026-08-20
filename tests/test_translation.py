import numpy as np
import pytest

from dictk.correlation import WindowingMethod
from dictk.image import PixelCoordinate, stretch, translate
from dictk.rosta import rosta
from dictk.translation import locate, locate_subpixel


def _reference_and_current(dx: float, dy: float):
    reference_image = rosta(width=120, height=120, density=0.4)
    current_image = translate(arr=reference_image, dx=dx, dy=dy)
    return reference_image, current_image


def test_locate_recovers_known_translation():
    ref, cur = _reference_and_current(dx=-6, dy=8)
    p0 = PixelCoordinate(x=60, y=60)
    p1 = locate(
        reference_image=ref,
        current_image=cur,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=20,
        kernel_margin_height=20,
        search_margin_width=35,
        search_margin_height=35,
    )
    assert (p1.x - p0.x, p1.y - p0.y) == (-6, 8)


def test_locate_with_rectangular_kernel_and_search_area():
    ref, cur = _reference_and_current(dx=-6, dy=8)
    p0 = PixelCoordinate(x=60, y=60)
    p1 = locate(
        reference_image=ref,
        current_image=cur,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=12,
        kernel_margin_height=20,
        search_margin_width=25,
        search_margin_height=40,
    )
    assert (p1.x - p0.x, p1.y - p0.y) == (-6, 8)


def test_locate_search_center_as_imperfect_estimate():
    # search_center only needs to place the true position within the
    # search area -- it isn't the answer, just where to start looking.
    ref, cur = _reference_and_current(dx=-6, dy=8)
    p0 = PixelCoordinate(x=60, y=60)
    rough_guess = PixelCoordinate(x=55, y=65)
    p1 = locate(
        reference_image=ref,
        current_image=cur,
        reference_point=p0,
        search_center=rough_guess,
        kernel_margin_width=20,
        kernel_margin_height=20,
        search_margin_width=35,
        search_margin_height=35,
    )
    assert (p1.x - p0.x, p1.y - p0.y) == (-6, 8)


def test_locate_recovers_displacement_beyond_kernel_margin_both_directions():
    # Regression test for a real, silent bug: kernel_padded's content used
    # to stay anchored at the padded array's top-left corner (rather than
    # centered), which made the recoverable displacement asymmetric --
    # unbounded (up to search_margin) in the negative direction, but
    # capped at exactly kernel_margin in the positive direction, past
    # which locate() returned a confidently wrong position (an FFT
    # circular-correlation wraparound) instead of failing visibly. Both
    # dx here exceed kernel_margin_width (15); both must still resolve
    # correctly now that kernel_padded is centered instead.
    p0 = PixelCoordinate(x=60, y=60)
    for dx in (25, -25):
        ref, cur = _reference_and_current(dx=dx, dy=0)
        p1 = locate(
            reference_image=ref,
            current_image=cur,
            reference_point=p0,
            search_center=p0,
            kernel_margin_width=15,
            kernel_margin_height=15,
            search_margin_width=40,
            search_margin_height=40,
        )
        assert (p1.x - p0.x, p1.y - p0.y) == (dx, 0)


def test_locate_point_near_edge_uses_zero_padding():
    # Near the top-left corner: kernel/search extraction goes out of
    # image bounds and relies on subimage()'s zero-padding rather than
    # raising or misbehaving.
    ref, cur = _reference_and_current(dx=-2, dy=3)
    p0 = PixelCoordinate(x=10, y=10)
    p1 = locate(
        reference_image=ref,
        current_image=cur,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=8,
        kernel_margin_height=8,
        search_margin_width=15,
        search_margin_height=15,
    )
    assert (p1.x - p0.x, p1.y - p0.y) == (-2, 3)


@pytest.mark.parametrize("kernel_margin_width", [0, -1])
def test_locate_invalid_kernel_margin_width_raises(kernel_margin_width):
    arr = np.zeros((50, 50), dtype=np.uint8)
    p = PixelCoordinate(x=25, y=25)
    with pytest.raises(ValueError):
        locate(
            reference_image=arr,
            current_image=arr,
            reference_point=p,
            search_center=p,
            kernel_margin_width=kernel_margin_width,
            kernel_margin_height=10,
            search_margin_width=20,
            search_margin_height=20,
        )


@pytest.mark.parametrize("kernel_margin_height", [0, -1])
def test_locate_invalid_kernel_margin_height_raises(kernel_margin_height):
    arr = np.zeros((50, 50), dtype=np.uint8)
    p = PixelCoordinate(x=25, y=25)
    with pytest.raises(ValueError):
        locate(
            reference_image=arr,
            current_image=arr,
            reference_point=p,
            search_center=p,
            kernel_margin_width=10,
            kernel_margin_height=kernel_margin_height,
            search_margin_width=20,
            search_margin_height=20,
        )


def test_locate_search_margin_width_not_greater_than_kernel_raises():
    arr = np.zeros((50, 50), dtype=np.uint8)
    p = PixelCoordinate(x=25, y=25)
    with pytest.raises(ValueError):
        locate(
            reference_image=arr,
            current_image=arr,
            reference_point=p,
            search_center=p,
            kernel_margin_width=20,
            kernel_margin_height=10,
            search_margin_width=20,
            search_margin_height=20,
        )


def test_locate_search_margin_height_not_greater_than_kernel_raises():
    arr = np.zeros((50, 50), dtype=np.uint8)
    p = PixelCoordinate(x=25, y=25)
    with pytest.raises(ValueError):
        locate(
            reference_image=arr,
            current_image=arr,
            reference_point=p,
            search_center=p,
            kernel_margin_width=10,
            kernel_margin_height=20,
            search_margin_width=20,
            search_margin_height=20,
        )


def test_locate_requires_keyword_arguments():
    arr = np.zeros((50, 50), dtype=np.uint8)
    p = PixelCoordinate(x=25, y=25)
    with pytest.raises(TypeError):
        locate(arr, arr, p, p, 10, 10, 20, 20)


def test_locate_windowing_none_matches_default():
    """windowing=None is identical to omitting the argument entirely."""
    ref, cur = _reference_and_current(dx=-6, dy=8)
    p0 = PixelCoordinate(x=60, y=60)
    kwargs = dict(
        reference_image=ref,
        current_image=cur,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=20,
        kernel_margin_height=20,
        search_margin_width=35,
        search_margin_height=35,
    )
    assert locate(**kwargs) == locate(**kwargs, windowing=None)


@pytest.mark.parametrize("method", [WindowingMethod.HANN, WindowingMethod.HAMMING])
def test_locate_windowing_still_recovers_known_translation(method):
    ref, cur = _reference_and_current(dx=-6, dy=8)
    p0 = PixelCoordinate(x=60, y=60)
    p1 = locate(
        reference_image=ref,
        current_image=cur,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=20,
        kernel_margin_height=20,
        search_margin_width=35,
        search_margin_height=35,
        windowing=method,
    )
    assert (p1.x - p0.x, p1.y - p0.y) == (-6, 8)


def test_locate_subpixel_requires_keyword_arguments():
    arr = np.zeros((50, 50), dtype=np.uint8)
    p = PixelCoordinate(x=25, y=25)
    with pytest.raises(TypeError):
        locate_subpixel(arr, arr, p, p, 10, 10, 20, 20)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(kernel_margin_width=0),
        dict(kernel_margin_height=0),
        dict(search_margin_width=10),
        dict(search_margin_height=10),
        dict(upsample_factor=0),
    ],
)
def test_locate_subpixel_invalid_arguments_raise(kwargs):
    arr = np.zeros((50, 50), dtype=np.uint8)
    p = PixelCoordinate(x=25, y=25)
    base = dict(
        reference_image=arr,
        current_image=arr,
        reference_point=p,
        search_center=p,
        kernel_margin_width=10,
        kernel_margin_height=10,
        search_margin_width=20,
        search_margin_height=20,
    )
    with pytest.raises(ValueError):
        locate_subpixel(**{**base, **kwargs})


def test_locate_subpixel_matches_locate_for_integer_displacement():
    """A pure integer translation's true target is already an integer --
    subpixel refinement should land close to it. Not exactly: translate()
    uses the same backward-mapping bilinear interpolation as stretch()
    even for integer dx/dy (see its own docstring), so a small residual
    error is expected here too, not a bug -- atol matches that, not an
    unrealistic exact-recovery expectation."""
    ref, cur = _reference_and_current(dx=-6, dy=8)
    p0 = PixelCoordinate(x=60, y=60)
    p1 = locate_subpixel(
        reference_image=ref,
        current_image=cur,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=20,
        kernel_margin_height=20,
        search_margin_width=35,
        search_margin_height=35,
    )
    assert np.isclose(p1.x - p0.x, -6, atol=0.05)
    assert np.isclose(p1.y - p0.y, 8, atol=0.05)


def test_locate_subpixel_recovers_true_fractional_target_more_closely_than_locate():
    """A uniaxial stretch's own true target is generally fractional, not
    an integer -- locate()'s own truncated answer is necessarily off by
    some amount, but locate_subpixel() should land measurably closer to
    the true value, not just report a different-but-equally-wrong one."""
    reference_image = rosta(width=200, height=200, density=0.4)
    factor_x = 1.02
    current_image = stretch(arr=reference_image, factor_x=factor_x)
    p0 = PixelCoordinate(x=63, y=100)  # 63 * 1.02 = 64.26, not an integer
    true_x = p0.x * factor_x

    integer_result = locate(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=20,
        kernel_margin_height=20,
        search_margin_width=48,
        search_margin_height=52,
    )
    subpixel_result = locate_subpixel(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=20,
        kernel_margin_height=20,
        search_margin_width=48,
        search_margin_height=52,
    )
    assert abs(subpixel_result.x - true_x) < abs(integer_result.x - true_x)
