import numpy as np
import pytest

from dictk.correlation import (
    WindowingMethod,
    cc,
    ncc,
    phase_correlation,
    window,
    zcc,
    zncc,
)
from dictk.image import PixelCoordinate, subimage, translate
from dictk.rosta import rosta
from dictk.translation import locate

CORRELATION_FUNCTIONS = [cc, ncc, zcc, zncc]

# phase_correlation shares cc/ncc/zcc/zncc's input validation (via the same
# _prepare() helper) but not their "valid" output shape -- see below -- so
# it's covered separately by validation-only tests, not the shape-asserting
# or invariance-comparison ones above.
VALIDATION_ONLY_FUNCTIONS = [*CORRELATION_FUNCTIONS, phase_correlation]


def _kernel_and_search(dx: float, dy: float, kernel_margin: int, search_margin: int):
    """Build a kernel/search pair from `reference_image`/`current_image` for a known translation."""
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
    """Each surface has the expected 'valid' shape."""
    kernel = np.zeros((20, 30), dtype=np.uint8)
    search = np.zeros((50, 70), dtype=np.uint8)
    surface = correlation_function(kernel=kernel, search=search)
    assert surface.shape == (50 - 20 + 1, 70 - 30 + 1)


@pytest.mark.parametrize("correlation_function", VALIDATION_ONLY_FUNCTIONS)
def test_requires_keyword_arguments(correlation_function):
    """Positional arguments are rejected."""
    kernel = np.zeros((10, 10), dtype=np.uint8)
    search = np.zeros((20, 20), dtype=np.uint8)
    with pytest.raises(TypeError):
        correlation_function(kernel, search)


@pytest.mark.parametrize("correlation_function", VALIDATION_ONLY_FUNCTIONS)
def test_search_smaller_than_kernel_raises(correlation_function):
    """A search smaller than kernel raises ValueError."""
    kernel = np.zeros((20, 20), dtype=np.uint8)
    search = np.zeros((10, 10), dtype=np.uint8)
    with pytest.raises(ValueError):
        correlation_function(kernel=kernel, search=search)


@pytest.mark.parametrize("correlation_function", VALIDATION_ONLY_FUNCTIONS)
def test_non_2d_kernel_raises(correlation_function):
    """A non-2D kernel raises ValueError."""
    kernel = np.zeros((10, 10, 3), dtype=np.uint8)
    search = np.zeros((20, 20), dtype=np.uint8)
    with pytest.raises(ValueError):
        correlation_function(kernel=kernel, search=search)


