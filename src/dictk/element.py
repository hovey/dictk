"""A single four-noded quadrilateral (Q4) finite element: shape functions,
Jacobian, deformation gradient, and Green-Lagrange strain at its Gauss
points.

Ported from the `hdic` codebase's
`~/hdic/src/hdic/types/fea.py` (see [[project_dictk_hdic_provenance]].
The one hdic FEA implementation actually wired into a
real pipeline there, and validated end to end against a hand-worked
example (a unit square stretched 5% in $x$ gives $E_{11} = 0.05125$
exactly), reproduced here as this module's own regression test.

See [Finite Element
Method](../getting_started/finite_element_method.html) for the full
derivation this module implements -- each function's docstring links to
the specific subsection its math comes from.
"""

from collections.abc import Sequence

import numpy as np

from dictk.image import PixelCoordinate

#: The 2x2 Gauss quadrature rule's local coordinate value -- see
#: [Gauss Points](../getting_started/finite_element_method.html#gauss-points).
GAUSS_POINT_COORDINATE: float = 1.0 / np.sqrt(3.0)


def gauss_points() -> list[tuple[float, float]]:
    r"""The 4 $(\xi, \eta)$ locations of the standard 2x2 Gauss rule.

    See [Gauss
    Points](../getting_started/finite_element_method.html#gauss-points).
    Ordered to match `shape_functions`' own $N_1$..$N_4$ corner
    convention (bottom-left, bottom-right, top-right, top-left in local
    coordinates).

    Returns:
        A length-4 list of `(xi, eta)` pairs.
    """
    g = GAUSS_POINT_COORDINATE
    return [(-g, -g), (g, -g), (g, g), (-g, g)]


def shape_functions(*, xi: float, eta: float) -> np.ndarray:
    r"""The 4 Q4 shape functions $N_1$..$N_4$ at local coordinate $(\xi, \eta)$.

    See [Shape
    Functions](../getting_started/finite_element_method.html#shape-functions).

    Args:
        xi: Local coordinate along $\xi$, in $[-1, 1]$.
        eta: Local coordinate along $\eta$, in $[-1, 1]$.

    Returns:
        `N`, shape `(4,)`: $N_1, N_2, N_3, N_4$.
    """
    return 0.25 * np.array(
        [
            (1 - xi) * (1 - eta),
            (1 + xi) * (1 - eta),
            (1 + xi) * (1 + eta),
            (1 - xi) * (1 + eta),
        ]
    )


def shape_function_derivatives(*, xi: float, eta: float) -> np.ndarray:
    r"""The shape functions' derivatives with respect to local coordinates $(\xi, \eta)$.

    See [Shape Function Derivatives in Local
    Coordinates](../getting_started/finite_element_method.html#shape-function-derivatives-in-local-coordinates).

    Args:
        xi: Local coordinate along $\xi$, in $[-1, 1]$.
        eta: Local coordinate along $\eta$, in $[-1, 1]$.

    Returns:
        `dN/d(xi, eta)`, shape `(2, 4)`: row 0 is $\partial N_a/\partial
        \xi$ for $a=1..4$, row 1 is $\partial N_a/\partial \eta$.
    """
    return 0.25 * np.array(
        [
            [-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)],
            [-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)],
        ]
    )


def jacobian(*, derivatives: np.ndarray, coordinates: np.ndarray) -> np.ndarray:
    r"""The Jacobian matrix $\boldsymbol{j}_0$ mapping local to global coordinate derivatives.

    See [Jacobian
    Matrix](../getting_started/finite_element_method.html#jacobian-matrix).

    Args:
        derivatives: `shape_function_derivatives`' own output, shape `(2, 4)`.
        coordinates: The element's 4 corner nodes' positions, shape
            `(4, 2)`, each row `[X_a, Y_a]`, in $N_1$..$N_4$ order.

    Returns:
        $\boldsymbol{j}_0$ = `derivatives @ coordinates`, shape `(2, 2)`.
    """
    return derivatives @ coordinates


def shape_function_gradients(
    *, derivatives: np.ndarray, jacobian: np.ndarray
) -> np.ndarray:
    r"""The shape functions' derivatives with respect to global coordinates $(X, Y)$.

    See [Shape Function Derivatives in Global
    Coordinates](../getting_started/finite_element_method.html#shape-function-derivatives-in-global-coordinates).

    Args:
        derivatives: `shape_function_derivatives`' own output, shape `(2, 4)`.
        jacobian: `jacobian()`'s own output for this same element and
            $(\xi, \eta)$, shape `(2, 2)`.

    Returns:
        $\partial N_a/\partial X$ = $\boldsymbol{j}_0^{-1}$ `@ derivatives`,
        shape `(2, 4)`.

    Raises:
        ValueError: If `jacobian` is singular (a degenerate element, e.g.
            two coincident corners) -- hdic's own `types/fea.py` doesn't
            guard this; this port does.
    """
    if np.isclose(np.linalg.det(jacobian), 0.0):
        raise ValueError(
            f"jacobian {jacobian.tolist()} is singular -- the element is degenerate "
            "(e.g. two coincident corners), so shape function gradients are undefined"
        )
    return np.linalg.inv(jacobian) @ derivatives


