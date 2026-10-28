import numpy as np
import pytest

from dictk.grid import generate
from dictk.image import PixelCoordinate, SubpixelCoordinate
from dictk.strain_window import displacement_gradients, log_strains, std_factors


def _grid(*, count_x, count_y, spacing_x=5, spacing_y=5):
    return generate(
        origin=PixelCoordinate(x=10, y=20),
        count_x=count_x,
        count_y=count_y,
        spacing_x=spacing_x,
        spacing_y=spacing_y,
    )


def _mapped(points, function):
    return [SubpixelCoordinate(*function(p.x, p.y)) for p in points]


def test_displacement_gradients_requires_keyword_arguments():
    """Positional arguments are rejected."""
    points = _grid(count_x=3, count_y=3)
    with pytest.raises(TypeError):
        displacement_gradients(points, points, 3, 3, 1)


def test_std_factors_requires_keyword_arguments():
    """Positional arguments are rejected."""
    with pytest.raises(TypeError):
        std_factors(3, 3, 1)


def test_displacement_gradients_recovers_affine_field_everywhere():
    """An affine field gives its exact gradient at interior, edge, and
    corner points, on a grid with unequal x and y spacing."""
    points = _grid(count_x=9, count_y=8, spacing_x=5, spacing_y=4)
    gradient = np.array([[0.02, -0.013], [0.007, -0.011]])
    center = np.array([31.0, 37.0])

    def affine(x, y):
        offset = np.array([x, y]) - center
        return np.array([x, y]) + np.array([1.5, -0.25]) + gradient @ offset

    gradients = displacement_gradients(
        reference_points=points,
        current_points=_mapped(points, affine),
        count_x=9,
        count_y=8,
        margin=2,
    )
    assert gradients.shape == (72, 2, 2)
    assert np.allclose(gradients, gradient, atol=1e-12)


