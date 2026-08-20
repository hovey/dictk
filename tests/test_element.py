import numpy as np
import pytest

from dictk.element import (
    deformation_gradient,
    displacement_gradient,
    gauss_point_coordinates,
    gauss_point_green_lagrange_strains,
    gauss_point_log_strains,
    gauss_points,
    green_lagrange_strain,
    jacobian,
    log_strain,
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
    """Returns the 4 correct (xi, eta) Gauss point locations."""
    points = gauss_points()
    assert len(points) == 4
    g = 1.0 / np.sqrt(3.0)
    assert np.allclose(points, [(-g, -g), (g, -g), (g, g), (-g, g)])


def test_gauss_point_coordinates_requires_keyword_arguments():
    """Positional arguments are rejected."""
    with pytest.raises(TypeError):
        gauss_point_coordinates(UNIT_SQUARE)


def test_gauss_point_coordinates_wrong_length_raises():
    """A points list of length != 4 raises ValueError."""
    with pytest.raises(ValueError):
        gauss_point_coordinates(points=UNIT_SQUARE[:3])


def test_gauss_point_coordinates_matches_hand_computation():
    """A 2x-scaled square's Gauss point 1 position, hand-computed via
    shape_functions(xi=-g, eta=-g) @ coordinates independently, matches."""
    square = [
        PixelCoordinate(x=0, y=0),
        PixelCoordinate(x=2, y=0),
        PixelCoordinate(x=2, y=2),
        PixelCoordinate(x=0, y=2),
    ]
    coords = gauss_point_coordinates(points=square)
    assert len(coords) == 4
    g = 1.0 / np.sqrt(3.0)
    expected_gp1 = shape_functions(xi=-g, eta=-g) @ np.array(
        [[0, 0], [2, 0], [2, 2], [0, 2]], dtype=float
    )
    assert np.allclose(coords[0], expected_gp1)


def test_gauss_point_coordinates_at_unit_square_center():
    """The unit square's own center, xi=eta=0, would map to (0.5, 0.5) --
    not one of the 4 returned Gauss points, but a sanity check that the
    4 actual Gauss points straddle it symmetrically."""
    coords = gauss_point_coordinates(points=UNIT_SQUARE)
    mean_x = sum(c[0] for c in coords) / 4
    mean_y = sum(c[1] for c in coords) / 4
    assert np.isclose(mean_x, 0.5)
    assert np.isclose(mean_y, 0.5)


def test_shape_functions_requires_keyword_arguments():
    """Positional arguments are rejected."""
    with pytest.raises(TypeError):
        shape_functions(0.0, 0.0)


def test_shape_functions_partition_of_unity():
    """N1+N2+N3+N4 sums to 1 at an arbitrary interior point."""
    n = shape_functions(xi=0.3, eta=-0.6)
    assert np.isclose(n.sum(), 1.0)


def test_shape_functions_kronecker_delta_at_corners():
    """Each shape function equals 1 at its own corner, 0 at the others --
    the corners are local (xi, eta) = (-1,-1), (1,-1), (1,1), (-1,1)."""
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for a, (xi, eta) in enumerate(corners):
        n = shape_functions(xi=xi, eta=eta)
        expected = np.zeros(4)
        expected[a] = 1.0
        assert np.allclose(n, expected)


def test_shape_functions_at_center():
    """All 4 shape functions equal 0.25 at the element's center."""
    assert np.allclose(shape_functions(xi=0.0, eta=0.0), [0.25, 0.25, 0.25, 0.25])


def test_shape_function_derivatives_requires_keyword_arguments():
    """Positional arguments are rejected."""
    with pytest.raises(TypeError):
        shape_function_derivatives(0.0, 0.0)


def test_shape_function_derivatives_at_center():
    """Matches the hand-derived dN/d(xi, eta) values at the element's center."""
    expected = np.array(
        [
            [-0.25, 0.25, 0.25, -0.25],
            [-0.25, -0.25, 0.25, 0.25],
        ]
    )
    assert np.allclose(shape_function_derivatives(xi=0.0, eta=0.0), expected)


def test_jacobian_requires_keyword_arguments():
    """Positional arguments are rejected."""
    coordinates = np.array([[p.x, p.y] for p in UNIT_SQUARE])
    derivatives = shape_function_derivatives(xi=0.0, eta=0.0)
    with pytest.raises(TypeError):
        jacobian(derivatives, coordinates)


def test_jacobian_of_unit_square_at_center():
    """A unit square's Jacobian at its center is 0.5*I."""
    coordinates = np.array([[p.x, p.y] for p in UNIT_SQUARE])
    derivatives = shape_function_derivatives(xi=0.0, eta=0.0)
    j = jacobian(derivatives=derivatives, coordinates=coordinates)
    assert np.allclose(j, 0.5 * np.eye(2))


def test_shape_function_gradients_requires_keyword_arguments():
    """Positional arguments are rejected."""
    coordinates = np.array([[p.x, p.y] for p in UNIT_SQUARE])
    derivatives = shape_function_derivatives(xi=0.0, eta=0.0)
    j = jacobian(derivatives=derivatives, coordinates=coordinates)
    with pytest.raises(TypeError):
        shape_function_gradients(derivatives, j)


def test_shape_function_gradients_singular_jacobian_raises():
    """All 4 corners collinear collapses the element to zero area -- a
    singular Jacobian. hdic's own types/fea.py doesn't guard this; this
    port does."""
    degenerate = np.array([[0, 0], [1, 0], [2, 0], [3, 0]], dtype=float)
    derivatives = shape_function_derivatives(xi=0.0, eta=0.0)
    j = jacobian(derivatives=derivatives, coordinates=degenerate)
    with pytest.raises(ValueError):
        shape_function_gradients(derivatives=derivatives, jacobian=j)


def test_displacement_gradient_requires_keyword_arguments():
    """Positional arguments are rejected."""
    gradients = np.zeros((2, 4))
    displacements = np.zeros((4, 2))
    with pytest.raises(TypeError):
        displacement_gradient(gradients, displacements)


def test_deformation_gradient_requires_keyword_arguments():
    """Positional arguments are rejected."""
    with pytest.raises(TypeError):
        deformation_gradient(np.zeros((2, 2)))


def test_deformation_gradient_at_zero_displacement_is_identity():
    """Zero displacement gradient gives F = I."""
    assert np.allclose(
        deformation_gradient(displacement_gradient=np.zeros((2, 2))), np.eye(2)
    )


def test_green_lagrange_strain_requires_keyword_arguments():
    """Positional arguments are rejected."""
    with pytest.raises(TypeError):
        green_lagrange_strain(np.eye(2))


def test_green_lagrange_strain_at_identity_is_zero():
    """F = I (no deformation) gives zero strain."""
    assert np.allclose(
        green_lagrange_strain(deformation_gradient=np.eye(2)), np.zeros((2, 2))
    )


def test_log_strain_requires_keyword_arguments():
    """Positional arguments are rejected."""
    with pytest.raises(TypeError):
        log_strain(np.eye(2))


def test_log_strain_at_identity_is_zero():
    """F = I (no deformation) gives zero strain."""
    assert np.allclose(log_strain(deformation_gradient=np.eye(2)), np.zeros((2, 2)))


def test_log_strain_matches_closed_form_uniaxial_stretch():
    """A pure axis-aligned stretch has no rotation, so U = F exactly, and
    ln(U) is diagonal with ln(stretch factor) on the diagonal -- an
    independent closed-form check of the spectral-decomposition result."""
    f = np.diag([1.05, 1.0])
    e = log_strain(deformation_gradient=f)
    assert np.isclose(e[0, 0], np.log(1.05))
    assert np.isclose(e[0, 1], 0.0)
    assert np.isclose(e[1, 0], 0.0)
    assert np.isclose(e[1, 1], 0.0)


def test_log_strain_matches_scipy_matrix_log_for_a_general_case():
    """Cross-check the eigendecomposition-based formula against scipy's
    general matrix logarithm on a case with shear, where U != F, so the
    closed-form diagonal shortcut above doesn't apply."""
    import scipy.linalg

    f = np.array([[1.05, 0.1], [0.02, 0.98]])
    e = log_strain(deformation_gradient=f)
    c = f.T @ f
    u = scipy.linalg.sqrtm(c)
    expected = np.real(scipy.linalg.logm(u))
    assert np.allclose(e, expected)


def test_gauss_point_green_lagrange_strains_requires_keyword_arguments():
    """Positional arguments are rejected."""
    with pytest.raises(TypeError):
        gauss_point_green_lagrange_strains(UNIT_SQUARE, UNIT_SQUARE)


def test_gauss_point_green_lagrange_strains_wrong_length_raises():
    """A reference_points or current_points list of length != 4 raises ValueError."""
    with pytest.raises(ValueError):
        gauss_point_green_lagrange_strains(
            reference_points=UNIT_SQUARE[:3], current_points=UNIT_SQUARE
        )
    with pytest.raises(ValueError):
        gauss_point_green_lagrange_strains(
            reference_points=UNIT_SQUARE, current_points=UNIT_SQUARE[:3]
        )


def test_gauss_point_green_lagrange_strains_matches_hdic_worked_example():
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
    strains = gauss_point_green_lagrange_strains(
        reference_points=reference, current_points=current
    )
    assert len(strains) == 4
    for e in strains:
        assert e.shape == (2, 2)
        assert np.isclose(e[0, 0], 0.05125)
        assert np.isclose(e[0, 1], 0.0)
        assert np.isclose(e[1, 0], 0.0)
        assert np.isclose(e[1, 1], 0.0)


def test_gauss_point_green_lagrange_strains_zero_displacement_is_zero_strain():
    """Identical reference and current points give zero strain at every Gauss point."""
    strains = gauss_point_green_lagrange_strains(
        reference_points=UNIT_SQUARE, current_points=UNIT_SQUARE
    )
    for e in strains:
        assert np.allclose(e, np.zeros((2, 2)))


def test_gauss_point_log_strains_requires_keyword_arguments():
    """Positional arguments are rejected."""
    with pytest.raises(TypeError):
        gauss_point_log_strains(UNIT_SQUARE, UNIT_SQUARE)


def test_gauss_point_log_strains_wrong_length_raises():
    """A reference_points or current_points list of length != 4 raises ValueError."""
    with pytest.raises(ValueError):
        gauss_point_log_strains(
            reference_points=UNIT_SQUARE[:3], current_points=UNIT_SQUARE
        )
    with pytest.raises(ValueError):
        gauss_point_log_strains(
            reference_points=UNIT_SQUARE, current_points=UNIT_SQUARE[:3]
        )


def test_gauss_point_log_strains_matches_closed_form_uniaxial_stretch():
    """Same scenario as the Green-Lagrange regression anchor above (5%
    uniaxial x-stretch, exact everywhere since it's affine), but checked
    against log strain's own closed form: ln(1.05), not 0.5*(1.05**2-1)."""
    reference = UNIT_SQUARE
    current = [
        PixelCoordinate(x=0, y=0),
        PixelCoordinate(x=1.05, y=0),
        PixelCoordinate(x=1.05, y=1),
        PixelCoordinate(x=0, y=1),
    ]
    strains = gauss_point_log_strains(
        reference_points=reference, current_points=current
    )
    assert len(strains) == 4
    for e in strains:
        assert e.shape == (2, 2)
        assert np.isclose(e[0, 0], np.log(1.05))
        assert np.isclose(e[0, 1], 0.0)
        assert np.isclose(e[1, 0], 0.0)
        assert np.isclose(e[1, 1], 0.0)


def test_gauss_point_log_strains_zero_displacement_is_zero_strain():
    """Identical reference and current points give zero strain at every Gauss point."""
    strains = gauss_point_log_strains(
        reference_points=UNIT_SQUARE, current_points=UNIT_SQUARE
    )
    for e in strains:
        assert np.allclose(e, np.zeros((2, 2)))
