import numpy as np
import pytest

import dictk
from dictk.discontinuity import (
    DiscontinuitySweep,
    _parabolic_vertex,
    locate,
    peak_ratio,
    sweep,
)
from dictk.image import PixelCoordinate, combine, crack_dislocation


def _synthetic_dislocation_fixture():
    """The exact fixture Synthetic Dislocation's own sweep scripts use:
    a 300x300 astronaut+rosta composite, offset=4.0, crack at x=150."""
    width = height = 300
    speckle = dictk.rosta(width=width, height=height, density=0.5)
    photo = dictk.astronaut(width=width, height=height)
    reference_image = combine(a=speckle, b=photo)
    current_image = crack_dislocation(arr=reference_image, offset=4.0)
    return reference_image, current_image


def test_peak_ratio_requires_keyword_arguments():
    with pytest.raises(TypeError):
        peak_ratio(np.zeros((10, 10)))


def test_peak_ratio_non_2d_raises():
    with pytest.raises(ValueError):
        peak_ratio(surface=np.zeros((10, 10, 3)))


def test_peak_ratio_single_peak_returns_zero():
    """A column with one clean peak and nothing else above threshold has ratio 0."""
    surface = np.zeros((21, 5))
    surface[10, :] = 1.0
    assert peak_ratio(surface=surface) == 0.0


def test_peak_ratio_two_equal_peaks_returns_near_one():
    """Two equal-height, well-separated peaks in the same column give ratio ~1.0."""
    surface = np.zeros((21, 5))
    surface[6, :] = 1.0
    surface[14, :] = 1.0
    assert peak_ratio(surface=surface) == pytest.approx(1.0)


def test_peak_ratio_flat_surface_returns_zero():
    """A surface with no positive maximum (nothing to resolve) has ratio 0."""
    surface = np.zeros((10, 10))
    assert peak_ratio(surface=surface) == 0.0


def test_peak_ratio_matches_synthetic_dislocation_straddling_value():
    """Regression anchor: the straddling window Synthetic Dislocation
    itself centers on the crack (x=150, y=150, margins 25/45) shows two
    peaks close enough in height that peak_ratio lands near 1.0, not the
    near-0.0 a clean, unambiguous window would show."""
    from dictk.correlation import zncc
    from dictk.image import PixelCoordinate, subimage

    reference_image, current_image = _synthetic_dislocation_fixture()
    p0 = PixelCoordinate(x=150, y=150)
    kernel_margin, search_margin = 25, 45
    kernel = subimage(
        image=reference_image,
        origin=PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin),
        width=2 * kernel_margin,
        height=2 * kernel_margin,
    )
    search = subimage(
        image=current_image,
        origin=PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin),
        width=2 * search_margin,
        height=2 * search_margin,
    )
    ratio = peak_ratio(surface=zncc(kernel=kernel, search=search))
    assert ratio > 0.9


def test_sweep_requires_keyword_arguments():
    reference_image, current_image = _synthetic_dislocation_fixture()
    with pytest.raises(TypeError):
        sweep(
            reference_image,
            current_image,
            PixelCoordinate(x=100, y=150),
            PixelCoordinate(x=200, y=150),
            11,
            25,
            25,
            45,
            45,
        )


def test_sweep_length_matches_samples():
    reference_image, current_image = _synthetic_dislocation_fixture()
    result = sweep(
        reference_image=reference_image,
        current_image=current_image,
        start=PixelCoordinate(x=100, y=150),
        end=PixelCoordinate(x=200, y=150),
        samples=11,
        kernel_margin_width=25,
        kernel_margin_height=25,
        search_margin_width=45,
        search_margin_height=45,
    )
    assert isinstance(result, DiscontinuitySweep)
    assert len(result.positions) == 11
    assert len(result.peak_ratios) == 11


@pytest.mark.parametrize("samples", [0, 1])
def test_sweep_invalid_samples_raises(samples):
    reference_image, current_image = _synthetic_dislocation_fixture()
    with pytest.raises(ValueError):
        sweep(
            reference_image=reference_image,
            current_image=current_image,
            start=PixelCoordinate(x=100, y=150),
            end=PixelCoordinate(x=200, y=150),
            samples=samples,
            kernel_margin_width=25,
            kernel_margin_height=25,
            search_margin_width=45,
            search_margin_height=45,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kernel_margin_width": 0},
        {"kernel_margin_height": 0},
        {"search_margin_width": 25},
        {"search_margin_height": 25},
    ],
)
def test_sweep_invalid_margins_raises(kwargs):
    reference_image, current_image = _synthetic_dislocation_fixture()
    base = dict(
        kernel_margin_width=25,
        kernel_margin_height=25,
        search_margin_width=45,
        search_margin_height=45,
    )
    base.update(kwargs)
    with pytest.raises(ValueError):
        sweep(
            reference_image=reference_image,
            current_image=current_image,
            start=PixelCoordinate(x=100, y=150),
            end=PixelCoordinate(x=200, y=150),
            samples=11,
            **base,
        )


