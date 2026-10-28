"""Locating a displacement-field discontinuity from correlation-surface peak structure."""

from typing import NamedTuple

import numpy as np
from scipy.signal import find_peaks

from dictk.correlation import WindowingMethod, _window, zncc
from dictk.image import PixelCoordinate, SubpixelCoordinate, subimage


def peak_ratio(
    *, surface: np.ndarray, height_threshold: float = 0.2, distance: int = 2
) -> float:
    """Second-tallest / tallest resolvable peak height along `surface`'s own argmax column.

    A correlation surface computed from a window straddling a
    discontinuity shows two comparably-tall peaks, not one -- see
    [Synthetic Dislocation](../getting_started/synthetic_dislocation.html)
    and [Experimental
    Dislocation](../getting_started/experimental_dislocation.html). This
    turns that qualitative signature into a single number, generalizing
    `two_peak_separation` (Synthetic Dislocation's own sweep script,
    which reports the two peaks' separation, not their heights, and
    exists only to check a *known* offset against a *known* separation).
    No ground truth is needed here: a value near `1.0` means two
    comparably-tall peaks -- an ambiguous window, straddling a
    discontinuity. A value near `0.0` (or exactly `0.0`, one peak only)
    means a single, unambiguous match -- no discontinuity in this
    window.

    Restricted to one column, not the full 2D surface, matching
    `two_peak_separation`'s own approach: a straddling window's two
    candidate matches differ in `y` (the two halves' opposite vertical
    shifts, per
    [`crack_dislocation`](./image.html#crack_dislocation)) but land at
    the same `x` (neither half moves horizontally), so both peaks always
    fall in the same column, the one through the surface's own global
    maximum.

    Args:
        surface: A 2D correlation surface, e.g. from
            [`dictk.correlation.zncc`](./correlation.html#zncc).
        height_threshold: Minimum peak height to resolve, as a fraction
            of the column's own maximum. Passed to
            `scipy.signal.find_peaks`'s `height`. Default `0.2`, matching
            `two_peak_separation`'s own threshold.
        distance: Minimum separation, in pixels, between resolvable
            peaks. Passed to `scipy.signal.find_peaks`'s `distance`.
            Default `2`, matching `two_peak_separation`'s own value.

    Returns:
        The second-tallest peak's height divided by the tallest's, or
        `0.0` if fewer than two peaks are resolvable along the column,
        or if the column's own maximum is not positive (nothing to
        divide by).

    Raises:
        ValueError: If `surface` is not 2D.
    """
    if surface.ndim != 2:
        raise ValueError(f"surface must be 2D, got shape {surface.shape}")

    x_max = int(np.argmax(surface.max(axis=0)))
    column = surface[:, x_max]
    column_max = column.max()
    if column_max <= 0:
        return 0.0

    peaks, props = find_peaks(
        column, height=height_threshold * column_max, distance=distance
    )
    if len(peaks) < 2:
        return 0.0

    order = np.argsort(props["peak_heights"])[::-1][:2]
    tallest, second_tallest = props["peak_heights"][order]
    return float(second_tallest / tallest)


class DiscontinuitySweep(NamedTuple):
    """One [`sweep`](#sweep) result: window-center positions paired with
    each one's own [`peak_ratio`](#peak_ratio).

    Attributes:
        positions: Window-center positions, in `current_image`'s pixel
            reference frame, in sweep order.
        peak_ratios: Each position's own `peak_ratio`, index-aligned
            with `positions`.
    """

    positions: list[PixelCoordinate]
    peak_ratios: list[float]


def _validate_margins(
    *,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
) -> None:
    """Shared margin validation, matching `translation.locate`'s own checks."""
    if kernel_margin_width < 1:
        raise ValueError(f"kernel_margin_width {kernel_margin_width} must be >= 1")
    if kernel_margin_height < 1:
        raise ValueError(f"kernel_margin_height {kernel_margin_height} must be >= 1")
    if search_margin_width <= kernel_margin_width:
        raise ValueError(
            f"search_margin_width {search_margin_width} must be greater than "
            f"kernel_margin_width {kernel_margin_width}"
        )
    if search_margin_height <= kernel_margin_height:
        raise ValueError(
            f"search_margin_height {search_margin_height} must be greater than "
            f"kernel_margin_height {kernel_margin_height}"
        )


