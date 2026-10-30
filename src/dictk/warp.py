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


def _translation_warp(
    *, reference_point: PixelCoordinate, start: PixelCoordinate
) -> np.ndarray:
    """The rigid seed: a warp that moves `reference_point` to the
    whole-pixel `start`, with all four gradient terms zero."""
    return np.array(
        [
            [1.0, 0.0, start.x - reference_point.x],
            [0.0, 1.0, start.y - reference_point.y],
            [0.0, 0.0, 1.0],
        ]
    )


def _shape_seeds(
    *,
    reference_coefficients: np.ndarray,
    current_image: np.ndarray,
    current_coefficients: np.ndarray,
    reference_point: PixelCoordinate,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    gradient_limit: float,
    gradient_step: float,
    seed_count: int,
) -> list[np.ndarray]:
    """Deformation-aware seeds for one point, best first.

    Tries every displacement gradient `(u_x, u_y, v_x, v_y)` on a grid
    from `-gradient_limit` to `gradient_limit` in steps of
    `gradient_step`. Each trial deforms the reference kernel by its
    gradient, then finds that kernel's whole-pixel translation by phase
    correlation against the search area, as `translation.locate` does
    for a rigid kernel. Each trial is scored by ZNSSD at that
    translation. Returns the `seed_count` lowest-scoring trials as 3x3
    warps, ready for `_refine`."""
    x0, y0 = reference_point.x, reference_point.y
    dy, dx = np.mgrid[
        -kernel_margin_height : kernel_margin_height + 1,
        -kernel_margin_width : kernel_margin_width + 1,
    ].astype(np.float64)
    count = int(round(gradient_limit / gradient_step))
    values = np.arange(-count, count + 1) * gradient_step
    gradients = np.stack(
        np.meshgrid(values, values, values, values, indexing="ij"), axis=-1
    ).reshape(-1, 4)
    shapes = np.eye(2) + gradients.reshape(-1, 2, 2)

    # The deformed kernel, on the current image's pixel grid: the
    # reference sampled at each offset carried back through the shape.
    inverses = np.linalg.inv(shapes)
    xs = x0 + inverses[:, 0, 0, None, None] * dx + inverses[:, 0, 1, None, None] * dy
    ys = y0 + inverses[:, 1, 0, None, None] * dx + inverses[:, 1, 1, None, None] * dy
    kernels = map_coordinates(
        reference_coefficients, [ys, xs], order=3, prefilter=False
    )

    # Phase correlation, with each kernel centered in a zero-padded copy
    # the size of the search area, as translation.locate pads its own.
    search = current_image[
        y0 - search_margin_height : y0 + search_margin_height,
        x0 - search_margin_width : x0 + search_margin_width,
    ].astype(np.float64)
    rows, columns = search.shape
    top = (rows - kernels.shape[1]) // 2
    left = (columns - kernels.shape[2]) // 2
    padded = np.zeros((len(kernels), rows, columns))
    padded[:, top : top + kernels.shape[1], left : left + kernels.shape[2]] = kernels
    product = np.fft.fft2(search)[None] * np.fft.fft2(padded).conj()
    product /= np.maximum(np.abs(product), 100 * np.finfo(np.float64).eps)
    surfaces = np.abs(np.fft.ifft2(product)).reshape(len(kernels), -1)
    peak_rows, peak_columns = np.unravel_index(surfaces.argmax(axis=1), (rows, columns))
    peak_rows = np.where(peak_rows >= rows // 2, peak_rows - rows, peak_rows)
    peak_columns = np.where(
        peak_columns >= columns // 2, peak_columns - columns, peak_columns
    )
    # A zero shift puts the kernel's center at search index
    # (top + margin, left + margin), which is the point's own position
    # minus this offset.
    u = peak_columns + left + kernel_margin_width - search_margin_width
    v = peak_rows + top + kernel_margin_height - search_margin_height

    xs = x0 + u[:, None, None] + shapes[:, 0, 0, None, None] * dx
    xs += shapes[:, 0, 1, None, None] * dy
    ys = y0 + v[:, None, None] + shapes[:, 1, 0, None, None] * dx
    ys += shapes[:, 1, 1, None, None] * dy
    g = map_coordinates(current_coefficients, [ys, xs], order=3, prefilter=False)
    g = g - g.mean(axis=(1, 2), keepdims=True)
    g /= np.maximum(np.sqrt((g**2).sum(axis=(1, 2), keepdims=True)), 1e-12)
    f = map_coordinates(
        reference_coefficients, [y0 + dy, x0 + dx], order=3, prefilter=False
    )
    f = f - f.mean()
    f /= np.sqrt((f**2).sum())
    znssds = ((g - f) ** 2).sum(axis=(1, 2))

    seeds = []
    for index in np.argsort(znssds)[:seed_count]:
        seed = np.eye(3)
        seed[:2, :2] = shapes[index]
        seed[:2, 2] = u[index], v[index]
        seeds.append(seed)
    return seeds


def _refine(
    *,
    reference_image: np.ndarray,
    reference_gradients: tuple[np.ndarray, np.ndarray],
    current_coefficients: np.ndarray,
    reference_point: PixelCoordinate,
    initial_warp: np.ndarray,
    kernel_margin_width: int,
    kernel_margin_height: int,
    max_iterations: int,
    tolerance: float,
) -> tuple[np.ndarray, float, int]:
    """IC-GN refinement of one point, starting from the 3x3
    `initial_warp` -- see [`fit`](#fit) for the method and the returned
    matrix. `_translation_warp` builds the rigid seed `fit` uses. Takes
    precomputed gradients and spline coefficients so a batch caller
    computes them once, not once per point.

    Also returns the ZNSSD between the reference kernel and
    `current_image` sampled through the returned warp, from 0 for a
    perfect match to 4, and how many updates IC-GN applied. That count
    equals `max_iterations` when IC-GN stopped without meeting
    `tolerance`."""
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

    def residual_at(warp):
        xs = x0 + warp[0, 0] * dx + warp[0, 1] * dy + warp[0, 2]
        ys = y0 + warp[1, 0] * dx + warp[1, 1] * dy + warp[1, 2]
        g = map_coordinates(current_coefficients, [ys, xs], order=3, prefilter=False)
        g = g - g.mean()
        return f_norm / np.sqrt((g**2).sum()) * g - f

    warp = np.array(initial_warp, dtype=np.float64)
    for iterations in range(1, max_iterations + 1):
        residual = residual_at(warp)
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

    znssd = float((residual_at(warp) ** 2).sum() / f_norm**2)
    return warp, znssd, iterations


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
    fitted, _znssd, _iterations = _refine(
        reference_image=reference_image,
        reference_gradients=_gradients(reference_image),
        current_coefficients=_spline_coefficients(current_image),
        reference_point=reference_point,
        initial_warp=_translation_warp(reference_point=reference_point, start=start),
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    return fitted


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