def test_sweep_peak_ratio_low_away_from_crack():
    """Far from the crack (x=100, well below the x=125 full-clearance
    boundary), the window is unambiguous: peak_ratio is 0."""
    reference_image, current_image = _synthetic_dislocation_fixture()
    result = sweep(
        reference_image=reference_image,
        current_image=current_image,
        start=PixelCoordinate(x=100, y=150),
        end=PixelCoordinate(x=200, y=150),
        samples=101,
        kernel_margin_width=25,
        kernel_margin_height=25,
        search_margin_width=45,
        search_margin_height=45,
    )
    assert result.peak_ratios[0] == 0.0


def test_sweep_peak_ratio_high_at_crack():
    """Centered on the crack (x=150), peak_ratio is near its maximum, 1.0."""
    reference_image, current_image = _synthetic_dislocation_fixture()
    result = sweep(
        reference_image=reference_image,
        current_image=current_image,
        start=PixelCoordinate(x=100, y=150),
        end=PixelCoordinate(x=200, y=150),
        samples=101,
        kernel_margin_width=25,
        kernel_margin_height=25,
        search_margin_width=45,
        search_margin_height=45,
    )
    center_index = result.positions.index(PixelCoordinate(x=150, y=150))
    assert result.peak_ratios[center_index] > 0.9
    assert result.peak_ratios[center_index] == max(result.peak_ratios)


def test_locate_requires_keyword_arguments():
    reference_image, current_image = _synthetic_dislocation_fixture()
    with pytest.raises(TypeError):
        locate(
            reference_image,
            current_image,
            PixelCoordinate(x=100, y=150),
            PixelCoordinate(x=200, y=150),
            101,
            25,
            25,
            45,
            45,
        )


def test_locate_recovers_known_crack_position():
    """The key regression test: locate() finds Synthetic Dislocation's
    known x=150 crack to within 1 pixel -- measured error is ~0.2px."""
    reference_image, current_image = _synthetic_dislocation_fixture()
    found = locate(
        reference_image=reference_image,
        current_image=current_image,
        start=PixelCoordinate(x=100, y=150),
        end=PixelCoordinate(x=200, y=150),
        samples=101,
        kernel_margin_width=25,
        kernel_margin_height=25,
        search_margin_width=45,
        search_margin_height=45,
    )
    assert abs(found.x - 150) < 1.0
    assert found.y == 150.0


def test_locate_endpoint_argmax_raises():
    """A sweep with no interior peak (monotonic or empty signal) raises,
    rather than fabricating a parabolic fit against a nonexistent neighbor."""
    reference_image, current_image = _synthetic_dislocation_fixture()
    with pytest.raises(ValueError):
        # A 2-sample sweep can only ever have its argmax at an endpoint.
        locate(
            reference_image=reference_image,
            current_image=current_image,
            start=PixelCoordinate(x=100, y=150),
            end=PixelCoordinate(x=105, y=150),
            samples=2,
            kernel_margin_width=25,
            kernel_margin_height=25,
            search_margin_width=45,
            search_margin_height=45,
        )


def test_parabolic_vertex_requires_keyword_arguments():
    with pytest.raises(TypeError):
        _parabolic_vertex(0.0, 1.0, 0.0)


def test_parabolic_vertex_matches_known_parabola():
    """y = -(n - 1.3)^2 sampled at n=0,1,2 has a known vertex offset of
    0.3 from index 1."""
    n0, n1, n2 = 0, 1, 2
    y0 = -((n0 - 1.3) ** 2)
    y1 = -((n1 - 1.3) ** 2)
    y2 = -((n2 - 1.3) ** 2)
    assert _parabolic_vertex(y0=y0, y1=y1, y2=y2) == pytest.approx(0.3)


def test_parabolic_vertex_symmetric_points_returns_zero():
    """A parabola already centered on index 1 (symmetric y0/y2) has vertex offset 0."""
    assert _parabolic_vertex(y0=1.0, y1=2.0, y2=1.0) == 0.0


def test_parabolic_vertex_collinear_points_returns_zero():
    """Three collinear points (zero curvature) return 0 rather than
    dividing by zero."""
    assert _parabolic_vertex(y0=1.0, y1=2.0, y2=3.0) == 0.0
