import numpy as np
import pytest

from dictk.core import zero_normalized_cross_correlation


def test_identical_arrays_give_perfect_correlation():
    a = np.array([[1.0, 2.0], [3.0, 4.0]])
    assert zero_normalized_cross_correlation(a, a) == pytest.approx(1.0)


def test_inverted_arrays_give_perfect_anticorrelation():
    a = np.array([1.0, 2.0, 3.0, 4.0])
    b = -a
    assert zero_normalized_cross_correlation(a, b) == pytest.approx(-1.0)


def test_brightness_and_contrast_shift_is_invariant():
    rng = np.random.default_rng(0)
    a = rng.normal(size=(8, 8))
    b = 3.0 * a + 5.0
    assert zero_normalized_cross_correlation(a, b) == pytest.approx(1.0)


def test_constant_array_yields_zero():
    a = np.full((4, 4), 7.0)
    b = np.random.default_rng(1).normal(size=(4, 4))
    assert zero_normalized_cross_correlation(a, b) == 0.0


def test_shape_mismatch_raises():
    a = np.zeros((2, 2))
    b = np.zeros((3, 3))
    with pytest.raises(ValueError):
        zero_normalized_cross_correlation(a, b)


def test_uncorrelated_orthogonal_signals_are_near_zero():
    x = np.linspace(0, 2 * np.pi, 100)
    a = np.sin(x)
    b = np.cos(x)
    assert zero_normalized_cross_correlation(a, b) == pytest.approx(0.0, abs=1e-9)