def sweep(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    start: PixelCoordinate,
    end: PixelCoordinate,
    samples: int,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None = None,
    height_threshold: float = 0.2,
    distance: int = 2,
) -> DiscontinuitySweep:
    """Evaluate `peak_ratio` at `samples` window-center positions evenly spaced from `start` to `end`.

    At each position, extracts a kernel from `reference_image` and a
    search area from `current_image`, both centered on that position
    (the same "center a window here" step [Synthetic
    Dislocation](../getting_started/synthetic_dislocation.html#moving-the-window-off-the-crack)
    does by hand at one fixed row), computes their ZNCC surface, and
    reads its `peak_ratio`. A discontinuity crossing the `start`-`end`
    line shows up as a rise in `peak_ratios` near the crossing, high on
    an ambiguous, straddling window and low everywhere else -- see
    [`locate`](#locate) to turn that rise into a single position.

    Args:
        reference_image: The reference (undeformed) 2D grayscale image.
        current_image: The current (deformed) 2D grayscale image.
        start: The first window-center position, in both images' shared
            pixel reference frame.
        end: The last window-center position.
        samples: Number of window-center positions, evenly spaced from
            `start` to `end` inclusive. Must be >= 2.
        kernel_margin_width: Half each kernel's width, in pixels. Must be
            >= 1.
        kernel_margin_height: Half each kernel's height, in pixels. Must
            be >= 1.
        search_margin_width: Half each search area's width, in pixels.
            Must be greater than `kernel_margin_width`.
        search_margin_height: Half each search area's height, in pixels.
            Must be greater than `kernel_margin_height`.
        windowing: Passed straight through to
            [`dictk.correlation.window`](./correlation.html#window) for
            both the kernel and search area at every position. Default
            `None` applies no windowing.
        height_threshold: Passed straight through to each position's own
            [`peak_ratio`](#peak_ratio) call.
        distance: Passed straight through to each position's own
            `peak_ratio` call.

    Returns:
        A `DiscontinuitySweep` pairing each swept position with its own
        `peak_ratio`, in sweep order.

    Raises:
        ValueError: If `samples` is less than 2, or the margin arguments
            are invalid (see `kernel_margin_width`/etc. above).
    """
    if samples < 2:
        raise ValueError(f"samples {samples} must be >= 2")
    _validate_margins(
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
    )

    positions = []
    peak_ratios = []
    for i in range(samples):
        t = i / (samples - 1)
        p0 = PixelCoordinate(
            x=round(start.x + t * (end.x - start.x)),
            y=round(start.y + t * (end.y - start.y)),
        )
        kernel = subimage(
            image=reference_image,
            origin=PixelCoordinate(
                x=p0.x - kernel_margin_width, y=p0.y - kernel_margin_height
            ),
            width=2 * kernel_margin_width,
            height=2 * kernel_margin_height,
        )
        search = subimage(
            image=current_image,
            origin=PixelCoordinate(
                x=p0.x - search_margin_width, y=p0.y - search_margin_height
            ),
            width=2 * search_margin_width,
            height=2 * search_margin_height,
        )
        kernel, search = _window(kernel=kernel, search=search, windowing=windowing)
        surface = zncc(kernel=kernel, search=search)
        positions.append(p0)
        peak_ratios.append(
            peak_ratio(
                surface=surface, height_threshold=height_threshold, distance=distance
            )
        )

    return DiscontinuitySweep(positions=positions, peak_ratios=peak_ratios)