@pytest.mark.parametrize("margin", [1, 2, 3])
def test_displacement_gradients_interior_weights_match_closed_form(margin):
    r"""Each point's weight in du/dX and du/dY at the window center is
    $c / (h n S_m)$ and $r / (h n S_m)$, the general-solution box."""
    n = 2 * margin + 1
    h = 5
    s_m = margin * (margin + 1) * (2 * margin + 1) / 3
    points = _grid(count_x=n, count_y=n, spacing_x=h, spacing_y=h)
    center = margin * n + margin

    weights_x = np.empty((n, n))
    weights_y = np.empty((n, n))
    for k in range(n * n):
        impulse = list(points)
        impulse[k] = SubpixelCoordinate(x=points[k].x + 1.0, y=points[k].y)
        g = displacement_gradients(
            reference_points=points,
            current_points=impulse,
            count_x=n,
            count_y=n,
            margin=margin,
        )[center]
        weights_x[k // n, k % n] = g[0, 0]
        weights_y[k // n, k % n] = g[0, 1]

    c = np.arange(-margin, margin + 1)
    assert np.allclose(weights_x, np.tile(c, (n, 1)) / (h * n * s_m), atol=1e-12)
    assert np.allclose(
        weights_y, np.tile(c[:, None], (1, n)) / (h * n * s_m), atol=1e-12
    )


def test_displacement_gradients_edge_returns_gradient_at_centroid():
    r"""A quadratic field's fitted gradient at a left-edge point is the
    true gradient at the kept points' centroid, $mh/2$ to its right."""
    margin = 3
    h = 5
    u_second = 1e-3
    points = _grid(count_x=11, count_y=11, spacing_x=h, spacing_y=h)
    x_ref = 10.0

    def quadratic(x, y):
        return x + 0.5 * u_second * (x - x_ref) ** 2, y

    gradients = displacement_gradients(
        reference_points=points,
        current_points=_mapped(points, quadratic),
        count_x=11,
        count_y=11,
        margin=margin,
    )
    edge = 5 * 11 + 0
    centroid_x = points[edge].x + margin * h / 2
    assert gradients[edge, 0, 0] == pytest.approx(u_second * (centroid_x - x_ref))

    interior = 5 * 11 + 5
    assert gradients[interior, 0, 0] == pytest.approx(
        u_second * (points[interior].x - x_ref)
    )


def test_log_strains_uniform_stretch():
    """A 2% stretch in x gives E11 = ln(1.02) and zero elsewhere."""
    points = _grid(count_x=7, count_y=6)
    strains = log_strains(
        reference_points=points,
        current_points=_mapped(points, lambda x, y: (1.02 * x, y)),
        count_x=7,
        count_y=6,
        margin=2,
    )
    expected = np.array([[np.log(1.02), 0.0], [0.0, 0.0]])
    assert np.allclose(strains, expected, atol=1e-12)


def test_log_strains_rigid_rotation_is_zero():
    """A pure rotation gives zero log strain at every point."""
    points = _grid(count_x=7, count_y=7)
    angle = np.radians(10.0)
    rotation = np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
    )
    strains = log_strains(
        reference_points=points,
        current_points=_mapped(
            points, lambda x, y: rotation @ (np.array([x, y]) - 25.0) + 40.0
        ),
        count_x=7,
        count_y=7,
        margin=1,
    )
    assert np.allclose(strains, 0.0, atol=1e-12)


@pytest.mark.parametrize(
    ("margin", "edge", "corner"), [(3, 2.37, 3.13), (7, 2.58, 3.54)]
)
def test_std_factors_match_edge_and_corner_formulas(margin, edge, corner):
    """Interior is 1. A left-edge point and the top-left corner match the
    page's edge and corner factors to the printed precision."""
    n = 2 * margin + 1
    factors = std_factors(count_x=n, count_y=n, margin=margin)
    interior = margin * n + margin
    left_edge = margin * n
    assert np.allclose(factors[interior], 1.0)
    assert factors[left_edge, 0] == pytest.approx(
        np.sqrt(4 * (2 * margin + 1) / (margin + 2))
    )
    assert factors[left_edge, 0] == pytest.approx(edge, abs=0.005)
    assert factors[left_edge, 1] == pytest.approx(np.sqrt(n / (margin + 1)))
    assert factors[0, 0] == pytest.approx(
        np.sqrt(4 * (2 * margin + 1) ** 2 / ((margin + 1) * (margin + 2)))
    )
    assert factors[0, 0] == pytest.approx(corner, abs=0.005)
    assert factors[0, 1] == pytest.approx(factors[0, 0])


def test_std_factors_match_displacement_gradients_weights():
    """std_factors agrees with the root sum of squared weights that
    displacement_gradients actually applies, at every point."""
    count, margin, h = 7, 2, 5
    points = _grid(count_x=count, count_y=count, spacing_x=h, spacing_y=h)
    sum_squares = np.zeros((count * count, 2))
    for k in range(count * count):
        impulse = list(points)
        impulse[k] = SubpixelCoordinate(x=points[k].x + 1.0, y=points[k].y)
        g = displacement_gradients(
            reference_points=points,
            current_points=impulse,
            count_x=count,
            count_y=count,
            margin=margin,
        )
        sum_squares += g[:, 0, :] ** 2
    measured = np.sqrt(sum_squares / sum_squares[margin * count + margin])
    assert np.allclose(
        std_factors(count_x=count, count_y=count, margin=margin), measured
    )


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        (dict(count_x=5, count_y=5, margin=0), "margin 0 must be >= 1"),
        (dict(count_x=5, count_y=7, margin=3), "must fit inside"),
        (dict(count_x=7, count_y=4, margin=2), "must fit inside"),
    ],
)
def test_std_factors_rejects_bad_window(kwargs, match):
    with pytest.raises(ValueError, match=match):
        std_factors(**kwargs)


def test_displacement_gradients_rejects_wrong_point_counts():
    points = _grid(count_x=5, count_y=5)
    with pytest.raises(ValueError, match="must be count_x \\* count_y"):
        displacement_gradients(
            reference_points=points[:-1],
            current_points=points[:-1],
            count_x=5,
            count_y=5,
            margin=1,
        )
    with pytest.raises(ValueError, match="must match"):
        displacement_gradients(
            reference_points=points,
            current_points=points[:-1],
            count_x=5,
            count_y=5,
            margin=1,
        )