def displacement_gradient(
    *, gradients: np.ndarray, displacements: np.ndarray
) -> np.ndarray:
    r"""The displacement field's gradient $\boldsymbol{\nabla}_0\boldsymbol{u}$ at a Gauss point.

    See [Displacement
    Gradient](../getting_started/finite_element_method.html#displacement-gradient).

    Args:
        gradients: `shape_function_gradients`' own output, shape `(2, 4)`.
        displacements: The element's 4 corner nodes' displacements
            (current position minus reference position), shape `(4, 2)`,
            each row `[u_a, v_a]`, same $N_1$..$N_4$ order as `coordinates`.

    Returns:
        $\boldsymbol{\nabla}_0\boldsymbol{u}$ = `(gradients @
        displacements).T`, shape `(2, 2)`.
    """
    return (gradients @ displacements).T


def deformation_gradient(*, displacement_gradient: np.ndarray) -> np.ndarray:
    r"""The deformation gradient $\boldsymbol{F} = \boldsymbol{I} + \boldsymbol{\nabla}_0\boldsymbol{u}$.

    See [Deformation
    Gradient](../getting_started/finite_element_method.html#deformation-gradient).

    Args:
        displacement_gradient: `displacement_gradient()`'s own output, shape `(2, 2)`.

    Returns:
        $\boldsymbol{F}$, shape `(2, 2)`.
    """
    return np.eye(2) + displacement_gradient


def green_lagrange_strain(*, deformation_gradient: np.ndarray) -> np.ndarray:
    r"""The Green-Lagrange strain tensor $\boldsymbol{E} = \frac{1}{2}(\boldsymbol{F}^T\boldsymbol{F} - \boldsymbol{I})$.

    See [Green-Lagrange
    Strain](../getting_started/continuum_mechanics.html#green-lagrange-strain).

    Args:
        deformation_gradient: `deformation_gradient()`'s own output, shape `(2, 2)`.

    Returns:
        $\boldsymbol{E}$, shape `(2, 2)`.
    """
    return 0.5 * (deformation_gradient.T @ deformation_gradient - np.eye(2))


def gauss_point_strains(
    *,
    reference_points: Sequence[PixelCoordinate],
    current_points: Sequence[PixelCoordinate],
) -> list[np.ndarray]:
    r"""Green-Lagrange strain at an element's 4 Gauss points.

    Composes `shape_function_derivatives` -> `jacobian` ->
    `shape_function_gradients` -> `displacement_gradient` ->
    `deformation_gradient` -> `green_lagrange_strain` at each of
    `gauss_points()`'s 4 locations, given the element's 4 corner nodes'
    reference and current positions directly -- unlike the hdic chain
    this is ported from, which requires the caller to pre-subtract raw
    numpy arrays into a `displacements` matrix before calling in.

    Args:
        reference_points: The element's 4 corner nodes' reference
            positions, in $N_1$..$N_4$ order (see [Shape
            Functions](../getting_started/finite_element_method.html#shape-functions)).
        current_points: The same 4 nodes' current positions, same order
            and indexing as `reference_points`.

    Returns:
        A length-4 list of `(2, 2)` Green-Lagrange strain tensors, one
        per Gauss point, in `gauss_points()`'s order.

    Raises:
        ValueError: If `reference_points` or `current_points` is not
            length 4, or the Jacobian is singular at some Gauss point
            (see `shape_function_gradients`).
    """
    if len(reference_points) != 4:
        raise ValueError(
            f"reference_points has {len(reference_points)} points, must be exactly 4"
        )
    if len(current_points) != 4:
        raise ValueError(
            f"current_points has {len(current_points)} points, must be exactly 4"
        )

    coordinates = np.array([[p.x, p.y] for p in reference_points], dtype=float)
    current = np.array([[p.x, p.y] for p in current_points], dtype=float)
    displacements = current - coordinates

    strains = []
    for xi, eta in gauss_points():
        derivatives = shape_function_derivatives(xi=xi, eta=eta)
        j = jacobian(derivatives=derivatives, coordinates=coordinates)
        gradients = shape_function_gradients(derivatives=derivatives, jacobian=j)
        grad_u = displacement_gradient(gradients=gradients, displacements=displacements)
        f = deformation_gradient(displacement_gradient=grad_u)
        strains.append(green_lagrange_strain(deformation_gradient=f))
    return strains