def _parabolic_vertex(*, y0: float, y1: float, y2: float) -> float:
    """Fractional offset (in samples, from index 1) of the vertex of the parabola through three equally-spaced points.

    Pure math, no DIC-specific meaning -- fits $y = a(n - n_0)^2 + c$
    through `(0, y0)`, `(1, y1)`, `(2, y2)` and returns $n_0 - 1$, the
    vertex's offset from the center sample. The same 3-point parabolic
    refinement idea [Parallelism with PyTorch](../getting_started/parallelism_pytorch.html#subpixel-from-a-correlation-surface)
    already found measurably more accurate than upsampling-based
    subpixel refinement, applied here along a 1D `peak_ratio` sweep
    instead of a 2D correlation surface.

    Args:
        y0: Value one sample before the center.
        y1: Value at the center.
        y2: Value one sample after the center.

    Returns:
        The vertex's fractional offset from index 1, in samples.
        Positive means the true vertex sits past index 1, toward index
        2. `0.0` if `y0`, `y1`, `y2` are collinear (no curvature to fit
        -- a division by zero avoided, not a meaningful answer).
    """
    denominator = y0 - 2 * y1 + y2
    if denominator == 0:
        return 0.0
    return 0.5 * (y0 - y2) / denominator


def locate(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    start: PixelCoordinate,
    end: PixelCoordinate,
    samples: int,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None = None,
    height_threshold: float = 0.2,
    distance: int = 2,
) -> SubpixelCoordinate:
    """Locate a discontinuity crossing the `start`-`end` line, to subpixel precision.

    Calls [`sweep`](#sweep) with every argument passed straight through,
    takes its `peak_ratios`' argmax -- the most ambiguous, most likely
    straddling window swept -- and refines that sample to a fractional
    position along the line with a 3-point parabolic fit
    ([`_parabolic_vertex`](#_parabolic_vertex)) through it and its two
    neighbors.

    Args:
        reference_image: The reference (undeformed) 2D grayscale image.
        current_image: The current (deformed) 2D grayscale image.
        start: The first window-center position swept.
        end: The last window-center position swept.
        samples: Number of window-center positions swept. Must be >= 2
            (from `sweep`); in practice needs an argmax with an interior
            neighbor on each side, so effectively >= 3.
        kernel_margin_width: Half each kernel's width, in pixels. Must be
            >= 1.
        kernel_margin_height: Half each kernel's height, in pixels. Must
            be >= 1.
        search_margin_width: Half each search area's width, in pixels.
            Must be greater than `kernel_margin_width`.
        search_margin_height: Half each search area's height, in pixels.
            Must be greater than `kernel_margin_height`.
        windowing: Passed straight through to `sweep`.
        height_threshold: Passed straight through to `sweep`.
        distance: Passed straight through to `sweep`.

    Returns:
        The discontinuity's estimated crossing position along the
        `start`-`end` line, generally fractional.

    Raises:
        ValueError: If the `peak_ratios` argmax sits at either sweep
            endpoint (no interior neighbor to fit a parabola against --
            the sweep never found a clear internal peak, so refining one
            would be fabricating precision, not measuring it), or (from
            `sweep`) if `samples` is less than 2 or the margin arguments
            are invalid.
    """
    result = sweep(
        reference_image=reference_image,
        current_image=current_image,
        start=start,
        end=end,
        samples=samples,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
        windowing=windowing,
        height_threshold=height_threshold,
        distance=distance,
    )
    ratios = result.peak_ratios
    i = int(np.argmax(ratios))
    if i == 0 or i == len(ratios) - 1:
        raise ValueError(
            f"peak_ratios argmax sits at sweep endpoint (index {i} of "
            f"{len(ratios)}); no interior neighbor to refine against"
        )

    offset = _parabolic_vertex(y0=ratios[i - 1], y1=ratios[i], y2=ratios[i + 1])
    fractional_index = i + offset
    t = fractional_index / (samples - 1)
    return SubpixelCoordinate(
        x=start.x + t * (end.x - start.x),
        y=start.y + t * (end.y - start.y),
    )
