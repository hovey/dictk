import numpy as np
import pytest

from dictk.element import (
    deformation_gradient,
    displacement_gradient,
    gauss_point_strains,
    gauss_points,
    green_lagrange_strain,
    jacobian,
    shape_function_derivatives,
    shape_function_gradients,
    shape_functions,
)
from dictk.image import PixelCoordinate

# A unit square, reference corners in N1..N4 order (bottom-left,
# bottom-right, top-right, top-left).
UNIT_SQUARE = [
    PixelCoordinate(x=0, y=0),
    PixelCoordinate(x=1, y=0),
    PixelCoordinate(x=1, y=1),
    PixelCoordinate(x=0, y=1),
]


def test_gauss_points_returns_four_points():
    points = gauss_points()
    assert len(points) == 4
    g = 1.0 / np.sqrt(3.0)
    assert np.allclose(points, [(-g, -g), (g, -g), (g, g), (-g, g)])


def test_shape_functions_requires_keyword_arguments():
    with pytest.raises(TypeError):
        shape_functions(0.0, 0.0)


def test_shape_functions_partition_of_unity():
    # An arbitrary interior point -- N1+N2+N3+N4 must sum to 1 everywhere.
    n = shape_functions(xi=0.3, eta=-0.6)
    assert np.isclose(n.sum(), 1.0)


def test_shape_functions_kronecker_delta_at_corners():
    # Each shape function equals 1 at its own corner, 0 at the others --
    # the corners are local (xi, eta) = (-1,-1), (1,-1), (1,1), (-1,1).
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for a, (xi, eta) in enumerate(corners):
        n = shape_functions(xi=xi, eta=eta)
        expected = np.zeros(4)
        expected[a] = 1.0
        assert np.allclose(n, expected)


def test_shape_functions_at_center():
    assert np.allclose(shape_functions(xi=0.0, eta=0.0), [0.25, 0.25, 0.25, 0.25])


def test_shape_function_derivatives_requires_keyword_arguments():
    with pytest.raises(TypeError):
        shape_function_derivatives(0.0, 0.0)


def test_shape_function_derivatives_at_center():
    expected = np.array(
        [
            [-0.25, 0.25, 0.25, -0.25],
            [-0.25, -0.25, 0.25, 0.25],
        ]
    )
    assert np.allclose(shape_function_derivatives(xi=0.0, eta=0.0), expected)


def test_jacobian_requires_keyword_arguments():
    coordinates = np.array([[p.x, p.y] for p in UNIT_SQUARE])
    derivatives = shape_function_derivatives(xi=0.0, eta=0.0)
    with pytest.raises(TypeError):
        jacobian(derivatives, coordinates)


def test_jacobian_of_unit_square_at_center():
    coordinates = np.array([[p.x, p.y] for p in UNIT_SQUARE])
    derivatives = shape_function_derivatives(xi=0.0, eta=0.0)
    j = jacobian(derivatives=derivatives, coordinates=coordinates)
    assert np.allclose(j, 0.5 * np.eye(2))


def test_shape_function_gradients_requires_keyword_arguments():
    coordinates = np.array([[p.x, p.y] for p in UNIT_SQUARE])
    derivatives = shape_function_derivatives(xi=0.0, eta=0.0)
    j = jacobian(derivatives=derivatives, coordinates=coordinates)
    with pytest.raises(TypeError):
        shape_function_gradients(derivatives, j)


def test_shape_function_gradients_singular_jacobian_raises():
    # All 4 corners collinear collapses the element to zero area -- a
    # singular Jacobian. hdic's own types/fea.py doesn't guard this;
    # this port does.
    degenerate = np.array([[0, 0], [1, 0], [2, 0], [3, 0]], dtype=float)
    derivatives = shape_function_derivatives(xi=0.0, eta=0.0)
    j = jacobian(derivatives=derivatives, coordinates=degenerate)
    with pytest.raises(ValueError):
        shape_function_gradients(derivatives=derivatives, jacobian=j)


def test_displacement_gradient_requires_keyword_arguments():
    gradients = np.zeros((2, 4))
    displacements = np.zeros((4, 2))
    with pytest.raises(TypeError):
        displacement_gradient(gradients, displacements)


def test_deformation_gradient_requires_keyword_arguments():
    with pytest.raises(TypeError):
        deformation_gradient(np.zeros((2, 2)))


def test_deformation_gradient_at_zero_displacement_is_identity():
    assert np.allclose(
        deformation_gradient(displacement_gradient=np.zeros((2, 2))), np.eye(2)
    )


def test_green_lagrange_strain_requires_keyword_arguments():
    with pytest.raises(TypeError):
        green_lagrange_strain(np.eye(2))


def test_green_lagrange_strain_at_identity_is_zero():
    assert np.allclose(
        green_lagrange_strain(deformation_gradient=np.eye(2)), np.zeros((2, 2))
    )


def test_gauss_point_strains_requires_keyword_arguments():
    with pytest.raises(TypeError):
        gauss_point_strains(UNIT_SQUARE, UNIT_SQUARE)


def test_gauss_point_strains_wrong_length_raises():
    with pytest.raises(ValueError):
        gauss_point_strains(
            reference_points=UNIT_SQUARE[:3], current_points=UNIT_SQUARE
        )
    with pytest.raises(ValueError):
        gauss_point_strains(
            reference_points=UNIT_SQUARE, current_points=UNIT_SQUARE[:3]
        )


def test_gauss_point_strains_matches_hdic_worked_example():
    """The primary regression anchor: hdic's own example_04a.md and its
    tests/test_fea.py independently agree that a unit square stretched
    5% in x gives E11 = 0.05125 exactly, at every Gauss point (a uniform
    stretch is affine, so Q4 bilinear interpolation reproduces it exactly
    everywhere, not just at the corners). Re-derived independently here
    too: F = diag(1.05, 1), E = 0.5*(F.T @ F - I), E11 = 0.5*(1.05**2-1)
    = 0.05125."""
    reference = UNIT_SQUARE
    current = [
        PixelCoordinate(x=0, y=0),
        PixelCoordinate(x=1.05, y=0),
        PixelCoordinate(x=1.05, y=1),
        PixelCoordinate(x=0, y=1),
    ]
    strains = gauss_point_strains(reference_points=reference, current_points=current)
    assert len(strains) == 4
    for e in strains:
        assert e.shape == (2, 2)
        assert np.isclose(e[0, 0], 0.05125)
        assert np.isclose(e[0, 1], 0.0)
        assert np.isclose(e[1, 0], 0.0)
        assert np.isclose(e[1, 1], 0.0)


def test_gauss_point_strains_zero_displacement_is_zero_strain():
    strains = gauss_point_strains(
        reference_points=UNIT_SQUARE, current_points=UNIT_SQUARE
    )
    for e in strains:
        assert np.allclose(e, np.zeros((2, 2)))
