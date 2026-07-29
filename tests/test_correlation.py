import numpy as np
import pytest

from dictk.correlation import cc, ncc, zcc, zncc
from dictk.image import PixelCoordinate, subimage, translate
from dictk.rosta import rosta

CORRELATION_FUNCTIONS = [cc, ncc, zcc, zncc]


def _kernel_and_search(dx: float, dy: float, kernel_margin: int, search_margin: int):
    reference_image = rosta(width=200, height=200, density=0.5)
    current_image = translate(arr=reference_image, dx=dx, dy=dy)
    p0 = PixelCoordinate(x=100, y=75)
    kernel = subimage(
        image=reference_image,
        origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin),
        width=2 * kernel_margin,
        height=2 * kernel_margin,
    )
    search_origin = PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin)
    search = subimage(
        image=current_image,
        origin=search_origin,
        width=2 * search_margin,
        height=2 * search_margin,
    )
    return kernel, search, search_origin, kernel_margin


@pytest.mark.parametrize("correlation_function", CORRELATION_FUNCTIONS)
def test_surface_shape(correlation_function):
    kernel = np.zeros((20, 30), dtype=np.uint8)
    search = np.zeros((50, 70), dtype=np.uint8)
    surface = correlation_function(kernel=kernel, search=search)
    assert surface.shape == (50 - 20 + 1, 70 - 30 + 1)


@pytest.mark.parametrize("correlation_function", CORRELATION_FUNCTIONS)
def test_requires_keyword_arguments(correlation_function):
    kernel = np.zeros((10, 10), dtype=np.uint8)
    search = np.zeros((20, 20), dtype=np.uint8)
    with pytest.raises(TypeError):
        correlation_function(kernel, search)


@pytest.mark.parametrize("correlation_function", CORRELATION_FUNCTIONS)
def test_search_smaller_than_kernel_raises(correlation_function):
    kernel = np.zeros((20, 20), dtype=np.uint8)
    search = np.zeros((10, 10), dtype=np.uint8)
    with pytest.raises(ValueError):
        correlation_function(kernel=kernel, search=search)


@pytest.mark.parametrize("correlation_function", CORRELATION_FUNCTIONS)
def test_non_2d_kernel_raises(correlation_function):
    kernel = np.zeros((10, 10, 3), dtype=np.uint8)
    search = np.zeros((20, 20), dtype=np.uint8)
    with pytest.raises(ValueError):
        correlation_function(kernel=kernel, search=search)


@pytest.mark.parametrize("correlation_function", CORRELATION_FUNCTIONS)
def test_non_2d_search_raises(correlation_function):
    kernel = np.zeros((10, 10), dtype=np.uint8)
    search = np.zeros((20, 20, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        correlation_function(kernel=kernel, search=search)


@pytest.mark.parametrize("correlation_function", CORRELATION_FUNCTIONS)
def test_peak_recovers_known_translation(correlation_function):
    kernel, search, search_origin, kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    surface = correlation_function(kernel=kernel, search=search)
    dy, dx = np.unravel_index(np.argmax(surface), surface.shape)
    found = PixelCoordinate(
        x=search_origin.x + dx + kernel_margin,
        y=search_origin.y + dy + kernel_margin,
    )
    assert (found.x, found.y) == (94, 83)


def test_ncc_invariant_to_contrast_scaling():
    kernel, search, search_origin, kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    search_scaled = search.astype(np.float64) * 1.7

    surface = ncc(kernel=kernel, search=search)
    surface_scaled = ncc(kernel=kernel, search=search_scaled)
    assert np.allclose(surface, surface_scaled)

    # cc(), by contrast, is not invariant to the same scaling.
    cc_surface = cc(kernel=kernel, search=search)
    cc_surface_scaled = cc(kernel=kernel, search=search_scaled)
    assert not np.allclose(cc_surface, cc_surface_scaled)


def test_zcc_invariant_to_brightness_offset():
    kernel, search, search_origin, kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    search_shifted = search.astype(np.float64) + 30

    surface = zcc(kernel=kernel, search=search)
    surface_shifted = zcc(kernel=kernel, search=search_shifted)
    assert np.allclose(surface, surface_shifted)

    # cc(), by contrast, is not invariant to the same brightness offset.
    cc_surface = cc(kernel=kernel, search=search)
    cc_surface_shifted = cc(kernel=kernel, search=search_shifted)
    assert not np.allclose(cc_surface, cc_surface_shifted)


def test_zncc_invariant_to_brightness_and_contrast():
    kernel, search, search_origin, kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    alpha, beta = 1.7, 30.0
    search_transformed = alpha * search.astype(np.float64) + beta

    surface = zncc(kernel=kernel, search=search)
    surface_transformed = zncc(kernel=kernel, search=search_transformed)
    assert np.allclose(surface, surface_transformed)

    # cc(), by contrast, is not invariant to this brightness+contrast change.
    cc_surface = cc(kernel=kernel, search=search)
    cc_surface_transformed = cc(kernel=kernel, search=search_transformed)
    assert not np.allclose(cc_surface, cc_surface_transformed)


def test_cc_value_matches_hand_computed_sum():
    kernel, search, _search_origin, _kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    surface = cc(kernel=kernel, search=search)
    dy, dx = 10, 15
    window = search[dy : dy + kernel.shape[0], dx : dx + kernel.shape[1]]
    expected = float(np.sum(window.astype(np.float64) * kernel.astype(np.float64)))
    assert surface[dy, dx] == pytest.approx(expected)
