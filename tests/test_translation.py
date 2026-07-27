import numpy as np
import pytest

from dictk.image import PixelCoordinate, translate
from dictk.rosta import rosta
from dictk.translation import locate


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
