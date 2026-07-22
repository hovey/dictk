import numpy as np
import pytest

from dictk.rosta import ImageSize, RostaParameters, rosta_pattern


def _params(**overrides) -> RostaParameters:
    defaults = dict(
        image_size=ImageSize(width=40, height=30),
        dot_size=4.0,
        density=0.32,
        smoothness=2.0,
        random_seed=42,
    )
    defaults.update(overrides)
    return RostaParameters(**defaults)


@pytest.mark.parametrize("dot_size", [0.0, 100.0, -1.0])
def test_invalid_dot_size_raises(dot_size):
    with pytest.raises(ValueError):
        _params(dot_size=dot_size)


@pytest.mark.parametrize("density", [0.0, 1.0, -0.5])
def test_invalid_density_raises(density):
    with pytest.raises(ValueError):
        _params(density=density)


@pytest.mark.parametrize("smoothness", [0.0, 100.0, -2.0])
def test_invalid_smoothness_raises(smoothness):
    with pytest.raises(ValueError):
        _params(smoothness=smoothness)


def test_valid_parameters_default_name():
    rp = _params()
    assert rp.name == "rosta"


def test_rosta_pattern_shape():
    rp = _params(image_size=ImageSize(width=40, height=30))
    pattern = rosta_pattern(rp)
    assert pattern.shape == (30, 40)


def test_rosta_pattern_value_range():
    rp = _params()
    pattern = rosta_pattern(rp)
    assert pattern.min() >= 0.0
    assert pattern.max() <= 1.0


def test_rosta_pattern_deterministic_given_seed():
    rp = _params(random_seed=7)
    first = rosta_pattern(rp)
    second = rosta_pattern(rp)
    assert np.array_equal(first, second)


def test_rosta_pattern_differs_with_different_seed():
    pattern_a = rosta_pattern(_params(random_seed=1))
    pattern_b = rosta_pattern(_params(random_seed=2))
    assert not np.array_equal(pattern_a, pattern_b)
