import numpy as np
import pytest
from scipy.ndimage import affine_transform, fourier_shift, gaussian_filter

from dictk import translation
from dictk.image import PixelCoordinate, stretch, translate
from dictk.rosta import rosta
from dictk.warp import fit, locate


def _locate_kwargs(**overrides):
    kwargs = dict(
        reference_point=PixelCoordinate(x=60, y=60),
        search_center=PixelCoordinate(x=60, y=60),
        kernel_margin_width=15,
        kernel_margin_height=15,
        search_margin_width=30,
        search_margin_height=30,
    )
    kwargs.update(overrides)
    return kwargs


def test_locate_requires_keyword_arguments():
    ref = rosta(width=120, height=120, density=0.4)
    with pytest.raises(TypeError):
        locate(ref, ref)  # type: ignore[misc]


def test_locate_recovers_integer_translation():
    ref = rosta(width=120, height=120, density=0.4)
    cur = translate(arr=ref, dx=-6, dy=8)
    found = locate(reference_image=ref, current_image=cur, **_locate_kwargs())
    assert found.x == pytest.approx(54, abs=1e-3)
    assert found.y == pytest.approx(68, abs=1e-3)


@pytest.mark.parametrize("dx", [0.1, 0.3, 0.5, 0.7, 0.9])
def test_locate_recovers_fractional_translation(dx):
    # An exact, Fourier-domain shift of a band-limited image, not
    # `image.translate`: bilinear resampling isn't a true subpixel shift.
    ref = gaussian_filter(rosta(width=120, height=120, density=0.4).astype(float), 1)
    cur = np.fft.ifft2(fourier_shift(np.fft.fft2(ref), (0, dx))).real
    found = locate(reference_image=ref, current_image=cur, **_locate_kwargs())
    phase_found = translation.locate_subpixel(
        reference_image=ref, current_image=cur, **_locate_kwargs()
    )
    assert found.x - 60 == pytest.approx(dx, abs=0.005)
    assert found.y - 60 == pytest.approx(0, abs=0.005)
    assert abs(found.x - 60 - dx) < abs(phase_found.x - 60 - dx)


def test_locate_beats_phase_correlation_under_stretch():
    ref = rosta(width=200, height=120, density=0.4)
    cur = stretch(arr=ref, factor_x=1.02)
    warp_errors, phase_errors = [], []
    for x in range(40, 160, 7):
        kwargs = _locate_kwargs(
            reference_point=PixelCoordinate(x=x, y=60),
            search_center=PixelCoordinate(x=x, y=60),
        )
        warp_found = locate(reference_image=ref, current_image=cur, **kwargs)
        phase_found = translation.locate_subpixel(
            reference_image=ref, current_image=cur, **kwargs
        )
        warp_errors.append(warp_found.x - 1.02 * x)
        phase_errors.append(phase_found.x - 1.02 * x)
    assert np.std(warp_errors) < 0.02
    assert np.std(warp_errors) < np.std(phase_errors)


def test_locate_invalid_max_iterations_raises():
    ref = rosta(width=120, height=120, density=0.4)
    with pytest.raises(ValueError, match="max_iterations"):
        locate(
            reference_image=ref,
            current_image=ref,
            max_iterations=0,
            **_locate_kwargs(),
        )


@pytest.mark.parametrize("tolerance", [0.0, -1e-6])
def test_locate_invalid_tolerance_raises(tolerance):
    ref = rosta(width=120, height=120, density=0.4)
    with pytest.raises(ValueError, match="tolerance"):
        locate(
            reference_image=ref,
            current_image=ref,
            tolerance=tolerance,
            **_locate_kwargs(),
        )


def test_locate_invalid_search_margin_raises():
    ref = rosta(width=120, height=120, density=0.4)
    with pytest.raises(ValueError, match="search_margin_width"):
        locate(
            reference_image=ref,
            current_image=ref,
            **_locate_kwargs(search_margin_width=15),
        )


def test_fit_requires_keyword_arguments():
    ref = rosta(width=120, height=120, density=0.4)
    with pytest.raises(TypeError):
        fit(ref, ref)  # type: ignore[misc]


def test_fit_recovers_affine_deformation():
    # Exact affine deformation about the point, with a quintic spline so
    # the generator itself adds little error.
    ref = gaussian_filter(rosta(width=160, height=160, density=0.4).astype(float), 1)
    deformation = np.array([[1.05, 0.03], [-0.02, 0.97]])
    translation_xy = np.array([3.0, -2.0])
    pivot = np.array([80.0, 80.0])
    inverse = np.linalg.inv(deformation)[::-1, ::-1]
    offset = pivot[::-1] - inverse @ (pivot[::-1] + translation_xy[::-1])
    cur = affine_transform(ref, inverse, offset=offset, order=5)
    point = PixelCoordinate(x=80, y=80)
    warp = fit(
        reference_image=ref,
        current_image=cur,
        **_locate_kwargs(reference_point=point, search_center=point),
    )
    np.testing.assert_allclose(warp[:2, :2], deformation, atol=2e-3)
    np.testing.assert_allclose(warp[:2, 2], translation_xy, atol=1e-2)
    np.testing.assert_array_equal(warp[2], [0.0, 0.0, 1.0])


def test_locate_matches_fit_translation():
    ref = rosta(width=120, height=120, density=0.4)
    cur = stretch(arr=ref, factor_x=1.02)
    warp = fit(reference_image=ref, current_image=cur, **_locate_kwargs())
    found = locate(reference_image=ref, current_image=cur, **_locate_kwargs())
    assert (found.x, found.y) == (60 + warp[0, 2], 60 + warp[1, 2])