@pytest.mark.parametrize("correlation_function", VALIDATION_ONLY_FUNCTIONS)
def test_non_2d_search_raises(correlation_function):
    """A non-2D search raises ValueError."""
    kernel = np.zeros((10, 10), dtype=np.uint8)
    search = np.zeros((20, 20, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        correlation_function(kernel=kernel, search=search)


@pytest.mark.parametrize("correlation_function", CORRELATION_FUNCTIONS)
def test_peak_recovers_known_translation(correlation_function):
    """The surface's peak recovers a known translation."""
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
    """ncc() is invariant to contrast scaling; cc() is not."""
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
    """zcc() is invariant to a brightness offset; cc() is not."""
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
    """zncc() is invariant to both brightness and contrast; cc() is not."""
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
    """cc()'s value at one offset matches a hand-computed sum."""
    kernel, search, _search_origin, _kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    surface = cc(kernel=kernel, search=search)
    dy, dx = 10, 15
    kernel_sized_window = search[dy : dy + kernel.shape[0], dx : dx + kernel.shape[1]]
    expected = float(
        np.sum(kernel_sized_window.astype(np.float64) * kernel.astype(np.float64))
    )
    assert surface[dy, dx] == pytest.approx(expected)


def test_phase_correlation_surface_shape():
    """phase_correlation()'s surface matches search's own shape."""
    # Unlike cc/ncc/zcc/zncc's smaller "valid" shape, phase_correlation's
    # surface is the same shape as search, since it's computed all at once
    # via FFT rather than excluding any candidate offset.
    kernel = np.zeros((20, 30), dtype=np.uint8)
    search = np.zeros((50, 70), dtype=np.uint8)
    surface = phase_correlation(kernel=kernel, search=search)
    assert surface.shape == search.shape


def test_phase_correlation_recovers_known_translation():
    """phase_correlation()'s peak recovers a known translation."""
    kernel, search, search_origin, kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    surface = phase_correlation(kernel=kernel, search=search)
    dy, dx = np.unravel_index(np.argmax(surface), surface.shape)
    found = PixelCoordinate(
        x=search_origin.x + dx + kernel_margin,
        y=search_origin.y + dy + kernel_margin,
    )
    assert (found.x, found.y) == (94, 83)


def test_phase_correlation_windowing_none_matches_default():
    """windowing=None is identical to omitting the argument entirely."""
    kernel, search, _search_origin, _kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    surface_default = phase_correlation(kernel=kernel, search=search)
    surface_explicit_none = phase_correlation(
        kernel=kernel, search=search, windowing=None
    )
    assert np.array_equal(surface_default, surface_explicit_none)


@pytest.mark.parametrize("method", [WindowingMethod.HANN, WindowingMethod.HAMMING])
def test_phase_correlation_windowing_changes_surface(method):
    """Windowing changes the surface relative to no windowing."""
    kernel, search, _search_origin, _kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    surface = phase_correlation(kernel=kernel, search=search)
    surface_windowed = phase_correlation(kernel=kernel, search=search, windowing=method)
    assert not np.allclose(surface, surface_windowed)


@pytest.mark.parametrize("method", [WindowingMethod.HANN, WindowingMethod.HAMMING])
def test_phase_correlation_windowing_still_recovers_known_translation(method):
    """The peak still recovers the known translation with windowing applied."""
    kernel, search, search_origin, kernel_margin = _kernel_and_search(
        dx=-6, dy=8, kernel_margin=25, search_margin=50
    )
    surface = phase_correlation(kernel=kernel, search=search, windowing=method)
    dy, dx = np.unravel_index(np.argmax(surface), surface.shape)
    found = PixelCoordinate(
        x=search_origin.x + dx + kernel_margin,
        y=search_origin.y + dy + kernel_margin,
    )
    assert (found.x, found.y) == (94, 83)


def test_phase_correlation_matches_locate():
    """phase_correlation() agrees with locate()'s own internal computation."""
    reference_image = rosta(width=200, height=200, density=0.5)
    p0 = PixelCoordinate(x=100, y=75)
    dx, dy = -6, 8
    current_image = translate(arr=reference_image, dx=dx, dy=dy)
    kernel_margin, search_margin = 25, 50

    kernel, search, search_origin, _ = _kernel_and_search(
        dx=dx, dy=dy, kernel_margin=kernel_margin, search_margin=search_margin
    )

    surface = phase_correlation(kernel=kernel, search=search)
    surface_dy, surface_dx = np.unravel_index(np.argmax(surface), surface.shape)

    found_point = locate(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=p0,
        search_center=p0,
        kernel_margin_width=kernel_margin,
        kernel_margin_height=kernel_margin,
        search_margin_width=search_margin,
        search_margin_height=search_margin,
    )
    # locate()'s returned point is r_OP'/F (the point's absolute position);
    # phase_correlation()'s argmax is r_SK/S (the kernel's found offset
    # within search's own frame). Converting between them means subtracting
    # both search's origin *and* kernel_margin (the point's fixed offset
    # from the kernel's own top-left corner) -- not just search's origin.
    locate_offset_x = found_point.x - search_origin.x - kernel_margin
    locate_offset_y = found_point.y - search_origin.y - kernel_margin

    assert (surface_dx, surface_dy) == (locate_offset_x, locate_offset_y)


def test_window_requires_keyword_arguments():
    """Positional arguments are rejected."""
    arr = np.ones((10, 10))
    with pytest.raises(TypeError):
        window(arr)


def test_window_non_2d_raises():
    """A non-2D array raises ValueError."""
    arr = np.ones((10, 10, 3))
    with pytest.raises(ValueError):
        window(arr=arr)


def test_window_preserves_shape():
    """window() preserves the input array's shape."""
    arr = np.ones((20, 30))
    windowed = window(arr=arr)
    assert windowed.shape == arr.shape


def test_window_default_method_is_hann():
    """The default method is Hann."""
    arr = np.ones((20, 30))
    assert np.array_equal(window(arr=arr), window(arr=arr, method=WindowingMethod.HANN))


def test_window_hann_tapers_edges_to_exactly_zero():
    """Hann tapers every edge to exactly 0."""
    arr = np.ones((20, 30))
    windowed = window(arr=arr, method=WindowingMethod.HANN)
    assert np.all(windowed[0, :] == 0.0)
    assert np.all(windowed[-1, :] == 0.0)
    assert np.all(windowed[:, 0] == 0.0)
    assert np.all(windowed[:, -1] == 0.0)


def test_window_hann_center_value_matches_original():
    """A Hann window's center value is exactly 1.0."""
    # Odd-sized so there's an exact center sample, where a Hann window
    # (both row and column) evaluates to exactly 1.0.
    arr = np.ones((21, 31))
    windowed = window(arr=arr, method=WindowingMethod.HANN)
    assert windowed[10, 15] == pytest.approx(1.0)


def test_window_hamming_does_not_taper_edges_to_zero():
    """Hamming, unlike Hann, does not taper edges to 0."""
    arr = np.ones((20, 30))
    windowed = window(arr=arr, method=WindowingMethod.HAMMING)
    assert not np.any(windowed[0, :] == 0.0)
    assert not np.any(windowed[:, 0] == 0.0)


def test_window_hamming_corner_value_matches_hand_computed():
    """Hamming's corner value matches a hand-computed product."""
    # Hamming's 1D window is exactly 0.08 at both edges; the 2D window is
    # the outer product of the row and column windows, so an all-ones
    # array's corner comes out to 0.08 * 0.08.
    arr = np.ones((20, 30))
    windowed = window(arr=arr, method=WindowingMethod.HAMMING)
    assert windowed[0, 0] == pytest.approx(0.08 * 0.08)
