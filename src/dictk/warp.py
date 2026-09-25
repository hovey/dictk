"""Subpixel point tracking by warping an affine kernel: inverse
compositional Gauss-Newton (IC-GN)."""

import numpy as np
from scipy.ndimage import map_coordinates, spline_filter

from dictk import translation
from dictk.correlation import WindowingMethod
from dictk.image import PixelCoordinate, SubpixelCoordinate


def _spline_coefficients(image: np.ndarray) -> np.ndarray:
    """Cubic B-spline coefficients of `image`, computed once so every
    per-point refinement can sample it with `prefilter=False`."""
    return spline_filter(image.astype(np.float64), order=3)


def _gradients(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """`image`'s `(d/dy, d/dx)` central-difference gradients."""
    gradient_y, gradient_x = np.gradient(image.astype(np.float64))
    return gradient_y, gradient_x


def _refine(
    *,
    reference_image: np.ndarray,
    reference_gradients: tuple[np.ndarray, np.ndarray],
    current_coefficients: np.ndarray,
    reference_point: PixelCoordinate,
    start: PixelCoordinate,
    kernel_margin_width: int,
    kernel_margin_height: int,
    max_iterations: int,
    tolerance: float,
) -> np.ndarray:
    """IC-GN refinement of one point, from an integer `start` -- see
    [`fit`](#fit) for the method and the returned matrix. Takes
    precomputed gradients and spline coefficients so a batch caller
    computes them once, not once per point."""
    gradient_y, gradient_x = reference_gradients
    x0, y0 = reference_point.x, reference_point.y
    rows = slice(y0 - kernel_margin_height, y0 + kernel_margin_height + 1)
    columns = slice(x0 - kernel_margin_width, x0 + kernel_margin_width + 1)
    dy, dx = np.mgrid[
        -kernel_margin_height : kernel_margin_height + 1,
        -kernel_margin_width : kernel_margin_width + 1,
    ].astype(np.float64)

    f = reference_image[rows, columns].astype(np.float64)
    f = f - f.mean()
    f_norm = np.sqrt((f**2).sum())

    gx = gradient_x[rows, columns]
    gy = gradient_y[rows, columns]
    steepest_descent = np.stack(
        [gx, gx * dx, gx * dy, gy, gy * dx, gy * dy], axis=-1
    ).reshape(-1, 6)
    hessian_inverse = np.linalg.inv(steepest_descent.T @ steepest_descent)

    warp = np.array(
        [
            [1.0, 0.0, start.x - x0],
            [0.0, 1.0, start.y - y0],
            [0.0, 0.0, 1.0],
        ]
    )
    for _ in range(max_iterations):
        xs = x0 + warp[0, 0] * dx + warp[0, 1] * dy + warp[0, 2]
        ys = y0 + warp[1, 0] * dx + warp[1, 1] * dy + warp[1, 2]
        g = map_coordinates(current_coefficients, [ys, xs], order=3, prefilter=False)
        g = g - g.mean()
        g_norm = np.sqrt((g**2).sum())
        residual = f_norm / g_norm * g - f
        dp = hessian_inverse @ (steepest_descent.T @ residual.ravel())
        increment = np.array(
            [
                [1.0 + dp[1], dp[2], dp[0]],
                [dp[4], 1.0 + dp[5], dp[3]],
                [0.0, 0.0, 1.0],
            ]
        )
        warp = warp @ np.linalg.inv(increment)
        if np.abs(dp).max() < tolerance:
            break

    return warp


def fit(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    reference_point: PixelCoordinate,
    search_center: PixelCoordinate,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None = None,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
) -> np.ndarray:
    """Fit the affine warp that carries a kernel of `reference_image`
    onto `current_image`.

    Two stages. First,
    [`dictk.translation.locate`](./translation.html#locate) finds the
    nearest whole-pixel position. Second, inverse compositional
    Gauss-Newton (IC-GN) refines it. IC-GN deforms a square kernel of
    `reference_image`, centered on `reference_point`, by a six-parameter
    affine warp. It then adjusts that warp until the warped kernel best
    matches `current_image`, by zero-normalized sum of squared
    differences (ZNSSD). Cubic B-spline interpolation samples
    `current_image` at the warped, fractional positions.

    The whole-pixel stage still matches a rigid, unwarped kernel. A
    deformation large enough to defeat that match, such as a stretch of
    about 10% or more with shear on a fine speckle pattern, leaves IC-GN
    starting too far away to converge. `fit` has no check for this.

    See [Kernel Warping](../getting_started/kernel_warping.html) for why
    this beats phase correlation's upsampled peak, and
    [`locate`](#locate) for the tracked position alone.

    This kernel is `2 * kernel_margin_width + 1` wide and
    `2 * kernel_margin_height + 1` tall, centered exactly on
    `reference_point`. That is one pixel larger than `translation.locate`'s
    own even kernel in each direction.

    Args:
        reference_image: The reference (undeformed) 2D grayscale image.
        current_image: The current (deformed) 2D grayscale image.
        reference_point: The point's fixed, known position, in
            `reference_image`'s pixel reference frame.
        search_center: Where to center the whole-pixel search, in
            `current_image`'s pixel reference frame -- see
            `translation.locate`'s own docstring.
        kernel_margin_width: Half the kernel's width, in pixels, not
            counting its center column. Must be >= 1.
        kernel_margin_height: Half the kernel's height, in pixels, not
            counting its center row. Must be >= 1.
        search_margin_width: Half the whole-pixel search area's width,
            in pixels. Must be greater than `kernel_margin_width`.
        search_margin_height: Half the whole-pixel search area's height,
            in pixels. Must be greater than `kernel_margin_height`.
        windowing: Passed straight through to the whole-pixel
            `translation.locate` stage. Default `None` applies no
            windowing. IC-GN itself never windows.
        max_iterations: The most IC-GN updates to apply. Default `50`.
            Must be >= 1.
        tolerance: IC-GN stops once every warp parameter's update falls
            below this. Default `1e-6`. Must be > 0.

    Returns:
        The 3x3 warp matrix

            [[1 + u_x, u_y,     u],
             [v_x,     1 + v_y, v],
             [0,       0,       1]]

        It maps a pixel's offset `(dx, dy, 1)` from `reference_point`
        in `reference_image` to that pixel's offset from
        `reference_point` in `current_image`. `(u, v)` is the tracked
        displacement. `u_x`, `u_y`, `v_x`, `v_y` are the displacement
        gradients across the kernel.

    Raises:
        ValueError: If any margin fails `translation.locate`'s own
            checks, `max_iterations` is less than 1, or `tolerance` is
            not positive.
    """
    if max_iterations < 1:
        raise ValueError(f"max_iterations {max_iterations} must be >= 1")
    if tolerance <= 0:
        raise ValueError(f"tolerance {tolerance} must be > 0")

    start = translation.locate(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=reference_point,
        search_center=search_center,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
        windowing=windowing,
    )
    return _refine(
        reference_image=reference_image,
        reference_gradients=_gradients(reference_image),
        current_coefficients=_spline_coefficients(current_image),
        reference_point=reference_point,
        start=start,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )


def locate(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    reference_point: PixelCoordinate,
    search_center: PixelCoordinate,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None = None,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
) -> SubpixelCoordinate:
    """Subpixel point tracking by warping an affine kernel, free of the
    pixel-locking bias of
    [`dictk.translation.locate_subpixel`](./translation.html#locate_subpixel).

    Runs [`fit`](#fit) and returns only the fitted warp's translation,
    as a position. Every argument passes straight through to `fit` --
    see its own docstring for each one, and for the method.

    Returns:
        The point's location, in `current_image`'s pixel reference
        frame, generally fractional.

    Raises:
        ValueError: Under the same conditions as `fit`.
    """
    warp = fit(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=reference_point,
        search_center=search_center,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
        windowing=windowing,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    return SubpixelCoordinate(
        x=reference_point.x + warp[0, 2], y=reference_point.y + warp[1, 2]
    )
