r"""Strain from a least-squares displacement fit over a window of grid points.

Each grid point gets the affine fit of $u$ and $v$ over the
$n \times n$ points around it, with $n = 2m + 1$ and $m$ the window's
`margin`. The fit's slopes are the displacement gradient
$\boldsymbol{\nabla}_0\,\boldsymbol{u}$ at that point. Near the grid
boundary the window truncates to the points that exist, and the fit
solves the full $3 \times 3$ normal equations.

See [Strain Window](../getting_started/strain_window.html) for the
derivation this module implements.
"""

from collections.abc import Sequence

import numpy as np

from dictk.element import deformation_gradient, log_strain
from dictk.image import PixelCoordinate, SubpixelCoordinate


def _check(*, count_x: int, count_y: int, margin: int, point_count: int) -> None:
    if margin < 1:
        raise ValueError(f"margin {margin} must be >= 1")
    size = 2 * margin + 1
    if size > count_x or size > count_y:
        raise ValueError(
            f"window of {size}x{size} points (margin {margin}) must fit inside "
            f"the {count_x}x{count_y} grid"
        )
    if point_count != count_x * count_y:
        raise ValueError(
            f"got {point_count} points, must be count_x * count_y = {count_x * count_y}"
        )


def _windows(*, count_x: int, count_y: int, margin: int) -> list[np.ndarray]:
    windows = []
    for j in range(count_y):
        rows = np.arange(max(j - margin, 0), min(j + margin + 1, count_y))
        for i in range(count_x):
            columns = np.arange(max(i - margin, 0), min(i + margin + 1, count_x))
            windows.append((rows[:, None] * count_x + columns[None, :]).ravel())
    return windows


def displacement_gradients(
    *,
    reference_points: Sequence[PixelCoordinate | SubpixelCoordinate],
    current_points: Sequence[PixelCoordinate | SubpixelCoordinate],
    count_x: int,
    count_y: int,
    margin: int,
) -> np.ndarray:
    r"""The displacement gradient $\boldsymbol{\nabla}_0\,\boldsymbol{u}$ at every grid point.

    See [General
    Window](../getting_started/strain_window.html#general-window) and
    [Window Edges](../getting_started/strain_window.html#window-edges).

    Args:
        reference_points: The grid's reference positions, in
            [`dictk.grid.generate`](./grid.html#generate)'s row-major
            order.
        current_points: The same points' current positions, same order.
        count_x: Number of grid points along x.
        count_y: Number of grid points along y.
        margin: The window's half-width $m$, in points, not counting its
            center. The window has $2m + 1$ points per side. Must be >= 1.

    Returns:
        Shape `(count_x * count_y, 2, 2)`. Entry `k` is
        `[[du/dX, du/dY], [dv/dX, dv/dY]]` at point `k`, the same layout
        as [`dictk.element.displacement_gradient`](./element.html#displacement_gradient).

    Raises:
        ValueError: If `margin` is less than 1, the $(2m + 1) \times
            (2m + 1)$ window does not fit inside the grid,
            `reference_points` does not hold `count_x * count_y` points,
            or `current_points` does not match its length.
    """
    _check(
        count_x=count_x,
        count_y=count_y,
        margin=margin,
        point_count=len(reference_points),
    )
    if len(current_points) != len(reference_points):
        raise ValueError(
            f"current_points length ({len(current_points)}) must match "
            f"reference_points length ({len(reference_points)})"
        )

    reference = np.array([[p.x, p.y] for p in reference_points], dtype=float)
    displacements = (
        np.array([[p.x, p.y] for p in current_points], dtype=float) - reference
    )

    gradients = np.empty((len(reference), 2, 2))
    for k, window in enumerate(
        _windows(count_x=count_x, count_y=count_y, margin=margin)
    ):
        offsets = reference[window] - reference[k]
        design = np.column_stack([np.ones(len(window)), offsets])
        coefficients = np.linalg.lstsq(design, displacements[window], rcond=None)[0]
        gradients[k] = coefficients[1:].T
    return gradients


def log_strains(
    *,
    reference_points: Sequence[PixelCoordinate | SubpixelCoordinate],
    current_points: Sequence[PixelCoordinate | SubpixelCoordinate],
    count_x: int,
    count_y: int,
    margin: int,
) -> np.ndarray:
    r"""The logarithmic strain $\boldsymbol{E}^{(0)} = \ln\boldsymbol{U}$ at every grid point.

    Passes each point's `displacement_gradients` entry through
    [`dictk.element.deformation_gradient`](./element.html#deformation_gradient)
    and [`dictk.element.log_strain`](./element.html#log_strain). See
    [From Gradient to
    Strain](../getting_started/strain_window.html#from-gradient-to-strain).

    Args:
        reference_points: The grid's reference positions, in
            [`dictk.grid.generate`](./grid.html#generate)'s row-major
            order.
        current_points: The same points' current positions, same order.
        count_x: Number of grid points along x.
        count_y: Number of grid points along y.
        margin: The window's half-width $m$, in points, not counting its
            center. Must be >= 1.

    Returns:
        Shape `(count_x * count_y, 2, 2)`, one strain tensor per point.

    Raises:
        ValueError: Same conditions as `displacement_gradients`.
    """
    return np.array(
        [
            log_strain(
                deformation_gradient=deformation_gradient(displacement_gradient=g)
            )
            for g in displacement_gradients(
                reference_points=reference_points,
                current_points=current_points,
                count_x=count_x,
                count_y=count_y,
                margin=margin,
            )
        ]
    )


def std_factors(*, count_x: int, count_y: int, margin: int) -> np.ndarray:
    r"""Each point's gradient standard deviation, relative to a full interior window.

    Assumes independent tracking errors with equal variance. A full
    window gives `1.0`. A window truncated by the grid boundary gives
    more. On a uniformly spaced grid, an edge point at $m = 7$ gives
    2.58 for the gradient across the edge and a corner point gives
    3.54. See [Window
    Edges](../getting_started/strain_window.html#window-edges).

    Correlated tracking error can exceed these factors. A full window
    cancels most of a periodic error, and a truncated window does not.
    On `dictk.grid.locate_warp` positions under a 2% stretch, whose
    error follows a 51 px wave, the measured $E_{11}$ error at an edge
    point is 4.03 times the interior's, against a predicted 2.58. Three
    columns in, it is 6.04 times, against a predicted 1.60. See [Edges
    and Corners](../getting_started/strain_window.html#edges-and-corners).

    Args:
        count_x: Number of grid points along x.
        count_y: Number of grid points along y.
        margin: The window's half-width $m$, in points. Must be >= 1.

    Returns:
        Shape `(count_x * count_y, 2)`, in row-major order. Column 0 is
        the factor for $\partial / \partial X$, column 1 for
        $\partial / \partial Y$.

    Raises:
        ValueError: If `margin` is less than 1 or the $(2m + 1) \times
            (2m + 1)$ window does not fit inside the grid.
    """
    _check(
        count_x=count_x,
        count_y=count_y,
        margin=margin,
        point_count=count_x * count_y,
    )

    indices = np.array(
        [[i, j] for j in range(count_y) for i in range(count_x)], dtype=float
    )
    variances = np.empty((len(indices), 2))
    for k, window in enumerate(
        _windows(count_x=count_x, count_y=count_y, margin=margin)
    ):
        offsets = indices[window] - indices[k]
        design = np.column_stack([np.ones(len(window)), offsets])
        variances[k] = np.diag(np.linalg.inv(design.T @ design))[1:]

    interior = margin * count_x + margin
    return np.sqrt(variances / variances[interior])
